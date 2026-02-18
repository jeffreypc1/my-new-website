"""Document translation engine.

Handles text extraction from PDFs, Word docs, and images, language
detection, and paragraph-by-paragraph translation via Google Translate
v2 Basic API.
"""

from __future__ import annotations

import os
import re
import sys as _sys
from pathlib import Path as _Path

import requests

_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent.parent))
from shared.config_store import get_config_value

# Google Translate v2 Basic API
_API_KEY = os.environ.get("GOOGLE_TRANSLATE_API_KEY", "")
_TRANSLATE_URL = "https://translation.googleapis.com/language/translate/v2"
_DETECT_URL = "https://translation.googleapis.com/language/translate/v2/detect"

# Common immigration languages (code -> display name)
_DEFAULT_LANGUAGES: dict[str, str] = {
    "en": "English",
    "es": "Spanish",
    "pt": "Portuguese",
    "zh": "Chinese (Simplified)",
    "zh-TW": "Chinese (Traditional)",
    "ar": "Arabic",
    "fr": "French",
    "ru": "Russian",
    "ko": "Korean",
    "tl": "Tagalog",
    "vi": "Vietnamese",
    "ht": "Haitian Creole",
    "am": "Amharic",
    "hi": "Hindi",
    "ur": "Urdu",
    "bn": "Bengali",
    "fa": "Farsi",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "ro": "Romanian",
    "sw": "Swahili",
    "so": "Somali",
    "ja": "Japanese",
    "de": "German",
    "it": "Italian",
    "pl": "Polish",
    "my": "Burmese",
    "km": "Khmer",
    "th": "Thai",
    "ne": "Nepali",
    "gu": "Gujarati",
    "ta": "Tamil",
    "te": "Telugu",
    "pa": "Punjabi",
}

# ── Config-aware loading (JSON override with hardcoded fallback) ─────────────
LANGUAGES: dict[str, str] = get_config_value("document-translator", "languages", _DEFAULT_LANGUAGES)

# Reverse lookup: display name -> code
LANGUAGE_BY_NAME: dict[str, str] = {v: k for k, v in LANGUAGES.items()}

# Target languages offered in the UI (subset, most useful)
TARGET_LANGUAGES: list[str] = [
    "English",
    "Spanish",
    "Portuguese",
    "French",
    "Chinese (Simplified)",
    "Arabic",
    "Russian",
]


def _check_api_key() -> None:
    if not _API_KEY:
        raise RuntimeError(
            "GOOGLE_TRANSLATE_API_KEY environment variable is not set. "
            "Enable the Cloud Translation API in your Google Cloud project "
            "and create an API key."
        )


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------


def extract_text(file_bytes: bytes, filename: str) -> list[str]:
    """Extract text from a file and return a list of paragraphs.

    Supports PDF (.pdf), Word (.docx), and images (.jpg, .jpeg, .png).
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "pdf":
        return _extract_pdf(file_bytes)
    elif ext == "docx":
        return _extract_docx(file_bytes)
    elif ext in ("jpg", "jpeg", "png", "tiff", "tif", "bmp", "webp"):
        return _extract_image(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: .{ext}")


def _extract_pdf(file_bytes: bytes) -> list[str]:
    """Extract text from a PDF using PyMuPDF, page by page."""
    import fitz

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    paragraphs: list[str] = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if text.strip():
            # Split into paragraphs (double newline or significant gap)
            page_paras = re.split(r"\n\s*\n", text.strip())
            for p in page_paras:
                cleaned = " ".join(p.split())
                if cleaned:
                    paragraphs.append(cleaned)
    doc.close()
    return paragraphs


def _extract_docx(file_bytes: bytes) -> list[str]:
    """Extract text from a Word document."""
    import io

    from docx import Document

    doc = Document(io.BytesIO(file_bytes))
    paragraphs: list[str] = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            paragraphs.append(text)
    return paragraphs


def _extract_image(file_bytes: bytes) -> list[str]:
    """Extract text from an image using Tesseract OCR."""
    import io

    import pytesseract
    from PIL import Image

    img = Image.open(io.BytesIO(file_bytes))
    text = pytesseract.image_to_string(img)
    paragraphs: list[str] = []
    if text.strip():
        page_paras = re.split(r"\n\s*\n", text.strip())
        for p in page_paras:
            cleaned = " ".join(p.split())
            if cleaned:
                paragraphs.append(cleaned)
    return paragraphs


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------


def detect_language(text: str) -> tuple[str, float]:
    """Detect the language of the given text.

    Returns (language_code, confidence) using Google Translate v2 detect.
    Sends at most the first 500 characters.
    """
    _check_api_key()

    sample = text[:500]
    resp = requests.post(
        _DETECT_URL,
        params={"key": _API_KEY},
        json={"q": sample},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    detections = data.get("data", {}).get("detections", [[]])
    if detections and detections[0]:
        best = detections[0][0]
        lang_code = best.get("language", "und")
        confidence = best.get("confidence", 0.0)
        return lang_code, confidence

    return "und", 0.0


def language_name(code: str) -> str:
    """Return the display name for a language code, or the code itself."""
    return LANGUAGES.get(code, code)


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------


def translate_paragraphs(
    paragraphs: list[str],
    target_lang: str,
    source_lang: str | None = None,
    on_progress: callable | None = None,
) -> list[dict]:
    """Translate paragraphs using Google Translate v2 Basic API.

    Batches up to 50 paragraphs per request to stay within API limits.
    Returns a list of dicts: {original, translated, detected_lang}.

    on_progress(completed, total) is called after each batch if provided.
    """
    _check_api_key()

    target_code = LANGUAGE_BY_NAME.get(target_lang, target_lang)

    results: list[dict] = []
    batch_size = 50
    total = len(paragraphs)

    for i in range(0, total, batch_size):
        batch = paragraphs[i : i + batch_size]

        body: dict = {
            "q": batch,
            "target": target_code,
            "format": "text",
        }
        if source_lang:
            src_code = LANGUAGE_BY_NAME.get(source_lang, source_lang)
            body["source"] = src_code

        resp = requests.post(
            _TRANSLATE_URL,
            params={"key": _API_KEY},
            json=body,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        translations = data.get("data", {}).get("translations", [])
        for j, t in enumerate(translations):
            results.append(
                {
                    "original": batch[j],
                    "translated": t.get("translatedText", ""),
                    "detected_lang": t.get("detectedSourceLanguage", source_lang or ""),
                }
            )

        if on_progress:
            on_progress(min(i + batch_size, total), total)

    return results


# ---------------------------------------------------------------------------
# Certification header
# ---------------------------------------------------------------------------


def certification_header() -> str:
    """Return the machine translation disclaimer for legal documents."""
    return (
        "NOTICE: This is a machine-assisted translation produced using "
        "Google Translate. It is provided for informational purposes only. "
        "Review by a qualified translator is recommended before use in "
        "legal proceedings. The accuracy of this translation has not been "
        "verified by a certified translator."
    )


# ---------------------------------------------------------------------------
# EOIR certificates (per Immigration Court Practice Manual / 8 CFR § 1003.33)
# ---------------------------------------------------------------------------

CERTIFICATE_TYPES = [
    "None",
    "Certificate of Translation",
    "Certificate of Sight Translation",
    "Certificate of Interpretation",
]


def build_certificate(
    cert_type: str,
    translator_name: str,
    translator_address: str,
    translator_phone: str,
    source_lang: str,
    target_lang: str,
    source_filename: str,
    client_name: str = "",
    client_pronoun: str = "they",
) -> str:
    """Build an EOIR-compliant certificate block.

    Returns the certificate text, or empty string if cert_type is "None".
    """
    from datetime import date

    if cert_type == "None" or not cert_type:
        return ""

    today = date.today().strftime("%m/%d/%Y")

    # Pronoun forms for interpretation cert
    pronoun_map = {
        "he": ("he", "his"),
        "she": ("she", "her"),
        "they": ("they", "their"),
    }
    subj, _poss = pronoun_map.get(client_pronoun, ("they", "their"))

    if cert_type == "Certificate of Translation":
        body = (
            f"I, {translator_name}, of {translator_address}, hereby certify "
            f"that I am competent to translate from {source_lang} to "
            f"{target_lang}, and that the foregoing document, identified as "
            f'"{source_filename}," is a true and accurate translation of the '
            f"original to the best of my knowledge and ability."
        )
    elif cert_type == "Certificate of Sight Translation":
        body = (
            f"I, {translator_name}, of {translator_address}, hereby certify "
            f"that I am competent to translate from {source_lang} to "
            f"{target_lang}. On {today}, I performed a sight translation of "
            f'the document identified as "{source_filename}," orally rendering '
            f"the written {source_lang} text into {target_lang}. The sight "
            f"translation was true and accurate to the best of my knowledge "
            f"and ability."
        )
    elif cert_type == "Certificate of Interpretation":
        body = (
            f"I, {translator_name}, of {translator_address}, hereby certify "
            f"that I am competent to interpret between {source_lang} and "
            f"{target_lang}. I read and interpreted the contents of the "
            f'document identified as "{source_filename}" to {client_name} in '
            f"{source_lang}, a language which {subj} understands, and {subj} "
            f"indicated understanding of the contents before signing."
        )
    else:
        return ""

    lines = [
        cert_type.upper(),
        "",
        body,
        "",
        f"Name: {translator_name}",
        f"Address: {translator_address}",
        f"Telephone: {translator_phone}",
        f"Date: {today}",
        "",
        "Signature: ____________________________",
    ]
    return "\n".join(lines)
