"""Multi-User Candidate Storage Manager for ResumePilot AI.

Manages persistent storage and retrieval of Candidate profiles per resume_id.
Maintains full backwards compatibility with Saketh's master profile ('saketh' / 'default').
"""
import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

from app.config import get_settings
from app.schemas.candidate import Candidate

settings = get_settings()


def get_candidates_dir() -> Path:
    """Ensure the candidates directory exists and return Path."""
    candidates_dir = Path(settings.candidate_json_path).parent / "candidates"
    candidates_dir.mkdir(parents=True, exist_ok=True)
    return candidates_dir


def save_candidate(
    resume_id: str,
    candidate: Candidate,
    pdf_bytes: Optional[bytes] = None,
) -> Path:
    """Save a candidate profile and optional source PDF under resume_id."""
    candidates_dir = get_candidates_dir()
    json_path = candidates_dir / f"{resume_id}.json"

    # Write structured JSON
    data = candidate.model_dump()
    data["_resume_id"] = resume_id
    data["_updated_at"] = time.time()
    json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # Optionally write source PDF
    if pdf_bytes:
        pdf_path = candidates_dir / f"{resume_id}.pdf"
        pdf_path.write_bytes(pdf_bytes)

    return json_path


def load_candidate(resume_id: str = "saketh") -> Candidate:
    """
    Load candidate by resume_id.
    - 'saketh' or 'default' loads the master candidate.json
    - custom resume_id loads from app/data/candidates/{resume_id}.json
    """
    cleaned_id = (resume_id or "saketh").strip().lower()

    if cleaned_id in ["saketh", "default", "master"]:
        master_path = Path(settings.candidate_json_path)
        if master_path.exists():
            data = json.loads(master_path.read_text(encoding="utf-8"))
            return Candidate(**data)

    # Check candidates directory
    custom_path = get_candidates_dir() / f"{cleaned_id}.json"
    if custom_path.exists():
        data = json.loads(custom_path.read_text(encoding="utf-8"))
        return Candidate(**data)

    # Fallback to master candidate.json
    master_path = Path(settings.candidate_json_path)
    if master_path.exists():
        data = json.loads(master_path.read_text(encoding="utf-8"))
        return Candidate(**data)

    raise FileNotFoundError(f"Candidate not found for resume_id='{resume_id}'")


def list_saved_resumes() -> List[Dict[str, Any]]:
    """List all available resumes."""
    resumes: List[Dict[str, Any]] = []

    # Master resume
    master_path = Path(settings.candidate_json_path)
    if master_path.exists():
        try:
            m_data = json.loads(master_path.read_text(encoding="utf-8"))
            resumes.append({
                "resume_id": "saketh",
                "name": m_data.get("personal", {}).get("name", "Saketh"),
                "email": m_data.get("personal", {}).get("email", ""),
                "is_master": True,
            })
        except Exception:
            pass

    # Custom uploaded resumes
    for p in get_candidates_dir().glob("*.json"):
        rid = p.stem
        if rid in ["saketh", "default"]:
            continue
        try:
            c_data = json.loads(p.read_text(encoding="utf-8"))
            resumes.append({
                "resume_id": rid,
                "name": c_data.get("personal", {}).get("name", "Candidate"),
                "email": c_data.get("personal", {}).get("email", ""),
                "is_master": False,
            })
        except Exception:
            continue

    return resumes
