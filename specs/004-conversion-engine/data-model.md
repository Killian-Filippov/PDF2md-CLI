# Data Model: PDF Conversion Engine

**Feature**: 004-conversion-engine
**Date**: 2026-01-08
**Status**: Draft

## Overview

This document defines the data entities used in the PDF to Markdown conversion engine. The engine is structured as a library module with abstract base classes and Pydantic models for configuration and metrics.

---

## Core Entities

### 1. ConverterConfig (Pydantic Model)

**Purpose**: Configuration settings for the conversion engine.

**Fields**:
```python
from pydantic import BaseModel, Field, PositiveInt
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
    gpu_memory_limit_mb: PositiveInt = Field(
        default=4096,
        description="Maximum GPU memory in MB (fail if exceeded)"
    )

    # Conversion Limits
    max_pages: PositiveInt = Field(
        default=500,
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
```

**Validation Rules**:
- `gpu_enabled=True` requires GPU available at startup (raises `GPUUnavailableError`)
- `max_pages` must be <= 1000 (hard limit)
- `ocr_confidence_threshold` must be between 0.0 and 1.0
- `image_downscale_threshold` must be >= 100 (minimum practical size)

---

### 2. ConversionMetrics (Dataclass)

**Purpose**: Performance metrics collected during conversion.

**Fields**:
```python
from dataclasses import dataclass
from time import time

@dataclass
class ConversionMetrics:
    """Performance metrics for PDF conversion."""

    # Conversion Results
    pages_processed: int
    pages_with_ocr: int
    images_extracted: int
    tables_detected: int

    # Timing
    start_time: float
    end_time: float
    conversion_time_seconds: float
    ocr_time_seconds: float

    # Resource Usage
    gpu_memory_used_mb: float
    peak_gpu_memory_mb: float
    cpu_time_seconds: float

    # Output
    output_size_bytes: int
    output_path: str

    # Errors
    low_confidence_pages: list[int]  # Page numbers with OCR confidence < threshold
    errors: list[str]  # Non-fatal errors encountered

    @property
    def elapsed_time(self) -> float:
        """Total elapsed time in seconds."""
        return self.end_time - self.start_time

    @property
    def pages_per_second(self) -> float:
        """Conversion throughput (pages per second)."""
        return self.pages_processed / self.conversion_time_seconds if self.conversion_time_seconds > 0 else 0.0
```

**Validation Rules**:
- `end_time` must be >= `start_time`
- `pages_processed` must be >= 0
- `gpu_memory_used_mb` must be >= 0 (0 if GPU not used)

---

### 3. ExtractionResult (Dataclass)

**Purpose**: Structured extraction data from PDF.

**Fields**:
```python
from typing import Optional
from pathlib import Path

@dataclass
class ExtractionResult:
    """Structured extraction result from PDF."""

    # Text Content
    text_blocks: list[str]  # Extracted text blocks by reading order
    headings: list[tuple[int, str]]  # (level, text) tuples for heading hierarchy
    lists: list[list[str]]  # Bullet and numbered lists

    # Rich Content
    tables: list[str]  # Markdown table representations
    images: list[tuple[Path, str]]  # (image_path, markdown_reference) tuples
    links: list[tuple[str, str]]  # (text, url) tuples

    # Metadata
    page_count: int
    has_text_layer: bool
    languages_detected: list[str]

    # Quality
    ocr_confidence_scores: dict[int, float]  # Page number -> confidence score

    @property
    def has_low_confidence_pages(self) -> bool:
        """Check if any pages have low OCR confidence."""
        return any(score < 0.5 for score in self.ocr_confidence_scores.values())

    @property
    def low_confidence_page_numbers(self) -> list[int]:
        """Get list of page numbers with low OCR confidence."""
        return [page for page, score in self.ocr_confidence_scores.items() if score < 0.5]
```

**State Transitions**:
1. **Initial** → **Extracting**: PDF parsing started
2. **Extracting** → **OCR Processing**: OCR applied to pages without text
3. **OCR Processing** → **Complete**: All text extracted and formatted
4. **Any** → **Error**: Conversion failed (raise exception)

---

### 4. PDFConverter (Abstract Base Class)

**Purpose**: Abstract interface for converter implementations.

**Methods**:
```python
from abc import ABC, abstractmethod
from pathlib import Path

class PDFConverter(ABC):
    """Abstract base class for PDF to Markdown converters."""

    def __init__(self, config: ConverterConfig) -> None:
        """Initialize converter with configuration."""
        self.config = config
        self._validate_gpu_availability()

    @abstractmethod
    def convert(self, pdf_path: Path, output_path: Path) -> ConversionMetrics:
        """
        Convert PDF to Markdown.

        Args:
            pdf_path: Path to input PDF file
            output_path: Path to output Markdown file

        Returns:
            ConversionMetrics with performance data

        Raises:
            GPUUnavailableError: GPU required but not available
            PasswordProtectedError: PDF is password-protected
            CorruptedPDFError: PDF file is corrupted
            ConversionError: General conversion error
        """
        pass

    def _validate_gpu_availability(self) -> None:
        """Validate GPU availability if gpu_enabled=True."""
        if self.config.gpu_enabled:
            from .ocr.gpu_checker import check_gpu_available
            if not check_gpu_available():
                raise GPUUnavailableError("GPU required but not available")

    @abstractmethod
    def _validate_inputs(self, pdf_path: Path, output_path: Path) -> None:
        """Validate input PDF and output path."""
        pass

    @abstractmethod
    def _cleanup(self, pdf_path: Path, output_path: Path) -> None:
        """Clean up temporary files on error or success."""
        pass
```

**Implementation**: `MarkerConverter` extends this abstract base class.

---

## Entity Relationships

```
ConverterConfig
      ↓
      │ (configuration injection)
      ↓
PDFConverter (ABC)
      ↓
      │ (extends)
      ↓
MarkerConverter
      │
      ├─→ ConversionMetrics (returns)
      ├─→ ExtractionResult (internal)
      └─→ ConversionError (raises on error)
```

---

## Data Flow

1. **Configuration**: `ConverterConfig` created with settings
2. **Instantiation**: `MarkerConverter` initialized with config
3. **Validation**: GPU availability checked (if `gpu_enabled=True`)
4. **Conversion**: `convert()` method called with PDF and output paths
5. **Extraction**: `ExtractionResult` generated with structured data
6. **Metrics**: `ConversionMetrics` returned with performance data
7. **Error**: Any exception raised includes cleanup via `_cleanup()`

---

## Type Hints Compliance

All entities include full type hints per Constitution Principle IV:
- Pydantic models: `BaseModel` with `Field()` types
- Dataclasses: `@dataclass` with type annotations
- Methods: Full parameter and return type hints
- Optional types: `Optional[T]` for nullable fields

---

## Validation Summary

| Entity | Validation Mechanism | Key Constraints |
|--------|---------------------|-----------------|
| ConverterConfig | Pydantic Field validators | GPU check, max pages, confidence range |
| ConversionMetrics | Dataclass properties | Time ordering, non-negative values |
| ExtractionResult | Dataclass properties | Confidence score range |
| PDFConverter | Abstract methods | Method signatures, error types |

---

## Next Steps

- Implement `MarkerConverter` class extending `PDFConverter`
- Create exception hierarchy in `converter/src/pdf2md_converter/exceptions.py`
- Implement GPU checker in `converter/src/pdf2md_converter/ocr/gpu_checker.py`
- Add type hints to all methods (mypy strict mode)
