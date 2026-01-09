"""
Mock RPC responses for testing Phase 2 functionality.

These fixtures simulate NotebookLM's internal API responses for
notebook and source operations.
"""

from typing import Any

# =============================================================================
# Notebook Responses
# =============================================================================

# Sample notebook data structure
# Sample notebook data structure
MOCK_NOTEBOOK_1 = [
    "My Research Notebook",  # Name
    [],  # Sources (empty)
    "nb_abc123",  # Notebook ID
    1704067200000,  # Created timestamp (milliseconds)
    None,  # Updated timestamp/metadata
]

MOCK_NOTEBOOK_2 = [
    "Project Notes",
    [  # Sources
        ["src_111", "Wikipedia Article", 1, "https://en.wikipedia.org/wiki/Python", 1],
        ["src_222", "Research Paper", 1, "https://arxiv.org/abs/2301.00001", 1],
    ],
    "nb_def456",
    1704153600000,
    None,
]

MOCK_NOTEBOOK_WITH_SOURCES = [
    "Full Notebook",
    [
        ["src_001", "Web Article", 1, "https://example.com/article", 1],
        ["src_002", "YouTube Tutorial", 2, "https://youtube.com/watch?v=abc123", 1],
        ["src_003", "Google Doc", 3, "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms", 1],
        ["src_004", "My Notes", 4, None, 1],
    ],
    "nb_xyz789",
    1704240000000,
    None,
]

# List notebooks response
MOCK_LIST_NOTEBOOKS_RESPONSE = [
    [MOCK_NOTEBOOK_1, MOCK_NOTEBOOK_2],
    None,
]

# Create notebook response
MOCK_CREATE_NOTEBOOK_RESPONSE = [
    "New Notebook",
    [],
    "nb_new123",
    1704326400000,
    None,
]


# =============================================================================
# Source Responses
# =============================================================================

MOCK_URL_SOURCE = [
    "src_url001",
    "Example Article",
    1,  # Type: URL
    "https://example.com/article",
    1,  # Status: Ready
]

MOCK_YOUTUBE_SOURCE = [
    "src_yt002",
    "Python Tutorial - Full Course",
    2,  # Type: YouTube
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    1,  # Status: Ready
]

MOCK_DRIVE_SOURCE = [
    "src_drive003",
    "Research Document",
    3,  # Type: Drive
    "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
    1,  # Status: Ready
]

MOCK_TEXT_SOURCE = [
    "src_txt004",
    "My Research Notes",
    4,  # Type: Text
    None,
    1,  # Status: Ready
]

MOCK_PROCESSING_SOURCE = [
    "src_proc005",
    "Large Document",
    1,
    "https://example.com/large",
    0,  # Status: Processing
]

MOCK_FAILED_SOURCE = [
    "src_fail006",
    "Broken Link",
    1,
    "https://invalid-url.example.com",
    2,  # Status: Failed
]


# =============================================================================
# Drive Documents Response
# =============================================================================

MOCK_DRIVE_DOCS = [
    ["doc_id_1", "Project Proposal", "application/vnd.google-apps.document"],
    ["doc_id_2", "Meeting Notes", "application/vnd.google-apps.document"],
    ["doc_id_3", "Research Data", "application/vnd.google-apps.spreadsheet"],
]


# =============================================================================
# Error Responses
# =============================================================================

MOCK_ERROR_NOT_FOUND = {
    "ok": False,
    "status": 404,
    "statusText": "Not Found",
    "text": "Notebook not found",
}

MOCK_ERROR_RATE_LIMIT = {
    "ok": False,
    "status": 429,
    "statusText": "Too Many Requests",
    "text": "Rate limit exceeded",
}

MOCK_ERROR_INVALID_URL = {
    "ok": False,
    "status": 400,
    "statusText": "Bad Request",
    "text": "Invalid URL provided",
}


# =============================================================================
# Helper Functions
# =============================================================================


def make_rpc_response(data: Any) -> dict[str, Any]:
    """
    Wrap data in a simulated RPC response format.

    Args:
        data: The data to wrap.

    Returns:
        Dictionary simulating browser fetch response.
    """
    import json

    # Simulate the nested response structure
    inner = [["wrb.fr", "rpcId", json.dumps(data), None, None]]
    text = ")]}'\n123\n" + json.dumps(inner)

    return {
        "ok": True,
        "status": 200,
        "statusText": "OK",
        "text": text,
    }


def make_error_response(
    status: int = 500, message: str = "Internal Error"
) -> dict[str, Any]:
    """
    Create a simulated error response.

    Args:
        status: HTTP status code.
        message: Error message.

    Returns:
        Dictionary simulating browser fetch error response.
    """
    return {
        "ok": False,
        "status": status,
        "statusText": message,
        "text": message,
    }
