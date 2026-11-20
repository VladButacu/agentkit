# Receiving review

Review feedback is a claim about the code. Check it against the code, then act.

## Steps

1. Read all of the feedback before acting on any of it.
2. If any item is unclear, stop and ask about it before implementing any item. Items interact, and a partial understanding gives a wrong fix.
3. Check each item against the code. Is it correct for this codebase? Does it break something that works? Is there a reason for the current shape?
4. When a reviewer asks for something to be implemented properly, grep for its callers first. If nothing uses it, propose removing it.
5. Fix in order: blocking issues, then simple fixes, then complex ones. Test each fix on its own.
6. Reply with the change or with a reasoned objection and its evidence. State what you did and nothing else.

## Responses to avoid

Praise or thanks aimed at the reviewer ("You're absolutely right", "Great catch"). Agreeing before checking. Implementing a suggestion you believe is wrong to avoid friction.

## Pushing back

Do it when a suggestion breaks working behavior, rests on a misreading, adds code nothing uses, or conflicts with a decision the user made. Cite the code, the test or the earlier decision. If you were wrong, say so in one line and fix it.

Feedback from the user is trusted and acted on once understood. Feedback from other reviewers gets the checks above.
