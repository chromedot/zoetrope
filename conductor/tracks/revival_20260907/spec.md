# Track Spec: Enforced Review Gates & Revival

## Overview
This project (Zoetrope, formerly "comfy-evergreen" / "ComfyUI Story Studio") was built Dec 2025–Feb 2026 by an unreviewed Gemini 2.5 + Conductor workflow. An audit found the project didn't actually run from a fresh checkout (hardcoded `/data/comfy` paths throughout) and that leaked model chain-of-thought ("Wait, the prompt asked for...", "I'll just... for now") had shipped straight into `studio/app.py`. Both are symptoms of the same root cause: review that existed on paper (`/conductor:conductor-review`) but nothing forced anyone — human or agent — to actually run it. 93 commits, zero invocations.

This track (a) repairs the project into a working, portable, sensibly-named state, and (b) replaces "review as an available command" with actual enforcement: deterministic gates that block bad patterns at edit-time and commit-time, so this specific failure mode can't quietly recur.

## Functional Requirements
1. Preserve the pre-revival codebase as a permanent, citable historical artifact (git tag, pushed) before changing anything.
2. Make the project runnable from any location — no hardcoded absolute paths in code.
3. Remove leaked model reasoning/deliberation comments from shipped code.
4. Add deterministic (no LLM) gates that **block**, not just flag, the two failure modes above from recurring — both at edit-time (PreToolUse hooks on Write/Edit) and at commit-time (a real `.git/hooks/pre-commit`, so it applies no matter who or what is committing), including a gate against bypassing the gate itself (`--no-verify`).
5. Establish a real pytest/coverage baseline — `conductor/workflow.md`'s aspirational ">80%" was never actually measured.
6. *(Optional)* Add an in-session LLM judgment layer on top of the deterministic gates, guarded so it can't fire more than once per diff state.
7. *(Optional)* Mirror the same deterministic gate in GitHub Actions — the actual non-bypassable-by-Claude backstop.
8. *(Optional)* Adopt the Conductor plugin for planning artifacts only — explicitly **not** as the enforcement mechanism, since `/conductor:conductor-review` has no hooks and would just reproduce the original failure.

## Non-Functional Requirements
- A broken or misconfigured hook must fail **open** (never silently block all work).
- Gates operate on new/changed text only where possible (PreToolUse hooks inspect the tool call's own new content, not the whole file), so they stay fast and low-noise.
- Project-scoped settings only (`.claude/settings.json`) — the user's global `~/.claude/settings.json` must stay untouched.

## Acceptance Criteria
- `v0-gemini-era` tag exists and is pushed; permalinks into it resolve.
- The project runs with zero hardcoded absolute paths in code (docs may still describe an example install path as prose).
- A staged commit containing a leaked-reasoning comment or a hardcoded absolute path is rejected by `.git/hooks/pre-commit`, regardless of whether it goes through Claude Code.
- `git commit --no-verify` (or `-n`) is blocked when attempted through Claude Code's Bash tool.
- Real pytest coverage is measured and the coverage floor reflects the real number, not an unverified aspirational one.

## Out of Scope
- Rewriting or fixing bugs in the actual storytelling application logic (SFX/TTS/video pipeline) — this track is the review/repair layer, not new product features.
- The project/repo rename itself (handled separately, already done: `chromedot/comfy` → `chromedot/zoetrope`, folder `comfy-evergreen` → `Zoetrope`).
- Perfect, unbypassable enforcement. Step 2's gates are an explicitly best-effort deterministic layer; Step 5's CI gate is the actual non-forgeable backstop, and is optional/not yet built.
