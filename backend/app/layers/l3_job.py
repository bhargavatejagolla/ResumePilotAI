"""L3 — Job Intelligence.

Parses a raw job description into structured JobRequirements,
classifies the company, loads the correct DNA, embeds the JD,
and pre-computes skill evidence against the candidate's knowledge base.
"""
import re
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any

import yaml

from app.config import get_settings
from app.schemas.job import JobRequirements, SkillEvidence
from app.services.groq_service import chat_json
from app.services.embedding_service import embed_one
from app.layers.l2_candidate import search, load_candidate

settings = get_settings()

KNOWN_THRESHOLD = 0.85   # cosine similarity threshold for likely known
SEARCH_TOP_K = 3


# ──────────────────────────────────────────────────────────────
#  Step A · Groq extraction of JD fields
# ──────────────────────────────────────────────────────────────

def _load_prompt(name: str) -> str:
    path = Path(settings.prompts_dir) / name
    return path.read_text(encoding="utf-8")


def _as_list(v: Any) -> List[str]:
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    if isinstance(v, str) and v.strip():
        return [s.strip() for s in re.split(r"[,;\n•]+", v) if s.strip()]
    return []


def _as_int(v: Any) -> Optional[int]:
    if v is None:
        return None
    try:
        if isinstance(v, str):
            match = re.search(r"\d+", v)
            return int(match.group(0)) if match else None
        return int(v)
    except (ValueError, TypeError):
        return None


def _fallback_extract_jd(jd_text: str) -> dict:
    """Dynamic fallback parser if Groq API is unavailable or returns an error."""
    lines = [line.strip() for line in jd_text.strip().splitlines() if line.strip()]
    first_line = lines[0] if lines else "Untitled Role"

    # Extract Title and Company
    job_title = first_line
    company_name = ""
    if " - " in first_line:
        parts = first_line.split(" - ", 1)
        job_title = parts[0].strip()
        company_name = parts[1].strip()
    elif " at " in first_line.lower():
        parts = re.split(r"\s+at\s+", first_line, flags=re.IGNORECASE)
        job_title = parts[0].strip()
        company_name = parts[1].strip()

    # Domain detection
    text_lower = jd_text.lower()
    if any(k in text_lower for k in ["deep learning", "ai resident", "machine learning", "genai", "llm", "neural"]):
        domain = "ai"
    elif any(k in text_lower for k in ["distributed system", "backend", "sde", "fastapi", "spring boot"]):
        domain = "backend"
    elif any(k in text_lower for k in ["frontend", "react", "ui", "ux"]):
        domain = "frontend"
    elif any(k in text_lower for k in ["fullstack", "full stack"]):
        domain = "fullstack"
    elif any(k in text_lower for k in ["phd", "researcher", "publications"]):
        domain = "research"
    else:
        domain = "other"

    # Skill extraction via section headers and regex
    req_skills: List[str] = []
    pref_skills: List[str] = []
    soft_skills: List[str] = []
    responsibilities: List[str] = []
    edu_reqs: List[str] = []

    req_match = re.search(r"(?:Required|Requirements|Qualifications|Must have):?\s*(.+?)(?=(?:Preferred|Responsibilities|Education|$))", jd_text, re.IGNORECASE | re.DOTALL)
    if req_match:
        items = re.split(r"[,;\n•]+", req_match.group(1))
        for item in items:
            clean = item.strip().rstrip(".").strip()
            if clean and len(clean) < 60:
                req_skills.append(clean)

    pref_match = re.search(r"(?:Preferred|Nice to have|Bonus):?\s*(.+?)(?=(?:Responsibilities|Education|Required|$))", jd_text, re.IGNORECASE | re.DOTALL)
    if pref_match:
        items = re.split(r"[,;\n•]+", pref_match.group(1))
        for item in items:
            clean = item.strip().rstrip(".").strip()
            if clean and len(clean) < 60:
                pref_skills.append(clean)

    resp_match = re.search(r"(?:Responsibilities|Duties|What you'll do):?\s*(.+?)(?=(?:Education|Required|Preferred|$))", jd_text, re.IGNORECASE | re.DOTALL)
    if resp_match:
        items = re.split(r"[\n•]+", resp_match.group(1))
        for item in items:
            clean = item.strip()
            if clean and len(clean) > 5:
                responsibilities.append(clean)

    edu_match = re.search(r"(?:Education):?\s*(.+?)(?=(?:Responsibilities|Required|Preferred|$))", jd_text, re.IGNORECASE | re.DOTALL)
    if edu_match:
        edu_reqs.append(edu_match.group(1).strip())

    # Technology keywords
    tech_candidates = [
        "Python", "PyTorch", "TensorFlow", "LangGraph", "LangChain", "FastAPI",
        "Docker", "Kubernetes", "AWS", "Azure", "GCP", "React", "Java", "Go",
        "PostgreSQL", "Redis", "Celery", "ChromaDB", "Chroma", "Pinecone", "MongoDB",
        "RAG", "SQL", "Git", "CI/CD", "REST API", "REST APIs"
    ]
    tools_tech = [t for t in tech_candidates if re.search(r"\b" + re.escape(t) + r"\b", jd_text, re.IGNORECASE)]

    # Action verbs
    verb_pool = [
        "design", "prototype", "publish", "collaborate", "build", "own", "drive",
        "deliver", "scale", "ship", "optimize", "lead", "engineer", "architect",
        "develop", "implement", "iterate", "maintain", "test"
    ]
    action_verbs = [v.capitalize() for v in verb_pool if re.search(r"\b" + re.escape(v) + r"\b", jd_text, re.IGNORECASE)]

    # Years experience
    exp_match = re.search(r"(\d+)\+?\s*years?", jd_text, re.IGNORECASE)
    min_exp = int(exp_match.group(1)) if exp_match else None

    # Priority keywords
    words = re.findall(r"\b[A-Za-z]{3,}\b", jd_text)
    freq: Dict[str, int] = {}
    for w in words:
        w_norm = w.capitalize()
        freq[w_norm] = freq.get(w_norm, 0) + 1
    priority_keywords = [w for w, count in freq.items() if count >= 2 and w.lower() not in {"the", "and", "for", "with", "that", "this", "our", "you", "will", "are", "have"}][:10]

    return {
        "job_title": job_title,
        "company_name": company_name,
        "domain": domain,
        "required_skills": req_skills if req_skills else tools_tech[:4],
        "preferred_skills": pref_skills,
        "soft_skills": soft_skills,
        "responsibilities": responsibilities,
        "min_years_experience": min_exp,
        "education_requirements": edu_reqs,
        "tools_technologies": tools_tech,
        "action_verbs": action_verbs,
        "priority_keywords": priority_keywords,
    }


def extract_jd_fields(jd_text: str) -> dict:
    """Send JD to Groq -> structured dict with skills, verbs, etc."""
    prompt = _load_prompt("v1_extract_jd.txt").replace("{jd_text}", jd_text[:6000])
    raw: dict = {}
    try:
        raw = chat_json(prompt)
    except Exception:
        raw = _fallback_extract_jd(jd_text)

    if not isinstance(raw, dict):
        raw = _fallback_extract_jd(jd_text)

    # Normalize fields
    return {
        "job_title":              raw.get("job_title", "") or "Untitled Role",
        "company_name":           raw.get("company_name", "") or "",
        "domain":                 raw.get("domain", "other") or "other",
        "required_skills":        _as_list(raw.get("required_skills")),
        "preferred_skills":       _as_list(raw.get("preferred_skills")),
        "soft_skills":            _as_list(raw.get("soft_skills")),
        "responsibilities":       _as_list(raw.get("responsibilities")),
        "min_years_experience":   _as_int(raw.get("min_years_experience")),
        "education_requirements": _as_list(raw.get("education_requirements")),
        "tools_technologies":     _as_list(raw.get("tools_technologies")),
        "action_verbs":           _as_list(raw.get("action_verbs")),
        "priority_keywords":      _as_list(raw.get("priority_keywords")),
    }


# ──────────────────────────────────────────────────────────────
#  Step B · Company classification
# ──────────────────────────────────────────────────────────────

def _fallback_classify_company(jd_text: str, company_name: str) -> dict:
    """Dynamic fallback company classifier."""
    haystack = f"{company_name} {jd_text}".lower()

    if any(k in haystack for k in ["google", "deepmind", "waymo", "youtube"]):
        return {
            "company_type": "google",
            "confidence": 0.95,
            "reason": "Research-heavy and algorithmic scale mentioned, Google DeepMind entity."
        }
    if any(k in haystack for k in ["amazon", "aws", "customer obsession", "leadership principles", "deliver results"]):
        return {
            "company_type": "amazon",
            "confidence": 0.95,
            "reason": "AWS/Amazon entity with focus on ownership and customer obsession."
        }
    if any(k in haystack for k in ["microsoft", "azure", "growth mindset"]):
        return {
            "company_type": "microsoft",
            "confidence": 0.95,
            "reason": "Microsoft Azure ecosystem with focus on collaboration and systems reliability."
        }
    if any(k in haystack for k in ["phd required", "neurips", "icml", "research resident", "publications in"]):
        return {
            "company_type": "research",
            "confidence": 0.90,
            "reason": "Focus on academic publication, PhD requirements, and research novelty."
        }
    if any(k in haystack for k in ["stealth", "startup", "wear many hats", "founding", "ship often", "fast-paced"]):
        return {
            "company_type": "startup",
            "confidence": 0.90,
            "reason": "Fast-paced stealth startup environment with end-to-end ownership."
        }

    return {
        "company_type": "generic",
        "confidence": 0.70,
        "reason": "General engineering role without specialized company traits."
    }


def classify_company(jd_text: str, company_name: str) -> dict:
    """Classify hiring company into one of six categories."""
    prompt = (
        _load_prompt("v1_classify_company.txt")
        .replace("{jd_excerpt}", jd_text[:2000])
        .replace("{company_name}", company_name or "unknown")
    )
    raw: dict = {}
    try:
        raw = chat_json(prompt)
    except Exception:
        raw = _fallback_classify_company(jd_text, company_name)

    if not isinstance(raw, dict):
        raw = _fallback_classify_company(jd_text, company_name)

    company_type = str(raw.get("company_type", "")).strip().lower()
    valid = {"google", "amazon", "microsoft", "research", "startup", "generic"}
    if company_type not in valid:
        # Check fallback
        fb = _fallback_classify_company(jd_text, company_name)
        company_type = fb["company_type"]
        confidence = fb["confidence"]
        reason = fb["reason"]
    else:
        try:
            confidence = float(raw.get("confidence", 0.8))
        except (ValueError, TypeError):
            confidence = 0.8
        reason = str(raw.get("reason", ""))

    return {
        "company_type": company_type,
        "confidence": max(0.0, min(1.0, confidence)),
        "reason": reason,
    }


# ──────────────────────────────────────────────────────────────
#  Step C · DNA loading
# ──────────────────────────────────────────────────────────────

_dna_cache: Dict[str, dict] = {}


def load_dna(company_type: str) -> dict:
    """Load dna/{company_type}.yaml, with caching + generic fallback."""
    if company_type in _dna_cache:
        return _dna_cache[company_type]

    path = Path(settings.dna_dir) / f"{company_type}.yaml"
    if not path.exists():
        path = Path(settings.dna_dir) / "generic.yaml"

    dna = yaml.safe_load(path.read_text(encoding="utf-8"))
    _dna_cache[company_type] = dna
    return dna


# ──────────────────────────────────────────────────────────────
#  Step D · JD embedding
# ──────────────────────────────────────────────────────────────

def embed_jd(jd_text: str) -> List[float]:
    """384-dim embedding of the first 3000 chars of the JD."""
    return embed_one(jd_text[:3000])


# ──────────────────────────────────────────────────────────────
#  Step E · Skill evidence pre-computation
# ──────────────────────────────────────────────────────────────

def _search_skill_in_candidate(skill: str) -> Tuple[str, Optional[str], Optional[float], Optional[str]]:
    """Return (status, evidence, score, matched_via)."""
    clean_skill = skill.strip().lower()
    if not clean_skill:
        return ("missing", None, None, None)

    # 1. Direct skill-list match
    try:
        candidate = load_candidate()
    except Exception:
        candidate = None

    if candidate and candidate.skills:
        flat_skills = set()
        for cat, items in candidate.skills.items():
            if isinstance(items, list):
                for s in items:
                    flat_skills.add(s.lower())

        if clean_skill in flat_skills:
            return ("known", "Resume Skills", 1.0, "skill_list")

        # Substring exact check (e.g., 'python' matches 'python', 'pytorch' in 'pytorch')
        for s in flat_skills:
            if clean_skill == s or (len(clean_skill) >= 4 and clean_skill in s) or (len(s) >= 4 and s in clean_skill):
                return ("known", "Resume Skills", 1.0, "skill_list")

    # 2. Semantic match in projects
    try:
        hits = search(skill, type_filter="project", top_k=SEARCH_TOP_K)
    except Exception:
        hits = []

    if hits:
        top = hits[0]
        has_kw = clean_skill in top["text"].lower()
        if top["score"] >= KNOWN_THRESHOLD or has_kw or top["score"] >= 0.28:
            eff_score = top["score"] if not has_kw else max(top["score"], 0.85)
            return (
                "likely",
                f"Project: {top['metadata'].get('name', '')}",
                round(float(eff_score), 4),
                "project",
            )

    # 3. Semantic match in experience
    try:
        hits = search(skill, type_filter="experience", top_k=SEARCH_TOP_K)
    except Exception:
        hits = []

    if hits:
        top = hits[0]
        has_kw = clean_skill in top["text"].lower()
        if top["score"] >= KNOWN_THRESHOLD or has_kw or top["score"] >= 0.28:
            eff_score = top["score"] if not has_kw else max(top["score"], 0.85)
            return (
                "likely",
                f"Experience: {top['metadata'].get('company', '')}",
                round(float(eff_score), 4),
                "experience",
            )

    return ("missing", None, None, None)


def compute_skill_evidence(required_skills: List[str], preferred_skills: List[str]) -> Dict[str, SkillEvidence]:
    """Pre-compute evidence for every required + preferred skill."""
    evidence: Dict[str, SkillEvidence] = {}
    for skill in required_skills + preferred_skills:
        if not skill or skill in evidence:
            continue
        status, ev, score, via = _search_skill_in_candidate(skill)
        evidence[skill] = SkillEvidence(
            skill=skill,
            status=status,  # type: ignore[arg-type]
            confidence=max(0.0, min(1.0, score if score is not None else 0.0)),
            evidence=ev,
            matched_via=via,
            matched_score=score,
        )
    return evidence


# ──────────────────────────────────────────────────────────────
#  Step F · Public entry point
# ──────────────────────────────────────────────────────────────

def parse_jd(jd_text: str) -> Tuple[JobRequirements, dict]:
    """
    Parse a job description end-to-end.

    Returns:
        (JobRequirements, dna_dict)
    """
    if not jd_text or len(jd_text.strip()) < 30:
        raise ValueError("Job description is too short (< 30 chars).")

    cleaned_jd = jd_text.strip()

    # Step A: extract fields
    fields = extract_jd_fields(cleaned_jd)

    # Step B: classify company
    classification = classify_company(cleaned_jd, fields["company_name"])

    # Step C: load DNA
    dna = load_dna(classification["company_type"])

    # Step D: embed JD
    jd_embedding = embed_jd(cleaned_jd)

    # Step E: skill evidence
    evidence = compute_skill_evidence(
        fields["required_skills"],
        fields["preferred_skills"],
    )

    # Step F: assemble
    reqs = JobRequirements(
        job_title=fields["job_title"],
        company_name=fields["company_name"],
        company_type=classification["company_type"],
        classification_confidence=classification["confidence"],
        classification_reason=classification["reason"],
        domain=fields["domain"],
        required_skills=fields["required_skills"],
        preferred_skills=fields["preferred_skills"],
        soft_skills=fields["soft_skills"],
        responsibilities=fields["responsibilities"],
        min_years_experience=fields["min_years_experience"],
        education_requirements=fields["education_requirements"],
        tools_technologies=fields["tools_technologies"],
        action_verbs=fields["action_verbs"],
        priority_keywords=fields["priority_keywords"],
        skill_evidence=evidence,
        jd_embedding=jd_embedding,
        raw_text=cleaned_jd,
    )

    return reqs, dna
