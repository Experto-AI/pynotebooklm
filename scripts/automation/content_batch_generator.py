#!/usr/bin/env python3
"""
Batch Content Generator for Multiple Notebooks.

This script generates content (audio, video, infographics, slides) for multiple
notebooks concurrently, with progress tracking and error handling.

Usage:
    python scripts/automation/content_batch_generator.py --type audio --notebooks nb1,nb2,nb3
    python scripts/automation/content_batch_generator.py --type all --file notebooks.txt
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from pynotebooklm import NotebookLMClient
from pynotebooklm.exceptions import PyNotebookLMError
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)
from rich.table import Table
from rich.panel import Panel

console = Console()


async def generate_content_for_notebook(
    client: NotebookLMClient,
    notebook_id: str,
    content_types: List[str],
) -> dict:
    """
    Generate requested content types for a single notebook.

    Args:
        client: NotebookLM client instance
        notebook_id: Target notebook ID
        content_types: List of content types to generate (audio, video, infographic, slides)

    Returns:
        Dictionary with results for each content type
    """
    results = {}
    
    try:
        # Get notebook and sources
        notebook = await client.notebooks.get(notebook_id)
        source_ids = [s.id for s in notebook.sources]
        
        if not source_ids:
            return {"error": "No sources in notebook"}
        
        # Generate audio
        if "audio" in content_types:
            try:
                audio = await client.content.create_audio(
                    notebook_id=notebook_id,
                    source_ids=source_ids,
                    format="deep_dive",
                )
                results["audio"] = {"status": "started", "artifact_id": audio.artifact_id}
            except Exception as e:
                results["audio"] = {"status": "failed", "error": str(e)}
        
        # Generate video
        if "video" in content_types:
            try:
                video = await client.content.create_video(
                    notebook_id=notebook_id,
                    source_ids=source_ids,
                    format="explainer",
                    style="auto_select",
                )
                results["video"] = {"status": "started", "artifact_id": video.artifact_id}
            except Exception as e:
                results["video"] = {"status": "failed", "error": str(e)}
        
        # Generate infographic
        if "infographic" in content_types:
            try:
                infographic = await client.content.create_infographic(
                    notebook_id=notebook_id,
                    source_ids=source_ids,
                    orientation="landscape",
                    detail_level="standard",
                )
                results["infographic"] = {"status": "started", "artifact_id": infographic.artifact_id}
            except Exception as e:
                results["infographic"] = {"status": "failed", "error": str(e)}
        
        # Generate slides
        if "slides" in content_types:
            try:
                slides = await client.content.create_slides(
                    notebook_id=notebook_id,
                    source_ids=source_ids,
                    format="detailed_deck",
                )
                results["slides"] = {"status": "started", "artifact_id": slides.artifact_id}
            except Exception as e:
                results["slides"] = {"status": "failed", "error": str(e)}
                
    except PyNotebookLMError as e:
        results["error"] = str(e)
    
    return results


async def batch_generate_content(
    notebook_ids: List[str],
    content_types: List[str],
    max_concurrent: int = 3,
) -> dict:
    """
    Generate content for multiple notebooks concurrently.

    Args:
        notebook_ids: List of notebook IDs to process
        content_types: Content types to generate for each notebook
        max_concurrent: Maximum concurrent operations

    Returns:
        Dictionary mapping notebook IDs to their results
    """
    console.print(Panel.fit(
        f"[bold cyan]Batch Content Generation[/bold cyan]\n"
        f"Notebooks: {len(notebook_ids)}\n"
        f"Content Types: {', '.join(content_types)}",
        title="Starting Batch Operation",
    ))
    
    results = {}
    
    async with NotebookLMClient() as client:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            
            task = progress.add_task(
                "Processing notebooks...",
                total=len(notebook_ids),
            )
            
            # Process in batches to limit concurrency
            for i in range(0, len(notebook_ids), max_concurrent):
                batch = notebook_ids[i:i + max_concurrent]
                
                # Create tasks for this batch
                tasks = [
                    generate_content_for_notebook(client, nb_id, content_types)
                    for nb_id in batch
                ]
                
                # Execute batch concurrently
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Store results
                for nb_id, result in zip(batch, batch_results):
                    if isinstance(result, Exception):
                        results[nb_id] = {"error": str(result)}
                    else:
                        results[nb_id] = result
                    
                    progress.update(task, advance=1)
    
    return results


def display_results(results: dict) -> None:
    """Display batch operation results in a formatted table."""
    table = Table(title="Batch Generation Results")
    table.add_column("Notebook ID", style="cyan", width=20)
    table.add_column("Status", style="yellow", width=10)
    table.add_column("Details", style="green")
    
    success_count = 0
    error_count = 0
    
    for notebook_id, result in results.items():
        if "error" in result:
            table.add_row(
                notebook_id[:20],
                "[red]ERROR[/red]",
                result["error"][:50],
            )
            error_count += 1
        else:
            status_parts = []
            for content_type, info in result.items():
                if info["status"] == "started":
                    status_parts.append(f"{content_type}: ✅")
                else:
                    status_parts.append(f"{content_type}: ❌")
            
            table.add_row(
                notebook_id[:20],
                "[green]OK[/green]",
                " | ".join(status_parts),
            )
            success_count += 1
    
    console.print(table)
    console.print(f"\n[bold]Summary:[/bold] {success_count} successful, {error_count} errors")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Batch generate content for multiple NotebookLM notebooks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate audio for specific notebooks
  python content_batch_generator.py --type audio --notebooks nb1,nb2,nb3

  # Generate all content types from file
  python content_batch_generator.py --type all --file notebooks.txt

  # Custom concurrent limit
  python content_batch_generator.py --type video --file notebooks.txt --concurrent 5
        """,
    )
    
    parser.add_argument(
        "--type",
        choices=["audio", "video", "infographic", "slides", "all"],
        required=True,
        help="Content type to generate (or 'all' for all types)",
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--notebooks",
        help="Comma-separated list of notebook IDs",
    )
    group.add_argument(
        "--file",
        help="File containing notebook IDs (one per line)",
    )
    
    parser.add_argument(
        "--concurrent",
        type=int,
        default=3,
        help="Maximum concurrent operations (default: 3)",
    )
    
    args = parser.parse_args()
    
    # Parse notebook IDs
    if args.notebooks:
        notebook_ids = [nb.strip() for nb in args.notebooks.split(",")]
    else:
        with open(args.file) as f:
            notebook_ids = [line.strip() for line in f if line.strip()]
    
    # Parse content types
    if args.type == "all":
        content_types = ["audio", "video", "infographic", "slides"]
    else:
        content_types = [args.type]
    
    # Run batch operation
    try:
        results = asyncio.run(
            batch_generate_content(
                notebook_ids=notebook_ids,
                content_types=content_types,
                max_concurrent=args.concurrent,
            )
        )
        display_results(results)
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
