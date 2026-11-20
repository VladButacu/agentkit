Use a background research agent when delegation is available, permitted and useful; otherwise research directly. Give delegated work a fresh context window.

0. **Vault first.** If `AGENTS.local.md` (`~/.config/agentkit/AGENTS.local.md`) names a knowledge vault, check it with the `vault` skill's `references/vault-recall.md` before researching from scratch. If it names no vault, skip this step.

Its job:

1. Investigate the question against **primary sources** (official docs, source code, specs, first-party APIs), not a secondary write-up of them. Follow every claim back to the source that owns it.
2. Cite the sources supporting the findings.
3. Save a Markdown report only when requested or required by the project workflow, following the existing location convention. Otherwise return the findings directly.
