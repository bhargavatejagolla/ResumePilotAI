"""L2 — Candidate Knowledge Base (Multi-Resume Isolated).

Loads candidate.json (or candidate_{resume_id}.json), embeds every entity,
and stores them in Chroma with structured metadata (including resume_id)
for completely isolated multi-user semantic search.
"""
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import get_settings
from app.layers.l1_storage import load_candidate as storage_load_candidate
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
        "index": idx,
        "title": a.get("title", ""),
    }


def _cert_metadata(c: dict, idx: int) -> dict:
    return {
        "type": T_CERT,
        "index": idx,
        "name": c.get("name", ""),
    }


def load_candidate(resume_id: str = "saketh") -> Candidate:
    """Load and validate candidate profile by resume_id."""
    return storage_load_candidate(resume_id)


def build_index(
    candidate: Optional[Candidate] = None,
    resume_id: str = "saketh",
    force_rebuild: bool = False,
) -> int:
    """
    Embed every entity for the given candidate and store in Chroma with resume_id metadata.
    Idempotent and isolated per resume_id.
    """
    if candidate is None:
        candidate = load_candidate(resume_id)

    collection = reset_collection() if force_rebuild else get_collection()

    # If not forcing rebuild, check if this resume_id is already indexed
    if not force_rebuild:
        existing = collection.get(where={"resume_id": resume_id})
        if existing and existing.get("ids") and len(existing["ids"]) > 0:
            return len(existing["ids"])

    ids: List[str] = []
    texts: List[str] = []
    metadatas: List[dict] = []

    # --- Projects ---
    for idx, p in enumerate(candidate.projects):
        p_dict = p.model_dump()
        pid = p.name.lower().replace(" ", "_")[:40] or f"proj_{idx}"
        ids.append(f"{resume_id}::proj::{pid}")
        texts.append(_project_text(p_dict))
        meta = _project_metadata(p_dict)
        meta["resume_id"] = resume_id
        metadatas.append(meta)

    # --- Experience ---
    for idx, e in enumerate(candidate.experience):
        e_dict = e.model_dump()
        eid = f"{e.company}_{e.title}".lower().replace(" ", "_")[:40] or f"exp_{idx}"
        ids.append(f"{resume_id}::exp::{eid}")
        texts.append(_experience_text(e_dict))
        meta = _experience_metadata(e_dict)
        meta["resume_id"] = resume_id
        metadatas.append(meta)

    # --- Skills ---
    for category, skills in candidate.skills.items():
        if isinstance(skills, list):
            for skill in skills:
                sid = f"{category}::{skill.lower().replace(' ', '_')}"
                ids.append(f"{resume_id}::skill::{sid}")
                texts.append(_skill_text(skill))
                meta = _skill_metadata(skill, category)
                meta["resume_id"] = resume_id
                metadatas.append(meta)

    # --- Achievements ---
    for idx, a in enumerate(candidate.achievements):
        a_dict = a.model_dump() if hasattr(a, "model_dump") else a
        ids.append(f"{resume_id}::ach::{idx}")
        texts.append(_achievement_text(a_dict))
        meta = _achievement_metadata(a_dict, idx)
        meta["resume_id"] = resume_id
        metadatas.append(meta)

    # --- Certifications ---
    for idx, c in enumerate(candidate.certifications):
        c_dict = c.model_dump() if hasattr(c, "model_dump") else c
        ids.append(f"{resume_id}::cert::{idx}")
        texts.append(_cert_text(c_dict))
        meta = _cert_metadata(c_dict, idx)
        meta["resume_id"] = resume_id
        metadatas.append(meta)

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


def _build_where_clause(resume_id: Optional[str], type_filter: Optional[str]) -> Optional[dict]:
    """Helper to build Chroma where clause with optional resume_id and type_filter."""
    conditions = []
    if resume_id:
        conditions.append({"resume_id": resume_id})
    if type_filter:
        conditions.append({"type": type_filter})

    if len(conditions) == 2:
        return {"$and": conditions}
    elif len(conditions) == 1:
        return conditions[0]
    return None


def search(
    query: str,
    *,
    resume_id: Optional[str] = "saketh",
    type_filter: Optional[str] = None,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """Semantic search over the candidate knowledge base filtered by resume_id."""
    collection = get_collection()
    query_vec = embed([query])[0]
    where = _build_where_clause(resume_id, type_filter)

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
    resume_id: Optional[str] = "saketh",
    type_filter: Optional[str] = None,
    top_k: int = 3,
) -> Dict[str, List[Dict[str, Any]]]:
    """Run multiple queries and return {query: hits}."""
    return {q: search(q, resume_id=resume_id, type_filter=type_filter, top_k=top_k) for q in queries}


def search_by_embedding(
    embedding: list[float],
    *,
    resume_id: Optional[str] = "saketh",
    type_filter: Optional[str] = None,
    top_k: int = 20,
) -> list[dict]:
    """Query the collection using a pre-computed embedding filtered by resume_id."""
    collection = get_collection()
    where = _build_where_clause(resume_id, type_filter)

    count = collection.count()
    if count == 0:
        return []
    actual_k = min(top_k, count)

    results = collection.query(
        query_embeddings=[embedding],
        n_results=actual_k,
        where=where,
        include=["metadatas", "documents", "distances"],
    )

    hits = []
    ids = results.get("ids", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    docs = results.get("documents", [[]])[0]
    dists = results.get("distances", [[]])[0]

    for i, doc_id in enumerate(ids):
        sim = 1.0 - dists[i] if i < len(dists) else 0.0
        hits.append({
            "id": doc_id,
            "score": round(sim, 4),
            "text": docs[i] if i < len(docs) else "",
            "metadata": metas[i] if i < len(metas) else {},
        })
    return hits
