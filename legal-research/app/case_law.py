"""Case law management for the Legal Research tool.

Provides structured access to landmark immigration decisions, BIA precedent,
and federal court holdings. Supports search by topic, citation, and keyword.

Part of the O'Brien Immigration Law tool suite.
"""

from dataclasses import dataclass, field
from datetime import date


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

KEY_DECISIONS: dict[str, CaseLaw] = {
    "matter-of-acosta": CaseLaw(
        name="Matter of Acosta",
        citation="19 I&N Dec. 211 (BIA 1985)",
        court="BIA",
        date="1985-03-01",
        holding=(
            "Defined 'particular social group' as a group of persons who share "
            "a common, immutable characteristic — one that members either cannot "
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
            "(1) immutability — the group must be defined by a characteristic "
            "that is immutable or fundamental; (2) particularity — the group "
            "must be defined with sufficient particularity; and (3) social "
            "distinction — the group must be perceived as a distinct group by "
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
}


# ---------------------------------------------------------------------------
# Legal topics for filtering and categorization
# ---------------------------------------------------------------------------

LEGAL_TOPICS: list[str] = [
    "asylum",
    "withholding",
    "CAT",
    "particular social group",
    "nexus",
    "credibility",
    "firm resettlement",
    "one-year bar",
]


# ---------------------------------------------------------------------------
# Search and retrieval stubs
# ---------------------------------------------------------------------------

def search_decisions(
    query: str,
    topics: list[str] | None = None,
    limit: int = 20,
) -> list[CaseLaw]:
    """Search indexed case law and BIA decisions.

    Args:
        query: Free-text search query.
        topics: Optional list of legal topics to filter by.
        limit: Maximum number of results to return.

    Returns:
        List of matching CaseLaw entries, ordered by relevance.

    TODO: Implement vector search using ChromaDB for semantic matching.
    TODO: Add support for citation-based search (e.g. "19 I&N Dec. 211").
    TODO: Index full-text decisions from BIA and federal reporters.
    TODO: Support circuit-specific filtering (9th Cir, 2nd Cir, etc.).
    """
    results: list[CaseLaw] = []

    query_lower = query.lower()
    for _key, decision in KEY_DECISIONS.items():
        # Basic substring matching as a placeholder
        if (
            query_lower in decision.name.lower()
            or query_lower in decision.holding.lower()
            or query_lower in decision.citation.lower()
        ):
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

    TODO: Implement fuzzy citation matching.
    TODO: Support multiple citation formats (I&N Dec., F.3d, S.Ct.).
    """
    citation_lower = citation.lower()
    for _key, decision in KEY_DECISIONS.items():
        if citation_lower in decision.citation.lower():
            return decision
    return None
