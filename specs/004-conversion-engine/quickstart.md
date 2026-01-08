# Quickstart Guide: PDF Conversion Engine

**Feature**: 004-conversion-engine
**Date**: 2026-01-08
**Audience**: Developers implementing the conversion engine

---

## Overview

The PDF conversion engine is a **Python library module** that converts PDF files to Markdown format using the Marker library with GPU-accelerated OCR. It's designed to be imported by the server component (003-server-api) and provides a clean API for single-conversion operations.

---

## Prerequisites

### Hardware Requirements

**Required**:
- **GPU**: NVIDIA GPU with CUDA 11.8+ support
- **VRAM**: Minimum 4GB GPU memory (recommended 8GB)
- **RAM**: 8GB system memory minimum (16GB recommended)
- **Disk**: 2GB free space for temporary conversion artifacts

**Supported GPUs**: Any NVIDIA GPU with Compute Capability 5.0+ (Maxwell, Pascal, Volta, Ampere, Hopper)

### Software Requirements

**Required**:
- **Operating System**: Ubuntu 22.04 LTS (other Linux distributions may work)
- **Python**: 3.11 or later
- **CUDA Toolkit**: 11.8 or later
- **Package Manager**: `uv` (NON-NEGOTIABLE per project constitution)

**Verified Dependencies**:
```toml
marker-pdf = ">=0.2.8"
torch = ">=2.0.0"  # CUDA 11.8 version
Pillow = ">=10.0.0"
pydantic = ">=2.0.0"
pikepdf = ">=8.0.0"  # For PDF encryption detection
```

---

## Installation

### Step 1: Clone Repository and Switch Branch

```bash
git clone https://github.com/Killian-Filippov/PDF2md-CLI.git
cd PDF2md-CLI
git checkout 004-conversion-engine
```

### Step 2: Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Step 3: Install Dependencies

```bash
cd converter
uv sync
```

This creates a virtual environment in `.venv/` and installs all dependencies from `pyproject.toml`.

### Step 4: Verify GPU Availability

```bash
uv run python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

Expected output: `CUDA available: True`

If `False`, install CUDA Toolkit 11.8+:
```bash
# Ubuntu 22.04
wget https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_520.61.05_linux.run
sudo sh cuda_11.8.0_520.61.05_linux.run --toolkit --silent --override
```

---

## Basic Usage

### Simple Conversion

```python
from pathlib import Path
from pdf2md_converter.marker_converter import MarkerConverter
from pdf2md_converter.config import ConverterConfig

# Create configuration with defaults
config = ConverterConfig(gpu_enabled=True)

# Initialize converter
converter = MarkerConverter(config)

# Convert PDF to Markdown
metrics = converter.convert(
    pdf_path=Path("input.pdf"),
    output_path=Path("output.md")
)

# Print metrics
print(f"Converted {metrics.pages_processed} pages in {metrics.conversion_time_seconds:.2f}s")
print(f"OCR applied to {metrics.pages_with_ocr} pages")
print(f"Extracted {metrics.images_extracted} images")
```

### Custom Configuration

```python
config = ConverterConfig(
    gpu_enabled=True,
    ocr_all_pages=True,  # Apply OCR to all pages, not just scanned
    max_pages=100,  # Limit to 100 pages
    ocr_confidence_threshold=0.7,  # Stricter OCR quality requirement
    image_downscale_threshold=3000,  # Downscale images >3000px width
    extract_images=True,
    timeout_seconds=600  # 10 minute timeout
)

converter = MarkerConverter(config)
metrics = converter.convert(Path("large.pdf"), Path("large.md"))
```

### Disable GPU (for testing)

```python
# Note: This will raise GPUUnavailableError if GPU is required but unavailable
config = ConverterConfig(gpu_enabled=False)
converter = MarkerConverter(config)
```

---

## Running Tests

### Unit Tests (No GPU Required)

```bash
cd converter
uv run pytest tests/unit/ -v
```

Expected output: All tests pass (GPU functions are mocked)

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

Coverage report generated at `htmlcov/index.html`.

---

## Development Workflow

### Project Structure

```
converter/
├── src/
│   └── pdf2md_converter/
│       ├── __init__.py
│       ├── base.py              # PDFConverter ABC
│       ├── marker_converter.py  # MarkerConverter implementation
│       ├── config.py            # ConverterConfig
│       ├── exceptions.py        # Exception hierarchy
│       ├── models/
│       │   └── metrics.py       # ConversionMetrics
│       ├── utils/
│       │   ├── image_utils.py   # Image processing
│       │   └── pdf_utils.py     # PDF validation
│       └── ocr/
│           └── gpu_checker.py   # GPU availability
│
├── tests/
│   ├── unit/                   # Mock GPU, fast tests
│   ├── integration/            # Real GPU, slow tests
│   └── fixtures/
│       └── test_pdfs/          # Sample PDFs
│
├── pyproject.toml
└── README.md
```

### Adding New Features

1. **Update spec.md**: Add functional requirements
2. **Update data-model.md**: Add new entities or fields
3. **Implement feature**: Add code in `src/pdf2md_converter/`
4. **Add tests**: Unit tests in `tests/unit/`, integration tests in `tests/integration/`
5. **Update documentation**: Edit this quickstart guide if API changes

### Code Quality Checks

```bash
# Type checking
uv run mypy src/pdf2md_converter

# Linting
uv run ruff check src/pdf2md_converter

# Formatting
uv run ruff format src/pdf2md_converter

# Run all checks
uv run mypy src/ && uv run ruff check src/ && uv run pytest tests/unit/
```

---

## Configuration Options

### Full Reference

```python
from pdf2md_converter.config import ConverterConfig

config = ConverterConfig(
    # OCR Settings
    ocr_enabled=True,                      # Enable OCR for scanned pages
    ocr_all_pages=True,                    # Apply OCR to all pages
    ocr_confidence_threshold=0.5,          # Low confidence threshold (0.0-1.0)

    # GPU Settings
    gpu_enabled=True,                      # Use GPU acceleration (required)
    gpu_memory_limit_mb=4096,              # Max GPU memory (fail if exceeded)

    # Conversion Limits
    max_pages=500,                         # Max pages to process
    timeout_seconds=300,                   # Max conversion time (5 minutes)

    # Image Processing
    extract_images=True,                   # Extract images from PDF
    image_downscale_threshold=2000,        # Downscale width >2000px
    image_output_format="original",        # Preserve original format

    # Multi-language Support
    languages=["en", "zh"],                # Supported languages (ISO 639-1)

    # Output Options
    output_directory=Path("/tmp/pdf2md_output")  # Output directory
)
```

---

## Error Handling

### Exception Hierarchy

```python
from pdf2md_converter.exceptions import (
    ConversionError,            # Base exception
    GPUUnavailableError,        # GPU not available
    PasswordProtectedError,     # PDF is encrypted
    CorruptedPDFError,          # PDF file corrupted
    GPUOutOfMemoryError,        # GPU OOM during conversion
    PageLimitExceededError      # Too many pages
)

try:
    metrics = converter.convert(pdf_path, output_path)
except GPUUnavailableError as e:
    print(f"GPU error: {e.message}")
    # Troubleshooting: Install CUDA 11.8+ and verify NVIDIA GPU
except PasswordProtectedError as e:
    print(f"PDF is encrypted: {e.message}")
    # Troubleshooting: Remove password with pdftk
except CorruptedPDFError as e:
    print(f"PDF corrupted: {e.message}")
    # Troubleshooting: Verify PDF file integrity
except ConversionError as e:
    print(f"Conversion failed: {e.message}")
    # Troubleshooting: Check logs for details
```

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `GPUUnavailableError` | GPU not detected or CUDA not installed | Install NVIDIA GPU and CUDA 11.8+ |
| `PasswordProtectedError` | PDF is encrypted | Remove password: `pdftk input.pdf output output.pdf user_pw PROMPT` |
| `CorruptedPDFError` | PDF file is damaged | Re-download or recreate PDF |
| `GPUOutOfMemoryError` | GPU ran out of memory | Reduce concurrent conversions or close other GPU processes |
| `PageLimitExceededError` | PDF has too many pages | Increase `max_pages` or split PDF |

---

## Performance Tuning

### GPU Memory Optimization

```python
# Reduce GPU memory usage
config = ConverterConfig(
    gpu_enabled=True,
    gpu_memory_limit_mb=2048,  # Limit to 2GB
    max_pages=50,              # Process fewer pages per conversion
    extract_images=False       # Skip image extraction (saves memory)
)
```

### Conversion Speed Optimization

```python
# Faster conversion (lower quality)
config = ConverterConfig(
    ocr_all_pages=False,           # Skip OCR for pages with text layer
    ocr_confidence_threshold=0.3,   # Lower threshold (faster processing)
    extract_images=False,           # Skip image extraction
    timeout_seconds=60              # Shorter timeout
)
```

### Quality Optimization

```python
# Highest quality (slower)
config = ConverterConfig(
    ocr_all_pages=True,             # OCR all pages
    ocr_confidence_threshold=0.8,   # Higher threshold (stricter quality)
    extract_images=True,            # Extract images
    image_downscale_threshold=4000,  # Less aggressive downscaling
    timeout_seconds=600             # Longer timeout
)
```

---

## Integration with Server

### Server Usage Example (003-server-api)

```python
# In server/src/pdf2md_server/services/conversion.py
from pathlib import Path
from pdf2md_converter.marker_converter import MarkerConverter
from pdf2md_converter.config import ConverterConfig
from pdf2md_converter.exceptions import ConversionError
import asyncio

async def convert_pdf_async(pdf_path: Path, output_path: Path) -> dict:
    """
    Async wrapper for conversion engine (server layer).

    This function is called by server API endpoints.
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
        return {
            "pages_processed": metrics.pages_processed,
            "conversion_time": metrics.conversion_time_seconds,
            "gpu_memory_used_mb": metrics.gpu_memory_used_mb
        }
    except ConversionError as e:
        # Server layer converts to HTTP response
        raise ConversionError(f"Conversion failed: {e.message}")
```

---

## Troubleshooting

### GPU Not Detected

**Symptom**: `GPUUnavailableError: GPU required but not available`

**Solutions**:
1. Verify NVIDIA GPU: `nvidia-smi`
2. Check CUDA installation: `nvcc --version`
3. Install PyTorch with CUDA: `uv add torch --index-url https://download.pytorch.org/whl/cu118`
4. Reboot system if CUDA was just installed

### GPU Out of Memory

**Symptom**: `GPUOutOfMemoryError: GPU out of memory`

**Solutions**:
1. Reduce concurrent conversions (server layer)
2. Close other GPU processes: `nvidia-smi`
3. Reduce batch size or max pages
4. Use GPU with more VRAM

### Slow Conversion

**Symptom**: Conversion takes >30 seconds for 10 pages

**Solutions**:
1. Verify GPU is being used: `nvidia-smi` during conversion
2. Check OCR is not running on CPU
3. Reduce `ocr_all_pages` to `False` (only OCR scanned pages)
4. Disable image extraction: `extract_images=False`

### Import Errors

**Symptom**: `ModuleNotFoundError: No module named 'pdf2md_converter'`

**Solutions**:
1. Run `uv sync` in converter directory
2. Activate virtual environment: `source .venv/bin/activate`
3. Verify package is installed: `uv run pip list | grep pdf2md`

---

## Next Steps

1. **Read the spec**: `/specs/004-conversion-engine/spec.md`
2. **Review the data model**: `/specs/004-conversion-engine/data-model.md`
3. **Check API contracts**: `/specs/004-conversion-engine/contracts/README.md`
4. **Implement the converter**: Follow task list in `/specs/004-conversion-engine/tasks.md` (after running `/speckit.tasks`)
5. **Run tests**: `uv run pytest tests/`

---

## Additional Resources

- **Marker Documentation**: https://github.com/VikParuchuri/marker
- **PyTorch CUDA Guide**: https://pytorch.org/docs/stable/cuda.html
- **Pillow Documentation**: https://pillow.readthedocs.io/
- **Project Constitution**: `.specify/memory/constitution.md`

---

## Support

For issues or questions:
1. Check this quickstart guide
2. Review the spec and contracts
3. Check test fixtures for usage examples
4. Open an issue on GitHub (project repository)
