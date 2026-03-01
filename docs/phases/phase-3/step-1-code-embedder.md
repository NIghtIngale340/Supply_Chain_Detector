# Phase 3 — Step 1: Implement Code Embedder

## Why this step first

All Layer 2 behavior depends on high-quality, deterministic embeddings. This is the foundation for FAISS search and clustering.

## Your coding target

Create `detector/layer2_embeddings/code_embedder.py`.

Implement a class/function interface such as:

- `encode(source_code: str) -> np.ndarray`

## Contract (must satisfy)

Input:

- `source_code: str`

Output:

- `np.ndarray` (1D or 2D depending on API, but documented and consistent)

Behavior:

- deterministic embedding shape
- empty/invalid input handled safely
- model loading managed once (avoid repeated expensive reloads)

Blueprint alignment:

- Use `sentence-transformers` with `microsoft/codebert-base` or lightweight fallback (`all-MiniLM-L6-v2`)

## Implementation notes (best practices)

1. Start with lightweight model for local iteration
2. Separate model initialization from encode logic
3. Normalize whitespace/code string before embedding
4. Expose embedding dimension in helper property/function

## Suggested mini-checklist while coding

- [ ] Add dependency and import checks
- [ ] Initialize model once
- [ ] Implement `encode` for single text input
- [ ] Return numpy array with stable shape
- [ ] Add guard for empty source input

## Manual validation commands

```powershell
python -c "from detector.layer2_embeddings.code_embedder import encode; import numpy as np; v=encode('import os\nprint(1)'); print(type(v), getattr(v, 'shape', None), np.isfinite(v).all())"
```

Expected:

- output is numeric vector
- shape is consistent
- values are finite

## Edge cases to handle now

- empty source string
- very large source snippets
- model download/load failure

## Done criteria for Step 1

- Embedder produces stable vectors for repeated identical input
- Unit tests cover shape and empty input behavior
- Lint/tests pass

## Mentor tip

Keep this module simple and deterministic now; performance optimizations can be added after correctness.
