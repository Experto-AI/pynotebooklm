#!/usr/bin/env python3
"""
Study Tools Example - PyNotebookLM

This example demonstrates study aid generation:
- Flashcards
- Quizzes
- Data tables
- Briefing documents

Author: PyNotebookLM Team
"""

import asyncio
import sys

from rich.console import Console
from rich.panel import Panel

from pynotebooklm import NotebookLMClient
from pynotebooklm.exceptions import PyNotebookLMError

console = Console()


async def create_study_notebook(client: NotebookLMClient) -> str:
    """Create a notebook with educational content."""
    console.print("📓 Creating study notebook...")
    notebook = await client.notebooks.create(name="Study Tools Demo")

    # Add educational sources
    await client.sources.add_text(
        notebook_id=notebook.id,
        title="World War II Overview",
        content="""
        World War II (1939-1945) was a global conflict involving most nations.

        Key Events:
        - September 1, 1939: Germany invades Poland, starting the war
        - December 7, 1941: Japan attacks Pearl Harbor
        - June 6, 1944: D-Day invasion of Normandy
        - August 6-9, 1945: Atomic bombs dropped on Hiroshima and Nagasaki
        - September 2, 1945: Japan surrenders, ending the war

        Major Powers:
        Allied Powers: USA, UK, Soviet Union, China, France
        Axis Powers: Germany, Italy, Japan

        Casualties: Estimated 70-85 million deaths
        """,
    )

    console.print(f"✅ Created notebook: {notebook.name}\n")
    return notebook.id


async def demonstrate_flashcards(client: NotebookLMClient, notebook_id: str) -> None:
    """Demonstrate flashcard generation."""
    console.print("\n[bold blue]🗂️  Flashcards[/bold blue]")

    # Generate flashcards with medium difficulty
    console.print("Generating flashcards (medium difficulty)...")
    flashcards = await client.study.create_flashcards(
        notebook_id=notebook_id,
        difficulty="medium",
        card_count=10,
    )

    console.print(f"✅ Flashcard generation started!")
    console.print(f"   Difficulty: Medium")
    console.print(f"   Artifact ID: {flashcards.artifact_id}\n")


async def demonstrate_quiz(client: NotebookLMClient, notebook_id: str) -> None:
    """Demonstrate quiz generation."""
    console.print("\n[bold blue]❓ Quiz[/bold blue]")

    # Generate quiz
    console.print("Generating quiz (10 questions, difficulty 2)...")
    quiz = await client.study.create_quiz(
        notebook_id=notebook_id,
        question_count=10,
        difficulty=2,
    )

    console.print(f"✅ Quiz generation started!")
    console.print(f"   Questions: 10")
    console.print(f"   Difficulty: 2 (Medium)")
    console.print(f"   Artifact ID: {quiz.artifact_id}\n")


async def demonstrate_data_table(client: NotebookLMClient, notebook_id: str) -> None:
    """Demonstrate data table extraction."""
    console.print("\n[bold blue]📊 Data Table[/bold blue]")

    # Generate data table
    console.print("Generating data table...")
    table = await client.study.create_data_table(
        notebook_id=notebook_id,
        description="Extract all major events with dates, countries involved, and significance",
        language="en",
    )

    console.print(f"✅ Data table generation started!")
    console.print(f"   Description: Extract events with dates")
    console.print(f"   Artifact ID: {table.artifact_id}\n")


async def demonstrate_briefing(client: NotebookLMClient, notebook_id: str) -> None:
    """Demonstrate briefing document creation."""
    console.print("\n[bold blue]📝 Briefing Document[/bold blue]")

    # Generate briefing
    console.print("Creating briefing document...")
    briefing_response = await client.chat.create_briefing(notebook_id=notebook_id)

    if briefing_response and briefing_response.text:
        console.print("✅ Briefing created!\n")
        console.print(Panel(briefing_response.text[:500] + "...", border_style="green"))
    else:
        console.print("[yellow]⚠️  Briefing created but no preview available[/yellow]\n")


async def main() -> None:
    """Demonstrate study tools."""
    console.print(
        Panel.fit("📚 PyNotebookLM - Study Tools Example", style="bold blue")
    )

    try:
        async with NotebookLMClient() as client:
            # Create study notebook
            notebook_id = await create_study_notebook(client)

            # Demonstrate study tools
            await demonstrate_flashcards(client, notebook_id)
            await demonstrate_quiz(client, notebook_id)
            await demonstrate_data_table(client, notebook_id)
            await demonstrate_briefing(client, notebook_id)

            console.print(
                "\n[yellow]💡 Tip: Use 'pynotebooklm studio status <notebook_id>' "
                "to check when study materials are ready[/yellow]\n"
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
