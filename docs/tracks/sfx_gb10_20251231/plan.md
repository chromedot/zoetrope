# Track Plan: High-Fidelity SFX for GB10

This plan upgrades the SFX engine to AudioLDM2-Large with FP8 optimizations for Blackwell hardware.

## Phase 1: Model & Environment Prep [checkpoint: pending]
Goal: Ensure weights are present and FP8 is supported.

- [x] Task: Download AudioLDM2-Large checkpoints and VAE weights to `models/audio_checkpoints`.
- [x] Task: Verify FP8 loading capabilities for AudioLDM2 nodes in the current ComfyUI environment.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Model Prep' (Protocol in workflow.md)

## Phase 2: Workflow Upgrade [checkpoint: pending]
Goal: Transition to the new model architecture in code.

- [x] Task: Create a new workflow template JSON for AudioLDM2-Large.
- [x] Task: Implement FP8 weight loading and compute nodes in the workflow template.
- [x] Task: Update `ComfyAudioGenerator._get_workflow` in `scripts/audio_utils.py` to use the new template.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Workflow Upgrade' (Protocol in workflow.md)

## Phase 3: Integration & Testing [checkpoint: pending]
Goal: Ensure the backend handles the new model output correctly.

- [x] Task: Write integration tests in `tests-unit/test_audio_upgrade.py` to verify generation with the new model.
- [x] Task: Update `api/generate_sfx` in `studio/app.py` to handle any changes in metadata or file formats.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Integration' (Protocol in workflow.md)

## Phase 4: Blackwell Optimization Audit [checkpoint: pending]
Goal: Verify performance and fidelity on GB10.

- [ ] Task: Verify FP8 execution via ComfyUI console logs and Blackwell Tensor Core utilization.
- [ ] Task: Perform a comparative quality audit between the old AudioLDM and new AudioLDM2-Large outputs.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Optimization Audit' (Protocol in workflow.md)
