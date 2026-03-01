# Phase 1 — Step 2: Implement npm Fetcher

## Why this step now

You already have the PyPI fetch pattern. This step builds symmetry so both registries produce a stable, shared result shape.

## Your coding target

Implement `fetch_npm_metadata(package_name: str) -> FetchResult` in `fetcher/npm_fetcher.py`.

## Contract (must satisfy)

Input:

- `package_name: str`

Output:

- `FetchResult.package_name`: exact input string (trimmed)
- `FetchResult.registry`: `"npm"`
- `FetchResult.status_code`: HTTP status from npm Registry API
- `FetchResult.metadata`: normalized dictionary with keys:
  - `name`
  - `version`
  - `description`
  - `author`
  - `license`
  - `repository`
  - `homepage`
  - `dependencies`
  - `dist_tarball`

## Implementation notes (best practices)

1. Validate input early
   - reject empty package names
2. Build URL from env-aware base
   - from `.env`: `NPM_BASE_URL`
   - default: `https://registry.npmjs.org`
   - final URL: `{base}/{package_name}`
3. Use timeout and clear error mapping
   - timeout 10s
4. Handle npm payload differences
   - prefer `dist-tags.latest` version
   - fallback safely if latest is missing
5. Keep normalized shape deterministic

## Suggested mini-checklist while coding

- [ ] Add input validation + trimming
- [ ] Read `NPM_BASE_URL`
- [ ] Send GET request with timeout
- [ ] Resolve latest version payload safely
- [ ] Normalize fields into stable metadata dict
- [ ] Return `FetchResult`

## Manual validation commands

Run this after implementation:

```powershell
python -c "from fetcher.npm_fetcher import fetch_npm_metadata; r=fetch_npm_metadata('lodash'); print(r.registry, r.status_code, r.metadata.get('name'), bool(r.metadata.get('version')) )"
```

Expected:

- registry should be `npm`
- status should be `200`
- name should be `lodash`
- version should be non-empty

## Edge cases to handle now

- package not found (404)
- scoped packages like `@types/node`
- missing `dist-tags` or malformed version entries
- temporary network failure

## Done criteria for Step 2

- Works for normal package and at least one scoped package
- Returns stable normalized shape
- Lint/tests still pass

```powershell
python -m ruff check .
python -m pytest -q
```

## Mentor tip

Match your PyPI and npm result schema philosophy now. Consistency here makes downstream aggregation significantly simpler.
