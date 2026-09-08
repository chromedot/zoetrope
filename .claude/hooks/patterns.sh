# .claude/hooks/patterns.sh
# Shared detection patterns for the Zoetrope review gates.
# Sourced by lint_write.sh (new-text-only) and precommit_core.sh
# (staged-diff) — this file is the single source of truth for both.
#
# This is sourced, not executed directly — no shebang, no `set -e`
# (an unrunnable/misbehaving hook must fail open, not take the caller
# down with it).
#
# Revision note: the first version of this file was adversarially
# red-teamed (bypass / false-positive / false-negative / shell-
# correctness angles) before it was ever committed. Several real
# issues came back and are fixed here; see each pattern's comment for
# what changed and why. What did NOT change: this is still a best-
# effort deterministic filter, not a semantic classifier or a security
# boundary. It cannot understand intent, can't evaluate a path built at
# runtime (string concatenation, base64, env vars), doesn't understand
# non-English text, and guard_commit.sh's Bash-command inspection is a
# regex over shell text, not a real shell/git parser -- a determined,
# deliberate bypass (quote-splitting a literal like `comm"it"` to dodge
# a substring match) is a known, accepted gap. That's exactly what
# Step 5's GitHub Actions gate (server-side, outside Claude's control
# entirely) exists to close -- see docs/revival-plan.md.

# Only code files are in scope. Markdown/docs are prose, not leaked
# reasoning or load-bearing paths — README.md, docs/comfy-setup.md and
# gemini.md all still describe the old /data/comfy install path on
# purpose (historical/example text), and that's fine.
GATE_CODE_FILE_PATTERN='\.(py|sh)$'

# Is this line a comment? Used to scope DELIBERATION_PATTERN to actual
# code comments -- NOT to arbitrary string literals/UI copy, which is
# where most of the red team's false positives came from (an opt-out
# checkbox label saying "I don't want...", an in-app assistant's reply
# string saying "I'm not sure how to help..."). A hardcoded path is
# exactly as dangerous in a string literal as in a comment, so
# ABSPATH_PATTERN below is deliberately NOT scoped this way.
COMMENT_LINE_PATTERN='^[[:space:]]*#'

# Leaked first-person model reasoning in a comment -- chain-of-thought
# that should never have shipped. Tuned against the actual historical
# specimen: studio/app.py:166-168 and :301-314 before Step 1 cleaned
# them up (git show 2ae6ca8^:studio/app.py).
#
# Validated: 9/17 line-level true positives on that historical block.
# That's fine, not a miss -- a real leak is always a multi-line chain,
# and ONE matching line is enough to flag the whole hunk. The other 8
# lines in that block ("We need start time...", "Let's get the record
# ...if we want...") are stylistically identical to normal engineering
# comments and are deliberately NOT targeted, because:
# 0/520 false positives across every comment currently in the repo
# (scripts/, studio/, tests-studio/, tests-unit/, *.sh) -- including
# the "# We need to ..." / "# We'll ..." / "# Let's verify ..." style
# comments that are completely legitimate, and a real "# Wait, TDD says
# write a failing test." comment in tests-studio/test_security_sfx.py.
#
# Changes from the red team pass:
#  - Callers now pre-filter to COMMENT_LINE_PATTERN lines before
#    applying this (see above) -- fixes 3 of the false-positive
#    findings outright (opt-out UI copy, assistant reply strings).
#  - Dropped "the (prompt|user) (asked|wants|said)": in an image/video
#    generation studio, ordinary product comments like "crop to the
#    aspect ratio the user wants" are completely idiomatic and would
#    have false-positived constantly. The one historical line this
#    alternative covered ("Wait, the prompt asked for...") is still
#    caught as part of the same block via its other 8 matching lines.
#  - Added "I will" / "I must" (the uncontracted forms of "I'll"/"I
#    should" the red team found evade the original list) and two
#    explicit backtracking markers ("scratch that", "on second
#    thought").
#  - The `??` alternative now requires the double question mark to be
#    followed by whitespace-or-end-of-line, not just "anywhere" --
#    matches the historical ")?? No." but not a glob idiom like
#    "frame??.png" (comment-scoping alone already excludes that
#    specific reproduction since it was actual code, not a comment, but
#    this is a second layer in case someone writes "# see frame??.png"
#    as a comment).
# Known, accepted misses (not chased further -- see Step 4's optional
# LLM judgment layer for anything needing actual semantic
# understanding): hedging with no "I ..." trigger word at all ("Hmm,
# the ticket says... actually wait... going with the simpler fix"),
# non-English text, and "I don't want"/"I think"/"I'm not sure" *as an
# actual human-written comment* rather than leaked model reasoning --
# a regex can't tell those apart by wording alone, same as it always
# could not.
DELIBERATION_PATTERN="I'll|\\bI will\\b|I should|I need to|\\bI must\\b|I'm not sure|\\bI think\\b|\\bI believe\\b|I don't want|I guess|scratch that|on second thought|(\\?\\?([[:space:]]|\$))|^[[:space:]]*#[[:space:]]*No\\.[[:space:]]*\$"

# Hardcoded absolute paths that break portability -- the exact
# /data/comfy regression Step 1 fixed (54 refs across 13 files).
# Matches a literal path into a specific machine's home directory, or a
# specific install location, instead of going through PROJECT_ROOT
# (studio/paths.py). Applies to every line, not just comments -- a
# hardcoded path in real code is the actual danger, not the comment
# next to it.
#
# Changes from the red team pass:
#  - Dropped the bare "/root/" alternative: it never appeared in the
#    actual historical regression (that was specifically /data/comfy),
#    and it's genuinely common as a legitimate *remote* path in
#    ops/deploy scripts (rsync/scp to `host:/root/incoming/` on a
#    different machine) -- more noise than signal.
#  - Added a narrow "/(opt|srv|mnt)/zoetrope" match (case-insensitive
#    via [Zz]) for a plausible future recurrence of the same failure
#    mode under a different top-level directory, WITHOUT the blanket
#    "/opt/[anything]" pattern the red team correctly noted would
#    false-positive on completely standard things like
#    /opt/homebrew/bin/python.
# Known, accepted misses: paths under /opt//srv//mnt/ that aren't this
# project by name, Windows/UNC paths (this is a Linux-hosted project),
# and anything not present as a literal substring in the source text
# -- string concatenation, base64, env-var assembly. A regex reads
# source text, not the value a program computes at runtime; that's a
# structural limit of this whole approach, not a bug to fix here.
ABSPATH_PATTERN='/data/comfy|/data/projects/[A-Za-z0-9_.-]+|/home/[A-Za-z0-9_.-]+|/Users/[A-Za-z0-9_.-]+|/(opt|srv|mnt)/[Zz]oetrope'
