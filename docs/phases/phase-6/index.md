# Phase 6 — Layer 5 Dependency Graph Risk Propagation

## Objective

Implement blueprint Layer 5 by building dependency graphs, propagating risk transitively, and calculating blast radius impact.

## Blueprint Alignment

- recursive dependency tree build (bounded depth)
- directed graph modeling with NetworkX
- transitive risk propagation from malicious dependencies
- blast radius calculation for downstream impact

## In Scope

- `detector/layer5_graph/graph_builder.py`
- `detector/layer5_graph/graph_analyzer.py`
- `detector/layer5_graph/blast_radius.py`

## Active Step Sequence

1. `docs/phases/phase-6/step-1-graph-builder.md`
2. `docs/phases/phase-6/step-2-risk-propagation.md`
3. `docs/phases/phase-6/step-3-blast-radius.md`
4. `docs/phases/phase-6/step-4-graph-visualization.md`
