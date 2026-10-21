"""strategy.py — adapt the base DNA based on JD specifics.

The base DNA (Phase 3) is a good default. This module applies
small, deliberate overrides based on the actual JD contents.

Never modifies the original dna dict — returns a deep copy.
"""
import copy


_SCALE_TRIGGERS = {
    "distributed", "scale", "scale-up", "high-throughput", "petabyte",
    "million", "billion", "low-latency", "real-time",
}

_LEADERSHIP_TRIGGERS = {
    "lead", "led", "mentor", "manage", "ownership", "drive", "director",
}

_RESEARCH_TRIGGERS = {
    "publication", "paper", "novel", "research", "phd", "neurips", "icml",
    "iclr", "cvpr", "acl",
}


def adapt_dna(reqs, base_dna: dict) -> dict:
    """
    Return a DNA dict with JD-specific overrides applied.
    """
    dna = copy.deepcopy(base_dna)

    # Keyword set from the JD
    kw_text = " ".join(
        reqs.required_skills + reqs.preferred_skills
        + reqs.priority_keywords + reqs.tools_technologies
    ).lower()

    # ── Scale emphasis ───────────────────────────────
    if any(w in kw_text for w in _SCALE_TRIGGERS):
        dna.setdefault("projects", {})["emphasize_scale"] = True

    # ── Leadership emphasis ──────────────────────────
    if any(w in kw_text for w in _LEADERSHIP_TRIGGERS):
        dna.setdefault("experience", {})["emphasize_leadership"] = True

    # ── Research emphasis ────────────────────────────
    if any(w in kw_text for w in _RESEARCH_TRIGGERS):
        dna["tone"] = "research_heavy"
        dna.setdefault("achievements", {})["prefer"] = ["research", "national"]

    # ── Missing-skill pressure ───────────────────────
    missing = [s for s in reqs.required_skills
               if reqs.skill_evidence.get(s, None)
               and reqs.skill_evidence[s].status == "missing"]
    if len(missing) >= 3:
        dna.setdefault("summary", {})["emphasize_breadth"] = True

    # ── Project cap — Saketh only has 3 projects ─────
    dna.setdefault("projects", {})["max_projects"] = 3

    # ── Bullet cap — never exceed what's available ───
    dna.setdefault("projects", {})
    dna["projects"]["bullets_per_project"] = min(
        dna["projects"].get("bullets_per_project", 3), 4
    )

    return dna
