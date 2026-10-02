import json
from pathlib import Path
from app.layers.l1_document import parse_resume_layout, extract_spans, detect_sections
from app.config import get_settings

settings = get_settings()
PDF = Path(settings.candidate_json_path).parent / "my_resume.pdf"
if not PDF.exists():
    fallback = Path("resume-saketh bro.pdf")
    if fallback.exists():
        PDF = fallback


def test_extract_spans():
    spans = extract_spans(str(PDF))
    assert len(spans) > 20, "Resume should yield many spans"
    assert any(s.size > 0 for s in spans), "Resume spans should have font sizes"


def test_detect_sections():
    spans = extract_spans(str(PDF))
    sections = detect_sections(spans)
    assert len(sections) >= 3, f"Expected at least 3 sections, found: {list(sections.keys())}"


def test_candidate_json_structure():
    path = Path(settings.candidate_json_path)
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "personal" in data
        assert data["personal"]["name"] == "Saketh"
