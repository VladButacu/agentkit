# Brainstorming

Turn a new or unclear request into an approved design before any code exists. Nothing is built, scaffolded or committed until the user has approved the design. A spike the user agreed to is the one exception, and its output is thrown away unless the design is approved.

Skip this for a request that already carries everything that matters. Do it, and say what you did.

## Steps

1. Read what the request touches: the code, the docs, the recent commits. Do not ask what the repository answers.
2. Echo the request back in a few lines, including anything the user may not have considered. Ask one open question about why, before offering options. Options steer, so let the user describe the need first.
3. Offer two or three approaches in a message of their own. Lead with the smallest that fully works, and say what each one leaves out. Wait for the user to pick.
4. Write the design for the chosen approach, sized to the change. A small change gets a few lines. A project gets goals, the interfaces, the data flow, error handling and how it will be verified. Play it back in chunks and wait for a yes on each. Approval covers only what the user saw.
5. For a design that others will build from, dispatch the `blind-reviewer` subagent on it with this rubric: report only the questions where a wrong guess would change the result. Sort the answers into three groups: settled by the design, minor and decided by you with the decision marked as yours, and the user's to decide. Put the last group to the user in one batch. One round only. Without the subagent, reread the design cold and apply the same rubric.
6. Hand the approved design to `writing-plans.md`, or to the work itself when it is small.

Done when the user has said yes to the design as written.
