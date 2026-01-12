#!/usr/bin/env python3
"""
End-to-End Research Automation Pipeline.

This script automates the complete research workflow:
1. Create a notebook for a specific topic
2. Start deep research on the topic
3. Poll until research is complete
4. Automatically import discovered sources
5. Generate a briefing document
6. Optionally create study materials (flashcards, quiz)

Usage:
    python scripts/automation/research_pipeline.py "AI Ethics" --study
    python scripts/automation/research_pipeline.py "Climate Change" --audio --video
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from pynotebooklm import NotebookLMClient
from pynotebooklm.exceptions import PyNotebookLMError
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table

console = Console()


async def run_research_pipeline(
    topic: str,
    deep: bool = True,
    generate_audio: bool = False,
    generate_video: bool = False,
    generate_study: bool = False,
    max_poll_attempts: int = 24,
) -> None:
    """
    Run the complete research automation pipeline.

    Args:
        topic: Research topic to investigate
        deep: Use deep research mode (more comprehensive)
        generate_audio: Generate an audio overview after research
        generate_video: Generate a video overview after research
        generate_study: Generate study materials (flashcards, quiz)
        max_poll_attempts: Maximum number of polling attempts (5s intervals)
    """
    console.print(
        Panel.fit(
            f"[bold cyan]Research Pipeline: {topic}[/bold cyan]",
            subtitle="Automated workflow",
        )
    )

    try:
        async with NotebookLMClient() as client:
            # Step 1: Create notebook
            console.print("\n[bold yellow]Step 1:[/bold yellow] Creating notebook...")
            notebook = await client.notebooks.create(f"Research: {topic}")
            console.print(f"✅ Created notebook: [green]{notebook.name}[/green] ({notebook.id})")

            # Step 2: Start research
            mode_str = "deep" if deep else "standard"
            console.print(f"\n[bold yellow]Step 2:[/bold yellow] Starting {mode_str} research...")
            session = await client.research.start_research(
                notebook_id=notebook.id,
                query=topic,
                mode="deep" if deep else "fast",
                source_type="web",
            )
            console.print(f"✅ Research session started: {session.task_id}")

            # Step 3: Poll for completion
            console.print(f"\n[bold yellow]Step 3:[/bold yellow] Waiting for research to complete...")
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Polling for results...", total=None)
                
                for attempt in range(max_poll_attempts):
                    await asyncio.sleep(5)
                    result = await client.research.poll_research(notebook.id)
                    
                    if result.status == "completed":
                        progress.update(task, description="✅ Research completed!")
                        break
                    
                    progress.update(
                        task,
                        description=f"Polling... ({result.status}) - Attempt {attempt + 1}/{max_poll_attempts}",
                    )
                else:
                    console.print("[red]⚠️  Research timed out. Continuing anyway...[/red]")
                    result = await client.research.poll_research(notebook.id)

            # Display discovered sources
            if result.sources:
                table = Table(title="Discovered Sources")
                table.add_column("#", style="cyan", width=4)
                table.add_column("Title", style="green")
                table.add_column("Type", style="yellow", width=10)
                
                for idx, source in enumerate(result.sources):
                    table.add_row(
                        str(idx),
                        source.title[:60] + "..." if len(source.title) > 60 else source.title,
                        "URL" if source.url else "Drive",
                    )
                
                console.print(table)

            # Step 4: Import sources
            if result.sources:
                console.print(f"\n[bold yellow]Step 4:[/bold yellow] Importing {len(result.sources)} sources...")
                imported = await client.research.import_research_sources(
                    notebook_id=notebook.id,
                    task_id=result.task_id,
                    source_indices=None,  # Import all
                )
                console.print(f"✅ Imported {len(imported)} sources successfully")
            else:
                console.print("[yellow]⚠️  No sources to import[/yellow]")

            # Step 5: Generate briefing
            console.print(f"\n[bold yellow]Step 5:[/bold yellow] Creating briefing document...")
            briefing = await client.chat.create_briefing(notebook.id)
            console.print(f"✅ Briefing created: {briefing.artifact_id}")
            if briefing.title:
                console.print(f"   Title: [cyan]{briefing.title}[/cyan]")

            # Optional: Generate audio overview
            if generate_audio and result.sources:
                console.print(f"\n[bold yellow]Step 6a:[/bold yellow] Generating audio overview...")
                # Get all source IDs
                notebook_data = await client.notebooks.get(notebook.id)
                source_ids = [s.id for s in notebook_data.sources]
                
                audio = await client.content.create_audio(
                    notebook_id=notebook.id,
                    source_ids=source_ids,
                    format="deep_dive",
                    length="default",
                )
                console.print(f"✅ Audio generation started: {audio.artifact_id}")

            # Optional: Generate video overview
            if generate_video and result.sources:
                console.print(f"\n[bold yellow]Step 6b:[/bold yellow] Generating video overview...")
                notebook_data = await client.notebooks.get(notebook.id)
                source_ids = [s.id for s in notebook_data.sources]
                
                video = await client.content.create_video(
                    notebook_id=notebook.id,
                    source_ids=source_ids,
                    format="explainer",
                    style="auto_select",
                )
                console.print(f"✅ Video generation started: {video.artifact_id}")

            # Optional: Generate study materials
            if generate_study and result.sources:
                console.print(f"\n[bold yellow]Step 6c:[/bold yellow] Generating study materials...")
                notebook_data = await client.notebooks.get(notebook.id)
                source_ids = [s.id for s in notebook_data.sources]
                
                # Flashcards
                flashcards = await client.study.create_flashcards(
                    notebook_id=notebook.id,
                    source_ids=source_ids,
                    difficulty="medium",
                )
                console.print(f"✅ Flashcards started: {flashcards.artifact_id}")
                
                # Quiz
                quiz = await client.study.create_quiz(
                    notebook_id=notebook.id,
                    source_ids=source_ids,
                    question_count=5,
                    difficulty=2,
                )
                console.print(f"✅ Quiz started: {quiz.artifact_id}")

            # Final summary
            console.print("\n" + "=" * 60)
            console.print(Panel.fit(
                f"[bold green]✅ Pipeline Complete![/bold green]\n\n"
                f"Notebook ID: [cyan]{notebook.id}[/cyan]\n"
                f"View in NotebookLM: https://notebooklm.google.com",
                title="Success",
            ))

    except PyNotebookLMError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        sys.exit(1)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Automate end-to-end research workflow in NotebookLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic research pipeline
  python research_pipeline.py "Machine Learning"

  # Deep research with audio
  python research_pipeline.py "Quantum Computing" --deep --audio

  # Full pipeline with all content types
  python research_pipeline.py "Renewable Energy" --audio --video --study
        """,
    )
    
    parser.add_argument("topic", help="Research topic to investigate")
    parser.add_argument(
        "--deep",
        action="store_true",
        help="Use deep research mode (more comprehensive)",
    )
    parser.add_argument(
        "--audio",
        action="store_true",
        help="Generate audio overview after research",
    )
    parser.add_argument(
        "--video",
        action="store_true",
        help="Generate video overview after research",
    )
    parser.add_argument(
        "--study",
        action="store_true",
        help="Generate study materials (flashcards, quiz)",
    )
    parser.add_argument(
        "--max-polls",
        type=int,
        default=24,
        help="Maximum polling attempts (default: 24 = 2 minutes)",
    )
    
    args = parser.parse_args()
    
    asyncio.run(
        run_research_pipeline(
            topic=args.topic,
            deep=args.deep,
            generate_audio=args.audio,
            generate_video=args.video,
            generate_study=args.study,
            max_poll_attempts=args.max_polls,
        )
    )


if __name__ == "__main__":
    main()
