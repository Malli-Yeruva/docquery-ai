"""
Streamlit Frontend — Main Page
==============================

Entry point for the Streamlit multi-page interface. Displays application introduction
and guides the user on how to run RAG operations.
"""

import streamlit as st

# Configure page settings before any other Streamlit commands
st.set_page_config(
    page_title="DocQuery AI — Intelligent Document Q&A",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Premium Styling
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@300;400;600&display=swap');
        
        * {
            font-family: 'Inter', sans-serif;
        }
        
        h1, h2, h3 {
            font-family: 'Outfit', sans-serif;
            font-weight: 800;
        }
        
        .main-title {
            font-size: 3rem;
            background: linear-gradient(135deg, #FF6B6B 0%, #4D96FF 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }
        
        .subtitle {
            font-size: 1.25rem;
            color: #888888;
            margin-bottom: 2.5rem;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid rgba(255, 255, 255, 0.05);
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(5px);
            -webkit-backdrop-filter: blur(5px);
            transition: transform 0.3s ease, border-color 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            border-color: rgba(77, 150, 255, 0.4);
        }
        
        .card-title {
            color: #4D96FF;
            font-size: 1.4rem;
            font-weight: 600;
            margin-bottom: 0.8rem;
        }
        
        .card-text {
            font-size: 0.95rem;
            color: #D1D1D1;
            line-height: 1.5;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Render Sidebar configuration
from components.sidebar import render_sidebar
backend_url, headers = render_sidebar()

# Main page layout
st.markdown('<h1 class="main-title">🧠 DocQuery AI</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Intelligent, 100% local document Q&A engine powered by Gemma3 & ChromaDB</p>',
    unsafe_allow_html=True,
)

st.markdown("### How it works")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div class="card">
            <div class="card-title">1. 📄 Upload Documents</div>
            <div class="card-text">
                Upload your PDFs, TXT files, Word files, spreadsheets, or raw HTML pages. 
                Our engine automatically parses, structure, and slices documents into context-rich text chunks.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class="card">
            <div class="card-title">2. ⚡ Generate Vectors</div>
            <div class="card-text">
                Chunks are mapped to dense vector embeddings using the local 
                <code>all-MiniLM-L6-v2</code> model, storing them inside a persistent instance of ChromaDB.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
        <div class="card">
            <div class="card-title">3. 💬 Semantic Chat</div>
            <div class="card-text">
                Ask natural language questions. The retriever pulls relevant context passages, 
                and local Gemma3 generates a complete, cited answer.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

st.markdown("### System Quick-Start Checklist")

# Active check connecting to the backend
import requests

backend_healthy = False
try:
    health_resp = requests.get(f"{backend_url}/health", timeout=3)
    if health_resp.status_code == 200:
        backend_healthy = True
except Exception:
    pass

ready_healthy = False
checks = {}
try:
    ready_resp = requests.get(f"{backend_url}/ready", timeout=5)
    if ready_resp.status_code == 200:
        ready_healthy = True
        checks = ready_resp.json().get("checks", {})
except Exception:
    pass

c_api, c_sqlite, c_chroma, c_ollama = st.columns(4)

with c_api:
    if backend_healthy:
        st.success("✅ Backend API: Connected")
    else:
        st.error("❌ Backend API: Offline")

with c_sqlite:
    if checks.get("sqlite", False):
        st.success("✅ Metadata DB: Ready")
    else:
        st.error("❌ Metadata DB: Error")

with c_chroma:
    if checks.get("chroma", False):
        st.success("✅ ChromaDB: Ready")
    else:
        st.error("❌ ChromaDB: Error")

with c_ollama:
    if checks.get("ollama", False):
        st.success("✅ Ollama LLM: Connected")
    else:
        st.error("❌ Ollama LLM: Offline")

if not backend_healthy:
    st.info(
        "💡 **Need help?** Make sure your FastAPI backend is running! "
        "Start it in your shell by running `make run` or `uvicorn main:app --reload`."
    )
elif not checks.get("ollama", False):
    st.info(
        "💡 **Ollama Offline?** Ensure your local Ollama app is running "
        "and you've pulled the model: `ollama pull gemma3:4b`."
    )
else:
    st.success("🚀 Everything is healthy and running! Navigate to the side pages to begin.")
