"""Unit tests for image downscaling utilities."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image
from pdf2md_converter.utils.image_utils import downscale_image


class TestDownscaleImage:
    """Test image downscaling functionality."""

    @patch("pdf2md_converter.utils.image_utils.Image.open")
    @patch("pdf2md_converter.utils.image_utils.Path.exists", return_value=True)
    def test_image_below_threshold_no_scaling(
        self, mock_exists: MagicMock, mock_image_open: MagicMock, tmp_path: Path
    ) -> None:
        """Test returns False when image width is below threshold."""
        # Create mock image with width 1000 (below threshold of 2000)
        mock_img = MagicMock()
        mock_img.size = (1000, 800)
        mock_img.format = "JPEG"
        mock_image_open.return_value.__enter__.return_value = mock_img

        input_path = Path("input.jpg")
        output_path = tmp_path / "output.jpg"

        result = downscale_image(input_path, output_path, max_width=2000)

        assert result is False
        # Image should still be saved (copied) since paths differ
        mock_img.save.assert_called_once()

    @patch("pdf2md_converter.utils.image_utils.Image.open")
    @patch("pdf2md_converter.utils.image_utils.Path.exists", return_value=True)
    def test_image_at_threshold_no_scaling(
        self, mock_exists: MagicMock, mock_image_open: MagicMock, tmp_path: Path
    ) -> None:
        """Test returns False when image width equals threshold."""
        # Create mock image with width 2000 (exactly at threshold)
        mock_img = MagicMock()
        mock_img.size = (2000, 1600)
        mock_img.format = "PNG"
        mock_image_open.return_value.__enter__.return_value = mock_img

        input_path = Path("input.png")
        output_path = tmp_path / "output.png"

        result = downscale_image(input_path, output_path, max_width=2000)

        assert result is False

    @patch("pdf2md_converter.utils.image_utils.Image.open")
    @patch("pdf2md_converter.utils.image_utils.Path.exists", return_value=True)
    def test_image_above_threshold_downscaled(
        self, mock_exists: MagicMock, mock_image_open: MagicMock, tmp_path: Path
    ) -> None:
        """Test downscales image when width exceeds threshold."""
        # Create mock image with width 3000 (above threshold of 2000)
        mock_img_original = MagicMock()
        mock_img_original.size = (3000, 2000)
        mock_img_original.format = "JPEG"

        # Create mock for downscaled image
        mock_img_downscaled = MagicMock()
        mock_img_original.resize.return_value = mock_img_downscaled

        mock_image_open.return_value.__enter__.return_value = mock_img_original

        input_path = Path("input.jpg")
        output_path = tmp_path / "output.jpg"

        result = downscale_image(input_path, output_path, max_width=2000)

        assert result is True
        # Verify resize was called with correct dimensions
        mock_img_original.resize.assert_called_once()
        args, _ = mock_img_original.resize.call_args
        assert args[0] == (2000, 1333)  # 2000 width, 1333 height (preserved aspect ratio)

        # Verify LANCZOS resampling was used
        _, kwargs = mock_img_original.resize.call_args
        assert "resample" in kwargs or len(args) > 1

    @patch("pdf2md_converter.utils.image_utils.Image.open")
    @patch("pdf2md_converter.utils.image_utils.Path.exists", return_value=True)
    def test_aspect_ratio_preservation(
        self, mock_exists: MagicMock, mock_image_open: MagicMock, tmp_path: Path
    ) -> None:
        """Test aspect ratio is preserved during downscaling."""
        # Create mock image with width 4000 and height 3000 (4:3 ratio)
        mock_img = MagicMock()
        mock_img.size = (4000, 3000)
        mock_img.format = "JPEG"
        mock_img_downscaled = MagicMock()
        mock_img.resize.return_value = mock_img_downscaled

        mock_image_open.return_value.__enter__.return_value = mock_img

        input_path = Path("input.jpg")
        output_path = tmp_path / "output.jpg"

        downscale_image(input_path, output_path, max_width=2000)

        # Check that resize preserves aspect ratio
        args, _ = mock_img.resize.call_args
        new_width, new_height = args[0]

        # Original ratio: 3000/4000 = 0.75
        # New ratio should also be ~0.75
        original_ratio = 3000 / 4000
        new_ratio = new_height / new_width

        assert abs(original_ratio - new_ratio) < 0.01  # Allow small floating point errors
        assert new_width == 2000
        assert new_height == 1500  # 2000 * 0.75

    @patch("pdf2md_converter.utils.image_utils.Image.open")
    @patch("pdf2md_converter.utils.image_utils.Path.exists", return_value=True)
    def test_format_preservation_jpeg(
        self, mock_exists: MagicMock, mock_image_open: MagicMock, tmp_path: Path
    ) -> None:
        """Test JPEG format is preserved."""
        mock_img = MagicMock()
        mock_img.size = (3000, 2000)
        mock_img.format = "JPEG"
        mock_img_downscaled = MagicMock()
        mock_img.resize.return_value = mock_img_downscaled

        mock_image_open.return_value.__enter__.return_value = mock_img

        input_path = Path("input.jpg")
        output_path = tmp_path / "output.jpg"

        downscale_image(input_path, output_path, max_width=2000)

        # Verify format is preserved
        mock_img_downscaled.save.assert_called_once()
        args, kwargs = mock_img_downscaled.save.call_args
        assert "format" in kwargs
        assert kwargs["format"] == "JPEG"

    @patch("pdf2md_converter.utils.image_utils.Image.open")
    @patch("pdf2md_converter.utils.image_utils.Path.exists", return_value=True)
    def test_format_preservation_png(
        self, mock_exists: MagicMock, mock_image_open: MagicMock, tmp_path: Path
    ) -> None:
        """Test PNG format is preserved."""
        mock_img = MagicMock()
        mock_img.size = (3000, 2000)
        mock_img.format = "PNG"
        mock_img_downscaled = MagicMock()
        mock_img.resize.return_value = mock_img_downscaled

        mock_image_open.return_value.__enter__.return_value = mock_img

        input_path = Path("input.png")
        output_path = tmp_path / "output.png"

        downscale_image(input_path, output_path, max_width=2000)

        # Verify format is preserved
        mock_img_downscaled.save.assert_called_once()
        args, kwargs = mock_img_downscaled.save.call_args
        assert kwargs["format"] == "PNG"

    @patch("pdf2md_converter.utils.image_utils.Path.exists", return_value=False)
    def test_file_not_found(self, mock_exists: MagicMock) -> None:
        """Test raises FileNotFoundError for missing input file."""
        with pytest.raises(FileNotFoundError, match="Image file not found"):
            downscale_image(Path("missing.jpg"), Path("output.jpg"), max_width=2000)

    @patch("pdf2md_converter.utils.image_utils.Image.open")
    @patch("pdf2md_converter.utils.image_utils.Path.exists", return_value=True)
    def test_invalid_image(
        self, mock_exists: MagicMock, mock_image_open: MagicMock, tmp_path: Path
    ) -> None:
        """Test raises ValueError for invalid image."""
        mock_image_open.side_effect = Exception("Cannot identify image file")

        with pytest.raises(ValueError, match="Invalid or corrupted image file"):
            downscale_image(Path("invalid.jpg"), Path("output.jpg"), max_width=2000)

    @patch("pdf2md_converter.utils.image_utils.Image.open")
    @patch("pdf2md_converter.utils.image_utils.Path.exists", return_value=True)
    def test_very_wide_image(
        self, mock_exists: MagicMock, mock_image_open: MagicMock, tmp_path: Path
    ) -> None:
        """Test downscaling very wide panoramic image."""
        mock_img = MagicMock()
        mock_img.size = (10000, 1000)  # Very wide 10:1 ratio
        mock_img.format = "JPEG"
        mock_img_downscaled = MagicMock()
        mock_img.resize.return_value = mock_img_downscaled

        mock_image_open.return_value.__enter__.return_value = mock_img

        input_path = Path("panorama.jpg")
        output_path = tmp_path / "output.jpg"

        result = downscale_image(input_path, output_path, max_width=2000)

        assert result is True
        args, _ = mock_img.resize.call_args
        new_width, new_height = args[0]

        # Should preserve 10:1 ratio
        assert new_width == 2000
        assert new_height == 200  # 2000 * (1000/10000)

    @patch("pdf2md_converter.utils.image_utils.Image.open")
    @patch("pdf2md_converter.utils.image_utils.Path.exists", return_value=True)
    def test_very_tall_image(
        self, mock_exists: MagicMock, mock_image_open: MagicMock, tmp_path: Path
    ) -> None:
        """Test downscaling very tall portrait image."""
        mock_img = MagicMock()
        mock_img.size = (2000, 8000)  # Very tall 1:4 ratio
        mock_img.format = "PNG"
        mock_img_downscaled = MagicMock()
        mock_img.resize.return_value = mock_img_downscaled

        mock_image_open.return_value.__enter__.return_value = mock_img

        input_path = Path("tall.png")
        output_path = tmp_path / "output.png"

        result = downscale_image(input_path, output_path, max_width=1500)

        assert result is True
        args, _ = mock_img.resize.call_args
        new_width, new_height = args[0]

        # Should preserve 1:4 ratio
        assert new_width == 1500
        assert new_height == 6000  # 1500 * (8000/2000)
