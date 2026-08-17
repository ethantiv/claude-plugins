#!/usr/bin/env bash
#
# Self-check for pr-snapshot.sh: runs it inside a throwaway git repo with a
# stubbed `gh` on PATH and asserts the jq assembly logic:
#   - paginated review pages (concatenated arrays) merge into one array
#   - changes_requested keeps only reviewers whose LATEST review requests
#     changes (a later APPROVED supersedes; a later COMMENTED does not)

set -uo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
snapshot="$script_dir/../pr-snapshot.sh"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cd "$tmp" || exit 1

git init -q -b feature/test
git config user.email test@test.local
git config user.name test
git commit -q --allow-empty -m init

mkdir -p "$tmp/fixtures" "$tmp/bin"

cat > "$tmp/fixtures/pr.json" <<'EOF'
{"number":42,"state":"OPEN","url":"https://example.test/pr/42",
 "headRefName":"feature/test","baseRefName":"main",
 "mergeable":"MERGEABLE","mergeStateStatus":"CLEAN","statusCheckRollup":[]}
EOF

# threads: one resolved (filtered out), one unresolved (kept)
cat > "$tmp/fixtures/threads.json" <<'EOF'
{"data":{"repository":{"pullRequest":{"reviewThreads":{"nodes":[
  {"id":"T_resolved","isResolved":true,"isOutdated":false,
   "comments":{"nodes":[{"body":"done","path":"a.txt","line":1,"originalLine":1,
     "author":{"login":"alice"},"createdAt":"2026-01-01T00:00:00Z"}]}},
  {"id":"T_open","isResolved":false,"isOutdated":false,
   "comments":{"nodes":[{"body":"fix this","path":"b.txt","line":2,"originalLine":2,
     "author":{"login":"bob"},"createdAt":"2026-01-02T00:00:00Z"}]}}
]}}}}}
EOF

# two pages as `gh api --paginate` emits them: concatenated JSON arrays.
# alice: CHANGES_REQUESTED then APPROVED  -> superseded, excluded
# bob:   CHANGES_REQUESTED (page 2 only)  -> included (proves pagination merge)
# carol: CHANGES_REQUESTED then COMMENTED -> COMMENTED does not supersede, included
cat > "$tmp/fixtures/reviews_pages.json" <<'EOF'
[{"user":{"login":"alice"},"state":"CHANGES_REQUESTED","body":"a1","submitted_at":"2026-01-01T00:00:00Z"},
 {"user":{"login":"carol"},"state":"CHANGES_REQUESTED","body":"c1","submitted_at":"2026-01-01T01:00:00Z"},
 {"user":{"login":"alice"},"state":"APPROVED","body":"a2","submitted_at":"2026-01-02T00:00:00Z"}]
[{"user":{"login":"bob"},"state":"CHANGES_REQUESTED","body":"b1","submitted_at":"2026-01-03T00:00:00Z"},
 {"user":{"login":"carol"},"state":"COMMENTED","body":"c2","submitted_at":"2026-01-03T01:00:00Z"}]
EOF

cat > "$tmp/bin/gh" <<EOF
#!/usr/bin/env bash
case "\$*" in
  *defaultBranchRef*) echo "main" ;;
  *nameWithOwner*)    echo "o/r" ;;
  "pr view"*)         cat "$tmp/fixtures/pr.json" ;;
  *graphql*)          cat "$tmp/fixtures/threads.json" ;;
  *--paginate*)       cat "$tmp/fixtures/reviews_pages.json" ;;
  *)                  exit 1 ;;
esac
EOF
chmod +x "$tmp/bin/gh"
export PATH="$tmp/bin:$PATH"

fail=0
field() { printf '%s' "$1" | jq -r "$2"; }
assert() {
  local label="$1" got="$2" want="$3"
  if [ "$got" = "$want" ]; then
    echo "ok   - $label"
  else
    echo "FAIL - $label: got '$got' want '$want'" >&2
    fail=1
  fi
}

out="$(bash "$snapshot")"

assert "status ok"                 "$(field "$out" .status)" "ok"
assert "resolved thread filtered"  "$(field "$out" '.review_threads | length')" "1"
assert "open thread kept"          "$(field "$out" '.review_threads[0].thread_id')" "T_open"
assert "changes_requested count"   "$(field "$out" '.changes_requested | length')" "2"
assert "superseded alice excluded" "$(field "$out" '[.changes_requested[].user] | index("alice")')" "null"
assert "paginated bob included"    "$(field "$out" '[.changes_requested[].user] | index("bob") != null')" "true"
assert "commented carol included"  "$(field "$out" '[.changes_requested[].user] | index("carol") != null')" "true"

exit "$fail"
