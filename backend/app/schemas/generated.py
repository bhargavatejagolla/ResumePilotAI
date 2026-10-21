"""GeneratedResume — the polished output of Phase 5.

Structurally identical to ResumePlan (so Phase 6 can re-verify),
but with polished bullet text and summary.
"""
from typing import List, Dict, Any
from pydantic import BaseModel, Field


class GeneratedBullet(BaseModel):
    text: str
    source: str
    original_text: str = ""     # what Phase 4 selected (for diff)
    score: float = 0.0
    has_metric: bool = False


class GeneratedProject(BaseModel):
    name: str
    tech: List[str] = Field(default_factory=list)
    bullets: List[GeneratedBullet] = Field(default_factory=list)
    total_score: float = 0.0
    relevance: float = 0.0
    award: str = ""


class GeneratedExperience(BaseModel):
    company: str
    title: str
    bullets: List[GeneratedBullet] = Field(default_factory=list)
    total_score: float = 0.0


class GeneratedResume(BaseModel):
    summary: str
    section_order: List[str] = Field(default_factory=list)
    projects: List[GeneratedProject] = Field(default_factory=list)
    experience: List[GeneratedExperience] = Field(default_factory=list)
    skills: Dict[str, List[str]] = Field(default_factory=dict)
    achievements: List[dict] = Field(default_factory=list)
    certifications: List[dict] = Field(default_factory=list)
    education: List[dict] = Field(default_factory=list)
    personal: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)
