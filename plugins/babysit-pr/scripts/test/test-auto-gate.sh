#!/usr/bin/env bash
#
# Self-check for auto-gate.sh: runs it inside a throwaway git repo and asserts
# only a positively-green snapshot reads as clean.

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
pending_snapshot='{"status":"ok","number":42,"mergeStateStatus":"CLEAN","has_conflicts":false,"failing_checks":[],"pending_checks":[{"name":"ci"}],"review_threads":[],"changes_requested":[]}'

# 1: a single clean pass is enough to merge
out="$(printf '%s' "$clean_snapshot" | bash "$gate")"
assert "clean" "$(field "$out" clean)" "true"
assert "clean sha" "$(field "$out" sha)" "$(git rev-parse HEAD)"

# 2: mergeStateStatus != CLEAN -> not clean
assert "blocked not clean" "$(field "$(printf '%s' "$dirty_snapshot" | bash "$gate")" clean)" "false"

# 3: open review thread despite CLEAN -> not clean
assert "open thread not clean" "$(field "$(printf '%s' "$thread_snapshot" | bash "$gate")" clean)" "false"

# 4: pending check despite CLEAN -> not clean
assert "pending check not clean" "$(field "$(printf '%s' "$pending_snapshot" | bash "$gate")" clean)" "false"

exit $fail
