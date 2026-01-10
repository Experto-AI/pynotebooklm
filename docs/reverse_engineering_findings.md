# Reverse Engineering: Findings from jacob-bd/notebooklm-mcp

**Data Source**: `analysis_repos/jacob-bd-notebooklm-mcp/src/notebooklm_mcp/api_client.py`
**Analysis Date**: 2026-01-10

## Executive Summary

The `jacob-bd` repository contains a complete, Python-based implementation of the NotebookLM internal API. Unlike `PleasePrompto` (which used Playwright), this project uses direct HTTP requests via `httpx`.

**We can port this code directly to PyNotebookLM.**

## RPC Constants Map

| Action | RPC ID | Endpoint | Notes |
| :--- | :--- | :--- | :--- |
| **List Notebooks** | `wXbhsf` | `batchexecute` | Params: `[None, 1, None, [2]]` |
| **Create Notebook** | `CCqFvf` | `batchexecute` | Params: `[title, None, None, [2], ...]` |
| **Get Notebook** | `rLM1Ne` | `batchexecute` | Params: `[notebook_id, None, [2], None, 0]` |
| **Delete Notebook** | `WWINqb` | `batchexecute` | Params: `[[notebook_id], [2]]` |
| **Add Source (URL/Text)** | `izAoDd` | `batchexecute` | Handles URL, Text, and Drive. |
| **Delete Source** | `tGMBJ` | `batchexecute` | Params: `[[[source_id]], [2]]` |
| **Start Fast Research**| `Ljjv0c` | `batchexecute` | Params: `[[query, source_type], None, 1, nb_id]` |
| **Start Deep Research**| `QA9ei` | `batchexecute` | Params: `[None, [1], [query, src_type], 5, nb_id]` |
| **Poll Research** | `e3bVqc` | `batchexecute` | Returns async results. |
| **Query (Chat)** | N/A | `GenerateFreeFormStreamed` | **Special Endpoint**: `/_/LabsTailwindUi/data/google.internal.labs.tailwind.orchestration.v1.LabsTailwindOrchestrationService/GenerateFreeFormStreamed` |

## Key Implementation Details

1.  **Chat & Query**:
    *   Does **NOT** use `batchexecute`.
    *   Uses a streaming gRPC-style endpoint: `GenerateFreeFormStreamed`.
    *   Requires `_reqid` parameter (incrementing integer).
    *   Payload uses specific `f.req` structure with `sources_array` and `conversation_history`.

2.  **Authentication**:
    *   Standard cookie-based auth (`SID`, `HSID`, etc.).
    *   Requires `SNlM0e` (CSRF token) and `FdrFJe` (Session ID) extracted from the HTML homepage.
    *   `jacob-bd` refreshes these tokens on init.

3.  **Drive Sources**:
    *   Supported! Uses `izAoDd` with `mime_type` and `document_id`.

## Action Plan (Porting Strategy)

1.  **API Client**: Update `src/pynotebooklm/api.py` to support the special `GenerateFreeFormStreamed` endpoint (currently we only support `batchexecute`).
2.  **Notebooks**: Implement `create` and `delete` using the payload structures from `api_client.py`. (We already have `wXbhsf` and `rLM1Ne`).
3.  **Sources**: Implement `add_url`, `add_text` using `izAoDd`.
4.  **Chat**: Implement `query` using the new endpoint. This is the biggest piece of missing functionality.

## JSON Payload Reference (Snippet)

```python
# Create Notebook
params = [title, None, None, [2], [1, None, None, None, None, None, None, None, None, None, [1]]]

# List Notebooks
params = [None, 1, None, [2]]

# Add URL Source
# URL: [null, null, [url], null, null, null, null, null, null, null, 1]
params = [[source_data], notebook_id, [2], [1, ...]]
```
