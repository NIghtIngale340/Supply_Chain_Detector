# Phase 4 — Step 1: Build AST Analyzer

## Why this step

AST-based behavioral features give low-cost, explainable security signals and are resilient against simple formatting obfuscation.

## Your coding target

Create `detector/layer3_static/ast_analyzer.py` with a function like:

- `analyze_ast(source_code: str) -> dict`

## Contract

Input:

- `source_code: str`

Output fields:

- `risk_score` (0-100)
- `feature_vector` (dict of counts)
- `is_suspicious` (bool)
- `evidence` (list[str])

Required feature counts (from blueprint):

- subprocess calls
- socket usage
- eval/exec usage
- `os.environ` access
- file open/write usage
- base64 decode usage

## Checklist

- [ ] Parse source safely with `ast`
- [ ] Walk nodes and count required patterns
- [ ] Convert feature counts to initial risk score
- [ ] Return stable schema with evidence

## Done criteria

- Works on benign and suspicious snippets
- Handles syntax errors without crashing
- Unit tests cover at least 3 risky patterns
