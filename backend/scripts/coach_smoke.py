"""Live smoke test of the configured coach LLM: one real call, straight to the provider.

    cd backend && uv run python scripts/coach_smoke.py
    cd backend && uv run python scripts/coach_smoke.py --scenario new_student

Reads the provider exactly like the app (COACH_PROVIDER and its variables from the environment or
the repo-root .env, see .env.example) and calls it DIRECTLY, not through the service's fallback,
so a bad key, a wrong model id, a rate limit or invalid output shows up here as an error instead
of a quiet "Maya's notebook" report. Works for any adapter (openai_compatible, anthropic). One
real call on the realistic sample contexts of app/ai/samples.py (default: Leo, fifth session,
so the memory rule is exercised). No database is needed.

Prints provider, label, model, prompt version, latency, token usage and the validated JSON.
Exit codes: 0 ok; 1 the call failed, or took longer than the app's 8-second budget (the app
would have served the fallback); 2 the configuration resolves to the mock (nothing to test).
The API key is never printed.
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
# Placeholders so Settings loads without a database config (nothing connects to them).
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://smoke:smoke@127.0.0.1:5432/smoke")
os.environ.setdefault("JWT_SECRET", "smoke-only-placeholder-secret-0123456789abcdef")

import httpx  # noqa: E402

from app.ai.factory import create_provider  # noqa: E402
from app.ai.ports import CoachProviderError  # noqa: E402
from app.ai.samples import new_student, veteran  # noqa: E402
from app.ai.service import BUDGET_SECONDS  # noqa: E402

SCENARIOS = {"veteran": veteran, "new_student": new_student}
HINTS = {
    401: "the key was rejected: check the API key variable",
    403: "access denied: check the key's permissions, or a proxy/firewall blocking the host",
    404: "not found: check the model id and the base URL (it must end before /chat/completions)",
    429: "rate limited: wait a minute (free tiers allow few requests per minute)",
}


def _secret(value: Any) -> str | None:
    raw = value.get_secret_value() if hasattr(value, "get_secret_value") else value
    return (str(raw).strip() or None) if raw else None


def _redact(text: str, secrets: list[str]) -> str:
    for secret in secrets:
        text = text.replace(secret, "[redacted]")
    return text


def _describe_failure(exc: CoachProviderError, secrets: list[str]) -> list[str]:
    lines = [f"FAILED: {exc}"]
    cause = exc.__cause__
    if isinstance(cause, httpx.HTTPStatusError):
        status = cause.response.status_code
        if status in HINTS:
            lines.append(f"hint: {HINTS[status]}")
        lines.append("response body: " + _redact(cause.response.text[:500], secrets))
    elif cause is not None:
        lines.append(f"cause: {type(cause).__name__}: {_redact(str(cause)[:1500], secrets)}")
    return lines


def main(argv: list[str] | None = None, settings: Any | None = None) -> int:
    parser = argparse.ArgumentParser(description="One live call to the configured coach LLM.")
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), default="veteran")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    if settings is None:
        from app.core.config import get_settings

        settings = get_settings()
    secrets = [
        s
        for s in (
            _secret(getattr(settings, "openai_compat_api_key", None)),
            _secret(getattr(settings, "anthropic_api_key", None)),
        )
        if s
    ]
    provider = create_provider(settings)
    if provider.provider == "mock":
        print(
            f"COACH_PROVIDER={getattr(settings, 'coach_provider', 'mock')!r} resolves to the mock: "
            "nothing to test. Set COACH_PROVIDER=openai_compatible (or anthropic) and its "
            "variables (see .env.example); any warning above names what is missing.",
            file=sys.stderr,
        )
        return 2

    context = SCENARIOS[args.scenario]()
    print(f"provider:       {provider.provider}")
    print(f"label:          {provider.label}")
    print(f"model:          {provider.model}")
    print(f"prompt_version: {provider.prompt_version}")
    who = f"{context.first_name}, session {context.sessions_count}"
    print(f"scenario:       {args.scenario} ({who})")

    started = time.monotonic()
    try:
        feedback = provider.generate(context)
    except CoachProviderError as exc:
        latency_ms = int((time.monotonic() - started) * 1000)
        print(f"latency_ms:     {latency_ms}")
        print("\n".join(_describe_failure(exc, secrets)), file=sys.stderr)
        return 1
    except Exception as exc:  # the service would fall back on this too
        print(f"FAILED (unexpected): {type(exc).__name__}", file=sys.stderr)
        return 1
    latency_ms = int((time.monotonic() - started) * 1000)

    usage = feedback.usage
    print(f"latency_ms:     {latency_ms}")
    if usage is not None:
        print(f"tokens:         input={usage.input_tokens} output={usage.output_tokens}")
    print(json.dumps(feedback.model_dump(), ensure_ascii=False, indent=2))
    if latency_ms > BUDGET_SECONDS * 1000:
        print(
            f"TOO SLOW: {latency_ms} ms is over the app's {BUDGET_SECONDS:.0f} s budget; submit "
            "would serve the fallback. Try a faster model.",
            file=sys.stderr,
        )
        return 1
    print("OK: valid feedback within the budget.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
