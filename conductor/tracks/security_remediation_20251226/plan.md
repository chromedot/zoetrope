# Plan: Security and Performance Remediation (Audio/SFX)

## Phase 1: Infrastructure & Dependencies [checkpoint: 6aa63ab]
Goal: Prepare the environment with required libraries and document tech stack changes.

- [x] Task: Install `httpx` in the `comfyui-env` virtual environment. 2aa8eb5
- [x] Task: Update `conductor/tech-stack.md` to include `httpx` as a core dependency. 604515c
- [x] Task: Conductor - User Manual Verification 'Phase 1: Infrastructure & Dependencies' (Protocol in workflow.md) 6aa63ab

## Phase 2: Asynchronous Audio Utilities Refactor [checkpoint: 6950ae4]
Goal: Convert synchronous network calls to non-blocking async calls using `httpx`.

- [x] Task: Write unit tests for `ComfyAudioGenerator` using `pytest-httpx` to mock ComfyUI responses. fea12d0
- [x] Task: Refactor `scripts/audio_utils.py` to replace `urllib` with `httpx.AsyncClient`. fea12d0
- [x] Task: Verify that `ComfyAudioGenerator.generate` is fully non-blocking and handles timeouts/errors gracefully. fea12d0
- [x] Task: Conductor - User Manual Verification 'Phase 2: Asynchronous Audio Utilities Refactor' (Protocol in workflow.md) 6950ae4

## Phase 3: Security Hardening (Path Traversal & Filenames)
Goal: Secure the file system against unauthorized access and prevent filename collisions.

- [x] Task: Write security tests for path traversal in `/api/check_status`, `/api/generate_audio`, and `/api/generate_sfx`. 9b0c42b
- [x] Task: Implement `safe_join` or similar path validation logic in `studio/app.py` to neutralize `../` or absolute path inputs. d048ad7
- [ ] Task: Write tests for unique filename generation.
- [ ] Task: Refactor filename generation in `app.py` and `audio_utils.py` to use `uuid.uuid4()`.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Security Hardening (Path Traversal & Filenames)' (Protocol in workflow.md)

## Phase 4: Dynamic Story Integration
Goal: Remove hardcoded "geronimo" references and allow the Studio to handle multiple stories.

- [ ] Task: Write integration tests for API endpoints with varying story names.
- [ ] Task: Update `/api/generate_audio` and `/api/generate_sfx` in `app.py` to use the `story_name` from the request body.
- [ ] Task: Update `studio/templates/editor.html` to dynamically pass the current story name from the UI to the API.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Dynamic Story Integration' (Protocol in workflow.md)
