"""Exception hierarchy for PDF conversion errors."""


class ConversionError(Exception):
    """Base exception for all conversion errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        """
        Initialize conversion error.

        Args:
            message: Human-readable error message
            details: Optional dict with additional error context
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return string representation including details."""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class GPUUnavailableError(ConversionError):
    """GPU required but not available or CUDA not installed."""

    def __init__(self, message: str = "GPU required but not available") -> None:
        super().__init__(message, {"error_code": "GPU_UNAVAILABLE"})


class PasswordProtectedError(ConversionError):
    """PDF is password-protected and cannot be converted."""

    def __init__(self, message: str = "PDF is password-protected") -> None:
        super().__init__(message, {"error_code": "PASSWORD_PROTECTED"})


class CorruptedPDFError(ConversionError):
    """PDF file structure is corrupted or invalid."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        default_details = {"error_code": "CORRUPTED_PDF"}
        if details:
            default_details.update(details)
        super().__init__(message, default_details)


class GPUOutOfMemoryError(ConversionError):
    """GPU ran out of memory during conversion."""

    def __init__(self, message: str = "GPU out of memory") -> None:
        super().__init__(message, {"error_code": "GPU_OOM"})


class PageLimitExceededError(ConversionError):
    """PDF page count exceeds maximum allowed."""

    def __init__(self, page_count: int, max_pages: int) -> None:
        message = f"PDF has {page_count} pages, exceeds maximum of {max_pages}"
        super().__init__(
            message,
            {"error_code": "PAGE_LIMIT_EXCEEDED", "page_count": page_count, "max_pages": max_pages}
        )

