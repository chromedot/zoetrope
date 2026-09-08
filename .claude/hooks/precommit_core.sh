#!/bin/bash
# .claude/hooks/precommit_core.sh
# The single source of truth for "is this commit allowed?" -- run BOTH by
# .git/hooks/pre-commit (so it applies to every commit, Claude-made or
# not) and pre-emptively by guard_commit.sh (so Claude gets the same
# verdict before the `git commit` Bash call even runs).
#
# Convention here is git's own hook convention, not Claude Code's:
#   exit 0 = allow the commit
#   exit 1 = block the commit (stderr explains why)
# guard_commit.sh is responsible for translating a 1 here into the 2
# Claude Code's PreToolUse hooks expect.
#
# Never `set -e` -- a script that dies partway through must still reach
# its own exit code, not vanish and leave the caller guessing.
#
# Revision note: adversarially red-teamed before the first commit. The
# original diff-scanning here used a single `git diff --cached -U0`
# call and parsed "+++ b/<file>" lines out of the stream to track which
# file each added line belonged to. Two real bugs came out of that: (1)
# --diff-filter=ACM silently excludes renamed files (status R), so a
# `git mv` + edit was never scanned at all; (2) an ADDED line whose own
# text happens to read like a diff header (e.g. a test fixture
# containing the literal string "++ b/other.py") gets misread as a real
# header by the parser, silently dropping that line from scanning and
# corrupting file attribution for everything after it. Fixed by looping
# per-file (using --diff-filter=ACMR) and tagging every added line with
# the filename the loop already knows, rather than ever trusting
# in-diff text to say what file it belongs to.
set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$REPO_ROOT" ]; then
    echo "precommit_core.sh: not inside a git repo -- failing open." >&2
    exit 0
fi
cd "$REPO_ROOT" || { echo "precommit_core.sh: cannot cd to repo root -- failing open." >&2; exit 0; }

# shellcheck source=patterns.sh
source "$REPO_ROOT/.claude/hooks/patterns.sh"

FAILED=0

# --- 1. Staged-diff pattern checks (added lines only, code files only) ---
# Reuses the exact same regexes lint_write.sh checks new Write/Edit text
# against, so this is a backstop for anything that reached the index by
# some other route (Bash heredoc/sed, a plain terminal commit, another
# tool) rather than a second, possibly-drifted copy of the rules.
DELIB_FOUND=""
ABSPATH_FOUND=""

# .claude/hooks/ is excluded: the gate's own rule definitions (patterns.sh)
# necessarily contain the literal bad substrings they detect (as regex
# source), and this file's own comments necessarily quote example
# trigger phrases for documentation -- both would otherwise always trip
# the very check they define. Same reasoning any linter uses to exempt
# its own rule-definition file from the rule it defines.
CHANGED_FILES="$(git diff --cached --name-only --diff-filter=ACMR -- '*.py' '*.sh' ':(exclude).claude/hooks/*' 2>/dev/null)"

if [ -n "$CHANGED_FILES" ]; then
    while IFS= read -r file; do
        [ -z "$file" ] && continue

        # Added lines only, this file only. The filename is already
        # known from the loop above -- never parsed back out of the
        # diff text itself.
        ADDED="$(git diff --cached -U0 -- "$file" 2>/dev/null | awk '
            /^@@/ { in_hunk=1; next }
            !in_hunk { next }
            /^\+/ { print substr($0, 2) }
        ')"
        [ -z "$ADDED" ] && continue

        DELIB_HIT="$(printf '%s\n' "$ADDED" | grep -E "$COMMENT_LINE_PATTERN" | grep -m 1 -E "$DELIBERATION_PATTERN" 2>/dev/null)"
        if [ -n "$DELIB_HIT" ]; then
            DELIB_FOUND="${DELIB_FOUND}${file}: ${DELIB_HIT}
"
        fi

        ABSPATH_HIT="$(printf '%s\n' "$ADDED" | grep -m 1 -E "$ABSPATH_PATTERN" 2>/dev/null)"
        if [ -n "$ABSPATH_HIT" ]; then
            ABSPATH_FOUND="${ABSPATH_FOUND}${file}: ${ABSPATH_HIT}
"
        fi
    done <<< "$CHANGED_FILES"
fi

if [ -n "$DELIB_FOUND" ]; then
    {
        echo "precommit_core.sh: staged changes contain what reads like a leaked reasoning/deliberation comment:"
        printf '%s' "$DELIB_FOUND" | sed 's/^/  /'
        echo "Rewrite as a plain statement of what the code does."
    } >&2
    FAILED=1
fi

if [ -n "$ABSPATH_FOUND" ]; then
    {
        echo "precommit_core.sh: staged changes hardcode an absolute, machine-specific path:"
        printf '%s' "$ABSPATH_FOUND" | sed 's/^/  /'
        echo "Use PROJECT_ROOT from studio/paths.py instead."
    } >&2
    FAILED=1
fi

# --- 2. Test suite ---
# Step 3 removed the carve-out that used to live here. Until then, pytest
# couldn't even collect tests-studio/ (studio/ wasn't on sys.path, so
# `import database` failed in studio/app.py), and this hook had to treat
# that specific signature as a warning so the repo stayed committable.
# pyproject.toml's `pythonpath` setting fixed the collection failure and
# the 9 real test failures it had been hiding are fixed too, so the suite
# is green and any failure here is now a genuine regression -- no
# exceptions, no special cases. Config (testpaths, coverage floor) comes
# from pyproject.toml, so this runs exactly what a bare `pytest` runs.
PYTEST_BIN="$REPO_ROOT/comfyui-env/bin/python"
if [ -x "$PYTEST_BIN" ]; then
    PYTEST_OUT="$(cd "$REPO_ROOT" && "$PYTEST_BIN" -m pytest -q 2>&1)"
    PYTEST_EXIT=$?

    if [ "$PYTEST_EXIT" -ne 0 ]; then
        {
            echo "precommit_core.sh: pytest failed (exit $PYTEST_EXIT):"
            printf '%s\n' "$PYTEST_OUT" | tail -30 | sed 's/^/  /'
        } >&2
        FAILED=1
    fi
else
    echo "precommit_core.sh: WARNING -- $PYTEST_BIN not found, skipping test suite." >&2
fi

if [ "$FAILED" -ne 0 ]; then
    exit 1
fi
exit 0
