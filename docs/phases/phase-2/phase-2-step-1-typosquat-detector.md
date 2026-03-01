# Phase 2 — Step 1: Implement Typosquat Detector

## Why this step first

Typosquatting is one of the most common and highest-impact supply chain attack vectors. It also gives immediate measurable risk signal from metadata alone.

## Your coding target

Create `detector/layer1_metadata/typosquat_detector.py`.

Implement a function such as:

- `analyze_typosquat(package_name: str, registry: str) -> dict`

## Contract (must satisfy)

Input:

- `package_name: str`
- `registry: str` (`pypi` or `npm`)

Output dictionary fields:

- `risk_score` (0-100)
- `nearest_package` (string or null)
- `edit_distance` (int or null)
- `is_suspicious` (bool)
- `evidence` (list[str])

Data dependency:

- `data/top_packages/pypi_top_1000.json`
- `data/top_packages/npm_top_1000.json`

Detection rule baseline (from blueprint):

- suspicious if minimum edit distance <= 2

## Implementation notes (best practices)

1. Normalize package names
   - lowercase + trim
2. Use deterministic distance implementation
   - use `python-Levenshtein` or a fallback pure-Python helper
3. Return structured evidence
   - include nearest package and distance in evidence text
4. Keep scoring simple and explainable
   - example: distance 1 => higher risk than distance 2

## Suggested mini-checklist while coding

- [ ] Load top package list by registry
- [ ] Validate package name and registry
- [ ] Compute min edit distance to top list
- [ ] Map distance to risk score
- [ ] Build evidence list and suspicion flag

## Manual validation commands

```powershell
python -c "from detector.layer1_metadata.typosquat_detector import analyze_typosquat as a; print(a('colourama','pypi'))"
python -c "from detector.layer1_metadata.typosquat_detector import analyze_typosquat as a; print(a('requests','pypi'))"
```

Expected:

- `colourama` should produce suspicious signal near `colorama`
- `requests` should not be marked suspicious

## Edge cases to handle now

- empty package name
- unknown registry
- missing top package file

## Done criteria for Step 1

- Deterministic typosquat analysis works for both registries
- Evidence is human-readable
- Unit tests cover suspicious and benign names

## Mentor tip

Avoid overfitting with complex distance logic now; simple, interpretable rules are better for interviews and debugging.
