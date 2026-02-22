"""Claude-powered translation engine for the Document Assembler.

Produces 3-part translation bundles: English translation PDF, original document,
and EOIR-compliant Certificate of Translation. Uses Claude via shared/claude_client.py.
"""

from __future__ import annotations

import io
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.claude_client import draft_with_claude

# US Letter dimensions in points
_PAGE_W = 612
_PAGE_H = 792

_SYSTEM_PROMPT = (
    "You are a professional legal translator. Translate the following text "
    "paragraph by paragraph from {source_lang} to {target_lang}. "
    "Maintain the original paragraph structure. For each paragraph, output "
    "the translation only — no commentary, no notes, no paragraph numbers. "
    "Separate paragraphs with a blank line. Preserve all proper nouns, "
    "dates, numbers, and legal terminology exactly as they appear. "
    "If a word or phrase has no direct translation, provide the closest "
    "equivalent and include the original term in parentheses."
)


def extract_text_from_pdf(file_bytes: bytes) -> list[str]:
    """Extract text from a PDF, returning a list of paragraphs.

    Uses PyMuPDF to read each page and splits on double newlines.
    """
    import pymupdf

    doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    paragraphs: list[str] = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if text.strip():
            page_paras = re.split(r"\n\s*\n", text.strip())
            for p in page_paras:
                cleaned = " ".join(p.split())
                if cleaned:
                    paragraphs.append(cleaned)
    doc.close()
    return paragraphs


def translate_with_claude(
    paragraphs: list[str],
    source_lang: str,
    target_lang: str = "English",
) -> list[dict]:
    """Translate paragraphs using Claude, chunking into ~3000-word batches.

    Returns a list of {original, translated} dicts.
    """
    results: list[dict] = []

    # Chunk paragraphs into batches of ~3000 words
    batches: list[list[str]] = []
    current_batch: list[str] = []
    current_words = 0

    for para in paragraphs:
        word_count = len(para.split())
        if current_words + word_count > 3000 and current_batch:
            batches.append(current_batch)
            current_batch = []
            current_words = 0
        current_batch.append(para)
        current_words += word_count

    if current_batch:
        batches.append(current_batch)

    system = _SYSTEM_PROMPT.format(source_lang=source_lang, target_lang=target_lang)

    for batch in batches:
        # Number paragraphs for alignment
        numbered = "\n\n".join(
            f"[{i+1}] {para}" for i, para in enumerate(batch)
        )
        user_msg = (
            f"Translate each numbered paragraph below from {source_lang} to "
            f"{target_lang}. Output each translation prefixed with the same "
            f"number in brackets. Do not include the original text.\n\n"
            f"{numbered}"
        )

        response = draft_with_claude(
            system_prompt=system,
            user_message=user_msg,
            max_tokens=8192,
            tool_name="document-assembler",
        )

        # Parse numbered translations from response
        translated_paras = _parse_numbered_response(response, len(batch))

        for i, para in enumerate(batch):
            results.append({
                "original": para,
                "translated": translated_paras[i] if i < len(translated_paras) else para,
            })

    return results


def _parse_numbered_response(response: str, expected_count: int) -> list[str]:
    """Parse numbered translation response into a list of paragraphs."""
    # Try to extract [1], [2], etc.
    parts: list[str] = []
    pattern = re.compile(r"\[(\d+)\]\s*")
    segments = pattern.split(response)

    # segments alternates: text_before, number, text, number, text, ...
    if len(segments) >= 3:
        # Skip the first segment (text before [1])
        for i in range(1, len(segments), 2):
            if i + 1 < len(segments):
                text = segments[i + 1].strip()
                parts.append(text)
    else:
        # Fallback: split on double newlines
        parts = [p.strip() for p in response.split("\n\n") if p.strip()]

    # Pad or trim to expected count
    while len(parts) < expected_count:
        parts.append("")

    return parts[:expected_count]


def build_translation_pdf(
    translated_paragraphs: list[dict],
    title: str,
) -> bytes:
    """Build a PDF containing the English translation.

    Header: "ENGLISH TRANSLATION" centered, bold.
    Subtitle: original document title.
    Body: 12pt Times New Roman, paragraph by paragraph.
    """
    import pymupdf

    doc = pymupdf.open()
    page = doc.new_page(width=_PAGE_W, height=_PAGE_H)

    # Margins: 1 inch = 72pt
    margin = 72
    y = margin
    text_width = _PAGE_W - 2 * margin

    # Header
    header_rect = pymupdf.Rect(margin, y, _PAGE_W - margin, y + 30)
    page.insert_textbox(
        header_rect,
        "ENGLISH TRANSLATION",
        fontsize=14,
        fontname="helv",
        align=1,  # center
        color=(0, 0, 0),
    )
    y += 36

    # Subtitle
    if title:
        sub_rect = pymupdf.Rect(margin, y, _PAGE_W - margin, y + 20)
        page.insert_textbox(
            sub_rect,
            title,
            fontsize=11,
            fontname="helv",
            align=1,
            color=(0.3, 0.3, 0.3),
        )
        y += 28

    # Divider line
    page.draw_line(
        pymupdf.Point(margin, y),
        pymupdf.Point(_PAGE_W - margin, y),
        color=(0.7, 0.7, 0.7),
        width=0.5,
    )
    y += 16

    # Body paragraphs
    for item in translated_paragraphs:
        text = item.get("translated", "")
        if not text:
            continue

        # Estimate height needed (rough: 14pt per line, ~80 chars per line)
        estimated_lines = max(1, len(text) / 75)
        estimated_height = estimated_lines * 16

        # Check if we need a new page
        if y + estimated_height > _PAGE_H - margin:
            page = doc.new_page(width=_PAGE_W, height=_PAGE_H)
            y = margin

        # Insert paragraph
        text_rect = pymupdf.Rect(margin, y, _PAGE_W - margin, y + max(estimated_height, 20))
        rc = page.insert_textbox(
            text_rect,
            text,
            fontsize=12,
            fontname="tiro",  # Times-like font
            align=0,
            color=(0, 0, 0),
        )
        # If text overflowed, the return is negative — add new page
        if rc < 0:
            # Text didn't fit; use a bigger box
            big_rect = pymupdf.Rect(margin, y, _PAGE_W - margin, _PAGE_H - margin)
            remaining = page.insert_textbox(
                big_rect,
                text,
                fontsize=12,
                fontname="tiro",
                align=0,
                color=(0, 0, 0),
            )
            y = _PAGE_H - margin
        else:
            y += estimated_height + 8

    result = doc.tobytes()
    doc.close()
    return result


def build_certificate_pdf(
    translator_name: str,
    translator_address: str,
    translator_phone: str,
    source_lang: str,
    target_lang: str,
    source_filename: str,
) -> bytes:
    """Build a single-page Certificate of Translation PDF.

    EOIR-compliant text following the Immigration Court Practice Manual format.
    """
    import pymupdf

    today = date.today().strftime("%m/%d/%Y")

    cert_body = (
        f"I, {translator_name}, of {translator_address}, hereby certify "
        f"that I am competent to translate from {source_lang} to "
        f"{target_lang}, and that the foregoing document, identified as "
        f'"{source_filename}," is a true and accurate translation of the '
        f"original to the best of my knowledge and ability."
    )

    doc = pymupdf.open()
    page = doc.new_page(width=_PAGE_W, height=_PAGE_H)

    margin = 72
    y = margin + 60

    # Title
    title_rect = pymupdf.Rect(margin, y, _PAGE_W - margin, y + 30)
    page.insert_textbox(
        title_rect,
        "CERTIFICATE OF TRANSLATION",
        fontsize=16,
        fontname="helv",
        align=1,
        color=(0, 0, 0),
    )
    y += 50

    # Body
    body_rect = pymupdf.Rect(margin, y, _PAGE_W - margin, y + 120)
    page.insert_textbox(
        body_rect,
        cert_body,
        fontsize=12,
        fontname="tiro",
        align=0,
        color=(0, 0, 0),
    )
    y += 140

    # Signature block
    lines = [
        f"Name: {translator_name}",
        f"Address: {translator_address}",
        f"Telephone: {translator_phone}",
        f"Date: {today}",
        "",
        "Signature: ____________________________",
    ]
    sig_text = "\n".join(lines)
    sig_rect = pymupdf.Rect(margin, y, _PAGE_W - margin, y + 130)
    page.insert_textbox(
        sig_rect,
        sig_text,
        fontsize=12,
        fontname="tiro",
        align=0,
        color=(0, 0, 0),
    )

    result = doc.tobytes()
    doc.close()
    return result


def create_translation_bundle(
    file_bytes: bytes,
    filename: str,
    source_lang: str,
    translator_info: dict,
    target_lang: str = "English",
) -> dict:
    """Create a complete 3-part translation bundle.

    Args:
        file_bytes: Original PDF bytes.
        filename: Original filename.
        source_lang: Source language name (e.g. "Spanish").
        translator_info: Dict with keys: name, address, phone.
        target_lang: Target language (default "English").

    Returns:
        {
            original_pdf: bytes,
            translated_pdf: bytes,
            certificate_pdf: bytes,
            page_count: int (of original),
            paragraphs: list[dict] ({original, translated}),
        }
    """
    # Extract text
    paragraphs = extract_text_from_pdf(file_bytes)

    # Translate
    translated = translate_with_claude(paragraphs, source_lang, target_lang)

    # Build translation PDF
    title = filename.rsplit(".", 1)[0] if "." in filename else filename
    translated_pdf = build_translation_pdf(translated, title)

    # Build certificate
    certificate_pdf = build_certificate_pdf(
        translator_name=translator_info.get("name", ""),
        translator_address=translator_info.get("address", ""),
        translator_phone=translator_info.get("phone", ""),
        source_lang=source_lang,
        target_lang=target_lang,
        source_filename=filename,
    )

    # Page count of original
    import pymupdf
    orig_doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    page_count = len(orig_doc)
    orig_doc.close()

    return {
        "original_pdf": file_bytes,
        "translated_pdf": translated_pdf,
        "certificate_pdf": certificate_pdf,
        "page_count": page_count,
        "paragraphs": translated,
    }
