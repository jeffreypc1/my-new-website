from pathlib import Path

import pymupdf


def extract_text(pdf_path: Path) -> str:
    """Extract all text from a PDF using PyMuPDF."""
    doc = pymupdf.open(pdf_path)
    pages = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()
    return "\n".join(pages)


def chunk_text(
    text: str,
    source_filename: str,
    country: str = "",
    chunk_size: int = 1000,
    overlap: int = 200,
) -> list[dict]:
    """Split text into overlapping chunks, preferring paragraph boundaries.

    Returns a list of dicts with keys: text, source, country, chunk_index.
    """
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""
    chunk_index = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # If adding this paragraph exceeds chunk_size and we already have content,
        # finalize the current chunk
        if current_chunk and len(current_chunk) + len(para) + 2 > chunk_size:
            chunks.append({
                "text": current_chunk.strip(),
                "source": source_filename,
                "country": country,
                "chunk_index": chunk_index,
            })
            chunk_index += 1
            # Keep the tail of the current chunk as overlap
            if overlap > 0 and len(current_chunk) > overlap:
                current_chunk = current_chunk[-overlap:]
            else:
                current_chunk = ""

        if current_chunk:
            current_chunk += "\n\n" + para
        else:
            current_chunk = para

        # Handle single paragraphs that exceed chunk_size
        while len(current_chunk) > chunk_size:
            split_point = current_chunk.rfind(" ", 0, chunk_size)
            if split_point == -1:
                split_point = chunk_size

            chunks.append({
                "text": current_chunk[:split_point].strip(),
                "source": source_filename,
                "chunk_index": chunk_index,
            })
            chunk_index += 1
            current_chunk = current_chunk[split_point - overlap :] if overlap else current_chunk[split_point:]

    # Don't forget the last chunk
    if current_chunk.strip():
        chunks.append({
            "text": current_chunk.strip(),
            "source": source_filename,
            "chunk_index": chunk_index,
        })

    return chunks
