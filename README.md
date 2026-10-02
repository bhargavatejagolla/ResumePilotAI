# ResumePilot AI

> Deterministic, Zero-Hallucination AI Resume Intelligence & Tailoring Engine.

## Stack
- **Backend:** FastAPI, Python 3.11, Pydantic v2, Structlog
- **Frontend:** Next.js (App Router), TypeScript, Tailwind CSS
- **LLM:** Groq (`llama-3.3-70b-versatile`)
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` (Local, CPU)
- **Vector DB:** ChromaDB (Local Persistent)
- **PDF Engine:** PyMuPDF & Playwright (Headless Chromium)
- **Orchestration:** LangGraph

## Quickstart

### Backend
```bash
cd backend
python -m venv .venv
# Activate venv:
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
python -m scripts.smoke_test
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Navigate to `http://localhost:3000`.
