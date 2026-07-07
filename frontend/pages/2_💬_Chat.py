"""
Streamlit Frontend — Chat Page
==============================

Implements the conversational interface, sending query requests to FastAPI
and rendering answers alongside citation expanders.
"""

import requests
import streamlit as st
from components.chat_message import render_message

# Custom page header style
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

st.markdown('<h1 class="main-title">💬 Document Q&A Chat</h1>', unsafe_allow_html=True)

# Initialize message history list in Streamlit session state
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Fetch active documents list to allow target scoping
active_docs = []
try:
    doc_resp = requests.get(
        f"{backend_url}/api/v1/documents",
        headers=headers,
        params={"skip": 0, "limit": 100},
        timeout=5,
    )
    if doc_resp.status_code == 200:
        active_docs = doc_resp.json().get("documents", [])
except Exception:
    pass

# Document scope selection
doc_options = {d["filename"]: d["id"] for d in active_docs}
selected_doc_names = st.multiselect(
    "🔍 Filter search to specific documents (Leave empty to search all)",
    options=list(doc_options.keys()),
    help="Restricts RAG retrieval only to checked files.",
)
selected_doc_ids = [doc_options[name] for name in selected_doc_names]

# Clear history button
col1, col2 = st.columns([8, 2])
with col2:
    if st.button("🗑️ Clear Chat History"):
        st.session_state["messages"] = []
        st.rerun()

# Display chat messages from history on app rerun
for msg in st.session_state["messages"]:
    render_message(
        role=msg["role"],
        text=msg["text"],
        sources=msg.get("sources"),
    )

# Accept user input
if prompt := st.chat_input("Ask a question about your documents..."):
    # Display user message in chat message container
    render_message(role="user", text=prompt)
    # Add user message to session state history
    st.session_state["messages"].append({"role": "user", "text": prompt})

    # Prepare query payload
    payload = {
        "question": prompt,
        "top_k": st.session_state.get("top_k", 5),
        "document_ids": selected_doc_ids if selected_doc_ids else None,
        "similarity_threshold": st.session_state.get("similarity_threshold", 0.3),
    }

    # Request answer from FastAPI server
    with st.spinner("Searching library and thinking..."):
        try:
            response = requests.post(
                f"{backend_url}/api/v1/query",
                headers=headers,
                json=payload,
                timeout=180,
            )

            if response.status_code == 200:
                res_data = response.json()
                answer = res_data.get("answer", "")
                sources = res_data.get("sources", [])

                # Render assistant response in chat container
                render_message(role="assistant", text=answer, sources=sources)

                # Add assistant response to session state history
                st.session_state["messages"].append(
                    {
                        "role": "assistant",
                        "text": answer,
                        "sources": sources,
                    }
                )
            else:
                err_msg = "Failed to fetch response"
                try:
                    err_msg = response.json().get("message", response.text)
                except Exception:
                    pass
                st.error(f"Error ({response.status_code}): {err_msg}")
        except Exception as e:
            st.error(f"❌ Connection error: {e}")
