"""
Integration tests for MindMapGenerator.

These tests verify mind map generation, saving, listing, and export
functionality using mocked API responses.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from pynotebooklm import (
    APIError,
    AuthManager,
    BrowserSession,
    MindMap,
    MindMapGenerateResult,
    MindMapGenerator,
    MindMapNode,
    NotebookNotFoundError,
    SourceError,
    export_to_freemind,
    export_to_json,
    export_to_opml,
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
def mindmap_generator(mock_session):
    """Create a MindMapGenerator with mocked session."""
    return MindMapGenerator(mock_session)


# =============================================================================
# Mock Mind Map Responses
# =============================================================================

SAMPLE_MIND_MAP_JSON = json.dumps(
    {
        "name": "Artificial Intelligence",
        "children": [
            {
                "name": "Machine Learning",
                "children": [
                    {"name": "Supervised Learning"},
                    {"name": "Unsupervised Learning"},
                    {"name": "Reinforcement Learning"},
                ],
            },
            {
                "name": "Deep Learning",
                "children": [
                    {"name": "Neural Networks"},
                    {"name": "CNNs"},
                    {"name": "RNNs"},
                ],
            },
        ],
    }
)

MOCK_GENERATE_RESPONSE = [
    [
        SAMPLE_MIND_MAP_JSON,
        None,
        ["gen_id_123", "gen_id_456", 1],
    ]
]

MOCK_SAVE_RESPONSE = [
    [
        "mindmap_uuid_001",
        SAMPLE_MIND_MAP_JSON,
        [2, "version_001", [1704067200, 0], 5, [["src_001"], ["src_002"]]],
        None,
        "AI Mind Map",
    ]
]

MOCK_LIST_RESPONSE = [
    [
        [
            "mindmap_uuid_001",
            [
                "mindmap_uuid_001",
                SAMPLE_MIND_MAP_JSON,
                [2, "version_001", [1704067200, 0], 5, [["src_001"], ["src_002"]]],
                None,
                "AI Mind Map",
            ],
        ],
        [
            "mindmap_uuid_002",
            [
                "mindmap_uuid_002",
                SAMPLE_MIND_MAP_JSON,
                [2, "version_002", [1704153600, 0], 5, [["src_003"]]],
                None,
                "Second Mind Map",
            ],
        ],
    ],
    [1704153600, 0],
]


# =============================================================================
# Generate Tests
# =============================================================================


class TestGenerate:
    """Tests for MindMapGenerator.generate()"""

    @pytest.mark.asyncio
    async def test_generate_returns_result(self, mindmap_generator, mock_session):
        """Should return MindMapGenerateResult with JSON."""
        mock_session.call_rpc.return_value = MOCK_GENERATE_RESPONSE

        result = await mindmap_generator.generate(["src_001", "src_002"])

        assert isinstance(result, MindMapGenerateResult)
        assert result.mind_map_json == SAMPLE_MIND_MAP_JSON
        assert result.generation_id == "gen_id_123"
        assert result.source_ids == ["src_001", "src_002"]

    @pytest.mark.asyncio
    async def test_generate_calls_correct_rpc(self, mindmap_generator, mock_session):
        """Should call the yyryJe RPC with correct structure."""
        mock_session.call_rpc.return_value = MOCK_GENERATE_RESPONSE

        await mindmap_generator.generate(["src_001"])

        mock_session.call_rpc.assert_called_once()
        call_args = mock_session.call_rpc.call_args
        assert call_args[0][0] == "yyryJe"  # RPC ID

        params = call_args[0][1]
        assert params[0] == [[["src_001"]]]  # Nested source IDs
        assert params[5] == ["interactive_mindmap", [["[CONTEXT]", ""]], ""]

    @pytest.mark.asyncio
    async def test_generate_rejects_empty_sources(self, mindmap_generator):
        """Should reject empty source_ids."""
        with pytest.raises(ValueError, match="source_ids cannot be empty"):
            await mindmap_generator.generate([])

    @pytest.mark.asyncio
    async def test_generate_handles_api_error(self, mindmap_generator, mock_session):
        """Should wrap API errors in SourceError."""
        mock_session.call_rpc.side_effect = APIError("Network error")

        with pytest.raises(SourceError, match="Failed to generate mind map"):
            await mindmap_generator.generate(["src_001"])

    @pytest.mark.asyncio
    async def test_generate_handles_empty_response(
        self, mindmap_generator, mock_session
    ):
        """Should raise SourceError for empty response."""
        mock_session.call_rpc.return_value = []

        with pytest.raises(SourceError, match="empty result"):
            await mindmap_generator.generate(["src_001"])


# =============================================================================
# Save Tests
# =============================================================================


class TestSave:
    """Tests for MindMapGenerator.save()"""

    @pytest.mark.asyncio
    async def test_save_returns_mindmap(self, mindmap_generator, mock_session):
        """Should return MindMap with saved details."""
        mock_session.call_rpc.return_value = MOCK_SAVE_RESPONSE

        result = await mindmap_generator.save(
            notebook_id="nb_123",
            mind_map_json=SAMPLE_MIND_MAP_JSON,
            source_ids=["src_001", "src_002"],
            title="AI Mind Map",
        )

        assert isinstance(result, MindMap)
        assert result.id == "mindmap_uuid_001"
        assert result.notebook_id == "nb_123"
        assert result.title == "AI Mind Map"
        assert result.mind_map_json == SAMPLE_MIND_MAP_JSON

    @pytest.mark.asyncio
    async def test_save_calls_correct_rpc(self, mindmap_generator, mock_session):
        """Should call the CYK0Xb RPC with correct structure."""
        mock_session.call_rpc.return_value = MOCK_SAVE_RESPONSE

        await mindmap_generator.save(
            "nb_123", SAMPLE_MIND_MAP_JSON, ["src_001"], "Test"
        )

        mock_session.call_rpc.assert_called_once()
        call_args = mock_session.call_rpc.call_args
        assert call_args[0][0] == "CYK0Xb"  # RPC ID

        params = call_args[0][1]
        assert params[0] == "nb_123"
        assert params[1] == SAMPLE_MIND_MAP_JSON
        assert params[2] == [2, None, None, 5, [["src_001"]]]
        assert params[4] == "Test"

    @pytest.mark.asyncio
    async def test_save_rejects_empty_notebook_id(self, mindmap_generator):
        """Should reject empty notebook_id."""
        with pytest.raises(ValueError, match="notebook_id cannot be empty"):
            await mindmap_generator.save("", SAMPLE_MIND_MAP_JSON, ["src"], "Title")

    @pytest.mark.asyncio
    async def test_save_rejects_empty_json(self, mindmap_generator):
        """Should reject empty mind_map_json."""
        with pytest.raises(ValueError, match="mind_map_json cannot be empty"):
            await mindmap_generator.save("nb_123", "", ["src"], "Title")

    @pytest.mark.asyncio
    async def test_save_raises_notebook_not_found(
        self, mindmap_generator, mock_session
    ):
        """Should raise NotebookNotFoundError for 404."""
        mock_session.call_rpc.side_effect = APIError("Not found", status_code=404)

        with pytest.raises(NotebookNotFoundError):
            await mindmap_generator.save(
                "missing_nb", SAMPLE_MIND_MAP_JSON, ["src"], "Title"
            )


# =============================================================================
# Create Tests
# =============================================================================


class TestCreate:
    """Tests for MindMapGenerator.create()"""

    @pytest.mark.asyncio
    async def test_create_combines_generate_and_save(
        self, mindmap_generator, mock_session
    ):
        """Should call generate then save."""
        mock_session.call_rpc.side_effect = [
            MOCK_GENERATE_RESPONSE,
            MOCK_SAVE_RESPONSE,
        ]

        result = await mindmap_generator.create(
            notebook_id="nb_123",
            source_ids=["src_001", "src_002"],
            title="AI Mind Map",
        )

        assert isinstance(result, MindMap)
        assert result.id == "mindmap_uuid_001"
        assert mock_session.call_rpc.call_count == 2

    @pytest.mark.asyncio
    async def test_create_rejects_empty_notebook_id(self, mindmap_generator):
        """Should reject empty notebook_id."""
        with pytest.raises(ValueError, match="notebook_id cannot be empty"):
            await mindmap_generator.create("", ["src_001"])

    @pytest.mark.asyncio
    async def test_create_rejects_empty_sources(self, mindmap_generator):
        """Should reject empty source list."""
        with pytest.raises(ValueError, match="no sources"):
            await mindmap_generator.create("nb_123", source_ids=[])


# =============================================================================
# List Tests
# =============================================================================


class TestList:
    """Tests for MindMapGenerator.list()"""

    @pytest.mark.asyncio
    async def test_list_returns_mindmaps(self, mindmap_generator, mock_session):
        """Should return list of MindMap objects."""
        mock_session.call_rpc.return_value = MOCK_LIST_RESPONSE

        result = await mindmap_generator.list("nb_123")

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(mm, MindMap) for mm in result)

    @pytest.mark.asyncio
    async def test_list_parses_details(self, mindmap_generator, mock_session):
        """Should parse mind map details correctly."""
        mock_session.call_rpc.return_value = MOCK_LIST_RESPONSE

        result = await mindmap_generator.list("nb_123")

        first = result[0]
        assert first.id == "mindmap_uuid_001"
        assert first.title == "AI Mind Map"
        assert first.mind_map_json == SAMPLE_MIND_MAP_JSON
        assert first.source_ids == ["src_001", "src_002"]

    @pytest.mark.asyncio
    async def test_list_calls_correct_rpc(self, mindmap_generator, mock_session):
        """Should call the cFji9 RPC."""
        mock_session.call_rpc.return_value = MOCK_LIST_RESPONSE

        await mindmap_generator.list("nb_123")

        mock_session.call_rpc.assert_called_once()
        call_args = mock_session.call_rpc.call_args
        assert call_args[0][0] == "cFji9"  # RPC ID
        assert call_args[0][1] == ["nb_123"]

    @pytest.mark.asyncio
    async def test_list_handles_empty_response(self, mindmap_generator, mock_session):
        """Should return empty list for no mind maps."""
        mock_session.call_rpc.return_value = []

        result = await mindmap_generator.list("nb_123")

        assert result == []

    @pytest.mark.asyncio
    async def test_list_rejects_empty_notebook_id(self, mindmap_generator):
        """Should reject empty notebook_id."""
        with pytest.raises(ValueError, match="notebook_id cannot be empty"):
            await mindmap_generator.list("")


# =============================================================================
# Get Tests
# =============================================================================


class TestGet:
    """Tests for MindMapGenerator.get()"""

    @pytest.mark.asyncio
    async def test_get_returns_mindmap(self, mindmap_generator, mock_session):
        """Should return specific MindMap if found."""
        mock_session.call_rpc.return_value = MOCK_LIST_RESPONSE

        result = await mindmap_generator.get("nb_123", "mindmap_uuid_001")

        assert isinstance(result, MindMap)
        assert result.id == "mindmap_uuid_001"

    @pytest.mark.asyncio
    async def test_get_returns_none_if_not_found(self, mindmap_generator, mock_session):
        """Should return None if mind map not found."""
        mock_session.call_rpc.return_value = MOCK_LIST_RESPONSE

        result = await mindmap_generator.get("nb_123", "nonexistent_id")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_rejects_empty_ids(self, mindmap_generator):
        """Should reject empty IDs."""
        with pytest.raises(ValueError, match="notebook_id cannot be empty"):
            await mindmap_generator.get("", "mindmap_id")

        with pytest.raises(ValueError, match="mindmap_id cannot be empty"):
            await mindmap_generator.get("nb_123", "")


# =============================================================================
# Export Function Tests
# =============================================================================


class TestExportToJson:
    """Tests for export_to_json()"""

    def test_export_json_pretty(self):
        """Should export formatted JSON."""
        result = export_to_json(SAMPLE_MIND_MAP_JSON, pretty=True)

        assert "Artificial Intelligence" in result
        assert "\n" in result  # Pretty printed
        parsed = json.loads(result)
        assert parsed["name"] == "Artificial Intelligence"

    def test_export_json_compact(self):
        """Should export compact JSON."""
        result = export_to_json(SAMPLE_MIND_MAP_JSON, pretty=False)

        assert "Artificial Intelligence" in result
        assert "  " not in result  # Not pretty printed

    def test_export_json_invalid_input(self):
        """Should raise ValueError for invalid JSON."""
        with pytest.raises(ValueError, match="Invalid mind map JSON"):
            export_to_json("not valid json")


class TestExportToOpml:
    """Tests for export_to_opml()"""

    def test_export_opml_structure(self):
        """Should create valid OPML structure."""
        result = export_to_opml(SAMPLE_MIND_MAP_JSON, title="Test Map")

        assert "<?xml version" in result
        assert '<opml version="2.0">' in result
        assert "<head>" in result
        assert "<body>" in result
        assert "<outline" in result

    def test_export_opml_includes_title(self):
        """Should include title in head."""
        result = export_to_opml(SAMPLE_MIND_MAP_JSON, title="My Mind Map")

        assert "<title>My Mind Map</title>" in result

    def test_export_opml_includes_content(self):
        """Should include mind map content."""
        result = export_to_opml(SAMPLE_MIND_MAP_JSON)

        assert 'text="Artificial Intelligence"' in result
        assert 'text="Machine Learning"' in result
        assert 'text="Deep Learning"' in result

    def test_export_opml_invalid_input(self):
        """Should raise ValueError for invalid JSON."""
        with pytest.raises(ValueError, match="Invalid mind map JSON"):
            export_to_opml("not valid json")


class TestExportToFreemind:
    """Tests for export_to_freemind()"""

    def test_export_freemind_structure(self):
        """Should create valid FreeMind structure."""
        result = export_to_freemind(SAMPLE_MIND_MAP_JSON)

        assert "<?xml version" in result
        assert '<map version="1.0.1">' in result
        assert "<node" in result

    def test_export_freemind_includes_content(self):
        """Should include mind map content."""
        result = export_to_freemind(SAMPLE_MIND_MAP_JSON)

        assert 'TEXT="Artificial Intelligence"' in result
        assert 'TEXT="Machine Learning"' in result
        assert 'TEXT="Neural Networks"' in result

    def test_export_freemind_invalid_input(self):
        """Should raise ValueError for invalid JSON."""
        with pytest.raises(ValueError, match="Invalid mind map JSON"):
            export_to_freemind("not valid json")


# =============================================================================
# Model Tests
# =============================================================================


class TestMindMapNode:
    """Tests for MindMapNode model."""

    def test_creates_with_name(self):
        """Should create node with name."""
        node = MindMapNode(name="Test Node")

        assert node.name == "Test Node"
        assert node.children == []

    def test_creates_with_children(self):
        """Should create node with children."""
        child = MindMapNode(name="Child")
        parent = MindMapNode(name="Parent", children=[child])

        assert len(parent.children) == 1
        assert parent.children[0].name == "Child"


class TestMindMapGenerateResult:
    """Tests for MindMapGenerateResult model."""

    def test_creates_with_json(self):
        """Should create result with JSON."""
        result = MindMapGenerateResult(
            mind_map_json='{"name": "Test"}',
            generation_id="gen_123",
            source_ids=["src_001"],
        )

        assert result.mind_map_json == '{"name": "Test"}'
        assert result.generation_id == "gen_123"
        assert result.source_ids == ["src_001"]


class TestMindMap:
    """Tests for MindMap model."""

    def test_creates_with_required_fields(self):
        """Should create with required fields."""
        mm = MindMap(id="mm_001", notebook_id="nb_123")

        assert mm.id == "mm_001"
        assert mm.notebook_id == "nb_123"
        assert mm.title == "Mind Map"

    def test_get_root_node_parses_json(self):
        """Should parse JSON into MindMapNode."""
        mm = MindMap(
            id="mm_001",
            notebook_id="nb_123",
            mind_map_json=SAMPLE_MIND_MAP_JSON,
        )

        root = mm.get_root_node()

        assert root is not None
        assert root.name == "Artificial Intelligence"
        assert len(root.children) == 2

    def test_get_root_node_returns_none_for_no_json(self):
        """Should return None if no JSON."""
        mm = MindMap(id="mm_001", notebook_id="nb_123", mind_map_json=None)

        assert mm.get_root_node() is None

    def test_get_root_node_handles_invalid_json(self):
        """Should return None for invalid JSON."""
        mm = MindMap(id="mm_001", notebook_id="nb_123", mind_map_json="not json")

        assert mm.get_root_node() is None
