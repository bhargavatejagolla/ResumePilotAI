"""Phase 7 Smoke Test — Playwright PDF Rendering."""
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

import fitz
from app.layers.l2_candidate import load_candidate
from app.layers.l3_job import parse_jd
from app.layers.l4_intelligence.selector import build_plan
from app.layers.l5_generation.writer import fallback_to_plan
from app.layers.l7_render import render_html, render_pdf_sync

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
    print("  PHASE 7 SMOKE TEST — PLAYWRIGHT PDF RENDERING")
    print("=" * 70)

    # 1. Pipeline L1 -> L5
    print("\n[1] Running Pipeline L1 -> L5...")
    candidate = load_candidate()
    reqs, dna = parse_jd(SAMPLE_JD)
    plan = build_plan(candidate, reqs, dna)
    resume = fallback_to_plan(plan, reqs, dna, reason="Smoke test PDF")

    # 2. Render HTML
    print("\n[2] Rendering Self-Contained HTML...")
    html = render_html(resume)
    print(f"    HTML rendered successfully ({len(html)} chars)")
    assert "<!DOCTYPE html>" in html
    assert "@page" in html

    # 3. Render PDF via Playwright
    print("\n[3] Rendering PDF with Playwright Chromium...")
    output_pdf_path = backend_dir / "app" / "data" / "output_test_resume.pdf"
    pdf_bytes = render_pdf_sync(resume, output_path=str(output_pdf_path))
    print(f"    PDF bytes generated: {len(pdf_bytes)} bytes")
    print(f"    Saved to: {output_pdf_path}")

    # 4. Verify Page Count with PyMuPDF
    print("\n[4] Verifying Page Count...")
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_count = len(doc)
    print(f"    Verified PDF Page Count: {page_count} page(s)")
    assert page_count == 1, f"Expected strictly 1 page, got {page_count}!"

    print("\n[SUCCESS] Phase 7 PDF Engine fully verified and operating at 1-page perfection!")


if __name__ == "__main__":
    main()
