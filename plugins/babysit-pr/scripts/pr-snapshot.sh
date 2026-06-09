#!/usr/bin/env bash
#
# Gather the full state of one PR as a single JSON object on stdout.
#
# Usage: pr-snapshot.sh [PR_NUMBER]
#   PR_NUMBER — optional. When omitted, the open PR for the current branch is used.
#
# Stdout: one JSON object. Always check ".status" first:
#   ok               — PR is open; act on the payload
#   no_pr            — no open PR for this branch (create one first, then retry)
#   on_default_branch— on the repo default branch with no PR (check out a feature branch)
#   merged | closed  — PR is finished; stop babysitting
#   gh_missing       — gh CLI not installed
#   gh_error         — gh call failed (see ".error")
#
# Payload fields when status == ok:
#   number, url, headRefName, baseRefName, state
#   mergeable           — MERGEABLE | CONFLICTING | UNKNOWN
#   mergeStateStatus    — CLEAN | DIRTY | BLOCKED | BEHIND | ...
#   has_conflicts       — bool (mergeable == CONFLICTING or mergeStateStatus == DIRTY)
#   failing_checks[]    — {name, conclusion, url}  (CI checks that failed)
#   pending_checks[]    — {name}                   (CI checks still running)
#   review_threads[]    — {thread_id, user, path, line, body, created_at, is_outdated}
#                          (UNRESOLVED inline review threads only; thread_id feeds resolveReviewThread)
#   changes_requested[] — {user, body, submitted_at}            (reviews requesting changes)
#   unpushed_local_commits — bool (local HEAD ahead of its upstream)
#
# The script never mutates anything; it only reads.

set -uo pipefail

err() { jq -n --arg s "$1" --arg e "$2" '{status:$s, error:$e}'; exit 0; }

command -v gh  >/dev/null 2>&1 || { jq -n '{status:"gh_missing"}'; exit 0; }
command -v jq  >/dev/null 2>&1 || { printf '{"status":"gh_error","error":"jq not found"}\n'; exit 0; }

pr_number="${1:-}"

current_branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")"
default_branch="$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name 2>/dev/null || echo "")"

if [[ -z "$pr_number" && -n "$default_branch" && "$current_branch" == "$default_branch" ]]; then
  jq -n '{status:"on_default_branch"}'; exit 0
fi

fields="number,state,url,headRefName,baseRefName,mergeable,mergeStateStatus,statusCheckRollup"
if [[ -n "$pr_number" ]]; then
  pr_json="$(gh pr view "$pr_number" --json "$fields" 2>pr_err.tmp)"
else
  pr_json="$(gh pr view --json "$fields" 2>pr_err.tmp)"
fi
gh_rc=$?
gh_msg="$(cat pr_err.tmp 2>/dev/null)"; rm -f pr_err.tmp

if [[ $gh_rc -ne 0 || -z "$pr_json" ]]; then
  if printf '%s' "$gh_msg" | grep -qi "no .*pull request\|no pull requests\|Could not resolve to a PullRequest\|no open"; then
    jq -n '{status:"no_pr"}'; exit 0
  fi
  err "gh_error" "${gh_msg:-gh pr view failed}"
fi

state="$(printf '%s' "$pr_json" | jq -r .state)"
case "$state" in
  MERGED) jq -n --argjson pr "$pr_json" '{status:"merged", number:$pr.number, url:$pr.url}'; exit 0 ;;
  CLOSED) jq -n --argjson pr "$pr_json" '{status:"closed", number:$pr.number, url:$pr.url}'; exit 0 ;;
esac

number="$(printf '%s' "$pr_json" | jq -r .number)"
slug="$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")"
owner="${slug%%/*}"; name="${slug##*/}"

threads_json="[]"; reviews_json="[]"
if [[ -n "$slug" ]]; then
  # shellcheck disable=SC2016  # $owner/$name/$number are GraphQL variables, bound via -f/-F below
  gql='query($owner:String!,$name:String!,$number:Int!){
    repository(owner:$owner,name:$name){
      pullRequest(number:$number){
        reviewThreads(first:100){nodes{
          id isResolved isOutdated
          comments(first:1){nodes{ body path line originalLine author{login} createdAt }}
        }}
      }
    }
  }'
  threads_resp="$(gh api graphql -f query="$gql" -f owner="$owner" -f name="$name" -F number="$number" 2>/dev/null || echo '{}')"
  threads_json="$(printf '%s' "$threads_resp" | jq '[.data.repository.pullRequest.reviewThreads.nodes[]?]' 2>/dev/null || echo "[]")"
  reviews_json="$(gh api --paginate "repos/$slug/pulls/$number/reviews" 2>/dev/null || echo "[]")"
fi
[[ -z "$threads_json" ]] && threads_json="[]"
[[ -z "$reviews_json" ]] && reviews_json="[]"

unpushed=false
if git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' >/dev/null 2>&1; then
  ahead="$(git rev-list --count '@{upstream}..HEAD' 2>/dev/null || echo 0)"
  [[ "${ahead:-0}" -gt 0 ]] && unpushed=true
fi

jq -n \
  --argjson pr "$pr_json" \
  --argjson threads "$threads_json" \
  --argjson reviews "$reviews_json" \
  --argjson unpushed "$unpushed" '
  ($pr.statusCheckRollup // []) as $checks
  | {
      status: "ok",
      number: $pr.number,
      url: $pr.url,
      headRefName: $pr.headRefName,
      baseRefName: $pr.baseRefName,
      state: $pr.state,
      mergeable: $pr.mergeable,
      mergeStateStatus: $pr.mergeStateStatus,
      has_conflicts: (($pr.mergeable == "CONFLICTING") or ($pr.mergeStateStatus == "DIRTY")),
      failing_checks: [
        $checks[]
        | select(
            (.conclusion // "") as $c
            | (.state // "") as $s
            | (["FAILURE","TIMED_OUT","CANCELLED","ACTION_REQUIRED","STARTUP_FAILURE","ERROR"] | index($c))
              or (["FAILURE","ERROR"] | index($s))
          )
        | {name: (.name // .context // "check"),
           conclusion: (.conclusion // .state),
           url: (.detailsUrl // .targetUrl // null)}
      ],
      pending_checks: [
        $checks[]
        | select(((.status // "") | IN("IN_PROGRESS","QUEUED","PENDING")) or ((.state // "") == "PENDING"))
        | {name: (.name // .context // "check")}
      ],
      review_threads: [
        $threads[]
        | select(.isResolved == false)
        | (.comments.nodes[0] // {}) as $c
        | {thread_id: .id, is_outdated: .isOutdated,
           user: ($c.author.login), path: ($c.path), line: ($c.line // $c.originalLine),
           body: ($c.body), created_at: ($c.createdAt)}
      ] | sort_by(.created_at),
      changes_requested: [
        $reviews[]
        | select(.state == "CHANGES_REQUESTED")
        | {user: .user.login, body: .body, submitted_at: .submitted_at}
      ],
      unpushed_local_commits: $unpushed
    }'
