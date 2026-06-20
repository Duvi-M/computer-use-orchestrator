# classify_and_act

## Use Case

Route a user goal into one of a small number of safe execution paths before
launching expensive computer-use work.

## Workflow Shape

1. Classify the goal.
2. Select a narrow contract.
3. Execute the smallest matching action path.
4. Verify evidence.
5. Complete or escalate.

## Contract

- Required outputs: classification, selected action, evidence.
- Budgets: short runtime, low message count.
- Tool grants: only the tools needed for the selected class.
- Completion: evidence recorded and eval gates pass.

## Expected Evidence

- Classification label.
- Action selected.
- Observation or artifact proving the selected action ran.

## Failure Handling

- Unknown class: ask human.
- Ambiguous class: stop before worker execution.
- Budget exceeded: mark failed and retain trace.

## When Not To Use It

- One obvious mechanical task.
- A bug fix where classification adds ceremony.
- Tasks requiring open-ended exploration.
