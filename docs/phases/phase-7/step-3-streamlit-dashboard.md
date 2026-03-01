# Phase 7 — Step 3: Build Streamlit Dashboard

## Why this step

Dashboard makes model behavior inspectable and demo-ready.

## Your coding target

Create `ui/streamlit_app.py` with three views:

1. live threat feed
2. per-package risk report
3. dependency graph visualization

## Contract

Behavior:

- can submit package scan request
- polls API for results
- renders per-layer evidence clearly

## Checklist

- [ ] Add package input form
- [ ] Add job status polling UI
- [ ] Add risk report components
- [ ] Add graph visualization panel

## Done criteria

- UI can run locally and display real API outputs
- failures are handled with user-friendly messages
