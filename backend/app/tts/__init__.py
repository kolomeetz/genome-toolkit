"""TTS provider system — pluggable text-to-speech with fallback to browser synthesis."""

from backend.app.tts.base import TTSProvider, TTSResult
from backend.app.tts.registry import get_provider, list_providers, get_active_provider_name, get_default_voice

__all__ = ["TTSProvider", "TTSResult", "get_provider", "list_providers", "get_active_provider_name", "get_default_voice"]
