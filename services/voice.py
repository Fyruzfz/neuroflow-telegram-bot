"""
NeuroFlow AI Bot - Voice Service
Tamil + English Speech-to-Text (STT) via faster-whisper
Tamil + English Text-to-Speech (TTS) via edge-tts
"""

import os
import asyncio
import tempfile
from pathlib import Path

# Output directory for voice files
VOICE_DIR = Path(__file__).parent.parent / "output" / "voice"
VOICE_DIR.mkdir(parents=True, exist_ok=True)

# ─── STT: Speech to Text ───

# Lazy-loaded model
_stt_model = None


def _get_stt_model():
    """Load faster-whisper model (lazy, only once)."""
    global _stt_model
    if _stt_model is None:
        from faster_whisper import WhisperModel
        # tiny model = Tamil OK, fastest, ~1GB
        _stt_model = WhisperModel("tiny", device="cpu", compute_type="int8")
    return _stt_model


async def speech_to_text(audio_path: str) -> str:
    """
    Convert voice audio to text using faster-whisper.
    Supports Tamil, English, and mixed.
    Returns transcribed text or empty string on failure.
    """
    try:
        model = _get_stt_model()
        segments, info = model.transcribe(
            audio_path,
            language=None,  # auto-detect
            beam_size=5,
            vad_filter=True,
        )

        text_parts = []
        for segment in segments:
            text_parts.append(segment.text.strip())

        result = " ".join(text_parts).strip()
        return result

    except Exception as e:
        print(f"[STT ERROR] {e}")
        return ""


# ─── TTS: Text to Speech ───

async def text_to_speech(text: str, lang: str = "ta") -> str:
    """
    Convert text to speech using edge-tts (Microsoft Edge TTS — free).
    Returns path to generated MP3 file.
    lang: 'ta' for Tamil, 'en' for English
    """
    try:
        import edge_tts

        voice = "ta-IN-PallaviNeural" if lang == "ta" else "en-US-JennyNeural"

        # Generate unique filename
        import uuid
        filename = f"voice_{uuid.uuid4().hex[:8]}.mp3"
        output_path = str(VOICE_DIR / filename)

        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)

        return output_path

    except Exception as e:
        print(f"[TTS ERROR] {e}")
        return ""


# ─── Voice Reply Pipeline ───

async def voice_reply(audio_path: str) -> dict:
    """
    Full voice pipeline:
    1. STT: audio → Tamil/English text
    2. Returns the transcribed text
    
    Returns: {"text": "...", "lang": "ta"|"en", "success": bool}
    """
    text = await speech_to_text(audio_path)
    if not text:
        return {"success": False, "text": "", "lang": "en", "error": "STT failed"}

    # Detect language (simple heuristic)
    tamil_chars = sum(1 for c in text if '\u0B80' <= c <= '\u0BFF')
    lang = "ta" if tamil_chars >= 2 else "en"

    return {"success": True, "text": text, "lang": lang}


async def generate_voice_response(text: str, lang: str = "ta") -> str:
    """
    Generate voice reply MP3 for given text.
    Returns path to MP3 file.
    """
    return await text_to_speech(text, lang)
