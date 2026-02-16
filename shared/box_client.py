"""Box client for browsing client document folders.

Shared module used across all office dashboard tools. Uses Box CCG
(Client Credentials Grant) authentication via environment variables:
    BOX_CLIENT_ID, BOX_CLIENT_SECRET, BOX_ENTERPRISE_ID

Credentials are read from the parent project .env file. All box_sdk_gen
imports are lazy (inside functions) so tools without boxsdk installed
can still import this module's existence check without crashing.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

# Load .env from the parent project directory
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
if _ENV_PATH.exists():
    from dotenv import load_dotenv

    load_dotenv(_ENV_PATH)


def parse_folder_id(value: str) -> str:
    """Extract a numeric Box folder ID from a URL or bare ID.

    Accepts:
        "163957038141"
        "https://app.box.com/folder/163957038141"
        "https://app.box.com/folder/163957038141?s=abc123"
    Returns the numeric folder ID string, or the original value if no match.
    """
    value = value.strip()
    # Try to extract from URL pattern
    m = re.search(r"folder/(\d+)", value)
    if m:
        return m.group(1)
    # Already a bare numeric ID
    if value.isdigit():
        return value
    return value


# Module-level cache for the Box client
_client = None


def get_box_client():
    """Authenticate with Box using Client Credentials Grant. Cached."""
    global _client
    if _client is not None:
        return _client

    from box_sdk_gen import BoxCCGAuth, BoxClient, CCGConfig

    config = CCGConfig(
        client_id=os.environ["BOX_CLIENT_ID"],
        client_secret=os.environ["BOX_CLIENT_SECRET"],
        enterprise_id=os.environ["BOX_ENTERPRISE_ID"],
    )
    auth = BoxCCGAuth(config=config)
    _client = BoxClient(auth=auth)
    return _client


def list_folder_items(folder_id: str) -> list[dict]:
    """Return all items in a Box folder as dicts, folders first then files.

    Each item: {id, name, type, size, modified_at, extension, web_url}
    """
    client = get_box_client()
    all_entries = []
    offset = 0
    limit = 1000

    while True:
        items = client.folders.get_folder_items(folder_id, offset=offset, limit=limit)
        if not items.entries:
            break
        all_entries.extend(items.entries)
        offset += len(items.entries)
        if offset >= items.total_count:
            break

    results = []
    for e in all_entries:
        item = {
            "id": e.id,
            "name": e.name,
            "type": e.type,
            "size": getattr(e, "size", 0) or 0,
            "modified_at": str(getattr(e, "modified_at", "") or ""),
            "extension": getattr(e, "extension", "") or "",
            "web_url": f"https://app.box.com/{'folder' if e.type == 'folder' else 'file'}/{e.id}",
        }
        results.append(item)

    # Sort: folders first (alphabetical), then files (alphabetical)
    folders = sorted([r for r in results if r["type"] == "folder"], key=lambda x: x["name"].lower())
    files = sorted([r for r in results if r["type"] != "folder"], key=lambda x: x["name"].lower())
    return folders + files


def get_file_content(file_id: str) -> bytes:
    """Download file bytes from Box by file ID."""
    client = get_box_client()
    stream = client.downloads.download_file(file_id)
    chunks = []
    for chunk in stream:
        chunks.append(chunk)
    return b"".join(chunks)


def get_folder_name(folder_id: str) -> str:
    """Return the display name of a Box folder."""
    client = get_box_client()
    folder = client.folders.get_folder_by_id(folder_id)
    return folder.name
