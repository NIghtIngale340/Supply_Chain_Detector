# Phase 5 — Step 1: Build Prompt Templates

## Why this step

Prompt quality determines consistency, explainability, and structured output reliability.

## Your coding target

Create `detector/layer4_llm/prompt_templates.py` with:

- system prompt (security analyst role)
- user prompt template (code + metadata + explicit output schema request)

## Contract

System prompt must enforce:

- security reasoning over package behavior
- explicit evidence extraction
- no unsafe speculation beyond observed code

User prompt must request:

- what code appears to do
- unexpected/malicious behavior assessment
- risk category
- supporting evidence
- JSON output format

## Checklist

- [ ] Define system prompt constant
- [ ] Define parameterized user prompt
- [ ] Include required JSON schema in prompt text
- [ ] Keep prompt deterministic and concise

## Done criteria

- prompts are reusable by auditor module
- prompt output requirements match parser schema
