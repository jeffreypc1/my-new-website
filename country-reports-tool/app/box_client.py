from pathlib import Path

from box_sdk_gen import BoxCCGAuth, BoxClient, CCGConfig

from app.config import get_settings


def get_box_client() -> BoxClient:
    """Authenticate with Box using Client Credentials Grant."""
    s = get_settings()
    config = CCGConfig(
        client_id=s.box_client_id,
        client_secret=s.box_client_secret,
        enterprise_id=s.box_enterprise_id,
    )
    auth = BoxCCGAuth(config=config)
    return BoxClient(auth=auth)


def _list_all_items(client: BoxClient, folder_id: str) -> list:
    """Paginate through all items in a Box folder."""
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

    return all_entries


def download_pdfs(client: BoxClient, folder_id: str) -> list[Path]:
    """Download all PDFs from a Box folder tree, recursing to any depth.

    PDFs are saved into per-country subdirectories under data/pdfs/.
    The country name is derived from the first level of subfolders.
    """
    s = get_settings()
    s.pdf_dir.mkdir(parents=True, exist_ok=True)
    downloaded: list[Path] = []

    def _recurse(fid: str, dest_dir: Path, depth: int = 0) -> None:
        entries = _list_all_items(client, fid)
        for entry in entries:
            if entry.type == "folder":
                indent = "  " * (depth + 1)
                print(f"{indent}Entering: {entry.name}/")
                sub_dir = dest_dir if depth > 0 else dest_dir / entry.name
                sub_dir.mkdir(parents=True, exist_ok=True)
                _recurse(entry.id, sub_dir, depth + 1)

            elif entry.type == "file" and entry.name.lower().endswith(".pdf"):
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest = dest_dir / entry.name
                if dest.exists():
                    downloaded.append(dest)
                    continue

                print(f"  [{len(downloaded) + 1}] {dest_dir.name}/{entry.name}")
                stream = client.downloads.download_file(entry.id)
                with open(dest, "wb") as f:
                    for chunk in stream:
                        f.write(chunk)
                downloaded.append(dest)

    _recurse(folder_id, s.pdf_dir)
    return downloaded
