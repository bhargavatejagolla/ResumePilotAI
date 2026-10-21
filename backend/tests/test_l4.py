import pytest
from app.layers.l2_candidate import load_candidate
from app.layers.l3_job import parse_jd
from app.layers.l4_intelligence.matcher import (
    score_projects, score_bullets, has_metric, count_metrics, verb_strength,
)
from app.layers.l4_intelligence.gap import group_skills
from app.layers.l4_intelligence.strategy import adapt_dna
from app.layers.l4_intelligence.ranker import (
    rank_projects, rank_experiences, _freshness,
)
from app.layers.l4_intelligence.selector import build_plan
from app.layers.l4_intelligence.truth import verify_plan


GOOGLE_JD = """AI Resident - Google DeepMind
Required: Python, PyTorch, TensorFlow, deep learning research.
Responsibilities: Design and prototype novel algorithms, publish research.
"""


@pytest.fixture(scope="module")
def fixture():
    candidate = load_candidate()
    reqs, dna = parse_jd(GOOGLE_JD)
    plan = build_plan(candidate, reqs, dna)
    return candidate, reqs, dna, plan


# ── matcher tests ────────────────────────────────────────────

def test_has_metric():
    assert has_metric("Reduced latency by 40%")
    assert has_metric("Trained on 91,000+ images")
    assert has_metric("Achieved 92.7% SSIM")
    assert has_metric("3-line integration")
    assert not has_metric("Built a REST API")


def test_count_metrics():
    text = "Trained on 91,000+ images; achieved 92.7% SSIM and 28.5 dB PSNR"
    assert count_metrics(text) >= 3


def test_verb_strength():
    assert verb_strength("Built a system") == 1.0
    assert verb_strength("Worked on a system") == 0.5


def test_score_projects_returns_all(fixture):
    candidate, reqs, _, _ = fixture
    results = score_projects(candidate, reqs)
    assert len(results) == 3
    for r in results:
        assert 0.0 <= r["relevance"] <= 1.0


def test_score_bullets_sorted(fixture):
    candidate, reqs, dna, _ = fixture
    proj = candidate.projects[0]
    bullets = score_bullets(proj.bullets, reqs, dna)
    scores = [b["score"] for b in bullets]
    assert scores == sorted(scores, reverse=True)


# ── gap tests ────────────────────────────────────────────────

def test_group_skills(fixture):
    _, reqs, _, _ = fixture
    gaps = group_skills(reqs)
    assert "known" in gaps
    assert "missing" in gaps
    assert 0.0 <= gaps["coverage"] <= 1.0


# ── strategy tests ───────────────────────────────────────────

def test_adapt_dna_preserves_original(fixture):
    _, reqs, dna, _ = fixture
    original = dict(dna)
    adapted = adapt_dna(reqs, dna)
    # Original must not be mutated
    assert dna["name"] == original["name"]
    # Adapted must have max_projects set
    assert adapted["projects"]["max_projects"] == 3


# ── ranker tests ─────────────────────────────────────────────

def test_freshness():
    assert _freshness("") == 1.0           # ongoing
    assert _freshness("2025-07") > 0.8     # recent
    assert _freshness("2015-01") < 0.3     # old


def test_rank_projects_ordered(fixture):
    candidate, reqs, _, _ = fixture
    ranked = rank_projects(candidate, reqs)
    assert len(ranked) == 3
    scores = [r["total_score"] for r in ranked]
    assert scores == sorted(scores, reverse=True)


def test_rank_experiences(fixture):
    candidate, reqs, _, _ = fixture
    ranked = rank_experiences(candidate, reqs)
    assert len(ranked) >= 1


# ── selector + truth tests ───────────────────────────────────

def test_plan_has_all_sections(fixture):
    _, _, _, plan = fixture
    assert "summary" in plan.section_order
    assert "projects" in plan.section_order
    assert "skills" in plan.section_order


def test_plan_selects_3_projects(fixture):
    _, _, _, plan = fixture
    assert len(plan.projects) == 3


def test_plan_bullets_have_sources(fixture):
    _, _, _, plan = fixture
    for p in plan.projects:
        for b in p.selected_bullets:
            assert b.source.startswith("resume:")


def test_plan_summary_within_bounds(fixture):
    _, _, _, plan = fixture
    wc = plan.metadata["summary_word_count"]
    assert 25 <= wc <= 100


def test_plan_no_truth_issues(fixture):
    candidate, _, _, plan = fixture
    issues = verify_plan(plan, candidate)
    assert issues == [], f"Truth issues: {issues}"


def test_plan_is_deterministic(fixture):
    candidate, reqs, dna, plan1 = fixture
    plan2 = build_plan(candidate, reqs, dna)
    # Summaries must be byte-identical
    assert plan1.summary_draft == plan2.summary_draft
    # Project order must be identical
    assert [p.name for p in plan1.projects] == [p.name for p in plan2.projects]
    # Bullet scores must be identical
    for p1, p2 in zip(plan1.projects, plan2.projects):
        for b1, b2 in zip(p1.selected_bullets, p2.selected_bullets):
            assert b1.score == b2.score
