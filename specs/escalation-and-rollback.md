# Escalation And Rollback

## Problem

Computer-use agents can get stuck, exceed budgets, fail eval gates, or reach a
state where continuing is riskier than stopping. A harness needs clear policies
for escalation and rollback.

## Goals

- Define when to ask a human.
- Define when to stop, expire, kill, or mark failed.
- Define when worker restart is reasonable.
- Preserve retained history for inspection.

## Non-Goals

- Full human-in-the-loop product UI.
- Automatic browser state rollback.
- Durable workflow replay.
- Remote worker rescheduling.

## Architecture

- `EscalationDecision` captures policy, reason, and rollback hint.
- Lifecycle handlers persist stop/fail/delete events.
- WorkerLauncher provides stop and future restart boundaries.
- Retention keeps deleted/failed context until policy cleanup.

## Data Flow

1. Budget, eval, worker, or API error occurs.
2. Harness creates an escalation decision.
3. Policy chooses continue, ask human, stop session, restart worker, or mark
   failed.
4. Orchestrator records event/status and stops worker if needed.
5. Operator can inspect history, metrics, and retention report.

## Edge Cases

- Worker cannot be stopped cleanly.
- Restart would lose desktop state.
- Eval fails but task produced useful partial evidence.
- Human escalation is unavailable.
- Rollback cannot undo external website actions.

## Acceptance Criteria

- Escalation policy is documented and represented in code.
- Terminal status preserves history.
- Stop/delete paths clean up active workers.
- Docs state rollback is limited to local session/worker control today.
