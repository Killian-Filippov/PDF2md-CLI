# Implementation Tasks: PDF Conversion Engine

**Feature**: 004-conversion-engine
**Date**: 2026-01-08
**Status**: Ready for Implementation
**Total Tasks**: 78

## Task Execution Strategy

This task list is organized by **user story** to enable independent implementation and testing. Each story can be developed in parallel once foundational tasks are complete.

### Dependency Graph

```
Phase 1: Setup (Foundation)
   ↓
Phase 2: Foundational (Blocking Prerequisites)
   ↓
Phase 3: User Story 1 (P1) ←→ Phase 4: User Story 2 (P1) [Parallel]
   ↓
Phase 5: User Story 3 (P2) ←→ Phase 6: User Story 4 (P2) [Parallel]
   ↓
Phase 7: User Story 5 (P3)
   ↓
Phase 8: Polish & Cross-Cutting Concerns
```

**Parallel Execution Opportunities**:
- After Phase 2: User Stories 1 & 2 can be developed in parallel (both P1)
- After Phase 4: User Stories 3 & 4 can be developed in parallel (both P2)
- All unit tests can be written in parallel with implementation

### MVP Scope

**Minimum Viable Product** = Phase 1 + Phase 2 + Phase 3 (User Story 1) + Phase 4 (User Story 2)

**MVP Task Count**: 48 tasks (62% of total)

---

## Phase 1: Setup (4 tasks)

*Initialize project structure and dependencies*

- [ ] [T001] Create `converter/` directory structure with `src/pdf2md_converter/`, `tests/`, `models/`, `utils/`, `ocr/` subdirectories (converter/)
- [ ] [T002] Create `pyproject.toml` with uv configuration, marker-pdf>=0.2.8, torch (CUDA 11.8+), Pillow>=10.0.0, Pydantic>=2.0.0, pikepdf>=8.0.0 (converter/pyproject.toml)
- [ ] [T003] Create `README.md` with converter overview, architecture diagram, and integration guide (converter/README.md)
- [ ] [T004] Create `tests/fixtures/test_pdfs/` directory with sample PDFs (valid_text.pdf, scanned.pdf, encrypted.pdf, corrupted.pdf, with_images.pdf, multi_column.pdf) (tests/fixtures/test_pdfs/)

**Acceptance**: Running `uv sync` in converter/ creates virtual environment and installs all dependencies without errors.

---

## Phase 2: Foundational (20 tasks)

*Core infrastructure, models, and utilities (BLOCKS all user stories)*

### Configuration & Models (5 tasks)

- [ ] [T005] Create `ConverterConfig` Pydantic model in `config.py` with ocr_enabled, gpu_enabled, max_pages, timeout_seconds, ocr_confidence_threshold, image_downscale_threshold, languages fields (converter/src/pdf2md_converter/config.py)
- [ ] [T006] Implement validation in `ConverterConfig` for gpu_memory_limit_mb (>=100, <=16384), max_pages (>=1, <=1000), ocr_confidence_threshold (0.0 to 1.0) (converter/src/pdf2md_converter/config.py)
- [ ] [T007] Create `ConversionMetrics` dataclass in `models/metrics.py` with pages_processed, pages_with_ocr, images_extracted, conversion_time_seconds, gpu_memory_used_mb, low_confidence_pages fields (converter/src/pdf2md_converter/models/metrics.py)
- [ ] [T008] Add `@property` methods to `ConversionMetrics`: `elapsed_time`, `pages_per_second` (converter/src/pdf2md_converter/models/metrics.py)
- [ ] [T009] Write unit tests for `ConverterConfig` and `ConversionMetrics` with valid and invalid configurations (tests/unit/test_config.py)

**Test Criteria**: Config validates correctly, GPU check rejects invalid values, metrics calculate derived properties correctly.

### Exception Hierarchy (3 tasks)

- [ ] [T010] Create base `ConversionError` exception class in `exceptions.py` with message and details attributes (converter/src/pdf2md_converter/exceptions.py)
- [ ] [T011] Create `GPUUnavailableError`, `PasswordProtectedError`, `CorruptedPDFError`, `GPUOutOfMemoryError`, `PageLimitExceededError` subclasses of `ConversionError` with error codes (converter/src/pdf2md_converter/exceptions.py)
- [ ] [T012] Write unit tests for exception hierarchy verifying error codes and message formatting (tests/unit/test_exceptions.py)

**Test Criteria**: All exceptions inherit from ConversionError, error codes match specification, messages include troubleshooting hints.

### GPU Checker (3 tasks)

- [ ] [T013] Create `check_gpu_available()` function in `ocr/gpu_checker.py` using `torch.cuda.is_available()` (converter/src/pdf2md_converter/ocr/gpu_checker.py)
- [ ] [T014] Implement CUDA version verification in `check_gpu_available()` using `torch.version.cuda` (converter/src/pdf2md_converter/ocr/gpu_checker.py)
- [ ] [T015] Write unit tests for GPU checker with mock torch.cuda (tests/unit/test_gpu_checker.py)

**Test Criteria**: Returns True if CUDA 11.8+ available, False otherwise. Logs warnings for missing CUDA.

### PDF Validation Utilities (4 tasks)

- [ ] [T016] Create `is_pdf_encrypted()` function in `utils/pdf_utils.py` using pikepdf that returns True if PDF has encryption flag (converter/src/pdf2md_converter/utils/pdf_utils.py)
- [ ] [T017] Create `validate_pdf_structure()` function in `utils/pdf_utils.py` that checks PDF is not corrupted (pikepdf.open() with exception handling) (converter/src/pdf2md_converter/utils/pdf_utils.py)
- [ ] [T018] Create `get_page_count()` function in `utils/pdf_utils.py` using pikepdf to count pages (converter/src/pdf2md_converter/utils/pdf_utils.py)
- [ ] [T019] Write unit tests for PDF validation functions with valid, encrypted, and corrupted PDFs (tests/unit/test_pdf_utils.py)

**Test Criteria**: Encrypted PDFs detected, corrupted PDFs raise exceptions, page count accurate.

### Image Processing Utilities (3 tasks)

- [ ] [T020] Create `downscale_image()` function in `utils/image_utils.py` using Pillow to downscale images > threshold width (converter/src/pdf2md_converter/utils/image_utils.py)
- [ ] [T021] Implement aspect ratio preservation in `downscale_image()` with LANCZOS resampling filter (converter/src/pdf2md_converter/utils/image_utils.py)
- [ ] [T022] Write unit tests for image downscaling with various sizes and formats (tests/unit/test_image_utils.py)

**Test Criteria**: Images >2000px width downscaled to 2000px, aspect ratio preserved, quality maintained.

### Abstract Base Class (2 tasks)

- [ ] [T023] Create `PDFConverter` abstract base class in `base.py` with `__init__(config)`, `convert()` abstract method, `_validate_inputs()`, `_cleanup()` methods (converter/src/pdf2md_converter/base.py)
- [ ] [T024] Add `_validate_gpu_availability()` method to `PDFConverter` that calls `check_gpu_available()` and raises `GPUUnavailableError` if needed (converter/src/pdf2md_converter/base.py)

**Test Criteria**: ABC enforces subclass implementation, GPU validation raises exception when required but unavailable.

**Acceptance**: All foundational services can be imported and instantiated without errors. Unit tests pass with >80% coverage.

---

## Phase 3: User Story 1 - Basic PDF to Markdown Conversion (13 tasks)

*Priority: P1 | Independent Test: Call converter with sample PDF, verify MD output*

### MarkerConverter Implementation (6 tasks)

- [ ] [T025] [P] [US1] Create `MarkerConverter` class in `marker_converter.py` extending `PDFConverter` ABC (converter/src/pdf2md_converter/marker_converter.py)
- [ ] [T026] [P] [US1] Implement `_validate_inputs()` in `MarkerConverter` checking PDF exists, output directory writable, page count <= max_pages (converter/src/pdf2md_converter/marker_converter.py)
- [ ] [T027] [US1] Implement `convert()` method in `MarkerConverter` calling Marker library's `convert_single_pdf()` with config parameters (converter/src/pdf2md_converter/marker_converter.py)
- [ ] [T028] [US1] Add Markdown output writing in `convert()` method using UTF-8 encoding to `output_path` (converter/src/pdf2md_converter/marker_converter.py)
- [ ] [T029] [US1] Implement `_cleanup()` method that removes output Markdown file on error (converter/src/pdf2md_converter/marker_converter.py)
- [ ] [T030] [US1] Collect and return `ConversionMetrics` from `convert()` with pages_processed, conversion_time_seconds, output_size_bytes (converter/src/pdf2md_converter/marker_converter.py)

**Test Criteria**: Calling `converter.convert(valid_text.pdf, output.md)` succeeds, output.md contains Markdown with proper headings, lists, tables.

### Error Handling (3 tasks)

- [ ] [T031] [US1] Wrap Marker library calls in try/except to catch exceptions and convert to `ConversionError` (converter/src/pdf2md_converter/marker_converter.py)
- [ ] [T032] [US1] Raise `PageLimitExceededError` if page count exceeds `config.max_pages` (converter/src/pdf2md_converter/marker_converter.py)
- [ ] [T033] [US1] Log detailed error information before raising exceptions (converter/src/pdf2md_converter/marker_converter.py)

**Test Criteria**: PDF with 600 pages raises PageLimitExceededError. Corrupted PDF raises CorruptedPDFError.

### Integration Tests (4 tasks)

- [ ] [T034] [US1] Write integration test for basic PDF conversion verifying Markdown output structure (tests/integration/test_conversion_flow.py)
- [ ] [T035] [US1] Write integration test for heading hierarchy preservation (tests/integration/test_conversion_flow.py)
- [ ] [T036] [US1] Write integration test for list conversion (bullet and numbered) (tests/integration/test_conversion_flow.py)
- [ ] [T037] [US1] Write integration test for table conversion to Markdown table syntax (tests/integration/test_conversion_flow.py)

**Test Criteria**: All integration tests pass with sample PDFs. Markdown output matches expected structure.

**Acceptance**: `uv run python -m pdf2md_converter` converts valid_text.pdf to valid Markdown with headings, lists, tables preserved.

---

## Phase 4: User Story 2 - GPU-Accelerated OCR (11 tasks)

*Priority: P1 | Independent Test: Convert scanned PDF, verify text extracted with >95% accuracy*

### GPU OCR Integration (5 tasks)

- [ ] [T038] [P] [US2] Add `ocr_all_pages` parameter to Marker library call in `convert()` method (converter/src/pdf2md_converter/marker_converter.py)
- [ ] [T039] [P] [US2] Implement GPU OCR wrapper calling Marker's OCR functionality with CUDA (converter/src/pdf2md_converter/marker_converter.py)
- [ ] [T040] [US2] Add GPU memory monitoring using `torch.cuda.memory_allocated()` during OCR (converter/src/pdf2md_converter/marker_converter.py)
- [ ] [T041] [US2] Implement GPU OOM detection catching `torch.cuda.OutOfMemoryError` and raising `GPUOutOfMemoryError` (converter/src/pdf2md_converter/marker_converter.py)
- [ ] [T042] [US2] Add OCR time tracking to `ConversionMetrics.ocr_time_seconds` (converter/src/pdf2md_converter/marker_converter.py)

**Test Criteria**: Scanned PDF converts with text extracted, GPU memory usage tracked, OOM raises GPUOutOfMemoryError.

### OCR Confidence Handling (4 tasks)

- [ ] [T043] [P] [US2] Extract OCR confidence scores from Marker output per page (converter/src/pdf2md_converter/marker_converter.py)
- [ ] [T044] [US2] Identify pages with confidence < `config.ocr_confidence_threshold` (converter/src/pdf2md_converter/marker_converter.py)
- [ ] [T045] [US2] Inject `<!-- OCR_LOW_CONFIDENCE -->` annotation in Markdown before low-confidence text blocks (converter/src/pdf2md_converter/marker_converter.py)
- [ ] [T046] [US2] Record low-confidence page numbers in `ConversionMetrics.low_confidence_pages` (converter/src/pdf2md_converter/marker_converter.py)

**Test Criteria**: Pages with OCR confidence <50% have warning annotation in Markdown. Metrics include list of low-confidence pages.

### Integration Tests (2 tasks)

- [ ] [T047] [US2] Write integration test for scanned PDF conversion verifying >95% text accuracy (tests/integration/test_conversion_flow.py)
- [ ] [T048] [US2] Write integration test for GPU OOM scenario using mock torch.cuda.OutOfMemoryError (tests/integration/test_conversion_flow.py)

**Test Criteria**: Scanned PDF conversion completes in <15 seconds for 10 pages. OCR accuracy >95%. OOM test raises GPUOutOfMemoryError with clear message.

**Acceptance**: Converting scanned.pdf extracts text with >95% accuracy, completes in <15 seconds for 10 pages. GPU OOM returns clear error message.

---

## Phase 5: User Story 3 - Image Extraction and Referencing (9 tasks)

*Priority: P2 | Independent Test: Convert PDF with images, verify images extracted and referenced*

### Image Extraction (5 tasks)

- [ ] [T049] [P] [US3] Implement image extraction from PDF using Marker in `convert()` method (converter/src/pdf2md_converter/marker_converter.py)
- [ ] [T050] [P] [US3] Save extracted images to `config.output_directory` with sequential naming (`image-001.png`, `image-002.png`, etc.) (converter/src/pdf2md_converter/marker_converter.py)
- [ ] [T051] [US3] Call `downscale_image()` for images with width > `config.image_downscale_threshold` (converter/src/pdf2md_converter/marker_converter.py)
- [ ] [T052] [US3] Generate Markdown image references using `![alt](path)` format in output (converter/src/pdf2md_converter/marker_converter.py)
- [ ] [T053] [US3] Preserve original image format (JPEG → JPEG, PNG → PNG) unless format specified (converter/src/pdf2md_converter/marker_converter.py)

**Test Criteria**: PDF with 3 images extracts to image-001.png, image-002.png, image-003.png. Markdown contains `![image](image-001.png)` references. Images >2000px width downscaled to 2000px.

### Metrics Tracking (2 tasks)

- [ ] [T054] [P] [US3] Track `images_extracted` count in `ConversionMetrics` (converter/src/pdf2md_converter/marker_converter.py)
- [ ] [T055] [P] [US3] Add image file paths to `ConversionMetrics` (optional field for debugging) (converter/src/pdf2md_converter/marker_converter.py)

**Test Criteria**: Metrics include correct count of extracted images.

### Integration Tests (2 tasks)

- [ ] [T056] [US3] Write integration test for image extraction and referencing (tests/integration/test_conversion_flow.py)
- [ ] [T057] [US3] Write integration test for image downscaling with large images (tests/integration/test_conversion_flow.py)

**Test Criteria**: PDF with images extracts all images, names them sequentially, generates correct Markdown references, downscales large images.

**Acceptance**: Converting with_images.pdf extracts all images to separate files, Markdown contains correct image references with sequential filenames.

---

## Phase 6: User Story 4 - Multi-Column Layout Handling (6 tasks)

*Priority: P2 | Independent Test: Convert two-column PDF, verify reading order preserved*

### Multi-Column Detection (3 tasks)

- [ ] [T058] [P] [US4] Research Marker's multi-column layout detection capabilities (already enabled by default in Marker) (converter/src/pdf2md_converter/marker_converter.py)
- [ ] [T059] [P] [US4] Configure Marker to preserve reading order for multi-column layouts (default behavior) (converter/src/pdf2md_converter/marker_converter.py)
- [ ] [T060] [P] [US4] Add configuration option `preserve_reading_order` to `ConverterConfig` (default True) (converter/src/pdf2md_converter/config.py)

**Test Criteria**: Marker automatically detects multi-column layouts and preserves reading order (top to bottom, left to right).

### Integration Tests (3 tasks)

- [ ] [T061] [US4] Write integration test for two-column PDF conversion (tests/integration/test_conversion_flow.py)
- [ ] [T062] [US4] Write integration test for PDF with sidebars (main content vs sidebar) (tests/integration/test_conversion_flow.py)
- [ ] [T063] [US4] Verify text order follows logical reading pattern (tests/integration/test_conversion_flow.py)

**Test Criteria**: Two-column PDF output preserves logical reading order. Sidebar content distinguished from main content.

**Acceptance**: Converting multi_column.pdf preserves reading order, output flows logically from top to bottom, left to right.

---

## Phase 7: User Story 5 - Password-Protected PDF Handling (7 tasks)

*Priority: P3 | Independent Test: Attempt conversion of encrypted PDF, verify clear error and cleanup*

### Encryption Detection (3 tasks)

- [ ] [T064] [P] [US5] Call `is_pdf_encrypted()` in `_validate_inputs()` before conversion (converter/src/pdf2md_converter/marker_converter.py)
- [ ] [T065] [P] [US5] Raise `PasswordProtectedError` with message "PDF is password-protected and cannot be converted. Please remove the password and try again." (converter/src/pdf2md_converter/marker_converter.py)
- [ ] [T066] [P] [US5] Add troubleshooting hint to error message: "Remove password protection using: pdftk input.pdf output output.pdf user_pw PROMPT" (converter/src/pdf2md_converter/marker_converter.py)

**Test Criteria**: Encrypted PDF raises PasswordProtectedError before conversion starts, error message includes troubleshooting hint.

### Cleanup Verification (2 tasks)

- [ ] [T067] [P] [US5] Verify no partial output files exist after encryption error (tests/integration/test_conversion_flow.py)
- [ ] [T068] [P] [US5] Ensure `_cleanup()` method is called in exception handler after PasswordProtectedError (converter/src/pdf2md_converter/marker_converter.py)

**Test Criteria**: Encrypted PDF conversion leaves no files on disk, output Markdown not created.

### Integration Tests (2 tasks)

- [ ] [T069] [US5] Write integration test for encrypted PDF rejection (tests/integration/test_conversion_flow.py)
- [ ] [T070] [US5] Write integration test for cleanup verification after encryption error (tests/integration/test_conversion_flow.py)

**Test Criteria**: Encrypted PDF raises PasswordProtectedError immediately, no partial files remain.

**Acceptance**: Attempting to convert encrypted.pdf raises PasswordProtectedError with clear message and troubleshooting hint, no files left on disk.

---

## Phase 8: Polish & Cross-Cutting Concerns (8 tasks)

*Testing, documentation, code quality, performance*

### Type Safety & Code Quality (3 tasks)

- [ ] [T071] Run mypy in strict mode (`disallow_untyped_defs=true`) on all converter code (converter/src/pdf2md_converter/)
- [ ] [T072] Run ruff linter and formatter on all converter code (converter/src/pdf2md_converter/)
- [ ] [T073] Fix all type hints and linting issues to achieve 100% compliance (converter/src/pdf2md_converter/)

**Test Criteria**: `uv run mypy src/` passes with no errors. `uv run ruff check src/` passes with no errors.

### Documentation (2 tasks)

- [ ] [T074] Update README.md with usage examples, API reference, troubleshooting guide (converter/README.md)
- [ ] [T075] Add docstrings to all public classes and methods following Google docstring format (converter/src/pdf2md_converter/)

**Test Criteria**: All public methods have docstrings. README includes quickstart examples.

### Performance Testing (2 tasks)

- [ ] [T076] Write performance test verifying 10-page conversion completes in <30 seconds (tests/integration/test_performance.py)
- [ ] [T077] Write performance test verifying GPU memory usage stays <4GB (tests/integration/test_performance.py)

**Test Criteria**: Performance tests pass on reference hardware. Conversion time and GPU memory within targets.

### Test Coverage (1 task)

- [ ] [T078] Run pytest with coverage and ensure >80% code coverage (converter/)

**Test Criteria**: `uv run pytest --cov=pdf2md_converter` shows >80% coverage.

---

## Task Summary

| Phase | Tasks | Priority | User Story | Parallel? |
|-------|-------|----------|------------|-----------|
| Phase 1: Setup | 4 | P0 | Foundation | No |
| Phase 2: Foundational | 20 | P0 | Foundation | Partial |
| Phase 3: Story 1 (Basic Conversion) | 13 | P1 | Single PDF Conversion | Yes (with Phase 4) |
| Phase 4: Story 2 (GPU OCR) | 11 | P1 | GPU-Accelerated OCR | Yes (with Phase 3) |
| Phase 5: Story 3 (Images) | 9 | P2 | Image Extraction | Yes (with Phase 6) |
| Phase 6: Story 4 (Multi-Column) | 6 | P2 | Multi-Column Layout | Yes (with Phase 5) |
| Phase 7: Story 5 (Encrypted PDFs) | 7 | P3 | Password-Protected Handling | No (after Phase 6) |
| Phase 8: Polish | 8 | P0 | Cross-Cutting | Yes (with any phase) |
| **Total** | **78** | | | |

### Parallel Execution Strategy

**Maximum Parallelism** (after Phase 2):
- **Team A**: Phase 3 (User Story 1) - 13 tasks
- **Team B**: Phase 4 (User Story 2) - 11 tasks
- **Team C**: Phase 5 (User Story 3) - 9 tasks (after Phase 3/4)
- **Team D**: Phase 6 (User Story 4) - 6 tasks (after Phase 3/4)
- **Team E**: Phase 8 (Polish) - 8 tasks (anytime)

**Critical Path**: Phase 1 → Phase 2 → Phase 3 → Phase 7 → Phase 8 (45 tasks for MVP)

### Independent Testing Criteria

Each user story can be tested independently:

1. **User Story 1** (P1): Call `converter.convert(valid_text.pdf, output.md)`
   - Success: output.md contains Markdown with headings (#), lists (-, 1.), tables (| Header |)

2. **User Story 2** (P1): Call `converter.convert(scanned.pdf, output.md)`
   - Success: output.md contains extracted text with >95% accuracy, completes in <15s for 10 pages

3. **User Story 3** (P2): Call `converter.convert(with_images.pdf, output.md)`
   - Success: Images extracted to image-001.png, image-002.png, etc., Markdown contains `![image](image-001.png)` references

4. **User Story 4** (P2): Call `converter.convert(multi_column.pdf, output.md)`
   - Success: output.md preserves logical reading order (top to bottom, left to right)

5. **User Story 5** (P3): Call `converter.convert(encrypted.pdf, output.md)`
   - Success: Raises PasswordProtectedError with message "PDF is password-protected", no files left on disk

---

**Status**: ✅ Ready for implementation

**Next Step**: Run `/speckit.implement` to execute tasks in dependency order, or begin manual implementation starting with Phase 1 (T001-T004).
