# Track Spec: High-Fidelity SFX for GB10

## Overview
This track upgrades the sound effects (SFX) generation engine from the standard AudioLDM to **AudioLDM2-Large**. This upgrade is specifically designed to leverage the NVIDIA GB10 (Grace-Blackwell) hardware, utilizing FP8 precision for optimal performance and high-fidelity output.

## Functional Requirements
1.  **Model Migration:** Replace the existing AudioLDM implementation with AudioLDM2-Large within the ComfyUI workflow.
2.  **Blackwell Optimization:** Implement and verify FP8 precision for the audio model weights and compute paths, ensuring compatibility with the GB10's Tensor Cores.
3.  **Enhanced Prompt Adherence:** Configure the model to prioritize natural sound generation and strict adherence to user prompts to minimize "hallucinated" or artificial sounds.
4.  **Backend Integration:** Update `scripts/audio_utils.py` to handle the new model's requirements (e.g., sample rates, duration limits).

## Non-Functional Requirements
- **Hardware Efficiency:** Must utilize the GB10's high VRAM and unified memory architecture.
- **Stability:** Ensure model loading and generation do not cause OOM (Out-of-Memory) errors given the 15GB OS reservation.

## Acceptance Criteria
- SFX generated using the AudioLDM2-Large model.
- Generation logs confirm the use of FP8 precision.
- Resulting audio is subjectively more realistic and matches the prompt more accurately than the previous version.
- No regression in TTS (narration) or image generation functionality.

## Out of Scope
- Replacing the Edge-TTS narration engine.
- Implementing real-time audio streaming.
