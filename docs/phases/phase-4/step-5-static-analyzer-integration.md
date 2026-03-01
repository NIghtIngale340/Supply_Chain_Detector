# Phase 4 — Step 5: Integrate Static Analyzer

## Why this step

This step merges AST, Semgrep, and obfuscation into one Layer 3 result used by downstream layers and model training.

## Your coding target

Create `detector/layer3_static/static_analyzer.py` with a function like:

- `analyze_static_risk(source_code: str, source_path: str) -> dict`

## Contract

Output fields:

- `final_score` (0-100)
- `decision` (`allow`/`review`/`high_risk`)
- `component_scores` (`ast`, `semgrep`, `obfuscation`)
- `evidence` (combined list)

Behavior:

- explicit component weights
- robust fallback when one component fails
- deterministic thresholds

## Checklist

- [ ] Wire AST analyzer output
- [ ] Wire Semgrep runner output
- [ ] Wire obfuscation detector output
- [ ] Apply weights + clamp score
- [ ] Return combined evidence and decision

## Done criteria

- End-to-end Layer 3 analyzer returns stable output
- Tests cover component failure fallback
- Lint/tests pass for Phase 4 scope
