import streamlit as st
import json
import os
import chromadb
from chromadb.utils import embedding_functions
import networkx as nx
from networkx.readwrite import json_graph
from groq import Groq
from openai import OpenAI
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
import tempfile

# --- 1. CONFIGURATION & PATHS ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") 
BASE_PATH = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2"

MASTER_FILE = os.path.join(BASE_PATH, "data", "master_legal_v1.json")
GRAPH_FILE = os.path.join(BASE_PATH, "data", "legal_graph.json")
DB_PATH = os.path.join(BASE_PATH, "vectordb")

# --- OCR ENGINE PATHS ---
# Explicitly telling Python where the vision engines are
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
POPPLER_PATH = r'C:\poppler\Library\bin' # Update if your poppler is extracted elsewhere

# --- 2. UI SETUP ---
st.set_page_config(page_title="Tom - Legal AI", page_icon="⚖️", layout="wide")

# Sidebar for Uploads and Transparency
with st.sidebar:
    st.header("📄 Document Analysis")
    uploaded_file = st.file_uploader("Upload an FIR, Notice, or Legal PDF", type=["pdf"])
    
    if uploaded_file and st.button("Analyze Document"):
        with st.spinner("Tom is reading the document..."):
            # Save uploaded file temporarily to process it
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            extracted_text = ""
            try:
                # Attempt 1: Fast Digital Text Extraction
                with pdfplumber.open(tmp_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            extracted_text += page_text + "\n"
                
                # Attempt 2: OCR Fallback (If the PDF is a scanned image)
                if len(extracted_text.strip()) < 50:
                    st.toast("Scanned document detected. Booting up OCR engine...")
                    images = convert_from_path(tmp_path, poppler_path=POPPLER_PATH)
                    for i, img in enumerate(images):
                        extracted_text += pytesseract.image_to_string(img) + "\n"
                        
                st.session_state.document_context = extracted_text
                st.success("Document read successfully! It is now in Tom's memory.")
                
            except Exception as e:
                st.error(f"Error processing document: {e}")
            finally:
                os.remove(tmp_path) # Clean up temp file

    st.divider()
    st.header("🧠 Graph RAG Engine")
    st.caption("Tom maps the BNS, BNSS, and BSA in real-time.")
    st.subheader("Retrieved Nodes:")
    context_placeholder = st.empty()
    context_placeholder.info("Ask a question to see the retrieved legal nodes here.")

st.title("⚖️ Tom - Indian Criminal Law Assistant")
st.caption("Ask me about the new criminal laws, or upload a document for legal review.")

# --- 3. CACHE RESOURCES ---
@st.cache_resource
def load_resources():
    # Point the OpenAI client to OpenRouter's URL
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )
    
    with open(MASTER_FILE, 'r', encoding='utf-8') as f:
        master_dict = {sec['uid']: sec for sec in json.load(f)}
        
    with open(GRAPH_FILE, 'r', encoding='utf-8') as f:
        G = json_graph.node_link_graph(json.load(f), edges="links")
        
    chroma_client = chromadb.PersistentClient(path=DB_PATH)
    emb_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = chroma_client.get_collection(name="indian_legal_acts", embedding_function=emb_func)
    
    return client, master_dict, G, collection

client, master_dict, G, collection = load_resources()

# --- 4. HYBRID RETRIEVAL LOGIC ---
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

# --- 5. STATE MANAGEMENT ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I am Tom. Upload a document or ask a legal question to begin."}]
if "document_context" not in st.session_state:
    st.session_state.document_context = ""

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. USER INTERACTION ---
if prompt := st.chat_input("E.g., Analyze the uploaded FIR..."):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Tom is analyzing..."):
        # We combine the user query + document text for the vector search 
        # so the Graph RAG pulls laws relevant to the document
        search_query = prompt
        if st.session_state.document_context:
            search_query += " " + st.session_state.document_context[:500] 
            
        context, retrieved_titles = get_hybrid_context(search_query)
        
        with context_placeholder.container():
            with st.expander("View Retrieved Legal Nodes", expanded=False):
                for title in retrieved_titles:
                    st.caption(f"🔹 {title}")
        
        history = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in st.session_state.messages[-4:-1]])
        
        # Inject the uploaded document into the LLM prompt
        doc_injection = f"\nUPLOADED DOCUMENT FACTS:\n{st.session_state.document_context}\n" if st.session_state.document_context else ""
        
        sys_prompt = f"""You are an expert Indian Legal AI named Tom. 

UPLOADED DOCUMENT FACTS:
{st.session_state.document_context if st.session_state.document_context else 'None'}

RETRIEVED LEGAL CONTEXT:
{context}

CHAT HISTORY:
{history}

YOUR INSTRUCTIONS:
1. Read the facts of the document or the user's question.
2. Look at the Retrieved Legal Context. ONLY use the sections that directly apply to the facts. 
3. STRICT GUARDRAIL: If the retrieved context contains irrelevant laws (like Robbery or Foreign Evidence for a traffic accident), completely IGNORE them. Do not mention them.
4. If the document mentions old IPC/CrPC sections, gently note that the new laws in effect are the BNS/BNSS/BSA.
5. Answer clearly and cite the specific applicable Acts and Sections.

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
            bot_reply = f"Error connecting to LLM: {e}"

    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    with st.chat_message("assistant"):
        st.markdown(bot_reply)