---
name: visual-prompt-ui
description: >-
  This skill should be used when the user wants to "generate a UI mockup prompt", "dashboard mockup prompt", "landing page prompt", "mobile screen prompt", "website mockup prompt", or explicitly invokes /visual-prompt-ui — forcing the `ui` profile of the visual-prompt orchestrator (artistic interface mockups: dashboards, landings, mobile screens, marketing sites, product UI). For artwork, posters or photography use visual-prompt-art instead.
argument-hint: "<interface description, e.g. operational dashboard for marine fleet monitoring>"
allowed-tools: Read, Glob, Agent, Workflow
---

## Agent compatibility

In Codex use its native `spawn_agent` and wait tools for the three independent directions; the Workflow/Agent examples below are Claude-specific equivalents. If delegation is unavailable, report that limitation and ask whether to produce the three directions sequentially; do not claim agents ran.

Use the host’s native reading, search, editing and web tools; Claude tool names below describe capabilities, not requirements to call missing tools. In Codex, invoke this skill as `$visual-prompt:visual-prompt-ui`; take arguments from the user’s message when `$ARGUMENTS` is unavailable. Cross-plugin slash references mean the corresponding `$plugin:skill` in Codex, only when that skill is installed. Resolve relative resource paths from this SKILL.md, never from the working directory.


# Visual Prompt — `ui` profile entry point

Force the **`ui` profile** of the shared visual-prompt orchestrator.

## Interface description

`$ARGUMENTS` carries the interface description. If it is empty, take the description from the user's message that triggered this skill; if there is still none, ask one short question — what interface should the mockup show? — and wait for the answer.

## Steps

Read the orchestrator and the `ui` brief, then follow the orchestrator exactly:

1. Read `../visual-prompt/SKILL.md` (the orchestrator).
2. Read `../visual-prompt/references/subagent-brief-ui.md`.
3. Run the orchestrator steps with the profile fixed to `ui`:
   - Determine the output language (the session's configured response language, otherwise the language of the user's request).
   - Reserve a free trio of file numbers in the current working directory (Glob).
   - Seed three contrasting `ui`-profile directions (movement, essence, hidden reference, axis), using the `ui` contrast axes.
   - Dispatch three subagents in parallel — the Workflow tool, or (fallback) three `Agent` calls in one message — each pasted the verbatim content of `subagent-brief-ui.md` plus its seeded direction, the output language, assigned file path, and the absolute path of `examples/example-ui.txt`.
   - Report back with exactly three lines: `<path> — <axis>`.

The deliverable is an artistic prompt for a text-to-image generator describing a **mockup-as-art-piece** — not a wireframe spec, not a flat product screenshot, not a UX deliverable.

Never write a prompt directly — the three prompts come from three independent subagents dispatched in parallel.
