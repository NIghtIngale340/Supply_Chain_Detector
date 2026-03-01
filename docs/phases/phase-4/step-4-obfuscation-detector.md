# Phase 4 — Step 4: Implement Obfuscation Detector

## Why this step

Attackers frequently use encoded payloads and dynamic execution to evade basic static checks.

## Your coding target

Create `detector/layer3_static/obfuscation_detector.py` with a function like:

- `analyze_obfuscation(source_code: str) -> dict`

## Contract

Detect and score signals from blueprint:

- long base64-like strings (e.g., >200 chars)
- hex-encoded string patterns
- `eval(compile(...))` chains
- lambda-heavy obfuscation patterns
- write-then-import behavior hints

Output fields:

- `risk_score` (0-100)
- `signals` (list[str])
- `is_suspicious` (bool)
- `evidence` (list[str])

## Checklist

- [ ] Add regex/pattern detectors for each signal
- [ ] Deduplicate repeated matches
- [ ] Map signal strength to risk score
- [ ] Return stable structured output

## Done criteria

- Flags synthetic obfuscation samples correctly
- Produces explainable evidence text
- Unit tests include positive and negative samples
