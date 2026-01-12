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
- [x] **Research Deletion**: Implement `pynotebooklm research delete` (or `del`) to clear/cancel research results.
- [x] **Advanced Source Details**:
    - [x] `pynotebooklm sources describe <id>`: Get AI-generated summary and keywords for a source (RPC `tr032e`).
    - [x] `pynotebooklm sources get-text <id>`: Extract raw indexed text from a source (RPC `hizoJc`).
- [ ] **Drive Synchronization**:
    - [x] `pynotebooklm sources sync <id>`: Sync stale Drive sources (RPC `FLmJqe`).
    - [ ] Implement freshness/stale check in `SourceManager.list_sources` using `yR9Yof`.
- [x] **Notebook AI Description**:
    - [x] `pynotebooklm notebooks describe <id>`: Get detailed AI summary of notebook content (RPC `VfAZjd`).
- [ ] **Notebook Management**:
    - [ ] `pynotebooklm notebooks get <id>`: Get detailed notebook info with sources (RPC `rLM1Ne`).
    - [ ] `pynotebooklm notebooks rename <id> <name>`: Rename a notebook (RPC `s0tc2d`).
    - [ ] Add created/modified timestamps to `notebooks list` and `notebooks get`.
- [ ] **Chat Personalization**:
    - [ ] `pynotebooklm chat configure`: Set chat goal (Learning Guide, Critique, Debate) and response style.
- [ ] **Improved Type Support**: Map all 50+ source type codes discovered in competitor analysis.
- [ ] **Full-Text search**: Implement searching across notebook sources using AI.

## Future / Icebox
- [ ] Note management (Save chat responses as notes).
- [ ] Collaborative features (Share notebooks).
- [ ] Export features (Download all sources as ZIP).
- [ ] GUI / TUI Dashboard for notebook management.
