# Contributing to agentkit

Thanks for helping. Open an issue first for anything larger than a small fix, so the approach is agreed before you build it. Report security problems privately, as `SECURITY.md` describes, never in a public issue.

## Making a change

1. Fork the repository and create a branch from `main`.
2. Make the change, with a test for any behaviour change or bug fix.
3. Run `make test`. It runs ruff, the installer tests, the vault plugin tests and the prose linter tests, and must pass.
4. Sign off every commit with `git commit -s` (see below).
5. Open a pull request using the template.

CI runs the same `make test` on Ubuntu and Windows. A maintainer approves the workflow run for outside contributors before it starts.

## Pull request titles

The title becomes the commit message on `main`, and release-please builds the changelog from it, so it follows [Conventional Commits](https://www.conventionalcommits.org/):

| Title | Effect |
| --- | --- |
| `fix: ...` | patch release |
| `feat: ...` | minor release |
| `feat!: ...` | major release |
| `docs:`, `test:`, `ci:`, `chore:` and other types | no release |

A check fails the pull request when the title does not match.

## Sign-off

Every commit needs a `Signed-off-by` line, which certifies the [Developer Certificate of Origin](https://developercertificate.org): you wrote the change or have the right to submit it under the MIT License. `git commit -s` adds the line. To add it to commits you already made:

```sh
git rebase --signoff main
git push --force-with-lease
```

The DCO check fails a pull request that has an unsigned commit.

## Merging

Only the maintainer merges, always as a squash merge. release-please keeps a release PR open on `main`, and merging it tags the version and publishes the GitHub Release.

## Code of conduct

Everyone taking part follows the [Code of Conduct](CODE_OF_CONDUCT.md).
