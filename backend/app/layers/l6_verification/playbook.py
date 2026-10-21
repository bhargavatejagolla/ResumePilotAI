"""Post-Generation 30-Day Improvement Playbook (Upgrade #3).

Generates an actionable 30-day sprint plan to bridge any remaining skill or metric gaps
for a specific target job posting.
"""
from typing import List

from app.schemas.candidate import Candidate
from app.schemas.job import JobRequirements
from app.schemas.verification import ATSScoreBreakdown, SprintWeek, ImprovementPlaybook


def generate_improvement_playbook(
    candidate: Candidate,
    reqs: JobRequirements,
    ats: ATSScoreBreakdown,
) -> ImprovementPlaybook:
    """Generate a dynamic 30-day interview readiness plan."""
    missing = ats.missing_keywords[:4]
    role = reqs.job_title or "Software Engineer"
    company = reqs.company_name or reqs.company_type.upper()

    curr_score = int(round(ats.total_score))
    projected = min(96, curr_score + 18)

    primary_missing = missing[0] if missing else "Cloud Microservices"
    secondary_missing = missing[1] if len(missing) > 1 else "Automated Benchmarks"

    weeks: List[SprintWeek] = [
        SprintWeek(
            week_number=1,
            title=f"Core Ramp-Up: {primary_missing}",
            focus="Bridge the primary missing keyword with a functional prototype.",
            action_items=[
                f"Clone a modern template implementing {primary_missing} in Python or your primary stack.",
                f"Build a minimal working endpoint or pipeline integrating {primary_missing} with your existing projects.",
                "Commit code to GitHub with clear README architectural diagrams.",
            ],
            deliverable=f"Public GitHub repo featuring {primary_missing} integration.",
        ),
        SprintWeek(
            week_number=2,
            title="Metric Quantization & Benchmarking",
            focus="Transform qualitative claims into verifiable numbers.",
            action_items=[
                "Profile API response times (p95 latency) using Locust or pytest-benchmark.",
                "Calculate parameter count, dataset volume, or queries per second handled.",
                "Draft 2 new metric-dense bullets following the STAR (Situation-Task-Action-Result) format.",
            ],
            deliverable="Benchmarked metrics document with verified latency and throughput figures.",
        ),
        SprintWeek(
            week_number=3,
            title="Production Readiness & CI/CD",
            focus="Signal senior-level engineering maturity to hiring managers.",
            action_items=[
                "Containerize your prototype with Docker and multi-stage builds.",
                "Add GitHub Actions CI pipeline executing automated unit tests on every commit.",
                f"Incorporate {secondary_missing} into your workflow documentation.",
            ],
            deliverable="Green CI/CD build badge and Docker Compose one-command launch.",
        ),
        SprintWeek(
            week_number=4,
            title="Re-Synthesis & Interview Rehearsal",
            focus="Update candidate profile and rehearse technical defense.",
            action_items=[
                "Add newly verified bullets to your candidate knowledge base.",
                f"Re-run ResumePilot AI against this {company} {role} JD to observe the updated ATS score ({projected}%+).",
                "Rehearse your top 3 STAR talking points focusing on your hackathon victory and engineering depth.",
            ],
            deliverable="Updated tailored resume achieving 88%+ ATS and top-tier interview probability.",
        ),
    ]

    summary = (
        f"You currently match {curr_score}% of the requirements for {role} at {company}. "
        f"By tackling {primary_missing} and tightening your project metrics across this 30-day sprint, "
        f"your calibrated interview probability will rise into the top 5% candidate tier."
    )

    return ImprovementPlaybook(
        target_role=role,
        target_company=company,
        current_match_percentage=curr_score,
        projected_match_percentage=projected,
        missing_critical_skills=missing,
        sprint_weeks=weeks,
        advisor_summary=summary,
    )
