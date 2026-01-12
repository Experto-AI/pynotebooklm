#!/usr/bin/env python3
"""
Error Handling Example - PyNotebookLM

This example demonstrates proper error handling patterns:
- Catching and handling specific exceptions
- Retry strategies
- Graceful degradation
- Logging and debugging

Author: PyNotebookLM Team
"""

import asyncio
import logging
import sys

from rich.console import Console
from rich.panel import Panel

from pynotebooklm import NotebookLMClient
from pynotebooklm.exceptions import (
    APIError,
    AuthenticationError,
    GenerationTimeoutError,
    NotebookNotFoundError,
    PyNotebookLMError,
    RateLimitError,
    SourceError,
)
from pynotebooklm.retry import RetryStrategy, with_retry

console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def demonstrate_authentication_error() -> None:
    """Demonstrate authentication error handling."""
    console.print("\n[bold blue]🔐 Authentication Error Handling[/bold blue]")

    try:
        # This will fail if not authenticated
        async with NotebookLMClient() as client:
            await client.notebooks.list()
            console.print("✅ Authentication successful\n")

    except AuthenticationError as e:
        console.print(f"[red]❌ Authentication failed: {e}[/red]")
        console.print(
            "[yellow]💡 Solution: Run 'pynotebooklm auth login' to authenticate[/yellow]\n"
        )
        # Graceful handling - don't crash the program
        return


async def demonstrate_not_found_error(client: NotebookLMClient) -> None:
    """Demonstrate notebook not found error handling."""
    console.print("\n[bold blue]🔍 Not Found Error Handling[/bold blue]")

    fake_notebook_id = "nonexistent-notebook-id-12345"

    try:
        await client.notebooks.get(notebook_id=fake_notebook_id)

    except NotebookNotFoundError as e:
        console.print(f"[red]❌ {e}[/red]")
        console.print(
            "[yellow]💡 Solution: Check notebook ID or create a new notebook[/yellow]\n"
        )


async def demonstrate_source_error(client: NotebookLMClient, notebook_id: str) -> None:
    """Demonstrate source error handling."""
    console.print("\n[bold blue]📄 Source Error Handling[/bold blue]")

    invalid_url = "not-a-valid-url"

    try:
        await client.sources.add_url(notebook_id=notebook_id, url=invalid_url)

    except SourceError as e:
        console.print(f"[red]❌ {e}[/red]")
        console.print("[yellow]💡 Solution: Provide a valid HTTP/HTTPS URL[/yellow]\n")

    except Exception as e:
        # Fallback for unexpected errors
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        logger.exception("Unexpected error adding source")


async def demonstrate_rate_limit_handling() -> None:
    """Demonstrate rate limit error handling."""
    console.print("\n[bold blue]⏱️  Rate Limit Handling[/bold blue]")

    console.print(
        "Rate limits are handled automatically by the retry decorator.\n"
        "If you hit a rate limit, the library will automatically:\n"
        "  1. Catch the RateLimitError\n"
        "  2. Wait for the suggested retry_after period\n"
        "  3. Retry the request\n"
    )

    # Example: Custom retry strategy for rate-limited operations
    @with_retry(RetryStrategy(max_attempts=5, base_delay=2.0))
    async def rate_limited_operation():
        # Your API call here
        pass

    console.print("✅ Rate limits handled automatically with exponential backoff\n")


async def demonstrate_timeout_handling(
    client: NotebookLMClient, notebook_id: str
) -> None:
    """Demonstrate generation timeout handling."""
    console.print("\n[bold blue]⏳ Timeout Handling[/bold blue]")

    try:
        # Start audio generation (demonstrating async operation)
        console.print("Starting audio generation...")
        audio = await client.content.create_audio(
            notebook_id=notebook_id,
            format="deep_dive",
        )
        console.print(f"✅ Generation started: {audio.artifact_id}\n")

        # In real code, you might poll with a timeout
        # This is just for demonstration
        console.print(
            "[yellow]💡 For long operations, use polling with timeout:[/yellow]"
        )
        console.print(
            "   artifacts = await client.content.poll_status(notebook_id)\n"
        )

    except GenerationTimeoutError as e:
        console.print(f"[red]❌ Generation timed out: {e}[/red]")
        console.print(
            f"[yellow]💡 Timeout was: {e.timeout}s. Consider increasing timeout[/yellow]\n"
        )


async def demonstrate_api_error_handling() -> None:
    """Demonstrate API error handling."""
    console.print("\n[bold blue]🌐 API Error Handling[/bold blue]")

    console.print(
        "API errors (5xx status codes) are automatically retried with exponential backoff.\n"
        "The retry decorator will:\n"
        "  1. Detect transient errors (500, 502, 503, 504)\n"
        "  2. Apply exponential backoff (1s, 2s, 4s, ...)\n"
        "  3. Add random jitter to prevent thundering herd\n"
        "  4. Retry up to max_attempts (default: 3)\n"
    )

    console.print("✅ Transient errors handled automatically\n")


async def demonstrate_custom_retry_strategy() -> None:
    """Demonstrate custom retry strategy."""
    console.print("\n[bold blue]🔄 Custom Retry Strategy[/bold blue]")

    # Create custom retry strategy
    aggressive_retry = RetryStrategy(
        max_attempts=5,  # Try 5 times
        base_delay=0.5,  # Start with 500ms
        max_delay=30.0,  # Cap at 30 seconds
        jitter=True,  # Add randomness
    )

    @with_retry(aggressive_retry)
    async def critical_operation():
        """Example of a critical operation with aggressive retry."""
        # Your important API call here
        pass

    console.print("Custom retry strategy configured:")
    console.print(f"  - Max attempts: {aggressive_retry.max_attempts}")
    console.print(f"  - Base delay: {aggressive_retry.base_delay}s")
    console.print(f"  - Max delay: {aggressive_retry.max_delay}s")
    console.print(f"  - Jitter: {aggressive_retry.jitter}\n")


async def demonstrate_graceful_degradation(
    client: NotebookLMClient, notebook_id: str
) -> None:
    """Demonstrate graceful degradation pattern."""
    console.print("\n[bold blue]🛡️  Graceful Degradation[/bold blue]")

    # Try premium feature, fallback to basic feature
    try:
        console.print("Attempting to generate video...")
        await client.content.create_video(notebook_id=notebook_id, format="explainer")
        console.print("✅ Video generation started\n")

    except (APIError, GenerationTimeoutError) as e:
        console.print(f"[yellow]⚠️  Video generation failed: {e}[/yellow]")
        console.print("[yellow]Falling back to audio overview...[/yellow]")

        try:
            await client.content.create_audio(notebook_id=notebook_id)
            console.print("✅ Audio fallback successful\n")

        except Exception as fallback_error:
            console.print(f"[red]❌ Fallback also failed: {fallback_error}[/red]")
            console.print("[yellow]Continuing with text-only mode...[/yellow]\n")


async def main() -> None:
    """Demonstrate error handling patterns."""
    console.print(
        Panel.fit("🛡️  PyNotebookLM - Error Handling Example", style="bold blue")
    )

    try:
        # Demonstrate authentication error handling
        await demonstrate_authentication_error()

        # Rest of examples require authentication
        async with NotebookLMClient() as client:
            # Create test notebook
            console.print("📓 Creating test notebook...")
            notebook = await client.notebooks.create(name="Error Handling Demo")
            console.print(f"✅ Created: {notebook.name}\n")

            # Add a source for testing
            await client.sources.add_text(
                notebook_id=notebook.id,
                title="Test Content",
                content="This is test content for error handling demonstrations.",
            )

            # Demonstrate different error scenarios
            await demonstrate_not_found_error(client)
            await demonstrate_source_error(client, notebook.id)
            await demonstrate_rate_limit_handling()
            await demonstrate_timeout_handling(client, notebook.id)
            await demonstrate_api_error_handling()
            await demonstrate_custom_retry_strategy()
            await demonstrate_graceful_degradation(client, notebook.id)

            # Cleanup
            console.print("🧹 Cleaning up...")
            await client.notebooks.delete(notebook_id=notebook.id, confirm=True)
            console.print("✅ Deleted notebook\n")

            console.print(
                Panel.fit("✨ Example completed successfully!", style="bold green")
            )

    except PyNotebookLMError as e:
        console.print(f"[red]❌ Unhandled error: {e}[/red]")
        logger.exception("Unhandled exception in main")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
