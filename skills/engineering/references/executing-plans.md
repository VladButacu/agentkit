# Executing plans

Run an approved plan task by task, inline or with fresh subagents per task. The same rules hold for both.

## Setup

1. Work in an isolated branch or worktree (`branch-hygiene.md`) with a green baseline.
2. Create a ledger file outside the tracked tree, named for the plan. One line per finished task. It outranks memory: after a compaction or a restart, read the ledger and `git log` and resume from them. Never redo a task the ledger lists.
3. Scan the plan once. For any two tasks that share a file or an interface, and any task that contradicts itself, record a ruling before starting.

## Per task

1. Record `BASE` as the commit sha before the task. Never use `HEAD~1`.
2. Write the task's text and the paths it needs to a brief file. Pass the path. A subagent given pasted history gets a bloated prompt and less attention on the task.
3. The implementer follows `tdd.md`, runs the suite, and writes its full report to a file. It returns a short status: done, done with concerns, blocked, or needs context. It does not dispatch subagents.
4. Handle the status. Concerns about correctness or scope are fixed before review. Needs context: supply it and rerun. Blocked: add context, use a stronger model, split the task, or rule on a plan correction. Do not repeat the same attempt.
5. Review the range `BASE..HEAD` with a fresh `blind-reviewer`. Give it the task text, the diff and the plan's review focus. Its rubric: spec compliance, then quality. It does not trust the report, never lowers a finding because the implementer explained it, and does not rerun the suite. A defect the plan mandated is still reported, labelled as plan-mandated.
6. Fix findings in rounds. Each round is one fix and one review of the fix diff only. After five rounds, rule on what remains, record it, and move on. Minor findings are logged and do not enter the loop.
7. Record the task in the ledger only when its tests pass.

Never run implementers in parallel on tasks that share files.

## Without subagents

Do the same loop inline. Before each review, reread the diff cold against the task text.

## Stopping

Do not check in between tasks. Stop only for an irreversible or destructive step, a security-sensitive step, a side effect outside the worktree such as a merge, push or publish, or a plan so broken that every path forward is a guess. Otherwise record `Ruling: <what> | <why> | <cost if wrong>` and continue.

## End

One final review of the whole branch with a fresh `blind-reviewer`. Tell it to list what it declined to judge, and rule on each line. Treat the design as a vision: silence in it is not permission. Fix Critical and Important findings with a test that goes red then green. Report the rulings you made, the deferred minors, and the evidence from `verification.md`. Then `branch-hygiene.md`.
