"""
Unit tests for ChatSession logic.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pynotebooklm.chat import ChatSession
from pynotebooklm.session import BrowserSession


class TestChatSession:
    @pytest.fixture
    def mock_session(self):
        session = MagicMock()
        parser_session = BrowserSession(MagicMock())
        session.parse_streaming_response.side_effect = (
            lambda text: parser_session.parse_streaming_response(text)
        )
        return session

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

    async def test_query_all_sources(self, chat):
        """Test query fetch all sources if none provided."""
        chat._api.get_notebook = AsyncMock(
            return_value=["Test", [["s1", "S1", 1, "url", 1]], "nb123"]
        )
        chat._api.query_notebook = AsyncMock(return_value={"raw_response": ""})

        await chat.query("nb_id", "question")

        chat._api.get_notebook.assert_called_once()
        chat._api.query_notebook.assert_called_once()
        args = chat._api.query_notebook.call_args[1]
        assert args["source_ids"] == ["s1"]

    async def test_get_all_source_ids_exception(self, chat):
        """Test helper handles API errors gracefully."""
        chat._api.get_notebook = AsyncMock(side_effect=Exception("API Down"))
        res = await chat._get_all_source_ids("nb_id")
        assert res == []

    async def test_create_report_all_sources(self, chat):
        """Test create_report fetches sources if not provided."""
        chat._api.get_notebook = AsyncMock(
            return_value=["Test", [["s1", "S1", 1, "url", 1]], "nb123"]
        )
        chat._api.create_studio_artifact = AsyncMock(return_value=[[["art_123"]]])

        await chat.create_report("nb_id", "Title", "Desc", "Prompt")

        chat._api.get_notebook.assert_called_once()
        args = chat._api.create_studio_artifact.call_args[0][2]
        # source_ids should be at index 3 in content
        assert args[3] == [[["s1"]]]

    async def test_list_artifacts_with_mindmaps(self, chat, mock_session):
        """Test artifact list includes mind maps and handles errors."""
        chat._api.list_studio_artifacts = AsyncMock(
            return_value=[{"id": "a1", "status": "completed"}]
        )

        # Mock MindMapGenerator
        with patch("pynotebooklm.chat.MindMapGenerator") as mock_mm_gen_cls:
            mock_mm_gen = MagicMock()
            mm_mock = MagicMock()
            mm_mock.id = "mm1"
            mm_mock.title = "Map 1"
            mm_mock.created_at = None
            mock_mm_gen.list = AsyncMock(return_value=[mm_mock])
            mock_mm_gen_cls.return_value = mock_mm_gen

            res = await chat.list_artifacts("nb_id")
            assert len(res) == 2
            assert res[1]["id"] == "mm1"
            assert res[1]["type"] == "Mind Map"

    async def test_parse_query_response_thinking(self, chat):
        """Test parsing of thinking process."""
        # Type 2 is thinking
        inner_data = [["Thinking...", None, None, None, [None, 2]]]
        import json

        inner_json = json.dumps(inner_data)
        outer_json = json.dumps([["wrb.fr", "id", inner_json]])

        answer = chat._parse_query_response(outer_json)
        assert answer == "Thinking..."

    async def test_extract_answer_case_b(self, chat):
        """Test Case B: direct string fallback in query chunk."""
        import json

        chunk = json.dumps([["wrb.fr", "id", json.dumps(["Direct String"])]])
        text, is_answer = chat._extract_answer_from_chunk(chunk)
        assert text == "Direct String"
        assert is_answer is False
