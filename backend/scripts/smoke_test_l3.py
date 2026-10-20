"""Run: python -m scripts.smoke_test_l3"""
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.layers.l3_job import parse_jd, classify_company

# Three sample JDs — one per company type
SAMPLE_JDS = {
    "google_ai_resident": """
    AI Resident - Google DeepMind
    We are looking for a final-year student or recent graduate to join our AI Residency program.
    Required: Strong Python, PyTorch or TensorFlow, experience with deep learning research.
    Preferred: Publications in ML venues, experience with large-scale systems, LangGraph or similar agentic frameworks.
    Responsibilities: Design and prototype novel deep learning algorithms, publish research,
    collaborate with senior researchers on productionizing models.
    Education: B.Tech/B.S. in CS or related field, GPA 8.5+ preferred.
    """,

    "amazon_sde": """
    Software Development Engineer - Amazon Web Services
    We are looking for an SDE to help us scale our distributed cloud infrastructure.
    Required: Python, Java, or Go; strong understanding of distributed systems; experience with Docker and Kubernetes.
    Preferred: Experience with AWS, REST API design, CI/CD pipelines.
    Responsibilities: Own end-to-end delivery of services; design and implement highly available distributed systems;
    collaborate with teams to deliver customer-obsessed solutions. You will drive ownership and deliver results.
    """,

    "startup_genai": """
    Founding GenAI Engineer - Stealth Startup
    We're a small team building the future of AI-powered developer tools. We move fast and ship often.
    Required: Python, LangChain or LangGraph, LLM APIs (OpenAI, Anthropic), FastAPI.
    Preferred: RAG experience, vector databases (Pinecone, Chroma), React.
    Responsibilities: Build and ship agentic AI features end-to-end; own the full stack from backend to frontend;
    iterate fast with customer feedback; wear many hats. You'll be our 5th engineer.
    """,
}

CLASSIFICATION_MATRIX = {
    "google":     "We are Google. Required: Python, algorithms, scale, publications.",
    "amazon":     "Amazon Web Services. Customer obsession, ownership, deliver results.",
    "microsoft":  "Microsoft Azure. Engineering collaboration, growth mindset, systems.",
    "research":   "OpenAI Research. PhD required, publications in NeurIPS/ICML.",
    "startup":    "Stealth startup. Move fast, wear many hats, ship often.",
    "generic":    "Company seeks software engineer. Required: Python, SQL.",
}


def main():
    all_pass = True

    print("\n🔍 Running Company Classification Matrix...")
    for expected, snippet in CLASSIFICATION_MATRIX.items():
        result = classify_company(snippet, "")
        icon = "✅" if result["company_type"] == expected else "⚠️"
        print(f"  {icon} {expected:<10} → {result['company_type']:<10} (conf={result['confidence']:.2f})")
        if result["company_type"] != expected:
            all_pass = False

    for name, jd in SAMPLE_JDS.items():
        print(f"\n{'='*60}")
        print(f"📋 Testing: {name}")
        print(f"{'='*60}")

        try:
            reqs, dna = parse_jd(jd)
        except Exception as e:
            print(f"❌ FAILED: {e}")
            all_pass = False
            continue

        print(f"  Title:           {reqs.job_title}")
        print(f"  Company type:    {reqs.company_type}  (conf={reqs.classification_confidence:.2f})")
        print(f"  DNA loaded:      {dna.get('name', '')}  (tone={dna.get('tone', '')})")
        print(f"  Domain:          {reqs.domain}")
        print(f"  Required skills: {reqs.required_skills[:5]}...")
        print(f"  JD embedding:    dim={len(reqs.jd_embedding)}")

        # Verify embedding dimension
        if len(reqs.jd_embedding) != 384:
            print(f"  ❌ Embedding dim is {len(reqs.jd_embedding)}, expected 384")
            all_pass = False

        # Print skill evidence
        print(f"  Skill evidence ({len(reqs.skill_evidence)} skills checked):")
        for skill, ev in list(reqs.skill_evidence.items())[:8]:
            icon = "✅" if ev.status == "known" else "🟡" if ev.status == "likely" else "❌"
            print(f"    {icon} {skill:<22} → {ev.status:<8}  [{ev.evidence or 'no evidence'}]")

        # Verify at least one skill is "known" or "likely"
        known_count = sum(1 for ev in reqs.skill_evidence.values() if ev.status in ("known", "likely"))
        if known_count == 0:
            print(f"  ⚠️ Warning: No skills matched. Check Phase 2 index.")
            all_pass = False

    print(f"\n{'='*60}")
    if all_pass:
        print("🎉 Phase 3 complete. All 3 JDs parsed and classified correctly.\n")
        sys.exit(0)
    print("❌ Some tests failed. Inspect output above.\n")
    sys.exit(1)


if __name__ == "__main__":
    main()
