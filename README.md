Here is the fully formatted Markdown code.

**To use this:** Click the small "Copy" icon in the top-right corner of the dark box below, then paste it directly into the GitHub edit box.


# ⚖️ AI Lawyer Pro: Hybrid GraphRAG Legal Assistant

AI Lawyer Pro is a deterministic Legal AI system designed to analyze First Information Reports (FIRs) using the newly enacted Indian criminal laws:

- **Bharatiya Nyaya Sanhita (BNS)**
- **Bharatiya Nagarik Suraksha Sanhita (BNSS)**
- **Bharatiya Sakshya Adhiniyam (BSA)**

Unlike standard LLM-based applications, this system implements a **Hybrid GraphRAG Architecture** that combines semantic retrieval and graph-based reasoning to deliver **accurate, explainable, and non-hallucinated legal outputs**.

---

## 🚀 Key Features

### 🔹 Hybrid Retrieval System
- Combines:
  - **Vector Search (ChromaDB)** for semantic understanding
  - **GraphRAG (NetworkX)** for relational reasoning
- Graph contains:
  - **1,143 Nodes**
  - **1,864 Edges**
- Enables **multi-hop legal reasoning**

### 🔹 Deterministic LLM Behavior
- Uses **Temperature = 0.0** (Zero-Creativity Mode)
- Enforces:
  - No guessing
  - No hallucinated sections
- Outputs are strictly grounded in retrieved data

### 🔹 Dual-Fallback OCR Pipeline
- Handles both:
  - Text-based PDFs
  - Scanned FIR documents
- Pipeline:
  1. `pdfplumber` (primary extraction)
  2. `pytesseract + pdf2image` (fallback OCR)

### 🔹 Structured JSON Output
- LLM outputs follow a strict schema
- Enables:
  - Reliable downstream processing
  - Direct integration with visualization layer

### 🔹 Interactive Visualization Dashboard
Built using **Plotly + Streamlit**:
- 📍 Timeline Analysis (Scatter Plot)
- ⚠️ Risk Severity Gauge
- 📊 Section Impact Analysis

### 🔹 Explainable AI
- Every response is backed by:
  - Retrieved legal sections
  - Structured reasoning
- Improves trust and transparency

---

## 🧠 System Architecture


User Query
   ↓
Vector Search (ChromaDB)
   ↓
Graph Traversal (NetworkX)
   ↓
Context Filtering
   ↓
LLM (Deterministic Mode)
   ↓
Structured JSON Output
   ↓
Visualization (Plotly)





## 🛠️ Technology Stack

### 🔹 Frontend

* Streamlit
* Custom CSS (Flexbox)

### 🔹 Backend / AI

* OpenRouter API (Llama 3.1)
* SentenceTransformers (`all-MiniLM-L6-v2`)

### 🔹 Databases

* ChromaDB (Vector DB)
* NetworkX (Graph Engine)

### 🔹 Data Processing

* pdfplumber
* pytesseract
* pdf2image

### 🔹 Visualization

* Plotly Express
* Plotly Graph Objects
* Pandas

---

## 📂 Project Structure


├── data/
│   ├── master_legal_v1.json      # Structured legal dataset (BNS, BNSS, BSA)
│   └── legal_graph.json          # Graph relationships
│
├── vectordb/                     # ChromaDB embeddings
│
├── frontend/
│   └── pages/
│       └── 2_tom_deep_dashboard.py   # Main Streamlit app
│
├── requirements.txt
├── packages.txt                  # System dependencies (OCR)
└── README.md



## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone [https://github.com/Mamideep115/tom-legal-ai.git](https://github.com/Mamideep115/tom-legal-ai.git)
cd tom-legal-ai

```

### 2. Install System Dependencies (OCR)

**Windows:**
Install [Tesseract-OCR](https://www.google.com/search?q=https://github.com/UB-Mannheim/tesseract/wiki) and [Poppler](https://github.com/oschwartz10612/poppler-windows). Add their `/bin` paths to your system environment variables.

**Linux (Debian/Ubuntu):**

```bash
sudo apt-get install tesseract-ocr poppler-utils

```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt

```

### 4. Set Environment Variables

Create a `.env` file:

```env
OPENROUTER_API_KEY=your_api_key_here

```

### 5. Run the Application

```bash
streamlit run frontend/pages/2_tom_deep_dashboard.py

```

---

## ⚡ Key Engineering Decisions

### 🔸 Why Hybrid GraphRAG?

* **Vector search alone:** Finds relevant laws, but ❌ cannot model relationships.
* **GraphRAG:** Enables multi-hop reasoning and captures strict legal dependencies across different Acts.

### 🔸 Why Deterministic LLM?

* Legal systems require Absolute Accuracy and Reproducibility.
* **Temperature = 0** ensures there is no randomness and no fabricated outputs.

### 🔸 Why OCR Fallback?

* Real-world FIRs are often scanned images. Without an OCR layer, the system fails. A dual pipeline ensures maximum robustness.

---

## 🚧 Challenges Faced

| Problem | Solution |
| --- | --- |
| **Incomplete datasets** | Switched to official legal texts |
| **Scanned PDFs** | OCR fallback pipeline |
| **Hallucination** | Deterministic prompts + validation |
| **Weak retrieval** | Reranking + GraphRAG |
| **Output inconsistency** | Strict JSON schema |

---

## 🏁 Final Capabilities

* 📄 FIR analysis using modern Indian laws.
* 🔗 Semantic + relational legal reasoning.
* 🛡️ Deterministic, non-hallucinated outputs.
* 📈 Structured insights + interactive visualizations.
* ⚖️ A fully Explainable AI system.

---

## 🔮 Future Improvements

* Hybrid search (BM25 + semantic).
* Migration to newer legal updates.
* Graph expansion for deeper reasoning.
* UI enhancements.

---

## 🎯 Final Statement

This project transforms a standard RAG pipeline into a Hybrid GraphRAG system by integrating semantic retrieval, graph-based reasoning, and deterministic LLM constraints to build a reliable and explainable Legal AI assistant.

---

### 👨‍💻 Author

**ALUR MANIDEEP** Developed as part of an advanced AI/ML project focused on real-world legal intelligence systems at VIT-AP University.
