"""Pydantic schemas for Phase 6 (Verification, ATS, Interview Probability, Explainability)."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ATSScoreBreakdown(BaseModel):
    total_score: float = Field(default=0.0, ge=0.0, le=100.0)
    keyword_match_score: float = Field(default=0.0, ge=0.0, le=100.0)
    semantic_similarity_score: float = Field(default=0.0, ge=0.0, le=100.0)
    metric_density_score: float = Field(default=0.0, ge=0.0, le=100.0)
    structure_score: float = Field(default=0.0, ge=0.0, le=100.0)
    matched_keywords: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)


class InterviewProbability(BaseModel):
    probability: float = Field(default=0.0, ge=0.0, le=1.0)
    percentage: int = Field(default=0, ge=0, le=100)
    tier: str = "Moderate"
    key_strengths: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    recommendation: str = ""


class ProjectDecision(BaseModel):
    project_name: str
    selected: bool
    score: float = 0.0
    reasons: List[str] = Field(default_factory=list)


class BulletDiff(BaseModel):
    entity: str
    original: str
    rewritten: str
    changed: bool
    source: str
    rejection: Optional[str] = ""


class ExplainabilityReport(BaseModel):
    project_decisions: List[ProjectDecision] = Field(default_factory=list)
    bullet_diffs: List[BulletDiff] = Field(default_factory=list)
    skill_coverage: Dict[str, Any] = Field(default_factory=dict)
    interview_talking_points: List[str] = Field(default_factory=list)


class SprintWeek(BaseModel):
    week_number: int
    title: str
    focus: str
    action_items: List[str] = Field(default_factory=list)
    deliverable: str


class ImprovementPlaybook(BaseModel):
    target_role: str
    target_company: str
    current_match_percentage: int
    projected_match_percentage: int
    missing_critical_skills: List[str] = Field(default_factory=list)
    sprint_weeks: List[SprintWeek] = Field(default_factory=list)
    advisor_summary: str


class VerificationResult(BaseModel):
    ats: ATSScoreBreakdown
    interview_prob: InterviewProbability
    explainability: ExplainabilityReport
    playbook: Optional[ImprovementPlaybook] = None
    passed_threshold: bool = True
