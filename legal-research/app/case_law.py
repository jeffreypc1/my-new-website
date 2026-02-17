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
    resource_type: str = "decision"  # decision, statute, regulation, agency_guidance


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
    # -------------------------------------------------------------------
    # Additional BIA decisions
    # -------------------------------------------------------------------
    "matter-of-c-y-z": CaseLaw(
        name="Matter of C-Y-Z-",
        citation="21 I&N Dec. 915 (BIA 1997)",
        court="BIA",
        date="1997-07-09",
        holding=(
            "Held that a spouse of a person who was forcibly sterilized or forced "
            "to have an abortion under China's coercive family planning policy "
            "is a 'refugee' under INA 101(a)(42). Each spouse is equally affected "
            "by forced sterilization and both qualify as persecuted."
        ),
        topics=["asylum", "persecution", "coercive population control"],
    ),
    "matter-of-j-b-n-and-s-m": CaseLaw(
        name="Matter of J-B-N- & S-M-",
        citation="24 I&N Dec. 208 (BIA 2007)",
        court="BIA",
        date="2007-05-11",
        holding=(
            "Clarified that for past persecution, the applicant must show "
            "(1) an incident or incidents that rise to the level of persecution; "
            "(2) on account of a protected ground; (3) committed by the government "
            "or forces the government is unable or unwilling to control."
        ),
        topics=["asylum", "past persecution", "nexus"],
    ),
    "matter-of-a-r-c-g": CaseLaw(
        name="Matter of A-R-C-G-",
        citation="26 I&N Dec. 388 (BIA 2014)",
        court="BIA",
        date="2014-08-26",
        holding=(
            "Held that 'married women in Guatemala who are unable to leave "
            "their relationship' can constitute a cognizable particular social "
            "group for asylum purposes. First BIA precedent recognizing a "
            "domestic violence-based PSG. Later vacated by Matter of A-B- (2018) "
            "and partially revived after the 2021 vacatur of A-B-."
        ),
        topics=["particular social group", "domestic violence", "gender", "asylum"],
    ),
    "matter-of-d-v": CaseLaw(
        name="Matter of D-V-",
        citation="25 I&N Dec. 131 (BIA 2009)",
        court="BIA",
        date="2009-10-30",
        holding=(
            "Addressed the framework for analyzing claims under the Convention "
            "Against Torture. Held that the applicant must show it is more likely "
            "than not that he would be tortured by or at the acquiescence of a "
            "government official. All evidence of torture must be assessed, "
            "including patterns of violence in the country."
        ),
        topics=["CAT", "torture", "acquiescence"],
    ),
    "matter-of-silva-trevino": CaseLaw(
        name="Matter of Silva-Trevino",
        citation="26 I&N Dec. 826 (BIA 2016)",
        court="BIA",
        date="2016-11-07",
        holding=(
            "Established the categorical approach and modified categorical approach "
            "for determining whether a conviction constitutes a 'crime involving "
            "moral turpitude' (CIMT). Applied the Supreme Court's framework from "
            "Descamps and Mathis to immigration proceedings."
        ),
        topics=["CIMT", "criminal grounds", "categorical approach"],
    ),
    "matter-of-leal": CaseLaw(
        name="Matter of Leal",
        citation="27 I&N Dec. 652 (BIA 2019)",
        court="BIA",
        date="2019-10-18",
        holding=(
            "Held that DUI offenses are categorically crimes involving moral "
            "turpitude (CIMTs) when the statute of conviction requires a mens rea "
            "of at least recklessness. Addressed the persistent circuit split "
            "on whether DUIs constitute CIMTs."
        ),
        topics=["CIMT", "DUI", "criminal grounds", "moral turpitude"],
    ),
    # -------------------------------------------------------------------
    # Federal court decisions
    # -------------------------------------------------------------------
    "perez-funez-v-ins": CaseLaw(
        name="Perez-Funez v. INS",
        citation="619 F.Supp. 656 (C.D. Cal. 1985)",
        court="C.D. California",
        date="1985-08-12",
        holding=(
            "Landmark case addressing due process rights of unaccompanied minors "
            "in immigration proceedings. The court established requirements for "
            "ensuring that minors understand their rights before signing voluntary "
            "departure forms."
        ),
        topics=["due process", "minors", "voluntary departure"],
    ),
    "gonzales-v-thomas": CaseLaw(
        name="Gonzales v. Thomas",
        citation="547 U.S. 183 (2006)",
        court="Supreme Court",
        date="2006-04-17",
        holding=(
            "Per curiam reversal holding that the Ninth Circuit erred in making "
            "its own particular social group determination rather than remanding "
            "to the BIA. Courts must allow the BIA to apply its expertise in "
            "the first instance for PSG determinations."
        ),
        topics=["particular social group", "judicial review", "remand"],
    ),
    "henriquez-rivas-v-holder": CaseLaw(
        name="Henriquez-Rivas v. Holder",
        citation="707 F.3d 1081 (9th Cir. 2013)",
        court="9th Circuit",
        date="2013-02-06",
        holding=(
            "Held that witnesses who testify against gang members in court "
            "proceedings may constitute a particular social group. Found "
            "that the BIA erred in not applying the immutability and social "
            "distinction analysis to the proposed group of Salvadoran witnesses."
        ),
        topics=["particular social group", "witnesses", "gang", "asylum"],
    ),
    "santos-v-lynch": CaseLaw(
        name="Ticas-Santos v. INS",
        citation="487 F.3d 1024 (7th Cir. 2007)",
        court="7th Circuit",
        date="2007-05-22",
        holding=(
            "Addressed asylum claims based on gang-related violence in Central "
            "America. Discussed the nexus requirement and held that generalized "
            "violence and gang threats, while terrible, do not necessarily establish "
            "persecution on account of a protected ground without more."
        ),
        topics=["asylum", "gang", "nexus", "Central America"],
    ),
    "perdomo-v-holder": CaseLaw(
        name="Perdomo v. Holder",
        citation="611 F.3d 662 (9th Cir. 2010)",
        court="9th Circuit",
        date="2010-07-08",
        holding=(
            "Held that 'all women in Guatemala' could potentially constitute "
            "a particular social group. Remanded for the BIA to properly analyze "
            "whether Guatemalan women who are targeted for violence satisfy "
            "the social visibility and particularity requirements."
        ),
        topics=["particular social group", "gender", "Guatemala", "asylum"],
    ),
    "guerrero-lasprilla-v-barr": CaseLaw(
        name="Guerrero-Lasprilla v. Barr",
        citation="589 U.S. 221 (2020)",
        court="Supreme Court",
        date="2020-03-23",
        holding=(
            "Held that federal courts of appeals have jurisdiction to review "
            "mixed questions of law and fact arising in the application of a "
            "legal standard to undisputed facts in removal proceedings. "
            "Broadened judicial review of BIA decisions under INA 242(a)(2)(D)."
        ),
        topics=["judicial review", "mixed questions", "removal"],
    ),
    "nken-v-holder": CaseLaw(
        name="Nken v. Holder",
        citation="556 U.S. 418 (2009)",
        court="Supreme Court",
        date="2009-04-22",
        holding=(
            "Established the standard for stays of removal pending judicial "
            "review. The traditional four-factor test applies: (1) likelihood "
            "of success on the merits, (2) irreparable injury, (3) balance "
            "of hardships, and (4) public interest."
        ),
        topics=["stay of removal", "judicial review", "standard of review"],
    ),
    # -------------------------------------------------------------------
    # INA (Immigration and Nationality Act) Statutory Sections
    # -------------------------------------------------------------------
    "ina-101-a-42": CaseLaw(
        name="INA 101(a)(42) -- Definition of Refugee",
        citation="8 U.S.C. 1101(a)(42)",
        court="Statute",
        date="",
        holding=(
            "Defines 'refugee' as any person who is outside their country of "
            "nationality and is unable or unwilling to return because of "
            "persecution or a well-founded fear of persecution on account of "
            "race, religion, nationality, membership in a particular social "
            "group, or political opinion."
        ),
        topics=["asylum", "refugee definition", "persecution"],
        resource_type="statute",
    ),
    "ina-208": CaseLaw(
        name="INA 208 -- Asylum",
        citation="8 U.S.C. 1158",
        court="Statute",
        date="",
        holding=(
            "Authorizes the granting of asylum to refugees. Establishes the "
            "one-year filing deadline, bars to asylum (persecution of others, "
            "particularly serious crime, firm resettlement, danger to security), "
            "and the burden of proof. Asylum is discretionary even if eligibility "
            "is established."
        ),
        topics=["asylum", "one-year bar", "bars to asylum", "discretion"],
        resource_type="statute",
    ),
    "ina-240a-b": CaseLaw(
        name="INA 240A(b) -- Cancellation of Removal (Non-LPR)",
        citation="8 U.S.C. 1229b(b)",
        court="Statute",
        date="",
        holding=(
            "Provides for cancellation of removal for certain non-permanent "
            "residents who (1) have been physically present for 10+ years, "
            "(2) have good moral character, (3) have not been convicted of "
            "certain offenses, and (4) whose removal would result in exceptional "
            "and extremely unusual hardship to a USC or LPR spouse, parent, "
            "or child."
        ),
        topics=["cancellation of removal", "hardship", "physical presence", "good moral character"],
        resource_type="statute",
    ),
    "ina-241-b-3": CaseLaw(
        name="INA 241(b)(3) -- Withholding of Removal",
        citation="8 U.S.C. 1231(b)(3)",
        court="Statute",
        date="",
        holding=(
            "Mandatory relief: prohibits removal to a country where the alien's "
            "life or freedom would be threatened on account of race, religion, "
            "nationality, membership in a particular social group, or political "
            "opinion. Higher 'clear probability' standard than asylum. No "
            "discretionary denial but subject to criminal bars."
        ),
        topics=["withholding", "persecution", "mandatory relief"],
        resource_type="statute",
    ),
    "ina-212-a": CaseLaw(
        name="INA 212(a) -- Grounds of Inadmissibility",
        citation="8 U.S.C. 1182(a)",
        court="Statute",
        date="",
        holding=(
            "Lists all grounds of inadmissibility including: health-related, "
            "criminal, security, public charge, labor certification, illegal "
            "entrants and immigration violators, documentation requirements, "
            "ineligible for citizenship, and miscellaneous grounds. Many grounds "
            "have waiver provisions."
        ),
        topics=["inadmissibility", "grounds of removal", "waivers"],
        resource_type="statute",
    ),
    "ina-237-a": CaseLaw(
        name="INA 237(a) -- Grounds of Deportability",
        citation="8 U.S.C. 1227(a)",
        court="Statute",
        date="",
        holding=(
            "Lists all grounds of deportability for aliens within the United "
            "States including: inadmissible at entry, criminal offenses, failure "
            "to register, document fraud, security grounds, public charge, "
            "and unlawful voting. Aliens in removal proceedings may be charged "
            "under these provisions."
        ),
        topics=["deportability", "grounds of removal", "criminal grounds"],
        resource_type="statute",
    ),
    "ina-245": CaseLaw(
        name="INA 245 -- Adjustment of Status",
        citation="8 U.S.C. 1255",
        court="Statute",
        date="",
        holding=(
            "Authorizes adjustment of status to permanent residence for aliens "
            "physically present in the U.S. who were inspected and admitted or "
            "paroled, are eligible for an immigrant visa, and whose visa is "
            "immediately available. Section 245(i) provides a limited exception "
            "for those who entered without inspection."
        ),
        topics=["adjustment of status", "green card", "immigrant visa"],
        resource_type="statute",
    ),
    "ina-240-a-a": CaseLaw(
        name="INA 240A(a) -- Cancellation of Removal (LPR)",
        citation="8 U.S.C. 1229b(a)",
        court="Statute",
        date="",
        holding=(
            "Provides for cancellation of removal for lawful permanent residents "
            "who (1) have been LPRs for at least 5 years, (2) have resided "
            "continuously in the U.S. for 7 years after admission, and (3) have "
            "not been convicted of an aggravated felony."
        ),
        topics=["cancellation of removal", "LPR", "aggravated felony"],
        resource_type="statute",
    ),
    # -------------------------------------------------------------------
    # CFR (Code of Federal Regulations) Key Provisions
    # -------------------------------------------------------------------
    "8-cfr-208-13": CaseLaw(
        name="8 CFR 208.13 -- Establishing Asylum Eligibility",
        citation="8 C.F.R. 208.13",
        court="Regulation",
        date="",
        holding=(
            "Implements asylum standards: burden of proof, standard of proof, "
            "well-founded fear analysis, past persecution presumption, "
            "changed country conditions rebuttal, internal relocation analysis, "
            "and discretionary factors. Central regulation for asylum adjudication."
        ),
        topics=["asylum", "burden of proof", "well-founded fear", "internal relocation"],
        resource_type="regulation",
    ),
    "8-cfr-1003-29": CaseLaw(
        name="8 CFR 1003.29 -- Continuances",
        citation="8 C.F.R. 1003.29",
        court="Regulation",
        date="",
        holding=(
            "Governs the grant or denial of continuances in immigration court. "
            "An immigration judge may grant a continuance for good cause shown. "
            "Factors include the DHS response, the length of the delay, "
            "and the number of prior continuances."
        ),
        topics=["continuances", "immigration court", "good cause"],
        resource_type="regulation",
    ),
    "8-cfr-1208-4": CaseLaw(
        name="8 CFR 1208.4 -- Filing the Asylum Application (One-Year Deadline)",
        citation="8 C.F.R. 1208.4",
        court="Regulation",
        date="",
        holding=(
            "Implements the one-year filing deadline for asylum applications. "
            "Must be filed within one year of arrival in the U.S. unless "
            "extraordinary circumstances (changed country conditions, changed "
            "personal circumstances, ineffective assistance of counsel, "
            "legal disability) caused the delay."
        ),
        topics=["asylum", "one-year bar", "extraordinary circumstances", "filing deadline"],
        resource_type="regulation",
    ),
    "8-cfr-1003-47": CaseLaw(
        name="8 CFR 1003.47 -- Identity, Law Enforcement, and Security Checks",
        citation="8 C.F.R. 1003.47",
        court="Regulation",
        date="",
        holding=(
            "Requires completion of identity, law enforcement, and security "
            "checks before any immigration judge may grant relief from removal. "
            "Outlines the specific checks DHS must complete and the procedures "
            "for updating stale checks."
        ),
        topics=["background checks", "security checks", "relief from removal"],
        resource_type="regulation",
    ),
    "8-cfr-208-16": CaseLaw(
        name="8 CFR 208.16 -- Withholding of Removal and CAT",
        citation="8 C.F.R. 208.16",
        court="Regulation",
        date="",
        holding=(
            "Implements withholding of removal under INA 241(b)(3) and "
            "protection under the Convention Against Torture. Sets forth the "
            "clear probability standard for withholding, and the 'more likely "
            "than not' standard for CAT claims, including the definitions of "
            "torture and government acquiescence."
        ),
        topics=["withholding", "CAT", "torture", "acquiescence", "standard of proof"],
        resource_type="regulation",
    ),
}


# ---------------------------------------------------------------------------
# Legal topics for filtering and categorization
# ---------------------------------------------------------------------------

_DEFAULT_LEGAL_TOPICS: list[str] = [
    # Relief types
    "asylum",
    "withholding",
    "CAT",
    "cancellation of removal",
    "adjustment of status",
    "stay of removal",
    # Substantive legal concepts
    "particular social group",
    "nexus",
    "persecution",
    "well-founded fear",
    "credibility",
    "corroboration",
    "firm resettlement",
    "one-year bar",
    "political opinion",
    "internal relocation",
    # Protected grounds and claim types
    "gender",
    "sexual orientation",
    "domestic violence",
    "gang",
    "forced recruitment",
    "family",
    "coercive population control",
    # Removal defense
    "inadmissibility",
    "deportability",
    "grounds of removal",
    "criminal grounds",
    "CIMT",
    "aggravated felony",
    "moral turpitude",
    # Procedural
    "hardship",
    "due process",
    "judicial review",
    "burden of proof",
    "standard of review",
    "continuances",
    "acquiescence",
    # Special populations
    "minors",
    "USC children",
    "LPR",
    # Additional
    "torture",
    "waivers",
    "good moral character",
    "physical presence",
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
                resource_type=v.get("resource_type", "decision"),
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
