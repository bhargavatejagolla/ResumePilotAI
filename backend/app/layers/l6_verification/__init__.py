"""Phase 6 — Verification, ATS Engine, Interview Probability, and Explainability."""
from typing import Optional
from app.layers.l2_candidate import load_candidate
from app.layers.l6_verification.ats import calculate_ats_score
from app.layers.l6_verification.interview_prob import calculate_interview_probability
from app.layers.l6_verification.explain import generate_explainability_report
from app.layers.l6_verification.playbook import generate_improvement_playbook
from app.schemas.candidate import Candidate
from app.schemas.job import JobRequirements
from app.schemas.resume import GeneratedResume
from app.schemas.verification import VerificationResult


def verify_resume(
    resume: GeneratedResume,
    reqs: JobRequirements,
    candidate: Optional[Candidate] = None,
    score_threshold: float = 65.0,
) -> VerificationResult:
    """Run full verification pipeline: ATS breakdown, interview probability, explainability, and 30-day playbook."""
    ats = calculate_ats_score(resume, reqs)
    prob = calculate_interview_probability(resume, reqs, ats)
    explain = generate_explainability_report(resume, reqs)
    cand = candidate or load_candidate()
    playbook = generate_improvement_playbook(cand, reqs, ats)
    passed = (ats.total_score >= score_threshold)

    return VerificationResult(
        ats=ats,
        interview_prob=prob,
        explainability=explain,
        playbook=playbook,
        passed_threshold=passed,
    )


__all__ = [
    "calculate_ats_score",
    "calculate_interview_probability",
    "generate_explainability_report",
    "generate_improvement_playbook",
    "verify_resume",
]
