"""In-memory login rate limit: at most 5 attempts per minute per (client IP, normalized email).

This is the ONE piece of per-instance state in the MVP (api-contract §5.3). With several API
instances each process counts separately; at scale it moves to a shared store (Redis) or to the
API gateway. Every login request counts, successful or not.
"""

import math
import threading
import time
from collections import deque
from collections.abc import Callable

from app.core.errors import DomainError, ErrorCode

LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 60.0


class SlidingWindowLimiter:
    def __init__(
        self,
        max_attempts: int,
        window_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def hit(self, key: str) -> None:
        """Record one attempt for `key`, or raise RATE_LIMITED if the window is full."""
        now = self._clock()
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and now - hits[0] >= self.window_seconds:
                hits.popleft()
            if len(hits) >= self.max_attempts:
                retry_after = max(1, math.ceil(self.window_seconds - (now - hits[0])))
                raise DomainError(
                    ErrorCode.RATE_LIMITED,
                    "Too many login attempts.",
                    {"retry_after_seconds": retry_after},
                    headers={"Retry-After": str(retry_after)},
                )
            hits.append(now)
            if len(self._hits) > 10_000:  # keep memory bounded: drop idle keys
                self._prune(now)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()

    def _prune(self, now: float) -> None:
        idle = [k for k, v in self._hits.items() if not v or now - v[-1] >= self.window_seconds]
        for key in idle:
            del self._hits[key]


login_limiter = SlidingWindowLimiter(LOGIN_MAX_ATTEMPTS, LOGIN_WINDOW_SECONDS)
