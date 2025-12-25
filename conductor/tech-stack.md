# Tech Stack - ComfyUI Story Studio

## Core Backend
- **Python:** The primary programming language for both the Studio application and the ComfyUI engine.
- **FastAPI:** Used to build the high-performance web API and management interface for the Studio.
- **ComfyUI:** The underlying generative engine used for node-based image generation.

## Data Management
- **SQLite:** A lightweight, serverless database used for persistent storage of story data, scene definitions, and system configurations.
- **SQLAlchemy/Alembic:** Used for Object-Relational Mapping (ORM) and database migrations, ensuring a structured and maintainable data layer.

## Frontend and UI
- **Jinja2 Templates:** Used by FastAPI to render dynamic HTML pages.
- **HTML/CSS/JavaScript:** Standard web technologies for building the user interface.

## Infrastructure and Automation
- **Bash Scripts:** Used for system startup, service management, and batch automation tasks.
- **Virtualenv (comfyui-env):** Ensures a consistent and isolated Python environment for all dependencies.
