import json
import os
import chromadb
from chromadb.utils import embedding_functions
import networkx as nx
from networkx.readwrite import json_graph
from groq import Groq

# --- 1. CONFIGURATION & PATHS ---
GROQ_API_KEY = "YOUR_API_KEY_HERE" # ⚠️ Replace with your actual key
BASE_PATH = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2"

MASTER_FILE = os.path.join(BASE_PATH, "data", "master_legal_v1.json")
GRAPH_FILE = os.path.join(BASE_PATH, "data", "legal_graph.json")
DB_PATH = os.path.join(BASE_PATH, "vectordb")

# Initialize Groq Client
client = Groq(api_key=GROQ_API_KEY)

# --- 2. LOAD RESOURCES ---
print("⚙️ Booting up Legal Graph RAG Engine...")

# Load Master Data into a dictionary for fast lookup
if not os.path.exists(MASTER_FILE):
    print(f"❌ Error: Could not find Master File at {MASTER_FILE}")
    exit()

with open(MASTER_FILE, 'r', encoding='utf-8') as f:
    master_list = json.load(f)
    master_dict = {sec['uid']: sec for sec in master_list}

# Load Knowledge Graph
if not os.path.exists(GRAPH_FILE):
    print(f"❌ Error: Could not find Graph File at {GRAPH_FILE}")
    exit()

with open(GRAPH_FILE, 'r', encoding='utf-8') as f:
    graph_data = json.load(f)
    G = json_graph.node_link_graph(graph_data, edges="links")

# Load ChromaDB Vector Store
chroma_client = chromadb.PersistentClient(path=DB_PATH)
emb_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = chroma_client.get_collection(name="indian_legal_acts", embedding_function=emb_func)

# --- 3. CORE RETRIEVAL LOGIC ---
def get_hybrid_context(query_text, top_k=10):
    """Retrieves context using Vector Search + 1-Hop Graph Expansion."""
    
    # Step A: Vector Search (Find the most semantically relevant nodes)
    results = collection.query(
        query_texts=[query_text],
        n_results=top_k
    )
    
    initial_uids = results['ids'][0]
    context_uids = set(initial_uids)
    
    # Step B: Graph Expansion (Find procedural/evidentiary neighbors)
    for uid in initial_uids:
        base_uid = uid.split('_v')[0] # Clean duplicate tags if any
        if G.has_node(base_uid):
            neighbors = list(G.neighbors(base_uid))
            # Keep only section nodes (ignore Chapter nodes to save LLM context window)
            section_neighbors = [n for n in neighbors if "_S" in n]
            context_uids.update(section_neighbors)

    # Step C: Assemble the Legal Text for the LLM
    assembled_context = ""
    for uid in context_uids:
        # Match back to master dictionary
        lookup_uid = next((k for k in master_dict.keys() if k.startswith(uid)), None)
        if lookup_uid:
            sec = master_dict[lookup_uid]
            assembled_context += f"\n--- {sec['act']} Section {sec['section_number']}: {sec['title']} ---\n"
            assembled_context += f"Content: {sec['content']}\n"
            
    return assembled_context

# --- 4. LLM SYNTHESIS ---
def ask_legal_bot(question):
    print(f"\n🧠 Analyzing legal network for: '{question}'...")
    
    # INCREASE THIS TO 10
    context = get_hybrid_context(question, top_k=10) 
    
    # ADD THIS DEBUG PRINT
    print("\n🔍 [DEBUG] Sections retrieved from Vector + Graph:")
    for line in context.split('\n'):
        if line.startswith("---"):
            print("  " + line)
            
    if not context.strip():
        return "I could not retrieve any relevant legal sections from the database."
        
    # ... rest of the function remains the same ...

    prompt = f"""You are an expert Indian Legal AI Assistant specializing in the Bharatiya Nyaya Sanhita (BNS), Bharatiya Nagarik Suraksha Sanhita (BNSS), and Bharatiya Sakshya Adhiniyam (BSA).
Answer the user's question using ONLY the provided legal context. 
If the context contains connected procedures (BNSS) or evidence rules (BSA) related to a crime (BNS), explain how they link together seamlessly.
If the exact answer is not in the context, state clearly that the provided legal text does not cover it.

Context:
{context}

Question: {question}
Answer:"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error connecting to LLM: {e}"

# --- 5. INTERACTIVE TERMINAL ---
if __name__ == "__main__":
    print("\n✅ Engine Online. Hybrid Retrieval (Vector + Graph) is active.")
    print("Type 'exit' or 'quit' to shut down the engine.")
    print("-" * 60)
    
    while True:
        user_query = input("\n⚖️ Ask a legal question: ")
        if user_query.lower() in ['exit', 'quit']:
            print("Shutting down engine. Goodbye!")
            break
            
        answer = ask_legal_bot(user_query)
        print(f"\n📜 Response:\n{answer}\n")
        print("-" * 60)