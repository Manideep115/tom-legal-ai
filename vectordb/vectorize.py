import json
import os
import chromadb
from chromadb.utils import embedding_functions

def initialize_vector_db():
    # 1. Setup Paths
    master_file = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\master_legal_v1.json"
    db_path = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\vectordb"

    if not os.path.exists(master_file):
        print(f"❌ Master file not found at: {master_file}")
        return
    
    if not os.path.exists(db_path):
        os.makedirs(db_path)

    # 2. Initialize ChromaDB
    client = chromadb.PersistentClient(path=db_path)
    
    # 3. Setup Embedding Model
    model_name = "all-MiniLM-L6-v2"
    emb_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_name)
    
    # 4. Create Collection
    collection = client.get_or_create_collection(
        name="indian_legal_acts", 
        embedding_function=emb_func,
        metadata={"hnsw:space": "cosine"}
    )

    # 5. Load Master Data
    with open(master_file, 'r', encoding='utf-8') as f:
        master_data = json.load(f)

    print(f"📦 Processing {len(master_data)} sections...")

    ids = []
    documents = []
    metadatas = []
    
    # --- DUPLICATE HANDLING LOGIC ---
    id_counts = {}

    for sec in master_data:
        raw_id = sec['uid']
        
        # If ID already exists, append a suffix
        if raw_id in id_counts:
            id_counts[raw_id] += 1
            final_id = f"{raw_id}_v{id_counts[raw_id]}"
        else:
            id_counts[raw_id] = 1
            final_id = raw_id

        ids.append(final_id)
        documents.append(sec['search_text'])
        metadatas.append({
            "act": sec['act'],
            "section": sec['section_number'],
            "title": sec['title']
        })

    # 6. Upsert in Batches
    print(f"🚀 Vectorizing and saving to: {db_path}")
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        try:
            collection.upsert(
                ids=ids[i:i + batch_size],
                documents=documents[i:i + batch_size],
                metadatas=metadatas[i:i + batch_size]
            )
            print(f"  ✅ Batched {i + len(ids[i:i + batch_size])}/{len(ids)}")
        except Exception as e:
            print(f"  ❌ Error in batch starting at {i}: {e}")
    
    print(f"\n✨ Successfully created Vector DB with {collection.count()} unique entries!")

if __name__ == "__main__":
    initialize_vector_db()