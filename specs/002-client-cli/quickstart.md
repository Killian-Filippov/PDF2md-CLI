# Quickstart Guide: Client CLI Interface

**Feature**: 002-client-cli
**Version**: 1.0.0
**Date**: 2026-01-07

This guide provides setup instructions and usage examples for the PDF2md CLI client.

---

## Installation

### Prerequisites

- **Python**: 3.11 or higher
- **Operating System**: Linux, macOS, or Windows
- **Network**: Access to PDF2md server on local network

### Install from Source

```bash
# Clone repository
git clone https://github.com/your-org/pdf2md-cli.git
cd pdf2md-cli/client

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .
```

### Install Dependencies

```bash
# Core dependencies
pip install typer httpx pydantic pydantic-settings rich platformdirs

# Development dependencies
pip install pytest pytest-asyncio pytest-cov ruff mypy
```

### Verify Installation

```bash
$ pdf2md --version
PDF2md CLI v1.0.0

$ pdf2md --help
Usage: pdf2md [OPTIONS] COMMAND [ARGS]...
  PDF2md - Convert PDF files to Markdown using a remote GPU server

Options:
  --version        Show version and exit
  --help           Show this message and exit

Commands:
  convert       Convert a PDF file to Markdown
  config        Configuration management commands
  --help        Show this message and exit
```

---

## Configuration

### Initialize Configuration

Run the `config init` command to create a default configuration file:

```bash
$ pdf2md config init --server-url http://192.168.1.100:8000
Configuration created at /home/user/.pdf2md/config.json
```

**Configuration File Location**:
- **Linux**: `~/.config/pdf2md/config.json`
- **macOS**: `~/Library/Application Support/pdf2md/config.json`
- **Windows**: `C:\Users\<username>\AppData\Roaming\pdf2md\config.json`

### Configuration Options

```bash
# Set timeout to 600 seconds
$ pdf2md config set timeout 600

# Set custom output directory
$ pdf2md config set output_dir /homeuser/Documents/output

# Enable overwrite mode
$ pdf2md config set overwrite true
```

### View Configuration

```bash
$ pdf2md config show
Current Configuration:
────────────────────────────
server_url:  http://192.168.1.100:8000
timeout:     300
chunk_size:  8192
max_retries: 3
verify_ssl:  true
output_dir:  /home/user/Documents/output
overwrite:   false
```

### Environment Variables

You can also override configuration using environment variables:

```bash
# Set server URL via environment
export PDF2MD_SERVER_URL=http://192.168.1.100:8000
export PDF2MD_TIMEOUT=600
export PDF2MD_VERBOSE=true

# Run conversion
pdf2md document.pdf
```

**Available Environment Variables**:
- `PDF2MD_SERVER_URL`: Server URL
- `PDF2MD_TIMEOUT`: Request timeout (seconds)
- `PDF2MD_CHUNK_SIZE`: Upload chunk size (bytes)
- `PDF2MD_MAX_RETRIES`: Maximum retry attempts
- `PDF2MD_VERIFY_SSL`: Verify SSL certificates (true/false)
- `PDF2MD_OUTPUT_DIR`: Default output directory
- `PDF2MD_OVERWRITE`: Overwrite existing files (true/false)
- `PDF2MD_VERBOSE`: Enable verbose logging (true/false)

**Priority**: CLI flags > Environment variables > Config file > Defaults

---

## Basic Usage

### Convert a PDF File

The simplest usage is to provide the PDF file path:

```bash
$ pdf2md ~/Documents/report.pdf
✓ Uploading report.pdf (5.2 MB)...
✓ Converting (42 pages)...
✓ Downloading report.md...
✓ Converted: report.md (42 pages, 12.3s)
```

**Output**: Markdown file is saved in the same directory as the PDF (`~/Documents/report.md`).

### Specify Custom Output Location

Use the `--output` flag to save to a specific directory:

```bash
$ pdf2md ~/Documents/report.pdf --output ~/Converted/
✓ Converted: ~/Converted/report.md (42 pages, 12.3s)
```

### Overwrite Existing Files

Use `--overwrite` to skip the confirmation prompt:

```bash
$ pdf2md report.pdf --overwrite
✓ Converted: report.md (42 pages, 12.3s)
```

Without `--overwrite`, the CLI will prompt:

```bash
$ pdf2md report.pdf
⚠ File exists: report.md
Overwrite? [y/N]: y
✓ Converting...
```

### Verbose Mode

Use `--verbose` to see detailed debugging information:

```bash
$ pdf2md report.pdf --verbose
[INFO] Loading config from /home/user/.pdf2md/config.json
[INFO] Server URL: http://192.168.1.100:8000
[INFO] Timeout: 300s
[DEBUG] Validating file: report.pdf
[DEBUG] File size: 5242880 bytes
[DEBUG] Connecting to server...
[INFO] ✓ Uploading report.pdf (5.2 MB)...
[INFO] ✓ Converting (42 pages)...
[INFO] ✓ Downloading report.md...
[INFO] ✓ Converted: report.md (42 pages, 12.3s)
```

---

## Command Reference

### Main Command: `pdf2md convert`

```bash
pdf2md convert [OPTIONS] PDF_FILE
```

**Arguments**:
| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `PDF_FILE` | Path | Yes | Path to PDF file to convert |

**Options**:
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--output`, `-o` | Path | Same as PDF | Custom output directory |
| `--overwrite` | Flag | False | Overwrite existing files without prompting |
| `--verbose`, `-v` | Flag | False | Enable verbose logging |
| `--server`, `-s` | URL | From config | Override server URL |
| `--timeout`, `-t` | Seconds | From config | Override request timeout |
| `--help` | - | - | Show help message |

**Examples**:

```bash
# Basic conversion
pdf2md convert document.pdf

# Custom output directory
pdf2md convert document.pdf --output ~/output/

# Verbose mode with custom server
pdf2md convert document.pdf --verbose --server http://gpu-server:8000

# Long timeout for large files
pdf2md convert large.pdf --timeout 600

# Overwrite existing file
pdf2md convert document.pdf --overwrite
```

### Config Commands

#### `config init`

Initialize configuration file:

```bash
pdf2md config init [OPTIONS]
```

**Options**:
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--server-url` | URL | http://localhost:8000 | Server URL |
| `--timeout` | Seconds | 300 | Request timeout |

**Example**:
```bash
pdf2md config init --server-url http://192.168.1.100:8000 --timeout 600
```

#### `config show`

Display current configuration:

```bash
pdf2md config show
```

#### `config set`

Set a configuration value:

```bash
pdf2md config set KEY VALUE
```

**Examples**:
```bash
pdf2md config set server_url http://new-server:8000
pdf2md config set timeout 600
pdf2md config set overwrite true
```

---

## Exit Codes

The CLI returns the following exit codes:

| Code | Meaning | Example Usage |
|------|---------|---------------|
| 0 | Success | `if pdf2md file.pdf; then echo "Success"; fi` |
| 1 | Generic Error | Unexpected error |
| 2 | Network Error | Server unreachable, timeout |
| 3 | Validation Error | File not found, invalid format |
| 4 | Conversion Error | Server-side conversion failed |
| 5 | Configuration Error | Invalid config file |
| 130 | User Cancelled | Ctrl+C pressed |

**Shell Script Example**:
```bash
#!/bin/bash
pdf2md document.pdf
case $? in
    0) echo "✓ Success" ;;
    2) echo "✗ Network error - check server" ;;
    3) echo "✗ Invalid file - check path" ;;
    4) echo "✗ Conversion failed - check PDF" ;;
    *) echo "✗ Unknown error" ;;
esac
```

---

## Common Workflows

### Workflow 1: First-Time Setup

```bash
# 1. Install CLI
pip install pdf2md-client

# 2. Initialize configuration
pdf2md config init --server-url http://gpu-server:8000

# 3. Verify server connectivity
pdf2md --help  # Should show help without errors

# 4. Convert test PDF
pdf2md test.pdf
```

### Workflow 2: Batch Conversion (Bash Script)

```bash
#!/bin/bash
# Convert all PDFs in a directory

for pdf in *.pdf; do
    echo "Converting $pdf..."
    pdf2md "$pdf" --output converted/ --overwrite
    if [ $? -eq 0 ]; then
        echo "✓ $pdf converted successfully"
    else
        echo "✗ $pdf failed (exit code $?)"
    fi
done
```

### Workflow 3: Server Migration

```bash
# Update server URL for all conversions
export PDF2MD_SERVER_URL=http://new-server:8000

# Convert with new server
pdf2md document.pdf

# Or update permanently
pdf2md config set server_url http://new-server:8000
```

### Workflow 4: Debugging Connection Issues

```bash
# Enable verbose logging
pdf2md document.pdf --verbose

# Check configuration
pdf2md config show

# Test server connectivity
curl http://192.168.1.100:8000/health

# Override with different server
pdf2md document.pdf --server http://localhost:8000
```

---

## Error Messages

### Network Error (Exit Code 2)

```
✗ Network Error: Cannot connect to server

The CLI could not reach the server at http://192.168.1.100:8000

Troubleshooting:
  1. Check if the server is running on the remote machine
  2. Verify the server URL in ~/.pdf2md/config.json
  3. Test network connectivity: ping 192.168.1.100
  4. Check firewall settings on both machines
```

**Solution**: Ensure server is running and accessible:
```bash
# On server machine
curl http://localhost:8000/health

# From client machine
ping 192.168.1.100
pdf2md config show  # Verify server URL
```

### Validation Error (Exit Code 3)

```
✗ Validation Error: File not found

The specified PDF file does not exist or is not readable.

File: ~/missing.pdf

Troubleshooting:
  1. Check if the file path is correct
  2. Use absolute paths if relative paths don't work
  3. Ensure the file extension is .pdf
```

**Solution**: Verify file exists and is readable:
```bash
ls -la ~/Documents/report.pdf
file ~/Documents/report.pdf
```

### Conversion Error (Exit Code 4)

```
✗ Conversion Error: PDF processing failed

The server failed to convert the PDF file.

File: document.pdf (15.2 MB)
Error: CUDA out of memory

Troubleshooting:
  1. The PDF might be too large or contain many high-res images
  2. Try converting a smaller file first
  3. Check server logs: ssh server 'tail -f /var/log/pdf2md.log'
  4. Ensure GPU is available on the server
```

**Solution**: Check server resources and logs:
```bash
# On server
nvidia-smi  # Check GPU status
docker logs pdf2md-server  # Check server logs
```

---

## Development

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=client --cov-report=html

# Run specific test
pytest tests/unit/test_config.py
```

### Code Quality

```bash
# Format code
ruff format client/

# Lint code
ruff check client/

# Type checking
mypy client/
```

### Local Development

```bash
# Install in editable mode
pip install -e .

# Run CLI directly
python -m pdf2md_client.cli convert test.pdf

# Or use installed command
pdf2md convert test.pdf
```

---

## Troubleshooting

### Issue: "Command not found: pdf2md"

**Cause**: CLI not installed or not in PATH

**Solution**:
```bash
# Reinstall with pip
pip install -e .

# Or add to PATH (if using virtualenv)
export PATH="$PATH:$(pwd)/.venv/bin"
```

### Issue: "Unicode symbols display incorrectly"

**Cause**: Legacy terminal (Windows cmd.exe)

**Solution**: Use modern terminal or ASCII fallback:
```bash
# On Windows, use PowerShell or Windows Terminal
# Or use VS Code integrated terminal

# Symbols will automatically fallback to ASCII on legacy terminals
# Output: [OK] instead of ✓
```

### Issue: "Progress bars flicker"

**Cause**: Terminal not compatible with Rich progress bars

**Solution**: Use `--verbose` flag to disable progress bars:
```bash
pdf2md document.pdf --verbose
```

### Issue: "Config file corrupted"

**Cause**: Invalid JSON in config file

**Solution**: Reinitialize config:
```bash
# Corrupted file will be backed up automatically
pdf2md config init --server-url http://server:8000
```

---

## FAQ

**Q: Can I convert multiple PDFs at once?**

A: Not directly in the current version. Use a shell script:
```bash
for f in *.pdf; do pdf2md "$f" --overwrite; done
```

**Q: How do I cancel a conversion?**

A: Press `Ctrl+C`. The CLI will exit cleanly with code 130.

**Q: Can I use HTTPS?**

A: Yes. Set `verify_ssl: false` in config if using self-signed certificates:
```bash
pdf2md config set verify_ssl false
pdf2md convert document.pdf --server https://server:8000
```

**Q: What's the maximum file size?**

A: 500MB per the architecture specification. Larger files will be rejected with a validation error.

**Q: Where are temporary files stored?**

A: The client doesn't store temporary files. The server stores uploads in `/tmp/pdf2md/`.

**Q: How do I check server status?**

A: Use the health endpoint:
```bash
curl http://server:8000/health
```

---

## Next Steps

1. **Server Setup**: See [Server Quickstart](../003-server-api/quickstart.md)
2. **API Documentation**: See [API Spec](../003-server-api/spec.md)
3. **Troubleshooting**: See [Architecture Design](../001-architecture-design/architecture-design.md)
4. **Contributing**: See [CONTRIBUTING.md](../../CONTRIBUTING.md)

---

## Support

- **Issues**: [GitHub Issues](https://github.com/your-org/pdf2md-cli/issues)
- **Documentation**: [Project Docs](https://github.com/your-org/pdf2md-cli#readme)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/pdf2md-cli/discussions)
