"""Ingest pipeline: Download PDFs from Box → extract text → chunk → store in ChromaDB.

Usage:
    uv run python -m app.ingest               # full pipeline (download + index)
    uv run python -m app.ingest --skip-download  # index already-downloaded PDFs only
"""

import subprocess
import sys
from pathlib import Path

from app.box_client import download_pdfs, get_box_client
from app.config import get_settings
from app.vector_store import get_or_create_collection, search


def _collect_local_pdfs(pdf_dir: Path) -> list[Path]:
    """Gather all PDFs already on disk under pdf_dir."""
    return sorted(pdf_dir.rglob("*.pdf"))


def main() -> None:
    settings = get_settings()
    skip_download = "--skip-download" in sys.argv

    if skip_download:
        print("Skipping Box download, using local PDFs...\n")
        pdf_paths = _collect_local_pdfs(settings.pdf_dir)
    else:
        print("Authenticating with Box...")
        client = get_box_client()
        print("  Authenticated successfully.\n")

        print(f"Downloading PDFs from Box folder {settings.box_folder_id}...")
        pdf_paths = download_pdfs(client, settings.box_folder_id)

    print(f"  {len(pdf_paths)} PDF(s) ready.\n")

    if not pdf_paths:
        print("No PDFs found. Nothing to ingest.")
        return

    # Find country subdirectories
    country_dirs = sorted(
        [d for d in settings.pdf_dir.iterdir() if d.is_dir()],
        key=lambda d: d.name,
    )

    if not country_dirs:
        print("No country subdirectories found.")
        return

    print(f"Indexing {len(country_dirs)} countries in separate processes...\n")

    for country_dir in country_dirs:
        pdf_count = len(list(country_dir.rglob("*.pdf")))
        if pdf_count == 0:
            continue

        print(f"=== {country_dir.name} ({pdf_count} files) ===")

        # Run each country in a subprocess so memory is fully reclaimed
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "app.ingest_country",
                str(country_dir),
                str(settings.pdf_dir),
            ],
            env={**dict(__import__("os").environ), "PYTHONUNBUFFERED": "1"},
            timeout=600,
        )

        if result.returncode != 0:
            print(f"  WARNING: {country_dir.name} exited with code {result.returncode}\n")
        print()

    # Final summary and test search
    collection = get_or_create_collection()
    count = collection.count()
    print(f"Ingestion complete: {count} total chunks in ChromaDB.\n")

    test_query = "human rights violations"
    print(f'Running test search: "{test_query}"')
    results = search(collection, test_query, n_results=5)

    if not results:
        print("  No results found.")
    else:
        for i, r in enumerate(results, 1):
            print(f"\n  --- Result {i} (distance: {r['distance']:.4f}) ---")
            print(f"  Source: {r['metadata'].get('country', '')}/{r['metadata']['source']}, chunk {r['metadata']['chunk_index']}")
            print(f"  Text: {r['text'][:300]}...")


if __name__ == "__main__":
    main()
