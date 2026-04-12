"""Groq Orpheus TTS provider."""
import io
import os
import wave

from backend.app.tts.base import TTSProvider, TTSResult


MODEL = "canopylabs/orpheus-v1-english"
MAX_CHARS = 200
VOICES = [
    {"id": "tara", "name": "Tara", "description": "Female, conversational, clear"},
    {"id": "leah", "name": "Leah", "description": "Female, warm, gentle"},
    {"id": "mia", "name": "Mia", "description": "Female, professional, articulate"},
    {"id": "jess", "name": "Jess", "description": "Female, energetic"},
    {"id": "leo", "name": "Leo", "description": "Male, confident"},
    {"id": "dan", "name": "Dan", "description": "Male, casual"},
]
VOICE_IDS = {v["id"] for v in VOICES}


def _get_api_key() -> str:
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        try:
            from scripts.lib.secrets import get_groq_key
            key = get_groq_key()
        except Exception:
            pass
    return key


def _chunk_text(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    chunks = []
    remaining = text
    while remaining:
        if len(remaining) <= max_chars:
            chunks.append(remaining)
            break
        candidate = remaining[:max_chars]
        split_at = -1
        for sep in [". ", "! ", "? ", "; ", ", ", " "]:
            idx = candidate.rfind(sep)
            if idx > 0:
                split_at = idx + len(sep)
                break
        if split_at <= 0:
            split_at = max_chars
        chunks.append(remaining[:split_at].rstrip())
        remaining = remaining[split_at:].lstrip()
    return chunks


def _apply_emotion(text: str, emotion: str = "") -> str:
    if not emotion or text.startswith("["):
        return text
    return f"[{emotion}] {text}"


def _concatenate_wav(wav_buffers: list[bytes]) -> bytes:
    if len(wav_buffers) == 1:
        return wav_buffers[0]
    all_frames = b""
    params = None
    for buf in wav_buffers:
        with wave.open(io.BytesIO(buf), "rb") as wf:
            if params is None:
                params = wf.getparams()
            all_frames += wf.readframes(wf.getnframes())
    if params is None:
        return b""
    out = io.BytesIO()
    with wave.open(out, "wb") as wf:
        wf.setparams(params)
        wf.writeframes(all_frames)
    return out.getvalue()


class GroqOrpheusProvider(TTSProvider):
    name = "groq_orpheus"

    def is_available(self) -> bool:
        return bool(_get_api_key())

    def voices(self) -> list[dict]:
        return VOICES

    def emotions(self) -> list[str]:
        return ["cheerful", "whisper", "calm", "excited", "sad", "angry"]

    async def synthesize(self, text: str, voice: str = "tara", emotion: str = "") -> TTSResult:
        from groq import AsyncGroq

        if voice not in VOICE_IDS:
            voice = "tara"

        client = AsyncGroq(api_key=_get_api_key())
        chunks = _chunk_text(text)
        wav_buffers = []

        for chunk in chunks:
            marked = _apply_emotion(chunk, emotion)
            response = await client.audio.speech.create(
                model=MODEL,
                input=marked,
                voice=voice,
                response_format="wav",
            )
            wav_buffers.append(response.content)

        audio = _concatenate_wav(wav_buffers)
        return TTSResult(audio=audio, content_type="audio/wav")
