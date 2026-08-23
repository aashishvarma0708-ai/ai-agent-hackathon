import io
import logging
from typing import Optional, Dict, Any
from groq import Groq
from .config import GROQ_API_KEY, STT_MODEL

logger = logging.getLogger("civicresolve.voice")


def transcribe_audio(
    uploaded_audio, 
    filename: str = "voice_recording.webm",
    language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transcribes audio using Groq Whisper model (e.g. whisper-large-v3-turbo).
    Supports English, Telugu, Hindi, Tamil, Kannada, and auto-detection.
    """
    if not GROQ_API_KEY:
        logger.error("GROQ_API_KEY is not configured in backend environment.")
        raise RuntimeError("GROQ_API_KEY is missing. Add it to backend .env to use voice transcription.")

    client = Groq(api_key=GROQ_API_KEY)
    
    if hasattr(uploaded_audio, "getvalue"):
        audio_bytes = uploaded_audio.getvalue()
    elif hasattr(uploaded_audio, "read"):
        audio_bytes = uploaded_audio.read()
    else:
        audio_bytes = uploaded_audio

    if not audio_bytes or len(audio_bytes) == 0:
        logger.warning("Empty audio payload received for transcription.")
        raise ValueError("Audio recording is empty (0 bytes).")

    # Map language codes for MVP (Supported: 'en', 'hi')
    lang_param = "en"
    if language and str(language).strip():
        code = str(language).strip().lower()
        if code in {"hi", "hindi"}:
            lang_param = "hi"
        elif code in {"en", "english"}:
            lang_param = "en"
        else:
            logger.warning(f"Language '{language}' requested outside MVP options. Falling back safely to 'en'.")
            lang_param = "en"

    logger.info(
        f"Transcribing audio: filename='{filename}', size={len(audio_bytes)}B, model='{STT_MODEL}', language_hint='{lang_param}'"
    )

    create_kwargs = {
        "file": (filename, audio_bytes),
        "model": STT_MODEL,
        "language": lang_param,
        "response_format": "verbose_json",
        "temperature": 0.0,
    }

    try:
        transcription = client.audio.transcriptions.create(**create_kwargs)
    except Exception as e:
        logger.error(f"Groq Whisper STT API error: {str(e)}", exc_info=True)
        raise RuntimeError(f"Groq Whisper transcription failed: {str(e)}")

    raw_text = getattr(transcription, "text", "") or ""
    det_language = getattr(transcription, "language", "") or lang_param or "unknown"
    clean_text = raw_text.strip()

    # Filter out empty or noise-only artifacts (like standalone punctuation)
    if clean_text in {".", "..", "...", ",", "?", "!", "--", "-"}:
        clean_text = ""

    logger.info(f"Transcription successful: detected_language='{det_language}', text='{clean_text}'")

    return {
        "success": bool(clean_text),
        "transcript": clean_text,
        "text": clean_text,
        "selected_language": lang_param or "auto",
        "detected_language": str(det_language),
        "language": str(det_language),
    }
