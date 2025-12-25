# Track Plan: Video Stitching and Gallery

This plan outlines the steps to implement the video stitching feature and the dedicated video gallery.

## Phase 1: Video Stitching Engine (Backend) [checkpoint: 9660559]
Goal: Implement the core logic for combining images/videos into an MP4 file with transitions.

- [x] Task: Write Tests for video stitching utility (verifying file discovery and transition command generation) 8a96f31
- [x] Task: Implement video stitching logic using ffmpeg (cross-fade and simple cuts) 2e0ec6b
- [x] Task: Implement background task handling for video generation 26e7048
- [x] Task: Conductor - User Manual Verification 'Phase 1: Video Stitching Engine' (Protocol in workflow.md) 9660559

## Phase 2: Selection UI and Generation API
Goal: Enable users to select scenes and trigger the video generation process.

- [x] Task: Write Tests for video generation API endpoint 3dd3457
- [ ] Task: Implement selection UI in the existing Gallery (checkboxes, "Select All" toggle)
- [ ] Task: Implement the POST /api/generate_video endpoint to trigger stitching
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Selection UI and Generation API' (Protocol in workflow.md)

## Phase 3: Video Gallery and Management
Goal: Create a dedicated space to view and manage generated MP4 files.

- [ ] Task: Write Tests for Video Gallery data retrieval and UI structure
- [ ] Task: Implement backend logic to discover and serve generated videos
- [ ] Task: Implement the Video Gallery page (HTML/CSS) with playback and download/delete actions
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Video Gallery and Management' (Protocol in workflow.md)
