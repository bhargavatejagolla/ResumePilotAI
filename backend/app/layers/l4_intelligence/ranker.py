"""ranker.py — combine matcher scores into final rankings.

Runs on every project/experience. No LLM. No randomness.
"""
import re
from typing import Tuple, Optional, List, Dict, Any
from app.schemas.candidate import Candidate
from app.schemas.job import JobRequirements
from app.layers.l4_intelligence.matcher import (
    score_projects, score_experiences, score_bullets,
    count_metrics,
)


# ── Freshness ────────────────────────────────────────────────

def _parse_year_month(s: Optional[str]) -> Optional[Tuple[int, int]]:
    if not s:
        return None
    m = re.search(r"(\d{4})[-/](\d{1,2})", s.strip())
    if m:
        return int(m.group(1)), int(m.group(2))
    m2 = re.search(r"(\d{1,2})[-/](\d{4})", s.strip())
    if m2:
        return int(m2.group(2)), int(m2.group(1))
    return None


def _freshness(end_date: Optional[str]) -> float:
    """
    Freshness in [0, 1]:
      - Ongoing (no end_date) → 1.0
      - Ended N years ago → 1 / (1 + N)
      - Unparseable → 0.5 (neutral)
    """
    if not end_date:
        return 1.0
    ym = _parse_year_month(end_date)
    if ym is None:
        return 0.5
    # Reference baseline (2025-08)
    ref_year, ref_month = 2025, 8
    years = max(0.0, (ref_year - ym[0]) + (ref_month - ym[1]) / 12.0)
    return round(1.0 / (1.0 + years), 3)


# ── Impact ───────────────────────────────────────────────────

def _impact(bullets: list) -> int:
    return sum(count_metrics(b.text if hasattr(b, "text") else b.get("text", ""))
               for b in bullets)


# ── Coverage (required-skill hit rate) ───────────────────────

def _coverage(project_or_exp: Any, reqs: JobRequirements) -> float:
    text = " ".join([
        getattr(project_or_exp, "name", "") or "",
        getattr(project_or_exp, "title", "") or "",
        getattr(project_or_exp, "company", "") or "",
        " ".join(getattr(project_or_exp, "tech", []) or []),
        " ".join(
            b.text if hasattr(b, "text") else b.get("text", "")
            for b in getattr(project_or_exp, "bullets", []) or []
        ),
    ]).lower()

    if not reqs.required_skills:
        return 0.0
    hits = sum(1 for skill in reqs.required_skills if skill.lower() in text)
    return round(hits / len(reqs.required_skills), 3)


# ── Public ranking functions ─────────────────────────────────

def rank_projects(candidate: Candidate, reqs: JobRequirements) -> List[Dict[str, Any]]:
    """
    Final project ranking:
      total = 0.50·relevance + 0.20·impact + 0.10·freshness
            + 0.15·coverage + 0.05·award_bonus
    """
    matches = score_projects(candidate, reqs)
    ranked = []

    for m in matches:
        proj = next((p for p in candidate.projects
                     if p.name == m["name"]), None)
        if proj is None:
            continue

        impact = _impact(proj.bullets)
        impact_norm = min(impact / 5.0, 1.0)
        fresh = _freshness(getattr(proj, "end", "") or "")
        cov = _coverage(proj, reqs)
        award_bonus = 0.05 if m.get("award") else 0.0

        total = (
            0.50 * m["relevance"]
            + 0.20 * impact_norm
            + 0.10 * fresh
            + 0.15 * cov
            + award_bonus
        )

        ranked.append({
            "name": proj.name,
            "relevance": m["relevance"],
            "impact": impact,
            "impact_norm": round(impact_norm, 3),
            "freshness": fresh,
            "coverage": cov,
            "award": m.get("award", ""),
            "total_score": round(total, 4),
        })

    return sorted(ranked, key=lambda x: -x["total_score"])


def rank_experiences(candidate: Candidate, reqs: JobRequirements) -> List[Dict[str, Any]]:
    """
    Final experience ranking:
      total = 0.60·relevance + 0.20·impact + 0.20·freshness
    """
    matches = score_experiences(candidate, reqs)
    ranked = []

    for m in matches:
        exp = next((e for e in candidate.experience
                    if e.company == m["company"]), None)
        if exp is None:
            continue

        impact = _impact(exp.bullets)
        impact_norm = min(impact / 5.0, 1.0)
        fresh = _freshness(getattr(exp, "end", "") or "")

        total = 0.60 * m["relevance"] + 0.20 * impact_norm + 0.20 * fresh
        ranked.append({
            "company": exp.company,
            "relevance": m["relevance"],
            "impact": impact,
            "impact_norm": round(impact_norm, 3),
            "freshness": fresh,
            "total_score": round(total, 4),
        })

    return sorted(ranked, key=lambda x: -x["total_score"])


def rank_bullets(
    bullets: list,
    reqs: JobRequirements,
    dna: dict,
) -> List[Dict[str, Any]]:
    """Pass-through to matcher.score_bullets — kept here for API symmetry."""
    return score_bullets(bullets, reqs, dna)
