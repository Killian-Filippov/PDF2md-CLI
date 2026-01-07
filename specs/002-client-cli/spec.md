# Feature Specification: Client CLI Interface

**Feature Branch**: `002-client-cli`
**Created**: 2026-01-06
**Status**: Draft
**Input**: Architecture design document - Section 4.1 (Client Component Design)

## Clarifications

### Session 2026-01-07

- Q: How should CLI handle edge cases like directory paths, multiple files, or invalid inputs? → A: Fast-fail with clear error messages and exit code 3 (validation error)
- Q: What is the network retry strategy for connection failures? → A: Exponential backoff (2s → 4s → 8s), max 3 retries, no retry on HTTP 4xx errors
- Q: What happens when server is completely unreachable after all retries? → A: Display detailed troubleshooting guide and exit with code 2
- Q: Where should file size validation be performed? → A: Both client-side (before upload) and server-side (safety net)
- Q: How should "Converting..." progress be displayed during server processing? → A: Static message with animated pulse indicator (e.g., "[●    ]") updates every 0.5s

## User Scenarios & Testing

### User Story 1 - Basic PDF Conversion Command (Priority: P1)

A user wants to convert a PDF file to Markdown. They open a terminal and run a simple command with the PDF file path. The CLI shows progress and saves the converted Markdown file.

**Why this priority**: This is the core user interaction - the primary way users will interact with the system.

**Independent Test**: Can be tested by running the CLI command with a test PDF and verifying the output file is created.

**Acceptance Scenarios**:
1. **Given** a PDF file exists at `~/documents/report.pdf`, **When** user runs `pdf2md ~/documents/report.pdf`, **Then** the system creates `~/documents/report.md`
2. **Given** conversion is in progress, **When** user watches terminal, **Then** they see progress bars for upload, conversion, and download
3. **Given** conversion completes successfully, **Then** system displays success message: "✓ Converted: report.md (42 pages, 12.3s)"

---

### User Story 2 - Configuration Management Commands (Priority: P2)

A user needs to set up the CLI tool to connect to their conversion server. They use simple commands to initialize, view, and update configuration.

**Why this priority**: Essential for usability, but can use command-line flags as fallback for MVP.

**Independent Test**: Can be tested by running config commands and verifying configuration file is created/updated correctly.

**Acceptance Scenarios**:
1. **Given** no configuration exists, **When** user runs `pdf2md config init --server-url http://192.168.1.100:8000`, **Then** system creates `~/.pdf2md/config.json` with specified URL
2. **Given** configuration exists, **When** user runs `pdf2md config show`, **Then** system displays current configuration in readable format
3. **Given** user wants to change server, **When** they run `pdf2md config set server-url http://new-server:8000`, **Then** configuration is updated with new URL

---

### User Story 3 - Custom Output Location (Priority: P2)

A user wants to save the converted Markdown file to a specific location instead of the PDF's directory.

**Why this priority**: Useful feature, but default behavior (same as PDF) is sufficient for MVP.

**Independent Test**: Can be tested by converting with `--output` flag and verifying file location.

**Acceptance Scenarios**:
1. **Given** a PDF at `~/docs/report.pdf`, **When** user runs `pdf2md ~/docs/report.pdf --output ~/converted/`, **Then** Markdown is saved at `~/converted/report.md`
2. **Given** output directory doesn't exist, **When** user runs command with `--output`, **Then** system creates directory before saving file

---

### User Story 4 - Verbose Mode for Debugging (Priority: P3)

A developer or advanced user wants to see detailed logging information to troubleshoot issues.

**Why this priority**: Nice to have for debugging, but not needed for normal operation.

**Independent Test**: Can be tested by running with `--verbose` flag and checking output includes detailed logs.

**Acceptance Scenarios**:
1. **Given** conversion is running, **When** user runs with `--verbose`, **Then** output includes detailed timing, HTTP requests, and server responses
2. **Given** an error occurs, **When** verbose mode is enabled, **Then** full stack trace and debugging information is displayed

---

### User Story 5 - Overwrite Existing Files (Priority: P3)

A user wants to overwrite an existing Markdown file without being prompted.

**Why this priority**: Convenience feature for batch operations, but interactive prompt is safer for MVP.

**Independent Test**: Can be tested by running with `--overwrite` flag when MD file exists.

**Acceptance Scenarios**:
1. **Given** `report.md` already exists, **When** user runs without flags, **Then** system prompts: "File exists. Overwrite? [y/N]"
2. **Given** `report.md` already exists, **When** user runs with `--overwrite` flag, **Then** system replaces file without prompting

---

## Edge Cases

- **Directory path provided**: Display error "Expected a PDF file, not a directory" and exit with code 3 (validation error)
- **Multiple PDF files**: Display error "Expected exactly one PDF file path" and exit with code 3
- **Spaces/special characters in path**: Support paths with spaces and special characters (require proper quoting in shell)
- **No arguments provided**: Display usage help and exit with code 3
- **Different working directory**: Resolve relative paths from current working directory; absolute paths work as-is
- **Corrupted configuration file**: Backup corrupted file with timestamp, use defaults, display warning message
- **`--output` as file path**: Treat as output directory path; if it's an existing file, display error asking for directory path
- **Server completely unreachable**: After all retries exhausted, display detailed troubleshooting guide (check server status, network connectivity, configuration) and exit with code 2

## Requirements

### Functional Requirements

**Core Command**:
- **FR-CLI-001**: System MUST provide `pdf2md` command that accepts a PDF file path as positional argument
- **FR-CLI-002**: System MUST support `--output` flag to specify custom output location
- **FR-CLI-003**: System MUST support `--overwrite` flag to skip confirmation prompts
- **FR-CLI-004**: System MUST support `--verbose` flag for detailed logging
- **FR-CLI-005**: System MUST display usage help when run with `--help` flag
- **FR-CLI-006**: System MUST display version information when run with `--version` flag

**Configuration Commands**:
- **FR-CLI-007**: System MUST provide `config init` command to create initial configuration
- **FR-CLI-008**: System MUST provide `config show` command to display current configuration
- **FR-CLI-009**: System MUST provide `config set <key> <value>` command to update configuration
- **FR-CLI-010**: `config init` MUST accept `--server-url` flag to set server address
- **FR-CLI-011**: `config init` MUST accept `--timeout` flag to set connection timeout
- **FR-CLI-012**: Configuration file MUST be created at `~/.pdf2md/config.json`

**Progress Display**:
- **FR-CLI-013**: System MUST display upload progress bar with bytes transferred and percentage
- **FR-CLI-014**: System MUST display "Converting..." message with animated pulse indicator during server processing (e.g., "Converting... [●    ]" updates every 0.5s)
- **FR-CLI-015**: System MUST display download progress bar for Markdown file
- **FR-CLI-016**: Progress bars MUST use cross-platform compatible library with consistent format and Unicode support

**User Feedback**:
- **FR-CLI-017**: System MUST display checkmark (✓) for success indicators
- **FR-CLI-018**: System MUST display cross mark (✗) for error indicators
- **FR-CLI-019**: Success message MUST include output filename, page count, and total time
- **FR-CLI-020**: Error message MUST include error type, description, and troubleshooting hints
- **FR-CLI-021**: System MUST color-code output (green for success, red for errors, yellow for warnings)

**Input Validation**:
- **FR-CLI-022**: System MUST validate argument count (requires exactly one PDF path)
- **FR-CLI-023**: System MUST validate PDF file exists before processing
- **FR-CLI-024**: System MUST validate file is readable (permissions check)
- **FR-CLI-025**: System MUST validate output directory exists or can be created
- **FR-CLI-026**: System MUST display clear error if validation fails
- **FR-CLI-027**: System MUST validate file size does not exceed 500MB before upload (client-side validation)
- **FR-CLI-028**: System MUST display error with actual size and limit when file too large

**Exit Codes**:
- **FR-CLI-029**: System MUST exit with code 0 on successful conversion
- **FR-CLI-030**: System MUST exit with code 1 for generic errors
- **FR-CLI-031**: System MUST exit with code 2 for network errors
- **FR-CLI-032**: System MUST exit with code 3 for validation errors
- **FR-CLI-033**: System MUST exit with code 4 for conversion errors
- **FR-CLI-034**: System MUST exit with code 5 for configuration errors

**Network Retry Strategy**:
- **FR-CLI-035**: System MUST retry on connection failures and timeouts with exponential backoff (2s → 4s → 8s)
- **FR-CLI-036**: System MUST stop retrying after max_retries attempts (default: 3)
- **FR-CLI-037**: System MUST NOT retry on HTTP 4xx errors (client errors)
- **FR-CLI-038**: System MUST display retry attempt number to user during backoff waits

### Key Entities

**CLICommand**:
- Represents a parsed command-line invocation
- Attributes: command name, arguments, flags, working directory, configuration

**ConfigCommand**:
- Represents configuration management subcommands
- Attributes: action (init/show/set), key, value, config file path

**ConversionOptions**:
- Represents user-provided options for conversion
- Attributes: input path, output path, overwrite flag, verbose flag, config overrides

## Success Criteria

### Measurable Outcomes

- **SC-CLI-001**: Help command displays all available commands and flags within 10 seconds of first run
- **SC-CLI-002**: Help command displays all available commands and flags in clear format
- **SC-CLI-003**: Configuration commands complete in under 2 seconds
- **SC-CLI-004**: Progress bars update smoothly without flickering or delay
- **SC-CLI-005**: 95% of users can successfully configure CLI tool on first attempt
- **SC-CLI-006**: Error messages fit within 80-character terminal width (no awkward wrapping)
- **SC-CLI-007**: Color-coding works on Windows, macOS, and Linux terminals

## Assumptions

1. **Terminal Compatibility**: CLI works on common terminals (bash, zsh, PowerShell, cmd.exe)
2. **User Experience**: Users are familiar with basic command-line concepts (file paths, flags)
3. **File Permissions**: Users have read permission for PDF files and write permission for output directories
4. **Python Environment**: Python 3.11+ is installed and accessible via `python` or `python3`
5. **Network Connectivity**: Client can reach server at configured URL (firewall allows connection)
6. **Configuration Directory**: User's home directory is writable for creating config file
7. **Encoding**: Terminal supports UTF-8 encoding for displaying progress bars and messages
8. **Interactive Mode**: Standard input/output is available for prompts and progress display

## Out of Scope

For the client CLI feature, the following are explicitly out of scope:

- GUI or web-based interface
- Interactive file selection dialogs
- Background daemon mode for batch processing
- Shell auto-completion scripts (can be added later)
- Man page generation (use `--help` instead)
- Internationalization of CLI messages (English only)
- Custom progress bar themes or styles
- Plugin system for extending CLI functionality
- Configuration file encryption or secure storage
- Integration with file managers for right-click conversion
