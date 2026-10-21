"""ResumePlan — the deterministic output of Phase 4.

Phase 5 (Groq Writer) will polish bullets/summary but never change structure.
Phase 6 (ATS + Explainability) will consume metadata for change logs.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class PlannedBullet(BaseModel):
    text: str
    source: str
    score: float = 0.0
    has_metric: bool = False


class PlannedProject(BaseModel):
    name: str
    tech: List[str] = Field(default_factory=list)
    selected_bullets: List[PlannedBullet] = Field(default_factory=list)
    total_score: float = 0.0
    relevance: float = 0.0
    impact: int = 0
    freshness: float = 0.0
    coverage: float = 0.0
    award: str = ""


class PlannedExperience(BaseModel):
    company: str
    title: str
    selected_bullets: List[PlannedBullet] = Field(default_factory=list)
    total_score: float = 0.0
    relevance: float = 0.0
    impact: int = 0
    freshness: float = 0.0


class ResumePlan(BaseModel):
    # ── Structure ────────────────────────────────────────────
    section_order: List[str] = Field(default_factory=list)
    summary_draft: str = ""

    # ── Selected content ─────────────────────────────────────
    projects: List[PlannedProject] = Field(default_factory=list)
    experience: List[PlannedExperience] = Field(default_factory=list)
    skills: Dict[str, List[str]] = Field(default_factory=dict)
    achievements: List[dict] = Field(default_factory=list)
    certifications: List[dict] = Field(default_factory=list)
    education: List[dict] = Field(default_factory=list)
    personal: dict = Field(default_factory=dict)

    # ── Explainability metadata (Phase 6 consumes this) ──────
    metadata: Dict[str, Any] = Field(default_factory=dict)
