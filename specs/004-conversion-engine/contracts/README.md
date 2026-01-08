# Internal API Contracts: PDF Conversion Engine

**Feature**: 004-conversion-engine
**Date**: 2026-01-08
**Status**: Draft

## Overview

The PDF conversion engine is a **library module** (not a standalone service), designed to be imported by the server component (003-server-api). This document defines the internal API contracts for converter implementations.

---

## Abstract Base Class Interface

### PDFConverter

**Package**: `pdf2md_converter.base`

**Purpose**: Abstract interface for all PDF to Markdown converter implementations.

#### Method Signature

```python
from abc import ABC, abstractmethod
from pathlib import Path
from pdf2md_converter.config import ConverterConfig
from pdf2md_converter.models.metrics import ConversionMetrics

class PDFConverter(ABC):
    """Abstract base class for PDF to Markdown converters."""

    @abstractmethod
    def __init__(self, config: ConverterConfig) -> None:
        """
        Initialize converter with configuration.

        Args:
            config: Converter configuration settings

        Raises:
            GPUUnavailableError: If config.gpu_enabled=True and GPU not available
        """
        pass

    @abstractmethod
    def convert(self, pdf_path: Path, output_path: Path) -> ConversionMetrics:
        """
        Convert PDF to Markdown.

        This is the primary conversion method. It:
        1. Validates inputs (PDF exists, output path writable)
        2. Extracts text structure (headings, lists, tables)
        3. Applies OCR if enabled (GPU-accelerated)
        4. Extracts and downcales images
        5. Writes Markdown to output_path
        6. Returns performance metrics

        Args:
            pdf_path: Path to input PDF file (must exist)
            output_path: Path to output Markdown file (parent must exist)

        Returns:
            ConversionMetrics with performance data:
                - pages_processed: Number of pages converted
                - conversion_time_seconds: Total conversion time
                - gpu_memory_used_mb: GPU memory consumed (0 if GPU not used)
                - images_extracted: Number of images extracted
                - low_confidence_pages: List of page numbers with OCR confidence < threshold

        Raises:
            GPUUnavailableError: GPU required but not available
            PasswordProtectedError: PDF is password-protected (reject immediately)
            CorruptedPDFError: PDF file structure is corrupted
            ConversionError: General conversion error with details

        Example:
            ```python
            from pathlib import Path
            from pdf2md_converter.marker_converter import MarkerConverter
            from pdf2md_converter.config import ConverterConfig

            config = ConverterConfig(gpu_enabled=True)
            converter = MarkerConverter(config)
            metrics = converter.convert(
                pdf_path=Path("input.pdf"),
                output_path=Path("output.md")
            )
            print(f"Converted {metrics.pages_processed} pages in {metrics.conversion_time_seconds:.2f}s")
            ```
        """
        pass
```

---

## MarkerConverter Implementation

### Public API

**Package**: `pdf2md_converter.marker_converter`

**Extends**: `PDFConverter`

#### Additional Methods (Internal)

```python
class MarkerConverter(PDFConverter):
    """Concrete implementation using Marker library."""

    def _validate_inputs(self, pdf_path: Path, output_path: Path) -> None:
        """
        Validate input PDF and output path.

        Checks:
        - PDF file exists
        - PDF file is readable
        - Output directory exists and is writable
        - PDF is not password-protected (fast fail)
        - PDF page count <= max_pages

        Raises:
            FileNotFoundError: PDF file does not exist
            PermissionError: Output directory not writable
            PasswordProtectedError: PDF is encrypted
            ValueError: Page count exceeds max_pages
        """
        pass

    def _apply_ocr(self, pdf_path: Path, output_dir: Path) -> dict[int, float]:
        """
        Apply OCR to PDF and return confidence scores per page.

        Args:
            pdf_path: Path to input PDF
            output_dir: Directory for OCR outputs

        Returns:
            Dictionary mapping page_number -> confidence_score (0.0 to 1.0)

        Raises:
            GPUUnavailableError: GPU required but not available
            ConversionError: OCR processing failed

        Note:
            If GPU runs out of memory, raises ConversionError immediately
            (no CPU fallback per clarification).
        """
        pass

    def _extract_images(self, pdf_path: Path, output_dir: Path) -> list[tuple[Path, str]]:
        """
        Extract images from PDF and downscale if needed.

        Args:
            pdf_path: Path to input PDF
            output_dir: Directory for extracted images

        Returns:
            List of (image_path, markdown_reference) tuples

        Note:
            Images with width > config.image_downscale_threshold are
            downscaled to max threshold width (aspect ratio preserved).
        """
        pass

    def _cleanup(self, pdf_path: Path, output_path: Path) -> None:
        """
        Clean up temporary files.

        Args:
            pdf_path: Input PDF path (not deleted, only referenced)
            output_path: Output Markdown path (deleted on error)

        Note:
            Called on both success and error paths to ensure
            no partial files remain on disk.
        """
        pass
```

---

## Exception Hierarchy

### Base Exception

```python
class ConversionError(Exception):
    """Base exception for all conversion errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        """
        Initialize conversion error.

        Args:
            message: Human-readable error message
            details: Optional dict with additional error context
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
```

### Specific Exceptions

```python
class GPUUnavailableError(ConversionError):
    """GPU required but not available or CUDA not installed."""

    def __init__(self, message: str = "GPU required but not available") -> None:
        super().__init__(message, {"error_code": "GPU_UNAVAILABLE"})


class PasswordProtectedError(ConversionError):
    """PDF is password-protected and cannot be converted."""

    def __init__(self, message: str = "PDF is password-protected") -> None:
        super().__init__(message, {"error_code": "PASSWORD_PROTECTED"})


class CorruptedPDFError(ConversionError):
    """PDF file structure is corrupted or invalid."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message, {"error_code": "CORRUPTED_PDF", **(details or {})})


class GPUOutOfMemoryError(ConversionError):
    """GPU ran out of memory during conversion."""

    def __init__(self, message: str = "GPU out of memory") -> None:
        super().__init__(message, {"error_code": "GPU_OOM"})


class PageLimitExceededError(ConversionError):
    """PDF page count exceeds maximum allowed."""

    def __init__(self, page_count: int, max_pages: int) -> None:
        message = f"PDF has {page_count} pages, exceeds maximum of {max_pages}"
        super().__init__(message, {"error_code": "PAGE_LIMIT_EXCEEDED", "page_count": page_count, "max_pages": max_pages})
```

---

## Error Codes Reference

| Error Code | Exception | HTTP Equivalent (Server Layer) | Troubleshooting |
|------------|-----------|-------------------------------|-----------------|
| GPU_UNAVAILABLE | GPUUnavailableError | 503 Service Unavailable | Install NVIDIA GPU and CUDA 11.8+ |
| PASSWORD_PROTECTED | PasswordProtectedError | 400 Bad Request | Remove password protection using pdftk |
| CORRUPTED_PDF | CorruptedPDFError | 400 Bad Request | Verify PDF file integrity |
| GPU_OOM | GPUOutOfMemoryError | 503 Service Unavailable | Retry later or reduce concurrent conversions |
| PAGE_LIMIT_EXCEEDED | PageLimitExceededError | 400 Bad Request | Split PDF into smaller files |
| CONVERSION_ERROR | ConversionError | 500 Internal Server Error | Check logs for details |

---

## Configuration Schema

### ConverterConfig Validation

```python
from pdf2md_converter.config import ConverterConfig
from pydantic import ValidationError

# Valid configuration
config = ConverterConfig(
    gpu_enabled=True,
    max_pages=100,
    ocr_confidence_threshold=0.6
)

# Invalid configuration (raises ValidationError)
try:
    config = ConverterConfig(
        gpu_enabled=True,
        ocr_confidence_threshold=1.5  # Must be <= 1.0
    )
except ValidationError as e:
    print(f"Validation error: {e}")
```

### Validation Rules

| Field | Type | Constraints | Default |
|-------|------|-------------|---------|
| ocr_enabled | bool | - | True |
| ocr_all_pages | bool | - | True |
| gpu_enabled | bool | Requires GPU available if True | True |
| gpu_device_id | int | >= 0, valid device ID | 0 |
| gpu_memory_limit_mb | int | >= 100, <= 16384 | 4096 |
| max_pages | int | >= 1, <= 1000 | 500 |
| timeout_seconds | int | >= 1, <= 3600 | 300 |
| extract_images | bool | - | True |
| image_downscale_threshold | int | >= 100, <= 10000 | 2000 |
| ocr_confidence_threshold | float | 0.0 to 1.0 | 0.5 |
| languages | list[str] | Non-empty, valid ISO 639-1 codes | ["en", "zh"] |

---

## Server Integration Contract

### Expected Usage by Server (003-server-api)

```python
# In server code (003-server-api)
from pathlib import Path
from pdf2md_converter.marker_converter import MarkerConverter
from pdf2md_converter.config import ConverterConfig
from pdf2md_converter.exceptions import ConversionError, GPUUnavailableError

async def convert_pdf(pdf_path: Path, output_path: Path) -> None:
    """
    Convert PDF to Markdown (async wrapper for server).

    This server-level function wraps the synchronous converter
    in asyncio.to_thread() for non-blocking execution.

    Raises:
        ConversionError: Propagated from converter
        GPUUnavailableError: Propagated from converter
    """
    config = ConverterConfig(gpu_enabled=True)
    converter = MarkerConverter(config)

    try:
        # Run blocking conversion in thread pool
        metrics = await asyncio.to_thread(
            converter.convert,
            pdf_path=pdf_path,
            output_path=output_path
        )
        logger.info(f"Converted {metrics.pages_processed} pages in {metrics.conversion_time_seconds:.2f}s")
    except (GPUUnavailableError, ConversionError) as e:
        # Re-raise for server layer to handle
        raise
```

### Exception Propagation

Converter exceptions propagate directly to server layer:
- Server converts to HTTP status codes (400, 500, 503)
- Server adds request ID and logs error
- Server returns structured error response to client

---

## Testing Contract

### Unit Test Requirements

```python
import pytest
from pdf2md_converter.marker_converter import MarkerConverter
from pdf2md_converter.config import ConverterConfig
from pdf2md_converter.exceptions import GPUUnavailableError, PasswordProtectedError

def test_converter_raises_on_gpu_unavailable(monkeypatch):
    """Test converter raises GPUUnavailableError when GPU not available."""
    # Mock GPU check to return False
    def mock_check_gpu():
        return False
    monkeypatch.setattr("pdf2md_converter.ocr.gpu_checker.check_gpu_available", mock_check_gpu)

    config = ConverterConfig(gpu_enabled=True)
    with pytest.raises(GPUUnavailableError):
        converter = MarkerConverter(config)

def test_converter_rejects_password_protected_pdf():
    """Test converter raises PasswordProtectedError for encrypted PDFs."""
    config = ConverterConfig(gpu_enabled=False)  # Skip GPU check
    converter = MarkerConverter(config)

    with pytest.raises(PasswordProtectedError):
        converter.convert(
            pdf_path=Path("tests/fixtures/test_pdfs/encrypted.pdf"),
            output_path=Path("output.md")
        )
```

### Integration Test Requirements

```python
@pytest.mark.skipif(not GPU_AVAILABLE, reason="GPU not available")
def test_conversion_with_real_gpu():
    """Test end-to-end conversion with real GPU hardware."""
    config = ConverterConfig(gpu_enabled=True, max_pages=10)
    converter = MarkerConverter(config)

    metrics = converter.convert(
        pdf_path=Path("tests/fixtures/test_pdfs/scanned.pdf"),
        output_path=Path("output.md")
    )

    assert metrics.pages_processed == 10
    assert metrics.conversion_time_seconds < 30
    assert metrics.pages_with_ocr > 0
    assert Path("output.md").exists()
```

---

## Versioning

**Current Version**: 1.0.0

**Compatibility Policy**:
- Minor version updates (1.x): Backward-compatible feature additions
- Patch version updates (1.x.y): Bug fixes only
- Major version updates (2.0.0): Breaking changes (update server integration)

---

## Performance Contract

### Expected Performance (Per FR-CONV Requirements)

| Metric | Target | Test Condition |
|--------|--------|----------------|
| 10-page conversion time | <30 seconds | Standard text PDF |
| Per-page average | <3 seconds | Mixed text/scanned |
| OCR accuracy | >95% | Clear scanned documents |
| GPU memory usage | <4GB | Typical conversions |
| Memory leak | None | After 100 consecutive conversions |

### Performance Monitoring

```python
metrics = converter.convert(pdf_path, output_path)

# Log performance metrics
logger.info(f"Conversion completed:")
logger.info(f"  Pages: {metrics.pages_processed}")
logger.info(f"  Time: {metrics.conversion_time_seconds:.2f}s")
logger.info(f"  Throughput: {metrics.pages_per_second:.2f} pages/sec")
logger.info(f"  GPU memory: {metrics.gpu_memory_used_mb:.0f}MB")
```

---

## Next Steps

- Implement `MarkerConverter` class
- Create exception hierarchy in `converter/src/pdf2md_converter/exceptions.py`
- Add comprehensive unit tests
- Add integration tests with real GPU hardware
- Document performance benchmarks
