# Specification: Security and Performance Remediation (Audio/SFX)

## Overview
This track addresses several critical and high-severity issues identified during the code review of the Audio and SFX integration. The primary goals are to eliminate blocking I/O that hampers server performance, close security vulnerabilities related to path traversal and filename predictability, and remove hardcoded story names that limit the application's functionality.

## Functional Requirements
- **Asynchronous ComfyUI Interaction:**
    - Replace all synchronous `urllib` calls in `scripts/audio_utils.py` with `httpx`.
    - Ensure `ComfyAudioGenerator` methods (`generate`, `_queue_prompt`, `_wait_for_history`) are fully non-blocking.
- **Secure File Handling:**
    - Implement robust path traversal protection in all API endpoints that accept folder or story names (e.g., `/api/check_status`, `/api/generate_audio`, `/api/generate_sfx`).
    - Replace `time.time()` based filename generation with UUID-based filenames to prevent collisions and predictability.
- **Dynamic Story Handling:**
    - Update the `editor.html` UI to dynamically pass the current story name to the backend.
    - Update the FastAPI endpoints (`/api/generate_audio`, `/api/generate_sfx`) to handle dynamic story names instead of the hardcoded "geronimo".

## Non-Functional Requirements
- **Performance:** The FastAPI event loop must remain responsive during audio generation/polling.
- **Reliability:** Filename generation must be collision-proof under concurrent load.
- **Security:** No file system access outside of the defined `OUTPUT_DIR`.

## Acceptance Criteria
- [ ] `scripts/audio_utils.py` uses `httpx` for all network requests.
- [ ] Multiple concurrent requests to `/api/generate_sfx` do not block other Studio API calls.
- [ ] Attempts to use `../` or absolute paths in story/folder parameters are rejected or safely neutralized.
- [ ] Generated audio filenames are unique (e.g., `sfx_[uuid].flac`).
- [ ] The "Generate Audio" and "Generate SFX" buttons work correctly for any loaded story, not just "geronimo".
- [ ] All unit tests pass, including new tests for security and async behavior.

## Out of Scope
- Refactoring the entire `VideoStitcher` to use `httpx` (unless it also uses `urllib` and is touched by these changes).
- Changing the underlying AudioLDM workflow logic.
