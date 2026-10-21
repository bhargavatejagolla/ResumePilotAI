"""Groq Writer for Phase 5.

Executes a single consolidated LLM call to polish the ResumePlan,
enforcing strict truthfulness, anti-hallucination metric guards, and seamless fallback.
"""
import logging
from typing import Dict, Any, List, Optional

from app.layers.l4_intelligence.matcher import has_metric
from app.layers.l5_generation.compiler import compile_rewrite_prompt
from app.schemas.job import JobRequirements
from app.schemas.resume import (
    ResumePlan,
    GeneratedResume,
    GeneratedProject,
    GeneratedExperience,
    RewrittenBullet,
)
from app.services import groq_service

logger = logging.getLogger(__name__)


def fallback_to_plan(
    plan: ResumePlan,
    reqs: Optional[JobRequirements] = None,
    dna: Optional[dict] = None,
    reason: str = "",
) -> GeneratedResume:
    """
    Construct a valid GeneratedResume directly from the deterministic ResumePlan.
    Invoked when Groq API is unavailable, unconfigured, or returns invalid output.
    """
    change_log: List[Dict[str, Any]] = []

    # Map projects
    projects: List[GeneratedProject] = []
    for p in plan.projects:
        bullets: List[RewrittenBullet] = []
        for b in p.selected_bullets:
            bullets.append(
                RewrittenBullet(
                    text=b.text,
                    original_text=b.text,
                    source=b.source,
                    score=b.score,
                    has_metric=b.has_metric,
                    is_rewritten=False,
                )
            )
            change_log.append({
                "entity": p.name,
                "source": b.source,
                "original": b.text,
                "rewritten": b.text,
                "changed": False,
                "type": "project_bullet",
            })
        projects.append(
            GeneratedProject(
                name=p.name,
                tech=p.tech,
                bullets=bullets,
                award=p.award,
            )
        )

    # Map experience
    experience: List[GeneratedExperience] = []
    for e in plan.experience:
        bullets = []
        for b in e.selected_bullets:
            bullets.append(
                RewrittenBullet(
                    text=b.text,
                    original_text=b.text,
                    source=b.source,
                    score=b.score,
                    has_metric=b.has_metric,
                    is_rewritten=False,
                )
            )
            change_log.append({
                "entity": e.company,
                "source": b.source,
                "original": b.text,
                "rewritten": b.text,
                "changed": False,
                "type": "experience_bullet",
            })
        experience.append(
            GeneratedExperience(
                company=e.company,
                title=e.title,
                start=e.start,
                end=e.end,
                location=e.location,
                bullets=bullets,
            )
        )

    meta = dict(plan.metadata)
    meta.update({
        "is_fallback": True,
        "fallback_reason": reason,
        "change_log": change_log,
        "total_bullets_rewritten": 0,
        "total_bullets_checked": len(change_log),
    })

    return GeneratedResume(
        personal=plan.personal,
        summary=plan.summary_draft,
        original_summary=plan.summary_draft,
        section_order=plan.section_order,
        projects=projects,
        experience=experience,
        skills=plan.skills,
        achievements=plan.achievements,
        certifications=plan.certifications,
        education=plan.education,
        metadata=meta,
    )


def rewrite_resume(
    plan: ResumePlan,
    reqs: JobRequirements,
    dna: dict,
    groq_svc: Any = None,
) -> GeneratedResume:
    """
    Takes a deterministic ResumePlan and rewrites bullet points and summary
    using Groq Llama 3.3 70B, checking anti-hallucination guards.
    """
    svc = groq_svc or groq_service

    # Check for placeholder or missing API key
    api_key = getattr(svc, "settings", None)
    key_val = getattr(api_key, "groq_api_key", "") if api_key else ""
    if not key_val or "your_actual_key_here" in key_val:
        logger.info("Groq API key not configured. Using deterministic plan fallback.")
        return fallback_to_plan(plan, reqs, dna, reason="Groq API key not configured")

    try:
        prompt = compile_rewrite_prompt(plan, reqs, dna)
        raw_response = svc.chat_json(prompt)
    except Exception as exc:
        logger.warning("Groq call failed during resume rewrite: %s. Falling back to plan.", exc)
        return fallback_to_plan(plan, reqs, dna, reason=str(exc))

    if not isinstance(raw_response, dict):
        logger.warning("Groq returned non-dict JSON response. Falling back to plan.")
        return fallback_to_plan(plan, reqs, dna, reason="Non-dict response from Groq")

    change_log: List[Dict[str, Any]] = []

    # 1. Summary rewrite
    rewritten_summary = raw_response.get("summary", "")
    summary_words = len(rewritten_summary.split()) if isinstance(rewritten_summary, str) else 0
    if isinstance(rewritten_summary, str) and 10 <= summary_words <= 120:
        final_summary = rewritten_summary.strip()
    else:
        final_summary = plan.summary_draft

    summary_changed = (final_summary.strip() != plan.summary_draft.strip())
    change_log.append({
        "entity": "Profile Summary",
        "source": "resume:summary",
        "original": plan.summary_draft,
        "rewritten": final_summary,
        "changed": summary_changed,
        "type": "summary",
    })

    # 2. Projects rewrite
    groq_projects = raw_response.get("projects", [])
    if not isinstance(groq_projects, list):
        groq_projects = []

    generated_projects: List[GeneratedProject] = []
    for p_idx, plan_proj in enumerate(plan.projects):
        # Match project from Groq output by name or index
        matched_gp = None
        for gp in groq_projects:
            if isinstance(gp, dict) and gp.get("name", "").strip().lower() == plan_proj.name.strip().lower():
                matched_gp = gp
                break
        if not matched_gp and p_idx < len(groq_projects) and isinstance(groq_projects[p_idx], dict):
            matched_gp = groq_projects[p_idx]

        groq_bullets = matched_gp.get("bullets", []) if matched_gp else []
        if not isinstance(groq_bullets, list):
            groq_bullets = []

        proj_bullets: List[RewrittenBullet] = []
        for b_idx, orig_b in enumerate(plan_proj.selected_bullets):
            cand_text = ""
            if b_idx < len(groq_bullets) and isinstance(groq_bullets[b_idx], str):
                cand_text = groq_bullets[b_idx].strip()

            final_text = orig_b.text
            was_rewritten = False
            rejection_reason = ""

            if cand_text and cand_text != orig_b.text:
                # Anti-hallucination check: If original had NO metric, candidate must not invent one
                if not orig_b.has_metric and has_metric(cand_text):
                    rejection_reason = "metric hallucination rejected"
                    final_text = orig_b.text
                    was_rewritten = False
                elif len(cand_text.split()) < 5:
                    rejection_reason = "bullet too short"
                    final_text = orig_b.text
                    was_rewritten = False
                else:
                    final_text = cand_text
                    was_rewritten = True

            proj_bullets.append(
                RewrittenBullet(
                    text=final_text,
                    original_text=orig_b.text,
                    source=orig_b.source,
                    score=orig_b.score,
                    has_metric=has_metric(final_text),
                    is_rewritten=was_rewritten,
                )
            )

            change_log.append({
                "entity": plan_proj.name,
                "source": orig_b.source,
                "original": orig_b.text,
                "rewritten": final_text,
                "changed": was_rewritten,
                "type": "project_bullet",
                "rejection": rejection_reason,
            })

        generated_projects.append(
            GeneratedProject(
                name=plan_proj.name,
                tech=plan_proj.tech,
                bullets=proj_bullets,
                award=plan_proj.award,
            )
        )

    # 3. Experience rewrite
    groq_exp = raw_response.get("experience", [])
    if not isinstance(groq_exp, list):
        groq_exp = []

    generated_exp: List[GeneratedExperience] = []
    for e_idx, plan_exp in enumerate(plan.experience):
        matched_ge = None
        for ge in groq_exp:
            if isinstance(ge, dict) and ge.get("company", "").strip().lower() in plan_exp.company.strip().lower():
                matched_ge = ge
                break
        if not matched_ge and e_idx < len(groq_exp) and isinstance(groq_exp[e_idx], dict):
            matched_ge = groq_exp[e_idx]

        groq_exp_bullets = matched_ge.get("bullets", []) if matched_ge else []
        if not isinstance(groq_exp_bullets, list):
            groq_exp_bullets = []

        exp_bullets: List[RewrittenBullet] = []
        for b_idx, orig_b in enumerate(plan_exp.selected_bullets):
            cand_text = ""
            if b_idx < len(groq_exp_bullets) and isinstance(groq_exp_bullets[b_idx], str):
                cand_text = groq_exp_bullets[b_idx].strip()

            final_text = orig_b.text
            was_rewritten = False
            rejection_reason = ""

            if cand_text and cand_text != orig_b.text:
                if not orig_b.has_metric and has_metric(cand_text):
                    rejection_reason = "metric hallucination rejected"
                    final_text = orig_b.text
                    was_rewritten = False
                elif len(cand_text.split()) < 5:
                    rejection_reason = "bullet too short"
                    final_text = orig_b.text
                    was_rewritten = False
                else:
                    final_text = cand_text
                    was_rewritten = True

            exp_bullets.append(
                RewrittenBullet(
                    text=final_text,
                    original_text=orig_b.text,
                    source=orig_b.source,
                    score=orig_b.score,
                    has_metric=has_metric(final_text),
                    is_rewritten=was_rewritten,
                )
            )

            change_log.append({
                "entity": plan_exp.company,
                "source": orig_b.source,
                "original": orig_b.text,
                "rewritten": final_text,
                "changed": was_rewritten,
                "type": "experience_bullet",
                "rejection": rejection_reason,
            })

        generated_exp.append(
            GeneratedExperience(
                company=plan_exp.company,
                title=plan_exp.title,
                start=plan_exp.start,
                end=plan_exp.end,
                location=plan_exp.location,
                bullets=exp_bullets,
            )
        )

    meta = dict(plan.metadata)
    meta.update({
        "is_fallback": False,
        "change_log": change_log,
        "total_bullets_rewritten": sum(1 for c in change_log if c.get("changed")),
        "total_bullets_checked": len(change_log),
    })

    return GeneratedResume(
        personal=plan.personal,
        summary=final_summary,
        original_summary=plan.summary_draft,
        section_order=plan.section_order,
        projects=generated_projects,
        experience=generated_exp,
        skills=plan.skills,
        achievements=plan.achievements,
        certifications=plan.certifications,
        education=plan.education,
        metadata=meta,
    )
