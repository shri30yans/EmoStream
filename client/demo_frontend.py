"""Generic live-event demo frontend (Streamlit).

Deliberately event-agnostic: the operator types any event title
("City Marathon", "Product Launch", "Lecture Hall Q&A") and picks from a
configurable reaction set. No hardcoded teams, leagues, or vendors.
"""

from __future__ import annotations

import os
import time

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")
REACTIONS = [r for r in os.getenv("REACTIONS", "👍,❤️,🎉,😮,🔥").split(",") if r]


def api_post(reaction: str, user_id: str = "demo-user") -> bool:
    try:
        resp = requests.post(
            f"{API_BASE_URL}/v1/reactions",
            json={"user_id": user_id, "reaction": reaction,
                  "timestamp": time.time()},
            timeout=5,
        )
        return resp.status_code in (200, 202)
    except Exception:
        return False


def api_stats() -> dict:
    try:
        resp = requests.get(f"{API_BASE_URL}/v1/stats", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return {}


def main() -> None:
    st.title("StreamAgg-Spark: live reaction demo")
    event_title = st.text_input("Event title", "Demo Live Event")
    st.header(event_title)

    choice = st.radio("Pick a reaction", REACTIONS, horizontal=True)
    if st.button("Send reaction"):
        if api_post(choice):
            st.success(f"Sent {choice}")
        else:
            st.error("Ingest API unreachable. Start it with: make api")

    st.subheader("Ingest throughput (from API counters)")
    st.json(api_stats())
    st.caption(
        "Live aggregated windows stream over WebSocket "
        "(python client/websocket_client.py). "
        "Spark writes them to the aggregate Kafka topic."
    )


if __name__ == "__main__":
    main()
