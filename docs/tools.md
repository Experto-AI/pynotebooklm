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

## Research Discovery (Phase 3) ✅
Tests: `tests/integration/test_research.py`

| Tool | ID | Description |
|------|----|-------------|
| `research_fast` | `Ljjv0c` | Start fast web research (param: 1) |
| `research_deep` | `QA9ei` | Start deep research (param: 5) |
| `research_status` | `e3bVqc` | Check research progress |
| `research_import` | `LBwxtb` | Import research findings to notebook |

### Notes:
- **Drive Sync**: Per-source operation, accessed via individual source context menu (not notebook-wide)
- **Topic Suggestions**: Appear as follow-up chips after chat responses; generated as part of chat, not a separate RPC

## Mind Maps (Phase 4)
Tests: `tests/integration/test_mindmaps.py`

| Tool | Description |
|------|-------------|
| `mindmap_create` | Generate mind map from sources |
| `mindmap_list` | List existing mind maps |
| `mindmap_export_xml` | Export to FreeMind format |
| `mindmap_export_opml` | Export to OPML format |

## Query & Chat (Phase 5)
Tests: `tests/integration/test_chat.py`

| Tool | Description |
|------|-------------|
| `notebook_query` | Ask question, get AI answer with citations |
| `chat_configure` | Set chat style, response length, goals |
| `briefing_create` | Generate briefing document |

## Content Generation (Phase 6)
Tests: `tests/integration/test_content.py`

| Tool | ID | Description |
|------|----|-------------|
| `audio_overview_create` | `R7cb6c` | Generate podcast (deep dive, briefing) |
| `video_overview_create` | N/A | Generate video explainer |
| `infographic_create` | N/A | Generate infographic image |
| `slide_deck_create` | N/A | Generate presentation slides |
| `studio_status` | `gArtLc` | Check generation progress |
| `studio_delete` | N/A | Delete generated artifact |

## Study Tools (Phase 7)
Tests: `tests/integration/test_study.py`

| Tool | Description |
|------|-------------|
| `flashcard_create` | Generate study flashcards |
| `quiz_create` | Generate quiz questions |
| `data_table_create` | Generate data analysis table |

## Utilities

| Tool | Description |
|------|-------------|
| `save_auth_tokens` | Explicitly save current auth state |
