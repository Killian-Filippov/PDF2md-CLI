# Feature Specification: Server REST API

**Feature Branch**: `003-server-api`
**Created**: 2026-01-06
**Status**: Draft
**Input**: Architecture design document - Section 4.2 (Server Component) and Section 6 (API Design)

## User Scenarios & Testing

### User Story 1 - Single PDF Conversion Endpoint (Priority: P1)

A client application sends a PDF file via HTTP POST to convert it to Markdown. The server processes the conversion and returns the Markdown file.

**Why this priority**: This is the core API functionality - the only endpoint needed for MVP.

**Independent Test**: Can be tested by sending a POST request with a PDF file and verifying Markdown is returned.

**Acceptance Scenarios**:
1. **Given** a valid PDF file is posted to `/convert`, **When** server processes request, **Then** it returns 200 OK with Markdown file content
2. **Given** conversion succeeds, **When** client receives response, **Then** headers include `X-Pages-Processed`, `X-Conversion-Time`, and `Content-Disposition`
3. **Given** conversion takes 20 seconds, **When** client waits for response, **Then** server doesn't timeout (300 second limit)

---

### User Story 2 - File Upload with Streaming (Priority: P1)

The server accepts large PDF files (up to 500MB) via multipart/form-data upload without loading the entire file into memory.

**Why this priority**: Essential for handling real-world PDFs. Streaming prevents memory exhaustion.

**Independent Test**: Can be tested by uploading a 500MB PDF and monitoring server memory usage.

**Acceptance Scenarios**:
1. **Given** client uploads a 100MB PDF, **When** server receives upload, **Then** it streams file to disk in chunks (8192 bytes)
2. **Given** client uploads file exceeding 500MB, **When** server checks size, **Then** it returns 400 Bad Request with error message
3. **Given** upload is interrupted, **When** connection drops, **Then** server cleans up partial file

---

### User Story 3 - Health Check Endpoint (Priority: P2)

Monitoring systems need to check if the server is running and if GPU is available for conversions.

**Why this priority**: Useful for deployment and monitoring, but not critical for CLI functionality.

**Independent Test**: Can be tested by calling GET `/health` and verifying response contains status and GPU info.

**Acceptance Scenarios**:
1. **Given** server is running normally, **When** client calls `/health`, **Then** it returns 200 OK with status "healthy"
2. **Given** GPU is available, **When** health check is called, **Then** response includes `gpu_available: true`
3. **Given** server is processing 3 conversions, **When** health check is called, **Then** response shows `active_conversions: 3`

---

### User Story 4 - Error Response Format (Priority: P2)

Clients receive structured error responses that help users understand and resolve issues.

**Why this priority**: Important for user experience, but basic error messages are sufficient for MVP.

**Independent Test**: Can be tested by sending invalid requests and verifying error response structure.

**Acceptance Scenarios**:
1. **Given** client uploads non-PDF file, **When** server validates, **Then** it returns 400 with JSON body containing error, detail, and troubleshooting fields
2. **Given** conversion fails on server, **When** error occurs, **Then** response includes specific error type and actionable hints
3. **Given** server is overloaded, **When** client makes request, **Then** it returns 503 with `Retry-After` header

---

### User Story 5 - Concurrent Request Handling (Priority: P3)

Multiple clients can submit conversion requests simultaneously without server crash or data corruption.

**Why this priority**: Important for production use, but single-threaded processing is acceptable for MVP.

**Independent Test**: Can be tested by sending 10 concurrent requests and verifying all complete successfully.

**Acceptance Scenarios**:
1. **Given** 5 clients submit conversions simultaneously, **When** server processes requests, **Then** all 5 conversions complete without errors
2. **Given** 10 requests are submitted, **When** 11th request comes in, **Then** server queues or rejects with 503 (configurable max concurrency)
3. **Given** concurrent conversions use GPU, **When** multiple jobs process, **Then** GPU resources are managed without OOM errors

---

## Clarifications

### Session 2026-01-07

- Q: When GPU runs out of memory during OCR, what recovery strategy should the server use? → A: Immediately release GPU memory, log warning, return 503 Service Unavailable with message suggesting client retry later. Avoid full CUDA context restart to prevent disrupting other concurrent conversions.
- Q: At what disk space threshold should the server start rejecting new requests? → B: Reject new conversion requests when available disk space falls below 2GB to ensure sufficient space for conversion operations and temporary files.
- Q: How should the server format logs for request tracing in concurrent scenarios? → C: Hybrid mode - human-readable text logs in development, switchable to structured JSON logs in production via `PDF2MD_LOG_FORMAT=json` environment variable
- Q: How should concurrent conversion tasks handle failures to prevent cascading errors? → A: Complete isolation - each conversion task runs in independent asyncio.Task with try/except catching all exceptions, ensuring one task's failure does not propagate to other tasks or main event loop
- Q: How should the server handle password-protected PDF files? → A: Fast-fail rejection - immediately detect PDF encryption flag after upload, return 400 Bad Request with error message "PDF is password-protected and cannot be converted. Please remove the password and try again.", do not attempt decryption or conversion

---

## Edge Cases

- What happens if client disconnects during file upload?
- What happens if conversion fails halfway through?
- What happens if server runs out of disk space? → Check available space on startup; reject new requests with 503 when available space < 2GB; clean up temp files immediately after conversion
- What happens if PDF is password-protected? → Immediately detect encryption flag and return 400 with message "PDF is password-protected and cannot be converted. Please remove the password and try again."
- What happens if PDF has malformed structure?
- What happens if GPU runs out of memory during OCR? → Release GPU memory, return 503 with retry suggestion
- What happens if multiple files have same UUID (collision)?
- What happens if temporary directory permissions are wrong?
- What happens if one conversion task fails while others are running? → Task isolation ensures other tasks continue; failed task logs error and returns 500 to client without affecting active tasks

## Requirements

### Functional Requirements

**POST /convert Endpoint**:
- **FR-API-001**: Server MUST accept POST requests at `/convert` endpoint with `multipart/form-data` content type and `file` field
- **FR-API-002**: (DEPRECATED - merged into FR-API-001)
- **FR-API-004**: Server MUST validate file magic bytes start with `%PDF-`
- **FR-API-004a**: Server MUST detect PDF encryption flag and reject password-protected files with 400 error and message "PDF is password-protected and cannot be converted. Please remove the password and try again."
- **FR-API-005**: Server MUST sanitize filename to remove path traversal and dangerous characters
- **FR-API-006**: Server MUST reject files larger than 500MB with 400 error
- **FR-API-007**: Server MUST save uploaded file to temporary directory with UUID prefix
- **FR-API-008**: Server MUST use `aiofiles` for async file writing (non-blocking)
- **FR-API-009**: Server MUST call conversion engine with PDF and output paths
- **FR-API-010**: Server MUST read converted Markdown file and stream to client
- **FR-API-011**: Server MUST clean up both PDF and MD temp files after response
- **FR-API-012**: Server MUST set `Content-Type: text/markdown; charset=utf-8` header
- **FR-API-013**: Server MUST set `Content-Disposition` header with original filename
- **FR-API-014**: Server MUST include `X-Pages-Processed` header in response
- **FR-API-015**: Server MUST include `X-Conversion-Time` header in response
- **FR-API-016**: Server MUST include `X-Request-ID` header (UUID) for tracing

**Error Responses**:
- **FR-API-017**: Server MUST return 400 for invalid file type with structured error JSON
- **FR-API-018**: Server MUST return 400 for file size exceeded with max size in error message
- **FR-API-019**: Server MUST return 400 for invalid PDF format with troubleshooting hints
- **FR-API-019a**: Server MUST return 400 for password-protected PDF files with error message "PDF is password-protected and cannot be converted. Please remove the password and try again." and troubleshooting hint "Remove password protection using: pdftk input.pdf output output.pdf user_pw PROMPT"
- **FR-API-020**: Server MUST return 500 for conversion errors with safe error messages
- **FR-API-021**: Server MUST return 503 for GPU overloaded with `Retry-After` header
- **FR-API-021a**: Server MUST return 503 for GPU out of memory with explicit "GPU out of memory" message, release GPU memory immediately, and suggest client retry after 30 seconds
- **FR-API-021b**: Server MUST return 503 for insufficient disk space with explicit "Insufficient disk space" message and suggest client retry later
- **FR-API-022**: All error responses MUST contain `error`, `detail`, and `troubleshooting` fields
- **FR-API-023**: Error responses MUST NOT leak internal paths or stack traces to client

**GET /health Endpoint**:
- **FR-API-024**: Server MUST accept GET requests at `/health` endpoint
- **FR-API-025**: Server MUST return JSON with status, version, and system info
- **FR-API-026**: Response MUST include `status` field ("healthy" or "unhealthy")
- **FR-API-027**: Response MUST include `version` field matching server version
- **FR-API-028**: Response MUST include `gpu_available` boolean field
- **FR-API-029**: Response MUST include `active_conversions` integer field
- **FR-API-030**: Response MUST include `max_conversions` integer field
- **FR-API-031**: Response MUST include `uptime_seconds` float field
- **FR-API-032**: Health check MUST complete in under 100ms

**Middleware and Headers**:
- **FR-API-033**: Server MUST include GZip middleware for response compression
- **FR-API-034**: Server MUST include CORS middleware (allow all origins for internal network)
- **FR-API-035**: Server MUST generate unique `X-Request-ID` for each request
- **FR-API-036**: Server MUST log request ID with all log messages for tracing, supporting both text (default) and JSON (via `PDF2MD_LOG_FORMAT=json` env var) formats with fields: `timestamp`, `level`, `request_id`, `message`, optional `context`
- **FR-API-036a-d**: (DEPRECATED - merged into FR-API-036)

**Concurrency and Resource Management**:
- **FR-API-037**: Server MUST use asyncio semaphore to limit concurrent conversions (max 10)
- **FR-API-038**: Server MUST reject new requests when at max concurrency with 503 error
- **FR-API-038a**: Server MUST run each conversion task in independent asyncio.Task with complete exception isolation
- **FR-API-038b**: Server MUST wrap each conversion task in try/except block catching all exceptions to prevent cascading failures
- **FR-API-038c**: Server MUST log conversion task failures with request_id without affecting other active tasks
- **FR-API-039**: Server MUST use temporary directory `/tmp/pdf2md/` for uploaded files
- **FR-API-040**: Server MUST create temp directory on startup if it doesn't exist
- **FR-API-041**: Server MUST set file permissions to 600 (owner read/write only)
- **FR-API-042**: Server MUST clean up temp directory on startup (remove orphaned files)

**Startup and Shutdown**:
- **FR-API-043**: Server MUST run startup event handler to initialize resources
- **FR-API-044**: Server MUST run shutdown event handler to clean up resources
- **FR-API-045**: Startup MUST validate GPU availability and log warning if not present
- **FR-API-045a**: Startup MUST check available disk space and log warning if less than 5GB
- **FR-API-046**: Server MUST check available disk space before each conversion and reject with 503 if less than 2GB available with message "Insufficient disk space"
- **FR-API-047**: Shutdown MUST clean up temp directory (remove all files)
- **FR-API-048**: Shutdown MUST wait for active conversions to complete (60 second timeout)

### Key Entities

**ConversionRequest**:
- Represents incoming conversion request
- Attributes: file (UploadFile), filename, file_size, content_type, client_ip, request_id
- client_ip source: Extracted from `X-Forwarded-For` header if present (proxy/load balancer), otherwise from direct connection `client.host`

**ConversionResponse**:
- Represents successful conversion response
- Attributes: markdown_content (stream), pages_processed, conversion_time, output_size, request_id

**ErrorResponse**:
- Represents structured error response
- Attributes: error_code, error_detail, troubleshooting_hints, request_id, timestamp

**HealthStatus**:
- Represents server health status
- Attributes: status, version, gpu_available, active_conversions, max_conversions, uptime_seconds

**TempFileInfo**:
- Represents uploaded file info
- Attributes: temp_path, original_filename, uuid, upload_time, file_size

**LogConfig**:
- Represents logging configuration
- Attributes: format ("text" or "json"), level ("DEBUG", "INFO", "WARNING", "ERROR"), log_file_path (optional), structured_enabled (boolean)

## Success Criteria

### Measurable Outcomes

- **SC-API-001**: API endpoints respond within 500ms for metadata requests (health check)
- **SC-API-002**: File upload throughput reaches at least 100 MB/s per client on gigabit network (measured from client start to server disk write completion)
- **SC-API-003**: Server can handle 10 concurrent conversion requests without errors
- **SC-API-004**: Memory usage stays under 2GB with 5 concurrent large file (100MB) uploads
- **SC-API-005**: Error responses are returned in under 100ms (fast validation)
- **SC-API-006**: 99% of valid PDFs are converted without server crashes
- **SC-API-007**: Server startup completes in under 5 seconds
- **SC-API-008**: Temporary files are cleaned up within 1 second after conversion

## Assumptions

1. **Network**: Client and server on same internal network with <10ms latency
2. **Storage**: Server has at least 10GB free disk space for temporary files
3. **GPU**: NVIDIA GPU with CUDA 11.8+ is available and functional
4. **Python**: Server runs on Python 3.11+ with async/await support
5. **Dependencies**: Marker library and OCR models are pre-installed
6. **File System**: Server filesystem supports async file I/O (aiofiles)
7. **Permissions**: Server process has write permission to `/tmp/pdf2md/`
8. **Load**: Average of less than 10 concurrent conversions per minute

## Out of Scope

For the server API feature, the following are explicitly out of scope:

- WebSocket or real-time progress updates
- Job queue or async task processing (synchronous only)
- Persistent storage of converted documents
- Authentication or authorization
- Rate limiting per client
- API versioning (single version only)
- Batch conversion endpoint (multiple files in one request)
- Conversion cancellation endpoint
- Conversion history or job status querying
- API documentation beyond OpenAPI auto-generated docs
- Pagination (no list endpoints)
- Partial content or range requests
- HTTPS/SSL (HTTP only for internal network)
- API key management
