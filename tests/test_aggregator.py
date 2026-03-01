from detector.aggregator import aggregate_risk


def test_aggregate_risk_bounds_and_decision() -> None:
    result = aggregate_risk(
        metadata_score=90,
        embedding_score=65,
        static_score=85,
        llm_score=80,
        graph_score=70,
        classifier_score=60,
    )

    assert 0 <= result["final_score"] <= 100
    assert result["decision"] == "block"
    assert result["consensus_signals"] >= 2
