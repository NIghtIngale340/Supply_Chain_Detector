# Phase 1 — Step 7: Add Core Tests for Pipeline Reliability

## Why this step now

Before notebook exploration, lock down behavior so future refactors don’t silently break ingestion.

## Your coding target

Add tests under `tests/` for:

- `fetcher/pypi_fetcher.py`
- `fetcher/npm_fetcher.py`
- `fetcher/source_extractor.py`
- one dataset normalization behavior

## Contract (must satisfy)

Minimum test coverage in Phase 1:

1. Success path for PyPI fetch
2. Not-found path for PyPI fetch
3. Success path for npm fetch
4. Not-found path for npm fetch
5. Unsupported archive type in extractor
6. Safe extraction check behavior

## Implementation notes (best practices)

1. Use mocking for HTTP calls
   - tests should not depend on live internet
2. Keep fixtures small and explicit
3. Name tests by behavior, not implementation
4. One assertion theme per test

## Suggested mini-checklist while coding

- [ ] Add `tests/test_pypi_fetcher.py`
- [ ] Add `tests/test_npm_fetcher.py`
- [ ] Add `tests/test_source_extractor.py`
- [ ] Mock HTTP responses deterministically
- [ ] Cover expected exceptions

## Manual validation commands

```powershell
python -m pytest -q
```

Expected:

- all tests pass
- no external network required for test suite

## Edge cases to handle now

- timeout exceptions
- malformed JSON responses
- archive with dangerous member path

## Done criteria for Step 7

- Required tests exist and pass
- Existing smoke test still passes
- Lint/tests pass together

```powershell
python -m ruff check .
python -m pytest -q
```

## Mentor tip

In security tooling, reliable negative-path testing is as important as happy-path testing.
