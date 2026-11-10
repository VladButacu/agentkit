---
name: release-notes
description: Use when a changelog entry must become user-facing release notes for a release. Skip changelogs that stay internal.
disable-model-invocation: false
metadata:
  opencode/autoinvoke: true
---

# Release notes

Turn the newest released changelog version into notes a reader with no technical background understands and cares about. The changelog stays technical; the notes translate it.

## Discover the convention first

Find how this repository publishes notes before writing: a `RELEASE_NOTES.md`, a `docs/releases/` folder, GitHub or GitLab releases, or nothing yet. Read one existing entry and follow its structure. With no established destination, ask the user where the notes go and do not invent one.

## Source of truth

Work only from the changelog section for the version being released. Every claim in the notes traces to a line in it. No invented features, no numbers the changelog does not contain, no promises about the future.

## Voice

Write to "you". Warm, plain words, no hype, no superlatives, no jargon. Say what the reader can now do, not what the code does. A sentence the reader cannot act on or picture does not belong.

## Shape

Open with two or three sentences of prose carrying the release's point. Group the rest under headings the reader recognizes (what is new, what changed, what got fixed). End with a "Good to know" section for behavior changes, requirements and caveats the reader must act on.

## Translate

Each technical change becomes the reader's outcome. Use the project's own words for features. When a term cannot be avoided, give it one plain sentence of meaning in place, the first time it appears. Read the result aloud once; anything you cannot say without slowing down is not done.
