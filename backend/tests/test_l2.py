import pytest
from app.layers.l2_candidate import build_index, search, load_candidate
from app.services.chroma_service import collection_count


@pytest.fixture(scope="module")
def indexed():
    try:
        build_index(force_rebuild=True)
        return True
    except FileNotFoundError:
        pytest.skip("candidate.json not present yet")


def test_candidate_loads(indexed):
    c = load_candidate()
    assert "Saketh" in c.personal.name
    assert len(c.projects) == 3
    assert len(c.experience) == 1


def test_index_populated(indexed):
    assert collection_count() > 0, "Expected entities indexed"


def test_project_search(indexed):
    hits = search("agentic AI", type_filter="project", top_k=3)
    assert len(hits) >= 1
    assert any("AgriBloom" in h["metadata"].get("name", "") for h in hits)


def test_scores_are_bounded(indexed):
    hits = search("systems", top_k=5)
    for h in hits:
        assert 0.0 <= h["score"] <= 1.0
