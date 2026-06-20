# loop_until_done

## Use Case

Iterate on a narrow goal until eval gates pass or a budget/escalation threshold
is reached.

## Workflow Shape

1. Attempt.
2. Evaluate.
3. Patch the smallest failing part.
4. Retry.
5. Complete only with evidence or escalate.

## Contract

- Required outputs: final answer, evidence, eval status.
- Budgets: max attempts, runtime, messages, events, optional token/cost cap.
- Tool grants: limited to tools required for the loop.
- Completion: eval gates pass and evidence exists.

## Expected Evidence

- Attempt records.
- Eval failures and patches.
- Final evidence artifact or trace.

## Failure Handling

- Repeated same failure: escalate.
- Goal drift: reload original contract.
- Context exhaustion: use durable trace/state instead of relying on chat memory.

## When Not To Use It

- Obvious one-shot fixes.
- Large ambiguous goals without acceptance criteria.
- Workflows requiring broad strategy changes each iteration.
