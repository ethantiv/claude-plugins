---
name: babysit-pr
description: >
  This skill should be used when the user asks to "babysit a PR", "monitor my
  PR", "watch the PR", "autofix my PR locally", "fix CI failures on my PR", or
  invokes /babysit-pr. It is the local equivalent of Claude Code's built-in
  autofix-pr: it inspects the current pull request and pushes fixes for failing
  CI, review comments requesting changes, and merge conflicts — all in the
  local session, not a remote cloud session. After one clean pass it merges the
  PR and deletes its branch on its own.
argument-hint: "[PR number]"
allowed-tools: Bash, Read, Edit, Write, Grep, Glob
---

# Babysit PR (local autofix)

Run **one monitoring pass** over a pull request: detect its state, fix what is broken, push the fix to the PR branch, then report. This is the local-session counterpart of the built-in `autofix-pr` command — the difference is that a local session receives no GitHub webhooks, so state is gathered by polling `gh` rather than arriving as push notifications.

One pass is deliberate: continuity comes from running this skill under the `/loop` skill, e.g. `/loop 10m /babysit-pr`. Each pass is self-contained and emits a clear terminal signal so the loop knows when to stop.

**Auto-merge is always on.** The skill closes the loop by itself: after **one clean pass** (green CI, no conflicts, no open reviewer comments) it merges the PR and deletes its branch, then signals the loop to stop. See Step 5.

## When NOT to use

- No open PR exists for the branch yet — open the PR first.
- The user wants a one-off review or critique of the diff — that is `/code-review`, not this.
- Changes need design discussion or a human decision — this skill fixes mechanical breakage, it does not negotiate.

## Step 1 — Snapshot the PR

Parse `$ARGUMENTS`: a bare integer is the PR number; pass it to the snapshot script. With no PR number it resolves the open PR for the current branch:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/pr-snapshot.sh" <PR_NUMBER or empty>
```

Keep the snapshot JSON — Step 5 feeds it to the auto-gate without re-querying `gh`.

The script prints one JSON object and never mutates anything. Branch on `.status` before doing anything else:

| `.status` | Action |
|---|---|
| `ok` | Continue to Step 2 with the payload. |
| `no_pr` | Report: no open PR for this branch. Stop — and tell the user to stop the loop. |
| `on_default_branch` | Report: on the default branch, check out a feature branch first. Stop the loop. |
| `merged` / `closed` | Report the outcome. **The job is done — tell the user to stop the loop** (`Esc`). |
| `gh_missing` | Report that `gh` is required but not installed. Stop. |
| `gh_error` | Report `.error`. Stop this pass; the loop may retry. |

## Step 2 — Learn the repository's conventions

Before changing code, find how this repo validates itself so fixes match local standards (this mirrors how `autofix-pr` accepts custom instructions). Read, if present: `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, and the manifest scripts (`package.json` → `scripts`, `Makefile`, `justfile`). Note the lint, type-check, and test commands — use them to verify a fix locally before pushing.

## Step 3 — Fix what is broken

Address every problem the snapshot reports, in this order. Verify each fix locally with the repo's own commands when feasible and commit it as you go, but **hold the push until the end** — see "Commit, resolve, then push" for why.

1. **Merge conflicts** (`.has_conflicts == true`): merge or rebase the base branch (`.baseRefName`) into the PR branch, resolve conflicts, verify.
2. **Failing CI** (`.failing_checks`): for each failing check, open its `.url` if needed to read the failure, reproduce locally, fix the root cause. Do not paper over a failure (no skipped tests, no disabled checks — Rule 10).
3. **Review threads** (`.review_threads`, `.changes_requested`): the snapshot already filters out resolved threads, so everything listed is still open. Act **only** on threads that clearly request a concrete code change. For each, make the change at the referenced `path`/`line`.
   - You decide each finding's worth yourself (see "Decide each finding's worth yourself" below); only genuinely un-adjudicable items stay open for a human.
   - `is_outdated == true` means the code moved since the comment; re-read the current code before deciding whether it still applies.

### Decide each finding's worth yourself

For every finding, judge whether it is worth applying — this is your call, not the human's:

- **Apply** it when it is a real bug or correctness/robustness issue with a clear, well-scoped fix that does **not** change the project's documented design.
- **Skip** it when it is trivial/low-value, *or* when its only fix would change a documented design assumption (behaviour spelled out in `IDEA.md` / `CLAUDE.md` / `AGENTS.md` or the PR's stated goals). On a skip, post a short reply on the thread explaining the decision, resolve it (so the loop does not revisit it), and note the skip in your report.

This overrides any "leave design feedback for the human" default: you are the decision-maker. Reserve a true hand-off only for findings you genuinely cannot adjudicate (ambiguous product direction, missing context) — leave those open.

### Commit, resolve, then push — in that order

The push is what a review bot reacts to. Repos commonly run a bot on `pull_request: synchronize` (i.e. on every push to the PR branch) that skips any finding whose review thread is already `isResolved`. If you push **before** resolving, the push wakes the bot, which reads the threads as still unresolved and re-posts findings you just fixed — a race you cannot win. So resolve **before** the push the bot sees.

For each problem:

1. Make the fix, verify locally, and **commit it — but do not push yet.** One focused commit per problem class (conflict resolution / CI fix / review fix); commit messages in English.
2. For a fixed **review thread**, mark it resolved with its `thread_id`: ```bash gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' -f id="<thread_id>" ``` Resolve threads you fixed in the committed code, and threads you deliberately skipped (after replying with the rationale — see "Decide each finding's worth yourself"). Only a thread you are genuinely handing to the human stays unresolved — resolving that one would hide it from the reviewer.

Once every fix is committed and every fixed thread resolved, **push once**:

```bash
git push
```

The single push triggers one bot run, and by then the fixed threads already read `isResolved == true`, so the bot skips them. Optionally reply on a thread first, so humans see what changed: `gh pr comment <PR_NUMBER> --body "Fixed in <short-sha>."`

### Restart an in-flight review after resolving threads

A review run that started *before* your resolves reads the pre-resolve thread state and re-posts findings you just handled. So whenever you resolve or close a thread while a review is still in progress — including a skip-resolve with no code change to push — restart the review so a fresh run sees the current state:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/restart-review.sh"
```

It no-ops when nothing is in progress, and cancels stale in-flight runs (on superseded commits) before rerunning the latest against the current HEAD. Pass the review workflow name (or set `$BABYSIT_REVIEW_WORKFLOW`) if it is not `claude-code-review.yml`.

**Safety net:** committing before resolving means a fix is never lost. If the push fails, the resolved thread is filtered out of the next snapshot, but `.unpushed_local_commits` will be `true` — so at the **start** of each pass, push any pending local commits before doing anything else.

**Stop and ask the human — do not commit or push — when:**
- The failure is in infrastructure you cannot change (flaky external service, secrets).
- Resolving a conflict would discard someone else's intent.
- A finding is genuinely un-adjudicable (ambiguous product direction, missing context) — leave its thread open rather than guessing. (A finding that merely *changes a documented design* is not this case: decide it yourself and skip.)

## Step 4 — Report and signal the loop

Close the pass with a one-paragraph status, then one of:

- **Fixed and pushed**: list what was fixed in one line each. The next loop pass will re-check CI.
- **Nothing to do**: PR is green, no actionable comments, no conflicts — say so plainly. Under a fixed-interval `/loop` this is normal; keep waiting. Proceed to Step 5 (this is the only path that can merge).
- **Done**: PR is merged or closed — state the outcome and tell the user to stop the loop.
- **Blocked**: a problem needs a human — state exactly what and why.

Keep the report short; the user can see the diffs and `gh` output.

## Step 5 — Auto-merge gate

**Run the gate ONLY on a "Nothing to do" pass** — one where Step 3 made no commits and no push, and the snapshot's `unpushed_local_commits == false`. Never run it after a fix: the snapshot was taken *before* the fix, so a pushed pass must just end and let the next pass re-evaluate the new commit from scratch.

Feed the Step 1 snapshot to the gate (no extra `gh` calls):

```bash
echo "$SNAPSHOT" | "${CLAUDE_PLUGIN_ROOT}/scripts/auto-gate.sh"
```

It prints `{clean, sha}`. "Clean" is positive confirmation of mergeability (`mergeStateStatus == CLEAN` plus no failing/pending checks, no conflicts, no open review threads, no changes-requested reviews) — not mere absence of red, so an empty CI rollup right after a push does not look clean. One clean pass is enough: `clean == true` means merge.

**Invariant that keeps this safe:** a finding you hand off to a human stays an *unresolved* review thread (Step 3), so `review_threads` is non-empty → not clean → the gate never merges a PR with an open human decision on it.

When `clean == true`, merge against the exact verified commit:

```bash
gh pr merge <number> --merge --delete-branch --match-head-commit <gate_sha>
```

- Merge method defaults to `--merge` (merge commit); override via `$BABYSIT_MERGE_METHOD` (`squash` | `merge` | `rebase`).
- `--match-head-commit <gate_sha>` (the `sha` the gate printed) makes the merge fail safely if anyone pushed between the clean read and now.
- **Never use `--admin`.** Branch protection and required approvals must be respected — if GitHub blocks the merge, that is the system working.

After the command, **verify the real state** — `gh pr merge` may *enable* auto-merge or queue the PR rather than merge immediately:

```bash
gh pr view <number> --json state -q .state
```

- `MERGED`: report the merge and branch deletion, and **tell the user to stop the loop** (`Esc`).
- Auto-merge enabled / queued: report that and **keep looping** — a later pass sees `merged` via Step 1 and signals done.
- Merge rejected (method disallowed, branch protection, missing approval, moved HEAD): report the exact reason and keep looping.
