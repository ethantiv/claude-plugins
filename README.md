# claude-plugins

**A plugin marketplace for [Claude Code](https://claude.com/claude-code)**, with Codex and GitHub Copilot CLI support for `eli`, `teach-me`, `unslop`, `visual-prompt`, and `docstyle`. Add the marketplace once, then install the plugins you need.

## Plugins

| Plugin | Language | What it does |
| --- | --- | --- |
| **book-forge** | Polish | A 12-stage novel-writing pipeline run by an agent swarm: from a market gap and an idea, through an outline and a "book bible", to writing, editing, and a submission package. Every stage ends with a mandatory edit for natural Polish (no AI slop). |
| **babysit-pr** | universal | A local equivalent of `autofix-pr`: it watches the current pull request and fixes it in your Claude Code session, covering CI failures, review comments that request changes, and merge conflicts. After one clean pass it merges the PR and deletes the branch. Run it with `--loop` to keep watching on an interval, or `--push` to commit, push, and open the PR first. |
| **read-arxiv-paper** | universal | Downloads the LaTeX source of an arXiv paper, analyzes it, and writes a summary grounded in the context of your project. |
| **roadmap** | universal | Generates `docs/ROADMAP.md` with an agent swarm: multiple perspectives propose features, then a panel of product managers scores them for usefulness, sellability, and wow factor. |
| **teach-me** | universal | An interactive tutor that walks you step by step to a deep understanding of a topic (a code change, a PR, a file, or an abstract concept): it explains from zero first, checks each step with a quiz, tells you whether you were right and why, and raises the difficulty as you progress. It doesn't stop until your understanding is confirmed. |
| **visual-prompt** | universal | Generates three `.txt` files with artistic text-to-image prompts in three contrasting directions, written in parallel by separate subagents in the conversation language. Two profiles: `art` (artwork, posters, photography) and `ui` (artistic interface mockups). Commands: `/visual-prompt-art`, `/visual-prompt-ui`. |
| **dependency-update** | universal | Scans your project's dependencies across all ecosystems and updates them safely: minor/patch in one pass, majors one at a time with separate research for each. |
| **eli** | universal | Explain like I'm an intern: explains any concept, term, or piece of code to a smart person who lacks the domain knowledge. Short, concrete, example-driven, no padding. |
| **docstyle** | universal | Applies the [Google developer documentation style guide](https://developers.google.com/style) to technical docs. `/docstyle` edits files in place (or reports findings with `--audit`) and activates automatically when you create or edit technical documentation. It does not style chat replies or install session hooks. Ships the full guide (70 pages) as local references with a topic index. |
| **unslop** | universal | Edits LLM-generated documents in place to remove the telltale signs of AI writing catalogued by Wikipedia's ["Signs of AI writing"](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing): AI vocabulary, negative parallelisms, rule of three, promotional tone, vague attributions, throat-clearing, fake-profound kickers, formatting slop—plus Polish officialese and bureaucratic heaviness. Handles Polish and English. Audit mode reports findings with red/yellow/green severity instead of editing; `/unslop:plain` rewrites Polish into plain language (a deliberate register change). The plugin provides skills only; it does not inject instructions at session start. |

## Installation

In a Claude Code session, run these commands (`/plugin` is built into Claude Code):

```text
/plugin marketplace add ethantiv/claude-plugins
/plugin install book-forge@ethantiv-plugins
/plugin install babysit-pr@ethantiv-plugins
/plugin install read-arxiv-paper@ethantiv-plugins
/plugin install roadmap@ethantiv-plugins
/plugin install teach-me@ethantiv-plugins
/plugin install visual-prompt@ethantiv-plugins
/plugin install dependency-update@ethantiv-plugins
/plugin install eli@ethantiv-plugins
/plugin install docstyle@ethantiv-plugins
/plugin install unslop@ethantiv-plugins
```

Or from the terminal, with the CLI:

```bash
claude plugin marketplace add ethantiv/claude-plugins
claude plugin install book-forge@ethantiv-plugins
claude plugin install babysit-pr@ethantiv-plugins
claude plugin install read-arxiv-paper@ethantiv-plugins
claude plugin install roadmap@ethantiv-plugins
claude plugin install teach-me@ethantiv-plugins
claude plugin install visual-prompt@ethantiv-plugins
claude plugin install dependency-update@ethantiv-plugins
claude plugin install eli@ethantiv-plugins
claude plugin install docstyle@ethantiv-plugins
claude plugin install unslop@ethantiv-plugins
```

Install only what you need; the plugins are independent of each other. After installing, verify the installation:

```bash
claude plugin marketplace list
```

### Updates

Claude Code adds the marketplace with `git clone`, so plugins update when you refresh the marketplace, with no reinstall:

```bash
claude plugin marketplace update ethantiv-plugins
```

## Requirements

All plugins work with Claude Code. The five plugins listed above also support Codex and GitHub Copilot CLI. Beyond the host CLI:

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

agent-browser has two layers: the **skill** is the Claude Code integration (the `npx skills add` command above), and the **CLI** is the browser-driving tool that the skill runs. **The skill won't work without the CLI.** It's a dependency, not an alternative, so start with the CLI:

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

**eli**, **unslop**, **docstyle**
- No dependencies beyond the host CLI.

**teach-me**
- Bash for randomizing quiz choices; Git for code-change lessons and authenticated `gh` for GitHub PR lessons.

**visual-prompt**
- Native subagent tools: Workflow/Agent in Claude Code, `spawn_agent` in Codex, or `task` in Copilot CLI. Without delegation, the skill asks before producing the three directions sequentially.

**dependency-update**
- The package managers of your ecosystems (for example, `npm`, `pip`, `cargo`, or `go`) available in `PATH`, used to check for and install updates.

## Usage

After installation, each plugin exposes its skills as `/<plugin>:<skill>` commands.

- **book-forge**: the full pipeline is described in [`plugins/book-forge/README.md`](plugins/book-forge/README.md); a visual guide to the 12 stages: [`przewodnik.html`](plugins/book-forge/przewodnik.html). Start with `/book-forge:market-report` (or the lighter `/book-forge:idea-spark`).
- **babysit-pr**: run `/babysit-pr` on a branch with an open PR to monitor and fix CI, reviews, and conflicts locally; once a pass comes back clean, it merges the PR and deletes the branch. `/babysit-pr --loop 10m` keeps watching by re-running the check every 10 minutes (you choose the interval). No PR yet? `/babysit-pr --push` commits your work, pushes it, opens the PR, and then starts the same watch loop.
- **read-arxiv-paper**: `/read-arxiv-paper:read-arxiv-paper` with a paper URL or ID (for example, `2401.12345`); you get a summary in the context of your repo.
- **roadmap**: `/roadmap:roadmap` gathers ideas with an agent swarm and writes `docs/ROADMAP.md`.
- **teach-me**: `/teach-me:teach-me` with a topic (a code change, a PR, a file, or a concept); it explains first, checks each step, and raises the difficulty until your understanding is confirmed.
- **visual-prompt**: `/visual-prompt-art` or `/visual-prompt-ui` (or describe what you need) generates three `.txt` files with prompts in contrasting directions.
- **dependency-update**: `/dependency-update:dependency-update` scans and safely updates your project's dependencies.
- **eli**: `/eli:eli` with a concept, term, or piece of code; you get a short, vivid explanation.
- **docstyle**: `/docstyle:docstyle` with a file path (or directory) edits documentation in place per the Google developer documentation style guide; `--audit` reports severity-graded findings instead. Creating or editing documentation also triggers the skill. Its rules apply to documentation only, not ordinary chat replies.
- **unslop**: `/unslop:unslop` with a file path (or directory); it edits the document in place to remove signs of AI writing and reports what it fixed. Add `--audit` (or ask for "tylko audyt") to get severity-graded findings without edits. `/unslop:plain` with a file path simplifies bureaucratic Polish into plain language.

## License

[MIT](LICENSE). Use, modify, and redistribute freely.

## Codex CLI

Native Codex packages are available for `unslop`, `eli`, `visual-prompt`, `teach-me`, and `docstyle`. Claude Code continues to use the existing marketplace and manifests.

```sh
codex plugin marketplace add ethantiv/claude-plugins
codex plugin add unslop@ethantiv-plugins
codex plugin add eli@ethantiv-plugins
codex plugin add visual-prompt@ethantiv-plugins
codex plugin add teach-me@ethantiv-plugins
codex plugin add docstyle@ethantiv-plugins
```

For local development, register the repository directory instead of the GitHub source. Restart the session after installation. Invoke `$unslop:unslop`, `$unslop:plain`, `$eli:eli`, `$visual-prompt:visual-prompt`, `$visual-prompt:visual-prompt-art`, `$visual-prompt:visual-prompt-ui`, `$teach-me:teach-me`, or `$docstyle:docstyle`. Skills use the tools available in their host; teach-me falls back to numbered chat choices when Codex has no interactive question tool. Visual-prompt uses Codex subagents when available.

Unslop provides skills only in both Claude Code and Codex. Version 0.4.3 removes its SessionStart hooks; existing `unslop-off` files are no longer used.

## GitHub Copilot CLI

The same five plugins use the existing `ethantiv-plugins` marketplace:

```sh
copilot plugin marketplace add ethantiv/claude-plugins
copilot plugin install eli@ethantiv-plugins
copilot plugin install teach-me@ethantiv-plugins
copilot plugin install unslop@ethantiv-plugins
copilot plugin install visual-prompt@ethantiv-plugins
copilot plugin install docstyle@ethantiv-plugins
```

Start a new session after installation. Invoke `/eli`, `/teach-me`, `/unslop`, `/plain`, `/visual-prompt`, `/visual-prompt-art`, `/visual-prompt-ui`, or `/docstyle`. Use the skill picker if another installed plugin has the same skill name. Teach-me uses `ask_user` when available and otherwise waits for numbered choices in chat. Visual-prompt uses native subagents. See the [Copilot CLI skill and tool reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference).

### Devcontainer configuration

In `build-cli-devcontainer`, both `claude.plugins.external` and `copilot.plugins.external` list the five names under `marketplace: ethantiv-plugins` and `source: ethantiv/claude-plugins`. In `ai-devcontainer-sync`, `defaults.codex.plugins` uses one entry per plugin with the same marketplace and source. The setup scripts install the published repository version; local edits become available through that source after publication.

### Docstyle update

Docstyle 0.1.1 removes all session hooks. It applies only when creating, editing, or auditing technical documentation; ordinary chat replies are outside its scope. After updating an existing installation, start a new session to discard previously injected style instructions. Old `docstyle-off` files are no longer used and can be removed.
