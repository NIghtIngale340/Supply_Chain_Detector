# Phase 5 — Layer 4 LLM-Assisted Audit

## Objective

Implement blueprint Layer 4 to perform structured LLM reasoning on suspicious package code after lower-cost filters trigger review.

## Blueprint Alignment

- security-focused prompt templates
- deobfuscation before LLM call
- structured JSON response parsing
- threshold-based cost control (trigger only after high prior risk)
- evaluation on malicious/benign package samples

## In Scope

- `detector/layer4_llm/prompt_templates.py`
- `detector/layer4_llm/deobfuscator.py`
- `detector/layer4_llm/response_parser.py`
- `detector/layer4_llm/llm_auditor.py`

## Out of Scope

- dependency graph propagation (Phase 6)
- API/worker deployment integration (Phase 7)

## Entry Criteria

- Layer 1 + Layer 3 risk signals available
- API key or local Ollama endpoint configured

## Exit Criteria

- LLM audit produces structured findings
- parser reliably handles markdown-wrapped JSON
- threshold gating controls LLM cost
- benchmark notes recorded for quality and hallucination behavior

## Active Step Sequence

1. `docs/phases/phase-5/step-1-prompt-templates.md`
2. `docs/phases/phase-5/step-2-deobfuscator.md`
3. `docs/phases/phase-5/step-3-response-parser.md`
4. `docs/phases/phase-5/step-4-cost-control-gate.md`
5. `docs/phases/phase-5/step-5-llm-evaluation.md`
