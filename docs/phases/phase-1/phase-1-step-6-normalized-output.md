# Phase 1 — Step 6: Create Normalized Output Pipeline

## Why this step now

You now have raw fetch and dataset scripts. This step standardizes outputs so downstream phases consume one canonical shape.

## Your coding target

Create a normalization utility module (for example `data/datasets/normalize_records.py`) and apply it in your dataset scripts.

## Contract (must satisfy)

Output files:

- `data/processed/malicious_normalized.json`
- `data/processed/benign_normalized.json`

Required fields per record:

- `package_name`
- `registry`
- `label`
- `version` (nullable)
- `source_url` (nullable)
- `collected_at` (ISO-8601 UTC string)

Behavior:

- deterministic key naming
- deterministic sorting (recommended)
- reject invalid records or quarantine them with reason

## Implementation notes (best practices)

1. Define schema once in code
2. Keep registry values standardized (`pypi`, `npm`)
3. Add lightweight validation function
4. Keep timestamp format consistent

## Suggested mini-checklist while coding

- [ ] Define canonical record schema
- [ ] Map malicious dataset to canonical schema
- [ ] Map benign dataset to canonical schema
- [ ] Validate required fields
- [ ] Save both normalized outputs

## Manual validation commands

```powershell
python -c "import json; m=json.load(open('data/processed/malicious_normalized.json', encoding='utf-8')); b=json.load(open('data/processed/benign_normalized.json', encoding='utf-8')); print(len(m), len(b))"
```

Expected:

- both files exist
- both have non-zero counts (or documented placeholder)
- required keys present in every record

## Edge cases to handle now

- missing version/source fields
- invalid registry values
- duplicate records with conflicting metadata

## Done criteria for Step 6

- Canonical normalized outputs exist
- Record validation catches obvious schema issues
- Lint/tests pass

## Mentor tip

Schema consistency is one of the highest-leverage engineering decisions in this project.
