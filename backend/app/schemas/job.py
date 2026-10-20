"""Pydantic schema for JobRequirements.

Everything Phase 4 needs to plan a resume, computed once in Phase 3.
"""
from typing import Literal, Optional, List, Dict
from pydantic import BaseModel, Field

CompanyType = Literal["google", "amazon", "microsoft", "research", "startup", "generic"]
SkillStatus = Literal["known", "likely", "missing"]


class SkillEvidence(BaseModel):
    skill: str
    status: SkillStatus
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: Optional[str] = None          # e.g. "Resume Skills" or "Project: AgriBloom Agentic"
    matched_via: Optional[str] = None       # "skill_list" | "project" | "experience" | None
    matched_score: Optional[float] = None   # cosine similarity of the top hit


class JobRequirements(BaseModel):
    # -- Core identification -------------------------------------
    job_title: str
    company_name: str = ""
    company_type: CompanyType = "generic"
    classification_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    classification_reason: str = ""
    domain: str = "other"                   # ai | backend | frontend | fullstack | data | research | other

    # -- Skills --------------------------------------------------
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)

    # -- Requirements --------------------------------------------
    responsibilities: List[str] = Field(default_factory=list)
    min_years_experience: Optional[int] = None
    education_requirements: List[str] = Field(default_factory=list)

    # -- Keyword signals -----------------------------------------
    tools_technologies: List[str] = Field(default_factory=list)
    action_verbs: List[str] = Field(default_factory=list)
    priority_keywords: List[str] = Field(default_factory=list)

    # -- Pre-computed for Phase 4 --------------------------------
    skill_evidence: Dict[str, SkillEvidence] = Field(default_factory=dict)
    jd_embedding: List[float] = Field(default_factory=list)

    # -- Metadata ------------------------------------------------
    raw_text: str = ""
