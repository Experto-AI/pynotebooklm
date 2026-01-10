# PyNotebookLM

Production-grade Python library for **Google NotebookLM** automation.

PyNotebookLM allows you to programmatically interact with Google NotebookLM, providing access to over 30 internal tools including notebook management, source handling, research discovery, and multi-modal content generation.

## Key Features

- 🔐 **Secure Authentication** - Browser-based Google login with cookie persistence
- 📓 **Notebook Management** - Create, list, rename, and delete notebooks
- 📰 **Source Management** - Add URLs, YouTube videos, Google Drive docs, and text
- 🔍 **Research & Analysis** - Query notebooks and discover related sources
- 🧠 **Mind Maps** - Generate, save, list, and export mind maps (JSON/OPML/FreeMind)
- 🎙️ **Content Generation** - Create audio overviews (podcasts), videos, infographics, and slides
- 📚 **Study Tools** - Create flashcards, quizzes, and briefing documents

## How It Works

PyNotebookLM uses browser automation (Playwright) to interact with NotebookLM's internal APIs. It handles the complexity of authentication, session management, and the internal RPC protocol, giving you a clean Pythonic interface.

!!! note
    This is an unofficial library. It uses NotebookLM's internal APIs which may change without notice.

## Getting Started

Check out the [Quickstart](quickstart.md) guide to get up and running in minutes.
