"""
Unit tests for ChatSession logic.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from pynotebooklm.chat import ChatSession


class TestChatSession:
    @pytest.fixture
    def mock_session(self):
        return MagicMock()

    @pytest.fixture
    def chat(self, mock_session):
        return ChatSession(mock_session)

    async def test_query_parses_response(self, chat):
        """Test that query correctly parses the complex JSON response."""
        # Mock the API response
        # The response is a raw string with anti-XSSI prefix and nested JSON

        # This matches what _parse_query_response expects:
        # 1. Anti-XSSI prefix ")]}'"
        # 2. Line with number (byte count)
        # 3. Line with JSON array
        # 4. JSON array contains entries. One entry matches "wrb.fr"
        # 5. That entry has a JSON string at index 2
        # 6. That JSON string parses to inner data
        # 7. Inner data[0][0] is the answer text
        # 8. Inner data[0][4][-1] is type 1 (answer)

        import json

        # Inner data
        inner_data = [
            [
                "This is the answer to the question you asked which is long enough.",
                None,
                None,
                None,
                [None, 1],
            ]
        ]
        inner_data_json = json.dumps(inner_data)

        # Outer item
        outer_item = ["wrb.fr", "ignored", inner_data_json]
        outer_json = json.dumps([{"key": "value"}, outer_item])

        raw_response = f")]}}'\n123\n{outer_json}"

        chat._api.query_notebook = AsyncMock(
            return_value={"raw_response": raw_response}
        )

        answer = await chat.query("nb_id", "question")
        assert (
            answer
            == "This is the answer to the question you asked which is long enough."
        )

    async def test_query_parsing_edge_cases(self, chat):
        """Test parsing edge cases."""
        # Test empty response
        assert chat._parse_query_response("") == ""

        # Test invalid JSON
        res = chat._extract_answer_from_chunk("invalid json")
        assert res == (None, False)

        # Test not a list
        res = chat._extract_answer_from_chunk("{}")
        assert res == (None, False)

        # Test wrong structure
        res = chat._extract_answer_from_chunk('[["wrb.fr", "ignored", "{}"]]')
        assert res == (None, False)

    async def test_configure(self, chat):
        """Test configure chat settings."""
        chat._api.configure_chat = AsyncMock(return_value={})

        await chat.configure("nb_id", goal="learning", length="shorter")

        chat._api.configure_chat.assert_called_once()
        call_args = chat._api.configure_chat.call_args[1]
        assert call_args["goal"] == chat.GOAL_LEARNING
        assert call_args["length"] == chat.LENGTH_SHORTER

    async def test_configure_custom_without_prompt(self, chat):
        """Test configure validaties custom prompt."""
        with pytest.raises(ValueError):
            await chat.configure("nb_id", goal="custom")

    async def test_get_notebook_summary(self, chat):
        """Test get notebook summary parsing."""
        # Mock structure: [ [summary], [ [ [q, p], [q, p] ] ] ]
        raw_response = [
            ["This is the summary."],
            [[["Topic 1", "Prompt 1"], ["Topic 2", "Prompt 2"]]],
        ]
        chat._api.get_notebook_summary = AsyncMock(return_value=raw_response)

        result = await chat.get_notebook_summary("nb_id")

        assert result["summary"] == "This is the summary."
        assert len(result["suggested_topics"]) == 2
        assert result["suggested_topics"][0]["question"] == "Topic 1"

    async def test_get_notebook_summary_empty(self, chat):
        """Test get notebook summary with empty response."""
        chat._api.get_notebook_summary = AsyncMock(return_value=[])
        result = await chat.get_notebook_summary("nb_id")
        assert result["summary"] == ""
        assert result["suggested_topics"] == []

    async def test_get_source_summary(self, chat):
        """Test get source summary parsing."""
        # Mock structure based on code: response[0][0] -> inner
        # inner[1][0] -> summary
        # inner[2][0] -> keywords

        inner = ["id", ["Source Summary"], [["Key1", "Key2"]]]
        raw_response = [[inner]]

        chat._api.get_source_guide = AsyncMock(return_value=raw_response)

        result = await chat.get_source_summary("src_id")

        assert result["summary"] == "Source Summary"
        assert result["keywords"] == ["Key1", "Key2"]

    async def test_get_source_summary_empty(self, chat):
        """Test get source summary with empty response."""
        chat._api.get_source_guide = AsyncMock(return_value=[])
        result = await chat.get_source_summary("src_id")
        assert result["summary"] == ""
        assert result["keywords"] == []

    async def test_create_report(self, chat):
        """Test create report artifact."""
        # API returns [[["artifact_id"]]]
        chat._api.create_studio_artifact = AsyncMock(return_value=[[["art_123"]]])

        result = await chat.create_report("nb_id", "Title", "Desc", "Prompt")

        assert result["artifact_id"] == "art_123"
        chat._api.create_studio_artifact.assert_called_once()

    async def test_create_briefing(self, chat):
        """Test create briefing convenience method."""
        chat.create_report = AsyncMock(return_value={"artifact_id": "art_123"})

        await chat.create_briefing("nb_id")

        chat.create_report.assert_called_once()
        assert chat.create_report.call_args[1]["title"] == "Briefing Doc"
