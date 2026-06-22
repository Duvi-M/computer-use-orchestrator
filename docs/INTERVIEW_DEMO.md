# BOS.PRO Interview Demo

This is the 5-7 minute live demo path. Keep it terminal-first and show the
project as an agentic harness, not primarily as a SaaS app.

## Before The Call

```bash
make interview-check
```

Optional cleanup:

```bash
scripts/clean_demo_state.sh
```

## 0. One-Sentence Setup

Say:

```text
This is an agentic harness for computer-use agents: specs become contracts,
contracts drive a goal/plan/action/evidence loop, worker events become
observations and evidence, eval gates decide whether the agent is actually
done, and traces/memory preserve state across runs.
```

## 1. Show Specs

Open:

```text
specs/agentic-harness.md
specs/multi-agent-harness.md
specs/spec-kit/agentic-harness/spec.md
specs/spec-kit/agentic-harness/plan.md
specs/spec-kit/agentic-harness/tasks.md
```

Command:

```bash
python3 scripts/interview_demo.py map
```

Talk track:

- Custom specs are practical for brownfield evolution.
- Spec Kit format is useful for greenfield structure.
- The code is traceable back to requirements and tests.

## 2. Run tmux Harness Loop

Use tmux if available:

```bash
scripts/run_harness_tmux.sh harness-demo tokyo-run "search Tokyo weather"
```

If tmux is noisy during the call, use bounded CLI mode:

```bash
python3 scripts/interview_demo.py loop
```

Show checkpoint:

```bash
cat data/interview_checkpoints/interview-loop.json
```

Talk track:

- The loop is `goal -> plan -> action -> observation -> evidence ->
  evaluation`.
- Checkpoints are frequent so a run can survive terminal/SSH interruption.
- Semantic memory is deduplicated; checkpoint ticks do not spam memory.

## 3. Show Memory

```bash
python3 scripts/interview_demo.py memory
```

Expected signal:

```text
memory recall query='search Osaka weather' -> 1 matches found
```

Talk track:

- Local demo uses file-backed memory by default.
- mem0 remains optional when a valid OpenAI key exists.
- This is flat memory; temporal knowledge graph memory such as Zep + Graphiti is
  roadmap for entity/relation/time-aware recall.

## 4. Show Runtime Adapter And Evals

```bash
python3 scripts/interview_demo.py session-harness
python3 scripts/interview_demo.py eval
```

Talk track:

- `SessionHarness` consumes worker-style events.
- Events become observations, evidence, eval-gate results, and traces.
- The worker execution path remains unchanged.
- Evals prevent trusting “done” without evidence.

## 5. Run Parallel Agents

Safe version:

```bash
python3 scripts/interview_demo.py agents
```

Real tmux/worktree version:

```bash
scripts/spawn_agents.sh 3
```

Show worktrees:

```bash
git worktree list
```

Show distribution:

```bash
python3 scripts/interview_demo.py agents --agents 6 --tasks 24
```

Talk track:

- One agent per git worktree prevents filesystem write conflicts.
- Shared task list is SQLite-backed.
- `BEGIN IMMEDIATE` gives a single-writer claim path.
- Tasks complete across multiple agents without double assignment.

## 6. Explain FastAPI Backend As Runtime

Say:

```text
The FastAPI/Docker/noVNC system is the runtime backend. It gives the harness real
worker events, SSE, session lifecycle, ownership checks, and a worker launcher
boundary. It is secondary to the harness story, but it proves the harness can
attach to a real Computer Use runtime.
```

Optional commands if Docker/API are ready:

```bash
make build-worker
make run-api
make run-web
```

Open:

```text
http://127.0.0.1:5173
http://127.0.0.1:9000/readyz
http://127.0.0.1:9000/metrics
```

## Closing Line

Say:

```text
The main idea is not that the model is smarter. The harness makes agent work
bounded, observable, resumable, and verifiable.
```

## Honest Limitations

- Not a hosted SaaS yet.
- Local auth and local Docker are development trust boundaries.
- File-backed memory is not a temporal knowledge graph.
- Multi-agent demo shows coordination substrate, not independent reasoning
  agents.
- Remote worker launcher, object storage, deployment, billing, and compliance
  are production roadmap.
