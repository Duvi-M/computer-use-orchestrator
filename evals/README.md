# Evals

This directory contains a lightweight offline benchmark for the Computer-Use
Agent Harness. It is intentionally safe for CI and interviews: it does not call
Anthropic, launch Docker, or require a live FastAPI server by default.

The eval demonstrates the expected harness shape:

1. create a session
2. send a goal/task
3. stream events
4. verify evidence/artifact
5. enforce timeout or budget
6. terminate the session

Run:

```bash
python3 evals/run_eval.py --json
```

The output is a JSON report with scenario status, eval gate results, trigger
events, and budget decisions. A future live mode can point these same scenarios
at the FastAPI API once CI has a worker sandbox available.
