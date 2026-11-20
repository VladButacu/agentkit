# Verification

Claims that work is done, fixed or passing rest on the evidence `instructions/global.md` in the agentkit repository requires.
Words that signal a skipped check: "should", "probably", "seems to", "looks right". Satisfaction before the run ("Done!") is the same signal.

## Gate

1. Name the repository's gate (its Makefile target or CI job), then the command that proves the claim.
2. Run each in full, now.
3. Read the output and the exit code.
4. State what it shows, including failures.
5. Only then claim the result.

## What proves what

| Claim | Evidence | Not enough |
| --- | --- | --- |
| Tests pass | Test run with zero failures | An earlier run, or "it should pass" |
| Build works | Build command exits 0 | A passing linter |
| Bug is fixed | The original symptom no longer reproduces | The code changed |
| Regression test works | Red then green (below) | Green once |
| Delegated work is done | The diff, read by you | The agent's report |
| Requirements met | Each requirement checked against the result | Tests pass |

## Regression test cycle

Write the test and see it pass. Revert the fix and see the test fail. Restore the fix and see it pass. A test that stays green with the fix removed does not guard anything.

## Report

Say what you ran and what it showed. Name anything you skipped or could not check.
