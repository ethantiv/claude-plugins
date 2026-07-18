# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A Claude Code plugin marketplace (`ethantiv-plugins`). There is no build, lint, or package step — plugins are plain markdown skills plus a few helper scripts. The manifest [.claude-plugin/marketplace.json](.claude-plugin/marketplace.json) lists every plugin; each plugin lives in `plugins/<name>/` with its own `.claude-plugin/plugin.json` (name, version, description) and one or more skills in `skills/<skill-name>/SKILL.md`.

## Tests

Only two plugins have executable code, each with its own self-contained tests (no frameworks, no dependencies):

```bash
bash plugins/babysit-pr/scripts/test/test-auto-gate.sh   # gate logic in a throwaway git repo
python3 plugins/book-forge/scripts/tests/test_bible.py    # canon-wiki library E2E
python3 plugins/book-forge/scripts/tests/test_echo.py     # repetition detector
```

Run the relevant test after touching anything in `plugins/babysit-pr/scripts/` or `plugins/book-forge/scripts/`.

## Architecture

- **Skills are the product.** A plugin is essentially its `SKILL.md` files — prompt instructions with YAML frontmatter (`name`, `description`). Larger skills split detail into `references/*.md` next to the SKILL.md (progressive disclosure); skills reference plugin files via `${CLAUDE_PLUGIN_ROOT}`.
- **book-forge** is the largest plugin: a 12-stage Polish novel-writing pipeline. Its skills share a common foundation in `plugins/book-forge/shared/` (`biblia-spec.md` — the book-bible data contract, `polish-style.md` — the mandatory Polish-language editing rules, `roadmap.md`). `scripts/bible.py` is the deterministic CLI the skills call for canon state (`status`, `check-stage`, write-back); `scripts/echo.py` detects prose repetition. Pipeline state lives in the user's book directory under `.book-forge/` — the stage-by-stage file map is in [plugins/book-forge/README.md](plugins/book-forge/README.md).
- **babysit-pr** drives its loop through `scripts/pr-snapshot.sh` (collect PR state as JSON) and `scripts/auto-gate.sh` (decide whether a snapshot is positively green); the SKILL.md orchestrates them.
- Swarm-based skills (book-forge, roadmap, visual-prompt) target the **Workflow** tool and must keep a documented fallback to parallel Task/Agent calls.

## Conventions

- Adding a plugin means three places: `plugins/<name>/`, an entry in `.claude-plugin/marketplace.json`, and the table + install command in [README.md](README.md).
- Bump the `version` in a plugin's `plugin.json` when changing that plugin.
- Conventional commits scoped to the plugin: `feat(babysit-pr): ...`, `style: ...`.
- Write markdown prose as long single lines — never hard-wrap at a column width.
- Language: root README and most plugins are English; book-forge is deliberately Polish (skills, shared docs, generated artifacts). Match the language of the file you edit.
