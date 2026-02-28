from collections.abc import Mapping

import networkx as nx


def propagate_risk(
    graph: nx.DiGraph,
    base_scores: Mapping[str, float],
    decay: float = 0.6,
    max_explanations: int = 3,
) -> dict[str, dict]:
    if not (0 < decay <= 1):
        raise ValueError("decay must be in (0, 1]")

    normalized_scores = {str(k).lower(): float(v) for k, v in base_scores.items()}
    results: dict[str, dict] = {}

    for node in sorted(graph.nodes):
        node_key = str(node).lower()
        direct_score = max(0.0, min(100.0, normalized_scores.get(node_key, 0.0)))

        contributions: list[dict] = []
        propagated_total = 0.0

        for risky_node, risky_score in normalized_scores.items():
            if risky_node == node_key or risky_node not in graph:
                continue

            try:
                distance = nx.shortest_path_length(graph, source=node, target=risky_node)
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue

            if distance <= 0:
                continue

            contribution = max(0.0, min(100.0, risky_score)) * (decay ** (distance - 1))
            propagated_total += contribution
            contributions.append(
                {
                    "source": risky_node,
                    "distance": distance,
                    "base_score": round(float(risky_score), 2),
                    "contribution": round(contribution, 2),
                }
            )

        final_score = max(0.0, min(100.0, direct_score + propagated_total))
        top_contributors = sorted(
            contributions,
            key=lambda item: (-item["contribution"], item["distance"], item["source"]),
        )[:max_explanations]

        results[node_key] = {
            "base_score": round(direct_score, 2),
            "propagated_score": round(min(100.0, propagated_total), 2),
            "final_score": round(final_score, 2),
            "top_contributors": top_contributors,
        }

    return results
