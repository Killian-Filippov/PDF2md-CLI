# PDF2md Client

Client CLI for PDF2md - Convert PDF files to Markdown using a remote GPU-enabled server.

## Installation

### Prerequisites

- **uv** package manager (required - see [Constitution](../../.specify/memory/constitution.md))
- Python 3.11+

### Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip (not recommended for production)
pip install uv
```

### From Source

```bash
# Clone repository
git clone https://github.com/your-org/pdf2md-cli.git
cd pdf2md-cli/client

# Install dependencies and create virtual environment
uv sync

# Activate virtual environment
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### With uv (Recommended)

```bash
# Add to project
uv add pdf2md-client
```

## Quick Start

### 1. Initialize Configuration

```bash
pdf2md config init --server-url http://your-server:8000
```

### 2. Convert a PDF

```bash
pdf2md convert document.pdf
```

The converted Markdown file will be saved in the same directory as the PDF.

### 3. Specify Custom Output Location

```bash
pdf2md convert document.pdf --output ~/converted/
```

## Configuration

Configuration is stored in `~/.pdf2md/config.json` (platform-specific location).

### Environment Variables

You can override configuration using environment variables:

- `PDF2MD_SERVER_URL`: Server URL
- `PDF2MD_TIMEOUT`: Request timeout (seconds)
- `PDF2MD_CHUNK_SIZE`: Upload chunk size (bytes)
- `PDF2MD_MAX_RETRIES`: Maximum retry attempts
- `PDF2MD_VERIFY_SSL`: Verify SSL certificates (true/false)
- `PDF2MD_OUTPUT_DIR`: Default output directory
- `PDF2MD_OVERWRITE`: Overwrite existing files (true/false)
- `PDF2MD_VERBOSE`: Enable verbose logging (true/false)

**Priority**: CLI flags > Environment variables > Config file > Defaults

## Commands

### Main Command: `pdf2md convert`

```bash
pdf2md convert [OPTIONS] PDF_FILE
```

**Options**:
- `--output`, `-o`: Custom output directory
- `--overwrite`: Overwrite existing files without prompting
- `--verbose`, `-v`: Enable verbose logging
- `--server`, `-s`: Override server URL
- `--timeout`, `-t`: Override request timeout
- `--help`: Show help message

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
- `--server-url`: Server URL (default: http://localhost:8000)
- `--timeout`: Request timeout (default: 300)

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

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Generic Error |
| 2 | Network Error |
| 3 | Validation Error |
| 4 | Conversion Error |
| 5 | Configuration Error |
| 130 | User Cancelled (Ctrl+C) |

## Development

### Adding Dependencies

```bash
# Add runtime dependency
uv add typer

# Add dev dependency
uv add --dev pytest

# Remove dependency
uv remove typer
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test
uv run pytest tests/unit/test_config.py
```

### Code Quality

```bash
# Format code
uv run ruff format src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type checking
uv run mypy src/

# Run commands without activating venv
uv run <command>
```

## Troubleshooting

### "Command not found: pdf2md"

**Cause**: CLI not installed or virtual environment not activated

**Solution**:
```bash
# Ensure dependencies are installed
uv sync

# Activate virtual environment
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Or use uv run without activation
uv run pdf2md --help
```

### "Network Error: Cannot connect to server"

**Cause**: Server unreachable or wrong URL

**Solution**:
```bash
# Check server status
curl http://your-server:8000/health

# Update configuration
pdf2md config set server_url http://correct-url:8000
```

### "Validation Error: File not found"

**Cause**: PDF file path is incorrect

**Solution**:
```bash
# Use absolute path
pdf2md convert /absolute/path/to/document.pdf

# Check file exists
ls -la ~/Documents/report.pdf
```

## License

MIT License - see LICENSE file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/your-org/pdf2md-cli/issues)
- **Documentation**: [Project Docs](https://github.com/your-org/pdf2md-cli#readme)
