<!--
DOCUMENTATION SCOPE: This file contains the complete inventory of all 31 planned tools.
DO NOT include here: Implementation details, architectural decisions, or reverse engineering notes.
-->

# Tool Inventory

This document lists all 31 tools planned for the library, categorized by their functionality and implementation phase.

## Notebook Management (Phase 2)
Tests: `tests/integration/test_notebooks.py`

| Tool | ID | Description |
|------|----|-------------|
| `notebook_list` | `wXbhsf` | List all notebooks in account |
| `notebook_create` | `CCqFvf` | Create new notebook with name |
| `notebook_get` | `rLM1Ne` | Get notebook details by ID |
| `notebook_rename` | N/A | Rename existing notebook |
| `notebook_delete` | N/A | Delete notebook (requires confirmation) |
| `notebook_describe` | (Phase 4) | AI summary of notebook contents |

## Source Management (Phase 2)
Tests: `tests/integration/test_sources.py`

| Tool | ID | Description |
|------|----|-------------|
| `notebook_add_url` | `izAoDd` | Add web URL as source |
| `notebook_add_text` | `izAoDd` | Add plain text as source |
| `notebook_add_drive` | `izAoDd` | Add Google Drive document |
| `source_list_drive` | N/A | List available Drive documents |
| `source_delete` | `tGMBJ` | Remove source from notebook |
| `source_describe` | (Phase 4) | AI summary of single source |
| `source_sync_drive` | (Phase 4) | Sync/update Drive sources |

## Content Generation (Phase 3)
Tests: `tests/integration/test_content.py`

| Tool | ID | Description |
|------|----|-------------|
| `audio_overview_create` | `R7cb6c` | Generate podcast (deep dive, briefing) |
| `video_overview_create` | N/A | Generate video explainer |
| `infographic_create` | N/A | Generate infographic image |
| `slide_deck_create` | N/A | Generate presentation slides |
| `studio_status` | `gArtLc` | Check generation progress |
| `studio_delete` | (Phase 5) | Delete generated artifact |

## Query & Chat (Phase 4)
Tests: `tests/integration/test_research.py`

| Tool | Description |
|------|-------------|
| `notebook_query` | Ask question, get AI answer with citations |
| `chat_configure` | Set chat style, response length, goals |

## Research (Phase 4)
Tests: `tests/integration/test_research.py`

| Tool | Description |
|------|-------------|
| `research_start` | Start web/Drive research on topic |
| `research_status` | Check research discovery progress |
| `research_import` | Import discovered sources to notebook |

## Study Tools (Phase 5)
Tests: `tests/integration/test_study.py`

| Tool | Description |
|------|-------------|
| `flashcard_create` | Generate study flashcards |
| `quiz_create` | Generate quiz questions |
| `briefing_create` | Generate briefing document |
| `data_table_create` | Generate data analysis table |

## Mind Maps (Phase 5)
Tests: `tests/integration/test_mindmaps.py`

| Tool | Description |
|------|-------------|
| `mindmap_create` | Generate mind map from sources |
| `mindmap_list` | List existing mind maps |
| `mindmap_export_xml` | Export to FreeMind format |
| `mindmap_export_opml` | Export to OPML format |

## Utilities

| Tool | Description |
|------|-------------|
| `save_auth_tokens` | Explicitly save current auth state |
