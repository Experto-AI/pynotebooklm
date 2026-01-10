# RPC Harvesting Strategy

**Objective**: Reverse engineer the internal NotebookLM API ("RPCs") by using browser automation to trigger user actions and capturing the resulting network traffic.

**Methodology**:
1.  **Automate**: Use Playwright to simulate a specific user action (e.g., "Ask Question").
2.  **Intercept**: Monitor all `POST` requests to `https://notebooklm.google.com/_/BarebonesUi/data/batchexecute`.
3.  **Extract**: Decrypt the generic `batchexecute` payload to find the specific `rpcId` (e.g., `wXbhsf`) and the argument structure.

---

## 1. Chat & Query (Flow Derived from Competitor)

This flow is confirmed working in the competitor's codebase (`browser-session.ts`). We can use this to capture the `notebook_query` RPC.

### Browser Sequence
1.  **Navigate**: `https://notebooklm.google.com/notebook/{{notebook_id}}`
2.  **Wait**: Identify the chat input box.
    *   *Primary Selector*: `textarea.query-box-input`
    *   *Fallback Selector*: `textarea[aria-label="Feld für Anfragen"]` (German locale in competitor code, likely `aria-label="Query box"` in English).
3.  **Action**:
    *   Focus input.
    *   Type query string (e.g., "Summarize this doc").
    *   Press `Enter` key.
4.  **Wait**: For response container to appear (streaming detection).

### RPC Capture Target
*   **Look for**: A `batchexecute` request initiated immediately after the `Enter` key.
*   **Payload Signature**: The payload body will contain the exact query string "Summarize this doc".
*   **Goal**: Extract the `rpcId` (likely related to `QUERY_NOTEBOOK`) and the JSON structure wrapping the query text.

---

## 2. Create Notebook (Proposed Flow)

The competitor does *not* automate this (they use a local JSON library). We must implement this flow to capture the `notebook_create` RPC.

### Browser Sequence
1.  **Navigate**: `https://notebooklm.google.com/` (Dashboard)
2.  **Wait**: Look for the "New Notebook" card/button.
    *   *Likely Selector*: `div[role="button"]` containing text "New Notebook" or similar generic tile grid element.
    *   *Action*: Click.
3.  **Action**:
    *   (Optional) If a modal appears asking for a title, type "RPC Test Notebook".
    *   (Optional) Click "Save" or "Create".
4.  **Wait**: Redirect to `/notebook/{{new_notebook_id}}`.

### RPC Capture Target
*   **Look for**: `batchexecute` requests during the click.
*   **Payload Signature**: May be empty (create default) or contain the title.
*   **Response Signature**: The response will definitely contain the new `notebook_id` (12-char string).

---

## 3. Add Source (Proposed Flow)

The competitor requires users to manually add sources. We will automate this to capture `notebook_add_url`, `notebook_add_text`, etc.

### Browser Sequence
1.  **Navigate**: `https://notebooklm.google.com/notebook/{{notebook_id}}`
2.  **Wait**: "Add Source" or "+" button in the left sidebar.
    *   *Action*: Click "+" button.
3.  **Wait**: Source type menu (Drive, Link, Text).
    *   *Action*: Click "Link" (or "Website").
4.  **Action**:
    *   Type URL: `https://example.com`
    *   Click "Insert" or "Add".

### RPC Capture Target
*   **Look for**: `batchexecute` request containing `https://example.com`.
*   **Response**: Confirmation of source addition, source ID.

---

## 4. Research / Deep Dive (Proposed Flow)

This is a key differentiator. We assume `research_start` corresponds to a specific UI Toggle or "Deep Dive" button.

### Browser Sequence
1.  **Navigate**: `https://notebooklm.google.com/notebook/{{notebook_id}}`
2.  **Initial Query**: Type a query in the chat box.
3.  **Action**: Look for "Deep Dive" or "Extended Research" toggle/icon *before* or *after* sending.
    *   *(Investigation required: This might be a specific 'mode' in the chat)*.

### RPC Capture Target
*   Compare the RPC payload of a "Normal Query" vs a "Deep/Research Query".
*   Look for a boolean flag or integer (e.g., `1` vs `2`) in the payload array that toggles this mode.

---

## Tooling Recommendation

To execute this plan, we should build a small helper script `scripts/harvest_rpc.py` that:
1.  Accepts a `flow_name` argument (e.g., `chat`).
2.  Launches Playwright with `pynotebooklm` auth.
3.  Performs the sequence.
4.  Dumps all `batchexecute` request bodies to a JSON file for analysis.
