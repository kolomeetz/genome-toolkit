"""ElevenLabs TTS provider."""
import os

from backend.app.tts.base import TTSProvider, TTSResult


def _get_api_key() -> str:
    key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not key:
        try:
            from scripts.lib.secrets import get_elevenlabs_key
            key = get_elevenlabs_key()
        except Exception:
            pass
    return key


class ElevenLabsProvider(TTSProvider):
    name = "elevenlabs"

    def is_available(self) -> bool:
        return bool(_get_api_key())

    def voices(self) -> list[dict]:
        return [
            {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "description": "Female, calm, narration"},
            {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Sarah", "description": "Female, soft, news"},
            {"id": "ErXwobaYiN019PkySvjV", "name": "Antoni", "description": "Male, warm, narration"},
            {"id": "VR6AewLTigWG4xSOukaG", "name": "Arnold", "description": "Male, deep, narration"},
            {"id": "pNInz6obpgDQGcFmaJgB", "name": "Adam", "description": "Male, deep, clear"},
        ]

    async def synthesize(self, text: str, voice: str = "21m00Tcm4TlvDq8ikWAM", emotion: str = "") -> TTSResult:
        import httpx

        api_key = _get_api_key()
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                headers={"xi-api-key": api_key, "Content-Type": "application/json"},
                json={
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                },
                timeout=30,
            )
            resp.raise_for_status()

        return TTSResult(audio=resp.content, content_type="audio/mpeg")
