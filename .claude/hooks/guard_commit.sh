#!/bin/bash
# .claude/hooks/guard_commit.sh
# PreToolUse hook on Bash. Three checks, in order:
#   1. Unconditional: is this command trying to reconfigure git's hook
#      path or define a commit-related alias? There's no legitimate
#      reason for that during normal work, and both are ways to defeat
#      .git/hooks/pre-commit without ever typing "--no-verify" -- so
#      this check runs regardless of whether "git commit" appears in
#      the same command.
#   2. Is this a `git commit` invocation, and does it try to bypass
#      hooks via --no-verify (or an abbreviation of it, or the short
#      -n form, plain or bundled with other short flags)? Deny outright
#      if so -- that flag skips .git/hooks/pre-commit entirely, which
#      is the one layer that's supposed to apply no matter who/what is
#      committing.
#   3. Otherwise, for a normal `git commit` attempt: pre-emptively run
#      the same precommit_core.sh the git hook will run, so Claude gets
#      the verdict immediately instead of finding out after attempting
#      the commit. precommit_core.sh follows git's own convention
#      (0=allow, 1=block); this hook translates that 1 into Claude
#      Code's own PreToolUse convention (2=block).
#
# Anything that keeps this hook from running cleanly fails OPEN (exit 0)
# -- the real backstop is .git/hooks/pre-commit itself, which runs
# regardless of whether this Claude-Code-side hook works.
#
# Revision note -- adversarially red-teamed before the first commit,
# three real bypasses came back, all fixed except one documented as an
# accepted gap:
#  - `git -c core.hooksPath=/dev/null commit` and a prior `git config
#    core.hooksPath ...` + `git config alias.ci commit` + `git ci`
#    sequence both defeated the original naive `git ... commit`
#    detection AND the native git hook itself (hooksPath redirection
#    means git never looks for .git/hooks/pre-commit at all). Fixed by
#    check #1 above, which fires on the hooksPath/alias-defining
#    command itself, before "git commit" (or an alias for it) is ever
#    typed.
#  - `--no-verif` (an abbreviation git accepts as a prefix match) and
#    `-nm` (bundling -n with another short flag) both evaded the
#    original exact-match bypass detector. Fixed by matching any
#    unambiguous prefix of --no-verify and any short-option token that
#    includes `n`, once we're already in the "this is a git commit"
#    branch.
#  - NOT fixed, documented as an accepted gap: shell quote-splitting a
#    literal substring this script looks for (e.g. `git comm"it"
#    --no-verify`, where bash reassembles "commit" from two quoted
#    fragments but the raw command text this hook sees never contains
#    the contiguous word). Detecting that would mean re-implementing a
#    real shell word-splitter, which is a losing battle against a
#    deliberately adversarial input by design -- a regex reads text, not
#    semantics. This is exactly why Step 5's GitHub Actions gate (runs
#    server-side, outside Claude's control entirely) is the real
#    non-bypassable backstop, not this script. See
#    docs/revival-plan.md.
set -uo pipefail

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v jq >/dev/null 2>&1; then
    echo "guard_commit.sh: jq not found -- failing open, not blocking." >&2
    exit 0
fi

INPUT="$(cat)"
COMMAND="$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)"

if [ -z "$COMMAND" ]; then
    exit 0
fi

# --- 1. Unconditional: hook-path / alias tampering ---
# Deliberately NOT gated on "does this also mention git commit" -- the
# red team's working bypass ran these as separate prior commands.
if printf '%s' "$COMMAND" | grep -qE 'core\.hooksPath|alias\.[a-zA-Z0-9_-]+[[:space:]=]+.*commit'; then
    {
        echo "BLOCKED by guard_commit.sh: this command reconfigures git's hook path or defines a commit alias."
        echo "Both are ways to make .git/hooks/pre-commit stop running -- not allowed, regardless of what it's for."
    } >&2
    exit 2
fi

# Not a git-commit invocation at all (git and commit anywhere in the
# same command, not necessarily adjacent -- `git -c x=y commit` still
# counts) -- not this hook's concern beyond check #1 above.
if ! printf '%s' "$COMMAND" | grep -qE '\bgit\b.*\bcommit\b'; then
    exit 0
fi

# --- 2. Bypass-flag detection ---
# --no-verify, any unambiguous prefix of it down to --no-v (git accepts
# prefix abbreviations of long options), a standalone -n, or -n bundled
# into any other short-option token (e.g. -nm, -an).
if printf '%s' "$COMMAND" | grep -qE -- '--no-v(e(r(i(f(y)?)?)?)?)?([[:space:]]|$)|(^|[[:space:]])-[a-zA-Z]*n[a-zA-Z]*([[:space:]]|$)'; then
    {
        echo "BLOCKED by guard_commit.sh: this git commit tries to bypass hooks (--no-verify, an abbreviation of it, or -n)."
        echo "The pre-commit gate exists specifically so commits can't skip review -- run the commit without that flag."
    } >&2
    exit 2
fi

# --- 3. Genuine commit attempt -- get the real verdict now rather than after. ---
PRECOMMIT_OUT="$("$HOOK_DIR/precommit_core.sh" 2>&1)"
PRECOMMIT_EXIT=$?

if [ "$PRECOMMIT_EXIT" -ne 0 ]; then
    {
        echo "BLOCKED by guard_commit.sh: precommit_core.sh would reject this commit:"
        printf '%s\n' "$PRECOMMIT_OUT" | sed 's/^/  /'
    } >&2
    exit 2
fi

# Surface any non-blocking warnings (e.g. the known Step-3 pytest issue)
# without failing the tool call.
if [ -n "$PRECOMMIT_OUT" ]; then
    printf '%s\n' "$PRECOMMIT_OUT" >&2
fi

exit 0
