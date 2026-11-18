---
name: research
description: Use when a task needs substantial investigation across primary sources, a comparison of options, or the history or trend of something. Trigger on phrasings such as "look into X", "compare A and B", "what's the state of X", "what changed in X" or any question that needs official docs or source code rather than a quick lookup. Run vault-recall first when the answer may already be filed. Skip simple documentation lookups that a direct search can answer.
metadata:
  opencode/autoinvoke: true
---

Use a background research agent when delegation is available, permitted and useful; otherwise research directly. Give delegated work a fresh context window.

Its job:

1. Investigate the question against **primary sources** (official docs, source code, specs, first-party APIs), not a secondary write-up of them. Follow every claim back to the source that owns it.
2. Cite the sources supporting the findings.
3. Save a Markdown report only when requested or required by the project workflow, following the existing location convention. Otherwise return the findings directly.
