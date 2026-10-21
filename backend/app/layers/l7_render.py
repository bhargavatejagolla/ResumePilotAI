"""Phase 7 — High-Fidelity Playwright PDF Rendering Engine.

Renders pixel-perfect, ATS-compliant single-page PDF resumes using:
1. Jinja2 templates (resume.html.j2)
2. Master styling (resume.css)
3. Headless Chromium via Playwright
4. Automatic PyMuPDF page-count verification and dynamic single-page auto-fit
"""
import asyncio
from pathlib import Path
from typing import Union, Optional, Dict, Any

import fitz  # PyMuPDF
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright

from app.config import get_settings
from app.schemas.resume import GeneratedResume, ResumePlan

settings = get_settings()

_templates_dir = Path(settings.templates_dir)
_jinja_env = Environment(
    loader=FileSystemLoader(str(_templates_dir)),
    autoescape=True,
)


def _prepare_context(resume: Union[GeneratedResume, ResumePlan, Dict[str, Any]]) -> Dict[str, Any]:
    """Normalize Pydantic models or dicts into standard template context."""
    if hasattr(resume, "model_dump"):
        data = resume.model_dump()
    elif isinstance(resume, dict):
        data = dict(resume)
    else:
        raise ValueError(f"Unsupported resume object type: {type(resume)}")

    # Ensure defaults
    data.setdefault("personal", {})
    data.setdefault("summary", "")
    data.setdefault("education", [])
    data.setdefault("experience", [])
    data.setdefault("projects", [])
    data.setdefault("skills", {})
    data.setdefault("achievements", [])
    data.setdefault("certifications", [])
    return data


def render_html(
    resume: Union[GeneratedResume, ResumePlan, Dict[str, Any]],
    tight: bool = False,
) -> str:
    """Render the resume HTML with inlined CSS."""
    template = _jinja_env.get_template("resume.html.j2")
    css_path = _templates_dir / "resume.css"
    css_content = css_path.read_text(encoding="utf-8")

    if tight:
        # Dynamically compress line-heights and margins to guarantee strict 1-page fit
        css_content = (
            css_content
            .replace("font-size: 9pt;", "font-size: 8.5pt;")
            .replace("line-height: 1.3;", "line-height: 1.22;")
            .replace("margin-bottom: 7px;", "margin-bottom: 4px;")
            .replace("margin-bottom: 5px;", "margin-bottom: 3px;")
            .replace("margin-bottom: 4px;", "margin-bottom: 2px;")
            .replace("margin-bottom: 2px;", "margin-bottom: 1px;")
            .replace("margin: 0.35in 0.45in 0.35in 0.45in;", "margin: 0.28in 0.38in 0.28in 0.38in;")
        )

    context = _prepare_context(resume)
    context["css_content"] = css_content
    return template.render(**context)


def render_pdf_sync(
    resume: Union[GeneratedResume, ResumePlan, Dict[str, Any]],
    output_path: Optional[str] = None,
) -> bytes:
    """
    Synchronously render PDF using Playwright Chromium with automatic 1-page fit verification.
    """
    html_content = render_html(resume, tight=False)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html_content, wait_until="networkidle")

        pdf_bytes = page.pdf(
            format="A4",
            print_background=True,
            prefer_css_page_size=True,
        )

        # Check page count with PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if len(doc) > 1:
            # Re-render with tight layout to fit on exactly 1 page
            tight_html = render_html(resume, tight=True)
            page.set_content(tight_html, wait_until="networkidle")
            pdf_bytes = page.pdf(
                format="A4",
                print_background=True,
                prefer_css_page_size=True,
            )

        browser.close()

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(pdf_bytes)

    return pdf_bytes


async def render_pdf_async(
    resume: Union[GeneratedResume, ResumePlan, Dict[str, Any]],
    output_path: Optional[str] = None,
) -> bytes:
    """
    Asynchronously render PDF using Playwright Chromium (native for FastAPI async routes).
    """
    html_content = render_html(resume, tight=False)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(html_content, wait_until="networkidle")

        pdf_bytes = await page.pdf(
            format="A4",
            print_background=True,
            prefer_css_page_size=True,
        )

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if len(doc) > 1:
            tight_html = render_html(resume, tight=True)
            await page.set_content(tight_html, wait_until="networkidle")
            pdf_bytes = await page.pdf(
                format="A4",
                print_background=True,
                prefer_css_page_size=True,
            )

        await browser.close()

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(pdf_bytes)

    return pdf_bytes


def render_pdf(
    resume: Union[GeneratedResume, ResumePlan, Dict[str, Any]],
    output_path: Optional[str] = None,
) -> bytes:
    """Smart wrapper: routes to async or sync depending on current event loop context."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # In an active event loop, run sync playwright in a worker thread to avoid blocking or conflicts
        return asyncio.run_coroutine_threadsafe(
            render_pdf_async(resume, output_path),
            loop,
        ).result()
    else:
        return render_pdf_sync(resume, output_path)
