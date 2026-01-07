# Research Report: Client CLI Interface

**Feature**: 002-client-cli
**Date**: 2026-01-07
**Status**: Complete

This document consolidates research findings for all technology decisions required to implement the client CLI interface.

---

## 1. Typer CLI Patterns

### Decision
Use **Typer** with synchronous command functions and multi-command structure using `typer.Typer()` app groups.

### Rationale
- **Modern & Actively Maintained**: Official FastAPI team project, excellent documentation
- **Type Hints**: Uses Python type hints for automatic CLI generation
- **Multi-Command Support**: Native support for subcommands via `typer.Typer()` app groups
- **Help Generation**: Automatic `--help` generation from docstrings
- **Async Ready**: While async support is planned, current pattern of sync commands with `asyncio.run()` bridge works well

### Alternatives Considered
- **Click**: Mature but requires more boilerplate, type hints not native
- **argparse**: Built-in but verbose, poor developer experience
- **Cyclopts**: Newer, less mature ecosystem

### Implementation Pattern

```python
# client/cli.py
import typer
from pathlib import Path
from typing import Optional

app = typer.Typer(help="PDF2md - Convert PDF files to Markdown")
config_app = typer.Typer(help="Configuration management")
app.add_typer(config_app, name="config")

@app.command()
def convert(
    pdf_file: Path = typer.Argument(..., help="PDF file to convert"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing files"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """Convert a PDF file to Markdown format."""
    # Implementation

@config_app.command("init")
def config_init(
    server_url: str = typer.Option(..., "--server-url", help="Server URL"),
    timeout: int = typer.Option(300, "--timeout", help="Timeout in seconds")
):
    """Initialize configuration file."""
    # Implementation

@config_app.command("show")
def config_show():
    """Show current configuration."""
    # Implementation

@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Configuration key"),
    value: str = typer.Argument(..., help="Configuration value")
):
    """Set configuration value."""
    # Implementation

if __name__ == "__main__":
    app()
```

### Key Findings
1. **Subcommands**: Use separate `typer.Typer()` instance for `config` commands
2. **Positional Arguments**: Use `typer.Argument(...)` for required positional args
3. **Flags**: Use `typer.Option()` with default values for optional flags
4. **Path Types**: Typer automatically validates `Path` types and checks existence
5. **Help Text**: Docstrings become `--help` text automatically

---

## 2. Async/Sync Mixing Pattern

### Decision
Use **synchronous Typer commands** as thin wrappers that bridge to async client code via `asyncio.run()`.

### Rationale
- **Separation of Concerns**: CLI handles parsing/validation; client handles async I/O
- **Testing**: Easier to test client logic independently
- **Compatibility**: Works with current Typer without external dependencies
- **Migration Path**: When Typer adds native async support, client code won't need changes
- **Clean Shutdown**: `asyncio.run()` handles event loop creation and cleanup automatically

### Alternatives Considered
- **async-typer**: Third-party package, adds dependency
- **Custom AsyncTyper**: Maintenance burden, less tested
- **All-Sync**: Can't use httpx async benefits

### Implementation Pattern

```python
import asyncio
import typer
from pathlib import Path
from .client import PDF2MDClient

@app.command()
def convert(
    pdf_file: Path = typer.Argument(..., help="PDF file to convert"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
    overwrite: bool = typer.Option(False, "--overwrite"),
    verbose: bool = typer.Option(False, "--verbose", "-v")
):
    """Convert a PDF file to Markdown format."""

    # Synchronous validation
    if not pdf_file.exists():
        typer.echo(f"Error: File not found: {pdf_file}", err=True)
        raise typer.Exit(code=3)

    # Bridge to async client
    try:
        exit_code = asyncio.run(_convert_async(
            pdf_file=pdf_file,
            output_dir=output,
            overwrite=overwrite,
            verbose=verbose
        ))
        raise typer.Exit(code=exit_code)
    except KeyboardInterrupt:
        typer.echo("\nConversion cancelled", err=True)
        raise typer.Exit(code=130)

async def _convert_async(
    pdf_file: Path,
    output_dir: Optional[Path],
    overwrite: bool,
    verbose: bool
) -> int:
    """Async conversion logic."""
    async with PDF2MDClient() as client:
        result = await client.convert_pdf(
            pdf_path=pdf_file,
            output_dir=output_dir,
            overwrite=overwrite,
            verbose=verbose
        )
        typer.echo(f"✓ Converted: {result.output_path} ({result.page_count} pages, {result.duration:.1f}s)")
        return 0
```

### Key Findings
1. **Typer Async Status**: No native support yet (planned, issue #950 with 66+ upvotes)
2. **asyncio.run()**: Built-in Python 3.7+ feature, handles event loop lifecycle
3. **Context Managers**: Use `async with` for httpx.AsyncClient to ensure cleanup
4. **KeyboardInterrupt**: Catch at Typer level for graceful Ctrl+C handling (exit code 130)
5. **Exit Codes**: Return int from async function, propagate to Typer

---

## 3. Terminal Output & Colors

### Decision
Use **Rich** for cross-platform terminal output, colors, and progress bars.

### Rationale
- **Cross-Platform**: Includes colorama for Windows support automatically
- **Modern**: 50k+ GitHub stars, active development (2025)
- **Feature-Rich**: Colors, progress bars, panels, text wrapping, terminal width detection
- **Unicode Support**: Properly handles Unicode symbols across platforms
- **Beautiful Defaults**: Professional output with minimal code

### Alternatives Considered
- **colorama**: Good for basic colors only, requires more code
- **termcolor**: Does NOT support Windows CMD.exe (deal-breaker)
- **blessed**: Too complex, steeper learning curve

### Implementation Pattern

```python
from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
import platform
import shutil

class CLIOutput:
    """Cross-platform CLI output handler."""

    THEME = Theme({
        "success": "green",
        "error": "bold red",
        "warning": "yellow",
        "info": "blue",
    })

    def __init__(self):
        # Terminal width (max 80 chars per spec SC-CLI-006)
        terminal_width = shutil.get_terminal_size(fallback=(80, 24)).columns
        self.width = min(terminal_width, 80)
        self.use_unicode = self._detect_unicode_support()
        self.console = Console(theme=self.THEME, width=self.width)

    def _detect_unicode_support(self) -> bool:
        """Detect if terminal supports Unicode symbols."""
        if platform.system() != "Windows":
            return True  # Unix systems

        # Windows: Check for modern terminal
        if os.environ.get("WT_SESSION"):  # Windows Terminal
            return True
        if os.environ.get("TERM_PROGRAM") == "vscode":  # VS Code
            return True
        if "powershell" in os.environ.get("PSModulePath", ""):  # PowerShell
            return True
        return False  # Legacy cmd.exe

    def _get_symbol(self, symbol_type: str) -> str:
        """Get Unicode or ASCII symbol."""
        if not self.use_unicode:
            return {
                "success": "[OK]",
                "error": "[FAIL]",
                "warning": "[WARN]",
                "info": "[INFO]",
            }.get(symbol_type, "?")
        return {
            "success": "✓",
            "error": "✗",
            "warning": "⚠",
            "info": "→",
        }.get(symbol_type, "?")

    def success(self, message: str) -> None:
        """Print success message."""
        symbol = self._get_symbol("success")
        self.console.print(f"{symbol} {message}", style="success")

    def error(self, message: str, details: Optional[str] = None) -> None:
        """Print error message."""
        symbol = self._get_symbol("error")
        if details:
            self.console.print(Panel(
                details,
                title=f"[error]{symbol} {message}[/error]",
                border_style="error"
            ))
        else:
            self.console.print(f"{symbol} {message}", style="error")
```

### Key Findings
1. **Symbol Fallback**: Use Unicode on modern terminals, ASCII on legacy cmd.exe
2. **Terminal Width**: Detect with `shutil.get_terminal_size()`, limit to 80 chars
3. **Color Scheme**: Green (success), bold red (error), yellow (warning)
4. **Panels**: Use `Panel` for multi-line errors/details
5. **Rich Progress**: Built-in progress bar support, better than tqdm alone

---

## 4. Error Handling & Display

### Decision
Create custom exception hierarchy with exit codes, hints, and context. Use structured error messages with troubleshooting sections.

### Rationale
- **Clear Separation**: Base exception for all app errors vs system errors
- **Exit Codes**: Embed exit codes in exceptions for correct shell propagation
- **Actionable Hints**: Include troubleshooting steps in error messages
- **Verbose Mode**: Stack traces only in verbose mode
- **Consistent Format**: All errors follow same structure

### Alternatives Considered
- **Generic Exceptions**: Lose specificity, harder to handle
- **Exit Codes Only**: No context or hints for users
- **Silent Failures**: Poor UX, users don't know what went wrong

### Implementation Pattern

```python
# client/exceptions.py
from typing import Optional, List, Dict, Any

class PDF2MDError(Exception):
    """Base exception for all PDF2MD-CLI errors."""

    def __init__(
        self,
        message: str,
        exit_code: int = 1,
        hints: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.exit_code = exit_code
        self.hints = hints or []
        self.context = context or {}
        super().__init__(self.message)

class NetworkError(PDF2MDError):
    """Network-related errors (exit code 2)."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, exit_code=2, **kwargs)

class ValidationError(PDF2MDError):
    """Input validation errors (exit code 3)."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, exit_code=3, **kwargs)

class ConversionError(PDF2MDError):
    """PDF conversion errors (exit code 4)."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, exit_code=4, **kwargs)

class ConfigError(PDF2MDError):
    """Configuration errors (exit code 5)."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, exit_code=5, **kwargs)

# Specific exceptions
class ConnectionError(NetworkError):
    def __init__(self, server_url: str):
        super().__init__(
            f"Cannot connect to server at {server_url}",
            hints=[
                "Check if the server is running on the remote machine",
                "Verify the server URL in ~/.pdf2md/config.json",
                "Test network connectivity: ping <server-ip>",
            ],
            context={"server_url": server_url}
        )
```

### Exit Code Convention

| Code | Type | Usage |
|------|------|-------|
| 0 | Success | Conversion completed successfully |
| 1 | Generic Error | Undefined failures |
| 2 | Network Error | Connection, timeout, HTTP errors |
| 3 | Validation Error | File not found, invalid input |
| 4 | Conversion Error | Server-side conversion failure |
| 5 | Configuration Error | Invalid/missing config |
| 130 | SIGINT | User cancelled (Ctrl+C) |

### Key Findings
1. **Exception Hierarchy**: Base `PDF2MDError` with semantic subclasses
2. **Hints**: Provide actionable troubleshooting steps
3. **Context**: Include debugging info (server_url, file_path, etc.)
4. **Exit Codes**: POSIX convention (0-125 available for apps, avoid 126-165, 255)
5. **Verbose Mode**: Show stack traces only when `--verbose` flag is set

---

## 5. Configuration File Management

### Decision
Use **Pydantic Settings** (v2.0+) for type-safe configuration with validation, environment variable support, and graceful fallback.

### Rationale
- **Type Validation**: Automatic type checking and coercion
- **Environment Variables**: Built-in `env_prefix` support
- **Clean Errors**: Validation errors are clear and actionable
- **IDE Support**: Autocompletion and type checking
- **Modern Standard**: Used by FastAPI, widely adopted

### Alternatives Considered
- **JSON + Manual Validation**: More code, error-prone
- **ConfigParser**: INI format, less modern
- **TOML**: Good but Pydantic has better ecosystem

### Implementation Pattern

```python
# client/config.py
from pathlib import Path
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    """Configuration model for PDF2md CLI."""

    # Server settings
    server_url: str = Field(
        default="http://localhost:8000",
        description="URL of the PDF conversion server"
    )

    # Request settings
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

    # Output settings
    output_dir: Optional[Path] = Field(
        default=None,
        description="Custom output directory"
    )

    overwrite: bool = Field(
        default=False,
        description="Overwrite existing Markdown files"
    )

    model_config = SettingsConfigDict(
        env_prefix="PDF2MD_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("server_url")
    @classmethod
    def validate_server_url(cls, v: str) -> str:
        """Validate server URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("server_url must start with http:// or https://")
        return v.rstrip("/")
```

### Config Hierarchy
**Priority**: CLI flags > Environment variables > Config file > Defaults

```python
class ConfigManager:
    """Manages loading and saving configuration."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.home() / ".pdf2md" / "config.json"
        self._config: Optional[Config] = None

    def load_config(self) -> Config:
        """Load with fallback logic."""
        # Pydantic loads env vars automatically
        config = Config()

        # Try to load config file
        if self.config_path.exists():
            try:
                import json
                with open(self.config_path) as f:
                    file_config = json.load(f)
                # File values override defaults (env vars still win)
                config = Config(**{**config.model_dump(), **file_config})
            except json.JSONDecodeError as e:
                self._handle_corrupted_config(e)
        return config

    def _handle_corrupted_config(self, error: json.JSONDecodeError):
        """Backup corrupted config and notify user."""
        from datetime import datetime
        import shutil

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.config_path.with_suffix(f".corrupted.{timestamp}.json")
        shutil.copy2(self.config_path, backup_path)

        print(f"Warning: Corrupted config backed up to {backup_path}")
        print(f"Using default configuration. Run 'pdf2md config init' to recreate.")
```

### Platform-Aware Config Directory

Use `platformdirs` for cross-platform config locations:

```python
import platformdirs
from pathlib import Path

class ConfigPaths:
    """Platform-aware configuration paths."""

    APP_NAME = "pdf2md"
    APP_AUTHOR = "pdf2md"

    @classmethod
    def get_config_dir(cls) -> Path:
        """Get platform-specific config directory."""
        return Path(platformdirs.user_config_dir(
            appname=cls.APP_NAME,
            appauthor=cls.APP_AUTHOR,
            roaming=True
        ))

    @classmethod
    def get_config_file(cls) -> Path:
        """Get full path to config file."""
        return cls.get_config_dir() / "config.json"
```

**Platform Locations**:
- **Linux**: `~/.config/pdf2md/config.json`
- **macOS**: `~/Library/Application Support/pdf2md/config.json`
- **Windows**: `C:\Users\user\AppData\Roaming\pdf2md\config.json`

### Security
Set file permissions to `chmod 600` (owner read/write only):

```python
import os
import stat

def set_secure_permissions(path: Path) -> bool:
    """Set secure permissions on config file."""
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)  # 0o600
        return True
    except Exception as e:
        print(f"Warning: Could not set permissions: {e}")
        print(f"Please run: chmod 600 {path}")
        return False
```

### Key Findings
1. **Pydantic Settings**: Best choice for type-safe, validated config
2. **Graceful Fallback**: Backup corrupted configs, use defaults
3. **Config Hierarchy**: CLI > env vars > file > defaults (Pydantic handles this)
4. **platformdirs**: Use for cross-platform config directories
5. **Secure Permissions**: chmod 600 for config files

---

## 6. Progress Bars with httpx

### Decision
Use **tqdm** with manual progress updates for httpx streaming uploads/downloads. For Rich integration, use Rich's built-in progress bars.

### Rationale
- **tqdm**: Standard for progress bars, works with async
- **Manual Updates**: Required for httpx streaming (no native progress support)
- **Rich Progress**: Alternative with better aesthetics, Rich already a dependency

### Alternatives Considered
- **tqdm.asyncio**: For concurrent tasks, not needed for single file
- **Rich Progress**: Better aesthetics, Rich already included
- **No Progress**: Poor UX for large files

### Implementation Pattern

**Option A: tqdm with Manual Updates**

```python
import httpx
from tqdm import tqdm
from pathlib import Path

async def upload_with_progress(
    client: httpx.AsyncClient,
    url: str,
    file_path: Path,
    chunk_size: int = 8192
) -> httpx.Response:
    """Upload file with tqdm progress bar."""

    file_size = file_path.stat().st_size

    # Open file and create progress bar
    with open(file_path, "rb") as f:
        with tqdm(
            total=file_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc="Uploading"
        ) as progress:

            # Prepare multipart upload
            files = {"file": (file_path.name, f, "application/pdf")}

            # Upload (httpx doesn't support upload progress natively)
            # We read the entire file and update progress after
            response = await client.post(url, files=files)
            response.raise_for_status()

            # Update progress (complete)
            progress.update(file_size)

    return response
```

**Option B: Rich Progress (Recommended)**

```python
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn

async def download_with_progress(
    client: httpx.AsyncClient,
    url: str,
    destination: Path
) -> None:
    """Download file with Rich progress bar."""

    console = Console()

    with console.status("[bold blue]Connecting to server...", spinner="dots"):
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", 0))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        console=console,
    ) as progress:

        task = progress.add_task("Downloading", total=total_size)

        with open(destination, "wb") as f:
            async for chunk in response.aiter_bytes(chunk_size=8192):
                f.write(chunk)
                progress.update(task, advance=len(chunk))
```

### Upload Progress Challenge

**httpx doesn't natively support upload progress** because it reads the entire file object. Workaround:

```python
class ProgressFile:
    """File wrapper that reports progress to tqdm."""

    def __init__(self, file_path: Path, progress: tqdm):
        self.file_path = file_path
        self.progress = progress
        self.file = open(file_path, "rb")

    def read(self, size=-1):
        chunk = self.file.read(size)
        if chunk:
            self.progress.update(len(chunk))
        return chunk

    def close(self):
        self.file.close()

# Usage
with tqdm(total=file_size, desc="Uploading") as progress:
    progress_file = ProgressFile(pdf_path, progress)
    files = {"file": (pdf_path.name, progress_file, "application/pdf")}
    response = await client.post(url, files=files)
```

### Key Findings
1. **Rich Progress**: Best choice, Rich already a dependency for colors
2. **Upload Progress**: Requires custom file wrapper class
3. **Download Progress**: Native support via `aiter_bytes()`
4. **Chunk Size**: 8192 bytes is good balance (configurable)
5. **Smooth Updates**: Rich handles terminal refresh better than tqdm

---

## 7. Dependencies Summary

### Required Dependencies (pyproject.toml)

```toml
[project]
name = "pdf2md-client"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.9.0",           # CLI framework
    "httpx>=0.25.0",          # Async HTTP client
    "pydantic>=2.0.0",        # Data validation
    "pydantic-settings>=2.0.0", # Config management
    "rich>=14.0.0",           # Terminal output, colors, progress
    "platformdirs>=4.0.0",    # Cross-platform paths
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]
```

### Dependency Rationale

| Package | Purpose | Why |
|---------|---------|-----|
| typer | CLI framework | Type hints, modern, official FastAPI team |
| httpx | HTTP client | Async support, HTTP/2, modern |
| pydantic | Validation | Type-safe, clean errors, ecosystem |
| pydantic-settings | Config | Environment variables, validation |
| rich | Output | Colors, progress, cross-platform |
| platformdirs | Paths | Cross-platform config locations |

---

## 8. Testing Strategy

### Unit Tests
- Mock httpx.AsyncClient for network calls
- Test config loading/saving with temp files
- Test validation logic

### Integration Tests
- Run test server (httpx MockTransport)
- Test full conversion flow
- Test error scenarios

### CLI Testing
```python
from typer.testing import CliRunner
from client.cli import app

runner = CliRunner()

def test_convert_success():
    result = runner.invoke(app, ["test.pdf"])
    assert result.exit_code == 0
    assert "✓ Converted:" in result.stdout

def test_convert_file_not_found():
    result = runner.invoke(app, ["/nonexistent/file.pdf"])
    assert result.exit_code == 3
    assert "Error: File not found" in result.stdout
```

---

## 9. Project Structure

```
client/
├── src/
│   └── pdf2md_client/
│       ├── __init__.py
│       ├── cli.py              # Typer CLI commands
│       ├── config.py           # Pydantic Config model
│       ├── config_manager.py   # Config load/save logic
│       ├── client.py           # HTTP client (async)
│       ├── file_handler.py     # File validation
│       ├── exceptions.py       # Exception hierarchy
│       └── output.py           # CLI output (Rich wrapper)
│
├── tests/
│   ├── unit/
│   │   ├── test_cli.py
│   │   ├── test_config.py
│   │   ├── test_client.py
│   │   └── test_file_handler.py
│   └── integration/
│       └── test_conversion_flow.py
│
├── pyproject.toml
└── README.md
```

---

## 10. Open Questions Resolved

All "NEEDS CLARIFICATION" items from plan.md have been resolved:

| Question | Decision |
|----------|----------|
| Typer multi-command structure | Use `typer.Typer()` app groups |
| Async/sync mixing | `asyncio.run()` bridge pattern |
| Terminal colors | Rich (cross-platform) |
| Error handling | Custom exception hierarchy |
| Config management | Pydantic Settings |
| Progress bars | Rich Progress with manual updates |

---

## 11. Next Steps

**Phase 1: Design & Contracts**
1. Generate `data-model.md` from entities in spec
2. Generate `quickstart.md` with command examples
3. Create agent context update

**Phase 2: Task Generation**
1. Run `/speckit.tasks` to generate implementation tasks
2. Review and prioritize tasks
3. Begin implementation
