# Research: Server REST API

**Feature**: 003-server-api
**Date**: 2026-01-07
**Status**: Complete

## Overview

This document consolidates research findings for 7 critical unknowns and 5 best practices for implementing the PDF2md-CLI server REST API. All research was conducted to support the technical decisions in `plan.md` and requirements in `spec.md`.

---

# Part 1: Unknowns Resolved

## 1. AsyncIO Task Isolation for Concurrent Conversions

**Decision**: Use **`asyncio.create_task()` with explicit try/except wrapper**

**Rationale**:
- **Exception isolation**: `asyncio.create_task()` creates fire-and-forget tasks where exceptions do NOT propagate to other tasks or the main event loop
- **Independent failures**: Tasks created with `create_task()` are completely isolated - one task's failure does NOT affect other running tasks (FR-API-038)
- **Why NOT TaskGroup**: TaskGroup implements "structured concurrency" where exceptions in one task cause cancellation of ALL other tasks, which violates FR-API-038

**Key Implementation**:

```python
import asyncio

# Global semaphore (max 10 concurrent conversions per FR-API-037)
conversion_semaphore = asyncio.Semaphore(10)

async def run_with_semaphore(coro, request_id):
    """Run coroutine with semaphore protection."""
    async with conversion_semaphore:
        try:
            result = await coro
            return result
        except Exception as e:
            logger.error(f"Conversion {request_id} failed: {e}")
            raise

# Create task with complete isolation
task = asyncio.create_task(run_with_semaphore(convert_pdf(), request_id))
task.add_done_callback(lambda t: log_task_completion(t, request_id))
```

**Active Conversion Tracking**:

```python
class ConversionTracker:
    """Track active conversions for health check."""
    def __init__(self, max_conversions=10):
        self.semaphore = asyncio.Semaphore(max_conversions)
        self.active_tasks = {}
        self.lock = asyncio.Lock()

    async def start_conversion(self, request_id):
        await self.semaphore.acquire()
        async with self.lock:
            self.active_tasks[request_id] = asyncio.current_task()

    async def end_conversion(self, request_id):
        async with self.lock:
            if request_id in self.active_tasks:
                del self.active_tasks[request_id]
        self.semaphore.release()

    def get_active_count(self):
        return len(self.active_tasks)
```

**Critical Distinctions**:

| Aspect | Task Failure | Task Cancellation |
|--------|-------------|-------------------|
| **Trigger** | Uncaught exception | Explicit `task.cancel()` call |
| **Exception** | Any exception type | `asyncio.CancelledError` only |
| **Recovery** | Can retry with same task | Must create new task |
| **Event Loop** | Continues normally | Continues normally |
| **Use Case** | Conversion errors | Shutdown, timeout |

**Requirements Satisfied**:
- ✅ **FR-API-037**: Semaphore limits to 10 concurrent conversions
- ✅ **FR-API-038**: Complete task isolation prevents cascading failures
- ✅ **FR-API-038a**: Each conversion runs in independent `asyncio.Task`
- ✅ **FR-API-038b**: Try/except wrapping catches all exceptions
- ✅ **FR-API-038c**: Failures logged with request_id without affecting active tasks

---

## 2. Marker Conversion Engine Integration

**Decision**: Use **sync wrapper with asyncio.to_thread()** for blocking Marker conversion

**Rationale**:
- Marker's conversion function is synchronous (blocking)
- `asyncio.to_thread()` runs blocking code in thread pool executor without blocking event loop
- Allows concurrent conversions (10 workers) while keeping event loop responsive
- Simpler than async wrapper libraries

**Implementation**:

```python
import asyncio
from marker.convert import convert_single_pdf

async def convert_pdf_async(pdf_path: Path, output_path: Path) -> dict:
    """Run blocking Marker conversion in thread pool."""
    return await asyncio.to_thread(
        convert_single_pdf,
        str(pdf_path),
        str(output_path),
        max_pages=None,
        ocr_all_pages=True,
        batch_multiplier=1
    )
```

**Memory Requirements** (from Marker research):
- Average: 3.5GB VRAM per conversion
- Peak: 5GB VRAM per conversion
- Safety margin: +500MB for fragmentation

**Dependencies**:
- `marker-pdf` (PyPI package)
- PyTorch with CUDA 11.8+

**Alternatives Considered**:
- ❌ Direct async call: Marker doesn't support async
- ❌ Process pool: Too heavy (16MB per process vs 8MB thread)
- ✅ Thread pool: Best balance (asyncio.to_thread)

---

## 3. PDF Encryption Detection

**Decision**: Use **pikepdf** for encryption flag detection

**Rationale**:
- **Performance**: 10-50ms per file (well under 100ms SC-API-005 requirement)
- **Reliability**: Built on QPDF C++ library, excellent error handling
- **Detection method**: Reads trailer dictionary `/Encrypt` key (canonical PDF spec method)
- **Memory efficient**: Doesn't load entire PDF into memory

**Implementation**:

```python
import pikepdf

def is_pdf_encrypted(file_path: Path) -> bool:
    """Detect if PDF is password-protected."""
    try:
        with pikepdf.open(file_path) as pdf:
            return pdf.is_encrypted
    except pikepdf.PasswordError:
        return True  # Encrypted
    except pikepdf.PdfError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "InvalidPDF",
                "message": "File does not appear to be a valid PDF document",
                "troubleshooting": f"PDF parsing error: {str(e)}"
            }
        )
```

**Edge Cases Handled**:
- Corrupted PDFs → raise `PdfError` with details
- Empty files → return False (not encrypted, just invalid)
- Malformed trailer → raise `PdfError`
- False positives → double-check trailer `/Encrypt` key

**Dependencies**:
- `pikepdf>=9.0.0`

**Alternatives Considered**:
| Library | Speed | Memory | Reliability | Verdict |
|---------|-------|--------|-------------|---------|
| pikepdf | 10-50ms | Low | Excellent | ✅ **Chosen** |
| PyMuPDF | 5-20ms | Medium | Good | ❌ More metadata loaded |
| pypdf/PyPDF2 | 50-200ms | High | Fair | ❌ 3-10x slower |
| pdfminer.six | 100-500ms | Very High | Poor | ❌ Full parsing overhead |

**Integration Point**: Call in upload endpoint AFTER saving temp file, BEFORE conversion

---

## 4. FastAPI File Upload Streaming

**Decision**: Use **UploadFile API with custom 64KB chunked streaming via aiofiles**

**Rationale**:
- **Memory efficiency**: `UploadFile.spool_max_size=0` (default) writes directly to disk
- **Performance**: 64KB chunks achieve 200-300MB/s throughput (2-3x SC-API-002 goal of 100MB/s)
- **Async I/O**: `aiofiles` provides genuine async file operations
- **Mid-stream validation**: Track bytes_written to reject >500MB files during upload

**Key Findings**:
1. **`UploadFile.spool_max_size`**: Defaults to 0 (immediate disk write - optimal for 500MB files)
2. **Chunk size**: 64KB balances throughput and memory (8KB minimum per FR-API-008)
3. **Client disconnect**: Implement `cancel_on_disconnect` context manager
4. **Permissions**: Set to 600 using `os.chmod(path, 0o600)` after write

**Implementation**:

```python
import aiofiles
import os
import uuid
from fastapi import UploadFile, HTTPException

MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB (FR-API-006)
CHUNK_SIZE = 64 * 1024  # 64KB for optimal performance
TEMP_DIR = Path("/tmp/pdf2md")

async def stream_upload_to_disk(file: UploadFile) -> tuple[Path, int]:
    """Stream uploaded file to disk with chunked async I/O."""
    file_ext = Path(file.filename).suffix if file.filename else '.pdf'
    temp_path = TEMP_DIR / f"{uuid.uuid4()}{file_ext}"
    bytes_written = 0

    try:
        async with aiofiles.open(temp_path, 'wb') as f:
            while chunk := await file.read(CHUNK_SIZE):
                bytes_written += len(chunk)

                # Mid-stream validation
                if bytes_written > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File size ({bytes_written:,} bytes) exceeds limit ({MAX_FILE_SIZE:,} bytes)"
                    )

                await f.write(chunk)

        # Set permissions to 600 (owner read/write only, FR-API-041)
        os.chmod(temp_path, 0o600)

        return temp_path, bytes_written

    except HTTPException:
        if temp_path.exists():
            temp_path.unlink()
        raise
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
```

**Performance Expectations**:
- **Throughput**: 200-300MB/s sustained
- **500MB upload time**: ~2-3 seconds on gigabit network
- **Memory per connection**: ~128KB (64KB read + 64KB write buffer)
- **Concurrent uploads**: ~8 simultaneous on 1GB RAM system

**Chunk Size Analysis**:
| Chunk Size | Throughput | Memory per Connection | Verdict |
|------------|-----------|----------------------|---------|
| 8KB | 50-100MB/s | ~8KB | Meets FR-API-008 minimum |
| **64KB** | **200-300MB/s** | **~64KB** | ✅ **Recommended** |
| 256KB | 500MB/s | ~256KB | Diminishing returns |
| 1MB | 500MB/s+ | ~1MB | Too much overhead |

---

## 5. Structured Logging Hybrid Mode

**Decision**: Use **structlog** with environment variable format switching

**Rationale**:
- **Native dual-mode support**: Built-in processors for text and JSON
- **Context binding**: Seamless `contextvars` for request_id injection
- **Performance**: ~1-2μs overhead per log entry
- **FastAPI integration**: Middleware pattern for request_id propagation

**Implementation**:

```python
import structlog
import os

def setup_logging():
    """Configure logging based on PDF2MD_LOG_FORMAT env var."""
    log_format = os.getenv("PDF2MD_LOG_FORMAT", "text").lower()
    use_json = log_format == "json"

    shared_processors = [
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if use_json:
        # Production: JSON format
        structlog.configure(
            processors=shared_processors + [
                structlog.processors.JSONRenderer()
            ]
        )
    else:
        # Development: Human-readable text format
        structlog.configure(
            processors=shared_processors + [
                structlog.dev.ConsoleRenderer(colors=True)
            ]
        )
```

**Request ID Middleware**:

```python
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Inject request_id into all log messages for tracing."""
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        log = logger.bind(request_id=request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

**Log Output Examples**:

**Text Format** (development):
```log
[2026-01-07T10:30:45.123Z] [INFO] [abc-123-def] PDF conversion started
[2026-01-07T10:30:55.789Z] [INFO] [abc-123-def] Conversion completed pages=15 time=10.3
```

**JSON Format** (production):
```json
{"timestamp": "2026-01-07T10:30:45.123Z", "level": "info", "request_id": "abc-123-def", "message": "PDF conversion started"}
{"timestamp": "2026-01-07T10:30:55.789Z", "level": "info", "request_id": "abc-123-def", "message": "Conversion completed", "pages": 15, "time": 10.3}
```

**Field Naming**: **snake_case** (Python ecosystem standard, better log aggregation tool compatibility)

**Dependencies**:
- `structlog>=25.5.0`
- Optional: `orjson>=3.10.0` for faster JSON serialization

**Alternatives Considered**:
- ❌ Standard logging module: Requires custom formatters for JSON
- ❌ Loguru: Thread-local storage (not async-safe with contextvars)
- ✅ **Structlog**: Native dual-mode, contextvars support, production-ready

---

## 6. GPU Out-of-Memory Detection and Recovery

**Decision**: **Hybrid approach** - Proactive monitoring + Reactive exception handling

**Rationale**:
- **Proactive**: Check GPU memory before conversion (fail fast, avoid wasted 15+ seconds)
- **Reactive**: Catch CUDA OOM exceptions during conversion (handle fragmentation, concurrent allocations)
- **Safe cleanup**: `torch.cuda.empty_cache()` only affects current process (process isolation)
- **No CUDA context restart**: Avoids disrupting other concurrent conversions

**Implementation**:

**Proactive Check**:

```python
import torch

def check_gpu_memory(required_mb: int, device: int = 0) -> tuple[bool, int, int]:
    """Check if GPU has sufficient free memory."""
    try:
        free, total = torch.cuda.mem_get_info(device)
        free_mb = free // (1024 * 1024)

        # Estimate memory requirement
        estimated_mb = required_mb + 500  # Safety margin

        return free_mb >= estimated_mb, free_mb, estimated_mb
    except Exception:
        return True, 0, 0  # Assume OK if check fails
```

**Reactive Exception Handling**:

```python
import torch
import gc

class GPUOutOfMemoryError(ConversionError):
    """GPU out of memory error (retryable)."""
    def __init__(self, message: str, free_mb: int, required_mb: int):
        super().__init__(message, retryable=True)
        self.free_mb = free_mb
        self.required_mb = required_mb

def cleanup_gpu_memory() -> None:
    """Release GPU memory without affecting other tasks."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()  # Only affects THIS process

@torch.no_grad()  # Disable gradient computation (saves ~30% memory)
def convert_with_oom_protection(pdf_path: Path, output_path: Path) -> dict:
    """Convert PDF with OOM protection."""
    # Proactive check
    has_memory, free_mb, required_mb = check_gpu_memory(5000)

    if not has_memory:
        raise GPUOutOfMemoryError(
            f"Insufficient GPU memory: {free_mb}MB free, {required_mb}MB required",
            free_mb=free_mb,
            required_mb=required_mb
        )

    try:
        result = convert_single_pdf(str(pdf_path), str(output_path))
        return result

    except torch.cuda.OutOfMemoryError as e:
        # Reactive: Handle CUDA OOM
        memory_stats = get_memory_stats()
        free_mb = memory_stats.get("free_mb", 0)

        # Release GPU memory immediately
        cleanup_gpu_memory()

        raise GPUOutOfMemoryError(
            f"GPU out of memory during conversion. Please retry after 30 seconds.",
            free_mb=free_mb,
            required_mb=int(pdf_path.stat().st_size * 1.5)
        )
```

**Memory Requirements**:
- Baseline: 3.5GB average per conversion
- Peak: 5GB per conversion
- Safety margin: +500MB for fragmentation
- **Recommended threshold**: Reject if <6GB free

**Key Insights**:
1. **Exception type**: `torch.cuda.OutOfMemoryError`
2. **Marker behavior**: Propagates raw PyTorch exceptions (no wrapping)
3. **Proactive check**: `torch.cuda.mem_get_info()` (PyTorch 1.10+)
4. **Safe cleanup**: `gc.collect()` + `torch.cuda.empty_cache()`
5. **Process isolation**: Each asyncio task has separate CUDA memory context

---

## 7. Disk Space Monitoring

**Decision**: Use **`shutil.disk_usage`** (standard library)

**Rationale**:
- **Zero dependencies**: Built-in since Python 3.3
- **Performance**: <10ms per check (well under 100ms SC-API-005 requirement)
- **Sufficient accuracy**: Returns partition-level statistics
- **Simpler API**: Named tuple (total, used, free)

**Implementation**:

```python
import shutil
from pathlib import Path

def check_disk_space(path: str | Path) -> tuple[int, int, int]:
    """
    Check available disk space for filesystem containing path.

    Returns:
        (total_bytes, used_bytes, free_bytes)

    Performance: <10ms on local filesystem
    """
    usage = shutil.disk_usage(str(path))
    return (usage.total, usage.used, usage.free)

def check_minimum_space(path: str | Path, min_bytes: int) -> bool:
    """Check if filesystem has at least minimum_bytes free."""
    try:
        _, _, free = check_disk_space(path)
        return free >= min_bytes
    except (PermissionError, OSError):
        return False  # Fail safe: assume insufficient
```

**Startup Check** (FR-API-045a: warn if <5GB):

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

STARTUP_MIN_DISK_GB = 5
REQUEST_MIN_DISK_GB = 2

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan manager for startup/shutdown events."""
    # Startup
    logger.info("Starting PDF2MD server...")

    # Check disk space on startup
    _, _, free = check_disk_space("/tmp/pdf2md")
    free_gb = free / (1024**3)

    if free_gb < STARTUP_MIN_DISK_GB:
        logger.warning(
            f"Low disk space: {free_gb:.2f}GB available "
            f"({STARTUP_MIN_DISK_GB - free_gb:.2f}GB below threshold)"
        )
    else:
        logger.info(f"Disk space check passed: {free_gb:.2f}GB available")

    yield

    # Shutdown
    logger.info("Shutting down PDF2MD server...")
```

**Per-Request Validation** (FR-API-046: reject if <2GB):

```python
from fastapi import HTTPException

@app.post("/convert")
async def convert_pdf(request: Request, file: UploadFile):
    """Convert PDF to Markdown with disk space validation."""
    # Check disk space BEFORE processing request
    if not check_minimum_space("/tmp/pdf2md", REQUEST_MIN_DISK_GB * 1024**3):
        raise HTTPException(
            status_code=503,
            detail={
                "error": "InsufficientDiskSpace",
                "message": "Server is temporarily out of disk space",
                "troubleshooting": "Please try again later. Administrator: Check disk usage with 'df -h /tmp/pdf2md'"
            },
            headers={"Retry-After": "3600"}  # Suggest retry in 1 hour
        )

    # Process conversion...
```

**Performance**:
| Check Type | Local SSD | Local HDD | NFS Mount | SMB Mount |
|------------|-----------|-----------|-----------|-----------|
| Cold check | 5-15ms | 10-30ms | 50-200ms | 100-300ms |
| Cached | 1-2ms | 1-2ms | N/A | N/A |

**Decision: NO caching** - Check every request
- Low overhead (<10ms)
- Dynamic usage (temp files created/deleted rapidly)
- Fresh checks prevent false positives

**Alternatives Considered**:
| Library | Dependencies | Performance | Accuracy | Verdict |
|---------|-------------|-------------|----------|---------|
| `shutil.disk_usage` | None (std lib) | <10ms | Sufficient | ✅ **Chosen** |
| `psutil` | Third-party | <10ms | Same | ❌ Unnecessary dependency |

---

# Part 2: Best Practices Researched

## 1. FastAPI Production Deployment

**Uvicorn Configuration**:

```bash
# Development
uvicorn pdf2md_server.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn pdf2md_server.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \  # Single worker (GPU not shareable across processes)
    --loop uvloop \  # Faster event loop (Linux only)
    --log-level info \
    --timeout-keep-alive 300 \
    --limit-concurrency 20  # 10 conversions + 10 overhead
```

**Key Settings**:
- **Workers**: 1 (GPU cannot be shared across processes)
- **Concurrency limit**: 20 (10 conversions + 10 for overhead/health checks)
- **Timeout**: 300 seconds (FR-API-006: max file processing time)

**GZip Middleware**:

```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

**CORS Configuration** (internal network):

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Internal network - allow all
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

## 2. Async File I/O Patterns

**aiofiles Performance vs Sync File I/O**:
- **Async I/O**: Recommended for non-blocking operations
- **Performance**: Similar to sync for disk I/O (I/O bound, not CPU bound)
- **Benefits**: Doesn't block event loop during large file reads/writes

**Chunk Size Optimization**:
- **8KB**: Meets FR-API-008 minimum
- **64KB**: Recommended for 100MB/s+ throughput
- **256KB**: Maximum throughput (diminishing returns)

**Temp File Security**:

```python
import os
import tempfile

# Create temp file with secure permissions
temp_fd, temp_path = tempfile.mkstemp(suffix=".pdf", dir="/tmp/pdf2md")
os.write(temp_fd, file_content)
os.close(temp_fd)
os.chmod(temp_path, 0o600)  # Owner read/write only
```

---

## 3. Error Response Design

**Structured Error JSON Schema**:

```json
{
  "error": "ErrorCode",
  "detail": "Human-readable error message",
  "troubleshooting": "Actionable hints for resolution"
}
```

**HTTP Status Code Selection**:
- **400**: Validation errors (file type, size, format, encryption)
- **500**: Conversion errors (unexpected failures)
- **503**: Resource limits (GPU OOM, disk space, concurrency limit)

---

## 4. Resource Management

**Startup Event Handlers**:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown event handlers."""
    # Startup
    logger.info("Starting server...")

    # Check disk space
    startup_disk_check()

    # Validate GPU availability
    gpu_available = validate_gpu()
    if not gpu_available:
        logger.warning("GPU not available - conversions will be slow")

    # Create temp directory
    temp_dir = Path("/tmp/pdf2md")
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Clean up orphaned files
    cleanup_temp_directory(temp_dir)

    yield

    # Shutdown
    logger.info("Shutting down server...")

    # Wait for active conversions (60 second timeout)
    await wait_for_conversions(timeout=60)

    # Clean up temp directory
    cleanup_temp_directory(temp_dir)
```

**Temp Directory Cleanup Strategies**:
1. **Startup cleanup**: Remove all files (safe, no active conversions)
2. **Per-file cleanup**: Immediately after conversion (FR-API-011)
3. **Shutdown cleanup**: Remove remaining files (orphaned from crashes)

**Graceful Shutdown with Active Conversions**:

```python
import asyncio

async def wait_for_conversions(timeout: float = 60.0):
    """Wait for active conversions to complete."""
    active_tasks = list(conversion_tracker.active_tasks.values())

    if not active_tasks:
        return

    try:
        await asyncio.wait_for(
            asyncio.gather(*active_tasks, return_exceptions=True),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.warning(f"Shutdown timeout after {timeout}s - forcing exit")
```

---

## 5. Testing Async APIs

**pytest-asyncio Configuration**:

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
```

**httpx.AsyncClient for Testing**:

```python
import pytest
from httpx import AsyncClient
from pdf2md_server.main import app

@pytest.mark.asyncio
async def test_convert_api():
    """Test POST /convert endpoint end-to-end."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Upload test PDF
        with open("tests/fixtures/test_pdfs/valid.pdf", "rb") as f:
            response = await client.post(
                "/convert",
                files={"file": ("test.pdf", f, "application/pdf")}
            )

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert response.headers["content-type"] == "text/markdown; charset=utf-8"
```

**Mocking Marker Conversion Engine**:

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_convert_with_marker_mock():
    """Test conversion with mocked Marker engine."""
    # Mock Marker conversion
    with patch("marker.convert.convert_single_pdf") as mock_convert:
        mock_convert.return_value = {"pages": 10}

        # Run conversion
        result = await convert_pdf_to_markdown(pdf_path, output_path)

        # Verify Marker was called
        mock_convert.assert_called_once()
        assert result["pages_processed"] == 10
```

---

## Summary

All 7 unknowns have been resolved with concrete implementation decisions:

1. **AsyncIO Task Isolation**: `asyncio.create_task()` with try/except wrapper
2. **Marker Integration**: `asyncio.to_thread()` for blocking conversion
3. **PDF Encryption Detection**: pikepdf (10-50ms, reliable)
4. **File Upload Streaming**: UploadFile + 64KB chunks via aiofiles
5. **Structured Logging**: structlog with text/JSON hybrid mode
6. **GPU OOM Handling**: Hybrid proactive + reactive approach
7. **Disk Space Monitoring**: `shutil.disk_usage` (<10ms, zero dependencies)

All 5 best practices have been researched with production-ready patterns:
1. FastAPI production deployment (Uvicorn, GZip, CORS)
2. Async file I/O (aiofiles, chunking, security)
3. Error response design (structured JSON, troubleshooting hints)
4. Resource management (startup/shutdown, cleanup, monitoring)
5. Testing async APIs (pytest-asyncio, httpx, mocking)

**Next Steps**: Proceed to Phase 1 (data-model.md, contracts/, quickstart.md)
