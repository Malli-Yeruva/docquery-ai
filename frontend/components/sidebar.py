"""
Streamlit Sidebar Component
===========================

Provides a unified configuration panel in the Streamlit sidebar, letting users edit:
- API endpoint URLs
- Authentication tokens (X-API-Key)
- RAG search parameters (top_k, similarity_threshold)
"""

from typing import Any
import streamlit as st


def render_sidebar() -> tuple[str, dict[str, str]]:
    """
    Renders sidebar settings.

    Returns:
        backend_url: Endpoint path.
        headers: Auth request headers.
    """
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 2rem;">
                <h2 style="font-family: 'Outfit', sans-serif; font-weight: 800; color: #4D96FF; margin: 0;">🔧 Control Panel</h2>
                <p style="font-size: 0.85rem; color: #888; margin-top: 0.2rem;">DocQuery AI settings</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### Backend connection")

        # Load defaults
        import os
        default_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        default_key = "your-secret-api-key-change-me"

        backend_url = st.text_input(
            "Backend Server URL",
            value=st.session_state.get("backend_url", default_url),
            help="Full path to the FastAPI server.",
            key="side_backend_url",
        )
        st.session_state["backend_url"] = backend_url

        api_key = st.text_input(
            "API Access Key",
            value=st.session_state.get("api_key", default_key),
            type="password",
            help="X-API-Key token value.",
            key="side_api_key",
        )
        st.session_state["api_key"] = api_key

        headers = {"X-API-Key": api_key}

        st.markdown("---")
        st.markdown("### Search parameters")

        top_k = st.slider(
            "Top K Documents",
            min_value=1,
            max_value=20,
            value=st.session_state.get("top_k", 5),
            help="Number of text chunks to retrieve for LLM context.",
            key="side_top_k",
        )
        st.session_state["top_k"] = top_k

        similarity_threshold = st.slider(
            "Similarity Threshold",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.get("similarity_threshold", 0.3),
            step=0.05,
            help="Minimum cosine similarity matching score.",
            key="side_similarity_threshold",
        )
        st.session_state["similarity_threshold"] = similarity_threshold

        st.markdown("---")
        st.markdown(
            """
            <div style="font-size: 0.8rem; color: #666; text-align: center;">
                DocQuery AI · Local & Safe
            </div>
            """,
            unsafe_allow_html=True,
        )

    return backend_url, headers
