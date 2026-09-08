"""studio/paths.py must agree with the paths the running code actually uses.

paths.py declares PROJECT_ROOT and the directories derived from it. Nothing
imports it at runtime: studio/database.py, scripts/video_utils.py and
studio/app.py each compute the repo root themselves with
`Path(__file__).resolve().parents[N]`, because those modules are loaded through
three different import conventions (a bare sibling import, a package import,
and a sys.path.append inside app.py) and a shared import would be fragile
across all of them.

That is a defensible trade, but it leaves paths.py as a declaration nobody
checks -- free to drift from reality without anything failing, while CLAUDE.md
points newcomers at it as the source of truth. These tests close that gap: the
declaration stays the canonical statement of the layout, and it becomes
load-bearing because the suite fails if code and declaration disagree.
"""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "studio"))

import paths  # noqa: E402  (needs the sys.path line above)


def test_project_root_resolves_to_the_repo():
    assert str(paths.PROJECT_ROOT) == REPO_ROOT, (
        f"paths.PROJECT_ROOT is {paths.PROJECT_ROOT}, but this test resolves the "
        f"repo root as {REPO_ROOT}. paths.py's parents[N] index is wrong."
    )


def test_declared_directories_exist():
    """Every directory paths.py names should be real.

    output/ and logs/ are created on demand rather than tracked, so they may be
    absent on a fresh checkout; the rest are part of the repo.
    """
    optional = {"OUTPUT_DIR", "LOGS_DIR"}
    missing = [
        f"{name}={getattr(paths, name)}"
        for name in ("DATA_DIR", "OUTPUT_DIR", "LOGS_DIR", "WORKFLOWS_DIR", "STORIES_DIR")
        if not os.path.isdir(getattr(paths, name)) and name not in optional
    ]
    assert not missing, f"paths.py names directories that do not exist: {missing}"


def test_output_dir_matches_what_the_app_serves():
    """paths.OUTPUT_DIR must match the OUTPUT_DIR studio/app.py mounts at /images.

    If these drift, media is written to one directory and served from another,
    and the gallery shows broken images with nothing obviously wrong.
    """
    from studio.app import OUTPUT_DIR as app_output_dir

    assert app_output_dir == str(paths.OUTPUT_DIR), (
        f"studio/app.py serves {app_output_dir} but paths.py declares "
        f"{paths.OUTPUT_DIR}. Media would be written and served from different places."
    )


def test_stories_dir_matches_the_story_the_app_loads():
    """paths.STORIES_DIR must contain the story studio/app.py loads by default."""
    from studio.app import STORY_PATH

    assert os.path.dirname(STORY_PATH) == str(paths.STORIES_DIR), (
        f"studio/app.py loads its story from {os.path.dirname(STORY_PATH)} but "
        f"paths.py declares STORIES_DIR as {paths.STORIES_DIR}."
    )
