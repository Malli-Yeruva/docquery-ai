"""
Chat Message Render Component
=============================

Helpers to display dialogue interactions, styled markdown content, and RAG sources.
"""

import streamlit as st


def render_message(role: str, text: str, sources: list[dict] | None = None) -> None:
    """
    Renders a message bubble with custom styles and source expanders.

    Args:
        role: "user" or "assistant" / "system"
        text: Message raw text
        sources: Optional citations retrieved from ChromaDB
    """
    with st.chat_message(role):
        # Display main text
        st.markdown(text)

        # Render sources in an expander if present
        if role == "assistant" and sources:
            with st.expander("📖 View retrieved sources and citations", expanded=False):
                # Build table for clear details
                st.markdown(
                    """
                    <style>
                        .source-block {
                            border-left: 3px solid #4D96FF;
                            padding-left: 10px;
                            margin-bottom: 15px;
                            background: rgba(255, 255, 255, 0.02);
                            border-radius: 0 8px 8px 0;
                            padding-top: 5px;
                            padding-bottom: 5px;
                        }
                        .source-meta {
                            font-size: 0.8rem;
                            color: #888;
                            margin-bottom: 5px;
                        }
                        .source-content {
                            font-size: 0.9rem;
                            color: #E2E2E2;
                        }
                        .badge {
                            background: rgba(77, 150, 255, 0.2);
                            color: #4D96FF;
                            padding: 2px 6px;
                            border-radius: 4px;
                            font-size: 0.75rem;
                            font-weight: bold;
                            margin-right: 5px;
                        }
                    </style>
                    """,
                    unsafe_allow_html=True,
                )

                for idx, src in enumerate(sources, 1):
                    doc_name = src.get("document_name", "Unknown File")
                    chunk_idx = src.get("chunk_index", 0)
                    score = src.get("similarity_score", 0.0)
                    content = src.get("content", "").strip()

                    # Highlight source
                    st.markdown(
                        f"""
                        <div class="source-block">
                            <div class="source-meta">
                                <span class="badge">Source [{idx}]</span>
                                <b>{doc_name}</b> (Chunk #{chunk_idx}) · Cosine Similarity: <code>{score:.2f}</code>
                            </div>
                            <div class="source-content">{content}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
