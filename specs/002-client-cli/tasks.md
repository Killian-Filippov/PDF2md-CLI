# Tasks: Client CLI Interface

**Input**: Design documents from `/specs/002-client-cli/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Tests**: Tests are OPTIONAL for this feature - not explicitly requested in specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Client project**: `client/` at repository root
- **Source**: `client/src/pdf2md_client/`
- **Tests**: `client/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create client directory structure: client/src/pdf2md_client/, client/tests/unit, client/tests/integration, client/tests/fixtures/test_pdfs
- [X] T002 Create pyproject.toml in client/ with dependencies: typer>=0.9.0, httpx>=0.25.0, pydantic>=2.0.0, pydantic-settings>=2.0.0, rich>=14.0.0, platformdirs>=4.0.0
- [X] T003 Create README.md in client/ with installation and usage instructions
- [X] T004 [P] Create .gitignore in client/ excluding __pycache__/, *.pyc, .venv/, .pytest_cache/, *.egg-info/
- [X] T005 [P] Create client/tests/__init__.py and client/tests/fixtures/__init__.py
- [X] T006 [P] Create client/.env.example with example environment variables (PDF2MD_SERVER_URL, PDF2MD_TIMEOUT, etc.)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Create exception hierarchy in client/src/pdf2md_client/exceptions.py (PDF2MDError base, NetworkError, ValidationError, ConversionError, ConfigError with subclasses)
- [X] T008 [P] Implement ServerConfig Pydantic model in client/src/pdf2md_client/config.py with field validators (server_url, timeout, chunk_size, max_retries, verify_ssl, output_dir, overwrite)
- [X] T009 [P] Implement ConfigManager in client/src/pdf2md_client/config_manager.py with load_config(), save_config(), _handle_corrupted_config(), set_secure_permissions()
- [X] T010 [P] Create CLIOutput wrapper using Rich in client/src/pdf2md_client/output.py with Console, THEME, _detect_unicode_support(), success(), error(), info(), warning() methods
- [X] T011 [P] Implement FileHandler in client/src/pdf2md_client/file_handler.py with validate_pdf_file(), check_output_conflict(), save_markdown() functions
- [X] T012 Create ConversionOptions Pydantic model in client/src/pdf2md_client/config.py with input_path, output_path, output_dir, overwrite, verbose, server_url, timeout, get_output_path()
- [X] T013 Create ConversionResult Pydantic model in client/src/pdf2md_client/config.py with success, output_path, page_count, duration, file_size, error
- [X] T014 Configure pytest in client/pyproject.toml with pytest-asyncio plugin and test dependencies
- [X] T015 Create __init__.py in client/src/pdf2md_client/ exporting public classes (ServerConfig, ConfigManager, ConversionOptions, ConversionResult, PDF2MDError, CLIOutput)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Basic PDF Conversion Command (Priority: P1) 🎯 MVP

**Goal**: Enable users to convert PDF files to Markdown via a single command with progress indicators

**Independent Test**: Run `pdf2md document.pdf` and verify that `document.md` is created in the same directory with converted content

### Implementation for User Story 1

- [X] T016 [P] [US1] Implement async PDF2MDClient class in client/src/pdf2md_client/client.py with __aenter__, __aexit__, convert_pdf(), _upload_pdf(), _wait_for_conversion(), _download_markdown() methods
- [X] T017 [P] [US1] Implement _upload_pdf() in client/src/pdf2md_client/client.py with httpx multipart file upload, Rich progress bar, file size validation (500MB max)
- [X] T018 [P] [US1] Implement _wait_for_conversion() in client/src/pdf2md_client/client.py with server polling logic and "Converting... [●    ]" animated pulse indicator every 0.5s
- [X] T019 [P] [US1] Implement _download_markdown() in client/src/pdf2md_client/client.py with httpx streaming download, Rich progress bar
- [X] T020 [P] [US1] Implement exponential backoff retry logic in client/src/pdf2md_client/client.py (2s→4s→8s, max 3 retries, display retry attempt number)
- [X] T020a [US1] Implement --version flag in client/src/pdf2md_client/cli.py using typer.Option to display version information
- [X] T021 [US1] Implement main convert command in client/src/pdf2md_client/cli.py using typer with pdf_file Path argument, --output Path option, --overwrite bool option, --verbose bool option
- [X] T022 [US1] Implement convert command argument validation in client/src/pdf2md_client/cli.py (validate exactly one PDF path, file exists, readable, PDF format, <500MB)
- [X] T023 [US1] Implement async bridge in client/src/pdf2md_client/cli.py with asyncio.run(_convert_async()) wrapper and KeyboardInterrupt handler (exit 130)
- [X] T024 [US1] Implement config merging in client/src/pdf2md_client/cli.py (CLI flags > environment variables > config file > defaults)
- [X] T025 [US1] Implement edge case error messages in client/src/pdf2md_client/cli.py (directory path, multiple files, no arguments, corrupted config with troubleshooting hints)
- [X] T026 [US1] Implement success message display in client/src/pdf2md_client/cli.py with "✓ Converted: {filename} ({pages} pages, {time:.1f}s)" format using CLIOutput.success()
- [X] T027 [US1] Implement error message display in client/src/pdf2md_client/cli.py using CLIOutput.error() with error type, description, troubleshooting hints, proper exit codes (0-5, 130)
- [X] T028 [US1] Implement verbose mode in client/src/pdf2md_client/cli.py with detailed timing, HTTP requests, server responses, stack traces on errors
- [X] T029 [US1] Implement file overwrite check in client/src/pdf2md_client/cli.py with prompt "File exists. Overwrite? [y/N]" when output exists and --overwrite not set
- [X] T030 [US1] Add entry point in client/pyproject.toml: [console_scripts] pdf2md = "pdf2md_client.cli:app"

**Checkpoint**: At this point, User Story 1 should be fully functional - users can run `pdf2md document.pdf` and get `document.md`

---

## Phase 4: User Story 2 - Configuration Management Commands (Priority: P2)

**Goal**: Enable users to initialize, view, and update server configuration via `config init/show/set` commands

**Independent Test**: Run `pdf2md config init --server-url http://localhost:8000`, `pdf2md config show`, `pdf2md config set server-url http://new-server:8000` and verify config file operations

### Implementation for User Story 2

- [X] T031 [P] [US2] Implement config subcommand app in client/src/pdf2md_client/cli.py using typer.Typer() with init, show, set commands
- [X] T032 [US2] Implement config init command in client/src/pdf2md_client/cli.py with --server-url and --timeout flags, create ~/.pdf2md/config.json using ConfigManager.save_config()
- [X] T033 [US2] Implement config show command in client/src/pdf2md_client/cli.py displaying current config in readable format using ConfigManager.load_config()
- [X] T034 [US2] Implement config set command in client/src/pdf2md_client/cli.py accepting key and value arguments, updating config using ConfigManager.load_config(), modifying field, saving with ConfigManager.save_config()
- [X] T035 [US2] Implement config file validation in client/src/pdf2md_client/cli.py with error messages for invalid JSON, backup corrupted files with timestamp
- [X] T036 [US2] Add config app to main CLI app in client/src/pdf2md_client/cli.py using app.add_typer(config_app, name="config")
- [X] T037 [US2] Implement environment variable support in client/src/pdf2md_client/config.py using pydantic-settings with env_prefix="PDF2MD_"
- [X] T038 [US2] Implement config hierarchy in client/src/pdf2md_client/cli.py (CLI flags override config file, config file overrides defaults)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - users can convert PDFs and manage configuration

---

## Phase 5: User Story 3 - Custom Output Location (Priority: P2)

**Goal**: Enable users to specify custom output directory via `--output` flag

**Independent Test**: Run `pdf2md document.pdf --output ~/converted/` and verify Markdown is saved in custom directory

### Implementation for User Story 3

- [X] T039 [US3] Extend convert command in client/src/pdf2md_client/cli.py to support --output flag (already exists in T021, ensure it works with ConversionOptions.get_output_path())
- [X] T040 [US3] Implement output directory creation in client/src/pdf2md_client/file_handler.py if --output directory doesn't exist (mkdir -p)
- [X] T041 [US3] Validate output directory path in client/src/pdf2md_client/cli.py (must be directory, not file path; if existing file, display error asking for directory)
- [X] T042 [US3] Update ConversionOptions.get_output_path() in client/src/pdf2md_client/config.py to use custom output_dir when specified

**Checkpoint**: All user stories 1-3 should now be independently functional - users can convert PDFs to custom locations

---

## Phase 6: User Story 4 - Verbose Mode for Debugging (Priority: P3)

**Goal**: Enable developers to see detailed logging for troubleshooting via `--verbose` flag

**Independent Test**: Run `pdf2md document.pdf --verbose` and verify output includes detailed timing, HTTP requests, server responses

### Implementation for User Story 4

- [X] T043 [P] [US4] Add logging configuration in client/src/pdf2md_client/client.py using structlog or standard logging module
- [X] T044 [US4] Implement verbose mode logging in client/src/pdf2md_client/client.py with log levels: INFO (normal), DEBUG (verbose)
- [X] T045 [US4] Add verbose logging to _convert_async() in client/src/pdf2md_client/cli.py for: config loading, file validation, server connection, upload/download progress, conversion timing
- [X] T046 [US4] Implement stack trace display in client/src/pdf2md_client/cli.py for exceptions when verbose mode enabled
- [X] T047 [US4] Add HTTP request/response logging in client/src/pdf2md_client/client.py when verbose mode is enabled

**Checkpoint**: User Stories 1-4 should now be functional - users can convert PDFs with detailed debugging output

---

## Phase 7: User Story 5 - Overwrite Existing Files (Priority: P3)

**Goal**: Enable users to overwrite existing Markdown files without prompting via `--overwrite` flag

**Independent Test**: Run `pdf2md document.pdf --overwrite` when document.md exists and verify it replaces without prompt

### Implementation for User Story 5

- [X] T048 [P] [US5] Implement file conflict check in client/src/pdf2md_client/file_handler.py check_output_conflict() function
- [X] T049 [US5] Add interactive prompt in client/src/pdf2md_client/cli.py when output file exists and --overwrite not set: "File exists. Overwrite? [y/N]"
- [X] T050 [US5] Implement overwrite flag bypass in client/src/pdf2md_client/cli.py to skip prompt when --overwrite is True
- [X] T051 [US5] Use questionary or typer.Confirm in client/src/pdf2md_client/cli.py for user prompt (or simple input() in try/except)

**Checkpoint**: All user stories should now be complete - full CLI functionality with all user stories independently testable

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T052 [P] Create test PDF fixtures in client/tests/fixtures/test_pdfs/ (sample.pdf, large.pdf, corrupted.pdf, multipage.pdf)
- [ ] T053 [P] Add unit tests for config module in client/tests/unit/test_config.py (test_ServerConfig validation, test_ConfigManager load/save, test_config_corruption)
- [ ] T054 [P] Add unit tests for exceptions in client/tests/unit/test_exceptions.py (test_exception_hierarchy, test_exit_codes)
- [ ] T055 [P] Add unit tests for file handler in client/tests/unit/test_file_handler.py (test_validate_pdf_file, test_check_output_conflict, test_save_markdown)
- [ ] T056 [P] Add unit tests for CLI output in client/tests/unit/test_output.py (test_CLIOutput_colors, test_CLIOutput_unicode_detection)
- [ ] T057 Add integration test for conversion flow in client/tests/integration/test_conversion_flow.py (mock httpx server, test full conversion workflow)
- [X] T058 Run ruff format on client/ and ruff check to ensure code quality
- [X] T059 Run mypy type checking on client/src/pdf2md_client/ for type safety
- [X] T060 Update client/README.md with quickstart guide, examples, and troubleshooting section
- [ ] T061 Validate quickstart.md examples work as documented (install, config init, convert)
- [ ] T062 Add shell completion examples in client/README.md (optional future enhancement)
- [ ] T063 Ensure all edge cases from spec.md are handled and tested

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4 → P5)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US1, extends CLI with config commands
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Extends US1 with --output flag
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Extends all stories with verbose logging
- **User Story 5 (P3)**: Can start after Foundational (Phase 2) - Extends US1 with overwrite prompt

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T001-T006)
- All Foundational tasks marked [P] can run in parallel (T008-T013)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Within US1, T016-T020 (client methods) can run in parallel
- Within US2, T031 can run after T036 (independent)
- All test fixtures (T052, T053-T056) can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all PDF2MDClient methods together:
Task T017: "Implement _upload_pdf() in client/src/pdf2md_client/client.py"
Task T018: "Implement _wait_for_conversion() in client/src/pdf2md_client/client.py"
Task T019: "Implement _download_markdown() in client/src/pdf2md_client/client.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T006)
2. Complete Phase 2: Foundational (T007-T015) - CRITICAL
3. Complete Phase 3: User Story 1 (T016-T030)
4. **STOP and VALIDATE**: Test `pdf2md document.pdf` independently
5. Document and demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → MVP Ready! 🎉
3. Add User Story 2 → Test independently → Config management
4. Add User Story 3 → Test independently → Custom output
5. Add User Story 4 → Test independently → Verbose mode
6. Add User Story 5 → Test independently → Overwrite support
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With 2-3 developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (T016-T030)
   - Developer B: User Story 2 (T031-T038)
   - Developer C: Polish & Tests (T052-T056)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Task count: 64 tasks across 8 phases
- MVP scope: Phases 1-3 (Tasks T001-T030) = 31 tasks for core PDF conversion functionality
