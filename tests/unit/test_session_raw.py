from unittest.mock import AsyncMock, MagicMock

import pytest

from pynotebooklm.session import APIError, BrowserSession


@pytest.fixture
def mock_auth():
    auth = MagicMock()
    auth.is_authenticated.return_value = True
    auth.get_cookies.return_value = []
    return auth


@pytest.mark.asyncio
async def test_call_api_raw_success(mock_auth):
    session = BrowserSession(mock_auth)
    session._page = AsyncMock()

    # Mock evaluate response
    session._page.evaluate.return_value = {
        "ok": True,
        "status": 200,
        "text": "Raw response",
    }

    result = await session.call_api_raw("http://test.com", body="data")
    assert result == "Raw response"

    # Verify evaluate called with correct args
    args = session._page.evaluate.call_args[0]
    script = args[0]
    params = args[1]
    assert params["body"] == "data"
    assert "fetch(args.endpoint" in script


@pytest.mark.asyncio
async def test_call_api_raw_failure(mock_auth):
    session = BrowserSession(mock_auth)
    session._page = AsyncMock()

    # Mock evaluate response
    session._page.evaluate.return_value = {
        "ok": False,
        "status": 500,
        "statusText": "Server Error",
        "text": "Error details",
    }

    with pytest.raises(APIError) as exc:
        await session.call_api_raw("http://test.com")

    assert "Server Error" in str(exc.value)
