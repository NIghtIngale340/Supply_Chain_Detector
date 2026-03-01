# Phase 3 — Step 2: Build FAISS Index Pipeline

## Why this step now

Once embeddings exist, FAISS gives fast nearest-neighbor retrieval, which is the core runtime primitive for similarity risk scoring.

## Your coding target

Create `ml/build_faiss_index.py`.

Implement an offline pipeline that:

1. Loads benign dataset samples
2. Embeds source text
3. Builds a FAISS index
4. Persists index and ID mapping metadata

## Contract (must satisfy)

Inputs:

- normalized benign dataset file(s)

Outputs:

- persisted FAISS index file (e.g., under `data/processed/` or `storage/`)
- id-to-package mapping file (JSON/CSV)

Behavior:

- deterministic indexing order
- skip or quarantine invalid records without crashing full build
- logs progress for long runs

Blueprint alignment:

- FAISS nearest-neighbor search over large benign set

## Implementation notes (best practices)

1. Start with `IndexFlatL2` for simplicity
2. Keep build script idempotent (safe rerun)
3. Save metadata required for reverse lookup
4. Keep memory usage visible (batch embedding when needed)

## Suggested mini-checklist while coding

- [ ] Load benign normalized records
- [ ] Encode records in batches
- [ ] Build `IndexFlatL2`
- [ ] Persist index to disk
- [ ] Persist ID mapping

## Manual validation commands

```powershell
python ml/build_faiss_index.py
python -c "import os; print('index_exists', os.path.exists('data/processed/faiss.index'))"
```

Expected:

- index file created
- mapping file created
- script prints build summary

## Edge cases to handle now

- missing source code field
- embeddings with inconsistent dimensions
- empty benign dataset

## Done criteria for Step 2

- Index builds successfully from current benign data
- Can query at least one vector and get neighbors
- Unit tests validate index build/load path

## Mentor tip

Index correctness matters more than index type complexity at this stage.
