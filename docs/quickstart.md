# Quickstart

Get started with PyNotebookLM in three simple steps.

## 1. Installation

Install PyNotebookLM via pip:

```bash
pip install pynotebooklm
```

After installing, you need to install the Playwright browser:

```bash
playwright install chromium
```

## 2. Authentication

First, login to NotebookLM with your Google account:

```bash
pynotebooklm auth login
```

This opens a browser window. Once you log in, cookies are saved to `~/.pynotebooklm/auth.json`.

Verify your authentication status:

```bash
pynotebooklm auth check
```

## 3. Basic Usage

### Using the CLI

List your notebooks:

```bash
pynotebooklm notebooks list
```

!!! tip
    You can run any command or sub-command without arguments to see the available options and help. For example: `pynotebooklm research start`.


### Using the Library

```python
import asyncio
from pynotebooklm import NotebookLMClient

async def main():
    async with NotebookLMClient() as client:
        # Create a new notebook
        notebook = await client.notebooks.create("My New Research")
        print(f"Created: {notebook.name} ({notebook.id})")
        
        # Add a source
        source = await client.sources.add_url(
            notebook.id, 
            "https://en.wikipedia.org/wiki/Artificial_intelligence"
        )
        print(f"Added source: {source.title}")
        
        # Ask a question
        answer = await client.chat.query(notebook.id, "What is AI?")
        print(f"Answer: {answer}")

if __name__ == "__main__":
    asyncio.run(main())
```

See the [Usage Guide](usage.md) for more advanced examples.
