"""Config store for brief types, boilerplate, and merge fields.

Reads/writes the ``brief-builder`` config key so that changes stay in sync
with the Brief Builder tool (:8507).

Part of the O'Brien Immigration Law tool suite.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.config_store import get_config_value, save_config


# ---------------------------------------------------------------------------
# Default brief types (fallback when no config exists yet)
# ---------------------------------------------------------------------------

_DEFAULT_BRIEF_TYPES: dict[str, list[dict[str, Any]]] = {
    "Asylum Merits Brief": [
        {"key": "introduction", "heading": "Introduction", "subsections": []},
        {"key": "statement_of_facts", "heading": "Statement of Facts", "subsections": []},
        {
            "key": "legal_standard",
            "heading": "Legal Standard",
            "subsections": [
                {"key": "asylum_standard", "heading": "Asylum under INA \u00a7208"},
                {"key": "withholding_standard", "heading": "Withholding of Removal under INA \u00a7241(b)(3)"},
                {"key": "cat_standard", "heading": "Protection under the Convention Against Torture"},
            ],
        },
        {
            "key": "argument",
            "heading": "Argument",
            "subsections": [
                {"key": "past_persecution", "heading": "Past Persecution"},
                {"key": "well_founded_fear", "heading": "Well-Founded Fear of Future Persecution"},
                {"key": "nexus", "heading": "Nexus to a Protected Ground"},
                {"key": "particular_social_group", "heading": "Particular Social Group"},
            ],
        },
        {"key": "country_conditions", "heading": "Country Conditions", "subsections": []},
        {"key": "conclusion", "heading": "Conclusion", "subsections": []},
    ],
    "Motion to Reopen": [
        {"key": "introduction", "heading": "Introduction", "subsections": []},
        {"key": "procedural_history", "heading": "Procedural History", "subsections": []},
        {"key": "legal_standard", "heading": "Legal Standard for Motions to Reopen", "subsections": []},
        {"key": "changed_country_conditions", "heading": "Changed Country Conditions", "subsections": []},
        {"key": "previously_unavailable_evidence", "heading": "Previously Unavailable Evidence", "subsections": []},
        {"key": "argument", "heading": "Argument", "subsections": []},
        {"key": "conclusion", "heading": "Conclusion", "subsections": []},
    ],
    "Appeal Brief": [
        {"key": "introduction", "heading": "Introduction", "subsections": []},
        {"key": "statement_of_facts", "heading": "Statement of Facts", "subsections": []},
        {"key": "issues_on_appeal", "heading": "Issues on Appeal", "subsections": []},
        {"key": "standard_of_review", "heading": "Standard of Review", "subsections": []},
        {"key": "argument", "heading": "Argument", "subsections": []},
        {"key": "conclusion", "heading": "Conclusion", "subsections": []},
    ],
    "Bond Brief": [
        {"key": "introduction", "heading": "Introduction", "subsections": []},
        {"key": "statement_of_facts", "heading": "Statement of Facts", "subsections": []},
        {"key": "legal_standard", "heading": "Legal Standard for Bond", "subsections": []},
        {"key": "not_a_danger", "heading": "Respondent Is Not a Danger to the Community", "subsections": []},
        {"key": "not_a_flight_risk", "heading": "Respondent Is Not a Flight Risk", "subsections": []},
        {"key": "conclusion", "heading": "Conclusion", "subsections": []},
    ],
    "Cancellation of Removal": [
        {"key": "introduction", "heading": "Introduction", "subsections": []},
        {"key": "statement_of_facts", "heading": "Statement of Facts", "subsections": []},
        {"key": "legal_standard", "heading": "Legal Standard for Cancellation of Removal", "subsections": []},
        {"key": "continuous_physical_presence", "heading": "Continuous Physical Presence", "subsections": []},
        {"key": "good_moral_character", "heading": "Good Moral Character", "subsections": []},
        {"key": "exceptional_hardship", "heading": "Exceptional and Extremely Unusual Hardship", "subsections": []},
        {"key": "conclusion", "heading": "Conclusion", "subsections": []},
    ],
    "Motion to Terminate": [
        {"key": "introduction", "heading": "Introduction", "subsections": []},
        {"key": "procedural_history", "heading": "Procedural History", "subsections": []},
        {"key": "statement_of_facts", "heading": "Statement of Facts", "subsections": []},
        {"key": "legal_standard", "heading": "Legal Standard", "subsections": []},
        {
            "key": "argument",
            "heading": "Argument",
            "subsections": [
                {"key": "nta_deficiency", "heading": "NTA Deficiency"},
                {"key": "no_jurisdiction", "heading": "No Jurisdiction"},
            ],
        },
        {"key": "conclusion", "heading": "Conclusion", "subsections": []},
    ],
    "Motion for Continuance": [
        {"key": "introduction", "heading": "Introduction", "subsections": []},
        {"key": "procedural_history", "heading": "Procedural History", "subsections": []},
        {"key": "good_cause", "heading": "Good Cause for Continuance", "subsections": []},
        {"key": "no_prejudice", "heading": "No Prejudice to DHS", "subsections": []},
        {"key": "conclusion", "heading": "Conclusion", "subsections": []},
    ],
    "Motion to Change Venue": [
        {"key": "introduction", "heading": "Introduction", "subsections": []},
        {"key": "procedural_history", "heading": "Procedural History", "subsections": []},
        {"key": "good_cause_venue", "heading": "Good Cause for Change of Venue", "subsections": []},
        {"key": "administrative_convenience", "heading": "Administrative Convenience", "subsections": []},
        {"key": "conclusion", "heading": "Conclusion", "subsections": []},
    ],
    "Motion to Suppress": [
        {"key": "introduction", "heading": "Introduction", "subsections": []},
        {"key": "statement_of_facts", "heading": "Statement of Facts", "subsections": []},
        {
            "key": "legal_standard",
            "heading": "Legal Standard",
            "subsections": [
                {"key": "fourth_amendment", "heading": "Fourth Amendment"},
                {"key": "egregious_violations", "heading": "Egregious Violations Standard"},
            ],
        },
        {"key": "argument", "heading": "Argument", "subsections": []},
        {"key": "conclusion", "heading": "Conclusion", "subsections": []},
    ],
}


# ---------------------------------------------------------------------------
# Default boilerplate (statutes, regulations, and case law)
# ---------------------------------------------------------------------------

_DEFAULT_BOILERPLATE: dict[str, dict[str, str]] = {
    "Asylum Merits Brief": {
        "asylum_standard": (
            "To establish eligibility for asylum, an applicant must demonstrate that "
            "he or she is a refugee within the meaning of INA \u00a7101(a)(42)(A), "
            "8 U.S.C. \u00a71101(a)(42)(A). See INA \u00a7208(b)(1), 8 U.S.C. \u00a71158(b)(1). "
            "A refugee is a person who is unable or unwilling to return to his or her "
            "country of nationality because of persecution or a well-founded fear of "
            "persecution on account of race, religion, nationality, membership in a "
            "particular social group, or political opinion. INA \u00a7101(a)(42)(A)."
        ),
        "withholding_standard": (
            "To qualify for withholding of removal under INA \u00a7241(b)(3), "
            "8 U.S.C. \u00a71231(b)(3), the applicant must demonstrate that it is "
            "\"more likely than not\" that his or her life or freedom would be threatened "
            "on account of a protected ground. INS v. Stevic, 467 U.S. 407, 429-30 (1984). "
            "The applicant must show a \"clear probability\" of persecution. "
            "INS v. Cardoza-Fonseca, 480 U.S. 421, 430 (1987)."
        ),
        "cat_standard": (
            "To establish eligibility for protection under the Convention Against Torture, "
            "the applicant must show that it is \"more likely than not\" that he or she "
            "would be tortured if removed to the proposed country of removal. "
            "8 C.F.R. \u00a71208.16(c)(2). Torture is defined as any act by which severe "
            "pain or suffering is intentionally inflicted on a person by or at the "
            "instigation of or with the consent or acquiescence of a public official. "
            "8 C.F.R. \u00a71208.18(a)(1)."
        ),
        "past_persecution": (
            "An applicant who establishes past persecution is presumed to have a "
            "well-founded fear of future persecution. 8 C.F.R. \u00a71208.13(b)(1). "
            "The burden then shifts to DHS to rebut the presumption by showing, by a "
            "preponderance of the evidence, that conditions in the country have changed "
            "or that the applicant could reasonably relocate. Id."
        ),
        "well_founded_fear": (
            "An applicant may establish a well-founded fear of future persecution by "
            "showing that there is a reasonable possibility of persecution. "
            "INS v. Cardoza-Fonseca, 480 U.S. 421, 440 (1987). The standard requires "
            "a showing that persecution is a reasonable possibility, which can be "
            "established by as little as a 10% chance. Id. at 431."
        ),
        "nexus": (
            "The applicant must establish a nexus between the persecution feared and "
            "one of the five protected grounds: race, religion, nationality, membership "
            "in a particular social group, or political opinion. INA \u00a7208(b)(1)(B)(i). "
            "The protected ground need not be the sole reason for persecution, but must "
            "be \"at least one central reason.\" INA \u00a7208(b)(1)(B)(i); see also "
            "Matter of J-B-N- & S-M-, 24 I&N Dec. 208 (BIA 2007)."
        ),
        "particular_social_group": (
            "A particular social group must be (1) composed of members who share a "
            "common immutable characteristic, (2) defined with particularity, and "
            "(3) socially distinct within the society in question. "
            "Matter of M-E-V-G-, 26 I&N Dec. 227 (BIA 2014); "
            "Matter of W-G-R-, 26 I&N Dec. 208 (BIA 2014). An immutable characteristic "
            "is one that members either cannot change or should not be required to change "
            "because it is fundamental to their identity. "
            "Matter of Acosta, 19 I&N Dec. 211, 233 (BIA 1985)."
        ),
    },
    "Motion to Reopen": {
        "legal_standard": (
            "A motion to reopen must be filed within 90 days of the date of entry "
            "of a final administrative order. INA \u00a7240(c)(7)(C)(i), "
            "8 U.S.C. \u00a71229a(c)(7)(C)(i). However, there is no time or number "
            "limitation for motions to reopen based on changed country conditions. "
            "INA \u00a7240(c)(7)(C)(ii). The movant must present evidence that is material "
            "and was not available and could not have been discovered or presented at "
            "the former hearing. 8 C.F.R. \u00a71003.23(b)(3)."
        ),
    },
    "Appeal Brief": {
        "standard_of_review": (
            "The Board of Immigration Appeals reviews findings of fact under a "
            "\"clearly erroneous\" standard. 8 C.F.R. \u00a71003.1(d)(3)(i). Questions "
            "of law, discretion, and judgment are reviewed de novo. "
            "8 C.F.R. \u00a71003.1(d)(3)(ii). The Board gives deference to the "
            "Immigration Judge's credibility findings based on demeanor. "
            "Matter of A-S-, 21 I&N Dec. 1106 (BIA 1998)."
        ),
    },
    "Bond Brief": {
        "legal_standard": (
            "An Immigration Judge may grant bond to a detained respondent upon a "
            "finding that the respondent does not pose a danger to the community "
            "and is not a flight risk. Matter of Guerra, 24 I&N Dec. 37 (BIA 2006). "
            "The minimum bond amount is $1,500. INA \u00a7236(a)(2)(A), "
            "8 U.S.C. \u00a71226(a)(2)(A). The Immigration Judge should consider the "
            "totality of the circumstances, including ties to the community, "
            "employment history, criminal history, immigration history, and "
            "manner of entry. Matter of Guerra, 24 I&N Dec. at 40."
        ),
    },
    "Cancellation of Removal": {
        "legal_standard": (
            "To qualify for cancellation of removal under INA \u00a7240A(b)(1), "
            "8 U.S.C. \u00a71229b(b)(1), a non-permanent resident must demonstrate: "
            "(1) continuous physical presence in the United States for not less than "
            "10 years; (2) good moral character during that period; (3) no disqualifying "
            "criminal convictions; and (4) that removal would result in exceptional and "
            "extremely unusual hardship to a qualifying relative who is a U.S. citizen "
            "or lawful permanent resident. See Matter of Recinas, 23 I&N Dec. 467 "
            "(BIA 2002)."
        ),
    },
    "Motion to Terminate": {
        "legal_standard": (
            "An Immigration Judge may terminate removal proceedings where the "
            "Notice to Appear (NTA) fails to meet the requirements of INA "
            "\u00a7239(a)(1), 8 U.S.C. \u00a71229(a)(1). The Supreme Court held in "
            "Pereira v. Sessions, 138 S. Ct. 2105 (2018), that a putative "
            "notice to appear that fails to designate the specific time or "
            "place of the removal proceedings is not a 'notice to appear' "
            "under \u00a7239(a). See also Matter of Bermudez-Cota, 27 I&N Dec. "
            "441 (BIA 2018)."
        ),
        "nta_deficiency": (
            "The NTA in this case fails to comply with the statutory "
            "requirements of INA \u00a7239(a)(1) because it does not specify "
            "the time and place of the hearing. Under Pereira v. Sessions, "
            "138 S. Ct. 2105 (2018), a document that fails to include this "
            "information is not a valid 'notice to appear' and does not "
            "trigger the stop-time rule or vest jurisdiction with the "
            "Immigration Court."
        ),
        "no_jurisdiction": (
            "Where an NTA is deficient under INA \u00a7239(a)(1), the "
            "Immigration Court lacks jurisdiction over the proceedings. "
            "Matter of Bermudez-Cota, 27 I&N Dec. 441 (BIA 2018), holds "
            "that a two-step notice process can cure certain NTA defects. "
            "However, where the NTA is fundamentally deficient, termination "
            "is the appropriate remedy."
        ),
    },
    "Motion for Continuance": {
        "good_cause": (
            "An Immigration Judge may grant a continuance for good cause "
            "shown. 8 C.F.R. \u00a71003.29. In determining whether to grant a "
            "continuance, the Immigration Judge should consider the reasons "
            "for the request, the length of time for which it is requested, "
            "and any opposition from the opposing party. Matter of Hashmi, "
            "24 I&N Dec. 785 (BIA 2009). Good cause exists where a "
            "continuance is necessary to ensure the respondent has a full "
            "and fair hearing."
        ),
    },
    "Motion to Change Venue": {
        "good_cause_venue": (
            "An Immigration Judge may change venue to another Immigration "
            "Court upon a showing of good cause. 8 C.F.R. \u00a71003.20(b). "
            "Good cause includes, but is not limited to, the respondent's "
            "residence, the location of counsel, witnesses, or evidence, "
            "and the administrative convenience of the parties and the "
            "court. Matter of Rahman, 20 I&N Dec. 480 (BIA 1992)."
        ),
        "administrative_convenience": (
            "Transfer of venue would serve administrative convenience "
            "because the respondent, counsel, and witnesses are located "
            "in the jurisdiction of the receiving court. 8 C.F.R. "
            "\u00a71003.20(b). The BIA has held that venue should generally "
            "lie where the respondent resides. Matter of Rahman, 20 I&N "
            "Dec. 480 (BIA 1992)."
        ),
    },
    "Motion to Suppress": {
        "fourth_amendment": (
            "The Fourth Amendment to the United States Constitution protects "
            "individuals from unreasonable searches and seizures. While the "
            "exclusionary rule does not generally apply in civil immigration "
            "proceedings, INS v. Lopez-Mendoza, 468 U.S. 1032 (1984), the "
            "Supreme Court recognized an exception where evidence is obtained "
            "through egregious violations of the Fourth Amendment."
        ),
        "egregious_violations": (
            "Evidence obtained through egregious violations of the Fourth "
            "Amendment must be suppressed in removal proceedings. INS v. "
            "Lopez-Mendoza, 468 U.S. 1032, 1050-51 (1984). An egregious "
            "violation is one that is fundamentally unfair and undermines "
            "the probative value of the evidence obtained or transgresses "
            "notions of fundamental fairness. The respondent bears the "
            "initial burden of establishing a prima facie case that the "
            "stop or arrest was egregiously unlawful."
        ),
    },
}


# ---------------------------------------------------------------------------
# Merge field definitions
# ---------------------------------------------------------------------------

MERGE_FIELDS: dict[str, str] = {
    "{client_name}": "Full name of the client / respondent",
    "{a_number}": "Alien registration number",
    "{court}": "Immigration court name",
    "{judge}": "Immigration judge name",
    "{date}": "Current date",
    "{hearing_date}": "Next hearing date",
    "{case_type}": "Type of legal case",
    "{attorney_name}": "Attorney full name",
    "{firm_name}": "Law firm name",
}


# ---------------------------------------------------------------------------
# Config read/write
# ---------------------------------------------------------------------------

_CONFIG_KEY = "brief-builder"


def get_brief_types() -> dict[str, list[dict[str, Any]]]:
    """Return brief types from config, falling back to defaults."""
    return get_config_value(_CONFIG_KEY, "brief_types", _DEFAULT_BRIEF_TYPES)


def get_boilerplate() -> dict[str, dict[str, str]]:
    """Return all boilerplate from config, falling back to defaults."""
    return get_config_value(_CONFIG_KEY, "boilerplate", _DEFAULT_BOILERPLATE)


def save_brief_config(
    brief_types: dict[str, list[dict[str, Any]]],
    boilerplate: dict[str, dict[str, str]],
) -> None:
    """Persist brief types and boilerplate to the shared config store."""
    save_config(_CONFIG_KEY, {"brief_types": brief_types, "boilerplate": boilerplate})


# ---------------------------------------------------------------------------
# Merge field resolution
# ---------------------------------------------------------------------------


def resolve_merge_fields(text: str, field_values: dict[str, str]) -> str:
    """Replace ``{placeholder}`` tokens in *text* with values from *field_values*."""
    for placeholder, value in field_values.items():
        if not placeholder.startswith("{"):
            placeholder = "{" + placeholder + "}"
        text = text.replace(placeholder, value)
    return text
