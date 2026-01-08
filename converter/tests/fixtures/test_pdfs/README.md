# Test PDF Fixtures

This directory contains sample PDFs for testing the converter.

## Required Test PDFs

### 1. valid_text.pdf
A standard PDF with embedded text, headings, lists, and tables.
- **Purpose**: Test basic PDF to Markdown conversion
- **Content**: 5-10 pages with mixed content

### 2. scanned.pdf
A scanned PDF with no text layer (images only).
- **Purpose**: Test GPU OCR functionality
- **Content**: 10 pages of clear text, good quality scan

### 3. encrypted.pdf
A password-protected PDF.
- **Purpose**: Test password detection and rejection
- **Password**: test123

### 4. corrupted.pdf
A corrupted or invalid PDF file.
- **Purpose**: Test error handling for invalid PDFs
- **Creation**: Truncate a valid PDF or use invalid header

### 5. with_images.pdf
A PDF containing embedded images.
- **Purpose**: Test image extraction and downscaling
- **Content**: 3-5 pages with JPEG/PNG images (>2000px width for testing)

### 6. multi_column.pdf
A PDF with multi-column layout.
- **Purpose**: Test layout detection
- **Content**: Academic paper or newsletter with 2+ columns

## How to Create Test PDFs

### Option 1: Use Existing PDFs
Replace these placeholder files with your own test PDFs matching the descriptions above.

### Option 2: Generate with Tools

#### Create valid_text.pdf
```bash
# Using LibreOffice
soffice --headless --convert-to pdf example.docx

# Or using Python (reportlab)
python -c "
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

doc = SimpleDocTemplate('valid_text.pdf', pagesize=letter)
styles = getSampleStyleSheet()
story = []

# Add content
story.append(Paragraph('Heading 1', styles['Heading1']))
story.append(Paragraph('This is a paragraph.', styles['BodyText']))
story.append(Spacer(1, 12))

doc.build(story)
"
```

#### Create encrypted.pdf
```bash
# Using qpdf
qpdf --encrypt test123 test123 40 -- input.pdf encrypted.pdf

# Or using pdftk
pdftk input.pdf output encrypted.pdf user_pw test123
```

#### Create corrupted.pdf
```bash
# Truncate a valid PDF
dd if=valid_text.pdf of=corrupted.pdf bs=1024 count=1

# Or create invalid file
echo "INVALID PDF HEADER" > corrupted.pdf
```

#### Create with_images.pdf
Use any PDF with images, or create from Word doc with embedded images.

#### Create scanned.pdf
Print a document to PDF, then scan it (or use a scanned document).

## Placeholder Files

For initial testing, you can use empty placeholder files:

```bash
touch valid_text.pdf scanned.pdf encrypted.pdf corrupted.pdf with_images.pdf multi_column.pdf
```

**Note**: Tests will fail with empty files. Replace with actual PDFs for integration tests.

## Test Data Requirements

- **File sizes**: Keep under 5MB each for fast testing
- **Page counts**: 5-20 pages each
- **Content variety**: Text, images, tables, lists, headings
- **Languages**: English and Chinese for multi-language testing
