"""Case law management for the Legal Research tool.

Provides structured access to landmark immigration decisions, BIA precedent,
and federal court holdings. Supports search by topic, citation, and keyword,
plus JSON-based collection persistence.

Part of the O'Brien Immigration Law tool suite.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.config_store import get_config_value


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "collections"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class CaseLaw:
    """A single case law entry with citation and holding information."""

    name: str
    citation: str
    court: str
    date: str
    holding: str
    full_text: str = ""
    topics: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Landmark immigration decisions
# ---------------------------------------------------------------------------

_DEFAULT_KEY_DECISIONS: dict[str, CaseLaw] = {
    "matter-of-acosta": CaseLaw(
        name="Matter of Acosta",
        citation="19 I&N Dec. 211 (BIA 1985)",
        court="BIA",
        date="1985-03-01",
        holding=(
            "Defined 'particular social group' as a group of persons who share "
            "a common, immutable characteristic -- one that members either cannot "
            "change or should not be required to change because it is fundamental "
            "to their individual identities or consciences."
        ),
        topics=["particular social group", "asylum"],
    ),
    "matter-of-mogharrabi": CaseLaw(
        name="Matter of Mogharrabi",
        citation="19 I&N Dec. 439 (BIA 1987)",
        court="BIA",
        date="1987-06-12",
        holding=(
            "Established the standard for well-founded fear of persecution: "
            "an applicant must show that a reasonable person in the applicant's "
            "circumstances would fear persecution on account of a protected ground."
        ),
        topics=["well-founded fear", "asylum"],
    ),
    "ins-v-cardoza-fonseca": CaseLaw(
        name="INS v. Cardoza-Fonseca",
        citation="480 U.S. 421 (1987)",
        court="Supreme Court",
        date="1987-03-09",
        holding=(
            "Held that the 'well-founded fear' standard for asylum is more "
            "generous than the 'clear probability' standard for withholding "
            "of deportation. An applicant need not prove that persecution is "
            "more likely than not, only that there is a reasonable possibility."
        ),
        topics=["asylum", "well-founded fear", "withholding"],
    ),
    "matter-of-a-b": CaseLaw(
        name="Matter of A-B-",
        citation="27 I&N Dec. 316 (A.G. 2018)",
        court="Attorney General",
        date="2018-06-11",
        holding=(
            "Held that claims based on domestic violence and gang violence "
            "generally will not qualify for asylum, stating that such claims "
            "are unlikely to satisfy the requirements for a cognizable "
            "particular social group. Subsequently vacated by Matter of A-B- II "
            "and AG Garland's 2021 decision."
        ),
        topics=["particular social group", "domestic violence", "asylum"],
    ),
    "matter-of-l-e-a": CaseLaw(
        name="Matter of L-E-A-",
        citation="27 I&N Dec. 581 (A.G. 2019)",
        court="Attorney General",
        date="2019-07-29",
        holding=(
            "Addressed whether family can constitute a particular social group. "
            "Held that while the nuclear family may be a cognizable PSG in some "
            "cases, an applicant must still demonstrate that family membership "
            "was a central reason for the claimed persecution. Subsequently "
            "vacated by AG Garland in 2021."
        ),
        topics=["particular social group", "family", "nexus", "asylum"],
    ),
    "matter-of-m-e-v-g": CaseLaw(
        name="Matter of M-E-V-G-",
        citation="26 I&N Dec. 227 (BIA 2014)",
        court="BIA",
        date="2014-02-07",
        holding=(
            "Established the modern three-part test for particular social group: "
            "(1) immutability -- the group must be defined by a characteristic "
            "that is immutable or fundamental; (2) particularity -- the group "
            "must be defined with sufficient particularity; and (3) social "
            "distinction -- the group must be perceived as a distinct group by "
            "the society in question."
        ),
        topics=[
            "particular social group",
            "immutability",
            "particularity",
            "social distinction",
            "asylum",
        ],
    ),
    # -------------------------------------------------------------------
    # Additional landmark decisions
    # -------------------------------------------------------------------
    "matter-of-kasinga": CaseLaw(
        name="Matter of Kasinga",
        citation="21 I&N Dec. 357 (BIA 1996)",
        court="BIA",
        date="1996-06-13",
        holding=(
            "Recognized female genital mutilation (FGM) as a form of persecution "
            "and held that young women of a particular tribe who have not been "
            "subjected to FGM and who oppose the practice constitute a cognizable "
            "particular social group. Landmark decision expanding PSG analysis "
            "to gender-based claims."
        ),
        topics=["particular social group", "gender", "persecution", "asylum"],
    ),
    "matter-of-toboso-alfonso": CaseLaw(
        name="Matter of Toboso-Alfonso",
        citation="20 I&N Dec. 819 (BIA 1990)",
        court="BIA",
        date="1990-03-12",
        holding=(
            "Held that sexual orientation can form the basis for a particular "
            "social group claim. The respondent, a Cuban national persecuted "
            "for being homosexual, was granted withholding of deportation. "
            "Designated as precedent by AG Reno in 1994."
        ),
        topics=["particular social group", "sexual orientation", "withholding", "asylum"],
    ),
    "matter-of-s-p": CaseLaw(
        name="Matter of S-P-",
        citation="21 I&N Dec. 486 (BIA 1996)",
        court="BIA",
        date="1996-06-27",
        holding=(
            "Articulated key credibility factors for asylum adjudication: "
            "the immigration judge should consider the totality of the "
            "circumstances, including the applicant's demeanor, the plausibility "
            "and consistency of the account, and any corroborating evidence. "
            "Minor inconsistencies alone do not necessarily undermine credibility."
        ),
        topics=["credibility", "asylum"],
    ),
    "matter-of-y-b": CaseLaw(
        name="Matter of Y-B-",
        citation="21 I&N Dec. 1136 (BIA 1998)",
        court="BIA",
        date="1998-12-18",
        holding=(
            "Addressed the corroboration requirement for asylum claims. Held that "
            "an applicant's testimony alone may be sufficient to sustain the "
            "burden of proof, but that where it is reasonable to expect "
            "corroborating evidence, its absence may form a proper basis for "
            "an adverse credibility or burden-of-proof finding."
        ),
        topics=["corroboration", "credibility", "asylum"],
    ),
    "ins-v-elias-zacarias": CaseLaw(
        name="INS v. Elias-Zacarias",
        citation="502 U.S. 478 (1992)",
        court="Supreme Court",
        date="1992-01-22",
        holding=(
            "Held that a guerrilla organization's attempt to coerce a person "
            "into performing military service does not necessarily constitute "
            "'persecution on account of political opinion.' The applicant must "
            "demonstrate that the persecutor seeks to punish the victim because "
            "of the victim's political opinion, not merely that the victim "
            "disagrees with the persecutor."
        ),
        topics=["political opinion", "nexus", "imputed opinion", "asylum"],
    ),
    "matter-of-c-a": CaseLaw(
        name="Matter of C-A-",
        citation="23 I&N Dec. 951 (BIA 2006)",
        court="BIA",
        date="2006-11-27",
        holding=(
            "Addressed claims based on forced recruitment by guerrilla or "
            "paramilitary organizations. Held that former members of the "
            "non-combatant civilian population of a specific department who "
            "do not wish to join the guerrillas did not constitute a cognizable "
            "particular social group because the group lacked social visibility."
        ),
        topics=["particular social group", "forced recruitment", "social visibility", "asylum"],
    ),
    "matter-of-w-g-r": CaseLaw(
        name="Matter of W-G-R-",
        citation="26 I&N Dec. 208 (BIA 2014)",
        court="BIA",
        date="2014-02-07",
        holding=(
            "Companion case to Matter of M-E-V-G-. Applied the refined "
            "three-part PSG test (immutability, particularity, social distinction) "
            "and held that 'former members of the Mara 18 gang in El Salvador "
            "who have renounced their gang membership' did not meet the "
            "particularity and social distinction requirements."
        ),
        topics=[
            "particular social group",
            "gang",
            "particularity",
            "social distinction",
            "asylum",
        ],
    ),
    "dent-v-holder": CaseLaw(
        name="Dent v. Holder",
        citation="627 F.3d 365 (9th Cir. 2010)",
        court="9th Circuit",
        date="2010-12-03",
        holding=(
            "Addressed the standard for 'acquiescence' under the Convention "
            "Against Torture (CAT). Held that government acquiescence to torture "
            "requires only that public officials have awareness of the activity "
            "and breach their legal responsibility to intervene to prevent it. "
            "Willful blindness by government officials satisfies the acquiescence "
            "standard."
        ),
        topics=["CAT", "acquiescence", "government complicity"],
    ),
    "matter-of-e-a-g": CaseLaw(
        name="Matter of E-A-G-",
        citation="24 I&N Dec. 591 (BIA 2008)",
        court="BIA",
        date="2008-07-30",
        holding=(
            "Held that persons resistant to gang membership in El Salvador did "
            "not constitute a particular social group. Found that the claimed "
            "group lacked the requisite social visibility and that being targeted "
            "by gangs for recruitment is not persecution on account of a "
            "protected ground but rather reflects the gang's desire for new members."
        ),
        topics=["particular social group", "gang", "social visibility", "asylum"],
    ),
    "matter-of-recinas": CaseLaw(
        name="Matter of Recinas",
        citation="23 I&N Dec. 467 (BIA 2002)",
        court="BIA",
        date="2002-05-20",
        holding=(
            "Addressed the 'exceptional and extremely unusual hardship' standard "
            "for cancellation of removal under INA 240A(b). Found that the "
            "respondent, a single mother with multiple U.S. citizen children, "
            "demonstrated the requisite hardship by showing the children would "
            "face severe economic deprivation and loss of educational opportunity "
            "if removed to Guatemala."
        ),
        topics=["cancellation of removal", "hardship", "USC children"],
    ),
}


# ---------------------------------------------------------------------------
# Legal topics for filtering and categorization
# ---------------------------------------------------------------------------

_DEFAULT_LEGAL_TOPICS: list[str] = [
    "asylum",
    "withholding",
    "CAT",
    "particular social group",
    "nexus",
    "credibility",
    "corroboration",
    "firm resettlement",
    "one-year bar",
    "political opinion",
    "gender",
    "sexual orientation",
    "domestic violence",
    "gang",
    "cancellation of removal",
    "hardship",
    "persecution",
    "acquiescence",
    "forced recruitment",
    "family",
]


# ── Config-aware loading (JSON override with hardcoded fallback) ─────────────
def _load_decisions() -> dict[str, CaseLaw]:
    """Load decisions from config (plain dicts) or fall back to hardcoded defaults."""
    from dataclasses import asdict
    _default_dicts = {k: asdict(v) for k, v in _DEFAULT_KEY_DECISIONS.items()}
    raw = get_config_value("legal-research", "decisions", _default_dicts)
    result: dict[str, CaseLaw] = {}
    for k, v in raw.items():
        if isinstance(v, CaseLaw):
            result[k] = v
        else:
            result[k] = CaseLaw(
                name=v.get("name", ""),
                citation=v.get("citation", ""),
                court=v.get("court", ""),
                date=v.get("date", ""),
                holding=v.get("holding", ""),
                full_text=v.get("full_text", ""),
                topics=v.get("topics", []),
            )
    return result

KEY_DECISIONS: dict[str, CaseLaw] = _load_decisions()
LEGAL_TOPICS: list[str] = get_config_value("legal-research", "topics", _DEFAULT_LEGAL_TOPICS)


# ---------------------------------------------------------------------------
# Search and retrieval
# ---------------------------------------------------------------------------


def search_decisions(
    query: str,
    topics: list[str] | None = None,
    limit: int = 20,
) -> list[CaseLaw]:
    """Search indexed case law and BIA decisions.

    Each word of the query is checked independently against the decision's
    name, holding, citation, and topics.  A decision matches when ALL query
    words are found somewhere across those fields.

    Args:
        query: Free-text search query.
        topics: Optional list of legal topics to filter by.
        limit: Maximum number of results to return.

    Returns:
        List of matching CaseLaw entries.
    """
    results: list[CaseLaw] = []
    query_words = query.lower().split()
    if not query_words:
        # Empty query: return all, optionally filtered by topic
        for _key, decision in KEY_DECISIONS.items():
            if topics:
                if any(t in decision.topics for t in topics):
                    results.append(decision)
            else:
                results.append(decision)
        return results[:limit]

    for _key, decision in KEY_DECISIONS.items():
        # Build a searchable text blob from all relevant fields
        searchable = " ".join([
            decision.name.lower(),
            decision.holding.lower(),
            decision.citation.lower(),
            " ".join(decision.topics).lower(),
        ])

        # Every query word must appear somewhere in the searchable text
        if all(word in searchable for word in query_words):
            if topics:
                if any(t in decision.topics for t in topics):
                    results.append(decision)
            else:
                results.append(decision)

    return results[:limit]


def get_by_citation(citation: str) -> CaseLaw | None:
    """Look up a decision by its citation string.

    Args:
        citation: Full or partial citation (e.g. "19 I&N Dec. 211").

    Returns:
        The matching CaseLaw entry, or None if not found.
    """
    citation_lower = citation.lower()
    for _key, decision in KEY_DECISIONS.items():
        if citation_lower in decision.citation.lower():
            return decision
    return None


def get_decision_by_key(key: str) -> CaseLaw | None:
    """Look up a decision by its dictionary key."""
    return KEY_DECISIONS.get(key)


# ---------------------------------------------------------------------------
# Collection persistence
# ---------------------------------------------------------------------------


def _collection_path(collection_id: str) -> Path:
    """Return the JSON file path for a given collection ID."""
    safe_id = "".join(c for c in collection_id if c.isalnum() or c in "-_")
    return DATA_DIR / f"{safe_id}.json"


def new_collection_id() -> str:
    """Generate a short unique collection ID."""
    return str(uuid.uuid4())[:8]


def save_collection(
    collection_id: str,
    case_name: str,
    a_number: str,
    decisions: list[dict[str, Any]],
    notes: str = "",
) -> dict[str, Any]:
    """Save or update a collection of decisions.

    Args:
        collection_id: Unique identifier for the collection.
        case_name: Client or case name.
        a_number: Alien registration number.
        decisions: List of decision dicts (each has name, citation, holding, etc.).
        notes: Free-text notes about this research collection.

    Returns:
        The saved collection dict.
    """
    path = _collection_path(collection_id)
    now = datetime.now().isoformat(timespec="seconds")

    created_at = now
    if path.exists():
        try:
            existing = json.loads(path.read_text())
            created_at = existing.get("created_at", now)
        except Exception:
            pass

    collection: dict[str, Any] = {
        "id": collection_id,
        "case_name": case_name,
        "a_number": a_number,
        "decisions": decisions,
        "notes": notes,
        "created_at": created_at,
        "updated_at": now,
    }

    path.write_text(json.dumps(collection, indent=2))
    return collection


def load_collection(collection_id: str) -> dict[str, Any] | None:
    """Load a collection by ID.

    Returns:
        The collection dict, or None if not found.
    """
    path = _collection_path(collection_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def list_collections() -> list[dict[str, Any]]:
    """Return summary info for all saved collections, newest first."""
    collections: list[dict[str, Any]] = []
    if not DATA_DIR.exists():
        return collections
    for p in DATA_DIR.glob("*.json"):
        try:
            data = json.loads(p.read_text())
            collections.append({
                "id": data["id"],
                "case_name": data.get("case_name", "Unnamed"),
                "a_number": data.get("a_number", ""),
                "decision_count": len(data.get("decisions", [])),
                "updated_at": data.get("updated_at", ""),
                "created_at": data.get("created_at", ""),
            })
        except Exception:
            continue
    collections.sort(key=lambda c: c["updated_at"], reverse=True)
    return collections


def delete_collection(collection_id: str) -> bool:
    """Delete a collection. Returns True if the file existed."""
    path = _collection_path(collection_id)
    if path.exists():
        path.unlink()
        return True
    return False
