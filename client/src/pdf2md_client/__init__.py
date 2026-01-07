"""PDF2md Client - Convert PDF files to Markdown using a remote GPU server.

This package provides a command-line interface for converting PDF files
to Markdown format using a remote GPU-enabled server.
"""

from pdf2md_client.config import ConversionOptions, ConversionResult, ServerConfig
from pdf2md_client.config_manager import ConfigManager
from pdf2md_client.exceptions import (
    ConfigError,
    ConversionError,
    NetworkError,
    PDF2MDError,
    ValidationError,
)
from pdf2md_client.output import CLIOutput

__version__ = "1.0.0"
__all__ = [
    "ServerConfig",
    "ConfigManager",
    "ConversionOptions",
    "ConversionResult",
    "PDF2MDError",
    "NetworkError",
    "ValidationError",
    "ConversionError",
    "ConfigError",
    "CLIOutput",
    "__version__",
]
