# Phase 2 — Step 2: Implement Author Analyzer

## Why this step now

Compromised or newly created maintainer identities are core indicators in real attacks. This adds trust-context beyond name similarity.

## Your coding target

Create `detector/layer1_metadata/author_analyzer.py`.

Implement a function such as:

- `analyze_author_signals(metadata: dict, registry: str) -> dict`

## Contract (must satisfy)

Input:

- `metadata: dict` from fetcher layer
- `registry: str` (`pypi`/`npm`)

Output dictionary fields:

- `risk_score` (0-100)
- `account_age_days` (int or null)
- `published_package_count` (int or null)
- `maintainer_reputation` (low/medium/high or null)
- `is_suspicious` (bool)
- `evidence` (list[str])

Blueprint-derived signals:

- account creation date
- total packages published
- minimal maintainer history as higher risk

## Implementation notes (best practices)

1. Start with available metadata fields first
   - add API enrichment as optional enhancement
2. Handle missing/partial data explicitly
3. Keep risk scoring transparent
   - document each rule contribution in evidence
4. Use UTC date math for deterministic age calculation

## Suggested mini-checklist while coding

- [ ] Parse author/maintainer fields safely
- [ ] Compute account age if creation date exists
- [ ] Compute simple reputation heuristics
- [ ] Build evidence strings with exact rationale
- [ ] Return score and flags with stable schema

## Manual validation commands

```powershell
python -c "from detector.layer1_metadata.author_analyzer import analyze_author_signals as a; print(a({'author':'unknown','created_at':'2026-02-01T00:00:00Z'}, 'pypi'))"
```

Expected:

- recent/unknown maintainer should produce elevated risk
- missing fields should not crash analyzer

## Edge cases to handle now

- no author fields
- invalid timestamp format
- missing registry-specific fields

## Done criteria for Step 2

- Analyzer returns deterministic output schema
- Suspicion logic is explainable via evidence
- Unit tests cover missing data and recent-account cases

## Mentor tip

Security signals are noisy. Favor conservative, explainable heuristics now and calibrate with real data later.
