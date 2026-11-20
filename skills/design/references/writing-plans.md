# Writing plans

Write a plan from an approved design for an implementer who has the code but not the conversation. The plan carries the decisions that implementer cannot make alone and nothing else. A plan longer than the code it describes has written the code instead.

## Header

- The design it implements, linked.
- Global constraints that hold for every task: compatibility, style, dependencies, performance.
- A review focus: the few failure modes most likely to bite, each with the test that owns it.

## Each task

- **Interfaces**: what it consumes from earlier tasks and what it produces for later ones, by name and shape. A task reader sees only its own task, so this block is what keeps tasks consistent.
- **Steps**: one checkable action each. Each ends with `Expected:` and the output that proves the step worked.
- Test steps come before the code they cover, and each names the production change that would make the test fail.

## Self-review before handing over

1. Every requirement in the design maps to a task.
2. Every interface a task consumes is produced by an earlier task.
3. No step says "handle edge cases" or "add tests" without naming them.
4. Any two tasks that touch one file or interface have a ruling on which goes first.
5. Proportion: if the plan is several times longer than the change, cut it to the decisions.

Then ask which way to run it: `executing-plans.md` in the `engineering` skill, or `to-tickets.md` to publish tickets. Give a one sentence recommendation.
