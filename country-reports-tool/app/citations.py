"""Citation template management — load, save, and format citations."""

import json
import re

from app.config import BASE_DIR

TEMPLATE_PATH = BASE_DIR / "data" / "citation_template.json"

_DEFAULT_TEMPLATE = '"{snippet}" - Source: {source}, Country: {country}'
_DEFAULT_MAX_SNIPPET_LENGTH = 300


def load_template() -> dict:
    """Return the saved citation template config, or defaults."""
    if TEMPLATE_PATH.exists():
        with open(TEMPLATE_PATH) as f:
            return json.load(f)
    return {
        "template": _DEFAULT_TEMPLATE,
        "max_snippet_length": _DEFAULT_MAX_SNIPPET_LENGTH,
    }


def save_template(template: str, max_snippet_length: int) -> None:
    """Persist citation template config to JSON."""
    TEMPLATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(TEMPLATE_PATH, "w") as f:
        json.dump(
            {"template": template, "max_snippet_length": max_snippet_length},
            f,
            indent=2,
        )


_SENTENCE_END = re.compile(r'[.!?]["\')\]]?\s+')
_SENTENCE_START = re.compile(r'(?<=[.!?]\s)[A-Z]')


def trim_to_sentences(text: str) -> str:
    """Trim text so it starts at the beginning of the first full sentence
    and ends at the completion of the last full sentence.

    Returns the original text unchanged if no sentence boundaries are found.
    """
    stripped = text.strip()
    if not stripped:
        return stripped

    # If text already starts with an uppercase letter, assume it's a sentence start
    starts_clean = stripped[0].isupper()

    # Find the first sentence start if we're mid-sentence
    if not starts_clean:
        m = _SENTENCE_START.search(stripped)
        if m:
            stripped = stripped[m.start():]
        # If no uppercase sentence start found, keep the original start

    # If text already ends with sentence-ending punctuation, keep the end as-is
    if re.search(r'[.!?]["\')\]]?\s*$', stripped):
        return stripped.rstrip()

    # Otherwise trim to the last complete sentence
    ends = list(_SENTENCE_END.finditer(stripped))
    if ends:
        last = ends[-1]
        stripped = stripped[: last.end()].rstrip()

    return stripped


def format_citation(
    text: str, source: str, country: str, chunk_index: int
) -> str:
    """Format a citation string using the saved template."""
    cfg = load_template()
    template = cfg["template"]
    max_len = cfg["max_snippet_length"]

    snippet = text[:max_len]
    if len(text) > max_len:
        snippet += "..."

    return template.format(
        snippet=snippet,
        source=source,
        country=country,
        chunk_index=chunk_index,
    )
