# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PDF2md-CLI is a client-server CLI tool that converts PDF files to Markdown format using a remote GPU-enabled server. Users run the CLI on their local machine to send PDFs to a remote server (device A with GPU), which converts them and returns the Markdown files back to the original PDF location.

## Architecture

The project follows a **client-server architecture** with two main components:

### Client Component (`client/`)
- **CLI Interface**: Command-line tool built with `click` or `typer`
- **HTTP Client**: Uses `httpx` for async file upload/download
- **Configuration Management**: JSON-based config at `~/.pdf2md/config.json`
- **File Handling**: Manages PDF upload and MD file save to original path

### Server Component (`server/`)
- **FastAPI Application**: REST API for receiving PDFs and serving converted MDs
- **PDF Conversion Engine**: Uses `marker` library for high-quality PDF→MD conversion
- **GPU Support**: Leverages GPU acceleration through marker's OCR capabilities
- **File Processing**: Handles multipart file uploads and returns converted files

## Technology Stack

**Client:**
- `click` or `typer` - CLI framework
- `httpx` - Async HTTP client
- `requests` - Fallback sync client
- `tqdm` - Progress bars

**Server:**
- `FastAPI` - Web framework
- `uvicorn` - ASGI server
- `marker` - PDF to Markdown conversion engine
- `python-multipart` - Multipart form data handling

**Development:**
- `pyproject.toml` - Dependency management (modern Python packaging)
- Virtual environment (`.venv/`) - Isolated development environment

**Code Quality Tools:**
- `ruff` - Fast Python linter and formatter (replaces flake8, black, isort)
- `mypy` - Static type checker (optional, enabled for critical paths)
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting

## API Design

The REST API endpoints (planned):
- `POST /convert` - Upload PDF, get conversion task ID
- `GET /status/{task_id}` - Check conversion status
- `GET /download/{task_id}` - Download converted Markdown file
- Alternative: `POST /convert` - Synchronous conversion (simpler, blocking)

## Configuration File

Location: `~/.pdf2md/config.json`

```json
{
  "server_url": "http://192.168.1.100:8000",
  "timeout": 300,
  "chunk_size": 8192
}
```

## Key Design Decisions

1. **HTTP REST API**: Chosen over gRPC/WebSocket for internal network use due to better developer experience and sufficient performance
2. **Marker Engine**: Selected for high-quality conversion, GPU support, and active maintenance (15k+ stars on GitHub)
3. **Async Client**: httpx provides async support for potential future concurrent uploads
4. **Single File Support**: Initial version supports only single file conversion (no batch processing)

## Development Workflow

```bash
# Install dependencies
pip install -e .

# Run server (device A)
cd server && uvicorn main:app --reload

# Run client (local machine)
pdf2md /path/to/document.pdf
```

## Project Status

**Current**: Initial setup phase, architecture planned
**Next Steps**:
1. Create project structure and dependencies
2. Implement server (FastAPI + Marker)
3. Implement client (CLI + HTTP client)
4. Add configuration management
5. Write documentation
