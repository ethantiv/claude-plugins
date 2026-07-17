#!/usr/bin/env bash
#
# Decide whether a babysit-pr monitoring pass is clean enough to merge.
#
# Usage: auto-gate.sh < snapshot.json
#   stdin — the JSON object emitted by pr-snapshot.sh (status == ok payload).
#
# Stdout: one JSON object {clean, sha}.
#   clean — this pass is a positive green (see definition below); merge when true
#   sha   — current HEAD sha (feeds `gh pr merge --match-head-commit`)
#
# "clean" is positive confirmation of mergeability, not mere absence of red:
# mergeStateStatus == CLEAN (which already requires passing required checks and
# approvals) plus empty failing/pending/review/changes arrays as a belt-and-
# suspenders. Any other mergeStateStatus (UNKNOWN, BEHIND, BLOCKED, DIRTY,
# UNSTABLE, DRAFT) is treated as not-clean.

set -uo pipefail

command -v jq >/dev/null 2>&1 || { echo "auto-gate: jq not found" >&2; exit 1; }

snapshot="$(cat)"
[ -n "$snapshot" ] || { echo "auto-gate: empty snapshot on stdin" >&2; exit 1; }

number="$(printf '%s' "$snapshot" | jq -r '.number // empty' 2>/dev/null)"
[ -n "$number" ] || { echo "auto-gate: snapshot has no PR number" >&2; exit 1; }

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

jq -n --argjson clean "$clean" --arg sha "$head_sha" '{clean:$clean, sha:$sha}'
