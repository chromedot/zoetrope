# Specification: Security Vulnerability Remediation

## Overview
This track addresses three specific security vulnerabilities identified in the recent security audit of `studio/app.py`. The goal is to prevent Path Traversal attacks in the audio generation endpoints and the status check endpoint.

## Functional Requirements
1.  **Sanitize SFX Generation Input:**
    -   Modify `generate_sfx` in `studio/app.py`.
    -   Ensure `request.story_name` is sanitized before being used in `os.path.join`.
    -   Prevent directory traversal sequences (e.g., `../`).

2.  **Sanitize TTS Audio Generation Input:**
    -   Modify `generate_audio` in `studio/app.py`.
    -   Ensure `request.story_name` is sanitized before being used in `os.path.join`.
    -   Prevent directory traversal sequences (e.g., `../`).

3.  **Secure Status Check Endpoint:**
    -   Modify `check_status` in `studio/app.py`.
    -   Validate the `prefix` parameter to ensure it resolves to a path within the expected `OUTPUT_DIR`.
    -   Prevent the use of traversal sequences to discover files outside the allowed directory.

## Non-Functional Requirements
-   **Security:** Fixes must robustly handle malicious input without crashing the server (fail securely).
-   **Compatibility:** Valid, normal inputs for `story_name` and `prefix` must continue to work as expected.

## Acceptance Criteria
-   [ ] **Test Case 1 (SFX):** Calling `generate_sfx` with a `story_name` containing `../` does *not* write files outside the `output` directory.
-   [ ] **Test Case 2 (TTS):** Calling `generate_audio` with a `story_name` containing `../` does *not* write files outside the `output` directory.
-   [ ] **Test Case 3 (Status):** Calling `check_status` with a `prefix` containing `../` does *not* reveal information about files outside the `output` directory.
-   [ ] **Regression:** Standard story generation workflows continue to function correctly.

## Out of Scope
-   Broader security audit of the entire codebase.
-   Refactoring of the entire `VideoStitcher` or other components not directly related to these specific input vectors.
