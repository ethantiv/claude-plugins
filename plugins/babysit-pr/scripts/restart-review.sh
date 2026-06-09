#!/usr/bin/env bash
#
# Restart the code-review workflow for the current PR branch so a fresh run
# evaluates the latest commit and the current (post-resolve) review-thread state.
#
# Run this after resolving/closing any review thread while a review is still in
# progress: an in-flight run read the pre-resolve snapshot and would re-post
# findings you already handled. It is especially important after a skip-resolve
# with no code change to push, since nothing else re-triggers the review.
#
# Scope / assumptions: the review must be a re-runnable GitHub Actions workflow
# (the claude-code-action convention). It does NOT cover reviews delivered by a
# webhook bot with no Actions run. Repos whose review workflow has a different
# file name pass it explicitly (arg or env), so the script stays repo-agnostic.
#
# Usage: restart-review.sh [WORKFLOW]
#   WORKFLOW — workflow file name or workflow name (e.g. "claude-code-review.yml"
#              or "Claude Code Review"). Precedence: arg > $BABYSIT_REVIEW_WORKFLOW
#              > default "claude-code-review.yml".
#
# Behaviour: if no review is in progress for the current branch, it does nothing
# (exit 0). Otherwise it cancels every in-flight run of that workflow on the
# branch — so none can post stale findings — and reruns the most recent run
# against the current HEAD.

set -uo pipefail

command -v gh >/dev/null 2>&1 || { echo "restart-review: gh not found" >&2; exit 1; }

workflow="${1:-${BABYSIT_REVIEW_WORKFLOW:-claude-code-review.yml}}"
branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")"
[ -n "$branch" ] || { echo "restart-review: not on a git branch" >&2; exit 1; }

latest="$(gh run list --workflow="$workflow" --branch="$branch" --limit 1 \
  --json databaseId -q '.[0].databaseId' 2>/dev/null || echo "")"
if [ -z "$latest" ]; then
  echo "restart-review: no '$workflow' run found for branch '$branch' — pass the" >&2
  echo "                review workflow name as an argument if it differs." >&2
  exit 0
fi

in_flight="$(gh run list --workflow="$workflow" --branch="$branch" --limit 20 \
  --json databaseId,status \
  -q '.[] | select(.status=="in_progress" or .status=="queued" or .status=="requested" or .status=="waiting") | .databaseId' \
  2>/dev/null || echo "")"

if [ -z "$in_flight" ]; then
  echo "restart-review: no in-progress '$workflow' run for '$branch'; nothing to restart"
  exit 0
fi

while IFS= read -r id; do
  [ -n "$id" ] || continue
  echo "restart-review: cancelling in-flight run $id"
  gh run cancel "$id" >/dev/null 2>&1 || true
done <<EOF
$in_flight
EOF

# A run can only be rerun once it leaves the in-progress state, so wait for the
# cancellation of the run we are about to rerun to settle (bounded ~60s).
i=0
while [ "$i" -lt 30 ]; do
  st="$(gh run view "$latest" --json status -q .status 2>/dev/null || echo "")"
  [ "$st" = "completed" ] && break
  sleep 2
  i=$((i + 1))
done

echo "restart-review: rerunning review (run $latest, branch $branch)"
gh run rerun "$latest"
