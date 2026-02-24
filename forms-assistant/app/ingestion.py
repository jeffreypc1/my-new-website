"""PDF ingestion engine for the Forms Assistant.

Handles fillable (AcroForm) and non-fillable (text block extraction) PDFs.
Detects PDF type, extracts fields or text blocks, builds FormSchema objects,
and manages schema versioning on disk.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Shared imports live one level above the forms-assistant package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.schema import FormFieldSchema, FormSchema

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "data" / "form_schemas"


# -- PDF type detection -------------------------------------------------------

def detect_pdf_type(pdf_bytes: bytes) -> str:
    """Determine whether a PDF is fillable, non-fillable, or scanned.

    Returns:
        "fillable"    - PDF contains AcroForm widget annotations.
        "nonfillable" - PDF has extractable text but no form widgets.
        "scanned"     - PDF has no text layer at all (image-only).
    """
    import pymupdf

    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")

    has_widgets = False
    has_text = False

    for page_num in range(len(doc)):
        page = doc[page_num]

        # Check for widget annotations
        widgets = page.widgets()
        if widgets:
            for _ in widgets:
                has_widgets = True
                break
        if has_widgets:
            break

        # Check for extractable text
        text = page.get_text("text").strip()
        if text:
            has_text = True

    # If we broke out early for widgets, we might not have checked text yet
    if has_widgets:
        doc.close()
        return "fillable"

    # Scan remaining pages for text if we haven't found any yet
    if not has_text:
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text").strip()
            if text:
                has_text = True
                break

    doc.close()

    if has_text:
        return "nonfillable"
    return "scanned"


# -- Main ingestion entry point -----------------------------------------------

def ingest_pdf(pdf_bytes: bytes, form_id: str, title: str = "") -> FormSchema:
    """Ingest a PDF and produce a FormSchema.

    Detects whether the PDF is fillable or non-fillable and extracts
    fields accordingly.  Scanned PDFs (no text layer) produce an empty
    schema with source="scanned".

    Args:
        pdf_bytes: Raw bytes of the uploaded PDF.
        form_id:   Unique identifier for this form.
        title:     Human-readable title (defaults to form_id).

    Returns:
        A fully populated FormSchema.
    """
    from shared.pdf_form_extractor import extract_form_fields, extract_text_blocks

    pdf_type = detect_pdf_type(pdf_bytes)
    now = datetime.now(timezone.utc).isoformat()
    title = title or form_id

    if pdf_type == "fillable":
        raw_fields = extract_form_fields(pdf_bytes)
        schema_fields = [
            FormFieldSchema(
                field_id=f["pdf_field_name"],
                display_label=f.get("display_label", f["pdf_field_name"]),
                field_type=f.get("field_type", "text"),
                section=f.get("section", ""),
                required=f.get("required", False),
                help_text=f.get("help_text", ""),
                options=f.get("options", []),
                page_number=f.get("page_number"),
                rect=f.get("rect"),
                role=f.get("role", "none"),
                sf_field=f.get("sf_field", ""),
            )
            for f in raw_fields
        ]
        source = "uploaded_fillable"

    elif pdf_type == "nonfillable":
        raw_blocks = extract_text_blocks(pdf_bytes)
        schema_fields = [
            FormFieldSchema(
                field_id=f"block_{i}",
                display_label=block["text"][:80],
                field_type="text",
                section=f"Page {block['page_number'] + 1}",
                page_number=block.get("page_number"),
                rect=block.get("rect"),
            )
            for i, block in enumerate(raw_blocks)
        ]
        source = "uploaded_nonfillable"

    else:
        # Scanned PDF -- no extractable content
        schema_fields = []
        source = "scanned"

    # Derive unique sections in order
    seen_sections: list[str] = []
    for f in schema_fields:
        if f.section and f.section not in seen_sections:
            seen_sections.append(f.section)

    schema = FormSchema(
        form_id=form_id,
        title=title,
        source=source,
        sections=seen_sections,
        fields=schema_fields,
        version=1,
        created_at=now,
        updated_at=now,
    )
    schema.version_hash = schema.compute_version_hash()

    return schema


# -- Version comparison -------------------------------------------------------

def compare_versions(old_schema: FormSchema, new_schema: FormSchema) -> dict:
    """Compare two FormSchema versions and report differences.

    Returns a dict with:
        added_fields   - list of field_ids present in new but not old.
        removed_fields - list of field_ids present in old but not new.
        changed_fields - list of dicts {field_id, changes: {attr: {old, new}}}.
        is_different   - bool, True if any difference found.
    """
    old_map = {f.field_id: f for f in old_schema.fields}
    new_map = {f.field_id: f for f in new_schema.fields}

    old_ids = set(old_map.keys())
    new_ids = set(new_map.keys())

    added = sorted(new_ids - old_ids)
    removed = sorted(old_ids - new_ids)

    changed: list[dict] = []
    for fid in sorted(old_ids & new_ids):
        old_dict = old_map[fid].to_dict()
        new_dict = new_map[fid].to_dict()
        changes: dict[str, dict] = {}
        for key in old_dict:
            if old_dict[key] != new_dict.get(key):
                changes[key] = {"old": old_dict[key], "new": new_dict.get(key)}
        if changes:
            changed.append({"field_id": fid, "changes": changes})

    is_different = bool(added or removed or changed)

    return {
        "added_fields": added,
        "removed_fields": removed,
        "changed_fields": changed,
        "is_different": is_different,
    }


# -- Persistence helpers ------------------------------------------------------

def save_form_schema(schema: FormSchema) -> Path:
    """Save a FormSchema to disk as JSON.

    File is stored at: data/form_schemas/{form_id}_v{version}.json

    Returns:
        Path to the saved file.
    """
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{schema.form_id}_v{schema.version}.json"
    path = SCHEMA_DIR / filename
    path.write_text(json.dumps(schema.to_dict(), indent=2), encoding="utf-8")
    return path


def load_form_schema(form_id: str, version: int | None = None) -> FormSchema | None:
    """Load a FormSchema from disk.

    Args:
        form_id: The form identifier.
        version: Specific version to load. If None, loads the latest version.

    Returns:
        FormSchema or None if not found.
    """
    if not SCHEMA_DIR.is_dir():
        return None

    if version is not None:
        path = SCHEMA_DIR / f"{form_id}_v{version}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return FormSchema.from_dict(data)

    # Find latest version
    pattern = f"{form_id}_v*.json"
    matches = sorted(SCHEMA_DIR.glob(pattern))
    if not matches:
        return None

    # Sort by version number extracted from filename
    def _version_key(p: Path) -> int:
        stem = p.stem  # e.g. "i-589_v3"
        parts = stem.rsplit("_v", 1)
        try:
            return int(parts[1])
        except (IndexError, ValueError):
            return 0

    matches.sort(key=_version_key)
    latest = matches[-1]
    data = json.loads(latest.read_text(encoding="utf-8"))
    return FormSchema.from_dict(data)


def list_form_schemas() -> list[FormSchema]:
    """List all saved form schemas (latest version of each).

    Returns:
        List of FormSchema objects, one per unique form_id.
    """
    if not SCHEMA_DIR.is_dir():
        return []

    # Collect all schema files grouped by form_id
    form_files: dict[str, list[Path]] = {}
    for path in SCHEMA_DIR.glob("*_v*.json"):
        stem = path.stem
        parts = stem.rsplit("_v", 1)
        if len(parts) == 2:
            fid = parts[0]
            form_files.setdefault(fid, []).append(path)

    def _version_key(p: Path) -> int:
        parts = p.stem.rsplit("_v", 1)
        try:
            return int(parts[1])
        except (IndexError, ValueError):
            return 0

    schemas: list[FormSchema] = []
    for fid, paths in sorted(form_files.items()):
        paths.sort(key=_version_key)
        latest = paths[-1]
        data = json.loads(latest.read_text(encoding="utf-8"))
        schemas.append(FormSchema.from_dict(data))

    return schemas
