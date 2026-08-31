#!/usr/bin/env bash
# SessionStart hook: injects the condensed Google developer documentation style rules so chat replies and written prose follow the guide from the first message.
# Stop flag: `touch .claude/docstyle-off` (this project) or `touch ~/.claude/docstyle-off` (global) disables it; delete the file to re-enable.
set -uo pipefail

[ -f "${CLAUDE_PROJECT_DIR:-.}/.claude/docstyle-off" ] && exit 0
[ -f "${HOME:-}/.claude/docstyle-off" ] && exit 0

ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"

cat "$ROOT/hooks/chat-style.md"
