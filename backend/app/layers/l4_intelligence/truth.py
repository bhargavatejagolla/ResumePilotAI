"""truth.py — verify every claim in the plan has a source and is consistent.

Runs after selection. Returns a list of human-readable issues (empty = clean).
Never blocks generation — issues are surfaced in Phase 6 explainability.
"""
import re
from typing import List
from app.schemas.resume import ResumePlan
from app.schemas.candidate import Candidate


_EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$")


def verify_plan(plan: ResumePlan, candidate: Candidate) -> List[str]:
    """Return a list of issues found in the plan. Empty = valid."""
    issues: List[str] = []

    # 1. Every bullet must have a source
    for proj in plan.projects:
        for b in proj.selected_bullets:
            if not b.source or not b.source.startswith("resume:"):
                issues.append(
                    f"Unsourced bullet in project '{proj.name}': "
                    f"{b.text[:60]}..."
                )

    for exp in plan.experience:
        for b in exp.selected_bullets:
            if not b.source or not b.source.startswith("resume:"):
                issues.append(
                    f"Unsourced bullet in experience '{exp.company}': "
                    f"{b.text[:60]}..."
                )

    # 2. Every project must have at least one bullet
    for proj in plan.projects:
        if not proj.selected_bullets:
            issues.append(f"Project '{proj.name}' has zero selected bullets")

    # 3. Summary must be within reasonable length
    wc = len(plan.summary_draft.split())
    if wc < 25:
        issues.append(f"Summary too short ({wc} words, min 25)")
    elif wc > 100:
        issues.append(f"Summary too long ({wc} words, max 100)")

    # 4. Personal info must have email
    email = plan.personal.get("email", "")
    if not email or not _EMAIL_RE.match(email):
        issues.append(f"Invalid or missing email: '{email}'")

    # 5. Section order must include required sections
    required_sections = {"summary", "skills", "experience", "projects", "education"}
    if not required_sections.issubset(set(plan.section_order)):
        missing = required_sections - set(plan.section_order)
        issues.append(f"Missing required sections: {sorted(missing)}")

    # 6. Achievements / certifications counts must be within limits
    if len(plan.achievements) > 4:
        issues.append(
            f"Too many achievements selected ({len(plan.achievements)}, max 4)"
        )

    # 7. No project should be selected twice
    names = [p.name for p in plan.projects]
    if len(names) != len(set(names)):
        issues.append("Duplicate project names detected")

    return issues
