"""Box folder browser with thumbnail generation for the Document Assembler.

Provides recursive listing and PDF/image thumbnail generation using PyMuPDF.
Builds on shared/box_client.py for Box API access.
"""

from __future__ import annotations

import base64
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.box_client import list_folder_items, get_file_content, get_folder_name


def list_folder_recursive(
    folder_id: str,
    max_depth: int = 5,
    on_progress=None,
    _depth: int = 0,
    _path: str = "",
) -> list[dict]:
    """Recursively list all files in a Box folder tree.

    Returns a flat list of file dicts with breadcrumb folder_path added.
    Folders are traversed but not included in the output.
    """
    if _depth > max_depth:
        return []

    items = list_folder_items(folder_id)
    results: list[dict] = []

    for item in items:
        if item["type"] == "folder":
            subfolder_path = f"{_path}/{item['name']}" if _path else item["name"]
            if on_progress:
                on_progress(f"Scanning {subfolder_path}...")
            sub_items = list_folder_recursive(
                item["id"],
                max_depth=max_depth,
                on_progress=on_progress,
                _depth=_depth + 1,
                _path=subfolder_path,
            )
            results.extend(sub_items)
        else:
            file_entry = {
                "id": item["id"],
                "name": item["name"],
                "type": item["type"],
                "extension": item.get("extension", ""),
                "web_url": item.get("web_url", ""),
                "size": item.get("size", 0),
                "modified_at": item.get("modified_at", ""),
                "folder_path": _path,
            }
            results.append(file_entry)

    return results


def generate_thumbnail(file_bytes: bytes, filename: str, size: int = 150) -> bytes:
    """Generate a PNG thumbnail from a PDF or image file.

    For PDFs, renders the first page. For images, opens and resizes.
    Returns PNG bytes, or empty bytes on failure.
    """
    import pymupdf

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    try:
        if ext == "pdf":
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
            if len(doc) == 0:
                doc.close()
                return b""
            page = doc[0]
            # Scale to fit within size x size
            zoom = size / max(page.rect.width, page.rect.height)
            mat = pymupdf.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            png_bytes = pix.tobytes("png")
            doc.close()
            return png_bytes
        elif ext in ("jpg", "jpeg", "png", "tiff", "tif", "bmp", "webp", "gif"):
            # Open image via pymupdf
            doc = pymupdf.open(stream=file_bytes, filetype=ext)
            if len(doc) == 0:
                doc.close()
                return b""
            page = doc[0]
            zoom = size / max(page.rect.width, page.rect.height)
            mat = pymupdf.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            png_bytes = pix.tobytes("png")
            doc.close()
            return png_bytes
        else:
            return b""
    except Exception:
        return b""


def get_thumbnail_b64(file_bytes: bytes, filename: str, size: int = 150) -> str:
    """Generate a base64 data URI for an HTML <img> tag.

    Returns a data:image/png;base64,... string, or empty string on failure.
    """
    png = generate_thumbnail(file_bytes, filename, size)
    if not png:
        return ""
    encoded = base64.b64encode(png).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def get_pdf_page_count(file_bytes: bytes) -> int:
    """Return the number of pages in a PDF."""
    import pymupdf

    try:
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        count = len(doc)
        doc.close()
        return count
    except Exception:
        return 0
