"""Fixtures for the coach tests (helpers live in tests/ai/helpers.py)."""

import pytest

from app.ai.ports import CoachContext
from app.ai.service import MemoryState
from tests.ai.helpers import LEO_NOTES, SKILLS_LEO, make_context


@pytest.fixture
def new_ctx() -> CoachContext:
    return make_context()


@pytest.fixture
def veteran_ctx() -> CoachContext:
    return make_context(
        first_name="Leo",
        skills=SKILLS_LEO,
        strength="vocabulary",
        challenge="listening",
        memory=MemoryState(sessions_count=4, notes=tuple({"text": n} for n in LEO_NOTES)),
    )
