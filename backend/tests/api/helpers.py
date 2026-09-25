"""Drive a mission through the HTTP API the way the frontend does (StateView in, action out).

The test knows the answer keys (it reads items.json); the client never receives them.
"""

from tests.fakes import load_docs
from tests.leak import OPEN_ATTEMPT_FORBIDDEN, forbidden_keys

ITEMS = {item["id"]: item for item in load_docs()[0]["items"]}


def answer_body(state: dict, correct: bool) -> dict:
    checkpoint = state["node"]["checkpoint"]
    item = ITEMS[checkpoint["item_id"]]
    if item["type"] == "fill_blank":
        text = item["answer_key"]["accepted"][0] if correct else "zzz wrong"
        return {"node_id": state["node"]["id"], "text": text}
    key = item["answer_key"]["correct_option_id"]
    wrong = next(o["id"] for o in item["options"] if o["id"] != key)
    return {"node_id": state["node"]["id"], "option_id": key if correct else wrong}


def play(client, mission_id="the-last-train", wrong=frozenset(), responses=None) -> dict:
    """Start (or resume) and play to the ending. `wrong` = item ids answered incorrectly.
    Every response body is appended to `responses` for the leak scan."""
    responses = [] if responses is None else responses
    r = client.post(f"/api/missions/{mission_id}/attempts")
    assert r.status_code in (200, 201), r.text
    responses.append(r.json())
    state = r.json()
    for _ in range(200):
        if state["status"] != "in_progress":
            return state
        if state["node"]["kind"] == "checkpoint":
            item_id = state["node"]["checkpoint"]["item_id"]
            r = client.post(
                f"/api/attempts/{state['attempt_id']}/answer",
                json=answer_body(state, item_id not in wrong),
            )
            assert r.status_code == 200, r.text
            responses.append(r.json())
            state = r.json()["state"]
        else:
            r = client.post(
                f"/api/attempts/{state['attempt_id']}/advance",
                json={"node_id": state["node"]["id"]},
            )
            assert r.status_code == 200, r.text
            responses.append(r.json())
            state = r.json()
        r = client.get(f"/api/attempts/{state['attempt_id']}")  # resume works at every node
        assert r.status_code == 200 and r.json() == state
        responses.append(r.json())
    raise AssertionError("the mission did not reach an ending")


def assert_no_leaks(responses: list) -> None:
    leaks = [path for body in responses for path in forbidden_keys(body, OPEN_ATTEMPT_FORBIDDEN)]
    assert leaks == [], leaks
