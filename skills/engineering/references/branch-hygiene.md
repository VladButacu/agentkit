# Branches and worktrees

## Start

1. Check whether you are already isolated: `git rev-parse --git-dir` differs from `git rev-parse --git-common-dir` inside a linked worktree. If so, use it. In a submodule the two also differ, so rule that out first.
2. Otherwise prefer the tool's own worktree command. A raw `git worktree add` where the tool has one leaves state the tool cannot see. Fall back to `git worktree add` in a directory that `git check-ignore` confirms is ignored.
3. Install dependencies and run the suite. If the baseline fails, report it and let the user decide.

## Finish

1. Run the full suite. If it fails, stop and fix it first.
2. Offer the user three outcomes: merge locally, open a pull request (`ship` in the `repo-ops` skill does this), or keep the branch as it is.
3. Delete a branch or a worktree only when the user types the word `discard`. Never use `--force`, force-push or force-remove unasked. A rejected push means the remote moved, so fetch and look.
4. After a merge or a discard, remove only worktrees you created.
