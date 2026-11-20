# Test-driven development

No production code without a failing test first. The test is the specification, so a test written after the code only describes what the code already does.

Code written before its test is deleted and rewritten from the test. Keeping it as a reference is not deleting it.

## Cycle

1. **Red.** Write one test for one behavior. Run it and watch it fail for the reason you expect. A test that has never failed has not been shown to test anything.
2. **Green.** Write the least code that passes. Run the whole suite, not one file. A scope limit on the task bounds the deliverable, not the verification.
3. **Refactor.** Clean up with the suite green. Add no behavior.

Trivial changes that alter no behavior (a rename, a comment, a config value, copy) need no new test.

## A good test

- Names the production change that would make it fail. If you cannot say which change, rewrite it.
- Takes expected values from the specification or from a hand calculation, written as literals. An expectation computed by the code under test cannot disagree with it.
- Tests behavior through the interface. A constant's value is not behavior. Test what depends on it.
- Uses the lowest layer that observes the behavior, and real objects before mocks.

## Excuses that mean stop

- "Too simple to test." Simple code breaks, and the test takes a minute.
- "I'll test after." Tests that pass at once prove nothing.
- "I already tested it by hand." That cannot be rerun.
- "Deleting this is wasteful." The sunk cost is the trap.
- "This one is different." It is the case the rule exists for.
