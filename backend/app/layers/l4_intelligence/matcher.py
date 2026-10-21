"""matcher.py — the only Phase 4 file that touches embeddings.

Rule: projects are scored using reqs.jd_embedding against Phase 2's
       pre-stored project embeddings (no re-embedding).
       Bullets are scored using reqs.jd_embedding against freshly-
       embedded bullet texts (cached in-process, ~10 ms for 15 bullets).
"""
import re
from typing import List, Dict, Set, Any
from app.schemas.candidate import Candidate
from app.schemas.job import JobRequirements
from app.services.embedding_service import embed_one
from app.layers.l2_candidate import search_by_embedding

# ── Keyword extraction (for jaccard) ──────────────────────────

_STOPWORDS = {
    "with", "using", "for", "and", "the", "to", "a", "an", "of", "in",
    "on", "by", "via", "as", "that", "this", "is", "are", "was", "were",
    "from", "which", "also", "or", "at", "be", "been", "has", "have",
}

_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9+#/\-]{1,}")


def _keywords_from(text: str) -> Set[str]:
    return {
        t.lower()
        for t in _TOKEN.findall(text)
        if len(t) >= 2 and t.lower() not in _STOPWORDS
    }


# ── Metric detection ─────────────────────────────────────────

_METRIC_PATTERNS = [
    r"\d+\.?\d*%",
    r"[₹$]\s?\d[\d,]*",
    r"\d[\d,]*\s?([KkMm]\b|INR|CR\b)",
    r"\d+\.?\d*\s?(ms|s|sec|min|h|hours?|dB)\b",
    r"\d+\.?\d*\s?(SSIM|PSNR)\b",
    r"\d+\s?[x×]\s?\d+",
    r"\d+\+",
    r"\d+[\s\-]line",
    r"\d+\s+(images|classes|users|requests|tests|models|APIs|agents|"
    r"pages|dimensions|metrics|pesticides|languages|participants|prize)",
]

_METRIC_RE = re.compile("|".join(_METRIC_PATTERNS), re.IGNORECASE)


def has_metric(text: str) -> bool:
    return bool(_METRIC_RE.search(text))


def count_metrics(text: str) -> int:
    return len(_METRIC_RE.findall(text))


# ── Verb strength ────────────────────────────────────────────

_STRONG_VERBS = {
    "built", "designed", "engineered", "developed", "created", "implemented",
    "optimized", "trained", "shipped", "launched", "led", "owned", "drove",
    "delivered", "scaled", "architected", "improved", "reduced", "increased",
    "achieved", "published", "analyzed", "evaluated", "integrated",
    "deployed", "containerized", "automated",
}


def _first_verb(text: str) -> str:
    m = re.match(r"\s*([A-Za-z]+)", text)
    return m.group(1).lower() if m else ""


def verb_strength(text: str) -> float:
    v = _first_verb(text)
    return 1.0 if v in _STRONG_VERBS else 0.5


# ── Project & experience scoring ────────────────────────────

def _project_keywords(proj: Any) -> Set[str]:
    text = " ".join([
        proj.name,
        " ".join(proj.tech or []),
        " ".join(b.text if hasattr(b, "text") else b.get("text", "") for b in proj.bullets),
    ])
    return _keywords_from(text)


def _jd_keywords(reqs: JobRequirements) -> Set[str]:
    return _keywords_from(" ".join(
        reqs.required_skills
        + reqs.priority_keywords
        + reqs.tools_technologies
        + reqs.preferred_skills
    ))


def score_projects(candidate: Candidate, reqs: JobRequirements) -> List[Dict[str, Any]]:
    """
    Score every project in the candidate's resume against the JD.

    Returns list of {name, relevance, cosine, jaccard, award}.
    Ordered by relevance descending.
    """
    hits = search_by_embedding(
        reqs.jd_embedding, type_filter="project", top_k=20
    ) if reqs.jd_embedding else []

    hit_scores: Dict[str, float] = {}
    for hit in hits:
        name = hit["metadata"].get("name", "")
        if name:
            hit_scores[name.strip().lower()] = hit["score"]

    jd_kw = _jd_keywords(reqs)
    results = []

    for proj in candidate.projects:
        cosine = hit_scores.get(proj.name.strip().lower(), 0.0)
        if cosine == 0.0:
            for h_name, h_score in hit_scores.items():
                if h_name in proj.name.lower() or proj.name.lower() in h_name:
                    cosine = max(cosine, h_score)

        proj_kw = _project_keywords(proj)
        intersection = len(jd_kw & proj_kw)
        union = len(jd_kw | proj_kw) or 1
        jaccard = intersection / union

        relevance = 0.7 * cosine + 0.3 * jaccard
        award = ""

        # Award bonus (e.g., Grand Champion projects)
        for ach in (candidate.achievements or []):
            ach_dict = ach if isinstance(ach, dict) else (ach.model_dump() if hasattr(ach, "model_dump") else {})
            desc = ach_dict.get("description", "")
            title = ach_dict.get("title", "")
            if proj.name.lower() in desc.lower() or (getattr(proj, "award", None) and proj.award):
                award = title or getattr(proj, "award", "")
                relevance = min(relevance + 0.10, 1.0)
                break

        results.append({
            "name": proj.name,
            "relevance": round(relevance, 4),
            "cosine": round(cosine, 4),
            "jaccard": round(jaccard, 4),
            "award": award,
        })

    return sorted(results, key=lambda x: -x["relevance"])


def score_experiences(candidate: Candidate, reqs: JobRequirements) -> List[Dict[str, Any]]:
    """Same pattern as score_projects, for experiences."""
    hits = search_by_embedding(
        reqs.jd_embedding, type_filter="experience", top_k=10
    ) if reqs.jd_embedding else []

    hit_scores: Dict[str, float] = {}
    for hit in hits:
        comp = hit["metadata"].get("company", "")
        if comp:
            hit_scores[comp.strip().lower()] = hit["score"]

    jd_kw = _jd_keywords(reqs)
    results = []

    for exp in candidate.experience:
        cosine = hit_scores.get(exp.company.strip().lower(), 0.0)
        if cosine == 0.0:
            for h_comp, h_score in hit_scores.items():
                if h_comp in exp.company.lower() or exp.company.lower() in h_comp:
                    cosine = max(cosine, h_score)

        exp_text = " ".join([exp.title, exp.company] +
                            [b.text if hasattr(b, "text") else b.get("text", "") for b in exp.bullets])
        exp_kw = _keywords_from(exp_text)
        jaccard = len(jd_kw & exp_kw) / max(len(jd_kw | exp_kw), 1)

        relevance = 0.7 * cosine + 0.3 * jaccard
        results.append({
            "company": exp.company,
            "relevance": round(relevance, 4),
            "cosine": round(cosine, 4),
            "jaccard": round(jaccard, 4),
        })

    return sorted(results, key=lambda x: -x["relevance"])


# ── Bullet scoring ───────────────────────────────────────────

_bullet_emb_cache: Dict[str, List[float]] = {}


def _bullet_emb(text: str) -> List[float]:
    if text not in _bullet_emb_cache:
        _bullet_emb_cache[text] = embed_one(text)
    return _bullet_emb_cache[text]


def _cosine(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def score_bullet(
    bullet_text: str,
    reqs: JobRequirements,
    dna: dict,
) -> float:
    """
    Bullet-level score = 0.50·cosine + 0.25·metric + 0.15·verb + 0.10·length_fit
    """
    b_emb = _bullet_emb(bullet_text)
    cosine = _cosine(b_emb, reqs.jd_embedding) if reqs.jd_embedding else 0.5

    metric = 1.0 if has_metric(bullet_text) else 0.0
    verb = verb_strength(bullet_text)

    word_count = len(bullet_text.split())
    lo, hi = dna.get("projects", {}).get("bullet_length", [16, 28])
    if lo <= word_count <= hi:
        length_fit = 1.0
    else:
        distance = min(abs(word_count - lo), abs(word_count - hi))
        length_fit = max(0.0, 1.0 - distance / 10.0)

    return round(
        0.50 * cosine + 0.25 * metric + 0.15 * verb + 0.10 * length_fit,
        4,
    )


def score_bullets(
    bullets: list,
    reqs: JobRequirements,
    dna: dict,
) -> List[Dict[str, Any]]:
    """
    Score every bullet in a project/experience.
    Returns list of {text, source, score, has_metric} sorted descending.
    """
    scored = []
    for b in bullets:
        text = b.text if hasattr(b, "text") else b["text"]
        source = b.source if hasattr(b, "source") else b["source"]
        scored.append({
            "text": text,
            "source": source,
            "score": score_bullet(text, reqs, dna),
            "has_metric": has_metric(text),
        })
    return sorted(scored, key=lambda x: -x["score"])
