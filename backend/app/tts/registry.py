"""TTS provider registry — resolves active provider from config/env."""
import os
from pathlib import Path

from backend.app.tts.base import TTSProvider
from backend.app.tts.groq_orpheus import GroqOrpheusProvider
from backend.app.tts.elevenlabs import ElevenLabsProvider
from backend.app.tts.deepgram import DeepgramProvider


_PROVIDERS: dict[str, type[TTSProvider]] = {
    "groq_orpheus": GroqOrpheusProvider,
    "elevenlabs": ElevenLabsProvider,
    "deepgram": DeepgramProvider,
}

# Aliases for config convenience
_ALIASES: dict[str, str] = {
    "orpheus": "groq_orpheus",
    "groq": "groq_orpheus",
    "eleven": "elevenlabs",
    "11labs": "elevenlabs",
    "dg": "deepgram",
}


def _resolve_name(name: str) -> str:
    return _ALIASES.get(name, name)


def _load_tts_config() -> dict:
    """Read tts section from config/settings.yaml if it exists."""
    try:
        import yaml
        settings_path = Path(__file__).resolve().parents[3] / "config" / "settings.yaml"
        if settings_path.exists():
            cfg = yaml.safe_load(settings_path.read_text()) or {}
            tts_cfg = cfg.get("tts", {})
            if isinstance(tts_cfg, dict):
                return tts_cfg
    except Exception:
        pass
    return {}


def _load_config_provider() -> str:
    return _load_tts_config().get("provider", "")


def get_default_voice() -> str:
    """Get configured default voice from settings.yaml."""
    return _load_tts_config().get("voice", "")


def get_active_provider_name() -> str:
    """Determine which provider to use. Priority: env var > config > auto-detect > browser."""
    # 1. Explicit env var
    env = os.environ.get("TTS_PROVIDER", "").strip().lower()
    if env:
        return _resolve_name(env)

    # 2. Config file
    cfg = _load_config_provider().strip().lower()
    if cfg and cfg != "browser" and cfg != "none":
        return _resolve_name(cfg)

    # 3. Auto-detect: first available provider
    for name, cls in _PROVIDERS.items():
        if cls().is_available():
            return name

    # 4. Fallback: browser (frontend handles it)
    return "browser"


def get_provider(name: str | None = None) -> TTSProvider | None:
    """Get a TTS provider instance. Returns None for 'browser' (handled client-side)."""
    if name is None:
        name = get_active_provider_name()
    if name in ("browser", "none"):
        return None
    resolved = _resolve_name(name)
    cls = _PROVIDERS.get(resolved)
    if cls is None:
        return None
    return cls()


def list_providers() -> list[dict]:
    """List all registered providers with availability status."""
    result = [{"id": "browser", "name": "Browser", "available": True, "description": "Built-in browser SpeechSynthesis (no API key needed)"}]
    for name, cls in _PROVIDERS.items():
        inst = cls()
        result.append({
            "id": name,
            "name": inst.name,
            "available": inst.is_available(),
            "description": f"{len(inst.voices())} voices",
        })
    return result
