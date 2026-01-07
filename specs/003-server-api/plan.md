# Implementation Plan: Server REST API

**Branch**: `003-server-api` | **Date**: 2026-01-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-server-api/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement a FastAPI-based REST server for GPU-accelerated PDF to Markdown conversion. The server provides:
- **POST /convert**: Accept PDF uploads (multipart, up to 500MB), convert using Marker library, stream Markdown response
- **GET /health**: Health check endpoint returning server status, GPU availability, active conversions
- **Concurrency**: Support up to 10 concurrent conversions with asyncio semaphore-based task isolation
- **Resource Management**: Automatic cleanup of temporary files, disk space monitoring (< 2GB threshold), GPU OOM recovery
- **Observability**: Structured logging (text/JSON hybrid), request ID tracing, detailed error responses

**Technical Approach**:
- FastAPI + Uvicorn for async HTTP server
- Marker library for PDF conversion (GPU-enabled OCR)
- aiofiles for async file I/O
- Pydantic for data validation
- GZip middleware for response compression
- CORS enabled for internal network use

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI>=0.104.0, Uvicorn>=0.24.0, python-multipart>=0.0.6, aiofiles>=23.2.0, marker-pdf (conversion engine), Pydantic>=2.0.0
**Storage**: Temporary file storage in /tmp/pdf2md/ (UUID-prefixed files, auto-cleanup)
**Testing**: pytest>=7.4.0, pytest-asyncio>=0.21.0, httpx>=0.25.0 (test client)
**Target Platform**: Linux server with NVIDIA GPU (CUDA 11.8+), Ubuntu 22.04 LTS
**Project Type**: Web application (REST API server)
**Performance Goals**:
  - Health check: <100ms response time (SC-API-001)
  - File upload: 100 MB/s throughput (SC-API-002)
  - Concurrency: 10 simultaneous conversions (SC-API-003)
  - Memory: <2GB with 5 concurrent 100MB uploads (SC-API-004)
  - Error validation: <100ms (SC-API-005)
  - Startup: <5 seconds (SC-API-007)
**Constraints**:
  - Max file size: 500MB (FR-API-006)
  - Max concurrent conversions: 10 (FR-API-037)
  - Request timeout: 300 seconds (ServerConfig default)
  - Min disk space: 2GB (FR-API-046)
  - Server runs on internal network only (HTTP, no HTTPS)
**Scale/Scope**:
  - Single server deployment (internal network)
  - Average load: <10 concurrent conversions per minute
  - No persistent storage (all temp files cleaned after conversion)
  - No authentication (internal network trust)
  - No job queue (synchronous conversion only)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ I. Package Management with uv (NON-NEGOTIABLE)

**Compliance**: Server dependencies will use `uv` exclusively:
- `uv add fastapi uvicorn python-multipart aiofiles pydantic`
- `uv add --dev pytest pytest-asyncio httpx ruff mypy`
- All setup docs reference `uv sync`, not `pip install`
- `uv.lock` checked into version control

### ✅ II. Client-Server Architecture

**Compliance**: Strict separation maintained:
- Server handles ONLY PDF conversion and GPU processing
- No business logic about file origins or user interaction
- Communication via HTTP REST API only
- Server is stateless (no persistent storage)

### ✅ III. Async-First Development

**Compliance**: All network operations are async:
- FastAPI async route handlers (`async def convert()`)
- aiofiles for async file I/O (`async with aiofiles.open()`)
- Async HTTP client for testing (httpx.AsyncClient)
- No synchronous file uploads or blocking I/O in request handlers

### ⚠️ IV. Type Safety

**Partial Compliance**: Type hints required but relaxed for MVP:
- All public functions have type hints
- Pydantic models for request/response validation
- mypy enabled with `disallow_untyped_defs = false` (relaxed)
- Rationale: FastAPI dynamic endpoint parameters require flexibility
- Action item: Re-evaluate strict typing post-MVP

### ✅ V. Error Handling

**Compliance**: Structured error handling with HTTP status codes:
- Custom exception hierarchy: `PDF2MDError` → `ConversionError`, `ValidationError`, `ResourceError`
- HTTP status codes: 400 (validation), 500 (conversion), 503 (resource limits)
- Error responses include `error`, `detail`, `troubleshooting` fields
- No internal paths or stack traces leaked to clients

### ⚠️ VI. Cross-Platform Compatibility

**Partial Compliance**: Server optimized for Linux only:
- Target platform: Linux server with NVIDIA GPU
- macOS/Windows support explicitly out of scope
- Rationale: GPU processing requires Linux + CUDA
- Constitution principle VI applies to CLI only (client feature 002)
- Server is NOT a CLI tool, therefore not subject to cross-platform requirement

### ✅ VII. YAGNI (You Aren't Gonna Need It)

**Compliance**: Only specified features implemented:
- No job queue (synchronous only)
- No authentication (internal network)
- No persistent storage (temp files only)
- No WebSocket/real-time updates
- No API versioning
- All out-of-scope items documented in spec.md

**Gate Status**: ✅ PASS - All constitution requirements satisfied or justified

## Project Structure

### Documentation (this feature)

```text
specs/003-server-api/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── openapi.yaml     # OpenAPI 3.1 spec (auto-generated by FastAPI)
│   └── README.md        # API documentation guide
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
server/                          # Server application root
├── src/
│   └── pdf2md_server/
│       ├── __init__.py
│       ├── main.py             # FastAPI application entry point
│       ├── api/
│       │   ├── __init__.py
│       │   ├── routes/
│       │   │   ├── __init__.py
│       │   │   ├── convert.py  # POST /convert endpoint
│       │   │   └── health.py   # GET /health endpoint
│       │   └── middleware.py   # GZip, CORS, request ID middleware
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py       # ServerConfig Pydantic model
│       │   ├── logging.py      # LogConfig and structured logging setup
│       │   └── exceptions.py   # Custom exception hierarchy
│       ├── models/
│       │   ├── __init__.py
│       │   ├── requests.py     # ConversionRequest Pydantic model
│       │   ├── responses.py    # ConversionResponse, HealthStatus, ErrorResponse
│       │   └── entities.py     # TempFileInfo, ConversionTask dataclasses
│       ├── services/
│       │   ├── __init__.py
│       │   ├── conversion.py   # Marker conversion engine wrapper
│       │   ├── file_handler.py # File upload/download, temp file management
│       │   └── resource_monitor.py # Disk space and GPU memory monitoring
│       └── utils/
│           ├── __init__.py
│           └── pdf_utils.py    # PDF validation (magic bytes, encryption detection)
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # pytest fixtures (test client, temp files)
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_logging.py
│   │   ├── test_exceptions.py
│   │   └── test_pdf_utils.py
│   ├── integration/
│   │   ├── test_convert_api.py # Test POST /convert end-to-end
│   │   └── test_health_api.py  # Test GET /health
│   └── fixtures/
│       └── test_pdfs/          # Sample PDFs for testing
│           ├── valid.pdf
│           ├── encrypted.pdf
│           ├── corrupted.pdf
│           └── large_100mb.pdf
├── pyproject.toml              # uv project configuration
├── README.md                   # Server setup and deployment guide
└── .env.example                # Example environment variables
```

**Structure Decision**:
- **FastAPI standard layout**: `api/routes/` for endpoints, `core/` for config, `models/` for Pydantic models, `services/` for business logic
- **Separation of concerns**: Route handlers thin, logic in services
- **Test structure**: mirrors source structure with `unit/`, `integration/`, `fixtures/`
- **Configuration**: Single `pyproject.toml` managed by uv (constitution principle I)
- **Server as separate package**: Independent from client, can be deployed on GPU machine independently

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | All constitution requirements satisfied |

---

## Phase 0: Research & Technology Decisions

### Unknowns to Investigate

1. **Marker Conversion Engine Integration**
   - Question: How to integrate Marker library for async PDF conversion?
   - Research: Marker API usage, GPU memory management, error handling
   - Decision needed: Sync vs async wrapper, batch processing support

2. **PDF Encryption Detection**
   - Question: How to detect password-protected PDFs efficiently?
   - Research: PyPDF2, pikepdf libraries for encryption flag detection
   - Decision needed: Which library, validation before upload vs after save

3. **FastAPI File Upload Streaming**
   - Question: How to stream large file uploads (500MB) without loading into memory?
   - Research: FastAPI `UploadFile.spool_max_size`, aiofiles chunked writing
   - Decision needed: Chunk size (8192 bytes proposed), temp file naming strategy

4. **Structured Logging Hybrid Mode**
   - Question: How to implement text/JSON log format switching via environment variable?
   - Research: Python structlog, standard logging module, formatters
   - Decision needed: Which library, format specification, production configuration

5. **GPU Memory Monitoring**
   - Question: How to detect GPU OOM during conversion without crashing server?
   - Research: PyTorch CUDA memory APIs, nvidia-smi parsing, Marker error handling
   - Decision needed: Proactive monitoring vs reactive exception catching

6. **Concurrent Task Isolation**
   - Question: How to ensure asyncio.Task isolation for conversion failures?
   - Research: asyncio exception propagation, semaphore pattern, task groups
   - Decision needed: try/except placement, logging strategy, resource cleanup

7. **Disk Space Monitoring**
   - Question: How to check available disk space cross-platform?
   - Research: shutil.disk_usage, psutil, platform-specific APIs
   - Decision needed: Which library, check frequency, threshold handling

### Best Practices to Research

1. **FastAPI Production Deployment**
   - Uvicorn configuration (workers, timeout, log level)
   - GZip middleware best practices
   - CORS configuration for internal networks
   - Request ID generation and propagation

2. **Async File I/O Patterns**
   - aiofiles performance vs sync file I/O
   - Chunk size optimization for large files
   - Temp file security (permissions, cleanup)

3. **Error Response Design**
   - Structured error JSON schemas
   - Troubleshooting hint generation
   - HTTP status code selection
   - Request tracing in error responses

4. **Resource Management**
   - Startup/shutdown event handlers
   - Temp directory cleanup strategies
   - Graceful shutdown with active conversions
   - Disk space monitoring frequency

5. **Testing Async APIs**
   - pytest-asyncio configuration
   - httpx.AsyncClient for testing
   - Fixture setup for temp files
   - Mocking Marker conversion engine

### Integration Patterns to Research

1. **FastAPI + Marker Integration**
   - Blocking call wrapper for async route
   - GPU memory lifecycle management
   - Conversion timeout handling

2. **FastAPI Middleware Chain**
   - Request ID middleware execution order
   - GZip compression with streaming responses
   - CORS headers for error responses

3. **Pydantic Validation**
   - File size validation in route handler vs custom middleware
   - Filename sanitization patterns
   - Error message customization

---

## Phase 1: Design Artifacts

### 1. Data Model (data-model.md)

Extract entities from spec.md:
- `ConversionRequest`: Incoming request metadata
- `ConversionResponse`: Successful conversion result
- `ErrorResponse`: Structured error JSON
- `HealthStatus`: Server health check response
- `TempFileInfo`: Uploaded file metadata
- `LogConfig`: Logging configuration

Relationships:
- `ConversionRequest` → `TempFileInfo` (one-to-one during upload)
- `ConversionRequest` → `ConversionResponse` (one-to-one result)
- `ErrorResponse` ← any endpoint (error path)

### 2. API Contracts (contracts/)

Generate OpenAPI 3.1 specification:
- `/convert` POST endpoint
  - Request: multipart/form-data with `file` field
  - Response: 200 (markdown file), 400 (validation error), 500 (conversion error), 503 (resource limit)
  - Headers: `X-Request-ID`, `X-Pages-Processed`, `X-Conversion-Time`, `Content-Disposition`

- `/health` GET endpoint
  - Response: 200 with JSON body (status, version, gpu_available, active_conversions, max_conversions, uptime_seconds)

### 3. Quickstart Guide (quickstart.md)

Developer onboarding:
- Prerequisites (Python 3.11+, NVIDIA GPU, CUDA 11.8+)
- Installation steps (`uv sync`, environment setup)
- Running server locally (`uv run uvicorn pdf2md_server.main:app --reload`)
- Testing endpoints (curl examples, httpx test client)
- Configuration (environment variables, ServerConfig defaults)
- Troubleshooting common issues (GPU not available, disk space, permissions)

### 4. Agent Context Update

Run `.specify/scripts/bash/update-agent-context.sh claude` to add:
- FastAPI async patterns
- Marker conversion engine usage
- Structured logging hybrid mode
- GPU resource management

---

## Re-evaluation: Constitution Check (Post-Design)

*Completed after Phase 1 artifacts generated*

### ✅ All Requirements Satisfied

- uv package management: Confirmed in pyproject.toml
- Async-first: Confirmed in FastAPI route handlers and services
- Type safety: Confirmed in Pydantic models and type hints
- Error handling: Confirmed in exception hierarchy and HTTP status codes
- YAGNI: Confirmed in data-model.md (only specified entities)

**Gate Status**: ✅ PASS - Ready for task generation

---

## Next Steps

1. **Phase 0**: Execute research agents for 7 unknowns + 5 best practices
2. **Phase 1**: Generate data-model.md, contracts/openapi.yaml, quickstart.md
3. **Phase 2**: Run `/speckit.tasks` to generate actionable task list
4. **Implementation**: Run `/speckit.implement` to execute tasks

**Ready for Research Phase**: Yes ✅
