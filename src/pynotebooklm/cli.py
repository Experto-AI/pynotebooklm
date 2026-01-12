import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from pynotebooklm.auth import AuthManager
from pynotebooklm.chat import ChatSession
from pynotebooklm.content import (
    AudioFormat,
    AudioLength,
    ContentGenerator,
    InfographicDetailLevel,
    InfographicOrientation,
    SlideDeckFormat,
    SlideDeckLength,
    VideoFormat,
    VideoStyle,
)
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
from pynotebooklm.study import FlashcardDifficulty, StudyManager

app = typer.Typer(help="PyNotebookLM CLI - Management Tools", no_args_is_help=True)
auth_app = typer.Typer(help="Authentication management", no_args_is_help=True)
notebooks_app = typer.Typer(help="Notebook management", no_args_is_help=True)
sources_app = typer.Typer(help="Source management", no_args_is_help=True)
research_app = typer.Typer(help="Research discovery", no_args_is_help=True)
mindmap_app = typer.Typer(help="Mind map generation and export", no_args_is_help=True)
query_app = typer.Typer(help="Chat and query tools", no_args_is_help=True)
generate_app = typer.Typer(
    help="Content generation (audio, video, infographic, slides)",
    no_args_is_help=True,
)
study_app = typer.Typer(help="Study tools (flashcards, quiz, data table)", no_args_is_help=True)

app.add_typer(auth_app, name="auth")
app.add_typer(notebooks_app, name="notebooks")
app.add_typer(sources_app, name="sources")
app.add_typer(research_app, name="research")
app.add_typer(mindmap_app, name="mindmap")
app.add_typer(query_app, name="query")
app.add_typer(generate_app, name="generate")
app.add_typer(study_app, name="study")

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
            with console.status("[bold green]Fetching notebooks..."):
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
            with console.status(f"[bold green]Creating notebook '{name}'..."):
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

            with console.status(f"[bold red]Deleting notebook {notebook_id}..."):
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
            with console.status(f"[bold green]Adding source {url}..."):
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
            with console.status(f"[bold green]Fetching sources for {notebook_id}..."):
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

            with console.status(f"[bold red]Deleting source {source_id}..."):
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
            with console.status(f"[bold green]Starting research on '{topic}'..."):
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
    auto_import: bool = typer.Option(
        False,
        "--auto-import",
        "-a",
        help="Automatically import all discovered sources when research is completed",
    ),
) -> None:
    """Poll for research results.

    Check the status of an ongoing research session and get results.
    Call this after 'research start' to see discovered sources.

    Use --auto-import to automatically add discovered sources to the notebook
    when research is completed. This saves a separate 'research import' step.
    """

    async def _run() -> None:
        auth = AuthManager()
        if not auth.is_authenticated():
            console.print("[red]Not authenticated. Run 'pynotebooklm auth login'[/red]")
            raise typer.Exit(1)

        async with BrowserSession(auth) as session:
            research = ResearchDiscovery(session)
            with console.status(
                f"[bold green]Polling research status for {notebook_id}..."
            ):
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

            # Auto-import if requested and research is completed
            if auto_import and result.status.value == "completed" and result.results:
                console.print("\n[bold green]Auto-importing sources...[/bold green]")
                with console.status("[bold green]Importing sources to notebook..."):
                    imported = await research.import_research_sources(
                        notebook_id=notebook_id,
                        task_id=result.task_id,
                        sources=result.results,
                    )
                console.print(
                    f"[green]✓ Imported {len(imported)} sources to notebook[/green]"
                )
                if imported:
                    for imp_src in imported[:5]:
                        console.print(f"  - {imp_src.title} ({imp_src.id[:8]}...)")
                    if len(imported) > 5:
                        console.print(f"  ... and {len(imported) - 5} more")

            elif auto_import and result.status.value != "completed":
                console.print(
                    "\n[yellow]Note: --auto-import skipped (research not completed yet)[/yellow]"
                )
                console.print(
                    "[dim]Poll again when status is 'completed' to auto-import sources[/dim]"
                )

    asyncio.run(_run())


@research_app.command("import")
def import_research(
    notebook_id: str = typer.Argument(..., help="Notebook ID to import sources into"),
    indices: str = typer.Option(
        None,
        "--indices",
        "-i",
        help="Comma-separated indices of sources to import (e.g., '0,1,2'). Imports all if not specified.",
    ),
    include_report: bool = typer.Option(
        True,
        "--include-report/--no-report",
        help="For deep research, also import the AI report as a text source",
    ),
) -> None:
    """Import discovered research sources into the notebook.

    This command imports sources that were discovered during research.
    Call this after 'research poll' shows status='completed'.

    By default, imports all discovered sources. Use --indices to import
    specific sources only (e.g., --indices 0,2,5 to import sources at
    those positions in the results list).

    For deep research, the AI-generated report is also added as a text
    source by default. Use --no-report to skip this.
    """
    from pynotebooklm.sources import SourceManager

    async def _run() -> None:
        auth = AuthManager()
        if not auth.is_authenticated():
            console.print("[red]Not authenticated. Run 'pynotebooklm auth login'[/red]")
            raise typer.Exit(1)

        async with BrowserSession(auth) as session:
            research = ResearchDiscovery(session)

            # First poll to get current research status
            with console.status(
                f"[bold green]Checking research status for {notebook_id}..."
            ):
                result = await research.poll_research(notebook_id)

            if not result or result.status.value == "no_research":
                console.print(
                    "[red]No research found for this notebook.[/red]\n"
                    "[dim]Run 'pynotebooklm research start' first.[/dim]"
                )
                raise typer.Exit(1)

            if result.status.value != "completed":
                console.print(
                    f"[yellow]Research is still in progress (status: {result.status.value})[/yellow]\n"
                    "[dim]Wait for completion, then run this command again.[/dim]"
                )
                raise typer.Exit(1)

            if not result.results:
                console.print("[yellow]No sources found in research results.[/yellow]")
                return

            # Parse indices if provided
            sources_to_import = result.results
            if indices:
                try:
                    index_list = [int(i.strip()) for i in indices.split(",")]
                    invalid_indices = [
                        i for i in index_list if i < 0 or i >= len(result.results)
                    ]
                    if invalid_indices:
                        console.print(
                            f"[red]Invalid indices: {invalid_indices}. "
                            f"Valid range is 0-{len(result.results) - 1}.[/red]"
                        )
                        raise typer.Exit(1)
                    sources_to_import = [result.results[i] for i in index_list]
                except ValueError:
                    console.print(
                        "[red]Invalid indices format. Use comma-separated numbers (e.g., '0,1,2')[/red]"
                    )
                    raise typer.Exit(1) from None

            console.print(
                f"[bold]Importing {len(sources_to_import)} sources to notebook...[/bold]"
            )

            # Import the sources
            with console.status("[bold green]Importing sources..."):
                imported = await research.import_research_sources(
                    notebook_id=notebook_id,
                    task_id=result.task_id,
                    sources=sources_to_import,
                )

            # Handle deep research report
            report_imported = False
            if include_report and result.mode == "deep" and result.report:
                console.print(
                    "[dim]Deep research detected - importing AI report as text source...[/dim]"
                )
                source_manager = SourceManager(session)
                try:
                    report_title = f"Deep Research Report: {result.query[:50]}"
                    await source_manager.add_text(
                        notebook_id=notebook_id,
                        content=result.report,
                        title=report_title,
                    )
                    report_imported = True
                except Exception as e:
                    console.print(
                        f"[yellow]Warning: Could not import report as text source: {e}[/yellow]"
                    )

            # Display results
            console.print(
                f"[green]✓ Successfully imported {len(imported)} sources[/green]"
            )
            if report_imported:
                console.print(
                    "[green]✓ Imported deep research report as text source[/green]"
                )

            if imported:
                table = Table(
                    title="Imported Sources",
                    show_header=True,
                    header_style="bold green",
                )
                table.add_column("#", style="dim", justify="right")
                table.add_column("ID", style="cyan", max_width=20)
                table.add_column("Title", style="white", max_width=50)

                for i, src in enumerate(imported):
                    table.add_row(
                        str(i),
                        f"{src.id[:16]}..." if len(src.id) > 16 else src.id,
                        src.title[:50] if len(src.title) > 50 else src.title,
                    )

                console.print(table)

            console.print(
                f"\n[dim]View sources: https://notebooklm.google.com/notebook/{notebook_id}[/dim]"
            )

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

            try:
                with console.status(
                    f"[bold green]Generating mind map for notebook {notebook_id}..."
                ):
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
            with console.status(f"[bold green]Asking notebook {notebook_id}..."):
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
                console.print("  Check 'Studio' in NotebookLM to view progress.")
            else:
                console.print(
                    "[yellow]  Note: Could not retrieve Artifact ID, but request was sent.[/yellow]"
                )
                console.print(
                    "  Check your notebook in the browser to view the new briefing."
                )

    asyncio.run(_run())


# =============================================================================
# Studio Commands
# =============================================================================


studio_app = typer.Typer(
    help="Studio artifact management (Briefings, Audio, etc)", no_args_is_help=True
)
app.add_typer(studio_app, name="studio")


@studio_app.command("list")
def list_studio(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
) -> None:
    """List all studio artifacts and show their status."""

    async def _run() -> None:
        auth = AuthManager()
        if not auth.is_authenticated():
            console.print("[red]Not authenticated.[/red]")
            raise typer.Exit(1)

        async with BrowserSession(auth) as session:
            chat = ChatSession(session)
            with console.status(
                f"[bold green]Fetching studio artifacts for {notebook_id}..."
            ):
                artifacts = await chat.list_artifacts(notebook_id)

            if not artifacts:
                console.print("[yellow]No studio artifacts found.[/yellow]")
                return

            table = Table(title=f"Studio Artifacts in {notebook_id}")
            table.add_column("Type", style="cyan")
            table.add_column("ID", style="dim")
            table.add_column("Title", style="white")
            table.add_column("Status", style="green")

            for item in artifacts:
                # Map type code to name if possible
                type_name = str(item.get("type", "unknown"))
                if item.get("type") == 2:
                    type_name = "Report"
                elif item.get("type") == 1:
                    type_name = "Audio"
                elif item.get("type") == 3:
                    type_name = "Video"
                elif item.get("type") == 4:
                    type_name = "Flashcards"
                elif item.get("type") == 7:
                    type_name = "Infographic"
                elif item.get("type") == 8:
                    type_name = "Slide Deck"

                status_color = (
                    "green" if item.get("status") == "completed" else "yellow"
                )
                if item.get("status") == "failed":
                    status_color = "red"

                status_display = f"[{status_color}]{item.get('status')}[/]"

                table.add_row(
                    type_name,
                    item.get("id", "Unknown"),
                    item.get("title", "Untitled"),
                    status_display,
                )

            console.print(table)

    asyncio.run(_run())


@studio_app.command("status")
def studio_status(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
) -> None:
    """Show detailed status of all studio artifacts with download URLs."""

    async def _run() -> None:
        auth = AuthManager()
        if not auth.is_authenticated():
            console.print("[red]Not authenticated.[/red]")
            raise typer.Exit(1)

        async with BrowserSession(auth) as session:
            generator = ContentGenerator(session)
            with console.status(
                f"[bold green]Fetching studio status for {notebook_id}..."
            ):
                artifacts = await generator.poll_status(notebook_id)

            if not artifacts:
                console.print("[yellow]No studio artifacts found.[/yellow]")
                return

            table = Table(title=f"Studio Artifacts in {notebook_id}")
            table.add_column("Type", style="cyan")
            table.add_column("ID", style="dim", no_wrap=True)
            table.add_column("Title", style="white", max_width=30)
            table.add_column("Status", style="green")
            table.add_column("URL/Info", style="blue", max_width=40)

            for artifact in artifacts:
                status_color = (
                    "green" if artifact.status.value == "completed" else "yellow"
                )
                if artifact.status.value == "unknown":
                    status_color = "dim"

                status_display = f"[{status_color}]{artifact.status.value}[/]"

                # Determine URL or info to show
                url_info = ""
                if artifact.audio_url:
                    url_info = artifact.audio_url[:40] + "..."
                elif artifact.video_url:
                    url_info = artifact.video_url[:40] + "..."
                elif artifact.infographic_url:
                    url_info = artifact.infographic_url[:40] + "..."
                elif artifact.slide_deck_url:
                    url_info = artifact.slide_deck_url[:40] + "..."
                elif artifact.duration_seconds:
                    url_info = f"{artifact.duration_seconds//60}m {artifact.duration_seconds%60}s"

                table.add_row(
                    artifact.artifact_type.value,
                    artifact.artifact_id,
                    artifact.title[:30] if artifact.title else "—",
                    status_display,
                    url_info,
                )

            console.print(table)

    asyncio.run(_run())


@studio_app.command("delete")
def studio_delete(
    artifact_id: str = typer.Argument(..., help="Artifact ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete a studio artifact. WARNING: This is irreversible."""

    async def _run() -> None:
        auth = AuthManager()
        if not auth.is_authenticated():
            console.print("[red]Not authenticated.[/red]")
            raise typer.Exit(1)

        if not force:
            confirm = typer.confirm(
                f"Are you sure you want to delete artifact {artifact_id}? This cannot be undone."
            )
            if not confirm:
                console.print("Aborted.")
                return

        async with BrowserSession(auth) as session:
            generator = ContentGenerator(session)
            with console.status(f"[bold red]Deleting artifact {artifact_id}..."):
                success = await generator.delete(artifact_id)

            if success:
                console.print(f"[green]✓ Deleted artifact: {artifact_id}[/green]")
            else:
                console.print(f"[red]Failed to delete artifact: {artifact_id}[/red]")
                raise typer.Exit(1)

    asyncio.run(_run())


# =============================================================================
# Generate Commands
# =============================================================================


@generate_app.command("audio")
def generate_audio(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    format: str = typer.Option(
        "deep_dive",
        "--format",
        "-f",
        help="Audio format: deep_dive, brief, critique, debate",
    ),
    length: str = typer.Option(
        "default", "--length", "-l", help="Audio length: short, default, long"
    ),
    language: str = typer.Option(
        "en", "--language", help="Language code (e.g., en, es)"
    ),
    focus: str = typer.Option("", "--focus", help="Focus prompt for the AI"),
) -> None:
    """Generate an audio overview (podcast) from notebook sources."""

    async def _run() -> None:
        auth = AuthManager()
        if not auth.is_authenticated():
            console.print("[red]Not authenticated.[/red]")
            raise typer.Exit(1)

        # Map format string to enum
        format_map = {
            "deep_dive": AudioFormat.DEEP_DIVE,
            "brief": AudioFormat.BRIEF,
            "critique": AudioFormat.CRITIQUE,
            "debate": AudioFormat.DEBATE,
        }
        length_map = {
            "short": AudioLength.SHORT,
            "default": AudioLength.DEFAULT,
            "long": AudioLength.LONG,
        }

        if format not in format_map:
            console.print(
                f"[red]Invalid format: {format}. Use: deep_dive, brief, critique, debate[/red]"
            )
            raise typer.Exit(1)
        if length not in length_map:
            console.print(
                f"[red]Invalid length: {length}. Use: short, default, long[/red]"
            )
            raise typer.Exit(1)

        async with BrowserSession(auth) as session:
            # First get sources from the notebook
            source_manager = SourceManager(session)
            sources = await source_manager.list_sources(notebook_id)

            if not sources:
                console.print(
                    "[red]No sources found in notebook. Add sources first.[/red]"
                )
                raise typer.Exit(1)

            source_ids = [s.id for s in sources]
            generator = ContentGenerator(session)
            with console.status(
                f"[bold green]Generating audio overview for {notebook_id}..."
            ):
                result = await generator.create_audio(
                    notebook_id=notebook_id,
                    source_ids=source_ids,
                    format=format_map[format],
                    length=length_map[length],
                    language=language,
                    focus_prompt=focus,
                )

            console.print("[green]✓ Audio generation started![/green]")
            console.print(f"  Artifact ID: [cyan]{result.artifact_id}[/cyan]")
            console.print(f"  Format: {result.format}")
            console.print(f"  Length: {result.length}")
            console.print(f"  Status: {result.status}")
            console.print()
            console.print(
                "[dim]Use 'pynotebooklm studio status <notebook_id>' to check progress[/dim]"
            )

    asyncio.run(_run())


@generate_app.command("video")
def generate_video(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    format: str = typer.Option(
        "explainer", "--format", "-f", help="Video format: explainer, brief"
    ),
    style: str = typer.Option(
        "auto_select",
        "--style",
        "-s",
        help="Visual style: auto_select, classic, whiteboard, kawaii, anime, watercolor, retro_print, heritage, paper_craft",
    ),
    language: str = typer.Option(
        "en", "--language", help="Language code (e.g., en, es)"
    ),
    focus: str = typer.Option("", "--focus", help="Focus prompt for the AI"),
) -> None:
    """Generate a video overview from notebook sources."""

    async def _run() -> None:
        auth = AuthManager()
        if not auth.is_authenticated():
            console.print("[red]Not authenticated.[/red]")
            raise typer.Exit(1)

        format_map = {
            "explainer": VideoFormat.EXPLAINER,
            "brief": VideoFormat.BRIEF,
        }
        style_map = {
            "auto_select": VideoStyle.AUTO_SELECT,
            "classic": VideoStyle.CLASSIC,
            "whiteboard": VideoStyle.WHITEBOARD,
            "kawaii": VideoStyle.KAWAII,
            "anime": VideoStyle.ANIME,
            "watercolor": VideoStyle.WATERCOLOR,
            "retro_print": VideoStyle.RETRO_PRINT,
            "heritage": VideoStyle.HERITAGE,
            "paper_craft": VideoStyle.PAPER_CRAFT,
        }

        if format not in format_map:
            console.print(f"[red]Invalid format: {format}. Use: explainer, brief[/red]")
            raise typer.Exit(1)
        if style not in style_map:
            console.print(
                f"[red]Invalid style: {style}. Use: auto_select, classic, whiteboard, etc.[/red]"
            )
            raise typer.Exit(1)

        async with BrowserSession(auth) as session:
            source_manager = SourceManager(session)
            sources = await source_manager.list_sources(notebook_id)

            if not sources:
                console.print(
                    "[red]No sources found in notebook. Add sources first.[/red]"
                )
                raise typer.Exit(1)

            source_ids = [s.id for s in sources]
            generator = ContentGenerator(session)
            with console.status(
                f"[bold green]Generating video overview for {notebook_id}..."
            ):
                result = await generator.create_video(
                    notebook_id=notebook_id,
                    source_ids=source_ids,
                    format=format_map[format],
                    style=style_map[style],
                    language=language,
                    focus_prompt=focus,
                )

            console.print("[green]✓ Video generation started![/green]")
            console.print(f"  Artifact ID: [cyan]{result.artifact_id}[/cyan]")
            console.print(f"  Format: {result.format}")
            console.print(f"  Style: {result.style}")
            console.print(f"  Status: {result.status}")
            console.print()
            console.print(
                "[dim]Use 'pynotebooklm studio status <notebook_id>' to check progress[/dim]"
            )

    asyncio.run(_run())


@generate_app.command("infographic")
def generate_infographic(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    orientation: str = typer.Option(
        "landscape",
        "--orientation",
        "-o",
        help="Orientation: landscape, portrait, square",
    ),
    detail: str = typer.Option(
        "standard", "--detail", "-d", help="Detail level: concise, standard, detailed"
    ),
    language: str = typer.Option(
        "en", "--language", help="Language code (e.g., en, es)"
    ),
    focus: str = typer.Option("", "--focus", help="Focus prompt for the AI"),
) -> None:
    """Generate an infographic from notebook sources."""

    async def _run() -> None:
        auth = AuthManager()
        if not auth.is_authenticated():
            console.print("[red]Not authenticated.[/red]")
            raise typer.Exit(1)

        orientation_map = {
            "landscape": InfographicOrientation.LANDSCAPE,
            "portrait": InfographicOrientation.PORTRAIT,
            "square": InfographicOrientation.SQUARE,
        }
        detail_map = {
            "concise": InfographicDetailLevel.CONCISE,
            "standard": InfographicDetailLevel.STANDARD,
            "detailed": InfographicDetailLevel.DETAILED,
        }

        if orientation not in orientation_map:
            console.print(
                f"[red]Invalid orientation: {orientation}. Use: landscape, portrait, square[/red]"
            )
            raise typer.Exit(1)
        if detail not in detail_map:
            console.print(
                f"[red]Invalid detail: {detail}. Use: concise, standard, detailed[/red]"
            )
            raise typer.Exit(1)

        async with BrowserSession(auth) as session:
            source_manager = SourceManager(session)
            sources = await source_manager.list_sources(notebook_id)

            if not sources:
                console.print(
                    "[red]No sources found in notebook. Add sources first.[/red]"
                )
                raise typer.Exit(1)

            source_ids = [s.id for s in sources]
            generator = ContentGenerator(session)
            with console.status(
                f"[bold green]Generating infographic for {notebook_id}..."
            ):
                result = await generator.create_infographic(
                    notebook_id=notebook_id,
                    source_ids=source_ids,
                    orientation=orientation_map[orientation],
                    detail_level=detail_map[detail],
                    language=language,
                    focus_prompt=focus,
                )

            console.print("[green]✓ Infographic generation started![/green]")
            console.print(f"  Artifact ID: [cyan]{result.artifact_id}[/cyan]")
            console.print(f"  Orientation: {result.orientation}")
            console.print(f"  Detail Level: {result.detail_level}")
            console.print(f"  Status: {result.status}")
            console.print()
            console.print(
                "[dim]Use 'pynotebooklm studio status <notebook_id>' to check progress[/dim]"
            )

    asyncio.run(_run())


@generate_app.command("slides")
def generate_slides(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    format: str = typer.Option(
        "detailed_deck",
        "--format",
        "-f",
        help="Slide format: detailed_deck, presenter_slides",
    ),
    length: str = typer.Option(
        "default", "--length", "-l", help="Slide deck length: short, default"
    ),
    language: str = typer.Option(
        "en", "--language", help="Language code (e.g., en, es)"
    ),
    focus: str = typer.Option("", "--focus", help="Focus prompt for the AI"),
) -> None:
    """Generate a slide deck from notebook sources."""

    async def _run() -> None:
        auth = AuthManager()
        if not auth.is_authenticated():
            console.print("[red]Not authenticated.[/red]")
            raise typer.Exit(1)

        format_map = {
            "detailed_deck": SlideDeckFormat.DETAILED_DECK,
            "presenter_slides": SlideDeckFormat.PRESENTER_SLIDES,
        }
        length_map = {
            "short": SlideDeckLength.SHORT,
            "default": SlideDeckLength.DEFAULT,
        }

        if format not in format_map:
            console.print(
                f"[red]Invalid format: {format}. Use: detailed_deck, presenter_slides[/red]"
            )
            raise typer.Exit(1)
        if length not in length_map:
            console.print(f"[red]Invalid length: {length}. Use: short, default[/red]")
            raise typer.Exit(1)

        async with BrowserSession(auth) as session:
            source_manager = SourceManager(session)
            sources = await source_manager.list_sources(notebook_id)

            if not sources:
                console.print(
                    "[red]No sources found in notebook. Add sources first.[/red]"
                )
                raise typer.Exit(1)

            source_ids = [s.id for s in sources]
            generator = ContentGenerator(session)
            with console.status(
                f"[bold green]Generating slide deck for {notebook_id}..."
            ):
                result = await generator.create_slides(
                    notebook_id=notebook_id,
                    source_ids=source_ids,
                    format=format_map[format],
                    length=length_map[length],
                    language=language,
                    focus_prompt=focus,
                )

            console.print("[green]✓ Slide deck generation started![/green]")
            console.print(f"  Artifact ID: [cyan]{result.artifact_id}[/cyan]")
            console.print(f"  Format: {result.format}")
            console.print(f"  Length: {result.length}")
            console.print(f"  Status: {result.status}")
            console.print()
            console.print(
                "[dim]Use 'pynotebooklm studio status <notebook_id>' to check progress[/dim]"
            )

    asyncio.run(_run())


# =============================================================================
# Study Commands
# =============================================================================


@study_app.command("flashcards")
def create_flashcards(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    difficulty: str = typer.Option(
        "medium", "--difficulty", "-d", help="Difficulty: easy, medium, hard"
    ),
) -> None:
    """Create flashcards from notebook sources.

    Generates study flashcards from all sources in the notebook.
    Results can be viewed with 'studio status'.
    """

    async def _run() -> None:
        auth = AuthManager()
        if not auth.is_authenticated():
            console.print("[red]Not authenticated. Run 'pynotebooklm auth login'[/red]")
            raise typer.Exit(1)

        # Validate difficulty
        difficulty_map = {
            "easy": FlashcardDifficulty.EASY,
            "medium": FlashcardDifficulty.MEDIUM,
            "hard": FlashcardDifficulty.HARD,
        }
        if difficulty.lower() not in difficulty_map:
            console.print(
                f"[red]Invalid difficulty: {difficulty}. Use easy, medium, or hard.[/red]"
            )
            raise typer.Exit(1)

        async with BrowserSession(auth) as session:
            # Get all source IDs from the notebook
            manager = NotebookManager(session)
            nb = await manager.get(notebook_id)
            if not nb:
                console.print(f"[red]Notebook not found: {notebook_id}[/red]")
                raise typer.Exit(1)

            source_ids = [src.id for src in nb.sources]
            if not source_ids:
                console.print("[red]No sources found in notebook[/red]")
                raise typer.Exit(1)

            study = StudyManager(session)
            with console.status(
                f"[bold green]Generating flashcards for {notebook_id}..."
            ):
                result = await study.create_flashcards(
                    notebook_id=notebook_id,
                    source_ids=source_ids,
                    difficulty=difficulty_map[difficulty.lower()],
                )

            console.print("[green]✓ Flashcard generation started![/green]")
            console.print(f"  Artifact ID: [cyan]{result.artifact_id}[/cyan]")
            console.print(f"  Difficulty: {result.difficulty}")
            console.print(f"  Status: {result.status}")
            console.print()
            console.print(
                "[dim]Use 'pynotebooklm studio status <notebook_id>' to check progress[/dim]"
            )

    asyncio.run(_run())


@study_app.command("quiz")
def create_quiz(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    questions: int = typer.Option(
        2, "--questions", "-q", help="Number of quiz questions"
    ),
    difficulty: int = typer.Option(
        2, "--difficulty", "-d", help="Difficulty level (1-3)"
    ),
) -> None:
    """Create a quiz from notebook sources.

    Generates a quiz with multiple-choice questions from all sources.
    Results can be viewed with 'studio status'.
    """

    async def _run() -> None:
        auth = AuthManager()
        if not auth.is_authenticated():
            console.print("[red]Not authenticated. Run 'pynotebooklm auth login'[/red]")
            raise typer.Exit(1)

        async with BrowserSession(auth) as session:
            # Get all source IDs from the notebook
            manager = NotebookManager(session)
            nb = await manager.get(notebook_id)
            if not nb:
                console.print(f"[red]Notebook not found: {notebook_id}[/red]")
                raise typer.Exit(1)

            source_ids = [src.id for src in nb.sources]
            if not source_ids:
                console.print("[red]No sources found in notebook[/red]")
                raise typer.Exit(1)

            study = StudyManager(session)
            with console.status(f"[bold green]Generating quiz for {notebook_id}..."):
                result = await study.create_quiz(
                    notebook_id=notebook_id,
                    source_ids=source_ids,
                    question_count=questions,
                    difficulty=difficulty,
                )

            console.print("[green]✓ Quiz generation started![/green]")
            console.print(f"  Artifact ID: [cyan]{result.artifact_id}[/cyan]")
            console.print(f"  Questions: {result.question_count}")
            console.print(f"  Difficulty: {result.difficulty}")
            console.print(f"  Status: {result.status}")
            console.print()
            console.print(
                "[dim]Use 'pynotebooklm studio status <notebook_id>' to check progress[/dim]"
            )

    asyncio.run(_run())


@study_app.command("table")
def create_data_table(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    description: str = typer.Option(
        ..., "--description", "-d", help="Description of data to extract"
    ),
    language: str = typer.Option(
        "en", "--language", "-l", help="Language code (e.g., en, es)"
    ),
) -> None:
    """Create a data table from notebook sources.

    Extracts structured data based on the provided description.
    For example: 'Extract key dates and events' or 'List all company names and revenues'.
    Results can be viewed with 'studio status'.
    """

    async def _run() -> None:
        auth = AuthManager()
        if not auth.is_authenticated():
            console.print("[red]Not authenticated. Run 'pynotebooklm auth login'[/red]")
            raise typer.Exit(1)

        async with BrowserSession(auth) as session:
            # Get all source IDs from the notebook
            manager = NotebookManager(session)
            nb = await manager.get(notebook_id)
            if not nb:
                console.print(f"[red]Notebook not found: {notebook_id}[/red]")
                raise typer.Exit(1)

            source_ids = [src.id for src in nb.sources]
            if not source_ids:
                console.print("[red]No sources found in notebook[/red]")
                raise typer.Exit(1)

            study = StudyManager(session)
            with console.status(
                f"[bold green]Generating data table for {notebook_id}..."
            ):
                result = await study.create_data_table(
                    notebook_id=notebook_id,
                    source_ids=source_ids,
                    description=description,
                    language=language,
                )

            console.print("[green]✓ Data table generation started![/green]")
            console.print(f"  Artifact ID: [cyan]{result.artifact_id}[/cyan]")
            console.print(f"  Description: {result.description}")
            console.print(f"  Language: {result.language}")
            console.print(f"  Status: {result.status}")
            console.print()
            console.print(
                "[dim]Use 'pynotebooklm studio status <notebook_id>' to check progress[/dim]"
            )

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
