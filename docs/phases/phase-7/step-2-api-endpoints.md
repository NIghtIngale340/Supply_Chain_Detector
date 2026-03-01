# Phase 7 — Step 2: Implement API Endpoints and Queue Flow

## Why this step

API endpoints are the contract for users, UI, and CI integrations.

## Your coding target

Implement:

- `POST /analyze`
- `GET /results/{id}`
- `GET /health`

## Contract

`POST /analyze`:

- validates input `{name, registry}`
- enqueues analysis task
- returns `job_id` and queued status quickly

`GET /results/{id}`:

- returns final report when ready
- returns pending status while processing

## Checklist

- [ ] Add request/response schemas
- [ ] Wire Celery enqueue path
- [ ] Add status polling behavior
- [ ] Add endpoint tests

## Done criteria

- end-to-end queue roundtrip works for one test package
- API tests pass with mocked worker paths
