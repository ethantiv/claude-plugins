# Repository Guidelines

## Project structure and module organization

This repository distributes independent agent plugins under `plugins/<plugin-name>/`. Most behavior lives in `skills/<skill-name>/SKILL.md`, with YAML frontmatter and Markdown instructions. Supporting material belongs in adjacent `references/`, `assets/`, or `examples/` directories.

Claude Code manifests live in each plugin's `.claude-plugin/plugin.json`. Plugins supporting Codex and Copilot also have `.codex-plugin/plugin.json` and root `plugin.json` manifests. Marketplace catalogs live in `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json`.

Executable helpers live in `plugins/book-forge/scripts/` (Python) and `plugins/babysit-pr/scripts/` (Bash). Their tests live in `scripts/tests/` and `scripts/test/`, respectively.

## Build, test, and development commands

Run these commands from the repository root. There is no root build step or package installation requirement.

- `python3 plugins/book-forge/scripts/tests/test_bible.py`: check canon storage and round-trip behavior.
- `python3 plugins/book-forge/scripts/tests/test_echo.py`: check repetition detection using synthetic scenes.
- `bash plugins/babysit-pr/scripts/test/test-auto-gate.sh`: check merge eligibility decisions.
- `bash plugins/babysit-pr/scripts/test/test-pr-snapshot.sh`: check review pagination and snapshot assembly with a stubbed GitHub CLI.
- `python3 -m json.tool .claude-plugin/marketplace.json >/dev/null`: validate catalog JSON syntax; repeat for changed manifests.

Python helpers use the standard library. Bash checks require Git and `jq`. For installation and host-specific invocation, follow `README.md`.

## Coding style and naming conventions

Use lowercase, hyphenated plugin and skill directory names, and retain the uppercase `SKILL.md` filename. Match existing indentation: two spaces for JSON and Bash blocks, four for Python. Use snake_case for Python functions and variables.

Write actionable skill instructions, preserve the intended language, and resolve supporting paths relative to the skill directory. No repository-wide formatter or linter is configured.

## Testing guidelines

Tests are standalone self-checks; there is no external test framework or configured coverage threshold. Extend `test_*.py` or `test-*.sh` checks when changing helper behavior. Keep fixtures isolated from real projects. For skill changes, check frontmatter, referenced paths, and invocation in the affected hosts.

## Commit and pull request guidelines

Follow the existing Conventional Commit style: `feat(teach-me): ...`, `fix: ...`, or `refactor(visual-prompt): ...`. Keep commits focused.

In pull requests, explain the behavior change, affected plugins and hosts, and validation performed. Link relevant issues and include screenshots for changed HTML assets. Keep versions consistent across a plugin's manifests and update catalogs and README entries when availability changes.
