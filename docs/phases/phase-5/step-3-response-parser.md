# Phase 5 — Step 3: Implement LLM Response Parser

## Why this step

Raw LLM output is noisy; parser strictness ensures downstream reliability.

## Your coding target

Create `detector/layer4_llm/response_parser.py` with function like:

- `parse_llm_audit_response(raw_text: str) -> dict`

## Contract

Parser must handle:

- pure JSON output
- markdown code-block wrapped JSON
- minor formatting noise

Normalized output fields:

- `risk_score` (0-100)
- `risk_category`
- `summary`
- `evidence` (list[str])
- `confidence` (optional)

## Checklist

- [ ] Strip markdown fences
- [ ] Parse JSON robustly
- [ ] Validate required fields
- [ ] Return fallback structure on parse failure

## Done criteria

- parser handles expected response variants
- malformed output does not crash pipeline
- tests include fence/no-fence/bad-json cases
