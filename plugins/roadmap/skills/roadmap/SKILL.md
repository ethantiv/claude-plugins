---
name: roadmap
description: >
  This skill should be used when the user asks to "generate roadmap",
  "create ROADMAP.md", "project proposals", "plan features", or
  "roadmap proposals". Runs an agent swarm: many perspectives propose
  feature ideas, a product-manager panel scores them for usefulness,
  sellability, creativity and wow-factor, and the survivors become the roadmap.
---

# docs/ROADMAP.md Generator (agent swarm)

Generate a project roadmap by running a **swarm of agents** in two groups:

- **Ideation group (divergent)** — several agents, each wearing a *different*
  product/market hat, independently propose feature ideas. They chase genuine
  usefulness, non-obvious niches, end-user impact, and a demoable **wow** the
  competition lacks — not obvious checkbox features.
- **Verification group (convergent)** — a product-manager panel scores every
  idea like a PM who wants to **sell a better product**, not ship a feature for
  its own sake. It kills generic/obvious/low-value ideas and keeps only the ones
  that earn their place.

The survivors are synthesized into `docs/ROADMAP.md`. If the file already exists,
it is regenerated from scratch — confirm overwrite before writing.

## When NOT to use

- Editing a single proposal inside an existing `docs/ROADMAP.md` — this skill regenerates the whole file.
- Sprint planning, task breakdown, or ticket/issue creation — out of scope.
- The user only wants ideas discussed in chat (no file write).
- A bug-fix / tech-debt backlog — this skill produces **product** proposals (value, differentiation), not an engineering chore list.

## Mindset (read first)

Both groups optimize for the **end user buying a better product**, never for
implementation convenience. Every idea must pass the *"so what?"* test:

- **Useful** — solves a real, frequent pain, not a theoretical one.
- **Non-obvious** — if a competitor's changelog already has it, it's not a proposal. Reach for sharp niches and underserved segments.
- **End-user-relevant** — a user (or operator, for infra/tooling) would *notice and care*. Internal refactors are not proposals.
- **Wow / differentiating** — demoable, makes someone say "oh, nice — nobody else does that".

Banned outputs unless analysis *proves* they are the actual gap: "add tests",
"improve docs", "dark mode", "add a settings page", generic "performance".

## Project analysis (shared brief)

Before the swarm runs, gather context that becomes the brief every agent receives:

1. **Detect project manifests:**
   ```bash
   find . -type f \( \
     -name "package.json" -o \
     -name "pyproject.toml" -o \
     -name "Cargo.toml" -o \
     -name "go.mod" -o \
     -name "pom.xml" \
   \) -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/vendor/*" 2>/dev/null
   ```
   Extract project name, description, dependencies. Multiple manifests → note the monorepo structure.
2. **Read README.md** — root and key subdirectory READMEs, for what the product *is and is for*.
3. **Review git log** — `git log --oneline -20` for recent direction.
4. **Scan structure** — `ls -la` and key subdirectories for the shape of the app.

Distill this into a 5–10 line brief: what the product does, who uses it, its stack,
and its current direction. The whole swarm reasons from this brief.

## The swarm

Drive the swarm with the **Workflow tool** — a generate → judge → synthesize
pipeline. Invoking this skill is the opt-in to run it. If the Workflow tool is
unavailable, fall back to the **parallel `Task` agents** described under
*Fallback* below; the two-group design is identical either way.

**Scale to the project.** Small/config/docs repo → 3 perspectives, 1 judge per
idea. Real app → 5–6 perspectives, a 2–3 judge panel per idea.

### Group A — ideation perspectives

Spawn one agent per selected perspective. Each gets the brief, explores the
codebase *through its own lens*, and returns 2–4 ideas. Agents do **not** see each
other's output (divergence is the point).

| Lens | What this agent hunts for |
| --- | --- |
| **Everyday user — frictions** | The recurring pains of the typical user; quality-of-life wins that remove friction from the core loop. |
| **Power user & integrations** | Automation, APIs, interop, pro workflows that create stickiness and upsell paths. |
| **First-run & activation** | The onboarding magic-moment; the feature that makes a newcomer succeed (and stay) in the first five minutes. |
| **Competitor gap** | Scan the category; propose what rivals visibly *lack* — the demoable differentiator. |
| **Adjacent niche** | A non-obvious user segment the product could win with one sharp, well-aimed feature. |
| **Emerging trend** | Where the category is heading (AI, new platforms, new expectations); a forward bet that signals leadership — without being sci-fi. |

Each idea carries: `title`, `pitch` (what changes for the user), `who` (target
user/segment), `wow` (what makes it non-obvious / what competitors lack), and
`evidence` (the concrete hook in the brief/codebase it is grounded in).

### Group B — product-manager verification panel

Every idea is scored by independent PM judges (1–3, scaled to project size). Each
judge reasons as a product manager who must *sell* this — would it win users,
retain them, justify a price, earn word-of-mouth? Score each on **1–5**:

- **usefulness** — real, frequent pain solved.
- **sales** — adoption / retention / monetization upside.
- **creativity** — original, non-obvious (not a checkbox).
- **wow** — differentiation; competition lacks it; demoable.
- **relevance** — matters to the actual end user, not just engineers.
- **feasibility** — buildable within this stack (a light sanity gate, not the goal).

The judge returns a `verdict` of **keep** or **kill**, a one-line PM case
(`why_it_wins`), and `kill_reason` when killing. **Kill** generic, obvious,
"so what?", or off-strategy ideas without mercy. With a panel, an idea survives
only on judge **majority keep**; merge near-duplicate ideas, keeping the strongest framing.

### Synthesis

From the survivors: dedupe, rank by aggregate value (weight **wow** and
**usefulness** highest), keep the top **4–7**, and map each to a priority tier
(below). Carry each survivor's `why_it_wins` line into the roadmap verbatim-ish.

### Reference workflow script

Author a Workflow along these lines (adapt counts to project size):

```javascript
export const meta = {
  name: 'roadmap-swarm',
  description: 'Swarm proposes features from many angles; a PM panel scores and prunes them',
  phases: [{ title: 'Ideate' }, { title: 'Judge' }, { title: 'Synthesize' }],
}

const BRIEF = args.brief                 // the 5–10 line project brief
const LENSES = args.lenses               // selected perspective prompts (3–6)

const IDEA_SCHEMA = { /* ideas: [{ title, pitch, who, wow, evidence }] */ }
const VERDICT_SCHEMA = { /* { title, usefulness, sales, creativity, wow, relevance, feasibility, verdict, why_it_wins, kill_reason } */ }

phase('Ideate')
const batches = await parallel(LENSES.map(lens => () =>
  agent(`${lens}\n\nProject brief:\n${BRIEF}\n\nExplore the repo through this lens and return 2–4 feature ideas. Chase usefulness, non-obvious niches, end-user impact, and a demoable wow competitors lack. No generic items.`,
    { label: `ideate:${lens.slice(0, 20)}`, phase: 'Ideate', schema: IDEA_SCHEMA })))
const ideas = batches.filter(Boolean).flatMap(b => b.ideas)

phase('Judge')
const judged = await parallel(ideas.map(idea => () =>
  parallel([1, 2, 3].map(n => () =>
    agent(`You are a product manager who must SELL this feature, not just build it.\nScore it 1–5 on usefulness, sales, creativity, wow, relevance, feasibility. Verdict keep|kill — kill anything generic, obvious, or "so what?". Give a one-line PM case (why_it_wins).\n\nIdea:\n${JSON.stringify(idea)}\n\nProject brief:\n${BRIEF}`,
      { label: `judge:${idea.title.slice(0, 24)}`, phase: 'Judge', schema: VERDICT_SCHEMA })))
    .then(votes => ({ idea, votes: votes.filter(Boolean) }))))

const survivors = judged
  .map(j => ({ ...j, keeps: j.votes.filter(v => v.verdict === 'keep') }))
  .filter(j => j.keeps.length > j.votes.length / 2)

phase('Synthesize')
return survivors  // ranked & mapped to tiers by the main loop
```

Use the returned survivors (with their `why_it_wins` lines and scores) to write the roadmap. The workflow coordinates the agents; the **Write** of `docs/ROADMAP.md` happens in the main session after it returns.

### Fallback (no Workflow tool)

Run the same two groups with the **Task tool**, `subagent_type="Explore"` for
ideation agents (launch all lenses in one message, in parallel), then a second
parallel batch of PM-judge agents over the collected ideas. Apply the same
keep/kill majority rule and synthesis. Slower and held in context, but identical logic.

## Priority tiers (product value, not engineering criticality)

| Tier | Meaning | Survivor profile |
| --- | --- | --- |
| `P1` | **Flagship** | High wow **and** high usefulness — the headline, demoable, differentiating feature. |
| `P2` | **Strong value** | Clear, broad usefulness or sales upside; solid but less of a standalone wow. |
| `P3` | **Promising bet** | Creative or niche idea with real upside for a specific segment; worth exploring next. |

Rank by aggregate score within each tier — highest wow/usefulness first.

## Output format

```markdown
# Roadmap

## Proposals

### P1 — Flagship

#### {title}
{description — 2–4 sentences on what changes for the user}
**Why it wins:** {one line — the PM case: usefulness × differentiation × who it's for}

### P2 — Strong value

#### {title}
{description}
**Why it wins:** {one line}

### P3 — Promising bet

#### {title}
{description}
**Why it wins:** {one line}
```

**Validation rules:**
- Proposals grouped by tier with H3 headers (P1, P2, P3).
- Each proposal: H4 title, a 2–4 sentence description, then a single `**Why it wins:**` line.
- Empty tiers may be omitted.
- Write the file in the project's documentation language (default English).

## Workflow

1. **Check for existing file:**
   ```bash
   test -f docs/ROADMAP.md && echo "EXISTS" || echo "NOT_EXISTS"
   ```
   If it exists, call `AskUserQuestion` to confirm overwrite. On decline, print a one-line note and stop — do not partially update the file.
2. **Build the brief:** gather context per *Project analysis* and distill it to 5–10 lines.
3. **Select the swarm size:** pick perspectives and judge count per *Scale to the project*.
4. **Run the swarm:** launch the Workflow (generate → judge → synthesize), or the Task-agent fallback.
5. **Synthesize:** dedupe survivors, rank, map to tiers, keep the top 4–7.
6. **Write docs/ROADMAP.md:** use the Write tool; structure per *Output format*.
7. **Display summary:** proposals per tier, how many ideas were generated vs. kept, and the file path.

## Quick reference
| Aspect | Rule |
| --- | --- |
| Output file | `docs/ROADMAP.md` (regenerated; confirm overwrite first) |
| Engine | Agent swarm via Workflow tool (Task-agent fallback) |
| Ideation | 3–6 perspectives, each blind to the others |
| Verification | 1–3 PM judges per idea; majority keep survives |
| Selection | Top 4–7 survivors, ranked by wow × usefulness |
| Tiers | P1 flagship · P2 strong value · P3 promising bet |
| Per proposal | 2–4 sentence description + one `**Why it wins:**` line |
| Skip / scale down | config-only / docs / dotfiles → 3 lenses, 1 judge |
| User declines overwrite | one-line note, stop without writing |

## Common mistakes

- **Generic proposals** ("add tests", "dark mode") not grounded in the codebase. Fix: tie every idea to a concrete hook; let the PM panel kill the rest.
- **Engineer-judging, not PM-judging.** Scoring on implementation ease/elegance instead of usefulness, sellability, and wow. Fix: judges reason as a PM who must *sell* the feature.
- **Convergent ideation.** Letting ideation agents see each other and converge on the same obvious idea. Fix: run them blind, in parallel.
- **Keeping everything.** A swarm generates many ideas; shipping all of them buries the wow. Fix: kill hard, keep the top 4–7.
- **Silent overwrite** of an existing roadmap. Fix: always `AskUserQuestion` first; stop on decline.
- **Sci-fi.** Wow ideas that the stack can't realistically support. Fix: the feasibility score is a sanity gate.
