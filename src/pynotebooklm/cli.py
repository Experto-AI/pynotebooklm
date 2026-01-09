import asyncio

import typer
from rich.console import Console
from rich.table import Table

from pynotebooklm.auth import AuthManager
from pynotebooklm.notebooks import NotebookManager
from pynotebooklm.research import ResearchDiscovery
from pynotebooklm.session import BrowserSession
from pynotebooklm.sources import SourceManager

app = typer.Typer(help="PyNotebookLM CLI - Management Tools")
auth_app = typer.Typer(help="Authentication management")
notebooks_app = typer.Typer(help="Notebook management")
sources_app = typer.Typer(help="Source management")
research_app = typer.Typer(help="Research discovery")

app.add_typer(auth_app, name="auth")
app.add_typer(notebooks_app, name="notebooks")
app.add_typer(sources_app, name="sources")
app.add_typer(research_app, name="research")

console = Console()


# =============================================================================
# Auth Commands
# =============================================================================


@auth_app.command("login")
def login(timeout: int = typer.Option(300, help="Timeout in seconds")) -> None:
    """Login to Google NotebookLM."""

    async def _run_login() -> None:
        auth = AuthManager()
        try:
            await auth.login(timeout=timeout)
            console.print("[green]✓ Login successful![/green]")
            console.print(f"  Auth file: {auth.auth_path}")
        except Exception as e:
            console.print(f"[red]Login failed: {e}[/red]")
            raise typer.Exit(1) from e

    asyncio.run(_run_login())


@auth_app.command("check")
def check() -> None:
    """Check authentication status."""
    auth = AuthManager()
    if auth.is_authenticated():
        console.print("[green]✓ Authenticated: True[/green]")
        console.print(f"  Auth file: {auth.auth_path}")
        if auth._auth_state and auth._auth_state.expires_at:
            console.print(f"  Expires: {auth._auth_state.expires_at.isoformat()}")
    else:
        console.print("[red]✗ Authenticated: False[/red]")
        console.print("  Run 'pynotebooklm auth login' to authenticate")
        raise typer.Exit(1)


@auth_app.command("logout")
def logout() -> None:
    """Log out and clear authentication state."""
    auth = AuthManager()
    auth.logout()
    console.print("[green]✓ Logged out successfully[/green]")


# =============================================================================
# Notebook Commands
# =============================================================================


@notebooks_app.command("list")
def list_notebooks(
    detailed: bool = typer.Option(
        False, "--detailed", "-d", help="Show detailed information"
    ),
    short: bool = typer.Option(False, "--short", "-s", help="Show only IDs and names"),
) -> None:
    """List all notebooks."""

    async def _run() -> None:
        auth = AuthManager()
        if not auth.is_authenticated():
            console.print("[red]Not authenticated. Run 'pynotebooklm auth login'[/red]")
            raise typer.Exit(1)

        async with BrowserSession(auth) as session:
            manager = NotebookManager(session)
            notebooks = await manager.list()

            if not notebooks:
                console.print("No notebooks found.")
                return

            table = Table(
                title="Your Notebooks", show_header=True, header_style="bold magenta"
            )
            table.add_column("#", style="dim", justify="right")

            if short:
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("Name", style="white")
                for i, nb in enumerate(notebooks, 1):
                    table.add_row(str(i), nb.id, nb.name)
            elif detailed:
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("Name", style="white")
                table.add_column("Sources", style="green", justify="right")
                table.add_column("Created At", style="blue")
                for i, nb in enumerate(notebooks, 1):
                    created = (
                        nb.created_at.strftime("%Y-%m-%d %H:%M")
                        if nb.created_at
                        else "Unknown"
                    )
                    table.add_row(str(i), nb.id, nb.name, str(nb.source_count), created)
            else:
                # Standard view
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("Name", style="white")
                table.add_column("Sources", style="green", justify="right")
                for i, nb in enumerate(notebooks, 1):
                    table.add_row(str(i), nb.id, nb.name, str(nb.source_count))

            console.print(table)

    asyncio.run(_run())


@notebooks_app.command("create")
def create_notebook(name: str = typer.Argument(..., help="Notebook name")) -> None:
    """Create a new notebook."""

    async def _run() -> None:
        auth = AuthManager()
        async with BrowserSession(auth) as session:
            manager = NotebookManager(session)
            nb = await manager.create(name)
            console.print(
                f"[green]✓ Created notebook: [bold]{nb.name}[/bold] ({nb.id})[/green]"
            )

    asyncio.run(_run())


@notebooks_app.command("delete")
def delete_notebook(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete a notebook."""

    async def _run() -> None:
        auth = AuthManager()
        async with BrowserSession(auth) as session:
            manager = NotebookManager(session)

            if not force:
                confirm = typer.confirm(
                    f"Are you sure you want to delete notebook {notebook_id}?"
                )
                if not confirm:
                    console.print("Aborted.")
                    return

            await manager.delete(notebook_id, confirm=True)
            console.print(f"[green]✓ Deleted notebook: {notebook_id}[/green]")

    asyncio.run(_run())


# =============================================================================
# Source Commands
# =============================================================================


@sources_app.command("add")
def add_source(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    url: str = typer.Argument(..., help="URL to add"),
) -> None:
    """Add a URL source to a notebook."""

    async def _run() -> None:
        auth = AuthManager()
        async with BrowserSession(auth) as session:
            manager = SourceManager(session)
            source = await manager.add_url(notebook_id, url)
            console.print(
                f"[green]✓ Added source: [bold]{source.title}[/bold] ({source.id})[/green]"
            )

    asyncio.run(_run())


@sources_app.command("list")
def list_sources(notebook_id: str = typer.Argument(..., help="Notebook ID")) -> None:
    """List sources in a notebook."""

    async def _run() -> None:
        auth = AuthManager()
        async with BrowserSession(auth) as session:
            manager = SourceManager(session)
            sources = await manager.list_sources(notebook_id)

            if not sources:
                console.print(f"No sources found in notebook {notebook_id}.")
                return

            table = Table(title=f"Sources in {notebook_id}")
            table.add_column("#", style="dim", justify="right")
            table.add_column("ID", style="cyan")
            table.add_column("Title", style="magenta")
            table.add_column("Type", style="green")

            for i, src in enumerate(sources, 1):
                table.add_row(str(i), src.id, src.title, src.type.value)

            console.print(table)

    asyncio.run(_run())


@sources_app.command("delete")
def delete_source(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    source_id: str = typer.Argument(..., help="Source ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete a source from a notebook."""

    async def _run() -> None:
        auth = AuthManager()
        async with BrowserSession(auth) as session:
            manager = SourceManager(session)

            if not force:
                confirm = typer.confirm(
                    f"Are you sure you want to delete source {source_id} from notebook {notebook_id}?"
                )
                if not confirm:
                    console.print("Aborted.")
                    return

            await manager.delete(notebook_id, source_id)
            console.print(f"[green]✓ Deleted source: {source_id}[/green]")

    asyncio.run(_run())


# =============================================================================
# Research Commands
# =============================================================================


@research_app.command("start")
def start_research(
    topic: str = typer.Argument(..., help="Research topic or query"),
    notebook_id: str = typer.Option(
        None, "--notebook", "-n", help="Notebook ID to associate research with"
    ),
    deep: bool = typer.Option(
        False, "--deep", "-d", help="Use deep research (more comprehensive)"
    ),
) -> None:
    """Start a web research session on a topic."""
    from pynotebooklm.research import ResearchType

    async def _run() -> None:
        auth = AuthManager()
        if not auth.is_authenticated():
            console.print("[red]Not authenticated. Run 'pynotebooklm auth login'[/red]")
            raise typer.Exit(1)

        research_type = ResearchType.DEEP if deep else ResearchType.FAST

        async with BrowserSession(auth) as session:
            research = ResearchDiscovery(session)
            result = await research.start_web_research(
                topic,
                notebook_id=notebook_id,
                research_type=research_type,
            )

            console.print("[green]✓ Started research session[/green]")
            console.print(f"  ID: [cyan]{result.id}[/cyan]")
            console.print(f"  Topic: {result.topic}")
            console.print(f"  Type: {research_type.value}")
            console.print(f"  Status: {result.status.value}")

            if result.error_message:
                console.print(f"  [yellow]Note: {result.error_message}[/yellow]")

            if result.results:
                console.print(f"  Results: {len(result.results)} found")

    asyncio.run(_run())


@research_app.command("status")
def research_status(
    research_id: str = typer.Argument(..., help="Research session ID"),
) -> None:
    """Check the status of a research session."""

    async def _run() -> None:
        auth = AuthManager()
        if not auth.is_authenticated():
            console.print("[red]Not authenticated. Run 'pynotebooklm auth login'[/red]")
            raise typer.Exit(1)

        async with BrowserSession(auth) as session:
            research = ResearchDiscovery(session)

            try:
                result = await research.get_status(research_id)

                console.print(f"[bold]Research Session: {result.id}[/bold]")
                console.print(f"  Topic: {result.topic}")
                console.print(f"  Status: {result.status.value}")

                if result.started_at:
                    console.print(f"  Started: {result.started_at.isoformat()}")
                if result.completed_at:
                    console.print(f"  Completed: {result.completed_at.isoformat()}")

                if result.results:
                    console.print(f"\n[bold]Results ({len(result.results)}):[/bold]")
                    table = Table(show_header=True, header_style="bold magenta")
                    table.add_column("#", style="dim", justify="right")
                    table.add_column("Title", style="white")
                    table.add_column("URL", style="cyan")
                    table.add_column("Score", style="green", justify="right")

                    for i, res in enumerate(result.results, 1):
                        url = (
                            res.url[:50] + "..."
                            if res.url and len(res.url) > 50
                            else (res.url or "N/A")
                        )
                        table.add_row(
                            str(i),
                            (
                                res.title[:40] + "..."
                                if len(res.title) > 40
                                else res.title
                            ),
                            url,
                            f"{res.relevance_score:.2f}",
                        )

                    console.print(table)

                if result.error_message:
                    console.print(f"\n[red]Error: {result.error_message}[/red]")

            except ValueError as e:
                console.print(f"[red]Error: {e}[/red]")
                raise typer.Exit(1) from e

    asyncio.run(_run())


@research_app.command("import")
def import_research(
    notebook_id: str = typer.Argument(..., help="Target notebook ID"),
    research_id: str = typer.Argument(..., help="Research session ID"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum results to import"),
) -> None:
    """Import research results as sources into a notebook."""

    async def _run() -> None:
        auth = AuthManager()
        if not auth.is_authenticated():
            console.print("[red]Not authenticated. Run 'pynotebooklm auth login'[/red]")
            raise typer.Exit(1)

        async with BrowserSession(auth) as session:
            research = ResearchDiscovery(session)

            try:
                # Get the research session
                research_session = await research.get_status(research_id)

                if not research_session.results:
                    console.print("[yellow]No results to import.[/yellow]")
                    return

                # Limit the results
                results_to_import = research_session.results[:limit]

                console.print(
                    f"Importing {len(results_to_import)} results to notebook {notebook_id}..."
                )

                source_ids = await research.import_research_results(
                    notebook_id, results_to_import
                )

                console.print(
                    f"[green]✓ Imported {len(source_ids)} sources successfully[/green]"
                )

                for source_id in source_ids:
                    console.print(f"  - {source_id}")

            except ValueError as e:
                console.print(f"[red]Error: {e}[/red]")
                raise typer.Exit(1) from e

    asyncio.run(_run())


@research_app.command("sync")
def sync_drive(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
) -> None:
    """Sync Google Drive sources for a notebook."""

    async def _run() -> None:
        auth = AuthManager()
        if not auth.is_authenticated():
            console.print("[red]Not authenticated. Run 'pynotebooklm auth login'[/red]")
            raise typer.Exit(1)

        async with BrowserSession(auth) as session:
            research = ResearchDiscovery(session)

            count = await research.sync_drive_sources(notebook_id)

            if count > 0:
                console.print(f"[green]✓ Synced {count} Drive source(s)[/green]")
            else:
                console.print("[yellow]No Drive sources to sync.[/yellow]")

    asyncio.run(_run())


# =============================================================================
# Root Commands (Compatibility & Utilities)
# =============================================================================


@app.command("login", hidden=True)
def root_login(timeout: int = typer.Option(300, help="Timeout in seconds")) -> None:
    """Compatibility wrapper for 'pynotebooklm login'."""
    login(timeout)


@app.command("check", hidden=True)
def root_check() -> None:
    """Compatibility wrapper for 'pynotebooklm check'."""
    check()


if __name__ == "__main__":
    app()
