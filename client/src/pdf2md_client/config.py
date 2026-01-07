"""PDF2md Client configuration models.

This module defines Pydantic models for configuration and conversion options.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseSettings):
    """Server configuration model.

    Loaded from config file, environment variables, or defaults.
    Environment variables use PDF2MD_ prefix (e.g., PDF2MD_SERVER_URL).
    """

    model_config = SettingsConfigDict(
        env_prefix="PDF2MD_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    server_url: str = Field(
        default="http://localhost:8000",
        description="URL of the PDF2md server",
    )

    timeout: int = Field(
        default=300,
        ge=1,
        le=3600,
        description="Request timeout in seconds (1-3600)",
    )

    chunk_size: int = Field(
        default=8192,
        ge=1024,
        le=1048576,
        description="Upload chunk size in bytes (1KB-1MB)",
    )

    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts for network errors",
    )

    verify_ssl: bool = Field(
        default=True,
        description="Verify SSL certificates for HTTPS connections",
    )

    output_dir: Optional[str] = Field(
        default=None,
        description="Default output directory for converted files",
    )

    overwrite: bool = Field(
        default=False,
        description="Overwrite existing files without prompting",
    )

    @field_validator("server_url")
    @classmethod
    def validate_server_url(cls, v: str) -> str:
        """Validate server URL format.

        Args:
            v: Server URL value

        Returns:
            Validated server URL

        Raises:
            ValueError: If URL format is invalid
        """
        if not v:
            raise ValueError("server_url cannot be empty")

        # Ensure URL has scheme
        if not v.startswith(("http://", "https://")):
            v = f"http://{v}"

        # Remove trailing slash
        v = v.rstrip("/")

        return v

    @field_validator("output_dir")
    @classmethod
    def validate_output_dir(cls, v: Optional[str]) -> Optional[str]:
        """Validate output directory if specified.

        Args:
            v: Output directory path

        Returns:
            Validated output directory or None

        Raises:
            ValueError: If path is not a directory (when it exists)
        """
        if v is None:
            return None

        path = Path(v)
        if path.exists() and not path.is_dir():
            raise ValueError(f"output_dir must be a directory, not a file: {v}")

        return v


class ConversionOptions:
    """Options for a single PDF conversion operation.

    Merges CLI arguments, environment variables, and config file settings.
    Priority: CLI flags > Environment variables > Config file > Defaults
    """

    def __init__(
        self,
        input_path: Path,
        output_path: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        overwrite: Optional[bool] = None,
        verbose: bool = False,
        server_url: Optional[str] = None,
        timeout: Optional[int] = None,
        config: Optional[ServerConfig] = None,
    ) -> None:
        """Initialize conversion options.

        Args:
            input_path: Path to input PDF file
            output_path: Optional specific output file path
            output_dir: Optional custom output directory
            overwrite: Optional overwrite flag
            verbose: Enable verbose logging
            server_url: Optional server URL override
            timeout: Optional timeout override
            config: ServerConfig instance for defaults
        """
        self.input_path = input_path
        self._output_path = output_path
        self._output_dir = output_dir
        self._overwrite = overwrite
        self.verbose = verbose
        self._server_url = server_url
        self._timeout = timeout
        self._config = config or ServerConfig()

    def get_output_path(self) -> Path:
        """Determine the output file path.

        Priority:
        1. Explicit output_path (if provided)
        2. output_dir + input filename (with .md extension)
        3. config.output_dir + input filename (if set)
        4. Input file directory + input filename (with .md extension)

        Returns:
            Path where the converted Markdown file should be saved
        """
        # Priority 1: Explicit output path
        if self._output_path:
            return self._output_path

        # Determine output directory
        if self._output_dir:
            # Priority 2: Custom output directory from CLI
            output_dir = self._output_dir
        elif self._config.output_dir:
            # Priority 3: Default output directory from config
            output_dir = Path(self._config.output_dir)
        else:
            # Priority 4: Same as input file
            output_dir = self.input_path.parent

        # Generate filename from input (replace .pdf with .md)
        output_filename = self.input_path.stem + ".md"
        return output_dir / output_filename

    @property
    def server_url(self) -> str:
        """Get effective server URL."""
        return self._server_url or self._config.server_url

    @property
    def timeout(self) -> int:
        """Get effective timeout."""
        return self._timeout or self._config.timeout

    @property
    def overwrite(self) -> bool:
        """Get effective overwrite flag."""
        if self._overwrite is not None:
            return self._overwrite
        return self._config.overwrite

    @property
    def chunk_size(self) -> int:
        """Get chunk size from config."""
        return self._config.chunk_size

    @property
    def max_retries(self) -> int:
        """Get max retries from config."""
        return self._config.max_retries

    @property
    def verify_ssl(self) -> bool:
        """Get SSL verification setting."""
        return self._config.verify_ssl


class ConversionResult:
    """Result of a PDF conversion operation.

    Contains success status, output path, and metadata.
    """

    def __init__(
        self,
        success: bool,
        output_path: Optional[Path] = None,
        page_count: Optional[int] = None,
        duration: Optional[float] = None,
        file_size: Optional[int] = None,
        error: Optional[str] = None,
    ) -> None:
        """Initialize conversion result.

        Args:
            success: Whether the conversion succeeded
            output_path: Path to output file (if successful)
            page_count: Number of pages in the PDF
            duration: Conversion duration in seconds
            file_size: Output file size in bytes
            error: Error message (if failed)
        """
        self.success = success
        self.output_path = output_path
        self.page_count = page_count
        self.duration = duration
        self.file_size = file_size
        self.error = error

    def __bool__(self) -> bool:
        """Return True if conversion succeeded."""
        return self.success
