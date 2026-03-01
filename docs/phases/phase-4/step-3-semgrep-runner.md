# Phase 4 — Step 3: Implement Semgrep Runner

## Why this step

Rules alone are not enough; you need a wrapper that runs Semgrep and converts output into structured findings for your pipeline.

## Your coding target

Create `detector/layer3_static/semgrep_runner.py` with a function like:

- `run_semgrep(target_path: str, rules_dir: str) -> dict`

## Contract

Input:

- path to package/source directory
- path to Semgrep rules directory

Output fields:

- `risk_score` (0-100)
- `finding_count` (int)
- `findings` (list[dict]) with `rule_id`, `severity`, `message`, `path`, `line`
- `is_suspicious` (bool)
- `evidence` (list[str])

Behavior:

- runs semgrep via subprocess with `--json`
- handles missing Semgrep binary gracefully
- non-zero exit behavior parsed safely

## Checklist

- [ ] Build subprocess command
- [ ] Parse JSON output robustly
- [ ] Normalize finding schema
- [ ] Map severities to risk points

## Done criteria

- Runner returns findings on known-rule matches
- Handles empty/no-finding scans cleanly
- Unit tests mock subprocess success/failure
