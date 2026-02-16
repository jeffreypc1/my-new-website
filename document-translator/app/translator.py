"""Document translation engine.

Handles text extraction from PDFs, Word docs, and images, language
detection, and paragraph-by-paragraph translation via Google Translate
v2 Basic API.
"""

from __future__ import annotations

import os
import re

import requests

# Google Translate v2 Basic API
_API_KEY = os.environ.get("GOOGLE_TRANSLATE_API_KEY", "")
_TRANSLATE_URL = "https://translation.googleapis.com/language/translate/v2"
_DETECT_URL = "https://translation.googleapis.com/language/translate/v2/detect"

# Common immigration languages (code -> display name)
LANGUAGES: dict[str, str] = {
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
