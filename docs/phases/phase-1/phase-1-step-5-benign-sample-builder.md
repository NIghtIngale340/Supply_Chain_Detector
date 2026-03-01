# Phase 1 — Step 5: Build Benign Sample Dataset

## Why this step now

You need a benign comparison set for early EDA and later model training. Start small for fast iteration.

## Your coding target

Create `data/datasets/build_benign_sample.py`.

## Contract (must satisfy)

Output artifact:

- `data/processed/benign_sample.json` (or `.csv`) with fields:
  - `package_name`
  - `registry`
  - `source` (how it was collected)
  - `label` = benign

Behavior:

- Build initial sample size of 50-200 packages
- Deterministic schema and file format
- No duplicates by `(registry, package_name)`

## Implementation notes (best practices)

1. Start with manageable scale
   - avoid 5000-package run initially
2. Keep one registry list at a time if needed
3. Add simple retry or skip logic for failed pulls
4. Record provenance field (`source`)

## Suggested mini-checklist while coding

- [ ] Create script file and CLI entrypoint
- [ ] Collect candidate package names
- [ ] Normalize records into schema
- [ ] Remove duplicates
- [ ] Save output in `data/processed`

## Manual validation commands

```powershell
python data/datasets/build_benign_sample.py
python -c "import json; d=json.load(open('data/processed/benign_sample.json', encoding='utf-8')); print(len(d))"
```

Expected:

- output file exists
- count is in target range
- labels are all benign

## Edge cases to handle now

- rate limits or timeouts
- malformed package names
- duplicate package records

## Done criteria for Step 5

- Benign sample file generated with stable schema
- Duplicates removed
- Lint/tests pass

## Mentor tip

Optimize for data quality and schema stability first, dataset size second.
