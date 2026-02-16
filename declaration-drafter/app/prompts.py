"""Guided prompt definitions and formatting helpers for declaration drafting.

Each question includes a 'tip' field with practical attorney guidance that
helps junior attorneys know what to ask and what makes a strong answer.
"""

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
#   - "title"        : section heading shown in the UI
#   - "instructions"  : brief guidance displayed above the questions
#   - "questions"     : list of dicts with "id", "label", and "tip"
# ---------------------------------------------------------------------------

DECLARATION_PROMPTS: dict[str, list[dict]] = {
    # -----------------------------------------------------------------------
    # Asylum Declaration (I-589 Supplement)
    # -----------------------------------------------------------------------
    "Asylum Declaration": [
        {
            "title": "Background",
            "instructions": (
                "Provide basic biographical details about the declarant. "
                "These facts establish identity, nationality, and personal "
                "context for the claim."
            ),
            "questions": [
                {
                    "id": "background_birth",
                    "label": "Where and when were you born? Describe the city/town and country.",
                    "tip": (
                        "Include the exact date of birth and the full name of "
                        "your city or town, region/province, and country. This "
                        "establishes identity and nationality. Example: 'I was "
                        "born on March 12, 1990, in San Pedro Sula, Cortés, "
                        "Honduras.'"
                    ),
                },
                {
                    "id": "background_family",
                    "label": "Describe your family background (parents, siblings, spouse, children).",
                    "tip": (
                        "Include names, ages, and current locations of immediate "
                        "family members. If family members remain in the home "
                        "country, describe their current situation — this can "
                        "corroborate ongoing danger. Mention any family members "
                        "who were also targeted."
                    ),
                },
                {
                    "id": "background_education",
                    "label": "What is your educational background?",
                    "tip": (
                        "State the highest level of education completed and "
                        "where you studied. Education can be relevant to "
                        "particular social group claims (e.g., educated women "
                        "in certain societies) or can establish credibility."
                    ),
                },
                {
                    "id": "background_occupation",
                    "label": "What is your occupation or work history in your home country?",
                    "tip": (
                        "Describe your work in your home country. If your "
                        "occupation is connected to your persecution (e.g., "
                        "journalist, union organizer, human rights worker, "
                        "business owner targeted for extortion), emphasize "
                        "that connection."
                    ),
                },
                {
                    "id": "background_religion",
                    "label": "What is your religion, ethnicity, or tribal affiliation, if relevant?",
                    "tip": (
                        "Only include if relevant to the claim. If religion, "
                        "ethnicity, or tribal identity is a basis for "
                        "persecution, describe it in detail — how you practice, "
                        "how you are identified by others, and why it makes you "
                        "a target."
                    ),
                },
                {
                    "id": "background_political",
                    "label": "Describe any political opinions, party membership, or civic involvement.",
                    "tip": (
                        "Political opinion claims require showing you hold — or "
                        "are perceived to hold — a political opinion. Include "
                        "party membership, activism, protests, social media "
                        "posts, or even refusal to cooperate with armed groups "
                        "(imputed political opinion)."
                    ),
                },
            ],
        },
        {
            "title": "Persecution History",
            "instructions": (
                "Describe each incident of harm or threat you experienced. "
                "Be specific about dates, locations, and the people involved. "
                "Explain WHY you believe you were targeted — this is the "
                "'nexus' to a protected ground, which is the most critical "
                "legal element."
            ),
            "questions": [
                {
                    "id": "persecution_first_incident",
                    "label": "What is the first incident of harm or threat you experienced? When and where did it happen?",
                    "tip": (
                        "Start with the earliest relevant event. Be specific "
                        "about dates, even if approximate ('around March 2019'). "
                        "Include sensory details — what you saw, heard, and "
                        "felt physically. Describe what happened step by step. "
                        "Example: 'On or around March 15, 2019, three men in "
                        "civilian clothes came to my home in [city]. They "
                        "forced open the door and...'"
                    ),
                },
                {
                    "id": "persecution_who",
                    "label": "Who harmed or threatened you? (government officials, military, gang members, family, etc.)",
                    "tip": (
                        "Be as specific as possible. 'Officers from the local "
                        "police station in [city]' is stronger than 'the "
                        "police.' Identify by name if known. If it was a gang, "
                        "name the gang (MS-13, Barrio 18, etc.). If it was "
                        "the government, identify the branch or unit."
                    ),
                },
                {
                    "id": "persecution_why",
                    "label": "Why do you believe you were targeted? (race, religion, nationality, political opinion, particular social group)",
                    "tip": (
                        "THIS IS THE MOST IMPORTANT QUESTION. The connection "
                        "between the harm and a protected ground is called "
                        "'nexus.' Did the persecutor say anything that reveals "
                        "their motive? ('We're doing this because you are "
                        "[identity/group]'). Even without explicit statements, "
                        "explain the logical connection — why someone like you "
                        "is targeted in your country."
                    ),
                },
                {
                    "id": "persecution_subsequent",
                    "label": "Describe any subsequent incidents of harm, threats, or persecution in chronological order.",
                    "tip": (
                        "List every significant incident in chronological "
                        "order. For each one include: approximate date, "
                        "location, who was involved, what happened, and how "
                        "it connects to the first incident. Showing a pattern "
                        "of escalating persecution strengthens the claim."
                    ),
                },
                {
                    "id": "persecution_police",
                    "label": "Did you report any incidents to the police or authorities? What happened?",
                    "tip": (
                        "Both reporting and not reporting help the case. If "
                        "you reported: describe what happened (were you "
                        "ignored? threatened? told to leave?). This shows the "
                        "government cannot or will not protect you. If you did "
                        "not report: explain why — fear of retaliation, "
                        "corruption, the persecutor IS the government, or "
                        "police are known to be ineffective."
                    ),
                },
                {
                    "id": "persecution_family_harm",
                    "label": "Were any family members harmed or threatened? Describe what happened to them.",
                    "tip": (
                        "Harm to family members corroborates your claim and "
                        "shows a pattern of persecution targeting your family "
                        "unit. Include dates and details. If a family member "
                        "was killed, provide the circumstances. If they were "
                        "threatened, describe the threats and what they were "
                        "told."
                    ),
                },
            ],
        },
        {
            "title": "Harm Feared on Return",
            "instructions": (
                "Explain what you believe would happen if you were deported. "
                "Connect your fear to specific, concrete threats — not "
                "general country conditions alone."
            ),
            "questions": [
                {
                    "id": "fear_what",
                    "label": "What do you fear would happen to you if you returned to your home country?",
                    "tip": (
                        "Be specific. 'I fear I will be killed' is less "
                        "compelling than 'I fear [specific person/group] will "
                        "find me and [specific harm] because [specific "
                        "reason].' Describe what you believe would actually "
                        "happen based on past experience and current "
                        "information."
                    ),
                },
                {
                    "id": "fear_who",
                    "label": "Who do you fear would harm you? Are they still active or in power?",
                    "tip": (
                        "Name the specific person, group, or entity. Explain "
                        "how you know they are still active or in power. Have "
                        "they contacted you or your family since you left? "
                        "Have they harmed others in similar situations? Are "
                        "they still in their position of authority?"
                    ),
                },
                {
                    "id": "fear_why_ongoing",
                    "label": "Why do you believe the threat is ongoing? Has anything happened recently to confirm this?",
                    "tip": (
                        "Explain what has changed (or not changed) since you "
                        "left. Have friends or family told you the persecutors "
                        "came looking for you? Have similar people been "
                        "targeted recently? Has the political or security "
                        "situation improved or worsened?"
                    ),
                },
                {
                    "id": "fear_country_conditions",
                    "label": "Describe the current conditions in your country that support your fear.",
                    "tip": (
                        "Reference current conditions from reliable sources. "
                        "The Country Reports tool can help identify relevant "
                        "source material. Mention government reports (State "
                        "Department, UNHCR), news articles, or expert analyses "
                        "that document the type of persecution you fear."
                    ),
                },
            ],
        },
        {
            "title": "Internal Relocation",
            "instructions": (
                "Explain why you cannot safely relocate to another part of "
                "your country. This addresses whether the persecutor can "
                "reach you anywhere, or whether the same danger exists "
                "nationwide."
            ),
            "questions": [
                {
                    "id": "relocation_why_not",
                    "label": "Why can you not safely relocate to another part of your country?",
                    "tip": (
                        "Explain why moving to another city or region would "
                        "not keep you safe. Consider: is the persecutor part "
                        "of the national government? Do they have a nationwide "
                        "network? Is the type of persecution you face present "
                        "throughout the country (e.g., systemic discrimination)?"
                    ),
                },
                {
                    "id": "relocation_persecutor_reach",
                    "label": "Does your persecutor have the ability to find you elsewhere? How do you know?",
                    "tip": (
                        "Explain the persecutor's power, connections, and "
                        "resources. Government actors often have nationwide "
                        "reach. Gangs and cartels may operate across regions. "
                        "Some persecutors have tracked victims who relocated. "
                        "If you know of specific examples, describe them."
                    ),
                },
                {
                    "id": "relocation_attempted",
                    "label": "Did you attempt to relocate within your country before leaving? What happened?",
                    "tip": (
                        "If you tried to relocate, describe what happened — "
                        "were you found? Did the same problems exist? If you "
                        "did not try, explain why it was not feasible based on "
                        "the persecutor's reach, your knowledge of conditions "
                        "elsewhere, or advice from others."
                    ),
                },
            ],
        },
        {
            "title": "Arrival in the United States",
            "instructions": (
                "Describe your journey to the United States, your life since "
                "arriving, and the timing of your asylum application."
            ),
            "questions": [
                {
                    "id": "arrival_when",
                    "label": "When did you leave your home country and when did you arrive in the United States?",
                    "tip": (
                        "Include exact dates if possible. If you fled on a "
                        "specific date, state it. If approximate, say 'on or "
                        "around [date].' The date of arrival is critical for "
                        "the one-year filing deadline."
                    ),
                },
                {
                    "id": "arrival_how",
                    "label": "How did you travel to the United States? Describe your journey.",
                    "tip": (
                        "Describe your route — which countries you passed "
                        "through, how you traveled, and how long the journey "
                        "took. If you passed through a country where you "
                        "could have sought protection, explain why you did not "
                        "stay (firm resettlement is a bar to asylum)."
                    ),
                },
                {
                    "id": "arrival_since",
                    "label": "What has happened since you arrived? (employment, family, community ties)",
                    "tip": (
                        "Describe your life in the US — employment, education, "
                        "community involvement, church membership, volunteer "
                        "work. These 'equities' show ties to the community "
                        "and support a favorable exercise of discretion."
                    ),
                },
                {
                    "id": "arrival_filing",
                    "label": "When did you file your asylum application? If there was a delay, explain why.",
                    "tip": (
                        "The one-year filing deadline is critical. If you "
                        "filed within one year of arrival, simply state the "
                        "dates. If there was a delay, you MUST explain why — "
                        "changed circumstances, extraordinary circumstances "
                        "(serious illness, mental health, bad legal advice, "
                        "being a minor), or material changes in conditions."
                    ),
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
            "instructions": (
                "Establish who you are and your relationship to the applicant. "
                "The judge needs to understand why your testimony is relevant."
            ),
            "questions": [
                {
                    "id": "witness_identity",
                    "label": "State your full name, date of birth, and immigration status.",
                    "tip": (
                        "Include your current immigration status (US citizen, "
                        "LPR, visa holder, etc.) as it establishes your "
                        "credibility and availability to testify."
                    ),
                },
                {
                    "id": "witness_relationship",
                    "label": "How do you know the applicant? How long have you known them?",
                    "tip": (
                        "Explain the nature and duration of your relationship. "
                        "'I have known [name] since 2015 when we worked "
                        "together at...' is stronger than 'I know them.' "
                        "Explain how often you interact."
                    ),
                },
            ],
        },
        {
            "title": "Personal Knowledge",
            "instructions": (
                "Describe what you personally witnessed or know about the "
                "applicant's situation. Only include facts you have direct "
                "knowledge of — not hearsay."
            ),
            "questions": [
                {
                    "id": "witness_observed",
                    "label": "What events did you personally witness or what facts do you have personal knowledge of?",
                    "tip": (
                        "Focus on what you personally saw, heard, or "
                        "experienced. 'I was present when [name] received a "
                        "threatening phone call' is direct evidence. Avoid "
                        "stating things you only heard about from others."
                    ),
                },
                {
                    "id": "witness_character",
                    "label": "Describe the applicant's character, credibility, and reputation for truthfulness.",
                    "tip": (
                        "Character testimony supports the applicant's "
                        "credibility. Describe specific examples of their "
                        "honesty, reliability, and good character rather "
                        "than general statements."
                    ),
                },
                {
                    "id": "witness_impact",
                    "label": "Describe any physical or emotional impact you have observed on the applicant.",
                    "tip": (
                        "If you have observed signs of trauma (anxiety, "
                        "nightmares, fear, physical scars), describe them. "
                        "'I have noticed that [name] becomes visibly "
                        "distressed when discussing...' These observations "
                        "corroborate the applicant's account."
                    ),
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
            "instructions": (
                "Establish your credentials and expertise. The court must "
                "be satisfied that you are qualified to offer expert opinions."
            ),
            "questions": [
                {
                    "id": "expert_name_title",
                    "label": "State your full name, title, and institutional affiliation.",
                    "tip": (
                        "Include your professional title, academic position, "
                        "and the institution you are affiliated with. This "
                        "establishes your authority on the subject matter."
                    ),
                },
                {
                    "id": "expert_credentials",
                    "label": "Summarize your education, training, and professional experience relevant to this matter.",
                    "tip": (
                        "Focus on credentials directly relevant to the case. "
                        "A country conditions expert should emphasize research "
                        "on the specific country. A medical expert should "
                        "emphasize experience with trauma or the specific "
                        "condition at issue."
                    ),
                },
                {
                    "id": "expert_publications",
                    "label": "List any relevant publications, research, or prior expert testimony.",
                    "tip": (
                        "Include publications, presentations, or prior "
                        "testimony in immigration proceedings. The number "
                        "of times you have been qualified as an expert is "
                        "relevant. List specific courts if applicable."
                    ),
                },
            ],
        },
        {
            "title": "Expert Opinion",
            "instructions": (
                "Provide your expert analysis relevant to the case. Base "
                "your opinions on the materials reviewed and your expertise."
            ),
            "questions": [
                {
                    "id": "expert_materials_reviewed",
                    "label": "What materials did you review in preparing this declaration?",
                    "tip": (
                        "List all materials reviewed: the applicant's "
                        "declaration, country condition reports, medical "
                        "records, news articles, government reports, etc. "
                        "This establishes the foundation for your opinions."
                    ),
                },
                {
                    "id": "expert_country_conditions",
                    "label": "Describe the relevant country conditions, cultural context, or subject-matter analysis.",
                    "tip": (
                        "Provide detailed analysis that a generalist judge "
                        "would not know. Explain cultural norms, political "
                        "dynamics, or medical conditions that are relevant "
                        "to understanding the applicant's situation."
                    ),
                },
                {
                    "id": "expert_opinion",
                    "label": "State your expert opinion and the basis for it.",
                    "tip": (
                        "State your conclusions clearly: 'Based on my review "
                        "of [materials] and my expertise in [field], it is "
                        "my professional opinion that...' Each opinion should "
                        "be supported by specific facts and reasoning."
                    ),
                },
            ],
        },
    ],

    # -----------------------------------------------------------------------
    # Personal Statement (VAWA, U-Visa, Cancellation, etc.)
    # -----------------------------------------------------------------------
    "Personal Statement": [
        {
            "title": "Personal Background",
            "instructions": (
                "Provide an overview of who you are and your personal "
                "circumstances."
            ),
            "questions": [
                {
                    "id": "personal_identity",
                    "label": "State your full name, date of birth, and country of origin.",
                    "tip": (
                        "Use your full legal name as it appears on your "
                        "immigration documents. Include any other names "
                        "you have used."
                    ),
                },
                {
                    "id": "personal_family",
                    "label": "Describe your family and personal circumstances.",
                    "tip": (
                        "Include your spouse/partner, children, parents, "
                        "and any other dependents. Mention the immigration "
                        "status of family members in the US, especially "
                        "US citizen or LPR relatives."
                    ),
                },
            ],
        },
        {
            "title": "Statement of Facts",
            "instructions": (
                "Describe the facts and circumstances relevant to your case. "
                "Be specific about dates, events, and their impact on you."
            ),
            "questions": [
                {
                    "id": "personal_circumstances",
                    "label": "Describe the circumstances that led you to seek relief.",
                    "tip": (
                        "Be specific about what happened and when. For VAWA: "
                        "describe the abuse (physical, emotional, financial, "
                        "sexual). For cancellation: describe your continuous "
                        "presence in the US. For U-Visa: describe the crime "
                        "you suffered and your cooperation with law "
                        "enforcement."
                    ),
                },
                {
                    "id": "personal_hardship",
                    "label": "Describe any hardship you or your family would face if relief is not granted.",
                    "tip": (
                        "Focus on concrete, specific hardships — not just "
                        "'it would be hard.' Consider: medical needs that "
                        "cannot be met abroad, children's education and "
                        "stability, safety concerns, financial devastation, "
                        "separation from US citizen family members."
                    ),
                },
                {
                    "id": "personal_equities",
                    "label": "Describe your ties to the United States (community, employment, family, education).",
                    "tip": (
                        "These are your 'equities' — reasons you deserve to "
                        "stay. Include: length of time in the US, US citizen "
                        "or LPR family members, employment history, tax "
                        "payments, community involvement, property ownership, "
                        "education, and any other positive contributions."
                    ),
                },
            ],
        },
    ],
}


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PERJURY_CLAUSE: str = (
    "I, {name}, hereby declare, under penalty of perjury, that the foregoing "
    "is true and correct to the best of my knowledge, information, and belief."
)

INTERPRETER_CERT: str = (
    "I, {interpreter_name}, am competent to interpret in {language} and "
    "English. I certify that I read the foregoing declaration to "
    "{declarant_name} in {language}, and {declarant_name} stated that "
    "{declarant_name} understood the contents and that the declaration is "
    "true and correct. I certify that the interpretation was true and "
    "accurate to the best of my abilities."
)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def format_numbered_paragraphs(
    answers: dict[str, str], declaration_type: str
) -> list[str]:
    """Convert filled answers into a flat list of paragraph texts.

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
    language: str = "English",
    interpreter_name: str = "",
) -> str:
    """Assemble a complete declaration as plain text with numbered paragraphs."""
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
    lines.append("____________________________")
    lines.append(declarant_name)
    lines.append("Date: _______________")

    if language != "English" and interpreter_name:
        lines.append("")
        lines.append("")
        lines.append("INTERPRETER CERTIFICATION")
        lines.append("")
        lines.append(
            INTERPRETER_CERT.format(
                interpreter_name=interpreter_name,
                language=language,
                declarant_name=declarant_name,
            )
        )
        lines.append("")
        lines.append("")
        lines.append("____________________________")
        lines.append(interpreter_name)
        lines.append("Date: _______________")

    return "\n".join(lines)
