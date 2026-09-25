"""to_state_view never exposes a forbidden field (api-contract §6, §9.A) on ANY node of the
fixture or the real mission, in any flag combination the content can produce."""

import itertools

import pytest

from app import engine
from app.engine import State
from app.services.state_view import to_state_view
from tests.fakes import load_docs
from tests.leak import OPEN_ATTEMPT_FORBIDDEN, forbidden_keys


@pytest.fixture(scope="module", params=["_fixture", "the-last-train"])
def loaded(request):
    graph = engine.build_graph(*load_docs(request.param))
    return graph, engine.compute_h(graph)


def _views(graph, h):
    flags = sorted(graph.declared_flags | {engine.TRAIN_DEPARTED})
    flag_sets = [
        frozenset(c) for n in range(len(flags) + 1) for c in itertools.combinations(flags, n)
    ][:32]
    for node_id, flag_set, decision in itertools.product(
        graph.nodes, flag_sets, ("quiet", "hint", "rescue")
    ):
        minutes = -2 if engine.TRAIN_DEPARTED in flag_set else 5
        state = State(node_id=node_id, minutes_left=minutes, flags=flag_set)
        yield (
            node_id,
            decision,
            to_state_view(
                attempt_id="a",
                mission_id="the-last-train",
                mission_title="The Last Train",
                status="in_progress",
                graph=graph,
                state=state,
                decision=decision,
            ).model_dump(mode="json"),
        )


def test_no_forbidden_key_on_any_node(loaded):
    graph, h = loaded
    for node_id, _, view in _views(graph, h):
        assert forbidden_keys(view, OPEN_ATTEMPT_FORBIDDEN) == [], node_id


def test_no_answer_content_or_explanation_text_on_any_node(loaded):
    graph, h = loaded
    secrets = set()
    for item in graph.items.values():
        secrets.add(item["explanation"])
        secrets.update(item["answer_key"].get("accepted", ()))
    for node_id, decision, view in _views(graph, h):
        text = repr(view)
        leaked = [s for s in secrets if f"'{s}'" in text]
        assert leaked == [], (node_id, decision, leaked)


def test_checkpoint_view_is_a_whitelist(loaded):
    graph, h = loaded
    for node_id in graph.nodes:
        if graph.kind(node_id) != "checkpoint":
            continue
        view = to_state_view(
            attempt_id="a",
            mission_id="m",
            mission_title="M",
            status="in_progress",
            graph=graph,
            state=State(node_id, 10),
            decision="quiet",
        )
        checkpoint = view.model_dump()["node"]["checkpoint"]
        assert set(checkpoint) == {"item_id", "type", "prompt", "stimulus", "options"}
        item = graph.item_at(node_id)
        if item["type"] == "fill_blank":
            assert checkpoint["options"] is None
        else:
            assert all(set(o) == {"id", "text"} for o in checkpoint["options"])


def test_the_hint_text_appears_only_as_mayas_line_on_hint(loaded):
    graph, h = loaded
    node_id = next(n for n in graph.nodes if graph.kind(n) == "checkpoint")
    item = graph.item_at(node_id)
    common = dict(
        attempt_id="a",
        mission_id="m",
        mission_title="M",
        status="in_progress",
        graph=graph,
        state=State(node_id, 10),
    )
    assert to_state_view(**common, decision="hint").maya.line == item["hint"]
    assert to_state_view(**common, decision="quiet").maya.line != item["hint"]


def test_clock_labels(loaded):
    graph, _ = loaded

    def label(minutes_left):
        return to_state_view(
            attempt_id="a",
            mission_id="m",
            mission_title="M",
            status="in_progress",
            graph=graph,
            state=State(graph.start_node, minutes_left),
            decision="quiet",
        ).clock.label

    assert label(18) == "21:47 · 18 min to departure"
    assert label(0) == "22:05 · Departing now"
    assert label(-2) == "22:07 · Train departed — Plan B"
