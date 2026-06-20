# adversarial_verification

## Use Case

Check whether an agent result is complete, grounded, and evidence-backed before
accepting it.

## Workflow Shape

1. Primary loop produces result and evidence.
2. Independent verifier reviews contract and trace.
3. Verifier checks missing outputs, weak evidence, and goal drift.
4. Result is accepted, patched, retried, or escalated.

## Contract

- Required outputs: primary answer, evidence, verifier decision.
- Budgets: separate small verifier budget.
- Tool grants: verifier should prefer read-only evidence access.
- Completion: verifier passes acceptance criteria.

## Expected Evidence

- Raw trace from primary run.
- Verifier notes.
- Pass/fail decision with reasons.

## Failure Handling

- Missing evidence: retry narrow patch loop.
- Self-preference risk: require independent verifier.
- Dangerous ambiguity: ask human.

## When Not To Use It

- Low-risk formatting edits.
- Mechanical refactors already covered by tests.
- Tasks where human review is faster than verifier setup.
