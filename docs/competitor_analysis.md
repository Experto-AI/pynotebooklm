# Competitor Analysis: notebooklm-mcp

**Repository**: `PleasePrompto/notebooklm-mcp` (also linked to `jacob-bd`)
**Description**: MCP Server for NotebookLM with "31 tools" (approx. 15 implemented tools).
**Analysis Date**: 2026-01-10

## Executive Summary

The `notebooklm-mcp` project does **not** use internal RPC calls (like `wXbhsf` or `CCqFvf`) to control NotebookLM. Instead, it relies entirely on **Browser Automation (Playwright)** to interact with the NotebookLM web interface, primarily by typing into the chat box.

For notebook management, it **does not** support creating or managing notebooks on the Google side programmatically. It uses a **local JSON database (`library.json`)** to track URLs of notebooks that the user *manually* creates and shares.

## Architecture

1.  **Browser Session (`src/session/browser-session.ts`)**:
    *   Uses `patchright` (Playwright fork) to launch a Headless Chrome instance.
    *   Manages Google Authentication by saving/loading cookies and `sessionStorage`.
    *   **Chat Interaction**: Types queries into `textarea.query-box-input` (or `textarea[aria-label="Feld für Anfragen"]`) and simulates "human-like" typing with delays and typos to avoid detection.
    *   **Response Handling**: Waits for the DOM to update with the new answer.

2.  **Notebook Library (`src/library/notebook-library.ts`)**:
    *   A local wrapper around a `library.json` file.
    *   Stores metadata: `id`, `url`, `name`, `description`, `topics`.
    *   **Crucial Limitation**: The `add_notebook` tool *only* adds an entry to this local JSON file. It requires the user to provide an existing NotebookLM URL. It cannot create new notebooks on Google.

3.  **Tools Implementation (`src/tools/handlers.ts`)**:
    *   `ask_question`: Navigates to the stored URL and automates the chat UI.
    *   `notebook_create` (etc): **Not implemented**. The "31 tools" likely refers to the granular conversational steps or is a marketing claim. The actual codebase implements ~15 MCP tools, mostly for local library management.

## Implication for PyNotebookLM

We **cannot** copy RPC definitions from this project because it doesn't use them.

### Options for PyNotebookLM:

1.  **Continue Reverse Engineering RPCs**:
    *   We have identified some RPC IDs (`wXbhsf`, etc.) in our own docs. We need to verify and implement these ourselves.
    *   This is harder but much faster and more robust than UI automation.

2.  **Fallback to UI Automation**:
    *   For features where RPCs are elusive (e.g., complex chat interactions), we can adopt the competitor's strategy of typing into the chat box.
    *   Reference `src/session/browser-session.ts` in the competitor repo for robust selectors and "stealth" strategies (random delays, error detection).

## Key Implementation Details (to enable "Porting")

If we decide to usage UI automation for specific features, here are the key patterns from the competitor:

*   **Selectors**:
    *   Input: `textarea.query-box-input`
    *   Error/Rate Limit: `.error-message`, `.rate-limit-message`
*   **Stealth**:
    *   Uses `humanType` function (random intervals between keystrokes).
    *   Restores `sessionStorage` meticulously to maintain auth state.
*   **Streaming Detection**:
    *   Polls the DOM for the answer container to stabilize.

## Conclusion

The "reverse engineer RPCs" shortcut via this competitor is a dead end. We must proceed with our own reverse engineering effort or accept UI automation as the primary method.
