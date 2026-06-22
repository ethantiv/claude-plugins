---
name: visual-prompt-ui
description: This skill should be used when the user wants to "generate a UI mockup prompt", "dashboard mockup prompt", "landing page prompt", "mobile screen prompt", "website mockup prompt", or explicitly invokes /visual-prompt-ui — forcing the `ui` profile of the visual-prompt orchestrator (artistic interface mockups: dashboards, landings, mobile screens, marketing sites, product UI). For artwork, posters or photography use visual-prompt-art instead.
argument-hint: "<interface description, e.g. operational dashboard for marine fleet monitoring>"
allowed-tools: Read, Bash, Agent
---

# Visual Prompt — `ui` profile entry point

Force the **`ui` profile** of the shared visual-prompt orchestrator for the interface described by the user (the text after the command, or the request that triggered this skill).

Read the orchestrator and the `ui` brief, then follow the orchestrator exactly:

1. Read `${CLAUDE_PLUGIN_ROOT}/skills/visual-prompt/orchestrator.md`.
2. Read `${CLAUDE_PLUGIN_ROOT}/skills/visual-prompt/subagent-brief-ui.md`.
3. Run the orchestrator steps in `SKILL.md` with the profile fixed to `ui`:
   - Reserve a free trio of file numbers in the current working directory.
   - Seed three contrasting `ui`-profile directions (movement, essence, hidden reference, axis), using the `ui` contrast axes.
   - Dispatch three subagents in one message, each pasted the verbatim content of `subagent-brief-ui.md` plus its seeded direction and assigned file path.
   - Report back with exactly three lines: `<path> — <axis>`.

The deliverable is an artistic prompt for a text-to-image generator describing a **mockup-as-art-piece** — not a wireframe spec, not a flat product screenshot, not a UX deliverable.

Never write a prompt directly — the three prompts come from three independent subagents dispatched in parallel.

If no interface description was supplied, ask one short question and wait for the answer.
