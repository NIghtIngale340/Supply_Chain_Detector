# Phase 5 — Step 2: Implement Deobfuscator

## Why this step

Preprocessing improves LLM signal quality by exposing hidden behavior before inference.

## Your coding target

Create `detector/layer4_llm/deobfuscator.py` with function like:

- `deobfuscate_source(source_code: str) -> dict`

## Contract

Detect/decode where feasible:

- base64 literals
- hex literals
- simple string concatenation patterns

Output fields:

- `cleaned_source` (str)
- `transformations_applied` (list[str])
- `warnings` (list[str])

## Checklist

- [ ] Add safe decoding helpers
- [ ] Preserve original source when decoding fails
- [ ] Track transformations for evidence chain
- [ ] Avoid executing target code

## Done criteria

- deterministic output for identical input
- no code execution side effects
- tests cover decode success/failure paths
