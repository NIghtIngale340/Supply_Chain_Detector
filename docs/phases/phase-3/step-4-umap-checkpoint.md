# Phase 3 — Step 4: UMAP Visualization Checkpoint

## Why this step now

This step validates Layer 2 behavior visually and gives you one of the strongest demo/interview artifacts in your project.

## Your coding target

Create `notebooks/03_embedding_clustering.ipynb`.

## Contract (must satisfy)

Notebook outputs should include:

1. 2D projection of benign embeddings
2. overlay of malicious package embeddings
3. color/label by class and optionally by cluster
4. short interpretation note: where separation is strong vs weak

Behavior:

- notebook reruns from saved processed artifacts
- no manual patching required between runs

Blueprint alignment:

- UMAP visualization showing malicious outliers against benign clusters

## Implementation notes (best practices)

1. Keep notebook deterministic (seed where possible)
2. Store intermediate vectors/labels to file for reproducibility
3. Add captions/markdown interpretation per figure
4. Explicitly call out false-overlap limitations

## Suggested mini-checklist while coding

- [ ] Load embedding vectors + labels
- [ ] Run UMAP reduction to 2D
- [ ] Plot class-colored scatter
- [ ] Add cluster overlays if available
- [ ] Write short conclusion cell

## Manual validation commands

```powershell
python -c "print('Run notebooks/03_embedding_clustering.ipynb end-to-end and verify plots render')"
```

Expected:

- notebook executes successfully
- visuals and interpretation are present

## Edge cases to handle now

- too few points for meaningful clusters
- extreme class imbalance in plotted subset
- non-finite embedding values

## Done criteria for Step 4

- Notebook exists and runs end-to-end
- Visual output supports Layer 2 decisions
- Phase 3 readiness documented

## Mentor tip

Use this notebook to explain tradeoffs, not just show pretty plots: discuss overlap, ambiguity, and where additional layers help.
