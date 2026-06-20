# Evals

## Problem

Harness quality should be demonstrable without relying only on manual UI demos.
The repo needs a small eval shape that can later grow into live agent
benchmarks.

## Goals

- Provide an offline eval that is safe in CI.
- Model create session, send goal, stream events, verify evidence, enforce
  budget, and terminate session.
- Produce a simple JSON or console report.
- Keep live Anthropic/Docker evals out of default tests.

## Non-Goals

- Full benchmark suite.
- Browser automation against real websites.
- Paid model calls in CI.
- Long-running worker stress tests.

## Architecture

- `evals/scenarios/` stores scenario definitions.
- `evals/run_eval.py` runs the offline harness simulation.
- Eval gates come from `computer_use_demo/harness/eval_gates.py`.
- Future live mode can call FastAPI endpoints with a local worker sandbox.

## Data Flow

1. Load scenario JSON.
2. Build goal, budgets, and tool grants.
3. Simulate lifecycle triggers.
4. Record observation and evidence.
5. Evaluate gates.
6. Print JSON report.

## Edge Cases

- Missing evidence.
- Budget exceeded.
- Tool grant denied.
- Scenario file malformed.
- Eval gate fails after session finish.

## Acceptance Criteria

- `python3 evals/run_eval.py --json` exits 0.
- Report includes scenario, gates, budget decision, and triggers.
- Tests cover eval gates directly.
- Docs state offline evals are not proof of real-world task success.
