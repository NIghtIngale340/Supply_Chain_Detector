#!/usr/bin/env python
"""Pre-compute heavy data for notebooks so they load instantly.

Run once:
    python notebooks/precompute_cache.py

Generates:
    data/processed/notebook_cache/
        features_all.csv        — 7 features + label + package_name for all records
        features_train.npz      — X_train, y_train arrays
        features_val.npz        — X_val, y_val arrays
        features_test.npz       — X_test, y_test, test_names arrays
        embeddings.npz          — all_embs, all_labels, all_names, tsne_coords
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

# Resolve project root
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

DATA_DIR = PROJECT_ROOT / "data" / "processed"
SPLITS_DIR = DATA_DIR / "splits"
CACHE_DIR = DATA_DIR / "notebook_cache"
CACHE_DIR.mkdir(exist_ok=True)

from detector.layer1_metadata.metadata_analyzer import analyze_metadata_risk
from detector.layer3_static.static_analyzer import analyze_static_risk
from detector.classifier import DEFAULT_FEATURE_NAMES

FEATURE_NAMES = list(DEFAULT_FEATURE_NAMES)



def _dep_count(rec: dict) -> int:
    n = 0
    if isinstance(rec.get("dependencies"), dict):
        n += len(rec["dependencies"])
    if isinstance(rec.get("requires_dist"), list):
        n += len(rec["requires_dist"])
    return n


def extract_features(rec: dict) -> list[float]:
    name = str(rec.get("package_name", "")).strip().lower()
    reg = str(rec.get("registry", "")).strip().lower()
    src = str(rec.get("source_code", ""))
    dc = _dep_count(rec)

    meta = float(analyze_metadata_risk(name, reg, rec).get("final_score", 0.0))
    stat = float(analyze_static_risk(src).get("final_score", 0.0)) if src.strip() else 0.0
    emb = (25.0 if len(src) < 200 else 10.0) if src.strip() else 0.0
    graph = min(float(dc) * 5.0, 100.0)

    return [meta, emb, stat, graph, float(len(name)), float(dc),
            float(0 if rec.get("author") else 1)]


def build_matrix(records: list[dict]):
    X, y, names = [], [], []
    for r in records:
        label = str(r.get("label", "")).strip().lower()
        if label not in {"benign", "malicious"}:
            continue
        X.append(extract_features(r))
        y.append(1 if label == "malicious" else 0)
        names.append(r.get("package_name", ""))
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int32), names


def precompute_features():
    print("=" * 60)
    print(" Step 1/2: Feature extraction")
    print("=" * 60)

    # Full dataset features (for notebook 02)
    with open(DATA_DIR / "malicious_normalized.json", "r", encoding="utf-8") as f:
        mal = json.load(f)
    with open(DATA_DIR / "benign_normalized.json", "r", encoding="utf-8") as f:
        ben = json.load(f)
    for r in mal:
        r.setdefault("label", "malicious")
    for r in ben:
        r.setdefault("label", "benign")
    all_records = mal + ben

    rows = []
    t0 = time.time()
    for i, rec in enumerate(all_records):
        feats = extract_features(rec)
        row = dict(zip(FEATURE_NAMES, feats))
        row["label"] = rec.get("label", "unknown")
        row["package_name"] = rec.get("package_name", "")
        rows.append(row)
        if (i + 1) % 100 == 0:
            print(f"  [{i+1}/{len(all_records)}] ({time.time()-t0:.1f}s)")

    df = pd.DataFrame(rows)
    df.to_csv(CACHE_DIR / "features_all.csv", index=False)
    print(f"  Saved features_all.csv ({len(df)} rows) in {time.time()-t0:.1f}s")

    # Split features (for notebooks 04, 05)
    for split_name in ["train", "val", "test"]:
        recs = json.loads((SPLITS_DIR / f"{split_name}.json").read_text(encoding="utf-8"))
        X, y, names = build_matrix(recs)
        np.savez(CACHE_DIR / f"features_{split_name}.npz", X=X, y=y, names=names)
        print(f"  Saved features_{split_name}.npz  shape={X.shape}")

    print(f"  Feature extraction total: {time.time()-t0:.1f}s\n")


def precompute_embeddings():
    print("=" * 60)
    print(" Step 2/2: Embeddings + t-SNE projection")
    print("=" * 60)

    with open(DATA_DIR / "benign_normalized.json", "r", encoding="utf-8") as f:
        benign_data = json.load(f)
    with open(DATA_DIR / "malicious_normalized.json", "r", encoding="utf-8") as f:
        malicious_data = json.load(f)

    print(f"  Loading sentence-transformers model (this takes ~30s)...")
    t0 = time.time()
    from detector.layer2_embeddings.code_embedder import encode as embed_code
    print(f"  Model loaded in {time.time()-t0:.1f}s")

    def embed_dataset(records, label):
        embeddings, labels, names = [], [], []
        skipped = 0
        for rec in records:
            source = rec.get("source_code", "") or rec.get("source", "")
            # Fallback: use package name + registry as text when no source code
            if not source or not source.strip():
                name = rec.get("name", rec.get("package_name", ""))
                reg = rec.get("registry", "")
                source = f"package {name} registry {reg}"
            try:
                vec = embed_code(source)
                embeddings.append(vec)
                labels.append(label)
                names.append(rec.get("name", rec.get("package_name", "unknown")))
            except Exception:
                skipped += 1
        print(f"    [{label}] Embedded {len(embeddings)}, skipped {skipped}")
        return embeddings, labels, names

    print("  Embedding benign samples...")
    ben_embs, ben_labels, ben_names = embed_dataset(benign_data, "benign")
    print("  Embedding malicious samples...")
    mal_embs, mal_labels, mal_names = embed_dataset(malicious_data, "malicious")

    all_embs = np.vstack(ben_embs + mal_embs).astype(np.float32)
    all_labels = np.array(ben_labels + mal_labels)
    all_names = np.array(ben_names + mal_names)
    print(f"  Total embedding matrix: {all_embs.shape}")

    # t-SNE projection
    print("  Running t-SNE (2D projection)...")
    from sklearn.manifold import TSNE
    tsne = TSNE(n_components=2, random_state=42, perplexity=min(30, len(all_embs) - 1))
    tsne_coords = tsne.fit_transform(all_embs)
    print(f"  t-SNE done: {tsne_coords.shape}")

    np.savez(
        CACHE_DIR / "embeddings.npz",
        all_embs=all_embs,
        all_labels=all_labels,
        all_names=all_names,
        tsne_coords=tsne_coords,
    )
    print(f"  Saved embeddings.npz\n")


if __name__ == "__main__":
    print(f"\nProject root: {PROJECT_ROOT}")
    print(f"Cache dir:    {CACHE_DIR}\n")

    precompute_features()
    precompute_embeddings()

    print("=" * 60)
    print(" All caches generated. Notebooks will load instantly.")
    print("=" * 60)
