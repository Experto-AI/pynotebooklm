"""
Mind map generation for PyNotebookLM.

This module provides the MindMapGenerator class for creating, saving,
listing, and exporting mind maps from NotebookLM notebooks.

Based on reverse engineering of jacob-bd/notebooklm-mcp (Jan 2026).
"""

import json
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from .exceptions import APIError, NotebookNotFoundError, SourceError

if TYPE_CHECKING:
    from .session import BrowserSession

logger = logging.getLogger(__name__)

# RPC IDs for mind map operations
RPC_GENERATE_MIND_MAP = "yyryJe"
RPC_SAVE_MIND_MAP = "CYK0Xb"
RPC_LIST_MIND_MAPS = "cFji9"


# =============================================================================
# Models
# =============================================================================


class MindMapNode(BaseModel):
    """Represents a node in a mind map tree structure."""

    name: str = Field(..., description="Node label/content")
    children: list["MindMapNode"] = Field(
        default_factory=list, description="Child nodes"
    )

    model_config = {"frozen": False}


class MindMapGenerateResult(BaseModel):
    """Result from generating a mind map (before saving)."""

    mind_map_json: str = Field(..., description="The mind map JSON structure")
    generation_id: str | None = Field(None, description="Generation ID from API")
    source_ids: list[str] = Field(
        default_factory=list, description="Source IDs used for generation"
    )

    model_config = {"frozen": False}


class MindMap(BaseModel):
    """Represents a saved mind map in a notebook."""

    id: str = Field(..., description="Unique mind map identifier")
    notebook_id: str = Field(..., description="Parent notebook ID")
    title: str = Field("Mind Map", description="Mind map title")
    mind_map_json: str | None = Field(None, description="The mind map JSON structure")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    source_ids: list[str] = Field(
        default_factory=list, description="Source IDs used to create this map"
    )

    model_config = {"frozen": False}

    def get_root_node(self) -> MindMapNode | None:
        """Parse the JSON and return the root MindMapNode."""
        if not self.mind_map_json:
            return None
        try:
            data = json.loads(self.mind_map_json)
            return _parse_node(data)
        except (json.JSONDecodeError, KeyError):
            return None


# =============================================================================
# Export Functions
# =============================================================================


def _parse_node(data: dict[str, Any]) -> MindMapNode:
    """Parse a dict into a MindMapNode recursively."""
    children = []
    for child in data.get("children", []):
        children.append(_parse_node(child))
    return MindMapNode(name=data.get("name", ""), children=children)


def export_to_opml(mind_map_json: str, title: str = "Mind Map") -> str:
    """
    Convert mind map JSON to OPML 2.0 format.

    OPML (Outline Processor Markup Language) is widely supported by
    outliner applications and can be imported into tools like OmniOutliner,
    Workflowy, Dynalist, etc.

    Args:
        mind_map_json: The mind map JSON string (hierarchical structure).
        title: Title for the OPML document.

    Returns:
        OPML XML string.

    Raises:
        ValueError: If the JSON is invalid.
    """
    try:
        data = json.loads(mind_map_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid mind map JSON: {e}") from e

    # Create OPML structure
    opml = ET.Element("opml", version="2.0")

    # Head section
    head = ET.SubElement(opml, "head")
    title_elem = ET.SubElement(head, "title")
    title_elem.text = title
    date_elem = ET.SubElement(head, "dateCreated")
    date_elem.text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")

    # Body section
    body = ET.SubElement(opml, "body")

    def add_outline(parent: ET.Element, node: dict[str, Any]) -> None:
        """Recursively add outline elements."""
        outline = ET.SubElement(parent, "outline", text=node.get("name", ""))
        for child in node.get("children", []):
            add_outline(outline, child)

    # Add root node and its children
    add_outline(body, data)

    # Generate XML string with proper declaration
    ET.indent(opml, space="  ")
    xml_str = ET.tostring(opml, encoding="unicode", xml_declaration=True)
    return xml_str


def export_to_freemind(mind_map_json: str, title: str = "Mind Map") -> str:
    """
    Convert mind map JSON to FreeMind (.mm) format.

    FreeMind is a popular open-source mind mapping application.
    This format is also compatible with Freeplane and many other
    mind mapping tools.

    Args:
        mind_map_json: The mind map JSON string (hierarchical structure).
        title: Title for the FreeMind map (used for root node if empty).

    Returns:
        FreeMind XML string.

    Raises:
        ValueError: If the JSON is invalid.
    """
    try:
        data = json.loads(mind_map_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid mind map JSON: {e}") from e

    # Create FreeMind map structure
    map_elem = ET.Element("map", version="1.0.1")

    def add_node(
        parent: ET.Element, node_data: dict[str, Any], position: str = ""
    ) -> None:
        """Recursively add node elements."""
        attribs = {"TEXT": node_data.get("name", "")}
        if position:
            attribs["POSITION"] = position

        node = ET.SubElement(parent, "node", **attribs)

        # Alternate position for first-level children (left/right)
        children = node_data.get("children", [])
        for i, child in enumerate(children):
            # FreeMind convention: alternate left/right for visual balance
            child_position = "right" if i % 2 == 0 else "left"
            add_node(node, child, child_position if parent.tag == "map" else "")

    # Add root node
    add_node(map_elem, data)

    # Generate XML string
    ET.indent(map_elem, space="  ")
    xml_str = ET.tostring(map_elem, encoding="unicode", xml_declaration=True)
    return xml_str


def export_to_json(mind_map_json: str, pretty: bool = True) -> str:
    """
    Export mind map as formatted JSON.

    Args:
        mind_map_json: The mind map JSON string.
        pretty: If True, format with indentation.

    Returns:
        JSON string (formatted if pretty=True).

    Raises:
        ValueError: If the JSON is invalid.
    """
    try:
        data = json.loads(mind_map_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid mind map JSON: {e}") from e

    if pretty:
        return json.dumps(data, indent=2, ensure_ascii=False)
    return json.dumps(data, separators=(",", ":"), ensure_ascii=False)


# =============================================================================
# Mind Map Generator Class
# =============================================================================


class MindMapGenerator:
    """
    Generates and manages mind maps for NotebookLM notebooks.

    This class provides methods for generating mind maps from sources,
    saving them to notebooks, listing existing maps, and exporting
    to various formats.

    Example:
        >>> async with BrowserSession(auth) as session:
        ...     generator = MindMapGenerator(session)
        ...     result = await generator.create(notebook_id, source_ids)
        ...     print(f"Created mind map: {result.id}")

    Attributes:
        session: Active BrowserSession instance.
    """

    def __init__(self, session: "BrowserSession") -> None:
        """
        Initialize the mind map generator.

        Args:
            session: Active BrowserSession instance.
        """
        self.session = session

    async def generate(self, source_ids: list[str]) -> MindMapGenerateResult:
        """
        Generate a mind map JSON structure from sources.

        This is step 1 of the 2-step creation process. After generation,
        use save() to persist the mind map to a notebook.

        Args:
            source_ids: List of source UUIDs to include in the mind map.

        Returns:
            MindMapGenerateResult with the JSON structure and generation ID.

        Raises:
            ValueError: If source_ids is empty.
            SourceError: If generation fails.
        """
        if not source_ids:
            raise ValueError("source_ids cannot be empty")

        # Build source IDs in the nested format: [[[id1]], [[id2]], ...]
        sources_nested = [[[sid]] for sid in source_ids]

        params = [
            sources_nested,
            None,
            None,
            None,
            None,
            ["interactive_mindmap", [["[CONTEXT]", ""]], ""],
            None,
            [2, None, [1]],
        ]

        logger.debug("Generating mind map from %d sources", len(source_ids))

        try:
            result = await self.session.call_rpc(RPC_GENERATE_MIND_MAP, params)
        except APIError as e:
            logger.error("Failed to generate mind map: %s", e)
            raise SourceError(f"Failed to generate mind map: {e}") from e

        # Parse response: [[json_string, null, [gen_ids]]]
        if not result or not isinstance(result, list) or len(result) == 0:
            raise SourceError("Mind map generation returned empty result")

        # Unwrap response - may be doubly nested
        inner = result[0] if isinstance(result[0], list) else result

        mind_map_json = (
            inner[0] if len(inner) > 0 and isinstance(inner[0], str) else None
        )
        if not mind_map_json:
            raise SourceError("Mind map generation did not return JSON structure")

        generation_id = None
        if len(inner) > 2 and isinstance(inner[2], list) and len(inner[2]) > 0:
            generation_id = str(inner[2][0])

        logger.info("Generated mind map (generation_id=%s)", generation_id)

        return MindMapGenerateResult(
            mind_map_json=mind_map_json,
            generation_id=generation_id,
            source_ids=source_ids,
        )

    async def save(
        self,
        notebook_id: str,
        mind_map_json: str,
        source_ids: list[str],
        title: str = "Mind Map",
    ) -> MindMap:
        """
        Save a generated mind map to a notebook.

        This is step 2 of the 2-step creation process. First use
        generate() to create the JSON structure.

        Args:
            notebook_id: The notebook UUID to save to.
            mind_map_json: The JSON string from generate().
            source_ids: List of source UUIDs used to generate the map.
            title: Display title for the mind map.

        Returns:
            MindMap with the saved mind map details.

        Raises:
            ValueError: If notebook_id or mind_map_json is empty.
            NotebookNotFoundError: If the notebook doesn't exist.
            APIError: If saving fails.
        """
        if not notebook_id:
            raise ValueError("notebook_id cannot be empty")
        if not mind_map_json:
            raise ValueError("mind_map_json cannot be empty")

        # Build source IDs in simpler format: [[id1], [id2], ...]
        sources_simple = [[sid] for sid in source_ids]

        # Metadata structure: [2, None, None, 5, sources]
        metadata = [2, None, None, 5, sources_simple]

        params = [
            notebook_id,
            mind_map_json,
            metadata,
            None,
            title,
        ]

        logger.debug("Saving mind map '%s' to notebook %s", title, notebook_id)

        try:
            result = await self.session.call_rpc(RPC_SAVE_MIND_MAP, params)
        except APIError as e:
            if e.status_code == 404:
                raise NotebookNotFoundError(f"Notebook not found: {notebook_id}") from e
            logger.error("Failed to save mind map: %s", e)
            raise

        # Parse response: [[mind_map_id, json, metadata, None, title]]
        if not result or not isinstance(result, list) or len(result) == 0:
            raise APIError("Mind map save returned empty result")

        inner = result[0] if isinstance(result[0], list) else result

        mind_map_id = inner[0] if len(inner) > 0 else None
        saved_json = inner[1] if len(inner) > 1 else mind_map_json
        saved_title = inner[4] if len(inner) > 4 else title

        if not mind_map_id:
            raise APIError("Mind map save did not return an ID")

        logger.info("Saved mind map '%s' (id=%s)", saved_title, mind_map_id)

        return MindMap(
            id=mind_map_id,
            notebook_id=notebook_id,
            title=saved_title,
            mind_map_json=saved_json,
            source_ids=source_ids,
            created_at=datetime.now(),
        )

    async def create(
        self,
        notebook_id: str,
        source_ids: list[str] | None = None,
        title: str = "Mind Map",
    ) -> MindMap:
        """
        Create a mind map from sources and save it to a notebook.

        This is a convenience method that combines generate() and save().
        If source_ids is not provided, it will use all sources from the notebook.

        Args:
            notebook_id: The notebook UUID.
            source_ids: Optional list of source UUIDs. If None, uses all sources.
            title: Display title for the mind map.

        Returns:
            MindMap with the created mind map details.

        Raises:
            ValueError: If notebook_id is empty or no sources available.
            NotebookNotFoundError: If the notebook doesn't exist.
            SourceError: If generation fails.
            APIError: If saving fails.
        """
        if not notebook_id:
            raise ValueError("notebook_id cannot be empty")

        # If no source_ids provided, get all sources from the notebook
        if source_ids is None:
            from .notebooks import NotebookManager

            notebook_manager = NotebookManager(self.session)
            notebook = await notebook_manager.get(notebook_id)
            source_ids = [s.id for s in notebook.sources]

        if not source_ids:
            raise ValueError(
                "Cannot create mind map: notebook has no sources. "
                "Add sources first, then create a mind map."
            )

        logger.info(
            "Creating mind map '%s' from %d sources in notebook %s",
            title,
            len(source_ids),
            notebook_id,
        )

        # Step 1: Generate
        gen_result = await self.generate(source_ids)

        # Step 2: Save
        return await self.save(
            notebook_id=notebook_id,
            mind_map_json=gen_result.mind_map_json,
            source_ids=source_ids,
            title=title,
        )

    async def list(self, notebook_id: str) -> list[MindMap]:
        """
        List all mind maps in a notebook.

        Args:
            notebook_id: The notebook UUID.

        Returns:
            List of MindMap objects.

        Raises:
            ValueError: If notebook_id is empty.
            NotebookNotFoundError: If the notebook doesn't exist.
            APIError: If the API call fails.
        """
        if not notebook_id:
            raise ValueError("notebook_id cannot be empty")

        params = [notebook_id]

        logger.debug("Listing mind maps for notebook %s", notebook_id)

        try:
            result = await self.session.call_rpc(RPC_LIST_MIND_MAPS, params)
        except APIError as e:
            if e.status_code == 404:
                raise NotebookNotFoundError(f"Notebook not found: {notebook_id}") from e
            raise

        mind_maps: list[MindMap] = []

        if not result or not isinstance(result, list) or len(result) == 0:
            return mind_maps

        # Response: [[[mind_map_id, [id, json, metadata, None, title]], ...], [timestamp]]
        mind_map_list = result[0] if isinstance(result[0], list) else []

        for item in mind_map_list:
            if not isinstance(item, list) or len(item) < 2:
                continue

            mind_map_id = item[0]
            details = item[1] if len(item) > 1 else []

            if not isinstance(details, list) or len(details) < 5:
                continue

            # Details: [id, json, metadata, None, title]
            mind_map_json = details[1] if len(details) > 1 else None
            title = details[4] if len(details) > 4 else "Mind Map"
            metadata = details[2] if len(details) > 2 else []

            # Extract timestamp from metadata [2, version_id, [timestamp, nanos], ...]
            created_at = None
            if isinstance(metadata, list) and len(metadata) > 2:
                ts = metadata[2]
                created_at = self._parse_timestamp(ts)

            # Extract source IDs from metadata
            source_ids = []
            if isinstance(metadata, list) and len(metadata) > 4:
                sources = metadata[4]
                if isinstance(sources, list):
                    for s in sources:
                        if isinstance(s, list) and len(s) > 0:
                            source_ids.append(s[0])

            mind_maps.append(
                MindMap(
                    id=mind_map_id,
                    notebook_id=notebook_id,
                    title=title,
                    mind_map_json=mind_map_json,
                    created_at=created_at,
                    source_ids=source_ids,
                )
            )

        logger.debug("Found %d mind maps", len(mind_maps))
        return mind_maps

    async def get(self, notebook_id: str, mindmap_id: str) -> MindMap | None:
        """
        Get a specific mind map by ID.

        Args:
            notebook_id: The notebook UUID.
            mindmap_id: The mind map UUID.

        Returns:
            MindMap if found, None otherwise.

        Raises:
            ValueError: If notebook_id or mindmap_id is empty.
            NotebookNotFoundError: If the notebook doesn't exist.
            APIError: If the API call fails.
        """
        if not notebook_id:
            raise ValueError("notebook_id cannot be empty")
        if not mindmap_id:
            raise ValueError("mindmap_id cannot be empty")

        mind_maps = await self.list(notebook_id)
        for mm in mind_maps:
            if mm.id == mindmap_id:
                return mm
        return None

    def _parse_timestamp(self, ts_data: Any) -> datetime | None:
        """Parse timestamp from API response."""
        try:
            if isinstance(ts_data, list) and len(ts_data) >= 1:
                # Format: [seconds, nanos] or just seconds
                seconds = ts_data[0]
                if isinstance(seconds, int | float):
                    return datetime.fromtimestamp(seconds)
            elif isinstance(ts_data, int | float):
                # Could be seconds or milliseconds
                if ts_data > 1e11:  # milliseconds
                    return datetime.fromtimestamp(ts_data / 1000)
                return datetime.fromtimestamp(ts_data)
        except (ValueError, OSError, OverflowError):
            pass
        return None
