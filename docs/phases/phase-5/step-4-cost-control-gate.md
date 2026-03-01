# Phase 5 — Step 4: Add Cost-Control Trigger Gate

## Why this step

Blueprint explicitly requires avoiding LLM on all packages to control cost and latency.

## Your coding target

Implement gating in `detector/layer4_llm/llm_auditor.py`:

- call LLM only when combined prior score >= threshold (default 40/100)

## Contract

Input:

- prior-layer combined score
- candidate package source

Behavior:

- if below threshold: skip LLM and return reason
- if above threshold: run full LLM audit flow

Output fields:

- `llm_triggered` (bool)
- `trigger_threshold`
- `reason`
- `audit_result` (if triggered)

## Checklist

- [ ] Add threshold constant/env config
- [ ] Implement branch logic and reason text
- [ ] Log trigger decision for observability
- [ ] Add tests for above/below threshold

## Done criteria

- below-threshold path is deterministic and cheap
- above-threshold path performs full audit
