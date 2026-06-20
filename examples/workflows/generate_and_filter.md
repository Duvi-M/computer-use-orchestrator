# generate_and_filter

## Use Case

Generate multiple candidate outputs, filter them with deterministic gates, and
keep only candidates with evidence.

## Workflow Shape

1. Generate candidates under a contract.
2. Evaluate each candidate against acceptance criteria.
3. Discard candidates with missing evidence.
4. Select or synthesize from passing candidates.

## Contract

- Required outputs: candidates, filter criteria, selected result, evidence.
- Budgets: candidate count, eval budget, total runtime.
- Tool grants: usually read-only unless candidate execution is required.
- Completion: at least one candidate passes or the workflow escalates.

## Expected Evidence

- Candidate list.
- Gate result per candidate.
- Selection rationale.

## Failure Handling

- No candidate passes: retry with narrowed prompt or ask human.
- Filter is subjective: use independent verifier.
- Too many candidates: stop at budget.

## When Not To Use It

- Single deterministic implementation tasks.
- Cases where candidate diversity is not useful.
