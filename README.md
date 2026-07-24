# claude-plugins

**A plugin marketplace for [Claude Code](https://claude.com/claude-code)**. Add it once, then install plugins with a single command. They work in the terminal, the desktop app, and the IDE extensions.

## Plugins

| Plugin | Language | What it does |
| --- | --- | --- |
| **action-first** | universal | A persistent response style for the whole session: every answer leads with the next concrete action, multi-step work is numbered, state is restated each turn, and preamble, recaps, and tangents are cut. Turn it off with "stop action-first" or "normal mode". |
| **book-forge** | Polish | A 12-stage novel-writing pipeline run by an agent swarm: from a market gap and an idea, through an outline and a "book bible", to writing, editing, and a submission package. Every stage ends with a mandatory edit for natural Polish (no AI slop). |
| **babysit-pr** | universal | A local equivalent of `autofix-pr`: it watches the current pull request and fixes it in your Claude Code session, covering CI failures, review comments that request changes, and merge conflicts. After one clean pass it merges the PR and deletes the branch. Run it with `--loop` to keep watching on an interval, or `--push` to commit, push, and open the PR first. |
| **read-arxiv-paper** | universal | Downloads the LaTeX source of an arXiv paper, analyzes it, and writes a summary grounded in the context of your project. |
| **roadmap** | universal | Generates `docs/ROADMAP.md` with an agent swarm: multiple perspectives propose features, then a panel of product managers scores them for usefulness, sellability, and wow factor. |
| **teach-me** | universal | An interactive tutor that walks you step by step to a deep understanding of a topic (a code change, a PR, a file, or an abstract concept): a running checklist, "why" drills, and quizzes. It doesn't stop until your understanding is confirmed. |
| **visual-prompt** | universal | Generates three `.txt` files with artistic text-to-image prompts in three contrasting directions, written in parallel by separate subagents. Two profiles: `art` (artwork, posters, photography) and `ui` (artistic interface mockups). Commands: `/visual-prompt-art`, `/visual-prompt-ui`. |
| **dependency-update** | universal | Scans your project's dependencies across all ecosystems and updates them safely: minor/patch in one pass, majors one at a time with separate research for each. |
| **eli** | universal | Explain like I'm an intern: explains any concept, term, or piece of code to a smart person who just lacks the domain knowledge. Short, concrete, example-driven, no padding. |
| **unslop** | universal | Edits LLM-generated documents in place to remove the telltale signs of AI writing catalogued by Wikipedia's ["Signs of AI writing"](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing): AI vocabulary, negative parallelisms, rule of three, promotional tone, vague attributions, throat-clearing, fake-profound kickers, formatting slop. Handles Polish and English. A SessionStart hook applies the style to all agent prose; disable it by creating `.claude/unslop-off`. |

## Installation

In a Claude Code session, run these commands (`/plugin` is built into Claude Code):

```text
/plugin marketplace add ethantiv/claude-plugins
/plugin install action-first@ethantiv-plugins
/plugin install book-forge@ethantiv-plugins
/plugin install babysit-pr@ethantiv-plugins
/plugin install read-arxiv-paper@ethantiv-plugins
/plugin install roadmap@ethantiv-plugins
/plugin install teach-me@ethantiv-plugins
/plugin install visual-prompt@ethantiv-plugins
/plugin install dependency-update@ethantiv-plugins
/plugin install eli@ethantiv-plugins
/plugin install unslop@ethantiv-plugins
```

Or from the terminal, via the CLI:

```bash
claude plugin marketplace add ethantiv/claude-plugins
claude plugin install action-first@ethantiv-plugins
claude plugin install book-forge@ethantiv-plugins
claude plugin install babysit-pr@ethantiv-plugins
claude plugin install read-arxiv-paper@ethantiv-plugins
claude plugin install roadmap@ethantiv-plugins
claude plugin install teach-me@ethantiv-plugins
claude plugin install visual-prompt@ethantiv-plugins
claude plugin install dependency-update@ethantiv-plugins
claude plugin install eli@ethantiv-plugins
claude plugin install unslop@ethantiv-plugins
```

Install only what you need; the plugins are independent of each other. After installing, check the state:

```bash
claude plugin marketplace list
```

### Updates

The marketplace is added via `git clone`, so plugins update when you refresh the marketplace, with no reinstall:

```bash
claude plugin marketplace update ethantiv-plugins
```

## Requirements

All plugins need a working Claude Code. Beyond that:

**book-forge**
- **Python 3**, standard library only, no `pip install`.
- **Node.js**, used to validate generated HTML artifacts (`node --check`).
- The **Workflow** tool (agent swarm); without it the skills fall back to parallel `Task` agents.
- The **`/unslop:unslop`** skill (the `unslop` plugin from this marketplace), a mandatory language-editing pass.
- The **agent-browser** skill, used for research and fact checking; project page: [agent-browser.dev](https://agent-browser.dev).

Install both skills with:

```bash
claude plugin install unslop@ethantiv-plugins
npx skills add https://github.com/vercel-labs/agent-browser --skill agent-browser
```

agent-browser has two layers: the **skill** is the Claude Code integration (the `npx skills add` command above), and the **CLI** is the browser-driving tool the skill uses under the hood. **The skill won't work without the CLI.** It's a dependency, not an alternative, so start with the CLI:

```bash
npm install -g agent-browser      # all platforms
brew install agent-browser        # macOS
agent-browser install             # downloads Chrome on first run

# or without installing
npx agent-browser open example.com
```

**babysit-pr**
- **`gh`** (GitHub CLI, logged in), **`jq`**, and **`git`** available in `PATH`.

**read-arxiv-paper**
- **`curl`** and **`tar`** (usually already on your system), used to download and unpack the arXiv source.

**roadmap**
- The **Workflow** tool (agent swarm); without it the skill falls back to parallel `Task` agents.

**teach-me**, **eli**, **action-first**
- No dependencies beyond Claude Code.

**visual-prompt**
- The **Workflow** tool (agent swarm) for writing prompts in parallel; without it the skills fall back to parallel `Task` agents.

**dependency-update**
- The package managers of your ecosystems (e.g. `npm`, `pip`, `cargo`, `go`) available in `PATH`, used to check for and install updates.

## Usage

After installation, each plugin exposes its skills as `/<plugin>:<skill>` commands.

- **book-forge**: the full pipeline is described in [`plugins/book-forge/README.md`](plugins/book-forge/README.md); a visual guide to the 12 stages: [`przewodnik.html`](plugins/book-forge/przewodnik.html). Start with `/book-forge:market-report` (or the lighter `/book-forge:idea-spark`).
- **babysit-pr**: run `/babysit-pr` on a branch with an open PR to monitor and fix CI, reviews, and conflicts locally; once a pass comes back clean, it merges the PR and deletes the branch. `/babysit-pr --loop 10m` keeps watching by re-running the check every 10 minutes (the interval is yours to pick). No PR yet? `/babysit-pr --push` commits your work, pushes it, opens the PR, and then starts the same watch loop.
- **read-arxiv-paper**: `/read-arxiv-paper:read-arxiv-paper` with a paper URL or ID (e.g. `2401.12345`); you get a summary in the context of your repo.
- **roadmap**: `/roadmap:roadmap` gathers ideas with an agent swarm and writes `docs/ROADMAP.md`.
- **teach-me**: `/teach-me:teach-me` with a topic (a code change, a PR, a file, or a concept); it teaches until your understanding is confirmed.
- **visual-prompt**: `/visual-prompt-art` or `/visual-prompt-ui` (or just describe what you need) generates three `.txt` files with prompts in contrasting directions.
- **dependency-update**: `/dependency-update:dependency-update` scans and safely updates your project's dependencies.
- **eli**: `/eli:eli` with a concept, term, or piece of code; you get a short, vivid explanation.
- **unslop**: `/unslop:unslop` with a file path (or directory); it edits the document in place to remove signs of AI writing and reports what it fixed.
- **action-first**: `/action-first:action-first` (or ask for "action-first mode") switches the whole session into the action-first response style; say "stop action-first" or "normal mode" to switch back.

## License

[MIT](LICENSE). Use, modify, and redistribute freely.
