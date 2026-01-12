#!/usr/bin/env python3
"""
Basic Usage Example - PyNotebookLM

This example demonstrates the fundamental operations:
- Authenticating with NotebookLM
- Creating a notebook
- Adding various types of sources
- Querying the notebook

Author: PyNotebookLM Team
"""

import asyncio
import sys

from rich.console import Console
from rich.panel import Panel

from pynotebooklm import NotebookLMClient
from pynotebooklm.exceptions import (
    AuthenticationError,
    NotebookNotFoundError,
    PyNotebookLMError,
)

console = Console()


async def main() -> None:
    """Demonstrate basic PyNotebookLM usage."""
    console.print(Panel.fit("📚 PyNotebookLM - Basic Usage Example", style="bold blue"))

    try:
        # Initialize client with async context manager
        async with NotebookLMClient() as client:
            console.print("\n✅ [green]Authenticated successfully![/green]\n")

            # Create a new notebook
            console.print("📓 Creating notebook...")
            notebook = await client.notebooks.create(name="Demo Notebook")
            console.print(
                f"✅ Created notebook: [bold]{notebook.name}[/bold] (ID: {notebook.id})\n"
            )

            # Add URL source
            console.print("🌐 Adding URL source...")
            url_source = await client.sources.add_url(
                notebook_id=notebook.id,
                url="https://en.wikipedia.org/wiki/Python_(programming_language)",
            )
            console.print(
                f"✅ Added URL source: [bold]{url_source.title}[/bold]\n"
            )

            # Add YouTube source
            console.print("🎥 Adding YouTube source...")
            yt_source = await client.sources.add_url(
                notebook_id=notebook.id,
                url="https://www.youtube.com/watch?v=x7X9w_GIm1s",  # Python tutorial
            )
            console.print(
                f"✅ Added YouTube source: [bold]{yt_source.title}[/bold]\n"
            )

            # Add text source
            console.print("📝 Adding text source...")
            text_source = await client.sources.add_text(
                notebook_id=notebook.id,
                title="Quick Notes",
                content="""
                Python is a high-level programming language known for:
                - Simple, readable syntax
                - Extensive standard library
                - Dynamic typing
                - Cross-platform compatibility
                """,
            )
            console.print(
                f"✅ Added text source: [bold]{text_source.title}[/bold]\n"
            )

            # List all sources
            console.print("📋 Listing all sources...")
            sources = await client.sources.list(notebook_id=notebook.id)
            console.print(f"✅ Found {len(sources)} sources in notebook:\n")
            for i, source in enumerate(sources, 1):
                console.print(f"  {i}. {source.title}")

            # Query the notebook
            console.print("\n💬 Querying notebook...")
            response = await client.chat.query(
                notebook_id=notebook.id,
                question="What is Python and what are its key features?",
            )
            console.print("\n[bold cyan]AI Response:[/bold cyan]")
            console.print(Panel(response.text, border_style="cyan"))

            # Get notebook summary
            console.print("\n📊 Getting notebook summary...")
            summary = await client.chat.get_notebook_summary(notebook_id=notebook.id)
            console.print("\n[bold magenta]Notebook Summary:[/bold magenta]")
            console.print(Panel(summary, border_style="magenta"))

            # Cleanup (optional)
            console.print("\n🧹 Cleaning up...")
            await client.notebooks.delete(notebook_id=notebook.id, confirm=True)
            console.print("✅ Deleted notebook\n")

            console.print(
                Panel.fit("✨ Example completed successfully!", style="bold green")
            )

    except AuthenticationError as e:
        console.print(f"[red]❌ Authentication failed: {e}[/red]")
        console.print(
            "\n[yellow]💡 Tip: Run 'pynotebooklm auth login' to authenticate[/yellow]"
        )
        sys.exit(1)

    except NotebookNotFoundError as e:
        console.print(f"[red]❌ Notebook not found: {e}[/red]")
        sys.exit(1)

    except PyNotebookLMError as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
