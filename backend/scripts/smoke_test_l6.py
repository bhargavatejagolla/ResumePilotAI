"""Phase 6 Smoke Test — ATS Engine, Interview Probability & Explainability."""
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.layers.l2_candidate import load_candidate
from app.layers.l3_job import parse_jd
from app.layers.l4_intelligence.selector import build_plan
from app.layers.l5_generation.writer import fallback_to_plan
from app.layers.l6_verification import verify_resume

SAMPLE_JD = """
Senior Distributed Systems Engineer - Amazon AWS
Bengaluru, India

Responsibilities:
- Architect high-throughput distributed microservices on AWS infrastructure.
- Build resilient backend systems using Python, FastAPI, Docker, and PostgreSQL.
- Drive latency reduction and high-concurrency scaling across tier-1 services.

Requirements:
- Bachelor's degree in Computer Science.
- Strong proficiency in Python, FastAPI, Microservices, and Cloud infrastructure.
- Proven track record of shipping production code with automated tests and CI/CD.
"""


def main():
    print("=" * 70)
    print("  PHASE 6 SMOKE TEST — VERIFICATION & ATS ENGINE")
    print("=" * 70)

    # 1. Pipeline L1 -> L5
    print("\n[1] Running Pipeline L1 -> L5...")
    candidate = load_candidate()
    reqs, dna = parse_jd(SAMPLE_JD)
    plan = build_plan(candidate, reqs, dna)
    resume = fallback_to_plan(plan, reqs, dna, reason="Smoke test resume")
    print(f"    Target: {reqs.company_type.upper()} ({reqs.company_name})")
    print(f"    Projects: {[p.name for p in resume.projects]}")

    # 2. Run Phase 6 Verification
    print("\n[2] Executing Phase 6 Verification...")
    result = verify_resume(resume, reqs)

    # 3. Print ATS Score Breakdown
    print("\n[3] ATS Score Breakdown:")
    print(f"    Total Composite ATS Score: {result.ats.total_score} / 100")
    print(f"    - Keyword Match Score:     {result.ats.keyword_match_score}%")
    print(f"    - Semantic Similarity:     {result.ats.semantic_similarity_score}%")
    print(f"    - Metric Density Score:    {result.ats.metric_density_score}%")
    print(f"    - Structure Health Score:  {result.ats.structure_score}%")
    print(f"    Matched keywords ({len(result.ats.matched_keywords)}): {', '.join(result.ats.matched_keywords[:6])}...")
    if result.ats.missing_keywords:
        print(f"    Missing keywords ({len(result.ats.missing_keywords)}): {', '.join(result.ats.missing_keywords[:4])}...")

    # 4. Print Interview Probability
    print("\n[4] Calibrated Interview Probability:")
    print(f"    Probability:  {result.interview_prob.percentage}% ({result.interview_prob.probability})")
    print(f"    Tier:         {result.interview_prob.tier}")
    print(f"    Key Strengths:")
    for s in result.interview_prob.key_strengths:
        print(f"      + {s}")
    if result.interview_prob.risk_factors:
        print(f"    Risk Factors:")
        for r in result.interview_prob.risk_factors:
            print(f"      - {r}")

    # 5. Print Explainability & Talking Points
    print("\n[5] Explainability & Talking Points:")
    for pt in result.explainability.interview_talking_points:
        print(f"    * {pt}")

    assert result.ats.total_score >= 60.0, "ATS score below baseline!"
    assert result.interview_prob.percentage >= 60, "Interview probability below baseline!"
    print("\n[SUCCESS] Phase 6 Verification Layer fully verified!")


if __name__ == "__main__":
    main()
