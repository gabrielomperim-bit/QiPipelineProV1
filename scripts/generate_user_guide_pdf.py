from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "guia_usuario_qitech_pipeline_pro.md"
OUTPUT = ROOT / "docs" / "guia_usuario_qitech_pipeline_pro.pdf"

PAGE_WIDTH = 595
PAGE_HEIGHT = 842
LEFT = 54
RIGHT = 54
TOP = 64
BOTTOM = 54
FONT_SIZE = 11
LINE_HEIGHT = 15
MAX_WIDTH = PAGE_WIDTH - LEFT - RIGHT


@dataclass
class Line:
    text: str
    kind: str


def read_sections(path: Path) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    current_title = ""
    current_lines: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            if current_title:
                sections.append((current_title, current_lines))
            current_title = line[3:].strip()
            current_lines = []
            continue
        current_lines.append(raw_line.rstrip())
    if current_title:
        sections.append((current_title, current_lines))
    return sections


def build_document_lines(sections: list[tuple[str, list[str]]]) -> tuple[list[Line], dict[str, int]]:
    toc_entries = [title for title, _ in sections]
    body_lines: list[Line] = []
    section_pages: dict[str, int] = {}

    title_block = [
        Line("QITech Pipeline Pro", "title"),
        Line("Guia de Usuario", "subtitle"),
        Line("", "blank"),
    ]
    body_lines.extend(title_block)

    current_page = 1
    current_y = PAGE_HEIGHT - TOP

    def push(line: Line) -> None:
        nonlocal current_page, current_y
        height = line_height_for(line.kind)
        if current_y - height < BOTTOM:
            current_page += 1
            current_y = PAGE_HEIGHT - TOP
        body_lines.append(line)
        current_y -= height

    for title, raw_lines in sections:
        if title == "Sumario":
            continue
        section_pages[title] = current_page
        push(Line(title, "h1"))
        for line in normalize_section_lines(raw_lines):
            push(line)
        push(Line("", "blank"))

    toc_lines = title_block[:]
    toc_lines.append(Line("Sumario", "h1"))
    for idx, title in enumerate(toc_entries, start=1):
        page = 1 if title == "Sumario" else section_pages.get(title, 1)
        dots = "." * max(4, 52 - len(title))
        toc_lines.append(Line(f"{idx}. {title} {dots} {page}", "toc"))
    toc_lines.append(Line("", "blank"))

    return toc_lines + body_lines[3:], section_pages


def normalize_section_lines(raw_lines: list[str]) -> list[Line]:
    lines: list[Line] = []
    for raw in raw_lines:
        stripped = raw.strip()
        if not stripped:
            lines.append(Line("", "blank"))
            continue
        if stripped.startswith("### "):
            lines.append(Line(stripped[4:].strip(), "h2"))
            continue
        if stripped.startswith("- "):
            bullet = wrap_text(f"- {stripped[2:].strip()}", MAX_WIDTH, FONT_SIZE)
            lines.extend(Line(part, "body") for part in bullet)
            continue
        if re.match(r"^\d+\.\s", stripped):
            wrapped = wrap_text(stripped, MAX_WIDTH, FONT_SIZE)
            lines.extend(Line(part, "body") for part in wrapped)
            continue
        wrapped = wrap_text(stripped, MAX_WIDTH, FONT_SIZE)
        lines.extend(Line(part, "body") for part in wrapped)
    return lines


def wrap_text(text: str, max_width: int, font_size: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if text_width(candidate, font_size) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def text_width(text: str, font_size: int) -> float:
    base = 0.56 * font_size
    return sum(base * char_factor(char) for char in text)


def char_factor(char: str) -> float:
    if char in "ilI.,:;|!":
        return 0.45
    if char in "mwMW@#%&":
        return 1.2
    if char == " ":
        return 0.45
    return 0.9


def line_height_for(kind: str) -> int:
    return {
        "title": 30,
        "subtitle": 22,
        "h1": 24,
        "h2": 18,
        "toc": 15,
        "blank": 10,
    }.get(kind, LINE_HEIGHT)


def font_for(kind: str) -> tuple[str, int]:
    if kind == "title":
        return "F2", 22
    if kind == "subtitle":
        return "F1", 15
    if kind == "h1":
        return "F2", 15
    if kind == "h2":
        return "F2", 12
    if kind == "toc":
        return "F1", 11
    return "F1", FONT_SIZE


def paginate(lines: list[Line]) -> list[list[Line]]:
    pages: list[list[Line]] = []
    current: list[Line] = []
    y = PAGE_HEIGHT - TOP
    for line in lines:
        height = line_height_for(line.kind)
        if y - height < BOTTOM:
            pages.append(current)
            current = []
            y = PAGE_HEIGHT - TOP
        current.append(line)
        y -= height
    if current:
        pages.append(current)
    return pages


def escape_pdf_text(text: str) -> str:
    replacements = {
        "\\": "\\\\",
        "(": "\\(",
        ")": "\\)",
    }
    return "".join(replacements.get(char, char) for char in text)


def build_content_stream(lines: list[Line], page_number: int) -> bytes:
    parts = ["BT"]
    y = PAGE_HEIGHT - TOP
    for line in lines:
        font_name, font_size = font_for(line.kind)
        if line.kind != "blank":
            parts.append(f"/{font_name} {font_size} Tf")
            parts.append(f"1 0 0 1 {LEFT} {y} Tm")
            parts.append(f"({escape_pdf_text(line.text)}) Tj")
        y -= line_height_for(line.kind)
    parts.append(f"/F1 9 Tf")
    parts.append(f"1 0 0 1 {PAGE_WIDTH - RIGHT - 24} {BOTTOM - 14} Tm")
    parts.append(f"({page_number}) Tj")
    parts.append("ET")
    return "\n".join(parts).encode("latin-1", errors="replace")


def build_pdf(pages: list[list[Line]]) -> bytes:
    objects: list[bytes] = []

    def add_object(data: bytes) -> int:
        objects.append(data)
        return len(objects)

    font_regular = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    font_bold = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")

    pages_id = add_object(b"<< /Type /Pages /Count 0 /Kids [] >>")
    page_ids = []

    for index, page_lines in enumerate(pages, start=1):
        content = build_content_stream(page_lines, index)
        content_id = add_object(b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream")
        page_obj = (
            f"<< /Type /Page /Parent {pages_id} 0 R "
            f"/MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
            f"/Resources << /Font << /F1 {font_regular} 0 R /F2 {font_bold} 0 R >> >> "
            f"/Contents {content_id} 0 R >>"
        ).encode("latin-1")
        page_ids.append(add_object(page_obj))

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[pages_id - 1] = f"<< /Type /Pages /Count {len(page_ids)} /Kids [{kids}] >>".encode("latin-1")
    catalog_id = add_object(f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode("latin-1"))

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("latin-1"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
            f"startxref\n{xref_start}\n%%EOF"
        ).encode("latin-1")
    )
    return bytes(pdf)


def main() -> None:
    sections = read_sections(SOURCE)
    lines, _ = build_document_lines(sections)
    pages = paginate(lines)
    OUTPUT.write_bytes(build_pdf(pages))
    print(f"PDF gerado em: {OUTPUT}")


if __name__ == "__main__":
    main()
