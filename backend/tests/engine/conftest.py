import copy

import pytest

from app.engine import build_graph, compute_h
from tests.engine.helpers import enumerate_paths, load_docs


@pytest.fixture
def docs():
    return copy.deepcopy(load_docs())


@pytest.fixture(scope="session")
def graph():
    return build_graph(*load_docs())


@pytest.fixture(scope="session")
def h(graph):
    return compute_h(graph)


@pytest.fixture(scope="session")
def all_paths(graph, h):
    return enumerate_paths(graph, h)
