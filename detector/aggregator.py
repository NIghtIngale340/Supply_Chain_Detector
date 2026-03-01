from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AggregationWeights:
    metadata: float = 0.22
    embedding: float = 0.15
    static: float = 0.25
    llm: float = 0.18
    graph: float = 0.15
    classifier: float = 0.05


def _bounded(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def aggregate_risk(
    metadata_score: float,
    embedding_score: float,
    static_score: float,
    llm_score: float,
    graph_score: float,
    classifier_score: float,
    weights: AggregationWeights = AggregationWeights(),
    llm_was_triggered: bool = True,
) -> dict:
    # When LLM was not triggered (below threshold or disabled),
    # redistribute its weight proportionally to the other layers
    # so that inactive layers don't suppress the total score.
    if not llm_was_triggered:
        active_total = (
            weights.metadata + weights.embedding + weights.static
            + weights.graph + weights.classifier
        )
        scale = 1.0 / active_total if active_total > 0 else 1.0
        weighted = (
            _bounded(metadata_score) * weights.metadata * scale
            + _bounded(embedding_score) * weights.embedding * scale
            + _bounded(static_score) * weights.static * scale
            + _bounded(graph_score) * weights.graph * scale
            + _bounded(classifier_score) * weights.classifier * scale
        )
    else:
        weighted = (
            _bounded(metadata_score) * weights.metadata
            + _bounded(embedding_score) * weights.embedding
            + _bounded(static_score) * weights.static
            + _bounded(llm_score) * weights.llm
            + _bounded(graph_score) * weights.graph
            + _bounded(classifier_score) * weights.classifier
        )

    consensus = (
        (_bounded(metadata_score) >= 60)
        + (_bounded(static_score) >= 60)
        + (_bounded(llm_score) >= 60)
        + (_bounded(graph_score) >= 60)
    )

    consensus_boost = 5.0 * max(0, consensus - 1)
    final_score = _bounded(weighted + consensus_boost)

    if final_score >= 80:
        decision = "block"
    elif final_score >= 50:
        decision = "review"
    else:
        decision = "allow"

    return {
        "final_score": round(final_score, 2),
        "decision": decision,
        "consensus_signals": int(consensus),
        "weights": weights.__dict__,
        "weighted_score": round(weighted, 2),
        "consensus_boost": round(consensus_boost, 2),
    }
