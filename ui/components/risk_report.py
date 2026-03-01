from __future__ import annotations

import streamlit as st


def render_layer_evidence(result: dict) -> None:
    layers = result.get("layers", {})
    st.subheader("Per-Layer Evidence")
    for layer_name in [
        "layer1_metadata",
        "layer2_embeddings",
        "layer3_static",
        "layer4_llm",
        "layer5_graph",
    ]:
        layer_payload = layers.get(layer_name, {})
        with st.expander(layer_name, expanded=False):
            st.json(layer_payload)
