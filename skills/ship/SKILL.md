---
name: ship
description: Use when the current changes are ready to go out as a pull request, from branch to green CI. Runs the repository's gate, commits, pushes, opens the pull request, watches CI and fixes failures. Stops before merge.
disable-model-invocation: true
---

# Ship

Typing this skill authorizes the branch, commit, push and pull request below, and nothing past them. The merge stays with the maintainer.

Run the steps in order. Each ends on a condition that must hold before the next starts.

## 1. Branch

Name the default branch with `git symbolic-ref --short refs/remotes/origin/HEAD`. On it, `git switch -c <name>` before anything else, carrying the working tree along. Take the name from the repository's recent branch names, or `<type>/<topic>` when none show a pattern.

Done when `git branch --show-current` is not the default branch.

## 2. Discover the conventions

Read, in this order, what the repository says about each item: `AGENTS.md`, `CONTRIBUTING.md`, the pull request template, CI workflow files, the Makefile.

- **Gate:** the command CI runs. Prefer a Makefile target.
- **Changelog:** hand-maintained, or generated from commits or PR titles (release-please, changesets, semantic-release).
- **Commit and PR title format**, and whether commits need a sign-off.

Done when each item has an answer taken from a file, or the file shows nothing and you use the plain default.

## 3. Gate

Run the gate. Save its output once. When it fails, rerun only the failing case before changing anything, fix the cause, and run the whole gate again.

Done when the gate exits 0 on the tree you will commit.

## 4. Changelog

Add an entry when the changelog is hand-maintained, in its existing format. A generated changelog stays as it is.

Done when the changelog matches what step 2 found.

## 5. Commit and push

Stage only the files this work changed. Make one commit in the repository's format, with a sign-off when step 2 found the requirement. Run `git push -u origin HEAD`. After a rejected push, rebase onto the remote and push again, never with force.

Done when `git status` is clean and the remote branch holds the commit.

## 6. Pull request

Open it with `gh pr create`, title in the repository's format and body from its template. The body says what changed and why, then lists the gate command and its result.

Done when `gh pr view --json url` returns the pull request.

## 7. CI

Run `gh pr checks --watch`. For each failing check, save `gh run view --log-failed` once, reproduce the failure locally on that case alone, fix it, commit, push, and watch again. Report and stop after three fix rounds.

Done when every check passes, or the repository has none.

## 8. Report

Give the pull request URL, the check status and anything you skipped or could not verify.
