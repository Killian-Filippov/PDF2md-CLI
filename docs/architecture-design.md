# PDF2md-CLI Architecture Design & Technical Solution

**Version**: 1.0
**Date**: 2026-01-06
**Status**: Draft
**Authors**: Project Team

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Principles](#2-architecture-principles)
3. [System Architecture](#3-system-architecture)
4. [Component Design](#4-component-design)
5. [Data Flow](#5-data-flow)
6. [API Design](#6-api-design)
7. [Data Models](#7-data-models)
8. [Error Handling Strategy](#8-error-handling-strategy)
9. [Security Design](#9-security-design)
10. [Technology Stack](#10-technology-stack)
11. [Deployment Architecture](#11-deployment-architecture)
12. [Performance Considerations](#12-performance-considerations)
13. [Testing Strategy](#13-testing-strategy)

---

## 1. System Overview

### 1.1 Purpose

PDF2md-CLI is a client-server tool that converts PDF files to Markdown format using a remote GPU-enabled server. The system is designed for internal network deployment, focusing on simplicity, robustness, and maintainability.

### 1.2 Key Requirements

**Functional Requirements (from spec.md)**:
- FR-001 to FR-027: Complete feature set
- Support single file conversion (MVP)
- Handle files up to 500MB
- Convert 10-page PDF in <30 seconds
- Support 10 concurrent requests
- Provide clear error messages

**Non-Functional Requirements**:
- **Robustness**: Handle network failures, conversion errors, timeouts
- **Readability**: Follow Python conventions (PEP 8), self-documenting code
- **Maintainability**: Modular design, SOLID principles, DRY compliance
- **Complexity Control**: No over-engineering, YAGNI compliance

### 1.3 Scope and Boundaries

**In Scope (MVP)**:
- Single file PDF to Markdown conversion
- Internal network deployment
- Configuration file management
- Basic error handling and retry
- Progress indication
- Temporary file cleanup

**Out of Scope (Future)**:
- Batch conversion (US3)
- Recursive directory processing (US3)
- Authentication/authorization
- Web UI
- Conversion history/queue management

---

## 2. Architecture Principles

The architecture follows the project constitution's core principles:

### 2.1 SOLID Principles

**Single Responsibility Principle (SRP)**:
- Each module has one reason to change
- Client handles CLI and HTTP communication only
- Server handles conversion and file management only

**Open/Closed Principle (OCP)**:
- Conversion engine can be swapped without modifying API
- New file formats can be added via extensions

**Liskov Substitution Principle (LSP)**:
- Any converter implementation can be substituted
- File storage backends are interchangeable

**Interface Segregation Principle (ISP)**:
- Small, focused interfaces for each component
- Clients don't depend on unused methods

**Dependency Inversion Principle (DIP)**:
- High-level modules depend on abstractions
- API layer depends on converter interface, not implementation

### 2.2 DRY Principle

**No Duplication**:
- Shared utilities in `shared/` module
- Common exception handling
- Single configuration management module

**Abstraction Over Duplication**:
- Generic file handler for both upload and download
- Reusable HTTP client wrapper

### 2.3 Simplicity and Anti-Over-Engineering

**YAGNI (You Aren't Gonna Need It)**:
- Synchronous API for MVP (async job queue added later if needed)
- Simple file storage (no database)
- Basic configuration (no complex validation)

**Simple Over Clever**:
- Straightforward error handling
- Clear function names
- Minimal abstraction layers

**No Premature Optimization**:
- Profile before optimizing
- Focus on readability first
- Optimize critical paths only after measurement

### 2.4 Robustness

**Explicit Error Handling**:
- All error paths handled explicitly
- Clear error messages for users
- Detailed logging for debugging

**Fail Fast and Loud**:
- Validate inputs at boundaries
- Raise errors immediately
- Don't propagate invalid state

**Graceful Degradation**:
- Clean up resources on errors
- Provide recovery guidance
- Never leave orphaned files

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Client Machine                        │
│  ┌────────────────────────────────────────────────────┐    │
│  │              CLI Interface (Typer)                 │    │
│  │  - Parse command-line arguments                     │    │
│  │  - Load configuration                               │    │
│  │  - Display progress/errors                          │    │
│  └─────────────────┬──────────────────────────────────┘    │
│                    │                                         │
│  ┌─────────────────▼──────────────────────────────────┐    │
│  │         HTTP Client (httpx)                         │    │
│  │  - Upload PDF with progress                         │    │
│  │  - Download Markdown                                │    │
│  │  - Handle network errors                            │    │
│  └─────────────────┬──────────────────────────────────┘    │
│                    │                                         │
│  ┌─────────────────▼──────────────────────────────────┐    │
│  │      File Handler & Validator                       │    │
│  │  - Validate PDF before upload                       │    │
│  │  - Check file conflicts                             │    │
│  │  - Save Markdown to original path                   │    │
│  └─────────────────┬──────────────────────────────────┘    │
│                    │                                         │
└────────────────────┼─────────────────────────────────────────┘
                     │
                     │ HTTP/HTTPS
                     │ (Multipart Upload)
                     │
┌────────────────────▼─────────────────────────────────────────┐
│                    Server (GPU Machine)                      │
│                     ┌──────────────────────┐                 │
│                     │   FastAPI App        │                 │
│                     │   - CORS handling    │                 │
│                     │   - Request logging  │                 │
│                     └──────────┬───────────┘                 │
│                                │                              │
│            ┌───────────────────┼───────────────────┐         │
│            │                   │                   │          │
│  ┌─────────▼────────┐  ┌──────▼───────┐  ┌───────▼──────┐  │
│  │  File Validator  │  │ File Manager │  │  Converter   │  │
│  │  - Type check    │  │ - Temp store │  │  - Marker    │  │
│  │  - Size limit    │  │ - Cleanup    │  │  - GPU OCR   │  │
│  │  - Sanitize name │  │ - Naming     │  │  - Output    │  │
│  └──────────────────┘  └──────────────┘  └──────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              GPU Resources (Marker)                     │  │
│  │  - CUDA acceleration                                    │  │
│  │  - OCR processing                                       │  │
│  │  - Table/image extraction                               │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Deployment Architecture

```
Internal Network (192.168.1.0/24)

┌─────────────────┐
│  User Machine   │
│  (Client)       │
│  192.168.1.10   │
└────────┬────────┘
         │
         │ HTTP Request
         │
┌────────▼───────────────────────┐
│  Server (Device A)             │
│  192.168.1.100:8000            │
│                                │
│  ┌──────────────────────────┐  │
│  │  Docker Container (opt.)  │  │
│  │  - FastAPI App           │  │
│  │  - Marker                │  │
│  │  - GPU Access            │  │
│  └──────────────────────────┘  │
│                                │
│  GPU: NVIDIA RTX 3080          │
│  Storage: /tmp/pdf2md/         │
└────────────────────────────────┘
```

### 3.3 Component Interaction Diagram

```
User → CLI → HTTP Client → [Network] → FastAPI → File Validator
                                                          ↓
                                                    File Manager
                                                          ↓
                                                    Converter (Marker)
                                                          ↓
                                                    File Manager (cleanup)
                                                          ↓
                                                    FastAPI → [Network] → HTTP Client → File Handler → Disk
```

---

## 4. Component Design

### 4.1 Client Component (`client/`)

#### 4.1.1 CLI Module (`cli.py`)

**Responsibility**: Parse commands, coordinate workflow

**Key Functions**:
```python
def convert(file_path: Path, output: Optional[Path] = None) -> None:
    """Convert PDF to Markdown via remote server."""

def config_init(server_url: str) -> None:
    """Initialize configuration file."""

def config_show() -> None:
    """Display current configuration."""
```

**Dependencies**: `typer`, `config.py`, `client.py`, `file_handler.py`

**Constitution Compliance**:
- ✅ SRP: Only CLI handling, no business logic
- ✅ DRY: Reuses configuration module

#### 4.1.2 Configuration Module (`config.py`)

**Responsibility**: Manage configuration file lifecycle

**Key Functions**:
```python
def load_config() -> ServerConfig:
    """Load config from ~/.pdf2md/config.json."""

def save_config(config: ServerConfig) -> None:
    """Save config to file."""

def get_config_path() -> Path:
    """Get platform-specific config path."""
```

**Configuration Schema**:
```python
class ServerConfig(BaseModel):
    server_url: str = "http://localhost:8000"
    timeout: int = 300
    chunk_size: int = 8192
    max_retries: int = 3
    verify_ssl: bool = True
    output_dir: Optional[Path] = None
    overwrite: bool = False
```

**Configuration Hierarchy** (priority order):
1. Command-line flags (highest)
2. Environment variables (`PDF2MD_SERVER_URL`, etc.)
3. Config file (`~/.pdf2md/config.json`)
4. Hardcoded defaults (lowest)

#### 4.1.3 HTTP Client Module (`client.py`)

**Responsibility**: Network communication with server

**Key Functions**:
```python
async def upload_pdf(pdf_path: Path, config: ServerConfig) -> ConversionResult:
    """Upload PDF and download converted Markdown."""

class PDF2MDClient:
    async def convert(self, pdf_path: Path) -> Path:
        """Convert PDF to Markdown."""

    async def _upload_with_progress(self, file: Path) -> None:
        """Upload file with progress bar."""

    async def _download_with_progress(self) -> Path:
        """Download result with progress bar."""
```

**Error Handling**:
- Network errors: Retry with exponential backoff (max 3 times)
- Server errors: Don't retry, log and exit
- Timeout: Configurable per request

**Progress Indication**:
- Upload: `tqdm` with bytes transferred
- Download: `tqdm` with bytes received
- Conversion: Server-side progress (if available)

#### 4.1.4 File Handler Module (`file_handler.py`)

**Responsibility**: Client-side file operations and validation

**Key Functions**:
```python
def validate_pdf_file(file_path: Path) -> None:
    """Validate PDF exists, readable, within size limit."""

def check_output_conflict(output_path: Path, overwrite: bool) -> None:
    """Check if output file exists, prompt or raise."""

def save_markdown(content: str, output_path: Path) -> None:
    """Save Markdown content to file."""
```

**Validation Checks**:
- File exists: `Path.exists()`
- File readable: `Path.stat().st_size > 0`
- File type: Magic bytes (`%PDF` at start)
- Size limit: `Path.stat().st_size <= 500 * 1024 * 1024`

#### 4.1.5 Exceptions Module (`exceptions.py`)

**Custom Exceptions**:
```python
class PDF2MDClientError(Exception): pass
class ConfigError(PDF2MDClientError): pass
class FileNotFoundError(ConfigError): pass
class ValidationError(PDF2MDClientError): pass
class NetworkError(PDF2MDClientError): pass
class ConversionError(PDF2MDClientError): pass
```

### 4.2 Server Component (`server/`)

#### 4.2.1 FastAPI Application (`main.py`)

**Responsibility**: HTTP server and request routing

**Key Configuration**:
```python
app = FastAPI(
    title="PDF2MD Conversion Service",
    version="1.0.0",
    description="Convert PDF files to Markdown using GPU acceleration"
)

# Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Internal network only
    allow_methods=["POST"],
    allow_headers=["*"]
)
```

**Startup/Shutdown**:
```python
@app.on_event("startup")
async def startup_event():
    """Initialize converter and cleanup temp directory."""
    logger.info("Starting PDF2MD server...")
    cleanup_temp_directory()

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources."""
    logger.info("Shutting down PDF2MD server...")
    cleanup_temp_directory()
```

#### 4.2.2 API Module (`api/convert.py`)

**Responsibility**: HTTP endpoint handling

**Endpoint**:
```python
@app.post("/convert")
async def convert_pdf(
    file: UploadFile,
    response: Response
) -> FileResponse:
    """
    Convert PDF to Markdown.

    - **file**: PDF file (multipart/form-data)
    - **returns**: Markdown file (application/octet-stream)
    - **raises**: 400 for invalid input, 500 for conversion errors
    """
```

**Request Flow**:
1. Validate file type and size
2. Save to temporary location
3. Call converter
4. Stream result back to client
5. Clean up temporary files

#### 4.2.3 Converter Module (`core/converter.py`)

**Responsibility**: PDF to Markdown conversion using Marker

**Key Interface**:
```python
class PDFConverter(ABC):
    @abstractmethod
    async def convert(self, pdf_path: Path, output_path: Path) -> None:
        """Convert PDF to Markdown."""

class MarkerConverter(PDFConverter):
    async def convert(self, pdf_path: Path, output_path: Path) -> None:
        """Convert using Marker library with GPU acceleration."""
        # Marker integration
        from marker.convert import convert_single_pdf

        convert_single_pdf(
            str(pdf_path),
            str(output_path),
            max_pages=None,  # No limit
            ocr_all_pages=True  # Use GPU OCR
        )
```

**Error Handling**:
- Catch Marker exceptions and wrap in `ConversionError`
- Log detailed error for debugging
- Provide user-friendly error message

#### 4.2.4 File Manager Module (`core/file_manager.py`)

**Responsibility**: Temporary file storage and cleanup

**Key Functions**:
```python
class TempFileManager:
    def __init__(self, base_dir: Path = Path("/tmp/pdf2md")):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, upload_file: UploadFile) -> Path:
        """Save uploaded file to temp location with unique name."""
        file_id = uuid4()
        temp_path = self.base_dir / f"{file_id}_{upload_file.filename}"

        async with aiofiles.open(temp_path, "wb") as f:
            while content := await upload_file.read(8192):
                await f.write(content)

        return temp_path

    async def cleanup(self, *paths: Path) -> None:
        """Delete temporary files."""
        for path in paths:
            try:
                path.unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Failed to cleanup {path}: {e}")

    def cleanup_all(self) -> None:
        """Remove all files in temp directory."""
        for file in self.base_dir.glob("*"):
            file.unlink(missing_ok=True)
```

**Naming Strategy**:
- Use UUID to prevent collisions
- Format: `{uuid}_{original_filename}`
- Example: `a1b2c3d4-document.pdf`

#### 4.2.5 File Validator Module (`utils/validation.py`)

**Responsibility**: Server-side input validation

**Key Functions**:
```python
async def validate_upload(
    file: UploadFile,
    max_size: int = 500 * 1024 * 1024
) -> None:
    """Validate uploaded file."""
    # Check file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    # Check file size (read first chunk)
    first_chunk = await file.read(8192)
    await file.seek(0)  # Reset for re-reading

    if not first_chunk.startswith(b"%PDF"):
        raise HTTPException(400, "Invalid PDF file")

    # Sanitize filename
    safe_filename = sanitize_filename(file.filename)
    file.filename = safe_filename

def sanitize_filename(filename: str) -> str:
    """Remove path traversal and dangerous characters."""
    # Remove directory paths
    filename = Path(filename).name
    # Remove dangerous characters
    filename = re.sub(r'[<>:"|?*]', '_', filename)
    return filename
```

#### 4.2.6 Models Module (`models/requests.py`)

**Responsibility**: Pydantic schemas for validation

**Schemas**:
```python
class ConversionRequest(BaseModel):
    """Request model for conversion."""

class ConversionResponse(BaseModel):
    """Response model for successful conversion."""
    output_filename: str
    pages_processed: int
    conversion_time: float

class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: str
    troubleshooting: str
```

---

## 5. Data Flow

### 5.1 Successful Conversion Flow

```
1. User runs: pdf2md document.pdf

2. CLI:
   - Load config from ~/.pdf2md/config.json
   - Validate document.pdf exists and is valid PDF
   - Check document.md doesn't exist (or ask to overwrite)

3. HTTP Client:
   - Connect to server_url (http://192.168.1.100:8000)
   - Upload document.pdf with multipart/form-data
   - Show progress bar: [################----] 80% 40MB/50MB

4. Server:
   - Receive request
   - Validate file type and size
   - Save to /tmp/pdf2md/{uuid}_document.pdf
   - Call converter.convert()

5. Converter (Marker):
   - Load PDF
   - Extract text, tables, images
   - Apply OCR (GPU accelerated)
   - Generate Markdown
   - Save to /tmp/pdf2md/{uuid}_document.md

6. Server:
   - Read Markdown file
   - Stream back to client with Content-Disposition header
   - Clean up both temp files

7. HTTP Client:
   - Download Markdown with progress bar
   - Save to document.md (original PDF location)

8. CLI:
   - Display success: "✓ Converted: document.md (42 pages, 12.3s)"
   - Exit with code 0
```

### 5.2 Error Flow - Network Failure

```
1. User runs: pdf2md document.pdf

2. HTTP Client:
   - Attempt to connect to server
   - Connection refused after 30s timeout

3. HTTP Client:
   - Log error: "Connection refused: 192.168.1.100:8000"
   - Retry 1: Wait 2s, try again (fail)
   - Retry 2: Wait 4s, try again (fail)
   - Retry 3: Wait 8s, try again (fail)
   - Max retries exceeded

4. CLI:
   - Display error:
     "✗ Network error: Could not connect to server
     Server: http://192.168.1.100:8000
     Troubleshooting:
     - Check server is running: 'curl http://192.168.1.100:8000/health'
     - Check network connectivity: 'ping 192.168.1.100'
     - Verify server_url in config: 'pdf2md config show'"

5. Exit with code 1
```

### 5.3 Error Flow - Invalid PDF

```
1. User runs: pdf2md document.txt

2. File Handler (client):
   - Validate file type
   - Check extension: .txt (not .pdf)
   - Read magic bytes: "Hello world" (not "%PDF")

3. CLI:
   - Display error:
     "✗ Invalid file: document.txt
     Expected: PDF file
     Got: Text file
     Hint: Use 'pdf2md document.pdf' to convert PDF files"

4. Exit with code 1
```

---

## 6. API Design

### 6.1 Endpoint Specification

#### POST /convert

Convert PDF file to Markdown.

**Request**:
```http
POST /convert HTTP/1.1
Host: 192.168.1.100:8000
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="document.pdf"
Content-Type: application/pdf

[PDF binary data]
------WebKitFormBoundary--
```

**Success Response** (200 OK):
```http
HTTP/1.1 200 OK
Content-Type: text/markdown
Content-Disposition: attachment; filename="document.md"
X-Pages-Processed: 42
X-Conversion-Time: 12.3

# Document Title

This is the converted markdown content...
```

**Error Responses**:

**400 Bad Request** (Invalid input):
```json
{
  "error": "InvalidRequest",
  "detail": "File size exceeds maximum allowed size",
  "troubleshooting": "Maximum file size is 500MB. Please split your PDF into smaller files."
}
```

**500 Internal Server Error** (Conversion failure):
```json
{
  "error": "ConversionError",
  "detail": "Failed to convert PDF: OCR processing failed",
  "troubleshooting": "Check server logs for details. The PDF may be corrupted or password-protected."
}
```

**503 Service Unavailable** (GPU overloaded):
```json
{
  "error": "ServiceUnavailable",
  "detail": "GPU resources are currently at capacity",
  "troubleshooting": "Try again in a few minutes, or contact administrator to increase capacity."
}
```

### 6.2 OpenAPI Specification

```yaml
openapi: 3.0.0
info:
  title: PDF2MD Conversion Service
  version: 1.0.0
  description: Convert PDF files to Markdown using GPU acceleration

paths:
  /convert:
    post:
      summary: Convert PDF to Markdown
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file:
                  type: string
                  format: binary
      responses:
        '200':
          description: Successful conversion
          content:
            text/markdown:
              schema:
                type: string
          headers:
            X-Pages-Processed:
              schema:
                type: integer
            X-Conversion-Time:
              schema:
                type: number
        '400':
          description: Invalid request
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '500':
          description: Conversion error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

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
        detail:
          type: string
        troubleshooting:
          type: string
```

---

## 7. Data Models

### 7.1 Configuration Model

```python
from pydantic import BaseModel, Field
from pathlib import Path

class ServerConfig(BaseModel):
    """Server configuration stored in ~/.pdf2md/config.json"""

    server_url: str = Field(
        default="http://localhost:8000",
        description="URL of the PDF2MD server"
    )

    timeout: int = Field(
        default=300,
        ge=1,
        le=3600,
        description="Request timeout in seconds"
    )

    chunk_size: int = Field(
        default=8192,
        ge=1024,
        le=1048576,
        description="Upload/download chunk size in bytes"
    )

    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts for network errors"
    )

    verify_ssl: bool = Field(
        default=True,
        description="Verify SSL certificate for HTTPS"
    )

    output_dir: Path | None = Field(
        default=None,
        description="Default output directory (null = same as PDF)"
    )

    overwrite: bool = Field(
        default=False,
        description="Overwrite existing Markdown files without asking"
    )

    class Config:
        json_encoders = {
            Path: str
        }
```

### 7.2 Request/Response Models

```python
from pydantic import BaseModel

class ConversionRequest(BaseModel):
    """Conversion request metadata (for future async version)"""
    filename: str
    file_size: int
    options: dict = {}

class ConversionResponse(BaseModel):
    """Successful conversion response"""
    output_filename: str
    pages_processed: int
    conversion_time: float
    output_size_bytes: int

class ErrorResponse(BaseModel):
    """Error response"""
    error: str  # Error code
    detail: str  # Human-readable description
    troubleshooting: str = ""  # Actionable hints

    class Config:
        schema_extra = {
            "example": {
                "error": "InvalidRequest",
                "detail": "File size exceeds maximum allowed size",
                "troubleshooting": "Maximum file size is 500MB. Please split your PDF."
            }
        }
```

### 7.3 Internal Models

```python
class ConversionJob:
    """Internal representation of a conversion job"""

    def __init__(
        self,
        job_id: str,
        pdf_path: Path,
        original_filename: str
    ):
        self.job_id = job_id
        self.pdf_path = pdf_path
        self.original_filename = original_filename
        self.md_path = pdf_path.with_suffix(".md")
        self.created_at = datetime.now()
        self.status = "pending"

    def mark_in_progress(self) -> None:
        self.status = "converting"
        self.started_at = datetime.now()

    def mark_completed(self, pages: int) -> None:
        self.status = "completed"
        self.completed_at = datetime.now()
        self.pages_processed = pages
        self.conversion_time = (
            self.completed_at - self.started_at
        ).total_seconds()

    def mark_failed(self, error: str) -> None:
        self.status = "failed"
        self.failed_at = datetime.now()
        self.error = error
```

---

## 8. Error Handling Strategy

### 8.1 Error Classification

**Client Errors (4xx)**:
- `ValidationError`: Invalid file type, size exceeded
- `NotFoundError`: Configuration file not found
- `ConflictError`: Output file already exists

**Network Errors**:
- `ConnectionError`: Server unreachable
- `TimeoutError`: Request timeout
- `HTTPError`: Non-2xx response from server

**Server Errors (5xx)**:
- `ConversionError`: PDF conversion failed
- `ResourceError`: GPU unavailable, disk full
- `InternalError`: Unexpected server error

### 8.2 Retry Strategy

**Retryable Errors**:
- Connection refused
- Request timeout
- Server unavailable (503)

**Retry Logic**:
```python
async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 2.0
) -> Any:
    """Retry with exponential backoff."""
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except (ConnectionError, TimeoutError) as e:
            if attempt == max_retries:
                raise
            delay = base_delay * (2 ** attempt)
            logger.warning(f"Retry {attempt + 1}/{max_retries} after {delay}s")
            await asyncio.sleep(delay)
```

**Non-Retryable Errors**:
- Validation errors (4xx): Won't change on retry
- Conversion errors (500): Likely persistent
- Authentication errors: Won't succeed without credential change

### 8.3 Error Message Design

**Principles**:
1. **Actionable**: Tell user what to do
2. **Specific**: Include relevant details (file name, error code)
3. **Structured**: Separate error, detail, troubleshooting

**Template**:
```
✗ {Error Type}: {Specific Description}

{What went wrong}

Troubleshooting:
- {Actionable hint 1}
- {Actionable hint 2}
- {Actionable hint 3}

Documentation: https://github.com/user/pdf2md-cli#error-codes
```

**Examples**:

**Network Error**:
```
✗ Network Error: Could not connect to server

Failed to connect to http://192.168.1.100:8000 after 3 attempts

Troubleshooting:
- Check server is running: curl http://192.168.1.100:8000/health
- Check network connectivity: ping 192.168.1.100
- Verify server_url in config: pdf2md config show
- Check firewall settings
```

**Conversion Error**:
```
✗ Conversion Error: Failed to process PDF

The PDF could not be converted: Marker processing failed

Details:
- File: document.pdf (15.2 MB)
- Server: http://192.168.1.100:8000
- Error: CUDA out of memory

Troubleshooting:
- The PDF may be too large or have too many images
- Try converting a smaller file first
- Check server logs for details: ssh server 'tail -f /var/log/pdf2md.log'
- Contact administrator if problem persists
```

### 8.4 Cleanup on Error

**Guaranteed Cleanup**:
```python
async def convert_with_cleanup(pdf_path: Path) -> Path:
    """Convert PDF, ensuring cleanup even on error."""
    temp_files = []

    try:
        # Save upload to temp
        temp_pdf = await file_manager.save_upload(pdf_path)
        temp_files.append(temp_pdf)

        # Convert
        temp_md = await converter.convert(temp_pdf)
        temp_files.append(temp_md)

        return temp_md

    except Exception as e:
        # Log error for debugging
        logger.error(f"Conversion failed: {e}", exc_info=True)

        # Raise user-facing error
        raise ConversionError(f"Failed to convert: {e}") from e

    finally:
        # Always cleanup
        await file_manager.cleanup(*temp_files)
```

---

## 9. Security Design

### 9.1 Input Validation

**File Type Validation**:
- Check file extension (`.pdf`)
- Verify magic bytes (`%PDF-`)
- Use `python-magic` library for reliable detection

**File Size Limits**:
- Client: Reject files > 500MB before upload
- Server: Enforce limit during upload
- Stream upload to avoid memory exhaustion

**Filename Sanitization**:
```python
def sanitize_filename(filename: str) -> str:
    """Remove dangerous characters and path traversal."""
    # Remove directory paths
    filename = Path(filename).name

    # Remove dangerous characters
    filename = re.sub(r'[<>:"|?*\\\x00-\x1f]', '_', filename)

    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255 - len(ext)] + ext

    # Prevent hidden files on Unix
    if filename.startswith("."):
        filename = "_" + filename[1:]

    return filename
```

### 9.2 Resource Limits

**DoS Prevention**:
```python
# FastAPI config
app = FastAPI()

# Limit request size
@app.post("/convert")
async def convert_pdf(
    file: UploadFile = File(max_size=500 * 1024 * 1024)  # 500MB
):
    ...
```

**Concurrency Limits**:
```python
from asyncio import Semaphore

# Limit concurrent conversions
conversion_semaphore = Semaphore(10)

@app.post("/convert")
async def convert_pdf(file: UploadFile):
    async with conversion_semaphore:
        # Only 10 conversions at a time
        return await do_conversion(file)
```

**Memory Limits**:
- Stream file uploads (don't load entire file into memory)
- Clean up temp files immediately after conversion
- Monitor memory usage, reject if > 80%

### 9.3 File Security

**Temporary File Isolation**:
- Use dedicated temp directory (`/tmp/pdf2md/`)
- Random UUID filenames prevent guessing
- Set restrictive permissions: `chmod 600`

**Path Traversal Prevention**:
```python
def safe_path_join(base: Path, filename: str) -> Path:
    """Safely join paths, preventing traversal."""
    # Sanitize filename
    safe = sanitize_filename(filename)

    # Join and resolve
    full_path = (base / safe).resolve()

    # Ensure result is under base directory
    if not str(full_path).startswith(str(base.resolve())):
        raise ValueError("Path traversal detected")

    return full_path
```

### 9.4 Logging Security

**Don't Log Sensitive Data**:
- ✅ Log: "Converting file: a1b2c3d4-document.pdf"
- ❌ Log: "Converting file: /home/user/sensitive-doc.pdf"

**Sanitize Error Messages**:
```python
def safe_error_message(error: Exception, file_path: Path) -> str:
    """Generate error message without leaking paths."""
    filename = file_path.name  # Only filename, not full path
    return f"Error processing {filename}: {str(error)}"
```

**Audit Logging**:
```python
logger.info(
    "conversion_requested",
    extra={
        "client_ip": request.client.host,
        "file_size": file_size,
        "filename": sanitized_filename,
        "timestamp": datetime.now().isoformat()
    }
)
```

---

## 10. Technology Stack

### 10.1 Final Technology Choices

**Client**:
- `typer` - Modern CLI framework with type hints
- `httpx` - Async HTTP client (supports both sync/async)
- `pydantic` - Data validation and settings management
- `tqdm` - Progress bars
- `questionary` - Interactive prompts (for config initialization)

**Server**:
- `FastAPI` - Modern async web framework
- `uvicorn[standard]` - ASGI server with websocket support
- `marker` - PDF to Markdown conversion engine
- `python-multipart` - Multipart form data parsing
- `aiofiles` - Async file operations
- `structlog` - Structured logging

**Development**:
- `pyproject.toml` - Modern Python packaging
- `ruff` - Fast linter and formatter
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `mypy` - Optional static type checking

**Justification**:
- ✅ **SOLID**: Each library has single, clear purpose
- ✅ **DRY**: No overlapping functionality (e.g., httpx replaces requests)
- ✅ **YAGNI**: No unnecessary abstractions (e.g., no Celery yet)
- ✅ **Modern**: All libraries actively maintained, Python 3.11+ compatible

### 10.2 Dependency Graph

```
client/
├── typer (CLI framework)
│   └── pydantic (validation)
├── httpx (HTTP client)
│   └── anyio (async backend)
├── tqdm (progress bars)
└── questionary (prompts)

server/
├── FastAPI (web framework)
│   ├── pydantic (validation)
│   ├── starlette (ASGI toolkit)
│   └── anyio (async backend)
├── uvicorn (ASGI server)
│   └── uvloop (event loop, Unix only)
├── marker (PDF conversion)
│   ├── torch (GPU support)
│   └── transformers (OCR models)
├── python-multipart (form parsing)
├── aiofiles (async file I/O)
│   └── aioconsole (async stdio)
└── structlog (logging)
    └── python-json-logger (JSON output)
```

### 10.3 Python Version

**Target**: Python 3.11+
**Reasoning**:
- Modern async/await syntax
- Better type hints (`|` union operator)
- Performance improvements
- `Self` type for cleaner code
- Exception groups (`ExceptionGroup`)

**Minimum**: 3.10 (if needed for compatibility)
**Not Supporting**: < 3.10 (lacks critical features)

---

## 11. Deployment Architecture

### 11.1 Development Environment

**Local Development**:
```bash
# Client (any machine)
$ cd client
$ python -m venv .venv
$ source .venv/bin/activate  # Windows: .venv\Scripts\activate
$ pip install -e .

# Server (GPU machine)
$ cd server
$ python -m venv .venv
$ source .venv/bin/activate
$ pip install -e .
$ uvicorn server.main:app --reload --port 8000
```

**Configuration**:
```bash
# Initialize client config
$ pdf2md config init --server-url http://localhost:8000

# Test connection
$ pdf2md test-connection
✓ Connected to server (version 1.0.0)
```

### 11.2 Production Deployment

**Docker Deployment (Recommended)**:

**Dockerfile** (server):
```dockerfile
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

# Install Python
RUN apt-get update && apt-get install -y python3.11 python3-pip

# Install system dependencies
RUN apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy application
COPY server/ server/

# Create temp directory
RUN mkdir -p /tmp/pdf2md

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run server
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Docker Compose**:
```yaml
version: '3.8'

services:
  pdf2md-server:
    build: .
    container_name: pdf2md-server
    ports:
      - "8000:8000"
    volumes:
      - /tmp/pdf2md:/tmp/pdf2md
    environment:
      - CUDA_VISIBLE_DEVICES=0
      - TMPDIR=/tmp/pdf2md
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

**Deployment Commands**:
```bash
# Build image
$ docker build -t pdf2md-server:1.0 .

# Run container
$ docker-compose up -d

# View logs
$ docker-compose logs -f

# Stop
$ docker-compose down
```

### 11.3 Systemd Service (Alternative)

**Service File**: `/etc/systemd/system/pdf2md.service`
```ini
[Unit]
Description=PDF2MD Conversion Service
After=network.target

[Service]
Type=simple
User=pdf2md
WorkingDirectory=/opt/pdf2md
Environment="PATH=/opt/pdf2md/venv/bin"
ExecStart=/opt/pdf2md/venv/bin/uvicorn server.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Commands**:
```bash
# Enable service
$ sudo systemctl enable pdf2md

# Start service
$ sudo systemctl start pdf2md

# Check status
$ sudo systemctl status pdf2md

# View logs
$ sudo journalctl -u pdf2md -f
```

### 11.4 Monitoring and Logging

**Structured Logging**:
```python
import structlog

logger = structlog.get_logger()

# Log conversion start
logger.info(
    "conversion_started",
    job_id=job_id,
    filename=sanitized_filename,
    file_size=file_size,
    client_ip=request.client.host
)

# Log conversion complete
logger.info(
    "conversion_completed",
    job_id=job_id,
    pages_processed=pages,
    duration_seconds=duration,
    output_size_bytes=output_size
)

# Log errors
logger.error(
    "conversion_failed",
    job_id=job_id,
    error=str(e),
    error_type=type(e).__name__,
    traceback=traceback.format_exc()
)
```

**Health Check Endpoint**:
```python
@app.get("/health")
async def health_check():
    """Health check for load balancers."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "gpu_available": torch.cuda.is_available(),
        "active_conversions": conversion_semaphore._value,
        "uptime_seconds": time.time() - start_time
    }
```

---

## 12. Performance Considerations

### 12.1 Performance Targets

**From Success Criteria**:
- **SC-001**: Convert 10-page PDF in <30 seconds
- **SC-004**: Support 10 concurrent requests
- **FR-012**: Handle files up to 500MB

### 12.2 Bottleneck Analysis

**Expected Timing Breakdown** (10-page PDF):
```
Total: 30 seconds

1. File Upload (5s):
   - Network transfer: 3s
   - Disk write: 2s

2. File Validation (1s):
   - Type check: 0.1s
   - Size check: 0.1s
   - Virus scan (optional): 0.8s

3. PDF Conversion (20s):
   - Load PDF: 1s
   - Extract text: 5s
   - OCR (GPU): 12s
   - Generate MD: 2s

4. File Download (4s):
   - Disk read: 1s
   - Network transfer: 3s
```

### 12.3 Optimization Strategies

**Network Optimization**:
- Use compression (GZip middleware)
- Increase chunk size for large files
- Enable HTTP/2 if supported

**Conversion Optimization**:
- Use batch processing for multi-page PDFs
- Cache frequently used OCR models
- Pre-warm GPU on startup

**Concurrency Optimization**:
- Use asyncio for concurrent I/O
- Semaphore to limit GPU usage
- Queue system for future scaling

**File I/O Optimization**:
- Use async file operations (aiofiles)
- Stream upload/download (don't buffer entire file)
- Use faster storage (SSD vs HDD)

### 12.4 Caching Strategy (Future)

**Not for MVP** (YAGNI), but potential future improvements:
- Cache converted Markdowns (hash-based)
- Pre-load OCR models on startup
- CDN for static assets (if web UI added)

---

## 13. Testing Strategy

### 13.1 Test Pyramid

```
        /\
       /  \
      / E2E \         (10% - Integration tests)
     /--------\
    /  Contract \     (20% - API contract tests)
   /--------------\
  /     Unit Tests  \ (70% - Component tests)
 /--------------------\
```

### 13.2 Unit Tests

**Client Tests** (`tests/unit/test_client/`):
```python
def test_validate_pdf_file_success(tmp_path):
    """Test valid PDF validation."""
    pdf_file = create_test_pdf(tmp_path, "test.pdf")
    validate_pdf_file(pdf_file)  # Should not raise

def test_validate_pdf_file_not_found(tmp_path):
    """Test missing file raises error."""
    with pytest.raises(FileValidationError):
        validate_pdf_file(tmp_path / "missing.pdf")

def test_config_load_default():
    """Test loading default config."""
    config = load_config()
    assert config.server_url == "http://localhost:8000"
    assert config.timeout == 300

def test_config_hierarchy():
    """Test config precedence: CLI > env > file > default."""
    # Test environment variable override
    os.environ["PDF2MD_SERVER_URL"] = "http://example.com"
    config = load_config()
    assert config.server_url == "http://example.com"
```

**Server Tests** (`tests/unit/test_server/`):
```python
def test_file_manager_save_upload(tmp_path):
    """Test saving uploaded file."""
    manager = TempFileManager(tmp_path)

    # Create mock upload
    upload = MockUploadFile("test.pdf", b"%PDF-1.4...")

    # Save upload
    path = asyncio.run(manager.save_upload(upload))

    # Verify file exists
    assert path.exists()
    assert path.name.startswith(upload.filename)

async def test_converter_success(tmp_path):
    """Test successful conversion."""
    converter = MarkerConverter()
    pdf_path = create_test_pdf(tmp_path, "input.pdf")
    md_path = tmp_path / "output.md"

    await converter.convert(pdf_path, md_path)

    assert md_path.exists()
    assert "# Test PDF" in md_path.read_text()
```

### 13.3 Contract Tests

**API Contract Tests** (`tests/contract/`):
```python
def test_convert_endpoint_contract(client):
    """Test /convert endpoint contract."""
    # Create test PDF
    pdf_content = b"%PDF-1.4\ntest content"

    # Send request
    response = client.post(
        "/convert",
        files={"file": ("test.pdf", pdf_content, "application/pdf")}
    )

    # Assert response format
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/markdown"
    assert "content-disposition" in response.headers

def test_convert_invalid_file_type(client):
    """Test 400 error for non-PDF file."""
    response = client.post(
        "/convert",
        files={"file": ("test.txt", b"not a pdf", "text/plain")}
    )

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "detail" in data
```

### 13.4 Integration Tests

**End-to-End Tests** (`tests/integration/`):
```python
@pytest.mark.asyncio
async def test_conversion_flow(server, client, tmp_path):
    """Test complete conversion flow."""
    # Start server
    async with server:
        # Create test PDF
        pdf_path = create_test_pdf(tmp_path, "document.pdf")

        # Convert using client
        result = await client.convert(pdf_path)

        # Verify output
        assert result.exists()
        assert result.suffix == ".md"
        assert "# Test PDF" in result.read_text()

@pytest.mark.asyncio
async def test_network_error_recovery(server, client, tmp_path):
    """Test retry on network error."""
    # Start server after delay
    async with delayed_server(delay=2):
        pdf_path = create_test_pdf(tmp_path, "test.pdf")

        # Should retry and succeed
        result = await client.convert(pdf_path)
        assert result.exists()
```

### 13.5 Performance Tests

**Benchmark Tests** (`tests/performance/`):
```python
def test_conversion_performance_10_pages(benchmark, tmp_path):
    """Benchmark 10-page PDF conversion."""
    pdf_path = create_test_pdf(tmp_path, "10pages.pdf", pages=10)

    result = benchmark.pedantic(
        convert_pdf,
        args=(pdf_path,)
    )

    # Assert < 30 seconds
    assert benchmark.stats.stats.mean < 30

def test_concurrent_requests_10_concurrent(tmp_path):
    """Test 10 concurrent conversions."""
    async def convert_10():
        tasks = [convert_pdf(create_test_pdf(tmp_path, f"{i}.pdf"))
                 for i in range(10)]
        await asyncio.gather(*tasks)

    # Should complete without errors
    asyncio.run(convert_10())
```

### 13.6 Test Coverage Goals

**Minimum Coverage**:
- Critical paths: 90%+
- Average coverage: 80%+
- Overall: 75%+

**Exclude from Coverage**:
- Test files
- Configuration stubs
- `__init__.py`
- Type definitions

---

## Appendix A: Configuration File Example

**`~/.pdf2md/config.json`**:
```json
{
  "server_url": "http://192.168.1.100:8000",
  "timeout": 300,
  "chunk_size": 8192,
  "max_retries": 3,
  "verify_ssl": true,
  "output_dir": null,
  "overwrite": false
}
```

## Appendix B: Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PDF2MD_SERVER_URL` | Server URL | `http://localhost:8000` |
| `PDF2MD_TIMEOUT` | Request timeout (seconds) | `300` |
| `PDF2MD_CONFIG_PATH` | Config file path | `~/.pdf2md/config.json` |
| `PDF2MD_VERBOSE` | Enable verbose logging | `false` |

## Appendix C: Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Generic error |
| 2 | Network error |
| 3 | Validation error |
| 4 | Conversion error |
| 5 | Configuration error |

## Appendix D: Error Codes Reference

| Code | Description | Retryable |
|------|-------------|-----------|
| `ConnectionError` | Cannot connect to server | Yes |
| `TimeoutError` | Request timeout | Yes |
| `ValidationError` | Invalid file input | No |
| `ConversionError` | PDF conversion failed | No |
| `ResourceError` | Server out of memory | Yes (after delay) |
| `ConfigError` | Invalid configuration | No |

---

**Document Version**: 1.0
**Last Updated**: 2026-01-06
**Next Review**: After MVP implementation
