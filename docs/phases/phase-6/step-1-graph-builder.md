# Phase 6 — Step 1: Build Dependency Graph Builder

## Why this step

Graph structure is required before any transitive risk can be computed.

## Your coding target

Create `detector/layer5_graph/graph_builder.py` with function like:

- `build_dependency_graph(package_name: str, registry: str, max_depth: int = 3) -> nx.DiGraph`

## Contract

Behavior:

- recursively fetch dependencies up to depth limit
- create directed edges `package -> dependency`
- prevent infinite recursion/cycles
- annotate node metadata where available

## Checklist

- [ ] Add dependency fetch abstraction
- [ ] Add visited-set cycle protection
- [ ] Enforce depth limit
- [ ] Return deterministic graph

## Done criteria

- graph builds for at least one real package
- node/edge counts are reproducible
