import streamlit as st
import json
import os
import re
import chromadb
from chromadb.utils import embedding_functions
import networkx as nx
from networkx.readwrite import json_graph
from openai import OpenAI
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
import tempfile
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dotenv import load_dotenv

# --- 1. CONFIGURATION ---
# Because this script is in frontend/pages/, going up '..' brings us to frontend/
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
env_path = os.path.join(frontend_dir, '.env')

# Load the environment variables from the exact path you provided
load_dotenv(dotenv_path=env_path)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# The Fail-Safe
if not OPENROUTER_API_KEY:
    st.error("🚨 Critical Error: OPENROUTER_API_KEY not found.")
    st.info(f"Python looked for your .env file exactly here: {env_path}")
    st.stop()

# ... [Keep your imports and .env loading code above this] ...

# --- CLOUD-SAFE PATHING ---
# Dynamically find the root folder (legal_rag_v2) instead of hardcoding the C: Drive
current_dir = os.path.dirname(__file__)
BASE_PATH = os.path.abspath(os.path.join(current_dir, '..', '..'))

MASTER_FILE = os.path.join(BASE_PATH, "data", "master_legal_v1.json")
GRAPH_FILE = os.path.join(BASE_PATH, "data", "legal_graph.json")
DB_PATH = os.path.join(BASE_PATH, "vectordb")

# REMOVED: pytesseract and poppler hardcoded Windows paths! Linux finds them automatically.

st.set_page_config(page_title="Tom Dashboard", page_icon="🤖", layout="wide")

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

# --- 2. HELPERS & VISUALIZATION ---
def extract_json_data(text):
    """Parses JSON from [[DATA]] tags in LLM response."""
    match = re.search(r"\[\[DATA\]\](.*?)\[\[/DATA\]\]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except:
            return None
    return None

def draw_timeline(data):
    if not data or "timeline" not in data or not data["timeline"]:
        return st.info("No timeline data found yet.")
    
    df = pd.DataFrame(data["timeline"])
    
    # --- SAFETY FIX 1: Auto-rename 'timestamp' to 'date' ---
    if "timestamp" in df.columns:
        df = df.rename(columns={"timestamp": "date"})
        
    # --- SAFETY FIX 2: Stop crash if columns are completely missing ---
    if "date" not in df.columns or "event" not in df.columns:
        st.warning(f"Waiting for valid timeline data... Received columns: {list(df.columns)}")
        return
    
    # Create the figure
    fig = px.scatter(df, x="date", y="event", text="event", 
                     title="Case Chronology", template="plotly_dark")
    
    fig.update_traces(textposition='middle right', marker=dict(size=14, color='red'))
    fig.update_layout(
        margin=dict(l=150),
        xaxis_title="Timeline",
        yaxis_title=None,
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)


def draw_sections_chart(data):
    if not data or "sections_impact" not in data:
        return st.info("No section data available.")
    
    # Convert dictionary to DataFrame for Plotly
    impact_data = data["sections_impact"]
    df = pd.DataFrame({
        'Section': list(impact_data.keys()),
        'Relevance': list(impact_data.values())
    }).sort_values(by='Relevance', ascending=True)

    # Horizontal Bar Chart looks best for long section names
    fig = px.bar(df, x='Relevance', y='Section', orientation='h',
                 title="Applicable Sections by Relevance",
                 color='Relevance', color_continuous_scale='Reds',
                 template="plotly_dark")
    
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

def draw_risk_gauge(data):
    risk_val = data.get("risk_score", 0) if data else 0
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = risk_val,
        title = {'text': "Case Severity Score"},
        gauge = {'axis': {'range': [0, 100]},
                 'bar': {'color': "darkred"},
                 'steps': [
                     {'range': [0, 30], 'color': "green"},
                     {'range': [30, 70], 'color': "orange"},
                     {'range': [70, 100], 'color': "red"}]}))
    st.plotly_chart(fig, use_container_width=True)

# --- 3. RESOURCE CACHING ---
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

# --- 4. HYBRID RETRIEVAL ---
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
    for uid in context_uids:
        lookup_uid = next((k for k in master_dict.keys() if k.startswith(uid)), None)
        if lookup_uid:
            sec = master_dict[lookup_uid]
            assembled_context += f"\n--- {sec['act']} Sec {sec['section_number']}: {sec['title']} ---\n{sec['content']}\n"
    return assembled_context

# --- 5. UI TABS & SIDEBAR ---
tab1, tab2 = st.tabs(["💬 Case Chat", "📊 Analysis Dashboard"])

with st.sidebar:
    st.header("📄 Upload Document")
    uploaded_file = st.file_uploader("Upload FIR or Legal PDF", type=["pdf"])
    
    if uploaded_file and st.button("Analyze Document"):
        with st.spinner("Tom is reading..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            extracted_text = ""
            try:
                with pdfplumber.open(tmp_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text: extracted_text += page_text + "\n"
                
                # If the PDF is an image/scanned, we use Poppler + Tesseract
                if len(extracted_text.strip()) < 50:
                    st.toast("Scanned document detected. Booting up OCR engine...")
                    
                    # CRITICAL FIX: Ensure poppler_path points to the 'bin' folder
                    # If the PDF is an image/scanned, we use Poppler + Tesseract
                if len(extracted_text.strip()) < 50:
                    st.toast("Scanned document detected. Booting up OCR engine...")
                    
                    # CLOUD-SAFE FIX: Removed the poppler_path argument
                    images = convert_from_path(tmp_path)
                    
                    for img in images:
                        extracted_text += pytesseract.image_to_string(img) + "\n"
                
                st.session_state.document_context = extracted_text
                st.success("Analysis Ready!")
            except Exception as e:
                st.error(f"Error: {e}")
            finally:
                os.remove(tmp_path)

# --- 6. CHAT LOGIC (TAB 1) ---
with tab1:
    st.title("🤖 Tom: Case Intelligence")
    if "messages_tom" not in st.session_state:
        st.session_state.messages_tom = [{"role": "assistant", "content": "Hello. I'm ready. Please upload a document to begin analysis."}]
    if "document_context" not in st.session_state:
        st.session_state.document_context = ""

    for message in st.session_state.messages_tom:
        with st.chat_message(message["role"]):
            # Clean text by removing DATA tags for display
            clean_text = re.sub(r"\[\[DATA\]\].*?\[\[/DATA\]\]", "", message["content"], flags=re.DOTALL)
            st.markdown(clean_text)

    if prompt := st.chat_input("Ask about the case..."):
        st.session_state.messages_tom.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.spinner("Processing..."):
            context = get_hybrid_context(prompt)
            doc_context = st.session_state.document_context
            
            sys_prompt = f"""You are a Precise Indian Legal AI named Tom. 

DOCUMENT FACTS: {st.session_state.document_context[:1500]}
LOCAL LEGAL CONTEXT (MASTER DATA): {context}
USER QUESTION: {prompt}

CRITICAL INSTRUCTIONS:
1. Answer the USER QUESTION. 
2. STRICT GROUNDING: Use ONLY the provided LEGAL CONTEXT to define sections. If a definition is requested, you MUST provide the literal legal text from the LOCAL LEGAL CONTEXT. 
3. NO SUMMARIZATION: Do not use general knowledge or psychological terms. If the law says "fracture," do not say "functional impairment."
4. RELEVANCY FILTER: If a section in the LEGAL CONTEXT is completely unrelated to the DOCUMENT FACTS (e.g., aircraft laws for a bike accident), label it as "Irrelevant" in your text analysis.
5. HALLUCINATION CHECK: If the answer is not in the provided LEGAL CONTEXT, state "The specific legal text is not available in my current local database."

MANDATORY: You MUST include a JSON block for charts inside [[DATA]] tags at the very end.
DYNAMIC DATA: Populate the JSON using real data from the DOCUMENT FACTS. Do not just copy the example.
You MUST use these exact keys: 'date' (format YYYY-MM-DD) and 'event'.


[[DATA]]
{{
  "timeline": [{{"date": "2024-07-01", "event": "FIR Registered"}}],
  "risk_score": 45,
  "sections_impact": {{"BNS 285": 90}}
}}
[[/DATA]]
"""

            try:
                response = client.chat.completions.create(
                    model="openrouter/free",
                    messages=[{"role": "user", "content": sys_prompt}],
                    temperature=0.0
                )
                bot_reply = response.choices[0].message.content
                st.session_state.last_json = extract_json_data(bot_reply)
            except Exception as e:
                bot_reply = f"Error: {e}"

            st.session_state.messages_tom.append({"role": "assistant", "content": bot_reply})
            with st.chat_message("assistant"):
                st.markdown(re.sub(r"\[\[DATA\]\].*?\[\[/DATA\]\]", "", bot_reply, flags=re.DOTALL))

# --- 7. DASHBOARD (TAB 2) ---
with tab2:
    st.header("📊 Case Visualization Dashboard")
    if "last_json" in st.session_state and st.session_state.last_json:
        data = st.session_state.last_json
        
        # Row 1: Timeline and Risk
        c1, c2 = st.columns(2)
        with c1: draw_timeline(data)
        with c2: draw_risk_gauge(data)
        
        st.divider()
        
        # Row 2: Section Impact
        st.write("### ⚖️ Legal Section Impact")
        draw_sections_chart(data)
    else:
        st.info("Charts will populate once a document is analyzed and a question is asked.")