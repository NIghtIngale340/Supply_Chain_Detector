from collections import deque

import networkx as nx


def _severity_band(affected_count: int) -> str:
    if affected_count >= 25:
        return "critical"
    if affected_count >= 10:
        return "high"
    if affected_count >= 4:
        return "medium"
    if affected_count >= 1:
        return "low"
    return "none"


def calculate_blast_radius(graph: nx.DiGraph, package_name: str) -> dict:
    package = package_name.strip().lower()

    if not package:
        raise ValueError("Package name cannot be empty")
    if package not in graph:
        return {
            "package": package,
            "affected_count": 0,
            "affected_packages": [],
            "max_depth_affected": 0,
            "severity": "none",
        }

    reverse_graph = graph.reverse(copy=False)
    visited_distances: dict[str, int] = {}
    queue: deque[tuple[str, int]] = deque([(package, 0)])
    seen = {package}

    while queue:
        current, distance = queue.popleft()
        for dependent in sorted(reverse_graph.successors(current)):
            if dependent in seen:
                continue
            seen.add(dependent)
            next_distance = distance + 1
            visited_distances[dependent] = next_distance
            queue.append((dependent, next_distance))

    affected_packages = sorted(visited_distances.keys())
    max_depth = max(visited_distances.values(), default=0)
    affected_count = len(affected_packages)

    return {
        "package": package,
        "affected_count": affected_count,
        "affected_packages": affected_packages,
        "max_depth_affected": max_depth,
        "severity": _severity_band(affected_count),
    }
