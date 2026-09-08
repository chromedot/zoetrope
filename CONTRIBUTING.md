# Contributing

Thanks for looking. Before anything else, read the [Hardware](README.md#hardware) note — this project currently targets one machine (NVIDIA GB10, 128 GB unified memory), and most of what could go wrong for you is downstream of that.

## Before you commit

Every commit here — human or AI-assisted — passes through an automated pre-commit gate: no hardcoded machine-specific paths, no code comments that read as leaked reasoning, and the full test suite (56 tests) must pass. `--no-verify` and its usual workarounds are blocked on purpose.

The full mechanics — exactly which patterns get rejected, which hooks enforce them, and the narrow exemptions — live in [`CLAUDE.md`](CLAUDE.md), and are kept there rather than duplicated here so there's one place to keep current.

## Definition of done

1. `./comfyui-env/bin/python -m pytest` passes, and the gates pass.
2. **If you touched the generation pipeline, you ran the pipeline** — started the services, generated a scene, assembled a video, watched it.

That second item is not boilerplate: `evergreen.sh` was unable to launch ComfyUI for months while printing a process id and reporting success over a dead backend, and every test passed throughout, because nothing in the suite starts a service. See `CLAUDE.md`'s Definition of done for the specifics of what that cost.

## Commit messages

No enforced format. What's expected: a subject line saying what changed, and a body saying **why** — including what you verified and anything you deliberately left alone. `git log` is the only durable record of reasoning this project keeps.

## Style

[`docs/style-python.md`](docs/style-python.md) and [`docs/style-general.md`](docs/style-general.md). Where a guide and the surrounding code disagree, match the surrounding code.

## Reporting a problem

Issues are open. The most useful report includes your hardware (especially if it isn't a GB10), the output of `./evergreen.sh status`, and the relevant tail of `logs/comfyui.log` or `logs/studio.log`.

If something generated a *bad video* rather than an error, that's the most valuable class of bug here — silent degradation is much harder to notice than a crash. Please include the ffprobe output.
