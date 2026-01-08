"""PDF2MD Converter - GPU-accelerated PDF to Markdown conversion library."""

from pdf2md_converter.config import ConverterConfig
from pdf2md_converter.base import PDFConverter
from pdf2md_converter.models.metrics import ConversionMetrics
from pdf2md_converter.exceptions import (
    ConversionError,
    GPUUnavailableError,
    PasswordProtectedError,
    CorruptedPDFError,
    GPUOutOfMemoryError,
    PageLimitExceededError,
)

__all__ = [
    # Configuration
    "ConverterConfig",
    # Base classes
    "PDFConverter",
    # Models
    "ConversionMetrics",
    # Exceptions
    "ConversionError",
    "GPUUnavailableError",
    "PasswordProtectedError",
    "CorruptedPDFError",
    "GPUOutOfMemoryError",
    "PageLimitExceededError",
]

__version__ = "0.1.0"
