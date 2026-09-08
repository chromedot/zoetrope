"""Central place for filesystem paths used across the studio app and scripts.

Previously these paths were hardcoded to /data/comfy throughout the codebase,
which made the project impossible to run from any other location. Import
PROJECT_ROOT (and the derived paths below) instead of hardcoding a location.
"""

from pathlib import Path

# Repo root: studio/paths.py -> studio/ -> <repo root>
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
LOGS_DIR = PROJECT_ROOT / "logs"
WORKFLOWS_DIR = PROJECT_ROOT / "data" / "workflows"
STORIES_DIR = PROJECT_ROOT / "data" / "stories"

DB_PATH = DATA_DIR / "story_studio.db"
