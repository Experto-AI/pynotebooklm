#!/usr/bin/env python3
"""
Research Workflow Example - PyNotebookLM

This example demonstrates the research discovery workflow:
- Starting web/deep research
- Polling for results
- Importing discovered sources
- Viewing research findings

Author: PyNotebookLM Team
"""

import asyncio
import sys
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from pynotebooklm import NotebookLMClient
from pynotebooklm.exceptions import PyNotebookLMError
from pynotebooklm.models import ResearchStatus

console = Console()


async def demonstrate_web_research(client: NotebookLMClient, notebook_id: str) -> None:
    """Demonstrate standard web research."""
    console.print("\n[bold blue]🔍 Standard Web Research[/bold blue]")

    # Start research
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Starting research...", total=None)

        result = await client.research.start_research(
            notebook_id=notebook_id,
            query="latest developments in artificial intelligence 2024",
            source="web",
            mode="standard",
        )

        progress.update(task, description=f"Research started (Task ID: {result.task_id})")

    console.print(f"✅ Research task created: {result.task_id}\n")

    # Poll for results
    console.print("⏳ Polling for results...")

    max_attempts = 30
    for attempt in range(max_attempts):
        status = await client.research.poll_research(notebook_id=notebook_id)

        if status.status == ResearchStatus.COMPLETED:
            console.print(f"✅ Research completed! Found {len(status.sources)} sources\n")
            break

        elif status.status == ResearchStatus.IN_PROGRESS:
            console.print(f"  Attempt {attempt + 1}/{max_attempts}: Still in progress...")
            await asyncio.sleep(5)

        else:
            console.print(f"⚠️  Status: {status.status}")
            break
    else:
        console.print("[yellow]⏱️  Research still in progress after max attempts[/yellow]")
        return

    # Display discovered sources
    if status.sources:
        table = Table(title="Discovered Sources")
        table.add_column("№", justify="right", style="cyan", no_wrap=True)
        table.add_column("Title", style="white")
        table.add_column("URL", style="blue")

        for i, source in enumerate(status.sources[:10], 1):  # Show first 10
            table.add_row(
                str(i),
                source.get("title", "Untitled")[:50] + "..." if len(source.get("title", "")) > 50 else source.get("title", "Untitled"),
                source.get("url", "N/A")[:60] + "..." if len(source.get("url", "")) > 60 else source.get("url", "N/A"),
            )

        console.print(table)

        # Import sources
        console.print("\n📥 Importing discovered sources...")
        imported = await client.research.import_research_sources(
            notebook_id=notebook_id,
            sources=status.sources[:5],  # Import first 5
        )
        console.print(f"✅ Imported {len(imported)} sources to notebook\n")


async def demonstrate_deep_research(client: NotebookLMClient, notebook_id: str) -> None:
    """Demonstrate deep research with report generation."""
    console.print("\n[bold blue]🔬 Deep Research (Comprehensive)[/bold blue]")

    # Start deep research
    result = await client.research.start_research(
        notebook_id=notebook_id,
        query="quantum computing applications",
        source="web",
        mode="deep",
    )

    console.print(f"✅ Deep research started: {result.task_id}\n")
    console.print("[yellow]⏳ Deep research takes longer (~60-120 seconds)[/yellow]")
    console.print("   This example will poll a few times then exit.\n")

    # Poll a few times to show progress
    for _ in range(3):
        status = await client.research.poll_research(notebook_id=notebook_id)
        console.print(f"  Status: {status.status}")

        if status.status == ResearchStatus.COMPLETED:
            console.print(
                f"\n✅ Deep research completed! Found {len(status.sources)} sources"
            )
            if status.report:
                console.print("\n[bold]📄 Research Report:[/bold]")
                console.print(Panel(status.report[:500] + "...", border_style="green"))
            break

        await asyncio.sleep(10)


async def main() -> None:
    """Demonstrate research workflow."""
    console.print(
        Panel.fit("🔍 PyNotebookLM - Research Workflow Example", style="bold blue")
    )

    try:
        async with NotebookLMClient() as client:
            # Create a research notebook
            console.print("\n📓 Creating research notebook...")
            notebook = await client.notebooks.create(name="Research Demo")
            console.print(f"✅ Created: {notebook.name} (ID: {notebook.id})\n")

            # Add initial source for context
            console.print("📄 Adding initial source...")
            await client.sources.add_text(
                notebook_id=notebook.id,
                title="Research Topic",
                content="We are researching recent developments in AI and quantum computing.",
            )

            # Demonstrate standard web research
            await demonstrate_web_research(client, notebook.id)

            # Demonstrate deep research
            await demonstrate_deep_research(client, notebook.id)

            # Cleanup
            console.print("\n🧹 Cleaning up...")
            await client.notebooks.delete(notebook_id=notebook.id, confirm=True)
            console.print("✅ Deleted notebook\n")

            console.print(
                Panel.fit("✨ Example completed successfully!", style="bold green")
            )

    except PyNotebookLMError as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
