# Python testing

Run tests with the repository's own environment and commands: the configured venv interpreter directly, or the repository's `make` target. Do not pipe, redirect or wrap test-runner output through `head`, `tail`, `grep`, files or timeouts; trust the runner's own summary line to judge pass or fail, and rerun a single failing test by name when you need its full output.

Prefer unit tests. Use property-based tests only for complex invariants that unit tests cannot cover, and never override Hypothesis `max_examples` per test: the central conftest owns the budget. Use efficient fixtures, with session-scoped database and artifact setup where safe. Fix failing checks rather than ignoring their origin. Add no noqa unless strictly necessary.
