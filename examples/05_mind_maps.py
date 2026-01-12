#!/usr/bin/env python3
"""
Mind Maps Example - PyNotebookLM

This example demonstrates mind map generation and export:
- Creating mind maps from sources
- Listing existing mind maps
- Exporting to different formats (JSON, OPML, FreeMind)

Author: PyNotebookLM Team
"""

import asyncio
import json
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree

from pynotebooklm import NotebookLMClient
from pynotebooklm.exceptions import PyNotebookLMError

console = Console()


async def create_mindmap_notebook(client: NotebookLMClient) -> str:
    """Create a notebook with content for mind mapping."""
    console.print("📓 Creating notebook for mind mapping...")
    notebook = await client.notebooks.create(name="Mind Map Demo")

    # Add structured content
    await client.sources.add_text(
        notebook_id=notebook.id,
        title="Machine Learning Basics",
        content="""
        Machine Learning is a subset of artificial intelligence.

        Types of Machine Learning:
        1. Supervised Learning
           - Classification
           - Regression
        2. Unsupervised Learning
           - Clustering
           - Dimensionality Reduction
        3. Reinforcement Learning
           - Q-Learning
           - Policy Gradient

        Applications:
        - Computer Vision
        - Natural Language Processing
        - Recommendation Systems
        - Autonomous Vehicles
        """,
    )

    console.print(f"✅ Created notebook: {notebook.name}\n")
    return notebook.id


def display_mindmap_tree(mindmap_json: dict, parent: Tree | None = None, root: bool = True) -> Tree:
    """Display mind map as a rich Tree."""
    if root:
        tree = Tree(f"[bold cyan]{mindmap_json.get('name', 'Root')}[/bold cyan]")
        parent = tree
    else:
        node = parent.add(f"[yellow]{mindmap_json.get('name', 'Node')}[/yellow]")
        parent = node

    for child in mindmap_json.get("children", []):
        display_mindmap_tree(child, parent, root=False)

    return tree if root else parent


async def demonstrate_mindmap_creation(
    client: NotebookLMClient, notebook_id: str
) -> str:
    """Demonstrate mind map creation."""
    console.print("\n[bold blue]🧠 Creating Mind Map[/bold blue]")

    # Create mind map from all sources
    console.print("Generating mind map from sources...")
    mindmap = await client.mindmaps.create(
        notebook_id=notebook_id,
        title="Machine Learning Concepts",
    )

    console.print(f"✅ Mind map created!")
    console.print(f"   ID: {mindmap.map_id}")
    console.print(f"   Title: {mindmap.title}\n")

    # Display structure
    if mindmap.content:
        console.print("[bold]Mind Map Structure:[/bold]")
        tree = display_mindmap_tree(mindmap.content)
        console.print(tree)
        console.print()

    return mindmap.map_id


async def demonstrate_mindmap_listing(
    client: NotebookLMClient, notebook_id: str
) -> None:
    """Demonstrate listing mind maps."""
    console.print("\n[bold blue]📋 Listing Mind Maps[/bold blue]")

    mindmaps = await client.mindmaps.list(notebook_id=notebook_id)

    console.print(f"Found {len(mindmaps)} mind map(s):\n")
    for i, mm in enumerate(mindmaps, 1):
        console.print(f"{i}. {mm.title} (ID: {mm.map_id})")

    console.print()


async def demonstrate_mindmap_export(
    client: NotebookLMClient, notebook_id: str, map_id: str
) -> None:
    """Demonstrate exporting mind maps to different formats."""
    console.print("\n[bold blue]💾 Exporting Mind Maps[/bold blue]")

    # Get the mind map
    mindmap = await client.mindmaps.get(notebook_id=notebook_id, mindmap_id=map_id)

    if not mindmap or not mindmap.content:
        console.print("[yellow]⚠️  No mind map content to export[/yellow]\n")
        return

    # Create output directory
    output_dir = Path("./mindmap_exports")
    output_dir.mkdir(exist_ok=True)

    # Export as JSON
    console.print("1. Exporting as JSON...")
    json_path = output_dir / "mindmap.json"
    with open(json_path, "w") as f:
        json.dump(mindmap.content, f, indent=2)
    console.print(f"   ✅ Saved to: {json_path}")

    # Export as OPML
    console.print("2. Exporting as OPML...")
    opml_content = await client.mindmaps.export_opml(
        notebook_id=notebook_id, mindmap_id=map_id
    )
    opml_path = output_dir / "mindmap.opml"
    with open(opml_path, "w") as f:
        f.write(opml_content)
    console.print(f"   ✅ Saved to: {opml_path}")

    # Export as FreeMind
    console.print("3. Exporting as FreeMind (.mm)...")
    freemind_content = await client.mindmaps.export_freemind(
        notebook_id=notebook_id, mindmap_id=map_id
    )
    freemind_path = output_dir / "mindmap.mm"
    with open(freemind_path, "w") as f:
        f.write(freemind_content)
    console.print(f"   ✅ Saved to: {freemind_path}")

    console.print(f"\n✅ All formats exported to: {output_dir.absolute()}\n")


async def main() -> None:
    """Demonstrate mind map features."""
    console.print(
        Panel.fit("🧠 PyNotebookLM - Mind Maps Example", style="bold blue")
    )

    try:
        async with NotebookLMClient() as client:
            # Create notebook with content
            notebook_id = await create_mindmap_notebook(client)

            # Create mind map
            map_id = await demonstrate_mindmap_creation(client, notebook_id)

            # List mind maps
            await demonstrate_mindmap_listing(client, notebook_id)

            # Export mind map
            await demonstrate_mindmap_export(client, notebook_id, map_id)

            console.print(
                "[yellow]💡 Use mind mapping tools like FreeMind, XMind, or MindNode "
                "to open the exported files[/yellow]\n"
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
