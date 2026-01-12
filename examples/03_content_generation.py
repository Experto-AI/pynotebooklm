#!/usr/bin/env python3
"""
Content Generation Example - PyNotebookLM

This example demonstrates multi-modal content generation:
- Audio overviews (podcasts)
- Video overviews
- Infographics
- Slide decks
- Polling artifact status

Author: PyNotebookLM Team
"""

import asyncio
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from pynotebooklm import NotebookLMClient
from pynotebooklm.exceptions import PyNotebookLMError

console = Console()


async def create_sample_notebook(client: NotebookLMClient) -> str:
    """Create a notebook with sample sources for content generation."""
    console.print("📓 Creating sample notebook...")
    notebook = await client.notebooks.create(name="Content Generation Demo")

    # Add sources about climate change
    await client.sources.add_url(
        notebook_id=notebook.id,
        url="https://en.wikipedia.org/wiki/Climate_change",
    )

    await client.sources.add_text(
        notebook_id=notebook.id,
        title="Climate Facts",
        content="""
        Key Facts About Climate Change:
        - Global temperatures have risen approximately 1.1°C since pre-industrial times
        - Arctic sea ice is declining at a rate of 13% per decade
        - Sea levels are rising at an accelerating rate
        - Renewable energy adoption is growing rapidly
        - Carbon capture technology is advancing
        """,
    )

    console.print(f"✅ Created notebook: {notebook.name}\n")
    return notebook.id


async def demonstrate_audio_generation(
    client: NotebookLMClient, notebook_id: str
) -> None:
    """Demonstrate audio overview generation."""
    console.print("\n[bold blue]🎙️  Audio Overview (Podcast)[/bold blue]")

    # Generate audio with different formats
    console.print("Generating deep dive audio overview...")
    audio = await client.content.create_audio(
        notebook_id=notebook_id,
        format="deep_dive",
        length="default",
        language="en",
        focus="Focus on solutions and positive developments",
    )

    console.print(f"✅ Audio generation started!")
    console.print(f"   Format: Deep Dive")
    console.print(f"   Artifact ID: {audio.artifact_id}\n")


async def demonstrate_video_generation(
    client: NotebookLMClient, notebook_id: str
) -> None:
    """Demonstrate video overview generation."""
    console.print("\n[bold blue]🎬 Video Overview[/bold blue]")

    # Generate video with anime style
    console.print("Generating animated video overview...")
    video = await client.content.create_video(
        notebook_id=notebook_id,
        format="explainer",
        style="anime",
        language="en",
        focus="Create an engaging explanation of climate solutions",
    )

    console.print(f"✅ Video generation started!")
    console.print(f"   Style: Anime")
    console.print(f"   Artifact ID: {video.artifact_id}\n")


async def demonstrate_infographic_generation(
    client: NotebookLMClient, notebook_id: str
) -> None:
    """Demonstrate infographic generation."""
    console.print("\n[bold blue]📊 Infographic[/bold blue]")

    # Generate portrait infographic
    console.print("Generating infographic...")
    infographic = await client.content.create_infographic(
        notebook_id=notebook_id,
        orientation="portrait",
        detail="detailed",
        language="en",
        focus="Visualize climate change statistics and solutions",
    )

    console.print(f"✅ Infographic generation started!")
    console.print(f"   Orientation: Portrait (9:16)")
    console.print(f"   Detail: Detailed")
    console.print(f"   Artifact ID: {infographic.artifact_id}\n")


async def demonstrate_slides_generation(
    client: NotebookLMClient, notebook_id: str
) -> None:
    """Demonstrate slide deck generation."""
    console.print("\n[bold blue]📽️  Slide Deck[/bold blue]")

    # Generate presenter slides
    console.print("Generating slide deck...")
    slides = await client.content.create_slides(
        notebook_id=notebook_id,
        format="presenter_slides",
        length="default",
        language="en",
        focus="Create a presentation on climate action",
    )

    console.print(f"✅ Slide deck generation started!")
    console.print(f"   Format: Presenter Slides")
    console.print(f"   Artifact ID: {slides.artifact_id}\n")


async def poll_artifact_status(client: NotebookLMClient, notebook_id: str) -> None:
    """Poll and display artifact generation status."""
    console.print("\n[bold blue]⏳ Polling Artifact Status[/bold blue]")
    console.print("Note: Studio artifacts typically take 60-300 seconds to generate.\n")

    # Poll status
    console.print("Checking current status...")
    artifacts = await client.content.poll_status(notebook_id=notebook_id)

    if not artifacts:
        console.print("[yellow]No artifacts found yet.[/yellow]\n")
        return

    # Display status table
    table = Table(title="Studio Artifacts")
    table.add_column("Type", style="cyan")
    table.add_column("Status", style="yellow")
    table.add_column("ID", style="blue", no_wrap=True)

    for artifact in artifacts:
        status_emoji = {
            "in_progress": "⏳",
            "completed": "✅",
            "failed": "❌",
        }.get(artifact.status, "❓")

        table.add_row(
            artifact.artifact_type or "Unknown",
            f"{status_emoji} {artifact.status}",
            artifact.artifact_id[:20] + "...",
        )

    console.print(table)
    console.print()

    # Show download URLs for completed artifacts
    completed = [a for a in artifacts if a.status == "completed"]
    if completed:
        console.print("\n[bold green]✅ Completed Artifacts:[/bold green]")
        for artifact in completed[:3]:  # Show first 3
            console.print(f"\n{artifact.artifact_type}:")
            if artifact.audio_url:
                console.print(f"  🎙️  Audio: {artifact.audio_url[:80]}...")
            if artifact.video_url:
                console.print(f"  🎬 Video: {artifact.video_url[:80]}...")
            if artifact.pdf_url:
                console.print(f"  📄 PDF: {artifact.pdf_url[:80]}...")


async def main() -> None:
    """Demonstrate content generation features."""
    console.print(
        Panel.fit("🎨 PyNotebookLM - Content Generation Example", style="bold blue")
    )

    try:
        async with NotebookLMClient() as client:
            # Create sample notebook
            notebook_id = await create_sample_notebook(client)

            # Demonstrate different content types
            await demonstrate_audio_generation(client, notebook_id)
            await demonstrate_video_generation(client, notebook_id)
            await demonstrate_infographic_generation(client, notebook_id)
            await demonstrate_slides_generation(client, notebook_id)

            # Wait a bit then check status
            console.print("\n⏳ Waiting 10 seconds before checking status...")
            await asyncio.sleep(10)

            await poll_artifact_status(client, notebook_id)

            console.print(
                "\n[yellow]💡 Tip: Use 'pynotebooklm studio status <notebook_id>' "
                "to check artifact status later[/yellow]\n"
            )

            # Cleanup
            console.print("🧹 Cleaning up...")
            await client.notebooks.delete(notebook_id=notebook_id, confirm=True)
            console.print("✅ Deleted notebook\n")

            console.print(
                Panel.fit("✨ Example completed successfully!", style="bold green")
            )

    except PyNotebookLMError as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
