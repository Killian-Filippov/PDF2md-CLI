# PDF2md-CLI Project Constitution

**Version**: 1.0.0
**Ratified**: 2026-01-07
**Last Amended**: 2026-01-07

## Core Principles

### I. Package Management with uv (NON-NEGOTIABLE)

**Principle**: PDF2md-CLI uses `uv` as the exclusive package management tool for all Python dependencies.

**Requirements**:
- **Mandatory**: All dependency installation MUST use `uv`
- **Mandatory**: All dependency additions MUST use `uv add` (not pip install)
- **Mandatory**: All dependency removals MUST use `uv remove`
- **Mandatory**: Project MUST use `uv.lock` for reproducible builds
- **Mandatory**: All documentation MUST reference `uv` commands (not pip)

**Rationale**:
- `uv` is 10-100x faster than pip for dependency resolution
- `uv` provides deterministic, reproducible builds via lockfile
- `uv` unifies dependency management and virtual environment handling
- `uv` is written in Rust, providing better performance and reliability

**Commands**:
```bash
# Install dependencies
uv sync

# Add new dependency
uv add <package>

# Add dev dependency
uv add --dev <package>

# Remove dependency
uv remove <package>

# Run commands in virtual environment
uv run <command>

# Activate virtual environment
source .venv/bin/activate  # Automatically managed by uv
```

**Compliance**:
- All pull requests MUST use `uv` for dependency changes
- All setup instructions MUST use `uv` commands
- CI/CD pipelines MUST use `uv` for dependency installation
- Violations MUST be corrected before merge

---

### II. Client-Server Architecture

**Principle**: PDF2md-CLI follows a strict client-server architecture with clear separation of concerns.

**Requirements**:
- Client handles ONLY user interaction and file I/O
- Server handles ONLY PDF conversion and GPU processing
- Communication via HTTP REST API ONLY
- No business logic on client side

---

### III. Async-First Development

**Principle**: Network operations MUST be async using asyncio and httpx.

**Requirements**:
- All HTTP client code MUST be async
- CLI provides sync wrapper via asyncio.run()
- No synchronous HTTP requests (no requests library)

---

### IV. Type Safety

**Principle**: All code MUST pass mypy type checking.

**Requirements**:
- All functions MUST have type hints
- Pydantic models for configuration
- Strict mypy checking enabled

---

### V. Error Handling

**Principle**: All errors MUST use structured exception hierarchy with exit codes.

**Requirements**:
- Custom exceptions inherit from PDF2MDError
- Exit codes: 0 (success), 1 (generic), 2 (network), 3 (validation), 4 (conversion), 5 (config), 130 (SIGINT)
- Error messages include troubleshooting hints

---

### VI. Cross-Platform Compatibility

**Principle**: CLI MUST work on Linux, macOS, and Windows.

**Requirements**:
- Use platformdirs for cross-platform paths
- Rich terminal output with Unicode fallback
- Test on all three platforms

---

### VII. YAGNI (You Aren't Gonna Need It)

**Principle**: Implement ONLY features specified in requirements.

**Requirements**:
- No premature optimization
- No speculative features
- Batch processing explicitly out of scope for MVP
- Background daemon mode explicitly out of scope

---

## Governance

### Amendment Process

1. Principle changes require documentation update
2. Majority approval from maintainers
3. Migration plan for existing code
4. Update constitution version number

### Compliance

- All PRs MUST verify compliance with constitution
- Violations MUST block merge
- Complexity MUST be justified against principles

---

## Technology Stack

**Mandatory**:
- Package Manager: `uv` (NON-NEGOTIABLE)
- Python: 3.11+
- CLI Framework: Typer
- HTTP Client: httpx (async)
- Data Validation: Pydantic v2+
- Terminal Output: Rich
- PDF Conversion (Server): marker-pdf (GPU-enabled OCR)

**Prohibited**:
- pip (use uv instead)
- requests (use httpx)
- click (use typer)
- tqdm (use rich)

---

## Version History

- **1.0.0** (2026-01-07): Initial constitution with uv package management principle
