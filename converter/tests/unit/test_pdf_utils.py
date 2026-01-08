"""Unit tests for PDF validation utilities."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from pikepdf import Pdf
from pdf2md_converter.utils.pdf_utils import is_pdf_encrypted, validate_pdf_structure, get_page_count
from pdf2md_converter.exceptions import CorruptedPDFError


class TestIsPdfEncrypted:
    """Test PDF encryption detection."""

    @patch("pdf2md_converter.utils.pdf_utils.Path.exists", return_value=True)
    @patch("pdf2md_converter.utils.pdf_utils.Pdf")
    def test_non_encrypted_pdf(self, mock_pdf_class: MagicMock, mock_exists: MagicMock) -> None:
        """Test returns False for non-encrypted PDF."""
        mock_pdf = MagicMock()
        mock_pdf.is_encrypted = False
        mock_pdf_class.open.return_value.__enter__.return_value = mock_pdf

        result = is_pdf_encrypted(Path("test.pdf"))

        assert result is False

    @patch("pdf2md_converter.utils.pdf_utils.Path.exists", return_value=True)
    @patch("pdf2md_converter.utils.pdf_utils.Pdf")
    def test_encrypted_pdf(self, mock_pdf_class: MagicMock, mock_exists: MagicMock) -> None:
        """Test returns True for encrypted PDF."""
        mock_pdf = MagicMock()
        mock_pdf.is_encrypted = True
        mock_pdf_class.open.return_value.__enter__.return_value = mock_pdf

        result = is_pdf_encrypted(Path("test.pdf"))

        assert result is True

    @patch("pdf2md_converter.utils.pdf_utils.Path.exists", return_value=False)
    def test_file_not_found(self, mock_exists: MagicMock) -> None:
        """Test raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError, match="PDF file not found"):
            is_pdf_encrypted(Path("missing.pdf"))

    @patch("pdf2md_converter.utils.pdf_utils.Path.exists", return_value=True)
    @patch("pdf2md_converter.utils.pdf_utils.Pdf")
    def test_corrupted_pdf(self, mock_pdf_class: MagicMock, mock_exists: MagicMock) -> None:
        """Test raises CorruptedPDFError for corrupted PDF."""
        mock_pdf_class.open.side_effect = Exception("PDF header not found")

        with pytest.raises(CorruptedPDFError):
            is_pdf_encrypted(Path("corrupted.pdf"))

    @patch("pdf2md_converter.utils.pdf_utils.Path.exists", return_value=True)
    @patch("pdf2md_converter.utils.pdf_utils.Pdf")
    def test_password_error_detected_as_encrypted(self, mock_pdf_class: MagicMock, mock_exists: MagicMock) -> None:
        """Test password-related errors return True."""
        mock_pdf_class.open.side_effect = Exception("Password required")

        result = is_pdf_encrypted(Path("encrypted.pdf"))

        assert result is True


class TestValidatePdfStructure:
    """Test PDF structure validation."""

    @patch("pdf2md_converter.utils.pdf_utils.Path.exists", return_value=True)
    @patch("pdf2md_converter.utils.pdf_utils.Pdf")
    def test_valid_pdf_structure(self, mock_pdf_class: MagicMock, mock_exists: MagicMock) -> None:
        """Test returns True for valid PDF structure."""
        mock_pdf = MagicMock()
        mock_pdf.pages = [MagicMock(), MagicMock()]
        mock_pdf.root = MagicMock()
        mock_pdf_class.open.return_value.__enter__.return_value = mock_pdf

        result = validate_pdf_structure(Path("valid.pdf"))

        assert result is True

    @patch("pdf2md_converter.utils.pdf_utils.Path.exists", return_value=False)
    def test_file_not_found(self, mock_exists: MagicMock) -> None:
        """Test raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError, match="PDF file not found"):
            validate_pdf_structure(Path("missing.pdf"))

    @patch("pdf2md_converter.utils.pdf_utils.Path.exists", return_value=True)
    @patch("pdf2md_converter.utils.pdf_utils.Pdf")
    def test_corrupted_pdf(self, mock_pdf_class: MagicMock, mock_exists: MagicMock) -> None:
        """Test raises CorruptedPDFError for corrupted PDF."""
        mock_pdf_class.open.side_effect = Exception("Invalid PDF structure")

        with pytest.raises(CorruptedPDFError, match="PDF file structure is corrupted"):
            validate_pdf_structure(Path("corrupted.pdf"))

    @patch("pdf2md_converter.utils.pdf_utils.Path.exists", return_value=True)
    @patch("pdf2md_converter.utils.pdf_utils.Pdf")
    def test_encrypted_pdf_passes(self, mock_pdf_class: MagicMock, mock_exists: MagicMock) -> None:
        """Test encrypted PDF returns True (not treated as corruption)."""
        mock_pdf_class.open.side_effect = Exception("PDF requires password")

        result = validate_pdf_structure(Path("encrypted.pdf"))

        # Encrypted PDFs pass structure validation
        assert result is True


class TestGetPageCount:
    """Test PDF page count retrieval."""

    @patch("pdf2md_converter.utils.pdf_utils.Path.exists", return_value=True)
    @patch("pdf2md_converter.utils.pdf_utils.Pdf")
    def test_single_page_pdf(self, mock_pdf_class: MagicMock, mock_exists: MagicMock) -> None:
        """Test returns 1 for single-page PDF."""
        mock_pdf = MagicMock()
        mock_pdf.pages = [MagicMock()]
        mock_pdf_class.open.return_value.__enter__.return_value = mock_pdf

        result = get_page_count(Path("single.pdf"))

        assert result == 1

    @patch("pdf2md_converter.utils.pdf_utils.Path.exists", return_value=True)
    @patch("pdf2md_converter.utils.pdf_utils.Pdf")
    def test_multi_page_pdf(self, mock_pdf_class: MagicMock, mock_exists: MagicMock) -> None:
        """Test returns correct count for multi-page PDF."""
        mock_pdf = MagicMock()
        mock_pdf.pages = [MagicMock() for _ in range(10)]
        mock_pdf_class.open.return_value.__enter__.return_value = mock_pdf

        result = get_page_count(Path("multipage.pdf"))

        assert result == 10

    @patch("pdf2md_converter.utils.pdf_utils.Path.exists", return_value=False)
    def test_file_not_found(self, mock_exists: MagicMock) -> None:
        """Test raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError, match="PDF file not found"):
            get_page_count(Path("missing.pdf"))

    @patch("pdf2md_converter.utils.pdf_utils.Path.exists", return_value=True)
    @patch("pdf2md_converter.utils.pdf_utils.Pdf")
    def test_corrupted_pdf(self, mock_pdf_class: MagicMock, mock_exists: MagicMock) -> None:
        """Test raises CorruptedPDFError for corrupted PDF."""
        mock_pdf_class.open.side_effect = Exception("Invalid PDF structure")

        with pytest.raises(CorruptedPDFError):
            get_page_count(Path("corrupted.pdf"))

    @patch("pdf2md_converter.utils.pdf_utils.Path.exists", return_value=True)
    @patch("pdf2md_converter.utils.pdf_utils.Pdf")
    def test_encrypted_pdf_error(self, mock_pdf_class: MagicMock, mock_exists: MagicMock) -> None:
        """Test raises CorruptedPDFError for encrypted PDF."""
        mock_pdf_class.open.side_effect = Exception("Password required")

        with pytest.raises(CorruptedPDFError, match="Cannot read page count from encrypted PDF"):
            get_page_count(Path("encrypted.pdf"))

    @patch("pdf2md_converter.utils.pdf_utils.Path.exists", return_value=True)
    @patch("pdf2md_converter.utils.pdf_utils.Pdf")
    def test_empty_pdf(self, mock_pdf_class: MagicMock, mock_exists: MagicMock) -> None:
        """Test returns 0 for PDF with no pages."""
        mock_pdf = MagicMock()
        mock_pdf.pages = []
        mock_pdf_class.open.return_value.__enter__.return_value = mock_pdf

        result = get_page_count(Path("empty.pdf"))

        assert result == 0
