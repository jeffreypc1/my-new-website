"""Thin wrapper around the Anthropic SDK for Claude AI drafting."""

from __future__ import annotations

from pathlib import Path

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
_MODEL = "claude-sonnet-4-5-20250929"


def draft_with_claude(
    system_prompt: str,
    user_message: str,
    max_tokens: int = 4096,
    tool_name: str = "",
) -> str:
    """Send a drafting request to Claude and return the text response.

    Loads the API key from the shared .env file. Raises RuntimeError if
    the key is missing. Logs token usage to the usage tracker.
    """
    from dotenv import dotenv_values
    import anthropic

    env = dotenv_values(_ENV_PATH)
    api_key = env.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not found in .env. "
            "Add it to /Users/jeff/my-new-website/.env to enable AI drafting."
        )

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=_MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    # Log usage
    try:
        from shared.usage_tracker import estimate_cost, log_api_call

        inp = message.usage.input_tokens
        out = message.usage.output_tokens
        log_api_call(
            service="anthropic",
            tool=tool_name or "unknown",
            operation="draft",
            model=_MODEL,
            input_tokens=inp,
            output_tokens=out,
            estimated_cost_usd=estimate_cost(_MODEL, inp, out),
        )
    except Exception:
        pass  # never let logging break the drafting flow

    return message.content[0].text
