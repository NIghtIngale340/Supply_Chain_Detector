# Phase 2 — Layer 1 Metadata Anomaly Detection

## Objective

Implement blueprint Layer 1 by scoring package risk from metadata anomalies before any code-level ML/LLM analysis.

## Blueprint Alignment

This phase maps directly to:

- Typosquat detection against top package lists (edit distance)
- Author trust signals (account age, maintainer history)
- Version anomalies (jumps, release velocity, dormancy)
- Weighted metadata risk score from 0-100

## In Scope

- `detector/layer1_metadata/typosquat_detector.py`
- `detector/layer1_metadata/author_analyzer.py`
- `detector/layer1_metadata/version_analyzer.py`
- `detector/layer1_metadata/metadata_analyzer.py`
- `data/top_packages/pypi_top_1000.json`
- `data/top_packages/npm_top_1000.json`

## Out of Scope

- Embedding similarity (Layer 2)
- Static code behavior analysis (Layer 3)
- LLM audit (Layer 4)
- Dependency graph propagation (Layer 5)

## Entry Criteria

- Phase 1 complete and validated
- Fetchers provide normalized metadata required by Layer 1
- Basic unit test setup already working

## Exit Criteria

- Each analyzer returns deterministic outputs
- Combined metadata score returns 0-100 with evidence
- Threshold-based flagging works and is documented
- Phase 2 unit tests pass

## Validation Commands

```powershell
python -m ruff check .
python -m pytest -q
```

## Active Step Sequence

1. `phase-2-step-1-typosquat-detector.md`
2. `phase-2-step-2-author-analyzer.md`
3. `phase-2-step-3-version-analyzer.md`
4. `phase-2-step-4-metadata-aggregator.md`

## Deliverables

- Layer 1 modules implemented
- Unit tests for positive/negative edge cases
- One notebook or markdown note documenting weights and rationale
