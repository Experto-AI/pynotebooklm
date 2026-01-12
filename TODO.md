# pynotebooklm TODO

## Phase 10: Stabilization & Performance (Current)
- [x] Implement persistent browser context pooling for faster startup.
- [x] Add automatic cookie refresh logic to `BrowserSession`.
- [x] Improve streaming response parsing with specific end-of-stream detection.
- [x] Add request/response logging hooks for `PYNOTEBOOKLM_DEBUG`.
- [x] Implement batch notebook deletion and batch URL source operations.
- [x] Add exponential backoff to research polling.
- [x] Create comprehensive integration tests for reliability edge cases.
- [x] Implement `cleanup_old_artifacts.py` automation script.
- [ ] Verify all code examples in `examples/` run successfully.
- [ ] Audit all documentation for accuracy after Refactor.

## Phase 11: Competitor Parity & Research Enhancements

### Completed Features
- [x] **Research Deletion**: `pynotebooklm research delete` to clear/cancel research results.
- [x] **Advanced Source Details**:
    - [x] `pynotebooklm sources describe <id>`: AI-generated summary and keywords (RPC `tr032e`).
    - [x] `pynotebooklm sources get-text <id>`: Extract raw indexed text (RPC `hizoJc`).
- [x] **Drive Source Sync**: `pynotebooklm sources sync <id>` (RPC `FLmJqe`).
- [x] **Notebook AI Description**: `pynotebooklm notebooks describe <id>` (RPC `VfAZjd`).
- [x] **Chat Personalization**: `pynotebooklm query configure` - Set goal (default/learning/custom) and response length.
- [x] **Drive Source Freshness Check** (RPC `yR9Yof`):
    - [x] Added `check_source_freshness(source_id: str) -> bool | None` to `NotebookLMAPI`.
    - [x] Updated `Source` model to include `is_fresh: bool | None` field.
- [x] **Notebook Management CLI Commands**:
    - [x] `pynotebooklm notebooks get <id>`: Show detailed notebook info with sources.
    - [x] `pynotebooklm notebooks rename <id> <name>`: Rename a notebook with confirmation.
    - [x] Detailed view (`-d`) shows created/modified timestamps.
- [x] **Improved Source Type Mapping**:
    - [x] Expanded `SOURCE_TYPE_MAP` in `api.py` with codes 1-9.
    - [x] Added `source_type_code: int` to `Source` model.
    - [x] `notebooks get` shows human-readable source types.

### Remaining Tasks

#### 1. SourceManager Integration
- [ ] Update `SourceManager.list_sources` to call freshness check for Drive sources.
- [ ] Update `sources list` CLI to show freshness status (✓/✗).

#### 2. Full-Text Search (Deferred - Low Priority)
- [ ] Research feasibility of searching across sources using the query RPC.
- [ ] Consider implementing via `query` command with special search prompt.

## Future / Icebox
- [ ] Note management (Save chat responses as notes).
- [ ] Export features (Download all sources as ZIP).

