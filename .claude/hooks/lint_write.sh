#!/bin/bash
# .claude/hooks/lint_write.sh
# PreToolUse hook on Write|Edit. Inspects ONLY the new text being
# introduced by this tool call (not the whole file) for leaked-reasoning
# comments and hardcoded absolute paths. See patterns.sh for the regexes
# and how they were validated.
#
# Convention: exit 2 + stderr = block (Claude sees the stderr text as the
# reason and can react). Anything that keeps this hook from running
# cleanly fails OPEN (exit 0) -- a broken hook must never silently block
# every write.
set -uo pipefail

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=patterns.sh
source "$HOOK_DIR/patterns.sh"

if ! command -v jq >/dev/null 2>&1; then
    echo "lint_write.sh: jq not found -- failing open, not blocking." >&2
    exit 0
fi

INPUT="$(cat)"

TOOL_NAME="$(printf '%s' "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null)"
FILE_PATH="$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)"

# Out of scope: not a code file (or we couldn't even tell).
if [ -z "$FILE_PATH" ] || ! printf '%s' "$FILE_PATH" | grep -qE "$GATE_CODE_FILE_PATTERN"; then
    exit 0
fi

# .claude/hooks/ is exempt: patterns.sh's own regex source necessarily
# contains the literal bad substrings it detects, and these files'
# comments necessarily quote example trigger phrases -- see
# precommit_core.sh for the same exemption and why.
if printf '%s' "$FILE_PATH" | grep -qE '/\.claude/hooks/'; then
    exit 0
fi

case "$TOOL_NAME" in
    Write)
        NEW_TEXT="$(printf '%s' "$INPUT" | jq -r '.tool_input.content // empty' 2>/dev/null)"
        ;;
    Edit)
        NEW_TEXT="$(printf '%s' "$INPUT" | jq -r '.tool_input.new_string // empty' 2>/dev/null)"
        ;;
    *)
        # Not a tool this hook cares about.
        exit 0
        ;;
esac

if [ -z "$NEW_TEXT" ]; then
    exit 0
fi

# Deliberation check is scoped to comment lines only -- a hardcoded
# path is just as dangerous in a string literal, but "I don't want"/
# "I'm not sure" show up constantly in ordinary product strings (opt-out
# copy, an in-app assistant's reply text) that have nothing to do with
# leaked model reasoning.
HIT="$(printf '%s' "$NEW_TEXT" | grep -E "$COMMENT_LINE_PATTERN" | grep -m 1 -E "$DELIBERATION_PATTERN" 2>/dev/null)"
if [ -n "$HIT" ]; then
    {
        echo "BLOCKED by lint_write.sh: new text in $FILE_PATH reads like a leaked reasoning/deliberation comment, not a normal code comment:"
        echo "  $HIT"
        echo "Rewrite it as a plain statement of what the code does. (See the history of studio/app.py around the Step 1 cleanup commit for the exact pattern this is guarding against.)"
    } >&2
    exit 2
fi

HIT="$(printf '%s' "$NEW_TEXT" | grep -m 1 -E "$ABSPATH_PATTERN" 2>/dev/null)"
if [ -n "$HIT" ]; then
    {
        echo "BLOCKED by lint_write.sh: new text in $FILE_PATH hardcodes an absolute, machine-specific path:"
        echo "  $HIT"
        echo "Use PROJECT_ROOT from studio/paths.py (or Path(__file__).resolve().parents[N]) instead."
    } >&2
    exit 2
fi

exit 0
