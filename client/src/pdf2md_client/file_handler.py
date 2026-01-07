"""PDF2md Client file handler.

Handles file validation, conflict checking, and Markdown file saving.
"""

import hashlib
from pathlib import Path

from pdf2md_client.exceptions import ValidationError


class FileHandler:
    """Handles file operations for PDF conversion.

    Provides file validation, output conflict checking, and
    Markdown file saving.
    """

    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB in bytes

    @classmethod
    def validate_pdf_file(cls, file_path: Path) -> None:
        """Validate PDF file before conversion.

        Checks:
        - File exists
        - File is readable
        - File has .pdf extension
        - File size is within limits (500MB)
        - File is not a directory

        Args:
            file_path: Path to PDF file

        Raises:
            ValidationError: If any validation check fails
        """
        # Check if path exists
        if not file_path.exists():
            raise ValidationError(
                f"File not found: {file_path}",
                troubleshooting=[
                    f"Check if the file exists at: {file_path}",
                    "Use absolute path if relative path doesn't work",
                    "Ensure the filename is spelled correctly",
                ],
            )

        # Check if it's a directory
        if file_path.is_dir():
            raise ValidationError(
                f"Expected a PDF file, not a directory: {file_path}",
                troubleshooting=[
                    "Provide a path to a PDF file, not a directory",
                    f"Example: pdf2md convert {file_path / 'document.pdf'}",
                ],
            )

        # Check file extension
        if file_path.suffix.lower() != ".pdf":
            raise ValidationError(
                f"Invalid file format: {file_path.suffix}",
                troubleshooting=[
                    "Only .pdf files are supported",
                    f"Ensure the file has .pdf extension: {file_path}",
                ],
            )

        # Check if file is readable
        if not file_path.is_file():
            raise ValidationError(
                f"Cannot read file: {file_path}",
                troubleshooting=[
                    "Check file permissions",
                    "Ensure you have read access to the file",
                ],
            )

        # Check file size
        try:
            file_size = file_path.stat().st_size
            if file_size == 0:
                raise ValidationError(
                    f"File is empty: {file_path}",
                    troubleshooting=[
                        "The PDF file might be corrupted",
                        "Try downloading or generating the file again",
                    ],
                )

            if file_size > cls.MAX_FILE_SIZE:
                size_mb = file_size / (1024 * 1024)
                max_mb = cls.MAX_FILE_SIZE / (1024 * 1024)
                raise ValidationError(
                    f"File too large: {size_mb:.1f}MB (max: {max_mb}MB)",
                    troubleshooting=[
                        f"Split the PDF into smaller files",
                        f"Current size: {size_mb:.1f}MB, maximum allowed: {max_mb}MB",
                        "Contact server administrator to increase limit",
                    ],
                )
        except OSError as e:
            raise ValidationError(
                f"Cannot access file: {file_path}",
                troubleshooting=[
                    f"Error: {e}",
                    "Check if the file is locked by another process",
                    "Ensure you have read permissions",
                ],
            ) from e

    @classmethod
    def check_output_conflict(cls, output_path: Path) -> bool:
        """Check if output file already exists.

        Args:
            output_path: Path to output Markdown file

        Returns:
            True if file exists (conflict), False otherwise
        """
        return output_path.exists()

    @classmethod
    def save_markdown(cls, content: str, output_path: Path) -> None:
        """Save Markdown content to file.

        Creates parent directories if they don't exist.

        Args:
            content: Markdown content to save
            output_path: Path where to save the file

        Raises:
            ValidationError: If file cannot be written
        """
        # Create parent directories if they don't exist
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ValidationError(
                f"Cannot create output directory: {output_path.parent}",
                troubleshooting=[
                    f"Error: {e}",
                    "Check if you have write permissions",
                    "Ensure the path is valid",
                ],
            ) from e

        # Write Markdown content
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
        except OSError as e:
            raise ValidationError(
                f"Cannot write output file: {output_path}",
                troubleshooting=[
                    f"Error: {e}",
                    "Check if you have write permissions",
                    "Ensure disk space is available",
                ],
            ) from e

    @classmethod
    def calculate_file_hash(cls, file_path: Path) -> str:
        """Calculate SHA256 hash of a file.

        Useful for detecting file changes or duplicates.

        Args:
            file_path: Path to file

        Returns:
            Hexadecimal SHA256 hash
        """
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()
