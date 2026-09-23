---
name: dependency-update
description: >
  This skill should be used when the user wants to bring project dependencies
  up-to-date — checking outdated packages, bumping minor/patch versions across
  detected ecosystems, or doing researched major-version upgrades. Triggers
  include "update dependencies", "upgrade packages", "bump versions", "check
  outdated", "update npm packages", "upgrade pip packages".
argument-hint: "[ecosystem or package scope] [dry run] — empty = full sweep"
allowed-tools: Read, Glob, Grep, Edit, WebFetch, Bash(git:*), Bash(command:*), Bash(npm:*), Bash(yarn:*), Bash(pnpm:*), Bash(bun:*), Bash(pip:*), Bash(pip-compile:*), Bash(uv:*), Bash(poetry:*), Bash(pipenv:*), Bash(bundle:*), Bash(go:*), Bash(cargo:*), Bash(composer:*), Bash(mvn:*), Bash(gradle:*), Bash(dotnet:*), Bash(dart:*), Bash(flutter:*), Bash(mix:*), Bash(swift:*), Bash(./gradlew:*)
---

# Dependency Update

Update dependencies within the user's requested scope, separate routine updates from migrations, and verify each batch. Version numbers indicate compatibility expectations, not a guarantee of safety.

## Scope

- A named package or ecosystem limits the run; do not expand it into a full sweep. Include related packages only when compatibility requires it, and explain why.
- For "check outdated", "check only", or "dry run", report candidates without changing manifests, lockfiles, or installed environments. Do not run an update command merely to discover its effects.
- Honor requested versions, release channels, pins, and repository policy. Default to stable releases. A request to update dependencies includes ordinary pinned dependencies; clarify only pins with a documented reason or policy conflict.
- In published libraries, preserve the intended consumer compatibility and peer-dependency ranges. Ask only when the requested update leaves that policy ambiguous.
- Security-only remediation is a narrower task; do not turn it into a general upgrade.

## 1. Discover and establish a baseline

Read applicable repository instructions (`AGENTS.md`, `CLAUDE.md`, and relevant nested instructions), CI configuration, and package scripts to find validation commands. Do not assume a particular heading or file exists.

Inspect `git status`, staged changes, and unstaged changes. Preserve existing edits and record the starting contents of files you will change so you can undo only your own work. Unrelated edits do not require stopping. Ask only if overlapping changes cannot be preserved safely; do not stash, commit, or discard user work automatically.

Discover manifests within scope, excluding generated and vendored directories such as `node_modules/`, `vendor/`, `.venv/`, `target/`, `build/`, and `dist/`:

| Ecosystem | Common manifests and lockfiles |
|-----------|--------------------------------|
| Node.js | `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `bun.lock`, `bun.lockb` |
| Python | `requirements*.in`, `requirements*.txt`, `pyproject.toml`, `setup.py`, `setup.cfg`, `Pipfile`, `uv.lock`, `poetry.lock`, `Pipfile.lock` |
| Ruby | `Gemfile`, `Gemfile.lock` |
| Go | `go.mod`, `go.sum` |
| Rust | `Cargo.toml`, `Cargo.lock` |
| PHP | `composer.json`, `composer.lock` |
| Java/Kotlin | `pom.xml`, `build.gradle`, `build.gradle.kts`, `gradle/libs.versions.toml` |
| .NET | `*.csproj`, `*.fsproj`, `Directory.Packages.props`, `packages.lock.json` |
| Dart/Flutter | `pubspec.yaml`, `pubspec.lock` |
| Elixir | `mix.exs`, `mix.lock` |
| Swift | `Package.swift`, `Package.resolved` |

Choose the package manager and version from repository declarations, lockfiles, and CI. Resolve conflicting evidence before updating; do not create a second lockfile. Use workspace roots for shared lockfiles and the project's Python environment rather than global pip. Update the source manifest of generated dependency files, then regenerate them with the existing workflow.

Prefer installed tooling. If a listing helper is missing, use the package manager or official registry metadata where possible. Ask before installing a helper or modifying build configuration to add one, unless already authorized; otherwise report the coverage gap.

Before mutations, run relevant baseline checks when practical, so existing failures are distinguishable from regressions. Report detected managers, scope, and available validation.

## 2. List candidates and classify

Use the installed manager's supported read-only listing command (for example `npm outdated`, `pnpm outdated`, `poetry show --outdated`, `go list -m -u all`, or `composer outdated --direct`). Check local help or official documentation for version-dependent commands; do not assume Yarn generations or other manager versions share flags. Treat a nonzero exit according to the command's documented behavior, not automatically as a failed scan.

Read current resolved versions from lockfiles where possible. An installed-environment listing such as `pip list --outdated` is not a complete inventory of declared project dependencies.

For each candidate, report current version, proposed target, latest stable version, and classification. A new major being available does not exclude a newer patch/minor on the current major line.

- Patch/minor under semver: candidates for the routine batch, subject to release notes and project constraints.
- Major or pre-1.0 minor: migration candidates; review compatibility before updating.
- Non-semver versions, prereleases, and known breaking changes: classify using the project's release policy rather than numeric assumptions.

For a read-only request, finish with this table and any discovery limits.

## 3. Apply routine updates

Work one ecosystem at a time, verifying each before continuing. Choose explicit target versions or bounded constraints that enforce the intended patch/minor scope. Preserve dependency groups, extras, registry sources, workspace placement, and the repository's pin/range style.

Do not treat a resolver's generic update command as a patch/minor filter. For example, [`npm update`](https://docs.npmjs.com/cli/commands/npm-update) follows declared ranges; [`pip-compile --upgrade`](https://pip-tools.readthedocs.io/en/stable/) re-resolves allowed versions. Broad ranges can permit major updates, while narrow ranges can prevent intended minor updates. Inspect constraints before running the command and inspect the resulting manifest and lockfile diff afterward.

Use package-scoped updates when the user named packages. Allow necessary transitive changes, but investigate unrelated churn or unexpected major upgrades before accepting the batch. Never hand-edit generated lockfiles or use force flags to hide dependency conflicts.

Run the collected checks (build, tests, type checks as applicable). If a regression appears, stop further updates, diagnose it, and either fix it within scope or undo only this batch's changes using the recorded baseline. A blanket `git restore` can erase user edits and earlier successful updates; do not use it as a generic rollback.

## 4. Apply migrations

For each requested major or other breaking update:

1. Read official release notes and migration guidance for the exact current-to-target path, including intermediate breaking releases when crossing several majors. Use a documentation MCP if available, otherwise official web sources. Summarize required changes before editing.
2. Update to the researched target, preserving dependency groups and manifest conventions. Do not substitute a moving `latest` for the version you reviewed. Some ecosystems require manifest constraints or import/module paths to change before the resolver can install a major release.
3. Apply the required code and configuration migration. Update tightly coupled packages together when peer or framework compatibility requires it; otherwise keep migrations separate.
4. Run validation and inspect the complete diff. If incompatible, undo only this migration, preserve prior work, and report the reason. If unresolved failure remains, stop dependent updates rather than building on a broken state.
5. Report the verified checkpoint and continue within the authorized scope. Do not auto-commit or require another confirmation solely because a major update completed.

## 5. Report

Summarize versions changed, migration edits, skipped packages with reasons, and checks actually run. Distinguish passing checks, failures, baseline failures, and checks not run; never label an untested update verified. Include important source links for migration decisions. Do not run a separate security audit unless requested.
