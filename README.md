# CodeRAG: Event-Driven Codebase Assistant

CodeRAG is a secure, containerized Retrieval-Augmented Generation (RAG) pipeline designed to analyze and chat with local software repositories. It features an idempotent ingestion engine, real-time filesystem syncing, and LPU-accelerated inference.

## 🚀 Key Features
* **Live Filesystem Sync:** A background worker detects code saves and automatically updates the vector space.
* **Idempotent Ingestion:** SQLite hash tracking ensures unmodified files are never redundantly embedded.
* **AST-Aware Chunking:** Uses `tree-sitter` to parse code logically, preserving functions and classes rather than blindly splitting text.
* **API Security & Rate Limiting:** Endpoints are locked behind custom headers and protected against spam.
* **Containerized Architecture:** Fully decoupled UI, API, and Vector Database running on Docker networks.

## 🛠️ Tech Stack
* **Backend:** FastAPI, Python, Docker
* **AI/RAG:** LangChain, ChromaDB, Groq API (Llama 3.1), Ollama (Local Embeddings)
* **Infrastructure:** SQLite (Caching), Watchdog (Event Monitoring), SlowAPI (Rate Limiting)
* **Frontend:** Streamlit

## ⚙️ Local Setup
1. Clone the repo.
2. Create a `.env` file with your `API_KEY` (Groq) and `BACKEND_API_KEY` (Custom).
3. Run `docker-compose up --build` to spin up the API, DB, and UI.
4. Run `python src/watcher.py` locally to start the live-sync worker.
