# Feature Specification: File Handling and Validation

**Feature Branch**: `005-file-handling`
**Created**: 2026-01-06
**Status**: Draft
**Input**: Architecture design document - Section 4.1.4 (File Handler) and Section 9 (Security Design)

## User Scenarios & Testing

### User Story 1 - Client-Side File Validation (Priority: P1)

Before uploading, the client validates the PDF file exists, is readable, and is a valid PDF format. This prevents wasted network requests.

**Why this priority**: Essential for good UX - fail fast before uploading.

**Independent Test**: Can be tested by providing invalid files and verifying validation catches them.

**Acceptance Scenarios**:
1. **Given** file doesn't exist, **When** user runs command, **Then** error "File not found" is displayed immediately
2. **Given** file has wrong extension (`.txt`), **When** validation runs, **Then** error "Expected PDF file, got Text file" is shown
3. **Given** file is 600MB (over limit), **When** validation checks size, **Then** error "File too large (max 500MB)" is displayed
4. **Given** file exists and is valid PDF, **When** validation succeeds, **Then** upload proceeds immediately

---

### User Story 2 - Server-Side File Validation (Priority: P1)

After receiving upload, server validates the file to prevent malicious uploads and resource exhaustion.

**Why this priority**: Critical for security and stability. Never trust client validation.

**Independent Test**: Can be tested by uploading malicious files and verifying server rejects them.

**Acceptance Scenarios**:
1. **Given** uploaded file has wrong magic bytes, **When** server validates, **Then** it returns 400 with "Invalid PDF file"
2. **Given** uploaded file has dangerous filename (`../../etc/passwd.pdf`), **When** server sanitizes, **Then** filename is cleaned to `______etc_passwd.pdf`
3. **Given** uploaded file is exactly 500MB, **When** server checks size, **Then** file is accepted
4. **Given** uploaded file is 500MB + 1 byte, **When** server checks size, **Then** file is rejected with 400 error

---

### User Story 3 - Temporary File Management (Priority: P1)

The server stores uploaded PDFs temporarily during conversion and cleans them up afterward to prevent disk exhaustion.

**Why this priority**: Essential for resource management. Without cleanup, server disk fills up.

**Independent Test**: Can be tested by converting files and verifying temp files are deleted.

**Acceptance Scenarios**:
1. **Given** PDF is uploaded, **When** saved to temp, **Then** filename uses UUID format: `{uuid}_original.pdf`
2. **Given** conversion completes, **When** response is sent, **Then** both PDF and MD temp files are deleted
3. **Given** conversion fails, **When** error is raised, **Then** uploaded PDF is still deleted (cleanup in finally block)
4. **Given** server crashes during conversion, **When** server restarts, **Then** startup cleanup removes orphaned files

---

### User Story 4 - Output File Conflict Resolution (Priority: P2)

When the Markdown output file already exists, the system prompts the user or overwrites based on configuration.

**Why this priority**: Important for safety, but default behavior (prompt) is safe for MVP.

**Independent Test**: Can be tested by converting PDF twice and checking behavior.

**Acceptance Scenarios**:
1. **Given** `document.md` already exists, **When** user runs without flags, **Then** system prompts: "Overwrite document.md? [y/N]"
2. **Given** user enters 'y', **When** they confirm, **Then** file is overwritten
3. **Given** user enters 'n', **When** they decline, **Then** command exits with message "Conversion cancelled"
4. **Given** `--overwrite` flag is set, **When** file exists, **Then** it's replaced without prompting

---

### User Story 5 - File Permission Handling (Priority: P3)

The system handles permission errors gracefully when files aren't readable or writable.

**Why this priority**: Edge case, but should provide clear error message.

**Independent Test**: Can be tested by using read-only files and directories.

**Acceptance Scenarios**:
1. **Given** PDF file has no read permission, **When** user runs command, **Then** error "Permission denied reading file" is shown
2. **Given** output directory is read-only, **When** conversion completes, **Then** error "Cannot write to directory" is displayed
3. **Given** temp directory is not writable, **When** server starts, **Then** startup fails with clear error

---

## Edge Cases

- What happens if PDF file is a symbolic link?
- What happens if PDF file changes during upload?
- What happens if output directory path is very long (>200 characters)?
- What happens if filename contains Unicode characters (emoji, Chinese, etc.)?
- What happens if disk is full during file save?
- What happens if temp directory is on a different filesystem with no space?
- What happens if file has null bytes in filename?
- What happens if client uploads during server cleanup?

## Requirements

### Functional Requirements

**Client-Side Validation**:
- **FR-FH-001**: Client MUST check file exists using `Path.exists()`
- **FR-FH-002**: Client MUST check file is readable using `Path.stat().st_size > 0`
- **FR-FH-003**: Client MUST validate file extension is `.pdf` (case-insensitive)
- **FR-FH-004**: Client MUST validate file size ≤ 500MB (500 * 1024 * 1024 bytes)
- **FR-FH-005**: Client MUST validate magic bytes start with `%PDF-`
- **FR-FH-006**: Client MUST display specific error for each validation failure type
- **FR-FH-007**: Client MUST perform all validations before initiating network request

**Server-Side Validation**:
- **FR-FH-008**: Server MUST validate `Content-Type` is `multipart/form-data`
- **FR-FH-009**: Server MUST validate file field exists in multipart form
- **FR-FH-010**: Server MUST validate filename extension (case-insensitive `.pdf`)
- **FR-FH-011**: Server MUST validate magic bytes from uploaded content
- **FR-FH-012**: Server MUST sanitize filename to remove path traversal (`..`, `\`)
- **FR-FH-013**: Server MUST sanitize filename to remove dangerous characters (`< > : " | ? *`)
- **FR-FH-014**: Server MUST limit filename length to 255 characters
- **FR-FH-015**: Server MUST validate file size ≤ 500MB during upload (streaming check)
- **FR-FH-016**: Server MUST return 400 Bad Request for validation failures

**Filename Sanitization**:
- **FR-FH-017**: Sanitizer MUST remove directory path components
- **FR-FH-018**: Sanitizer MUST replace dangerous chars with underscore (`_`)
- **FR-FH-019**: Sanitizer MUST prevent hidden files (prepend `_` if starts with `.`)
- **FR-FH-020**: Sanitizer MUST preserve file extension
- **FR-FH-021**: Sanitizer MUST handle Unicode characters properly

**Temporary File Management**:
- **FR-FH-022**: Server MUST use `/tmp/pdf2md/` as temp base directory
- **FR-FH-023**: Server MUST create temp directory on startup if missing
- **FR-FH-024**: Server MUST generate UUID4 for each uploaded file
- **FR-FH-025**: Server MUST use filename format `{uuid}_{sanitized_original}`
- **FR-FH-026**: Server MUST save uploaded file using async file I/O (`aiofiles`)
- **FR-FH-027**: Server MUST read file in chunks (8192 bytes) to avoid memory overload
- **FR-FH-028**: Server MUST set file permissions to 600 (owner read/write only)
- **FR-FH-029**: Server MUST clean up temp files in `finally` block (always execute)
- **FR-FH-030**: Server MUST clean up all temp files on shutdown
- **FR-FH-031**: Server MUST log cleanup failures as warnings (not errors)

**Output File Handling**:
- **FR-FH-032**: Client MUST save Markdown to same directory as PDF by default
- **FR-FH-033**: Client MUST replace `.pdf` extension with `.md`
- **FR-FH-034**: Client MUST check if output file exists before saving
- **FR-FH-035**: Client MUST prompt user if file exists and `--overwrite` not set
- **FR-FH-036**: Client MUST support custom output directory via `--output` flag
- **FR-FH-037**: Client MUST create output directory if it doesn't exist
- **FR-FH-038**: Client MUST validate output directory is writable before conversion

**File Security**:
- **FR-FH-039**: Server MUST prevent path traversal attacks
- **FR-FH-040**: Server MUST validate resolved path is under temp directory
- **FR-FH-041**: Client MUST NOT log full file paths (log filename only)
- **FR-FH-042**: Server MUST NOT log file contents (only metadata)
- **FR-FH-043**: Temp files MUST be readable only by owner (permissions 600)

**Error Recovery**:
- **FR-FH-044**: System MUST delete uploaded PDF if conversion fails
- **FR-FH-045**: System MUST delete partial MD if conversion fails midway
- **FR-FH-046**: System MUST log cleanup errors but not raise
- **FR-FH-047**: Startup cleanup MUST remove files older than 1 hour (orphaned)

### Key Entities

**FileValidator** (Client):
- Validates PDF files before upload
- Methods: `validate_exists()`, `validate_readable()`, `validate_pdf_type()`, `validate_size()`

**FileSanitizer** (Shared):
- Cleans filenames for safe filesystem use
- Methods: `sanitize_filename()`, `safe_path_join()`, `remove_path_traversal()`

**TempFileManager** (Server):
- Manages temporary file lifecycle
- Attributes: base_dir (Path), max_age_seconds (int)
- Methods: `save_upload()`, `cleanup()`, `cleanup_all()`, `cleanup_orphans()`

**FileMetadata**:
- Represents validated file information
- Attributes: original_filename, sanitized_filename, size_bytes, content_type, magic_bytes, is_valid_pdf, validation_errors

## Success Criteria

### Measurable Outcomes

- **SC-FH-001**: 100% of invalid files are caught before upload (client-side)
- **SC-FH-002**: 100% of malicious uploads are rejected (server-side)
- **SC-FH-003**: 99.9% of temp files are cleaned up after conversion
- **SC-FH-004**: No disk space exhaustion after 1000 conversions
- **SC-FH-005**: File validation completes in under 100ms per file
- **SC-FH-006**: Sanitized filenames never contain dangerous characters
- **SC-FH-007**: User understands error message and can fix issue 80% of time

## Assumptions

1. **File System**: Filesystem supports UTF-8 filenames and permissions
2. **Disk Space**: Server has at least 10GB free for temp files
3. **Permissions**: User running command has read access to PDF files
4. **Temp Location**: `/tmp` is writable and has sufficient space
5. **File Size**: Most PDFs are under 100MB (500MB is edge case)
6. **Character Set**: Filenames use Unicode (UTF-8) encoding
7. **Symlinks**: Symlinks are not commonly used for PDF files

## Out of Scope

For file handling feature, the following are explicitly out of scope:

- File compression or decompression
- File encryption or decryption
- File versioning or backup
- Cloud storage integration (S3, etc.)
- File watching or auto-conversion
- Recursive directory scanning
- Batch file operations
- File metadata extraction (author, creation date)
- Thumbnail generation
- File format conversion beyond PDF→MD
- Delta encoding or differential uploads
- Resumable uploads after interruption
