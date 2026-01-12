#!/usr/bin/env python3
"""
Backup All Notebooks to JSON.

This script exports all notebooks (including sources, artifacts, and metadata)
to JSON files for backup or migration purposes.

Usage:
    python scripts/automation/backup_notebooks.py --output backups/
    python scripts/automation/backup_notebooks.py --output backup.json --single-file
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from pynotebooklm import NotebookLMClient
from pynotebooklm.models import Notebook
from pynotebooklm.exceptions import PyNotebookLMError
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel

console = Console()


async def export_notebook(client: NotebookLMClient, notebook_id: str) -> Dict[str, Any]:
    """
    Export a single notebook to a dictionary.

    Args:
        client: NotebookLM client instance
        notebook_id: Notebook ID to export

    Returns:
        Dictionary containing all notebook data
    """
    try:
        # Get notebook details
        notebook = await client.notebooks.get(notebook_id)
        
        # Get artifacts
        try:
            artifacts = await client.chat.list_artifacts(notebook_id)
        except Exception:
            artifacts = []
        
        # Prepare export data
        export_data = {
            "id": notebook.id,
            "name": notebook.name,
            "created_at": notebook.created_at.isoformat() if notebook.created_at else None,
            "updated_at": notebook.updated_at.isoformat() if notebook.updated_at else None,
            "sources": [
                {
                    "id": source.id,
                    "title": source.title,
                    "type": source.type,
                    "url": source.url if hasattr(source, "url") else None,
                    "status": source.status if hasattr(source, "status") else None,
                    "created_at": source.created_at.isoformat() if hasattr(source, "created_at") and source.created_at else None,
                }
                for source in notebook.sources
            ],
            "artifacts": [
                {
                    "id": artifact.id,
                    "type": artifact.type,
                    "status": artifact.status,
                    "title": artifact.title if hasattr(artifact, "title") else None,
                    "created_at": artifact.created_at.isoformat() if hasattr(artifact, "created_at") and artifact.created_at else None,
                }
                for artifact in artifacts
            ],
            "exported_at": datetime.now().isoformat(),
        }
        
        return export_data
        
    except PyNotebookLMError as e:
        console.print(f"[red]Failed to export {notebook_id}: {e}[/red]")
        return {
            "id": notebook_id,
            "error": str(e),
            "exported_at": datetime.now().isoformat(),
        }


async def backup_all_notebooks(
    output_dir: Path | None = None,
    single_file: Path | None = None,
) -> List[Dict[str, Any]]:
    """
    Backup all notebooks to JSON files.

    Args:
        output_dir: Directory to save individual JSON files (one per notebook)
        single_file: Single JSON file to save all notebooks

    Returns:
        List of exported notebook data
    """
    console.print(Panel.fit(
        "[bold cyan]Notebook Backup Tool[/bold cyan]\n"
        "Exporting all notebooks to JSON",
        title="Starting Backup",
    ))
    
    exported_notebooks = []
    
    async with NotebookLMClient() as client:
        # Get all notebooks
        console.print("[yellow]Fetching notebook list...[/yellow]")
        notebooks = await client.notebooks.list()
        
        if not notebooks:
            console.print("[yellow]No notebooks found to backup[/yellow]")
            return []
        
        console.print(f"[green]Found {len(notebooks)} notebooks[/green]\n")
        
        # Export each notebook with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            
            task = progress.add_task("Exporting notebooks...", total=len(notebooks))
            
            for notebook in notebooks:
                progress.update(task, description=f"Exporting: {notebook.name}")
                
                export_data = await export_notebook(client, notebook.id)
                exported_notebooks.append(export_data)
                
                # Save to individual file if output_dir specified
                if output_dir:
                    output_dir.mkdir(parents=True, exist_ok=True)
                    # Sanitize filename
                    safe_name = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in notebook.name)
                    filename = output_dir / f"{safe_name}_{notebook.id[:8]}.json"
                    
                    with open(filename, "w") as f:
                        json.dump(export_data, f, indent=2)
                
                progress.update(task, advance=1)
    
    # Save to single file if specified
    if single_file:
        single_file.parent.mkdir(parents=True, exist_ok=True)
        with open(single_file, "w") as f:
            json.dump(
                {
                    "backup_date": datetime.now().isoformat(),
                    "notebook_count": len(exported_notebooks),
                    "notebooks": exported_notebooks,
                },
                f,
                indent=2,
            )
    
    return exported_notebooks


def display_summary(exported_notebooks: List[Dict[str, Any]]) -> None:
    """Display backup summary."""
    success_count = sum(1 for nb in exported_notebooks if "error" not in nb)
    error_count = len(exported_notebooks) - success_count
    
    total_sources = sum(len(nb.get("sources", [])) for nb in exported_notebooks if "error" not in nb)
    total_artifacts = sum(len(nb.get("artifacts", [])) for nb in exported_notebooks if "error" not in nb)
    
    console.print("\n" + "=" * 60)
    console.print(Panel.fit(
        f"[bold green]Backup Complete![/bold green]\n\n"
        f"Notebooks: [cyan]{success_count}[/cyan] successful, [red]{error_count}[/red] failed\n"
        f"Total Sources: [cyan]{total_sources}[/cyan]\n"
        f"Total Artifacts: [cyan]{total_artifacts}[/cyan]",
        title="Summary",
    ))


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Backup all NotebookLM notebooks to JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Backup to individual files
  python backup_notebooks.py --output backups/

  # Backup to a single file
  python backup_notebooks.py --single-file backup_2026-01-12.json

  # Both individual and combined
  python backup_notebooks.py --output backups/ --single-file full_backup.json
        """,
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        help="Output directory for individual JSON files",
    )
    parser.add_argument(
        "--single-file",
        type=Path,
        help="Single JSON file for all notebooks",
    )
    
    args = parser.parse_args()
    
    if not args.output and not args.single_file:
        parser.error("At least one of --output or --single-file must be specified")
    
    try:
        exported = asyncio.run(
            backup_all_notebooks(
                output_dir=args.output,
                single_file=args.single_file,
            )
        )
        
        display_summary(exported)
        
        if args.output:
            console.print(f"\n📁 Individual files: [cyan]{args.output}[/cyan]")
        if args.single_file:
            console.print(f"📄 Combined file: [cyan]{args.single_file}[/cyan]")
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Backup cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
