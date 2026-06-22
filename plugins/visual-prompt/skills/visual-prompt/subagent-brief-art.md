# Subagent brief — write one text-to-image prompt

You are one of three subagents writing one text-to-image prompt rooted in a distinct design philosophy. The orchestrator has handed you:

- **Topic** — the subject matter.
- **Movement name** — 1–2 words.
- **Philosophy essence** — 2–3 sentences.
- **Hidden reference** — one-line niche conceptual thread.
- **Axis label** — short visual register.
- **File path** — absolute path where the output goes.

Your job: expand the philosophy mentally, write one prompt that expresses it, save one `.txt` file. Reply with the absolute path.

Never write the philosophy as prose to the file. The philosophy stays in your head; only the prompt and its short headers reach the file.

## Step 1 — Expand the philosophy (mental model only)

Build a 4–6 paragraph mental model of the movement covering:

- Space and form
- Color and material
- Scale and rhythm
- Composition and balance
- Visual hierarchy

The model exists to make the prompt coherent — rooted in a real aesthetic worldview, not a string of generic adjectives. Do not write it down.

The rendered image must look as if it took countless hours and came from someone at the top of their field. Carry phrases such as `meticulously crafted`, `painstaking attention`, `master-level execution`, `every alignment the work of countless refinements` into the prompt itself, woven in — not stickered on.

Leave room for the generator's interpretive choices at a high level of craft. Set the aesthetic; don't lock down every pixel.

## Step 2 — Write the prompt

### Rules

| Aspect | Rule |
|---|---|
| Language | Natural descriptive English. Same string must work in Midjourney, nano banana, DALL-E, Flux, Stable Diffusion without edits. |
| Forbidden syntax | No tool-specific flags (`--ar`, `--v`, `--style`), no parentheses-weight syntax, no `::`, no weights, no negative prompts, no emoji, no hashtags, no markdown, no code fences. |
| Length | 80–140 words. |
| Order | subject → composition & spatial logic → lighting & atmosphere → palette & material → texture & craft → typography (if any) → mood & subtle reference. |
| Form | Comma-separated phrases, not full prose paragraphs. |
| Forbidden words | `masterpiece`, `trending on artstation`, `4k`, `8k`, `ultra detailed`, `hyperdetailed`, `epic`, `cinematic lighting`, `award-winning`, `beautiful`, `stunning`, `amazing`, `photorealistic ultra detailed`. |

### What must be present

- The user's topic, unmistakably anchored.
- The aesthetic movement embodied through concrete sensory detail — materials, light qualities, spatial relations, surface treatments.
- The hidden reference woven in invisibly. Think jazz musician quoting another song: those who know catch it, everyone else just hears the music.
- Craftsmanship vocabulary as integrated phrases, not stickers.

### Typography inside the rendered image

Minimal and visual-first. Most of the time thin and restrained; context may warrant bolder typographic gestures (a punk venue poster vs. a minimalist ceramics identity), but never paragraphs.

Always instruct the generator: nothing falls off the frame, nothing overlaps, every element contained with proper margins and breathing room. This containment is non-negotiable for professional execution.

## Step 3 — Refinement pass

Re-read the prompt as if the user already said: *"It isn't perfect enough. It must be pristine."*

Don't add adjectives or flourishes. Tighten word choice, strengthen spatial verbs, remove anything generic. Make the existing composition more cohesive with the philosophy.

Verify before saving:

- [ ] Topic is unmistakable in the prompt.
- [ ] Philosophy and hidden reference run through every part.
- [ ] Prompt stays on its assigned axis.
- [ ] No tool-specific syntax, no quality boosters, no forbidden words.
- [ ] Sensory detail is concrete (materials, light, spatial geometry).
- [ ] Craftsmanship vocabulary woven in, not tacked on.
- [ ] Length is 80–140 words.

If any check fails, rewrite. Save once.

## Step 4 — Save the file

UTF-8 plain text. No markdown, no code fences. Exact layout (no extra lines, no footer):

```
TOPIC: <user's topic, single line>
PHILOSOPHY: <movement name> — <one-sentence essence>
HIDDEN REFERENCE: <one-line subtle thread>
AXIS: <axis label>

<prompt text>
```

A complete example file is at `example.txt` next to this brief.

## Step 5 — Reply

Single line: the absolute path of the file you wrote. Nothing else.
