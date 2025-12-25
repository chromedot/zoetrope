# Track Spec: Enhanced Video Transitions

## Overview
Enhance the existing video stitching engine to support advanced transitions between scenes. This track focuses on implementing standard "Cross-Fade" transitions using FFmpeg and establishing the architectural placeholder for future AI-driven "Morphing" transitions (leveraging the local 128GB VRAM).

## User Stories
- As a creator, I want to choose "Cross-Fade" as a transition style to make my videos look smoother and more professional.
- As a developer, I want a clear interface for adding new transition types (like AI Morphing) without rewriting the core stitching logic.

## Functional Requirements
- **Transition System Architecture:**
    - Refactor `VideoStitcher` to use a strategy pattern or extensible handler for different transition types.
- **Cross-Fade Implementation:**
    - Implement FFmpeg logic to overlap and cross-fade between two images/video clips.
    - Support configurable duration (e.g., 1s, 2s).
- **AI Morphing Placeholder:**
    - Create a stub/interface for an "AI Morph" transition.
    - The implementation should currently log a "Not Implemented" warning or fall back to a simple cross-fade, but the code path must be distinct.

## Non-Functional Requirements
- **Performance:** Cross-fades require re-encoding. Ensure the process remains performant and utilizes available CPU/GPU acceleration where possible.
- **Maintainability:** Isolate FFmpeg command complexity from the main application logic.

## Acceptance Criteria
- [ ] User can select "Cross-Fade" in the UI (already exists) and it actually produces a video with overlapping fades.
- [ ] User can select "AI Morph" (new option), which currently triggers a specific log entry or fallback behavior, proving the path works.
- [ ] Code structure allows adding a real AI Morph implementation later by just filling in the handler.
