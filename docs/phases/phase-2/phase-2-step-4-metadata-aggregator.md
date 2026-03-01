# Phase 2 — Step 4: Combine Metadata Signals into Final Layer 1 Score

## Why this step now

This completes blueprint Phase 2 by producing one actionable metadata risk score from all Layer 1 components.

## Your coding target

Create `detector/layer1_metadata/metadata_analyzer.py`.

Implement a function such as:

- `analyze_metadata_risk(package_name: str, registry: str, metadata: dict) -> dict`

## Contract (must satisfy)

Input:

- package identity and normalized metadata

Output dictionary fields:

- `final_score` (0-100)
- `decision` (`allow`, `review`, `high_risk`)
- `layer_scores`:
  - `typosquat`
  - `author`
  - `version`
- `thresholds` used
- `evidence` (combined list)

Required behavior:

- combine three analyzer outputs using explicit weights
- clamp final score to 0-100
- deterministic decision thresholds
- log weight rationale in notebook or markdown note

Blueprint alignment:

- weighted metadata risk score (0-100)
- rationale logging for interview discussion

## Implementation notes (best practices)

1. Start with explicit static weights
   - example baseline: typosquat 0.40, author 0.30, version 0.30
2. Keep thresholds configurable
   - env or constants module
3. Preserve per-layer evidence in final output
4. Add a small calibration note in docs/notebook

## Suggested mini-checklist while coding

- [ ] Wire typosquat analyzer output
- [ ] Wire author analyzer output
- [ ] Wire version analyzer output
- [ ] Apply weights and clamp score
- [ ] Map score to decision band
- [ ] Return combined evidence and score breakdown

## Manual validation commands

```powershell
python -c "from detector.layer1_metadata.metadata_analyzer import analyze_metadata_risk as a; print(a('colourama','pypi',{'name':'colourama'}))"
```

Expected:

- output includes final score, decision, and layer score breakdown
- suspicious packages trend to `review`/`high_risk`

## Edge cases to handle now

- one analyzer fails or returns partial data
- missing metadata fields
- score drift due to inconsistent scaling

## Done criteria for Step 4

- Final Layer 1 score endpoint/function is deterministic
- Score rationale is documented and reviewable
- Phase 2 tests pass end-to-end

```powershell
python -m ruff check .
python -m pytest -q
```

## Mentor tip

Interview strength comes from explainability: be able to justify every weight and threshold with evidence and tradeoffs.
