# Phase 6 — Step 2: Implement Graph Risk Propagation

## Why this step

This is the core value of Layer 5: estimating indirect compromise risk from transitive dependencies.

## Your coding target

Create `detector/layer5_graph/graph_analyzer.py` with function like:

- `propagate_risk(graph: nx.DiGraph, base_scores: dict) -> dict`

## Contract

Input:

- dependency graph
- known package risk scores (from earlier layers)

Output:

- propagated score per node
- explanation metadata for top contributors

Behavior:

- closer malicious dependencies contribute higher impact
- decay by graph distance/depth
- scores clamped to 0-100

## Checklist

- [ ] Define decay model
- [ ] Compute shortest-path contributions
- [ ] Aggregate and clamp scores
- [ ] Return explanation payload

## Done criteria

- transitive risk increases for packages depending on risky nodes
- tests validate distance-based decay behavior
