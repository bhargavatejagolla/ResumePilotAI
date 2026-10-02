from fastapi import APIRouter
from app.services.embedding_service import embed_one
from app.services.groq_service import chat

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/health/deep")
def deep_health():
    """Verifies Groq + embeddings are wired correctly."""
    emb = embed_one("test")
    try:
        groq_reply = chat("Reply with the single word: pong")
    except Exception as e:
        groq_reply = f"error: {str(e)}"
        
    return {
        "status": "ok",
        "embedding_dim": len(emb),
        "groq_reply": groq_reply.strip()[:60],
    }


@router.get("/")
def root():
    return {
        "service": "ResumePilot AI",
        "version": "0.1.0",
        "docs": "/docs",
    }
