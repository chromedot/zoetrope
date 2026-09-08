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
| `scripts/` | Automation: `story_manager.py`, `run_story.py`, `generate_all_images.py`, `video_utils.py`, `audio_utils.py`, TUI (`review_story.py`), startup shells |
| `data/` | `stories/*.story`, `workflows/*.json`, `story_studio.db` |
| `tests-studio/`, `tests-unit/` | pytest suite — 46 tests, all passing, 47% coverage (floor 45% in `pyproject.toml`) |
| `output/` | Generated media, per story. `ComfyUI/output` is a symlink to this |
| `docs/` | `revival-plan.md` (the current work plan), `gb10-optimization.md`, `comfy-setup.md` |
| `conductor/` | Gemini-era planning docs. Historical — `conductor/archive/` is frozen, don't rewrite it |

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

## Style

`conductor/code_styleguides/python.md` and `conductor/code_styleguides/general.md`. Match surrounding code over the guide where they disagree.
