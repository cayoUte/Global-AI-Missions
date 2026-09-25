"""SHARED_CONTEXT §4-§5 on the REAL mission (qa-engineer), checked independently of the validator.

The validator is the code under test elsewhere; here every one of the 1,024 outcome paths of
The Last Train is enumerated with a plain tree search and each invariant is asserted directly.
"""

from collections import Counter

import pytest

from app.engine import RESCUE, SimulatedStudent, build_graph, compute_h, run
from tests.engine.helpers import REAL_DIR, enumerate_paths, load_docs

pytestmark = pytest.mark.skipif(
    not (REAL_DIR / "mission.json").exists(), reason="real mission not written"
)

BLUEPRINT = Counter(
    {
        ("multiple_choice", "grammar"): 2,
        ("multiple_choice", "listening"): 2,
        ("fill_blank", "grammar"): 2,
        ("comprehension", "reading"): 2,
        ("vocabulary", "vocabulary"): 2,
    }
)
CEFR_ORDER = ["A1", "A1", "A2", "A2", "A2", "B1", "B1", "B1", "B2", "B2"]
ENDINGS = {"made_it", "made_it_with_maya", "night_bus"}


@pytest.fixture(scope="module")
def real():
    graph = build_graph(*load_docs(REAL_DIR))
    h = compute_h(graph)
    return graph, h, enumerate_paths(graph, h)


def _checkpoints(graph, path):
    return [s.node_id for s, _ in path if graph.kind(s.node_id) == "checkpoint"]


def test_all_1024_paths_visit_the_same_10_checkpoints_with_the_4_2_2_2_blueprint(real):
    graph, _, paths = real
    assert len(paths) == 2**10
    sequences = {tuple(_checkpoints(graph, p)) for p in paths}
    assert len(sequences) == 1  # braided: one checkpoint order on every path
    (sequence,) = sequences
    assert len(sequence) == 10
    items = [graph.item_at(node) for node in sequence]
    assert len({i["id"] for i in items}) == 10
    assert Counter((i["type"], i["skill"]) for i in items) == BLUEPRINT
    assert [i["cefr"] for i in items] == CEFR_ORDER  # rising with the story clock


def test_every_path_ends_in_one_of_three_endings_with_at_most_one_rescue(real):
    graph, h, paths = real
    endings = Counter()
    for path in paths:
        final = path[-1][0]
        assert graph.kind(final.node_id) == "ending"
        endings[graph.nodes[final.node_id]["ending"]["key"]] += 1
        rescues = [t for _, t in path if t is not None and t.maya_decision == RESCUE]
        assert len(rescues) <= 1
        assert final.rescued == bool(rescues)
        for t in rescues:  # CR-002: a rescue is spent only if it can still save the train
            assert t.next_state.minutes_left - h[t.next_state.node_id] >= 0
        key = graph.nodes[final.node_id]["ending"]["key"]
        if key == "made_it_with_maya":  # this ending means Maya's rescue was used...
            assert final.rescued
        if key == "made_it":  # ...and made_it means it was not (a rescue may still end on the
            assert not final.rescued  # night bus if later misses lose the train, CR-002)
    assert set(endings) == ENDINGS  # every ending is reachable
    assert sum(endings.values()) == 1024


def test_the_heuristic_is_exact_admissible_and_consistent_on_the_real_graph(real):
    graph, h, paths = real
    for path in paths:
        if path[-1][0].rescued:  # h is defined over non-rescue edges
            continue
        final_minutes = path[-1][0].minutes_left
        for s, _ in path:
            assert 0 <= h[s.node_id] <= s.minutes_left - final_minutes
    for edge in graph.edges:
        if not edge.rescue:
            assert h[edge.source] <= edge.minutes + h[edge.target]
    all_correct = min(paths, key=lambda p: sum(1 for _, t in p if t and t.outcome == "incorrect"))
    assert h[graph.start_node] == all_correct[0][0].minutes_left - all_correct[-1][0].minutes_left


def test_the_simulator_is_deterministic_on_the_real_mission(real):
    graph, h, _ = real
    for profile in ("A1", "A2", "B1", "B2", "A2_weak_listening"):
        student = SimulatedStudent(profile)
        assert run(graph, h, student, 42) == run(graph, h, student, 42)
