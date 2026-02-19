"""Multi-turn Claude evaluator for Hearing Prep.

Unlike shared/claude_client.py (single-turn, used by 13 tools), this module
maintains conversation history across turns so Claude can detect inconsistencies
and ask increasingly probing follow-ups.

Uses the same API key loading, model constant, and usage tracking pattern.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
_MODEL = "claude-sonnet-4-5-20250929"


def evaluate_answer(
    system_prompt: str,
    conversation_history: list[dict],
    current_question: str,
    answer_transcript: str,
    case_type: str,
) -> dict:
    """Send the full conversation to Claude and return a parsed evaluation.

    Parameters:
        system_prompt: The ICE evaluator system prompt.
        conversation_history: Previous messages in Claude format
            [{"role": "user", "content": ...}, {"role": "assistant", "content": ...}, ...]
        current_question: The question that was asked.
        answer_transcript: The respondent's transcribed answer.
        case_type: The case type for context.

    Returns:
        {
            "evaluation": str,
            "score": int (1-5),
            "strengths": list[str],
            "weaknesses": list[str],
            "follow_up_question": str,
        }
    """
    from dotenv import dotenv_values
    import anthropic

    env = dotenv_values(_ENV_PATH)
    api_key = env.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not found in .env. "
            "Add it to /Users/jeff/my-new-website/.env to enable AI evaluation."
        )

    # Build the current turn's user message
    user_message = (
        f"Case Type: {case_type}\n\n"
        f"Question asked: {current_question}\n\n"
        f"Respondent's answer: {answer_transcript}\n\n"
        "Evaluate this answer and respond with the required JSON format."
    )

    # Combine history with current message
    messages = list(conversation_history) + [{"role": "user", "content": user_message}]

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=_MODEL,
        max_tokens=2048,
        system=system_prompt,
        messages=messages,
    )

    response_text = message.content[0].text

    # Log usage
    try:
        from shared.usage_tracker import estimate_cost, log_api_call

        inp = message.usage.input_tokens
        out = message.usage.output_tokens
        log_api_call(
            service="anthropic",
            tool="hearing-prep",
            operation="evaluate",
            model=_MODEL,
            input_tokens=inp,
            output_tokens=out,
            estimated_cost_usd=estimate_cost(_MODEL, inp, out),
        )
    except Exception:
        pass

    return _parse_evaluation(response_text)


def build_conversation_history(turns_and_evals: list[dict]) -> list[dict]:
    """Reconstruct Claude-compatible message array from DB records.

    Each turn becomes a user message (question + answer) and the evaluation
    becomes an assistant message. This lets Claude see the full session
    context when evaluating a new answer.

    Parameters:
        turns_and_evals: Output of database.get_session_transcript()
            Each item has turn fields + 'evaluation' dict (or None).

    Returns:
        List of {"role": "user"/"assistant", "content": str} dicts.
    """
    messages: list[dict] = []
    for item in turns_and_evals:
        # User message: the question and answer
        user_msg = (
            f"Question asked: {item['question_text']}\n\n"
            f"Respondent's answer: {item['transcript']}"
        )
        messages.append({"role": "user", "content": user_msg})

        # Assistant message: the evaluation (if exists)
        evaluation = item.get("evaluation")
        if evaluation:
            eval_json = {
                "evaluation": evaluation.get("evaluation_text", ""),
                "score": evaluation.get("score", 0),
                "strengths": evaluation.get("strengths", []),
                "weaknesses": evaluation.get("weaknesses", []),
                "follow_up_question": evaluation.get("follow_up_question", ""),
            }
            messages.append({"role": "assistant", "content": json.dumps(eval_json)})

    return messages


def _parse_evaluation(text: str) -> dict:
    """Extract evaluation JSON from Claude's response.

    Handles markdown fences, extra text around JSON, and malformed output.
    """
    # Try to find JSON in markdown code fences
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1)

    # Try to find raw JSON object
    json_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            return _normalize_evaluation(parsed)
        except json.JSONDecodeError:
            pass

    # Try parsing the whole text as JSON
    try:
        parsed = json.loads(text)
        return _normalize_evaluation(parsed)
    except json.JSONDecodeError:
        pass

    # Fallback: return the raw text as the evaluation
    return {
        "evaluation": text.strip(),
        "score": 3,
        "strengths": [],
        "weaknesses": [],
        "follow_up_question": "",
    }


def _normalize_evaluation(parsed: dict) -> dict:
    """Ensure all expected fields exist with correct types."""
    return {
        "evaluation": str(parsed.get("evaluation", "")),
        "score": int(parsed.get("score", 3)),
        "strengths": list(parsed.get("strengths", [])),
        "weaknesses": list(parsed.get("weaknesses", [])),
        "follow_up_question": str(parsed.get("follow_up_question", "")),
    }
