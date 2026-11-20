# Debugging

A fix that targets a symptom hides the defect and adds a second one.

## Steps

1. **Read the failure.** The whole error, the stack, the exact inputs. Reproduce it on demand. If you cannot reproduce it, gather more evidence before touching code.
2. **Check what changed.** Recent commits, config, dependencies, environment.
3. **Instrument the boundaries.** When the failure crosses components, log what enters and leaves each one and run once. The evidence shows which boundary breaks. Guessing does not.
4. **Compare with working code.** Find a similar case that works and list every difference, however small.
5. **One hypothesis.** State it as "the cause is X because Y". Make the smallest change that tests it, one variable at a time. If it fails, form a new hypothesis. Do not stack fixes.
6. **Fix at the root.** Write the failing test first (`tdd.md`), apply one fix, confirm the test passes and the suite is green. Where the bad value entered, validate it there and at each layer it passes through.

## Stop rule

The stop after three failed fixes is in `instructions/global.md` in the agentkit repository. Three failures mean the model of the system is wrong, not the last guess. Question the design, tell the user what you learned, and agree the next step before a fourth attempt.

## Techniques

- **Backward trace.** Follow the bad value up the call chain to where it first went wrong, and fix there.
- **Wait on a condition, not a timer.** Replace sleeps in tests with a poll on the state you need.
- **Polluted tests.** When a test fails only after others run, bisect the test list to find the one that leaves state behind.

## Excuses that mean stop

- "Quick fix now, investigate later."
- "It's probably X, let me just change it."
- "One more attempt" after two failures.
