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
    notebook_id: str = typer.Argument(..., help="Notebook ID to perform research in"),
    topic: str = typer.Argument(..., help="Research topic or query"),
    deep: bool = typer.Option(
        False, "--deep", "-d", help="Use deep research (more comprehensive)"
    ),
    source: str = typer.Option(
        "web", "--source", "-s", help="Search source: 'web' or 'drive'"
    ),
) -> None:
    """Start a web research session on a topic.

    Research is ASYNC - this returns a task_id immediately.
    Use 'pynotebooklm research poll' to check status and get results.

    Results are stored on NotebookLM's servers and persist in the notebook.
    """
    from pynotebooklm.research import ResearchType

    async def _run() -> None:
        auth = AuthManager()
        if not auth.is_authenticated():
            console.print("[red]Not authenticated. Run 'pynotebooklm auth login'[/red]")
            raise typer.Exit(1)

        research_type = ResearchType.DEEP if deep else ResearchType.FAST

        async with BrowserSession(auth) as session:
            research = ResearchDiscovery(session)
            result = await research.start_research(
                notebook_id=notebook_id,
                query=topic,
                source=source,
                mode=research_type,
            )

            console.print("[green]✓ Started research session[/green]")
            console.print(f"  Notebook: [cyan]{notebook_id}[/cyan]")
            console.print(f"  Task ID: [cyan]{result.task_id}[/cyan]")
            console.print(f"  Query: {result.query}")
            console.print(f"  Mode: {result.mode}")
            console.print(f"  Source: {result.source}")
            console.print(f"  Status: {result.status.value}")
            console.print()
            console.print(
                "[dim]Use 'pynotebooklm research poll <notebook_id>' to check status[/dim]"
            )

    asyncio.run(_run())


@research_app.command("poll")
def poll_research(
    notebook_id: str = typer.Argument(..., help="Notebook ID to poll research for"),
) -> None:
    """Poll for research results.

    Check the status of an ongoing research session and get results.
    Call this after 'research start' to see discovered sources.
    """

    async def _run() -> None:
        auth = AuthManager()
        if not auth.is_authenticated():
            console.print("[red]Not authenticated. Run 'pynotebooklm auth login'[/red]")
            raise typer.Exit(1)

        async with BrowserSession(auth) as session:
            research = ResearchDiscovery(session)
            result = await research.poll_research(notebook_id)

            if not result or result.status.value == "no_research":
                console.print(
                    "[yellow]No active research found for this notebook.[/yellow]"
                )
                return

            console.print("[bold]Research Status[/bold]")
            console.print(f"  Task ID: [cyan]{result.task_id}[/cyan]")
            console.print(f"  Query: {result.query}")
            console.print(f"  Mode: {result.mode}")
            console.print(
                f"  Status: [{'green' if result.status.value == 'completed' else 'yellow'}]{result.status.value}[/]"
            )
            console.print(f"  Sources found: {result.source_count}")

            if result.summary:
                console.print(f"\n[bold]Summary:[/bold]\n{result.summary}")

            if result.report:
                console.print(f"\n[bold]Report:[/bold]\n{result.report[:500]}...")

            if result.results:
                console.print(
                    f"\n[bold]Discovered Sources ({len(result.results)}):[/bold]"
                )
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("#", style="dim", justify="right")
                table.add_column("Title", style="white", max_width=40)
                table.add_column("Type", style="green")
                table.add_column("URL", style="cyan", max_width=50)

                for src in result.results[:10]:  # Show first 10
                    table.add_row(
                        str(src.index),
                        src.title[:40] if src.title else "—",
                        src.result_type_name,
                        src.url[:50] if src.url else "—",
                    )

                console.print(table)

                if len(result.results) > 10:
                    console.print(f"  ... and {len(result.results) - 10} more")

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
