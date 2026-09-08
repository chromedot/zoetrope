# Enforced Review Gates & Revival

*Status: in progress — Steps 0-3 done, Steps 4-6 optional and not started. Started 2026-09-07.*

## Overview
This project (Zoetrope, formerly "comfy-evergreen" / "ComfyUI Story Studio") was built Dec 2025–Feb 2026 by an unreviewed Gemini 2.5 + Conductor workflow. An audit found the project didn't actually run from a fresh checkout (hardcoded `/data/comfy` paths throughout) and that leaked model chain-of-thought ("Wait, the prompt asked for...", "I'll just... for now") had shipped straight into `studio/app.py`. Both are symptoms of the same root cause: review that existed on paper (`/conductor:conductor-review`) but nothing forced anyone — human or agent — to actually run it. 93 commits, zero invocations.

This plan (a) repairs the project into a working, portable, sensibly-named state, and (b) replaces "review as an available command" with actual enforcement: deterministic gates that block bad patterns at edit-time and commit-time, so this specific failure mode can't quietly recur.

## Functional Requirements
1. Preserve the pre-revival codebase as a permanent, citable historical artifact (git tag, pushed) before changing anything.
2. Make the project runnable from any location — no hardcoded absolute paths in code.
3. Remove leaked model reasoning/deliberation comments from shipped code.
4. Add deterministic (no LLM) gates that **block**, not just flag, the two failure modes above from recurring — both at edit-time (PreToolUse hooks on Write/Edit) and at commit-time (a real `.git/hooks/pre-commit`, so it applies no matter who or what is committing). This must include guarding against bypassing the gate itself: not just the literal `--no-verify` flag, but abbreviations of it, short-flag bundling (`-nm`), and git-config-level tampering (`core.hooksPath`, a commit-aliasing `git config alias.*`) that defeats the native hook without ever typing `--no-verify` at all.
5. Establish a real pytest/coverage baseline — the old `conductor/workflow.md`'s aspirational ">80%" was never actually measured.
6. *(Optional)* Add an in-session LLM judgment layer on top of the deterministic gates, guarded so it can't fire more than once per diff state.
7. *(Optional)* Mirror the same deterministic gate in GitHub Actions — the actual non-bypassable-by-Claude backstop.
8. *(Optional)* Adopt the Conductor plugin for planning artifacts only — explicitly **not** as the enforcement mechanism, since `/conductor:conductor-review` has no hooks and would just reproduce the original failure.

## Non-Functional Requirements
- A broken or misconfigured hook must fail **open** (never silently block all work).
- Gates operate on new/changed text only where possible (PreToolUse hooks inspect the tool call's own new content, not the whole file), so they stay fast and low-noise.
- Project-scoped settings only (`.claude/settings.json`) — the user's global `~/.claude/settings.json` must stay untouched.
- A gate's own rule-definition files (e.g. a shared regex-patterns file) must be exempt from the rules they define. The file that documents or detects a bad pattern will otherwise always contain a literal instance of it — as regex source, or as a worked example in a comment — and fail its own check. (Confirmed in practice: `patterns.sh` tripped its own `ABSPATH_PATTERN` the first time it was staged.)
- Pattern-based detection should be scoped as narrowly as the actual failure mode (e.g. a leaked-reasoning check should look at code comments only, never string literals or product copy), and validated against *this* codebase's real vocabulary before being trusted — a phrase can be completely ordinary language in one domain ("the user wants X" in an image/video generation studio) and a real signal in another.

## Acceptance Criteria
- `v0-gemini-era` tag exists and is pushed; permalinks into it resolve.
- The project runs with zero hardcoded absolute paths in code (docs may still describe an example install path as prose).
- A staged commit containing a leaked-reasoning comment or a hardcoded absolute path is rejected by `.git/hooks/pre-commit`, regardless of whether it goes through Claude Code.
- `git commit --no-verify` (or `-n`) is blocked when attempted through Claude Code's Bash tool.
- Real pytest coverage is measured and the coverage floor reflects the real number, not an unverified aspirational one.
- Any new deterministic pattern or gate (Step 2's, and any added later in Steps 3–6) is adversarially tested — bypass attempts, false positives against this codebase's real code, false negatives, and script correctness — before being merged, not just checked against the positive/negative examples it was originally designed around. Step 2's own red-team pass found 3 real high-severity bypasses and 6 real false positives that its manual test battery had missed.

## Out of Scope
- Rewriting or fixing bugs in the actual storytelling application logic (SFX/TTS/video pipeline) — this is the review/repair layer, not new product features.
- The project/repo rename itself (handled separately, already done: `chromedot/comfy` → `chromedot/zoetrope`, folder `comfy-evergreen` → `Zoetrope`).
- Perfect, unbypassable enforcement. Step 2's gates are an explicitly best-effort deterministic layer, confirmed during implementation to be evadable by shell-quote-splitting a literal substring the gate looks for (e.g. `git comm"it" --no-verify`, where bash reassembles the word "commit" from two quoted fragments the gate's regex never sees as contiguous text) — a regex reads command text, not shell semantics, and closing that gap fully isn't worth chasing here. Step 5's CI gate (server-side, outside Claude's control entirely) is the actual non-forgeable backstop, and is optional/not yet built.

---

## Step 0 — Preserve the artifact, then branch [done]
Goal: pin the pre-revival state permanently before touching anything.

- [x] Set git identity to the real author (was `Conductor Agent <conductor@example.com>` on all 93 prior commits).
- [x] `git tag -a v0-gemini-era 7e45c6f` — annotated with what it preserves.
- [x] `git push origin v0-gemini-era` (needed installing + authenticating `gh` first).
- [x] `git checkout -b revival`.

## Step 1 — Unblock and repair [done, commits `2ae6ca8` + `8198b02`]
Goal: gates armed on a dirty/broken baseline get disabled, so fix the baseline first.

- [x] `.gitignore` — remove `/tests-studio` and `/tests-unit` ignores (were hiding 2 already-written test files); add `user/` (flagged by a Copilot review — ComfyUI-Manager cache + per-user settings), `.claude/settings.local.json`, `.claude/review-receipts/`.
- [x] Add `studio/paths.py` — `PROJECT_ROOT = Path(__file__).resolve().parents[1]` and derived `DATA_DIR`/`OUTPUT_DIR`/`LOGS_DIR`/`WORKFLOWS_DIR`/`STORIES_DIR`/`DB_PATH`.
- [x] Replace all 54 hardcoded `/data/comfy` references across 13 code files (`scripts/`, `studio/database.py`, `evergreen.sh`) with paths derived from each file's own location. Two shebangs became the portable `#!/usr/bin/env python3`.
- [x] Fix the 2 `tests-studio/` files that had real hardcoded-path content (not just docs-style mentions).
- [x] Delete the leaked-reasoning comments in `studio/app.py` (lines ~166-168 and ~301-314), replaced with accurate comments describing what the code does.
- [x] Rename the project to **Zoetrope** everywhere it's the live product name (README, in-app title, `gemini.md`, `conductor/` docs) — a zoetrope spins a sequence of stills into the illusion of motion, which is what this pipeline does. Left `conductor/archive/*/spec.md` untouched (frozen history) and left `story_studio.db`/`studio/`/the repo name as internal identifiers, not the product name.
- [x] Rename the folder `comfy-evergreen` → `Zoetrope` (verified: `PROJECT_ROOT`-based path resolution meant zero code changes were needed — the whole point of Step 1).
- [x] Rename the GitHub repo `chromedot/comfy` → `chromedot/zoetrope`; updated the local `origin` remote; verified the `v0-gemini-era` tag permalinks still resolve at the new URL.

## Step 2 — Deterministic gates (no LLM; closes 5 of 7 failures from the original audit) [done, commits `b397f07`, `e83f551`, `6b014a5`]
Goal: block the two failure modes above from recurring, without relying on anyone remembering to run a reviewer.

- [x] `.claude/hooks/patterns.sh` — shared `DELIBERATION_PATTERN` / `ABSPATH_PATTERN` regexes (single source of truth, sourced by both hooks below). Validated against real git history (`2ae6ca8^:studio/app.py`, the actual pre-cleanup leak): 8/17 line-level true positives (sufficient — a real leak is always multi-line and one hit flags the whole hunk) and 0 false positives across ~520 real comment lines currently in the repo.
- [x] `.claude/hooks/lint_write.sh` — PreToolUse hook on `Write|Edit`, inspects **new text only**, scoped to `.py`/`.sh` files (docs stay out of scope on purpose).
- [x] `.claude/hooks/precommit_core.sh` — staged-diff pattern check + pytest, single source of truth, git-hook exit convention (0=allow, 1=block). Pytest's known pre-existing collection failure (`import database` — tracked for Step 3) is surfaced as a warning, not a block, so Step 2 doesn't make the repo uncommittable before Step 3 lands.
- [x] `.claude/hooks/guard_commit.sh` — PreToolUse hook on `Bash`; denies `git commit --no-verify`/abbreviations/`-n`/bundled short flags/`core.hooksPath`-or-alias tampering; pre-emptively runs `precommit_core.sh` on a genuine commit attempt and translates its exit 1 into Claude Code's exit 2.
- [x] `.git/hooks/pre-commit` → execs `precommit_core.sh` (this is what catches a commit made outside Claude Code too).
- [x] `.claude/settings.json` — project-scoped only; wires `PreToolUse: Write|Edit → lint_write.sh` and `PreToolUse: Bash → guard_commit.sh`. `~/.claude/settings.json` untouched.
- [x] `chmod +x` on every runnable hook (not `patterns.sh`, which is sourced, not executed); `stderr` + exit 2 convention; no `set -e` anywhere (a script that fails must still reach its own exit code, not just vanish).
- [x] Verification — positive control (deliberation comment → exit 2), negative control (legit comment → exit 0), abspath positive/negative, docs-out-of-scope check, `--no-verify`/`-n` bypass → exit 2, unrelated commands pass through, and one full end-to-end real `git commit` that a bad staged change actually blocked.
- [x] Adversarial red-team pass (bypass techniques / false-positive / false-negative / shell-script correctness) on the four scripts before committing. Found real issues, all fixed except one documented gap: a `core.hooksPath`/alias-tampering bypass that defeated the native hook too (fixed with an unconditional check), an abbreviated/bundled `--no-verify` bypass (fixed), several real false positives ("the user wants X" as ordinary product language, opt-out UI copy, an assistant reply string, a shell glob idiom — fixed by dropping that alternative and scoping the deliberation check to comment lines only), a diff-scanning bug that silently skipped renamed files and could be confused by content that looks like a diff header (fixed by scanning per-file with a known filename instead of parsing it from the diff text), and a self-reference bug where the gate's own rule-definition file tripped its own rules (fixed by exempting `.claude/hooks/` from both scans, same as any linter exempts its own config). Not fixed, documented as accepted: shell quote-splitting a literal substring (`git comm"it"`) — a regex reads text, not shell semantics; that gap is exactly what Step 5's CI gate is for.
- [ ] **User verification — not done, needs you, not me:** existing Claude Code sessions with `cwd` inside this repo need a restart for the new `.claude/settings.json` hooks to register (confirm via `/hooks`).

## Step 3 — Config substrate [done, commit pending]
Goal: give the gates (and pytest) a real foundation instead of an unmeasured aspiration.

- [x] `pip install pytest-cov pytest-asyncio` (pytest-asyncio and pytest-httpx were already installed; only pytest-cov was missing).
- [x] `pyproject.toml` — first real dependency declaration this project has ever had (no requirements.txt existed), plus `testpaths`, `pythonpath`, and coverage config.
- [x] Fix the pytest collection failure — `pythonpath = ["studio", "scripts"]` in `pyproject.toml` (pytest's own native option). This unblocked all 14 test files, which then surfaced **9 real test failures that had never once run**. All 9 are now fixed, in three groups: 4 stale assertions against the *completed* video Strategy-pattern refactor (`build_command` gained `audio_files`/`sfx_files` kwargs; `_build_ffmpeg_command` was replaced entirely); 2 security tests that assumed path traversal still worked when the app already correctly rejects it before `os.makedirs` is ever reached (rewritten to assert the real, correct behaviour); and 2 caused by a genuine cross-test pollution bug — `tests-studio/test_av_api.py` overwrote the global `database.DB_PATH` and never restored it, silently pointing every later test at a deleted file. Also removed Step 2's now-unnecessary carve-out from `precommit_core.sh`: the pytest gate is fully enforcing, no exceptions.
- [x] Measured: **47.44%**. Floor set to **45%** (`--cov-fail-under=45`), enforced on every commit and meant to ratchet upward.
- [x] Amended all 5 occurrences of the aspirational ">80%" in the old `conductor/workflow.md` to the real, enforced floor. (That file was later deleted outright: 333 lines of mostly-unfilled Conductor template — Node/Go command examples in a Python project, an iPhone testing section, a commit convention followed by 27% of commits. Correcting a number inside boilerplate was the wrong call; the real standards now live in `CLAUDE.md`, which is actually read.)
- [x] `tests-unit/test_docs_match_deps.py` — 4 checks: imports ⊆ declared deps; declared deps ⊆ imports (with a *documented-reason* allowlist for pytest plugins, uvicorn, jinja2, python-multipart); `docs/tech-stack.md` may not claim a library nothing imports (this caught the SQLAlchemy/Alembic lie — now corrected to say the data layer is raw `sqlite3`); and directories referenced in docs must exist (this caught `stories/`/`workflows/` in README, which are really `data/stories/`/`data/workflows/`). Both doc checks had to be narrowed after first-run false positives, per the spec's own scoping rule.
- [x] Wrote `CLAUDE.md` (non-negotiables, what the gates check, real layout, how to run it, GB10 note, styleguide link). Folded the unique GB10 content from `gemini.md` — hardware architecture, SageAttention 3, the ARM64 Docker image, why `--reserve-vram 15` behaves differently under unified memory — into `docs/gb10-optimization.md`, then deleted `gemini.md`. Its "Repository Structure" section had documented `src/`, `web/`, `stories/` and `workflows/`, none of which have ever existed in this repo.
- [ ] **User verification — not done, needs you, not me.**

## Step 4 — In-session judgment layer (optional) [not started]
Goal: an LLM reviewer as an *additional* layer, not a replacement for the deterministic gates above.

- [ ] `Stop` command hook + receipt keyed to the diff's sha256 in `.claude/review-receipts/`, guarded by `stop_hook_active` so it fires at most once per diff state.
- [ ] `.claude/agents/diff-reviewer.md` — instructed to flag only correctness/requirements gaps; explicitly, "PASS with zero findings is valid" (a reviewer that must always find something manufactures work).
- [ ] User verification.

## Step 5 — GitHub Actions: the non-forgeable layer (optional) [not started]
Goal: a gate Claude cannot talk its way around, because it doesn't run on Claude's machine.

- [ ] `.github/workflows/gates.yml` runs the exact same `precommit_core.sh` — no AI, no token required, free on a public repo.
- [ ] (Later, if wanted) LLM review in CI — verify token/cost requirements first.
- [ ] User verification.

## Step 6 — Conductor (optional, last) [not started]
Goal: use Conductor for what it's good at, not for the thing that already failed once.

- [ ] Install Conductor as a Claude Code plugin — for planning artifacts only, giving the diff-reviewer a requirements baseline to check against.
- [ ] Explicitly do **not** wire `/conductor:conductor-review` as a gate — it has no hooks, so using it as "the" review step would just reproduce the original failure (a good reviewer nobody's forced to invoke).
- [ ] User verification.
