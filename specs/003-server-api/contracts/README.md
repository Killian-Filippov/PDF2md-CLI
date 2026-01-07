# API Contracts: Server REST API

**Feature**: 003-server-api
**Date**: 2026-01-07
**Version**: 1.0.0

## Overview

This document describes the REST API contracts for the PDF2md-CLI server, including endpoints, request/response schemas, and error handling.

---

## Base URL

```
http://localhost:8000
```

**Note**: Server runs on HTTP only (internal network, per spec.md "Out of Scope" section).

---

## Endpoints

### 1. POST /convert

Convert PDF file to Markdown.

**Request**:
- Method: `POST`
- Path: `/convert`
- Content-Type: `multipart/form-data`
- Body: File upload with `file` field

**Request Headers**:
```
Content-Type: multipart/form-data
Content-Length: {file_size_bytes}
```

**Request Body**:
```
file: <PDF file contents>
```

**Validation**:
- File extension must be `.pdf` (case-insensitive)
- File magic bytes must start with `%PDF-`
- File must NOT be password-protected
- File size must be ≤ 500MB
- Filename sanitized (no path traversal)

**Success Response** (200 OK):
- Content-Type: `text/markdown; charset=utf-8`
- Headers:
  - `X-Request-ID`: UUID for tracing
  - `X-Pages-Processed`: Number of pages converted
  - `X-Conversion-Time`: Conversion duration in seconds
  - `Content-Disposition`: Attachment with original filename
- Body: Markdown file content

**Example**:
```bash
curl -X POST http://localhost:8000/convert \
  -F "file=@document.pdf" \
  -O -J

# Response headers:
HTTP/1.1 200 OK
Content-Type: text/markdown; charset=utf-8
X-Request-ID: abc-123-def-456
X-Pages-Processed: 15
X-Conversion-Time: 10.3
Content-Disposition: attachment; filename="document.md"

# Response body:
# Document Title

Document content converted to Markdown...
```

**Error Responses**:

**400 Bad Request** (Invalid file type):
```json
{
  "error_code": "InvalidRequest",
  "error_detail": "File type not supported: .txt. Expected: .pdf",
  "troubleshooting_hints": [
    "Ensure the file is a PDF document with .pdf extension"
  ],
  "request_id": "abc-123-def",
  "timestamp": 1704602645.123
}
```

**400 Bad Request** (Encrypted PDF):
```json
{
  "error_code": "EncryptedPDF",
  "error_detail": "PDF is password-protected and cannot be converted. Please remove the password and try again.",
  "troubleshooting_hints": [
    "Remove password protection using: pdftk input.pdf output output.pdf user_pw PROMPT",
    "Verify PDF is not password-protected in PDF reader"
  ],
  "request_id": "abc-123-def",
  "timestamp": 1704602645.123
}
```

**400 Bad Request** (File too large):
```json
{
  "error_code": "FileTooLarge",
  "error_detail": "File size (600.0 MB) exceeds maximum (500 MB)",
  "troubleshooting_hints": [
    "Split the PDF into smaller files using: pdfjam input.pdf -- pages 1-100 -- output smaller.pdf",
    "Compress the PDF using: gs -sDEVICE=pdfwrite -dPDFSETTINGS=/ebook -o output.pdf input.pdf"
  ],
  "request_id": "abc-123-def",
  "timestamp": 1704602645.123
}
```

**500 Internal Server Error** (Conversion failed):
```json
{
  "error_code": "ConversionError",
  "error_detail": "Conversion failed: PDF file is corrupted",
  "troubleshooting_hints": [
    "Try opening the file in a PDF reader to verify it's not corrupted",
    "Re-download or recreate the PDF file"
  ],
  "request_id": "abc-123-def",
  "timestamp": 1704602645.123
}
```

**503 Service Unavailable** (GPU OOM):
```json
{
  "error_code": "GPUOutOfMemory",
  "error_detail": "GPU out of memory. Please retry after 30 seconds.",
  "troubleshooting_hints": [
    "Wait 30 seconds for GPU memory to be released",
    "Reduce concurrent conversions"
  ],
  "request_id": "abc-123-def",
  "timestamp": 1704602645.123
}
```

Headers:
- `Retry-After`: 30

**503 Service Unavailable** (Insufficient disk space):
```json
{
  "error_code": "InsufficientDiskSpace",
  "error_detail": "Server is temporarily out of disk space",
  "troubleshooting_hints": [
    "Please try again later",
    "Administrator: Check disk usage with 'df -h /tmp/pdf2md'"
  ],
  "request_id": "abc-123-def",
  "timestamp": 1704602645.123
}
```

Headers:
- `Retry-After`: 3600

---

### 2. GET /health

Health check endpoint for monitoring and load balancers.

**Request**:
- Method: `GET`
- Path: `/health`

**Success Response** (200 OK):
- Content-Type: `application/json`
- Body:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "gpu_available": true,
  "active_conversions": 3,
  "max_conversions": 10,
  "uptime_seconds": 3600.5
}
```

**Field Descriptions**:
- `status`: "healthy" or "unhealthy"
- `version`: Server version string
- `gpu_available`: Whether GPU is available for conversions
- `active_conversions`: Number of currently active conversions
- `max_conversions`: Maximum concurrent conversions (always 10)
- `uptime_seconds`: Server uptime in seconds since start

**Performance**:
- Must complete in under 100ms (SC-API-001)

---

## Error Response Format

All error responses follow this structure:

```json
{
  "error_code": "{ErrorCode}",
  "error_detail": "{Human-readable message}",
  "troubleshooting_hints": [
    "{Hint 1}",
    "{Hint 2}"
  ],
  "request_id": "{UUID}",
  "timestamp": {Unix timestamp}
}
```

**Error Codes**:
- `InvalidRequest`: Invalid file type or request format
- `InvalidPDF`: File is not a valid PDF
- `EncryptedPDF`: PDF is password-protected
- `FileTooLarge`: File size exceeds 500MB limit
- `ConversionError`: Conversion failed (unexpected error)
- `GPUOutOfMemory`: GPU ran out of memory
- `InsufficientDiskSpace`: Server disk space too low
- `ServiceUnavailable`: Server at maximum capacity (10 concurrent conversions)

**HTTP Status Codes**:
- 200: Success
- 400: Validation errors (file type, size, format, encryption)
- 500: Conversion errors (unexpected failures)
- 503: Resource limits (GPU OOM, disk space, concurrency limit)

---

## Request ID Tracing

All requests include a unique `X-Request-ID` header for tracing:

**Request**:
```
X-Request-ID: {auto-generated UUID}
```

**Response**:
```
X-Request-ID: {same UUID from request}
```

All log messages include this request_id for debugging and monitoring (FR-API-036).

---

## Rate Limiting & Concurrency

**No rate limiting** per client (explicitly out of scope per spec.md).

**Concurrency limiting**:
- Server allows maximum 10 concurrent conversions (FR-API-037)
- When at max capacity, returns 503 Service Unavailable
- Client should retry after delay indicated by `Retry-After` header

---

## CORS Configuration

Server is configured for internal network use:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST
Access-Control-Allow-Headers: *
```

**Note**: No authentication (internal network trust).

---

## OpenAPI Specification

FastAPI auto-generates OpenAPI 3.1 specification at `/docs` and `/openapi.json`.

**Interactive API docs**: `http://localhost:8000/docs`
**OpenAPI JSON**: `http://localhost:8000/openapi.json`

---

## Testing Examples

### Convert PDF (success)

```bash
curl -X POST http://localhost:8000/convert \
  -F "file=@document.pdf" \
  -H "X-Request-ID: test-123" \
  -o document.md
```

### Convert PDF (error - encrypted PDF)

```bash
curl -X POST http://localhost:8000/convert \
  -F "file=@encrypted.pdf" \
  -v
```

Expected response: 400 Bad Request with error_code "EncryptedPDF"

### Health Check

```bash
curl http://localhost:8000/health
```

Expected response: 200 OK with health status JSON

---

## Performance Requirements

- **Health check**: <100ms response time (SC-API-001)
- **File upload**: 100 MB/s throughput (SC-API-002)
- **Error validation**: <100ms (SC-API-005)
- **Server startup**: <5 seconds (SC-API-007)

---

## Next Steps

1. **Implementation**: Use FastAPI to implement endpoints
2. **Testing**: Use httpx.AsyncClient for integration tests
3. **Documentation**: Auto-generated OpenAPI docs at /docs
4. **Monitoring**: Health check endpoint for load balancers

---

**Summary**: Complete REST API contracts with 2 endpoints, structured error responses, request tracing, and performance requirements. Ready for implementation and testing.
