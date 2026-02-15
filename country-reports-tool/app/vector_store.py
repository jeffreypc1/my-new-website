import chromadb

from app.config import BASE_DIR

COLLECTION_NAME = "country_reports"
CHROMA_DIR = BASE_DIR / "data" / "chroma"


def get_or_create_collection() -> chromadb.Collection:
    """Get or create the ChromaDB collection with persistent storage."""
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(name=COLLECTION_NAME)


def add_chunks(collection: chromadb.Collection, chunks: list[dict], batch_size: int = 500) -> None:
    """Upsert text chunks into the ChromaDB collection in batches.

    Each chunk dict must have keys: text, source, country, chunk_index.
    """
    if not chunks:
        return

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        collection.upsert(
            ids=[f"{c.get('country', '')}/{c['source']}__chunk_{c['chunk_index']}" for c in batch],
            documents=[c["text"] for c in batch],
            metadatas=[
                {
                    "source": c["source"],
                    "country": c.get("country", ""),
                    "chunk_index": c["chunk_index"],
                }
                for c in batch
            ],
        )


def get_all_metadata(collection: chromadb.Collection, batch_size: int = 10_000) -> list[dict]:
    """Fetch all metadata from the collection in batches to avoid SQL variable limits."""
    total = collection.count()
    all_meta: list[dict] = []
    for offset in range(0, total, batch_size):
        batch = collection.get(
            include=["metadatas"], limit=batch_size, offset=offset
        )
        all_meta.extend(batch["metadatas"])
    return all_meta


def search(
    collection: chromadb.Collection,
    query: str,
    n_results: int = 5,
    countries: list[str] | None = None,
) -> list[dict]:
    """Search the collection and return matching chunks with metadata.

    If countries is provided, results are filtered to only those countries.
    """
    kwargs: dict = {"query_texts": [query], "n_results": n_results}
    if countries:
        kwargs["where"] = {"country": {"$in": countries}}

    results = collection.query(**kwargs)

    matches = []
    for i in range(len(results["ids"][0])):
        matches.append({
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })
    return matches
