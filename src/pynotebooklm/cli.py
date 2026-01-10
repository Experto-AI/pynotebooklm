import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from pynotebooklm.auth import AuthManager
from pynotebooklm.chat import ChatSession
from pynotebooklm.mindmaps import (
    MindMapGenerator,
    export_to_freemind,
    export_to_json,
    export_to_opml,
)
from pynotebooklm.notebooks import NotebookManager
from pynotebooklm.research import ResearchDiscovery
from pynotebooklm.session import BrowserSession
from pynotebooklm.sources import SourceManager

app = typer.Typer(help="PyNotebookLM CLI - Management Tools")
auth_app = typer.Typer(help="Authentication management")
notebooks_app = typer.Typer(help="Notebook management")
sources_app = typer.Typer(help="Source management")
research_app = typer.Typer(help="Research discovery")
mindmap_app = typer.Typer(help="Mind map generation and export")
query_app = typer.Typer(help="Chat and query tools")

app.add_typer(auth_app, name="auth")
app.add_typer(notebooks_app, name="notebooks")
app.add_typer(sources_app, name="sources")
app.add_typer(research_app, name="research")
app.add_typer(mindmap_app, name="mindmap")
app.add_typer(query_app, name="query")

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
# Mind Map Commands
# =============================================================================


@mindmap_app.command("create")
def create_mindmap(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    title: str = typer.Option("Mind Map", "--title", "-t", help="Mind map title"),
) -> None:
    """Create a mind map from all sources in a notebook.

    Generates a hierarchical mind map visualization of the notebook's
    content. The mind map is saved to the notebook and can be viewed
    in the NotebookLM web interface.
    """

    async def _run() -> None:
        auth = AuthManager()
        if not auth.is_authenticated():
            console.print("[red]Not authenticated. Run 'pynotebooklm auth login'[/red]")
            raise typer.Exit(1)

        async with BrowserSession(auth) as session:
            generator = MindMapGenerator(session)

            console.print(
                f"[dim]Generating mind map for notebook {notebook_id}...[/dim]"
            )

            try:
                mindmap = await generator.create(notebook_id, title=title)
                console.print("[green]✓ Created mind map successfully![/green]")
                console.print(f"  ID: [cyan]{mindmap.id}[/cyan]")
                console.print(f"  Title: [bold]{mindmap.title}[/bold]")
                console.print(f"  Sources: {len(mindmap.source_ids)}")

                # Show root structure if available
                root = mindmap.get_root_node()
                if root:
                    console.print(f"  Root: [magenta]{root.name}[/magenta]")
                    console.print(f"  Top-level topics: {len(root.children)}")

            except ValueError as e:
                console.print(f"[red]Error: {e}[/red]")
                raise typer.Exit(1) from e
            except Exception as e:
                console.print(f"[red]Failed to create mind map: {e}[/red]")
                raise typer.Exit(1) from e

    asyncio.run(_run())


@mindmap_app.command("list")
def list_mindmaps(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
) -> None:
    """List all mind maps in a notebook."""

    async def _run() -> None:
        auth = AuthManager()
        if not auth.is_authenticated():
            console.print("[red]Not authenticated. Run 'pynotebooklm auth login'[/red]")
            raise typer.Exit(1)

        async with BrowserSession(auth) as session:
            generator = MindMapGenerator(session)
            mindmaps = await generator.list(notebook_id)

            if not mindmaps:
                console.print(f"No mind maps found in notebook {notebook_id}.")
                return

            table = Table(
                title=f"Mind Maps in {notebook_id[:8]}...",
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("#", style="dim", justify="right")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Title", style="white")
            table.add_column("Sources", style="green", justify="right")
            table.add_column("Created", style="blue")

            for i, mm in enumerate(mindmaps, 1):
                created = (
                    mm.created_at.strftime("%Y-%m-%d %H:%M") if mm.created_at else "—"
                )
                table.add_row(
                    str(i),
                    mm.id,
                    mm.title,
                    str(len(mm.source_ids)),
                    created,
                )

            console.print(table)

    asyncio.run(_run())


@mindmap_app.command("export")
def export_mindmap(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    mindmap_id: str = typer.Argument(..., help="Mind map ID"),
    format: str = typer.Option(
        "json", "--format", "-f", help="Export format: json, opml, or freemind"
    ),
    output: str = typer.Option(
        None, "--output", "-o", help="Output file path (default: mindmap.<format>)"
    ),
) -> None:
    """Export a mind map to JSON, OPML, or FreeMind format.

    Supported formats:
    - json: Standard JSON with name/children structure
    - opml: OPML 2.0 (importable by most outliners)
    - freemind: FreeMind .mm format (compatible with Freeplane)
    """

    async def _run() -> None:
        auth = AuthManager()
        if not auth.is_authenticated():
            console.print("[red]Not authenticated. Run 'pynotebooklm auth login'[/red]")
            raise typer.Exit(1)

        async with BrowserSession(auth) as session:
            generator = MindMapGenerator(session)

            console.print(f"[dim]Fetching mind map {mindmap_id}...[/dim]")

            mindmap = await generator.get(notebook_id, mindmap_id)
            if not mindmap:
                console.print(f"[red]Mind map not found: {mindmap_id}[/red]")
                raise typer.Exit(1)

            if not mindmap.mind_map_json:
                console.print("[red]Mind map has no content[/red]")
                raise typer.Exit(1)

            # Determine output format and filename
            format_lower = format.lower()
            extensions = {"json": ".json", "opml": ".opml", "freemind": ".mm"}
            if format_lower not in extensions:
                console.print(
                    f"[red]Invalid format: {format}. Use json, opml, or freemind[/red]"
                )
                raise typer.Exit(1)

            output_path = (
                Path(output) if output else Path(f"mindmap{extensions[format_lower]}")
            )

            # Export to selected format
            try:
                if format_lower == "json":
                    content = export_to_json(mindmap.mind_map_json, pretty=True)
                elif format_lower == "opml":
                    content = export_to_opml(mindmap.mind_map_json, title=mindmap.title)
                else:  # freemind
                    content = export_to_freemind(
                        mindmap.mind_map_json, title=mindmap.title
                    )

                output_path.write_text(content, encoding="utf-8")
                console.print(f"[green]✓ Exported to: {output_path}[/green]")
                console.print(f"  Format: {format_lower}")
                console.print(f"  Size: {len(content)} bytes")

            except ValueError as e:
                console.print(f"[red]Export failed: {e}[/red]")
                raise typer.Exit(1) from e

    asyncio.run(_run())


# =============================================================================
# Query Commands
# =============================================================================


@query_app.command("ask")
def query_ask(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    question: str = typer.Argument(..., help="Question to ask"),
) -> None:
    """Ask a question to the notebook."""

    async def _run() -> None:
        auth = AuthManager()
        if not auth.is_authenticated():
            console.print("[red]Not authenticated. Run 'pynotebooklm auth login'[/red]")
            raise typer.Exit(1)

        async with BrowserSession(auth) as session:
            chat = ChatSession(session)
            console.print(f"[dim]Asking notebook {notebook_id}...[/dim]")

            answer = await chat.query(notebook_id, question)

            console.print("\n[bold]Answer:[/bold]")
            console.print(answer)

    asyncio.run(_run())


@query_app.command("configure")
def query_configure(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    goal: str = typer.Option("default", help="Goal: default, learning, custom"),
    prompt: str = typer.Option(
        None, help="Custom system prompt (required for custom goal)"
    ),
    length: str = typer.Option(
        "default", help="Response length: default, longer, shorter"
    ),
) -> None:
    """Configure chat settings (tone, style, length)."""

    async def _run() -> None:
        auth = AuthManager()
        if not auth.is_authenticated():
            console.print("[red]Not authenticated.[/red]")
            raise typer.Exit(1)

        async with BrowserSession(auth) as session:
            chat = ChatSession(session)
            await chat.configure(
                notebook_id, goal=goal, custom_prompt=prompt, length=length
            )
            console.print(
                f"[green]✓ Configured chat settings for {notebook_id}[/green]"
            )

    asyncio.run(_run())


@query_app.command("summary")
def query_summary(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
) -> None:
    """Get AI summary of the notebook."""

    async def _run() -> None:
        auth = AuthManager()
        if not auth.is_authenticated():
            console.print("[red]Not authenticated.[/red]")
            raise typer.Exit(1)

        async with BrowserSession(auth) as session:
            chat = ChatSession(session)
            result = await chat.get_notebook_summary(notebook_id)

            console.print("\n[bold]Summary:[/bold]")
            console.print(result["summary"])

            if result["suggested_topics"]:
                console.print("\n[bold]Suggested Topics:[/bold]")
                for topic in result["suggested_topics"]:
                    console.print(f"- {topic['question']}")

    asyncio.run(_run())


@query_app.command("briefing")
def query_briefing(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
) -> None:
    """Create a Briefing Doc from the notebook."""

    async def _run() -> None:
        auth = AuthManager()
        if not auth.is_authenticated():
            console.print("[red]Not authenticated.[/red]")
            raise typer.Exit(1)

        async with BrowserSession(auth) as session:
            chat = ChatSession(session)
            console.print("[dim]Creating briefing doc...[/dim]")
            result = await chat.create_briefing(notebook_id)

            console.print("[green]✓ Briefing generation started[/green]")
            if result.get("artifact_id"):
                console.print(f"  Artifact ID: {result['artifact_id']}")

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
