# Implementation Tasks: Server REST API

**Feature**: 003-server-api
**Date**: 2026-01-07
**Status**: Ready for Implementation
**Total Tasks**: 87

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
Phase 8: Polish & Cross-Cutting
```

**Parallel Execution Opportunities**:
- After Phase 2: User Stories 1 & 2 can be developed in parallel (both P1)
- After Phase 4: User Stories 3 & 4 can be developed in parallel (both P2)
- All unit tests can be written in parallel with implementation

### MVP Scope

**Minimum Viable Product** = Phase 1 + Phase 2 + Phase 3 (User Story 1) + Phase 4 (User Story 2)

**MVP Task Count**: 52 tasks (60% of total)

---

## Phase 1: Setup (5 tasks)

*Initialize project structure and dependencies*

- [ ] [T001] [P0] [Setup] Create `server/` directory structure with `src/pdf2md_server/`, `tests/`, `api/`, `core/`, `models/`, `services/`, `utils/` subdirectories (server/)
- [ ] [T002] [P0] [Setup] Create `pyproject.toml` with uv configuration, FastAPI>=0.104.0, Uvicorn>=0.24.0, python-multipart>=0.0.6, aiofiles>=23.2.0, marker-pdf, Pydantic>=2.0.0 (server/pyproject.toml)
- [ ] [T003] [P0] [Setup] Create `README.md` with server overview, architecture diagram, and quickstart reference (server/README.md)
- [ ] [T004] [P0] [Setup] Create `.env.example` with ServerConfig environment variables (PDF2MD_HOST, PDF2MD_PORT, PDF2MD_MAX_FILE_SIZE, etc.) (server/.env.example)
- [ ] [T005] [P0] [Setup] Create `tests/fixtures/test_pdfs/` directory with sample PDFs (valid.pdf, encrypted.pdf, corrupted.pdf) (tests/fixtures/test_pdfs/)

**Acceptance**: Running `uv sync` in server/ creates virtual environment and installs all dependencies without errors.

---

## Phase 2: Foundational (27 tasks)

*Core infrastructure, models, and utilities (BLOCKS all user stories)*

### Configuration & Logging (6 tasks)

- [ ] [T006] [P0] [Foundation] Create `ServerConfig` Pydantic model in `core/config.py` with host, port, max_file_size, max_conversions, temp_dir, timeout, log_level, log_format fields (server/src/pdf2md_server/core/config.py)
- [ ] [T007] [P0] [Foundation] Implement environment variable loading in `ServerConfig` using `ConfigDict` with `PDF2MD_` prefix (server/src/pdf2md_server/core/config.py)
- [ ] [T008] [P0] [Foundation] Create `LogConfig` Pydantic model in `core/logging.py` with format ("text" or "json"), level, log_file_path, structured_enabled fields (server/src/pdf2md_server/core/logging.py)
- [ ] [T009] [P0] [Foundation] Implement structured logging setup with `structlog` that switches between text and JSON format based on `PDF2MD_LOG_FORMAT` env var (server/src/pdf2md_server/core/logging.py)
- [ ] [T010] [P0] [Foundation] Add request ID context processor to logging that includes `request_id` in all log messages (server/src/pdf2md_server/core/logging.py)
- [ ] [T011] [P0] [Foundation] Write unit tests for `ServerConfig` and `LogConfig` with valid and invalid environment variables (tests/unit/test_config.py)

**Test Criteria**: Config loads from env vars, logging switches format when `PDF2MD_LOG_FORMAT=json` is set.

### Data Models (5 tasks)

- [ ] [T012] [P0] [Foundation] Create `ConversionRequest` Pydantic model in `models/requests.py` with request_id, client_ip, filename, file_size, content_type, upload_time fields (server/src/pdf2md_server/models/requests.py)
- [ ] [T013] [P0] [Foundation] Create `ConversionResponse`, `HealthStatus`, `ErrorResponse` Pydantic models in `models/responses.py` with all required fields from data-model.md (server/src/pdf2md_server/models/responses.py)
- [ ] [T014] [P0] [Foundation] Create `TempFileInfo` dataclass in `models/entities.py` with temp_path, original_filename, uuid, upload_time, file_size, permissions fields (server/src/pdf2md_server/models/entities.py)
- [ ] [T015] [P0] [Foundation] Add UUID v4 validator to `ConversionRequest.request_id` and `ErrorResponse.request_id` fields (server/src/pdf2md_server/models/requests.py, server/src/pdf2md_server/models/responses.py)
- [ ] [T016] [P0] [Foundation] Write unit tests for all Pydantic models with valid and invalid data (tests/unit/test_models.py)

**Test Criteria**: Models validate correctly, UUID validator rejects invalid formats, all required fields enforced.

### Exception Hierarchy (4 tasks)

- [ ] [T017] [P0] [Foundation] Create base `PDF2MDError` exception class in `core/exceptions.py` with error_code and error_detail attributes (server/src/pdf2md_server/core/exceptions.py)
- [ ] [T018] [P0] [Foundation] Create `ConversionError`, `ValidationError`, `ResourceError` subclasses of `PDF2MDError` (server/src/pdf2md_server/core/exceptions.py)
- [ ] [T019] [P0] [Foundation] Implement custom exception handlers for FastAPI that convert exceptions to proper HTTP status codes (400, 500, 503) with ErrorResponse JSON (server/src/pdf2md_server/core/exceptions.py)
- [ ] [T020] [P0] [Foundation] Write unit tests for exception handlers verifying correct HTTP status codes and error response format (tests/unit/test_exceptions.py)

**Test Criteria**: Raising custom exception in route handler returns correct HTTP status and ErrorResponse JSON.

### File Handler Service (7 tasks)

- [ ] [T021] [P0] [Foundation] Create `FileHandler` class in `services/file_handler.py` with async `save_upload_file()` and `cleanup_temp_files()` methods (server/src/pdf2md_server/services/file_handler.py)
- [ ] [T022] [P0] [Foundation] Implement async file upload streaming with `aiofiles` using 64KB chunks to avoid loading entire file into memory (server/src/pdf2md_server/services/file_handler.py)
- [ ] [T023] [P0] [Foundation] Implement UUID-prefixed temp file naming with `/{uuid}-{sanitized_filename}` pattern (server/src/pdf2md_server/services/file_handler.py)
- [ ] [T024] [P0] [Foundation] Implement file permission setting to 0o600 (owner read/write only) after saving temp file (server/src/pdf2md_server/services/file_handler.py)
- [ ] [T025] [P0] [Foundation] Implement `cleanup_temp_files()` method that removes both PDF and MD temp files (server/src/pdf2md_server/services/file_handler.py)
- [ ] [T026] [P0] [Foundation] Add disk space check using `shutil.disk_usage` that raises `ResourceError` if available space < 2GB (server/src/pdf2md_server/services/file_handler.py)
- [ ] [T027] [P0] [Foundation] Write unit tests for file upload streaming, temp file cleanup, and disk space check (tests/unit/test_file_handler.py)

**Test Criteria**: 500MB file uploads without memory spike, temp files cleaned up, disk space check rejects when < 2GB.

### PDF Validation Utilities (5 tasks)

- [ ] [T028] [P0] [Foundation] Create `validate_pdf_extension()` function in `utils/pdf_utils.py` that checks file extension is `.pdf` (case-insensitive) (server/src/pdf2md_server/utils/pdf_utils.py)
- [ ] [T029] [P0] [Foundation] Create `validate_pdf_magic_bytes()` function that reads first 5 bytes and checks for `%PDF-` string (server/src/pdf2md_server/utils/pdf_utils.py)
- [ ] [T030] [P0] [Foundation] Create `is_pdf_encrypted()` function using `pikepdf` that returns True if PDF has encryption flag (server/src/pdf2md_server/utils/pdf_utils.py)
- [ ] [T031] [P0] [Foundation] Create `sanitize_filename()` function that removes path traversal sequences (`..`, `/`, `\`) and dangerous characters (server/src/pdf2md_server/utils/pdf_utils.py)
- [ ] [T032] [P0] [Foundation] Write unit tests for PDF validation functions with valid PDFs, encrypted PDFs, and malicious filenames (tests/unit/test_pdf_utils.py)

**Test Criteria**: Extension validator accepts `.PDF` and `.pdf`, magic bytes validator rejects non-PDFs, encryption detector flags password-protected PDFs, filename sanitizer removes `../../../etc/passwd` to `etcpasswd`.

**Acceptance**: All foundational services can be imported and instantiated without errors. Unit tests pass with >80% coverage.

---

## Phase 3: User Story 1 - Single PDF Conversion Endpoint (15 tasks)

*Priority: P1 | Independent Test: POST /convert with valid PDF returns Markdown*

### Conversion Service (5 tasks)

- [ ] [T033] [P1] [Story1] Create `ConversionService` class in `services/conversion.py` with async `convert_pdf()` method (server/src/pdf2md_server/services/conversion.py)
- [ ] [T034] [P1] [Story1] Implement Marker library integration using `asyncio.to_thread()` to wrap blocking `convert_single_pdf()` call (server/src/pdf2md_server/services/conversion.py)
- [ ] [T035] [P1] [Story1] Implement conversion timeout handling that raises `ConversionError` if conversion exceeds ServerConfig.timeout (default 300s) (server/src/pdf2md_server/services/conversion.py)
- [ ] [T036] [P1] [Story1] Add GPU OOM detection that catches CUDA out-of-memory errors, releases GPU memory, and raises `ResourceError` (server/src/pdf2md_server/services/conversion.py)
- [ ] [T037] [P1] [Story1] Write unit tests for conversion service with mock Marker engine, testing success, timeout, and GPU OOM scenarios (tests/unit/test_conversion.py)

**Test Criteria**: Conversion service calls Marker, returns MD file path, handles timeout and GPU OOM gracefully.

### Convert Endpoint (6 tasks)

- [ ] [T038] [P1] [Story1] Create `POST /convert` route handler in `api/routes/convert.py` accepting FastAPI `UploadFile` parameter (server/src/pdf2md_server/api/routes/convert.py)
- [ ] [T039] [P1] [Story1] Implement file upload validation chain: extension → magic bytes → encryption → file size (500MB max) (server/src/pdf2md_server/api/routes/convert.py)
- [ ] [T040] [P1] [Story1] Call `FileHandler.save_upload_file()` to stream uploaded PDF to temp directory with UUID prefix (server/src/pdf2md_server/api/routes/convert.py)
- [ ] [T041] [P1] [Story1] Call `ConversionService.convert_pdf()` with temp PDF path and output MD path (server/src/pdf2md_server/api/routes/convert.py)
- [ ] [T042] [P1] [Story1] Read converted Markdown file with `aiofiles` and return `StreamingResponse` with `Content-Type: text/markdown; charset=utf-8` (server/src/pdf2md_server/api/routes/convert.py)
- [ ] [T043] [P1] [Story1] Implement response headers: `X-Request-ID` (UUID), `X-Pages-Processed` (integer), `X-Conversion-Time` (float seconds), `Content-Disposition` (attachment filename) (server/src/pdf2md_server/api/routes/convert.py)

**Test Criteria**: POST /convert with valid.pdf returns 200 OK, Markdown content, and all required headers.

### Error Responses (4 tasks)

- [ ] [T044] [P1] [Story1] Return 400 Bad Request with ErrorResponse when file validation fails (extension, magic bytes, encryption, size) (server/src/pdf2md_server/api/routes/convert.py)
- [ ] [T045] [P1] [Story1] Return 500 Internal Server Error with ErrorResponse when conversion fails with safe error message (no stack traces) (server/src/pdf2md_server/api/routes/convert.py)
- [ ] [T046] [P1] [Story1] Return 503 Service Unavailable with ErrorResponse when GPU OOM or disk space < 2GB (server/src/pdf2md_server/api/routes/convert.py)
- [ ] [T047] [P1] [Story1] Write integration tests for POST /convert covering success path, validation errors (400), conversion failure (500), and resource limits (503) (tests/integration/test_convert_api.py)

**Test Criteria**: Invalid PDF returns 400 with error_code and troubleshooting_hints. Conversion failure returns 500 without leaking internals. GPU OOM returns 503 with retry suggestion.

**Acceptance**: `curl -X POST http://localhost:8000/convert -F "file=@valid.pdf" -o output.md` succeeds with 200 OK, valid Markdown content, X-Pages-Processed header present.

---

## Phase 4: User Story 2 - File Upload with Streaming (10 tasks)

*Priority: P1 | Independent Test: Upload 500MB PDF, memory usage stable*

### Streaming Upload (5 tasks)

- [ ] [T048] [P1] [Story2] Configure FastAPI `UploadFile.spool_max_size` to 0 to force immediate disk write (no in-memory buffering) (server/src/pdf2md_server/api/routes/convert.py)
- [ ] [T049] [P1] [Story2] Implement chunked file reading from `UploadFile.file` with 64KB chunk size (not loading entire file into memory) (server/src/pdf2md_server/services/file_handler.py)
- [ ] [T050] [P1] [Story2] Implement chunked async file writing with `aiofiles.open()` in binary append mode (server/src/pdf2md_server/services/file_handler.py)
- [ ] [T051] [P1] [Story2] Add upload progress logging every 10MB with request_id and bytes written (server/src/pdf2md_server/services/file_handler.py)
- [ ] [T052] [P1] [Story2] Write unit test for file upload streaming that verifies memory usage stays < 500MB with 100MB test file (tests/unit/test_file_handler.py)

**Test Criteria**: Uploading 500MB PDF uses < 1GB RAM (not 3GB+ if loaded into memory). Progress logs show chunked writes.

### File Size Validation (3 tasks)

- [ ] [T053] [P1] [Story2] Implement file size validation during upload that reads `Content-Length` header and checks against ServerConfig.max_file_size (server/src/pdf2md_server/api/routes/convert.py)
- [ ] [T054] [P1] [Story2] Return 400 Bad Request with ErrorResponse if `Content-Length` exceeds 500MB (FR-API-006) (server/src/pdf2md_server/api/routes/convert.py)
- [ ] [T055] [P1] [Story2] Write integration test for file size validation with 600MB file returning 400 and error_code "FileTooLarge" (tests/integration/test_convert_api.py)

**Test Criteria**: Upload 600MB file returns immediate 400 before processing, error message shows actual and max size.

### Upload Interruption Handling (2 tasks)

- [ ] [T056] [P1] [Story2] Implement try/except around file upload that catches `ConnectionError` and cleans up partial temp files (server/src/pdf2md_server/services/file_handler.py)
- [ ] [T057] [P1] [Story2] Write integration test for upload interruption by closing connection mid-upload and verifying temp directory cleanup (tests/integration/test_convert_api.py)

**Test Criteria**: Disconnecting during 100MB upload leaves no partial files in /tmp/pdf2md/.

**Acceptance**: Uploading 500MB PDF completes in < 5 seconds on gigabit network (100 MB/s throughput). Memory usage stays < 2GB during upload.

---

## Phase 5: User Story 3 - Health Check Endpoint (6 tasks)

*Priority: P2 | Independent Test: GET /health returns JSON status*

### Health Endpoint (4 tasks)

- [ ] [T058] [P2] [Story3] Create `GET /health` route handler in `api/routes/health.py` (server/src/pdf2md_server/api/routes/health.py)
- [ ] [T059] [P2] [Story3] Implement `HealthStatus` response with status ("healthy" or "unhealthy"), version, gpu_available, active_conversions, max_conversions, uptime_seconds fields (server/src/pdf2md_server/api/routes/health.py)
- [ ] [T060] [P2] [Story3] Implement GPU availability check using `torch.cuda.is_available()` (server/src/pdf2md_server/api/routes/health.py)
- [ ] [T061] [P2] [Story3] Implement uptime tracking using `time.time() - server_start_time` stored in FastAPI app.state (server/src/pdf2md_server/main.py)

**Test Criteria**: GET /health returns 200 OK with all required fields, gpu_available=True if NVIDIA GPU present.

### Active Conversions Tracking (2 tasks)

- [ ] [T062] [P2] [Story3] Create `ConversionTracker` class in `services/conversion.py` using `asyncio.Semaphore(10)` to track active conversions (server/src/pdf2md_server/services/conversion.py)
- [ ] [T063] [P2] [Story3] Write integration test for GET /health that verifies active_conversions count increments during conversions (tests/integration/test_health_api.py)

**Test Criteria**: Health check shows active_conversions=0 when idle, active_conversions=3 when 3 conversions in progress.

**Acceptance**: `curl http://localhost:8000/health` returns 200 OK in < 100ms with JSON containing status, version, gpu_available, active_conversions fields.

---

## Phase 6: User Story 4 - Error Response Format (9 tasks)

*Priority: P2 | Independent Test: Invalid request returns structured ErrorResponse*

### Error Response Structure (4 tasks)

- [ ] [T064] [P2] [Story4] Update all error responses to use `ErrorResponse` Pydantic model with error_code, error_detail, troubleshooting_hints, request_id, timestamp fields (server/src/pdf2md_server/api/routes/convert.py)
- [ ] [T065] [P2] [Story4] Implement error_code enum with values: InvalidRequest, InvalidPDF, EncryptedPDF, FileTooLarge, ConversionError, GPUOutOfMemory, InsufficientDiskSpace, ServiceUnavailable (server/src/pdf2md_server/models/responses.py)
- [ ] [T066] [P2] [Story4] Add troubleshooting hints for each error type (e.g., EncryptedPDF: "Remove password protection using: pdftk input.pdf output output.pdf user_pw PROMPT") (server/src/pdf2md_server/api/routes/convert.py)
- [ ] [T067] [P2] [Story4] Ensure all error responses include current Unix timestamp in timestamp field (server/src/pdf2md_server/models/responses.py)

**Test Criteria**: All error responses follow same structure with error_code, error_detail, troubleshooting_hints array, request_id (UUID), timestamp (float).

### Validation Errors (3 tasks)

- [ ] [T068] [P2] [Story4] Return 400 with error_code "InvalidRequest" when file extension is not .pdf (server/src/pdf2md_server/api/routes/convert.py)
- [ ] [T069] [P2] [Story4] Return 400 with error_code "InvalidPDF" when magic bytes validation fails (server/src/pdf2md_server/api/routes/convert.py)
- [ ] [T070] [P2] [Story4] Return 400 with error_code "EncryptedPDF" with troubleshooting hint "Remove password protection using: pdftk input.pdf output output.pdf user_pw PROMPT" (server/src/pdf2md_server/api/routes/convert.py)

**Test Criteria**: Uploading .txt file returns 400 with error_code "InvalidRequest" and hint "Ensure the file is a PDF document with .pdf extension". Encrypted PDF returns 400 with error_code "EncryptedPDF" and pdftk command hint.

### Retry-After Header (2 tasks)

- [ ] [T071] [P2] [Story4] Add `Retry-After` header to 503 responses with value 30 for GPU OOM, 3600 for disk space (server/src/pdf2md_server/api/routes/convert.py)
- [ ] [T072] [P2] [Story4] Write integration tests for all error response types verifying correct HTTP status, error_code, and troubleshooting hints (tests/integration/test_convert_api.py)

**Test Criteria**: 503 GPU OOM includes `Retry-After: 30` header. 503 disk space includes `Retry-After: 3600` header.

**Acceptance**: Sending invalid file type returns 400 with JSON body containing error_code, error_detail, troubleshooting_hints array, request_id, timestamp.

---

## Phase 7: User Story 5 - Concurrent Request Handling (8 tasks)

*Priority: P3 | Independent Test: 10 concurrent requests complete successfully*

### Concurrency Limiting (4 tasks)

- [ ] [T073] [P3] [Story5] Implement `asyncio.Semaphore(10)` in `ConversionTracker` to limit concurrent conversions (server/src/pdf2md_server/services/conversion.py)
- [ ] [T074] [P3] [Story5] Wrap conversion task in `async with conversion_semaphore:` block (server/src/pdf2md_server/services/conversion.py)
- [ ] [T075] [P3] [Story5] Return 503 Service Unavailable with error_code "ServiceUnavailable" when semaphore acquisition would block (FR-API-038) (server/src/pdf2md_server/api/routes/convert.py)
- [ ] [T076] [P3] [Story5] Write integration test that submits 11 concurrent requests and verifies 10 succeed, 11th returns 503 (tests/integration/test_convert_api.py)

**Test Criteria**: 10 concurrent conversions run in parallel. 11th request returns immediate 503 without queuing.

### Task Isolation (4 tasks)

- [ ] [T077] [P3] [Story5] Launch each conversion in `asyncio.create_task()` with complete exception isolation (server/src/pdf2md_server/services/conversion.py)
- [ ] [T078] [P3] [Story5] Wrap task execution in try/except that logs errors with request_id without raising to main event loop (server/src/pdf2md_server/services/conversion.py)
- [ ] [T079] [P3] [Story5] Ensure failed task cleans up its temp files and releases semaphore before exiting (server/src/pdf2md_server/services/conversion.py)
- [ ] [T080] [P3] [Story5] Write integration test that verifies one conversion failure doesn't affect other concurrent conversions or crash server (tests/integration/test_convert_api.py)

**Test Criteria**: Submit 5 concurrent requests, 1 with corrupted PDF. 4 succeed with 200 OK, 1 fails with 500. No cascading failures. Server remains healthy (health check returns 200). All temp files cleaned up. Server event loop continues processing requests after failure.

**Acceptance**: Sending 10 concurrent POST /convert requests with valid PDFs results in all 10 completing successfully with 200 OK responses.

---

## Phase 8: Polish & Cross-Cutting Concerns (7 tasks)

*Startup/shutdown, middleware, monitoring, deployment*

### Startup & Shutdown Handlers (4 tasks)

- [ ] [T081] [P0] [Polish] Implement FastAPI `@app.on_event("startup")` handler in `main.py` that creates `/tmp/pdf2md/` directory if missing (server/src/pdf2md_server/main.py)
- [ ] [T082] [P0] [Polish] Implement startup handler that cleans up orphaned temp files from previous runs (server/src/pdf2md_server/main.py)
- [ ] [T083] [P0] [Polish] Implement startup handler that validates GPU availability and logs warning if not present (server/src/pdf2md_server/main.py)
- [ ] [T084] [P0] [Polish] Implement `@app.on_event("shutdown")` handler that waits for active conversions to complete (60s timeout) then cleans up temp directory (server/src/pdf2md_server/main.py)

**Test Criteria**: Server creates /tmp/pdf2md/ on startup if missing. Shutdown waits for active conversions then removes all temp files.

### Middleware (2 tasks)

- [ ] [T085] [P0] [Polish] Add GZip middleware to FastAPI app with `middleware=GZipMiddleware` (server/src/pdf2md_server/main.py)
- [ ] [T086] [P0] [Polish] Add CORS middleware with `allow_origins=["*"]` for internal network use (server/src/pdf2md_server/main.py)

**Test Criteria**: Response headers include `Content-Encoding: gzip` for large responses. CORS headers include `Access-Control-Allow-Origin: *`.

### Documentation & Deployment (1 task)

- [ ] [T087] [P0] [Polish] Verify FastAPI auto-generated OpenAPI docs at `/docs` and `/redoc` are accurate and complete (server/src/pdf2md_server/main.py)

**Test Criteria**: Visiting http://localhost:8000/docs shows interactive API docs with POST /convert and GET /health endpoints documented.

---

## Task Summary

| Phase | Tasks | Priority | User Story | Parallel? |
|-------|-------|----------|------------|-----------|
| Phase 1: Setup | 5 | P0 | Foundation | No |
| Phase 2: Foundational | 27 | P0 | Foundation | Partial |
| Phase 3: Story 1 (Convert Endpoint) | 15 | P1 | Single PDF Conversion | Yes (with Phase 4) |
| Phase 4: Story 2 (Streaming Upload) | 10 | P1 | File Upload with Streaming | Yes (with Phase 3) |
| Phase 5: Story 3 (Health Check) | 6 | P2 | Health Check Endpoint | Yes (with Phase 6) |
| Phase 6: Story 4 (Error Format) | 9 | P2 | Error Response Format | Yes (with Phase 5) |
| Phase 7: Story 5 (Concurrency) | 8 | P3 | Concurrent Request Handling | No (after Phase 6) |
| Phase 8: Polish | 7 | P0 | Cross-Cutting | Yes (with any phase) |
| **Total** | **87** | | | |

### Parallel Execution Strategy

**Maximum Parallelism** (after Phase 2):
- Team A: Phase 3 (User Story 1) - 15 tasks
- Team B: Phase 4 (User Story 2) - 10 tasks
- Team C: Phase 5 (User Story 3) - 6 tasks (after Phase 3/4)
- Team D: Phase 6 (User Story 4) - 9 tasks (after Phase 3/4)
- Team E: Phase 8 (Polish) - 7 tasks (anytime)

**Critical Path**: Phase 1 → Phase 2 → Phase 3 → Phase 7 → Phase 8 (52 tasks for MVP)

### Independent Testing Criteria

Each user story can be tested independently:

1. **User Story 1** (P1): `curl -X POST http://localhost:8000/convert -F "file=@valid.pdf" -o output.md`
   - Success: 200 OK, Markdown content, X-Pages-Processed header present

2. **User Story 2** (P1): `curl -X POST http://localhost:8000/convert -F "file=@large_100mb.pdf" -o output.md`
   - Success: Upload completes in < 1s on gigabit network, memory usage < 2GB

3. **User Story 3** (P2): `curl http://localhost:8000/health`
   - Success: 200 OK in < 100ms, JSON with status, version, gpu_available, active_conversions

4. **User Story 4** (P2): `curl -X POST http://localhost:8000/convert -F "file=@encrypted.pdf"`
   - Success: 400 Bad Request with error_code "EncryptedPDF" and troubleshooting hints

5. **User Story 5** (P3): `for i in {1..10}; do curl -X POST http://localhost:8000/convert -F "file=@valid.pdf" & done`
   - Success: All 10 requests complete successfully, no crashes, no GPU OOM

---

**Status**: ✅ Ready for implementation

**Next Step**: Run `/speckit.implement` to execute tasks in dependency order, or begin manual implementation starting with Phase 1 (T001-T005).
