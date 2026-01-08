"""Configuration model for PDF to Markdown conversion engine."""

from pydantic import BaseModel, Field, PositiveInt, field_validator
from pathlib import Path


class ConverterConfig(BaseModel):
    """Configuration for PDF to Markdown conversion engine."""

    # OCR Settings
    ocr_enabled: bool = Field(
        default=True,
        description="Enable OCR for scanned PDFs"
    )
    ocr_all_pages: bool = Field(
        default=True,
        description="Apply OCR to all pages, not just those without text"
    )

    # GPU Settings
    gpu_enabled: bool = Field(
        default=True,
        description="Use GPU acceleration for OCR (CUDA required)"
    )
    gpu_device_id: int = Field(
        default=0,
        ge=0,
        description="GPU device ID to use (for multi-GPU systems, e.g., 0 or 1)"
    )
    gpu_memory_limit_mb: PositiveInt = Field(
        default=4096,
        ge=100,
        le=16384,
        description="Maximum GPU memory in MB (fail if exceeded)"
    )

    # Conversion Limits
    max_pages: PositiveInt = Field(
        default=500,
        ge=1,
        le=1000,
        description="Maximum number of pages to process"
    )
    timeout_seconds: PositiveInt = Field(
        default=300,
        description="Maximum conversion time in seconds"
    )

    # Image Processing
    extract_images: bool = Field(
        default=True,
        description="Extract images from PDF"
    )
    image_downscale_threshold: PositiveInt = Field(
        default=2000,
        ge=100,
        description="Downscale images with width > this value (pixels)"
    )
    image_output_format: str = Field(
        default="original",
        description="Image output format: 'original' (preserve), 'jpeg', 'png'"
    )

    # OCR Quality
    ocr_confidence_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="OCR confidence threshold (below this, add warning annotation)"
    )

    # Multi-language Support
    languages: list[str] = Field(
        default=["en", "zh"],
        description="Supported languages for OCR (ISO 639-1 codes)"
    )

    # Output Options
    output_directory: Path = Field(
        default=Path("/tmp/pdf2md_output"),
        description="Directory for extracted images and Markdown output"
    )

    @field_validator("languages")
    @classmethod
    def validate_languages(cls, v: list[str]) -> list[str]:
        """Validate that languages list is not empty."""
        if not v:
            raise ValueError("languages list cannot be empty")
        return v
