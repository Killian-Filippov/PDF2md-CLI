"""Unit tests for exception hierarchy."""

import pytest
from pdf2md_converter.exceptions import (
    ConversionError,
    GPUUnavailableError,
    PasswordProtectedError,
    CorruptedPDFError,
    GPUOutOfMemoryError,
    PageLimitExceededError,
)


class TestConversionError:
    """Test base ConversionError class."""

    def test_create_basic_error(self) -> None:
        """Test creating error with message only."""
        error = ConversionError("Test error")
        assert error.message == "Test error"
        assert error.details == {}
        assert str(error) == "Test error"

    def test_create_error_with_details(self) -> None:
        """Test creating error with message and details."""
        error = ConversionError("Test error", {"code": "TEST", "value": 123})
        assert error.message == "Test error"
        assert error.details == {"code": "TEST", "value": 123}
        assert "code=TEST" in str(error)
        assert "value=123" in str(error)

    def test_string_representation(self) -> None:
        """Test string representation includes details."""
        error = ConversionError("Failed", {"reason": "timeout", "retries": 3})
        error_str = str(error)
        assert "Failed" in error_str
        assert "reason=timeout" in error_str
        assert "retries=3" in error_str


class TestGPUUnavailableError:
    """Test GPUUnavailableError subclass."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = GPUUnavailableError()
        assert error.message == "GPU required but not available"
        assert error.details["error_code"] == "GPU_UNAVAILABLE"

    def test_custom_message(self) -> None:
        """Test custom error message."""
        error = GPUUnavailableError("CUDA not installed")
        assert error.message == "CUDA not installed"
        assert error.details["error_code"] == "GPU_UNAVAILABLE"

    def test_inheritance(self) -> None:
        """Test inherits from ConversionError."""
        error = GPUUnavailableError()
        assert isinstance(error, ConversionError)
        assert isinstance(error, Exception)


class TestPasswordProtectedError:
    """Test PasswordProtectedError subclass."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = PasswordProtectedError()
        assert error.message == "PDF is password-protected"
        assert error.details["error_code"] == "PASSWORD_PROTECTED"

    def test_custom_message(self) -> None:
        """Test custom error message."""
        error = PasswordProtectedError("Encrypted with unknown password")
        assert error.message == "Encrypted with unknown password"
        assert error.details["error_code"] == "PASSWORD_PROTECTED"


class TestCorruptedPDFError:
    """Test CorruptedPDFError subclass."""

    def test_default_details(self) -> None:
        """Test default error details."""
        error = CorruptedPDFError("Invalid PDF structure")
        assert error.message == "Invalid PDF structure"
        assert error.details["error_code"] == "CORRUPTED_PDF"

    def test_custom_details(self) -> None:
        """Test custom error details are merged with defaults."""
        error = CorruptedPDFError("Truncated file", {"offset": 1024, "reason": "EOF"})
        assert error.message == "Truncated file"
        assert error.details["error_code"] == "CORRUPTED_PDF"
        assert error.details["offset"] == 1024
        assert error.details["reason"] == "EOF"

    def test_string_with_details(self) -> None:
        """Test string representation includes all details."""
        error = CorruptedPDFError("Bad header", {"position": 0, "bytes": b"TEST"})
        error_str = str(error)
        assert "Bad header" in error_str
        assert "error_code=CORRUPTED_PDF" in error_str
        assert "position=0" in error_str


class TestGPUOutOfMemoryError:
    """Test GPUOutOfMemoryError subclass."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = GPUOutOfMemoryError()
        assert error.message == "GPU out of memory"
        assert error.details["error_code"] == "GPU_OOM"

    def test_custom_message(self) -> None:
        """Test custom error message."""
        error = GPUOutOfMemoryError("GPU 0 ran out of memory")
        assert error.message == "GPU 0 ran out of memory"
        assert error.details["error_code"] == "GPU_OOM"


class TestPageLimitExceededError:
    """Test PageLimitExceededError subclass."""

    def test_error_creation(self) -> None:
        """Test creating error with page counts."""
        error = PageLimitExceededError(page_count=600, max_pages=500)
        assert error.message == "PDF has 600 pages, exceeds maximum of 500"
        assert error.details["error_code"] == "PAGE_LIMIT_EXCEEDED"
        assert error.details["page_count"] == 600
        assert error.details["max_pages"] == 500

    def test_string_representation(self) -> None:
        """Test string includes page count details."""
        error = PageLimitExceededError(page_count=1000, max_pages=100)
        error_str = str(error)
        assert "1000 pages" in error_str
        assert "maximum of 100" in error_str
        assert "error_code=PAGE_LIMIT_EXCEEDED" in error_str

    def test_different_limits(self) -> None:
        """Test with different page limits."""
        error = PageLimitExceededError(page_count=501, max_pages=500)
        assert error.details["page_count"] == 501
        assert error.details["max_pages"] == 500


class TestExceptionHierarchy:
    """Test exception hierarchy relationships."""

    def test_all_subclasses_inherit_from_base(self) -> None:
        """Test all specific exceptions inherit from ConversionError."""
        exceptions = [
            GPUUnavailableError(),
            PasswordProtectedError(),
            CorruptedPDFError("test"),
            GPUOutOfMemoryError(),
            PageLimitExceededError(100, 50),
        ]

        for exc in exceptions:
            assert isinstance(exc, ConversionError)
            assert isinstance(exc, Exception)

    def test_error_codes_are_unique(self) -> None:
        """Test each exception has unique error code."""
        error = GPUUnavailableError()
        assert error.details["error_code"] == "GPU_UNAVAILABLE"

        error = PasswordProtectedError()
        assert error.details["error_code"] == "PASSWORD_PROTECTED"

        error = CorruptedPDFError("test")
        assert error.details["error_code"] == "CORRUPTED_PDF"

        error = GPUOutOfMemoryError()
        assert error.details["error_code"] == "GPU_OOM"

        error = PageLimitExceededError(100, 50)
        assert error.details["error_code"] == "PAGE_LIMIT_EXCEEDED"

    def test_catching_base_exception(self) -> None:
        """Test catching specific exceptions via base class."""
        caught_errors = []

        try:
            raise GPUUnavailableError("Test")
        except ConversionError as e:
            caught_errors.append(type(e).__name__)

        try:
            raise PasswordProtectedError("Test")
        except ConversionError as e:
            caught_errors.append(type(e).__name__)

        assert len(caught_errors) == 2
        assert "GPUUnavailableError" in caught_errors
        assert "PasswordProtectedError" in caught_errors
