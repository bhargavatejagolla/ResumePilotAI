"""Deterministic ATS Scoring Engine for Phase 6.

Computes a transparent, reproducible ATS breakdown based on:
1. Keyword and required skills coverage
2. Full-text semantic similarity against JD embedding
3. Metric density across all bullets
4. Structural integrity and formatting health
"""
import re
from typing import List, Set, Tuple
from app.schemas.job import JobRequirements
from app.schemas.resume import GeneratedResume
from app.schemas.verification import ATSScoreBreakdown
from app.services.embedding_service import embed_one


def _extract_full_resume_text(resume: GeneratedResume) -> str:
    parts: List[str] = [
        resume.summary,
        resume.personal.get("name", ""),
        resume.personal.get("email", ""),
        resume.personal.get("location", ""),
    ]

    for p in resume.projects:
        parts.append(p.name)
        parts.extend(p.tech)
        for b in p.bullets:
            parts.append(b.text)

    for e in resume.experience:
        parts.append(e.company)
        parts.append(e.title)
        for b in e.bullets:
            parts.append(b.text)

    for cat_skills in resume.skills.values():
        if isinstance(cat_skills, list):
            parts.extend([str(s) for s in cat_skills])

    for a in resume.achievements:
        parts.append(a.get("title", ""))
        parts.append(a.get("description", ""))

    for c in resume.certifications:
        parts.append(c.get("name", ""))

    for ed in resume.education:
        parts.append(ed.get("institution", ""))
        parts.append(ed.get("degree", ""))
        parts.append(ed.get("field", ""))

    return " ".join(parts)


def _check_keywords(
    resume_text: str,
    target_keywords: List[str],
) -> Tuple[List[str], List[str], float]:
    """Check how many target keywords appear in the resume text."""
    if not target_keywords:
        return [], [], 100.0

    text_lower = resume_text.lower()
    matched = []
    missing = []

    for kw in target_keywords:
        kw_clean = kw.strip()
        if not kw_clean:
            continue
        # Use regex boundary where appropriate, otherwise plain substring
        kw_pattern = r"\b" + re.escape(kw_clean.lower()) + r"\b"
        if re.search(kw_pattern, text_lower):
            matched.append(kw_clean)
        elif kw_clean.lower() in text_lower:
            matched.append(kw_clean)
        else:
            missing.append(kw_clean)

    total = len(matched) + len(missing)
    score = (len(matched) / total * 100.0) if total > 0 else 100.0
    return matched, missing, round(score, 1)


def _calculate_metric_density(resume: GeneratedResume) -> float:
    total_bullets = 0
    metric_bullets = 0

    for p in resume.projects:
        for b in p.bullets:
            total_bullets += 1
            if b.has_metric:
                metric_bullets += 1

    for e in resume.experience:
        for b in e.bullets:
            total_bullets += 1
            if b.has_metric:
                metric_bullets += 1

    if total_bullets == 0:
        return 0.0

    ratio = metric_bullets / total_bullets
    # 65% metric density is considered optimal (100 ATS score)
    score = min(100.0, (ratio / 0.65) * 100.0)
    return round(score, 1)


def _calculate_structure_score(resume: GeneratedResume) -> float:
    score = 100.0

    # Summary checks
    words = len(resume.summary.split()) if resume.summary else 0
    if not resume.summary:
        score -= 20.0
    elif not (15 <= words <= 120):
        score -= 10.0

    # Project checks
    if len(resume.projects) < 2:
        score -= 15.0
    elif len(resume.projects) > 4:
        score -= 5.0

    # Experience check
    if not resume.experience:
        score -= 15.0

    # Skills check
    if not resume.skills or len(resume.skills) < 2:
        score -= 15.0

    # Contact check
    personal = resume.personal or {}
    if not personal.get("email") or "@" not in personal.get("email", ""):
        score -= 10.0
    if not personal.get("phone"):
        score -= 5.0

    return max(0.0, round(score, 1))


def _calculate_semantic_similarity(
    resume_text: str,
    jd_embedding: List[float],
) -> float:
    if not jd_embedding or len(jd_embedding) == 0:
        return 80.0

    try:
        resume_emb = embed_one(resume_text[:3000])
        dot = sum(a * b for a, b in zip(resume_emb, jd_embedding))
        # Cosine for domain-matched text typically sits in 0.40 - 0.85
        normalized = (dot - 0.35) / 0.45
        scaled = max(0.0, min(100.0, normalized * 100.0))
        return round(scaled, 1)
    except Exception:
        return 80.0


def calculate_ats_score(
    resume: GeneratedResume,
    reqs: JobRequirements,
) -> ATSScoreBreakdown:
    """Calculate the full deterministic ATS score and sub-scores."""
    resume_text = _extract_full_resume_text(resume)

    # Keywords pool: required skills + priority keywords
    keyword_pool = list(dict.fromkeys(reqs.required_skills + reqs.priority_keywords))
    matched, missing, kw_score = _check_keywords(resume_text, keyword_pool)

    # Semantic similarity
    sem_score = _calculate_semantic_similarity(resume_text, reqs.jd_embedding)

    # Metric density
    met_score = _calculate_metric_density(resume)

    # Structural health
    struct_score = _calculate_structure_score(resume)

    # Weighted composite total: 35% keywords + 30% semantic + 20% metrics + 15% structure
    total = (
        0.35 * kw_score
        + 0.30 * sem_score
        + 0.20 * met_score
        + 0.15 * struct_score
    )

    return ATSScoreBreakdown(
        total_score=round(total, 1),
        keyword_match_score=kw_score,
        semantic_similarity_score=sem_score,
        metric_density_score=met_score,
        structure_score=struct_score,
        matched_keywords=matched,
        missing_keywords=missing,
    )
