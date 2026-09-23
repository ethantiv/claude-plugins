---
name: visual-prompt-art
description: This skill should be used when the user wants to "generate an artwork prompt", "poster prompt", "photography prompt", "key visual prompt", or explicitly invokes /visual-prompt-art — forcing the `art` profile of the visual-prompt orchestrator (artwork, posters, photography, illustration, key visuals). For interface mockups use visual-prompt-ui instead.
argument-hint: "<topic, e.g. cyberpunk samurai walking through neon Tokyo>"
allowed-tools: Read, Glob, Write, Agent, Workflow
---

## Agent compatibility

For the three independent directions, use Claude Code’s Workflow/Agent tools, Codex’s native `spawn_agent` and wait tools, or Copilot CLI’s `task` tool and its available completion/status mechanism. Start all three before waiting for completion. The Workflow/Agent examples below apply only to Claude Code. If delegation is unavailable, ask whether to produce the three directions sequentially and wait for the answer. Only with that agreement may the orchestrator write the prompts itself; never claim agents ran.

Use the host’s native tools: Claude Code tool names below describe capabilities, not requirements to call missing tools. Invoke this skill as `/visual-prompt:visual-prompt-art` in Claude Code, `$visual-prompt:visual-prompt-art` in Codex, or `/visual-prompt-art` in Copilot CLI (use its skill picker if names collide). Take arguments from the user’s message when `$ARGUMENTS` is unavailable. Resolve relative resource paths from this SKILL.md, never from the working directory. For optional helper skills, use the host’s skill tool when available, otherwise read the installed skill’s SKILL.md; continue without helpers that are not installed. Cross-plugin references use the invocation syntax of the current host.

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
   - Dispatch three subagents in parallel using the host-specific delegation above — each pasted the verbatim content of `subagent-brief-art.md` plus its seeded direction, the output language, assigned file path, and the absolute path of `examples/example-art.txt`.
   - Report back with exactly three lines: `<path> — <axis>`.

Use three independent subagents unless the user approved the sequential fallback described above.
