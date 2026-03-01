from __future__ import annotations

import logging
from typing import Any

from api.config import get_settings
from detector.aggregator import aggregate_risk
from detector.classifier import build_feature_vector, predict_classifier_risk
from detector.layer1_metadata.metadata_analyzer import analyze_metadata_risk
from detector.layer2_embeddings.embedding_analyzer import analyze_embedding_risk
from detector.layer3_static.static_analyzer import analyze_static_risk
from detector.layer4_llm.llm_auditor import audit_code_with_llm
from detector.layer5_graph.blast_radius import calculate_blast_radius
from detector.layer5_graph.graph_analyzer import propagate_risk
from detector.layer5_graph.graph_builder import build_dependency_graph


logger = logging.getLogger(__name__)


def orchestrate_analysis(
    package_name: str,
    registry: str,
    metadata: dict,
    source_context: str,
    source_path: str | None = None,
) -> dict[str, Any]:
    settings = get_settings()

    metadata_result = analyze_metadata_risk(package_name, registry, metadata)
    embedding_result = analyze_embedding_risk(source_context)
    static_result = analyze_static_risk(source_context, source_path=source_path)

    graph = build_dependency_graph(package_name, registry, max_depth=3)
    base_scores = {
        package_name: float(metadata_result.get("final_score", 0.0)),
    }
    graph_scores = propagate_risk(graph, base_scores)
    graph_result = graph_scores.get(package_name, {"final_score": 0.0})
    blast_radius = calculate_blast_radius(graph, package_name)

    pre_llm_risk = max(
        float(metadata_result.get("final_score", 0.0)),
        float(static_result.get("final_score", 0.0)),
        float(graph_result.get("final_score", 0.0)),
    )

    llm_result = audit_code_with_llm(
        source_code=source_context,
        prior_layer_score=int(pre_llm_risk),
        trigger_threshold=settings.llm_trigger_threshold,
    )

    classifier_features = build_feature_vector(
        package_name=package_name,
        metadata_score=float(metadata_result.get("final_score", 0.0)),
        embedding_score=float(embedding_result.get("risk_score", 0.0)),
        static_score=float(static_result.get("final_score", 0.0)),
        graph_score=float(graph_result.get("final_score", 0.0)),
        metadata=metadata,
    )
    classifier_result = predict_classifier_risk(classifier_features)

    llm_score = float(llm_result.get("risk_score", 0.0))
    llm_triggered = bool(llm_result.get("llm_triggered", False))
    aggregate = aggregate_risk(
        metadata_score=float(metadata_result.get("final_score", 0.0)),
        embedding_score=float(embedding_result.get("risk_score", 0.0)),
        static_score=float(static_result.get("final_score", 0.0)),
        llm_score=llm_score,
        graph_score=float(graph_result.get("final_score", 0.0)),
        classifier_score=float(classifier_result.get("risk_score", 0.0)),
        llm_was_triggered=llm_triggered,
    )

    logger.info(
        "Analysis completed package=%s registry=%s final_score=%s decision=%s",
        package_name,
        registry,
        aggregate["final_score"],
        aggregate["decision"],
    )

    return {
        "package": package_name,
        "registry": registry,
        "final_score": aggregate["final_score"],
        "decision": aggregate["decision"],
        "aggregation": aggregate,
        "classifier": {
            **classifier_result,
            "features": classifier_features,
        },
        "layers": {
            "layer1_metadata": metadata_result,
            "layer2_embeddings": embedding_result,
            "layer3_static": static_result,
            "layer4_llm": llm_result,
            "layer5_graph": {
                "node_count": graph.number_of_nodes(),
                "edge_count": graph.number_of_edges(),
                "propagated": graph_result,
                "blast_radius": blast_radius,
            },
        },
    }
