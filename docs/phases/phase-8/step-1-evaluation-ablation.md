# Phase 8 — Step 1: Run Full Evaluation and Ablation

## Why this step

This is your quantitative proof that each layer contributes measurable value.

## Your coding target

Use `notebooks/05_evaluation_ablation.ipynb` (or equivalent script) to compute:

- precision
- recall
- F1
- per-layer ablation impact

## Contract

Evaluation output must include:

- dataset split details
- confusion matrix metrics
- ablation table removing one layer at a time

## Checklist

- [ ] Freeze evaluation dataset/version
- [ ] Compute baseline full-system metrics
- [ ] Run layer removal ablations
- [ ] Record results table for README

## Done criteria

- reproducible metrics are documented
- each layer contribution is clearly shown
