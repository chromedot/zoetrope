# Zoetrope

Automated AI storytelling: a `.story` file (scenes + prompts + narration text) goes in, a narrated MP4 comes out. ComfyUI (port 8188) does image and SFX generation; the Studio (FastAPI, port 8189) is the web UI that drives it and assembles the result.

## Non-negotiables

**Never hardcode an absolute path.** Import `PROJECT_ROOT` from `studio/paths.py`, or derive it with `Path(__file__).resolve().parents[N]`. The project used to hardcode one machine's install directory in 54 places and could not run anywhere else; that's fixed, and a pre-commit gate now rejects any reintroduction.

**Never leave reasoning in a comment.** A comment says what the code does. "I'll just… for now", "Wait, the prompt asked for…", "I'm not sure but…" — that's thinking-out-loud, it shipped to `main` once already, and the same gate rejects it. Reasoning belongs in the response, not the file.

**Never bypass the gates.** `git commit --no-verify` (and `-n`, and abbreviations, and `core.hooksPath` tricks) is blocked on purpose. If a gate fires, fix the finding — the gate existing but being skippable is the exact failure this project was rebuilt to eliminate.

## What the gates check

- `.claude/hooks/lint_write.sh` — PreToolUse on Write/Edit: leaked-reasoning comments and hardcoded paths, in new text only, `.py`/`.sh` only.
- `.claude/hooks/precommit_core.sh` — the same two checks against the staged diff, plus the full pytest suite. Run by `.git/hooks/pre-commit`, so it applies to *every* commit, not just Claude's.
- `.claude/hooks/guard_commit.sh` — PreToolUse on Bash: blocks hook-bypass attempts.
- `.claude/hooks/patterns.sh` — the shared regexes. `.claude/hooks/` is exempt from its own checks (a rule file necessarily contains the thing it detects).

## Layout

| Path | What |
| :--- | :--- |
| `studio/` | FastAPI app (`app.py`), `database.py` (raw `sqlite3`, no ORM), `paths.py`, templates, static |
| `scripts/` | Automation: `story_manager.py` (submits to ComfyUI), `generate_all_images.py` (batch), `video_utils.py` (ffmpeg strategies), `audio_utils.py` (TTS/SFX), `review_story.py` (TUI) |
| `data/` | `stories/*.story`, `workflows/*.json`, `story_studio.db` |
| `tests-studio/`, `tests-unit/` | pytest suite — 56 tests, all passing (floor 52% in `pyproject.toml`, real coverage 54%) |
| `output/` | Generated media, per story. ComfyUI writes here because `evergreen.sh` passes `--output-directory`, not via any symlink |
| `docs/` | Setup and reference for anyone running this: `models.md` (the downloads), `gb10-optimization.md` (hardware tuning), `tech-stack.md`, `product.md`, `comfy-setup.md`, and the `style-*.md` guides |

## Running it

```bash
./evergreen.sh start        # both services (also: stop, restart, status)
tail -f logs/studio.log     # or logs/comfyui.log
curl http://127.0.0.1:8189/status   # studio health
curl http://127.0.0.1:8188/queue    # comfy health
./comfyui-env/bin/python -m pytest  # tests (config in pyproject.toml)
```

**If you change `studio/*.py` or anything in `ComfyUI/`, restart** — `./evergreen.sh restart`. The running process won't pick it up otherwise.

Use `./comfyui-env/bin/python`, never bare `python` — the venv has torch/diffusers/fastapi; the system Python doesn't.

## Hardware

NVIDIA GB10 (Grace-Blackwell), 128GB unified memory, ~140W shared TDP. The ComfyUI startup flags in `evergreen.sh` are tuned for it and are not optional — see `docs/gb10-optimization.md` before changing them.

## Definition of done

1. `./comfyui-env/bin/python -m pytest` passes (56 tests; the pre-commit gate runs them too).
2. The gates pass. If one fires, fix the finding — don't reach for a bypass.
3. **If you changed anything in the generation pipeline, actually run it.** Not the tests — the pipeline. Start the services, generate a scene, assemble a video, look at the output.

That third one is not boilerplate. `evergreen.sh` could not launch ComfyUI for months: it printed a pid and reported success while the backend was dead. Every test passed the whole time, because nothing in the suite starts a service. Three of the four bugs found on 2026-09-08 were invisible to the test suite by construction and turned up within minutes of running the thing for real.

## Commit messages

No enforced format — the conventional-commits convention this project once documented was followed in 27% of commits, so it isn't claimed here. What's expected: a subject line that says what changed, and a body that says *why*, including what you verified and anything you deliberately left alone. `git log` is the only record of reasoning this project keeps.

## Style

`docs/style-python.md` and `docs/style-general.md`. Match surrounding code over the guide where they disagree.
