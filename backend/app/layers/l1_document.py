from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import fitz  # PyMuPDF
import re
from statistics import median


@dataclass
class Span:
    text: str
    font: str
    size: float
    bold: bool
    italic: bool
    x: float
    y: float
    page: int
    block_no: int
    line_no: int

    def to_dict(self) -> dict:
        return asdict(self)


def extract_spans(pdf_path: str) -> List[Span]:
    """
    Extract every text span from a PDF with full layout metadata.
    """
    doc = fitz.open(pdf_path)
    spans: List[Span] = []

    for page_no in range(len(doc)):
        page = doc.load_page(page_no)
        page_dict = page.get_text("dict")

        for block in page_dict.get("blocks", []):
            if "lines" not in block:  # skip image blocks
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "")
                    if not text.strip():
                        continue

                    # Bold detection: bit 4 of flags is bold, or font name has bold
                    font_lower = span.get("font", "").lower()
                    is_bold = bool(span.get("flags", 0) & (1 << 4)) or ("bold" in font_lower) or ("black" in font_lower)
                    is_italic = bool(span.get("flags", 0) & (1 << 1)) or ("italic" in font_lower)

                    spans.append(Span(
                        text=text,
                        font=span.get("font", ""),
                        size=round(span.get("size", 0.0), 1),
                        bold=is_bold,
                        italic=is_italic,
                        x=round(span.get("bbox", [0, 0, 0, 0])[0], 1),
                        y=round(span.get("bbox", [0, 0, 0, 0])[1], 1),
                        page=page_no,
                        block_no=block.get("number", 0),
                        line_no=line.get("number", 0),
                    ))

    doc.close()
    return spans


def _reading_order(spans: List[Span]) -> List[Span]:
    """Sort spans by page, then y (top->bottom, grouped to nearest 2pt), then x (left->right)."""
    return sorted(spans, key=lambda s: (s.page, round(s.y / 2) * 2, s.x))


SECTION_PATTERNS = {
    "summary":       r"(?i)^(profile\s*summary|professional\s*summary|summary|objective|about(\s*me)?)$",
    "education":     r"(?i)^(education|academic\s*background|qualifications?)$",
    "experience":    r"(?i)^(internship(\s*experience)?|work\s*experience|experience|employment)$",
    "projects":      r"(?i)^(projects?|personal\s*projects?|key\s*projects?)$",
    "skills":        r"(?i)^(skills?|technical\s*skills?|technologies|core\s*competencies)$",
    "achievements":  r"(?i)^(achievements?|awards?|honou?rs?|honors\s*&\s*achievements?)$",
    "publications":  r"(?i)^(publications?|papers?|research(\s*publications?)?)$",
    "certifications":r"(?i)^(certifications?|certificates?)$",
    "languages":     r"(?i)^(languages?)$",
}


def _map_heading(text: str) -> Optional[str]:
    clean = text.strip().rstrip(":").strip()
    for key, pattern in SECTION_PATTERNS.items():
        if re.match(pattern, clean):
            return key
    return None


def detect_sections(spans: List[Span]) -> Dict[str, List[Span]]:
    """
    Deterministic heading + section detection.
    """
    ordered = _reading_order(spans)
    if not ordered:
        return {}

    sizes = [s.size for s in ordered]
    doc_median = median(sizes) if sizes else 10.0

    sections: Dict[str, List[Span]] = {}
    current_key: Optional[str] = None

    for span in ordered:
        text_clean = span.text.strip()
        is_large = span.size > doc_median * 1.2
        is_short = len(text_clean) <= 40
        is_heading_style = is_large or (
            span.size >= doc_median and (span.bold or text_clean.isupper()) and is_short
        )

        if is_heading_style and is_short:
            mapped = _map_heading(text_clean)
            if mapped:
                current_key = mapped
                sections.setdefault(current_key, [])
                continue

        if current_key:
            sections[current_key].append(span)

    return sections


def extract_sections_text(sections: Dict[str, List[Span]]) -> Dict[str, str]:
    """
    Convert each section's spans into a single clean text block.
    """
    result = {}
    for key, spans in sections.items():
        lines = []
        current_y = None
        current_line = []
        for s in spans:
            if current_y is None or abs(s.y - current_y) <= 2.5:
                current_line.append(s.text)
                current_y = s.y if current_y is None else current_y
            else:
                lines.append(" ".join(current_line).strip())
                current_line = [s.text]
                current_y = s.y
        if current_line:
            lines.append(" ".join(current_line).strip())

        result[key] = "\n".join(lines)
    return result


def parse_resume_layout(pdf_path: str) -> Dict[str, str]:
    """
    Full pipeline: PDF -> {section_key: section_text}.
    """
    spans = extract_spans(pdf_path)
    sections = detect_sections(spans)
    return extract_sections_text(sections)
