# Phase 7 — Step 4: Add GitHub Action CI Scanner

## Why this step

This turns your project into a practical CI guardrail and maps directly to recruiter-facing impact.

## Your coding target

Implement `github_action/` components:

- `action.yml`
- `entrypoint.sh`
- `scan_requirements.py`

## Contract

Behavior:

- reads dependency manifest (`requirements.txt` / `package.json`)
- calls analysis API per dependency
- fails workflow if score exceeds threshold

## Checklist

- [ ] Parse dependency files reliably
- [ ] Add API call + retry handling
- [ ] Implement configurable fail threshold
- [ ] Add usage example in docs

## Done criteria

- action runs in sample repo workflow
- workflow fails on intentionally risky package fixture
