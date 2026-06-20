# Execution Contracts

## Problem

Agentic systems drift when tasks are described only in conversational context.
Each session needs a durable contract that defines what must be produced, which
tools are allowed, how much budget can be spent, and when to escalate.

## Goals

- Define required outputs before execution.
- Attach budgets and tool grants to the task.
- Define completion conditions and evidence paths.
- Carry an escalation policy with the contract.

## Non-Goals

- Full workflow language.
- Contract negotiation UI.
- Billing enforcement.

## Architecture

- `ExecutionContract` lives in `computer_use_demo/harness/contracts.py`.
- Budgets are represented by `SessionBudgets`.
- Tool permissions are represented by `ToolGrantPolicy`.
- Output and budget validation are unit-tested.

## Data Flow

1. Caller defines goal and required outputs.
2. Harness validates tool grant before action.
3. Harness checks budget snapshot during or after execution.
4. Eval gates check completion evidence.
5. Escalation policy decides stop, ask human, restart, or mark failed.

## Edge Cases

- Required output is missing.
- Tool grant is denied.
- Multiple budgets fail at once.
- Evidence path is declared but not written.

## Acceptance Criteria

- Contract validation can pass and fail deterministically.
- Denied tools raise a clear error.
- Budget failures include exceeded budget names.
- Docs state contracts constrain the agent before execution.
