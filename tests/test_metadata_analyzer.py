from detector.layer1_metadata.metadata_analyzer import analyze_metadata_risk


def test_metadata_analyzer_returns_nonzero_score_for_suspicious_package() -> None:
    metadata = {
        "name": "colourama",
        "author": "x",
        "created_at": "2026-02-20T00:00:00Z",
        "published_count": 1,
        "version": "3.0.0",
        "release_history": [
            {"version": "1.2.0", "date": "2022-01-01T00:00:00Z"},
            {"version": "3.0.0", "date": "2026-02-01T00:00:00Z"},
        ],
    }

    result = analyze_metadata_risk("colourama", "pypi", metadata)

    assert result["final_score"] > 0
    assert result["decision"] in {"review", "high_risk"}
    assert result["layer_scores"]["typosquat"] > 0


def test_metadata_analyzer_thresholds_are_0_to_100_scale() -> None:
    metadata = {
        "name": "requests",
        "author": "trusted",
        "created_at": "2020-01-01T00:00:00Z",
        "published_count": 50,
        "version": "2.32.5",
        "release_history": [
            {"version": "2.32.4", "date": "2026-02-20T00:00:00Z"},
            {"version": "2.32.5", "date": "2026-02-21T00:00:00Z"},
        ],
    }

    result = analyze_metadata_risk("requests", "pypi", metadata)

    assert 0 <= result["final_score"] <= 100
    assert result["thresholds"]["review"] == 40
    assert result["thresholds"]["high_risk"] == 70
