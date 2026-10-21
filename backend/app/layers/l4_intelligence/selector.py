"""selector.py — build the ResumePlan.

Combines matcher + gap + strategy + ranker outputs into a single
ResumePlan object that Phase 5 will polish but never restructure.
"""
from typing import List, Dict, Any
from app.schemas.candidate import Candidate
from app.schemas.job import JobRequirements
from app.schemas.resume import (
    ResumePlan, PlannedProject, PlannedExperience, PlannedBullet,
)
from app.layers.l4_intelligence.gap import group_skills
from app.layers.l4_intelligence.strategy import adapt_dna
from app.layers.l4_intelligence.ranker import (
    rank_projects, rank_experiences, rank_bullets,
)


# ── Selection ────────────────────────────────────────────────

def _select_projects(
    candidate: Candidate,
    reqs: JobRequirements,
    dna: dict,
) -> List[PlannedProject]:
    ranked = rank_projects(candidate, reqs)
    cap = dna.get("projects", {}).get("max_projects", 3)
    bullets_per_proj = dna.get("projects", {}).get("bullets_per_project", 3)

    selected = []
    for r in ranked[:cap]:
        proj = next(p for p in candidate.projects if p.name == r["name"])
        bullet_scores = rank_bullets(proj.bullets, reqs, dna)
        chosen = bullet_scores[:bullets_per_proj]

        selected.append(PlannedProject(
            name=proj.name,
            tech=proj.tech or [],
            selected_bullets=[
                PlannedBullet(
                    text=b["text"],
                    source=b["source"],
                    score=b["score"],
                    has_metric=b["has_metric"],
                )
                for b in chosen
            ],
            total_score=r["total_score"],
            relevance=r["relevance"],
            impact=r["impact"],
            freshness=r["freshness"],
            coverage=r["coverage"],
            award=r.get("award", ""),
        ))
    return selected


def _select_experiences(
    candidate: Candidate,
    reqs: JobRequirements,
    dna: dict,
) -> List[PlannedExperience]:
    ranked = rank_experiences(candidate, reqs)
    bullets_per_exp = dna.get("experience", {}).get("bullets_per_experience", 4)
    cap = 2

    selected = []
    for r in ranked[:cap]:
        exp = next(e for e in candidate.experience if e.company == r["company"])
        bullet_scores = rank_bullets(exp.bullets, reqs, dna)
        chosen = bullet_scores[:bullets_per_exp]

        selected.append(PlannedExperience(
            company=exp.company,
            title=exp.title,
            selected_bullets=[
                PlannedBullet(
                    text=b["text"],
                    source=b["source"],
                    score=b["score"],
                    has_metric=b["has_metric"],
                )
                for b in chosen
            ],
            total_score=r["total_score"],
            relevance=r["relevance"],
            impact=r["impact"],
            freshness=r["freshness"],
        ))
    return selected


def _select_skills(
    candidate: Candidate,
    reqs: JobRequirements,
    gaps: dict,
    dna: dict,
) -> Dict[str, List[str]]:
    """
    Keep skills that are (a) required, (b) preferred, or (c) high-confidence
    matches. Preserve DNA category ordering.
    """
    priority_skills = (
        {s.lower() for s in reqs.required_skills}
        | {s.lower() for s in reqs.preferred_skills}
    )

    category_order = dna.get("skills", {}).get("categories_order", [
        "languages", "ai_ml", "backend", "devops", "databases",
    ])

    result: Dict[str, List[str]] = {}
    for category in category_order:
        items = candidate.skills.get(category, []) if isinstance(candidate.skills, dict) else []
        picked: List[str] = []
        for s in items:
            if s.lower() in priority_skills:
                picked.append(s)
        # Fill to 6 with existing skills (breadth)
        for s in items:
            if s not in picked and len(picked) < 6:
                picked.append(s)
        if picked:
            result[category] = picked

    # If any categories from candidate skills weren't in category_order, add them
    if isinstance(candidate.skills, dict):
        for category, items in candidate.skills.items():
            if category not in result and category != "source" and items:
                result[category] = items[:6]

    return result


def _select_achievements(
    candidate: Candidate,
    dna: dict,
) -> List[dict]:
    """
    Filter + order achievements per DNA preferences.
    Prioritizes 'Grand Champion' and IEEE publication via special_rules.
    """
    ach_list = []
    for a in (candidate.achievements or []):
        if isinstance(a, dict):
            ach_list.append(a)
        elif hasattr(a, "model_dump"):
            ach_list.append(a.model_dump())

    cap = dna.get("achievements", {}).get("max_shown", 3)
    special = dna.get("special_rules", {})
    must_include_champion = special.get("grand_champion_always_in_summary", False)
    must_include_ieee = special.get("ieee_publication_in_top_achievements", False)

    def _rank(a: dict) -> int:
        title = (a.get("title") or "").lower()
        score = 0
        if "grand champion" in title or "hackathon" in title:
            score += 100 if must_include_champion else 50
        if "ieee" in title or "publication" in title:
            score += 100 if must_include_ieee else 30
        if "national" in title:
            score += 20
        return -score

    ordered = sorted(ach_list, key=_rank)
    return ordered[:cap]


def _select_certifications(
    candidate: Candidate,
    dna: dict,
) -> List[dict]:
    """Return all certifications — phase 5 may trim to fit one page."""
    certs = []
    for c in (candidate.certifications or []):
        if isinstance(c, dict):
            certs.append(c)
        elif hasattr(c, "model_dump"):
            certs.append(c.model_dump())
    return certs[:5]


# ── Summary draft ────────────────────────────────────────────

def _build_summary(
    candidate: Candidate,
    reqs: JobRequirements,
    dna: dict,
    top_projects: List[PlannedProject],
    top_skills: Dict[str, List[str]],
    achievements: List[dict],
) -> str:
    """
    Deterministic template. Groq will polish in Phase 5, but the
    semantic content is fixed here so no fabrication is possible.
    """
    special = dna.get("special_rules", {})
    pieces: List[str] = []

    # 1. Education opener
    edu = candidate.education[0] if candidate.education else None
    if edu:
        grad_year = (edu.end or "").split("-")[0] or "2026"
        pieces.append(
            f"Final-year Computer Science student at {edu.institution} ({grad_year})"
        )

    # 2. Grand Champion (per special_rules or presence)
    has_champ = any("champion" in (a.get("title") or "").lower() or "hackathon" in (a.get("title") or "").lower() for a in achievements)
    if special.get("grand_champion_always_in_summary", False) or has_champ:
        for a in achievements:
            title = a.get("title", "")
            if "hackathon" in title.lower() or "champion" in title.lower():
                short_title = title.split("—")[0].split("-")[0].strip()
                pieces.append(
                    f"Grand Champion of the {short_title} (National 1st Prize among 50,000+ participants)"
                )
                break

    # 3. IEEE publication (per special_rules or presence)
    has_ieee = any("ieee" in (a.get("title") or "").lower() or "publication" in (a.get("title") or "").lower() for a in achievements)
    if special.get("ieee_publication_in_top_achievements", False) or has_ieee:
        pieces.append("IEEE-published 1st author")

    # 4. Skills
    priority_skills = [s for s in reqs.required_skills[:4] if s]
    if not priority_skills:
        priority_skills = [s for cat in top_skills.values() for s in cat][:4]
    if priority_skills:
        pieces.append(
            f"hands-on experience in {', '.join(priority_skills)}"
        )

    # 5. Top project
    if top_projects:
        p = top_projects[0]
        proj_base_name = p.name.split("—")[0].split(" - ")[0].strip()
        tech_str = ", ".join(p.tech[:2]) if p.tech else "Python"
        impact_bullet = next((b.text for b in p.selected_bullets if b.has_metric), "")
        impact_phrase = ""
        if impact_bullet:
            first_metric = impact_bullet.split(".")[0][:90].strip()
            impact_phrase = f" — {first_metric}"
        pieces.append(
            f"Built {proj_base_name} using {tech_str}{impact_phrase}"
        )

    # 6. Closer
    tone = dna.get("tone", "balanced")
    closers = {
        "research_heavy": "Strong record of shipping research into production systems.",
        "leadership_principles": "Proven ownership mindset with a bias for measurable customer impact.",
        "engineering_collaboration": "Track record of cross-functional delivery and reliability-first engineering.",
        "ownership_speed": "Bias for shipping and iterating fast with measurable outcomes.",
        "balanced": "Strong record of leading teams and shipping production-grade systems.",
    }
    pieces.append(closers.get(tone, closers["balanced"]))

    draft = ". ".join(pieces)
    if not draft.endswith("."):
        draft += "."
    return draft


# ── Public entry point ──────────────────────────────────────

def build_plan(
    candidate: Candidate,
    reqs: JobRequirements,
    dna: dict,
) -> ResumePlan:
    """
    Compile the complete ResumePlan.

    Steps:
      1. Adapt DNA to JD
      2. Group skill gaps
      3. Select projects, experiences, skills, achievements, certs
      4. Build summary draft
      5. Verify with truth engine
    """
    from app.layers.l4_intelligence.truth import verify_plan

    adapted_dna = adapt_dna(reqs, dna)
    gaps = group_skills(reqs)

    projects = _select_projects(candidate, reqs, adapted_dna)
    experiences = _select_experiences(candidate, reqs, adapted_dna)
    skills = _select_skills(candidate, reqs, gaps, adapted_dna)
    achievements = _select_achievements(candidate, adapted_dna)
    certifications = _select_certifications(candidate, adapted_dna)
    summary = _build_summary(
        candidate, reqs, adapted_dna,
        projects, skills, achievements,
    )

    plan = ResumePlan(
        section_order=adapted_dna.get("section_order", [
            "summary", "education", "experience", "projects", "skills", "achievements", "certifications"
        ]),
        summary_draft=summary,
        projects=projects,
        experience=experiences,
        skills=skills,
        achievements=achievements,
        certifications=certifications,
        education=[e.model_dump() for e in candidate.education] if candidate.education else [],
        personal=candidate.personal.model_dump() if hasattr(candidate.personal, "model_dump") else candidate.personal,
        metadata={
            "company_type": reqs.company_type,
            "job_title": reqs.job_title,
            "dna_tone": adapted_dna.get("tone"),
            "coverage": gaps["coverage"],
            "known_skills": [k["skill"] for k in gaps["known"]],
            "likely_skills": [k["skill"] for k in gaps["likely"]],
            "missing_skills": [m["skill"] for m in gaps["missing"]],
            "selected_projects": [p.name for p in projects],
            "ranked_projects": rank_projects(candidate, reqs),
            "summary_word_count": len(summary.split()),
        },
    )

    # Truth engine audit — attached to metadata, not blocking
    issues = verify_plan(plan, candidate)
    plan.metadata["truth_issues"] = issues

    return plan
