# API Reference

This page provides the complete API reference for the PyNotebookLM library, covering all modules from Phases 1-10.

## Unified Client

::: pynotebooklm.client.NotebookLMClient
    options:
      show_root_heading: true
      show_source: true
      members:
        - __init__
        - __aenter__
        - __aexit__
        - notebooks
        - sources
        - research
        - chat
        - mindmaps
        - content
        - study

## Notebook Management

::: pynotebooklm.notebooks.NotebookManager
    options:
      show_root_heading: true
      members:
        - list
        - create
        - get
        - delete
        - rename
        - exists

## Source Management

::: pynotebooklm.sources.SourceManager
    options:
      show_root_heading: true
      members:
        - add_url
        - add_youtube
        - add_text
        - add_drive
        - list_sources
        - delete
        - list_drive

## Research & Discovery

::: pynotebooklm.research.ResearchDiscovery
    options:
      show_root_heading: true
      members:
        - start_research
        - poll_research
        - import_research_sources
        - start_web_research

## Chat & Query

::: pynotebooklm.chat.ChatSession
    options:
      show_root_heading: true
      members:
        - query
        - configure
        - get_citation
        - get_notebook_summary
        - get_source_summary
        - create_briefing
        - list_artifacts

## Mind Maps

::: pynotebooklm.mindmaps.MindMapGenerator
    options:
      show_root_heading: true
      members:
        - generate
        - save
        - create
        - list
        - get

### Export Functions

::: pynotebooklm.mindmaps.export_to_opml
    options:
      show_root_heading: true

::: pynotebooklm.mindmaps.export_to_freemind
    options:
      show_root_heading: true

## Content Generation (Phase 6)

::: pynotebooklm.content.ContentGenerator
    options:
      show_root_heading: true
      members:
        - create_audio
        - create_video
        - create_infographic
        - create_slides
        - poll_status
        - delete

### Content Types and Options

Available formats and options for content generation:

**Audio Formats:**
- `deep_dive` - Conversational podcast (default)
- `brief` - Short summary
- `critique` - Critical analysis
- `debate` - Multiple perspectives

**Video Styles:**
- `auto_select` - Let AI choose
- `classic` - Clean professional style
- `whiteboard` - Hand-drawn style
- `kawaii` - Cute Japanese style
- `anime` - Anime-inspired
- `watercolor` - Watercolor painting
- `retro_print` - Vintage poster style
- `heritage` - Classical art style
- `paper_craft` - Paper cutout style

**Infographic Orientations:**
- `landscape` - 16:9 aspect ratio
- `portrait` - 9:16 aspect ratio
- `square` - 1:1 aspect ratio

**Slide Deck Formats:**
- `detailed_deck` - Comprehensive slides
- `presenter_slides` - Speaker notes style

## Study Tools (Phase 7)

::: pynotebooklm.study.StudyManager
    options:
      show_root_heading: true
      members:
        - create_flashcards
        - create_quiz
        - create_data_table

### Study Tool Options

**Flashcard Difficulties:**
- `easy` - Simple recall questions
- `medium` - Moderate complexity
- `hard` - Advanced concepts

**Quiz Options:**
- `question_count` - Number of questions (default: 2)
- `difficulty` - Difficulty level 1-3 (default: 2)

## Retry Strategies (Phase 10)

::: pynotebooklm.retry.RetryStrategy
    options:
      show_root_heading: true
      members:
        - __init__
        - should_retry
        - calculate_delay

::: pynotebooklm.retry.with_retry
    options:
      show_root_heading: true

### Environment Configuration

Control retry behavior with environment variables:

```bash
export PYNOTEBOOKLM_MAX_RETRIES=5      # Default: 3
export PYNOTEBOOKLM_BASE_DELAY=2.0     # Default: 1.0 seconds
export PYNOTEBOOKLM_MAX_DELAY=120.0    # Default: 60.0 seconds
```

## Data Models

::: pynotebooklm.models.Notebook
    options:
      show_root_heading: true

::: pynotebooklm.models.Source
    options:
      show_root_heading: true

::: pynotebooklm.models.Artifact
    options:
      show_root_heading: true

::: pynotebooklm.models.ChatMessage
    options:
      show_root_heading: true

::: pynotebooklm.models.ResearchResult
    options:
      show_root_heading: true

::: pynotebooklm.models.MindMap
    options:
      show_root_heading: true

::: pynotebooklm.models.MindMapNode
    options:
      show_root_heading: true

::: pynotebooklm.models.StudioArtifact
    options:
      show_root_heading: true

## Exceptions

::: pynotebooklm.exceptions.PyNotebookLMError
    options:
      show_root_heading: true

::: pynotebooklm.exceptions.AuthenticationError
    options:
      show_root_heading: true

::: pynotebooklm.exceptions.NotebookNotFoundError
    options:
      show_root_heading: true

::: pynotebooklm.exceptions.SourceError
    options:
      show_root_heading: true

::: pynotebooklm.exceptions.GenerationError
    options:
      show_root_heading: true

::: pynotebooklm.exceptions.GenerationTimeoutError
    options:
      show_root_heading: true

::: pynotebooklm.exceptions.RateLimitError
    options:
      show_root_heading: true

::: pynotebooklm.exceptions.APIError
    options:
      show_root_heading: true

## Browser Session Management

::: pynotebooklm.session.BrowserSession
    options:
      show_root_heading: true
      members:
        - __init__
        - __aenter__
        - __aexit__
        - call_rpc
        - call_api

## Authentication

::: pynotebooklm.auth.AuthManager
    options:
      show_root_heading: true
      members:
        - login
        - is_authenticated
        - get_cookies
        - refresh

::: pynotebooklm.auth.save_auth_tokens
    options:
      show_root_heading: true

## Usage Examples

For detailed usage examples of all APIs, see:
- [Examples Documentation](examples.md) - Comprehensive code walkthroughs
- [Advanced Usage](advanced_usage.md) - Retry strategies and optimization
- [FAQ](faq.md) - Common issues and solutions
