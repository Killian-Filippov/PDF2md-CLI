"""Performance metrics for PDF conversion."""

from dataclasses import dataclass


@dataclass
class ConversionMetrics:
    """Performance metrics for PDF conversion."""

    # Conversion Results
    pages_processed: int
    pages_with_ocr: int
    images_extracted: int
    tables_detected: int

    # Timing
    start_time: float
    end_time: float
    conversion_time_seconds: float
    ocr_time_seconds: float

    # Resource Usage
    gpu_device_id: int  # GPU device ID used for conversion
    gpu_memory_used_mb: float
    peak_gpu_memory_mb: float
    cpu_time_seconds: float

    # Output
    output_size_bytes: int
    output_path: str

    # Errors
    low_confidence_pages: list[int]  # Page numbers with OCR confidence < threshold
    errors: list[str]  # Non-fatal errors encountered

    @property
    def elapsed_time(self) -> float:
        """Total elapsed time in seconds."""
        return self.end_time - self.start_time

    @property
    def pages_per_second(self) -> float:
        """Conversion throughput (pages per second)."""
        return self.pages_processed / self.conversion_time_seconds if self.conversion_time_seconds > 0 else 0.0
