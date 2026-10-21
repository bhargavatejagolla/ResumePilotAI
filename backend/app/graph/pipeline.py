"""Phase 8 — Orchestration Pipeline using LangGraph.

Connects all layers:
Job Intelligence (L3) -> Resume Planning (L4) -> Groq Writer (L5) -> Verification (L6) -> PDF Render (L7).
Includes an automated revision feedback loop when ATS threshold is not met.
"""
from typing import TypedDict, Optional, Dict, Any, List
from langgraph.graph import StateGraph, START, END

from app.layers.l2_candidate import load_candidate
from app.layers.l3_job import parse_jd, load_dna
from app.layers.l4_intelligence.selector import build_plan
from app.layers.l5_generation.writer import rewrite_resume
from app.layers.l6_verification import verify_resume
from app.layers.l7_render import render_html, render_pdf_sync
from app.schemas.job import JobRequirements
from app.schemas.resume import ResumePlan, GeneratedResume
from app.schemas.verification import VerificationResult


class PipelineState(TypedDict, total=False):
    jd_text: str
    company_override: Optional[str]
    tone_override: Optional[str]
    reqs: Optional[JobRequirements]
    dna: Optional[Dict[str, Any]]
    plan: Optional[ResumePlan]
    resume: Optional[GeneratedResume]
    verification: Optional[VerificationResult]
    html: Optional[str]
    pdf_bytes: Optional[bytes]
    retry_count: int
    error: Optional[str]


def node_parse_job(state: PipelineState) -> Dict[str, Any]:
    """Step 1: Parse job description, classify company, load DNA."""
    jd_text = state.get("jd_text", "").strip()
    if not jd_text:
        raise ValueError("Job description cannot be empty.")

    reqs, dna = parse_jd(jd_text)

    # Apply manual overrides if specified by user
    company_override = state.get("company_override")
    if company_override and company_override.lower() in ["google", "amazon", "microsoft", "research", "startup", "generic"]:
        reqs.company_type = company_override.lower()  # type: ignore
        dna = load_dna(company_override.lower())

    tone_override = state.get("tone_override")
    if tone_override:
        dna["tone"] = tone_override

    return {"reqs": reqs, "dna": dna}


def node_plan_resume(state: PipelineState) -> Dict[str, Any]:
    """Step 2: Deterministic planning (L4) with zero hallucinations."""
    candidate = load_candidate()
    reqs = state["reqs"]
    dna = state["dna"]
    plan = build_plan(candidate, reqs, dna)
    return {"plan": plan}


def node_write_resume(state: PipelineState) -> Dict[str, Any]:
    """Step 3: Groq LLM rewrite (L5) with anti-hallucination guards."""
    plan = state["plan"]
    reqs = state["reqs"]
    dna = state["dna"]
    resume = rewrite_resume(plan, reqs, dna)
    return {"resume": resume}


def node_verify_resume(state: PipelineState) -> Dict[str, Any]:
    """Step 4: ATS breakdown, interview probability, and explainability (L6)."""
    resume = state["resume"]
    reqs = state["reqs"]
    verification = verify_resume(resume, reqs)
    return {"verification": verification}


def should_revise(state: PipelineState) -> str:
    """Conditional Edge: Retry with targeted polish if ATS score failed threshold."""
    verification = state.get("verification")
    retry_count = state.get("retry_count", 0)

    # Max 1 automated revision loop to respect latency and rate limits
    if verification and not verification.passed_threshold and retry_count < 1:
        return "revise"
    return "render"


def node_revise_resume(state: PipelineState) -> Dict[str, Any]:
    """Step 4b: Targeted revision loop if ATS keywords missed."""
    retry_count = state.get("retry_count", 0) + 1
    resume = state["resume"]
    reqs = state["reqs"]
    verification = state.get("verification")

    # In revision mode, prioritize any missing priority keywords in profile summary
    if verification and verification.ats.missing_keywords and resume:
        missing_top = verification.ats.missing_keywords[:2]
        additional_mention = f" Specialized in {' and '.join(missing_top)}."
        new_summary = resume.summary.rstrip(".") + additional_mention
        resume.summary = new_summary

    return {"resume": resume, "retry_count": retry_count}


def node_render(state: PipelineState) -> Dict[str, Any]:
    """Step 5: High-fidelity HTML & PDF rendering (L7)."""
    resume = state["resume"]
    if not resume:
        raise ValueError("Cannot render empty resume.")

    html = render_html(resume)
    pdf_bytes = render_pdf_sync(resume)
    return {"html": html, "pdf_bytes": pdf_bytes}


def build_pipeline() -> Any:
    """Construct and compile the ResumePilot StateGraph."""
    workflow = StateGraph(PipelineState)

    # Add Nodes
    workflow.add_node("parse_job", node_parse_job)
    workflow.add_node("plan_resume", node_plan_resume)
    workflow.add_node("write_resume", node_write_resume)
    workflow.add_node("verify_resume", node_verify_resume)
    workflow.add_node("revise_resume", node_revise_resume)
    workflow.add_node("render_output", node_render)

    # Add Edges
    workflow.add_edge(START, "parse_job")
    workflow.add_edge("parse_job", "plan_resume")
    workflow.add_edge("plan_resume", "write_resume")
    workflow.add_edge("write_resume", "verify_resume")

    workflow.add_conditional_edges(
        "verify_resume",
        should_revise,
        {
            "revise": "revise_resume",
            "render": "render_output",
        },
    )
    workflow.add_edge("revise_resume", "verify_resume")
    workflow.add_edge("render_output", END)

    return workflow.compile()


# Singleton compiled app
pipeline = build_pipeline()


def run_pipeline(
    jd_text: str,
    company_override: Optional[str] = None,
    tone_override: Optional[str] = None,
) -> PipelineState:
    """Convenience runner for execution."""
    initial_state: PipelineState = {
        "jd_text": jd_text,
        "company_override": company_override,
        "tone_override": tone_override,
        "retry_count": 0,
    }
    return pipeline.invoke(initial_state)
