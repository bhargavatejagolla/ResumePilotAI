"""gap.py — deterministic skill gap analysis.

Phase 3 already pre-computed `reqs.skill_evidence`. Phase 4 just
groups it into actionable buckets for the strategy and summary.
"""
from app.schemas.job import JobRequirements


def group_skills(reqs: JobRequirements) -> dict:
    """
    Bucket every required + preferred skill by status.

    Returns:
        {
            "known":    [{skill, evidence, confidence}, ...],
            "likely":   [{skill, evidence, confidence}, ...],
            "missing":  [{skill}, ...],
            "required_missing": [...],   # only from required_skills
            "coverage": 0.0-1.0,          # known / total required
        }
    """
    known, likely, missing = [], [], []
    required_missing = []

    for skill in reqs.required_skills:
        ev = reqs.skill_evidence.get(skill)
        if ev is None:
            missing.append({"skill": skill})
            required_missing.append(skill)
            continue
        entry = {
            "skill": skill,
            "evidence": ev.evidence,
            "confidence": ev.confidence,
            "matched_via": ev.matched_via,
        }
        if ev.status == "known":
            known.append(entry)
        elif ev.status == "likely":
            likely.append(entry)
        else:
            missing.append({"skill": skill})
            required_missing.append(skill)

    for skill in reqs.preferred_skills:
        ev = reqs.skill_evidence.get(skill)
        if ev is None or ev.status == "missing":
            missing.append({"skill": skill})
        elif ev.status == "known":
            known.append({
                "skill": skill,
                "evidence": ev.evidence,
                "confidence": ev.confidence,
                "matched_via": ev.matched_via,
            })
        else:
            likely.append({
                "skill": skill,
                "evidence": ev.evidence,
                "confidence": ev.confidence,
                "matched_via": ev.matched_via,
            })

    total_required = len(reqs.required_skills) or 1
    coverage = round(len(known) / total_required, 3)

    return {
        "known": known,
        "likely": likely,
        "missing": missing,
        "required_missing": required_missing,
        "coverage": coverage,
    }
