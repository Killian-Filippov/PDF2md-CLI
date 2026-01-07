"""PDF2md Client exception hierarchy.

This module defines all custom exceptions used by the PDF2md client,
with specific exit codes for CLI error handling.
"""

from typing import Optional


class PDF2MDError(Exception):
    """Base exception for all PDF2md client errors.

    All custom exceptions inherit from this base class.
    Subclasses should define a default exit code for CLI error handling.
    """

    def __init__(
        self,
        message: str,
        exit_code: int = 1,
        troubleshooting: Optional[list[str]] = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message
            exit_code: CLI exit code (0-5, 130 for SIGINT)
            troubleshooting: Optional list of troubleshooting hints
        """
        self.message = message
        self.exit_code = exit_code
        self.troubleshooting = troubleshooting or []
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return string representation with troubleshooting hints."""
        output = [self.message]
        if self.troubleshooting:
            output.append("\nTroubleshooting:")
            for i, hint in enumerate(self.troubleshooting, 1):
                output.append(f"  {i}. {hint}")
        return "\n".join(output)


class NetworkError(PDF2MDError):
    """Network-related errors (connection failures, timeouts, etc.).

    Exit code: 2
    """

    def __init__(
        self,
        message: str,
        troubleshooting: Optional[list[str]] = None,
    ) -> None:
        """Initialize network error.

        Args:
            message: Human-readable error message
            troubleshooting: Optional list of troubleshooting hints
        """
        default_hints = [
            "Check if the server is running on the remote machine",
            "Verify the server URL in ~/.pdf2md/config.json",
            "Test network connectivity: ping <server_host>",
            "Check firewall settings on both machines",
        ]
        super().__init__(
            message=message,
            exit_code=2,
            troubleshooting=troubleshooting or default_hints,
        )


class ValidationError(PDF2MDError):
    """Input validation errors (file not found, invalid format, etc.).

    Exit code: 3
    """

    def __init__(
        self,
        message: str,
        troubleshooting: Optional[list[str]] = None,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Human-readable error message
            troubleshooting: Optional list of troubleshooting hints
        """
        default_hints = [
            "Check if the file path is correct",
            "Use absolute paths if relative paths don't work",
            "Ensure the file extension is .pdf",
            "Verify the file is not corrupted",
        ]
        super().__init__(
            message=message,
            exit_code=3,
            troubleshooting=troubleshooting or default_hints,
        )


class ConversionError(PDF2MDError):
    """PDF conversion errors (server-side processing failures).

    Exit code: 4
    """

    def __init__(
        self,
        message: str,
        troubleshooting: Optional[list[str]] = None,
    ) -> None:
        """Initialize conversion error.

        Args:
            message: Human-readable error message
            troubleshooting: Optional list of troubleshooting hints
        """
        default_hints = [
            "The PDF might be too large or contain many high-res images",
            "Try converting a smaller file first",
            "Check server logs for detailed error information",
            "Ensure GPU is available on the server",
        ]
        super().__init__(
            message=message,
            exit_code=4,
            troubleshooting=troubleshooting or default_hints,
        )


class ConfigError(PDF2MDError):
    """Configuration-related errors (invalid config, corrupted file, etc.).

    Exit code: 5
    """

    def __init__(
        self,
        message: str,
        troubleshooting: Optional[list[str]] = None,
    ) -> None:
        """Initialize configuration error.

        Args:
            message: Human-readable error message
            troubleshooting: Optional list of troubleshooting hints
        """
        default_hints = [
            "Run 'pdf2md config init' to create a new configuration",
            "Check if ~/.pdf2md/config.json is valid JSON",
            "Corrupted config files are automatically backed up with timestamp",
            "Ensure you have write permissions for the config directory",
        ]
        super().__init__(
            message=message,
            exit_code=5,
            troubleshooting=troubleshooting or default_hints,
        )
