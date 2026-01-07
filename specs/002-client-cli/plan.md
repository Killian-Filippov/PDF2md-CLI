# Implementation Plan: Client CLI Interface

**Branch**: `002-client-cli` | **Date**: 2026-01-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-client-cli/spec.md`

## Summary

Implement the client-side CLI interface for PDF2md-CLI that enables users to convert PDF files to Markdown via a remote GPU-enabled server. The CLI provides:
- Main `pdf2md <file.pdf>` conversion command with progress indicators
- Configuration management (`config init/show/set`) for server connectivity
- User-friendly output with color-coding, progress bars, and clear error messages
- Cross-platform compatibility (Linux, macOS, Windows)

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**:
- `typer` - CLI framework with type hints
- `httpx` - Async HTTP client for file upload/download
- `pydantic` - Configuration validation and settings management
- `rich` - Terminal colors, progress bars, and Unicode support

**Storage**: JSON configuration file at `~/.pdf2md/config.json`
**Testing**: `pytest` with `pytest-asyncio` for async client tests
**Target Platform**: Linux, macOS, Windows (CLI tool)
**Project Type**: Single project (client component of distributed system)
**Performance Goals**:
- Config commands: <2 seconds
- Progress bar updates: Smooth, no flicker
- File upload/download: Stream with chunk_size=8192

**Constraints**:
- Terminal width: Messages fit within 80 characters
- Color support: Works across bash, zsh, PowerShell, cmd.exe
- UTF-8 encoding: Required for symbols (✓, ✗)

**Scale/Scope**:
- ~5-7 Python modules in `client/` directory
- ~30-40 functional requirements (FR-CLI-001 through FR-CLI-032)
- Single file conversion only (no batch processing in MVP)

## Architecture Principles Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Status**: Principles validated against architecture design.

**Core Principles**:
- **SOLID**: Single responsibility - CLI only handles user interaction, not business logic
- **DRY**: Shared utilities in common modules, no duplicated code
- **YAGNI**: MVP features only (no batch processing, no daemon mode)
- **Robustness**: Explicit error handling, clear user messages, graceful cleanup

## Project Structure

### Documentation (this feature)

```text
specs/002-client-cli/
├── spec.md              # Feature specification (existing)
├── plan.md              # This file
├── research.md          # Phase 0 output (typer patterns, error handling)
├── data-model.md        # Phase 1 output (ServerConfig, ConversionOptions)
├── quickstart.md        # Phase 1 output (dev setup, usage examples)
├── contracts/           # Phase 1 output (N/A - no API contracts for CLI)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
client/                  # Client component
├── src/
│   └── pdf2md_client/
│       ├── __init__.py
│       ├── cli.py              # Typer CLI commands (convert, config)
│       ├── config.py           # Config load/save/validation
│       ├── client.py           # HTTP client for upload/download
│       ├── file_handler.py     # File validation, conflict checking
│       ├── exceptions.py       # Custom exception hierarchy
│       └── output.py           # CLI output wrapper using Rich
│
├── tests/
│   ├── unit/
│   │   ├── test_cli.py         # CLI command tests
│   │   ├── test_config.py      # Config management tests
│   │   ├── test_client.py      # HTTP client tests (mocked)
│   │   └── test_file_handler.py # File validation tests
│   ├── integration/
│   │   └── test_conversion_flow.py # End-to-end conversion (with test server)
│   └── fixtures/
│       └── test_pdfs/          # Sample PDF files for testing
│
├── pyproject.toml             # Client package configuration
└── README.md                  # Client-specific documentation
```

**Structure Decision**: Single `client/` directory with separate `src/pdf2md_client/` package following modern Python packaging standards. Tests co-located with client code. Configuration file in user's home directory (`~/.pdf2md/config.json`).

## Complexity Tracking

> **No violations expected** - CLI interface is a straightforward command-line tool with clear separation of concerns.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

## Phase 0: Research & Technology Decisions

### Research Tasks

1. **Typer CLI Patterns** (NEEDS CLARIFICATION)
   - Research: Best practices for multi-command CLI (main command + `config` subcommand)
   - Research: How to structure `config init/show/set` as typer subcommands
   - Research: Handling positional arguments vs flags in typer

2. **Async/Sync Mixing** (NEEDS CLARIFICATION)
   - Research: Can typer commands be `async`? How does this work?
   - Research: Best pattern: sync CLI wrapper calling async client code?
   - Research: How to handle progress bars with async operations

3. **Terminal Output & Colors** (NEEDS CLARIFICATION)
   - Research: Cross-platform color library (rich? colorama? termcolor?)
   - Research: Unicode symbol compatibility (✓, ✗) on Windows
   - Research: Terminal width detection for message wrapping

4. **Error Display Patterns** (NEEDS CLARIFICATION)
   - Research: Best practices for structured error messages in CLI tools
   - Research: How to implement "troubleshooting" hints (from architecture spec)
   - Research: Exit code conventions for CLI tools

5. **Configuration File Best Practices** (NEEDS CLARIFICATION)
   - Research: JSON validation on load (pydantic BaseModel?)
   - Research: Handling corrupted config files
   - Research: Config hierarchy: CLI flags > env vars > config file > defaults

6. **Progress Bar with httpx** (NEEDS CLARIFICATION)
   - Research: How to integrate tqdm with httpx streaming uploads
   - Research: How to integrate tqdm with httpx streaming downloads
   - Research: Handling progress updates during async operations

### Output Target
- **File**: `/Users/kexinwan/code/PDF2md-CLI/specs/002-client-cli/research.md`
- **Format**: Decision/Rationale/Alternatives for each research task

## Phase 1: Design & Contracts

### Design Tasks

1. **Data Model Design** → `data-model.md`
   - Extract entities from spec: CLICommand, ConfigCommand, ConversionOptions
   - Define Pydantic models: ServerConfig (with validation)
   - Define configuration schema (JSON structure)
   - Document state transitions (conversion: pending → uploading → converting → downloading → complete)

2. **CLI Command Structure** → `quickstart.md`
   - Define command tree: `pdf2md [convert]`, `pdf2md config init|show|set`
   - Document all flags: `--output`, `--overwrite`, `--verbose`, `--server-url`, `--timeout`
   - Define exit codes (0-5) with mapping to error types
   - Example usage for all commands

3. **Internal APIs** (no external contracts - client only)
   - CLI → Config module interface
   - CLI → HTTP client interface
   - CLI → File handler interface
   - Error handling hierarchy

### Output Targets
- **File**: `/Users/kexinwan/code/PDF2md-CLI/specs/002-client-cli/data-model.md`
- **File**: `/Users/kexinwan/code/PDF2md-CLI/specs/002-client-cli/quickstart.md`
- **Directory**: `/Users/kexinwan/code/PDF2md-CLI/specs/002-client-cli/contracts/` (may be empty)

## Phase 2: Task Generation

*Executed by `/speckit.tasks` command (NOT part of this plan)*

**Input**: `spec.md` + `research.md` + `data-model.md` + `quickstart.md`
**Output**: `tasks.md` with dependency-ordered implementation tasks
