"""
Streamlit Frontend — Upload Page
================================

Supports file uploads and metadata listing. Allows users to delete ingested files.
"""

import requests
import streamlit as st

# Custom Styling (Shared class styling)
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
    </style>
    """,
    unsafe_allow_html=True,
)

# Render control panel
from components.sidebar import render_sidebar
backend_url, headers = render_sidebar()

st.markdown('<h1 class="main-title">📄 Document Management</h1>', unsafe_allow_html=True)

# ── File Upload Section ──────────────────────────────────────────────
st.markdown("### Upload new documents")

uploaded_files = st.file_uploader(
    "Choose documents to add to the RAG database",
    type=["pdf", "txt", "docx", "csv", "xlsx", "html", "htm"],
    accept_multiple_files=True,
)

if uploaded_files:
    upload_btn = st.button("🚀 Process & Ingest Documents")
    if upload_btn:
        for file in uploaded_files:
            with st.spinner(f"Ingesting '{file.name}'..."):
                try:
                    files = {"file": (file.name, file.getvalue(), file.type)}
                    response = requests.post(
                        f"{backend_url}/api/v1/documents/upload",
                        headers=headers,
                        files=files,
                        timeout=180,  # File ingestion could take time (embedding model run)
                    )

                    if response.status_code == 201:
                        data = response.json()
                        st.success(
                            f"✅ Successfully ingested '{file.name}'! "
                            f"Created {data.get('chunk_count', 0)} chunks."
                        )
                    else:
                        err_msg = "Unknown error"
                        try:
                            err_msg = response.json().get("message", response.text)
                        except Exception:
                            pass
                        st.error(f"❌ Failed to ingest '{file.name}': {err_msg}")
                except Exception as e:
                    st.error(f"❌ Server connection error: {e}")

st.markdown("---")

# ── Documents List Section ───────────────────────────────────────────
st.markdown("### Ingested Documents Library")


def load_documents():
    """Fetch current documents metadata list from backend API."""
    try:
        response = requests.get(
            f"{backend_url}/api/v1/documents",
            headers=headers,
            params={"skip": 0, "limit": 100},
            timeout=10,
        )
        if response.status_code == 200:
            return response.json().get("documents", []), response.json().get("total", 0)
        else:
            st.error(f"Failed to fetch library: {response.status_code}")
            return [], 0
    except Exception as e:
        st.error(f"API connection error: {e}")
        return [], 0


docs, total = load_documents()

if not docs:
    st.info("No documents found in the database. Upload files above to get started!")
else:
    st.write(f"Total documents: **{total}**")

    # Render a clean grid of documents
    for doc in docs:
        col1, col2, col3, col4 = st.columns([4, 2, 2, 2])
        with col1:
            st.markdown(f"📄 **{doc['filename']}**")
        with col2:
            st.write(f"`{doc['file_type'].upper()}`")
        with col3:
            st.write(f"{doc['chunk_count']} chunks")
        with col4:
            # Delete button
            delete_key = f"del_{doc['id']}"
            if st.button("🗑️ Delete", key=delete_key):
                with st.spinner("Deleting..."):
                    try:
                        del_response = requests.delete(
                            f"{backend_url}/api/v1/documents/{doc['id']}",
                            headers=headers,
                            timeout=10,
                        )
                        if del_response.status_code == 204:
                            st.success(f"Deleted '{doc['filename']}'!")
                            st.rerun()
                        else:
                            st.error(f"Failed: {del_response.status_code}")
                    except Exception as e:
                        st.error(f"Error: {e}")
        st.markdown('<hr style="margin: 0.5rem 0; opacity: 0.1;"/>', unsafe_allow_html=True)
