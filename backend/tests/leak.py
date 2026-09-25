"""The recursive forbidden-field scanner (api-contract §9)."""

from typing import Any

# §9.A: no key anywhere in a StateView-bearing response while an attempt is open.
OPEN_ATTEMPT_FORBIDDEN = frozenset(
    {
        "is_correct",
        "correct",
        "incorrect",
        "outcome",
        "correct_option_id",
        "answer_key",
        "accepted",
        "accepted_answers",
        "correct_answer",
        "explanation",
        "hint",
        "skill",
        "cefr",
        "score_pct",
        "edges",
        "edge",
        "nodes",
        "next_node_id",
        "variants",
        "when_flag",
        "flags",
    }
)
# §9.B: everywhere except the Report of a submitted attempt.
ANSWER_KEY_FIELDS = frozenset(
    {
        "is_correct",
        "correct_option_id",
        "answer_key",
        "accepted",
        "accepted_answers",
        "correct_answer",
        "explanation",
    }
)


def forbidden_keys(payload: Any, forbidden: frozenset[str], path: str = "$") -> list[str]:
    found = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in forbidden:
                found.append(f"{path}.{key}")
            found += forbidden_keys(value, forbidden, f"{path}.{key}")
    elif isinstance(payload, list):
        for i, value in enumerate(payload):
            found += forbidden_keys(value, forbidden, f"{path}[{i}]")
    return found
