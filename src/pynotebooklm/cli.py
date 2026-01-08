import asyncio
import typer
from rich.console import Console
from pynotebooklm.auth import AuthManager

app = typer.Typer(help="PyNotebookLM CLI - Management Tools")
console = Console()

@app.command()
def login(timeout: int = typer.Option(300, help="Timeout in seconds")):
    """Login to Google NotebookLM."""
    async def _run_login():
        auth = AuthManager()
        try:
            await auth.login(timeout=timeout)
            console.print("[green]✓ Login successful![/green]")
            console.print(f"  Auth file: {auth.auth_path}")
        except Exception as e:
            console.print(f"[red]Login failed: {e}[/red]")
            raise typer.Exit(1)
            
    asyncio.run(_run_login())

@app.command()
def check():
    """Check authentication status."""
    auth = AuthManager()
    if auth.is_authenticated():
        console.print("[green]✓ Authenticated: True[/green]")
        console.print(f"  Auth file: {auth.auth_path}")
        if auth._auth_state and auth._auth_state.expires_at:
            console.print(f"  Expires: {auth._auth_state.expires_at.isoformat()}")
    else:
        console.print("[red]✗ Authenticated: False[/red]")
        console.print("  Run 'pynotebooklm login' to authenticate")
        raise typer.Exit(1)

@app.command()
def logout():
    """Log out and clear authentication state."""
    auth = AuthManager()
    auth.logout()
    console.print("[green]✓ Logged out successfully[/green]")

if __name__ == "__main__":
    app()
