# API Contracts

**Feature**: PDF2md-CLI
**Version**: 1.0.0
**Date**: 2026-01-06

## Overview

This document defines the API contracts between the client and server components. All contracts must be adhered to for compatibility.

## Endpoint: POST /convert

### Purpose

Convert a PDF file to Markdown format.

### Request

**Method**: `POST`
**Path**: `/convert`
**Content-Type**: `multipart/form-data`

#### Request Body

```http
POST /convert HTTP/1.1
Host: 192.168.1.100:8000
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Length: [calculated]

------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="file"; filename="document.pdf"
Content-Type: application/pdf

[PDF binary data]
------WebKitFormBoundary7MA4YWxkTrZu0gW--
```

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | PDF file to convert (max 500MB) |

#### Request Headers

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Content-Type` | String | Yes | Must be `multipart/form-data` |
| `Content-Length` | Integer | Yes | Size of request body in bytes |

#### Validation Rules

1. **File Type**: Must be PDF file
   - Check extension: `.pdf` (case-insensitive)
   - Verify magic bytes: `%PDF-` at start of file

2. **File Size**: Maximum 500MB
   - Reject if `Content-Length > 500 * 1024 * 1024`

3. **Filename**: Must be sanitized
   - Max length: 255 characters
   - No path traversal: `../` or `\..`
   - No special characters: `< > : " | ? * \`

### Response

#### Success Response (200 OK)

```http
HTTP/1.1 200 OK
Content-Type: text/markdown; charset=utf-8
Content-Disposition: attachment; filename="document.md"
X-Pages-Processed: 42
X-Conversion-Time: 12.3
X-Request-ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890

# Document Title

This is the converted markdown content...

[Rest of Markdown content]
```

**Response Headers**:

| Header | Type | Description |
|--------|------|-------------|
| `Content-Type` | String | `text/markdown; charset=utf-8` |
| `Content-Disposition` | String | `attachment; filename="[original_name].md"` |
| `X-Pages-Processed` | Integer | Number of pages converted |
| `X-Conversion-Time` | Float | Conversion time in seconds |
| `X-Request-ID` | String | Unique request identifier (UUID) |

**Response Body**: Markdown file content as binary stream

#### Error Responses

**400 Bad Request** - Invalid Input

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json
X-Request-ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890

{
  "error": "InvalidRequest",
  "detail": "File type not supported: .txt. Expected: .pdf",
  "troubleshooting": "Ensure the file is a PDF document with .pdf extension."
}
```

**400 Bad Request** - File Size Exceeded

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json
X-Request-ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890

{
  "error": "FileTooLarge",
  "detail": "File size (750.5 MB) exceeds maximum allowed size (500 MB)",
  "troubleshooting": "Split the PDF into smaller files or compress the PDF."
}
```

**400 Bad Request** - Invalid PDF File

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json
X-Request-ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890

{
  "error": "InvalidPDF",
  "detail": "File does not appear to be a valid PDF document",
  "troubleshooting": "Verify the file is not corrupted and is a valid PDF. Try opening it in a PDF reader."
}
```

**500 Internal Server Error** - Conversion Failure

```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/json
X-Request-ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890

{
  "error": "ConversionError",
  "detail": "Failed to convert PDF: Marker processing failed - CUDA out of memory",
  "troubleshooting": "The PDF may be too large or have too many images. Try a smaller file or contact administrator."
}
```

**503 Service Unavailable** - Server Overloaded

```http
HTTP/1.1 503 Service Unavailable
Content-Type: application/json
X-Request-ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
Retry-After: 60

{
  "error": "ServiceUnavailable",
  "detail": "Server is currently processing maximum number of concurrent conversions",
  "troubleshooting": "Try again in a few minutes. Maximum concurrent conversions: 10"
}
```

### Error Response Schema

All error responses follow this structure:

```json
{
  "error": "<ErrorCode>",
  "detail": "<Human-readable description>",
  "troubleshooting": "<Actionable hints (optional)>"
}
```

### Error Codes

| Error Code | HTTP Status | Description | Retryable |
|------------|-------------|-------------|-----------|
| `InvalidRequest` | 400 | Invalid request parameters | No |
| `FileTooLarge` | 400 | File exceeds size limit | No |
| `InvalidPDF` | 400 | File is not a valid PDF | No |
| `ConversionError` | 500 | PDF conversion failed | No |
| `ServiceUnavailable` | 503 | Server at capacity | Yes |
| `InternalError` | 500 | Unexpected server error | No |

## Endpoint: GET /health

### Purpose

Health check endpoint for monitoring and load balancers.

### Request

**Method**: `GET`
**Path**: `/health`

```http
GET /health HTTP/1.1
Host: 192.168.1.100:8000
```

### Response

#### Success Response (200 OK)

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "healthy",
  "version": "1.0.0",
  "gpu_available": true,
  "active_conversions": 3,
  "max_conversions": 10,
  "uptime_seconds": 3600.5,
  "timestamp": "2026-01-06T12:00:00Z"
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `status` | String | Health status: `healthy` or `unhealthy` |
| `version` | String | Server version |
| `gpu_available` | Boolean | Whether GPU is accessible |
| `active_conversions` | Integer | Currently processing conversions |
| `max_conversions` | Integer | Maximum concurrent conversions |
| `uptime_seconds` | Float | Server uptime in seconds |
| `timestamp` | String | ISO 8601 timestamp |

## Client Behavior

### Upload Strategy

1. **Pre-upload Validation**:
   - Check file exists locally
   - Verify file extension is `.pdf`
   - Check file size ≤ 500MB
   - Read magic bytes to confirm PDF format

2. **Upload Process**:
   - Open file in binary mode
   - Stream upload with chunk size (default: 8192 bytes)
   - Display progress bar using `tqdm`
   - Handle timeout (default: 300 seconds)

3. **Retry Logic**:
   - Retry on network errors only
   - Exponential backoff: 2s, 4s, 8s
   - Max retries: 3
   - Don't retry on 4xx errors (client error)

### Download Strategy

1. **Stream Download**:
   - Receive response as stream
   - Write to file in chunks
   - Display progress bar

2. **File Handling**:
   - Save to original PDF location
   - Replace `.pdf` extension with `.md`
   - Check for file conflicts
   - Prompt user if overwrite disabled

### Error Handling

1. **Network Errors**:
   - Log error with details
   - Show troubleshooting hints
   - Exit with code 2

2. **Validation Errors**:
   - Show specific error message
   - Display file path and issue
   - Exit with code 3

3. **Conversion Errors**:
   - Display server error response
   - Show troubleshooting hints
   - Exit with code 4

## Security Considerations

### Client-Side

1. **Filename Sanitization**:
   - Remove path traversal attempts
   - Remove special characters
   - Limit length to 255 characters

2. **Input Validation**:
   - Validate file before upload
   - Check file size
   - Verify file type

### Server-Side

1. **Resource Limits**:
   - Enforce 500MB file size limit
   - Limit concurrent requests (max 10)
   - Timeout after 300 seconds

2. **Input Sanitization**:
   - Sanitize all filenames
   - Validate file type (magic bytes)
   - Prevent path traversal

3. **Rate Limiting** (Future):
   - Per-IP rate limits
   - Token bucket algorithm
   - Response: `429 Too Many Requests`

## OpenAPI Specification

```yaml
openapi: 3.0.0
info:
  title: PDF2MD Conversion Service
  version: 1.0.0
  description: Convert PDF files to Markdown using GPU acceleration

servers:
  - url: http://192.168.1.100:8000
    description: Internal network deployment

paths:
  /convert:
    post:
      summary: Convert PDF to Markdown
      description: Upload a PDF file and receive converted Markdown
      operationId: convertPdf
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required:
                - file
              properties:
                file:
                  type: string
                  format: binary
                  description: PDF file to convert (max 500MB)
      responses:
        '200':
          description: Successful conversion
          content:
            text/markdown:
              schema:
                type: string
                example: "# Document Title\n\nConverted content..."
          headers:
            X-Pages-Processed:
              schema:
                type: integer
                example: 42
            X-Conversion-Time:
              schema:
                type: number
                format: float
                example: 12.3
            X-Request-ID:
              schema:
                type: string
                format: uuid
        '400':
          description: Invalid request
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
          examples:
            invalidFileType:
              value:
                error: "InvalidRequest"
                detail: "File type not supported: .txt. Expected: .pdf"
                troubleshooting: "Ensure the file is a PDF document."
            fileTooLarge:
              value:
                error: "FileTooLarge"
                detail: "File size (750.5 MB) exceeds maximum (500 MB)"
                troubleshooting: "Split the PDF into smaller files."
        '500':
          description: Conversion error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
          examples:
            conversionFailed:
              value:
                error: "ConversionError"
                detail: "Failed to convert PDF: CUDA out of memory"
                troubleshooting: "Try a smaller file or contact administrator."
        '503':
          description: Service unavailable
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
          headers:
            Retry-After:
              schema:
                type: integer
                example: 60

  /health:
    get:
      summary: Health check
      description: Check server health and status
      operationId: healthCheck
      responses:
        '200':
          description: Server is healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: "healthy"
                  version:
                    type: string
                    example: "1.0.0"
                  gpu_available:
                    type: boolean
                    example: true
                  active_conversions:
                    type: integer
                    example: 3
                  max_conversions:
                    type: integer
                    example: 10
                  uptime_seconds:
                    type: number
                    format: float
                    example: 3600.5
                  timestamp:
                    type: string
                    format: date-time
                    example: "2026-01-06T12:00:00Z"

components:
  schemas:
    ErrorResponse:
      type: object
      required:
        - error
        - detail
      properties:
        error:
          type: string
          description: Error code
          example: "InvalidRequest"
        detail:
          type: string
          description: Human-readable error description
          example: "File type not supported"
        troubleshooting:
          type: string
          description: Actionable troubleshooting hints
          example: "Ensure the file is a PDF document."
```

## Testing Contracts

### Contract Tests

Use `pytest` + `httpx` to verify API contracts:

```python
def test_convert_success_contract(client):
    """Test successful conversion response contract."""
    pdf_content = b"%PDF-1.4\ntest"

    response = client.post(
        "/convert",
        files={"file": ("test.pdf", pdf_content, "application/pdf")}
    )

    # Assert status code
    assert response.status_code == 200

    # Assert headers
    assert response.headers["content-type"] == "text/markdown; charset=utf-8"
    assert "content-disposition" in response.headers
    assert "x-pages-processed" in response.headers
    assert "x-conversion-time" in response.headers
    assert "x-request-id" in response.headers

    # Assert body is markdown
    content = response.text
    assert content  # Not empty

def test_convert_invalid_file_contract(client):
    """Test error response contract for invalid file."""
    response = client.post(
        "/convert",
        files={"file": ("test.txt", b"not pdf", "text/plain")}
    )

    # Assert error response structure
    assert response.status_code == 400
    data = response.json()

    assert "error" in data
    assert "detail" in data
    assert isinstance(data["error"], str)
    assert isinstance(data["detail"], str)
```

---

**Contract Version**: 1.0.0
**Last Updated**: 2026-01-06
