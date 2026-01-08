# PDF2MD Converter

GPU-accelerated PDF to Markdown conversion engine using the Marker library.

## Overview

This is a Python library module that converts PDF files to Markdown format with:
- **High-quality text extraction** with structure preservation (headings, lists, tables)
- **GPU-accelerated OCR** for scanned PDFs using CUDA
- **Image extraction** with automatic downscaling
- **Multi-language support** (English and Chinese)
- **Comprehensive error handling** for encrypted, corrupted, or invalid PDFs

## Architecture

```
converter/
├── src/pdf2md_converter/
│   ├── __init__.py
│   ├── base.py              # PDFConverter ABC
│   ├── marker_converter.py  # MarkerConverter implementation
│   ├── config.py            # ConverterConfig
│   ├── exceptions.py        # Exception hierarchy
│   ├── models/
│   │   └── metrics.py       # ConversionMetrics
│   ├── utils/
│   │   ├── image_utils.py   # Image processing
│   │   └── pdf_utils.py     # PDF validation
│   └── ocr/
│       └── gpu_checker.py   # GPU availability
└── tests/
    ├── unit/                # Mock GPU, fast tests
    ├── integration/         # Real GPU, slow tests
    └── fixtures/
        └── test_pdfs/       # Sample PDFs
```

## Quick Start

### Installation

```bash
cd converter
uv sync
```

### Basic Usage

```python
from pathlib import Path
from pdf2md_converter import MarkerConverter, ConverterConfig

# Create configuration
config = ConverterConfig(
    gpu_enabled=True,
    gpu_device_id=0,  # Use GPU 0 (or 1 for second GPU)
    max_pages=500
)

# Initialize converter
converter = MarkerConverter(config)

# Convert PDF to Markdown
metrics = converter.convert(
    pdf_path=Path("input.pdf"),
    output_path=Path("output.md")
)

# Check results
print(f"Converted {metrics.pages_processed} pages in {metrics.conversion_time_seconds:.2f}s")
print(f"GPU used: {metrics.gpu_device_id}, Memory: {metrics.gpu_memory_used_mb:.0f}MB")
```

## Configuration

### ConverterConfig Options

```python
from pdf2md_converter import ConverterConfig

config = ConverterConfig(
    # OCR Settings
    ocr_enabled=True,
    ocr_all_pages=True,

    # GPU Settings
    gpu_enabled=True,
    gpu_device_id=0,  # For multi-GPU systems
    gpu_memory_limit_mb=4096,

    # Conversion Limits
    max_pages=500,
    timeout_seconds=300,

    # Image Processing
    extract_images=True,
    image_downscale_threshold=2000,

    # OCR Quality
    ocr_confidence_threshold=0.5,

    # Multi-language
    languages=["en", "zh"]
)
```

## Error Handling

The converter provides specific exceptions for different error scenarios:

```python
from pdf2md_converter.exceptions import (
    GPUUnavailableError,
    PasswordProtectedError,
    CorruptedPDFError,
    GPUOutOfMemoryError,
    PageLimitExceededError,
    ConversionError
)

try:
    metrics = converter.convert(pdf_path, output_path)
except GPUUnavailableError:
    print("GPU not available or CUDA not installed")
except PasswordProtectedError:
    print("PDF is password-protected")
except CorruptedPDFError:
    print("PDF file is corrupted")
except GPUOutOfMemoryError:
    print("GPU ran out of memory")
except ConversionError as e:
    print(f"Conversion failed: {e.message}")
```

## Requirements

### Hardware
- **GPU**: NVIDIA GPU with CUDA 11.8+ support
- **VRAM**: Minimum 4GB (recommended 8GB)
- **RAM**: 8GB system memory minimum (16GB recommended)

### Software
- **Python**: 3.11 or later
- **CUDA**: 11.8 or later
- **Package Manager**: `uv` (NON-NEGOTIABLE)

## Integration with Server

This converter is designed to be imported by the server component (003-server-api):

```python
# In server code
import asyncio
from pdf2md_converter import MarkerConverter, ConverterConfig

async def convert_pdf_async(pdf_path: Path, output_path: Path):
    config = ConverterConfig(gpu_enabled=True)
    converter = MarkerConverter(config)

    # Run blocking conversion in thread pool
    metrics = await asyncio.to_thread(
        converter.convert,
        pdf_path=pdf_path,
        output_path=output_path
    )

    return {
        "pages_processed": metrics.pages_processed,
        "conversion_time": metrics.conversion_time_seconds,
        "gpu_memory_used_mb": metrics.gpu_memory_used_mb
    }
```

## Testing

### Unit Tests (No GPU Required)

```bash
cd converter
uv run pytest tests/unit/ -v
```

### Integration Tests (GPU Required)

```bash
# Run with GPU
uv run pytest tests/integration/ -v

# Run specific test
uv run pytest tests/integration/test_conversion_flow.py::test_scanned_pdf_conversion -v
```

### Test Coverage

```bash
uv run pytest --cov=pdf2md_converter --cov-report=html
```

## Performance Targets

| Metric | Target |
|--------|--------|
| 10-page conversion time | <30 seconds |
| Per-page average | <3 seconds |
| OCR accuracy | >95% |
| GPU memory usage | <4GB |

## License

Part of the PDF2md-CLI project.
