"""PDF2md Client configuration manager.

Handles loading, saving, and validation of configuration files.
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from platformdirs import user_config_dir

from pdf2md_client.config import ServerConfig
from pdf2md_client.exceptions import ConfigError


class ConfigManager:
    """Manages PDF2md client configuration.

    Handles loading from/saving to platform-specific config directory,
    with automatic backup of corrupted files.
    """

    CONFIG_DIR = Path(user_config_dir("pdf2md", appauthor=False))
    CONFIG_FILE = CONFIG_DIR / "config.json"

    @classmethod
    def get_config_path(cls) -> Path:
        """Get the platform-specific config file path.

        Returns:
            Path to config.json
        """
        return cls.CONFIG_FILE

    @classmethod
    def load_config(cls) -> ServerConfig:
        """Load configuration from file.

        Searches for config in platform-specific directory:
        - Linux: ~/.config/pdf2md/config.json
        - macOS: ~/Library/Application Support/pdf2md/config.json
        - Windows: C:\\Users\\<username>\\AppData\\Roaming\\pdf2md\\config.json

        Returns:
            ServerConfig instance (with defaults if file doesn't exist)

        Raises:
            ConfigError: If config file is corrupted and cannot be recovered
        """
        config_path = cls.get_config_path()

        # Return defaults if config doesn't exist
        if not config_path.exists():
            return ServerConfig()

        # Try to load and parse config file
        try:
            with open(config_path, encoding="utf-8") as f:
                data = json.load(f)

            # Validate with Pydantic model
            return ServerConfig(**data)

        except json.JSONDecodeError as e:
            # Corrupted JSON - backup and return defaults
            cls._handle_corrupted_config(config_path, str(e))
            return ServerConfig()

        except Exception as e:
            # Validation error - backup and re-raise
            cls._handle_corrupted_config(config_path, str(e))
            raise ConfigError(
                f"Invalid configuration: {e}",
                troubleshooting=[
                    "Run 'pdf2md config init' to create a new configuration",
                    f"Corrupted config backed up to: {config_path}.backup",
                ],
            ) from e

    @classmethod
    def save_config(cls, config: ServerConfig) -> None:
        """Save configuration to file.

        Creates config directory if it doesn't exist.
        Sets secure permissions (user read/write only).

        Args:
            config: ServerConfig instance to save

        Raises:
            ConfigError: If config directory is not writable
        """
        config_path = cls.get_config_path()

        # Create config directory if it doesn't exist
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ConfigError(
                f"Cannot create config directory: {e}",
                troubleshooting=[
                    f"Ensure you have write permissions for: {config_path.parent}",
                    "Check if the directory path is valid",
                ],
            ) from e

        # Serialize config to JSON
        config_data = config.model_dump(exclude_none=True)

        # Write to temporary file first (atomic write)
        temp_path = config_path.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2)

            # Atomic rename
            temp_path.replace(config_path)

        except OSError as e:
            # Clean up temp file
            temp_path.unlink(missing_ok=True)
            raise ConfigError(
                f"Cannot write config file: {e}",
                troubleshooting=[
                    f"Ensure you have write permissions for: {config_path}",
                    "Check disk space",
                ],
            ) from e

        # Set secure permissions (user read/write only)
        cls.set_secure_permissions(config_path)

    @classmethod
    def _handle_corrupted_config(cls, config_path: Path, error: str) -> None:
        """Handle corrupted configuration file.

        Creates a backup with timestamp, logs a warning.

        Args:
            config_path: Path to corrupted config file
            error: Error message
        """
        # Create backup with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = config_path.with_suffix(f".json.backup_{timestamp}")

        try:
            shutil.copy2(config_path, backup_path)
        except Exception:
            # Backup failed - not critical, just continue
            pass

        # Note: In a real application, this would log to a file
        # For CLI, we'll let the caller handle the warning message

    @classmethod
    def set_secure_permissions(cls, config_path: Path) -> None:
        """Set secure permissions on config file (user read/write only).

        Args:
            config_path: Path to config file
        """
        try:
            # Set permissions: user read/write only (0o600)
            os.chmod(config_path, 0o600)
        except OSError:
            # Non-critical - continue without setting permissions
            # (Windows might not support Unix-style permissions)
            pass
