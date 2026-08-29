#!/usr/bin/env bash
# SessionStart hook: injects the full unslop catalog (SKILL.md + Polish patterns) so all agent prose is slop-free from the first reply.
# Stop flag: `touch .claude/unslop-off` (this project) or `touch ~/.claude/unslop-off` (global) disables it; delete the file to re-enable.
set -uo pipefail

[ -f "${CLAUDE_PROJECT_DIR:-.}/.claude/unslop-off" ] && exit 0
[ -f "${HOME:-}/.claude/unslop-off" ] && exit 0

ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"

cat <<'EOF'
UNSLOP MODE ACTIVE — apply the full unslop catalog below to ALL prose you produce this session (chat replies and written documents, Polish and English). The workflow and audit-mode sections apply only when the unslop skill is invoked on files; every pattern catalog applies to everything you write. Prefer deletion over substitution; keep the register; never invent facts. Disable: create the file .claude/unslop-off.

EOF
# ponytail: naive frontmatter strip (prints everything after the second ---), fine for these two files
awk 'f>1 {print} /^---$/ {f++}' "$ROOT/skills/unslop/SKILL.md"
echo
cat "$ROOT/skills/unslop/references/polish-patterns.md"
