import re
from typing import Callable

import networkx as nx

from fetcher.npm_fetcher import fetch_npm_metadata
from fetcher.pypi_fetcher import fetch_pypi_metadata


DependencyFetcher = Callable[[str, str], tuple[list[str], dict]]


def _normalize_pypi_requirement(requirement: str) -> str | None:
    token = requirement.strip().split(";", 1)[0].strip()
    if not token:
        return None
    match = re.match(r"^([A-Za-z0-9_.-]+)", token)
    if not match:
        return None
    return match.group(1).lower()


def default_dependency_fetcher(package_name: str, registry: str) -> tuple[list[str], dict]:
    if registry == "pypi":
        result = fetch_pypi_metadata(package_name)
        metadata = result.metadata if result.status_code == 200 else {}
        raw = metadata.get("requires_dist", []) or []
        dependencies = sorted(
            {
                normalized
                for item in raw
                if isinstance(item, str)
                for normalized in [_normalize_pypi_requirement(item)]
                if normalized
            }
        )
        return dependencies, metadata

    if registry == "npm":
        result = fetch_npm_metadata(package_name)
        metadata = result.metadata if result.status_code == 200 else {}
        dep_map = metadata.get("dependencies", {}) or {}
        dependencies = sorted(dep_map.keys()) if isinstance(dep_map, dict) else []
        return dependencies, metadata

    raise ValueError("Unsupported registry. Use 'pypi' or 'npm'.")


def build_dependency_graph(
    package_name: str,
    registry: str,
    max_depth: int = 3,
    dependency_fetcher: DependencyFetcher | None = None,
) -> nx.DiGraph:
    if not package_name.strip():
        raise ValueError("Package name cannot be empty")
    if max_depth < 0:
        raise ValueError("max_depth must be >= 0")

    graph = nx.DiGraph()
    fetcher = dependency_fetcher or default_dependency_fetcher
    root = package_name.strip().lower()

    def _walk(current: str, depth: int, active_path: set[str]) -> None:
        if depth > max_depth:
            return

        if current not in graph:
            graph.add_node(current, registry=registry, depth=depth)

        dependencies, metadata = fetcher(current, registry)
        graph.nodes[current]["metadata"] = metadata
        graph.nodes[current]["depth"] = min(graph.nodes[current].get("depth", depth), depth)

        if depth == max_depth:
            return

        for dep in sorted(set(dependencies)):
            normalized_dep = dep.strip().lower()
            if not normalized_dep:
                continue

            if normalized_dep not in graph:
                graph.add_node(normalized_dep, registry=registry, depth=depth + 1)
            else:
                graph.nodes[normalized_dep]["depth"] = min(
                    graph.nodes[normalized_dep].get("depth", depth + 1), depth + 1
                )

            graph.add_edge(current, normalized_dep)

            if normalized_dep in active_path:
                continue

            _walk(normalized_dep, depth + 1, active_path | {normalized_dep})

    _walk(root, 0, {root})
    return graph
