# fan_out_and_synthesize

## Use Case

Run several isolated sessions against independent subtasks, then synthesize a
single result from their evidence.

## Workflow Shape

1. Split goal into independent contracts.
2. Run sessions in parallel.
3. Store a trace per session.
4. Verify each result independently.
5. Synthesize only verified evidence.

## Contract

- Required outputs: subtask answer, evidence path, final status.
- Budgets: per-session runtime/message/event limits.
- Tool grants: scoped to each subtask.
- Completion: every required subtask passes eval or is explicitly excluded.

## Expected Evidence

- One trace per worker/session.
- Evidence paths for each accepted result.
- Synthesis summary that cites accepted traces.

## Failure Handling

- Failed subtask: retry narrowly or exclude with reason.
- Conflicting evidence: escalate to human or adversarial verifier.
- Budget exceeded: keep partial trace and stop that branch.

## When Not To Use It

- Strongly sequential workflows.
- Tasks that share mutable state without locks.
- Simple tasks where parallelism only adds overhead.
