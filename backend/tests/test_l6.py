"""Unit tests for Phase 6 (ATS Engine, Interview Probability, Explainability)."""
import pytest

from app.layers.l2_candidate import load_candidate
from app.layers.l3_job import parse_jd
from app.layers.l4_intelligence.selector import build_plan
from app.layers.l5_generation.writer import fallback_to_plan
from app.layers.l6_verification import (
    calculate_ats_score,
    calculate_interview_probability,
    generate_explainability_report,
    verify_resume,
)
from app.schemas.verification import VerificationResult


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


@pytest.fixture(scope="module")
def resume_and_reqs():
    candidate = load_candidate()
    reqs, dna = parse_jd(SAMPLE_JD)
    plan = build_plan(candidate, reqs, dna)
    resume = fallback_to_plan(plan, reqs, dna, reason="Test fixture")
    return resume, reqs


def test_calculate_ats_score(resume_and_reqs):
    resume, reqs = resume_and_reqs
    ats = calculate_ats_score(resume, reqs)

    assert 0.0 <= ats.total_score <= 100.0
    assert 0.0 <= ats.keyword_match_score <= 100.0
    assert 0.0 <= ats.semantic_similarity_score <= 100.0
    assert 0.0 <= ats.metric_density_score <= 100.0
    assert 0.0 <= ats.structure_score <= 100.0

    assert len(ats.matched_keywords) > 0
    # Python, FastAPI or Docker should be matched
    matched_lower = [k.lower() for k in ats.matched_keywords]
    assert any(k in matched_lower for k in ["python", "fastapi", "docker", "pytorch"])


def test_interview_probability(resume_and_reqs):
    resume, reqs = resume_and_reqs
    ats = calculate_ats_score(resume, reqs)
    prob = calculate_interview_probability(resume, reqs, ats)

    assert 0.15 <= prob.probability <= 0.95
    assert 15 <= prob.percentage <= 95
    assert len(prob.tier) > 3
    assert len(prob.key_strengths) >= 2
    # Check that prestige factors are recognized
    strengths_str = " ".join(prob.key_strengths).lower()
    assert "hackathon" in strengths_str or "intel" in strengths_str or "ieee" in strengths_str


def test_explainability_report(resume_and_reqs):
    resume, reqs = resume_and_reqs
    explain = generate_explainability_report(resume, reqs)

    assert len(explain.project_decisions) == len(resume.projects)
    for dec in explain.project_decisions:
        assert dec.selected is True
        assert len(dec.reasons) > 0

    assert len(explain.bullet_diffs) > 0
    assert explain.skill_coverage["total_required"] > 0
    assert len(explain.interview_talking_points) >= 3


def test_verify_resume_orchestrator(resume_and_reqs):
    resume, reqs = resume_and_reqs
    res = verify_resume(resume, reqs, score_threshold=60.0)

    assert isinstance(res, VerificationResult)
    assert res.ats.total_score > 60.0
    assert res.passed_threshold is True
    assert res.interview_prob.percentage >= 60
    assert len(res.explainability.project_decisions) == 3
