"""Unit tests for ConverterConfig and ConversionMetrics."""

import pytest
from pathlib import Path
from pdf2md_converter.config import ConverterConfig
from pdf2md_converter.models.metrics import ConversionMetrics
from pydantic import ValidationError


class TestConverterConfig:
    """Test ConverterConfig validation."""

    def test_default_config(self) -> None:
        """Test creating config with all defaults."""
        config = ConverterConfig()

        assert config.ocr_enabled is True
        assert config.ocr_all_pages is True
        assert config.gpu_enabled is True
        assert config.gpu_device_id == 0
        assert config.gpu_memory_limit_mb == 4096
        assert config.max_pages == 500
        assert config.timeout_seconds == 300
        assert config.extract_images is True
        assert config.image_downscale_threshold == 2000
        assert config.ocr_confidence_threshold == 0.5
        assert config.languages == ["en", "zh"]

    def test_custom_config(self) -> None:
        """Test creating config with custom values."""
        config = ConverterConfig(
            gpu_enabled=False,
            max_pages=100,
            gpu_device_id=1,
            ocr_confidence_threshold=0.7
        )

        assert config.gpu_enabled is False
        assert config.max_pages == 100
        assert config.gpu_device_id == 1
        assert config.ocr_confidence_threshold == 0.7

    def test_gpu_memory_limit_validation(self) -> None:
        """Test gpu_memory_limit_mb constraints (100 to 16384)."""
        # Valid values
        ConverterConfig(gpu_memory_limit_mb=100)
        ConverterConfig(gpu_memory_limit_mb=16384)

        # Too low
        with pytest.raises(ValidationError):
            ConverterConfig(gpu_memory_limit_mb=99)

        # Too high
        with pytest.raises(ValidationError):
            ConverterConfig(gpu_memory_limit_mb=16385)

    def test_max_pages_validation(self) -> None:
        """Test max_pages constraints (1 to 1000)."""
        # Valid values
        ConverterConfig(max_pages=1)
        ConverterConfig(max_pages=1000)

        # Too low (PositiveInt enforces >= 1, but double-check upper bound)
        with pytest.raises(ValidationError):
            ConverterConfig(max_pages=1001)

    def test_ocr_confidence_threshold_validation(self) -> None:
        """Test ocr_confidence_threshold constraints (0.0 to 1.0)."""
        # Valid values
        ConverterConfig(ocr_confidence_threshold=0.0)
        ConverterConfig(ocr_confidence_threshold=0.5)
        ConverterConfig(ocr_confidence_threshold=1.0)

        # Too low
        with pytest.raises(ValidationError):
            ConverterConfig(ocr_confidence_threshold=-0.1)

        # Too high
        with pytest.raises(ValidationError):
            ConverterConfig(ocr_confidence_threshold=1.1)

    def test_image_downscale_threshold_validation(self) -> None:
        """Test image_downscale_threshold constraints (>= 100)."""
        # Valid value
        ConverterConfig(image_downscale_threshold=100)

        # Too low
        with pytest.raises(ValidationError):
            ConverterConfig(image_downscale_threshold=99)

    def test_gpu_device_id_validation(self) -> None:
        """Test gpu_device_id constraints (>= 0)."""
        # Valid values
        ConverterConfig(gpu_device_id=0)
        ConverterConfig(gpu_device_id=1)
        ConverterConfig(gpu_device_id=2)

        # Negative
        with pytest.raises(ValidationError):
            ConverterConfig(gpu_device_id=-1)

    def test_languages_validation(self) -> None:
        """Test languages list cannot be empty."""
        # Valid
        ConverterConfig(languages=["en"])
        ConverterConfig(languages=["en", "zh", "fr"])

        # Empty list
        with pytest.raises(ValidationError, match="languages list cannot be empty"):
            ConverterConfig(languages=[])

    def test_output_directory_type(self) -> None:
        """Test output_directory is a Path object."""
        config = ConverterConfig()
        assert isinstance(config.output_directory, Path)
        assert config.output_directory == Path("/tmp/pdf2md_output")

        # Custom path
        custom_path = Path("/custom/output")
        config = ConverterConfig(output_directory=custom_path)
        assert config.output_directory == custom_path


class TestConversionMetrics:
    """Test ConversionMetrics dataclass."""

    def test_create_metrics(self) -> None:
        """Test creating metrics with all fields."""
        metrics = ConversionMetrics(
            pages_processed=10,
            pages_with_ocr=5,
            images_extracted=3,
            tables_detected=2,
            start_time=0.0,
            end_time=15.0,
            conversion_time_seconds=15.0,
            ocr_time_seconds=8.0,
            gpu_device_id=0,
            gpu_memory_used_mb=2048.0,
            peak_gpu_memory_mb=2500.0,
            cpu_time_seconds=7.0,
            output_size_bytes=1024,
            output_path="/tmp/output.md",
            low_confidence_pages=[3, 7],
            errors=[]
        )

        assert metrics.pages_processed == 10
        assert metrics.pages_with_ocr == 5
        assert metrics.images_extracted == 3
        assert metrics.tables_detected == 2
        assert metrics.gpu_device_id == 0

    def test_elapsed_time_property(self) -> None:
        """Test elapsed_time property calculation."""
        metrics = ConversionMetrics(
            pages_processed=1,
            pages_with_ocr=0,
            images_extracted=0,
            tables_detected=0,
            start_time=100.0,
            end_time=115.5,
            conversion_time_seconds=15.5,
            ocr_time_seconds=0.0,
            gpu_device_id=0,
            gpu_memory_used_mb=0.0,
            peak_gpu_memory_mb=0.0,
            cpu_time_seconds=15.5,
            output_size_bytes=100,
            output_path="/tmp/test.md",
            low_confidence_pages=[],
            errors=[]
        )

        assert metrics.elapsed_time == 15.5

    def test_pages_per_second_property(self) -> None:
        """Test pages_per_second property calculation."""
        # Normal case
        metrics = ConversionMetrics(
            pages_processed=10,
            pages_with_ocr=5,
            images_extracted=0,
            tables_detected=0,
            start_time=0.0,
            end_time=20.0,
            conversion_time_seconds=20.0,
            ocr_time_seconds=10.0,
            gpu_device_id=0,
            gpu_memory_used_mb=2048.0,
            peak_gpu_memory_mb=2500.0,
            cpu_time_seconds=10.0,
            output_size_bytes=1000,
            output_path="/tmp/test.md",
            low_confidence_pages=[],
            errors=[]
        )

        assert metrics.pages_per_second == 0.5  # 10 pages / 20 seconds

    def test_pages_per_second_zero_time(self) -> None:
        """Test pages_per_second when conversion_time_seconds is 0."""
        metrics = ConversionMetrics(
            pages_processed=5,
            pages_with_ocr=0,
            images_extracted=0,
            tables_detected=0,
            start_time=0.0,
            end_time=0.0,
            conversion_time_seconds=0.0,
            ocr_time_seconds=0.0,
            gpu_device_id=0,
            gpu_memory_used_mb=0.0,
            peak_gpu_memory_mb=0.0,
            cpu_time_seconds=0.0,
            output_size_bytes=100,
            output_path="/tmp/test.md",
            low_confidence_pages=[],
            errors=[]
        )

        # Should return 0.0 to avoid division by zero
        assert metrics.pages_per_second == 0.0

    def test_metrics_with_errors(self) -> None:
        """Test metrics with non-fatal errors."""
        metrics = ConversionMetrics(
            pages_processed=3,
            pages_with_ocr=0,
            images_extracted=0,
            tables_detected=0,
            start_time=0.0,
            end_time=5.0,
            conversion_time_seconds=5.0,
            ocr_time_seconds=0.0,
            gpu_device_id=1,
            gpu_memory_used_mb=1024.0,
            peak_gpu_memory_mb=1200.0,
            cpu_time_seconds=5.0,
            output_size_bytes=500,
            output_path="/tmp/test.md",
            low_confidence_pages=[2],
            errors=["Low OCR confidence on page 2", "Image extraction failed on page 3"]
        )

        assert len(metrics.errors) == 2
        assert metrics.low_confidence_pages == [2]
        assert metrics.gpu_device_id == 1
