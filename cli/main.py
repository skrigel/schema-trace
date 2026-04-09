import click
from rich.console import Console
from rich.table import Table
from pathlib import Path
import sys
import webbrowser

from cli.config import load_config, save_config, get_api_key, CLIConfig
from cli.client import APIClient, SchemaTraceAPIError

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """
    SchemaTrace CLI - Track your database schema evolution

    Quick Start:
      1. schematrace config --set-api-url http://localhost:8000
      2. schematrace init --project "my-app"
      3. schematrace scan ./migrations --project "my-app"
      4. schematrace open
    """
    pass


@cli.command()
@click.option('--project', required=True, help='Project name')
@click.option('--description', help='Project description')
def init(project: str, description: str):
    """Initialize a new project"""
    try:
        config = load_config()
        client = APIClient(config)

        # Create project
        console.print(f"Creating project '{project}'...")
        result = client.create_project(name=project, description=description)

        # Save as default project
        config.default_project = project
        save_config(config)

        console.print(f"[green]✓[/green] Project '{project}' created (ID: {result['id']})")
        console.print(f"[dim]Set as default project[/dim]")

    except SchemaTraceAPIError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('migrations_dir', type=click.Path(exists=True))
@click.option('--project', help='Project name (uses default if not specified)')
@click.option('--framework', type=click.Choice(['django', 'auto']), default='auto')
def scan(migrations_dir: str, project: str, framework: str):
    """
    Scan migration files and upload schema events

    NOTE: Django adapter parser is not fully implemented yet.
    This command will work once the adapter is complete.
    """
    try:
        from cli.scanner import scan_migrations

        config = load_config()

        # Determine project name
        if not project:
            project = config.default_project # type: ignore
            if not project:
                console.print("[red]Error: No project specified and no default project configured[/red]")
                console.print("Use --project flag or run: schematrace init --project <name>")
                sys.exit(1)

        client = APIClient(config)

        # Get or create project
        console.print(f"Looking up project '{project}'...")
        try:
            project_data = client.get_project_by_name(project)
        except SchemaTraceAPIError:
            console.print(f"[yellow]Project '{project}' not found. Creating it...[/yellow]")
            project_data = client.create_project(name=project)

        project_id = project_data['id']

        # Scan migrations
        console.print(f"\n[bold]Scanning migrations in {migrations_dir}...[/bold]")
        events, models_created = scan_migrations(
            Path(migrations_dir),
            project_id=project_id,
            client=client,
            framework=framework
        )

        if not events:
            console.print("[yellow]No schema events found[/yellow]")
            console.print("\n[dim]Possible reasons:[/dim]")
            console.print("  - No migration files in directory")
            console.print("  - Django adapter parser not fully implemented")
            console.print("  - Migration files are malformed")
            return

        # Upload events
        console.print(f"\nUploading {len(events)} events...")
        with console.status("[bold green]Uploading..."):
            result = client.upload_events_bulk(events)

        console.print(f"[green]✓[/green] Uploaded {result['created_count']} events")
        console.print(f"[green]✓[/green] Created {models_created} models")
        console.print(f"\n[dim]View at: {config.api_url}/docs[/dim]")

    except ImportError:
        console.print("[red]Error: Scanner module not found (cli/scanner.py)[/red]")
        console.print("The scan functionality is not yet fully implemented.")
        sys.exit(1)
    except SchemaTraceAPIError as e:
        console.print(f"[red]API Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


@cli.command()
@click.option('--url', help='Custom URL to open')
def open(url: str):
    """Open SchemaTrace web UI in browser"""
    config = load_config()
    target_url = url or f"{config.api_url}/docs"

    console.print(f"Opening {target_url} in browser...")
    webbrowser.open(target_url)


@cli.command()
@click.option('--show', is_flag=True, help='Show current configuration')
@click.option('--set-api-url', help='Set API URL')
@click.option('--set-api-key', help='Set API key')
@click.option('--set-default-project', help='Set default project')
def config(show: bool, set_api_url: str, set_api_key: str, set_default_project: str):
    """View or modify CLI configuration"""
    cfg = load_config()

    # Update configuration
    changed = False

    if set_api_key:
        cfg.api_key = set_api_key
        changed = True
        console.print("[green]✓[/green] API key updated")

    if set_api_url:
        cfg.api_url = set_api_url
        changed = True
        console.print("[green]✓[/green] API URL updated")

    if set_default_project:
        cfg.default_project = set_default_project
        changed = True
        console.print("[green]✓[/green] Default project updated")

    if changed:
        save_config(cfg)

    # Show configuration
    if show or not changed:
        console.print("\n[bold]Current Configuration:[/bold]")
        console.print(f"  API URL: {cfg.api_url}")
        console.print(f"  API Key: {'*' * 8 if cfg.api_key else '[dim]Not set[/dim]'}")
        console.print(f"  Default Project: {cfg.default_project or '[dim]Not set[/dim]'}")
        console.print(f"\n[dim]Config file: ~/.schematrace/config.json[/dim]")

        # Check if environment variables are set
        import os
        if os.getenv("SCHEMATRACE_API_URL"):
            console.print(f"\n[yellow]Note: SCHEMATRACE_API_URL environment variable is set[/yellow]")
        if os.getenv("SCHEMATRACE_API_KEY"):
            console.print(f"[yellow]Note: SCHEMATRACE_API_KEY environment variable is set[/yellow]")


@cli.command()
def projects():
    """List all projects"""
    try:
        config = load_config()
        client = APIClient(config)

        console.print("[bold]Fetching projects...[/bold]")
        projects_list = client.list_projects()

        if not projects_list:
            console.print("[yellow]No projects found[/yellow]")
            console.print("Create one with: [cyan]schematrace init --project <name>[/cyan]")
            return

        # Create rich table
        table = Table(title="Projects")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Description", style="white")
        table.add_column("Created", style="dim")

        for proj in projects_list:
            table.add_row(
                str(proj['id']),
                proj['name'],
                proj.get('description', ''),
                proj['created_at'][:10]  # Just the date part
            )

        console.print(table)

        # Show default project indicator
        if config.default_project:
            console.print(f"\n[dim]Default project: {config.default_project}[/dim]")

    except SchemaTraceAPIError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('project_name')
def models(project_name: str):
    """List models in a project"""
    try:
        config = load_config()
        client = APIClient(config)

        # Get project by name
        console.print(f"Looking up project '{project_name}'...")
        project_data = client.get_project_by_name(project_name)
        project_id = project_data['id']

        # Get models
        models_list = client.list_models(project_id=project_id)

        if not models_list:
            console.print(f"[yellow]No models found in project '{project_name}'[/yellow]")
            console.print("Models are created automatically when you scan migrations")
            return

        # Create rich table
        table = Table(title=f"Models in {project_name}")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Description", style="white")

        for model in models_list:
            table.add_row(
                str(model['id']),
                model['name'],
                model.get('description', '')
            )

        console.print(table)

    except SchemaTraceAPIError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('model_id', type=int)
def events(model_id: int):
    """View event history for a model"""
    try:
        config = load_config()
        client = APIClient(config)

        # Get model info
        console.print(f"Fetching events for model {model_id}...")
        model_data = client.get_model(model_id)

        # Get events
        events_list = client.list_model_events(model_id)

        if not events_list:
            console.print(f"[yellow]No events found for model '{model_data['name']}'[/yellow]")
            return

        # Create rich table
        table = Table(title=f"Schema Events for {model_data['name']}")
        table.add_column("Timestamp", style="dim")
        table.add_column("Event", style="cyan")
        table.add_column("Field", style="green")
        table.add_column("Risk", style="yellow")

        for event in events_list:
            # Color code risk levels
            risk_color = {
                'low': 'green',
                'medium': 'yellow',
                'high': 'red'
            }.get(event['risk_level'], 'white')

            table.add_row(
                event['timestamp'][:19],  # Remove milliseconds
                event['event_type'],
                event['field_name'],
                f"[{risk_color}]{event['risk_level']}[/{risk_color}]"
            )

        console.print(table)
        console.print(f"\n[dim]Total events: {len(events_list)}[/dim]")

    except SchemaTraceAPIError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli()
