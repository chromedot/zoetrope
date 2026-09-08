# Track Plan: High-Fidelity SFX for GB10

This plan upgrades the SFX engine to AudioLDM2-Large with FP8 optimizations for Blackwell hardware.

## Phase 1: Model & Environment Prep [checkpoint: pending]
Goal: Ensure weights are present and FP8 is supported.

- [x] Task: Download AudioLDM2-Large checkpoints and VAE weights to `models/audio_checkpoints`.
- [x] Task: Verify FP8 loading capabilities for AudioLDM2 nodes in the current ComfyUI environment.
- [ ] Task: User Manual Verification 'Phase 1: Model Prep' (manual check by the user)

## Phase 2: Workflow Upgrade [checkpoint: pending]
Goal: Transition to the new model architecture in code.

- [x] Task: Create a new workflow template JSON for AudioLDM2-Large.
- [x] Task: Implement FP8 weight loading and compute nodes in the workflow template.
- [x] Task: Update `ComfyAudioGenerator._get_workflow` in `scripts/audio_utils.py` to use the new template.
- [ ] Task: User Manual Verification 'Phase 2: Workflow Upgrade' (manual check by the user)

## Phase 3: Integration & Testing [checkpoint: pending]
Goal: Ensure the backend handles the new model output correctly.

- [x] Task: Write integration tests in `tests-unit/test_audio_upgrade.py` to verify generation with the new model.
- [x] Task: Update `api/generate_sfx` in `studio/app.py` to handle any changes in metadata or file formats.
- [ ] Task: User Manual Verification 'Phase 3: Integration' (manual check by the user)

## STATUS as of 2026-09-08: SFX generation is currently broken

Verified by running it: `POST /api/generate_sfx` returns `{"status":"error","message":"'21'"}`.
That error is `audio_utils.py` failing to find node 21's output in ComfyUI's
history — a symptom, not the cause. ComfyUI's own log has the real failure:

```
RuntimeError: mat1 and mat2 must have the same dtype, but got Half and Float8_e4m3fn
  diffusers/pipelines/audioldm2/pipeline_audioldm2.py:1061 in __call__
  diffusers/pipelines/audioldm2/modeling_audioldm2.py:729 in forward
```

The model loads fine — `Loading cvssp/audioldm2-large. Target precision: fp8.
Load dtype: torch.float16` — and then the first matmul fails, because weights
loaded as float16 are multiplied against an fp8 tensor. This is Phase 2 of this
track (FP8 loading) being incomplete rather than done: the plumbing runs, the
precision conversion does not.

Unblocking it means either casting consistently at load time, or dropping to
fp16 for AudioLDM2 specifically and keeping fp8 for the image models. Existing
SFX files in output/ predate the fp8 change and are unaffected.

Note also that scene duration is currently driven by SFX length where a scene
has no narration, so broken SFX has knock-on effects on video timing.

## Phase 4: Blackwell Optimization Audit [checkpoint: pending]
Goal: Verify performance and fidelity on GB10.

- [ ] Task: Verify FP8 execution via ComfyUI console logs and Blackwell Tensor Core utilization.
- [ ] Task: Perform a comparative quality audit between the old AudioLDM and new AudioLDM2-Large outputs.
- [ ] Task: User Manual Verification 'Phase 4: Optimization Audit' (manual check by the user)
