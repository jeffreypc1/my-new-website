"""Evidence management for the Evidence Indexer tool.

Provides structured handling of evidence packages for immigration cases,
including document categorization, exhibit lettering, index generation,
and bundle compilation.

Part of the O'Brien Immigration Law tool suite.

Note: Bundle compilation shares patterns with
country-reports-tool/app/exhibit_compiler.py for PDF merging with tab pages.
"""

from dataclasses import dataclass, field
from datetime import date


@dataclass
class EvidenceItem:
    """A single document in an evidence package."""

    exhibit_letter: str
    title: str
    category: str
    page_count: int = 0
    date_added: str = ""
    box_url: str = ""
    description: str = ""
    doc_id: str = ""


# ---------------------------------------------------------------------------
# Standard immigration evidence categories
# ---------------------------------------------------------------------------

DOCUMENT_CATEGORIES: list[str] = [
    "Identity Documents",
    "Country Conditions",
    "Medical/Psychological",
    "Expert Reports",
    "Declarations",
    "Photographs",
    "Government Documents",
    "Correspondence",
    "Other",
]


# ---------------------------------------------------------------------------
# Exhibit lettering utilities
# ---------------------------------------------------------------------------

def _exhibit_letter(index: int) -> str:
    """Convert 0-based index to exhibit letter: 0->A, 1->B, ..., 25->Z, 26->AA.

    This mirrors the implementation in country-reports-tool/app/exhibit_compiler.py.
    """
    if index < 26:
        return chr(ord("A") + index)
    return chr(ord("A") + index // 26 - 1) + chr(ord("A") + index % 26)


def auto_assign_letters(items: list[EvidenceItem]) -> list[EvidenceItem]:
    """Assign sequential exhibit letters (Tab A, Tab B, ...) to evidence items.

    Preserves any manually-assigned letters and fills gaps with auto-assigned
    sequential letters for items with empty exhibit_letter fields.

    Args:
        items: List of EvidenceItem objects in desired exhibit order.

    Returns:
        The same list with exhibit_letter fields populated.

    TODO: Support custom starting letter (e.g., start at "D" if A-C are reserved).
    TODO: Handle cases where manual letters conflict with auto-assigned ones.
    """
    next_index = 0
    for item in items:
        if not item.exhibit_letter:
            item.exhibit_letter = _exhibit_letter(next_index)
        next_index += 1
    return items


def reorder_exhibits(
    items: list[EvidenceItem],
    new_order: list[int],
) -> list[EvidenceItem]:
    """Reorder exhibits according to a new index ordering and reassign letters.

    Args:
        items: Current list of EvidenceItem objects.
        new_order: List of current indices in the desired new order.
            e.g. [2, 0, 1] means: current item 2 becomes first, then 0, then 1.

    Returns:
        Reordered list with reassigned exhibit letters.

    TODO: Validate that new_order contains all valid indices.
    TODO: Support partial reordering (move a single item).
    """
    reordered = [items[i] for i in new_order if 0 <= i < len(items)]

    # Reassign sequential letters after reordering
    for idx, item in enumerate(reordered):
        item.exhibit_letter = _exhibit_letter(idx)

    return reordered


def generate_index(items: list[EvidenceItem]) -> list[dict]:
    """Generate a structured exhibit index suitable for Word doc export.

    Args:
        items: List of EvidenceItem objects in exhibit order.

    Returns:
        List of dicts with keys: exhibit_letter, title, category, page_count,
        description. Suitable for rendering into a Word table.

    TODO: Add page range computation (start page - end page) for compiled bundle.
    TODO: Add Bates number support.
    TODO: Generate Word doc directly using python-docx.
    """
    index_rows: list[dict] = []
    for item in items:
        index_rows.append({
            "exhibit_letter": item.exhibit_letter,
            "title": item.title,
            "category": item.category,
            "page_count": item.page_count,
            "description": item.description,
            "date_added": item.date_added,
        })
    return index_rows


def generate_index_docx(items: list[EvidenceItem], case_name: str = "") -> bytes:
    """Generate a Word document exhibit index.

    Creates a formatted Word document with a table listing all exhibits,
    suitable for filing with the immigration court or USCIS.

    Args:
        items: List of EvidenceItem objects in exhibit order.
        case_name: Client name or case caption for the document header.

    Returns:
        Bytes of the generated .docx file.

    TODO: Add proper formatting (margins, fonts, table styling).
    TODO: Add court caption block at the top.
    TODO: Add attorney signature block at the bottom.
    """
    try:
        from docx import Document

        doc = Document()
        doc.add_heading("Exhibit Index", level=0)
        if case_name:
            doc.add_paragraph(f"In the Matter of: {case_name}")
        doc.add_paragraph("")

        # Create exhibit table
        table = doc.add_table(rows=1, cols=4)
        table.style = "Table Grid"
        header_cells = table.rows[0].cells
        header_cells[0].text = "Exhibit"
        header_cells[1].text = "Document Title"
        header_cells[2].text = "Category"
        header_cells[3].text = "Pages"

        for item in items:
            row = table.add_row().cells
            row[0].text = f"Tab {item.exhibit_letter}"
            row[1].text = item.title
            row[2].text = item.category
            row[3].text = str(item.page_count) if item.page_count else ""

        import io
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return buf.read()

    except ImportError:
        # Graceful degradation if python-docx is not installed yet
        return b""
