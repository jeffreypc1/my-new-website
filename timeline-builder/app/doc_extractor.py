"""PDF text extraction and AI-powered timeline event extraction.

Uses pymupdf for per-page text extraction and the shared Claude client
for batched event extraction from document text.
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.events import CATEGORY_DESCRIPTIONS, EVENT_CATEGORIES

BATCH_SIZE = 25  # pages per AI call


def extract_pages_from_pdf(pdf_bytes: bytes) -> list[str]:
    """Extract text from each page of a PDF.

    Returns a list where index 0 = page 1 text, etc.
    Page numbering is preserved (empty pages return empty strings).
    """
    import pymupdf

    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    pages: list[str] = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()
    return pages


def _build_system_prompt(categories: list[str]) -> str:
    """Build the system prompt for Claude event extraction."""
    cat_lines = "\n".join(
        f"- {cat}: {CATEGORY_DESCRIPTIONS.get(cat, '')}"
        for cat in categories
    )
    return f"""You are a senior legal analyst extracting chronological events from case documents for an immigration attorney.

Your task:
1. Read the provided document pages carefully.
2. Extract every dated or datable event mentioned in the text.
3. For each event, determine the most specific date possible (exact date, month+year, or year).
4. Categorize each event into one of these categories:
{cat_lines}

Rules:
- Include pinpoint page citations for every event.
- ALWAYS format dates as "Month Day, Year" (e.g. "January 15, 2019"). If only month and year are known, use "January 2019". If only the year, use "2019". Never use numeric formats like "01/15/2019" or "2019-01-15".
- The "source" field must be the document name and page number, e.g. "Medical_Records.pdf, Page 4".
- If a single passage describes multiple distinct events, extract each as a separate entry.
- Do NOT fabricate or infer events that are not clearly stated in the text.
- Return ONLY a JSON array — no commentary, no markdown fences.

Response format — a JSON array of objects:
[
  {{
    "date": "March 15, 2019",
    "category": "Medical",
    "title": "Short event title",
    "description": "Detailed description of the event. [Source, Page N]"
  }}
]"""


def _build_user_message(doc_name: str, pages: list[str], start_page: int) -> str:
    """Build the user message for a batch of pages."""
    parts: list[str] = [f'Document: "{doc_name}"\n']
    for i, text in enumerate(pages):
        page_num = start_page + i
        parts.append(f"[Page {page_num}]\n{text}\n")
    return "\n".join(parts)


def _parse_ai_response(raw: str) -> list[dict]:
    """Parse Claude's JSON response, handling markdown fences."""
    cleaned = raw.strip()
    # Strip markdown code fences if present
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    cleaned = cleaned.strip()

    try:
        result = json.loads(cleaned)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # Try to find a JSON array in the response
    match = re.search(r"\[.*\]", cleaned, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    return []


def extract_events_from_documents(
    docs: list[dict],
    categories: list[str],
    on_progress: Callable[[int, int], None] | None = None,
) -> list[dict]:
    """Extract timeline events from multiple documents using Claude AI.

    Parameters
    ----------
    docs : list[dict]
        Each dict has ``"name"`` (filename) and ``"pages"`` (list of page text strings).
    categories : list[str]
        The event categories to map to (e.g. keys of EVENT_CATEGORIES).
    on_progress : callable, optional
        Called with ``(completed_batches, total_batches)`` after each batch.

    Returns
    -------
    list[dict]
        Extracted events with keys: date, category, title, description, source.
    """
    from shared.claude_client import draft_with_claude

    system_prompt = _build_system_prompt(categories)

    # Count total batches for progress
    total_batches = 0
    for doc in docs:
        page_count = len(doc["pages"])
        total_batches += max(1, (page_count + BATCH_SIZE - 1) // BATCH_SIZE)

    all_events: list[dict] = []
    completed = 0
    errors: list[str] = []

    for doc in docs:
        doc_name = doc["name"]
        pages = doc["pages"]

        for batch_start in range(0, max(len(pages), 1), BATCH_SIZE):
            batch_pages = pages[batch_start : batch_start + BATCH_SIZE]
            if not batch_pages or all(not p.strip() for p in batch_pages):
                completed += 1
                if on_progress:
                    on_progress(completed, total_batches)
                continue

            # Page numbers are 1-indexed
            start_page = batch_start + 1
            user_message = _build_user_message(doc_name, batch_pages, start_page)

            try:
                raw_response = draft_with_claude(
                    system_prompt=system_prompt,
                    user_message=user_message,
                    max_tokens=4096,
                    tool_name="timeline-builder",
                )
                parsed = _parse_ai_response(raw_response)
                for event in parsed:
                    # Ensure source citation is in the description
                    source = event.get("source", f"{doc_name}")
                    desc = event.get("description", "")
                    # Only append if the doc name doesn't already appear in a bracket citation
                    if source and doc_name not in desc:
                        desc = f"{desc} [{source}]" if desc else f"[{source}]"

                    all_events.append({
                        "date": event.get("date", ""),
                        "category": event.get("category", "Personal"),
                        "title": event.get("title", "Untitled event"),
                        "description": desc,
                        "source": source,
                    })
            except Exception as exc:
                errors.append(f"{doc_name} (pages {start_page}-{start_page + len(batch_pages) - 1}): {exc}")

            completed += 1
            if on_progress:
                on_progress(completed, total_batches)

    return all_events


def compile_exhibit_pdf(docs: list[dict]) -> tuple[bytes, list[dict]]:
    """Merge source PDFs into an exhibit package with TOC and separator pages.

    Parameters
    ----------
    docs : list[dict]
        Each dict has ``"name"`` (str) and ``"pdf_bytes"`` (bytes).

    Returns
    -------
    tuple[bytes, list[dict]]
        (merged_pdf_bytes, page_map) where page_map entries have:
        name, start_page, end_page, num_pages.
    """
    import pymupdf

    merged = pymupdf.open()

    # First pass: figure out page counts so we can build the TOC
    doc_info: list[dict] = []
    for d in docs:
        src = pymupdf.open(stream=d["pdf_bytes"], filetype="pdf")
        doc_info.append({"name": d["name"], "num_pages": len(src), "doc": src})

    # Page 1 is the TOC. Then for each doc: 1 separator + N pages.
    # Calculate page ranges.
    current_page = 2  # page 1 = TOC, so first content starts at 2
    page_map: list[dict] = []
    for info in doc_info:
        separator_page = current_page
        content_start = current_page + 1  # after separator
        content_end = content_start + info["num_pages"] - 1
        page_map.append({
            "name": info["name"],
            "start_page": content_start,
            "end_page": content_end,
            "num_pages": info["num_pages"],
            "separator_page": separator_page,
        })
        current_page = content_end + 1

    # -- Build TOC page --
    toc_page = merged.new_page(width=612, height=792)
    # Title
    y = 72
    toc_page.insert_text(
        pymupdf.Point(72, y), "EXHIBIT PACKAGE — TABLE OF CONTENTS",
        fontsize=16, fontname="helv",
    )
    y += 36
    toc_page.insert_text(
        pymupdf.Point(72, y),
        f"Documents: {len(doc_info)}  |  "
        f"Total pages: {current_page - 1}",
        fontsize=10, fontname="helv", color=(0.35, 0.35, 0.35),
    )
    y += 30

    # Draw a line
    toc_page.draw_line(pymupdf.Point(72, y), pymupdf.Point(540, y),
                       color=(0.8, 0.8, 0.8), width=0.5)
    y += 20

    # Column headers
    toc_page.insert_text(pymupdf.Point(72, y), "#", fontsize=9,
                         fontname="helvetica-bold", color=(0.4, 0.4, 0.4))
    toc_page.insert_text(pymupdf.Point(96, y), "Document", fontsize=9,
                         fontname="helvetica-bold", color=(0.4, 0.4, 0.4))
    toc_page.insert_text(pymupdf.Point(370, y), "Pages in Exhibit", fontsize=9,
                         fontname="helvetica-bold", color=(0.4, 0.4, 0.4))
    y += 16

    for idx, pm in enumerate(page_map):
        if y > 720:
            # New page if TOC overflows
            toc_page = merged.new_page(width=612, height=792)
            # Shift all page numbers forward by 1
            for p in page_map:
                p["start_page"] += 1
                p["end_page"] += 1
                p["separator_page"] += 1
            current_page += 1
            y = 72

        name = pm["name"]
        if len(name) > 50:
            name = name[:47] + "..."

        toc_page.insert_text(pymupdf.Point(72, y), f"{idx + 1}.",
                             fontsize=10, fontname="helv")
        toc_page.insert_text(pymupdf.Point(96, y), name,
                             fontsize=10, fontname="helv")
        toc_page.insert_text(
            pymupdf.Point(370, y),
            f"pp. {pm['start_page']}–{pm['end_page']}  ({pm['num_pages']} pg)",
            fontsize=10, fontname="helv", color=(0.3, 0.3, 0.5),
        )
        y += 18

    # -- Insert separator + pages for each document --
    for idx, (info, pm) in enumerate(zip(doc_info, page_map)):
        # Separator page
        sep = merged.new_page(width=612, height=792)
        # Centered document name
        sep.insert_text(
            pymupdf.Point(72, 320), f"Document {idx + 1}",
            fontsize=12, fontname="helv", color=(0.5, 0.5, 0.5),
        )
        sep.insert_text(
            pymupdf.Point(72, 350), info["name"],
            fontsize=18, fontname="helvetica-bold",
        )
        sep.insert_text(
            pymupdf.Point(72, 380),
            f"Pages {pm['start_page']}–{pm['end_page']} in this exhibit  "
            f"({pm['num_pages']} document pages)",
            fontsize=11, fontname="helv", color=(0.4, 0.4, 0.4),
        )

        # Insert the actual PDF pages
        merged.insert_pdf(info["doc"])
        info["doc"].close()

    # Serialize
    buf = merged.tobytes()
    merged.close()

    # Strip internal doc refs from page_map before returning
    for pm in page_map:
        pm.pop("separator_page", None)

    return buf, page_map
