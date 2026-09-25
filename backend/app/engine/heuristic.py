"""h(n): the exact minimum story-minutes from node n to any ending, ignoring rescue edges.

Computed once per mission version with a backward uniform-cost search: Dijkstra on the
reversed graph, starting from every ending at cost 0 (several goal states).

Why it is admissible: h(n) is the cheapest cost over *all* non-rescue paths from n, as if every
remaining answer were correct. The student's real path is one of those paths (or uses the rescue
edge, which the content keeps no cheaper than the correct edge), so h(n) never overestimates.
Why it is consistent: shortest-path distances obey the triangle inequality, so for every
non-rescue edge n -> n' with cost c, h(n) <= c + h(n'). Rescue edges are excluded because the
rescue is a one-time resource that depends on the state, while h must depend on the node only.
"""

import heapq
from collections import defaultdict

from app.engine.graph import ENDING, Edge, MissionGraph


def compute_h(graph: MissionGraph) -> dict[str, int]:
    incoming: dict[str, list[Edge]] = defaultdict(list)  # the reversed graph
    for edge in graph.edges:
        if not edge.rescue:
            incoming[edge.target].append(edge)
    frontier = [(0, node_id) for node_id in graph.nodes if graph.kind(node_id) == ENDING]
    heapq.heapify(frontier)
    h: dict[str, int] = {}  # doubles as the explored set
    while frontier:
        cost, node_id = heapq.heappop(frontier)
        if node_id in h:
            continue  # already settled with a cheaper (or equal) cost
        h[node_id] = cost
        for edge in incoming[node_id]:
            if edge.source not in h:
                heapq.heappush(frontier, (cost + edge.minutes, edge.source))
    return h
