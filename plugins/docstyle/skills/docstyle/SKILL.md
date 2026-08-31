---
name: docstyle
description: >-
  This skill should be used when the user asks to "apply the Google style guide", "check documentation style", "review this README for style", "fix the docs style", "make this follow docstyle", "edit per the developer documentation style guide", "popraw styl dokumentacji", "zastosuj przewodnik stylu Google", or invokes /docstyle — and also whenever developer documentation is being written or substantially edited in the session (README, tutorial, how-to, API reference, user guide), where its rules apply to the prose being produced. Covers audit-only requests: "audit the docs style", "report style issues without editing". Applies the Google developer documentation style guide (developers.google.com/style), shipped in full as local references. Not for removing AI-slop patterns, rewriting Polish into plain language, or prose that is not technical documentation (fiction, marketing copy, chat messages).
argument-hint: "<file path(s) to fix, or a directory> [--audit]"
allowed-tools: Read, Edit, Grep, Glob
---

# docstyle — apply the Google developer documentation style guide

Edit the document(s) in `$ARGUMENTS` **in place** so they follow the [Google developer documentation style guide](https://developers.google.com/style). Preserve the meaning, the facts, and the technical content; change wording, style, and formatting. The full guide (70 pages) is available locally under [references/guide/](references/guide/) — never answer a style question from memory when the relevant page is one `Read` away.

## Workflow

1. **Resolve targets.** If `$ARGUMENTS` contains the flag `--audit`, strip it and run in audit mode (see below) instead of editing. The rest of `$ARGUMENTS` may hold one or more file paths or a directory (expand it with `Glob` pattern `**/*.md`; other extensions inside a directory are skipped — name them explicitly to include them). Empty → if documentation writing is already in progress in the conversation, skip the workflow and apply the guide to all documentation prose produced from that point on; otherwise ask in one sentence which file to fix — don't guess.
2. **Read each file whole** (long files in sequential chunks). Apply the core rules below directly; they cover most findings.
3. **Consult the guide for anything beyond the core rules.** `Read` [references/index.md](references/index.md) — a topic → page map — and load only the pages matching the issues actually present in the text. For rulings on a specific term (for example "allowlist", "click", "e-mail", "please"), `Grep` [references/guide/word-list.md](references/guide/word-list.md) for the term instead of reading the whole page.
4. **Fix with surgical `Edit` calls** — sentence-level replacements, not a wholesale rewrite. The author's structure and voice stay; the style violations go.
5. **Summarize in chat** when done: per file, counts for the main rule categories touched and one or two before → after examples, each citing the guide page that motivated it. Write the summary in the conversation language.

Hard rules:

- **Never change technical meaning.** Command names, flags, API signatures, outputs, and version numbers stay exactly as written. If a technical claim looks wrong, flag it in the summary instead of editing it.
- **Don't touch:** code blocks and inline code (except prose inside code comments when the user asked for it), URLs, quoted material, proper names, YAML frontmatter keys, data values in tables.
- **Language scope.** The guide is written for English. Apply the full rule set to English prose. To prose in other languages apply only the structural rules (second person, active voice, present tense, conditions before instructions, list and heading discipline, descriptive links, no future promises, no excessive claims) — never anglicize spelling, punctuation, or word choice.
- **Respect the project's existing conventions** where the guide itself defers to them (see `guide/index.md` on precedence): an established API's naming, a repo's heading style used consistently. Note the conflict in the summary rather than churning the whole file.

## Core rules

The always-apply subset; the index maps everything else.

**Tone and content** — conversational but not frivolous; no marketing superlatives ("powerful", "blazing fast", "simple", "easy", "just"); no pre-announcing future features; no anthropomorphism ("the server wants"); descriptive link text, never "click here"; define jargon on first use; write for a global audience (short sentences, no idioms).

**Language and grammar** — second person ("you", not "we"/"the user"); active voice; present tense (no "will" for behavior); conditions before instructions ("If X, do Y"); contractions are fine; standard American spelling.

**Formatting and organization** — sentence case for titles and headings; numbered lists for sequences, bulleted for unordered sets; procedure steps start with the imperative verb; serial comma; code font for code, filenames, commands, and literal values; bold for UI element names; unambiguous dates (spell out the month); one idea per paragraph, point first.

## Audit mode

With `--audit`, produce a report instead of editing. For each file list the findings grouped by guide topic, each with: severity (**high** — misleads or blocks the reader: ambiguous instructions, future promises, wrong person/tense in procedures; **medium** — clear guide violations: title case headings, "click here" links, passive procedures, superlatives; **low** — polish: serial commas, contractions, number formatting), the location (`file:line`), a quoted fragment, the proposed fix, and the guide page it comes from. End with a per-file tally by severity. Make no edits in audit mode.

## Session-wide style

The plugin's SessionStart hook injects a condensed rule set (`${CLAUDE_PLUGIN_ROOT}/hooks/chat-style.md`) so all session prose follows the guide without invoking this skill. When this skill is active it supersedes the hook's condensed rules. Disable the hook by creating `.claude/docstyle-off` in the project or `~/.claude/docstyle-off` globally.

## Scope boundaries

- Removing AI-writing patterns (negative parallelisms, fake-profound kickers, AI vocabulary) is a different job: if the unslop plugin is installed, use `/unslop:unslop` for it.
- Deliberately simplifying Polish officialese into plain language: if the unslop plugin is installed, that is `/unslop:plain`.
- This skill styles developer documentation; leave fiction, marketing copy, and conversational text alone unless the user explicitly asks.
