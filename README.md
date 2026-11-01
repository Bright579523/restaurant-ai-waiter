# 🍛 ReDi Restaurant AI Waiter

An intelligent, allergy-safe menu recommendation chatbot for **ReDi Restaurant** built with **Retrieval-Augmented Generation (RAG)**, **Hybrid Vector Search**, and **Groq LLM**.

[![Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🌟 Highlights & Key Features

- **🛡️ Allergy-Safe & Dietary Aware**: Two-tier allergen detection (strict letter-code matching + keyword checking for dairy, nuts, gluten, etc.). Supports Vegetarian and Vegan options.
- **💰 Budget-Conscious Filtering**: Precise numeric price filtering combined with semantic intent parsing.
- **🧠 Hybrid Vector Retrieval**: Combines SQL-like Boolean metadata filtering (Pandas/NumPy) with Cosine Similarity semantic ranking (`paraphrase-multilingual-MiniLM-L12-v2`).
- **🌐 Multilingual Intelligence**: Converses naturally in English, German, and Thai, translating German dish descriptions dynamically.
- **⚡ Ultra-Fast Inference**: Powered by the Groq LPU engine for instant real-time waiter responses.
- **📊 Interactive Streamlit UI**: Chat history, quick example questions, catalog filtering, and embedded original menu PDF viewer.

---

## 🏗️ System Architecture

```text
User Natural Language Query
          │
          ▼
┌────────────────────────────────────────┐
│  1. Intent Parsing (Groq LLM)          │
│  - Extracts semantic search query      │
│  - Extracts structured Pydantic filter │
│    (price, dietary, allergens, meal)   │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│  2. Hybrid Retrieval Engine            │
│  - Step 1: Boolean Metadata Filter     │
│  - Step 2: Cosine Similarity Ranking   │
│            (SentenceTransformers)      │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│  3. Response Generation (Groq RAG)     │
│  - Grounds answers in menu items       │
│  - Explains allergens & dietary safety │
│  - Matches user language automatically │
└──────────────────┬─────────────────────┘
                   │
                   ▼
       Streamlit Chat Interface
```

---

## 📁 Repository Structure

```text
Final Project/
├── raw_data/                         # Original restaurant menu document
│   └── Menu of ReDi Restaurant.pdf 
├── data_pipeline/                    # Extraction & cleaning scripts
│   ├── extract_text.py               # PDF text extractor
│   ├── extracted_menu.txt            # Raw extracted text
│   ├── generate_csv.py               # Structured CSV parser & allergen tagger
│   └── verify_csv.py                 # Dataset verification script
├── data_output/                      # Final structured dataset
│   └── redi_menu.csv                 # 157 dishes with full metadata tags
├── embeddings/                       # Vector cache builder
│   ├── build_embeddings.py           # Encodes search_text column
│   └── menu_embeddings.pkl           # Precomputed vector cache
├── search_engine/                    # Hybrid retrieval engine
│   └── search_engine.py              # Boolean mask + Cosine Similarity ranker
├── agent/                            # Conversational RAG agent
│   └── agent.py                      # Intent parser, retrieval & answer generator
├── app/                              # Streamlit application
│   └── app.py                        # Multi-tab web application
├── app.py                            # Root Streamlit entrypoint
├── report/                           # Architecture diagrams and documentation
│   ├── project_summary.md
│   ├── system_architecture.png
│   └── dashboard_home.png
├── requirements.txt                  # Python dependencies
├── .env.example                      # Template for environment variables
└── README.md
```

---

## 🛠️ Tech Stack

| Category | Technology |
|---|---|
| **Programming Language** | Python 3.10+ |
| **PDF Extraction** | `pypdf` |
| **Data Processing & Filtering** | `pandas`, `numpy` |
| **Text Embedding Model** | `paraphrase-multilingual-MiniLM-L12-v2` (`sentence-transformers`) |
| **Vector Similarity** | `scikit-learn` (Cosine Similarity) |
| **Data Serialization** | `pickle` |
| **Intent Schema Validation** | `Pydantic v2` |
| **LLM Inference** | Groq API (`qwen/qwen3.8-27b`) |
| **Web Framework** | `streamlit` |

---

## 🚀 Quick Start Guide

### 1. Clone the repository
```bash
git clone https://github.com/Bright579523/redi-restaurant-ai-waiter.git
cd redi-restaurant-ai-waiter
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Key
Create a `.env` file in the project root:
```bash
cp .env.example .env
```
Add your free Groq API key:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
```

### 4. (Optional) Rebuild Vector Cache
If you update the menu CSV, rebuild the vector cache:
```bash
python embeddings/build_embeddings.py
```

### 5. Launch the Streamlit App
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 👨‍💻 Author

**Watcharapon Anaketanaset (Bright)**  
ReDi School of Digital Integration — Final Project 2026  
GitHub: [@Bright579523](https://github.com/Bright579523)
