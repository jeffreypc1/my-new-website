"""Google Speech-to-Text wrapper for Hearing Prep.

Provides synchronous recognition for short audio (< 1 min) and
long-running recognition for longer recordings. Auto-detects audio
format from file header.

Auth: GOOGLE_APPLICATION_CREDENTIALS env var pointing to service account JSON.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# ---------------------------------------------------------------------------
# Supported languages
# ---------------------------------------------------------------------------

SUPPORTED_LANGUAGES: dict[str, str] = {
    "English": "en-US",
    "Spanish": "es-US",
    "French": "fr-FR",
    "Portuguese": "pt-BR",
    "Arabic": "ar-SA",
    "Mandarin": "zh",
    "Cantonese": "yue-Hant-HK",
    "Hindi": "hi-IN",
    "Urdu": "ur-PK",
    "Bengali": "bn-BD",
    "Tagalog": "fil-PH",
    "Korean": "ko-KR",
    "Russian": "ru-RU",
    "Haitian Creole": "ht-HT",
    "Amharic": "am-ET",
    "Tigrinya": "ti-ET",
    "Somali": "so-SO",
    "Swahili": "sw-KE",
    "Nepali": "ne-NP",
    "Burmese": "my-MM",
    "Vietnamese": "vi-VN",
    "Gujarati": "gu-IN",
}


def _detect_encoding(audio_bytes: bytes):
    """Auto-detect audio encoding from file header.

    Returns a (RecognitionConfig.AudioEncoding, sample_rate) tuple.
    """
    from google.cloud.speech_v1 import RecognitionConfig

    # WebM/Opus (Streamlit audio_input default)
    if audio_bytes[:4] == b"\x1a\x45\xdf\xa3" or b"webm" in audio_bytes[:40]:
        return RecognitionConfig.AudioEncoding.WEBM_OPUS, 48000

    # WAV/RIFF
    if audio_bytes[:4] == b"RIFF":
        return RecognitionConfig.AudioEncoding.LINEAR16, 16000

    # OGG/Opus
    if audio_bytes[:4] == b"OggS":
        return RecognitionConfig.AudioEncoding.OGG_OPUS, 48000

    # FLAC
    if audio_bytes[:4] == b"fLaC":
        return RecognitionConfig.AudioEncoding.FLAC, 16000

    # Default: assume WebM/Opus (most common from browser)
    return RecognitionConfig.AudioEncoding.WEBM_OPUS, 48000


def transcribe_audio(
    audio_bytes: bytes,
    language_code: str = "en-US",
) -> dict:
    """Transcribe short audio (< 1 minute) using synchronous recognition.

    Returns:
        {
            "transcript": str,
            "confidence": float,
            "language_code": str,
        }
    """
    from google.cloud.speech_v1 import RecognitionAudio, RecognitionConfig, SpeechClient

    encoding, sample_rate = _detect_encoding(audio_bytes)

    client = SpeechClient()
    audio = RecognitionAudio(content=audio_bytes)
    config = RecognitionConfig(
        encoding=encoding,
        sample_rate_hertz=sample_rate,
        language_code=language_code,
        enable_automatic_punctuation=True,
        model="latest_long",
    )

    response = client.recognize(config=config, audio=audio)

    transcript = ""
    confidence = 0.0
    if response.results:
        transcript = " ".join(
            result.alternatives[0].transcript
            for result in response.results
            if result.alternatives
        )
        confidences = [
            result.alternatives[0].confidence
            for result in response.results
            if result.alternatives
        ]
        confidence = sum(confidences) / len(confidences) if confidences else 0.0

    # Log usage
    _log_usage(audio_bytes, language_code)

    return {
        "transcript": transcript.strip(),
        "confidence": round(confidence, 4),
        "language_code": language_code,
    }


def transcribe_long_audio(
    audio_bytes: bytes,
    language_code: str = "en-US",
) -> dict:
    """Transcribe long audio (> 1 minute) using long-running recognition.

    Returns same dict format as transcribe_audio().
    """
    from google.cloud.speech_v1 import RecognitionAudio, RecognitionConfig, SpeechClient

    encoding, sample_rate = _detect_encoding(audio_bytes)

    client = SpeechClient()
    audio = RecognitionAudio(content=audio_bytes)
    config = RecognitionConfig(
        encoding=encoding,
        sample_rate_hertz=sample_rate,
        language_code=language_code,
        enable_automatic_punctuation=True,
        model="latest_long",
    )

    operation = client.long_running_recognize(config=config, audio=audio)
    response = operation.result(timeout=300)

    transcript = ""
    confidence = 0.0
    if response.results:
        transcript = " ".join(
            result.alternatives[0].transcript
            for result in response.results
            if result.alternatives
        )
        confidences = [
            result.alternatives[0].confidence
            for result in response.results
            if result.alternatives
        ]
        confidence = sum(confidences) / len(confidences) if confidences else 0.0

    _log_usage(audio_bytes, language_code)

    return {
        "transcript": transcript.strip(),
        "confidence": round(confidence, 4),
        "language_code": language_code,
    }


def _log_usage(audio_bytes: bytes, language_code: str) -> None:
    """Log Speech-to-Text usage to the shared usage tracker."""
    try:
        from shared.usage_tracker import log_api_call

        # Google Speech-to-Text pricing: $0.006 per 15 seconds
        # Rough estimate based on file size (actual duration would need parsing)
        duration_estimate_sec = len(audio_bytes) / 16000  # rough estimate
        cost_estimate = (duration_estimate_sec / 15) * 0.006

        log_api_call(
            service="google_speech",
            tool="hearing-prep",
            operation="transcribe",
            estimated_cost_usd=round(cost_estimate, 6),
            details=f"language={language_code}",
        )
    except Exception:
        pass
