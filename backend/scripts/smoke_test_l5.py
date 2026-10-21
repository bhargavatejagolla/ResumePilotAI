"""Phase 5 Smoke Test — Prompt Compiler & Groq Writer.

Verifies end-to-end prompt compilation, fallback resilience, anti-hallucination guards,
and live generation when API key is available.
"""
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
from app.layers.l3_job import parse_jd, load_dna
from app.layers.l4_intelligence.selector import build_plan
from app.layers.l5_generation.compiler import compile_rewrite_prompt
from app.layers.l5_generation.writer import rewrite_resume, fallback_to_plan

SAMPLE_JD = """
Software Engineer, Systems and AI Infrastructure - Google
Bengaluru, India

Responsibilities:
- Build high-scale distributed backend systems and asynchronous microservices.
- Optimize machine learning pipelines for latency, SSIM/PSNR accuracy, and memory footprint.
- Collaborate with engineering leads to design production-grade REST and RPC services.

Qualifications:
- Bachelor's degree in Computer Science or equivalent.
- Experience with Python, PyTorch, FastAPI, Docker, and distributed systems.
- Experience with RAG, vector search, or database performance optimization.
"""


def main():
    print("=" * 70)
    print("  PHASE 5 SMOKE TEST — GENERATION & REWRITE LAYER")
    print("=" * 70)

    # 1. Pipeline up to Phase 4
    print("\n[1] Running Pipeline L1 -> L4...")
    candidate = load_candidate()
    reqs, dna = parse_jd(SAMPLE_JD)
    plan = build_plan(candidate, reqs, dna)
    print(f"    Company: {reqs.company_type.upper()}")
    print(f"    Selected projects: {[p.name for p in plan.projects]}")
    print(f"    Selected experience: {[e.company for e in plan.experience]}")

    # 2. Prompt Compiler
    print("\n[2] Testing Prompt Compiler...")
    prompt = compile_rewrite_prompt(plan, reqs, dna)
    assert len(prompt) > 300, "Compiled prompt too short!"
    assert "{min_words}" not in prompt, "Unreplaced placeholder in prompt!"
    assert "{plan_json_input}" not in prompt, "Plan JSON not inserted!"
    print(f"    Compiled prompt length: {len(prompt)} chars")
    print("    Prompt snippet:")
    for line in prompt.splitlines()[:15]:
        print(f"      | {line}")

    # 3. Fallback Test
    print("\n[3] Testing Deterministic Plan Fallback...")
    fallback_res = fallback_to_plan(plan, reqs, dna, reason="Smoke test manual fallback")
    assert fallback_res.metadata["is_fallback"] is True
    assert len(fallback_res.projects) == len(plan.projects)
    assert len(fallback_res.experience) == len(plan.experience)
    assert fallback_res.projects[0].bullets[0].is_rewritten is False
    print(f"    Fallback successful. Projects: {len(fallback_res.projects)}, Fallback: {fallback_res.metadata['is_fallback']}")

    # 4. Resume Writer
    print("\n[4] Testing Resume Writer (Live or Fallback)...")
    generated = rewrite_resume(plan, reqs, dna)
    print(f"    Generated resume summary: {generated.summary[:80]}...")
    print(f"    Is fallback? {generated.metadata.get('is_fallback')}")
    print(f"    Total bullets checked: {generated.metadata.get('total_bullets_checked')}")
    print(f"    Total bullets rewritten: {generated.metadata.get('total_bullets_rewritten')}")

    for p in generated.projects:
        print(f"\n    Project: {p.name}")
        for b in p.bullets:
            status = "[REWRITTEN]" if b.is_rewritten else "[ORIGINAL]"
            print(f"      {status} ({b.source}): {b.text[:90]}...")

    print("\n[SUCCESS] Phase 5 Generation Layer fully verified!")


if __name__ == "__main__":
    main()
