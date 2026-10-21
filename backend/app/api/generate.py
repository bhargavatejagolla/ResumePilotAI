"""FastAPI API Endpoints for ResumePilot AI.

Provides REST endpoints for:
- Multi-user resume PDF upload, layout parsing, and health diagnosis
- End-to-end resume generation via LangGraph pipeline (with resume_id & variant)
- Direct PDF and HTML rendering
- On-demand ATS, interview probability, and 30-day playbook verification
- Candidate profile inspection
"""
import base64
import uuid
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Response, UploadFile, File
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.graph.pipeline import run_pipeline
from app.layers.l1_parse_resume import parse_resume_pdf
from app.layers.l1_storage import save_candidate, load_candidate, list_saved_resumes
from app.layers.l2_candidate import build_index
from app.layers.l2_health import diagnose_resume_health, ResumeHealthReport
from app.layers.l3_job import parse_jd
from app.layers.l6_verification import verify_resume
from app.layers.l7_render import render_html, render_pdf_sync
from app.schemas.resume import GeneratedResume
from app.schemas.verification import VerificationResult

router = APIRouter(tags=["generation"])


class GenerateRequest(BaseModel):
    jd_text: str = Field(..., min_length=20, description="Full job description text")
    resume_id: Optional[str] = Field("saketh", description="ID of the resume profile to tailor")
    variant: Optional[str] = Field("balanced", description="Generation variant: balanced, aggressive, conservative")
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


class UploadResumeResponse(BaseModel):
    resume_id: str
    candidate: Dict[str, Any]
    health_report: ResumeHealthReport
    message: str


class VerifyRequest(BaseModel):
    resume: GeneratedResume
    jd_text: str
    resume_id: Optional[str] = "saketh"


@router.get("/profile")
@router.get("/profile/{resume_id}")
def get_candidate_profile(resume_id: str = "saketh"):
    """Retrieve candidate profile (defaults to Saketh's master profile)."""
    try:
        candidate = load_candidate(resume_id)
        return candidate.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Candidate not found: {str(exc)}")


@router.get("/resumes")
def get_all_resumes():
    """List all stored candidate resumes."""
    return list_saved_resumes()


@router.get("/health-report/{resume_id}", response_model=ResumeHealthReport)
def get_resume_health_report(resume_id: str = "saketh"):
    """Retrieve pre-generation health diagnostic for any resume."""
    try:
        candidate = load_candidate(resume_id)
        return diagnose_resume_health(candidate)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Candidate not found: {str(exc)}")


@router.post("/upload_resume", response_model=UploadResumeResponse)
@router.post("/api/upload_resume", response_model=UploadResumeResponse)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload any PDF resume.
    Parses layout & sections, indexes in Chroma under resume_id, and computes pre-generation health audit.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        pdf_bytes = await file.read()
        if len(pdf_bytes) < 500:
            raise HTTPException(status_code=400, detail="Invalid or empty PDF file.")

        resume_id = str(uuid.uuid4())[:8]

        # 1. Parse PDF to structured Candidate model
        candidate = parse_resume_pdf(pdf_bytes)

        # 2. Persist in storage
        save_candidate(resume_id, candidate, pdf_bytes)

        # 3. Index entities in Chroma tagged with resume_id
        build_index(candidate, resume_id=resume_id, force_rebuild=True)

        # 4. Generate Pre-Generation Health Report
        health_report = diagnose_resume_health(candidate)

        return UploadResumeResponse(
            resume_id=resume_id,
            candidate=candidate.model_dump(),
            health_report=health_report,
            message="Resume parsed, indexed, and diagnosed successfully.",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to process uploaded resume: {str(exc)}")


@router.post("/generate", response_model=GenerateResponse)
@router.post("/api/generate", response_model=GenerateResponse)
def generate_resume(req: GenerateRequest):
    """
    Execute full end-to-end pipeline for any resume_id and any JD:
    Parse JD -> Deterministic Plan -> Groq Rewrite -> ATS Verification -> 1-Page PDF.
    """
    try:
        state = run_pipeline(
            jd_text=req.jd_text,
            resume_id=req.resume_id or "saketh",
            variant=req.variant or "balanced",
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
        cand = load_candidate(req.resume_id or "saketh")
        return verify_resume(req.resume, reqs, candidate=cand)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(exc)}")
