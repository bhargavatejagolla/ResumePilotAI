"""Unit tests for Phase 5 (Prompt Compiler & Groq Writer)."""
from unittest.mock import MagicMock
import pytest

from app.layers.l2_candidate import load_candidate
from app.layers.l3_job import parse_jd, load_dna
from app.layers.l4_intelligence.selector import build_plan
from app.layers.l5_generation.compiler import (
    compile_rewrite_prompt,
    compile_revision_prompt,
)
from app.layers.l5_generation.writer import (
    fallback_to_plan,
    rewrite_resume,
)
from app.schemas.resume import GeneratedResume


SAMPLE_JD = """
Software Engineer, Distributed Systems - Google
Location: Mountain View, CA

Responsibilities:
- Build high-scale distributed backend services handling 100K+ RPS.
- Optimize low-latency microservices and database query performance.
- Collaborate with cross-functional teams to design scalable APIs.

Required Skills:
- Python, FastAPI, Distributed Systems, Microservices, PostgreSQL, Redis, Docker, Kubernetes.
"""


@pytest.fixture(scope="module")
def sample_plan_and_context():
    candidate = load_candidate()
    reqs, dna = parse_jd(SAMPLE_JD)
    plan = build_plan(candidate, reqs, dna)
    return plan, reqs, dna


def test_compile_rewrite_prompt(sample_plan_and_context):
    plan, reqs, dna = sample_plan_and_context
    prompt = compile_rewrite_prompt(plan, reqs, dna)

    assert isinstance(prompt, str)
    assert len(prompt) > 200
    assert "{min_words}" not in prompt
    assert "{max_words}" not in prompt
    assert "{company_type}" not in prompt
    assert "{plan_json_input}" not in prompt
    assert "GOOGLE" in prompt
    assert "AgriBloom" in prompt or "ZKProofAPI" in prompt


def test_compile_revision_prompt(sample_plan_and_context):
    plan, reqs, _ = sample_plan_and_context
    feedback = "Improve keyword alignment for PostgreSQL and Docker."
    prompt = compile_revision_prompt({"summary": plan.summary_draft}, feedback, reqs)

    assert isinstance(prompt, str)
    assert "{revision_feedback}" not in prompt
    assert "{current_draft_json}" not in prompt
    assert feedback in prompt


def test_fallback_to_plan(sample_plan_and_context):
    plan, reqs, dna = sample_plan_and_context
    res = fallback_to_plan(plan, reqs, dna, reason="Testing fallback")

    assert isinstance(res, GeneratedResume)
    assert res.metadata.get("is_fallback") is True
    assert res.metadata.get("fallback_reason") == "Testing fallback"
    assert len(res.projects) == len(plan.projects)
    assert len(res.experience) == len(plan.experience)
    assert res.summary == plan.summary_draft

    for p in res.projects:
        for b in p.bullets:
            assert b.text == b.original_text
            assert b.is_rewritten is False
            assert b.source.startswith("resume:")


def test_metric_hallucination_guard(sample_plan_and_context):
    """If original bullet had no metrics, but Groq added fake numbers, it must be rejected."""
    plan, reqs, dna = sample_plan_and_context

    mock_svc = MagicMock()
    mock_svc.settings.groq_api_key = "gsk_valid_mock_key_12345"
    mock_svc.chat_json.return_value = {
        "summary": "Polished high impact summary for distributed systems.",
        "projects": [
            {
                "name": plan.projects[0].name,
                "bullets": [
                    "Engineered distributed pipeline achieving 99.9% uptime with 40% latency drop and $500 savings."
                    if not plan.projects[0].selected_bullets[0].has_metric
                    else plan.projects[0].selected_bullets[0].text
                ],
            }
        ],
        "experience": [],
    }

    # Find a bullet with has_metric == False
    test_bullet = plan.projects[0].selected_bullets[0]
    had_metric_originally = test_bullet.has_metric

    res = rewrite_resume(plan, reqs, dna, groq_svc=mock_svc)
    assert isinstance(res, GeneratedResume)

    if not had_metric_originally:
        # The hallucinated bullet must be rejected and reverted to original
        first_bullet = res.projects[0].bullets[0]
        assert first_bullet.text == test_bullet.text
        assert first_bullet.is_rewritten is False


def test_valid_rewrite_accepted(sample_plan_and_context):
    """Stronger verbs without invented metrics should be accepted."""
    plan, reqs, dna = sample_plan_and_context

    mock_svc = MagicMock()
    mock_svc.settings.groq_api_key = "gsk_valid_mock_key_12345"

    improved_bullet_text = "Architected autonomous microservices orchestrating resilient multi-model pipelines across cloud infrastructure."
    mock_svc.chat_json.return_value = {
        "summary": "Innovative Software Engineer experienced in scalable distributed architectures, low-latency microservices, and high-throughput data processing pipelines.",
        "projects": [
            {
                "name": plan.projects[0].name,
                "bullets": [improved_bullet_text],
            }
        ],
        "experience": [],
    }

    res = rewrite_resume(plan, reqs, dna, groq_svc=mock_svc)
    assert isinstance(res, GeneratedResume)
    assert res.projects[0].bullets[0].text == improved_bullet_text
    assert res.projects[0].bullets[0].is_rewritten is True
    assert "Innovative Software Engineer" in res.summary


def test_groq_exception_falls_back(sample_plan_and_context):
    """When Groq throws an unexpected exception, gracefully fallback to plan."""
    plan, reqs, dna = sample_plan_and_context

    mock_svc = MagicMock()
    mock_svc.settings.groq_api_key = "gsk_valid_mock_key_12345"
    mock_svc.chat_json.side_effect = ConnectionError("Groq endpoint unreachable")

    res = rewrite_resume(plan, reqs, dna, groq_svc=mock_svc)
    assert isinstance(res, GeneratedResume)
    assert res.metadata.get("is_fallback") is True
    assert "Groq endpoint unreachable" in res.metadata.get("fallback_reason", "")
    assert res.summary == plan.summary_draft
