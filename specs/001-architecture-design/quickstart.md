# Quickstart Guide

**Feature**: PDF2md-CLI
**Version**: 1.0.0
**Date**: 2026-01-06

## Overview

This guide helps you set up the PDF2md-CLI development environment and run the application locally for development and testing.

## Prerequisites

### System Requirements

**For Client (Any Platform)**:
- Python 3.11 or higher
- 100 MB free disk space
- Network access to server

**For Server (Linux with GPU)**:
- Python 3.11 or higher
- NVIDIA GPU with CUDA support
- 2 GB GPU memory minimum
- 4 GB RAM minimum
- 10 GB free disk space
- Linux (Ubuntu 22.04 recommended)

### Software Dependencies

**Required**:
- Python 3.11+
- pip (Python package manager)
- git (for cloning repository)

**For GPU Support** (Server only):
- NVIDIA GPU drivers (525.60.13 or later)
- CUDA Toolkit 11.8 or later

## Quick Start (5 Minutes)

### 1. Clone Repository

```bash
git clone https://github.com/your-org/pdf2md-cli.git
cd pdf2md-cli
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -e .
```

This installs:
- Client dependencies (any platform)
- Server dependencies (Linux only)
- Development tools (ruff, pytest, etc.)

### 4. Start Server (GPU Machine)

```bash
# On the machine with GPU
uvicorn server.main:app --reload --port 8000
```

**Expected Output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 5. Configure Client (Any Machine)

```bash
# Initialize configuration
pdf2md config init --server-url http://192.168.1.100:8000

# Verify connection
pdf2md test-connection
```

**Expected Output**:
```
✓ Connected to server successfully
  Server: http://192.168.1.100:8000
  Version: 1.0.0
  GPU Available: Yes
```

### 6. Convert PDF

```bash
# Convert a PDF file
pdf2md document.pdf

# Expected output
✓ Converting: document.pdf (15.2 MB)
✓ Upload: [████████████████████] 100% 3.2s
✓ Converting... (12.5s)
✓ Download: [████████████████████] 100% 1.8s
✓ Converted: document.md (42 pages, 17.7s total)
```

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/your-username/pdf2md-cli.git
cd pdf2md-cli

# Add upstream remote
git remote add upstream https://github.com/original-org/pdf2md-cli.git
```

### 2. Create Development Branch

```bash
git checkout -b feature/your-feature-name
```

### 3. Install Development Dependencies

```bash
# Install with development extras
pip install -e ".[dev]"

# This installs additional tools:
# - ruff (linting and formatting)
# - pytest (testing)
# - pytest-cov (coverage)
# - pytest-asyncio (async tests)
# - mypy (type checking)
```

### 4. Verify Installation

```bash
# Run all checks
python -m pytest
python -m ruff check .
python -m mypy server/ client/

# Expected: All tests pass, no linting errors
```

## Project Structure

```
pdf2md-cli/
├── client/                 # CLI client code
│   ├── __init__.py
│   ├── cli.py             # Typer CLI commands
│   ├── config.py          # Configuration management
│   ├── client.py          # HTTP client
│   ├── file_handler.py    # File operations
│   └── exceptions.py      # Client exceptions
│
├── server/                 # FastAPI server code
│   ├── __init__.py
│   ├── main.py            # FastAPI app entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── convert.py     # Conversion endpoint
│   ├── core/
│   │   ├── __init__.py
│   │   ├── converter.py   # Marker wrapper
│   │   ├── file_manager.py # Temp file handling
│   │   └── gpu_manager.py # GPU resource management
│   ├── models/
│   │   ├── __init__.py
│   │   └── requests.py    # Pydantic schemas
│   └── utils/
│       ├── __init__.py
│       ├── validation.py  # Input validation
│       └── cleanup.py     # Cleanup utilities
│
├── shared/                 # Shared utilities
│   ├── __init__.py
│   └── validation.py
│
├── tests/
│   ├── contract/          # API contract tests
│   ├── integration/       # End-to-end tests
│   └── unit/              # Component tests
│
├── specs/                  # Design documents
│   └── 001-architecture-design/
│       ├── spec.md
│       ├── contracts.md
│       ├── data-model.md
│       └── quickstart.md  # This file
│
├── docs/                   # Additional documentation
│   └── architecture-design.md
│
├── pyproject.toml         # Dependencies and config
├── CLAUDE.md              # Project guidance
├── README.md              # User documentation
└── LICENSE                # MIT License
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test Category

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Contract tests only
pytest tests/contract/
```

### Run with Coverage

```bash
pytest --cov=server --cov=client --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Run Specific Test

```bash
pytest tests/unit/test_client.py::test_validate_pdf_file
```

### Run Async Tests

```bash
pytest tests/ -k async
```

## Development Workflow

### 1. Code Linting and Formatting

**Check Linting**:
```bash
ruff check .
```

**Auto-fix Linting Issues**:
```bash
ruff check --fix .
```

**Format Code**:
```bash
ruff format .
```

### 2. Type Checking

```bash
# Check server code
mypy server/

# Check client code
mypy client/

# Check all
mypy server/ client/
```

### 3. Run Server in Development Mode

```bash
# With auto-reload on file changes
uvicorn server.main:app --reload --port 8000

# With verbose logging
uvicorn server.main:app --reload --log-level debug

# With custom host and port
uvicorn server.main:app --host 0.0.0.0 --port 8080
```

### 4. Test Client Locally

```bash
# In a separate terminal, activate venv
source .venv/bin/activate

# Test with sample PDF
pdf2md tests/fixtures/sample.pdf

# Test with verbose output
pdf2md --verbose document.pdf

# Test with custom output
pdf2md document.pdf --output /tmp/output.md
```

## Debugging

### Debug Server

**Enable Debug Logging**:
```bash
export PDF2MD_VERBOSE=true
uvicorn server.main:app --reload --log-level debug
```

**Use Python Debugger**:
```python
# In server code, add breakpoint
import pdb; pdb.set_trace()

# Or use ipdb (better formatting)
import ipdb; ipdb.set_trace()
```

**Attach Debugger**:
```bash
# Run server with debugger
python -m pdb -m uvicorn server.main:app
```

### Debug Client

**Enable Verbose Mode**:
```bash
pdf2md --verbose document.pdf
```

**Check Configuration**:
```bash
pdf2md config show
```

**Test Network Connection**:
```bash
# Test server connectivity
curl http://192.168.1.100:8000/health

# Test with file upload
curl -X POST \
  -F "file=@document.pdf" \
  http://192.168.1.100:8000/convert \
  -o output.md
```

## Common Issues and Solutions

### Issue 1: Import Error "No module named 'marker'"

**Solution**:
```bash
# Install server dependencies
pip install -e ".[server]"

# Or install marker directly
pip install marker-pdf
```

### Issue 2: GPU Not Available

**Check GPU**:
```bash
# Check NVIDIA driver
nvidia-smi

# Check PyTorch CUDA
python -c "import torch; print(torch.cuda.is_available())"
```

**Solution**: Install CUDA Toolkit and NVIDIA drivers

### Issue 3: Port Already in Use

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# Or use different port
uvicorn server.main:app --port 8080
```

### Issue 4: Permission Denied Writing to /tmp

**Solution**:
```bash
# Set custom temp directory
export TMPDIR=/home/user/pdf2md-temp
mkdir -p $TMPDIR

uvicorn server.main:app
```

### Issue 5: Configuration File Not Found

**Solution**:
```bash
# Create default config
pdf2md config init

# Or manually create
mkdir -p ~/.pdf2md
cat > ~/.pdf2md/config.json << EOF
{
  "server_url": "http://localhost:8000",
  "timeout": 300
}
EOF
```

## Performance Profiling

### Profile Server Performance

```bash
# Install profiler
pip install py-spy

# Run server
uvicorn server.main:app &

# Profile CPU usage
sudo py-spy top --pid $(pgrep -f uvicorn)

# Record flame graph
sudo py-spy record --pid $(pgrep -f uvicorn) -o profile.svg
```

### Profile Memory Usage

```bash
# Install memory profiler
pip install memory_profiler

# Profile server
python -m memory_profiler uvicorn server.main:app
```

### Profile Client Performance

```bash
# Use verbose mode to see timing
pdf2md --verbose document.pdf

# Expected output includes timing breakdown
✓ Upload: 3.2s (15.2 MB → 4.7 MB/s)
✓ Conversion: 12.5s (42 pages)
✓ Download: 1.8s (127 KB → 71 KB/s)
✓ Total: 17.5s
```

## Tips and Tricks

### 1. Auto-Reload on Code Changes

Server automatically reloads when code changes:

```bash
uvicorn server.main:app --reload
```

### 2. Test with Sample PDFs

Generate test PDFs:

```bash
# Create test PDF with Python
python -c "
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

c = canvas.Canvas('test.pdf', pagesize=letter)
c.drawString(100, 750, 'Hello, World!')
c.save()
"

# Convert it
pdf2md test.pdf
```

### 3. Use Environment Variables

```bash
# Override config without editing file
export PDF2MD_SERVER_URL=http://localhost:8000
export PDF2MD_VERBOSE=true
pdf2md document.pdf
```

### 4. Batch Conversion (Shell Script)

```bash
#!/bin/bash
# Convert all PDFs in current directory

for pdf in *.pdf; do
    echo "Converting $pdf..."
    pdf2md "$pdf"
done
```

### 5. Monitor Server Health

```bash
# Watch server stats
watch -n 5 'curl -s http://localhost:8000/health | jq'

# Or use browser
open http://localhost:8000/docs  # FastAPI auto-docs
```

## Next Steps

1. **Read Architecture**: `docs/architecture-design.md`
2. **Review API Contracts**: `specs/001-architecture-design/contracts.md`
3. **Understand Data Models**: `specs/001-architecture-design/data-model.md`
4. **Check Constitution**: `.specify/memory/constitution.md`

## Getting Help

- **Documentation**: `README.md`, `CLAUDE.md`
- **Issues**: https://github.com/your-org/pdf2md-cli/issues
- **Discussions**: https://github.com/your-org/pdf2md-cli/discussions

---

**Quickstart Version**: 1.0.0
**Last Updated**: 2026-01-06
