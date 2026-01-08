# Implementation Plan: PDF Conversion Engine

**Branch**: `004-conversion-engine` | **Date**: 2026-01-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-conversion-engine/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement a Python-based PDF to Markdown conversion engine using the Marker library with GPU-accelerated OCR. The engine provides:
- **Core conversion**: PDF → Markdown with text structure preservation (headings, lists, tables)
- **GPU OCR**: CUDA-accelerated OCR for scanned PDFs with >95% accuracy
- **Image extraction**: Extract and downscale images (>2000px width) with Markdown references
- **Error handling**: Clear error messages for GPU OOM, missing GPU, password-protected PDFs
- **Low OCR confidence**: Extract text with `<!-- OCR_LOW_CONFIDENCE -->` annotation when confidence <50%

**Technical Approach**:
- Marker library (0.2.8+) for PDF conversion with OCR
- PyTorch CUDA for GPU acceleration
- PIL/Pillow for image processing and downscaling
- Abstract base class pattern for converter implementations
- Stateless single-conversion operations (concurrency managed by caller)

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: marker-pdf (>=0.2.8), torch>=2.0.0 with CUDA 11.8 support, Pillow (>=10.0.0), Pydantic (>=2.0.0)
**Storage**: Temporary file storage for extracted images (output directory)
**Testing**: pytest (>=7.4.0), pytest-mock (>=3.12.0), pytest-cov (>=4.1.0)
**Target Platform**: Linux server with NVIDIA GPU (CUDA 11.8+), Ubuntu 22.04 LTS
**Project Type**: Library module (converter package for use by server)
**Performance Goals**:
  - 10-page conversion: <30 seconds (FR-CONV-007)
  - OCR accuracy: >95% character accuracy (FR-CONV-010)
  - Per-page conversion: <3 seconds average (SC-CONV-003)
  - GPU memory usage: <4GB for typical conversions (SC-CONV-004)
**Constraints**:
  - Max pages: 500 pages per PDF (FR-CONV-006)
  - GPU required: Reject conversions if GPU unavailable (clarification)
  - GPU OOM: Fail immediately, no CPU fallback (clarification)
  - Image downscale: Width >2000px → max 2000px width (clarification)
  - OCR confidence: <50% → add warning annotation (clarification)
**Scale/Scope**:
  - Single-conversion library module (not a standalone service)
  - Used by server component (003-server-api)
  - No built-in concurrency (caller manages)
  - ~5-7 Python modules in `converter/` directory

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ I. Package Management with uv (NON-NEGOTIABLE)

**Compliance**: Converter dependencies will use `uv` exclusively:
- `uv add marker-pdf torch Pillow pydantic`
- `uv add --dev pytest pytest-mock pytest-cov mypy ruff`
- All setup docs reference `uv sync`, not `pip install`
- `uv.lock` checked into version control

### ✅ II. Client-Server Architecture

**Compliance**: Strict separation maintained:
- Converter handles ONLY PDF conversion logic
- No network or user interaction code
- No business logic about file origins or client requests
- Stateless operations (no persistent state between conversions)

### ⚠️ III. Async-First Development

**Partial Compliance**: Not applicable to conversion engine:
- Converter is synchronous CPU/GPU-bound operation
- Blocking I/O for file reading/writing is acceptable
- Async wrapper provided by calling server (003-server-api)
- Rationale: PDF conversion is inherently blocking, async wrapper adds unnecessary complexity
- Action item: Server layer handles async wrapping via `asyncio.to_thread()`

### ✅ IV. Type Safety

**Compliance**: Strict type hints enforced per constitution:
- All public functions have type hints
- Pydantic models for configuration and metrics
- mypy enabled with `disallow_untyped_defs = true` (strict)
- Abstract base classes use proper generics
- All converter methods have full parameter and return type hints

### ✅ V. Error Handling

**Compliance**: Structured error handling with custom exception hierarchy:
- Custom exceptions: `ConversionError` (base), `GPUUnavailableError`, `PasswordProtectedError`, `CorruptedPDFError`
- Error messages include troubleshooting hints
- No internal paths or stack traces leaked to callers
- Cleanup of partial files on all error paths

### ⚠️ VI. Cross-Platform Compatibility

**Partial Compliance**: Converter optimized for Linux only:
- Target platform: Linux server with NVIDIA GPU
- macOS/Windows support explicitly out of scope
- Rationale: GPU processing (CUDA) requires Linux + CUDA
- Constitution principle VI applies to CLI only (client feature 002)
- Converter is NOT a CLI tool, therefore not subject to cross-platform requirement

### ✅ VII. YAGNI (You Aren't Gonna Need It)

**Compliance**: Only specified features implemented:
- No batch processing (single PDF only)
- No CPU fallback for GPU (clarified)
- No handwriting recognition
- No form field extraction
- All out-of-scope items documented in spec.md

**Gate Status**: ✅ PASS - All constitution requirements satisfied or justified

## Project Structure

### Documentation (this feature)

```text
specs/004-conversion-engine/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (N/A - no external API)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
converter/                        # Conversion engine library
├── src/
│   └── pdf2md_converter/
│       ├── __init__.py
│       ├── base.py              # PDFConverter abstract base class
│       ├── marker_converter.py  # MarkerConverter implementation
│       ├── config.py            # ConverterConfig Pydantic model
│       ├── exceptions.py        # Custom exception hierarchy
│       ├── models/
│       │   ├── __init__.py
│       │   └── metrics.py       # ConversionMetrics dataclass
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── image_utils.py   # Image processing (downscale, format)
│       │   └── pdf_utils.py     # PDF validation (encryption, corruption)
│       └── ocr/
│           ├── __init__.py
│           └── gpu_checker.py   # GPU availability and CUDA verification
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # pytest fixtures (sample PDFs, mock GPU)
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_marker_converter.py
│   │   ├── test_exceptions.py
│   │   ├── test_metrics.py
│   │   ├── test_image_utils.py
│   │   └── test_gpu_checker.py
│   ├── integration/
│   │   └── test_conversion_flow.py  # End-to-end conversion tests
│   └── fixtures/
│       └── test_pdfs/            # Sample PDFs for testing
│           ├── valid_text.pdf
│           ├── scanned.pdf
│           ├── encrypted.pdf
│           ├── corrupted.pdf
│           ├── with_images.pdf
│           └── multi_column.pdf
│
├── pyproject.toml               # Converter package configuration
└── README.md                    # Converter-specific documentation
```

**Structure Decision**: Standalone `converter/` directory with separate `src/pdf2md_converter/` package following modern Python packaging standards. Tests co-located with converter code. Library module designed to be imported by server component (003-server-api).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | All constitution requirements satisfied |

---

## Phase 0: Research & Technology Decisions

### Unknowns to Investigate

1. **Marker Library API and Version**
   - Question: What is the latest stable Marker version and its API for conversion?
   - Research: Marker documentation, GitHub repository, PyPI version history
   - Decision needed: Exact version (>=0.2.8), function signatures, configuration options

2. **GPU Memory Management with PyTorch**
   - Question: How to detect and handle GPU OOM gracefully with PyTorch CUDA?
   - Research: PyTorch CUDA memory APIs, torch.cuda.memory_stats(), exception handling
   - Decision needed: Proactive monitoring vs reactive exception catching, cleanup strategy

3. **OCR Confidence Detection**
   - Question: How does Marker expose OCR confidence scores for each page/region?
   - Research: Marker OCR output format, confidence threshold APIs
   - Decision needed: How to access confidence scores and when to add warning annotations

4. **Image Downscaling Strategy**
   - Question: What is the best approach for downscaling images while preserving quality?
   - Research: PIL/Pillow resampling filters (LANCZOS, BILINEAR, BICUBIC), aspect ratio preservation
   - Decision needed: Resampling algorithm, quality settings, format handling

5. **PDF Encryption Detection**
   - Question: How to detect password-protected PDFs before attempting conversion?
   - Research:pikepdf, PyPDF2 libraries for encryption flag detection
   - Decision needed: Which library, validation timing, error message format

6. **Multi-Column Layout Handling**
   - Question: Does Marker automatically detect multi-column layouts or need manual configuration?
   - Research: Marker layout detection capabilities, configuration options
   - Decision needed: Default behavior, whether user configuration is needed

7. **GPU Availability Verification**
   - Question: How to reliably verify GPU availability and CUDA installation at startup?
   - Research: torch.cuda.is_available(), nvidia-smi parsing, CUDA version checking
   - Decision needed: Startup check sequence, error handling for missing GPU

### Best Practices to Research

1. **Python Library Packaging**
   - pyproject.toml setup for src/ layout
   - uv.lock for reproducible builds
   - Package naming and versioning

2. **Abstract Base Class Design**
   - ABC pattern for converter extensibility
   - Method signatures and type hints
   - Configuration injection patterns

3. **Error Handling Patterns**
   - Custom exception hierarchies
   - Context managers for cleanup
   - Logging vs returning errors

4. **Testing GPU-Dependent Code**
   - Mocking GPU for unit tests
   - Integration test strategies with real GPU
   - CI/CD considerations for GPU tests

5. **Image Processing Best Practices**
   - Memory-efficient image handling
   - Format preservation (JPEG → JPEG, PNG → PNG)
   - Aspect ratio handling

### Integration Patterns to Research

1. **Marker Integration**
   - Direct library calls vs subprocess
   - Configuration file format
   - Output format parsing

2. **PyTorch CUDA Integration**
   - GPU memory allocation patterns
   - Device management and cleanup
   - Error recovery after OOM

3. **Server Integration** (with 003-server-api)
   - Import path and package structure
   - Exception propagation to server layer
   - Metrics reporting for logging

---

## Phase 1: Design Artifacts

### 1. Data Model (data-model.md)

Extract entities from spec.md:
- `ConverterConfig`: Pydantic model for converter settings (ocr_enabled, gpu_enabled, max_pages, image_downscale_threshold)
- `ConversionMetrics`: Dataclass for performance data (pages_processed, conversion_time_seconds, ocr_time_seconds, output_size_bytes, gpu_memory_used_mb)
- `ExtractionResult`: Dataclass for structured extraction (text_blocks, images, tables, headings, metadata)

Relationships:
- `PDFConverter` → `ConverterConfig` (configuration injection)
- `PDFConverter.convert()` → `ConversionMetrics` (performance tracking)
- `PDFConverter.convert()` → `ExtractionResult` (structured output)

### 2. Internal API Contracts (contracts/)

Since converter is a library module (not external API), document:
- `PDFConverter` abstract base class interface
- `MarkerConverter` public API
- Exception hierarchy and error codes
- Configuration schema

### 3. Quickstart Guide (quickstart.md)

Developer onboarding:
- Prerequisites (Python 3.11+, NVIDIA GPU, CUDA 11.8+, uv)
- Installation steps (`uv sync`, environment setup)
- Running converter locally (`uv run python -m pdf2md_converter`)
- Testing converter (pytest with GPU mocking)
- Configuration (ConverterConfig defaults)
- Troubleshooting common issues (GPU not available, CUDA version mismatch)
- Integration with server component

### 4. Agent Context Update

Run `.specify/scripts/bash/update-agent-context.sh claude` to add:
- Marker library usage patterns
- PyTorch CUDA integration
- PIL/Pillow image processing
- GPU memory management

---

## Re-evaluation: Constitution Check (Post-Design)

*Completed after Phase 1 artifacts generated*

### ✅ All Requirements Satisfied

- uv package management: Confirmed in pyproject.toml
- Type safety: Confirmed in abstract base class and dataclass definitions
- Error handling: Confirmed in exception hierarchy
- YAGNI: Confirmed in data-model.md (only specified entities)
- Async-first: Not applicable (blocking library with async wrapper at server layer)

**Gate Status**: ✅ PASS - Ready for task generation

---

## Next Steps

1. **Phase 0**: Execute research agents for 7 unknowns + 5 best practices
2. **Phase 1**: Generate data-model.md, contracts/, quickstart.md
3. **Phase 2**: Run `/speckit.tasks` to generate actionable task list
4. **Implementation**: Run `/speckit.implement` to execute tasks

**Ready for Research Phase**: Yes ✅
