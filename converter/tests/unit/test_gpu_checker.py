"""Unit tests for GPU checker with mocked torch.cuda."""

import pytest
from unittest.mock import patch, MagicMock
from pdf2md_converter.ocr.gpu_checker import check_gpu_available, get_gpu_count, get_gpu_name


class TestCheckGPUAvailable:
    """Test GPU availability checking."""

    @patch("pdf2md_converter.ocr.gpu_checker.torch")
    def test_cuda_not_available(self, mock_torch: MagicMock) -> None:
        """Test returns False when CUDA is not available."""
        mock_torch.cuda.is_available.return_value = False

        result = check_gpu_available()

        assert result is False
        mock_torch.cuda.is_available.assert_called_once()

    @patch("pdf2md_converter.ocr.gpu_checker.torch")
    def test_cuda_available_with_version_11_8(self, mock_torch: MagicMock) -> None:
        """Test returns True for CUDA 11.8."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.version.cuda = "11.8"

        result = check_gpu_available()

        assert result is True

    @patch("pdf2md_converter.ocr.gpu_checker.torch")
    def test_cuda_available_with_version_12_0(self, mock_torch: MagicMock) -> None:
        """Test returns True for CUDA 12.0."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.version.cuda = "12.0"

        result = check_gpu_available()

        assert result is True

    @patch("pdf2md_converter.ocr.gpu_checker.torch")
    def test_cuda_available_with_version_12_9(self, mock_torch: MagicMock) -> None:
        """Test returns True for CUDA 12.9."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.version.cuda = "12.9"

        result = check_gpu_available()

        assert result is True

    @patch("pdf2md_converter.ocr.gpu_checker.torch")
    def test_cuda_version_too_low(self, mock_torch: MagicMock) -> None:
        """Test returns False for CUDA version < 11.8."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.version.cuda = "11.7"

        result = check_gpu_available()

        assert result is False

    @patch("pdf2md_converter.ocr.gpu_checker.torch")
    def test_cuda_version_10_x(self, mock_torch: MagicMock) -> None:
        """Test returns False for CUDA 10.x."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.version.cuda = "10.2"

        result = check_gpu_available()

        assert result is False

    @patch("pdf2md_converter.ocr.gpu_checker.torch")
    def test_pytorch_not_installed(self, mock_torch: MagicMock) -> None:
        """Test returns False when PyTorch import fails."""
        # Simulate ImportError
        mock_torch.cuda.is_available.side_effect = ImportError("No module named 'torch'")

        result = check_gpu_available()

        assert result is False

    @patch("pdf2md_converter.ocr.gpu_checker.torch", None)
    def test_torch_not_available(self) -> None:
        """Test returns False when torch module is not available."""
        with patch("pdf2md_converter.ocr.gpu_checker.logger"):
            # Torch is None, so import will fail
            result = check_gpu_available()
            assert result is False

    @patch("pdf2md_converter.ocr.gpu_checker.torch")
    def test_cuda_version_none(self, mock_torch: MagicMock) -> None:
        """Test returns False when CUDA version is None (CPU-only PyTorch)."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.version.cuda = None

        result = check_gpu_available()

        assert result is False

    @patch("pdf2md_converter.ocr.gpu_checker.torch")
    def test_cuda_version_invalid_format(self, mock_torch: MagicMock) -> None:
        """Test returns False when CUDA version string is invalid."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.version.cuda = "invalid"

        result = check_gpu_available()

        assert result is False

    @patch("pdf2md_converter.ocr.gpu_checker.torch")
    def test_cuda_version_without_minor(self, mock_torch: MagicMock) -> None:
        """Test handles CUDA version without minor number (e.g., '12')."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.version.cuda = "12"

        result = check_gpu_available()

        # Version 12.0 should pass (>= 11.8)
        assert result is True


class TestGetGPUCount:
    """Test getting GPU count."""

    @patch("pdf2md_converter.ocr.gpu_checker.torch")
    def test_no_gpus(self, mock_torch: MagicMock) -> None:
        """Test returns 0 when CUDA is not available."""
        mock_torch.cuda.is_available.return_value = False

        result = get_gpu_count()

        assert result == 0

    @patch("pdf2md_converter.ocr.gpu_checker.torch")
    def test_single_gpu(self, mock_torch: MagicMock) -> None:
        """Test returns 1 for single GPU system."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 1

        result = get_gpu_count()

        assert result == 1
        mock_torch.cuda.device_count.assert_called_once()

    @patch("pdf2md_converter.ocr.gpu_checker.torch")
    def test_dual_gpu(self, mock_torch: MagicMock) -> None:
        """Test returns 2 for dual GPU system."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 2

        result = get_gpu_count()

        assert result == 2

    @patch("pdf2md_converter.ocr.gpu_checker.torch")
    def test_exception_handling(self, mock_torch: MagicMock) -> None:
        """Test returns 0 on exception."""
        mock_torch.cuda.is_available.side_effect = RuntimeError("CUDA error")

        result = get_gpu_count()

        assert result == 0


class TestGetGPUName:
    """Test getting GPU name."""

    @patch("pdf2md_converter.ocr.gpu_checker.torch")
    def test_gpu_not_available(self, mock_torch: MagicMock) -> None:
        """Test returns None when CUDA is not available."""
        mock_torch.cuda.is_available.return_value = False

        result = get_gpu_name()

        assert result is None

    @patch("pdf2md_converter.ocr.gpu_checker.torch")
    def test_get_default_gpu_name(self, mock_torch: MagicMock) -> None:
        """Test gets name of default GPU (device_id=0)."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 2
        mock_torch.cuda.get_device_name.return_value = "NVIDIA GeForce RTX 4090"

        result = get_gpu_name()

        assert result == "NVIDIA GeForce RTX 4090"
        mock_torch.cuda.get_device_name.assert_called_with(0)

    @patch("pdf2md_converter.ocr.gpu_checker.torch")
    def test_get_second_gpu_name(self, mock_torch: MagicMock) -> None:
        """Test gets name of second GPU (device_id=1)."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 2
        mock_torch.cuda.get_device_name.return_value = "NVIDIA GeForce RTX 4090"

        result = get_gpu_name(device_id=1)

        assert result == "NVIDIA GeForce RTX 4090"
        mock_torch.cuda.get_device_name.assert_called_with(1)

    @patch("pdf2md_converter.ocr.gpu_checker.torch")
    def test_invalid_device_id(self, mock_torch: MagicMock) -> None:
        """Test returns None for invalid device_id."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 1

        result = get_gpu_name(device_id=5)

        assert result is None

    @patch("pdf2md_converter.ocr.gpu_checker.torch")
    def test_exception_handling(self, mock_torch: MagicMock) -> None:
        """Test returns None on exception."""
        mock_torch.cuda.is_available.side_effect = RuntimeError("CUDA error")

        result = get_gpu_name()

        assert result is None
