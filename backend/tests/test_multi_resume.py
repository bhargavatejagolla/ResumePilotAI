"""Unit tests for Multi-Resume Pipeline, Health Diagnostic, and Playbook."""
import io
from pathlib import Path
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app

settings = get_settings()
from app.layers.l1_storage import load_candidate, save_candidate
from app.layers.l1_parse_resume import parse_resume_pdf
from app.layers.l2_candidate import build_index, search
from app.layers.l2_health import diagnose_resume_health
from app.layers.l3_job import parse_jd
from app.layers.l4_intelligence.selector import build_plan
from app.layers.l5_generation.writer import fallback_to_plan
from app.layers.l6_verification.ats import calculate_ats_score
from app.layers.l6_verification.playbook import generate_improvement_playbook

client = TestClient(app)

SAMPLE_JD = """
Software Engineer, Systems and AI Infrastructure - Google
Responsibilities: Build high-scale microservices using Python, FastAPI, Docker, and PostgreSQL.
Requirements: Python, FastAPI, Docker, PostgreSQL, Microservices.
"""


def test_diagnose_resume_health():
    candidate = load_candidate("saketh")
    health = diagnose_resume_health(candidate)

    assert 0 <= health.overall_score <= 100
    assert 0.0 <= health.metric_density <= 1.0
    assert health.total_bullets > 0
    assert len(health.top_improvements) > 0


def test_generate_improvement_playbook():
    candidate = load_candidate("saketh")
    reqs, dna = parse_jd(SAMPLE_JD)
    plan = build_plan(candidate, reqs, dna)
    resume = fallback_to_plan(plan, reqs, dna)
    ats = calculate_ats_score(resume, reqs)
    playbook = generate_improvement_playbook(candidate, reqs, ats)

    assert playbook.current_match_percentage >= 50
    assert playbook.projected_match_percentage > playbook.current_match_percentage
    assert len(playbook.sprint_weeks) == 4
    for w in playbook.sprint_weeks:
        assert len(w.action_items) >= 2
        assert len(w.deliverable) > 5


def test_parse_resume_pdf_from_bytes():
    template_path = Path(settings.templates_dir) / "resume-template.pdf"
    if not template_path.exists():
        template_path = Path(settings.candidate_json_path).parent / "my_resume.pdf"
    assert template_path.exists(), "Template PDF not found!"

    pdf_bytes = template_path.read_bytes()
    cand = parse_resume_pdf(pdf_bytes)

    assert "Saketh" in cand.personal.name
    assert len(cand.projects) >= 2
    assert len(cand.skills) >= 2


def test_multi_user_chroma_isolation():
    cand_saketh = load_candidate("saketh")

    # Build index for two distinct IDs
    build_index(cand_saketh, resume_id="user_alpha", force_rebuild=False)
    build_index(cand_saketh, resume_id="user_beta", force_rebuild=False)

    # Search user_alpha
    hits_alpha = search("authentication", resume_id="user_alpha", top_k=3)
    for h in hits_alpha:
        assert h["metadata"]["resume_id"] == "user_alpha"

    # Search user_beta
    hits_beta = search("authentication", resume_id="user_beta", top_k=3)
    for h in hits_beta:
        assert h["metadata"]["resume_id"] == "user_beta"


def test_upload_resume_api():
    template_path = Path(settings.templates_dir) / "resume-template.pdf"
    if not template_path.exists():
        template_path = Path(settings.candidate_json_path).parent / "my_resume.pdf"

    pdf_bytes = template_path.read_bytes()
    files = {"file": ("test_resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")}

    response = client.post("/upload_resume", files=files)
    assert response.status_code == 200
    data = response.json()

    assert "resume_id" in data
    assert "candidate" in data
    assert "health_report" in data
    assert data["health_report"]["overall_score"] > 50

    # Test that /generate works with this newly uploaded resume_id
    gen_response = client.post("/generate", json={
        "jd_text": SAMPLE_JD,
        "resume_id": data["resume_id"],
        "variant": "aggressive",
    })
    assert gen_response.status_code == 200
    gen_data = gen_response.json()
    assert "pdf_base64" in gen_data
    assert "playbook" in gen_data["verification"]
