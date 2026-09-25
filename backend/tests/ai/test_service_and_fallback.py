"""generate_feedback: every provider failure still yields valid feedback, fast (status fallback)."""

import time
from datetime import UTC, datetime

import anthropic
import httpx
import pytest

from app.ai.anthropic_provider import AnthropicCoachProvider
from app.ai.mock_provider import MockCoachProvider, compose_feedback
from app.ai.ports import CoachFeedback
from app.ai.service import MemoryState, generate_feedback, update_memory
from tests.ai.helpers import as_json, fake_client, good_output


class FakeProvider:
    provider, label, model, prompt_version = "fake", "Fake LLM", "fake-1", "v-test"

    def __init__(self, fn):
        self.fn = fn

    def generate(self, context):
        return self.fn(context)


def claude(text=None, **kwargs) -> AnthropicCoachProvider:
    return AnthropicCoachProvider("test-key", "claude-test", client=fake_client(text, **kwargs))


def assert_fallback(result, ctx, reason=None):
    feedback, meta = result
    assert meta.status == "fallback" and meta.provider == "mock"
    assert meta.provider_label == "Maya's notebook"
    assert feedback.model_dump() == compose_feedback(ctx).model_dump()
    if reason:
        assert meta.fallback_reason == reason


def test_mock_is_reported_as_fallback(new_ctx):
    assert_fallback(generate_feedback(new_ctx, MockCoachProvider()), new_ctx)
    assert_fallback(generate_feedback(new_ctx, None), new_ctx)


def test_valid_claude_output_is_ready_with_label_and_usage(new_ctx):
    provider = claude(as_json(good_output(new_ctx)))
    feedback, meta = generate_feedback(new_ctx, provider)
    assert meta.status == "ready" and meta.provider_label == "Claude"
    assert (meta.provider, meta.model, meta.prompt_version) == (
        "anthropic",
        "claude-test",
        "maya_feedback_v1",
    )
    assert (meta.input_tokens, meta.output_tokens) == (1800, 240)
    assert feedback.strength == "reading"
    call = provider._client.messages.calls[0]
    assert call["max_tokens"] <= 2000  # capped
    schema = call["output_config"]["format"]["schema"]
    assert schema["properties"]["strength"]["enum"] == ["reading"]
    assert schema["properties"]["next_mission_id"]["enum"] == list(new_ctx.candidate_mission_ids)


@pytest.mark.parametrize(
    "change",
    [{"strength": "cooking"}, {"challenge": "grammar"}, {"next_mission_id": "unknown-mission"}],
)
def test_invalid_skill_or_unknown_mission_falls_back(new_ctx, change):
    assert_fallback(
        generate_feedback(new_ctx, claude(as_json(good_output(new_ctx, **change)))), new_ctx
    )
    # Same from a provider that returns a raw mapping instead of a CoachFeedback.
    raw = FakeProvider(lambda ctx: good_output(ctx, **change))
    assert_fallback(generate_feedback(new_ctx, raw), new_ctx)


@pytest.mark.parametrize(
    "text",
    ["not json at all", "", '["a list"]', '{"summary": "half an object"', "```json\n{}\n```"],
)
def test_malformed_json_falls_back(new_ctx, text):
    assert_fallback(generate_feedback(new_ctx, claude(text)), new_ctx, "CoachProviderError")


def test_refusal_or_truncation_falls_back(new_ctx):
    for stop in ("refusal", "max_tokens"):
        text = as_json(good_output(new_ctx))
        assert_fallback(generate_feedback(new_ctx, claude(text, stop_reason=stop)), new_ctx)


def test_api_errors_fall_back(new_ctx):
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    errors = [
        anthropic.APITimeoutError(request=request),
        anthropic.APIConnectionError(request=request),
        anthropic.InternalServerError(
            "overloaded", response=httpx.Response(529, request=request), body=None
        ),
        anthropic.AuthenticationError(
            "bad key", response=httpx.Response(401, request=request), body=None
        ),
    ]
    for error in errors:
        assert_fallback(generate_feedback(new_ctx, claude(error=error)), new_ctx)


def test_timeout_falls_back_within_the_budget(new_ctx):
    def slow(ctx):
        time.sleep(2)
        return CoachFeedback.validated(good_output(ctx), ctx)

    started = time.monotonic()
    result = generate_feedback(new_ctx, FakeProvider(slow), budget_seconds=0.2)
    assert time.monotonic() - started < 1.5
    assert_fallback(result, new_ctx, "timeout")


def test_provider_exception_falls_back(new_ctx):
    def boom(ctx):
        raise RuntimeError("down")

    assert_fallback(generate_feedback(new_ctx, FakeProvider(boom)), new_ctx, "RuntimeError")


# --- memory -------------------------------------------------------------------------------------


def test_update_memory_first_session(new_ctx):
    feedback = compose_feedback(new_ctx)
    now = datetime(2026, 9, 25, 21, 0, tzinfo=UTC)
    memory = update_memory(None, feedback, now)
    assert memory.sessions_count == 1
    assert memory.notes == ({"text": feedback.memory_note, "created_at": now.isoformat()},)
    assert memory.next_greeting == feedback.next_greeting


def test_update_memory_keeps_the_last_five_newest_first(new_ctx):
    old = tuple({"text": f"note {i}", "created_at": "2026-09-0{i}"} for i in range(5))
    memory = update_memory(MemoryState(5, old, "old greeting"), compose_feedback(new_ctx))
    assert memory.sessions_count == 6
    assert len(memory.notes) == 5
    assert memory.notes[0]["text"].startswith("Strong in reading")
    assert [n["text"] for n in memory.notes[1:]] == ["note 0", "note 1", "note 2", "note 3"]
    assert memory.next_greeting != "old greeting"


def test_memory_round_trip_personalizes_the_next_report(new_ctx):
    """Session 1 writes a note; session 2 reads it back (sessions_count >= 2)."""
    from tests.ai.helpers import make_context

    memory = update_memory(None, compose_feedback(new_ctx))
    second = make_context(memory=memory)
    assert second.sessions_count == 2 and second.stage == "getting_to_know"
    summary = compose_feedback(second).summary
    assert "Once again, you did well with signs and messages." in summary
    assert "You still hesitate when someone speaks quickly." in summary
