# Dataset Documentation

This document describes the datasets used for training, evaluation, and benchmarking.

---

## Overview

| Property | Value |
|----------|-------|
| Total records | 429 |
| Benign | 400 (93.2%) |
| Malicious | 29 (6.8%) |
| Class ratio | ~14:1 |
| Registries | PyPI, npm |
| Format | JSON (normalized) |

---

## Data Sources

### Benign Packages

**Source:** Top-1000 most downloaded packages from PyPI and npm.

| Registry | Count | Selection Criteria |
|----------|-------|--------------------|
| PyPI | ~200 | Top packages by monthly download count |
| npm | ~200 | Top packages by weekly download count |

**Package lists:**
- `data/top_packages/pypi_top_1000.json`
- `data/top_packages/npm_top_1000.json`

**Rationale:** High-download packages are maintained by established authors, have extensive review, and represent the "known-good" baseline for the embedding space and typosquat distance calculations.

### Malicious Packages

**Source:** [Backstabber's Knife Collection](https://dasfreak.github.io/Backstabbers-Knife-Collection/)

A curated, publicly-available research dataset of known malicious packages that were uploaded to PyPI and npm and subsequently removed by registry maintainers.

| Property | Value |
|----------|-------|
| Count | 29 |
| Attack types | Primarily typosquatting and code injection |
| Registries | PyPI and npm |
| Status | All removed from registries |

**Ethical note:** These packages are sourced from a published academic research dataset. No new malicious packages were created for this project.

---

## Data Collection Pipeline

```
1. data/datasets/build_benign_sample.py
   → Fetches metadata from PyPI/npm APIs
   → Saves to data/raw/

2. Manual curation of malicious samples
   → Source: Backstabber's Knife Collection
   → Saved to data/raw/

3. Normalization
   → Both sources normalized to common schema
   → Output: data/processed/benign_normalized.json
   →         data/processed/malicious_normalized.json
```

---

## Normalized Schema

Each record in the normalized JSON files contains:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Package name |
| `registry` | string | "pypi" or "npm" |
| `version` | string | Latest version at collection time |
| `author` | string/null | Author name (if available) |
| `author_email` | string/null | Author email |
| `description` | string/null | Package description |
| `dependencies` | list[string] | Direct dependency names |
| `source` | string | Registry source identifier |
| `source_code` | string/null | Source code text (if available) |
| `release_history` | list[dict] | Version release dates |
| `published_count` | int | Number of published versions |
| `created_at` | string/null | First publication date |

### Data completeness

| Field | Benign (400) | Malicious (29) |
|-------|-------------|---------------|
| `name` | 100% | 100% |
| `version` | 100% | 100% |
| `author` | ~85% | ~70% |
| `source_code` | 0% | 0% |
| `dependencies` | ~95% | ~80% |
| `release_history` | ~90% | ~60% |

**Important:** Source code is not available in the offline dataset (packages were not downloaded during collection). In live scanning mode, the fetcher downloads and extracts actual source tarballs.

---

## Train/Validation/Test Split

Stratified random split preserving class ratios:

| Split | Total | Benign | Malicious | Ratio |
|-------|-------|--------|-----------|-------|
| Train | 300 (70%) | ~280 | ~20 | ~14:1 |
| Validation | 64 (15%) | ~60 | ~4 | ~15:1 |
| Test | 65 (15%) | 60 | 5 | 12:1 |

Split files cached at `data/processed/notebook_cache/`:
- `features_train.npz` — X shape (300, 7), y shape (300,)
- `features_val.npz` — X shape (64, 7), y shape (64,)
- `features_test.npz` — X shape (65, 7), y shape (65,), names shape (65,)

---

## Feature Extraction

Features are computed from the normalized records using the actual detection layer code:

| Feature | Extraction Method |
|---------|------------------|
| `metadata_score` | `detector.layer1_metadata.metadata_analyzer.analyze_metadata_risk()` |
| `embedding_score` | `detector.layer2_embeddings.embedding_analyzer.analyze_embedding_risk()` — returns 0 offline |
| `static_score` | `detector.layer3_static.static_analyzer.analyze_static_risk()` — returns 0 without source |
| `graph_score` | Set to 0 (requires live registry access) |
| `name_length` | `len(package_name)` |
| `dep_count` | `len(metadata.get("dependencies", []))` |
| `author_missing` | `1 if not metadata.get("author") else 0` |

---

## Embedding Corpus

For Layer 2 evaluation, all 429 package records are embedded using `all-MiniLM-L6-v2`:

| Property | Value |
|----------|-------|
| Model | `all-MiniLM-L6-v2` |
| Dimensions | 384 |
| Input | Package name + description (fallback text for records without source) |
| Total embeddings | 429 |
| t-SNE coordinates | 429 × 2 (for visualization) |

Cached at `data/processed/notebook_cache/embeddings.npz`.

**Cluster quality:**

| Metric | Value |
|--------|-------|
| Silhouette Score | 0.609 |
| Inter-class L2 distance | 1.12 |
| Intra-class (benign) L2 | 0.39 |

---

## Known Limitations

1. **Small sample size** — 429 records is insufficient for robust generalization; risk of overfitting
2. **Class imbalance** — 14:1 ratio requires careful handling (`scale_pos_weight`)
3. **No source code** — offline dataset lacks source code, so Layers 2, 3, 5 produce zero scores
4. **Typosquat-heavy malicious set** — the Backstabber's Knife Collection skews toward typosquatting attacks
5. **Temporal bias** — packages collected at a specific point in time; attack patterns evolve
6. **No dependency confusion samples** — this attack type is underrepresented

### Planned improvements

- Add dependency confusion and protestware samples
- Collect source tarballs for all records
- Expand to 1000+ malicious samples from multiple sources
- Add temporal validation (train on older, test on newer packages)
