# Track Plan: Enhanced Video Transitions

This plan outlines the steps to implement advanced video transitions.

## Phase 1: Architecture and Cross-Fade [checkpoint: 059e0de]
Goal: Refactor the stitching engine to support complex transitions and implement Cross-Fading.

- [x] Task: Write Tests for `VideoStitcher` verifying different transition strategies (mocked)
- [x] Task: Refactor `VideoStitcher` to use a Transition Strategy pattern
- [x] Task: Implement `CrossFadeStrategy` using complex FFmpeg filters (xfade)
- [x] Task: Conductor - User Manual Verification 'Phase 1: Architecture and Cross-Fade' (Protocol in workflow.md)

## Phase 2: UI Updates and AI Placeholder [checkpoint: 1dba472]
Goal: Update the UI to expose new options and create the placeholder for AI Morphing.

- [x] Task: Update VideoStitcher with AIMorphStrategy placeholder (stub)
- [x] Task: Update Gallery UI to include "AI Morph" in the transition dropdown
- [x] Task: Write Tests ensuring "AI Morph" selection routes to the correct strategy
- [x] Task: Conductor - User Manual Verification 'Phase 2: UI Updates and AI Placeholder' (Protocol in workflow.md)
