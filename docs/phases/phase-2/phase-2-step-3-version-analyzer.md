# Phase 2 — Step 3: Implement Version Analyzer

## Why this step now

Version and release-pattern anomalies often reveal hijacks or abrupt malicious insertions, especially on dormant packages.

## Your coding target

Create `detector/layer1_metadata/version_analyzer.py`.

Implement a function such as:

- `analyze_version_signals(metadata: dict) -> dict`

## Contract (must satisfy)

Input:

- `metadata: dict` containing version/release history fields

Output dictionary fields:

- `risk_score` (0-100)
- `version_jump_magnitude` (float/int or null)
- `release_velocity` (float/int or null)
- `days_since_last_release` (int or null)
- `is_suspicious` (bool)
- `evidence` (list[str])

Blueprint-derived signals:

- version jump magnitude
- release velocity spikes
- dormant package suddenly active

## Implementation notes (best practices)

1. Parse version history defensively
2. Avoid strict assumptions about semantic versioning
3. Use simple robust heuristics first
4. Keep every rule explainable in evidence strings

## Suggested mini-checklist while coding

- [ ] Parse release timeline from metadata
- [ ] Estimate jump magnitude between last two versions
- [ ] Estimate release velocity over recent interval
- [ ] Detect dormancy followed by sudden release
- [ ] Return stable schema with evidence

## Manual validation commands

```powershell
python -c "from detector.layer1_metadata.version_analyzer import analyze_version_signals as a; sample={'version':'3.0.0','release_history':[{'version':'1.2.0','date':'2022-01-01T00:00:00Z'},{'version':'3.0.0','date':'2026-02-01T00:00:00Z'}]}; print(a(sample))"
```

Expected:

- large jumps with long dormancy should increase risk

## Edge cases to handle now

- single-version packages
- non-semver version strings
- missing release dates

## Done criteria for Step 3

- Analyzer handles sparse and noisy version metadata safely
- Suspicious patterns produce clear evidence
- Unit tests cover normal and anomaly cases

## Mentor tip

Heuristics that fail gracefully on messy real-world metadata are better than brittle precision.
