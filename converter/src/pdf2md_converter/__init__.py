"""PDF2MD Converter - GPU-accelerated PDF to Markdown conversion library."""

from pdf2md_converter.base import PDFConverter
from pdf2md_converter.config import ConverterConfig
from pdf2md_converter.exceptions import (
    ConversionError,
    CorruptedPDFError,
    GPUOutOfMemoryError,
    GPUUnavailableError,
    PageLimitExceededError,
    PasswordProtectedError,
)
from pdf2md_converter.marker_converter import MarkerConverter
from pdf2md_converter.models.metrics import ConversionMetrics

__all__ = [
    # Configuration
    "ConverterConfig",
    # Converters
    "PDFConverter",
    "MarkerConverter",
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
