from __future__ import annotations

import networkx as nx
import streamlit as st


def render_graph_from_blast_radius(result: dict) -> None:
    layer5 = result.get("layers", {}).get("layer5_graph", {})
    blast = layer5.get("blast_radius", {})
    root = result.get("package", "target")
    affected = blast.get("affected_packages", [])

    graph = nx.DiGraph()
    graph.add_node(root)
    for package in affected:
        graph.add_edge(package, root)

    st.subheader("Dependency Graph Visualization")
    st.caption("Simplified view from blast-radius output")

    if not graph.nodes:
        st.graphviz_chart("digraph G { }")
        return

    lines = ["digraph G {"]
    for node in sorted(graph.nodes):
        lines.append(f'  "{node}";')
    for source, target in sorted(graph.edges):
        lines.append(f'  "{source}" -> "{target}";')
    lines.append("}")
    st.graphviz_chart("\n".join(lines))
