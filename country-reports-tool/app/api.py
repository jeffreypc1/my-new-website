"""FastAPI backend for the Country Conditions search dashboard."""

from fastapi import FastAPI, Query
from pydantic import BaseModel

from app.box_links import load_box_links
from app.citations import load_template, save_template, trim_to_sentences
from app.vector_store import get_all_metadata, get_or_create_collection, search

app = FastAPI(title="Country Conditions Assembler API")

_collection = None
_box_links: dict[str, str] | None = None


def _get_collection():
    global _collection
    if _collection is None:
        _collection = get_or_create_collection()
    return _collection


def _get_box_links() -> dict[str, str]:
    global _box_links
    if _box_links is None:
        _box_links = load_box_links()
    return _box_links


@app.get("/api/countries")
def list_countries() -> list[str]:
    """Return sorted list of distinct countries in the index."""
    collection = _get_collection()
    all_meta = get_all_metadata(collection)
    countries = sorted({m.get("country", "") for m in all_meta} - {""})
    return countries


@app.get("/api/search")
def search_chunks(
    q: str = Query(..., min_length=1, description="Search query"),
    countries: list[str] | None = Query(None, description="Filter by country"),
    n: int = Query(20, ge=1, le=100, description="Number of results"),
) -> list[dict]:
    """Vector search across indexed country reports."""
    collection = _get_collection()
    results = search(collection, query=q, n_results=n, countries=countries or None)
    return [
        {
            "text": r["text"],
            "country": r["metadata"].get("country", ""),
            "source": r["metadata"].get("source", ""),
            "chunk_index": r["metadata"].get("chunk_index", 0),
            "distance": r["distance"],
        }
        for r in results
    ]


@app.get("/api/search/grouped")
def search_grouped(
    q: str = Query(..., min_length=1, description="Search query"),
    countries: list[str] | None = Query(None, description="Filter by country"),
    n: int = Query(20, ge=1, le=100, description="Number of document groups"),
) -> list[dict]:
    """Vector search grouped by source document."""
    collection = _get_collection()
    raw_n = min(n * 5, 500)
    results = search(collection, query=q, n_results=raw_n, countries=countries or None)
    box_links = _get_box_links()

    # Group by source filename
    groups: dict[str, dict] = {}
    for r in results:
        meta = r["metadata"]
        source = meta.get("source", "")
        if source not in groups:
            groups[source] = {
                "source": source,
                "country": meta.get("country", ""),
                "best_distance": r["distance"],
                "box_url": box_links.get(source),
                "chunks": [],
            }
        group = groups[source]
        group["best_distance"] = min(group["best_distance"], r["distance"])
        group["chunks"].append({
            "text": trim_to_sentences(r["text"]),
            "chunk_index": meta.get("chunk_index", 0),
            "distance": r["distance"],
        })

    # Sort chunks within each group by reading order
    for group in groups.values():
        group["chunks"].sort(key=lambda c: c["chunk_index"])

    # Sort groups by best relevance, return top n
    sorted_groups = sorted(groups.values(), key=lambda g: g["best_distance"])
    return sorted_groups[:n]


@app.get("/api/citation-template")
def get_citation_template() -> dict:
    """Return the current citation template config."""
    return load_template()


class CitationTemplateBody(BaseModel):
    template: str
    max_snippet_length: int = 300


@app.post("/api/citation-template")
def set_citation_template(body: CitationTemplateBody) -> dict:
    """Save a new citation template. The template must contain {snippet}."""
    if "{snippet}" not in body.template:
        return {"error": "Template must contain {snippet} placeholder."}
    save_template(body.template, body.max_snippet_length)
    return {"status": "saved"}
