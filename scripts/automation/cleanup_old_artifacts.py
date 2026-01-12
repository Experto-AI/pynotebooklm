#!/usr/bin/env python3
"""
Cleanup Old Studio Artifacts.

This script deletes old or unwanted studio artifacts (audio, video, slides, etc.)
based on age, type, or status criteria.

Usage:
    python scripts/automation/cleanup_old_artifacts.py --days 30
    python scripts/automation/cleanup_old_artifacts.py --type audio --status failed
    python scripts/automation/cleanup_old_artifacts.py --notebook-id NB123 --dry-run
"""

import argparse
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from pynotebooklm import NotebookLMClient
from pynotebooklm.models import Notebook
from pynotebooklm.exceptions import PyNotebookLMError
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm

console = Console()


async def find_artifacts_to_delete(
    client: NotebookLMClient,
    notebook_ids: List[str] | None = None,
    artifact_type: str | None = None,
    status: str | None = None,
    older_than_days: int | None = None,
) -> List[tuple[str, dict]]:
    """
    Find artifacts matching deletion criteria.

    Args:
        client: NotebookLM client instance
        notebook_ids: Optional list of specific notebook IDs to check
        artifact_type: Optional artifact type filter (audio, video, etc.)
        status: Optional status filter (completed, failed, in_progress)
        older_than_days: Delete artifacts older than this many days

    Returns:
        List of (artifact_id, artifact_info) tuples to delete
    """
    to_delete = []
    
    # Get notebooks to check
    if notebook_ids:
        notebooks = []
        for nb_id in notebook_ids:
            try:
                nb = await client.notebooks.get(nb_id)
                notebooks.append(nb)
            except PyNotebookLMError:
                console.print(f"[yellow]Skipping invalid notebook: {nb_id}[/yellow]")
    else:
        notebooks = await client.notebooks.list()
    
    # Check each notebook
    for notebook in notebooks:
        try:
            artifacts = await client.chat.list_artifacts(notebook.id)
            
            for artifact in artifacts:
                # Apply filters
                if artifact_type and artifact.type != artifact_type:
                    continue
                
                if status and artifact.status != status:
                    continue
                
                if older_than_days and hasattr(artifact, "created_at") and artifact.created_at:
                    age = datetime.now() - artifact.created_at
                    if age.days < older_than_days:
                        continue
                
                # Add to deletion list
                artifact_info = {
                    "id": artifact.id,
                    "type": artifact.type,
                    "status": artifact.status,
                    "notebook_id": notebook.id,
                    "notebook_name": notebook.name,
                    "created_at": artifact.created_at.isoformat() if hasattr(artifact, "created_at") and artifact.created_at else "Unknown",
                }
                to_delete.append((artifact.id, artifact_info))
                
        except PyNotebookLMError as e:
            console.print(f"[yellow]Failed to list artifacts for {notebook.name}: {e}[/yellow]")
    
    return to_delete


async def delete_artifacts(
    client: NotebookLMClient,
    artifacts_to_delete: List[tuple[str, dict]],
    dry_run: bool = False,
) -> dict:
    """
    Delete the specified artifacts.

    Args:
        client: NotebookLM client instance
        artifacts_to_delete: List of (artifact_id, info) tuples
        dry_run: If True, don't actually delete

    Returns:
        Dictionary with deletion results
    """
    results = {"success": 0, "failed": 0, "skipped": 0}
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        
        task = progress.add_task(
            "Deleting artifacts..." if not dry_run else "Simulating deletion...",
            total=len(artifacts_to_delete),
        )
        
        for artifact_id, info in artifacts_to_delete:
            try:
                if not dry_run:
                    await client.content.delete(artifact_id)
                    results["success"] += 1
                else:
                    results["skipped"] += 1
                    
                progress.update(task, advance=1)
                
            except PyNotebookLMError as e:
                console.print(f"[red]Failed to delete {artifact_id}: {e}[/red]")
                results["failed"] += 1
                progress.update(task, advance=1)
    
    return results


def display_artifacts_table(artifacts: List[tuple[str, dict]]) -> None:
    """Display artifacts to be deleted in a table."""
    if not artifacts:
        console.print("[yellow]No artifacts found matching criteria[/yellow]")
        return
    
    table = Table(title=f"Artifacts to Delete ({len(artifacts)} total)")
    table.add_column("Artifact ID", style="cyan", width=12)
    table.add_column("Type", style="yellow", width=12)
    table.add_column("Status", style="magenta", width=12)
    table.add_column("Notebook", style="green", width=20)
    table.add_column("Created", style="blue", width=20)
    
    for artifact_id, info in artifacts[:20]:  # Show first 20
        table.add_row(
            artifact_id[:12],
            info["type"],
            info["status"],
            info["notebook_name"][:20],
            info["created_at"][:20],
        )
    
    console.print(table)
    
    if len(artifacts) > 20:
        console.print(f"[dim]... and {len(artifacts) - 20} more[/dim]")


async def cleanup_artifacts(
    notebook_ids: List[str] | None = None,
    artifact_type: str | None = None,
    status: str | None = None,
    older_than_days: int | None = None,
    dry_run: bool = False,
    force: bool = False,
) -> None:
    """
    Main cleanup logic.

    Args:
        notebook_ids: Optional specific notebooks to clean
        artifact_type: Optional artifact type filter
        status: Optional status filter
        older_than_days: Delete artifacts older than this
        dry_run: Simulate without deleting
        force: Skip confirmation prompt
    """
    console.print(Panel.fit(
        "[bold cyan]Artifact Cleanup Tool[/bold cyan]\n"
        f"{'DRY RUN - No deletions will occur' if dry_run else 'WARNING: This will permanently delete artifacts'}",
        title="Starting Cleanup",
        border_style="yellow" if not dry_run else "green",
    ))
    
    async with NotebookLMClient() as client:
        # Find artifacts
        console.print("\n[yellow]Scanning for artifacts...[/yellow]")
        artifacts_to_delete = await find_artifacts_to_delete(
            client=client,
            notebook_ids=notebook_ids,
            artifact_type=artifact_type,
            status=status,
            older_than_days=older_than_days,
        )
        
        # Display what will be deleted
        display_artifacts_table(artifacts_to_delete)
        
        if not artifacts_to_delete:
            return
        
        # Confirm deletion
        if not dry_run and not force:
            if not Confirm.ask(f"\n[bold red]Delete {len(artifacts_to_delete)} artifacts?[/bold red]"):
                console.print("[yellow]Cancelled by user[/yellow]")
                return
        
        # Perform deletion
        console.print()
        results = await delete_artifacts(client, artifacts_to_delete, dry_run=dry_run)
        
        # Summary
        console.print("\n" + "=" * 60)
        if dry_run:
            console.print(Panel.fit(
                f"[bold green]Dry Run Complete![/bold green]\n\n"
                f"Would delete: [cyan]{results['skipped']}[/cyan] artifacts",
                title="Summary",
            ))
        else:
            console.print(Panel.fit(
                f"[bold green]Cleanup Complete![/bold green]\n\n"
                f"Deleted: [green]{results['success']}[/green]\n"
                f"Failed: [red]{results['failed']}[/red]",
                title="Summary",
            ))


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Cleanup old or unwanted NotebookLM studio artifacts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run: Find artifacts older than 30 days
  python cleanup_old_artifacts.py --days 30 --dry-run

  # Delete failed audio artifacts
  python cleanup_old_artifacts.py --type audio --status failed

  # Clean specific notebook
  python cleanup_old_artifacts.py --notebook-id NB123 --force

  # Delete all completed artifacts over 60 days old
  python cleanup_old_artifacts.py --days 60 --status completed
        """,
    )
    
    parser.add_argument(
        "--notebook-id",
        action="append",
        dest="notebook_ids",
        help="Specific notebook ID to clean (can specify multiple times)",
    )
    parser.add_argument(
        "--type",
        choices=["audio", "video", "infographic", "slides", "flashcards", "quiz", "data_table", "briefing"],
        help="Filter by artifact type",
    )
    parser.add_argument(
        "--status",
        choices=["completed", "failed", "in_progress"],
        help="Filter by status",
    )
    parser.add_argument(
        "--days",
        type=int,
        help="Delete artifacts older than this many days",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview deletions without actually deleting",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt",
    )
    
    args = parser.parse_args()
    
    try:
        asyncio.run(
            cleanup_artifacts(
                notebook_ids=args.notebook_ids,
                artifact_type=args.type,
                status=args.status,
                older_than_days=args.days,
                dry_run=args.dry_run,
                force=args.force,
            )
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Cleanup cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
