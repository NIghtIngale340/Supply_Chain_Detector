# Phase 1 — Step 8: First EDA Checkpoint Notebook

## Why this step now

This is your Phase 1 validation narrative. You confirm dataset quality before moving into detection layers.

## Your coding target

Create `notebooks/01_eda_and_dataset.ipynb` with deterministic cells for data quality checks.

## Contract (must satisfy)

Notebook outputs must include:

1. Malicious vs benign record counts
2. Registry distribution (`pypi` vs `npm`)
3. Missing field rates for critical columns
4. Top packages by occurrence (if duplicates retained pre-dedup analysis)
5. One short written conclusion: data is ready (or not ready) for Phase 2

## Implementation notes (best practices)

1. Load only processed normalized files
2. Keep notebook deterministic and rerunnable
3. Use simple plots/tables over complex visuals
4. Save key stats to markdown in `docs/` if helpful

## Suggested mini-checklist while coding

- [ ] Load normalized datasets
- [ ] Compute record counts and ratios
- [ ] Compute null/missing rates
- [ ] Add at least one table/plot
- [ ] Write checkpoint conclusion cell

## Manual validation commands

```powershell
python -c "import json; print('malicious', len(json.load(open('data/processed/malicious_normalized.json', encoding='utf-8')))); print('benign', len(json.load(open('data/processed/benign_normalized.json', encoding='utf-8'))))"
```

Expected:

- notebook runs without manual data patching
- conclusion cell clearly states readiness for Phase 2

## Edge cases to handle now

- one class is empty
- excessive missing values
- registry imbalance too extreme for meaningful early comparisons

## Done criteria for Step 8

- Notebook exists and runs end-to-end
- Key quality metrics are visible
- Phase 1 checkpoint marked complete in docs

## Mentor tip

Use this notebook as interview evidence: show that you validate data quality before modeling.
