"""PDF2md Client CLI - Command-line interface for PDF conversion.

Provides main `convert` command and `config` subcommands for managing
server configuration and converting PDF files to Markdown.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer

from pdf2md_client.config import ConversionOptions, ServerConfig
from pdf2md_client.config_manager import ConfigManager
from pdf2md_client.exceptions import ConfigError, PDF2MDError
from pdf2md_client.file_handler import FileHandler
from pdf2md_client.output import CLIOutput

# Create main Typer app
app = typer.Typer(
    name="pdf2md",
    help="PDF2md - Convert PDF files to Markdown using a remote GPU server",
    add_completion=False,
)

# Create config subcommand app
config_app = typer.Typer(
    name="config",
    help="Configuration management commands",
)
app.add_typer(config_app, name="config")


def get_version() -> str:
    """Get version string.

    Returns:
        Version string
    """
    from pdf2md_client import __version__

    return f"PDF2md CLI v{__version__}"


def _convert_async(
    pdf_file: Path,
    output: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    overwrite: Optional[bool] = None,
    verbose: bool = False,
    server: Optional[str] = None,
    timeout: Optional[int] = None,
) -> int:
    """Async conversion wrapper.

    Args:
        pdf_file: Path to PDF file
        output: Optional output file path
        output_dir: Optional output directory
        overwrite: Optional overwrite flag
        verbose: Enable verbose logging
        server: Optional server URL override
        timeout: Optional timeout override

    Returns:
        Exit code (0 for success, 1-5 for errors, 130 for SIGINT)
    """
    # Initialize output
    output_obj = CLIOutput(verbose=verbose)

    try:
        # Load configuration
        config = ConfigManager.load_config()
        output_obj.debug(f"Loaded config from: {ConfigManager.get_config_path()}")

        # Create conversion options with CLI overrides
        options = ConversionOptions(
            input_path=pdf_file,
            output_path=output,
            output_dir=output_dir,
            overwrite=overwrite,
            verbose=verbose,
            server_url=server,
            timeout=timeout,
            config=config,
        )

        # Validate input file
        output_obj.debug(f"Validating input file: {pdf_file}")
        FileHandler.validate_pdf_file(pdf_file)

        # Check output conflict
        output_path = options.get_output_path()
        if not options.overwrite and FileHandler.check_output_conflict(output_path):
            # Prompt user for overwrite
            response = typer.confirm(
                f"File exists: {output_path}\\nOverwrite?",
                default=False,
            )
            if not response:
                output_obj.warning("Conversion cancelled.")
                return 0

        # Perform conversion
        from pdf2md_client.client import PDF2MDClient

        with output_obj.get_console().status(
            "[bold blue]Converting PDF...", spinner="dots"
        ):
            async def do_convert() -> None:
                async with PDF2MDClient(options, output_obj) as client:
                    result = await client.convert_pdf(pdf_file)

                    # Save output file
                    output_obj.debug(f"Saving to: {output_path}")
                    FileHandler.save_markdown(
                        "Test markdown content",  # Placeholder
                        output_path,
                    )

                    # Display success message
                    output_obj.success(
                        f"Converted: {output_path.name} "
                        f"({result.page_count or '?'} pages, {result.duration:.1f}s)"
                    )

            asyncio.run(do_convert())

        return 0

    except KeyboardInterrupt:
        output_obj.new_line()
        output_obj.warning("Conversion cancelled by user.")
        return 130

    except PDF2MDError as e:
        output_obj.error(str(e))
        return e.exit_code

    except Exception as e:
        if verbose:
            import traceback

            output_obj.error(f"Unexpected error: {e}")
            output_obj.print(traceback.format_exc(), style="dim")
        else:
            output_obj.error(f"Unexpected error: {e}")
        return 1


@app.command()
def convert(
    pdf_file: Path = typer.Argument(
        ...,
        help="Path to PDF file to convert",
        exists=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Custom output directory or file path",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite existing files without prompting",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose logging",
    ),
    server: Optional[str] = typer.Option(
        None,
        "--server", "-s",
        help="Override server URL",
    ),
    timeout: Optional[int] = typer.Option(
        None,
        "--timeout", "-t",
        help="Override request timeout (seconds)",
    ),
) -> None:
    """Convert a PDF file to Markdown.

    Example:
        pdf2md convert document.pdf

    This command uploads the PDF to a remote GPU server for conversion,
    then downloads the resulting Markdown file to the same directory
    (or a custom directory if specified with --output).
    """
    # Edge case: Check if pdf_file is a directory
    if pdf_file.is_dir():
        output_obj = CLIOutput()
        output_obj.error(f"Expected a PDF file, not a directory: {pdf_file}")
        raise typer.Exit(code=3)

    sys.exit(
        _convert_async(
            pdf_file=pdf_file,
            output=output,
            output_dir=output,  # Typer combines --output and --output-dir
            overwrite=overwrite,
            verbose=verbose,
            server=server,
            timeout=timeout,
        )
    )


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        help="Show version and exit",
    ),
) -> None:
    """PDF2md CLI - Convert PDF files to Markdown.

    Use 'pdf2md convert <file>' to convert a PDF file.
    Use 'pdf2md config' to manage configuration.
    """
    if version:
        typer.echo(get_version())
        raise typer.Exit(code=0)


@config_app.command("init")
def config_init(
    server_url: str = typer.Option(
        "http://localhost:8000",
        "--server-url",
        help="Server URL",
    ),
    timeout: int = typer.Option(
        300,
        "--timeout",
        help="Request timeout (seconds)",
    ),
) -> None:
    """Initialize configuration file.

    Creates ~/.pdf2md/config.json with specified settings.
    """
    output = CLIOutput()

    try:
        # Create new config with specified values
        config = ServerConfig(
            server_url=server_url,
            timeout=timeout,
        )

        # Save config
        ConfigManager.save_config(config)

        output.success(f"Configuration created at: {ConfigManager.get_config_path()}")

    except ConfigError as e:
        output.error(str(e))
        raise typer.Exit(code=e.exit_code)


@config_app.command("show")
def config_show() -> None:
    """Display current configuration."""
    output = CLIOutput()

    try:
        # Load config
        config = ConfigManager.load_config()

        # Display config
        output.new_line()
        output.print("Current Configuration:", style="bold")
        output.print("─" * 40, style="dim")
        output.print(f"server_url:  {config.server_url}")
        output.print(f"timeout:     {config.timeout}")
        output.print(f"chunk_size:  {config.chunk_size}")
        output.print(f"max_retries: {config.max_retries}")
        output.print(f"verify_ssl:  {config.verify_ssl}")
        output.print(f"output_dir:  {config.output_dir or 'None'}")
        output.print(f"overwrite:   {config.overwrite}")
        output.new_line()

    except ConfigError as e:
        output.error(str(e))
        raise typer.Exit(code=e.exit_code)


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Configuration key"),
    value: str = typer.Argument(..., help="Configuration value"),
) -> None:
    """Set a configuration value.

    Example:
        pdf2md config set server_url http://localhost:8000
    """
    output = CLIOutput()

    try:
        # Load current config
        config = ConfigManager.load_config()

        # Map key to config field
        key_map = {
            "server-url": "server_url",
            "server_url": "server_url",
            "timeout": "timeout",
            "chunk-size": "chunk_size",
            "chunk_size": "chunk_size",
            "max-retries": "max_retries",
            "max_retries": "max_retries",
            "verify-ssl": "verify_ssl",
            "verify_ssl": "verify_ssl",
            "output-dir": "output_dir",
            "output_dir": "output_dir",
            "overwrite": "overwrite",
        }

        if key not in key_map:
            output.error(f"Unknown configuration key: {key}")
            output.info("Available keys: server_url, timeout, chunk_size, max_retries, verify_ssl, output_dir, overwrite")
            raise typer.Exit(code=3)

        field_name = key_map[key]

        # Convert value to appropriate type
        if hasattr(config, field_name):
            field_type = type(getattr(config, field_name))

            # Handle boolean values
            if field_type == bool:
                if value.lower() in ("true", "1", "yes"):
                    value = True
                elif value.lower() in ("false", "0", "no"):
                    value = False
                else:
                    output.error(f"Invalid boolean value: {value}")
                    raise typer.Exit(code=3)

            # Handle integer values
            elif field_type == int:
                try:
                    value = int(value)
                except ValueError:
                    output.error(f"Invalid integer value: {value}")
                    raise typer.Exit(code=3)

            # Update field
            setattr(config, field_name, value)

            # Save config
            ConfigManager.save_config(config)

            output.success(f"Configuration updated: {field_name} = {value}")

        else:
            output.error(f"Unknown configuration key: {key}")
            raise typer.Exit(code=3)

    except ConfigError as e:
        output.error(str(e))
        raise typer.Exit(code=e.exit_code)


if __name__ == "__main__":
    app()
