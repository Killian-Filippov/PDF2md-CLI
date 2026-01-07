# Quickstart Guide: Server REST API

**Feature**: 003-server-api
**Date**: 2026-01-07
**Audience**: Developers setting up PDF2md-CLI server

## Overview

This guide will help you quickly set up and run the PDF2md-CLI server on a Linux machine with NVIDIA GPU.

---

## Prerequisites

### Hardware

- **GPU**: NVIDIA GPU with CUDA 11.8+ support
- **VRAM**: Minimum 6GB free GPU memory (recommended 8GB+)
- **RAM**: 8GB system memory minimum (16GB recommended)
- **Disk**: 10GB free disk space for temporary files

### Software

- **Operating System**: Ubuntu 22.04 LTS (or similar Linux distribution)
- **Python**: 3.11 or later
- **CUDA Toolkit**: 11.8 or later (if GPU available)
- **Package Manager**: `uv` (required - see [Constitution](../../.specify/memory/constitution.md))

### Network

- Internal network connection between client machine and GPU server
- Open port 8000 (or configured port) on GPU server

---

## Installation

### Step 1: Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

### Step 2: Clone Repository

```bash
git clone https://github.com/your-org/pdf2md-cli.git
cd pdf2md-cli/server
```

### Step 3: Install Dependencies

```bash
# Create virtual environment and install dependencies
uv sync

# Verify installation
uv run python --version
```

**Note**: Per project constitution, `uv` is the exclusive package manager. Do NOT use `pip install`.

### Step 4: Verify GPU Setup

```bash
# Check CUDA installation
nvcc --version

# Check GPU availability
nvidia-smi

# Verify PyTorch can access GPU
uv run python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

Expected output:
```
CUDA available: True
```

If `False`, verify CUDA drivers and PyTorch installation.

---

## Configuration

### Environment Variables

Create `.env` file in `server/` directory:

```bash
# Server configuration
PDF2MD_HOST=0.0.0.0
PDF2MD_PORT=8000
PDF2MD_WORKERS=1
PDF2MD_LOG_LEVEL=INFO

# Logging format (text for dev, json for prod)
PDF2MD_LOG_FORMAT=text  # or "json" for production

# Conversion settings
PDF2MD_MAX_FILE_SIZE=524288000  # 500MB in bytes
PDF2MD_MAX_CONVERSIONS=10  # Max concurrent conversions
PDF2MD_TEMP_DIR=/tmp/pdf2md
```

### Logging Configuration

**Development** (human-readable logs):
```bash
export PDF2MD_LOG_FORMAT=text
```

Log output:
```log
[2026-01-07T10:30:45.123Z] [INFO] [abc-123-def] PDF conversion started
[2026-01-07T10:30:55.789Z] [INFO] [abc-123-def] Conversion completed pages=15 time=10.3
```

**Production** (structured JSON logs):
```bash
export PDF2MD_LOG_FORMAT=json
```

Log output:
```json
{"timestamp": "2026-01-07T10:30:45.123Z", "level": "info", "request_id": "abc-123-def", "message": "PDF conversion started"}
{"timestamp": "2026-01-07T10:30:55.789Z", "level": "info", "request_id": "abc-123-def", "message": "Conversion completed", "pages": 15, "time": 10.3}
```

---

## Running the Server

### Development Mode

```bash
cd server
uv run uvicorn pdf2md_server.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```log
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Features**:
- Auto-reload on code changes
- Detailed logging
- Debug mode enabled

### Production Mode

```bash
cd server
uv run uvicorn pdf2md_server.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 1 \
  --loop uvloop \
  --log-level info \
  --timeout-keep-alive 300 \
  --limit-concurrency 20
```

**Key Settings**:
- `--workers 1`: Single worker (GPU not shareable across processes)
- `--loop uvloop`: Faster event loop (Linux only)
- `--limit-concurrency 20`: 10 conversions + 10 overhead
- `--timeout-keep-alive 300`: 5-minute timeout for long conversions

---

## Testing the Server

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "gpu_available": true,
  "active_conversions": 0,
  "max_conversions": 10,
  "uptime_seconds": 10.5
}
```

### 2. Convert PDF (Success)

```bash
# Create test PDF (or use your own)
echo "%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Page /Parent 1 0 R /MediaBox [0 0 612 792] /Contents 3 0 R >>
endobj
3 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000158 00000 n
trailer
<< /Size 4 /Root 1 0 R >>
startxref
196
%%EOF" > test.pdf

# Upload and convert
curl -X POST http://localhost:8000/convert \
  -F "file=@test.pdf" \
  -D - \
  -o output.md

# Check response headers
# Response: 200 OK
# X-Request-ID: <uuid>
# X-Pages-Processed: 1
# X-Conversion-Time: <seconds>
```

### 3. Convert PDF (Error - Encrypted PDF)

```bash
# Upload encrypted PDF (if you have one)
curl -X POST http://localhost:8000/convert \
  -F "file=@encrypted.pdf" \
  -v
```

Expected response: 400 Bad Request with error_code "EncryptedPDF"

---

## API Documentation

### Interactive Docs

FastAPI auto-generates interactive API documentation:

**Swagger UI**: http://localhost:8000/docs
**ReDoc**: http://localhost:8000/redoc
**OpenAPI JSON**: http://localhost:8000/openapi.json

Features:
- Try out API endpoints directly from browser
- View request/response schemas
- Download OpenAPI specification

---

## Troubleshooting

### Server won't start

**Problem**: `ImportError: No module named 'fastapi'`

**Solution**:
```bash
cd server
uv sync  # Reinstall dependencies
```

### GPU not available

**Problem**: `CUDA available: False` in health check

**Solutions**:
1. Check GPU drivers:
   ```bash
   nvidia-smi
   ```

2. Check CUDA installation:
   ```bash
   nvcc --version
   ```

3. Verify PyTorch CUDA support:
   ```bash
   uv run python -c "import torch; print(torch.version.cuda)"
   ```

4. Reinstall PyTorch with CUDA support (if needed)

### File upload fails

**Problem**: 400 Bad Request "File type not supported"

**Solutions**:
1. Verify file has `.pdf` extension (case-insensitive)
2. Check file magic bytes start with `%PDF-`
3. Ensure file is not password-protected

### Disk space error

**Problem**: 503 Service Unavailable "Insufficient disk space"

**Solutions**:
1. Check available disk space:
   ```bash
   df -h /tmp/pdf2md
   ```

2. Clean up temp files:
   ```bash
   rm -rf /tmp/pdf2md/*
   ```

3. Ensure at least 2GB free space (FR-API-046)

### GPU out of memory

**Problem**: 503 Service Unavailable "GPU out of memory"

**Solutions**:
1. Check GPU memory usage:
   ```bash
   nvidia-smi
   ```

2. Wait 30 seconds for GPU memory to be released
3. Reduce concurrent conversions (default: 10)
4. Kill other GPU processes if needed

### Slow conversion

**Problem**: Conversion takes > 30 seconds

**Solutions**:
1. Check if GPU is being used (should be faster than CPU)
2. Verify PDF is not excessively large (pages, images)
3. Check GPU memory usage (may be swapping to CPU)

---

## Performance Tuning

### Chunk Size Optimization

Default chunk size: 64KB (recommended for 100MB/s+ throughput)

To adjust (in `src/pdf2md_server/services/file_handler.py`):
```python
CHUNK_SIZE = 64 * 1024  # Increase to 256KB for faster networks
```

Trade-offs:
- 8KB: Meets minimum requirement (FR-API-008)
- 64KB: Recommended for 100MB/s+ throughput
- 256KB: Maximum throughput (diminishing returns)

### Concurrency Limits

Default max concurrent conversions: 10 (FR-API-037)

To adjust (in `src/pdf2md_server/core/config.py`):
```python
MAX_CONVERSIONS = 10  # Increase if GPU has more VRAM
```

**Guidelines**:
- 6GB VRAM: 10 concurrent conversions (default)
- 8GB VRAM: 12-15 concurrent conversions
- 12GB+ VRAM: 20+ concurrent conversions

Monitor GPU memory with:
```bash
watch -n 1 nvidia-smi
```

---

## Monitoring

### Health Check Metrics

Monitor server health:

```bash
watch -n 5 'curl -s http://localhost:8000/health | jq .'
```

Key metrics:
- `status`: Should be "healthy"
- `gpu_available`: Should be true
- `active_conversions`: Should be ≤ max_conversions
- `uptime_seconds`: Server uptime

### Log Monitoring

**Development** (text logs):
```bash
tail -f /var/log/pdf2md/server.log
```

**Production** (JSON logs):
```bash
tail -f /var/log/pdf2md/server.log | jq
```

Filter by request_id:
```bash
grep "abc-123-def" /var/log/pdf2md/server.log
```

### Disk Space Monitoring

Check temp directory size:
```bash
du -sh /tmp/pdf2md
```

Count temp files:
```bash
ls /tmp/pdf2md | wc -l
```

---

## Deployment

### Systemd Service (Linux)

Create `/etc/systemd/system/pdf2md-server.service`:

```ini
[Unit]
Description=PDF2md Conversion Server
After=network.target

[Service]
Type=notify
User=pdf2md
Group=pdf2md
WorkingDirectory=/home/pdf2md/server
Environment="PATH=/home/pdf2md/server/.venv/bin"
ExecStart=/home/pdf2md/server/.venv/bin/uvicorn pdf2md_server.main:app --host 0.0.0.0 --port 8000
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable pdf2md-server
sudo systemctl start pdf2md-server
sudo systemctl status pdf2md-server
```

### Docker (Optional)

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN uv sync

# Expose port
EXPOSE 8000

# Run server
CMD ["uv", "run", "uvicorn", "pdf2md_server.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t pdf2md-server .
docker run -p 8000:8000 --gpus all pdf2md-server
```

---

## Next Steps

1. **Integration**: Connect client CLI to server
2. **Testing**: Run integration tests with `uv run pytest`
3. **Monitoring**: Set up log aggregation and monitoring
4. **Scaling**: Deploy to production GPU server

---

## Support

For issues and questions:
- GitHub Issues: https://github.com/your-org/pdf2md-cli/issues
- Documentation: [CLAUDE.md](../../CLAUDE.md)
- Constitution: [.specify/memory/constitution.md](../../.specify/memory/constitution.md)

---

**Summary**: Server is ready to run! Install dependencies with `uv sync`, start with `uv run uvicorn pdf2md_server.main:app`, and test with `curl` or the interactive API docs at `/docs`.
