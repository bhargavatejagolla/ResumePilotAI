"""Run: python -m scripts.smoke_test_l4"""
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.layers.l2_candidate import load_candidate
from app.layers.l3_job import parse_jd
from app.layers.l4_intelligence.selector import build_plan


GOOGLE_JD = """AI Resident - Google DeepMind
Required: Python, PyTorch, TensorFlow, deep learning research.
Preferred: Publications in ML venues, LangGraph experience.
Responsibilities: Design and prototype novel algorithms, publish research.
"""

AMAZON_JD = """Software Development Engineer - AWS
Required: Python, Java, distributed systems, Docker, Kubernetes.
Preferred: AWS, REST APIs, CI/CD.
Responsibilities: Own end-to-end delivery, drive ownership, deliver results.
"""

STARTUP_JD = """Founding GenAI Engineer - stealth startup
Required: Python, LangGraph, LLM APIs, FastAPI.
Preferred: RAG, Chroma, React.
Responsibilities: Build and ship agentic features, wear many hats.
"""


def run(jd_text, label):
    print(f"\n{'='*70}\n📋 {label}\n{'='*70}")
    candidate = load_candidate()
    reqs, dna = parse_jd(jd_text)
    plan = build_plan(candidate, reqs, dna)

    print(f"Company type:  {reqs.company_type}")
    print(f"DNA tone:      {plan.metadata.get('dna_tone')}")
    print(f"Coverage:      {plan.metadata.get('coverage', 0)*100:.0f}%")

    print(f"\nSection order:")
    for s in plan.section_order:
        print(f"  → {s}")

    print(f"\nSummary ({plan.metadata.get('summary_word_count')} words):")
    print(f"  {plan.summary_draft}")

    print(f"\nSelected projects ({len(plan.projects)}):")
    for p in plan.projects:
        print(f"  [{p.total_score:.3f}] {p.name}")
        print(f"          relevance={p.relevance} impact={p.impact} "
              f"freshness={p.freshness} coverage={p.coverage}")
        for b in p.selected_bullets:
            icon = "📊" if b.has_metric else "  "
            print(f"          {icon} [{b.score:.3f}] {b.text[:90]}...")

    print(f"\nSelected experience ({len(plan.experience)}):")
    for e in plan.experience:
        print(f"  [{e.total_score:.3f}] {e.company} — {e.title}")
        for b in e.selected_bullets:
            icon = "📊" if b.has_metric else "  "
            print(f"          {icon} [{b.score:.3f}] {b.text[:90]}...")

    print(f"\nSkills ({sum(len(v) for v in plan.skills.values())} total):")
    for cat, items in plan.skills.items():
        print(f"  {cat}: {', '.join(items[:5])}{'...' if len(items)>5 else ''}")

    print(f"\nAchievements ({len(plan.achievements)}):")
    for a in plan.achievements:
        print(f"  • {a.get('title','')[:70]}")

    print(f"\nCertifications ({len(plan.certifications)}):")
    for c in plan.certifications:
        print(f"  • {c.get('name','')} — {c.get('issuer','')}")

    issues = plan.metadata.get("truth_issues", [])
    if issues:
        print(f"\n⚠️  Truth issues ({len(issues)}):")
        for i in issues:
            print(f"  • {i}")
    else:
        print(f"\n✅ Truth engine: no issues")

    return plan, issues


def main():
    for jd, label in [(GOOGLE_JD, "Google"), (AMAZON_JD, "Amazon"),
                      (STARTUP_JD, "Startup")]:
        plan, issues = run(jd, label)

        # Basic acceptance checks
        assert len(plan.projects) == 3, f"{label}: expected 3 projects"
        assert all(p.selected_bullets for p in plan.projects), "Empty project bullets"
        assert len(plan.summary_draft) > 100, "Summary draft too short"
        assert len(issues) == 0, f"{label}: truth issues {issues}"

    print(f"\n{'='*70}")
    print("🎉 Phase 4 complete. Deterministic ResumePlan produced for all 3 JDs.")
    print("   No Groq calls. No Chroma queries after initial load. Pure Python.\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
