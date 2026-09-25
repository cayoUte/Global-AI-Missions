"""Mission content as engine objects, cached in memory by mission version id.

Versions are immutable (a content change creates a new version), so a cache entry never goes
stale: build the MissionGraph and h(n) once per version per process. The graph holds answer keys
in memory on the server only; nothing here is ever serialized to a client.
"""

import threading
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app import engine
from app.engine import MissionGraph
from app.repositories import missions as missions_repo


@dataclass(frozen=True)
class LoadedMission:
    graph: MissionGraph
    h: dict[str, int]


_cache: dict[Any, LoadedMission] = {}
_lock = threading.Lock()


def get_loaded_mission(session: Session, mission_version_id: Any) -> LoadedMission:
    key = str(mission_version_id)
    cached = _cache.get(key)
    if cached is not None:
        return cached
    docs = missions_repo.load_mission_content(session, mission_version_id)
    graph = engine.build_graph(docs.items_doc, docs.mission_doc)
    loaded = LoadedMission(graph=graph, h=engine.compute_h(graph))
    with _lock:
        return _cache.setdefault(key, loaded)


def clear_cache() -> None:
    """Tests only."""
    with _lock:
        _cache.clear()
