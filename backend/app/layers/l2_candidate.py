"""L2 — Candidate Knowledge Base.

Loads candidate.json, embeds every entity, and stores them in Chroma
with structured metadata for filtered semantic search.
"""
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import get_settings
from app.schemas.candidate import Candidate
from app.services.embedding_service import embed
from app.services.chroma_service import get_collection, reset_collection

settings = get_settings()

# Metadata type tags used for filtered search
T_PROJECT     = "project"
T_EXPERIENCE  = "experience"
T_SKILL       = "skill"
T_ACHIEVEMENT = "achievement"
T_CERT        = "certification"


def _project_text(p: dict) -> str:
    """Embed: name + tech + award + all bullets."""
    parts = [
        p.get("name", ""),
        "Technologies: " + ", ".join(p.get("tech", [])),
        p.get("award", ""),
        p.get("description", ""),
    ]
    parts.extend(
        (b.get("text", "") if isinstance(b, dict) else str(b))
        for b in p.get("bullets", [])
    )
    return " | ".join(x for x in parts if x)


def _experience_text(e: dict) -> str:
    """Embed: title + company + all bullets."""
    parts = [
        f"{e.get('title', '')} at {e.get('company', '')}",
    ]
    parts.extend(
        (b.get("text", "") if isinstance(b, dict) else str(b))
        for b in e.get("bullets", [])
    )
    return " | ".join(x for x in parts if x)


def _skill_text(skill: str) -> str:
    """Skills embed as their bare name; the model handles synonymy."""
    return skill


def _achievement_text(a: dict) -> str:
    """Embed: title + description + metrics."""
    parts = [a.get("title", ""), a.get("description", "")]
    if a.get("metrics"):
        parts.append(", ".join(a.get("metrics", [])))
    return " — ".join(x for x in parts if x)


def _cert_text(c: dict) -> str:
    return f"{c.get('name', '')} by {c.get('issuer', '')}"


def _project_metadata(p: dict) -> dict:
    return {
        "type": T_PROJECT,
        "id": p.get("id", ""),
        "name": p.get("name", ""),
        "tech": ", ".join(p.get("tech", [])),
        "bullet_count": len(p.get("bullets", [])),
    }


def _experience_metadata(e: dict) -> dict:
    return {
        "type": T_EXPERIENCE,
        "id": e.get("id", ""),
        "company": e.get("company", ""),
        "title": e.get("title", ""),
        "bullet_count": len(e.get("bullets", [])),
    }


def _skill_metadata(skill: str, category: str) -> dict:
    return {
        "type": T_SKILL,
        "name": skill,
        "category": category,
    }


def _achievement_metadata(a: dict, idx: int) -> dict:
    return {
        "type": T_ACHIEVEMENT,
        "id": a.get("id", f"ach_{idx}"),
        "title": a.get("title", ""),
    }


def _cert_metadata(c: dict, idx: int) -> dict:
    return {
        "type": T_CERT,
        "id": c.get("id", f"cert_{idx}"),
        "name": c.get("name", ""),
    }


def load_candidate() -> Candidate:
    """Load and validate candidate.json from Phase 1."""
    path = Path(settings.candidate_json_path)
    if not path.exists():
        raise FileNotFoundError(
            f"candidate.json not found at {path}. Run Phase 1 first."
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    return Candidate(**raw)


def build_index(force_rebuild: bool = False) -> int:
    """
    Embed every entity in candidate.json and store in Chroma.

    Returns the number of entities indexed.
    Idempotent: safe to call on every startup.
    """
    candidate = load_candidate()

    collection = reset_collection() if force_rebuild else get_collection()

    if not force_rebuild and collection.count() > 0:
        return collection.count()

    ids: List[str] = []
    texts: List[str] = []
    metadatas: List[dict] = []

    # --- Projects ---
    for idx, p in enumerate(candidate.projects):
        p_dict = p.model_dump()
        pid = p.name.lower().replace(" ", "_")[:40] or f"proj_{idx}"
        ids.append(f"proj::{pid}")
        texts.append(_project_text(p_dict))
        metadatas.append(_project_metadata(p_dict))

    # --- Experience ---
    for idx, e in enumerate(candidate.experience):
        e_dict = e.model_dump()
        eid = f"{e.company}_{e.title}".lower().replace(" ", "_")[:40] or f"exp_{idx}"
        ids.append(f"exp::{eid}")
        texts.append(_experience_text(e_dict))
        metadatas.append(_experience_metadata(e_dict))

    # --- Skills (grouped by category) ---
    for category, skills in candidate.skills.items():
        if isinstance(skills, list):
            for skill in skills:
                sid = f"{category}::{skill.lower().replace(' ', '_')}"
                ids.append(f"skill::{sid}")
                texts.append(_skill_text(skill))
                metadatas.append(_skill_metadata(skill, category))

    # --- Achievements ---
    for idx, a in enumerate(candidate.achievements):
        a_dict = a.model_dump() if hasattr(a, "model_dump") else a
        ids.append(f"ach::{idx}")
        texts.append(_achievement_text(a_dict))
        metadatas.append(_achievement_metadata(a_dict, idx))

    # --- Certifications ---
    for idx, c in enumerate(candidate.certifications):
        c_dict = c.model_dump() if hasattr(c, "model_dump") else c
        ids.append(f"cert::{idx}")
        texts.append(_cert_text(c_dict))
        metadatas.append(_cert_metadata(c_dict, idx))

    if not ids:
        return 0

    # Batch encode
    vectors = embed(texts, batch_size=32)

    # Store in Chroma
    collection.add(
        ids=ids,
        embeddings=vectors,
        documents=texts,
        metadatas=metadatas,
    )

    return len(ids)


def search(
    query: str,
    *,
    type_filter: Optional[str] = None,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Semantic search over the candidate knowledge base.
    """
    collection = get_collection()
    query_vec = embed([query])[0]

    where = {"type": type_filter} if type_filter else None

    # Protect against asking for more results than collection size
    count = collection.count()
    if count == 0:
        return []
    actual_k = min(top_k, count)

    results = collection.query(
        query_embeddings=[query_vec],
        n_results=actual_k,
        where=where,
        include=["metadatas", "documents", "distances"],
    )

    hits: List[Dict[str, Any]] = []
    ids       = results.get("ids", [[]])[0]
    metas     = results.get("metadatas", [[]])[0]
    docs      = results.get("documents", [[]])[0]
    dists     = results.get("distances", [[]])[0]

    for i, doc_id in enumerate(ids):
        similarity = 1.0 - dists[i] if i < len(dists) else 0.0
        hits.append({
            "id": doc_id,
            "score": round(similarity, 4),
            "text": docs[i] if i < len(docs) else "",
            "metadata": metas[i] if i < len(metas) else {},
        })

    return hits


def search_multi(
    queries: List[str],
    *,
    type_filter: Optional[str] = None,
    top_k: int = 3,
) -> Dict[str, List[Dict[str, Any]]]:
    """Run multiple queries and return {query: hits}."""
    return {q: search(q, type_filter=type_filter, top_k=top_k) for q in queries}
