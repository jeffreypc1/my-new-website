"""Build a filename → Box URL mapping by walking the Box folder tree."""

import json

from app.box_client import get_box_client, _list_all_items
from app.config import BASE_DIR, get_settings

BOX_LINKS_PATH = BASE_DIR / "data" / "box_links.json"


def build_box_links() -> dict[str, str]:
    """Recursively walk the Box folder tree and save {filename: url} mappings."""
    s = get_settings()
    client = get_box_client()
    links: dict[str, str] = {}

    def _recurse(folder_id: str) -> None:
        entries = _list_all_items(client, folder_id)
        for entry in entries:
            if entry.type == "folder":
                _recurse(entry.id)
            elif entry.type == "file" and entry.name.lower().endswith(".pdf"):
                links[entry.name] = f"https://app.box.com/file/{entry.id}"

    print(f"Walking Box folder {s.box_folder_id} ...")
    _recurse(s.box_folder_id)
    print(f"Found {len(links)} PDF files.")

    BOX_LINKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(BOX_LINKS_PATH, "w") as f:
        json.dump(links, f, indent=2)

    print(f"Saved to {BOX_LINKS_PATH}")
    return links


def load_box_links() -> dict[str, str]:
    """Read the cached Box links JSON. Returns empty dict if not built yet."""
    if BOX_LINKS_PATH.exists():
        with open(BOX_LINKS_PATH) as f:
            return json.load(f)
    return {}


if __name__ == "__main__":
    build_box_links()
