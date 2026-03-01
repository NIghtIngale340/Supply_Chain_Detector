from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from xgboost import XGBClassifier

from data.datasets.label_and_split import label_and_split
from detector.classifier import DEFAULT_FEATURE_NAMES
from detector.layer1_metadata.metadata_analyzer import analyze_metadata_risk
from detector.layer3_static.static_analyzer import analyze_static_risk


PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DATA_DIR = PROJECT_ROOT / "data" / "processed"
BENIGN_FILE = DATA_DIR / "benign_normalized.json"
MALICIOUS_FILE = DATA_DIR / "malicious_normalized.json"
MODEL_FILE = DATA_DIR / "xgboost_model.json"
META_FILE = DATA_DIR / "xgboost_model_meta.json"
SPLITS_DIR = DATA_DIR / "splits"
TRAIN_FILE = SPLITS_DIR / "train.json"
VAL_FILE = SPLITS_DIR / "val.json"
TEST_FILE = SPLITS_DIR / "test.json"

FEATURE_NAMES = list(DEFAULT_FEATURE_NAMES)


def _load_json(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as file:
        payload = json.load(file)
    return payload if isinstance(payload, list) else []


def _dependency_count(record: dict) -> int:
    total = 0
    dependencies = record.get("dependencies")
    requires_dist = record.get("requires_dist")
    if isinstance(dependencies, dict):
        total += len(dependencies)
    if isinstance(requires_dist, list):
        total += len(requires_dist)
    return total


def _extract_features(record: dict) -> list[float]:
    package_name = str(record.get("package_name", record.get("name", ""))).strip().lower()
    registry = str(record.get("registry", "")).strip().lower()
    source_code = str(record.get("source_code", ""))
    dep_count = _dependency_count(record)

    metadata_score = float(
        analyze_metadata_risk(
            package_name=package_name,
            registry=registry,
            metadata=record,
        ).get("final_score", 0.0)
    )

    static_score = float(analyze_static_risk(source_code).get("final_score", 0.0)) if source_code else 0.0

    embedding_score = 0.0
    if source_code.strip():
        size = len(source_code)
        if size < 200:
            embedding_score = 25.0
        elif size < 1_000:
            embedding_score = 10.0

    graph_score = min(float(dep_count) * 5.0, 100.0)

    return [
        metadata_score,
        embedding_score,
        static_score,
        graph_score,
        float(len(package_name)),
        float(dep_count),
        float(0 if record.get("author") else 1),
    ]


def _load_or_create_splits() -> tuple[list[dict], list[dict], list[dict]]:
    train = _load_json(TRAIN_FILE)
    val = _load_json(VAL_FILE)
    test = _load_json(TEST_FILE)
    if train and val and test:
        return train, val, test

    label_and_split(
        malicious_path=str(MALICIOUS_FILE),
        benign_path=str(BENIGN_FILE),
        output_dir=str(SPLITS_DIR),
        seed=42,
        force=True,
    )

    return _load_json(TRAIN_FILE), _load_json(VAL_FILE), _load_json(TEST_FILE)


def _build_matrix(records: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    x_rows: list[list[float]] = []
    y_rows: list[int] = []

    for row in records:
        label = str(row.get("label", "")).strip().lower()
        if label not in {"benign", "malicious"}:
            continue
        x_rows.append(_extract_features(row))
        y_rows.append(1 if label == "malicious" else 0)

    if not x_rows:
        return np.empty((0, len(FEATURE_NAMES)), dtype=np.float32), np.empty((0,), dtype=np.int32)
    return np.array(x_rows, dtype=np.float32), np.array(y_rows, dtype=np.int32)


def _calc_metrics(y_true: np.ndarray, proba: np.ndarray) -> dict[str, float]:
    if y_true.size == 0:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "roc_auc": 0.0}

    y_pred = (proba >= 0.5).astype(np.int32)
    metrics = {
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }
    if len(np.unique(y_true)) < 2:
        metrics["roc_auc"] = 0.0
    else:
        metrics["roc_auc"] = float(roc_auc_score(y_true, proba))
    return metrics


def train_and_save() -> None:
    train_records, val_records, test_records = _load_or_create_splits()
    if not train_records:
        raise RuntimeError("Training split missing or empty")

    x_train, y_train = _build_matrix(train_records)
    x_val, y_val = _build_matrix(val_records)
    x_test, y_test = _build_matrix(test_records)

    if x_train.size == 0:
        raise RuntimeError("No usable rows in training split")

    negative = int((y_train == 0).sum())
    positive = int((y_train == 1).sum())
    scale_pos_weight = float(negative / positive) if positive > 0 else 1.0

    model = XGBClassifier(
        n_estimators=180,
        max_depth=4,
        learning_rate=0.08,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=42,
        scale_pos_weight=scale_pos_weight,
    )

    eval_set = [(x_val, y_val)] if x_val.size and y_val.size else None
    model.fit(x_train, y_train, eval_set=eval_set, verbose=False)

    val_proba = model.predict_proba(x_val)[:, 1] if x_val.size else np.array([], dtype=np.float32)
    test_proba = model.predict_proba(x_test)[:, 1] if x_test.size else np.array([], dtype=np.float32)

    val_metrics = _calc_metrics(y_val, val_proba)
    test_metrics = _calc_metrics(y_test, test_proba)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    model.save_model(MODEL_FILE)

    with open(META_FILE, "w", encoding="utf-8") as file:
        json.dump(
            {
                "feature_names": FEATURE_NAMES,
                "training_rows": int(len(y_train)),
                "validation_rows": int(len(y_val)),
                "test_rows": int(len(y_test)),
                "benign_train_rows": negative,
                "malicious_train_rows": positive,
                "scale_pos_weight": scale_pos_weight,
                "val_metrics": val_metrics,
                "test_metrics": test_metrics,
            },
            file,
            indent=2,
        )

    print(f"Saved model to {MODEL_FILE}")
    print(f"Saved metadata to {META_FILE}")
    print(f"Validation metrics: {val_metrics}")
    print(f"Test metrics: {test_metrics}")


if __name__ == "__main__":
    train_and_save()
