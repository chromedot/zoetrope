# Contributing

Thanks for looking. Before anything else, read the [Hardware](README.md#hardware) note — this project currently targets one machine (NVIDIA GB10, 128 GB unified memory), and most of what could go wrong for you is downstream of that.

## The gates

Commits in this repo pass through automated checks. They are not advisory, and they exist because of a specific history: this project was originally built by an unreviewed AI workflow that shipped 54 hardcoded absolute paths and a block of leaked model reasoning into `main` across 93 commits, because review existed as a command nobody was obliged to run.

`.git/hooks/pre-commit` runs `.claude/hooks/precommit_core.sh`, which rejects a commit if:

- **A hardcoded machine-specific path** appears in new `.py`/`.sh` code. Derive paths from `PROJECT_ROOT` in `studio/paths.py`, or `Path(__file__).resolve().parents[N]`.
- **A code comment reads as leaked reasoning** — "I'll just… for now", "not sure but…", "Wait, the prompt asked for…". A comment should say what the code does.
- **A test fails.** All 51 must pass, and coverage must stay at or above the floor in `pyproject.toml`.

If a gate fires, fix the finding. Don't reach for `--no-verify` — it's blocked on purpose, along with its abbreviations, bundled short flags, and `core.hooksPath` tampering.

Two exemptions, both narrow: `.claude/hooks/` is exempt from the pattern checks, because a rules file necessarily contains the patterns it detects. Documentation is out of scope for the path check, since docs legitimately quote example paths.

## Definition of done

1. `./comfyui-env/bin/python -m pytest` passes.
2. The gates pass.
3. **If you touched the generation pipeline, you ran the pipeline.**

That third item is not boilerplate. `evergreen.sh` was unable to launch ComfyUI for months while printing a process id and reporting success over a dead backend — and every test passed throughout, because nothing in the suite starts a service. Three of the four bugs found on 8 September 2026 were invisible to the test suite by construction and surfaced within minutes of actually running the thing.

Start the services, generate a scene, assemble a video, watch it.

## Commit messages

No enforced format. This project documented a conventional-commits standard once and followed it in 27% of commits, so it isn't claimed here.

What is expected: a subject line saying what changed, and a body saying **why** — including what you verified and anything you deliberately left alone. `git log` is the only durable record of reasoning this project keeps, and it's treated that way.

## Style

[`docs/code_styleguides/python.md`](docs/code_styleguides/python.md) and [`general.md`](docs/code_styleguides/general.md). Where a guide and the surrounding code disagree, match the surrounding code.

## Reporting a problem

Issues are open. The most useful report includes your hardware (especially if it isn't a GB10), the output of `./evergreen.sh status`, and the relevant tail of `logs/comfyui.log` or `logs/studio.log`.

If something generated a *bad video* rather than an error, that's the most valuable class of bug here — silent degradation is much harder to notice than a crash. Please include the ffprobe output.
