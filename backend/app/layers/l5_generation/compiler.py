"""Prompt Compiler for Phase 5 (Groq Writer).

Compiles structured prompts for rewriting resume bullets and summary drafts,
conditioned on JobRequirements, Style DNA, and deterministic ResumePlan.
"""
import json
from pathlib import Path
from typing import Dict, Any

from app.config import get_settings
from app.schemas.job import JobRequirements
from app.schemas.resume import ResumePlan

settings = get_settings()


def _load_prompt(filename: str) -> str:
    path = Path(settings.prompts_dir) / filename
    return path.read_text(encoding="utf-8")


def _format_jd_summary(reqs: JobRequirements) -> str:
    role_title = getattr(reqs, "job_title", "") or getattr(reqs, "title", "Software Engineer")
    parts = [
        f"Target Role: {role_title}",
        f"Target Company: {reqs.company_name or reqs.company_type.upper()}",
        f"Domain: {reqs.domain}",
    ]
    if reqs.required_skills:
        parts.append(f"Required Skills: {', '.join(reqs.required_skills[:12])}")
    if reqs.preferred_skills:
        parts.append(f"Preferred Skills: {', '.join(reqs.preferred_skills[:8])}")
    if reqs.responsibilities:
        parts.append("Key Responsibilities:\n  - " + "\n  - ".join(reqs.responsibilities[:5]))
    keywords = getattr(reqs, "priority_keywords", []) or getattr(reqs, "keywords", [])
    if keywords:
        parts.append(f"Priority Keywords: {', '.join(keywords[:15])}")
    return "\n".join(parts)


def _format_dna_summary(dna: dict) -> str:
    bullet_style = dna.get("bullet_style", {})
    priorities = dna.get("priorities", [])
    parts = [
        f"Tone: {dna.get('tone', 'technical, metric-driven, rigorous')}",
        f"Focus Areas: {dna.get('focus', 'engineering excellence')}",
        f"Metric Density: {bullet_style.get('metric_density', 'high')}",
        f"Bullet Word Range: {bullet_style.get('min_words', 12)} to {bullet_style.get('max_words', 22)} words",
        f"Preferred Verbs: {', '.join(bullet_style.get('action_verbs', [])[:8])}",
        f"Priorities: {', '.join(priorities) if priorities else 'impact, clarity, system ownership'}",
    ]
    return "\n".join(parts)


def _format_plan_for_prompt(plan: ResumePlan) -> str:
    data = {
        "summary": plan.summary_draft,
        "projects": [
            {
                "name": p.name,
                "tech": p.tech,
                "award": p.award,
                "bullets": [b.text for b in p.selected_bullets],
            }
            for p in plan.projects
        ],
        "experience": [
            {
                "company": e.company,
                "title": e.title,
                "bullets": [b.text for b in e.selected_bullets],
            }
            for e in plan.experience
        ],
        "skills": plan.skills,
        "achievements": [
            {
                "title": a.get("title", ""),
                "description": a.get("description", ""),
            }
            for a in plan.achievements
        ],
    }
    return json.dumps(data, indent=2)


def compile_rewrite_prompt(
    plan: ResumePlan,
    reqs: JobRequirements,
    dna: dict,
) -> str:
    """
    Compile the single comprehensive prompt for Groq Llama 3.3 70B rewrite.
    Uses safe string replacements to avoid JSON bracket conflicts.
    """
    template = _load_prompt("v1_write_resume.txt")
    bullet_style = dna.get("bullet_style", {})
    action_verbs = bullet_style.get(
        "action_verbs",
        ["Engineered", "Architected", "Spearheaded", "Built", "Optimized", "Designed", "Led"],
    )

    allowed_verbs = ", ".join(action_verbs)
    min_words = str(bullet_style.get("min_words", 12))
    max_words = str(bullet_style.get("max_words", 22))
    tone = dna.get("tone", "technical, rigorous, metric-focused")
    priorities = ", ".join(dna.get("priorities", ["high impact", "system performance"]))

    jd_summary = _format_jd_summary(reqs)
    dna_summary = _format_dna_summary(dna)
    plan_json = _format_plan_for_prompt(plan)

    prompt = (
        template
        .replace("{min_words}", min_words)
        .replace("{max_words}", max_words)
        .replace("{allowed_verbs}", allowed_verbs)
        .replace("{company_type}", reqs.company_type.upper())
        .replace("{tone}", tone)
        .replace("{priorities}", priorities)
        .replace("{jd_summary}", jd_summary)
        .replace("{dna_summary}", dna_summary)
        .replace("{plan_json_input}", plan_json)
    )

    return prompt


def compile_revision_prompt(
    current_draft: Dict[str, Any],
    revision_feedback: str,
    reqs: JobRequirements,
) -> str:
    """
    Compile the revision prompt for targeted polishing if ATS scores trigger a retry loop.
    """
    template = _load_prompt("v1_revise.txt")
    jd_summary = _format_jd_summary(reqs)
    draft_json = json.dumps(current_draft, indent=2)

    prompt = (
        template
        .replace("{revision_feedback}", revision_feedback)
        .replace("{jd_summary}", jd_summary)
        .replace("{current_draft_json}", draft_json)
    )

    return prompt
