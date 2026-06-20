# Budgets And Safety

## Problem

Computer-use sessions can consume provider tokens, worker runtime, local
resources, and operator attention. A harness needs explicit budgets and clear
stop policies.

## Goals

- Represent runtime, idle, message, event, token, and cost budgets.
- Enforce implemented runtime, idle, message, and event limits server-side.
- Keep token and cost budgets as documented placeholders until provider usage
  reconciliation is added.
- Emit quota/lifecycle events when budgets are exceeded.

## Non-Goals

- Billing integration.
- Stripe or invoices.
- Provider cost reconciliation.
- Per-tool fine-grained kernel sandboxing.

## Architecture

- Runtime limits live in environment config.
- Route handlers enforce message/session limits.
- Cleanup logic expires idle or over-runtime sessions.
- `computer_use_demo/harness/budgets.py` provides a small budget decision model.

## Data Flow

1. Settings load budget limits.
2. Session creation checks concurrent user/org budgets.
3. Message submission checks status, runtime, idle, and message count.
4. Event insertion can be capped by event budget.
5. Exceeded budgets record events and stop/deny work.

## Edge Cases

- A budget is zero or invalid.
- Multiple limits are exceeded at the same time.
- Kill switch is enabled while a session is active.
- A stopped worker still has retained events.

## Acceptance Criteria

- Tests cover concurrent limits and max messages.
- Harness budget model returns exceeded budget names.
- README explains implemented and placeholder budgets honestly.
- Default local values remain permissive for demos.
