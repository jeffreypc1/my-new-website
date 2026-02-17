"""Checklist templates and case persistence for the Case Checklist tool.

Provides comprehensive, real-world checklist templates for common immigration
case types, along with CRUD functions to create, read, update, and delete
cases persisted as JSON files.

Part of the O'Brien Immigration Law tool suite.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.config_store import get_config_value

# ── Storage ──────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "cases"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ── Data models ──────────────────────────────────────────────────────────────


@dataclass
class ChecklistItem:
    """A single actionable item in a case checklist."""

    id: str
    title: str
    category: str  # Filing, Evidence, Preparation, Administrative
    is_completed: bool = False
    completed_date: str | None = None
    deadline: str | None = None  # ISO date string, e.g. "2026-06-15"
    notes: str = ""


@dataclass
class Case:
    """An immigration case with its associated checklist."""

    id: str
    client_name: str
    a_number: str
    case_type: str
    attorney: str
    created_at: str
    updated_at: str
    items: list[dict[str, Any]]
    status: str = "Active"  # Active or Completed


# ── Templates ────────────────────────────────────────────────────────────────

_DEFAULT_CASE_TYPES: list[str] = [
    "Asylum (I-589)",
    "Family-Based (I-130/I-485)",
    "Adjustment of Status (I-485)",
    "Naturalization (N-400)",
    "VAWA (I-360)",
    "U-Visa (I-918)",
    "T-Visa (I-914)",
    "Special Immigrant Juvenile (SIJ)",
    "Cancellation of Removal",
    "Removal Defense (General)",
    "DACA (I-821D)",
    "TPS (I-821)",
    "Employment-Based (I-140)",
    "Bond / Custody (I-352)",
]

_DEFAULT_TEMPLATES: dict[str, list[dict[str, str]]] = {
    "Asylum (I-589)": [
        # Filing
        {"title": "I-589 application completed and signed", "category": "Filing"},
        {"title": "G-28 Notice of Entry of Appearance filed", "category": "Filing"},
        {"title": "Personal declaration drafted and finalized", "category": "Filing"},
        {"title": "Country condition reports gathered", "category": "Filing"},
        {"title": "Supporting evidence compiled and tabbed", "category": "Filing"},
        {"title": "Pre-hearing brief / legal memo written", "category": "Filing"},
        {"title": "Exhibit index prepared (ICPM compliant)", "category": "Filing"},
        {"title": "Witness list with summaries filed (ICPM 4.18)", "category": "Filing"},
        {"title": "All exhibits served on DHS trial attorney", "category": "Filing"},
        {"title": "Biometrics completed", "category": "Filing"},
        # Evidence
        {"title": "Identity documents gathered (passport, birth certificate)", "category": "Evidence"},
        {"title": "Corroborating evidence for each claim element", "category": "Evidence"},
        {"title": "Translation certifications for foreign-language documents", "category": "Evidence"},
        {"title": "Photographs documenting harm/conditions", "category": "Evidence"},
        {"title": "Police / incident reports obtained", "category": "Evidence"},
        {"title": "News articles supporting country conditions", "category": "Evidence"},
        # Preparation
        {"title": "Initial client interview completed", "category": "Preparation"},
        {"title": "Interpreter arranged (if needed)", "category": "Preparation"},
        {"title": "Psychological evaluation scheduled and completed", "category": "Preparation"},
        {"title": "Expert declaration requested and received", "category": "Preparation"},
        {"title": "Witness declarations gathered", "category": "Preparation"},
        {"title": "Client testimony preparation (mock hearing)", "category": "Preparation"},
        {"title": "Direct and cross-examination questions prepared", "category": "Preparation"},
        # Administrative
        {"title": "One-year filing deadline tracked", "category": "Administrative"},
        {"title": "Master calendar hearing date calendared", "category": "Administrative"},
        {"title": "Individual hearing date calendared", "category": "Administrative"},
        {"title": "30-day pre-hearing filing deadline tracked (ICPM 3.1(b)(ii))", "category": "Administrative"},
        {"title": "15-day evidence filing deadline tracked (ICPM 3.1(b)(iii))", "category": "Administrative"},
        {"title": "DHS lodging/pre-hearing exchange completed", "category": "Administrative"},
    ],
    "Family-Based (I-130/I-485)": [
        # Filing
        {"title": "I-130 petition completed and filed", "category": "Filing"},
        {"title": "I-485 adjustment application filed", "category": "Filing"},
        {"title": "I-765 (EAD) application filed", "category": "Filing"},
        {"title": "I-131 (Advance Parole) filed", "category": "Filing"},
        {"title": "I-864 Affidavit of Support completed", "category": "Filing"},
        {"title": "G-28 Notice of Entry of Appearance filed", "category": "Filing"},
        {"title": "I-693 (Medical Exam) sealed envelope obtained", "category": "Filing"},
        # Evidence
        {"title": "Civil documents gathered (birth/marriage certificates)", "category": "Evidence"},
        {"title": "Certified translations of foreign documents", "category": "Evidence"},
        {"title": "Passport-style photos taken (2x2, per specs)", "category": "Evidence"},
        {"title": "Financial documents for I-864 (tax returns, W-2s, pay stubs)", "category": "Evidence"},
        {"title": "Evidence of bona fide relationship compiled", "category": "Evidence"},
        {"title": "Joint financial records (bank accounts, leases, insurance)", "category": "Evidence"},
        {"title": "Photographs together over time", "category": "Evidence"},
        {"title": "Affidavits from friends/family re: relationship", "category": "Evidence"},
        # Preparation
        {"title": "Interview preparation completed", "category": "Preparation"},
        {"title": "Stokes interview prep (if fraud suspected)", "category": "Preparation"},
        # Administrative
        {"title": "Biometrics appointment completed", "category": "Administrative"},
        {"title": "Priority date current (check Visa Bulletin)", "category": "Administrative"},
        {"title": "Medical exam (I-693) completed within 60 days of filing", "category": "Administrative"},
        {"title": "Interview notice received and calendared", "category": "Administrative"},
        {"title": "RFE response deadline tracked (if applicable)", "category": "Administrative"},
    ],
    "Adjustment of Status (I-485)": [
        # Filing
        {"title": "I-485 application completed and filed", "category": "Filing"},
        {"title": "I-765 (EAD) filed concurrently", "category": "Filing"},
        {"title": "I-131 (Advance Parole) filed concurrently", "category": "Filing"},
        {"title": "G-28 Notice of Entry of Appearance filed", "category": "Filing"},
        {"title": "Filing fee paid or fee waiver approved", "category": "Filing"},
        # Evidence
        {"title": "Passport and travel documents copied", "category": "Evidence"},
        {"title": "Birth certificate with translation", "category": "Evidence"},
        {"title": "I-94 arrival/departure record printed", "category": "Evidence"},
        {"title": "Visa approval notice / petition receipt", "category": "Evidence"},
        {"title": "Evidence of maintained status", "category": "Evidence"},
        {"title": "Passport-style photos (2x2)", "category": "Evidence"},
        {"title": "Medical exam (I-693) completed", "category": "Evidence"},
        # Preparation
        {"title": "Eligibility for adjustment confirmed (INA 245)", "category": "Preparation"},
        {"title": "Bars to adjustment reviewed (3/10 year bars, etc.)", "category": "Preparation"},
        {"title": "Interview preparation completed", "category": "Preparation"},
        # Administrative
        {"title": "Priority date current (check Visa Bulletin)", "category": "Administrative"},
        {"title": "Biometrics appointment completed", "category": "Administrative"},
        {"title": "Interview notice received", "category": "Administrative"},
        {"title": "RFE response deadline tracked", "category": "Administrative"},
    ],
    "Naturalization (N-400)": [
        # Filing
        {"title": "N-400 application completed and filed", "category": "Filing"},
        {"title": "Filing fee paid ($710) or fee waiver (I-912) approved", "category": "Filing"},
        {"title": "Copies of green card (front and back)", "category": "Filing"},
        {"title": "Passport-style photos (2x2)", "category": "Filing"},
        # Evidence
        {"title": "5 years of tax returns gathered (3 years if married to USC)", "category": "Evidence"},
        {"title": "Travel history documented (trips outside U.S.)", "category": "Evidence"},
        {"title": "Employment history for past 5 years", "category": "Evidence"},
        {"title": "Residence history for past 5 years", "category": "Evidence"},
        {"title": "Marital history documented", "category": "Evidence"},
        {"title": "Criminal history documentation (if applicable)", "category": "Evidence"},
        {"title": "Selective Service registration verified (males 18-26)", "category": "Evidence"},
        # Preparation
        {"title": "Civics test study materials provided to client", "category": "Preparation"},
        {"title": "English proficiency assessment", "category": "Preparation"},
        {"title": "N-400 interview preparation completed", "category": "Preparation"},
        {"title": "Good moral character issues identified and addressed", "category": "Preparation"},
        {"title": "Continuous residence and physical presence calculated", "category": "Preparation"},
        # Administrative
        {"title": "Biometrics appointment completed", "category": "Administrative"},
        {"title": "Interview notice received and calendared", "category": "Administrative"},
        {"title": "Oath ceremony date calendared", "category": "Administrative"},
        {"title": "90-day early filing window confirmed", "category": "Administrative"},
    ],
    "VAWA (I-360)": [
        # Filing
        {"title": "I-360 self-petition completed and filed", "category": "Filing"},
        {"title": "G-28 Notice of Entry of Appearance filed", "category": "Filing"},
        {"title": "Personal declaration drafted and finalized", "category": "Filing"},
        {"title": "I-485 filed concurrently (if eligible)", "category": "Filing"},
        {"title": "I-765 (EAD) filed", "category": "Filing"},
        # Evidence
        {"title": "Evidence of qualifying relationship (marriage certificate, etc.)", "category": "Evidence"},
        {"title": "Evidence of abuse (photos, medical records, police reports)", "category": "Evidence"},
        {"title": "Evidence of abuser's USC/LPR status", "category": "Evidence"},
        {"title": "Evidence of good faith marriage (if spouse petition)", "category": "Evidence"},
        {"title": "Evidence of good moral character", "category": "Evidence"},
        {"title": "Evidence of residence in the U.S.", "category": "Evidence"},
        {"title": "Restraining orders / protective orders", "category": "Evidence"},
        {"title": "Affidavits from friends, family, counselors", "category": "Evidence"},
        {"title": "Certified translations of foreign documents", "category": "Evidence"},
        # Preparation
        {"title": "Client safety plan reviewed and documented", "category": "Preparation"},
        {"title": "Psychological evaluation scheduled and completed", "category": "Preparation"},
        {"title": "Country conditions for removal country researched", "category": "Preparation"},
        # Administrative
        {"title": "Prima facie determination received", "category": "Administrative"},
        {"title": "Deferred action / work authorization received", "category": "Administrative"},
        {"title": "Confidentiality protections verified (8 USC 1367)", "category": "Administrative"},
    ],
    "U-Visa (I-918)": [
        # Filing
        {"title": "I-918 petition completed and filed", "category": "Filing"},
        {"title": "I-918 Supplement B (law enforcement certification) obtained", "category": "Filing"},
        {"title": "G-28 Notice of Entry of Appearance filed", "category": "Filing"},
        {"title": "Personal declaration drafted", "category": "Filing"},
        {"title": "I-192 waiver of inadmissibility filed (if needed)", "category": "Filing"},
        {"title": "I-918 Supplement A for qualifying family members", "category": "Filing"},
        # Evidence
        {"title": "Evidence of qualifying criminal activity documented", "category": "Evidence"},
        {"title": "Evidence of substantial physical/mental abuse", "category": "Evidence"},
        {"title": "Evidence of helpfulness to law enforcement", "category": "Evidence"},
        {"title": "Medical records / psychological evaluation", "category": "Evidence"},
        {"title": "Police reports / court records", "category": "Evidence"},
        {"title": "Affidavits from witnesses", "category": "Evidence"},
        {"title": "Certified translations of foreign documents", "category": "Evidence"},
        # Preparation
        {"title": "Client interview completed", "category": "Preparation"},
        {"title": "Law enforcement agency contacted for Supplement B", "category": "Preparation"},
        {"title": "Qualifying crime analysis completed", "category": "Preparation"},
        # Administrative
        {"title": "Biometrics completed", "category": "Administrative"},
        {"title": "Bona fide determination received (if applicable)", "category": "Administrative"},
        {"title": "Work authorization received", "category": "Administrative"},
        {"title": "3-year waiting period for adjustment tracked", "category": "Administrative"},
    ],
    "T-Visa (I-914)": [
        # Filing
        {"title": "I-914 application completed and filed", "category": "Filing"},
        {"title": "I-914 Supplement A (derivative family members)", "category": "Filing"},
        {"title": "I-914 Supplement B (declaration of law enforcement)", "category": "Filing"},
        {"title": "G-28 Notice of Entry of Appearance filed", "category": "Filing"},
        {"title": "Personal declaration drafted and finalized", "category": "Filing"},
        {"title": "I-192 waiver of inadmissibility filed (if needed)", "category": "Filing"},
        # Evidence
        {"title": "Evidence of trafficking victimization", "category": "Evidence"},
        {"title": "Evidence of physical presence due to trafficking", "category": "Evidence"},
        {"title": "Evidence of compliance with law enforcement requests", "category": "Evidence"},
        {"title": "Psychological evaluation documenting trauma", "category": "Evidence"},
        {"title": "Medical records", "category": "Evidence"},
        {"title": "Police / FBI reports", "category": "Evidence"},
        {"title": "Affidavits from social workers, counselors", "category": "Evidence"},
        # Preparation
        {"title": "Client interview (trauma-informed approach)", "category": "Preparation"},
        {"title": "Referral to victim services / shelter", "category": "Preparation"},
        # Administrative
        {"title": "Bona fide determination requested", "category": "Administrative"},
        {"title": "Work authorization received", "category": "Administrative"},
        {"title": "Continued presence request (via law enforcement)", "category": "Administrative"},
    ],
    "Special Immigrant Juvenile (SIJ)": [
        # Filing
        {"title": "State court SIJ predicate order obtained", "category": "Filing"},
        {"title": "I-360 (SIJ petition) filed with USCIS", "category": "Filing"},
        {"title": "I-485 adjustment application filed", "category": "Filing"},
        {"title": "G-28 Notice of Entry of Appearance filed", "category": "Filing"},
        # Evidence
        {"title": "Birth certificate with certified translation", "category": "Evidence"},
        {"title": "Evidence of age (under 21 at filing)", "category": "Evidence"},
        {"title": "State court order with required SIJ findings", "category": "Evidence"},
        {"title": "Evidence of abuse, neglect, or abandonment", "category": "Evidence"},
        {"title": "Declarations from client and caregivers", "category": "Evidence"},
        {"title": "School records", "category": "Evidence"},
        {"title": "Country conditions for return not in best interest", "category": "Evidence"},
        # Preparation
        {"title": "State court proceedings initiated", "category": "Preparation"},
        {"title": "Guardian ad litem appointed (if applicable)", "category": "Preparation"},
        {"title": "Best interest analysis prepared", "category": "Preparation"},
        # Administrative
        {"title": "Visa number availability confirmed", "category": "Administrative"},
        {"title": "Biometrics completed", "category": "Administrative"},
        {"title": "Age-out protections reviewed (TVPRA)", "category": "Administrative"},
    ],
    "Cancellation of Removal": [
        # Filing
        {"title": "EOIR-42B application completed and filed", "category": "Filing"},
        {"title": "G-28 filed with immigration court", "category": "Filing"},
        {"title": "Personal declaration drafted and finalized", "category": "Filing"},
        {"title": "Legal brief written", "category": "Filing"},
        {"title": "Exhibit bundle compiled with index (ICPM compliant)", "category": "Filing"},
        {"title": "Witness list with summaries filed", "category": "Filing"},
        # Evidence
        {"title": "10+ years continuous physical presence documented", "category": "Evidence"},
        {"title": "Good moral character evidence compiled (10-year period)", "category": "Evidence"},
        {"title": "Background check / FBI clearance", "category": "Evidence"},
        {"title": "Exceptional and extremely unusual hardship to USC/LPR relatives", "category": "Evidence"},
        {"title": "Medical evidence for qualifying relatives", "category": "Evidence"},
        {"title": "Psychological evaluation of qualifying relatives", "category": "Evidence"},
        {"title": "School records for USC children", "category": "Evidence"},
        {"title": "Country condition evidence (conditions upon return)", "category": "Evidence"},
        {"title": "Tax returns, employment records (10 years)", "category": "Evidence"},
        {"title": "Community ties letters (church, school, employer)", "category": "Evidence"},
        # Preparation
        {"title": "Client testimony preparation (mock hearing)", "category": "Preparation"},
        {"title": "Witness testimony prepared", "category": "Preparation"},
        {"title": "Direct and cross-examination questions prepared", "category": "Preparation"},
        {"title": "Physical presence calculation completed", "category": "Preparation"},
        # Administrative
        {"title": "Individual hearing date calendared", "category": "Administrative"},
        {"title": "30-day pre-hearing filing deadline tracked", "category": "Administrative"},
        {"title": "15-day evidence deadline tracked", "category": "Administrative"},
        {"title": "DHS lodging / pre-hearing exchange completed", "category": "Administrative"},
    ],
    "Removal Defense (General)": [
        # Filing
        {"title": "G-28 filed with immigration court", "category": "Filing"},
        {"title": "Application for relief identified and filed", "category": "Filing"},
        {"title": "Change of venue motion filed (if applicable)", "category": "Filing"},
        {"title": "Continuance motion filed (if needed)", "category": "Filing"},
        # Evidence
        {"title": "NTA reviewed for errors / DHS allegations", "category": "Evidence"},
        {"title": "Criminal history obtained and analyzed", "category": "Evidence"},
        {"title": "Prior immigration history obtained (A-file FOIA)", "category": "Evidence"},
        {"title": "Supporting evidence for relief compiled", "category": "Evidence"},
        {"title": "Country conditions researched", "category": "Evidence"},
        # Preparation
        {"title": "Legal analysis of removability charges completed", "category": "Preparation"},
        {"title": "Eligibility for relief screened (asylum, cancellation, etc.)", "category": "Preparation"},
        {"title": "Client interview and case theory developed", "category": "Preparation"},
        {"title": "Client testimony preparation", "category": "Preparation"},
        # Administrative
        {"title": "Master calendar hearing date calendared", "category": "Administrative"},
        {"title": "Individual hearing date calendared", "category": "Administrative"},
        {"title": "Filing deadlines tracked", "category": "Administrative"},
        {"title": "ICE check-in dates tracked (if applicable)", "category": "Administrative"},
        {"title": "Bond hearing requested (if detained)", "category": "Administrative"},
    ],
    "DACA (I-821D)": [
        # Filing
        {"title": "I-821D completed and filed", "category": "Filing"},
        {"title": "I-765 (EAD) filed concurrently", "category": "Filing"},
        {"title": "Filing fee paid ($495)", "category": "Filing"},
        {"title": "Passport-style photos (2x2)", "category": "Filing"},
        # Evidence
        {"title": "Proof of continuous residence since June 15, 2007", "category": "Evidence"},
        {"title": "Proof of physical presence on June 15, 2012", "category": "Evidence"},
        {"title": "Proof of entry before age 16 (for initial)", "category": "Evidence"},
        {"title": "School records / enrollment verification", "category": "Evidence"},
        {"title": "Medical / hospital records", "category": "Evidence"},
        {"title": "Financial records (bank statements, tax returns)", "category": "Evidence"},
        {"title": "Employment records", "category": "Evidence"},
        {"title": "Identity documents (passport, birth certificate, school ID)", "category": "Evidence"},
        # Preparation
        {"title": "Criminal background check clear", "category": "Preparation"},
        {"title": "Education requirement verified (HS diploma/GED/enrolled)", "category": "Preparation"},
        {"title": "Travel history reviewed (no unauthorized departure)", "category": "Preparation"},
        # Administrative
        {"title": "Biometrics appointment completed", "category": "Administrative"},
        {"title": "Renewal filed 150 days before expiration", "category": "Administrative"},
        {"title": "EAD received and employer updated", "category": "Administrative"},
    ],
    "TPS (I-821)": [
        # Filing
        {"title": "I-821 TPS application completed", "category": "Filing"},
        {"title": "I-765 (EAD) filed concurrently", "category": "Filing"},
        {"title": "Filing fee paid or fee waiver (I-912) approved", "category": "Filing"},
        {"title": "Passport-style photos (2x2)", "category": "Filing"},
        # Evidence
        {"title": "Proof of nationality (passport, birth certificate)", "category": "Evidence"},
        {"title": "Proof of continuous residence in U.S. since designation date", "category": "Evidence"},
        {"title": "Proof of continuous physical presence since cutoff date", "category": "Evidence"},
        {"title": "Identity documents", "category": "Evidence"},
        {"title": "Evidence of entry date to U.S.", "category": "Evidence"},
        # Preparation
        {"title": "TPS country designation confirmed active", "category": "Preparation"},
        {"title": "Criminal background reviewed (bars to TPS)", "category": "Preparation"},
        # Administrative
        {"title": "Biometrics completed", "category": "Administrative"},
        {"title": "Re-registration window tracked", "category": "Administrative"},
        {"title": "EAD received", "category": "Administrative"},
        {"title": "Federal Register notice for re-registration monitored", "category": "Administrative"},
    ],
    "Employment-Based (I-140)": [
        # Filing
        {"title": "PERM labor certification filed (if required)", "category": "Filing"},
        {"title": "I-140 petition filed by employer", "category": "Filing"},
        {"title": "I-485 adjustment filed (if priority date current)", "category": "Filing"},
        {"title": "I-765 (EAD) filed concurrently with I-485", "category": "Filing"},
        {"title": "I-131 (Advance Parole) filed concurrently", "category": "Filing"},
        # Evidence
        {"title": "Job offer letter / employment verification", "category": "Evidence"},
        {"title": "Education credentials evaluated (foreign degrees)", "category": "Evidence"},
        {"title": "Experience letters from prior employers", "category": "Evidence"},
        {"title": "Prevailing wage determination obtained", "category": "Evidence"},
        {"title": "Employer financial documents (ability to pay)", "category": "Evidence"},
        {"title": "Beneficiary's passport and I-94", "category": "Evidence"},
        # Preparation
        {"title": "EB category determined (EB-1, EB-2, EB-3)", "category": "Preparation"},
        {"title": "Priority date established", "category": "Preparation"},
        {"title": "National Interest Waiver analysis (if EB-2 NIW)", "category": "Preparation"},
        # Administrative
        {"title": "PERM audit response (if audited)", "category": "Administrative"},
        {"title": "Visa Bulletin monitored for priority date", "category": "Administrative"},
        {"title": "H-1B status maintained during pendency", "category": "Administrative"},
        {"title": "RFE response deadline tracked", "category": "Administrative"},
    ],
    "Bond / Custody (I-352)": [
        # Filing
        {"title": "Bond motion / request filed with immigration court", "category": "Filing"},
        {"title": "G-28 filed with court and DHS", "category": "Filing"},
        {"title": "Bond brief written", "category": "Filing"},
        # Evidence
        {"title": "Evidence of community ties (family, employer, residence)", "category": "Evidence"},
        {"title": "Evidence respondent is not a danger to community", "category": "Evidence"},
        {"title": "Evidence respondent is not a flight risk", "category": "Evidence"},
        {"title": "Letters of support from family and community", "category": "Evidence"},
        {"title": "Proof of stable residence (lease, mortgage)", "category": "Evidence"},
        {"title": "Employment verification / offer letter", "category": "Evidence"},
        {"title": "Criminal record (or lack thereof)", "category": "Evidence"},
        {"title": "Proof of immigration relief eligibility", "category": "Evidence"},
        # Preparation
        {"title": "Rodriguez bond analysis (if prolonged detention)", "category": "Preparation"},
        {"title": "Mandatory detention screening (INA 236(c))", "category": "Preparation"},
        {"title": "Bond sponsor identified and prepared", "category": "Preparation"},
        # Administrative
        {"title": "Bond hearing date calendared", "category": "Administrative"},
        {"title": "Bond amount paid (if granted)", "category": "Administrative"},
        {"title": "Conditions of release communicated to client", "category": "Administrative"},
        {"title": "Check-in schedule with ICE confirmed", "category": "Administrative"},
    ],
}

# ── Config-aware loading (JSON override with hardcoded fallback) ─────────────
CASE_TYPES: list[str] = get_config_value("case-checklist", "case_types", _DEFAULT_CASE_TYPES)
_TEMPLATES: dict[str, list[dict[str, str]]] = get_config_value("case-checklist", "templates", _DEFAULT_TEMPLATES)


def _make_item_id() -> str:
    """Generate a short unique item ID."""
    return uuid.uuid4().hex[:12]


def _new_case_id() -> str:
    """Generate a unique case ID."""
    return uuid.uuid4().hex[:16]


def _items_from_template(case_type: str) -> list[dict[str, Any]]:
    """Build checklist item dicts from a case-type template."""
    template = _TEMPLATES.get(case_type, [])
    items: list[dict[str, Any]] = []
    for entry in template:
        item = ChecklistItem(
            id=_make_item_id(),
            title=entry["title"],
            category=entry["category"],
        )
        items.append(asdict(item))
    return items


# ── Persistence helpers ──────────────────────────────────────────────────────


def _case_path(case_id: str) -> Path:
    """Return the JSON file path for a given case ID."""
    # Sanitize to prevent path traversal
    safe_id = "".join(c for c in case_id if c.isalnum() or c in "-_")
    return DATA_DIR / f"{safe_id}.json"


# ── CRUD functions ───────────────────────────────────────────────────────────


def create_case(
    client_name: str,
    case_type: str,
    a_number: str = "",
    attorney: str = "",
) -> dict[str, Any]:
    """Create a new case auto-populated from a case-type template.

    Args:
        client_name: Full legal name of the client.
        case_type: One of the keys in CASE_TYPES.
        a_number: Alien registration number (optional).
        attorney: Name of the assigned attorney.

    Returns:
        The newly-created case dict, already saved to disk.
    """
    now = datetime.now().isoformat(timespec="seconds")
    case_id = _new_case_id()

    case_data: dict[str, Any] = {
        "id": case_id,
        "client_name": client_name,
        "a_number": a_number,
        "case_type": case_type,
        "attorney": attorney,
        "created_at": now,
        "updated_at": now,
        "status": "Active",
        "items": _items_from_template(case_type),
    }

    save_case(case_data)
    return case_data


def save_case(case_data: dict[str, Any]) -> None:
    """Persist a case dict to disk as JSON.

    Args:
        case_data: Must contain an ``id`` key.
    """
    case_id = case_data.get("id", "")
    if not case_id:
        raise ValueError("case_data must include an 'id' key.")
    case_data["updated_at"] = datetime.now().isoformat(timespec="seconds")
    path = _case_path(case_id)
    path.write_text(json.dumps(case_data, indent=2, default=str))


def load_case(case_id: str) -> dict[str, Any] | None:
    """Load a single case by its ID.

    Returns:
        The case dict, or ``None`` if not found or unreadable.
    """
    path = _case_path(case_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def list_cases() -> list[dict[str, Any]]:
    """Return all saved cases, sorted by most-recently updated first."""
    cases: list[dict[str, Any]] = []
    if not DATA_DIR.exists():
        return cases
    for path in DATA_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text())
            cases.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    # Sort by updated_at descending
    cases.sort(key=lambda c: c.get("updated_at", ""), reverse=True)
    return cases


def delete_case(case_id: str) -> bool:
    """Delete a case from disk.

    Returns:
        ``True`` if the file was deleted, ``False`` if it didn't exist.
    """
    path = _case_path(case_id)
    if path.exists():
        path.unlink()
        return True
    return False


def update_item(case_id: str, item_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    """Update a single checklist item within a case.

    Args:
        case_id: The case identifier.
        item_id: The unique item ID within the case's checklist.
        updates: Dict of fields to update, e.g.
            ``{"is_completed": True, "deadline": "2026-06-01", "notes": "..."}``.

    Returns:
        The updated case dict, or ``None`` if the case or item wasn't found.
    """
    case_data = load_case(case_id)
    if case_data is None:
        return None

    items = case_data.get("items", [])
    target = None
    for item in items:
        if item.get("id") == item_id:
            target = item
            break

    if target is None:
        return None

    # Apply updates
    for key, value in updates.items():
        if key in ("is_completed", "deadline", "notes"):
            target[key] = value

    # Auto-set completed_date when completing an item
    if updates.get("is_completed") is True:
        target["completed_date"] = date.today().isoformat()
    elif updates.get("is_completed") is False:
        target["completed_date"] = None

    save_case(case_data)
    return case_data


def add_custom_item(
    case_id: str,
    title: str,
    category: str,
    deadline: str | None = None,
) -> dict[str, Any] | None:
    """Add a custom checklist item to an existing case.

    Args:
        case_id: The case identifier.
        title: Label for the new item.
        category: One of Filing, Evidence, Preparation, Administrative.
        deadline: Optional ISO date string for the deadline.

    Returns:
        The updated case dict, or ``None`` if the case wasn't found.
    """
    case_data = load_case(case_id)
    if case_data is None:
        return None

    new_item = ChecklistItem(
        id=_make_item_id(),
        title=title,
        category=category,
        deadline=deadline,
    )
    case_data["items"].append(asdict(new_item))
    save_case(case_data)
    return case_data


def get_case_progress(case_data: dict[str, Any]) -> dict[str, Any]:
    """Compute completion progress for a case.

    Returns a dict with ``total``, ``completed``, and ``pct`` keys,
    plus a ``by_category`` breakdown.
    """
    items = case_data.get("items", [])
    total = len(items)
    completed = sum(1 for item in items if item.get("is_completed"))
    pct = round((completed / total) * 100) if total > 0 else 0

    by_category: dict[str, dict[str, int]] = {}
    for item in items:
        cat = item.get("category", "General")
        if cat not in by_category:
            by_category[cat] = {"total": 0, "completed": 0}
        by_category[cat]["total"] += 1
        if item.get("is_completed"):
            by_category[cat]["completed"] += 1

    return {
        "total": total,
        "completed": completed,
        "pct": pct,
        "by_category": by_category,
    }


def get_deadline_status(deadline_str: str | None) -> dict[str, Any]:
    """Evaluate a deadline relative to today.

    Returns:
        A dict with ``days_remaining``, ``label``, and ``urgency``
        (one of ``overdue``, ``due_soon``, ``on_track``, or ``none``).
    """
    if not deadline_str:
        return {"days_remaining": None, "label": "", "urgency": "none"}

    try:
        dl = datetime.strptime(deadline_str, "%Y-%m-%d").date()
    except ValueError:
        return {"days_remaining": None, "label": "", "urgency": "none"}

    today = date.today()
    days_remaining = (dl - today).days

    if days_remaining < 0:
        return {
            "days_remaining": days_remaining,
            "label": f"OVERDUE by {abs(days_remaining)} day{'s' if abs(days_remaining) != 1 else ''}",
            "urgency": "overdue",
        }
    elif days_remaining <= 7:
        return {
            "days_remaining": days_remaining,
            "label": f"Due in {days_remaining} day{'s' if days_remaining != 1 else ''}",
            "urgency": "due_soon",
        }
    else:
        return {
            "days_remaining": days_remaining,
            "label": f"Due in {days_remaining} days",
            "urgency": "on_track",
        }
