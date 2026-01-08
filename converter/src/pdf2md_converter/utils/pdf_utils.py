"""PDF validation utilities using pikepdf."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def is_pdf_encrypted(pdf_path: Path) -> bool:
    """
    Check if PDF file is encrypted/password-protected.

    Args:
        pdf_path: Path to PDF file

    Returns:
        True if PDF is encrypted, False otherwise

    Raises:
        FileNotFoundError: If PDF file does not exist
        CorruptedPDFError: If PDF file structure is corrupted
    """
    from pikepdf import Pdf

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        with Pdf.open(pdf_path) as pdf:
            # Check if PDF is encrypted
            # Pikepdf opens encrypted PDFs only if no password is set
            # If it's encrypted with a password, is_encrypted will be True
            return pdf.is_encrypted

    except Exception as e:
        # Check if error is related to encryption
        error_msg = str(e).lower()
        if "password" in error_msg or "encrypted" in error_msg:
            return True

        # Other errors likely indicate corruption
        from pdf2md_converter.exceptions import CorruptedPDFError
        raise CorruptedPDFError(
            f"Failed to check PDF encryption: {e}",
            {"pdf_path": str(pdf_path), "original_error": str(e)}
        )


def validate_pdf_structure(pdf_path: Path) -> bool:
    """
    Validate that PDF file structure is not corrupted.

    Args:
        pdf_path: Path to PDF file

    Returns:
        True if PDF structure is valid

    Raises:
        FileNotFoundError: If PDF file does not exist
        CorruptedPDFError: If PDF file structure is corrupted
    """
    from pikepdf import Pdf

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        with Pdf.open(pdf_path) as pdf:
            # Basic structure validation - access PDF properties
            _ = pdf.pages
            _ = pdf.root

        return True

    except Exception as e:
        error_msg = str(e).lower()

        # Check if error is encryption-related (not corruption)
        if "password" in error_msg or "encrypted" in error_msg:
            # PDF is encrypted, not necessarily corrupted
            # Let caller decide how to handle encrypted PDFs
            return True

        # Other errors indicate corruption
        from pdf2md_converter.exceptions import CorruptedPDFError
        raise CorruptedPDFError(
            f"PDF file structure is corrupted or invalid: {e}",
            {"pdf_path": str(pdf_path), "original_error": str(e)}
        )


def get_page_count(pdf_path: Path) -> int:
    """
    Get the number of pages in PDF.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Number of pages in PDF

    Raises:
        FileNotFoundError: If PDF file does not exist
        CorruptedPDFError: If PDF file structure is corrupted
    """
    from pikepdf import Pdf

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        with Pdf.open(pdf_path) as pdf:
            return len(pdf.pages)

    except Exception as e:
        error_msg = str(e).lower()

        # Check if error is encryption-related
        if "password" in error_msg or "encrypted" in error_msg:
            from pdf2md_converter.exceptions import CorruptedPDFError
            raise CorruptedPDFError(
                f"Cannot read page count from encrypted PDF: {e}",
                {"pdf_path": str(pdf_path), "original_error": str(e)}
            )

        # Other errors indicate corruption
        from pdf2md_converter.exceptions import CorruptedPDFError
        raise CorruptedPDFError(
            f"Failed to get page count: {e}",
            {"pdf_path": str(pdf_path), "original_error": str(e)}
        )
