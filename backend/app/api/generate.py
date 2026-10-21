"""FastAPI API Endpoints for ResumePilot AI.

Provides REST endpoints for:
- End-to-end resume generation via LangGraph pipeline
- Direct PDF and HTML rendering
- On-demand ATS and interview verification
- Master candidate profile inspection
"""
import base64
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.graph.pipeline import run_pipeline
from app.layers.l2_candidate import load_candidate
from app.layers.l3_job import parse_jd
from app.layers.l6_verification import verify_resume
from app.layers.l7_render import render_html, render_pdf_sync
from app.schemas.resume import GeneratedResume
from app.schemas.verification import VerificationResult

router = APIRouter(tags=["generation"])


class GenerateRequest(BaseModel):
    jd_text: str = Field(..., min_length=20, description="Full job description text")
    company_override: Optional[str] = Field(None, description="Force company type: google, amazon, microsoft, startup, research, generic")
    tone_override: Optional[str] = Field(None, description="Tone override: metric_heavy, technical, leadership, balanced")


class GenerateResponse(BaseModel):
    job: Dict[str, Any]
    dna: Dict[str, Any]
    plan: Dict[str, Any]
    resume: Dict[str, Any]
    verification: Dict[str, Any]
    html: str
    pdf_base64: str


class VerifyRequest(BaseModel):
    resume: GeneratedResume
    jd_text: str


@router.get("/profile")
def get_master_profile():
    """Retrieve Saketh's master profile from candidate.json."""
    candidate = load_candidate()
    return candidate.model_dump()


@router.post("/generate", response_model=GenerateResponse)
@router.post("/api/generate", response_model=GenerateResponse)
def generate_resume(req: GenerateRequest):
    """
    Execute full end-to-end pipeline:
    Parse JD -> Deterministic Plan -> Groq Rewrite -> ATS Verification -> 1-Page PDF.
    """
    try:
        state = run_pipeline(
            jd_text=req.jd_text,
            company_override=req.company_override,
            tone_override=req.tone_override,
        )

        job_data = state["reqs"].model_dump() if state.get("reqs") else {}
        dna_data = state.get("dna") or {}
        plan_data = state["plan"].model_dump() if state.get("plan") else {}
        resume_data = state["resume"].model_dump() if state.get("resume") else {}
        verification_data = state["verification"].model_dump() if state.get("verification") else {}
        html_str = state.get("html") or ""
        pdf_bytes = state.get("pdf_bytes") or b""
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8") if pdf_bytes else ""

        return GenerateResponse(
            job=job_data,
            dna=dna_data,
            plan=plan_data,
            resume=resume_data,
            verification=verification_data,
            html=html_str,
            pdf_base64=pdf_b64,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(exc)}")


@router.post("/render-pdf")
@router.post("/api/render-pdf")
def export_pdf(resume: GeneratedResume):
    """Render and download the current resume as an A4 single-page PDF."""
    try:
        pdf_bytes = render_pdf_sync(resume)
        name_clean = resume.personal.get("name", "Resume").replace(" ", "_")
        filename = f"{name_clean}_Resume.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF rendering failed: {str(exc)}")


@router.post("/render-html", response_class=HTMLResponse)
@router.post("/api/render-html", response_class=HTMLResponse)
def export_html(resume: GeneratedResume):
    """Render self-contained HTML with inlined CSS for frontend preview."""
    try:
        return render_html(resume)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"HTML rendering failed: {str(exc)}")


@router.post("/verify", response_model=VerificationResult)
@router.post("/api/verify", response_model=VerificationResult)
def run_verification(req: VerifyRequest):
    """On-demand ATS and interview probability verification."""
    try:
        reqs, _ = parse_jd(req.jd_text)
        return verify_resume(req.resume, reqs)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(exc)}")
