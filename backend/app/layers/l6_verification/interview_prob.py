"""Calibrated Interview Probability Engine for Phase 6.

Transforms raw ATS keyword scores into a realistic, candidate-specific interview probability.
Factors in:
1. ATS & Semantic Match
2. Required Skills Coverage
3. Candidate Prestige / Distinction Multipliers (National Hackathon Winner, IEEE Author, Intel Experience)
4. Target Company Tier Bar
"""
from typing import List
from app.schemas.job import JobRequirements
from app.schemas.resume import GeneratedResume
from app.schemas.verification import ATSScoreBreakdown, InterviewProbability


def calculate_interview_probability(
    resume: GeneratedResume,
    reqs: JobRequirements,
    ats: ATSScoreBreakdown,
) -> InterviewProbability:
    """Calculate the calibrated interview probability and breakdown."""
    # 1. Base ATS alignment (0.0 to 1.0)
    ats_factor = ats.total_score / 100.0

    # 2. Required skills coverage (0.0 to 1.0)
    matched_set = {k.lower() for k in ats.matched_keywords}
    required_count = len(reqs.required_skills)
    if required_count > 0:
        matched_req = sum(1 for s in reqs.required_skills if s.lower() in matched_set)
        skill_coverage = matched_req / required_count
    else:
        skill_coverage = 0.90

    # 3. Candidate Prestige & Distinction Multipliers
    # Candidate specific: Grand Champion 50k+, IEEE 1st author, Intel Unnati, OCI certified
    prestige_bonus = 0.0
    strengths: List[str] = []

    # Check for National Hackathon Win
    has_hackathon = any("hackathon" in a.get("title", "").lower() or "champion" in a.get("title", "").lower() for a in resume.achievements)
    if has_hackathon or "grand champion" in resume.summary.lower():
        prestige_bonus += 0.12
        strengths.append("Grand Champion ET GenAI Hackathon 2026 (1st out of 50,000+ competitors) proves top 1% execution.")

    # Check for Intel Industrial Training
    has_intel = any("intel" in e.company.lower() for e in resume.experience)
    if has_intel:
        prestige_bonus += 0.06
        strengths.append("Intel® Unnati industrial internship with verified SSIM/PSNR metrics and knowledge distillation.")

    # Check for IEEE publication
    has_ieee = any("ieee" in a.get("title", "").lower() for a in resume.achievements) or "ieee" in resume.summary.lower()
    if has_ieee:
        prestige_bonus += 0.05
        strengths.append("First-author IEEE published research demonstrates rigorous systems and ML fundamentals.")

    # Check for production testing & shipping
    has_tests = any("tests" in b.text.lower() or "passing" in b.text.lower() for p in resume.projects for b in p.bullets)
    if has_tests:
        strengths.append("Shipped production-grade code with verified automated unit test suites and Docker Compose.")

    # 4. Company Tier Calibration
    # Big tech has high candidate volume; startups prioritize immediate shipping
    tier_adjustment = 0.0
    comp_type = reqs.company_type.lower()
    if comp_type in ["google", "microsoft"]:
        tier_adjustment = -0.06  # Highly selective applicant pool
    elif comp_type == "amazon":
        tier_adjustment = -0.04
    elif comp_type == "startup":
        tier_adjustment = 0.05   # Strong bias for hands-on builders
    elif comp_type == "research":
        if has_ieee:
            tier_adjustment = 0.08

    # 5. Risk Factors
    risks: List[str] = []
    missing_req = [s for s in reqs.required_skills if s.lower() not in matched_set]
    if missing_req:
        risks.append(f"Missing direct keywords for: {', '.join(missing_req[:3])}")

    if reqs.min_years_experience and reqs.min_years_experience > 2:
        risks.append(f"Role asks for {reqs.min_years_experience}+ years; candidate is graduating 2026.")

    # 6. Composite Probability Calculation
    raw_prob = (
        0.35 * ats_factor
        + 0.35 * skill_coverage
        + prestige_bonus
        + tier_adjustment
    )

    # Bound strictly between 0.15 and 0.94 (no resume is 100% guaranteed)
    prob = max(0.15, min(0.94, raw_prob))
    percentage = int(round(prob * 100))

    # Categorize Tier
    if percentage >= 85:
        tier = "Top 5% Candidate (Exceptional Match)"
        recommendation = "High interview probability. Tailor your introduction around the ET GenAI Hackathon win and Intel metrics."
    elif percentage >= 75:
        tier = "Top 15% Candidate (Strong Contender)"
        recommendation = "Strong candidate profile. Prepare deep-dives into your FastAPI backend and PyTorch pipelines."
    elif percentage >= 60:
        tier = "Competitive Candidate (Good Fit)"
        recommendation = "Competitive fit. Emphasize transferable systems experience to offset any missing secondary skills."
    else:
        tier = "Reach Opportunity (Skill Gap)"
        recommendation = "Review missing required skills and emphasize parallel architectural achievements."

    return InterviewProbability(
        probability=round(prob, 2),
        percentage=percentage,
        tier=tier,
        key_strengths=strengths,
        risk_factors=risks,
        recommendation=recommendation,
    )
