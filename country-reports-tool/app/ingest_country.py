"""Ingest a single country's PDFs into ChromaDB. Called as a subprocess by ingest.py."""

import sys
from pathlib import Path

from app.pdf_processor import chunk_text, extract_text
from app.vector_store import add_chunks, get_or_create_collection


def main(country_dir: Path, pdf_dir: Path) -> None:
    country = country_dir.name
    pdfs = sorted(country_dir.rglob("*.pdf"))

    if not pdfs:
        return

    collection = get_or_create_collection()
    total = 0

    for i, pdf_path in enumerate(pdfs, 1):
        print(f"  [{i}/{len(pdfs)}] {pdf_path.name}")

        try:
            text = extract_text(pdf_path)
        except Exception as e:
            print(f"    (error: {e}, skipping)")
            continue

        if not text.strip():
            print(f"    (no text, skipping)")
            continue

        chunks = chunk_text(text, source_filename=pdf_path.name, country=country)
        add_chunks(collection, chunks)
        total += len(chunks)
        print(f"    → {len(chunks)} chunks")
        del text, chunks

    print(f"  {country}: {total} chunks indexed from {len(pdfs)} files")


if __name__ == "__main__":
    country_dir = Path(sys.argv[1])
    pdf_dir = Path(sys.argv[2])
    main(country_dir, pdf_dir)
