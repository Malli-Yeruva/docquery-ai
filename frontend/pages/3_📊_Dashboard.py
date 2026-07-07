"""
Streamlit Frontend — Analytics Dashboard
=======================================

Displays analytics on documents, chunks, query performance, and history.
Uses Plotly for interactive graphs.
"""

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# Premium custom style overrides
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@300;400;600&display=swap');
        h1, h2, h3 { font-family: 'Outfit', sans-serif; font-weight: 800; }
        .main-title {
            font-size: 2.5rem;
            background: linear-gradient(135deg, #FF6B6B 0%, #4D96FF 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 2rem;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Render control panel
from components.sidebar import render_sidebar
backend_url, headers = render_sidebar()

st.markdown('<h1 class="main-title">📊 System Dashboard & Analytics</h1>', unsafe_allow_html=True)

# ── Load statistics ──────────────────────────────────────────────────
@st.fragment
def fetch_logs_and_docs():
    """Fetch logs and documents to populate the dashboard metrics."""
    docs = []
    logs = []

    try:
        doc_resp = requests.get(
            f"{backend_url}/api/v1/documents",
            headers=headers,
            params={"skip": 0, "limit": 100},
            timeout=5,
        )
        if doc_resp.status_code == 200:
            docs = doc_resp.json().get("documents", [])
    except Exception:
        pass

    try:
        log_resp = requests.get(
            f"{backend_url}/api/v1/query/logs",
            headers=headers,
            params={"limit": 100},
            timeout=5,
        )
        if log_resp.status_code == 200:
            logs = log_resp.json()
    except Exception:
        pass

    return docs, logs


docs, logs = fetch_logs_and_docs()

# Calculate stats
total_docs = len(docs)
total_chunks = sum(d.get("chunk_count", 0) for d in docs)
total_queries = len(logs)
avg_latency = 0.0
if total_queries > 0:
    avg_latency = sum(l.get("query_time_ms", 0.0) for l in logs) / total_queries

# ── Metric Cards ─────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Total Documents", total_docs)
with m2:
    st.metric("Total Indexed Chunks", total_chunks)
with m3:
    st.metric("Total Queries", total_queries)
with m4:
    st.metric("Avg Latency", f"{avg_latency:.1f} ms" if avg_latency > 0 else "0.0 ms")

st.markdown("---")

# ── Graphs and Charts ────────────────────────────────────────────────
if total_queries > 0:
    st.markdown("### Performance & Query History")

    # Create latency dataframe
    df = pd.DataFrame(logs)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df = df.sort_values(by="created_at")

    # Plotly Line Chart for query latency over time
    fig = px.line(
        df,
        x="created_at",
        y="query_time_ms",
        title="Query Latency (ms) Over Time",
        labels={"created_at": "Timestamp", "query_time_ms": "Latency (ms)"},
        markers=True,
        template="plotly_dark",
    )
    fig.update_traces(line_color="#4D96FF", marker=dict(size=8, color="#FF6B6B"))
    st.plotly_chart(fig, use_container_width=True)

    # ── History log table ────────────────────────────────────────────
    st.markdown("### Query Logs")
    table_data = []
    for log in logs:
        # Truncate answer for readability
        ans = log["answer"]
        if len(ans) > 100:
            ans = ans[:100] + "..."

        table_data.append(
            {
                "Timestamp": pd.to_datetime(log["created_at"]).strftime("%Y-%m-%d %H:%M:%S"),
                "Question": log["question"],
                "Generated Answer Summary": ans,
                "Latency": f"{log['query_time_ms']:.1f} ms",
                "Model": log["model"],
            }
        )
    st.dataframe(pd.DataFrame(table_data), use_container_width=True)
else:
    st.info("No query logs found. Submit some questions in the Chat page to populate the dashboard analytics!")
