"""Deepgram Aura TTS provider."""
import os

from backend.app.tts.base import TTSProvider, TTSResult


def _get_api_key() -> str:
    key = os.environ.get("DEEPGRAM_API_KEY", "")
    if not key:
        try:
            from scripts.lib.secrets import get_deepgram_key
            key = get_deepgram_key()
        except Exception:
            pass
    return key


class DeepgramProvider(TTSProvider):
    name = "deepgram"

    def is_available(self) -> bool:
        return bool(_get_api_key())

    def voices(self) -> list[dict]:
        return [
            {"id": "aura-asteria-en", "name": "Asteria", "description": "Female, warm, expressive"},
            {"id": "aura-luna-en", "name": "Luna", "description": "Female, soft, gentle"},
            {"id": "aura-stella-en", "name": "Stella", "description": "Female, bright, clear"},
            {"id": "aura-athena-en", "name": "Athena", "description": "Female, professional"},
            {"id": "aura-hera-en", "name": "Hera", "description": "Female, authoritative"},
            {"id": "aura-orion-en", "name": "Orion", "description": "Male, deep, clear"},
            {"id": "aura-arcas-en", "name": "Arcas", "description": "Male, warm, conversational"},
            {"id": "aura-perseus-en", "name": "Perseus", "description": "Male, confident"},
        ]

    async def synthesize(self, text: str, voice: str = "aura-asteria-en", emotion: str = "") -> TTSResult:
        import httpx

        api_key = _get_api_key()
        url = f"https://api.deepgram.com/v1/speak?model={voice}&encoding=mp3"

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                headers={
                    "Authorization": f"Token {api_key}",
                    "Content-Type": "application/json",
                },
                json={"text": text},
                timeout=30,
            )
            resp.raise_for_status()

        return TTSResult(audio=resp.content, content_type="audio/mpeg")
