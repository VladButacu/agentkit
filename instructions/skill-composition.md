# Skill composition

Several skills can apply to one task. Their kind decides how many run at once.

| Kind | Active at once | Governs | Skills |
| --- | --- | --- | --- |
| Workflow | One | Which steps run, and in what order | The Superpowers chain (`brainstorming`, `writing-plans`, `subagent-driven-development` or `executing-plans`, `finishing-a-development-branch`, with `test-driven-development`, `systematic-debugging` and `verification-before-completion` inside it), `desloppify`, `research`, `retro`, `vault-dream` |
| Mode | Any | The size and form of each output | `ponytail` for code, `prose` for text a person reads, `writing-for-agents` for text an agent reads |
| Tool | Any | One bounded job inside a step | `codebase-design`, `domain-modeling`, `to-tickets`, `release-notes`, `repo-bootstrap`, `makefile-generator`, `pyproject-generator`, the Obsidian and vault skills, including `vault-prune` |

The user's instructions and `AGENTS.md` come first. Below them, a workflow decides which steps run and a mode decides how large each step's output is. A mode never removes a workflow step, and a workflow never grows an output past what the mode allows.

## Ponytail inside Superpowers

| Superpowers step | Ponytail's part |
| --- | --- |
| `brainstorming`, laying out approaches | The first approach is the smallest that fully works, with one line on what it leaves out |
| `writing-plans` | Each task names the helper, library or pattern it reuses before it plans new code |
| `test-driven-development`, green | Ponytail's ladder defines minimal code |
| Reviewer subagents | Ponytail's review order: correct, safe, holds under load, tested, fast, lean |
| `verification-before-completion` | The evidence comes first; Ponytail's closing line on what was skipped follows it |

## Collisions

| Situation | Use |
| --- | --- |
| A change alters behavior | `test-driven-development`: the test comes first |
| A change alters no behavior (a rename, a comment, a config value, copy) | No new test |
| "Review this" outside a plan | `ponytail-review` |
| Review inside a Superpowers plan | `superpowers:requesting-code-review` and the plan's reviewer subagents |
| A one-off codebase audit | `ponytail-audit` |
| A tracked cleanup with a scored queue | `desloppify` |
| New or unclear work, or pressure-testing an existing plan | `superpowers:brainstorming` |
| Domain terms, a glossary or an architecture decision | `domain-modeling` |
| The task asks for an interface or boundary change | `codebase-design` picks the interface and `ponytail` sizes the code behind it. Otherwise keep the structure the codebase has |
| An approved plan becomes tickets | `to-tickets`, after `superpowers:writing-plans` |
| Creating or changing a skill | `superpowers:writing-skills`, with `writing-for-agents` for wording and invocation |
| A failed Superpowers session | `superpowers:diagnosing-superpowers` for evidence, then `retro` for setup changes |
| A research question | `vault-recall`, then `research` |

Claude Code's own `/code-review`, `/simplify` and `deep-research` run only when the user names them.

## Subagents

| Subagent | Dispatched by | What the separate context buys |
| --- | --- | --- |
| `blind-reviewer` | `prose` for its final review, `desloppify` for blind scoring, `vault-lint` for its judgement checks | A judgement of the artifact against a rubric, made without the author's conversation and with read-only tools |
| `scout` | `retro` for session logs, `to-tickets` for the current state of the code, `vault-recall` for a wide search, `vault-prune` for claim checks across many notes, `vault-dream` for a long digest | Raw reads stay out of the caller's context, and only a cited summary returns |

`research` and `codebase-design` dispatch their own agents, so they keep each tool's general-purpose agent.

Both subagents reach every supported tool, and run on the model of the session that dispatches them:
- **Claude Code:** under its native plugin they are named `agentkit:blind-reviewer` and `agentkit:scout`.
- **Codex:** they have no shell, but Codex cannot narrow its parent's sandbox, so they stay read-only only through their instructions.

Where a subagent is missing, each calling skill says how to do the work without it.

Ponytail reaches every subagent through its `SubagentStart` hook. Superpowers' skill router does not: `using-superpowers` loads at session start and tells subagents to ignore it. The global rules in `instructions/global.md` do reach subagents, so their rule to invoke every matching skill first is what makes a subagent load one. A dispatching agent that names the skills in the prompt adds to that rule and does not replace it: subagents given a list of skills invoked some and skipped others.
