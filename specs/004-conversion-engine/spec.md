# Feature Specification: PDF Conversion Engine

**Feature Branch**: `004-conversion-engine`
**Created**: 2026-01-06
**Status**: Draft
**Input**: Architecture design document - Section 4.2.3 (Converter Module)

## User Scenarios & Testing

### User Story 1 - Basic PDF to Markdown Conversion (Priority: P1)

The conversion engine receives a PDF file path and converts it to Markdown format, preserving text structure, headings, lists, and images.

**Why this priority**: This is the core functionality - without this, nothing works.

**Independent Test**: Can be tested by calling the converter with a sample PDF and verifying MD output.

**Acceptance Scenarios**:
1. **Given** a standard PDF with text and headings, **When** converter processes it, **Then** output Markdown preserves heading hierarchy with `#` symbols
2. **Given** a PDF with bullet lists, **When** converter processes it, **Then** output uses `-` for list items
3. **Given** a PDF with numbered lists, **When** converter processes it, **Then** output uses `1.` format
4. **Given** a PDF with tables, **When** converter processes it, **Then** output uses Markdown table syntax

---

### User Story 2 - GPU-Accelerated OCR (Priority: P1)

PDFs with scanned images or non-embedded text need OCR processing. The engine uses GPU acceleration for fast OCR.

**Why this priority**: Essential for handling scanned PDFs, which are common use cases.

**Independent Test**: Can be tested by converting a scanned PDF and verifying text is extracted correctly.

**Acceptance Scenarios**:
1. **Given** a scanned PDF with no text layer, **When** converter processes it, **Then** GPU OCR extracts text with >95% accuracy
2. **Given** GPU is available, **When** OCR runs, **Then** processing completes in under 15 seconds for 10 pages
3. **Given** GPU runs out of memory, **When** conversion fails, **Then** clear error message is logged and returned

---

### User Story 3 - Image Extraction and Referencing (Priority: P2)

PDFs contain images that should be extracted and referenced in the Markdown output.

**Why this priority**: Important for complete conversion, but text-only conversion is acceptable for MVP.

**Independent Test**: Can be tested by converting a PDF with images and checking MD output.

**Acceptance Scenarios**:
1. **Given** a PDF with embedded images, **When** converter processes it, **Then** images are extracted to separate files
2. **Given** images are extracted, **When** Markdown is generated, **Then** image references use `![alt](path)` format
3. **Given** multiple images, **When** converter processes them, **Then** each gets unique filename (e.g., `image-001.png`)

---

### User Story 4 - Multi-Column Layout Handling (Priority: P2)

Some PDFs have complex layouts with multiple columns. The engine should detect and preserve reading order.

**Why this priority**: Improves quality for academic papers and publications, but left-to-right single column is acceptable for MVP.

**Independent Test**: Can be tested by converting a two-column PDF and verifying text order.

**Acceptance Scenarios**:
1. **Given** a two-column PDF, **When** converter processes it, **Then** output preserves logical reading order (top to bottom, left to right)
2. **Given** PDF with sidebars, **When** converter processes it, **Then** main content is distinguished from sidebars

---

### User Story 5 - Password-Protected PDF Handling (Priority: P3)

Some PDFs are password-protected or encrypted. The engine should detect this and fail gracefully.

**Why this priority**: Edge case, but should provide clear error message rather than crash.

**Independent Test**: Can be tested by attempting to convert a password-protected PDF.

**Acceptance Scenarios**:
1. **Given** a password-protected PDF, **When** converter attempts processing, **Then** it fails with clear error: "PDF is password-protected"
2. **Given** encryption is detected, **When** conversion fails, **Then** no partial files are left on disk

---

## Edge Cases

- What happens if PDF has no pages (empty file)?
- What happens if PDF has corrupted internal structure?
- What happens if PDF uses embedded fonts that aren't available?
- What happens if PDF has rotation or page orientation changes?
- What happens if PDF has very large pages (e.g., map or poster)?
- What happens if OCR confidence is very low (<50%)?
- What happens if PDF has mixed landscape and portrait pages?
- What happens if GPU crashes during conversion?
- What happens if Marker library throws unexpected exception?

## Requirements

### Functional Requirements

**Core Conversion**:
- **FR-CONV-001**: Engine MUST accept PDF file path and output Markdown path
- **FR-CONV-002**: Engine MUST use Marker library for conversion
- **FR-CONV-003**: Engine MUST enable GPU OCR when available via `ocr_all_pages=True`
- **FR-CONV-004**: Engine MUST preserve document structure (headings, paragraphs, lists)
- **FR-CONV-005**: Engine MUST extract text with proper encoding (UTF-8)
- **FR-CONV-006**: Engine MUST handle PDFs up to 500 pages without crashes
- **FR-CONV-007**: Engine MUST complete 10-page conversion in under 30 seconds

**OCR and Text Extraction**:
- **FR-CONV-008**: Engine MUST apply OCR to pages without embedded text
- **FR-CONV-009**: Engine MUST use CUDA-enabled GPU for OCR acceleration
- **FR-CONV-010**: Engine MUST achieve >95% character accuracy on standard text
- **FR-CONV-011**: Engine MUST detect and skip blank pages
- **FR-CONV-012**: Engine MUST handle multi-language text (English and Chinese)

**Image Handling**:
- **FR-CONV-013**: Engine MUST extract images from PDF (JPEG, PNG)
- **FR-CONV-014**: Engine MUST save images to separate files in output directory
- **FR-CONV-015**: Engine MUST name images sequentially (`image-001.png`, `image-002.png`, etc.)
- **FR-CONV-016**: Engine MUST reference images in Markdown using relative paths
- **FR-CONV-017**: Engine MUST preserve image resolution (downscale if >2000px width)

**Table and Structure**:
- **FR-CONV-018**: Engine MUST detect tables in PDF and convert to Markdown tables
- **FR-CONV-019**: Engine MUST preserve table headers with `| Header |` syntax
- **FR-CONV-020**: Engine MUST detect headings and use `#`, `##`, `###` hierarchy
- **FR-CONV-021**: Engine MUST convert bold text to `**bold**`
- **FR-CONV-022**: Engine MUST convert italic text to `_italic_`
- **FR-CONV-023**: Engine MUST convert links to `[text](url)` format

**Error Handling**:
- **FR-CONV-024**: Engine MUST catch Marker exceptions and wrap in `ConversionError`
- **FR-CONV-025**: Engine MUST log detailed error information for debugging
- **FR-CONV-026**: Engine MUST provide user-friendly error messages
- **FR-CONV-027**: Engine MUST clean up partial files on conversion failure
- **FR-CONV-028**: Engine MUST detect password-protected PDFs and fail with clear message
- **FR-CONV-029**: Engine MUST detect corrupted PDFs and fail gracefully

**Performance**:
- **FR-CONV-030**: Engine MUST use GPU memory efficiently (avoid OOM)
- **FR-CONV-031**: Engine MUST release GPU resources after conversion
- **FR-CONV-032**: Engine MUST log conversion time (seconds) and page count
- **FR-CONV-033**: Engine MUST handle PDFs with mixed orientations

### Key Entities

**PDFConverter** (ABC):
- Abstract base class for converter implementations
- Methods: `convert(pdf_path: Path, output_path: Path) -> None`

**MarkerConverter** (Implementation):
- Concrete implementation using Marker library
- Attributes: ocr_enabled (bool), gpu_enabled (bool)
- Methods: `convert()`, `_validate_inputs()`, `_cleanup()`

**ConversionMetrics**:
- Represents conversion performance data
- Attributes: pages_processed, conversion_time_seconds, ocr_time_seconds, output_size_bytes, gpu_memory_used_mb

**ExtractionResult**:
- Represents structured extraction from PDF
- Attributes: text_blocks, images, tables, headings, metadata

## Success Criteria

### Measurable Outcomes

- **SC-CONV-001**: 95% of standard text PDFs convert successfully
- **SC-CONV-002**: OCR accuracy exceeds 95% on clear scanned documents
- **SC-CONV-003**: Conversion speed averages under 3 seconds per page
- **SC-CONV-004**: GPU memory usage stays under 4GB for typical conversions
- **SC-CONV-005**: Markdown output preserves 90% of document structure
- **SC-CONV-006**: No memory leaks after 100 consecutive conversions
- **SC-CONV-007**: Engine recovers gracefully from GPU crashes

## Assumptions

1. **Marker Library**: Marker version 0.2.8+ is installed with GPU support
2. **GPU Drivers**: NVIDIA drivers 525.60.13+ with CUDA 11.8+
3. **OCR Models**: Pre-trained OCR models are downloaded and available
4. **Memory**: Server has at least 8GB RAM (4GB for GPU, 4GB for system)
5. **Disk Space**: At least 2GB free for temporary conversion artifacts
6. **PDF Quality**: Input PDFs are not severely corrupted or malformed
7. **Language**: PDFs primarily contain English or Chinese text
8. **Image Format**: PDFs use standard image formats (JPEG, PNG)

## Out of Scope

For the conversion engine feature, the following are explicitly out of scope:

- Handwriting recognition
- Form field extraction
- Annotation or comment extraction
- Digital signature validation
- PDF page reordering or deletion
- Image format conversion (keep original format)
- Advanced layout analysis (zoning)
- Custom OCR training or fine-tuning
- PDF metadata extraction to frontmatter
- Table of contents generation
- Cross-reference resolution
- Embedded video or audio handling
- 3D model or interactive content extraction
