"""Unit tests for Phase 7 (Playwright PDF & HTML Rendering)."""
import os
import fitz
import pytest

from app.layers.l2_candidate import load_candidate
from app.layers.l3_job import parse_jd
from app.layers.l4_intelligence.selector import build_plan
from app.layers.l5_generation.writer import fallback_to_plan
from app.layers.l7_render import render_html, render_pdf_sync


SAMPLE_JD = """
Software Engineer, Distributed Systems - Google
Responsibilities: Build high-scale microservices using Python, FastAPI, Docker, and PostgreSQL.
Requirements: Python, FastAPI, Docker, PostgreSQL, Microservices.
"""


@pytest.fixture(scope="module")
def sample_resume():
    candidate = load_candidate()
    reqs, dna = parse_jd(SAMPLE_JD)
    plan = build_plan(candidate, reqs, dna)
    return fallback_to_plan(plan, reqs, dna, reason="Test fixture")


def test_render_html(sample_resume):
    html = render_html(sample_resume)

    assert isinstance(html, str)
    assert "<!DOCTYPE html>" in html
    assert "GUNNAM SAI SAKETH RAM" in html
    assert "FastAPI" in html or "ZKProofAPI" in html
    assert "<style>" in html
    assert "@page" in html


def test_render_html_tight(sample_resume):
    normal_html = render_html(sample_resume, tight=False)
    tight_html = render_html(sample_resume, tight=True)

    assert "font-size: 8.5pt;" in tight_html
    assert "font-size: 9pt;" in normal_html


def test_render_pdf_sync(sample_resume):
    pdf_bytes = render_pdf_sync(sample_resume)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 10000
    assert pdf_bytes.startswith(b"%PDF-")

    # Verify with PyMuPDF
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    assert len(doc) == 1, f"Expected strictly 1 page, got {len(doc)} pages!"


def test_render_pdf_to_file(sample_resume, tmp_path):
    output_file = str(tmp_path / "test_resume.pdf")
    pdf_bytes = render_pdf_sync(sample_resume, output_path=output_file)

    assert os.path.exists(output_file)
    assert os.path.getsize(output_file) == len(pdf_bytes)
    assert os.path.getsize(output_file) > 10000
