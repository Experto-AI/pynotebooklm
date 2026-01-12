"""
Integration tests for ResearchDiscovery.

These tests verify research discovery operations including
starting research, polling for results, and importing sources.

Updated for the new async research API (Jan 2026).
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from pynotebooklm import APIError, AuthManager, BrowserSession
from pynotebooklm.research import (
    ImportedSource,
    ResearchDiscovery,
    ResearchResult,
    ResearchSession,
    ResearchSource,
    ResearchStatus,
    ResearchType,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_auth():
    """Create a mock AuthManager."""
    auth = MagicMock(spec=AuthManager)
    auth.is_authenticated.return_value = True
    auth.get_cookies.return_value = [
        {"name": "SID", "value": "test", "domain": ".google.com"},
        {"name": "HSID", "value": "test", "domain": ".google.com"},
        {"name": "SSID", "value": "test", "domain": ".google.com"},
    ]
    return auth


@pytest.fixture
def mock_session(mock_auth):
    """Create a mock BrowserSession."""
    session = MagicMock(spec=BrowserSession)
    session.call_rpc = AsyncMock()
    return session


@pytest.fixture
def research_discovery(mock_session):
    """Create a ResearchDiscovery with mocked session."""
    return ResearchDiscovery(mock_session)


# =============================================================================
# Mock Research Responses
# =============================================================================

# Start research response: [task_id, report_id]
MOCK_START_RESEARCH_RESPONSE = [
    "task_abc123xyz",  # task_id
    "report_def456",  # report_id (optional, for deep research)
]

# Poll research response: [[task_data, ...], ...]
MOCK_POLL_IN_PROGRESS_RESPONSE = [
    [
        [
            "task_abc123xyz",  # task_id
            [
                None,  # [0] unknown
                ["AI trends 2024", 1],  # [1] query_info: [query, source_type]
                1,  # [2] mode (1=fast, 5=deep)
                [[], ""],  # [3] sources_and_summary: [sources, summary]
                1,  # [4] status (1=in_progress, 2=completed)
            ],
        ],
    ],
]

MOCK_POLL_COMPLETED_RESPONSE = [
    [
        [
            "task_abc123xyz",
            [
                None,
                ["AI trends 2024", 1],
                1,
                [
                    [  # sources
                        [
                            "https://example.com/ai",
                            "AI Trends 2024",
                            "Summary of AI",
                            1,
                        ],
                        ["https://example.com/ml", "ML Guide", "ML overview", 1],
                        ["https://example.com/dl", "Deep Learning", "DL paper", 1],
                    ],
                    "This is the research summary",  # summary
                ],
                2,  # status = completed
            ],
        ],
    ],
]

MOCK_POLL_DEEP_RESEARCH_RESPONSE = [
    [
        [
            "task_deep_123",
            [
                None,
                ["What are the latest AI trends?", 1],
                5,  # mode = deep
                [
                    [
                        [
                            None,
                            "Deep Research Report",
                            None,
                            5,
                            None,
                            None,
                            ["This is a detailed report about AI trends..."],
                        ],
                    ],
                    "",
                ],
                2,
            ],
        ],
    ],
]


# =============================================================================
# Poll With Backoff Tests
# =============================================================================


@pytest.mark.asyncio
async def test_poll_with_backoff_completes(research_discovery, mock_session) -> None:
    """poll_with_backoff returns when research completes."""
    mock_session.call_rpc = AsyncMock(
        side_effect=[
            MOCK_POLL_IN_PROGRESS_RESPONSE,
            MOCK_POLL_COMPLETED_RESPONSE,
        ]
    )

    result = await research_discovery.poll_with_backoff(
        "notebook123", max_attempts=2, base_interval=0, max_interval=0
    )

    assert result.status == ResearchStatus.COMPLETED


# Import research response: [[source1, source2, ...]]
MOCK_IMPORT_RESPONSE = [
    [
        [["src_001"], "AI Trends 2024"],
        [["src_002"], "ML Guide"],
    ]
]


# =============================================================================
# Start Research Tests
# =============================================================================


class TestStartResearch:
    """Tests for ResearchDiscovery.start_research()"""

    @pytest.mark.asyncio
    async def test_start_returns_research_session(
        self, research_discovery, mock_session
    ):
        """Should return ResearchSession with task_id."""
        mock_session.call_rpc.return_value = MOCK_START_RESEARCH_RESPONSE

        session = await research_discovery.start_research("nb_123", "AI trends 2024")

        assert isinstance(session, ResearchSession)
        assert session.task_id == "task_abc123xyz"
        assert session.notebook_id == "nb_123"
        assert session.query == "AI trends 2024"

    @pytest.mark.asyncio
    async def test_start_with_deep_mode(self, research_discovery, mock_session):
        """Should work with deep research mode."""
        mock_session.call_rpc.return_value = MOCK_START_RESEARCH_RESPONSE

        session = await research_discovery.start_research(
            "nb_123", "AI", mode=ResearchType.DEEP
        )

        assert session.mode == "deep"
        assert session.status == ResearchStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_start_with_drive_source(self, research_discovery, mock_session):
        """Should work with drive source type."""
        mock_session.call_rpc.return_value = MOCK_START_RESEARCH_RESPONSE

        session = await research_discovery.start_research(
            "nb_123", "Company docs", source=ResearchSource.DRIVE
        )

        assert session.source == "drive"

    @pytest.mark.asyncio
    async def test_start_rejects_deep_drive_combination(self, research_discovery):
        """Should reject deep research with drive source."""
        with pytest.raises(ValueError, match="Deep Research only supports Web"):
            await research_discovery.start_research(
                "nb_123", "Test", source="drive", mode="deep"
            )

    @pytest.mark.asyncio
    async def test_start_rejects_empty_query(self, research_discovery):
        """Should reject empty query."""
        with pytest.raises(ValueError, match="query cannot be empty"):
            await research_discovery.start_research("nb_123", "")

    @pytest.mark.asyncio
    async def test_start_rejects_empty_notebook_id(self, research_discovery):
        """Should reject empty notebook ID."""
        with pytest.raises(ValueError, match="Notebook ID cannot be empty"):
            await research_discovery.start_research("", "Test topic")

    @pytest.mark.asyncio
    async def test_start_strips_whitespace(self, research_discovery, mock_session):
        """Should strip whitespace from query."""
        mock_session.call_rpc.return_value = MOCK_START_RESEARCH_RESPONSE

        session = await research_discovery.start_research("nb_123", "  Padded Topic  ")

        assert session.query == "Padded Topic"

    @pytest.mark.asyncio
    async def test_start_calls_correct_rpc_for_fast(
        self, research_discovery, mock_session
    ):
        """Should call fast research RPC."""
        mock_session.call_rpc.return_value = MOCK_START_RESEARCH_RESPONSE

        await research_discovery.start_research("nb_123", "Test", mode="fast")

        mock_session.call_rpc.assert_called_once()
        call_args = mock_session.call_rpc.call_args
        assert call_args[0][0] == "Ljjv0c"  # Fast research RPC ID

    @pytest.mark.asyncio
    async def test_start_calls_correct_rpc_for_deep(
        self, research_discovery, mock_session
    ):
        """Should call deep research RPC."""
        mock_session.call_rpc.return_value = MOCK_START_RESEARCH_RESPONSE

        await research_discovery.start_research("nb_123", "Test", mode="deep")

        mock_session.call_rpc.assert_called_once()
        call_args = mock_session.call_rpc.call_args
        assert call_args[0][0] == "QA9ei"  # Deep research RPC ID


# =============================================================================
# Poll Research Tests
# =============================================================================


class TestPollResearch:
    """Tests for ResearchDiscovery.poll_research()"""

    @pytest.mark.asyncio
    async def test_poll_returns_research_session(
        self, research_discovery, mock_session
    ):
        """Should return ResearchSession with status."""
        mock_session.call_rpc.return_value = MOCK_POLL_COMPLETED_RESPONSE

        result = await research_discovery.poll_research("nb_123")

        assert isinstance(result, ResearchSession)
        assert result.task_id == "task_abc123xyz"

    @pytest.mark.asyncio
    async def test_poll_detects_in_progress(self, research_discovery, mock_session):
        """Should detect in-progress status."""
        mock_session.call_rpc.return_value = MOCK_POLL_IN_PROGRESS_RESPONSE

        result = await research_discovery.poll_research("nb_123")

        assert result.status == ResearchStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_poll_detects_completed(self, research_discovery, mock_session):
        """Should detect completed status."""
        mock_session.call_rpc.return_value = MOCK_POLL_COMPLETED_RESPONSE

        result = await research_discovery.poll_research("nb_123")

        assert result.status == ResearchStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_poll_parses_sources(self, research_discovery, mock_session):
        """Should parse discovered sources."""
        mock_session.call_rpc.return_value = MOCK_POLL_COMPLETED_RESPONSE

        result = await research_discovery.poll_research("nb_123")

        assert len(result.results) == 3
        assert result.results[0].title == "AI Trends 2024"
        assert result.results[0].url == "https://example.com/ai"

    @pytest.mark.asyncio
    async def test_poll_parses_summary(self, research_discovery, mock_session):
        """Should parse research summary."""
        mock_session.call_rpc.return_value = MOCK_POLL_COMPLETED_RESPONSE

        result = await research_discovery.poll_research("nb_123")

        assert result.summary == "This is the research summary"

    @pytest.mark.asyncio
    async def test_poll_parses_deep_research_report(
        self, research_discovery, mock_session
    ):
        """Should parse deep research report."""
        mock_session.call_rpc.return_value = MOCK_POLL_DEEP_RESEARCH_RESPONSE

        result = await research_discovery.poll_research("nb_123")

        assert "detailed report" in result.report

    @pytest.mark.asyncio
    async def test_poll_rejects_empty_notebook_id(self, research_discovery):
        """Should reject empty notebook ID."""
        with pytest.raises(ValueError, match="Notebook ID cannot be empty"):
            await research_discovery.poll_research("")

    @pytest.mark.asyncio
    async def test_poll_no_research_found(self, research_discovery, mock_session):
        """Should handle no active research."""
        mock_session.call_rpc.return_value = []

        result = await research_discovery.poll_research("nb_123")

        assert result.status == ResearchStatus.NO_RESEARCH


# =============================================================================
# Import Research Sources Tests
# =============================================================================


class TestImportResearchSources:
    """Tests for ResearchDiscovery.import_research_sources()"""

    @pytest.mark.asyncio
    async def test_import_returns_imported_sources(
        self, research_discovery, mock_session
    ):
        """Should return list of ImportedSource."""
        mock_session.call_rpc.return_value = MOCK_IMPORT_RESPONSE

        sources = [
            ResearchResult(index=0, url="https://example.com/1", title="Test 1"),
            ResearchResult(index=1, url="https://example.com/2", title="Test 2"),
        ]

        result = await research_discovery.import_research_sources(
            "nb_123", "task_abc123", sources
        )

        assert isinstance(result, list)
        assert all(isinstance(s, ImportedSource) for s in result)

    @pytest.mark.asyncio
    async def test_import_rejects_empty_notebook_id(self, research_discovery):
        """Should reject empty notebook ID."""
        sources = [ResearchResult(index=0, url="https://example.com", title="Test")]

        with pytest.raises(ValueError, match="Notebook ID cannot be empty"):
            await research_discovery.import_research_sources("", "task_id", sources)

    @pytest.mark.asyncio
    async def test_import_rejects_empty_task_id(self, research_discovery):
        """Should reject empty task ID."""
        sources = [ResearchResult(index=0, url="https://example.com", title="Test")]

        with pytest.raises(ValueError, match="Task ID cannot be empty"):
            await research_discovery.import_research_sources("nb_123", "", sources)

    @pytest.mark.asyncio
    async def test_import_rejects_empty_sources(self, research_discovery):
        """Should reject empty sources list."""
        with pytest.raises(ValueError, match="Sources list cannot be empty"):
            await research_discovery.import_research_sources("nb_123", "task_id", [])

    @pytest.mark.asyncio
    async def test_import_skips_deep_report_sources(
        self, research_discovery, mock_session
    ):
        """Should skip deep_report type sources (type 5)."""
        mock_session.call_rpc.return_value = MOCK_IMPORT_RESPONSE

        sources = [
            ResearchResult(
                index=0, url="https://example.com", title="Web", result_type=1
            ),
            ResearchResult(index=1, url="", title="Deep Report", result_type=5),
        ]

        await research_discovery.import_research_sources("nb_123", "task_id", sources)

        # Should only send one source to the API
        call_args = mock_session.call_rpc.call_args
        source_array = call_args[0][1][4]  # params[4] is source_array
        assert len(source_array) == 1


# =============================================================================
# Legacy API Compatibility Tests
# =============================================================================


class TestLegacyAPI:
    """Tests for backward-compatible API methods."""

    @pytest.mark.asyncio
    async def test_start_web_research_calls_start_research(
        self, research_discovery, mock_session
    ):
        """start_web_research should work as a wrapper."""
        mock_session.call_rpc.return_value = MOCK_START_RESEARCH_RESPONSE

        session = await research_discovery.start_web_research(
            "nb_123", "AI topics", ResearchType.FAST
        )

        assert isinstance(session, ResearchSession)
        assert session.task_id == "task_abc123xyz"


# =============================================================================
# ResearchResult Model Tests
# =============================================================================


class TestResearchResultModel:
    """Tests for ResearchResult model."""

    def test_creates_with_required_fields(self):
        """Should create with required fields."""
        result = ResearchResult(index=0, title="Test Title")

        assert result.index == 0
        assert result.title == "Test Title"
        assert result.url == ""
        assert result.result_type_name == "web"

    def test_creates_with_all_fields(self):
        """Should create with all fields."""
        result = ResearchResult(
            index=0,
            title="Full Result",
            url="https://example.com",
            description="This is a description",
            result_type=2,
            result_type_name="google_doc",
        )

        assert result.url == "https://example.com"
        assert result.description == "This is a description"
        assert result.result_type == 2


# =============================================================================
# ResearchSession Model Tests
# =============================================================================


class TestResearchSessionModel:
    """Tests for ResearchSession model."""

    def test_creates_with_defaults(self):
        """Should create with default values."""
        session = ResearchSession(task_id="t1", notebook_id="nb1", query="Test")

        assert session.task_id == "t1"
        assert session.query == "Test"
        assert session.status == ResearchStatus.IN_PROGRESS
        assert session.results == []

    def test_status_enum_values(self):
        """Should have correct status enum values."""
        assert ResearchStatus.IN_PROGRESS.value == "in_progress"
        assert ResearchStatus.COMPLETED.value == "completed"
        assert ResearchStatus.NO_RESEARCH.value == "no_research"


# =============================================================================
# ResearchType Enum Tests
# =============================================================================


class TestResearchTypeEnum:
    """Tests for ResearchType enum."""

    def test_has_fast_and_deep(self):
        """Should have FAST and DEEP values."""
        assert ResearchType.FAST.value == "fast"
        assert ResearchType.DEEP.value == "deep"


# =============================================================================
# ResearchSource Enum Tests
# =============================================================================


class TestResearchSourceEnum:
    """Tests for ResearchSource enum."""

    def test_has_web_and_drive(self):
        """Should have WEB and DRIVE values."""
        assert ResearchSource.WEB.value == "web"
        assert ResearchSource.DRIVE.value == "drive"


# =============================================================================
# Additional Coverage Tests
# =============================================================================


class TestStartResearchErrorScenarios:
    """Additional tests for start_research error handling."""

    @pytest.mark.asyncio
    async def test_start_raises_notebook_not_found(
        self, research_discovery, mock_session
    ):
        """Should raise NotebookNotFoundError for 404."""
        from pynotebooklm import NotebookNotFoundError

        mock_session.call_rpc.side_effect = APIError("Not found", status_code=404)

        with pytest.raises(NotebookNotFoundError):
            await research_discovery.start_research("missing_nb", "Test")

    @pytest.mark.asyncio
    async def test_start_raises_api_error_on_no_task_id(
        self, research_discovery, mock_session
    ):
        """Should raise APIError if no task_id returned."""
        mock_session.call_rpc.return_value = []  # Empty response

        with pytest.raises(APIError, match="no task_id returned"):
            await research_discovery.start_research("nb_123", "Test")

    @pytest.mark.asyncio
    async def test_start_with_invalid_source(self, research_discovery):
        """Should reject invalid source type."""
        with pytest.raises(ValueError, match="Invalid source"):
            await research_discovery.start_research("nb_123", "Test", source="invalid")

    @pytest.mark.asyncio
    async def test_start_with_invalid_mode(self, research_discovery):
        """Should reject invalid mode."""
        with pytest.raises(ValueError, match="Invalid mode"):
            await research_discovery.start_research("nb_123", "Test", mode="invalid")


class TestPollResearchErrorScenarios:
    """Additional tests for poll_research error handling."""

    @pytest.mark.asyncio
    async def test_poll_raises_notebook_not_found(
        self, research_discovery, mock_session
    ):
        """Should raise NotebookNotFoundError for 404."""
        from pynotebooklm import NotebookNotFoundError

        mock_session.call_rpc.side_effect = APIError("Not found", status_code=404)

        with pytest.raises(NotebookNotFoundError):
            await research_discovery.poll_research("missing_nb")


class TestImportDriveSources:
    """Tests for Drive source import handling."""

    @pytest.mark.asyncio
    async def test_import_drive_source_with_doc_id(
        self, research_discovery, mock_session
    ):
        """Should extract doc_id from Drive URL."""
        mock_session.call_rpc.return_value = MOCK_IMPORT_RESPONSE

        sources = [
            ResearchResult(
                index=0,
                url="https://docs.google.com/document?id=doc123abc&other=param",
                title="Google Doc",
                result_type=2,  # GOOGLE_DOC
            ),
        ]

        await research_discovery.import_research_sources("nb_123", "task_id", sources)

        call_args = mock_session.call_rpc.call_args
        source_array = call_args[0][1][4]
        # Drive source structure: [[doc_id, mime_type, 1, title], None x9, 2]
        assert source_array[0][0][0] == "doc123abc"

    @pytest.mark.asyncio
    async def test_import_drive_source_with_d_path(
        self, research_discovery, mock_session
    ):
        """Should extract doc_id from /d/ path."""
        mock_session.call_rpc.return_value = MOCK_IMPORT_RESPONSE

        sources = [
            ResearchResult(
                index=0,
                url="https://docs.google.com/document/d/doc456xyz/edit",
                title="Google Doc",
                result_type=2,  # GOOGLE_DOC
            ),
        ]

        await research_discovery.import_research_sources("nb_123", "task_id", sources)

        call_args = mock_session.call_rpc.call_args
        source_array = call_args[0][1][4]
        assert source_array[0][0][0] == "doc456xyz"

    @pytest.mark.asyncio
    async def test_import_drive_source_slides(self, research_discovery, mock_session):
        """Should handle Google Slides source."""
        mock_session.call_rpc.return_value = MOCK_IMPORT_RESPONSE

        sources = [
            ResearchResult(
                index=0,
                url="https://docs.google.com/presentation?id=slide123",
                title="Slides",
                result_type=3,  # GOOGLE_SLIDES
            ),
        ]

        await research_discovery.import_research_sources("nb_123", "task_id", sources)

        call_args = mock_session.call_rpc.call_args
        source_array = call_args[0][1][4]
        assert "presentation" in source_array[0][0][1]

    @pytest.mark.asyncio
    async def test_import_drive_source_sheets(self, research_discovery, mock_session):
        """Should handle Google Sheets source."""
        mock_session.call_rpc.return_value = MOCK_IMPORT_RESPONSE

        sources = [
            ResearchResult(
                index=0,
                url="https://docs.google.com/spreadsheet?id=sheet123",
                title="Sheets",
                result_type=8,  # GOOGLE_SHEETS
            ),
        ]

        await research_discovery.import_research_sources("nb_123", "task_id", sources)

        call_args = mock_session.call_rpc.call_args
        source_array = call_args[0][1][4]
        assert "spreadsheet" in source_array[0][0][1]

    @pytest.mark.asyncio
    async def test_import_drive_source_without_id_param(
        self, research_discovery, mock_session
    ):
        """Should fallback to web-style for Drive URL without id= param."""
        mock_session.call_rpc.return_value = MOCK_IMPORT_RESPONSE

        sources = [
            ResearchResult(
                index=0,
                url="https://docs.google.com/document/abc123",  # No id= param
                title="Doc Without ID",
                result_type=2,
            ),
        ]

        await research_discovery.import_research_sources("nb_123", "task_id", sources)

        call_args = mock_session.call_rpc.call_args
        source_array = call_args[0][1][4]
        # Should fallback to web-style: [None, None, [url, title], ...]
        assert source_array[0][2] == [
            "https://docs.google.com/document/abc123",
            "Doc Without ID",
        ]

    @pytest.mark.asyncio
    async def test_import_returns_empty_when_no_importable_sources(
        self, research_discovery, mock_session
    ):
        """Should return empty list when only deep_report sources."""
        sources = [
            ResearchResult(
                index=0,
                url="",
                title="Deep Report",
                result_type=5,  # deep_report
            ),
        ]

        result = await research_discovery.import_research_sources(
            "nb_123", "task_id", sources
        )

        assert result == []
        mock_session.call_rpc.assert_not_called()

    @pytest.mark.asyncio
    async def test_import_raises_notebook_not_found(
        self, research_discovery, mock_session
    ):
        """Should raise NotebookNotFoundError for 404."""
        from pynotebooklm import NotebookNotFoundError

        mock_session.call_rpc.side_effect = APIError("Not found", status_code=404)

        sources = [ResearchResult(index=0, url="https://example.com", title="Test")]

        with pytest.raises(NotebookNotFoundError):
            await research_discovery.import_research_sources(
                "missing_nb", "task_id", sources
            )


class TestParseImportResponse:
    """Tests for _parse_import_response helper."""

    def test_parse_empty_response(self, research_discovery):
        """Should handle empty response."""
        result = research_discovery._parse_import_response([])
        assert result == []

    def test_parse_none_response(self, research_discovery):
        """Should handle None response."""
        result = research_discovery._parse_import_response(None)
        assert result == []

    def test_parse_wrapped_response(self, research_discovery):
        """Should unwrap nested response."""
        response = [[[["src_001"], "Title 1"], [["src_002"], "Title 2"]]]
        result = research_discovery._parse_import_response(response)
        assert len(result) == 2
        assert result[0].id == "src_001"
        assert result[1].title == "Title 2"

    def test_parse_skips_invalid_entries(self, research_discovery):
        """Should skip entries without valid source_id."""
        response = [[None, "No ID"], [[None], "Also no ID"], [["valid_id"], "Valid"]]
        result = research_discovery._parse_import_response(response)
        assert len(result) == 1
        assert result[0].id == "valid_id"


class TestGetResultTypeName:
    """Tests for _get_result_type_name helper."""

    def test_web_type(self, research_discovery):
        """Should return 'web' for type 1."""
        assert research_discovery._get_result_type_name(1) == "web"

    def test_google_doc_type(self, research_discovery):
        """Should return 'google_doc' for type 2."""
        assert research_discovery._get_result_type_name(2) == "google_doc"

    def test_google_slides_type(self, research_discovery):
        """Should return 'google_slides' for type 3."""
        assert research_discovery._get_result_type_name(3) == "google_slides"

    def test_deep_report_type(self, research_discovery):
        """Should return 'deep_report' for type 5."""
        assert research_discovery._get_result_type_name(5) == "deep_report"

    def test_google_sheets_type(self, research_discovery):
        """Should return 'google_sheets' for type 8."""
        assert research_discovery._get_result_type_name(8) == "google_sheets"

    def test_unknown_type(self, research_discovery):
        """Should return 'unknown' for unrecognized type."""
        assert research_discovery._get_result_type_name(999) == "unknown"


class TestParsePollResponseEdgeCases:
    """Tests for _parse_poll_response edge cases."""

    @pytest.mark.asyncio
    async def test_poll_with_malformed_response(self, research_discovery, mock_session):
        """Should handle malformed response gracefully."""
        mock_session.call_rpc.return_value = [[[123, "not a list"]]]

        result = await research_discovery.poll_research("nb_123")

        assert result.status == ResearchStatus.NO_RESEARCH

    @pytest.mark.asyncio
    async def test_poll_with_drive_source_type(self, research_discovery, mock_session):
        """Should parse drive source type correctly."""
        mock_session.call_rpc.return_value = [
            [
                [
                    "task_drive",
                    [
                        None,
                        ["Drive search", 2],  # source_type = 2 = drive
                        1,
                        [
                            [
                                [
                                    "https://drive.google.com/doc",
                                    "My Doc",
                                    "Description",
                                    2,
                                ]
                            ],
                            "",
                        ],
                        2,
                    ],
                ],
            ],
        ]

        result = await research_discovery.poll_research("nb_123")

        assert result.source == "drive"
        assert len(result.results) == 1
