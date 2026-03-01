# Phase 4 — Layer 3 Static Behavioral Analysis

## Objective

Implement blueprint Layer 3 using AST features, Semgrep pattern rules, and obfuscation signals to produce structured static-analysis risk evidence.

## Blueprint Alignment

- `ast_analyzer.py` for static behavior feature extraction
- four Semgrep YAML rules under `data/semgrep_rules/`
- `semgrep_runner.py` for CLI execution and JSON parsing
- `obfuscation_detector.py` for encoded/eval-style patterns
- static feature output ready for later model training

## In Scope

- `detector/layer3_static/ast_analyzer.py`
- `detector/layer3_static/semgrep_runner.py`
- `detector/layer3_static/obfuscation_detector.py`
- `detector/layer3_static/static_analyzer.py`
- `data/semgrep_rules/*.yaml`

## Out of Scope

- LLM auditing (Phase 5)
- Dependency graph propagation (Phase 6)
- API/UI orchestration (Phase 7)

## Entry Criteria

- Phase 3 completed and validated
- Sample extracted package source available from Phase 1

## Exit Criteria

- AST analyzer returns deterministic feature vectors
- Semgrep rules run and parse into structured findings
- Obfuscation detector flags suspicious patterns with evidence
- Combined static analyzer outputs a stable risk object

## Active Step Sequence

1. `docs/phases/phase-4/step-1-ast-analyzer.md`
2. `docs/phases/phase-4/step-2-semgrep-rules.md`
3. `docs/phases/phase-4/step-3-semgrep-runner.md`
4. `docs/phases/phase-4/step-4-obfuscation-detector.md`
5. `docs/phases/phase-4/step-5-static-analyzer-integration.md`

## Validation Commands

```powershell
python -m ruff check .
python -m pytest -q
```
