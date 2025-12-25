# Track Spec: Video Stitching and Gallery

## Overview
Implement a feature to stitch together multiple generated images/videos from a story into a single MP4 video file. This includes a user-friendly selection process, configurable transitions (including potential AI-driven effects), and a dedicated Video Gallery for playback and management.

## User Stories
- As a creator, I want to easily combine my generated scenes into a cohesive video so I can share my stories.
- As a creator, I want to choose how scenes transition into each other to add a professional and artistic touch.
- As a creator, I want a dedicated space to view, play, and manage my generated videos.

## Functional Requirements
- **Selection Interface:**
    - Integrated with the existing story gallery.
    - "Select All" scenes by default.
    - Ability to unselect/select individual scenes for the final video.
- **Stitching Engine:**
    - Combine selected images/videos into an MP4 file.
    - Implement configurable transitions (e.g., cross-fade, simple cuts).
    - Provide a placeholder for AI-enhanced transitions (e.g., morphing) to leverage local 128GB VRAM.
    - Configurable transition duration.
- **Output Management:**
    - Save videos to `output/<story_name>/videos/`.
    - Generate unique filenames (e.g., `<story_name>_YYYYMMDD_HHMMSS.mp4`).
- **Video Gallery:**
    - A new web page/section to list all generated MP4s.
    - Integrated video player for direct playback.
    - Display metadata: Story name, creation date, and transition settings used.
    - Management actions: Delete video, Download video.

## Non-Functional Requirements
- **Performance:** Stitching should happen in the background or with a clear progress indicator.
- **UI/UX:** Adhere to the "Functional Minimalism" and "Action-Oriented Feedback" principles.
- **Scalability:** Leverage local GPU (128GB VRAM) for computationally intensive transition effects.

## Out of Scope
- Advanced video editing (trimming, audio overlay, text-to-speech) in this initial track.
- Cloud-based video processing.

## Acceptance Criteria
- [ ] User can select a set of scenes from a story.
- [ ] A video is successfully generated and saved in the correct directory.
- [ ] The generated video correctly applies the selected transition type and duration.
- [ ] The new Video Gallery correctly lists all generated videos with their metadata.
- [ ] Videos can be played, downloaded, and deleted from the gallery.
