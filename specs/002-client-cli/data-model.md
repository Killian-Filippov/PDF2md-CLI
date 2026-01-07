# Data Model: Client CLI Interface

**Feature**: 002-client-cli
**Date**: 2026-01-07
**Status**: Complete

This document defines the data entities and models for the client CLI component.

---

## Core Entities

### 1. ServerConfig (Configuration Model)

**Purpose**: Type-safe configuration management with validation

**Fields**:
| Field | Type | Default | Validation | Description |
|-------|------|---------|------------|-------------|
| `server_url` | `str` | `"http://localhost:8000"` | Must start with `http://` or `https://` | URL of PDF conversion server |
| `timeout` | `int` | `300` | 1-3600 seconds | Request timeout in seconds |
| `chunk_size` | `int` | `8192` | 1024-1048576 bytes | Upload/download chunk size |
| `max_retries` | `int` | `3` | 0-10 attempts | Maximum retry attempts for network errors |
| `verify_ssl` | `bool` | `true` | - | Verify SSL certificates for HTTPS |
| `output_dir` | `Optional[Path]` | `null` | Must exist if specified | Custom output directory (null = same as PDF) |
| `overwrite` | `bool` | `false` | - | Overwrite existing Markdown files |

**Validation Rules**:
- `server_url`: Must be valid URL, trailing slashes stripped
- `timeout`: Must be between 1 and 3600 seconds (1 hour max)
- `chunk_size`: Must be power of 2, between 1KB and 1MB
- `max_retries`: Cannot be negative
- `output_dir`: Directory must exist if specified

**Config Hierarchy** (priority order):
1. CLI flags (highest priority)
2. Environment variables (`PDF2MD_SERVER_URL`, `PDF2MD_TIMEOUT`, etc.)
3. Config file (`~/.pdf2md/config.json` or platform-specific)
4. Hard-coded defaults (lowest priority)

**Pydantic Model**:
```python
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional

class ServerConfig(BaseSettings):
    """Configuration model for PDF2md CLI."""

    server_url: str = Field(
        default="http://localhost:8000",
        description="URL of the PDF conversion server"
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
        description="Upload chunk size in bytes"
    )

    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts"
    )

    verify_ssl: bool = Field(
        default=True,
        description="Verify SSL certificates"
    )

    output_dir: Optional[Path] = Field(
        default=None,
        description="Custom output directory"
    )

    overwrite: bool = Field(
        default=False,
        description="Overwrite existing files"
    )

    model_config = SettingsConfigDict(
        env_prefix="PDF2MD_",
        env_file=".env",
        extra="ignore"
    )

    @field_validator("server_url")
    @classmethod
    def validate_server_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("server_url must start with http:// or https://")
        return v.rstrip("/")

    @field_validator("output_dir")
    @classmethod
    def validate_output_dir(cls, v: Optional[Path]) -> Optional[Path]:
        if v is not None and not v.exists():
            raise ValueError(f"output_dir does not exist: {v}")
        return v
```

**JSON Schema** (for config file):
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "server_url": {
      "type": "string",
      "format": "uri",
      "default": "http://localhost:8000"
    },
    "timeout": {
      "type": "integer",
      "minimum": 1,
      "maximum": 3600,
      "default": 300
    },
    "chunk_size": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 1048576,
      "default": 8192
    },
    "max_retries": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10,
      "default": 3
    },
    "verify_ssl": {
      "type": "boolean",
      "default": true
    },
    "output_dir": {
      "type": ["string", "null"],
      "default": null
    },
    "overwrite": {
      "type": "boolean",
      "default": false
    }
  }
}
```

---

### 2. ConversionOptions (Command-Line Options)

**Purpose**: User-provided options for a single conversion operation

**Fields**:
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `input_path` | `Path` | Yes | - | Path to input PDF file |
| `output_path` | `Optional[Path]` | No | Derived from input | Output Markdown file path |
| `output_dir` | `Optional[Path]` | No | From config | Custom output directory |
| `overwrite` | `bool` | No | From config | Overwrite existing file |
| `verbose` | `bool` | No | `false` | Enable verbose logging |
| `server_url` | `Optional[str]` | No | From config | Override server URL |
| `timeout` | `Optional[int]` | No | From config | Override timeout |

**Derivation Rules**:
- `output_path`:
  - If `output_dir` specified: `{output_dir}/{input_filename}.md`
  - Else: `{input_path.parent}/{input_filename}.md`
- `server_url`: CLI flag > config > default
- `timeout`: CLI flag > config > default
- `overwrite`: CLI flag > config > default

**Pydantic Model**:
```python
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Optional

class ConversionOptions(BaseModel):
    """Options for a single PDF conversion."""

    input_path: Path = Field(..., description="Path to input PDF file")
    output_path: Optional[Path] = Field(None, description="Output Markdown file path")
    output_dir: Optional[Path] = Field(None, description="Custom output directory")
    overwrite: bool = Field(False, description="Overwrite existing file")
    verbose: bool = Field(False, description="Enable verbose logging")
    server_url: Optional[str] = Field(None, description="Override server URL")
    timeout: Optional[int] = Field(None, description="Override timeout")

    def get_output_path(self, config: ServerConfig) -> Path:
        """Determine output path from options and config."""
        if self.output_path:
            return self.output_path

        # Use output_dir from options or config
        base_dir = self.output_dir or config.output_dir or self.input_path.parent

        # Generate filename: input PDF name with .md extension
        return base_dir / f"{self.input_path.stem}.md"
```

---

### 3. ConversionResult (Operation Result)

**Purpose**: Result of a PDF to Markdown conversion operation

**Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `success` | `bool` | Whether conversion succeeded |
| `output_path` | `Path` | Path to generated Markdown file |
| `page_count` | `int` | Number of pages in PDF |
| `duration` | `float` | Conversion time in seconds |
| `file_size` | `int` | Size of output Markdown file in bytes |
| `error` | `Optional[str]` | Error message if failed |

**Pydantic Model**:
```python
from pydantic import BaseModel
from pathlib import Path
from typing import Optional

class ConversionResult(BaseModel):
    """Result of a PDF conversion operation."""

    success: bool
    output_path: Optional[Path] = None
    page_count: int = 0
    duration: float = 0.0
    file_size: int = 0
    error: Optional[str] = None

    class Config:
        json_encoders = {
            Path: str
        }
```

---

## State Machines

### Conversion State Machine

```
┌─────────────┐
│   START     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  VALIDATING │  ← Check file exists, readable, PDF format
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  UPLOADING  │  ← Upload PDF to server with progress bar
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ CONVERTING  │  ← Server processes PDF (OCR, extraction)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ DOWNLOADING │  ← Download Markdown file with progress bar
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   COMPLETE  │  ← Success message, exit code 0
└─────────────┘

Error States (any stage):
  │
  ├─→ VALIDATION_ERROR (exit code 3)
  ├─→ NETWORK_ERROR (exit code 2)
  ├─→ CONVERSION_ERROR (exit code 4)
  └─→ CONFIG_ERROR (exit code 5)
```

**State Transitions**:
- `START` → `VALIDATING`: User runs command
- `VALIDATING` → `UPLOADING`: File validation passed
- `VALIDATING` → `VALIDATION_ERROR`: File not found, invalid format, permissions
- `UPLOADING` → `CONVERTING`: Upload complete, server processing
- `UPLOADING` → `NETWORK_ERROR`: Connection failed, timeout
- `CONVERTING` → `DOWNLOADING`: Server completed conversion
- `CONVERTING` → `CONVERSION_ERROR`: Server-side failure
- `DOWNLOADING` → `COMPLETE`: Download complete, file saved
- `DOWNLOADING` → `NETWORK_ERROR`: Download failed

---

## Error Hierarchy

```
Exception (Python built-in)
    │
    └── PDF2MDError (base)
            │
            ├── NetworkError (exit code 2)
            │       ├── ConnectionError
            │       ├── TimeoutError
            │       └── HTTPError
            │
            ├── ValidationError (exit code 3)
            │       ├── FileNotFoundError
            │       ├── InvalidFileError
            │       └── ConfigValidationError
            │
            ├── ConversionError (exit code 4)
            │       ├── ServerConversionError
            │       └── ResourceError
            │
            └── ConfigError (exit code 5)
                    ├── MissingConfigError
                    └── CorruptedConfigError
```

**Exit Code Mapping**:
| Exit Code | Error Type | Description |
|-----------|------------|-------------|
| 0 | Success | Conversion completed |
| 1 | GenericError | Unexpected error |
| 2 | NetworkError | Connection, timeout, HTTP error |
| 3 | ValidationError | Invalid input |
| 4 | ConversionError | Server-side failure |
| 5 | ConfigError | Configuration issue |
| 130 | SIGINT | User cancelled (Ctrl+C) |

---

## Configuration File Schema

**Location**: `~/.pdf2md/config.json` (or platform-specific)

**Example**:
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

**Environment Variables**:
| Variable | Type | Example |
|----------|------|---------|
| `PDF2MD_SERVER_URL` | string | `http://192.168.1.100:8000` |
| `PDF2MD_TIMEOUT` | int | `300` |
| `PDF2MD_CHUNK_SIZE` | int | `8192` |
| `PDF2MD_MAX_RETRIES` | int | `3` |
| `PDF2MD_VERIFY_SSL` | bool | `true` |
| `PDF2MD_OUTPUT_DIR` | path | `/home/user/output` |
| `PDF2MD_OVERWRITE` | bool | `false` |
| `PDF2MD_VERBOSE` | bool | `false` |

---

## Data Flow

### 1. Configuration Loading Flow

```
User runs command
       │
       ▼
Load default ServerConfig (Pydantic loads env vars)
       │
       ▼
Check if config file exists
       │
       ├─ Yes → Parse JSON, merge with defaults
       │         │
       │         ├─ Valid → Use merged config
       │         └─ Invalid → Backup corrupted file, use defaults
       │
       └─ No → Use defaults (Pydantic + env vars)
       │
       ▼
Apply CLI flag overrides (highest priority)
       │
       ▼
Final merged config
```

### 2. Conversion Flow

```
CLI command invoked
       │
       ▼
Parse arguments → ConversionOptions
       │
       ▼
Load config → ServerConfig
       │
       ▼
Validate input file (exists, readable, PDF format)
       │
       ├─ Invalid → Raise ValidationError (exit 3)
       │
       ▼
Merge options + config → final options
       │
       ▼
Async bridge: asyncio.run(_convert_async())
       │
       ▼
Create httpx.AsyncClient
       │
       ▼
Upload PDF (with progress bar)
       │
       ├─ Network error → Raise NetworkError (exit 2)
       │
       ▼
Wait for conversion (polling)
       │
       ├─ Server error → Raise ConversionError (exit 4)
       │
       ▼
Download Markdown (with progress bar)
       │
       ├─ Network error → Raise NetworkError (exit 2)
       │
       ▼
Save to output path
       │
       ├─ File exists + !overwrite → Prompt user
       │
       ▼
Display success message
       │
       ▼
Exit code 0
```

---

## Relationships

```
ServerConfig
    │
    ├─ used by ──→ ConfigManager (load/save)
    │
    └─ merged with ──→ ConversionOptions
                          │
                          └─ produces ──→ final conversion parameters

ConversionOptions
    │
    ├─ validated by ──→ FileHandler
    │
    └─ passed to ──→ PDF2MDClient
                          │
                          └─ returns ──→ ConversionResult

ConversionResult
    │
    └─ displayed by ──→ CLIOutput (Rich formatter)
```

---

## Validation Rules Summary

| Entity | Field | Rule | Error |
|--------|-------|------|-------|
| ServerConfig | server_url | Must be valid URL | ValueError |
| ServerConfig | timeout | 1-3600 seconds | ValueError |
| ServerConfig | chunk_size | 1024-1048576 bytes | ValueError |
| ServerConfig | output_dir | Must exist if specified | ValueError |
| ConversionOptions | input_path | Must exist, be readable | FileNotFoundError |
| ConversionOptions | input_path | Must be PDF file | InvalidFileError |
| ConversionOptions | output_path | Parent directory writable | PermissionError |
