"""Base class for TTS providers."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TTSResult:
    audio: bytes
    content_type: str  # e.g. "audio/wav", "audio/mpeg"
    sample_rate: int | None = None


class TTSProvider(ABC):
    """Abstract TTS provider interface."""

    name: str = "base"

    @abstractmethod
    async def synthesize(self, text: str, voice: str = "", emotion: str = "") -> TTSResult:
        """Generate speech audio from text."""

    @abstractmethod
    def voices(self) -> list[dict]:
        """Return list of available voices with id, name, description."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is configured and ready."""

    def emotions(self) -> list[str]:
        """Return supported emotion tags. Empty list if unsupported."""
        return []
