"""
Command Line Interface for MCP Config Manager
"""

import click
from . import __version__

@click.group()
@click.version_option(version=__version__)
def cli():
    """MCP Config Manager - Manage your MCP server configurations"""
    pass

@cli.command()
def gui():
    """Launch the GUI interface"""
    click.echo("GUI not yet implemented. Coming soon!")
    # TODO: Import and launch GUI when ready
    # from .gui.main_window import launch_gui
    # launch_gui()

@cli.command()
@click.argument('config_file', type=click.Path(exists=True))
def validate(config_file):
    """Validate an MCP configuration file"""
    click.echo(f"Validating {config_file}...")
    # TODO: Implement validation logic
    click.echo("Validation not yet implemented.")

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
def convert(input_file, output_file):
    """Convert between different MCP configuration formats"""
    click.echo(f"Converting {input_file} to {output_file}...")
    # TODO: Implement conversion logic
    click.echo("Conversion not yet implemented.")

def main():
    """Main entry point"""
    cli()

if __name__ == "__main__":
    main()
