---
name: visual-prompt-art
description: This skill should be used when the user wants to "generate an artwork prompt", "poster prompt", "photography prompt", "key visual prompt", or explicitly invokes /visual-prompt-art — forcing the `art` profile of the visual-prompt orchestrator (artwork, posters, photography, illustration, key visuals). For interface mockups use visual-prompt-ui instead.
argument-hint: "<topic, e.g. cyberpunk samurai walking through neon Tokyo>"
allowed-tools: Read, Glob, Agent, Workflow
---

# Visual Prompt — `art` profile entry point

Force the **`art` profile** of the shared visual-prompt orchestrator.

## Topic

`$ARGUMENTS` carries the topic. If it is empty, take the topic from the user's message that triggered this skill; if there is still no topic, ask one short question — what should the image be about? — and wait for the answer.

## Steps

Read the orchestrator and the `art` brief, then follow the orchestrator exactly:

1. Read `${CLAUDE_PLUGIN_ROOT}/skills/visual-prompt/SKILL.md` (the orchestrator).
2. Read `${CLAUDE_PLUGIN_ROOT}/skills/visual-prompt/references/subagent-brief-art.md`.
3. Run the orchestrator steps with the profile fixed to `art`:
   - Reserve a free trio of file numbers in the current working directory (Glob).
   - Seed three contrasting `art`-profile directions (movement, essence, hidden reference, axis), using the `art` contrast axes.
   - Dispatch three subagents in parallel — the Workflow tool, or (fallback) three `Agent` calls in one message — each pasted the verbatim content of `subagent-brief-art.md` plus its seeded direction, assigned file path, and the absolute path of `examples/example-art.txt`.
   - Report back with exactly three lines: `<path> — <axis>`.

Never write a prompt directly — the three prompts come from three independent subagents dispatched in parallel.
