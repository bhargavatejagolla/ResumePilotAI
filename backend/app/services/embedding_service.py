from sentence_transformers import SentenceTransformer
from app.config import get_settings

settings = get_settings()
_model: SentenceTransformer | None = None


def _load():
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embedding_model)
    return _model


def embed(texts: list[str]) -> list[list[float]]:
    return _load().encode(texts, normalize_embeddings=True).tolist()


def embed_one(text: str) -> list[float]:
    return embed([text])[0]
