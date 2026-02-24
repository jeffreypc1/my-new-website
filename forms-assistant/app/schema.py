"""Unified data models for the Forms Assistant.

Dataclasses for form field schemas, SF mappings, sync logs, and audit entries.
All models support JSON serialization via asdict/from_dict patterns.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class FormFieldSchema:
    """A single field within a form schema."""

    field_id: str              # pdf_field_name (uploaded) or name (hardcoded)
    display_label: str
    field_type: str = "text"   # text, date, select, checkbox, textarea, combo
    section: str = ""
    required: bool = False
    help_text: str = ""
    options: list[str] = field(default_factory=list)
    validation_rules: dict = field(default_factory=dict)
    page_number: int | None = None
    rect: list[float] | None = None   # bounding box for PDF overlay
    role: str = "none"
    sf_field: str = ""
    sf_confidence: float = 0.0
    sf_approved: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> FormFieldSchema:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class FormSchema:
    """Complete schema for a form (hardcoded or uploaded)."""

    form_id: str
    title: str
    agency: str = ""
    filing_fee: str = ""
    processing_time: str = ""
    source: str = "hardcoded"  # hardcoded | uploaded_fillable | uploaded_nonfillable
    sections: list[str] = field(default_factory=list)
    fields: list[FormFieldSchema] = field(default_factory=list)
    version: int = 1
    version_hash: str = ""     # SHA256 of sorted field_ids
    created_at: str = ""
    updated_at: str = ""

    def compute_version_hash(self) -> str:
        """Compute a hash of sorted field IDs for version comparison."""
        ids = sorted(f.field_id for f in self.fields)
        return hashlib.sha256(json.dumps(ids).encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> FormSchema:
        fields_data = d.pop("fields", [])
        fields = [FormFieldSchema.from_dict(f) for f in fields_data]
        filtered = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        schema = cls(**filtered)
        schema.fields = fields
        return schema

    def get_fields_by_section(self) -> dict[str, list[FormFieldSchema]]:
        """Group fields by section, maintaining order."""
        result: dict[str, list[FormFieldSchema]] = {}
        for f in self.fields:
            result.setdefault(f.section, []).append(f)
        return result


@dataclass
class FieldMapping:
    """Mapping of a single form field to a Salesforce field."""

    form_id: str
    field_id: str
    sf_object: str = "Contact"
    sf_field: str = ""
    match_method: str = ""     # exact | synonym | fuzzy | manual | history
    confidence: float = 0.0
    approved: bool = False
    approved_by: str = ""
    approved_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> FieldMapping:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class MappingSet:
    """All SF mappings for a single form."""

    form_id: str
    mappings: list[FieldMapping] = field(default_factory=list)
    last_auto_mapped: str = ""
    version: int = 1

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> MappingSet:
        mappings_data = d.pop("mappings", [])
        mappings = [FieldMapping.from_dict(m) for m in mappings_data]
        filtered = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        ms = cls(**filtered)
        ms.mappings = mappings
        return ms

    def get_mapping(self, field_id: str) -> FieldMapping | None:
        """Find a mapping by field_id."""
        for m in self.mappings:
            if m.field_id == field_id:
                return m
        return None

    def get_approved_mappings(self) -> list[FieldMapping]:
        """Return only approved mappings."""
        return [m for m in self.mappings if m.approved]

    def get_pending_mappings(self) -> list[FieldMapping]:
        """Return mappings that have a suggestion but aren't approved."""
        return [m for m in self.mappings if m.sf_field and not m.approved]


@dataclass
class SyncLogEntry:
    """Record of a single sync operation."""

    timestamp: str
    direction: str             # sf_to_form | form_to_sf
    form_id: str
    contact_id: str
    fields_synced: dict = field(default_factory=dict)  # {sf_field: {old, new}}
    status: str = "success"    # success | partial | failed
    error: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> SyncLogEntry:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class AuditEntry:
    """A single audit trail entry."""

    timestamp: str
    action: str                # mapping_approved | field_value_changed | form_ingested | sync_executed
    form_id: str = ""
    field_id: str = ""
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> AuditEntry:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
