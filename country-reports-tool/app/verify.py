"""Verify ChromaDB index — print chunk count, country breakdown, and file counts."""

from collections import Counter

from app.vector_store import get_or_create_collection, get_all_metadata


def main() -> None:
    collection = get_or_create_collection()
    total = collection.count()
    print(f"Total chunks indexed: {total:,}")

    # Fetch all metadata in batches to compute stats
    all_meta = get_all_metadata(collection)

    countries: Counter[str] = Counter()
    files_by_country: dict[str, set[str]] = {}

    for meta in all_meta:
        country = meta.get("country", "Unknown")
        source = meta.get("source", "")
        countries[country] += 1
        files_by_country.setdefault(country, set()).add(source)

    print(f"Distinct countries: {len(countries)}")
    print()
    print(f"{'Country':<30} {'Chunks':>8} {'Files':>6}")
    print("-" * 46)
    for country, count in sorted(countries.items()):
        n_files = len(files_by_country.get(country, set()))
        print(f"{country:<30} {count:>8,} {n_files:>6}")


if __name__ == "__main__":
    main()
