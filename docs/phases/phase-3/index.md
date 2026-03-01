# Phase 3 — Layer 2 Code Embedding Similarity

## Objective

Implement blueprint Layer 2 by converting package source code into embeddings, searching nearest neighbors, and flagging outliers from legitimate clusters.

## Blueprint Alignment

This phase maps directly to:

- `code_embedder.py` with `encode(source_code: str) -> np.ndarray`
- FAISS index build over benign package embeddings
- cluster distance scoring against legitimate package groups
- UMAP visualization notebook for demo and analysis

## In Scope

- `detector/layer2_embeddings/code_embedder.py`
- `detector/layer2_embeddings/cluster_manager.py`
- `detector/layer2_embeddings/embedding_analyzer.py`
- `ml/build_faiss_index.py`
- `notebooks/03_embedding_clustering.ipynb`

## Out of Scope

- Static behavioral analysis (Phase 4 / Layer 3)
- LLM audit (Phase 5 / Layer 4)
- Dependency graph propagation (Phase 6 / Layer 5)

## Entry Criteria

- Phase 2 completed and validated
- Normalized benign/malicious datasets available from Phase 1
- Python 3.11+ runtime recommended before heavy ML dependencies

## Exit Criteria

- Embedding model encodes source text reliably
- FAISS index builds and queries nearest neighbors
- Cluster distance metric returns deterministic risk signal
- UMAP notebook shows separation trends and explains limitations

## Validation Commands

```powershell
python -m ruff check .
python -m pytest -q
```

## Active Step Sequence

1. `docs/phases/phase-3/step-1-code-embedder.md`
2. `docs/phases/phase-3/step-2-faiss-index.md`
3. `docs/phases/phase-3/step-3-cluster-manager.md`
4. `docs/phases/phase-3/step-4-umap-checkpoint.md`

## Deliverables

- Layer 2 modules implemented and tested
- Offline FAISS build script working on current dataset
- Notebook artifact for cluster visualization and interview storytelling
