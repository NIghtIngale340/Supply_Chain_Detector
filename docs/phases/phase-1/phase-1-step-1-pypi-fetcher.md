# Phase 1 — Step 1: Implement PyPI Fetcher

## Why this step first

This is the smallest meaningful unit in the pipeline:

- one external API call
- one normalized output shape
- one place for retry/error handling

If this is clean, npm fetcher and extractor become much easier.

## Your coding target

Implement `fetch_pypi_metadata(package_name: str) -> FetchResult` in `fetcher/pypi_fetcher.py`.

## Contract (must satisfy)

Input:

- `package_name: str`

Output:

- `FetchResult.package_name`: exact input string
- `FetchResult.registry`: `"pypi"`
- `FetchResult.status_code`: HTTP status from PyPI API
- `FetchResult.metadata`: normalized dictionary with keys:
  - `name`
  - `version`
  - `summary`
  - `author`
  - `license`
  - `project_urls`
  - `requires_dist`
  - `source_url` (best available from PyPI payload)

## Implementation notes (best practices)

1. Validate input early
   - reject empty or whitespace-only package names
2. Build URL from env-aware base
   - from `.env`: `PYPI_BASE_URL`
   - default: `https://pypi.org/pypi`
   - final URL: `{base}/{package_name}/json`
3. Use timeout and clear error mapping
   - timeout 10s
   - network errors should raise a clear exception message
4. Normalize payload instead of returning raw JSON
   - keep output stable even if upstream shape changes
5. Keep function deterministic
   - no prints, no side effects, just return `FetchResult`

## Suggested mini-checklist while coding

- [ ] Add input validation
- [ ] Read base URL from env
- [ ] Send GET request with timeout
- [ ] Parse `info` section safely with `.get()`
- [ ] Build normalized metadata dictionary
- [ ] Return `FetchResult`

## Manual validation commands

Run this after implementation:

```powershell
python -c "from fetcher.pypi_fetcher import fetch_pypi_metadata; r=fetch_pypi_metadata('requests'); print(r.registry, r.status_code, r.metadata.get('name'), r.metadata.get('version'))"
```

Expected:

- registry should be `pypi`
- status should be `200`
- name should be `requests`
- version should be non-empty

## Edge cases to handle now

- package not found (404)
- package name has leading/trailing spaces
- temporary network failure

## Done criteria for Step 1

- Function works for at least one real package
- Function returns stable normalized shape
- Lint and tests still pass:

```powershell
python -m ruff check .
python -m pytest -q
```

## Mentor tip

Do not optimize prematurely with retries/backoff libraries yet. Keep this first implementation simple, readable, and testable. We can add resilient retry strategy once npm fetcher is in place and both share the same pattern.
