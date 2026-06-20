# tournament

## Use Case

Compare multiple agents, prompts, or strategies against the same contract and
promote the best evidence-backed result.

## Workflow Shape

1. Run candidates independently.
2. Score with shared eval gates.
3. Compare evidence and failure reasons.
4. Select winner or escalate.

## Contract

- Required outputs: candidate result, evidence, score, winner.
- Budgets: per-candidate and total tournament budget.
- Tool grants: same grants for each candidate unless intentionally varied.
- Completion: winner passes minimum acceptance criteria.

## Expected Evidence

- Trace per candidate.
- Eval scores.
- Selection rationale.

## Failure Handling

- All candidates fail: escalate.
- Scores tie: prefer cheaper/simpler result or ask human.
- Candidate exceeds budget: exclude it.

## When Not To Use It

- Normal CRUD/API changes.
- Cheap tasks where one well-tested implementation is enough.
- Shared mutable environments without isolation.
