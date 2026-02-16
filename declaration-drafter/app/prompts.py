"""Guided prompt definitions and formatting helpers for declaration drafting."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Declaration type constants
# ---------------------------------------------------------------------------

DECLARATION_TYPES: list[str] = [
    "Asylum Declaration",
    "Witness Declaration",
    "Expert Declaration",
    "Personal Statement",
]

# ---------------------------------------------------------------------------
# Guided prompts — keyed by declaration type
#
# Each entry is an ordered list of *sections*.  Every section contains:
#   - "title"       : section heading shown in the UI
#   - "instructions" : brief guidance displayed above the questions
#   - "questions"    : list of dicts with "id" (unique key) and "label" (prompt)
# ---------------------------------------------------------------------------

DECLARATION_PROMPTS: dict[str, list[dict]] = {
    # -----------------------------------------------------------------------
    # Asylum Declaration
    # -----------------------------------------------------------------------
    "Asylum Declaration": [
        {
            "title": "Background",
            "instructions": (
                "Provide basic biographical details about the declarant. "
                "These facts establish who you are and where you come from."
            ),
            "questions": [
                {
                    "id": "background_birth",
                    "label": "Where and when were you born? Describe the city/town and country.",
                },
                {
                    "id": "background_family",
                    "label": "Describe your family background (parents, siblings, spouse, children).",
                },
                {
                    "id": "background_education",
                    "label": "What is your educational background?",
                },
                {
                    "id": "background_occupation",
                    "label": "What is your occupation or work history in your home country?",
                },
                {
                    "id": "background_religion",
                    "label": "What is your religion, ethnicity, or tribal affiliation, if relevant?",
                },
                {
                    "id": "background_political",
                    "label": "Describe any political opinions, party membership, or civic involvement.",
                },
            ],
        },
        {
            "title": "Persecution History",
            "instructions": (
                "Describe each incident of harm or threat you experienced. "
                "Be specific about dates, locations, and the people involved. "
                "Explain WHY you believe you were targeted (nexus to a protected ground)."
            ),
            "questions": [
                {
                    "id": "persecution_first_incident",
                    "label": "What is the first incident of harm or threat you experienced? When and where did it happen?",
                },
                {
                    "id": "persecution_who",
                    "label": "Who harmed or threatened you? (government officials, military, gang members, family, etc.)",
                },
                {
                    "id": "persecution_why",
                    "label": "Why do you believe you were targeted? (race, religion, nationality, political opinion, particular social group)",
                },
                {
                    "id": "persecution_subsequent",
                    "label": "Describe any subsequent incidents of harm, threats, or persecution in chronological order.",
                },
                {
                    "id": "persecution_police",
                    "label": "Did you report any incidents to the police or authorities? What happened?",
                },
                {
                    "id": "persecution_family_harm",
                    "label": "Were any family members harmed or threatened? Describe what happened to them.",
                },
            ],
        },
        {
            "title": "Harm Feared on Return",
            "instructions": (
                "Explain what you believe would happen if you were deported. "
                "Connect your fear to specific, concrete threats."
            ),
            "questions": [
                {
                    "id": "fear_what",
                    "label": "What do you fear would happen to you if you returned to your home country?",
                },
                {
                    "id": "fear_who",
                    "label": "Who do you fear would harm you? Are they still active or in power?",
                },
                {
                    "id": "fear_why_ongoing",
                    "label": "Why do you believe the threat is ongoing? Has anything happened recently to confirm this?",
                },
                {
                    "id": "fear_country_conditions",
                    "label": "Describe the current conditions in your country that support your fear.",
                },
            ],
        },
        {
            "title": "Internal Relocation",
            "instructions": (
                "Explain why you cannot safely relocate to another part of your country. "
                "This addresses whether the persecutor can reach you anywhere in the country."
            ),
            "questions": [
                {
                    "id": "relocation_why_not",
                    "label": "Why can you not safely relocate to another part of your country?",
                },
                {
                    "id": "relocation_persecutor_reach",
                    "label": "Does your persecutor have the ability to find you elsewhere? How do you know?",
                },
                {
                    "id": "relocation_attempted",
                    "label": "Did you attempt to relocate within your country before leaving? What happened?",
                },
            ],
        },
        {
            "title": "Arrival in the United States",
            "instructions": (
                "Describe your journey to the United States and what has happened since you arrived."
            ),
            "questions": [
                {
                    "id": "arrival_when",
                    "label": "When did you leave your home country and when did you arrive in the United States?",
                },
                {
                    "id": "arrival_how",
                    "label": "How did you travel to the United States? Describe your journey.",
                },
                {
                    "id": "arrival_since",
                    "label": "What has happened since you arrived in the United States? (employment, family, community ties)",
                },
                {
                    "id": "arrival_filing",
                    "label": "When did you file your asylum application? If there was a delay, explain why.",
                },
            ],
        },
    ],

    # -----------------------------------------------------------------------
    # Witness Declaration
    # -----------------------------------------------------------------------
    "Witness Declaration": [
        {
            "title": "Witness Background",
            "instructions": "Establish who you are and your relationship to the applicant.",
            "questions": [
                {
                    "id": "witness_identity",
                    "label": "State your full name, date of birth, and immigration status.",
                },
                {
                    "id": "witness_relationship",
                    "label": "How do you know the applicant? How long have you known them?",
                },
            ],
        },
        {
            "title": "Personal Knowledge",
            "instructions": "Describe what you personally witnessed or know about the applicant's situation.",
            "questions": [
                {
                    "id": "witness_observed",
                    "label": "What events did you personally witness or what facts do you have personal knowledge of?",
                },
                {
                    "id": "witness_character",
                    "label": "Describe the applicant's character, credibility, and reputation for truthfulness.",
                },
                {
                    "id": "witness_impact",
                    "label": "Describe any physical or emotional impact you have observed on the applicant.",
                },
            ],
        },
    ],

    # -----------------------------------------------------------------------
    # Expert Declaration
    # -----------------------------------------------------------------------
    "Expert Declaration": [
        {
            "title": "Expert Qualifications",
            "instructions": "Establish your credentials and expertise.",
            "questions": [
                {
                    "id": "expert_name_title",
                    "label": "State your full name, title, and institutional affiliation.",
                },
                {
                    "id": "expert_credentials",
                    "label": "Summarize your education, training, and professional experience relevant to this matter.",
                },
                {
                    "id": "expert_publications",
                    "label": "List any relevant publications, research, or prior expert testimony.",
                },
            ],
        },
        {
            "title": "Expert Opinion",
            "instructions": "Provide your expert analysis relevant to the case.",
            "questions": [
                {
                    "id": "expert_materials_reviewed",
                    "label": "What materials did you review in preparing this declaration?",
                },
                {
                    "id": "expert_country_conditions",
                    "label": "Describe the relevant country conditions, cultural context, or subject-matter analysis.",
                },
                {
                    "id": "expert_opinion",
                    "label": "State your expert opinion and the basis for it.",
                },
            ],
        },
    ],

    # -----------------------------------------------------------------------
    # Personal Statement
    # -----------------------------------------------------------------------
    "Personal Statement": [
        {
            "title": "Personal Background",
            "instructions": "Provide an overview of who you are.",
            "questions": [
                {
                    "id": "personal_identity",
                    "label": "State your full name, date of birth, and country of origin.",
                },
                {
                    "id": "personal_family",
                    "label": "Describe your family and personal circumstances.",
                },
            ],
        },
        {
            "title": "Statement of Facts",
            "instructions": "Describe the facts and circumstances relevant to your case.",
            "questions": [
                {
                    "id": "personal_circumstances",
                    "label": "Describe the circumstances that led you to seek relief.",
                },
                {
                    "id": "personal_hardship",
                    "label": "Describe any hardship you or your family would face if relief is not granted.",
                },
                {
                    "id": "personal_equities",
                    "label": "Describe your ties to the United States (community, employment, family, education).",
                },
            ],
        },
    ],
}


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

PERJURY_CLAUSE: str = (
    "I, {name}, hereby declare, under penalty of perjury, that the foregoing "
    "is true and correct to the best of my knowledge, information, and belief."
)


def format_numbered_paragraphs(answers: dict[str, str], declaration_type: str) -> list[str]:
    """Convert filled answers into a flat list of numbered paragraph texts.

    Skips any question whose answer is empty.  Returns plain strings — the
    caller is responsible for rendering them with paragraph numbers.
    """
    sections = DECLARATION_PROMPTS.get(declaration_type, [])
    paragraphs: list[str] = []
    for section in sections:
        for question in section["questions"]:
            answer = answers.get(question["id"], "").strip()
            if answer:
                paragraphs.append(answer)
    return paragraphs


def build_declaration_text(
    answers: dict[str, str],
    declaration_type: str,
    declarant_name: str,
) -> str:
    """Assemble a complete declaration as plain text with numbered paragraphs.

    Includes a header, numbered body paragraphs, and the penalty-of-perjury
    closing clause.
    """
    # TODO: add declaration header (caption, case number, court)
    paragraphs = format_numbered_paragraphs(answers, declaration_type)

    lines: list[str] = []
    lines.append(f"DECLARATION OF {declarant_name.upper()}")
    lines.append("")
    lines.append(
        f"I, {declarant_name}, hereby declare under penalty of perjury "
        "that the following statements are true and correct:"
    )
    lines.append("")

    for idx, para in enumerate(paragraphs, start=1):
        lines.append(f"{idx}. {para}")
        lines.append("")

    lines.append(PERJURY_CLAUSE.format(name=declarant_name))
    lines.append("")
    lines.append("")
    lines.append(f"____________________________")
    lines.append(f"{declarant_name}")
    lines.append("Date: _______________")

    return "\n".join(lines)
