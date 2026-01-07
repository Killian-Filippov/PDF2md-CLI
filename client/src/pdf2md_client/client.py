"""PDF2md Client - HTTP client for PDF conversion.

Handles upload, conversion polling, and download of converted Markdown files.
"""

import asyncio
import time
from pathlib import Path

import httpx

from pdf2md_client.config import ConversionOptions, ConversionResult
from pdf2md_client.exceptions import ConversionError, NetworkError
from pdf2md_client.output import CLIOutput


class PDF2MDClient:
    """Async HTTP client for PDF2md server.

    Manages PDF upload, conversion status polling, and Markdown download.
    Uses exponential backoff for network errors with retry logic.
    """

    def __init__(self, options: ConversionOptions, output: CLIOutput) -> None:
        """Initialize HTTP client.

        Args:
            options: Conversion options (server URL, timeout, etc.)
            output: CLI output wrapper for progress display
        """
        self.options = options
        self.output = output

        # HTTP client configuration
        self.client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "PDF2MDClient":
        """Initialize async context manager.

        Returns:
            Self for context manager protocol
        """
        self.client = httpx.AsyncClient(
            timeout=self.options.timeout,
            verify=self.options.verify_ssl,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Cleanup async context manager.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        if self.client:
            await self.client.aclose()

    async def convert_pdf(self, pdf_path: Path) -> ConversionResult:
        """Convert PDF to Markdown.

        Orchestrates upload, conversion, and download workflow.

        Args:
            pdf_path: Path to PDF file

        Returns:
            ConversionResult with output path and metadata

        Raises:
            NetworkError: If server communication fails
            ConversionError: If conversion fails on server
        """
        start_time = time.time()

        try:
            # Step 1: Upload PDF
            self.output.info(f"Uploading {pdf_path.name}...")
            task_id = await self._upload_pdf(pdf_path)

            # Step 2: Wait for conversion
            self.output.info("Converting...")
            result = await self._wait_for_conversion(task_id)

            # Step 3: Download Markdown
            self.output.info(f"Downloading {pdf_path.stem}.md...")
            markdown_content = await self._download_markdown(task_id)

            # Calculate duration
            duration = time.time() - start_time

            # Return successful result
            return ConversionResult(
                success=True,
                output_path=self.options.get_output_path(),
                page_count=result.get("page_count"),
                duration=duration,
                file_size=len(markdown_content.encode("utf-8")),
            )

        except httpx.HTTPError as e:
            raise NetworkError(
                f"Network error during conversion: {e}",
                troubleshooting=[
                    f"Server URL: {self.options.server_url}",
                    "Check if the server is running",
                    "Test connectivity: curl " + self.options.server_url,
                ],
            ) from e

        except Exception as e:
            raise ConversionError(
                f"Conversion failed: {e}",
            ) from e

    async def _upload_pdf(self, pdf_path: Path) -> str:
        """Upload PDF file to server.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Task ID for tracking conversion

        Raises:
            NetworkError: If upload fails after retries
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        retry_count = 0
        max_retries = self.options.max_retries

        while retry_count <= max_retries:
            try:
                # Get file size for progress reporting
                file_size = pdf_path.stat().st_size
                size_mb = file_size / (1024 * 1024)

                self.output.debug(f"Uploading {pdf_path.name} ({size_mb:.1f} MB)...")

                # Open file and upload
                with open(pdf_path, "rb") as f:
                    files = {
                        "file": (pdf_path.name, f, "application/pdf"),
                    }

                    response = await self.client.post(
                        f"{self.options.server_url}/convert",
                        files=files,
                    )

                    response.raise_for_status()

                    # Extract task ID from response
                    result = response.json()
                    task_id = result.get("task_id")

                    if not task_id:
                        raise ConversionError("Server did not return task ID")

                    self.output.debug(f"Upload complete. Task ID: {task_id}")
                    return task_id

            except httpx.HTTPStatusError as e:
                # Don't retry on client errors (4xx)
                if e.response.status_code >= 400 and e.response.status_code < 500:
                    raise ConversionError(
                        f"Upload rejected by server: {e.response.status_code}",
                    ) from e

                # Retry on server errors (5xx)
                if retry_count < max_retries:
                    retry_count += 1
                    wait_time = 2**retry_count  # Exponential backoff: 2s, 4s, 8s
                    self.output.warning(
                        f"Upload failed (attempt {retry_count}/{max_retries}), "
                        f"retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise NetworkError(
                        f"Upload failed after {max_retries} retries: {e}",
                    ) from e

            except httpx.ConnectError as e:
                # Connection errors - retry with backoff
                if retry_count < max_retries:
                    retry_count += 1
                    wait_time = 2**retry_count
                    self.output.warning(
                        f"Connection failed (attempt {retry_count}/{max_retries}), "
                        f"retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise NetworkError(
                        f"Cannot connect to server after {max_retries} retries: {e}",
                        troubleshooting=[
                            f"Server URL: {self.options.server_url}",
                            "Check if the server is running",
                            "Test network connectivity",
                        ],
                    ) from e

        raise NetworkError("Upload failed: Maximum retries exceeded")

    async def _wait_for_conversion(self, task_id: str) -> dict:
        """Wait for PDF conversion to complete.

        Polls server status endpoint with animated progress indicator.

        Args:
            task_id: Task ID from upload

        Returns:
            Conversion result with page count

        Raises:
            ConversionError: If conversion fails
            NetworkError: If status polling fails
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        pulse_frames = ["[●    ]", "[ ●   ]", "[  ●  ]", "[   ● ]", "[    ●]"]
        frame = 0

        while True:
            try:
                # Check conversion status
                response = await self.client.get(f"{self.options.server_url}/status/{task_id}")
                response.raise_for_status()

                result = response.json()
                status = result.get("status")

                self.output.debug(f"Conversion status: {status}")

                # Check if conversion is complete
                if status == "complete":
                    return result

                # Check if conversion failed
                if status == "failed":
                    error = result.get("error", "Unknown error")
                    raise ConversionError(f"Conversion failed: {error}")

                # Still processing - update animated indicator
                if self.output.verbose:
                    print(f"\r  Converting... {pulse_frames[frame]}", end="", flush=True)
                    frame = (frame + 1) % len(pulse_frames)

                # Wait before polling again
                await asyncio.sleep(0.5)

            except httpx.HTTPStatusError as e:
                raise ConversionError(
                    f"Server returned error status: {e.response.status_code}",
                ) from e

            except httpx.ConnectError as e:
                # Don't retry connection errors during polling
                # (likely server is down mid-conversion)
                raise NetworkError(
                    f"Lost connection to server: {e}",
                    troubleshooting=[
                        "The server may have gone down during conversion",
                        "Check if the server is still running",
                    ],
                ) from e

    async def _download_markdown(self, task_id: str) -> str:
        """Download converted Markdown file.

        Args:
            task_id: Task ID from upload

        Returns:
            Markdown content as string

        Raises:
            NetworkError: If download fails
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        retry_count = 0
        max_retries = self.options.max_retries

        while retry_count <= max_retries:
            try:
                self.output.debug(f"Downloading Markdown for task {task_id}...")

                # Stream download for large files
                response = await self.client.get(f"{self.options.server_url}/download/{task_id}")
                response.raise_for_status()

                # Read content
                content = response.text

                self.output.debug("Download complete.")
                return content

            except httpx.HTTPStatusError as e:
                # Don't retry on client errors
                if e.response.status_code >= 400 and e.response.status_code < 500:
                    raise ConversionError(
                        f"Download rejected by server: {e.response.status_code}",
                    ) from e

                # Retry on server errors
                if retry_count < max_retries:
                    retry_count += 1
                    wait_time = 2**retry_count
                    self.output.warning(
                        f"Download failed (attempt {retry_count}/{max_retries}), "
                        f"retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise NetworkError(
                        f"Download failed after {max_retries} retries: {e}",
                    ) from e

            except httpx.ConnectError as e:
                # Retry connection errors
                if retry_count < max_retries:
                    retry_count += 1
                    wait_time = 2**retry_count
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise NetworkError(
                        f"Cannot connect to server: {e}",
                    ) from e

        raise NetworkError("Download failed: Maximum retries exceeded")
