"""Choose the coach provider from COACH_PROVIDER and expose it to submit (CR-004).

- COACH_PROVIDER=mock (default): the deterministic mock; no key, no network.
- COACH_PROVIDER=anthropic: Claude, if ANTHROPIC_API_KEY is set; otherwise the mock (logged).
- COACH_PROVIDER=openai_compatible: any OpenAI-compatible chat-completions API (Groq, xAI Grok,
  ...), if OPENAI_COMPAT_BASE_URL, OPENAI_COMPAT_API_KEY and OPENAI_COMPAT_MODEL are all set;
  otherwise the mock (logged).
- Unknown value or a constructor error: the mock (logged). Submit never breaks on configuration.
Timeouts, API errors and invalid output fall back per call (service.generate_feedback and
app.services.coach.run_coach).

Adding a provider: write <name>_provider.py implementing ports.CoachProvider and register a
builder in PROVIDERS. Nothing outside app/ai changes except the value of COACH_PROVIDER.
"""

import logging
from collections.abc import Callable
from functools import lru_cache
from typing import Any

from app.ai.mock_provider import MockCoachProvider
from app.ai.ports import CoachProvider

logger = logging.getLogger(__name__)


def _secret(value: Any) -> str | None:
    if value is None:
        return None
    raw = value.get_secret_value() if hasattr(value, "get_secret_value") else str(value)
    return raw.strip() or None


def _build_mock(settings: Any) -> CoachProvider:
    return MockCoachProvider()


def _build_anthropic(settings: Any) -> CoachProvider:
    api_key = _secret(getattr(settings, "anthropic_api_key", None))
    if not api_key:
        logger.warning("COACH_PROVIDER=anthropic but ANTHROPIC_API_KEY is empty; using the mock")
        return MockCoachProvider()
    from app.ai.anthropic_provider import AnthropicCoachProvider  # SDK imported only when used

    return AnthropicCoachProvider(api_key, getattr(settings, "anthropic_model", None) or None)


def _build_openai_compatible(settings: Any) -> CoachProvider:
    base_url = str(getattr(settings, "openai_compat_base_url", None) or "").strip()
    api_key = _secret(getattr(settings, "openai_compat_api_key", None))
    model = str(getattr(settings, "openai_compat_model", None) or "").strip()
    missing = [
        name
        for name, value in (
            ("OPENAI_COMPAT_BASE_URL", base_url),
            ("OPENAI_COMPAT_API_KEY", api_key),
            ("OPENAI_COMPAT_MODEL", model),
        )
        if not value
    ]
    if missing or api_key is None:
        logger.warning(
            "COACH_PROVIDER=openai_compatible but %s is empty; using the mock", ", ".join(missing)
        )
        return MockCoachProvider()
    from app.ai.openai_compatible_provider import OpenAICompatibleCoachProvider

    return OpenAICompatibleCoachProvider(
        base_url, api_key, model, label=getattr(settings, "openai_compat_label", None)
    )


PROVIDERS: dict[str, Callable[[Any], CoachProvider]] = {
    "mock": _build_mock,
    "anthropic": _build_anthropic,
    "openai_compatible": _build_openai_compatible,
}


def create_provider(settings: Any | None = None) -> CoachProvider:
    if settings is None:
        from app.core.config import get_settings

        settings = get_settings()
    name = str(getattr(settings, "coach_provider", "mock") or "mock").lower()
    builder = PROVIDERS.get(name)
    if builder is None:
        logger.warning("Unknown COACH_PROVIDER=%r; using the mock", name)
        return MockCoachProvider()
    try:
        return builder(settings)
    except Exception:
        logger.exception("Coach provider %r could not be created; using the mock", name)
        return MockCoachProvider()


class SubmitSeamAdapter:
    """What app.services.coach.run_coach expects (CR-004): provider / model / prompt_version /
    label attributes and generate(CoachRequest) -> dict. It converts the backend request into the
    port's CoachContext, calls the provider and returns the validated JSON. Errors propagate:
    run_coach turns them into the fallback within its 8-second budget."""

    def __init__(self, inner: CoachProvider) -> None:
        self.inner = inner
        self.provider = inner.provider
        self.label = inner.label
        self.model = inner.model
        self.prompt_version = inner.prompt_version

    def generate(self, request: Any) -> dict[str, str]:
        from app.ai.service import context_from_request

        feedback = self.inner.generate(context_from_request(request))
        if feedback.usage is not None:
            logger.info(
                "coach.usage provider=%s model=%s input_tokens=%d output_tokens=%d",
                self.provider,
                self.model,
                feedback.usage.input_tokens,
                feedback.usage.output_tokens,
            )
        return feedback.model_dump()


@lru_cache
def get_coach_provider() -> SubmitSeamAdapter:
    """The provider used by submit. Cached: one SDK client per process (settings are cached too).
    A mock here makes run_coach use the deterministic feedback directly (status fallback)."""
    return SubmitSeamAdapter(create_provider())
