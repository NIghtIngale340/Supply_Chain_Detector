import os
import time

import requests
import streamlit as st

from ui.components.graph_view import render_graph_from_blast_radius
from ui.components.risk_report import render_layer_evidence
from ui.components.threat_feed import render_threat_feed


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


def _load_recent_feed(limit: int = 15) -> list[dict]:
    response = requests.get(f"{API_BASE_URL}/results/recent", params={"limit": limit}, timeout=10)
    response.raise_for_status()
    return response.json().get("items", [])


def main() -> None:
    st.set_page_config(page_title="Supply Chain Detector", layout="wide")
    st.title("Supply Chain Detector Dashboard")

    feed_col, report_col = st.columns([1, 2])

    with feed_col:
        try:
            feed_items = _load_recent_feed()
            render_threat_feed(feed_items)
        except Exception as exc:
            st.subheader("Live Threat Feed")
            st.warning(f"Unable to load feed: {exc}")

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
                st.write(f"Decision: {result.get('decision', 'unknown')}")
                render_layer_evidence(result)
                render_graph_from_blast_radius(result)
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")


if __name__ == "__main__":
    main()
