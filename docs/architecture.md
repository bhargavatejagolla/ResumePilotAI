# ResumePilot AI – Architecture Overview

## 1. System Pipeline
```
┌────────────────────────────────────────────────────────────────┐
│                    Next.js Frontend (Vercel)                  │
│           Upload JD · Preview · Download PDF                  │
└────────────────────────────────────────────────────────────────┘
                            │  HTTPS
                            ▼
┌────────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Render Free Tier)               │
│                                                                │
│  Layer 1 · Document Intelligence (offline, once)               │
│  Layer 2 · Candidate Intelligence (Chroma in-memory / local)   │
│  Layer 3 · Job Intelligence (Groq JD + Company DNA)           │
│  Layer 4 · Resume Intelligence (Deterministic Match & Rank)    │
│  Layer 5 · Generation (Prompt Compiler + Groq Writer)          │
│  Layer 6 · Verification (Deterministic ATS + Prob + Explain)   │
│  Layer 7 · Rendering (Jinja2 + Playwright -> PDF)              │
│  Layer 8 · Memory (SQLite history + feedback)                  │
└────────────────────────────────────────────────────────────────┘
```

## 2. Core Decisions
- Single-user hyper-tailored profile (Saketh)
- Groq (`llama-3.3-70b-versatile`)
- Local Embeddings (`sentence-transformers/all-MiniLM-L6-v2`)
- Local Chroma Vector DB
- Playwright Headless PDF rendering
