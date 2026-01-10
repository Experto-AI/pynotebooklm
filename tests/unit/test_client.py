from unittest.mock import MagicMock, patch

import pytest

from pynotebooklm.auth import AuthManager
from pynotebooklm.client import NotebookLMClient


@pytest.mark.asyncio
async def test_client_init():
    auth = MagicMock(spec=AuthManager)
    client = NotebookLMClient(auth=auth)
    assert client._auth == auth
    assert client.notebooks is None


@pytest.mark.asyncio
async def test_client_context_manager():
    auth = MagicMock(spec=AuthManager)

    with patch("pynotebooklm.client.BrowserSession") as mock_session_cls:
        mock_session = mock_session_cls.return_value
        mock_session.__aenter__.return_value = mock_session

        async with NotebookLMClient(auth=auth) as client:
            assert client._session == mock_session
            assert client.notebooks is not None
            assert client.sources is not None
            assert client.research is not None
            assert client.mindmaps is not None
            assert client.content is not None
            assert client.study is not None
            assert client.chat is not None

        mock_session.__aexit__.assert_called_once()
