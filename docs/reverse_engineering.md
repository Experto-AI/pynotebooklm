# Reverse Engineering NotebookLM RPCs

This guide documents the process of reverse-engineering Google NotebookLM's internal RPC API using the Antigravity "Browser Subagent". This technique is essential for maintaining `pynotebooklm` since the API is undocumented and subject to change.

## The Problem

NotebookLM uses an internal batched RPC protocol (`batchexecute`) where payloads are deeply nested JSON arrays with obscure single-letter keys (e.g., `f.req`). Finding the correct RPC ID (like `tGMBJ` vs `oPkhIc`) and the exact array structure (e.g., `[[["id"]], [2]]`) is impossible through static analysis.

## The Solution: Browser Subagent Interception

We use an agentic browser (Antigravity's `browser_subagent`) to automate the UI interactions while injecting a JavaScript interceptor to capture the underlying network requests.

### 1. The Interceptor Script

This JavaScript code mocks the `window.fetch` and `XMLHttpRequest` functions to "spy" on POST requests sent to the `batchexecute` endpoint.

```javascript
(function() {
    window.CAPTURED_RPCS = window.CAPTURED_RPCS || [];
    
    // Intercept Fetch
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        const [resource, config] = args;
        // Filter for NotebookLM's RPC endpoint
        if (resource && resource.toString().includes('batchexecute') && config && config.method === 'POST') {
            // Check if this payload looks relevant (e.g. contains "delete")
            if (config.body && (config.body.includes('delete') || config.body.includes('source'))) {
                window.CAPTURED_RPCS.push({type: 'fetch', body: config.body.toString()});
            }
        }
        return originalFetch.apply(this, args);
    };

    console.log('RPC Interceptor Active');
})();
```

### 2. The Agent Workflow

The `browser_subagent` performs the following steps autonomously:

1.  **Navigate & Inject**:
    *   Opens `https://notebooklm.google.com/`.
    *   Injects the interceptor script immediately.
2.  **Perform UI Action**:
    *   Clicks "New Notebook".
    *   Adds a dummy source (e.g., `https://example.com`) to ensure a clean state.
    *   *Crucial Step*: Performs the exact action we want to reverse engineer (e.g., identifying the "Delete Source" button, clicking it, and confirming the dialog).
3.  **Extract Data**:
    *   Executes `return window.CAPTURED_RPCS` to retrieve the list of intercepted payloads.

### 3. Analyzing the Payload

The agent returns raw URL-encoded strings like:
`f.req=[[["tGMBJ","[[[\"source_id\"]],[2]]",null,"generic"]]]`

We decode this to identify:
*   **RPC ID**: `tGMBJ` (The string at index 0 of the inner array).
*   **Payload Structure**: `[[["source_id"]], [2]]` (The JSON string at index 1).

## Case Study: Deleting a Source

In January 2026, the `delete_source` function was failing with a 400 error because it used the RPC ID `oPkhIc`.

**Action Taken:**
We tasked the browser subagent: *"Go to NotebookLM, create a notebook, add a source, delete it, and return the captured RPCs."*

**Result:**
The agent returned a captured payload showing the correct ID `tGMBJ` and a simpler array structure than previously thought.

**Fix Applied:**
Updated `api.py`:
```python
# Old (Broken)
RPC_DELETE_SOURCE = "oPkhIc"
payload = [[[source_id]], None, [2]]

# New (Fixed)
RPC_DELETE_SOURCE = "tGMBJ"
payload = [[[source_id]], [2]]
```

## How to specificy the task to the Agent

When asking the AI assistant to perform this, use a prompt like:

> "Use the browser subagent to inspect the 'Delete Source' RPC. Inject a fetch interceptor for 'batchexecute', create a dummy notebook, add a source, delete it via the UI, and return the captured `window.CAPTURED_RPCS`."
