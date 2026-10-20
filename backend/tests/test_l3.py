import pytest
from app.layers.l3_job import (
    parse_jd, extract_jd_fields, classify_company, load_dna,
)
from app.schemas.job import JobRequirements


GOOGLE_JD = """AI Resident - Google DeepMind
Required: Python, PyTorch, TensorFlow, deep learning research.
Preferred: Publications in ML venues, LangGraph experience.
Responsibilities: Design and prototype novel algorithms, publish research.
Education: B.Tech in CS.
"""

AMAZON_JD = """Software Development Engineer - AWS
Required: Python, Java, distributed systems, Docker, Kubernetes.
Preferred: AWS, REST APIs, CI/CD.
Responsibilities: Own end-to-end delivery, drive ownership, deliver results.
"""

STARTUP_JD = """Founding GenAI Engineer - stealth startup
Required: Python, LangGraph, LLM APIs, FastAPI.
Preferred: RAG, Chroma, React.
Responsibilities: Build and ship agentic features, wear many hats, iterate fast.
"""


def test_extract_jd_fields():
    fields = extract_jd_fields(GOOGLE_JD)
    assert any("python" in s.lower() for s in fields["required_skills"])
    assert any("pytorch" in s.lower() for s in fields["required_skills"])
    assert fields["job_title"] != ""


def test_classify_google():
    result = classify_company(GOOGLE_JD, "Google DeepMind")
    assert result["company_type"] == "google"
    assert result["confidence"] > 0.5


def test_classify_amazon():
    result = classify_company(AMAZON_JD, "Amazon Web Services")
    assert result["company_type"] == "amazon"


def test_classify_startup():
    result = classify_company(STARTUP_JD, "Stealth Startup")
    assert result["company_type"] in ("startup", "generic")


def test_load_dna():
    for ct in ["google", "amazon", "microsoft", "research", "startup", "generic"]:
        dna = load_dna(ct)
        assert dna["name"] == ct
        assert "section_order" in dna
        assert "summary" in dna
        assert "projects" in dna


def test_parse_jd_google():
    reqs, dna = parse_jd(GOOGLE_JD)
    assert isinstance(reqs, JobRequirements)
    assert reqs.company_type == "google"
    assert dna["name"] == "google"
    assert len(reqs.jd_embedding) == 384
    assert len(reqs.skill_evidence) >= 3
    # Python should be known
    assert "Python" in reqs.skill_evidence
    assert reqs.skill_evidence["Python"].status == "known"


def test_parse_jd_amazon():
    reqs, dna = parse_jd(AMAZON_JD)
    assert reqs.company_type == "amazon"
    assert any("docker" in s.lower() for s in reqs.required_skills)


def test_parse_jd_rejects_short_input():
    with pytest.raises(ValueError):
        parse_jd("too short")


def test_skill_evidence_has_evidence_string():
    reqs, _ = parse_jd(GOOGLE_JD)
    for skill, ev in reqs.skill_evidence.items():
        if ev.status == "known":
            assert ev.evidence == "Resume Skills"
        elif ev.status == "likely":
            assert ev.evidence is not None
            assert ev.matched_via in ("project", "experience")
