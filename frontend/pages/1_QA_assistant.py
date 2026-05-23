import streamlit as st
import json
import os
import re
import chromadb
from chromadb.utils import embedding_functions
import networkx as nx
from networkx.readwrite import json_graph
from openai import OpenAI
from dotenv import load_dotenv

# --- 1. CONFIGURATION & SECRETS ---
load_dotenv() 
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_PATH = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2"
MASTER_FILE = os.path.join(BASE_PATH, "data", "master_legal_v1.json")
GRAPH_FILE = os.path.join(BASE_PATH, "data", "legal_graph.json")
DB_PATH = os.path.join(BASE_PATH, "vectordb")

st.set_page_config(page_title="General Legal Assistant", page_icon="🔍", layout="wide")

# --- UI FIX: STICKY CHAT INPUT ---
# --- UI FIX: STICKY & FULL-WIDTH CHAT INPUT ---
# --- UI FIX: RIGHT-ALIGNED STICKY CHAT BAR ---
st.markdown("""
    <style>
    /* 1. Position the fixed container to the right */
    div[data-testid="stChatInput"] {
        position: fixed;
        bottom: 20px;
        right: 100px; /* Distance from the right edge */
        left: auto;  /* Remove any left-side anchoring */
        width: 800px; /* Fixed width for a 'sidebar' chat feel */
        z-index: 999;
        background-color: transparent;
    }

    /* 2. Ensure the input box fills the 400px container */
    div[data-testid="stChatInput"] > div {
        width: 100% !important;
    }

    /* 3. Adjust main content padding so nothing is hidden */
    .main .block-container {
        padding-bottom: 100px;
        margin-right: 420px; /* Pushes content left so it doesn't overlap the bar */
    }

    /* 4. Responsive tweak: If sidebar is closed, keep it anchored right */
    @media (max-width: 768px) {
        div[data-testid="stChatInput"] {
            width: 90%;
            right: 5%;
        }
        .main .block-container {
            margin-right: 0;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CACHE RESOURCES ---
@st.cache_resource
def load_resources():
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
    with open(MASTER_FILE, 'r', encoding='utf-8') as f:
        master_dict = {sec['uid']: sec for sec in json.load(f)}
    with open(GRAPH_FILE, 'r', encoding='utf-8') as f:
        G = json_graph.node_link_graph(json.load(f), edges="links")
    chroma_client = chromadb.PersistentClient(path=DB_PATH)
    emb_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = chroma_client.get_collection(name="indian_legal_acts", embedding_function=emb_func)
    return client, master_dict, G, collection

client, master_dict, G, collection = load_resources()

# --- 3. HYBRID RETRIEVAL LOGIC ---
def get_hybrid_context(query_text, top_k=10):
    results = collection.query(query_texts=[query_text], n_results=top_k)
    initial_uids = results['ids'][0]
    context_uids = set(initial_uids)
    for uid in initial_uids:
        base_uid = uid.split('_v')[0]
        if G.has_node(base_uid):
            neighbors = [n for n in G.neighbors(base_uid) if "_S" in n]
            context_uids.update(neighbors)
    assembled_context = ""
    retrieved_titles = []
    for uid in context_uids:
        lookup_uid = next((k for k in master_dict.keys() if k.startswith(uid)), None)
        if lookup_uid:
            sec = master_dict[lookup_uid]
            title_str = f"{sec['act']} Sec {sec['section_number']}: {sec['title']}"
            retrieved_titles.append(title_str)
            assembled_context += f"\n--- {title_str} ---\n{sec['content']}\n"
    return assembled_context, retrieved_titles

# --- 4. UI LAYOUT ---
st.title("🔍 General Legal Assistant")
st.caption("Quickly research BNS, BNSS, and BSA laws via local database.")

with st.sidebar:
    st.header("🧠 Engine Status")
    st.success("Knowledge Graph Connected")
    st.success("Vector DB Online")
    context_placeholder = st.empty()

if "messages_qa" not in st.session_state:
    st.session_state.messages_qa = [{"role": "assistant", "content": "How can I help you with Indian law today?"}]

for message in st.session_state.messages_qa:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. USER INTERACTION & SEARCH ---
if prompt := st.chat_input("Ask about any section or recent judgment..."):
    st.session_state.messages_qa.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Searching Law Library..."):
        # Local RAG Context
        local_context, retrieved_titles = get_hybrid_context(prompt)
        
        # Display the local context titles in the sidebar
        with context_placeholder.container():
            with st.expander("Retrieved Legal Context", expanded=False):
                for title in retrieved_titles:
                    st.caption(f"🔹 {title}")
        
        # Combined System Prompt
        sys_prompt = f"""You are an expert Indian Legal AI. 
        LOCAL LEGAL CONTEXT (BNS/BNSS/BSA):
        {local_context}

        YOUR INSTRUCTIONS:
        1. Answer based on Local Laws primarily. 
        2. If no relevant info is found, say so. Do not invent facts.
        
        Latest Question: {prompt}
        Answer:"""

        try:
            response = client.chat.completions.create(
                model="openrouter/free",
                messages=[{"role": "user", "content": sys_prompt}],
                temperature=0.2,
            )
            bot_reply = response.choices[0].message.content.strip()
        except Exception as e:
            bot_reply = f"Error: {e}"

    # Display Response
    st.session_state.messages_qa.append({"role": "assistant", "content": bot_reply})
    with st.chat_message("assistant"):
        st.markdown(bot_reply)