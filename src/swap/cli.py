"""Command line interface for swap application."""

import sys
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from .config import get_settings
from .config.logging import setup_logging, get_logger
from .data.database import get_database, init_database
from .services import SheetsService, CalendarService, SyncService
from .data.repositories import SyncHistoryRepository, UserRepository

console = Console()
logger = get_logger(__name__)


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option("--log-level", default="INFO", help="Set logging level")
@click.pass_context
def cli(ctx, debug: bool, log_level: str):
    """Swap - Rota to Google Calendar Sync"""
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug
    ctx.obj["log_level"] = log_level
    
    # Setup logging
    setup_logging(log_level, debug)


@cli.command()
@click.pass_context
def sync(ctx):
    """Synchronize rota data to Google Calendar."""
    try:
        settings = get_settings()
        
        # Override settings with CLI options
        if ctx.obj["debug"]:
            settings.debug = True
            settings.log_level = ctx.obj["log_level"]
        
        logger.info("Starting synchronization...")
        
        # Initialize database
        init_database()
        
        # Get database session
        db_session = next(get_database())
        
        try:
            # Initialize services
            sheets_service = SheetsService(settings.google.service_account_file)
            calendar_service = CalendarService(
                settings.google.service_account_file,
                settings.google.timezone
            )
            
            sync_service = SyncService(
                settings=settings,
                db=db_session,
                sheets_service=sheets_service,
                calendar_service=calendar_service,
            )
            
            # Perform synchronization
            results = sync_service.sync_all_users()
            
            # Display results
            _display_sync_results(results)
            
            if results["errors"]:
                sys.exit(1)
            
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"Synchronization failed: {e}", exc_info=ctx.obj["debug"])
        rprint(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--limit", default=10, help="Number of history entries to show")
def history(limit: int):
    """Show synchronization history."""
    try:
        init_database()
        db_session = next(get_database())
        
        try:
            sync_history_repo = SyncHistoryRepository(db_session)
            history_entries = sync_history_repo.get_recent(limit=limit)
            
            if not history_entries:
                rprint("[yellow]No synchronization history found.[/yellow]")
                return
            
            table = Table(title="Synchronization History")
            table.add_column("Timestamp", style="cyan")
            table.add_column("User", style="magenta")
            table.add_column("Status", style="green")
            table.add_column("Shifts", justify="right")
            table.add_column("Events", justify="right")
            table.add_column("Errors", style="red")
            
            for entry in history_entries:
                user_name = "All Users" if not entry.user else entry.user.user_name
                timestamp = entry.sync_timestamp.strftime("%Y-%m-%d %H:%M:%S")
                status_color = "green" if entry.status == "success" else "red"
                status = f"[{status_color}]{entry.status}[/{status_color}]"
                
                events = f"C:{entry.events_created} U:{entry.events_updated} D:{entry.events_deleted}"
                error_msg = entry.error_message[:50] + "..." if entry.error_message and len(entry.error_message) > 50 else entry.error_message or ""
                
                table.add_row(
                    timestamp,
                    user_name,
                    status,
                    str(entry.total_shifts_processed),
                    events,
                    error_msg,
                )
            
            console.print(table)
            
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"Failed to retrieve history: {e}")
        rprint(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
def status():
    """Show current configuration and status."""
    try:
        settings = get_settings()
        
        rprint("[bold]Swap Configuration Status[/bold]")
        rprint(f"Database URL: {settings.database.url}")
        rprint(f"Spreadsheet ID: {settings.google.spreadsheet_id}")
        rprint(f"Range: {settings.google.range_name}")
        rprint(f"Timezone: {settings.google.timezone}")
        rprint(f"Service Account: {settings.google.service_account_file}")
        
        rprint("\\n[bold]Configured Users:[/bold]")
        for i, user in enumerate(settings.users, 1):
            rprint(f"{i}. {user.user_name} -> {user.calendar_name}")
            rprint(f"   Shared with: {', '.join(user.emails_to_share)}")
        
        # Check database
        try:
            init_database()
            db_session = next(get_database())
            
            try:
                user_repo = UserRepository(db_session)
                users = user_repo.get_all()
                rprint(f"\\n[bold]Database Users:[/bold] {len(users)} users")
                
                sync_history_repo = SyncHistoryRepository(db_session)
                latest_sync = sync_history_repo.get_latest()
                if latest_sync:
                    rprint(f"[bold]Last Sync:[/bold] {latest_sync.sync_timestamp} ({latest_sync.status})")
                else:
                    rprint("[yellow]No synchronization history found.[/yellow]")
                    
            finally:
                db_session.close()
                
        except Exception as e:
            rprint(f"[red]Database error: {e}[/red]")
        
    except Exception as e:
        logger.error(f"Failed to show status: {e}")
        rprint(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--force", is_flag=True, help="Force database initialization")
def init_db(force: bool):
    """Initialize the database."""
    try:
        if force:
            rprint("[yellow]Force initializing database...[/yellow]")
        else:
            rprint("Initializing database...")
        
        init_database()
        rprint("[green]Database initialized successfully![/green]")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        rprint(f"[red]Error: {e}[/red]")
        sys.exit(1)


def _display_sync_results(results: dict):
    """Display synchronization results in a nice format."""
    rprint("\\n[bold green]Synchronization Results[/bold green]")
    
    table = Table()
    table.add_column("Metric", style="cyan")
    table.add_column("Count", justify="right", style="magenta")
    
    table.add_row("Users Processed", str(results["users_processed"]))
    table.add_row("Total Shifts", str(results["total_shifts_processed"]))
    table.add_row("Events Created", str(results["total_events_created"]))
    table.add_row("Events Updated", str(results["total_events_updated"]))
    table.add_row("Events Deleted", str(results["total_events_deleted"]))
    
    console.print(table)
    
    if results["errors"]:
        rprint("\\n[bold red]Errors:[/bold red]")
        for error in results["errors"]:
            rprint(f"  [red]• {error}[/red]")
    else:
        rprint("\\n[green]✓ Synchronization completed successfully![/green]")


if __name__ == "__main__":
    cli()
