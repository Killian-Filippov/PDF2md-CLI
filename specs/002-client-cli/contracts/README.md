# Contracts Directory

**Feature**: 002-client-cli

## Status: No External API Contracts

The client CLI component is a **consumer** of the server API. External API contracts are defined in:

- **Server API Specification**: [`../003-server-api/spec.md`](../003-server-api/spec.md)
- **Server API Contracts**: [`../003-server-api/contracts/`](../003-server-api/contracts/)

## Internal Interfaces

The following internal interfaces are defined in the implementation:

1. **CLI → Config Module Interface** (`client/config.py`)
   - Functions: `load_config()`, `save_config()`
   - Returns: `ServerConfig` (Pydantic model)

2. **CLI → HTTP Client Interface** (`client/client.py`)
   - Class: `PDF2MDClient`
   - Methods: `convert_pdf()`, `upload_pdf()`, `download_markdown()`
   - Async context manager pattern

3. **CLI → File Handler Interface** (`client/file_handler.py`)
   - Functions: `validate_pdf()`, `check_conflict()`, `save_markdown()`
   - Raises: `ValidationError`, `FileExistsError`

4. **Exception Hierarchy** (`client/exceptions.py`)
   - Base: `PDF2MDError`
   - Subtypes: `NetworkError`, `ValidationError`, `ConversionError`, `ConfigError`

## Server API Endpoints Used

The client CLI interacts with the following server endpoints:

### `POST /convert`
- **Purpose**: Upload PDF and download converted Markdown
- **Request**: `multipart/form-data` with PDF file
- **Response**: Markdown file (stream) with headers:
  - `Content-Type: text/markdown`
  - `X-Pages-Processed`: Page count
  - `X-Conversion-Time`: Duration
  - `Content-Disposition`: Attachment filename

### `GET /health`
- **Purpose**: Check server health and GPU availability
- **Response**: JSON with status, version, gpu_available, active_conversions

## Configuration Schema

Client configuration is defined in [`../data-model.md`](../data-model.md#1-serverconfig-configuration-model):

**Config File**: `~/.pdf2md/config.json` (platform-specific)

**Environment Variables**: `PDF2MD_*` prefix

**Fields**: `server_url`, `timeout`, `chunk_size`, `max_retries`, `verify_ssl`, `output_dir`, `overwrite`

## Data Models

All data models are defined in [`../data-model.md`](../data-model.md):

- `ServerConfig`: Configuration model
- `ConversionOptions`: Command-line options
- `ConversionResult`: Operation result
- Error hierarchy with exit codes
