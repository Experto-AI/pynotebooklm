<!--
DOCUMENTATION SCOPE: This file contains the reverse-engineered RPC protocol, authentication flow, and techniques.
DO NOT include here: Public API usage or general architecture.
-->

# Internal API Protocol & Reverse Engineering

## Internal API Protocol

**Base URL:** `https://notebooklm.google.com/_/LabsTailwindUi/data/batchexecute`

### Request Format (RPC Protocol)
Requests are sent as `POST` to the `batchexecute` endpoint. The payload is form-encoded:

```python
# URL-encoded payload
body = f"f.req={urllib.parse.quote(json_payload)}&at={csrf_token}&"
```

The `json_payload` is a complex nested structure:

```python
json_payload = json.dumps([
    [[rpc_id, params, None, "generic"]]
], separators=(',', ':'))
```

### Response Parsing
The response is a custom format that needs text processing before JSON parsing:

1.  **Remove Prefix:** Strip the anti-XSSI prefix `)]}'`.
2.  **Split Lines:** The response is often newline-delimited JSON.
3.  **Extract Data:** The actual data is usually deeply nested within the parsed JSON, often at index `[0][2]`.

### Key RPC Endpoints
(See `docs/tools.md` for tool mappings)

| ID | Operation | Params Structure |
|----|-----------|------------------|
| `wXbhsf` | List Notebooks | `[null, 1, null, [2]]` |
| `CCqFvf` | Create Notebook | `[title, null, null, [2], [...]]` |
| `izAoDd` | Add Source | `[[source_data], notebook_id, [2]]` |
| `tGMBJ` | Delete Source | `[[[source_id]], [2]]` |

## Authentication Flow

**Essential Cookies:**
- `SID`, `HSID`, `SSID`: Google account authentication.
- `__Secure-*PSID`: Secure persistent session tokens.

**Tokens:**
- `CSRF Token`: Often passed as `at=` in the body or strictly required headers.
- `SNlM0e`, `FdrFJe`: specific tokens found in the page HTML (via `window.WIZ_global_data` or similar scripts).

**Strategy:**
Uses `BrowserSession` (Playwright) to log in via the standard Google login flow, then extracts cookies and saves them to `~/.pynotebooklm/auth.json`.

## Reverse Engineering Guide

### The Methodology
Since the API is undocumented, we use an agentic browser approach to discover RPC IDs and payload structures.

### Tooling: Browser Subagent
We use the Antigravity `browser_subagent` to automate UI interactions and intercept network requests.

#### The Interceptor Script
Inject this JavaScript to spy on `batchexecute` calls:

```javascript
(function() {
    window.CAPTURED_RPCS = window.CAPTURED_RPCS || [];
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        const [resource, config] = args;
        if (resource && resource.toString().includes('batchexecute') && config && config.method === 'POST') {
            window.CAPTURED_RPCS.push({type: 'fetch', body: config.body.toString()});
        }
        return originalFetch.apply(this, args);
    };
})();
```

#### Workflow
1.  **Navigate:** Go to `https://notebooklm.google.com`.
2.  **Inject:** Run the interceptor script.
3.  **Action:** Perform the UI action you want to reverse engineer (e.g., "Pin Notebook").
4.  **Extract:** Read `window.CAPTURED_RPCS`.
5.  **Decode:** URL-decode the `f.req` parameter to see the JSON structure.

### Case Study: Deleting a Source
In Jan 2026, `delete_source` failed. By using the subagent to perform the action and capture the RPC, we identified the correct RPC ID changed from `oPkhIc` to `tGMBJ` and the payload structure was simplified.
