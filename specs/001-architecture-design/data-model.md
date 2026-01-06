# Data Models

**Feature**: PDF2md-CLI
**Version**: 1.0.0
**Date**: 2026-01-06

## Overview

This document defines all data structures used in the PDF2md-CLI system, including configuration models, API request/response models, and internal data structures.

## Architecture Principles

All data models follow these principles:

1. **SOLID Compliance**:
   - Single Responsibility: Each model has one purpose
   - Open/Closed: Extensible via inheritance
   - Liskov Substitution: Substitutable model implementations

2. **DRY Compliance**:
   - Shared base models for common fields
   - Reusable validation logic
   - Single source of truth for each entity

3. **Robustness**:
   - Pydantic validation on all inputs
   - Type hints for all fields
   - Clear error messages

4. **Simplicity**:
   - Flat structures (no deep nesting)
   - No unnecessary abstractions
   - Self-documenting field names

## Core Models

### 1. Configuration Model

**File**: `client/config.py`

```python
from pydantic import BaseModel, Field, field_validator
from pathlib import Path
from typing import Optional
import json

class ServerConfig(BaseModel):
    """
    Server configuration stored in ~/.pdf2md/config.json

    Configuration Hierarchy (priority order):
    1. Command-line flags (highest)
    2. Environment variables
    3. Config file
    4. Hardcoded defaults (lowest)
    """

    # Connection Settings
    server_url: str = Field(
        default="http://localhost:8000",
        description="URL of the PDF2MD server",
        min_length=1,
        max_length=2048
    )

    timeout: int = Field(
        default=300,
        description="Request timeout in seconds",
        ge=1,
        le=3600
    )

    # Transfer Settings
    chunk_size: int = Field(
        default=8192,
        description="Upload/download chunk size in bytes",
        ge=1024,
        le=1048576
    )

    # Retry Settings
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts for network errors",
        ge=0,
        le=10
    )

    retry_delay: float = Field(
        default=2.0,
        description="Base retry delay in seconds (exponential backoff)",
        ge=0.1,
        le=60.0
    )

    # Security Settings
    verify_ssl: bool = Field(
        default=True,
        description="Verify SSL certificate for HTTPS"
    )

    # Output Settings
    output_dir: Optional[Path] = Field(
        default=None,
        description="Default output directory (null = same as PDF)"
    )

    overwrite: bool = Field(
        default=False,
        description="Overwrite existing Markdown files without asking"
    )

    # Progress Settings
    show_progress: bool = Field(
        default=True,
        description="Show progress bars during upload/download"
    )

    verbose: bool = Field(
        default=False,
        description="Enable verbose logging"
    )

    @field_validator("server_url")
    @classmethod
    def validate_server_url(cls, v: str) -> str:
        """Validate server URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("server_url must start with http:// or https://")
        return v

    @field_validator("output_dir")
    @classmethod
    def validate_output_dir(cls, v: Optional[Path]) -> Optional[Path]:
        """Validate output directory if specified."""
        if v is not None:
            if v.exists() and not v.is_dir():
                raise ValueError("output_dir must be a directory")
        return v

    class Config:
        json_encoders = {
            Path: str
        }
        extra = "forbid"  # Prevent unknown fields

    @classmethod
    def from_file(cls, path: Path) -> "ServerConfig":
        """Load configuration from JSON file."""
        if not path.exists():
            return cls()  # Return defaults

        with open(path, "r") as f:
            data = json.load(f)

        return cls(**data)

    def to_file(self, path: Path) -> None:
        """Save configuration to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(
                self.model_dump(mode="json"),
                f,
                indent=2
            )

    def merge_with_env(self) -> "ServerConfig":
        """Merge configuration with environment variables."""
        import os

        env_mapping = {
            "PDF2MD_SERVER_URL": ("server_url", str),
            "PDF2MD_TIMEOUT": ("timeout", int),
            "PDF2MD_CHUNK_SIZE": ("chunk_size", int),
            "PDF2MD_MAX_RETRIES": ("max_retries", int),
            "PDF2MD_VERIFY_SSL": ("verify_ssl", lambda x: x.lower() == "true"),
            "PDF2MD_VERBOSE": ("verbose", lambda x: x.lower() == "true"),
        }

        data = self.model_dump()

        for env_var, (field, parser) in env_mapping.items():
            value = os.environ.get(env_var)
            if value:
                data[field] = parser(value)

        return ServerConfig(**data)
```

**Usage Example**:

```python
# Load config (with fallback to defaults)
config_path = Path.home() / ".pdf2md" / "config.json"
config = ServerConfig.from_file(config_path)

# Merge with environment variables
config = config.merge_with_env()

# Use config
print(f"Connecting to: {config.server_url}")
print(f"Timeout: {config.timeout}s")

# Save config
config.to_file(config_path)
```

### 2. API Request/Response Models

**File**: `server/models/requests.py`

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ============================================================================
# Request Models
# ============================================================================

class ConversionRequest(BaseModel):
    """
    Conversion request metadata.

    For future async version with job queue.
    Not used in synchronous MVP.
    """

    filename: str = Field(
        ...,
        description="Original PDF filename",
        min_length=1,
        max_length=255
    )

    file_size: int = Field(
        ...,
        description="File size in bytes",
        ge=1,
        le=500 * 1024 * 1024
    )

    options: dict = Field(
        default_factory=dict,
        description="Conversion options (reserved for future use)"
    )

# ============================================================================
# Response Models
# ============================================================================

class ConversionResponse(BaseModel):
    """Successful conversion response metadata."""

    output_filename: str = Field(
        ...,
        description="Generated Markdown filename"
    )

    pages_processed: int = Field(
        ...,
        description="Number of pages converted",
        ge=0
    )

    conversion_time: float = Field(
        ...,
        description="Conversion time in seconds",
        ge=0.0
    )

    output_size_bytes: int = Field(
        ...,
        description="Output file size in bytes",
        ge=0
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp of conversion"
    )

# ============================================================================
# Error Models
# ============================================================================

class ErrorResponse(BaseModel):
    """
    Standard error response for all API errors.

    All errors return JSON with this structure.
    """

    error: str = Field(
        ...,
        description="Error code (e.g., 'InvalidRequest', 'ConversionError')",
        min_length=1,
        max_length=100
    )

    detail: str = Field(
        ...,
        description="Human-readable error description",
        min_length=1,
        max_length=1000
    )

    troubleshooting: str = Field(
        default="",
        description="Actionable troubleshooting hints",
        max_length=2000
    )

    request_id: Optional[str] = Field(
        default=None,
        description="Unique request identifier (UUID)"
    )

    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Error timestamp"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "error": "InvalidRequest",
                    "detail": "File type not supported: .txt. Expected: .pdf",
                    "troubleshooting": "Ensure the file is a PDF document with .pdf extension."
                },
                {
                    "error": "ConversionError",
                    "detail": "Failed to convert PDF: CUDA out of memory",
                    "troubleshooting": "The PDF may be too large. Try a smaller file or contact administrator."
                }
            ]
        }

# ============================================================================
# Health Check Models
# ============================================================================

class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(
        ...,
        description="Health status: 'healthy' or 'unhealthy'",
        pattern="^(healthy|unhealthy)$"
    )

    version: str = Field(
        ...,
        description="Server version",
        min_length=1
    )

    gpu_available: bool = Field(
        ...,
        description="Whether GPU is accessible"
    )

    active_conversions: int = Field(
        ...,
        description="Currently processing conversions",
        ge=0
    )

    max_conversions: int = Field(
        ...,
        description="Maximum concurrent conversions",
        ge=1
    )

    uptime_seconds: float = Field(
        ...,
        description="Server uptime in seconds",
        ge=0.0
    )

    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Response timestamp"
    )
```

### 3. Internal Models

**File**: `server/models/internal.py`

```python
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Optional
from datetime import datetime
from enum import Enum
import uuid

class ConversionStatus(str, Enum):
    """Conversion job status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class ConversionJob(BaseModel):
    """
    Internal representation of a conversion job.

    Tracks the lifecycle of a PDF to Markdown conversion.
    Used for logging and monitoring.
    """

    # Identification
    job_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique job identifier"
    )

    # File Information
    pdf_path: Path = Field(
        ...,
        description="Path to input PDF file"
    )

    original_filename: str = Field(
        ...,
        description="Original PDF filename"
    )

    output_path: Path = Field(
        ...,
        description="Path to output Markdown file"
    )

    file_size_bytes: int = Field(
        ...,
        description="Input file size in bytes",
        ge=0
    )

    # Client Information
    client_ip: Optional[str] = Field(
        default=None,
        description="Client IP address"
    )

    user_agent: Optional[str] = Field(
        default=None,
        description="Client user agent"
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Job creation timestamp"
    )

    started_at: Optional[datetime] = Field(
        default=None,
        description="Conversion start timestamp"
    )

    completed_at: Optional[datetime] = Field(
        default=None,
        description="Conversion completion timestamp"
    )

    # Status
    status: ConversionStatus = Field(
        default=ConversionStatus.PENDING,
        description="Current job status"
    )

    # Results (only if completed)
    pages_processed: Optional[int] = Field(
        default=None,
        description="Number of pages processed",
        ge=0
    )

    conversion_time_seconds: Optional[float] = Field(
        default=None,
        description="Conversion duration in seconds",
        ge=0.0
    )

    output_size_bytes: Optional[int] = Field(
        default=None,
        description="Output file size in bytes",
        ge=0
    )

    # Error Information (only if failed)
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if conversion failed"
    )

    error_type: Optional[str] = Field(
        default=None,
        description="Error type if conversion failed"
    )

    # Methods
    def mark_in_progress(self) -> None:
        """Mark job as in progress."""
        self.status = ConversionStatus.IN_PROGRESS
        self.started_at = datetime.now()

    def mark_completed(
        self,
        pages: int,
        duration: float,
        output_size: int
    ) -> None:
        """Mark job as completed."""
        self.status = ConversionStatus.COMPLETED
        self.completed_at = datetime.now()
        self.pages_processed = pages
        self.conversion_time_seconds = duration
        self.output_size_bytes = output_size

    def mark_failed(self, error: Exception) -> None:
        """Mark job as failed."""
        self.status = ConversionStatus.FAILED
        self.completed_at = datetime.now()
        self.error_message = str(error)
        self.error_type = type(error).__name__

    @property
    def duration_seconds(self) -> Optional[float]:
        """Get total duration from creation to completion."""
        if self.completed_at and self.created_at:
            return (self.completed_at - self.created_at).total_seconds()
        return None

    @property
    def is_finished(self) -> bool:
        """Check if job is finished (completed or failed)."""
        return self.status in (
            ConversionStatus.COMPLETED,
            ConversionStatus.FAILED
        )

    class Config:
        use_enum_values = True

# ============================================================================
# File Metadata
# ============================================================================

class FileMetadata(BaseModel):
    """
    Metadata about uploaded or downloaded files.

    Used for logging and debugging.
    """

    filename: str = Field(
        ...,
        description="Original filename"
    )

    sanitized_filename: str = Field(
        ...,
        description="Sanitized filename (safe for filesystem)"
    )

    size_bytes: int = Field(
        ...,
        description="File size in bytes",
        ge=0
    )

    content_type: str = Field(
        ...,
        description="MIME content type"
    )

    magic_bytes: Optional[str] = Field(
        default=None,
        description="File magic bytes (first 4 bytes)"
    )

    is_valid_pdf: bool = Field(
        ...,
        description="Whether file is a valid PDF"
    )

    validation_errors: list[str] = Field(
        default_factory=list,
        description="List of validation errors (if any)"
    )

    @classmethod
    def from_upload(
        cls,
        filename: str,
        size: int,
        content: bytes
    ) -> "FileMetadata":
        """Create metadata from uploaded file."""
        # Sanitize filename
        sanitized = sanitize_filename(filename)

        # Detect magic bytes
        magic_bytes = content[:4].hex() if len(content) >= 4 else None

        # Validate PDF
        is_valid = validate_pdf_magic_bytes(content)

        validation_errors = []
        if not is_valid:
            validation_errors.append("Invalid PDF magic bytes")

        return cls(
            filename=filename,
            sanitized_filename=sanitized,
            size_bytes=size,
            content_type="application/pdf",
            magic_bytes=magic_bytes,
            is_valid_pdf=is_valid,
            validation_errors=validation_errors
        )

# ============================================================================
# Server Statistics
# ============================================================================

class ServerStats(BaseModel):
    """Server statistics for monitoring."""

    total_conversions: int = Field(
        default=0,
        description="Total conversions processed",
        ge=0
    )

    successful_conversions: int = Field(
        default=0,
        description="Successful conversions",
        ge=0
    )

    failed_conversions: int = Field(
        default=0,
        description="Failed conversions",
        ge=0
    )

    total_pages_processed: int = Field(
        default=0,
        description="Total pages processed",
        ge=0
    )

    total_data_processed_bytes: int = Field(
        default=0,
        description="Total data processed in bytes",
        ge=0
    )

    average_conversion_time: float = Field(
        default=0.0,
        description="Average conversion time in seconds",
        ge=0.0
    )

    last_conversion_time: Optional[datetime] = Field(
        default=None,
        description="Timestamp of last conversion"
    )

    @property
    def success_rate(self) -> float:
        """Calculate success rate (0.0 to 1.0)."""
        if self.total_conversions == 0:
            return 0.0
        return self.successful_conversions / self.total_conversions

    def record_conversion(self, job: ConversionJob) -> None:
        """Record a conversion in statistics."""
        self.total_conversions += 1
        self.total_pages_processed += job.pages_processed or 0
        self.total_data_processed_bytes += job.file_size_bytes

        if job.status == ConversionStatus.COMPLETED:
            self.successful_conversions += 1
            if job.conversion_time_seconds:
                # Update average
                total_time = (
                    self.average_conversion_time *
                    (self.successful_conversions - 1)
                )
                total_time += job.conversion_time_seconds
                self.average_conversion_time = (
                    total_time / self.successful_conversions
                )
        else:
            self.failed_conversions += 1

        self.last_conversion_time = datetime.now()
```

### 4. Client Models

**File**: `client/models.py`

```python
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Optional
from datetime import datetime

class ConversionResult(BaseModel):
    """Result of a client-side conversion request."""

    # Input
    input_path: Path = Field(
        ...,
        description="Path to input PDF file"
    )

    # Output
    output_path: Path = Field(
        ...,
        description="Path to output Markdown file"
    )

    # Timing
    upload_time_seconds: float = Field(
        ...,
        description="Upload duration in seconds",
        ge=0.0
    )

    conversion_time_seconds: float = Field(
        ...,
        description="Server conversion time in seconds",
        ge=0.0
    )

    download_time_seconds: float = Field(
        ...,
        description="Download duration in seconds",
        ge=0.0
    )

    total_time_seconds: float = Field(
        ...,
        description="Total duration in seconds",
        ge=0.0
    )

    # Metadata
    pages_processed: int = Field(
        ...,
        description="Number of pages converted",
        ge=0
    )

    output_size_bytes: int = Field(
        ...,
        description="Output file size in bytes",
        ge=0
    )

    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Conversion timestamp"
    )

    @property
    def upload_speed_mbps(self) -> float:
        """Calculate upload speed in Mbps."""
        input_size = self.input_path.stat().st_size
        if self.upload_time_seconds > 0:
            return (input_size * 8) / (1_000_000 * self.upload_time_seconds)
        return 0.0

    @property
    def download_speed_mbps(self) -> float:
        """Calculate download speed in Mbps."""
        if self.download_time_seconds > 0:
            return (self.output_size_bytes * 8) / (1_000_000 * self.download_time_seconds)
        return 0.0

class ProgressUpdate(BaseModel):
    """Progress update for file transfer."""

    operation: str = Field(
        ...,
        description="Operation: 'upload' or 'download'"
    )

    bytes_transferred: int = Field(
        ...,
        description="Bytes transferred so far",
        ge=0
    )

    total_bytes: int = Field(
        ...,
        description="Total bytes to transfer",
        ge=1
    )

    percentage: float = Field(
        ...,
        description="Percentage complete (0.0 to 100.0)",
        ge=0.0,
        le=100.0
    )

    speed_mbps: float = Field(
        ...,
        description="Current speed in Mbps",
        ge=0.0
    )

    eta_seconds: Optional[float] = Field(
        default=None,
        description="Estimated time remaining in seconds",
        ge=0.0
    )

    @property
    def is_complete(self) -> bool:
        """Check if transfer is complete."""
        return self.bytes_transferred >= self.total_bytes
```

## Data Validation

### Validation Functions

**File**: `shared/validation.py`

```python
from pathlib import Path
import re

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe filesystem usage.

    Removes:
    - Path traversal attempts (../, ..\\)
    - Dangerous characters (< > : " | ? * \\)
    - Control characters (0x00-0x1f)

    Limits:
    - Maximum length to 255 characters
    - Prevents hidden files on Unix (.)

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for filesystem
    """
    # Remove directory paths
    filename = Path(filename).name

    # Remove dangerous characters
    filename = re.sub(r'[<>:"|?*\\\x00-\x1f]', '_', filename)

    # Limit length
    if len(filename) > 255:
        name, ext = Path(filename).stem, Path(filename).suffix
        max_name_len = 255 - len(ext)
        filename = name[:max_name_len] + ext

    # Prevent hidden files on Unix
    if filename.startswith("."):
        filename = "_" + filename[1:]

    return filename

def validate_pdf_magic_bytes(content: bytes) -> bool:
    """
    Validate PDF magic bytes.

    Args:
        content: File content (first few bytes)

    Returns:
        True if valid PDF, False otherwise
    """
    if len(content) < 5:
        return False

    return content[:5] == b"%PDF-"

def validate_file_size(size: int, max_size: int = 500 * 1024 * 1024) -> bool:
    """
    Validate file size.

    Args:
        size: File size in bytes
        max_size: Maximum allowed size (default: 500MB)

    Returns:
        True if size is valid, False otherwise
    """
    return 0 < size <= max_size

def validate_server_url(url: str) -> bool:
    """
    Validate server URL format.

    Args:
        url: Server URL

    Returns:
        True if valid URL, False otherwise
    """
    return url.startswith(("http://", "https://"))
```

## Data Flow

### Configuration Loading Flow

```
1. Check command-line flags (highest priority)
   ↓
2. Check environment variables (PDF2MD_*)
   ↓
3. Load config file (~/.pdf2md/config.json)
   ↓
4. Use hardcoded defaults (lowest priority)
```

### Conversion Job Lifecycle

```
1. Job Created (ConversionStatus.PENDING)
   - File uploaded
   - Metadata extracted
   ↓
2. Job Started (ConversionStatus.IN_PROGRESS)
   - Conversion begun
   - Timestamp recorded
   ↓
3. Job Completed (ConversionStatus.COMPLETED)
   OR
   Job Failed (ConversionStatus.FAILED)
   - Results recorded
   - Cleanup performed
```

---

**Model Version**: 1.0.0
**Last Updated**: 2026-01-06
