# Phase 6 — Step 3: Implement Blast Radius Analysis

## Why this step

Blast radius is a strong operational metric: it quantifies downstream impact if a package is compromised.

## Your coding target

Create `detector/layer5_graph/blast_radius.py` with function like:

- `calculate_blast_radius(graph: nx.DiGraph, package_name: str) -> dict`

## Contract

Output fields:

- `affected_count`
- `affected_packages`
- `max_depth_affected`
- optional severity band

Behavior:

- use reverse graph traversal
- deterministic ordering of results

## Checklist

- [ ] Traverse reverse dependencies
- [ ] Count unique impacted nodes
- [ ] Compute depth statistics
- [ ] Return stable report format

## Done criteria

- known central packages show larger blast radius than leaf packages
- tests validate edge and empty graph cases
