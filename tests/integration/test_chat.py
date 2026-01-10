import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from pynotebooklm.api import QUERY_ENDPOINT, RPC_CONFIGURE_CHAT, RPC_CREATE_STUDIO
from pynotebooklm.chat import ChatSession
from pynotebooklm.session import BrowserSession


@pytest.fixture
def mock_session():
    session = MagicMock(spec=BrowserSession)
    session.call_rpc = AsyncMock()
    session.call_api_raw = AsyncMock()
    session.csrf_token = "mock_token"
    return session


@pytest.mark.asyncio
async def test_query(mock_session):
    chat = ChatSession(mock_session)

    # Mock response: XSSI prefix + byte count + JSON chunk
    # Inner JSON: [["Answer text", null, null, null, [1]]]
    long_answer = "This is a much longer answer text that should pass the length check"
    inner_json = json.dumps([[long_answer, None, None, None, [1]]])
    chunk = [["wrb.fr", None, inner_json]]
    chunk_str = json.dumps(chunk)

    mock_response = f")]}}'\n{len(chunk_str)}\n{chunk_str}"

    mock_session.call_api_raw.return_value = mock_response

    answer = await chat.query("nb-123", "Hello")
    assert answer == long_answer

    mock_session.call_api_raw.assert_called_once()
    call_args = mock_session.call_api_raw.call_args
    assert call_args.kwargs["endpoint"].startswith(QUERY_ENDPOINT)


@pytest.mark.asyncio
async def test_configure(mock_session):
    chat = ChatSession(mock_session)
    mock_session.call_rpc.return_value = {}

    await chat.configure(
        "nb-123", goal="custom", custom_prompt="Be pirate", length="shorter"
    )

    mock_session.call_rpc.assert_called_once()
    args = mock_session.call_rpc.call_args[0]
    assert args[0] == RPC_CONFIGURE_CHAT

    params = args[1]
    assert params[0] == "nb-123"
    # Verify structure: params[1][0][7] contains chat settings
    # [[goal, prompt], [length]]
    chat_settings = params[1][0][7]
    assert chat_settings[0] == [2, "Be pirate"]  # Goal 2 = custom
    assert chat_settings[1] == [5]  # Length 5 = shorter


@pytest.mark.asyncio
async def test_create_briefing(mock_session):
    chat = ChatSession(mock_session)
    # Mock create result: [[id, ..., status=1]]
    mock_session.call_rpc.return_value = [[["artifact-123", None, None, None, 1]]]

    result = await chat.create_briefing("nb-123")
    assert result["artifact_id"] == "artifact-123"
    assert result["status"] == "in_progress"

    mock_session.call_rpc.assert_called_once()
    args = mock_session.call_rpc.call_args[0]
    assert args[0] == RPC_CREATE_STUDIO


@pytest.mark.asyncio
async def test_get_notebook_summary(mock_session):
    chat = ChatSession(mock_session)

    # Mock summary result
    # [[summary], [[question, prompt], ...]]
    mock_session.call_rpc.return_value = [
        ["This is a summary"],
        [[["Topic 1", "Prompt 1"], ["Topic 2", "Prompt 2"]]],
    ]

    result = await chat.get_notebook_summary("nb-123")
    assert result["summary"] == "This is a summary"
    assert len(result["suggested_topics"]) == 2
    assert result["suggested_topics"][0]["question"] == "Topic 1"
