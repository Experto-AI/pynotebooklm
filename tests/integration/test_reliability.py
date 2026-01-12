"""
Integration-style tests for reliability improvements.
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pynotebooklm.exceptions import APIError, AuthenticationError
from pynotebooklm.session import BrowserSession


@pytest.fixture
def mock_auth():
    auth = MagicMock()
    auth.is_authenticated.return_value = True
    auth.is_expired.return_value = False
    auth.get_cookies.return_value = []
    auth.refresh = AsyncMock()
    return auth


@pytest.mark.asyncio
async def test_call_rpc_auto_refresh(mock_auth):
    session = BrowserSession(mock_auth, auto_refresh=True)
    session._page = AsyncMock()
    session._page.url = "https://notebooklm.google.com/"
    session._csrf_token = "token"
    session._csrf_cached_at = datetime.now()

    response = {
        "ok": True,
        "status": 200,
        "text": ")]}'\n1\n[]",
    }
    session._page.evaluate = AsyncMock(return_value=response)

    with (
        patch.object(
            session,
            "_check_auth_validity",
            AsyncMock(side_effect=[AuthenticationError("expired"), None]),
        ) as _,
        patch.object(session, "_refresh_session", AsyncMock()) as refresh_mock,
    ):
        result = await session.call_rpc("rpc_id", [])
        refresh_mock.assert_awaited_once()

    assert result == []


@pytest.mark.asyncio
async def test_call_rpc_rate_limit_retry(mock_auth):
    session = BrowserSession(mock_auth)
    session._page = AsyncMock()
    session._page.url = "https://notebooklm.google.com/"
    session._csrf_token = "token"
    session._csrf_cached_at = datetime.now()

    response_rate_limited = {
        "ok": False,
        "status": 429,
        "text": "",
    }

    inner_data = '{"notebooks":[]}'
    json_line = json.dumps(
        [["wrb.fr", "rpc_id", inner_data, None, None, None, "generic"]]
    )
    response_ok = {
        "ok": True,
        "status": 200,
        "text": ")]}'\n12345\n" + json_line,
    }

    session._page.evaluate = AsyncMock(side_effect=[response_rate_limited, response_ok])

    result = await session.call_rpc("rpc_id", [])
    assert result == {"notebooks": []}
    assert session._page.evaluate.call_count == 2


@pytest.mark.asyncio
async def test_call_api_raw_timeout(mock_auth):
    session = BrowserSession(mock_auth)
    session._page = AsyncMock()
    session._page.url = "https://notebooklm.google.com/"
    session._csrf_token = "token"
    session._csrf_cached_at = datetime.now()

    session._page.evaluate = AsyncMock(
        return_value={
            "ok": False,
            "status": 0,
            "statusText": "AbortError",
            "text": "",
        }
    )

    with pytest.raises(APIError):
        await session.call_api_raw("https://example.com", timeout_ms=10)
