# Tech Stack - Zoetrope

## Core Backend
- **Python:** The primary programming language for both the Studio application and the ComfyUI engine.
- **FastAPI:** Used to build the high-performance web API and management interface for the Studio.
- **ComfyUI:** The underlying generative engine used for node-based image generation.
- **edge-tts (Python library):** Used for generating high-quality narration audio. Selected for its balance of quality and performance.
- **httpx:** Used for non-blocking asynchronous HTTP requests, primarily for communicating with the ComfyUI API.

## Data Management
- **SQLite:** A lightweight, serverless database used for persistent storage of story data, scene definitions, and system configurations.
- **`sqlite3` (Python stdlib):** The database layer is raw `sqlite3` — hand-written SQL in `studio/database.py`, with schema changes applied as idempotent `ALTER TABLE` statements inside `init_db()`. There is no ORM and no migration framework. (This section previously claimed SQLAlchemy/Alembic provided ORM and migrations; neither was ever imported anywhere in the codebase. `tests-unit/test_docs_match_deps.py` now fails if this file names a library nothing imports.)
- **Story files:** Per-story JSON (`.story` files under `data/stories/`), managed by `scripts/story_manager.py` — the source of truth for scene text, prompts, and per-scene media references.

## Frontend and UI
- **Jinja2 Templates:** Used by FastAPI to render dynamic HTML pages.
- **HTML/CSS/JavaScript:** Standard web technologies for building the user interface.

## Infrastructure and Automation
- **Bash Scripts:** Used for system startup, service management, and batch automation tasks.
- **Virtualenv (comfyui-env):** Ensures a consistent and isolated Python environment for all dependencies.
- **FFmpeg:** Used for high-performance video stitching and processing transitions.
