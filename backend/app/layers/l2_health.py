"""Resume Health Diagnostic Engine (Upgrade #2).

Provides an instant, deterministic diagnostic assessment of any candidate resume
BEFORE job description tailoring. Evaluates metric density, verb power, skill grounding,
and produces prioritized recommendations to coach the candidate.
"""
import re
from typing import List, Dict, Any, Set
from pydantic import BaseModel, Field

from app.layers.l4_intelligence.matcher import has_metric
from app.schemas.candidate import Candidate


WEAK_VERBS = {
    "worked", "helped", "assisted", "did", "participated",
    "involved", "responsible", "handled", "tried", "supported",
    "made", "used", "utilized", "contributed", "learned",
}

STRONG_VERBS_SUGGESTIONS = [
    "Architected", "Engineered", "Spearheaded", "Optimized",
    "Pioneered", "Automated", "Delivered", "Scaled", "Designed",
]


class WeakVerbOccurrence(BaseModel):
    verb: str
    bullet_snippet: str
    location: str


class ResumeHealthReport(BaseModel):
    overall_score: int = Field(default=0, ge=0, le=100)
    metric_density: float = Field(default=0.0, ge=0.0, le=1.0)
    total_bullets: int = 0
    metric_bullets_count: int = 0
    weak_verbs_count: int = 0
    weak_verbs: List[WeakVerbOccurrence] = Field(default_factory=list)
    unevidenced_skills: List[str] = Field(default_factory=list)
    project_count: int = 0
    experience_count: int = 0
    top_improvements: List[str] = Field(default_factory=list)


def diagnose_resume_health(candidate: Candidate) -> ResumeHealthReport:
    """Run deterministic pre-generation health audit on a candidate profile."""
    all_bullets: List[tuple[str, str]] = []  # (location, text)

    # Collect project bullets
    for p_i, p in enumerate(candidate.projects):
        p_name = p.name or f"Project {p_i+1}"
        for b in p.bullets:
            b_text = b.text if hasattr(b, "text") else str(b)
            all_bullets.append((p_name, b_text))

    # Collect experience bullets
    for e_i, e in enumerate(candidate.experience):
        c_name = e.company or f"Experience {e_i+1}"
        for b in e.bullets:
            b_text = b.text if hasattr(b, "text") else str(b)
            all_bullets.append((c_name, b_text))

    total_bullets = len(all_bullets)
    metric_bullets_count = sum(1 for _, text in all_bullets if has_metric(text))
    metric_ratio = (metric_bullets_count / max(total_bullets, 1))

    # 2. Check for weak opening verbs
    weak_occurrences: List[WeakVerbOccurrence] = []
    for loc, text in all_bullets:
        words = re.findall(r"[A-Za-z]+", text.strip())
        if words:
            first_word = words[0].lower()
            if first_word in WEAK_VERBS:
                snippet = text[:70] + ("..." if len(text) > 70 else "")
                weak_occurrences.append(
                    WeakVerbOccurrence(
                        verb=first_word.capitalize(),
                        bullet_snippet=snippet,
                        location=loc,
                    )
                )

    # 3. Check for unevidenced skills
    # Combine project and experience text into a corpus
    body_corpus = " ".join(t for _, t in all_bullets).lower()
    all_skills_flat: Set[str] = set()
    if isinstance(candidate.skills, dict):
        for cat, s_list in candidate.skills.items():
            if isinstance(s_list, list):
                for s in s_list:
                    if str(s).strip():
                        all_skills_flat.add(str(s).strip())

    unevidenced: List[str] = []
    for s in all_skills_flat:
        s_clean = s.lower()
        # Look for skill in body text
        if not re.search(r"\b" + re.escape(s_clean) + r"\b", body_corpus):
            unevidenced.append(s)

    # 4. Calculate overall score (0 to 100)
    # Metric component: up to 35 points (target 0.65 density)
    metric_pts = min(35.0, (metric_ratio / 0.65) * 35.0)

    # Verb power component: up to 25 points (deduct 4 pts per weak verb)
    verb_pts = max(5.0, 25.0 - len(weak_occurrences) * 4.0)

    # Skill grounding component: up to 20 points (deduct 3 pts per ungrounded skill)
    skill_pts = max(5.0, 20.0 - min(len(unevidenced), 5) * 3.0)

    # Structural completeness: up to 20 points
    struct_pts = 0.0
    if candidate.personal.email and "@" in candidate.personal.email:
        struct_pts += 5.0
    if len(candidate.projects) >= 2:
        struct_pts += 5.0
    if candidate.experience:
        struct_pts += 5.0
    if candidate.education:
        struct_pts += 5.0

    overall_score = int(round(metric_pts + verb_pts + skill_pts + struct_pts))
    overall_score = max(20, min(100, overall_score))

    # 5. Prioritized top improvements
    improvements: List[str] = []
    if metric_ratio < 0.60:
        improvements.append(
            f"Increase quantified metrics: only {metric_bullets_count}/{total_bullets} bullets have numbers or percentages. Target at least 65%."
        )

    if weak_occurrences:
        top_weak = weak_occurrences[0]
        improvements.append(
            f"Replace weak verb '{top_weak.verb}' in {top_weak.location} with high-impact power verbs like 'Architected', 'Spearheaded', or 'Engineered'."
        )

    if unevidenced:
        top_unev = ", ".join(unevidenced[:3])
        improvements.append(
            f"Provide evidence in your project bullets for listed skills: {top_unev}."
        )

    if not improvements:
        improvements.append("Solid resume baseline! Proceed with target JD synthesis to tailor keyword alignment.")

    return ResumeHealthReport(
        overall_score=overall_score,
        metric_density=round(metric_ratio, 2),
        total_bullets=total_bullets,
        metric_bullets_count=metric_bullets_count,
        weak_verbs_count=len(weak_occurrences),
        weak_verbs=weak_occurrences[:5],
        unevidenced_skills=unevidenced[:8],
        project_count=len(candidate.projects),
        experience_count=len(candidate.experience),
        top_improvements=improvements,
    )
