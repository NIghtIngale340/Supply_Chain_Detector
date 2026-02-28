import os
import time

import networkx as nx
import requests
import streamlit as st


API_BASE_URL = os.getenv("SCD_API_BASE_URL", "http://localhost:8000")


def _submit_job(package: str, registry: str) -> str:
    response = requests.post(
        f"{API_BASE_URL}/analyze",
        json={"name": package, "registry": registry},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["job_id"]


def _poll_job(job_id: str, timeout_seconds: int = 60) -> dict:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        response = requests.get(f"{API_BASE_URL}/results/{job_id}", timeout=10)
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") == "completed":
            return payload
        time.sleep(2)
    raise TimeoutError("Timed out waiting for analysis result")


def _render_graph_from_blast_radius(result: dict) -> None:
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


def main() -> None:
    st.set_page_config(page_title="Supply Chain Detector", layout="wide")
    st.title("Supply Chain Detector Dashboard")

    feed_col, report_col = st.columns([1, 2])

    with feed_col:
        st.subheader("Live Threat Feed")
        st.write("Recent high-risk packages from latest checks")
        st.info("Feed is populated after scans run in this session.")

    with report_col:
        st.subheader("Per-Package Risk Report")
        package = st.text_input("Package name", value="requests")
        registry = st.selectbox("Registry", options=["pypi", "npm"], index=0)

        if st.button("Analyze package"):
            try:
                with st.spinner("Submitting and polling analysis job..."):
                    job_id = _submit_job(package, registry)
                    st.write(f"Job submitted: {job_id}")
                    payload = _poll_job(job_id)
                    result = payload.get("result", {})

                st.success("Analysis completed")
                st.metric("Final risk score", result.get("final_score", 0))
                st.json(result.get("layers", {}))
                _render_graph_from_blast_radius(result)
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")


if __name__ == "__main__":
    main()
