"""MarkerConverter implementation using Marker library."""

import logging
import time
from pathlib import Path
from typing import Any
import torch

from pdf2md_converter.base import PDFConverter
from pdf2md_converter.config import ConverterConfig
from pdf2md_converter.models.metrics import ConversionMetrics
from pdf2md_converter.exceptions import (
    ConversionError,
    PageLimitExceededError,
    PasswordProtectedError,
    CorruptedPDFError,
    GPUOutOfMemoryError,
)
from pdf2md_converter.utils.pdf_utils import (
    is_pdf_encrypted,
    validate_pdf_structure,
    get_page_count,
)

logger = logging.getLogger(__name__)


class MarkerConverter(PDFConverter):
    """Concrete implementation using Marker library for PDF to Markdown conversion."""

    def __init__(self, config: ConverterConfig) -> None:
        """
        Initialize MarkerConverter with configuration.

        Args:
            config: Converter configuration settings

        Raises:
            GPUUnavailableError: If config.gpu_enabled=True and GPU not available
        """
        super().__init__(config)
        self._initial_gpu_memory: int = 0

    def convert(self, pdf_path: Path, output_path: Path) -> ConversionMetrics:
        """
        Convert PDF to Markdown using Marker library.

        Args:
            pdf_path: Path to input PDF file
            output_path: Path to output Markdown file

        Returns:
            ConversionMetrics with performance data

        Raises:
            GPUUnavailableError: GPU required but not available
            PasswordProtectedError: PDF is password-protected
            CorruptedPDFError: PDF file is corrupted
            PageLimitExceededError: PDF has too many pages
            GPUOutOfMemoryError: GPU ran out of memory
            ConversionError: General conversion error
        """
        start_time = time.time()
        initial_gpu_memory = 0

        if self.config.gpu_enabled:
            initial_gpu_memory = torch.cuda.memory_allocated(self.config.gpu_device_id)

        try:
            # Validate inputs
            self._validate_inputs(pdf_path, output_path)

            # Track OCR time
            ocr_start_time = time.time()

            # Call Marker library
            markdown_text = self._convert_with_marker(pdf_path)

            ocr_end_time = time.time()

            # Write output
            output_path.write_text(markdown_text, encoding="utf-8")

            # Calculate metrics
            end_time = time.time()
            conversion_time = end_time - start_time
            ocr_time = ocr_end_time - ocr_start_time

            # Get GPU memory usage
            gpu_memory_used = 0.0
            peak_gpu_memory = 0.0
            if self.config.gpu_enabled:
                final_gpu_memory = torch.cuda.memory_allocated(self.config.gpu_device_id)
                gpu_memory_used = (final_gpu_memory - initial_gpu_memory) / (1024 * 1024)  # Convert to MB
                peak_gpu_memory = torch.cuda.max_memory_allocated(self.config.gpu_device_id) / (1024 * 1024)

            # Get page count
            page_count = get_page_count(pdf_path)

            # Get output file size
            output_size = output_path.stat().st_size if output_path.exists() else 0

            metrics = ConversionMetrics(
                pages_processed=page_count,
                pages_with_ocr=0,  # Will be updated in Phase 4
                images_extracted=0,  # Will be updated in Phase 5
                tables_detected=0,  # Will be updated in Phase 4
                start_time=start_time,
                end_time=end_time,
                conversion_time_seconds=conversion_time,
                ocr_time_seconds=ocr_time,
                gpu_device_id=self.config.gpu_device_id,
                gpu_memory_used_mb=gpu_memory_used,
                peak_gpu_memory_mb=peak_gpu_memory,
                cpu_time_seconds=0.0,  # Not tracked in this implementation
                output_size_bytes=output_size,
                output_path=str(output_path),
                low_confidence_pages=[],  # Will be updated in Phase 4
                errors=[],
            )

            logger.info(
                f"Conversion completed: {page_count} pages in {conversion_time:.2f}s, "
                f"GPU memory: {gpu_memory_used:.0f}MB"
            )

            return metrics

        except torch.cuda.OutOfMemoryError as e:
            logger.error(f"GPU out of memory during conversion: {e}")
            # Clean up partial output
            self._cleanup(pdf_path, output_path)
            raise GPUOutOfMemoryError("GPU ran out of memory during conversion") from e

        except (PasswordProtectedError, CorruptedPDFError, PageLimitExceededError):
            # Re-raise known exceptions as-is
            self._cleanup(pdf_path, output_path)
            raise

        except Exception as e:
            error_msg = f"Conversion failed: {e}"
            logger.error(error_msg, exc_info=True)

            # Wrap in ConversionError
            conversion_error = ConversionError(
                error_msg,
                {
                    "pdf_path": str(pdf_path),
                    "output_path": str(output_path),
                    "original_error": str(e),
                },
            )

            # Clean up partial output
            self._cleanup(pdf_path, output_path)

            raise conversion_error from e

    def _validate_inputs(self, pdf_path: Path, output_path: Path) -> None:
        """
        Validate input PDF and output path.

        Args:
            pdf_path: Path to input PDF
            output_path: Path to output Markdown

        Raises:
            FileNotFoundError: PDF file does not exist
            PermissionError: Output directory not writable
            PasswordProtectedError: PDF is encrypted
            CorruptedPDFError: PDF file structure is corrupted
            PageLimitExceededError: Page count exceeds max_pages
        """
        # Check PDF exists
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Check PDF structure
        validate_pdf_structure(pdf_path)

        # Check if encrypted
        if is_pdf_encrypted(pdf_path):
            raise PasswordProtectedError(
                f"PDF is password-protected and cannot be converted: {pdf_path}"
            )

        # Check page count
        page_count = get_page_count(pdf_path)
        if page_count > self.config.max_pages:
            raise PageLimitExceededError(page_count, self.config.max_pages)

        # Check output directory exists and is writable
        output_dir = output_path.parent
        if not output_dir.exists():
            raise FileNotFoundError(f"Output directory does not exist: {output_dir}")

        if not output_dir.is_dir():
            raise NotADirectoryError(f"Output path is not a directory: {output_dir}")

        # Test if we can write to output directory
        test_file = output_dir / f".write_test_{time.time()}.tmp"
        try:
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            raise PermissionError(f"Output directory is not writable: {output_dir}") from e

    def _convert_with_marker(self, pdf_path: Path) -> str:
        """
        Convert PDF to Markdown text using Marker library.

        Args:
            pdf_path: Path to input PDF

        Returns:
            Markdown text as string

        Raises:
            ConversionError: If Marker library conversion fails
        """
        try:
            import marker

            # Marker's convert_single_pdf expects a Path and returns a Path to the output
            # We'll use a temporary file
            import tempfile

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_output = Path(temp_dir) / pdf_path.with_suffix(".md").name

                # Call Marker's conversion function
                marker.convert_single_pdf(
                    pdf_path,
                    temp_output,
                    max_pages=self.config.max_pages,
                    ocr_all_pages=self.config.ocr_all_pages,
                )

                # Read the generated Markdown
                markdown_text = temp_output.read_text(encoding="utf-8")

                return markdown_text

        except ImportError as e:
            raise ConversionError(
                "Marker library is not installed",
                {"install_command": "uv add marker-pdf", "original_error": str(e)},
            ) from e
        except Exception as e:
            raise ConversionError(
                f"Marker library conversion failed: {e}",
                {"pdf_path": str(pdf_path), "original_error": str(e)},
            ) from e

    def _cleanup(self, pdf_path: Path, output_path: Path) -> None:
        """
        Clean up temporary files on error or success.

        Args:
            pdf_path: Input PDF path (not deleted)
            output_path: Output Markdown path (deleted on error)
        """
        if output_path.exists():
            try:
                output_path.unlink()
                logger.info(f"Cleaned up partial output file: {output_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up output file {output_path}: {e}")
