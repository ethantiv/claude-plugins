---
name: visual-prompt
description: This skill should be used when the user asks to generate text-to-image prompts for AI image generators (Midjourney, DALL-E, Flux, Stable Diffusion, nano banana) — for artwork, posters, photography and key visuals, OR for artistic mockups of interfaces, websites, dashboards, landing pages and mobile screens. Also triggers on "design brief for AI", "image generation prompt", "UI mockup prompt", "interface concept", "website mockup prompt".
allowed-tools: Read, Glob, Agent, Workflow
---

# Visual Prompt — Orchestrator

Produces **three `.txt` files**, each holding one text-to-image prompt rooted in a different invented design philosophy. Two profiles available:

- **`art` profile** — artwork, posters, photography, key visuals, illustration, magazine spreads.
- **`ui` profile** — artistic mockups of interfaces (dashboards, landings, mobile screens, marketing sites, product UI). Same artistic register as `art`, applied to interface description.

Both profiles produce artistic prompts — the `ui` profile is **not** a wireframe spec. The output is a mockup-as-art-piece: an interface rendered as if photographed for a design publication or framed for a museum exhibit.

Explicit entry points (sibling skills in this plugin, slash-invocable):
- `visual-prompt-art` (`/visual-prompt-art <topic>`) → forces `art` profile.
- `visual-prompt-ui` (`/visual-prompt-ui <topic>`) → forces `ui` profile.
- Natural-language trigger → this orchestrator infers the profile (mentions of `dashboard`, `interface`, `landing page`, `mobile screen`, `website mockup`, `admin panel` → `ui`; otherwise `art`). If unsure, ask once before dispatching.

The orchestrator never writes a prompt itself. Three prompts are written by three independent subagents dispatched in parallel.

## Inputs

- **Topic given**: use it directly as the seed concept.
- **Topic missing**: ask one short question — what should the image be about? Wait for the answer.
- **Profile unclear**: ask which profile (`art` / `ui`).

## Orchestrator steps

### 1. Load the brief for the chosen profile

| Profile | Subagent brief | Example output |
|---|---|---|
| `art` | `${CLAUDE_PLUGIN_ROOT}/skills/visual-prompt/references/subagent-brief-art.md` | `${CLAUDE_PLUGIN_ROOT}/skills/visual-prompt/examples/example-art.txt` |
| `ui` | `${CLAUDE_PLUGIN_ROOT}/skills/visual-prompt/references/subagent-brief-ui.md` | `${CLAUDE_PLUGIN_ROOT}/skills/visual-prompt/examples/example-ui.txt` |

Read the corresponding brief once (Read tool). Paste it verbatim into each subagent call. Note the absolute path of the example file — each subagent gets that path as a format reference.

### 2. Reserve a free trio of file numbers

Filename pattern: `visual-prompt-<slug>-<n>.txt` (the profile is reflected inside the file, not in the name).

Glob the working directory for `visual-prompt-<slug>-*.txt`, then pick the first free trio from the matches:

```
slug    = topic lowercased, hyphenated, max 40 chars
n_start = 1
while ANY of (-n_start, -n_start+1, -n_start+2) already exists:
    n_start += 3
trio    = (n_start, n_start+1, n_start+2)
```

Reserve the whole trio at once before dispatching — don't let two subagents race to the same numbers.

### 3. Seed three contrasting directions

For each direction define:

- **Movement name** — 1–2 words, freshly invented (`Brutalist Joy`, `Ledger Calm`, `Chromatic Silence`, `Lacquered Stillness`).
- **Philosophy essence** — 2–3 sentences capturing the movement's logic. The subagent expands this into a full mental model.
- **Hidden reference** — one line, a niche conceptual thread tied to the topic.
- **Axis label** — short label naming the visual register.

The three directions MUST differ on multiple axes simultaneously. If two feel adjacent, replace one before dispatching.

### Contrast axes — `art` profile

| Axis | Poles |
|---|---|
| Medium | photographic / painterly / graphic poster |
| Density | maximal density / extreme negative space |
| Structure | architectural / organic / typographic |
| Color | monochromatic restraint / chromatic field / analog warmth |
| Scale | macro intimacy / monumental / diagrammatic distance |

### Contrast axes — `ui` profile

| Axis | Poles |
|---|---|
| Surface | data-dense admin / marketing landing / onboarding wizard / mobile feed / settings panel |
| Information density | dense data grid / sparse hero composition / mixed editorial |
| Tone | clinical restraint / warm editorial / brutalist editorial |
| Typography role | system-driven hierarchy / monospace gravitas / display-driven |
| Reference culture | Swiss-grid / Bloomberg-terminal / Memphis revival / Bauhaus-modernist / brutalist-web |

### Hidden reference — what it looks like in practice

The reference is felt by someone familiar with the source; everyone else sees a masterful composition. It is never named in the prompt.

`art` example, topic `cyberpunk samurai walking through neon Tokyo`:
- `Edo-period ukiyo-e sequencing`
- `Tokyo 1964 Olympic graphic system`
- `Hiroshi Sugimoto long-exposure stillness`

`ui` example, topic `operational dashboard for marine fleet`:
- `Bloomberg terminal monospace gravitas`
- `Swiss railway timetable typographic discipline`
- `1970s NASA mission-control panel layout`

Same topic, different cultural angle each time.

### 4. Dispatch three subagents in parallel

Drive the trio with the **Workflow tool** — invoking this skill is the opt-in to run it. If the Workflow tool is unavailable, use the `Agent` fallback below. Either way three is the cap — one subagent per direction, and no fourth agent to review, compare, or re-rank what the three returned. The refinement checklist inside the brief is the quality gate; the orchestrator only reports paths.

Each subagent prompt contains:

1. The verbatim content of the profile-appropriate brief (`subagent-brief-art.md` or `subagent-brief-ui.md`).
2. The seeded direction (movement, essence, hidden reference, axis).
3. The user's topic.
4. The assigned absolute file path: `<cwd>/visual-prompt-<slug>-<n>.txt`.
5. The absolute path of the profile example file (`example-art.txt` / `example-ui.txt`) — a format reference the subagent Reads before writing.

Each subagent writes exactly one file and replies with its absolute path.

Reference workflow script:

```javascript
export const meta = {
  name: 'visual-prompt-trio',
  description: 'Three subagents each write one text-to-image prompt file',
  phases: [{ title: 'Write' }],
}
// args: { brief, topic, examplePath, directions: [{ movement, essence, reference, axis, path }] }
const paths = await parallel(args.directions.map(d => () =>
  agent(
    `${args.brief}\n\nTopic: ${args.topic}\nMovement name: ${d.movement}\nPhilosophy essence: ${d.essence}\nHidden reference: ${d.reference}\nAxis label: ${d.axis}\nFile path: ${d.path}\nFormat example (Read it before writing): ${args.examplePath}`,
    { label: `write:${d.axis}`, phase: 'Write' })))
return paths.filter(Boolean)
```

**Fallback (no Workflow tool):** in **one** assistant message, call the `Agent` tool three times with `subagent_type: "general-purpose"` — one call per direction, same prompt contents. Identical logic, same three-agent cap.

### 5. Report back

After all three return, send **one** chat message with exactly three lines:

```
<absolute path 1> — <axis label 1>
<absolute path 2> — <axis label 2>
<absolute path 3> — <axis label 3>
```

No summary of the prompts. No usage hints. No offer to generate more.

## Common mistakes

- Writing the prompts yourself instead of dispatching subagents.
- Three flavours of the same idea instead of three genuinely contrasting directions.
- Mixing profiles inside one trio — all three directions stay on one profile.
- Using `art` axes for a `ui` topic or vice versa — each profile has its own contrast table.
- Skipping trio reservation, so two subagents collide on the same `-N` number.
- Dispatching subagents sequentially. They run in parallel — one Workflow call, or (fallback) three `Agent` calls in one assistant message.
- Naming the hidden reference inside the seed text the subagent will read — it's a conceptual thread, not a label to mention.
- Summarising prompts in the report-back. Three lines, that's it.
- Treating the `ui` profile as a wireframe spec or a UX deliverable. It produces an artistic prompt that describes a mockup as an art piece — same 80–140 word artistic register as `art`.
