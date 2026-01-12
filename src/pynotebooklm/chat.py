"""
Chat and Writing tools for PyNotebookLM.

This module provides the ChatSession class for interacting with NotebookLM's
chat, writing, and studio definition capabilities.
"""

import json
import logging
from typing import Any

from .api import (
    STUDIO_TYPE_REPORT,
    NotebookLMAPI,
    parse_notebook_response,
)
from .mindmaps import MindMapGenerator
from .session import BrowserSession

logger = logging.getLogger(__name__)


class ChatSession:
    """
    Manages chat conversation and content creation sessions.

    Example:
        >>> async with BrowserSession(auth) as session:
        ...     chat = ChatSession(session)
        ...     answer = await chat.query(nb_id, "Summarize this")
    """

    # Chat configuration constants
    GOAL_DEFAULT = 1
    GOAL_CUSTOM = 2
    GOAL_LEARNING = 3

    LENGTH_DEFAULT = 1
    LENGTH_LONGER = 4
    LENGTH_SHORTER = 5

    def __init__(self, session: BrowserSession) -> None:
        """
        Initialize the chat session.

        Args:
            session: Active BrowserSession instance.
        """
        self._session = session
        self._api = NotebookLMAPI(session)

    async def _get_all_source_ids(self, notebook_id: str) -> list[str]:
        """Helper to get all source IDs for a notebook."""
        try:
            raw_data = await self._api.get_notebook(notebook_id)
            if not raw_data:
                return []

            notebook = parse_notebook_response(raw_data)
            return [s.id for s in notebook.sources if s.id]
        except Exception as e:
            logger.warning(
                "Failed to fetch sources for notebook %s: %s", notebook_id, e
            )
            return []

    async def query(
        self,
        notebook_id: str,
        question: str,
        source_ids: list[str] | None = None,
        conversation_id: str | None = None,
    ) -> str:
        """
        Ask a question to the notebook.

        Args:
            notebook_id: Notebook UUID.
            question: The question text.
            source_ids: Optional list of source IDs to limit scope.
            conversation_id: Optional conversation ID for follow-up.

        Returns:
            The AI's answer text.
        """
        logger.info("Querying notebook %s: %s", notebook_id, question)

        # If no sources provided, use all sources
        if not source_ids:
            source_ids = await self._get_all_source_ids(notebook_id)
            logger.debug("Using all %d sources for query", len(source_ids))

        result = await self._api.query_notebook(
            notebook_id,
            question,
            source_ids=source_ids,
            conversation_id=conversation_id,
        )

        raw_response = result.get("raw_response", "")
        answer = self._parse_query_response(raw_response)

        return answer

    async def configure(
        self,
        notebook_id: str,
        goal: str = "default",
        custom_prompt: str | None = None,
        length: str = "default",
    ) -> dict[str, Any]:
        """
        Configure chat settings (tone, style, length).

        Args:
            notebook_id: Notebook UUID.
            goal: "default", "learning", "custom".
            custom_prompt: Required if goal is "custom".
            length: "default", "longer", "shorter".
        """
        goal_map = {
            "default": self.GOAL_DEFAULT,
            "learning": self.GOAL_LEARNING,
            "custom": self.GOAL_CUSTOM,
        }
        length_map = {
            "default": self.LENGTH_DEFAULT,
            "longer": self.LENGTH_LONGER,
            "shorter": self.LENGTH_SHORTER,
        }

        goal_code = goal_map.get(goal.lower(), self.GOAL_DEFAULT)
        length_code = length_map.get(length.lower(), self.LENGTH_DEFAULT)

        if goal.lower() == "custom" and not custom_prompt:
            raise ValueError("custom_prompt is required for 'custom' goal")

        logger.info("Configuring chat: goal=%s, length=%s", goal, length)

        return await self._api.configure_chat(
            notebook_id,
            goal=goal_code,
            custom_prompt=custom_prompt,
            length=length_code,
        )

    async def get_notebook_summary(self, notebook_id: str) -> dict[str, Any]:
        """
        Get AI summary and suggested topics for the notebook.

        Returns dict with keys: 'summary', 'suggested_topics'
        """
        raw = await self._api.get_notebook_summary(notebook_id)

        # Parse result
        summary = ""
        suggested_topics: list[dict[str, str]] = []

        if raw and isinstance(raw, list):
            # Summary is at result[0][0]
            if len(raw) > 0 and isinstance(raw[0], list) and len(raw[0]) > 0:
                summary = raw[0][0]

            # Suggested topics are at result[1][0]
            if len(raw) > 1 and raw[1]:
                topics_data = (
                    raw[1][0] if isinstance(raw[1], list) and len(raw[1]) > 0 else []
                )
                for topic in topics_data:
                    if isinstance(topic, list) and len(topic) >= 2:
                        suggested_topics.append(
                            {
                                "question": topic[0],
                                "prompt": topic[1],
                            }
                        )

        return {
            "summary": summary,
            "suggested_topics": suggested_topics,
        }

    async def get_source_summary(self, source_id: str) -> dict[str, Any]:
        """
        Get AI summary and keywords for a source.

        Returns dict with keys: 'summary', 'keywords'
        """
        raw = await self._api.get_source_guide(source_id)

        summary = ""
        keywords: list[str] = []

        if raw and isinstance(raw, list):
            if len(raw) > 0 and isinstance(raw[0], list):
                if len(raw[0]) > 0 and isinstance(raw[0][0], list):
                    inner = raw[0][0]

                    if (
                        len(inner) > 1
                        and isinstance(inner[1], list)
                        and len(inner[1]) > 0
                    ):
                        summary = inner[1][0]

                    if (
                        len(inner) > 2
                        and isinstance(inner[2], list)
                        and len(inner[2]) > 0
                    ):
                        keywords = inner[2][0] if isinstance(inner[2][0], list) else []

        return {
            "summary": summary,
            "keywords": keywords,
        }

    async def create_report(
        self,
        notebook_id: str,
        title: str,
        description: str,
        prompt: str,
        source_ids: list[str] | None = None,
        language: str = "en",
    ) -> dict[str, Any]:
        """
        Create a report (briefing doc, blog post, etc) artifact.
        """
        # If no sources provided, use all sources
        if not source_ids:
            source_ids = await self._get_all_source_ids(notebook_id)
            logger.debug("Using all %d sources for report", len(source_ids))

        # Build source IDs structure
        sources_nested = [[[sid]] for sid in source_ids] if source_ids else []
        sources_simple = [[sid] for sid in source_ids] if source_ids else []

        # Options at position 7
        report_options = [
            None,
            [title, description, None, sources_simple, language, prompt, None, True],
        ]

        # Outer content params
        content = [
            None,
            None,
            STUDIO_TYPE_REPORT,
            sources_nested,
            None,
            None,
            None,
            report_options,
        ]

        logger.info("Creating report '%s'...", title)
        result = await self._api.create_studio_artifact(
            notebook_id, STUDIO_TYPE_REPORT, content
        )

        # Parse result for artifact_id
        artifact_id = None
        if result and isinstance(result, list) and len(result) > 0:
            artifact_data = result[0]
            if isinstance(artifact_data, list) and len(artifact_data) > 0:
                first_item = artifact_data[0]
                # It might be a string ID directly or wrapped in list
                if isinstance(first_item, str):
                    artifact_id = first_item
                elif isinstance(first_item, list) and len(first_item) > 0:
                    artifact_id = first_item[0]

        return {
            "artifact_id": artifact_id,
            "status": "in_progress",
        }

    async def create_briefing(
        self, notebook_id: str, source_ids: list[str] | None = None
    ) -> dict[str, Any]:
        """Convenience method to create a Briefing Doc."""
        return await self.create_report(
            notebook_id,
            title="Briefing Doc",
            description="Key insights and quotes",
            prompt="Create a comprehensive briefing document...",
            source_ids=source_ids,
        )

    async def list_artifacts(self, notebook_id: str) -> list[dict[str, Any]]:
        """List all studio artifacts and their statuses."""
        # Get studio artifacts (audio, video, reports)
        artifacts = await self._api.list_studio_artifacts(notebook_id)

        # Get mind maps
        try:
            mm_gen = MindMapGenerator(self._session)
            mind_maps = await mm_gen.list(notebook_id)
            for mm in mind_maps:
                artifacts.append(
                    {
                        "id": mm.id,
                        "title": mm.title,
                        "type": "Mind Map",
                        "status": "completed",
                        "created_at": mm.created_at,
                    }
                )
        except Exception as e:
            logger.warning("Failed to list mind maps: %s", e)

        return artifacts

    def _parse_query_response(self, response_text: str) -> str:
        """
        Parse streaming query response to extract the final answer.
        """
        if not response_text:
            return ""

        longest_answer = ""
        longest_thinking = ""
        chunks = self._session.parse_streaming_response(response_text)
        for chunk in chunks:
            text, is_answer = self._extract_answer_from_chunk(chunk)
            if text:
                if is_answer and len(text) > len(longest_answer):
                    longest_answer = text
                elif not is_answer and len(text) > len(longest_thinking):
                    longest_thinking = text

        return longest_answer if longest_answer else longest_thinking

    def _extract_answer_from_chunk(self, chunk: Any) -> tuple[str | None, bool]:
        """Extract answer from a JSON query chunk."""
        data = chunk
        if isinstance(chunk, str):
            try:
                data = json.loads(chunk)
            except json.JSONDecodeError:
                return None, False

        if not isinstance(data, list) or len(data) == 0:
            return None, False

        for item in data:
            if not isinstance(item, list) or len(item) < 3:
                continue
            if item[0] != "wrb.fr":
                continue

            inner_json_str = item[2]
            if not isinstance(inner_json_str, str):
                continue

            try:
                inner_data = json.loads(inner_json_str)
            except json.JSONDecodeError:
                continue

            # Type indicator is at inner_data[0][4][-1]: 1 = answer, 2 = thinking
            if isinstance(inner_data, list) and len(inner_data) > 0:
                first_elem = inner_data[0]

                # Case A: nested list (standard)
                if isinstance(first_elem, list) and len(first_elem) > 0:
                    answer_text = first_elem[0]
                    # REDUCED THRESHOLD: > 0 chars (was 20)
                    if isinstance(answer_text, str) and len(answer_text) > 0:
                        # Check type
                        is_answer = False
                        if (
                            len(first_elem) > 4
                            and isinstance(first_elem[4], list)
                            and len(first_elem[4]) > 0
                        ):
                            # Check for type code safely
                            val = first_elem[4][-1]
                            if isinstance(val, int) and val == 1:
                                is_answer = True

                        return answer_text, is_answer

                # Case B: direct string (fallback)
                elif isinstance(first_elem, str) and len(first_elem) > 0:
                    return first_elem, False

        return None, False
