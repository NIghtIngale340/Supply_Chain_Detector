# Phase 1 — Step 4: Bootstrap Malicious Dataset Seed

## Why this step now

You need a trustworthy malicious baseline before feature engineering. This creates ground truth inputs for later training and validation.

## Your coding target

Implement `download_backstabbers_dataset()` in `data/datasets/download_backstabbers.py`.

## Contract (must satisfy)

Output artifact:

- `data/processed/backstabbers_seed.json` (or `.csv`) with at least:
  - `package_name`
  - `registry`
  - `source_reference`
  - `label` (malicious)
  - `notes` (optional)

Behavior:

- Deterministic output format
- Idempotent reruns (re-running does not corrupt output)

## Implementation notes (best practices)

1. Start small
   - first produce a tiny seed list if full pull is not yet wired
2. Keep schema explicit
   - define required fields and enforce them
3. Separate raw vs processed
   - raw download snapshot under `data/raw`
   - normalized output under `data/processed`

## Suggested mini-checklist while coding

- [ ] Define normalized schema
- [ ] Download/read source dataset info
- [ ] Map records to normalized schema
- [ ] Write deterministic output file
- [ ] Handle reruns safely

## Manual validation commands

```powershell
python data/datasets/download_backstabbers.py
python -c "import json; d=json.load(open('data/processed/backstabbers_seed.json', encoding='utf-8')); print(len(d), d[0].keys() if d else 'empty')"
```

Expected:

- output file exists
- count is non-zero (or documented placeholder count)
- keys match your schema

## Edge cases to handle now

- upstream unavailable
- partial/missing fields
- duplicate package entries

## Done criteria for Step 4

- Seed malicious dataset exists with stable schema
- Script is rerunnable without manual cleanup
- Lint/tests pass

## Mentor tip

A small, clean seed dataset beats a large, noisy one at this stage.
