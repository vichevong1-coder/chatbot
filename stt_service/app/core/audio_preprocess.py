"""Audio preprocessing and format validation for speech-to-text."""

from __future__ import annotations

MAX_AUDIO_BYTES = 10 * 1024 * 1024  # 10 MB limit


class AudioValidationError(Exception):
    pass


def validate_and_inspect_audio(data: bytes, filename: str | None = None) -> dict[str, str | int]:
    """Validate audio header and size, returning metadata."""
    if not data:
        raise AudioValidationError("Empty audio payload")

    if len(data) > MAX_AUDIO_BYTES:
        raise AudioValidationError(f"Audio payload exceeds {MAX_AUDIO_BYTES} bytes")

    # Inspect magic bytes
    if data.startswith(b"\x1a\x45\xdf\xa3"):
        fmt = "webm"
    elif data.startswith(b"RIFF") and b"WAVE" in data[:12]:
        fmt = "wav"
    elif data.startswith(b"OggS"):
        fmt = "ogg"
    elif data.startswith(b"ID3") or data.startswith(b"\xff\xfb"):
        fmt = "mp3"
    else:
        fmt = "wav" if (filename and filename.endswith(".wav")) else "webm"

    return {
        "format": fmt,
        "size_bytes": len(data),
    }
