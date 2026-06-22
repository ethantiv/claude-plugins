---
name: dependency-update
description: >
  This skill should be used when the user wants to bring project dependencies
  up-to-date — checking outdated packages, bumping minor/patch versions across
  detected ecosystems, or doing researched major-version upgrades. Triggers
  include "update dependencies", "upgrade packages", "bump versions", "check
  outdated", "update npm packages", "upgrade pip packages".
---

# Dependency Update

Scan the current project for dependency manifests across all ecosystems, separate safe minor/patch bumps from risky major bumps, and verify after each phase.

## When NOT to use

- **Security-only fix** (e.g. `npm audit fix`, CVE patching): that is a narrower workflow, run it directly.
- **Library projects publishing version ranges**: tightening or widening `^x.y.z` ranges in published libraries has consumer-impact rules this skill does not cover — confirm scope with the user first.
- **Reproducible-build / pinned environments**: repos that intentionally pin exact versions should not be bumped without an explicit user request.
- **Single-package update**: if the user names one package, just update that package; the full multi-ecosystem sweep is overkill.

## Workflow

### Step 1: Discover and preflight

1. **Working tree check** — Run `git status`. If there are uncommitted changes, ask the user whether to stash, commit, or proceed anyway. Aggressive updates plus pre-existing edits make rollback impossible.
2. **Manifest discovery** — Scan with the Glob tool, excluding `node_modules/`, `vendor/`, `.venv/`, `target/`, `build/`, `dist/`:

| Ecosystem | Files to find |
|-----------|---------------|
| Node.js | `package.json` + lockfile (`package-lock.json` / `yarn.lock` / `pnpm-lock.yaml` / `bun.lock`) |
| Python | `requirements*.txt`, `pyproject.toml`, `setup.py`, `setup.cfg`, `Pipfile`, `uv.lock` |
| Ruby | `Gemfile` |
| Go | `go.mod` |
| Rust | `Cargo.toml` |
| PHP | `composer.json` |
| Java/Kotlin | `pom.xml`, `build.gradle`, `build.gradle.kts` |
| .NET | `*.csproj`, `*.fsproj`, `Directory.Packages.props` |
| Dart/Flutter | `pubspec.yaml` |
| Elixir | `mix.exs` |
| Swift | `Package.swift` |

3. **Tooling check** — For each detected ecosystem, verify that the listing tool is installed (e.g. `command -v cargo-outdated`, `command -v dotnet-outdated`, presence of Gradle's `dependencyUpdates` plugin). If a helper is missing, **ask the user** whether to install it or skip that ecosystem. Never install global tools silently.
4. **Read `CLAUDE.md`** — Look up the `## Validation` section in the project's `CLAUDE.md` (root and nested). Those exact commands are the ones to run in Step 3.b and Step 4.d.

Report findings: ecosystems detected, lockfiles found, package manager per ecosystem, tools missing, and validation commands collected.

### Step 2: List outdated and classify

For each detected ecosystem, run the appropriate listing command:

| Ecosystem | Listing command |
|-----------|-----------------|
| Node.js (npm) | `npm outdated` |
| Node.js (yarn) | `yarn outdated` |
| Node.js (pnpm) | `pnpm outdated` |
| Node.js (bun) | `bun outdated` |
| Python (pip) | `pip list --outdated` |
| Python (uv) | `uv pip list --outdated` |
| Python (poetry) | `poetry show --outdated` |
| Python (pipenv) | `pipenv update --dry-run` |
| Ruby | `bundle outdated` |
| Go | `go list -m -u all` |
| Rust | `cargo outdated` (only if installed — see Step 1.3) |
| PHP | `composer outdated --direct` |
| Java (Maven) | `mvn versions:display-dependency-updates` |
| Java (Gradle) | `gradle dependencyUpdates` (only if plugin configured) |
| .NET | `dotnet list package --outdated` |
| Dart | `dart pub outdated` / `flutter pub outdated` |
| Elixir | `mix hex.outdated` |

**Classify every outdated package** by semver delta of current → latest:

- **patch** (z bump): safe, apply in Step 3.
- **minor** (y bump): usually safe, apply in Step 3.
- **major** (x bump): risky, handle in Step 4 one at a time.
- **pre-1.0** (`0.y.z`): treat any y bump as major (libraries on `0.y.z` use y as their breaking-change axis).

Present a table grouped by bucket:

```
| Package | Ecosystem | Current | Latest | Bucket |
|---------|-----------|---------|--------|--------|
```

### Step 3: Minor and patch sweep

Goal: apply all patch and minor bumps in one pass per ecosystem, then verify before touching majors.

a. **Update patch/minor only** — Use the conservative form of each tool. Do **not** use `--latest`, `--major-versions`, or `npm-check-updates` here:

| Ecosystem | Patch/minor update |
|-----------|--------------------|
| Node.js (npm) | `npm update` |
| Node.js (yarn) | `yarn upgrade` |
| Node.js (pnpm) | `pnpm update` (without `--latest`) |
| Node.js (bun) | `bun update` |
| Python (pip-tools) | `pip-compile --upgrade` |
| Python (uv) | `uv lock --upgrade` |
| Python (poetry) | `poetry update` |
| Python (pipenv) | `pipenv update` |
| Ruby | `bundle update --conservative` |
| Go | `go get -u=patch ./... && go mod tidy` |
| Rust | `cargo update` |
| PHP | `composer update --with-dependencies` |
| Java (Maven) | `mvn versions:use-latest-releases -DallowMajorUpdates=false` |
| Java (Gradle) | Edit version numbers in `build.gradle` manually (non-major only) |
| .NET | Edit `*.csproj` manually (non-major only), or `dotnet outdated --upgrade` if the tool is installed |
| Dart | `dart pub upgrade` (no `--major-versions`) |
| Elixir | `mix deps.update --all` |

Run these **per ecosystem, not all at once** — sequential updates allow attributing a failure to a specific ecosystem.

b. **Verify after the sweep** — Run the validation commands collected in Step 1.4. Check:
- Lockfile regenerated.
- Build passes.
- Tests pass.
- Type check passes (if applicable).

If verification fails, **stop**. Do not proceed to Step 4. Revert one ecosystem at a time with `git restore` until the culprit is isolated.

### Step 4: Major bumps loop

For each package classified as **major** in Step 2, run this loop **one package at a time**:

a. **Research breaking changes**
   - **context7 MCP** — `resolve-library-id` then `query-docs` for migration guides and changelog. Prefer this over web fetching.
   - **agent-browser** — Fallback if context7 lacks migration info: open the library's CHANGELOG / migration guide on GitHub or the docs site.
   - Summarize required code changes for the user **before** updating.

b. **Update only this package**

| Ecosystem | Single-package major update |
|-----------|------------------------------|
| Node.js (npm) | `npm install <pkg>@latest` |
| Node.js (yarn) | `yarn add <pkg>@latest` |
| Node.js (pnpm) | `pnpm add <pkg>@latest` |
| Node.js (bun) | `bun add <pkg>@latest` |
| Python (uv) | `uv add <pkg>@latest` |
| Python (poetry) | `poetry add <pkg>@latest` |
| Python (pip) | `pip install --upgrade <pkg>` (then regenerate the lockfile) |
| Ruby | `bundle update <gem>` |
| Go | `go get <module>@latest && go mod tidy` |
| Rust | `cargo add <crate>@<version>` (or edit `Cargo.toml`, then `cargo update -p <crate>`) |
| PHP | `composer require <pkg>:^<major>` |
| Dart | `dart pub upgrade --major-versions <pkg>` |

c. **Apply code changes** identified in Step 4.a (call sites, deprecated APIs, config format changes).

d. **Verify** with the same validation commands as Step 3.b. If it fails, either fix the breakage or revert with `git restore` and skip this bump (report as "skipped — incompatible").

e. **Checkpoint** — Do NOT auto-commit, but pause and tell the user: "Major bump `<pkg>` `X` → `Y` complete and verified — good checkpoint to commit." Per-major checkpoints make the eventual git history reviewable.

Repeat until all major bumps are processed (or skipped with reason).

### Step 5: Report

```
## Dependency Update Summary

### Patch/minor sweep
| Package | Ecosystem | From | To |
|---------|-----------|------|-----|

### Major bumps applied
| Package | From | To | Code changes |
|---------|------|----|--------------|

### Major bumps skipped
| Package | Reason |
|---------|--------|

### Verification
- Build: PASS/FAIL
- Tests: PASS/FAIL (X/Y)
- Type check: PASS/FAIL
```

## Common mistakes

- **Running `pnpm update --latest` / `npm-check-updates -u` / `dart pub upgrade --major-versions` in Step 3.** Those commands skip the major-bump research gate. Use them only inside Step 4's per-package loop, after researching changes.
- **Auto-installing helper tools.** `cargo install cargo-outdated`, `dotnet tool install -g dotnet-outdated-tool`, Gradle plugin injection — all require explicit user consent. Ask, do not assume.
- **Batching all ecosystems before any verification.** Updating Node + Python + Go and then running tests once means a failure cannot be attributed. Verify after each ecosystem in Step 3, after each major bump in Step 4.
- **Ignoring peer-dependency conflicts.** React/Vue/Angular bumps often require coordinated updates across multiple packages. Inspect the `peerDependencies` warnings from the install step before assuming success.
- **Treating `pre-1.0` minor as safe.** Libraries on `0.y.z` use the y-bump as their major. Classify them as major in Step 2.
- **Updating a library's published version ranges silently.** If `package.json` of a publishable library has `peerDependencies` or wide ranges, the bump policy is different — confirm scope with the user.

## Important Notes

- **Lockfile detection drives package-manager choice** — presence of `pnpm-lock.yaml` / `yarn.lock` / `bun.lock` / `package-lock.json` decides the Node.js tool. Never assume npm.
- **Monorepos** — npm/yarn/pnpm workspaces, Nx, Turborepo: run updates at the workspace root, not in individual packages.
- **Virtual environments** — For Python, detect and activate `.venv` / `venv` / poetry env before running pip commands.
- **Selective scope** — If the user names ecosystems or packages, limit the run accordingly; do not expand scope without explicit instruction.
- **Dry run** — If the user asks for "check only" or "dry run", stop after Step 2 (the classified outdated table) without running any update commands.
- **Git safety** — Do NOT commit changes automatically. Surface checkpoints (especially after each major bump) so the user can choose what to commit and when.
- **Security audit is a separate workflow** — `npm audit`, `pip-audit`, `cargo audit`, `bundle audit`, `composer audit`. Run them only if the user explicitly asks.
