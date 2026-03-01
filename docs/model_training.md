# Model Training Guide

This document covers the complete ML training pipeline: dataset construction, feature engineering, model selection, training, evaluation, and reproducibility.

---

## Overview

The classifier is a supervised binary classification model that distinguishes between **benign** (label=0) and **malicious** (label=1) packages based on 7 engineered features extracted from the 5-layer detection pipeline.

---

## Dataset

| Source | Count | Label | Description |
|--------|-------|-------|-------------|
| Top PyPI packages | ~200 | 0 (benign) | High-download, well-maintained packages |
| Top npm packages | ~200 | 0 (benign) | Popular npm ecosystem packages |
| Backstabber's Knife Collection | 29 | 1 (malicious) | Known supply chain attack packages |
| **Total** | **429** | — | ~14:1 class imbalance |

**Data files:**
- `data/processed/benign_normalized.json` — 400 benign records
- `data/processed/malicious_normalized.json` — 29 malicious records

**Split strategy:** Stratified random split preserving class ratios:

| Split | Count | Purpose |
|-------|-------|---------|
| Train | 300 (~70%) | Model fitting |
| Validation | 64 (~15%) | Hyperparameter tuning |
| Test | 65 (~15%) | Final evaluation |

> See [docs/dataset.md](dataset.md) for detailed dataset documentation.

---

## Feature Engineering

Seven features are extracted per package by running the detection layers:

| Feature | Source | Type | Range | Description |
|---------|--------|------|-------|-------------|
| `metadata_score` | Layer 1 | Continuous | 0–100 | Composite: typosquat×0.4 + author×0.3 + version×0.3 |
| `embedding_score` | Layer 2 | Continuous | 0–100 | FAISS distance-based similarity score |
| `static_score` | Layer 3 | Continuous | 0–100 | Composite: AST×0.4 + semgrep×0.35 + obfuscation×0.25 |
| `graph_score` | Layer 5 | Continuous | 0–100 | Propagated transitive risk score |
| `name_length` | Package name | Integer | 1–100+ | Character count of package name |
| `dep_count` | Metadata | Integer | 0–100+ | Number of direct dependencies |
| `author_missing` | Metadata | Binary | 0 or 1 | Whether author field is absent |

### Feature extraction in training

The training script (`ml/train_classifier.py`) calls the actual Layer 1 (metadata) and Layer 3 (static) analyzers on each record. Layers 2 and 5 require live infrastructure (FAISS index, registry network access) so they produce zero scores in offline training.

### Feature importance (trained model)

| Feature | Importance | Interpretation |
|---------|-----------|----------------|
| `metadata_score` | 0.843 | Dominant signal — typosquat detection is the primary differentiator |
| `name_length` | 0.157 | Weak proxy — malicious names tend to be longer (typosquat patterns) |
| All others | 0.000 | Zero in offline eval (no source code → layers 2, 3, 5 produce zeros) |

---

## Algorithm Choice

**XGBoost** (`xgboost.XGBClassifier`) was selected for:

1. **Tabular data performance** — consistently top-performing on structured/tabular datasets
2. **Small sample handling** — regularization prevents overfitting with ~400 samples
3. **Class imbalance support** — native `scale_pos_weight` parameter
4. **Feature importance** — built-in gain/weight importance metrics
5. **No feature scaling** — tree-based models are invariant to feature scales
6. **Fast inference** — <5ms per prediction, suitable for real-time scoring
7. **Serialization** — JSON model format for easy versioning and deployment

### Why not deep learning?

With only 429 samples and 7 features, deep learning would overfit severely. XGBoost with regularization is the appropriate tool for this data regime.

### Why not logistic regression?

XGBoost captures non-linear interactions (e.g., high metadata_score + high name_length is more suspicious than either alone). Logistic regression would miss these.

---

## Hyperparameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `n_estimators` | 180 | Enough trees for convergence without overfitting |
| `max_depth` | 4 | Shallow trees for regularization |
| `learning_rate` | 0.08 | Low rate for stable convergence |
| `scale_pos_weight` | auto (~13.8) | Computed as `n_benign / n_malicious` to handle 14:1 imbalance |
| `eval_metric` | logloss | Binary cross-entropy for probabilistic outputs |
| `use_label_encoder` | False | Suppress deprecation warning |
| `random_state` | 42 | Reproducibility |

### Class imbalance handling

The `scale_pos_weight` parameter upweights malicious samples by the class ratio (~13.8×), effectively making each malicious sample count as ~14 benign samples during training. This dramatically improves recall at the cost of some precision.

---

## Training Pipeline

```python
# Simplified training flow (see ml/train_classifier.py for full code)

1. Load benign_normalized.json + malicious_normalized.json
2. Label: benign=0, malicious=1
3. Stratified split → train (300), val (64), test (65)
4. For each record:
   a. Run Layer 1 metadata analyzer → metadata_score
   b. Run Layer 3 static analyzer → static_score (0 if no source)
   c. Extract: name_length, dep_count, author_missing
   d. Set embedding_score=0, graph_score=0 (offline)
5. Construct feature matrix X (n×7), label vector y (n×1)
6. Train XGBClassifier on (X_train, y_train) with eval on (X_val, y_val)
7. Evaluate on (X_test, y_test)
8. Save model → data/processed/xgboost_model.json
9. Save metadata → data/processed/xgboost_model_meta.json
```

### Heuristic fallback

If the model file is not found at inference time, the classifier uses:

```python
score = metadata_score * 0.4 + static_score * 0.4 + graph_score * 0.2
```

This ensures the system works without a trained model, though with lower accuracy.

---

## Evaluation Results

### Baseline (all features)

| Metric | Value |
|--------|-------|
| **ROC-AUC** | **0.950** |
| Recall | 0.800 |
| Precision | 0.400 |
| F1 Score | 0.533 |

### Confusion Matrix (test set, threshold=0.5)

|  | Predicted Benign | Predicted Malicious |
|--|-----------------|-------------------|
| **Actual Benign** (60) | 54 (TN) | 6 (FP) |
| **Actual Malicious** (5) | 1 (FN) | 4 (TP) |

### Error Analysis

**False Positives** (6 benign flagged as malicious):
- All share: `metadata_score=10.5`, `author_missing=1`, various `name_length` values
- Root cause: Missing author metadata triggers moderate metadata risk, and name length serves as a noisy proxy

**False Negatives** (1 malicious missed):
- Package `dlogging` — predicted probability 0.39 (below 0.5 threshold)
- Low edit distance to legitimate packages insufficient to trigger high metadata score

### Ablation Study

| Configuration | Precision | Recall | F1 | AUC | ΔF1 |
|---------------|-----------|--------|-----|-----|-----|
| All features | 0.400 | 0.800 | 0.533 | 0.950 | — |
| − Metadata | 0.148 | 0.800 | 0.250 | 0.688 | −0.283 |
| − Embeddings | 0.400 | 0.800 | 0.533 | 0.950 | 0.000 |
| − Static | 0.400 | 0.800 | 0.533 | 0.950 | 0.000 |
| − Graph | 0.400 | 0.800 | 0.533 | 0.950 | 0.000 |
| − Identity | 1.000 | 0.800 | 0.889 | 0.900 | +0.356 |

**Key insight:** Identity features (`name_length`, `dep_count`, `author_missing`) actually hurt performance — removing them improves F1 from 0.533 to 0.889. This is because `name_length` is a spurious correlate in this small dataset. With a larger, more diverse dataset, identity features would provide useful signal.

---

## Reproducibility

### Retrain the model

```powershell
poetry run python ml/train_classifier.py
```

### Output artifacts

| File | Content |
|------|---------|
| `data/processed/xgboost_model.json` | Serialized XGBoost model |
| `data/processed/xgboost_model_meta.json` | Training metadata: features, metrics, split sizes, timestamp |

### Notebook evaluation

Notebooks 04 and 05 provide interactive evaluation:
- `notebooks/04_model_training.ipynb` — Training workflow, confusion matrix, ROC curve
- `notebooks/05_evaluation_ablation.ipynb` — Ablation study, false positive analysis

### Pre-compute cache for notebooks

```powershell
poetry run python notebooks/precompute_cache.py
```

Generates `data/processed/notebook_cache/` with pre-computed features and embeddings so notebooks run in < 5 seconds.
