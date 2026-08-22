"""Image preprocessing, validation, and normalization for OCR service."""

from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image, ImageOps

MAX_IMAGE_BYTES = 15 * 1024 * 1024  # 15 MB limit
MIN_DIMENSION = 10
MAX_DIMENSION = 8192
MAX_NORMALIZED_DIMENSION = 2048

SUPPORTED_FORMATS = frozenset({"JPEG", "JPG", "PNG", "WEBP"})


class ImageValidationError(Exception):
    """Raised when an uploaded image fails validation."""


@dataclass
class PreprocessedImage:
    image_bytes: bytes
    format: str
    width: int
    height: int
    size_bytes: int
    mime_type: str


def validate_and_preprocess_image(
    data: bytes,
    filename: str | None = None,
    max_size: int = MAX_IMAGE_BYTES,
) -> PreprocessedImage:
    """Validate format and dimensions, handle EXIF orientation, and normalize to RGB JPEG."""
    if not data:
        raise ImageValidationError("Empty image payload")

    if len(data) > max_size:
        raise ImageValidationError(f"Image payload exceeds maximum allowed size of {max_size} bytes")

    try:
        image = Image.open(io.BytesIO(data))
    except Exception as exc:
        raise ImageValidationError(f"Invalid or corrupted image: {str(exc)}") from exc

    raw_format = (image.format or "").upper()
    if raw_format not in SUPPORTED_FORMATS:
        raise ImageValidationError(
            f"Unsupported image format: {raw_format or 'unknown'}. Supported formats: JPEG, PNG, WebP"
        )

    # Apply EXIF rotation if present
    try:
        image = ImageOps.exif_transpose(image) or image
    except Exception:
        pass

    width, height = image.size
    if width < MIN_DIMENSION or height < MIN_DIMENSION:
        raise ImageValidationError(
            f"Image dimensions too small ({width}x{height}). Minimum is {MIN_DIMENSION}x{MIN_DIMENSION}."
        )

    if width > MAX_DIMENSION or height > MAX_DIMENSION:
        raise ImageValidationError(
            f"Image dimensions too large ({width}x{height}). Maximum is {MAX_DIMENSION}x{MAX_DIMENSION}."
        )

    # Downscale large images while preserving aspect ratio
    if max(width, height) > MAX_NORMALIZED_DIMENSION:
        image.thumbnail((MAX_NORMALIZED_DIMENSION, MAX_NORMALIZED_DIMENSION), Image.Resampling.LANCZOS)
        width, height = image.size

    # Convert mode to RGB (compositing alpha onto white background)
    if image.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode == "P":
            image = image.convert("RGBA")
        background.paste(image, mask=image.split()[-1] if "A" in image.getbands() else None)
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")

    output_buffer = io.BytesIO()
    image.save(output_buffer, format="JPEG", quality=90, optimize=True)
    normalized_bytes = output_buffer.getvalue()

    return PreprocessedImage(
        image_bytes=normalized_bytes,
        format="jpeg",
        width=width,
        height=height,
        size_bytes=len(normalized_bytes),
        mime_type="image/jpeg",
    )
