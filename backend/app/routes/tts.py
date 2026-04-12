"""TTS endpoint — multi-provider text-to-speech with browser fallback."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from backend.app.tts import get_provider, list_providers, get_active_provider_name, get_default_voice

router = APIRouter(prefix="/api")


class TTSRequest(BaseModel):
    text: str
    voice: str = ""
    emotion: str = ""
    provider: str = ""  # override active provider for this request


@router.post("/tts")
async def text_to_speech(req: TTSRequest):
    """Generate speech audio from text.

    Uses the configured provider (env TTS_PROVIDER, config, or auto-detect).
    Returns audio bytes. If provider is 'browser', returns 204 (frontend handles it).
    """
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text is required")

    provider_name = req.provider or None
    provider = get_provider(provider_name)

    if provider is None:
        # 'browser' mode — tell frontend to use SpeechSynthesis
        return Response(status_code=204)

    if not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail=f"TTS provider '{provider.name}' not configured. Set the appropriate API key.",
        )

    voice = req.voice or get_default_voice()
    try:
        result = await provider.synthesize(
            text=req.text,
            voice=voice,
            emotion=req.emotion,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {e}")

    return Response(
        content=result.audio,
        media_type=result.content_type,
        headers={"Content-Disposition": "inline"},
    )


@router.get("/tts/voices")
async def get_voices():
    """List voices for the active provider."""
    provider = get_provider()
    if provider is None:
        return {"provider": "browser", "voices": [], "emotions": [], "note": "Using browser SpeechSynthesis"}

    voices = provider.voices()
    emotions = provider.emotions()
    return {
        "provider": provider.name,
        "voices": voices,
        "emotions": emotions,
    }


@router.get("/tts/providers")
async def get_providers():
    """List all available TTS providers and which is active."""
    return {
        "active": get_active_provider_name(),
        "providers": list_providers(),
    }
