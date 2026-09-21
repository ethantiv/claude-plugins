---
name: visual-prompt-art
description: This skill should be used when the user wants to "generate an artwork prompt", "poster prompt", "photography prompt", "key visual prompt", or explicitly invokes /visual-prompt-art — forcing the `art` profile of the visual-prompt orchestrator (artwork, posters, photography, illustration, key visuals). For interface mockups use visual-prompt-ui instead.
argument-hint: "<topic, e.g. cyberpunk samurai walking through neon Tokyo>"
allowed-tools: Read, Glob, Agent, Workflow
---

## Agent compatibility

In Codex use its native `spawn_agent` and wait tools for the three independent directions; the Workflow/Agent examples below are Claude-specific equivalents. If delegation is unavailable, report that limitation and ask whether to produce the three directions sequentially; do not claim agents ran.

Use the host’s native reading, search, editing and web tools; Claude tool names below describe capabilities, not requirements to call missing tools. In Codex, invoke this skill as `$visual-prompt:visual-prompt-art`; take arguments from the user’s message when `$ARGUMENTS` is unavailable. Cross-plugin slash references mean the corresponding `$plugin:skill` in Codex, only when that skill is installed. Resolve relative resource paths from this SKILL.md, never from the working directory.


# Visual Prompt — `art` profile entry point

Force the **`art` profile** of the shared visual-prompt orchestrator.

## Topic

`$ARGUMENTS` carries the topic. If it is empty, take the topic from the user's message that triggered this skill; if there is still no topic, ask one short question — what should the image be about? — and wait for the answer.

## Steps

Read the orchestrator and the `art` brief, then follow the orchestrator exactly:

1. Read `../visual-prompt/SKILL.md` (the orchestrator).
2. Read `../visual-prompt/references/subagent-brief-art.md`.
3. Run the orchestrator steps with the profile fixed to `art`:
   - Determine the output language (the session's configured response language, otherwise the language of the user's request).
   - Reserve a free trio of file numbers in the current working directory (Glob).
   - Seed three contrasting `art`-profile directions (movement, essence, hidden reference, axis), using the `art` contrast axes.
   - Dispatch three subagents in parallel — the Workflow tool, or (fallback) three `Agent` calls in one message — each pasted the verbatim content of `subagent-brief-art.md` plus its seeded direction, the output language, assigned file path, and the absolute path of `examples/example-art.txt`.
   - Report back with exactly three lines: `<path> — <axis>`.

Never write a prompt directly — the three prompts come from three independent subagents dispatched in parallel.
