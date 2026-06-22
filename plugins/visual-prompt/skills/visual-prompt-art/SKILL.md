---
name: visual-prompt-art
description: This skill should be used when the user wants to "generate an artwork prompt", "poster prompt", "photography prompt", "key visual prompt", or explicitly invokes /visual-prompt-art — forcing the `art` profile of the visual-prompt orchestrator (artwork, posters, photography, illustration, key visuals). For interface mockups use visual-prompt-ui instead.
argument-hint: "<topic, e.g. cyberpunk samurai walking through neon Tokyo>"
allowed-tools: Read, Bash, Agent
---

# Visual Prompt — `art` profile entry point

Force the **`art` profile** of the shared visual-prompt orchestrator for the topic supplied by the user (the text after the command, or the request that triggered this skill).

Read the orchestrator and the `art` brief, then follow the orchestrator exactly:

1. Read `${CLAUDE_PLUGIN_ROOT}/skills/visual-prompt/orchestrator.md`.
2. Read `${CLAUDE_PLUGIN_ROOT}/skills/visual-prompt/subagent-brief-art.md`.
3. Run the orchestrator steps in `SKILL.md` with the profile fixed to `art`:
   - Reserve a free trio of file numbers in the current working directory.
   - Seed three contrasting `art`-profile directions (movement, essence, hidden reference, axis), using the `art` contrast axes.
   - Dispatch three subagents in one message, each pasted the verbatim content of `subagent-brief-art.md` plus its seeded direction and assigned file path.
   - Report back with exactly three lines: `<path> — <axis>`.

Never write a prompt directly — the three prompts come from three independent subagents dispatched in parallel.

If no topic was supplied, ask one short question and wait for the answer.
