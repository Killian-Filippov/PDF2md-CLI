"""PDF2md Client CLI output wrapper using Rich.

Provides consistent, cross-platform terminal output with colors,
progress bars, and Unicode support.
"""

import sys

from rich.console import Console
from rich.theme import Theme

# Custom theme for consistent styling
THEME = Theme(
    {
        "success": "green bold",
        "error": "red bold",
        "warning": "yellow bold",
        "info": "blue bold",
        "dim": "dim",
    }
)


class CLIOutput:
    """Wrapper for Rich console output.

    Provides consistent output formatting with automatic Unicode
    support detection and fallback to ASCII symbols.
    """

    def __init__(self, verbose: bool = False) -> None:
        """Initialize CLI output wrapper.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self.unicode_supported = self._detect_unicode_support()

        # Initialize Rich console
        self.console = Console(theme=THEME)

        # Fallback symbols for legacy terminals
        self.symbols = {
            "check": "✓" if self.unicode_supported else "[OK]",
            "cross": "✗" if self.unicode_supported else "[X]",
            "arrow": "→" if self.unicode_supported else "->",
            "bullet": "•" if self.unicode_supported else "*",
        }

    @staticmethod
    def _detect_unicode_support() -> bool:
        """Detect if terminal supports Unicode.

        Returns:
            True if Unicode is supported, False for ASCII fallback
        """
        # Check if we're on Windows and not in a modern terminal
        if sys.platform == "win32":
            # Windows Terminal, PowerShell, and modern cmd.exe support Unicode
            # Legacy cmd.exe does not
            try:
                import ctypes

                # Check if using Windows Terminal or modern console
                kernel32 = ctypes.windll.kernel32
                kernel32.GetConsoleMode(kernel32.GetStdHandle(-11), ctypes.byref(ctypes.c_uint()))
                return True
            except Exception:
                return False

        # Unix-like systems generally support Unicode
        return True

    def success(self, message: str) -> None:
        """Print success message in green with checkmark.

        Args:
            message: Success message to display
        """
        self.console.print(f"{self.symbols['check']} {message}", style="success")

    def error(self, message: str) -> None:
        """Print error message in red with cross mark.

        Args:
            message: Error message to display
        """
        self.console.print(f"{self.symbols['cross']} {message}", style="error")

    def warning(self, message: str) -> None:
        """Print warning message in yellow.

        Args:
            message: Warning message to display
        """
        self.console.print(f"{self.symbols['bullet']} {message}", style="warning")

    def info(self, message: str) -> None:
        """Print info message in blue.

        Args:
            message: Info message to display
        """
        self.console.print(f"{self.symbols['arrow']} {message}", style="info")

    def debug(self, message: str) -> None:
        """Print debug message (only in verbose mode).

        Args:
            message: Debug message to display
        """
        if self.verbose:
            self.console.print(f"[DEBUG] {message}", style="dim")

    def print(self, message: str, style: str | None = None) -> None:
        """Print raw message with optional style.

        Args:
            message: Message to display
            style: Optional Rich style (e.g., "bold", "red", etc.)
        """
        if style:
            self.console.print(message, style=style)
        else:
            self.console.print(message)

    def new_line(self) -> None:
        """Print empty line."""
        self.console.print()

    def get_console(self) -> Console:
        """Get underlying Rich console for advanced usage.

        Returns:
            Rich Console instance
        """
        return self.console
