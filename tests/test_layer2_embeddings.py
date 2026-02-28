import numpy as np

from detector.layer2_embeddings import embedding_analyzer


def test_embedding_risk_score_monotonic_bands() -> None:
    assert embedding_analyzer.embedding_risk_score(1.0) == 0
    assert 20 <= embedding_analyzer.embedding_risk_score(25.0) <= 60
    assert embedding_analyzer.embedding_risk_score(100.0) >= 60


def test_analyze_embedding_risk_handles_missing_index(monkeypatch) -> None:
    monkeypatch.setattr(embedding_analyzer, "embed_code", lambda _: np.zeros((384,), dtype=np.float32))

    def _missing_index(_embedding, k=5):  # noqa: ARG001
        raise FileNotFoundError("index missing")

    monkeypatch.setattr(embedding_analyzer, "find_nearest", _missing_index)

    result = embedding_analyzer.analyze_embedding_risk("print('hello')")

    assert result["risk_score"] == 0
    assert result["is_suspicious"] is False
    assert "FAISS index unavailable" in result["evidence"][0]


def test_analyze_embedding_risk_flags_far_neighbors(monkeypatch) -> None:
    monkeypatch.setattr(embedding_analyzer, "embed_code", lambda _: np.zeros((384,), dtype=np.float32))

    def _far_neighbors(_embedding, k=5):  # noqa: ARG001
        return [
            {"distance": 120.0, "index": 0, "name": "pkg-a", "registry": "pypi"},
            {"distance": 130.0, "index": 1, "name": "pkg-b", "registry": "npm"},
        ]

    monkeypatch.setattr(embedding_analyzer, "find_nearest", _far_neighbors)

    result = embedding_analyzer.analyze_embedding_risk("print('hello')")

    assert result["risk_score"] >= 60
    assert result["is_suspicious"] is True
    assert "distant from benign clusters" in result["evidence"][0]
