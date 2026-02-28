import networkx as nx

from detector.layer5_graph.blast_radius import calculate_blast_radius
from detector.layer5_graph.graph_analyzer import propagate_risk
from detector.layer5_graph.graph_builder import build_dependency_graph


def test_graph_builder_depth_limit_and_cycle_protection() -> None:
    adjacency = {
        "root": ["dep-a", "dep-b"],
        "dep-a": ["dep-c"],
        "dep-b": ["dep-c", "root"],
        "dep-c": ["dep-d"],
        "dep-d": [],
    }

    def _fetcher(name: str, registry: str) -> tuple[list[str], dict]:
        return adjacency.get(name, []), {"name": name, "registry": registry}

    graph = build_dependency_graph("root", "pypi", max_depth=2, dependency_fetcher=_fetcher)

    assert set(graph.nodes) == {"root", "dep-a", "dep-b", "dep-c"}
    assert ("dep-c", "dep-d") not in graph.edges
    assert graph.number_of_edges() >= 4


def test_propagate_risk_applies_distance_decay() -> None:
    graph = nx.DiGraph()
    graph.add_edges_from(
        [
            ("app", "lib-a"),
            ("lib-a", "lib-b"),
            ("app", "lib-direct"),
        ]
    )

    results = propagate_risk(
        graph,
        {
            "lib-b": 80,
            "lib-direct": 40,
        },
        decay=0.5,
    )

    assert results["lib-b"]["final_score"] == 80.0
    assert results["lib-a"]["final_score"] == 80.0
    assert results["app"]["final_score"] == 80.0
    assert results["app"]["top_contributors"][0]["source"] == "lib-direct"


def test_blast_radius_handles_central_and_leaf_and_missing() -> None:
    graph = nx.DiGraph()
    graph.add_edges_from(
        [
            ("app", "framework"),
            ("worker", "framework"),
            ("framework", "utils"),
        ]
    )

    central = calculate_blast_radius(graph, "framework")
    leaf = calculate_blast_radius(graph, "utils")
    missing = calculate_blast_radius(graph, "does-not-exist")

    assert central["affected_count"] == 2
    assert central["affected_packages"] == ["app", "worker"]
    assert leaf["affected_count"] == 3
    assert missing["affected_count"] == 0
