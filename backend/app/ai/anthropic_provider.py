"""Claude adapter for the coach port (official Anthropic SDK). The only file that imports it.

- Structured outputs: output_config.format = a JSON schema, so the reply is one JSON object whose
  strength / challenge / next_mission_id are constrained by enums. The reply is still parsed and
  validated with Pydantic (CoachFeedback.validated) before anything is trusted.
- Budget: the HTTP timeout is below the service's 8-second total budget and retries are off, so a
  slow call ends by itself instead of lingering after the fallback has been served.
- Cost: max_tokens is capped and effort is "low" (a short, well-specified writing task).
- Any failure raises CoachProviderError; the service turns it into the deterministic fallback.
"""

import logging
import time
from typing import Any

import anthropic

from app.ai.ports import CoachContext, CoachFeedback, CoachProviderError, TokenUsage
from app.ai.prompting import (
    PROMPT_VERSION,
    load_prompt,
    output_schema,
    parse_json_object,
    render_user_message,
)

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-opus-5"
REQUEST_TIMEOUT_SECONDS = 7.0
MAX_TOKENS = 1500
# Models without the effort parameter (it returns a 400 there).
_NO_EFFORT_PREFIXES = ("claude-haiku-4", "claude-sonnet-4-5", "claude-3")


class AnthropicCoachProvider:
    provider = "anthropic"
    label = "Claude"

    def __init__(
        self,
        api_key: str,
        model: str | None = None,
        *,
        timeout_seconds: float = REQUEST_TIMEOUT_SECONDS,
        max_tokens: int = MAX_TOKENS,
        client: Any | None = None,  # tests inject a fake with .messages.create(...)
    ) -> None:
        self.model: str | None = model or DEFAULT_MODEL
        self.prompt_version = PROMPT_VERSION
        self._max_tokens = max_tokens
        self._system = load_prompt(PROMPT_VERSION)
        self._client = client or anthropic.Anthropic(
            api_key=api_key, timeout=timeout_seconds, max_retries=0
        )

    def generate(self, context: CoachContext) -> CoachFeedback:
        started = time.monotonic()
        output_config: dict[str, Any] = {
            "format": {"type": "json_schema", "schema": output_schema(context)}
        }
        if not str(self.model).startswith(_NO_EFFORT_PREFIXES):
            output_config["effort"] = "low"
        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=self._max_tokens,
                system=self._system,
                messages=[{"role": "user", "content": render_user_message(context)}],
                output_config=output_config,
            )
        except anthropic.APITimeoutError as exc:
            raise CoachProviderError("Claude request timed out") from exc
        except anthropic.APIStatusError as exc:
            raise CoachProviderError(f"Claude API error {exc.status_code}") from exc
        except anthropic.APIError as exc:  # connection errors and the rest of the SDK's errors
            raise CoachProviderError(f"Claude API error: {type(exc).__name__}") from exc

        usage = TokenUsage(
            input_tokens=int(getattr(response.usage, "input_tokens", 0) or 0),
            output_tokens=int(getattr(response.usage, "output_tokens", 0) or 0),
        )
        logger.info(
            "coach.anthropic model=%s stop=%s input_tokens=%d output_tokens=%d latency_ms=%d",
            self.model,
            response.stop_reason,
            usage.input_tokens,
            usage.output_tokens,
            int((time.monotonic() - started) * 1000),
        )
        if response.stop_reason != "end_turn":  # refusal, max_tokens, ...
            raise CoachProviderError(f"unexpected stop_reason {response.stop_reason}")
        text = next((b.text for b in response.content if getattr(b, "type", "") == "text"), None)
        data = parse_json_object(text)
        try:
            feedback = CoachFeedback.validated(data, context)
        except ValueError as exc:  # pydantic.ValidationError is a ValueError
            raise CoachProviderError("Claude output failed validation") from exc
        return feedback.with_usage(usage)
