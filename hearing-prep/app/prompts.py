"""Question banks and Claude system prompt for Hearing Prep.

Each case type has ordered sections with questions and coaching tips,
following the same pattern as declaration-drafter/app/prompts.py.
Config-aware via shared.config_store.get_config_value().
"""

from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path

_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent.parent))
from shared.config_store import get_config_value

# ---------------------------------------------------------------------------
# Case type constants
# ---------------------------------------------------------------------------

_DEFAULT_CASE_TYPES: list[str] = [
    "Asylum / Withholding / CAT",
    "Cancellation of Removal (Non-LPR)",
    "Cancellation of Removal (LPR)",
    "Adjustment of Status (Defensive)",
    "Bond / Custody Redetermination",
]

# ---------------------------------------------------------------------------
# Question banks — keyed by case type
#
# Each entry is an ordered list of sections. Every section contains:
#   - "title"        : section heading shown in the UI
#   - "instructions"  : brief guidance for the attorney/client
#   - "questions"     : list of dicts with "id", "label", and "tip"
# ---------------------------------------------------------------------------

_DEFAULT_QUESTION_BANKS: dict[str, list[dict]] = {
    # -------------------------------------------------------------------
    # Asylum / Withholding / CAT
    # -------------------------------------------------------------------
    "Asylum / Withholding / CAT": [
        {
            "title": "Identity & Background",
            "instructions": (
                "These questions establish who the respondent is. ICE will "
                "probe for inconsistencies between testimony and the I-589. "
                "Answers should match the application exactly."
            ),
            "questions": [
                {
                    "id": "asylum_full_name",
                    "label": "State your full legal name for the record.",
                    "tip": (
                        "Must match the I-589 exactly. If the client uses "
                        "nicknames or has name variations, practice saying the "
                        "full legal name naturally."
                    ),
                },
                {
                    "id": "asylum_dob_nationality",
                    "label": "What is your date of birth and nationality?",
                    "tip": (
                        "ICE may ask this rapidly to test recall. The client "
                        "should answer without hesitation. Confirm the date "
                        "format matches what's on the I-589."
                    ),
                },
                {
                    "id": "asylum_entry",
                    "label": "When and how did you enter the United States?",
                    "tip": (
                        "ICE will compare this to CBP records. Include the "
                        "exact date of entry, port of entry, and manner of "
                        "entry. If the client entered without inspection, "
                        "practice answering honestly without elaborating "
                        "beyond what's asked."
                    ),
                },
                {
                    "id": "asylum_filing_date",
                    "label": "When did you file your asylum application?",
                    "tip": (
                        "Critical for the one-year bar. If filed late, the "
                        "client must be ready to explain changed or "
                        "extraordinary circumstances. Practice the exact "
                        "dates and the reason for any delay."
                    ),
                },
            ],
        },
        {
            "title": "Basis of Claim",
            "instructions": (
                "ICE will challenge the core of the claim. The respondent "
                "must clearly articulate what happened, who did it, and "
                "why — connecting harm to a protected ground."
            ),
            "questions": [
                {
                    "id": "asylum_why_fear",
                    "label": "Why are you afraid to return to your country?",
                    "tip": (
                        "This is the central question. The answer should be "
                        "concise but specific: who persecuted you, what they "
                        "did, and why (the nexus to a protected ground). "
                        "Practice a 2-3 sentence summary before going into "
                        "detail."
                    ),
                },
                {
                    "id": "asylum_persecutor",
                    "label": "Who specifically harmed or threatened you?",
                    "tip": (
                        "ICE wants specifics. 'The government' is too vague. "
                        "Practice naming the specific person, group, or "
                        "entity. If it's a non-state actor, be ready to "
                        "explain why the government can't or won't protect."
                    ),
                },
                {
                    "id": "asylum_incidents",
                    "label": "Describe the most serious incident of harm you experienced.",
                    "tip": (
                        "ICE will probe for sensory details: What did you "
                        "see? What did they say? What time of day? Who else "
                        "was present? Practice including these details "
                        "naturally without sounding rehearsed."
                    ),
                },
                {
                    "id": "asylum_nexus",
                    "label": "Why do you believe you were targeted? What protected ground applies?",
                    "tip": (
                        "The weakest point in many cases. The client should "
                        "connect the harm to race, religion, nationality, "
                        "political opinion, or particular social group. "
                        "Practice: 'I was targeted BECAUSE OF my [ground].'"
                    ),
                },
            ],
        },
        {
            "title": "Credibility Challenges",
            "instructions": (
                "ICE will look for inconsistencies between the declaration, "
                "I-589, country conditions evidence, and live testimony. "
                "Practice handling discrepancies honestly."
            ),
            "questions": [
                {
                    "id": "asylum_inconsistency",
                    "label": "Your declaration says X happened in March, but your I-589 says April. Which is correct?",
                    "tip": (
                        "Practice acknowledging the discrepancy without "
                        "getting defensive. Good answer pattern: 'The correct "
                        "date is [X]. When I filled out the I-589, I was "
                        "nervous/confused about the exact month, but as I "
                        "stated in my declaration, it was [X].' Never say "
                        "'I don't know which is right.'"
                    ),
                },
                {
                    "id": "asylum_no_report",
                    "label": "Did you report any of these incidents to the police? Why not?",
                    "tip": (
                        "Common ICE attack. If the client didn't report, "
                        "they should explain why: the persecutor IS the "
                        "police, police are corrupt, fear of retaliation, "
                        "others who reported were harmed. If they did report, "
                        "explain what happened (nothing, or it made things "
                        "worse)."
                    ),
                },
                {
                    "id": "asylum_no_evidence",
                    "label": "Do you have any documents or evidence to prove this happened?",
                    "tip": (
                        "If no corroborating evidence exists, practice "
                        "explaining why: had to flee quickly, evidence was "
                        "destroyed, government records aren't reliable. "
                        "Remind the client that testimony alone can be "
                        "sufficient if credible."
                    ),
                },
                {
                    "id": "asylum_delay",
                    "label": "If things were so bad, why didn't you leave sooner?",
                    "tip": (
                        "ICE uses this to undermine the severity of the "
                        "claim. Practice explaining: lack of resources, hope "
                        "things would improve, family obligations, didn't "
                        "know asylum was an option, escalation that finally "
                        "made leaving necessary."
                    ),
                },
            ],
        },
        {
            "title": "Relocation & Country Conditions",
            "instructions": (
                "ICE will argue the respondent could have relocated within "
                "their country. Be prepared to explain why internal "
                "relocation is not safe or reasonable."
            ),
            "questions": [
                {
                    "id": "asylum_relocate",
                    "label": "Could you have moved to another part of your country instead of coming here?",
                    "tip": (
                        "Practice explaining the persecutor's reach: "
                        "nationwide government apparatus, gang networks "
                        "across regions, small country where everyone knows "
                        "everyone. If the client tried relocating, describe "
                        "what happened."
                    ),
                },
                {
                    "id": "asylum_country_change",
                    "label": "Have conditions in your country changed since you left?",
                    "tip": (
                        "ICE may argue conditions have improved. The client "
                        "should acknowledge any changes honestly but explain "
                        "why the personal threat persists. Reference specific "
                        "recent reports or events."
                    ),
                },
                {
                    "id": "asylum_return_fear",
                    "label": "What specifically would happen to you if you were deported tomorrow?",
                    "tip": (
                        "Make the fear concrete and personal, not abstract. "
                        "'I would be killed' is less effective than 'The "
                        "[specific group] knows I left and they have "
                        "threatened my [family member] since I've been "
                        "gone. My [relative] was [harmed] last [month].'"
                    ),
                },
            ],
        },
        {
            "title": "Bars to Relief",
            "instructions": (
                "ICE will probe for statutory bars: firm resettlement, "
                "criminal history, persecutor bar, material support. "
                "Prepare for direct questioning on these topics."
            ),
            "questions": [
                {
                    "id": "asylum_third_country",
                    "label": "Did you live in or travel through any other country before coming to the US?",
                    "tip": (
                        "Firm resettlement bar. If the client passed through "
                        "Mexico or another country, practice explaining why "
                        "they did not stay: no legal status offered, safety "
                        "concerns, no meaningful ties, transit only."
                    ),
                },
                {
                    "id": "asylum_criminal",
                    "label": "Have you ever been arrested, charged, or convicted of any crime in any country?",
                    "tip": (
                        "Including traffic offenses, dismissed charges, and "
                        "juvenile matters. The client must disclose everything "
                        "— ICE will have the criminal history. Practice "
                        "answering honestly and briefly without volunteering "
                        "extra information."
                    ),
                },
            ],
        },
    ],

    # -------------------------------------------------------------------
    # Cancellation of Removal (Non-LPR)
    # -------------------------------------------------------------------
    "Cancellation of Removal (Non-LPR)": [
        {
            "title": "Physical Presence",
            "instructions": (
                "ICE will challenge the 10-year continuous physical presence "
                "requirement. Prepare to prove presence with specific dates "
                "and corroborating evidence."
            ),
            "questions": [
                {
                    "id": "cancel_nlpr_entry",
                    "label": "When did you first enter the United States?",
                    "tip": (
                        "The 10-year clock starts from the date of entry. "
                        "If there were multiple entries, identify the last "
                        "entry and continuous presence since then."
                    ),
                },
                {
                    "id": "cancel_nlpr_continuous",
                    "label": "Have you left the United States at any time since you entered?",
                    "tip": (
                        "Any departure can break continuous presence. If "
                        "the client left briefly, know the exact dates and "
                        "duration. Departures under 90 days may not break "
                        "continuity, but over 90 days is presumed to break it."
                    ),
                },
                {
                    "id": "cancel_nlpr_prove_presence",
                    "label": "How can you prove you have been in the US for 10 years?",
                    "tip": (
                        "Practice listing evidence: tax returns, lease "
                        "agreements, utility bills, school records, medical "
                        "records, employer letters, church membership, "
                        "children's birth certificates. Year by year if "
                        "possible."
                    ),
                },
            ],
        },
        {
            "title": "Good Moral Character",
            "instructions": (
                "ICE will scrutinize the 10-year GMC period for any criminal "
                "history, immigration fraud, or conduct reflecting poor "
                "moral character."
            ),
            "questions": [
                {
                    "id": "cancel_nlpr_criminal",
                    "label": "Have you ever been arrested, cited, or had any contact with law enforcement?",
                    "tip": (
                        "Must disclose everything including DUIs, traffic "
                        "tickets, dismissed charges, and incidents where no "
                        "charges were filed. Practice honest, brief answers."
                    ),
                },
                {
                    "id": "cancel_nlpr_taxes",
                    "label": "Have you filed tax returns for every year you have been in the US?",
                    "tip": (
                        "Tax compliance is critical for GMC. If the client "
                        "didn't file some years, they should file amended "
                        "returns before the hearing. Practice explaining any "
                        "gaps honestly."
                    ),
                },
                {
                    "id": "cancel_nlpr_false_claims",
                    "label": "Have you ever used a false Social Security number or made any false claims to US citizenship?",
                    "tip": (
                        "False claim to citizenship is a permanent bar. "
                        "Using a false SSN for employment is common but "
                        "must be addressed carefully. Practice acknowledging "
                        "it without minimizing."
                    ),
                },
            ],
        },
        {
            "title": "Exceptional & Extremely Unusual Hardship",
            "instructions": (
                "This is the hardest element to prove. Hardship must be to "
                "a qualifying relative (USC or LPR spouse, parent, or "
                "child), not to the respondent."
            ),
            "questions": [
                {
                    "id": "cancel_nlpr_qualifying",
                    "label": "Who are your qualifying relatives? What is their immigration status?",
                    "tip": (
                        "Must identify USC or LPR spouse, parent, or child. "
                        "Practice stating each relative's full name, "
                        "relationship, and status clearly."
                    ),
                },
                {
                    "id": "cancel_nlpr_hardship_detail",
                    "label": "What hardship would your qualifying relatives suffer if you were removed?",
                    "tip": (
                        "Must rise above 'normal' hardship of separation. "
                        "Practice specific examples: child's medical needs "
                        "that can't be met abroad, severe emotional impact "
                        "documented by a therapist, financial devastation, "
                        "educational disruption, safety concerns in the "
                        "home country."
                    ),
                },
                {
                    "id": "cancel_nlpr_hardship_country",
                    "label": "What would happen to your family if they had to relocate to your country with you?",
                    "tip": (
                        "Address both scenarios: family stays in US without "
                        "the respondent, or family goes to the home country. "
                        "For children born in the US: language barriers, "
                        "lack of educational opportunities, safety concerns, "
                        "medical care limitations."
                    ),
                },
            ],
        },
        {
            "title": "Discretion & Equities",
            "instructions": (
                "Even if all statutory requirements are met, the judge "
                "exercises discretion. ICE will challenge the respondent's "
                "positive equities."
            ),
            "questions": [
                {
                    "id": "cancel_nlpr_community",
                    "label": "Describe your ties to your community.",
                    "tip": (
                        "Employment history, church involvement, volunteer "
                        "work, children's schools, property ownership. "
                        "Practice listing these without rambling — concrete "
                        "facts, not feelings."
                    ),
                },
                {
                    "id": "cancel_nlpr_employment",
                    "label": "Where do you work and how long have you worked there?",
                    "tip": (
                        "Be prepared for ICE to ask about work authorization. "
                        "If working without authorization, don't lie. "
                        "Practice: 'I have been working to support my family. "
                        "I understand I did not have work authorization.'"
                    ),
                },
                {
                    "id": "cancel_nlpr_why_deserve",
                    "label": "Why should the judge grant you cancellation of removal?",
                    "tip": (
                        "Practice a concise closing statement that ties "
                        "everything together: length of presence, good "
                        "character, hardship to qualifying relatives, "
                        "community contributions."
                    ),
                },
            ],
        },
    ],

    # -------------------------------------------------------------------
    # Cancellation of Removal (LPR)
    # -------------------------------------------------------------------
    "Cancellation of Removal (LPR)": [
        {
            "title": "Statutory Eligibility",
            "instructions": (
                "LPR cancellation requires 5 years of LPR status, 7 years "
                "of continuous residence, and no aggravated felony. ICE "
                "will challenge each element."
            ),
            "questions": [
                {
                    "id": "cancel_lpr_status",
                    "label": "When did you become a lawful permanent resident?",
                    "tip": (
                        "Need 5 years of LPR status. Practice stating the "
                        "exact date and basis for obtaining the green card."
                    ),
                },
                {
                    "id": "cancel_lpr_residence",
                    "label": "Have you continuously resided in the US for at least 7 years?",
                    "tip": (
                        "The 7-year clock stops when a Notice to Appear is "
                        "served or certain offenses are committed ('stop-time "
                        "rule'). Know the exact dates."
                    ),
                },
                {
                    "id": "cancel_lpr_conviction",
                    "label": "Describe the conviction that placed you in removal proceedings.",
                    "tip": (
                        "The client must know the exact charge, statute, "
                        "date of conviction, and sentence imposed. Practice "
                        "stating these facts calmly without making excuses."
                    ),
                },
                {
                    "id": "cancel_lpr_other_convictions",
                    "label": "Do you have any other criminal convictions or arrests?",
                    "tip": (
                        "Full disclosure is essential. ICE will have the "
                        "complete record. Practice listing each incident "
                        "with date, charge, and outcome."
                    ),
                },
            ],
        },
        {
            "title": "Rehabilitation & Remorse",
            "instructions": (
                "The judge needs to see genuine rehabilitation. ICE will "
                "test whether the respondent truly takes responsibility."
            ),
            "questions": [
                {
                    "id": "cancel_lpr_responsibility",
                    "label": "Do you take responsibility for what happened? Tell me about it.",
                    "tip": (
                        "This is critical. The client must express genuine "
                        "remorse without making excuses. Practice: 'I take "
                        "full responsibility for my actions. What I did was "
                        "wrong and I deeply regret it.' Then describe steps "
                        "taken toward rehabilitation."
                    ),
                },
                {
                    "id": "cancel_lpr_rehabilitation",
                    "label": "What steps have you taken to rehabilitate yourself?",
                    "tip": (
                        "Programs completed, counseling, substance abuse "
                        "treatment, community service, employment stability, "
                        "family support. Have specific dates and details "
                        "ready."
                    ),
                },
                {
                    "id": "cancel_lpr_future",
                    "label": "How can you assure the court this won't happen again?",
                    "tip": (
                        "Concrete changes: new support system, ongoing "
                        "treatment, stable employment, family responsibilities, "
                        "removal from negative influences. Not just 'I've "
                        "learned my lesson.'"
                    ),
                },
            ],
        },
        {
            "title": "Equities & Hardship",
            "instructions": (
                "The judge weighs positive factors against the negative. "
                "Build the strongest possible case for discretion."
            ),
            "questions": [
                {
                    "id": "cancel_lpr_family",
                    "label": "Tell me about your family in the United States.",
                    "tip": (
                        "Emphasize USC and LPR family members, especially "
                        "children. Their ages, needs, dependence on the "
                        "respondent, and what would happen if the respondent "
                        "is removed."
                    ),
                },
                {
                    "id": "cancel_lpr_hardship",
                    "label": "What hardship would your family experience if you were deported?",
                    "tip": (
                        "Unlike non-LPR cancellation, there's no 'exceptional "
                        "and extremely unusual' standard, but hardship is "
                        "still a major factor. Financial impact, emotional "
                        "impact on children, medical needs, safety concerns."
                    ),
                },
                {
                    "id": "cancel_lpr_community",
                    "label": "What contributions have you made to your community?",
                    "tip": (
                        "Employment history, tax payments, volunteer work, "
                        "church involvement, military service, business "
                        "ownership. Length of time in the US matters — "
                        "emphasize deep roots."
                    ),
                },
            ],
        },
    ],

    # -------------------------------------------------------------------
    # Adjustment of Status (Defensive)
    # -------------------------------------------------------------------
    "Adjustment of Status (Defensive)": [
        {
            "title": "Eligibility & Petition",
            "instructions": (
                "ICE will challenge the bona fides of the underlying "
                "petition and the respondent's eligibility for adjustment."
            ),
            "questions": [
                {
                    "id": "aos_petition_basis",
                    "label": "What is the basis of your adjustment application?",
                    "tip": (
                        "Family-based (which relative?), employment-based, "
                        "or other. Practice stating the relationship and "
                        "petition type clearly: 'My US citizen spouse filed "
                        "an I-130 petition on my behalf.'"
                    ),
                },
                {
                    "id": "aos_relationship",
                    "label": "Describe your relationship with your petitioner.",
                    "tip": (
                        "For marriage-based: how you met, when you started "
                        "dating, wedding details, living together, shared "
                        "finances. ICE will test whether the relationship "
                        "is genuine. Practice natural, detailed answers."
                    ),
                },
                {
                    "id": "aos_admissibility",
                    "label": "Are there any grounds of inadmissibility that apply to you?",
                    "tip": (
                        "Unlawful presence, prior removal orders, criminal "
                        "history, fraud, public charge. If a waiver is being "
                        "sought, know which waiver and its requirements."
                    ),
                },
            ],
        },
        {
            "title": "Marriage Bona Fides (if applicable)",
            "instructions": (
                "ICE aggressively tests marriage-based cases for fraud. "
                "Both spouses should know consistent details about their "
                "relationship and daily life."
            ),
            "questions": [
                {
                    "id": "aos_how_met",
                    "label": "How did you and your spouse meet?",
                    "tip": (
                        "Be specific: exact location, date (at least month "
                        "and year), circumstances. Both spouses' accounts "
                        "must match. Practice telling the story naturally."
                    ),
                },
                {
                    "id": "aos_daily_life",
                    "label": "Describe your daily routine with your spouse.",
                    "tip": (
                        "ICE may ask very specific questions: Who cooks? "
                        "What side of the bed do you sleep on? What did you "
                        "do last weekend? Practice answering naturally with "
                        "real details."
                    ),
                },
                {
                    "id": "aos_evidence_marriage",
                    "label": "What evidence do you have that your marriage is genuine?",
                    "tip": (
                        "Joint bank accounts, lease/mortgage, insurance, "
                        "photos together, joint tax returns, birth "
                        "certificates of children, affidavits from friends "
                        "and family. Practice listing these confidently."
                    ),
                },
            ],
        },
        {
            "title": "Discretion",
            "instructions": (
                "Even when eligible, adjustment is discretionary. ICE may "
                "argue negative factors outweigh the positive."
            ),
            "questions": [
                {
                    "id": "aos_positive_factors",
                    "label": "Why should the judge grant your adjustment application?",
                    "tip": (
                        "Practice a concise summary: genuine relationship, "
                        "USC family members who would suffer hardship, "
                        "community ties, employment, good moral character, "
                        "length of residence."
                    ),
                },
                {
                    "id": "aos_negative_factors",
                    "label": "Are there any negative factors the judge should know about?",
                    "tip": (
                        "Immigration violations, prior orders, criminal "
                        "history, use of false documents. Better to "
                        "acknowledge proactively than to be caught hiding "
                        "something. Practice honest answers."
                    ),
                },
                {
                    "id": "aos_immigration_history",
                    "label": "Describe your complete immigration history in the United States.",
                    "tip": (
                        "Every entry, every status, every application filed. "
                        "ICE will have the full record. Practice going "
                        "through the timeline without confusion."
                    ),
                },
            ],
        },
    ],

    # -------------------------------------------------------------------
    # Bond / Custody Redetermination
    # -------------------------------------------------------------------
    "Bond / Custody Redetermination": [
        {
            "title": "Flight Risk",
            "instructions": (
                "The judge must determine whether the respondent is a flight "
                "risk. ICE will argue against release. Prepare to show ties "
                "to the community and a plan to appear at all hearings."
            ),
            "questions": [
                {
                    "id": "bond_ties",
                    "label": "What ties do you have to this community?",
                    "tip": (
                        "Family in the area (especially USC/LPR relatives), "
                        "stable address, employment or job offer, children "
                        "in school, church membership. These show the "
                        "respondent won't flee."
                    ),
                },
                {
                    "id": "bond_appearances",
                    "label": "Have you ever missed a court date or immigration appointment?",
                    "tip": (
                        "If yes, explain the circumstances honestly. If no, "
                        "emphasize the clean record of appearances. Practice: "
                        "'I have appeared at every hearing and appointment "
                        "scheduled in my case.'"
                    ),
                },
                {
                    "id": "bond_sponsor",
                    "label": "Who will you live with if released? Describe your living situation.",
                    "tip": (
                        "Name the sponsor, their relationship, address, and "
                        "immigration status. A USC or LPR sponsor is "
                        "strongest. Have the address ready."
                    ),
                },
            ],
        },
        {
            "title": "Danger to Community",
            "instructions": (
                "ICE must show by clear and convincing evidence that the "
                "respondent is a danger. If there is a criminal record, "
                "prepare to address it directly."
            ),
            "questions": [
                {
                    "id": "bond_criminal",
                    "label": "Do you have any criminal history? Describe each incident.",
                    "tip": (
                        "Full disclosure. For each: date, charge, outcome, "
                        "sentence. If there's rehabilitation evidence "
                        "(completed programs, no reoffending), emphasize it."
                    ),
                },
                {
                    "id": "bond_danger",
                    "label": "Why should the judge believe you are not a danger to the community?",
                    "tip": (
                        "Rehabilitation, time since offense, family support, "
                        "employment, no history of violence. Practice a "
                        "concise, confident answer."
                    ),
                },
                {
                    "id": "bond_amount",
                    "label": "What bond amount can you afford? Who will pay it?",
                    "tip": (
                        "Be realistic. Know the exact amount available and "
                        "who will post it. If using a bond company, know "
                        "the details. The judge needs to believe the bond "
                        "amount is sufficient to ensure appearance."
                    ),
                },
            ],
        },
    ],
}

# ---------------------------------------------------------------------------
# Claude system prompt for ICE cross-examination evaluation
# ---------------------------------------------------------------------------

ICE_EVALUATOR_SYSTEM_PROMPT: str = """\
You are an experienced ICE trial attorney evaluator for immigration hearing preparation. Your role is to evaluate a respondent's answer to a cross-examination question as an ICE trial attorney would, then provide structured feedback.

## Your Evaluation Approach

For each answer, you should:

1. **Assess the answer** as a skilled ICE trial attorney would — looking for weaknesses, inconsistencies, vagueness, or opportunities to undermine credibility.

2. **Apply cross-examination tactics**:
   - **Probing for details**: If the answer is vague, note what specific details are missing
   - **Challenging inconsistencies**: Flag any internal contradictions or statements that conflict with typical case narratives
   - **Testing corroboration**: Note if the answer lacks verifiable details or documentary support
   - **Exploring alternatives**: Identify innocent explanations ICE might propose for the claimed persecution
   - **Motive questioning**: Consider whether ICE would question the respondent's motives for seeking relief

3. **Score the answer** from 1-5:
   - 1 = Very weak — answer would significantly damage the case
   - 2 = Weak — answer has major gaps or credibility issues
   - 3 = Adequate — answer is acceptable but could be stronger
   - 4 = Strong — answer is detailed, consistent, and persuasive
   - 5 = Excellent — answer would withstand aggressive cross-examination

4. **Formulate a follow-up question** that an ICE trial attorney would likely ask based on the answer given. This should target the weakest point of the answer.

## Response Format

You MUST respond with valid JSON in exactly this format:

```json
{
  "evaluation": "A detailed evaluation paragraph analyzing the answer's strengths and weaknesses from the ICE trial attorney's perspective. Be specific about what worked and what didn't.",
  "score": 4,
  "strengths": ["Specific strength 1", "Specific strength 2"],
  "weaknesses": ["Specific area for improvement 1", "Specific area for improvement 2"],
  "follow_up_question": "The next probing question an ICE trial attorney would ask based on this answer."
}
```

## Important Guidelines

- Be rigorous but constructive. The goal is to prepare the respondent, not discourage them.
- Consider the case type and legal standards when evaluating.
- If the answer contains information that could hurt the case, flag it clearly.
- Your follow-up questions should mimic real ICE cross-examination style: pointed, specific, and designed to test credibility.
- Keep your evaluation paragraph to 3-5 sentences.
- List 1-3 strengths and 1-3 weaknesses.
- If this is a follow-up to a previous question, consider the full conversation history for consistency.
- Always respond in English, even if the respondent's answer was in another language (which has been translated).
"""


# ---------------------------------------------------------------------------
# Config-aware loading
# ---------------------------------------------------------------------------

CASE_TYPES = _DEFAULT_CASE_TYPES
QUESTION_BANKS = _DEFAULT_QUESTION_BANKS


def get_case_types() -> list[str]:
    """Return case types from admin config, falling back to defaults."""
    return get_config_value("hearing-prep", "case_types", _DEFAULT_CASE_TYPES)


def get_question_banks() -> dict[str, list[dict]]:
    """Return question banks from admin config, falling back to defaults."""
    return get_config_value("hearing-prep", "question_banks", _DEFAULT_QUESTION_BANKS)


def get_all_questions(case_type: str) -> list[dict]:
    """Return a flat list of all questions for a case type."""
    banks = get_question_banks()
    sections = banks.get(case_type, [])
    questions = []
    for section in sections:
        for q in section["questions"]:
            questions.append({**q, "section": section["title"]})
    return questions
