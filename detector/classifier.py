from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from xgboost import XGBClassifier


_PROJECT_ROOT = Path(__file__).parent.parent.resolve()
_MODEL_FILE = _PROJECT_ROOT / "data" / "processed" / "xgboost_model.json"
_META_FILE = _PROJECT_ROOT / "data" / "processed" / "xgboost_model_meta.json"

_model: XGBClassifier | None = None
_feature_names: list[str] | None = None


DEFAULT_FEATURE_NAMES = [
    "metadata_score",
    "embedding_score",
    "static_score",
    "graph_score",
    "name_length",
    "dep_count",
    "author_missing",
]


def _load_model() -> tuple[XGBClassifier | None, list[str]]:
    global _model, _feature_names

    if _model is not None and _feature_names is not None:
        return _model, _feature_names

    if not _MODEL_FILE.exists() or not _META_FILE.exists():
        _feature_names = DEFAULT_FEATURE_NAMES
        return None, _feature_names

    model = XGBClassifier()
    model.load_model(_MODEL_FILE)

    with open(_META_FILE, "r", encoding="utf-8") as file:
        meta = json.load(file)

    _model = model
    _feature_names = meta.get("feature_names", DEFAULT_FEATURE_NAMES)
    return _model, _feature_names


def build_feature_vector(
    package_name: str,
    metadata_score: float,
    embedding_score: float,
    static_score: float,
    graph_score: float,
    metadata: dict,
) -> dict[str, float]:
    dep_count = 0
    dependencies = metadata.get("dependencies")
    requires_dist = metadata.get("requires_dist")
    if isinstance(dependencies, dict):
        dep_count += len(dependencies)
    if isinstance(requires_dist, list):
        dep_count += len(requires_dist)

    return {
        "metadata_score": float(metadata_score),
        "embedding_score": float(embedding_score),
        "static_score": float(static_score),
        "graph_score": float(graph_score),
        "name_length": float(len(package_name)),
        "dep_count": float(dep_count),
        "author_missing": float(0 if metadata.get("author") else 1),
    }


def predict_classifier_risk(features: dict[str, float]) -> dict:
    model, feature_names = _load_model()
    row = np.array([[float(features.get(name, 0.0)) for name in feature_names]], dtype=np.float32)

    if model is None:
        heuristic_score = min(
            100.0,
            features.get("metadata_score", 0.0) * 0.4
            + features.get("static_score", 0.0) * 0.4
            + features.get("graph_score", 0.0) * 0.2,
        )
        return {
            "risk_score": round(heuristic_score, 2),
            "confidence": 0.5,
            "model": "heuristic-fallback",
            "feature_names": feature_names,
        }

    probability = float(model.predict_proba(row)[0][1])
    return {
        "risk_score": round(probability * 100.0, 2),
        "confidence": round(abs(probability - 0.5) * 2, 4),
        "model": "xgboost",
        "feature_names": feature_names,
    }
