"""Unit tests for Phase 8 (LangGraph Pipeline & FastAPI Endpoints)."""
import base64
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

SAMPLE_JD = """
Software Engineer, Distributed Systems - Google
Bengaluru, India

Responsibilities:
- Build high-scale distributed backend systems and asynchronous microservices.
- Optimize machine learning pipelines for latency, SSIM/PSNR accuracy, and memory footprint.
- Collaborate with engineering leads to design production-grade REST and RPC services.

Qualifications:
- Bachelor's degree in Computer Science or equivalent.
- Experience with Python, PyTorch, FastAPI, Docker, and distributed systems.
- Experience with RAG, vector search, or database performance optimization.
"""


def test_get_master_profile():
    r = client.get("/profile")
    assert r.status_code == 200
    data = r.json()
    assert "Saketh" in data["personal"]["name"]
    assert len(data["projects"]) == 3
    assert len(data["experience"]) == 1


def test_generate_endpoint_e2e():
    r = client.post("/generate", json={"jd_text": SAMPLE_JD})
    assert r.status_code == 200
    data = r.json()

    # Verify all layers returned
    assert "job" in data
    assert "dna" in data
    assert "plan" in data
    assert "resume" in data
    assert "verification" in data
    assert "html" in data
    assert "pdf_base64" in data

    # Verify Job
    assert data["job"]["company_type"] == "google"

    # Verify Plan
    assert len(data["plan"]["projects"]) == 3

    # Verify Verification
    assert data["verification"]["ats"]["total_score"] >= 60.0
    assert data["verification"]["interview_prob"]["percentage"] >= 60

    # Verify PDF Base64
    pdf_bytes = base64.b64decode(data["pdf_base64"])
    assert len(pdf_bytes) > 10000
    assert pdf_bytes.startswith(b"%PDF-")


def test_render_html_endpoint():
    # First generate a resume
    gen_res = client.post("/generate", json={"jd_text": SAMPLE_JD})
    assert gen_res.status_code == 200
    resume_obj = gen_res.json()["resume"]

    # Now render html
    html_res = client.post("/render-html", json=resume_obj)
    assert html_res.status_code == 200
    assert "<!DOCTYPE html>" in html_res.text
    assert "GUNNAM SAI SAKETH RAM" in html_res.text


def test_render_pdf_endpoint():
    gen_res = client.post("/generate", json={"jd_text": SAMPLE_JD})
    assert gen_res.status_code == 200
    resume_obj = gen_res.json()["resume"]

    pdf_res = client.post("/render-pdf", json=resume_obj)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 10000
    assert pdf_res.content.startswith(b"%PDF-")
