# PyNotebookLM Examples

This directory contains practical examples demonstrating how to use PyNotebookLM in real-world scenarios.

## Prerequisites

1. Install PyNotebookLM:
```bash
pip install pynotebooklm
```

2. Authenticate:
```bash
pynotebooklm auth login
```

3. Install optional dependencies for rich console output:
```bash
pip install rich
```

## Examples

### 01_basic_usage.py
**Basic Usage - Getting Started**

Demonstrates fundamental operations:
- Authenticating with NotebookLM
- Creating a notebook
- Adding various types of sources (URL, YouTube, text)
- Querying the notebook
- Getting summaries

```bash
python examples/01_basic_usage.py
```

### 02_research_workflow.py
**Research Workflow - Discovery & Import**

Shows how to use research discovery features:
- Starting standard and deep web research
- Polling for research results
- Importing discovered sources
- Handling async research operations

```bash
python examples/02_research_workflow.py
```

### 03_content_generation.py
**Content Generation - Multi-modal Outputs**

Demonstrates creating various content types:
- Audio overviews (podcasts)
- Video overviews with different styles
- Infographics with custom orientations
- Slide decks for presentations
- Polling artifact generation status

```bash
python examples/03_content_generation.py
```

### 04_study_tools.py
**Study Tools - Educational Aids**

Shows study aid generation:
- Flashcards with different difficulties
- Quizzes with custom question counts
- Data tables for structured extraction
- Briefing documents

```bash
python examples/04_study_tools.py
```

### 05_mind_maps.py
**Mind Maps - Visual Knowledge Graphs**

Demonstrates mind mapping capabilities:
- Creating mind maps from sources
- Listing existing mind maps
- Exporting to JSON, OPML, and FreeMind formats
- Visual tree display

```bash
python examples/05_mind_maps.py
```

### 06_batch_operations.py
**Batch Operations - Concurrent Processing**

Demonstrates efficient batch processing:
- Adding multiple sources concurrently
- Creating multiple notebooks in parallel
- Bulk deletion operations
- Rate limiting and chunking strategies
- Progress tracking for batch operations

```bash
python examples/06_batch_operations.py
```

### 07_error_handling.py
**Error Handling - Production Patterns**

Comprehensive error handling guide:
- Catching specific exceptions
- Using retry strategies
- Graceful degradation
- Custom retry configurations
- Timeout handling

```bash
python examples/07_error_handling.py
```

## Notes

- **Studio Artifacts**: Content generation (audio, video, slides, etc.) typically takes 60-300 seconds. Use `pynotebooklm studio status <notebook_id>` to check progress.

- **Research Operations**: Deep research can take 60-120 seconds. The examples poll a few times then exit. In production, implement proper polling with backoff.

- **Rate Limits**: The library automatically handles rate limits with exponential backoff. See `07_error_handling.py` for customization options.

- **Cleanup**: All examples clean up created notebooks automatically. Remove the cleanup code if you want to inspect results in the NotebookLM web UI.

## Environment Variables

Configure retry behavior:
```bash
export PYNOTEBOOKLM_MAX_RETRIES=5
export PYNOTEBOOKLM_BASE_DELAY=2.0
export PYNOTEBOOKLM_MAX_DELAY=60.0
```

Enable debug logging:
```bash
export PYNOTEBOOKLM_DEBUG=1
```

## Contribution

Feel free to add more examples! Follow the existing pattern:
1. Use rich console output for visual appeal
2. Include comprehensive error handling
3. Add docstrings explaining use cases
4. Clean up resources after execution
