from typing import Any

from detector.layer1_metadata.metadata_analyzer import analyze_metadata_risk
from detector.layer2_embeddings.embedding_analyzer import analyze_embedding_risk
from detector.layer3_static.static_analyzer import analyze_static_risk
from detector.layer4_llm.llm_auditor import audit_code_with_llm
from detector.layer5_graph.blast_radius import calculate_blast_radius
from detector.layer5_graph.graph_analyzer import propagate_risk
from detector.layer5_graph.graph_builder import build_dependency_graph
from fetcher.npm_fetcher import fetch_npm_metadata
from fetcher.pypi_fetcher import fetch_pypi_metadata


def _fetch_metadata(name: str, registry: str) -> dict:
    if registry == "pypi":
        result = fetch_pypi_metadata(name)
    else:
        result = fetch_npm_metadata(name)
    if result.status_code != 200:
        raise ValueError(f"Failed to fetch metadata for {name} from {registry}")
    return result.metadata


def run_analysis_for_package(name: str, registry: str) -> dict[str, Any]:
    normalized_name = name.strip().lower()
    metadata = _fetch_metadata(normalized_name, registry)

    metadata_result = analyze_metadata_risk(normalized_name, registry, metadata)
    source_context = str(metadata)

    embedding_result = analyze_embedding_risk(source_context)
    static_result = analyze_static_risk(source_context)
    llm_result = audit_code_with_llm(source_context, int(static_result.get("final_score", 0)))

    graph = build_dependency_graph(normalized_name, registry, max_depth=2)
    base_scores = {normalized_name: float(metadata_result.get("final_score", 0.0))}
    graph_scores = propagate_risk(graph, base_scores)
    blast_radius = calculate_blast_radius(graph, normalized_name)

    final_score = max(
        float(metadata_result.get("final_score", 0.0)),
        float(embedding_result.get("risk_score", 0.0)),
        float(static_result.get("final_score", 0.0)),
        float(llm_result.get("risk_score", 0.0)),
        float(graph_scores.get(normalized_name, {}).get("final_score", 0.0)),
    )

    return {
        "package": normalized_name,
        "registry": registry,
        "final_score": round(min(max(final_score, 0), 100), 2),
        "layers": {
            "layer1_metadata": metadata_result,
            "layer2_embeddings": embedding_result,
            "layer3_static": static_result,
            "layer4_llm": llm_result,
            "layer5_graph": {
                "node_count": graph.number_of_nodes(),
                "edge_count": graph.number_of_edges(),
                "propagated": graph_scores.get(normalized_name, {}),
                "blast_radius": blast_radius,
            },
        },
    }
