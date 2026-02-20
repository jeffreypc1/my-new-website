"""Upload .docx bytes to Google Drive as a Google Doc."""

import json
from pathlib import Path

_TOKEN_PATH = Path(__file__).resolve().parent.parent / "google_token.json"
_SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/documents",
]


def _get_credentials():
    """Load OAuth2 user credentials, refreshing if expired."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    with open(_TOKEN_PATH) as f:
        token_data = json.load(f)

    creds = Credentials(
        token=token_data["token"],
        refresh_token=token_data["refresh_token"],
        token_uri=token_data["token_uri"],
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=token_data.get("scopes", _SCOPES),
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_data["token"] = creds.token
        with open(_TOKEN_PATH, "w") as f:
            json.dump(token_data, f, indent=2)

    return creds


def upload_to_google_docs(
    docx_bytes: bytes, title: str, folder_id: str = ""
) -> str:
    """Upload .docx bytes to Google Drive as a Google Doc.

    Returns the URL of the created Google Doc.
    """
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaInMemoryUpload

    creds = _get_credentials()
    drive = build("drive", "v3", credentials=creds)

    file_metadata: dict = {
        "name": title,
        "mimeType": "application/vnd.google-apps.document",
    }
    if folder_id:
        file_metadata["parents"] = [folder_id]

    media = MediaInMemoryUpload(
        docx_bytes,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        resumable=True,
    )
    created = (
        drive.files()
        .create(body=file_metadata, media_body=media, fields="id")
        .execute()
    )
    url = f"https://docs.google.com/document/d/{created['id']}/edit"

    # Log usage
    try:
        from shared.usage_tracker import log_api_call

        log_api_call(
            service="google_docs",
            tool="",
            operation="upload",
            details=title,
        )
    except Exception:
        pass

    return url


def copy_template_and_fill(
    template_id: str,
    title: str,
    replacements: dict[str, str],
    folder_id: str = "",
) -> str:
    """Copy a Google Docs template and fill placeholders.

    Args:
        template_id: The Google Docs file ID of the template to copy.
        title: Name for the new document.
        replacements: Dict of placeholder → replacement text,
                      e.g. {"{{CONTENT}}": "letter body here"}.
        folder_id: Optional Google Drive folder ID to place the copy in.

    Returns:
        The URL of the newly created Google Doc.
    """
    from googleapiclient.discovery import build

    creds = _get_credentials()
    drive = build("drive", "v3", credentials=creds)
    docs = build("docs", "v1", credentials=creds)

    # 1. Copy the template
    copy_metadata: dict = {"name": title}
    if folder_id:
        copy_metadata["parents"] = [folder_id]
    copied = drive.files().copy(
        fileId=template_id, body=copy_metadata, fields="id"
    ).execute()
    new_id = copied["id"]

    # 2. Replace placeholders
    requests = [
        {
            "replaceAllText": {
                "containsText": {"text": placeholder, "matchCase": True},
                "replaceText": replacement,
            }
        }
        for placeholder, replacement in replacements.items()
    ]
    if requests:
        docs.documents().batchUpdate(
            documentId=new_id, body={"requests": requests}
        ).execute()

    url = f"https://docs.google.com/document/d/{new_id}/edit"

    # Log usage
    try:
        from shared.usage_tracker import log_api_call

        log_api_call(
            service="google_docs",
            tool="",
            operation="template_copy_fill",
            details=title,
        )
    except Exception:
        pass

    return url
