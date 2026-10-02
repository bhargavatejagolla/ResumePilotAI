"""
One-time script: Parse my_resume.pdf -> candidate.json.

Run from backend/:
    python -m scripts.parse_my_resume
"""
import json
import re
from pathlib import Path

from app.config import get_settings
from app.layers.l1_document import parse_resume_layout, extract_spans
from app.services.groq_service import chat_json
from app.schemas.candidate import Candidate

settings = get_settings()

SECTION_SCHEMAS = {
    "summary": '{"summary": "verbatim profile summary text"}',
    "education": '{"education": [{"institution": "...", "degree": "...", "field": "...", "start": "YYYY-MM", "end": "YYYY-MM", "location": "...", "gpa": "..."}]}',
    "experience": '{"experience": [{"company": "...", "title": "...", "location": "...", "start": "YYYY-MM", "end": "YYYY-MM", "bullets": [{"text": "...", "metrics": 0, "source": "..."}]}]}',
    "projects": '{"projects": [{"name": "...", "tech": ["..."], "award": "...", "links": {"github": "..."}, "bullets": [{"text": "...", "metrics": 0, "source": "..."}]}]}',
    "skills": '{"skills": {"languages": ["..."], "ai_ml": ["..."], "backend": ["..."], "devops": ["..."], "databases": ["..."]}}',
    "achievements": '{"achievements": [{"title": "...", "category": "...", "description": "...", "metrics": ["..."], "links": ["..."]}]}',
    "certifications": '{"certifications": [{"name": "...", "issuer": "...", "year": "..."}]}',
}


def build_prompt(section_type: str, section_text: str) -> str:
    prompt_file = Path(settings.prompts_dir, "v1_extract_resume.txt")
    if not prompt_file.exists():
        # Fallback inline template
        template = """You are a precise resume information extractor.
Return ONLY valid JSON.
Extract text VERBATIM from the input.
For every item include source tags where appropriate.

SECTION TYPE: {section_type}
EXPECTED SCHEMA: {schema_description}

INPUT TEXT:
---
{section_text}
---
"""
    else:
        template = prompt_file.read_text(encoding="utf-8")

    return (
        template
        .replace("{section_type}", section_type)
        .replace("{schema_description}", SECTION_SCHEMAS.get(section_type, "{}"))
        .replace("{section_text}", section_text)
    )


def extract_section(section_type: str, section_text: str) -> dict:
    """Call Groq via Phase 0 wrapper. Returns parsed JSON or {} on failure."""
    if not section_text.strip():
        return {}
    prompt = build_prompt(section_type, section_text)
    try:
        return chat_json(prompt)
    except Exception as e:
        print(f"  ⚠️  Groq failed for section '{section_type}': {e}")
        return {}


def extract_personal_info(spans_text: str) -> dict:
    """Parse header contact info with robust regex."""
    email_m = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", spans_text)
    phone_m = re.search(r"(\+?\d[\d\s\-()]{7,}\d)", spans_text)
    linkedin_m = re.search(r"linkedin\.com/in/[\w\-]+|linkedin\.com/[\w/-]+", spans_text, re.I)
    github_m = re.search(r"github\.com/[\w\-]+|github\.com/[\w/-]+", spans_text, re.I)
    return {
        "name": "Saketh",
        "email": email_m.group(0) if email_m else "",
        "phone": phone_m.group(0) if phone_m else "",
        "linkedin": f"https://{linkedin_m.group(0)}" if linkedin_m and not linkedin_m.group(0).startswith("http") else (linkedin_m.group(0) if linkedin_m else ""),
        "github": f"https://{github_m.group(0)}" if github_m and not github_m.group(0).startswith("http") else (github_m.group(0) if github_m else ""),
        "location": "Bengaluru, India",
    }


def main():
    pdf_path = Path(settings.candidate_json_path).parent / "my_resume.pdf"
    if not pdf_path.exists():
        # Check workspace root
        fallback_pdf = Path("resume-saketh bro.pdf")
        if fallback_pdf.exists():
            pdf_path = fallback_pdf
        else:
            raise FileNotFoundError(f"Place your resume at {pdf_path}")

    print(f"📄 Parsing {pdf_path.name} ...")
    spans = extract_spans(str(pdf_path))
    sections = parse_resume_layout(str(pdf_path))

    print(f"🔍 Detected sections: {list(sections.keys())}")

    # Header text extraction for contact details
    all_raw_text = " ".join(s.text for s in spans[:30])
    personal = extract_personal_info(all_raw_text)

    candidate: dict = {"personal": personal}
    for section_type, section_text in sections.items():
        print(f"  ⚙️  Extracting '{section_type}' ...")
        data = extract_section(section_type, section_text)
        for k, v in data.items():
            if v:
                candidate[k] = v

    # Fallback / verify sources on every bullet
    for proj_idx, proj in enumerate(candidate.get("projects", [])):
        proj["id"] = proj.get("id") or f"proj_{proj_idx+1}"
        for b_idx, bullet in enumerate(proj.get("bullets", [])):
            if isinstance(bullet, str):
                bullet = {"text": bullet, "source": f"resume:projects[{proj_idx}].bullets[{b_idx}]", "metrics": 0}
                proj["bullets"][b_idx] = bullet
            elif isinstance(bullet, dict) and "source" not in bullet:
                bullet["source"] = f"resume:projects[{proj_idx}].bullets[{b_idx}]"

    for exp_idx, exp in enumerate(candidate.get("experience", [])):
        exp["id"] = exp.get("id") or f"exp_{exp_idx+1}"
        for b_idx, bullet in enumerate(exp.get("bullets", [])):
            if isinstance(bullet, str):
                bullet = {"text": bullet, "source": f"resume:experience[{exp_idx}].bullets[{b_idx}]", "metrics": 0}
                exp["bullets"][b_idx] = bullet
            elif isinstance(bullet, dict) and "source" not in bullet:
                bullet["source"] = f"resume:experience[{exp_idx}].bullets[{b_idx}]"

    # Validate with Pydantic
    try:
        validated = Candidate(**candidate)
        out_json = validated.model_dump_json(indent=2)
    except Exception as e:
        print(f"⚠️ Pydantic validation warning: {e}. Saving candidate dict directly.")
        out_json = json.dumps(candidate, indent=2, ensure_ascii=False)

    out = Path(settings.candidate_json_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(out_json, encoding="utf-8")

    print(f"\n✅ Successfully parsed and saved -> {out}")
    print(f"   Projects: {len(candidate.get('projects', []))}")
    print(f"   Experience: {len(candidate.get('experience', []))}")
    print(f"   Skills categories: {list(candidate.get('skills', {}).keys())}")
    print(f"   Achievements: {len(candidate.get('achievements', []))}")


if __name__ == "__main__":
    main()
