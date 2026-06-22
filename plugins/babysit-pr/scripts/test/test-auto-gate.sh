#!/usr/bin/env bash
#
# Self-check for auto-gate.sh: runs it inside a throwaway git repo and asserts
# the consecutive-clean counter behaves across passes.

set -uo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
gate="$script_dir/../auto-gate.sh"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cd "$tmp" || exit 1

git init -q
git config user.email test@test.local
git config user.name test
git commit -q --allow-empty -m init

fail=0
field() { printf '%s' "$1" | jq -r ".$2"; }
assert() {
  local label="$1" got="$2" want="$3"
  if [ "$got" = "$want" ]; then
    echo "ok   - $label"
  else
    echo "FAIL - $label: got '$got' want '$want'" >&2
    fail=1
  fi
}

clean_snapshot='{"status":"ok","number":42,"mergeStateStatus":"CLEAN","has_conflicts":false,"failing_checks":[],"pending_checks":[],"review_threads":[],"changes_requested":[]}'
dirty_snapshot='{"status":"ok","number":42,"mergeStateStatus":"BLOCKED","has_conflicts":false,"failing_checks":[],"pending_checks":[],"review_threads":[],"changes_requested":[]}'
thread_snapshot='{"status":"ok","number":42,"mergeStateStatus":"CLEAN","has_conflicts":false,"failing_checks":[],"pending_checks":[],"review_threads":[{"thread_id":"x"}],"changes_requested":[]}'

# 1: first clean pass -> consecutive 1, no merge
out="$(printf '%s' "$clean_snapshot" | bash "$gate")"
assert "pass1 consecutive" "$(field "$out" consecutive)" "1"
assert "pass1 should_merge" "$(field "$out" should_merge)" "false"

# 2: second clean pass, same sha -> consecutive 2, merge
out="$(printf '%s' "$clean_snapshot" | bash "$gate")"
assert "pass2 consecutive" "$(field "$out" consecutive)" "2"
assert "pass2 should_merge" "$(field "$out" should_merge)" "true"

# 3: not-clean (mergeStateStatus != CLEAN) -> reset to 0
out="$(printf '%s' "$dirty_snapshot" | bash "$gate")"
assert "blocked resets" "$(field "$out" consecutive)" "0"
assert "blocked no merge" "$(field "$out" should_merge)" "false"

# 3b: open review thread despite CLEAN -> not clean
out="$(printf '%s' "$thread_snapshot" | bash "$gate")"
assert "open thread not clean" "$(field "$out" clean)" "false"
assert "open thread resets" "$(field "$out" consecutive)" "0"

# 4: rebuild streak to 1, then a new commit (sha change) keeps it at 1, not 2
printf '%s' "$clean_snapshot" | bash "$gate" >/dev/null
git commit -q --allow-empty -m next
out="$(printf '%s' "$clean_snapshot" | bash "$gate")"
assert "new sha restarts at 1" "$(field "$out" consecutive)" "1"

# 5: corrupt state file -> treated as count 0, no crash
git_dir="$(git rev-parse --absolute-git-dir)"
printf 'not json' > "$git_dir/babysit-pr-42.json"
out="$(printf '%s' "$clean_snapshot" | bash "$gate")"
assert "corrupt state -> 1" "$(field "$out" consecutive)" "1"

exit $fail
