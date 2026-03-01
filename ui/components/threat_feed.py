from __future__ import annotations

import streamlit as st


def render_threat_feed(feed_items: list[dict]) -> None:
    st.subheader("Live Threat Feed")
    if not feed_items:
        st.info("No scans recorded yet.")
        return

    for item in feed_items:
        score = item.get("final_score")
        badge = "🔴" if score is not None and score >= 70 else "🟡" if score is not None and score >= 40 else "🟢"
        st.write(
            f"{badge} {item.get('registry')}:{item.get('package')}"
            f" | score={score if score is not None else 'n/a'} | {item.get('status')}"
        )
