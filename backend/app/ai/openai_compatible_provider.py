"""OpenAI-compatible chat-completions adapter for the coach port (Groq, xAI Grok, any other).

One file, no SDK: a single `POST {base_url}/chat/completions` through httpx (already a
dependency), so the same code talks to Groq (https://api.groq.com/openai/v1), xAI
(https://api.x.ai/v1) or a local server, chosen only by environment variables (factory.py).

- Same prompt as the Claude adapter: the versioned system prompt and the delimited user message
  from prompting.py. There is no JSON schema here (not every compatible server supports one), so
  the request asks for JSON mode (response_format json_object) and the reply goes through the same
  strict parser and the same Pydantic validation (CoachFeedback.validated) as Claude's.
- Budget: the HTTP timeout is below the service's 8-second total budget and there are no
  retries; the service abandons anything slower anyway.
- Cost: max_tokens is capped and the temperature is low (a short, well-specified writing task).
- Any failure (HTTP error, timeout, non-JSON, refusal, truncation, invalid output) raises
  CoachProviderError; the service turns it into the deterministic fallback.
- The API key only travels in the Authorization header; it is never logged, and httpx masks it
  in reprs. Logs carry host, model, finish reason, token usage and latency only.
"""

import logging
import time
from typing import Any
from urllib.parse import urlparse

import httpx

from app.ai.ports import CoachContext, CoachFeedback, CoachProviderError, TokenUsage
from app.ai.prompting import PROMPT_VERSION, load_prompt, parse_json_object, render_user_message

logger = logging.getLogger(__name__)

PROVIDER_NAME = "openai_compatible"
REQUEST_TIMEOUT_SECONDS = 7.0
CONNECT_TIMEOUT_SECONDS = 3.0
MAX_TOKENS = 1500
TEMPERATURE = 0.3
_LOCAL_HOSTS = ("localhost", "127.0.0.1", "::1")
# Shown to the student when OPENAI_COMPAT_LABEL is not set ("Written by Maya using Groq.").
_KNOWN_HOSTS = (("groq.com", "Groq"), ("x.ai", "Grok (xAI)"))


def _host(base_url: str) -> str:
    return (urlparse(base_url).hostname or "").lower()


def default_label(base_url: str) -> str:
    """A neutral, honest label derived from the host; never a guess about the model."""
    host = _host(base_url)
    for domain, label in _KNOWN_HOSTS:
        if host == domain or host.endswith("." + domain):
            return label
    return "AI coach"


def normalize_base_url(base_url: str) -> str:
    """https only, except for a local server; a bearer key must not travel in clear text."""
    url = base_url.strip().rstrip("/")
    parsed = urlparse(url)
    if not parsed.hostname or parsed.scheme not in ("http", "https"):
        raise ValueError("OPENAI_COMPAT_BASE_URL must be an http(s) URL")
    if parsed.scheme == "http" and parsed.hostname not in _LOCAL_HOSTS:
        raise ValueError("OPENAI_COMPAT_BASE_URL must use https for a remote host")
    return url


class OpenAICompatibleCoachProvider:
    provider = PROVIDER_NAME

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        *,
        label: str | None = None,
        timeout_seconds: float = REQUEST_TIMEOUT_SECONDS,
        max_tokens: int = MAX_TOKENS,
        transport: httpx.BaseTransport | None = None,  # tests inject httpx.MockTransport
    ) -> None:
        if not api_key or not model:
            raise ValueError("an API key and a model are required")
        self.base_url = normalize_base_url(base_url)
        self.host = _host(self.base_url)
        self.model: str | None = model
        self.label = (label or "").strip() or default_label(self.base_url)
        self.prompt_version = PROMPT_VERSION
        self._max_tokens = max_tokens
        self._system = load_prompt(PROMPT_VERSION)
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=httpx.Timeout(timeout_seconds, connect=CONNECT_TIMEOUT_SECONDS),
            transport=transport,
        )

    def __repr__(self) -> str:  # never the key
        return f"OpenAICompatibleCoachProvider(host={self.host!r}, model={self.model!r})"

    def _payload(self, context: CoachContext) -> dict[str, Any]:
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self._system},
                {"role": "user", "content": render_user_message(context)},
            ],
            "response_format": {"type": "json_object"},
            "temperature": TEMPERATURE,
            "max_tokens": self._max_tokens,
        }

    def generate(self, context: CoachContext) -> CoachFeedback:
        started = time.monotonic()
        try:
            response = self._client.post("/chat/completions", json=self._payload(context))
            response.raise_for_status()
            body = response.json()
        except httpx.TimeoutException as exc:
            raise CoachProviderError(f"{self.host} request timed out") from exc
        except httpx.HTTPStatusError as exc:  # 401 bad key, 429 rate limit, 5xx, ...
            raise CoachProviderError(f"{self.host} API error {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:  # connection errors and the rest of httpx's errors
            raise CoachProviderError(f"{self.host} API error: {type(exc).__name__}") from exc
        except ValueError as exc:  # a 2xx whose body is not JSON (a proxy page, ...)
            raise CoachProviderError(f"{self.host} returned a non-JSON body") from exc

        try:
            choice = body["choices"][0]
            message = choice["message"]
            finish_reason = choice.get("finish_reason")
        except (KeyError, IndexError, TypeError) as exc:
            raise CoachProviderError("unexpected chat-completions response shape") from exc
        raw_usage = body.get("usage") if isinstance(body.get("usage"), dict) else {}
        usage = TokenUsage(
            input_tokens=int(raw_usage.get("prompt_tokens") or 0),
            output_tokens=int(raw_usage.get("completion_tokens") or 0),
        )
        logger.info(
            "coach.openai_compatible host=%s model=%s finish=%s input_tokens=%d "
            "output_tokens=%d latency_ms=%d",
            self.host,
            self.model,
            finish_reason,
            usage.input_tokens,
            usage.output_tokens,
            int((time.monotonic() - started) * 1000),
        )
        if not isinstance(message, dict) or message.get("refusal"):
            raise CoachProviderError("the model refused")
        if finish_reason != "stop":  # "length" (truncated), "content_filter", tool calls, ...
            raise CoachProviderError(f"unexpected finish_reason {finish_reason}")
        content = message.get("content")
        data = parse_json_object(content if isinstance(content, str) else None)
        try:
            feedback = CoachFeedback.validated(data, context)
        except ValueError as exc:  # pydantic.ValidationError is a ValueError
            raise CoachProviderError(f"{self.host} output failed validation") from exc
        return feedback.with_usage(usage)
