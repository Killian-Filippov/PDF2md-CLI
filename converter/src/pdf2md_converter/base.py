"""Abstract base class for PDF to Markdown converters."""

from abc import ABC, abstractmethod
from pathlib import Path
from pdf2md_converter.config import ConverterConfig
from pdf2md_converter.models.metrics import ConversionMetrics
from pdf2md_converter.exceptions import GPUUnavailableError


class PDFConverter(ABC):
    """Abstract base class for PDF to Markdown converters."""

    def __init__(self, config: ConverterConfig) -> None:
        """
        Initialize converter with configuration.

        Args:
            config: Converter configuration settings

        Raises:
            GPUUnavailableError: If config.gpu_enabled=True and GPU not available
        """
        self.config = config
        self._validate_gpu_availability()

    @abstractmethod
    def convert(self, pdf_path: Path, output_path: Path) -> ConversionMetrics:
        """
        Convert PDF to Markdown.

        This is the primary conversion method. It:
        1. Validates inputs (PDF exists, output path writable)
        2. Extracts text structure (headings, lists, tables)
        3. Applies OCR if enabled (GPU-accelerated)
        4. Extracts and downscales images
        5. Writes Markdown to output_path
        6. Returns performance metrics

        Args:
            pdf_path: Path to input PDF file (must exist)
            output_path: Path to output Markdown file (parent must exist)

        Returns:
            ConversionMetrics with performance data:
                - pages_processed: Number of pages converted
                - conversion_time_seconds: Total conversion time
                - gpu_memory_used_mb: GPU memory consumed (0 if GPU not used)
                - images_extracted: Number of images extracted
                - low_confidence_pages: List of page numbers with OCR confidence < threshold

        Raises:
            GPUUnavailableError: GPU required but not available
            PasswordProtectedError: PDF is password-protected (reject immediately)
            CorruptedPDFError: PDF file structure is corrupted
            ConversionError: General conversion error with details
        """
        pass

    def _validate_gpu_availability(self) -> None:
        """Validate GPU availability if gpu_enabled=True."""
        if self.config.gpu_enabled:
            from pdf2md_converter.ocr.gpu_checker import check_gpu_available

            if not check_gpu_available():
                raise GPUUnavailableError(
                    f"GPU required but not available (config.gpu_enabled=True, gpu_device_id={self.config.gpu_device_id}). "
                    "Install CUDA 11.8+ or set gpu_enabled=False."
                )

    @abstractmethod
    def _validate_inputs(self, pdf_path: Path, output_path: Path) -> None:
        """
        Validate input PDF and output path.

        Checks:
        - PDF file exists
        - PDF file is readable
        - Output directory exists and is writable
        - PDF is not password-protected (fast fail)
        - PDF page count <= max_pages

        Raises:
            FileNotFoundError: PDF file does not exist
            PermissionError: Output directory not writable
            PasswordProtectedError: PDF is encrypted
            ValueError: Page count exceeds max_pages
        """
        pass

    @abstractmethod
    def _cleanup(self, pdf_path: Path, output_path: Path) -> None:
        """
        Clean up temporary files on error or success.

        Args:
            pdf_path: Input PDF path (not deleted, only referenced)
            output_path: Output Markdown path (deleted on error)

        Note:
            Called on both success and error paths to ensure
            no partial files remain on disk.
        """
        pass
