---
name: research
description: Use when a task needs substantial investigation across primary sources or delegated research. Skip simple documentation lookups that a direct search can answer.
disable-model-invocation: false
metadata:
  opencode/autoinvoke: true
---

Use a background research agent when delegation is available, permitted and useful; otherwise research directly. Give delegated work a fresh context window.

Its job:

1. Investigate the question against **primary sources** (official docs, source code, specs, first-party APIs), not a secondary write-up of them. Follow every claim back to the source that owns it.
2. Cite the sources supporting the findings.
3. Save a Markdown report only when requested or required by the project workflow, following the existing location convention. Otherwise return the findings directly.
