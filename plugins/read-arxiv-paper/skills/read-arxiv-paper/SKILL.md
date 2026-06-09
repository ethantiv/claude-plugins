---
name: read-arxiv-paper
description: >
  This skill should be used when the user asks to read, summarize, analyze, or
  review an arxiv paper, or provides an arxiv URL or ID — including versioned
  IDs (e.g. 2601.07372v3) and old-format IDs (e.g. cs/0301012).
---

# Read arXiv Paper

Download an arXiv paper's LaTeX source, read and analyze it, and produce a project-contextualized summary in a local `./arxiv/knowledge/` directory.

## When NOT to Use

- User wants the rendered PDF for printing or sharing — use a PDF tool instead.
- Paper is not on arXiv (bioRxiv, OpenReview, NeurIPS/ICML proceedings) — needs a different fetcher.
- User wants only metadata (title, authors, abstract) — query the arXiv API directly, no source download.

## Workflow

### Step 1: Normalize the URL

Extract the arXiv ID. Supported inputs:

- `https://arxiv.org/abs/2601.07372`
- `https://arxiv.org/abs/2601.07372v3` — versioned
- `https://arxiv.org/pdf/2601.07372`
- `https://arxiv.org/abs/cs/0301012` — old format (pre-April 2007)
- Bare ID: `2601.07372`, `2601.07372v3`, `cs/0301012`

Keep two variables:

- `arxiv_id` — exactly as it appears in the URL (may contain `/` and `vN`). Used in URLs.
- `safe_id` — `arxiv_id` with `/` replaced by `_`. Used for filenames and directories.

Example: `cs/0301012` → `arxiv_id=cs/0301012`, `safe_id=cs_0301012`.

### Step 2: Download the Source

Download to a neutral filename (the archive type is not known yet):

```bash
mkdir -p ./arxiv
[ -f ./arxiv/{safe_id}.src ] || curl -L -f -o ./arxiv/{safe_id}.src "https://arxiv.org/src/{arxiv_id}"
```

The `[ -f ... ] ||` guard skips re-downloads. `-f` makes `curl` exit non-zero on HTTP errors so a 404 doesn't silently produce an HTML file.

Suggest adding `arxiv/` (but not `arxiv/knowledge/`) to `.gitignore` so downloaded sources don't get committed:

```
arxiv/*
!arxiv/knowledge/
```

### Step 3: Detect Type and Unpack

arXiv returns one of: gzipped tarball, plain `.tex`, occasionally a `.zip` or raw `.tar`. Detect first, then unpack:

```bash
mkdir -p ./arxiv/{safe_id}
file ./arxiv/{safe_id}.src
```

Dispatch on the output:

- `gzip compressed data` → `tar -xzf ./arxiv/{safe_id}.src -C ./arxiv/{safe_id}`
- `POSIX tar archive` → `tar -xf  ./arxiv/{safe_id}.src -C ./arxiv/{safe_id}`
- `LaTeX 2e document` or `ASCII text` → `cp ./arxiv/{safe_id}.src ./arxiv/{safe_id}/main.tex`
- `Zip archive` → `unzip -d ./arxiv/{safe_id} ./arxiv/{safe_id}.src`

If the archive unpacks into a single nested directory, flatten path lookups with:

```bash
find ./arxiv/{safe_id} -maxdepth 3 -name '*.tex'
```

### Step 4: Locate the Entrypoint

Find the file containing `\documentclass`:

```bash
grep -rlF '\documentclass' --include='*.tex' ./arxiv/{safe_id}/
```

If multiple candidates, pick the one that also contains `\begin{document}`. Common names (`main.tex`, `paper.tex`, `ms.tex`) are hints, not guarantees — the `grep` is authoritative.

### Step 5: Read the Paper

Use the `Read` tool (not `cat`) on `.tex` files — it handles large files better and supports offset/limit when papers run long.

Starting from the entrypoint:

1. Read the main `.tex`.
2. Follow `\input{...}` and `\include{...}` directives to read referenced fragments.
3. Prefer `.bbl` over `.bib` when both exist (`.bbl` is the rendered bibliography).
4. Skip binary files (figures, compiled output).
5. For papers with `*-supplementary.tex` or `appendix.tex`, read them only if the user asks about results details.

Extract: title, authors, abstract, all sections, key equations, algorithms, conclusions.

### Step 6: Produce a Summary

Write to `./arxiv/knowledge/summary_{tag}_{safe_id}.md` in the **current project directory**. Including `safe_id` in the filename makes it deterministic — no collision check needed, and re-running on the same paper overwrites cleanly.

```bash
mkdir -p ./arxiv/knowledge
```

Derive `tag` from the paper's core topic in snake_case (e.g. `conditional_memory`, `sparse_attention`, `rl_from_feedback`).

#### Summary Structure

```markdown
# {Paper Title}

**Authors:** {authors}
**arXiv:** [{arxiv_id}](https://arxiv.org/abs/{arxiv_id})
**Date:** {publication date}

## Key Idea

{1–2 paragraph summary of the core contribution}

## Method

{Description of the approach, architecture, or algorithm}

## Key Results

{Main experimental findings and comparisons}

## Relevance to This Project

{How the paper's techniques relate to this project and what to try}

## Notable Details

{Interesting implementation details, hyperparameters, or insights worth remembering}
```

#### Project Contextualization

The "Relevance to This Project" section is the value-add of this skill. To write it:

1. Read relevant parts of the current codebase to understand architecture and goals.
2. Identify concrete connections between the paper's techniques and the project.
3. Suggest specific experiments or changes inspired by the paper.

If project context is unclear or too broad, ask which aspects to focus on before writing.

## End-to-End Example

Input from the user: `https://arxiv.org/abs/2601.07372v2`

```bash
# Step 1: arxiv_id=2601.07372v2, safe_id=2601.07372v2

# Step 2: download
mkdir -p ./arxiv
[ -f ./arxiv/2601.07372v2.src ] || curl -L -f -o ./arxiv/2601.07372v2.src \
  "https://arxiv.org/src/2601.07372v2"

# Step 3: detect + unpack
mkdir -p ./arxiv/2601.07372v2
file ./arxiv/2601.07372v2.src
# -> gzip compressed data
tar -xzf ./arxiv/2601.07372v2.src -C ./arxiv/2601.07372v2

# Step 4: entrypoint
grep -rlF '\documentclass' --include='*.tex' ./arxiv/2601.07372v2/
# -> ./arxiv/2601.07372v2/main.tex

# Step 5: Read tool on main.tex, then follow \input{sections/method.tex} etc.

# Step 6: write summary
mkdir -p ./arxiv/knowledge
# Write ./arxiv/knowledge/summary_sparse_attention_2601.07372v2.md
```

## Notes

- Always fetch the **TeX source** (`/src/`), never the PDF — LaTeX source is far more readable and token-efficient.
- `./arxiv/` holds downloaded sources locally; `./arxiv/knowledge/` keeps summaries inside the project.
- Filename pattern `summary_{tag}_{safe_id}.md` is deterministic — re-running on the same paper overwrites in place.
