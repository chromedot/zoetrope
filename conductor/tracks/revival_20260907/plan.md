# Track Plan: Enforced Review Gates & Revival

## Step 0 — Preserve the artifact, then branch [checkpoint: done]
Goal: pin the pre-revival state permanently before touching anything.

- [x] Task: Set git identity to the real author (was `Conductor Agent <conductor@example.com>` on all 93 prior commits).
- [x] Task: `git tag -a v0-gemini-era 7e45c6f` — annotated with what it preserves.
- [x] Task: `git push origin v0-gemini-era` (needed installing + authenticating `gh` first).
- [x] Task: `git checkout -b revival`.

## Step 1 — Unblock and repair [checkpoint: done, commits `2ae6ca8` + `8198b02`]
Goal: gates armed on a dirty/broken baseline get disabled, so fix the baseline first.

- [x] Task: `.gitignore` — remove `/tests-studio` and `/tests-unit` ignores (were hiding 2 already-written test files); add `user/` (flagged by a Copilot review — ComfyUI-Manager cache + per-user settings), `.claude/settings.local.json`, `.claude/review-receipts/`.
- [x] Task: Add `studio/paths.py` — `PROJECT_ROOT = Path(__file__).resolve().parents[1]` and derived `DATA_DIR`/`OUTPUT_DIR`/`LOGS_DIR`/`WORKFLOWS_DIR`/`STORIES_DIR`/`DB_PATH`.
- [x] Task: Replace all 54 hardcoded `/data/comfy` references across 13 code files (`scripts/`, `studio/database.py`, `evergreen.sh`) with paths derived from each file's own location. Two shebangs became the portable `#!/usr/bin/env python3`.
- [x] Task: Fix the 2 `tests-studio/` files that had real hardcoded-path content (not just docs-style mentions).
- [x] Task: Delete the leaked-reasoning comments in `studio/app.py` (lines ~166-168 and ~301-314), replaced with accurate comments describing what the code does.
- [x] Task: Rename the project to **Zoetrope** everywhere it's the live product name (README, in-app title, `gemini.md`, `conductor/` docs) — a zoetrope spins a sequence of stills into the illusion of motion, which is what this pipeline does. Left `conductor/archive/*/spec.md` untouched (frozen history) and left `story_studio.db`/`studio/`/the repo name as internal identifiers, not the product name.
- [x] Task: Rename the folder `comfy-evergreen` → `Zoetrope` (verified: `PROJECT_ROOT`-based path resolution meant zero code changes were needed — the whole point of Step 1).
- [x] Task: Rename the GitHub repo `chromedot/comfy` → `chromedot/zoetrope`; updated the local `origin` remote; verified the `v0-gemini-era` tag permalinks still resolve at the new URL.

## Step 2 — Deterministic gates (no LLM; closes 5 of 7 failures from the original audit) [checkpoint: in progress]
Goal: block the two failure modes above from recurring, without relying on anyone remembering to run a reviewer.

- [x] Task: `.claude/hooks/patterns.sh` — shared `DELIBERATION_PATTERN` / `ABSPATH_PATTERN` regexes (single source of truth, sourced by both hooks below). Validated against real git history (`2ae6ca8^:studio/app.py`, the actual pre-cleanup leak): 9/17 line-level true positives (sufficient — a real leak is always multi-line and one hit flags the whole hunk) and 0 false positives across ~520 real comment lines currently in the repo.
- [x] Task: `.claude/hooks/lint_write.sh` — PreToolUse hook on `Write|Edit`, inspects **new text only**, scoped to `.py`/`.sh` files (docs stay out of scope on purpose).
- [x] Task: `.claude/hooks/precommit_core.sh` — staged-diff pattern check + pytest, single source of truth, git-hook exit convention (0=allow, 1=block). Pytest's known pre-existing collection failure (`import database` — tracked for Step 3) is surfaced as a warning, not a block, so Step 2 doesn't make the repo uncommittable before Step 3 lands.
- [x] Task: `.claude/hooks/guard_commit.sh` — PreToolUse hook on `Bash`; denies `git commit --no-verify`/`-n`; pre-emptively runs `precommit_core.sh` on a genuine commit attempt and translates its exit 1 into Claude Code's exit 2.
- [x] Task: `.git/hooks/pre-commit` → execs `precommit_core.sh` (this is what catches a commit made outside Claude Code too).
- [x] Task: `.claude/settings.json` — project-scoped only; wires `PreToolUse: Write|Edit → lint_write.sh` and `PreToolUse: Bash → guard_commit.sh`. `~/.claude/settings.json` untouched.
- [x] Task: `chmod +x` on every runnable hook (not `patterns.sh`, which is sourced, not executed); `stderr` + exit 2 convention; no `set -e` anywhere (a script that fails must still reach its own exit code, not just vanish).
- [x] Task: Verification — positive control (deliberation comment → exit 2), negative control (legit comment → exit 0), abspath positive/negative, docs-out-of-scope check, `--no-verify`/`-n` bypass → exit 2, unrelated commands pass through, and one full end-to-end real `git commit` that a bad staged change actually blocked.
- [ ] Task: Adversarial red-team pass (bypass techniques / false-positive / false-negative / shell-script correctness) on the four scripts before committing — running now.
- [ ] Task: Commit Step 2.
- [ ] Task: Conductor - User Manual Verification 'Step 2: Deterministic gates' — note for the user: after this commits, existing Claude Code sessions with `cwd` inside this repo need a restart for the new `.claude/settings.json` hooks to register (confirm via `/hooks`).

## Step 3 — Config substrate [checkpoint: not started]
Goal: give the gates (and pytest) a real foundation instead of an unmeasured aspiration.

- [ ] Task: `pip install pytest-cov pytest-asyncio`.
- [ ] Task: `pyproject.toml` — deps, `testpaths`, coverage wired at `--cov-fail-under=0` initially.
- [ ] Task: Fix the pre-existing pytest collection failure (`studio/` not on `sys.path` when running under pytest — `import database` fails in `studio/app.py`) that Step 2's `precommit_core.sh` currently has to special-case as a warning.
- [ ] Task: Measure the real coverage number once tests actually collect; set the floor to `floor(actual) - 2`, ratchet upward over time.
- [ ] Task: Amend `conductor/workflow.md`'s aspirational ">80%" to the real number.
- [ ] Task: `tests-unit/test_docs_match_deps.py` — (a) imports ⊆ declared deps, (b) declared deps ⊆ imports ∪ {uvicorn, jinja2} (catches the SQLAlchemy-in-tech-stack-but-never-imported lie), (c) every backticked path in docs must exist (catches phantom dirs and any future `/data/comfy`-style regression in docs).
- [ ] Task: Write `CLAUDE.md` (short, re-read every turn: project + the `PROJECT_ROOT` rule + what the gates reject + a link to `conductor/code_styleguides/python.md`). Fold `gemini.md`'s GB10 content into `docs/gb10-optimization.md` and delete `gemini.md` — two context files where an agent reads only one is how the second one silently rots.
- [ ] Task: Conductor - User Manual Verification 'Step 3: Config substrate'.

## Step 4 — In-session judgment layer (optional) [checkpoint: not started]
Goal: an LLM reviewer as an *additional* layer, not a replacement for the deterministic gates above.

- [ ] Task: `Stop` command hook + receipt keyed to the diff's sha256 in `.claude/review-receipts/`, guarded by `stop_hook_active` so it fires at most once per diff state.
- [ ] Task: `.claude/agents/diff-reviewer.md` — instructed to flag only correctness/requirements gaps; explicitly, "PASS with zero findings is valid" (a reviewer that must always find something manufactures work).
- [ ] Task: Conductor - User Manual Verification 'Step 4: In-session judgment layer'.

## Step 5 — GitHub Actions: the non-forgeable layer (optional) [checkpoint: not started]
Goal: a gate Claude cannot talk its way around, because it doesn't run on Claude's machine.

- [ ] Task: `.github/workflows/gates.yml` runs the exact same `precommit_core.sh` — no AI, no token required, free on a public repo.
- [ ] Task: (Later, if wanted) LLM review in CI — verify token/cost requirements first.
- [ ] Task: Conductor - User Manual Verification 'Step 5: GitHub Actions'.

## Step 6 — Conductor (optional, last) [checkpoint: not started]
Goal: use Conductor for what it's good at, not for the thing that already failed once.

- [ ] Task: Install Conductor as a Claude Code plugin — for planning artifacts only, giving the diff-reviewer a requirements baseline to check against.
- [ ] Task: Explicitly do **not** wire `/conductor:conductor-review` as a gate — it has no hooks, so using it as "the" review step would just reproduce the original failure (a good reviewer nobody's forced to invoke).
- [ ] Task: Conductor - User Manual Verification 'Step 6: Conductor plugin'.
