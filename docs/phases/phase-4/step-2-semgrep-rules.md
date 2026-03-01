# Phase 4 — Step 2: Write Semgrep Rules

## Why this step

Semgrep rules give precise pattern-based detections you can explain and tune quickly.

## Your coding target

Create rule files in `data/semgrep_rules/`:

1. `network_on_import.yaml`
2. `credential_harvesting.yaml`
3. `reverse_shell.yaml`
4. `setup_py_exec.yaml`

## Contract

Each rule must include:

- rule id
- message
- severity
- language(s)
- pattern(s)

Behavior:

- rules are valid Semgrep YAML
- rules target Python package threat patterns from blueprint

## Checklist

- [ ] Create all four rule files
- [ ] Validate YAML structure
- [ ] Test each rule on one matching snippet
- [ ] Keep rule messages evidence-friendly

## Done criteria

- All four rules parse and execute
- At least one positive match per rule on sample code
- False-positive examples documented for tuning
