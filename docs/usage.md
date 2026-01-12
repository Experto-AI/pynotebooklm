# Usage Guide

This guide covers common tasks and advanced features of PyNotebookLM.

## Content Generation

NotebookLM can generate various types of content based on your sources.

### Audio Overviews (Podcasts)

Generate a "Deep Dive" conversation between two AI hosts:

```bash
pynotebooklm generate audio <notebook_id> --format deep_dive --length long
```

From Python:

```python
result = await client.content.create_audio(
    notebook_id=notebook_id,
    source_ids=source_ids,
    format=AudioFormat.DEEP_DIVE,
    length=AudioLength.LONG
)
```

### Video Overviews

```bash
pynotebooklm generate video <notebook_id> --style anime
```

### Mind Maps

Generate a hierarchical visualization of your research:

```bash
pynotebooklm mindmap create <notebook_id> --title "Research Landscape"
```

Export to OPML (importable in most mind mapping tools):

```bash
pynotebooklm mindmap export <notebook_id> <mindmap_id> --format opml
```

## Study Tools

Generate aids to help you learn from your sources.

### Flashcards

```bash
pynotebooklm study flashcards <notebook_id> --difficulty hard
```

### Quizzes

```bash
pynotebooklm study quiz <notebook_id> --questions 5 --difficulty 3
```

## Source Management

Add different types of content to your notebooks.

### Web & YouTube URLs
```bash
pynotebooklm sources add <notebook_id> "https://en.wikipedia.org/wiki/Python"
pynotebooklm sources add <notebook_id> "https://www.youtube.com/watch?v=..."
```

### Plain Text
```bash
pynotebooklm sources add-text <notebook_id> "Your research notes here..." --title "My Notes"
```

### Google Drive
```bash
pynotebooklm sources add-drive <notebook_id> "<drive_doc_id>"
```

## Chat & Query

Interact with your sources through AI.

### Asking Questions
```bash
pynotebooklm query ask <notebook_id> "What are the main findings?"
```

### Restricting Scope
Focus the answer on specific sources only:
```bash
pynotebooklm query ask <notebook_id> "..." --sources "source1,source2"
```

### Follow-up Conversations
```bash
pynotebooklm query ask <notebook_id> "What else?" --conversation-id "conv_123"
```

## Research Discovery

Search the web or Google Drive for new sources related to your topic:

```bash
pynotebooklm research start <notebook_id> "Quantum Computing" --deep
# For Google Drive research
pynotebooklm research start <notebook_id> "Internal Project X" --source drive
```

Research is asynchronous. Check the status:

```bash
pynotebooklm research poll <notebook_id>
```


## Advanced Authentication

If you can't use the interactive login, you can manually save tokens:

```python
from pynotebooklm import save_auth_tokens

# From a cookie string
save_auth_tokens(cookies="SID=xxx; HSID=yyy; ...")

# Or from a list of dictionaries
save_auth_tokens(cookies=[{"name": "SID", "value": "xxx", "domain": ".google.com"}])
```
