# Track Spec: Story Dashboard

## Overview
Implement a centralized dashboard in the Story Studio to provide users with a clear overview of all their stories, their current status, and quick management actions.

## User Stories
- As a creator, I want to see a list of all my stories in one place so I can easily manage my library.
- As a creator, I want to see the generation progress of each story so I know what's ready and what's still processing.
- As a creator, I want to be able to start or stop generations directly from the dashboard for better efficiency.

## Functional Requirements
- **Story List View:** A clean table or grid layout displaying story names, creation dates, and scene counts.
- **Status Indicators:** Visual cues (e.g., progress bars, status labels) showing the percentage of generated scenes for each story.
- **Quick Actions:**
    - "Generate All" button for stories with pending scenes.
    - "Review" button to jump to the story's output gallery.
    - "Delete" button to remove a story and its associated data.
- **Search and Filter:** Ability to filter stories by name or status (e.g., "In Progress", "Completed").

## Non-Functional Requirements
- **Performance:** The dashboard should load quickly even with a large number of stories.
- **UI/UX:** Adhere to the "Functional Minimalism" principle defined in the product guidelines.
- **Mobile Friendly:** Ensure the dashboard is usable on smaller screens.

## Technical Considerations
- Backend: New FastAPI endpoints to aggregate story statistics and generation status.
- Frontend: New HTML template and CSS for the dashboard view, potentially using AJAX for status updates.
- Database: Efficient queries to the `story_studio.db` to fetch story summaries.
