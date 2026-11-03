# ResumePilot AI (v5.0 Master Engine)

> **Deterministic, Zero-Hallucination AI Resume Intelligence & Tailoring Engine.**  
> Custom-tailored specifically for **Gunnam Sai Saketh Ram** (GITAM University, Grand Champion ET GenAI Hackathon 2026, IEEE 1st author).

---

## 🎯 Architecture Philosophy

Unlike generic resume generators that invent facts or produce unpredictable hallucinated content, ResumePilot AI is built upon **three foundational pillars**:

1. **Single-User Ruthless Optimization:** Your master resume (`candidate.json`) is parsed once, source-tagged down to every individual bullet point (`resume:projects[0].bullets[0]`), and embedded locally.
2. **Deterministic Python Core (Zero LLM Selection):** Project ranking, bullet scoring, section ordering, and skill gap grouping happen via pure deterministic algorithms (cosine similarity, Jaccard token overlap, recency decay, and style DNA).
3. **Anti-Hallucination Guarded Generation:** Groq Llama 3.3 70B is used exclusively as a writing compiler to polish verbs and phrasing. If an original bullet has no quantitative metric, the engine strictly rejects any fabricated numbers and preserves factual truth integrity.
4. **Guaranteed 1-Page Playwright PDF Engine:** Headless Chromium renders pixel-perfect A4/Letter PDFs with automatic PyMuPDF page-count verification and dynamic auto-fit.

---

## 🏗️ Layer-by-Layer Architecture

```
User Pastes Job Description
        │
        ▼
┌────────────────────────────────────────────────────────┐
│  Phase 3: Job Intelligence & Company Classifier (L3)   │
│  - Groq extraction / Regex fallback                    │
│  - Company DNA classification (Google/Amazon/Startup)  │
│  - 384-dim JD embedding & precomputed skill evidence   │
└────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────┐
│  Phase 4: Resume Intelligence Layer (L4 Core)          │
│  - Matcher: Cosine similarity + Jaccard + Metrics      │
│  - Gap Analysis: Known vs Likely vs Missing skills     │
│  - Strategy: DNA adaptation & project ranking          │
│  - Selector: Deterministic ResumePlan assembly         │
│  - Truth Engine: Source tag validation                 │
└────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────┐
│  Phase 5: Generation Layer (L5 Groq Writer)            │
│  - Single consolidated prompt compilation              │
│  - Anti-hallucination metric guards                    │
│  - Graceful deterministic plan fallback                │
└────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────┐
│  Phase 6: Verification & ATS Engine (L6)               │
│  - Transparent ATS Score breakdown (Keywords, Metrics) │
│  - Calibrated Interview Probability gauge              │
│  - Full Explainability audit diff & STAR talking points│
└────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────┐
│  Phase 7 & 8: LangGraph Pipeline & Playwright Render   │
│  - StateGraph orchestration with retry revision loop   │
│  - Headless Chromium 1-Page PDF generation             │
│  - REST API (FastAPI) & Interactive Next.js Frontend   │
└────────────────────────────────────────────────────────┘
```

---

## ⚡ Tech Stack (100% Free Tier Verified)

- **Backend:** FastAPI, Python 3.11, Pydantic v2, Structlog
- **Frontend:** Next.js (App Router, Turbopack), TypeScript, Tailwind CSS
- **LLM:** Groq (`llama-3.3-70b-versatile`)
- **Local Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` (Runs on CPU, 0 API cost)
- **Vector DB:** ChromaDB (Local Persistent)
- **PDF Engine:** Playwright Headless Chromium & PyMuPDF (`fitz`)
- **Orchestration:** LangGraph

---

## 🚀 Quickstart Guide

### 1. Backend Setup

```bash
cd backend
python -m venv .venv

# Activate Virtual Environment:
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install dependencies & Playwright Chromium:
pip install -r requirements.txt
playwright install chromium

# Run all 52 unit tests across layers:
pytest -v

# Start the FastAPI server:
uvicorn app.main:app --reload --port 8000
```

Backend will be active at: `http://localhost:8000` (API documentation at `http://localhost:8000/docs`).

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will be active at: `http://localhost:3000`.

### 3. Docker Compose (Single Command Run)

```bash
docker-compose up --build
```

---

## 🧪 Verification & Test Health

All 52 tests passing across all layers:
- `test_health.py` — Root service & deep health checks
- `test_l1.py` — PDF document parsing & section detection
- `test_l2.py` — ChromaDB semantic knowledge base & vector search
- `test_l3.py` — Job requirements extraction & DNA classification
- `test_l4.py` — Deterministic ResumePlan matcher, gap analysis, ranker, selector, truth guards
- `test_l5.py` — Groq rewrite compiler, anti-hallucination guards, plan fallback
- `test_l6.py` — Deterministic ATS scoring, interview probability, explainability
- `test_l7.py` — Playwright PDF rendering, HTML templating, PyMuPDF 1-page verification
- `test_l8.py` — LangGraph pipeline orchestration & FastAPI REST endpoints
