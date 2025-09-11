"""
Command Line Interface for GenEWeb Python Modernization

This module provides a command-line interface for the GenEWeb system,
allowing users to start servers, manage databases, import/export data,
and perform various administrative tasks.

Copyright (c) 1998-2007 INRIA
Python modernization preserving original structure and functionality.
"""

import logging
import os
import sys
from typing import Optional

import click

from .db.driver import create_database_driver, get_available_databases
from .web.server import start_server


@click.group()
@click.version_option()
def main():
    """
    GenEWeb Python Modernization

    A modern Python implementation of the GenEWeb genealogical software,
    carefully translated from OCaml while preserving all core functionality
    and historical significance.
    """


@main.command()
@click.option("--host", default="localhost", help="Host to bind the server to")
@click.option("--port", default=2317, type=int, help="Port to bind the server to")
@click.option(
    "--database-dir",
    default="databases",
    help="Directory containing databases",
)
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option("--daemon", is_flag=True, help="Run server as daemon")
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    help="Set logging level",
)
def server(
    host: str,
    port: int,
    database_dir: str,
    debug: bool,
    daemon: bool,
    log_level: str,
):
    """Start the GenEWeb web server"""

    # Set up logging
    numeric_level = getattr(logging, log_level.upper())
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Check database directory
    if not os.path.exists(database_dir):
        click.echo(f"Creating database directory: {database_dir}")
        os.makedirs(database_dir, exist_ok=True)

    # Show available databases
    databases = get_available_databases(database_dir)
    if databases:
        click.echo(f"Available databases: {', '.join(databases)}")
    else:
        click.echo(f"No databases found in {database_dir}")
        click.echo("You can create a new database using 'geneweb create-db' command")

    # Show server information
    click.echo(f"Starting GenEWeb server on http://{host}:{port}/")
    click.echo("Press Ctrl+C to stop the server")

    try:
        start_server(
            host=host,
            port=port,
            database_dir=database_dir,
            debug=debug,
            daemon=daemon,
        )
    except KeyboardInterrupt:
        click.echo("\nServer stopped by user")
    except Exception as e:
        click.echo(f"Error starting server: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("database_name")
@click.option(
    "--database-dir",
    default="databases",
    help="Directory to create database in",
)
@click.option(
    "--type",
    "db_type",
    default="pickle",
    type=click.Choice(["pickle", "sqlite"], case_sensitive=False),
    help="Database type to create",
)
def create_db(database_name: str, database_dir: str, db_type: str):
    """Create a new database"""

    if not os.path.exists(database_dir):
        os.makedirs(database_dir, exist_ok=True)

    db_path = os.path.join(database_dir, database_name)

    # Check if database already exists
    if os.path.exists(db_path + ".gwb") or os.path.exists(db_path + ".pickle"):
        click.echo(f"Database '{database_name}' already exists", err=True)
        sys.exit(1)

    try:
        # Create database
        driver = create_database_driver(db_path + ".pickle", db_type)
        if driver.open_database(read_only=False):
            driver.close_database()
            click.echo(f"Created database '{database_name}' in {database_dir}")
        else:
            click.echo(f"Failed to create database '{database_name}'", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"Error creating database: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    "--database-dir",
    default="databases",
    help="Directory containing databases",
)
def list_db(database_dir: str):
    """List available databases"""

    if not os.path.exists(database_dir):
        click.echo(f"Database directory '{database_dir}' does not exist")
        return

    databases = get_available_databases(database_dir)

    if not databases:
        click.echo(f"No databases found in {database_dir}")
        return

    click.echo(f"Available databases in {database_dir}:")
    for db_name in databases:
        db_path = os.path.join(database_dir, db_name)

        # Try to get database info
        try:
            driver = create_database_driver(db_path + ".pickle")
            if driver.open_database():
                info = driver.get_database_info()
                click.echo(f"  {db_name}: {info.number_of_persons} persons, {info.number_of_families} families")
                driver.close_database()
            else:
                click.echo(f"  {db_name}: (unable to read)")
        except Exception:
            click.echo(f"  {db_name}: (format unknown)")


@main.command()
@click.argument("database_name")
@click.option(
    "--database-dir",
    default="databases",
    help="Directory containing databases",
)
def info(database_name: str, database_dir: str):
    """Show information about a database"""

    db_path = os.path.join(database_dir, database_name)

    try:
        driver = create_database_driver(db_path + ".pickle")
        if not driver.open_database():
            click.echo(f"Failed to open database '{database_name}'", err=True)
            sys.exit(1)

        info = driver.get_database_info()

        click.echo(f"Database: {info.name}")
        click.echo(f"Path: {info.path}")
        click.echo(f"Persons: {info.number_of_persons:,}")
        click.echo(f"Families: {info.number_of_families:,}")
        click.echo(f"Version: {info.version}")

        if info.created_date:
            click.echo(f"Created: {info.created_date}")
        if info.modified_date:
            click.echo(f"Modified: {info.modified_date}")

        driver.close_database()

    except Exception as e:
        click.echo(f"Error reading database info: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("database_name")
@click.option(
    "--database-dir",
    default="databases",
    help="Directory containing databases",
)
@click.option("--limit", default=10, type=int, help="Number of persons to show")
def persons(database_name: str, database_dir: str, limit: int):
    """List persons in a database"""

    db_path = os.path.join(database_dir, database_name)

    try:
        driver = create_database_driver(db_path + ".pickle")
        if not driver.open_database():
            click.echo(f"Failed to open database '{database_name}'", err=True)
            sys.exit(1)

        count = 0
        for person_id, person in driver.get_persons():
            if count >= limit:
                break

            click.echo(f"  {person.first_name} {person.surname}")
            if person.birth_date:
                from .util.string_utils import geneweb_date_to_string

                birth_str = geneweb_date_to_string(person.birth_date)
                click.echo(f"    Born: {birth_str}")

            count += 1

        total_count = driver.get_person_count()
        if count < total_count:
            click.echo(f"  ... and {total_count - count} more persons")

        driver.close_database()

    except Exception as e:
        click.echo(f"Error reading persons: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("database_name")
@click.argument("query")
@click.option(
    "--database-dir",
    default="databases",
    help="Directory containing databases",
)
@click.option("--limit", default=20, type=int, help="Maximum number of results")
def search(database_name: str, query: str, database_dir: str, limit: int):
    """Search for persons in a database"""

    db_path = os.path.join(database_dir, database_name)

    try:
        driver = create_database_driver(db_path + ".pickle")
        if not driver.open_database():
            click.echo(f"Failed to open database '{database_name}'", err=True)
            sys.exit(1)

        results = driver.search_persons(query, limit)

        if not results:
            click.echo(f"No persons found matching '{query}'")
        else:
            click.echo(f"Found {len(results)} person(s) matching '{query}':")

            for person_id, person in results:
                click.echo(f"  {person.first_name} {person.surname}")
                if person.birth_date:
                    from .util.string_utils import geneweb_date_to_string

                    birth_str = geneweb_date_to_string(person.birth_date)
                    click.echo(f"    Born: {birth_str}")
                if person.occupation:
                    click.echo(f"    Occupation: {person.occupation}")

        driver.close_database()

    except Exception as e:
        click.echo(f"Error searching database: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("source_file")
@click.argument("database_name")
@click.option(
    "--database-dir",
    default="databases",
    help="Directory to create database in",
)
@click.option(
    "--format",
    "file_format",
    default="gedcom",
    type=click.Choice(["gedcom", "csv", "gw"], case_sensitive=False),
    help="Format of source file",
)
def import_data(source_file: str, database_name: str, database_dir: str, file_format: str):
    """Import data from various formats"""

    if not os.path.exists(source_file):
        click.echo(f"Source file '{source_file}' not found", err=True)
        sys.exit(1)

    # This would be implemented with proper import functionality
    click.echo(f"Importing {file_format} data from '{source_file}' to database '{database_name}'")
    click.echo("Import functionality not yet implemented in this modernization phase")
    click.echo("This will be added in subsequent development iterations")


@main.command()
@click.argument("database_name")
@click.argument("output_file")
@click.option(
    "--database-dir",
    default="databases",
    help="Directory containing databases",
)
@click.option(
    "--format",
    "file_format",
    default="gedcom",
    type=click.Choice(["gedcom", "csv", "gw"], case_sensitive=False),
    help="Format for export file",
)
def export_data(database_name: str, output_file: str, database_dir: str, file_format: str):
    """Export data to various formats"""

    os.path.join(database_dir, database_name)

    # This would be implemented with proper export functionality
    click.echo(f"Exporting database '{database_name}' to {file_format} format: '{output_file}'")
    click.echo("Export functionality not yet implemented in this modernization phase")
    click.echo("This will be added in subsequent development iterations")


@main.command()
@click.argument("database_name")
@click.option(
    "--database-dir",
    default="databases",
    help="Directory containing databases",
)
@click.option(
    "--backup-dir",
    help="Directory to store backup (default: database-dir/backups)",
)
def backup(database_name: str, database_dir: str, backup_dir: Optional[str]):
    """Create a backup of a database"""

    if backup_dir is None:
        backup_dir = os.path.join(database_dir, "backups")

    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir, exist_ok=True)

    db_path = os.path.join(database_dir, database_name)

    # Create timestamp for backup filename
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{database_name}_{timestamp}.backup"
    backup_path = os.path.join(backup_dir, backup_filename)

    try:
        driver = create_database_driver(db_path + ".pickle")
        if driver.backup_database(backup_path):
            click.echo(f"Database '{database_name}' backed up to: {backup_path}")
        else:
            click.echo(f"Failed to backup database '{database_name}'", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"Error creating backup: {e}", err=True)
        sys.exit(1)


@main.command()
def version():
    """Show version information"""
    from . import __author__, __license__, __version__

    click.echo(f"GenEWeb Python Modernization version {__version__}")
    click.echo(f"Author: {__author__}")
    click.echo(f"License: {__license__}")
    click.echo("")
    click.echo("This is a modern Python implementation of GenEWeb genealogical software,")
    click.echo("carefully translated from the original OCaml version while preserving")
    click.echo("all core functionality and historical significance.")
    click.echo("")
    click.echo("Original GenEWeb Copyright (c) 1998-2007 INRIA")


@main.command()
def config():
    """Show configuration information"""

    click.echo("GenEWeb Configuration:")
    click.echo(f"  Python executable: {sys.executable}")
    click.echo(f"  Python version: {sys.version}")
    click.echo(f"  Working directory: {os.getcwd()}")

    # Check for configuration files
    config_files = [".geneweb.yml", ".geneweb.yaml", "geneweb.conf"]
    for config_file in config_files:
        if os.path.exists(config_file):
            click.echo(f"  Configuration file found: {config_file}")

    # Check environment variables
    env_vars = ["GENEWEB_DATABASE_DIR", "GENEWEB_DEBUG", "GENEWEB_PORT"]
    for env_var in env_vars:
        value = os.environ.get(env_var)
        if value:
            click.echo(f"  Environment variable {env_var}: {value}")


if __name__ == "__main__":
    main()
