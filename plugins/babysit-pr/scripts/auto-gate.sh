#!/usr/bin/env bash
#
# Track consecutive clean monitoring passes for the --auto mode of babysit-pr.
#
# Each babysit-pr pass runs in a fresh session, so "two clean passes in a row"
# needs cross-pass state. This script keeps a per-PR counter under the git dir,
# anchored to HEAD's sha so the streak only counts when the code did not change.
#
# Usage: auto-gate.sh < snapshot.json
#   stdin — the JSON object emitted by pr-snapshot.sh (status == ok payload).
#
# Stdout: one JSON object {clean, consecutive, sha, should_merge}.
#   clean        — this pass is a positive green (see definition below)
#   consecutive  — number of clean passes in a row at the current sha
#   sha          — current HEAD sha (feeds `gh pr merge --match-head-commit`)
#   should_merge — clean && consecutive >= 2
#
# "clean" is positive confirmation of mergeability, not mere absence of red:
# mergeStateStatus == CLEAN (which already requires passing required checks and
# approvals) plus empty failing/pending/review/changes arrays as a belt-and-
# suspenders. Any other mergeStateStatus (UNKNOWN, BEHIND, BLOCKED, DIRTY,
# UNSTABLE, DRAFT) is treated as not-clean and resets the counter to 0.
#
# Fail-safe: a missing/corrupt state file is treated as count 0, never as a
# reason to merge, and never aborts the pass.

set -uo pipefail

command -v jq >/dev/null 2>&1 || { echo "auto-gate: jq not found" >&2; exit 1; }

snapshot="$(cat)"
[ -n "$snapshot" ] || { echo "auto-gate: empty snapshot on stdin" >&2; exit 1; }

number="$(printf '%s' "$snapshot" | jq -r '.number // empty' 2>/dev/null)"
[ -n "$number" ] || { echo "auto-gate: snapshot has no PR number" >&2; exit 1; }

git_dir="$(git rev-parse --absolute-git-dir 2>/dev/null || echo "")"
[ -n "$git_dir" ] || { echo "auto-gate: not in a git repository" >&2; exit 1; }
state_file="$git_dir/babysit-pr-$number.json"

head_sha="$(git rev-parse HEAD 2>/dev/null || echo "")"
[ -n "$head_sha" ] || { echo "auto-gate: cannot resolve HEAD" >&2; exit 1; }

clean="$(printf '%s' "$snapshot" | jq -r '
  (.status == "ok")
  and (.mergeStateStatus == "CLEAN")
  and (.has_conflicts == false)
  and ((.failing_checks // []) | length == 0)
  and ((.pending_checks // []) | length == 0)
  and ((.review_threads // []) | length == 0)
  and ((.changes_requested // []) | length == 0)
' 2>/dev/null)"
[ "$clean" = "true" ] || clean="false"

# ponytail: corrupt/missing state -> prev_count 0, prev_sha empty; never crash.
prev_count="$(jq -r '.count // 0' "$state_file" 2>/dev/null)"
prev_sha="$(jq -r '.sha // ""' "$state_file" 2>/dev/null)"
[[ "$prev_count" =~ ^[0-9]+$ ]] || prev_count=0

if [ "$clean" = "true" ]; then
  if [ "$prev_sha" = "$head_sha" ]; then
    count=$((prev_count + 1))
  else
    count=1
  fi
else
  count=0
fi

jq -n --argjson count "$count" --arg sha "$head_sha" \
  '{count:$count, sha:$sha}' > "$state_file"

should_merge=false
[ "$clean" = "true" ] && [ "$count" -ge 2 ] && should_merge=true

jq -n \
  --argjson clean "$clean" \
  --argjson consecutive "$count" \
  --arg sha "$head_sha" \
  --argjson should_merge "$should_merge" \
  '{clean:$clean, consecutive:$consecutive, sha:$sha, should_merge:$should_merge}'
