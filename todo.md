# Project Roadmap

## Phase 1: MVP Setup (Foundation)
- [x] **Get MVP of ComfyUI and Studio running.**
    - *Status:* Completed. Backend (Port 8188) and Frontend (Port 8000) are running locally. Database and Logs are unified.

## Phase 2: Content Refinement & Pipeline Stability
- [ ] **Determine how to select the 10 best images.**
    - *Goal:* Establish a workflow (manual or automated) to curate the output folder.
    - *Idea:* Maybe add a "Star/Favorite" feature in the Studio Gallery?
- [ ] **Test if regenerating keeps file names the same.**
    - *Hypothesis:* Current logic adds a timestamp (`new:HHMM...`) to the prefix. This implies filenames *change* on every generation to preserve history.
    - *Action:* Verify if this behavior is desired or if we need a "Overwrite" mode for the final render.
    ?<maybe use the sql id as part of the filename?>

## Phase 3: Audio & Video (The "Geronimo" Pipeline)
- [ ] **Write a script to make text-to-voice.**
    - *Tech:* Kokoro-82M (or similar).
    - *Input:* A text script.
    - *Output:* `.wav` files for each scene.
- [ ] **Create a text script for the Geronimo video.**
    - *Action:* Write the narration that matches the 10 scenes.

## Phase 4: Assembly
- [ ] **Stitch Images + Audio into Video.**
    - *Tools:* ffmpeg or Python editing lib.
