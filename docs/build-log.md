# ResumePilot AI – Build Log

## Phase 0: Foundation Setup (Completed)
- [x] Initialized monorepo with `backend/` and `frontend/`
- [x] Pinned Python requirements and verified Python 3.11 virtual environment
- [x] Implemented Core Service Wrappers:
  - `groq_service.py` (Llama 3.3 70B Versatile, JSON mode with fallback)
  - `embedding_service.py` (`all-MiniLM-L6-v2` local embedding generator)
  - `chroma_service.py` (`PersistentClient` vector storage with cosine distance)
- [x] Setup FastAPI App with structured logging, CORS, and health endpoints (`/health`, `/health/deep`)
- [x] Setup prompt templates and company DNA profiles (Google, Amazon, Microsoft, Research, Startup, Generic)
- [x] Created Jinja2 template + print-ready CSS
- [x] Scaffolding Next.js App Router frontend with TypeScript and Tailwind CSS
