"""Image processing utilities for downscaling."""

import logging
from pathlib import Path
from PIL import Image

logger = logging.getLogger(__name__)


def downscale_image(
    image_path: Path,
    output_path: Path,
    max_width: int,
) -> bool:
    """
    Downscale image if its width exceeds max_width while preserving aspect ratio.

    Args:
        image_path: Path to input image
        output_path: Path to save downscaled image
        max_width: Maximum width in pixels (downscale if width > max_width)

    Returns:
        True if image was downscaled, False if no downscaling needed

    Raises:
        FileNotFoundError: If input image does not exist
        ValueError: If image file is invalid or cannot be read
    """
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    try:
        with Image.open(image_path) as img:
            width, height = img.size

            # Check if downscaling is needed
            if width <= max_width:
                # No downscaling needed, just copy if paths differ
                if image_path != output_path:
                    img.save(output_path)
                return False

            # Calculate new dimensions preserving aspect ratio
            aspect_ratio = height / width
            new_width = max_width
            new_height = int(new_width * aspect_ratio)

            # Downscale using LANCZOS resampling filter (high quality)
            downscaled = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Save downscaled image
            # Preserve original format
            output_format = img.format or "PNG"
            downscaled.save(output_path, format=output_format)

            logger.info(
                f"Downscaled image: {width}x{height} -> {new_width}x{new_height} "
                f"({image_path} -> {output_path})"
            )

            return True

    except Exception as e:
        logger.error(f"Failed to downscale image {image_path}: {e}")
        raise ValueError(f"Invalid or corrupted image file: {e}")
