from detector import orchestrator


def test_orchestrator_returns_all_layers(monkeypatch) -> None:
    monkeypatch.setattr(
        orchestrator,
        "analyze_metadata_risk",
        lambda package_name, registry, metadata: {"final_score": 35, "evidence": []},
    )
    monkeypatch.setattr(
        orchestrator,
        "analyze_embedding_risk",
        lambda source_code: {"risk_score": 20, "evidence": []},
    )
    monkeypatch.setattr(
        orchestrator,
        "analyze_static_risk",
        lambda source_code, source_path=None: {"final_score": 45, "evidence": []},
    )
    monkeypatch.setattr(
        orchestrator,
        "build_dependency_graph",
        lambda package_name, registry, max_depth=3: __import__("networkx").DiGraph([(package_name, "dep")]),
    )
    monkeypatch.setattr(
        orchestrator,
        "propagate_risk",
        lambda graph, base_scores: {"requests": {"final_score": 30}},
    )
    monkeypatch.setattr(
        orchestrator,
        "calculate_blast_radius",
        lambda graph, package_name: {"affected_count": 1, "affected_packages": ["app"]},
    )
    monkeypatch.setattr(
        orchestrator,
        "audit_code_with_llm",
        lambda source_code, prior_layer_score, trigger_threshold=40: {"llm_triggered": True, "risk_score": 40},
    )
    monkeypatch.setattr(
        orchestrator,
        "predict_classifier_risk",
        lambda features: {"risk_score": 50, "confidence": 0.8, "model": "xgboost", "feature_names": list(features.keys())},
    )

    result = orchestrator.orchestrate_analysis(
        package_name="requests",
        registry="pypi",
        metadata={"author": "a", "dependencies": {}},
        source_context="print('x')",
    )

    assert "layers" in result
    assert "layer1_metadata" in result["layers"]
    assert "layer5_graph" in result["layers"]
    assert result["decision"] in {"allow", "review", "block"}
