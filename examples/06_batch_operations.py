#!/usr/bin/env python3
"""
Example 06: Batch Operations

Demonstrates how to perform batch operations efficiently:
- Adding multiple sources to a notebook concurrently
- Creating multiple notebooks in parallel
- Bulk deletion operations
- Best practices for concurrent API calls

This example shows how to use asyncio.gather() for parallel operations
while respecting rate limits and handling errors gracefully.
"""

import asyncio
from typing import List

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.panel import Panel

from pynotebooklm import NotebookLMClient
from pynotebooklm.exceptions import PyNotebookLMError


console = Console()


async def batch_add_urls(notebook_id: str, urls: List[str]) -> None:
    """
    Add multiple URLs to a notebook concurrently.
    
    Args:
        notebook_id: Target notebook ID
        urls: List of URLs to add
    """
    console.print("\n[bold cyan]🔗 Batch Adding URLs[/bold cyan]")
    console.print(f"Notebook ID: {notebook_id}")
    console.print(f"Number of URLs: {len(urls)}\n")
    
    async with NotebookLMClient() as client:
        # Create a list of coroutines for parallel execution
        tasks = [
            client.sources.add_url(notebook_id, url)
            for url in urls
        ]
        
        # Execute all tasks concurrently with progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            task = progress.add_task("Adding sources...", total=len(tasks))
            
            # Gather results with error handling
            results = []
            for coro in asyncio.as_completed(tasks):
                try:
                    result = await coro
                    results.append(result)
                    progress.advance(task)
                except PyNotebookLMError as e:
                    console.print(f"[red]Error adding source: {e}[/red]")
                    progress.advance(task)
        
        # Display results
        if results:
            table = Table(title="✅ Successfully Added Sources")
            table.add_column("Source ID", style="cyan")
            table.add_column("Title", style="green")
            
            for source in results:
                table.add_row(source.id, source.title)
            
            console.print(table)


async def batch_create_notebooks(names: List[str]) -> List[str]:
    """
    Create multiple notebooks concurrently.
    
    Args:
        names: List of notebook names
        
    Returns:
        List of created notebook IDs
    """
    console.print("\n[bold cyan]📚 Batch Creating Notebooks[/bold cyan]")
    console.print(f"Number of notebooks: {len(names)}\n")
    
    async with NotebookLMClient() as client:
        # Create tasks for parallel execution
        tasks = [
            client.notebooks.create(name)
            for name in names
        ]
        
        # Execute with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            task = progress.add_task("Creating notebooks...", total=len(tasks))
            
            notebook_ids = []
            for coro in asyncio.as_completed(tasks):
                try:
                    notebook = await coro
                    notebook_ids.append(notebook.id)
                    progress.advance(task)
                except PyNotebookLMError as e:
                    console.print(f"[red]Error creating notebook: {e}[/red]")
                    progress.advance(task)
        
        console.print(f"\n[green]✅ Created {len(notebook_ids)} notebooks[/green]")
        return notebook_ids


async def batch_delete_notebooks(notebook_ids: List[str]) -> None:
    """
    Delete multiple notebooks concurrently.
    
    Args:
        notebook_ids: List of notebook IDs to delete
    """
    console.print("\n[bold yellow]🗑️  Batch Deleting Notebooks[/bold yellow]")
    console.print(f"Number of notebooks: {len(notebook_ids)}\n")
    
    # Confirm deletion
    confirm = input("Are you sure you want to delete these notebooks? (yes/no): ")
    if confirm.lower() != "yes":
        console.print("[yellow]Deletion cancelled[/yellow]")
        return
    
    async with NotebookLMClient() as client:
        # Create delete tasks
        tasks = [
            client.notebooks.delete(notebook_id, confirm=True)
            for notebook_id in notebook_ids
        ]
        
        # Execute with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            task = progress.add_task("Deleting notebooks...", total=len(tasks))
            
            deleted_count = 0
            for coro in asyncio.as_completed(tasks):
                try:
                    await coro
                    deleted_count += 1
                    progress.advance(task)
                except PyNotebookLMError as e:
                    console.print(f"[red]Error deleting notebook: {e}[/red]")
                    progress.advance(task)
        
        console.print(f"\n[green]✅ Deleted {deleted_count} notebooks[/green]")


async def batch_operations_demo() -> None:
    """Demonstrate various batch operations."""
    console.print(Panel.fit(
        "[bold cyan]Batch Operations Demo[/bold cyan]\n"
        "This example demonstrates concurrent operations for improved performance.",
        border_style="cyan"
    ))
    
    # Example URLs for batch adding
    example_urls = [
        "https://www.python.org/dev/peps/pep-0008/",
        "https://www.python.org/dev/peps/pep-0020/",
        "https://docs.python.org/3/library/asyncio.html",
    ]
    
    # Example notebook names
    example_names = [
        "Test Notebook 1",
        "Test Notebook 2",
        "Test Notebook 3",
    ]
    
    try:
        # 1. Batch create notebooks
        console.print("\n[bold]Step 1: Creating notebooks in parallel[/bold]")
        notebook_ids = await batch_create_notebooks(example_names)
        
        if notebook_ids:
            # 2. Add sources to first notebook
            console.print("\n[bold]Step 2: Adding sources to first notebook[/bold]")
            await batch_add_urls(notebook_ids[0], example_urls)
            
            # 3. Batch delete notebooks
            console.print("\n[bold]Step 3: Cleaning up (batch delete)[/bold]")
            await batch_delete_notebooks(notebook_ids)
        
        console.print("\n[bold green]✅ Batch operations completed successfully![/bold green]")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        raise


async def best_practices_demo() -> None:
    """Demonstrate best practices for batch operations."""
    console.print(Panel.fit(
        "[bold cyan]Batch Operations Best Practices[/bold cyan]",
        border_style="cyan"
    ))
    
    console.print("\n[bold]Key Best Practices:[/bold]\n")
    
    practices = [
        ("1. Use asyncio.gather()", "Execute independent operations concurrently"),
        ("2. Handle errors gracefully", "Use try/except for each operation"),
        ("3. Respect rate limits", "Don't overwhelm the API with too many concurrent requests"),
        ("4. Show progress", "Use rich.progress for user feedback"),
        ("5. Batch similar operations", "Group creates, updates, deletes separately"),
        ("6. Set reasonable limits", "Consider limiting concurrent operations to 5-10 tasks"),
    ]
    
    for title, description in practices:
        console.print(f"[cyan]{title}[/cyan]: {description}")
    
    console.print("\n[bold]Example: Rate-Limited Batch Operation[/bold]\n")
    
    # Demonstrate chunking for rate limiting
    async with NotebookLMClient() as client:
        # Simulate a large list of operations
        urls = [f"https://example.com/page{i}" for i in range(20)]
        
        # Process in chunks of 5 to respect rate limits
        chunk_size = 5
        console.print(f"Processing {len(urls)} URLs in chunks of {chunk_size}...\n")
        
        for i in range(0, len(urls), chunk_size):
            chunk = urls[i:i + chunk_size]
            console.print(f"[cyan]Processing chunk {i//chunk_size + 1} ({len(chunk)} URLs)[/cyan]")
            
            # Simulated batch operation (not actually adding to avoid creating real sources)
            # In real code, you would use:
            # tasks = [client.sources.add_url(notebook_id, url) for url in chunk]
            # results = await asyncio.gather(*tasks, return_exceptions=True)
            
            await asyncio.sleep(0.5)  # Simulate network delay
    
    console.print("\n[green]✅ All chunks processed successfully![/green]")


async def main() -> None:
    """Main entry point."""
    console.print("\n[bold]Choose a demo:[/bold]")
    console.print("1. Full batch operations demo (creates/deletes notebooks)")
    console.print("2. Best practices demonstration (read-only)")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        await batch_operations_demo()
    elif choice == "2":
        await best_practices_demo()
    else:
        console.print("[red]Invalid choice[/red]")


if __name__ == "__main__":
    asyncio.run(main())
