"""GPU availability and CUDA verification utilities."""

import logging

logger = logging.getLogger(__name__)


def check_gpu_available() -> bool:
    """
    Check if GPU is available with CUDA support.

    Verifies:
    - CUDA is available via torch.cuda.is_available()
    - CUDA version is 11.8 or later

    Returns:
        True if GPU with CUDA 11.8+ is available, False otherwise

    Logs warnings if:
    - CUDA is not available at all
    - CUDA version is less than 11.8
    """
    try:
        import torch

        if not torch.cuda.is_available():
            logger.warning("CUDA is not available. GPU acceleration disabled.")
            return False

        # Check CUDA version
        cuda_version = torch.version.cuda
        if cuda_version is None:
            logger.warning("PyTorch was built without CUDA support.")
            return False

        # Parse CUDA version (e.g., "11.8" -> 11.8)
        try:
            version_parts = cuda_version.split(".")
            major = int(version_parts[0])
            minor = int(version_parts[1]) if len(version_parts) > 1 else 0
            version = float(f"{major}.{minor}")

            if version < 11.8:
                logger.warning(
                    f"CUDA version {cuda_version} is installed, but 11.8 or later is required. "
                    "GPU acceleration may not work properly."
                )
                return False

            logger.info(f"CUDA {cuda_version} is available. GPU acceleration enabled.")
            return True

        except (ValueError, IndexError) as e:
            logger.error(f"Failed to parse CUDA version '{cuda_version}': {e}")
            return False

    except ImportError:
        logger.warning("PyTorch is not installed. GPU acceleration disabled.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking GPU availability: {e}")
        return False


def get_gpu_count() -> int:
    """
    Get the number of available GPUs.

    Returns:
        Number of GPUs available, or 0 if CUDA is not available
    """
    try:
        import torch

        if not torch.cuda.is_available():
            return 0

        return torch.cuda.device_count()

    except Exception:
        return 0


def get_gpu_name(device_id: int = 0) -> str | None:
    """
    Get the name of a specific GPU.

    Args:
        device_id: GPU device ID (default: 0)

    Returns:
        GPU name string, or None if GPU is not available
    """
    try:
        import torch

        if not torch.cuda.is_available():
            return None

        if device_id >= torch.cuda.device_count():
            logger.warning(f"GPU device {device_id} not found. Available devices: {torch.cuda.device_count()}")
            return None

        return torch.cuda.get_device_name(device_id)

    except Exception as e:
        logger.error(f"Error getting GPU name for device {device_id}: {e}")
        return None
