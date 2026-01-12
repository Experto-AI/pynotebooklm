# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Persistent browser sessions with context pooling.
- Auto-refresh support for expired authentication cookies.
- Streaming response parsing improvements and request/response debug logging.
- Batch helpers for notebook deletion and URL source ingestion.
- Research polling with exponential backoff.
- Reliability integration tests and telemetry logging hooks.
- **Research Deletion**: Added `pynotebooklm research delete` (and `del`) commands.
- **Advanced Source Details**: Added `sources describe` and `sources get-text` commands.
- **Notebook AI Description**: Added `notebooks describe` for automated summaries.

### Changed
- Added package metadata URLs and documentation link.

## [0.19.0] - 2026-01-12

### Added
- Research discovery and import workflows (automated source joining).
- Multi-modal content generation (audio, video, slides, infographics).
- Study tools (flashcards, quizzes, data tables).
- Mind map generation, export (JSON, OPML, FreeMind), and management.
- Chat session management with tone/style configuration.
- Notebook and source management (create, list, delete).
- Unified `NotebookLMClient` for programmatic access.
- Low-level RPC wrapper for internal Google APIs.
- Production-ready CLI with rich output and spinners.
- Docker and Docker-compose support.

### Changed
- Refactored CLI to use unified client.
- Improved error handling for streaming responses.

## [0.1.0] - 2026-01-08

### Added
- Initial project setup with Poetry and Playwright.
- Basic authentication and browser session management.
- Basic notebook and source listing.

