"""Embedding service — Phase 2 upgrade.

Uses all-MiniLM-L6-v2 (384-dim, CPU-friendly, ~80 MB).
Normalizes all outputs so Chroma's cosine space is exact.
"""
from sentence_transformers import SentenceTransformer
from app.config import get_settings

settings = get_settings()
_model: SentenceTransformer | None = None


def _load() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embedding_model)
    return _model


def embed(texts: list[str], batch_size: int = 32) -> list[list[float]]:
    """Batch-encode texts with L2 normalization.

    normalize_embeddings=True ensures dot product == cosine similarity,
    which is what Chroma's hnsw:space='cosine' expects.
    """
    if not texts:
        return []
    model = _load()
    vectors = model.encode(
        texts,
        batch_size=batch_size,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return vectors.tolist()


def embed_one(text: str) -> list[float]:
    return embed([text])[0]


def embedding_dim() -> int:
    return _load().get_sentence_embedding_dimension()
