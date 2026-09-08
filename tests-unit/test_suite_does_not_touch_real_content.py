"""The test suite must not modify real story content.

This exists because it happened. tests-studio/test_audio_api.py posted
story_name "geronimo" to /api/generate_audio, and the endpoint wrote the
payload text into data/stories/geronimo.story through a process-global
StoryManager. Every pytest run silently replaced scene 1's narration with
"Test narration text"; the real line had to be recovered from git history
(ff48ae2: "Geronimo was an Apache medicine man").

It was invisible for months because it looked like a placeholder someone had
left behind rather than damage the tooling was doing, and nothing failed.

This module is a tripwire, not a unit test: it records a checksum of every
real story file at session start and asserts nothing changed by the end. Any
future test that writes to real content fails here instead of quietly eating
words.
"""

import hashlib
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORIES_DIR = os.path.join(REPO_ROOT, "data", "stories")


def _story_checksums():
    """{filename: sha256} for every real story file on disk."""
    if not os.path.isdir(STORIES_DIR):
        return {}
    out = {}
    for name in sorted(os.listdir(STORIES_DIR)):
        if not name.endswith(".story"):
            continue
        path = os.path.join(STORIES_DIR, name)
        with open(path, "rb") as fh:
            out[name] = hashlib.sha256(fh.read()).hexdigest()
    return out


# Captured at MODULE IMPORT, which pytest does during collection -- before any
# test body runs. A session-scoped fixture is not good enough here: fixtures are
# evaluated lazily, on first request, which is inside this very test. By then a
# misbehaving test has already written, the "baseline" records the damaged file,
# and the comparison passes trivially. That exact mistake was made writing this
# module and only surfaced when a deliberate probe failed to trip it.
BASELINE_STORIES = _story_checksums()


def test_real_story_files_are_untouched_by_the_suite():
    """Fails if any test mutated a real .story file during this session.

    Ordering note: pytest collects tests-studio/ before tests-unit/
    alphabetically, so by the time this runs the endpoint tests have already
    executed. That is the point -- this is the check after the fact.
    """
    current = _story_checksums()

    changed = sorted(
        name for name, digest in current.items()
        if name in BASELINE_STORIES and BASELINE_STORIES[name] != digest
    )
    assert not changed, (
        f"The test suite modified real story content: {changed}. A test is "
        "writing to data/stories/ instead of a temporary copy. Patch "
        "studio.app.manager to a StoryManager built on a tmp_path story, the "
        "way tests-studio/test_audio_api.py does."
    )

    removed = sorted(set(BASELINE_STORIES) - set(current))
    assert not removed, f"The test suite deleted real story files: {removed}"
