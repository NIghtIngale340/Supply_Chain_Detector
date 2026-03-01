# Phase 3 — Step 3: Implement Cluster Manager and Distance Risk

## Why this step now

Nearest neighbors alone are not enough; you need a cluster-relative score to tell whether a package is far from legitimate software patterns.

## Your coding target

Create `detector/layer2_embeddings/cluster_manager.py` and optionally `detector/layer2_embeddings/embedding_analyzer.py`.

Implement interfaces such as:

- `assign_cluster(embedding: np.ndarray) -> str | int`
- `distance_to_nearest_cluster(embedding: np.ndarray) -> float`
- `embedding_risk_score(distance: float) -> int`

## Contract (must satisfy)

Input:

- package embedding vector

Output:

- nearest cluster identifier
- distance metric
- risk score (0-100)
- evidence text describing nearest cluster and distance

Behavior:

- deterministic distance computation
- safe behavior when clusters/index missing
- score increases with distance from legitimate clusters

Blueprint alignment:

- cluster outlier detection against legitimate package groups

## Implementation notes (best practices)

1. Start with centroid-based clusters from benign embeddings
2. Keep scoring threshold values explicit and documented
3. Return interpretable evidence for debugging/interviews
4. Separate math logic from I/O logic

## Suggested mini-checklist while coding

- [ ] Load FAISS index / centroids
- [ ] Compute nearest cluster and distance
- [ ] Map distance to risk score
- [ ] Return structured analysis object
- [ ] Add tests for near vs far examples

## Manual validation commands

```powershell
python -c "from detector.layer2_embeddings.embedding_analyzer import analyze_embedding_risk; print(analyze_embedding_risk('import requests\nprint(1)'))"
```

Expected:

- output includes distance and risk score
- evidence explains why score was assigned

## Edge cases to handle now

- FAISS index unavailable
- malformed embedding dimensions
- unsupported source type

## Done criteria for Step 3

- End-to-end embedding risk analysis returns stable output
- Tests cover error fallback and normal path
- Lint/tests pass

## Mentor tip

Treat distance-to-risk mapping as an explainable heuristic first; calibrate with data later.
