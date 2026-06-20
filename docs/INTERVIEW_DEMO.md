# Interview Demo

This is the 10-minute live demo path for the Business Operating System / agentic
harness interview. It is intentionally terminal-first: the point is to show
spec-driven thinking, agent loop control, memory, evals, and orchestration.

## Timing

- 1 min: explain the product/harness framing.
- 2 min: show specs and how implementation follows them.
- 2 min: run the durable loop and memory recall.
- 2 min: run evals and explain evidence gates.
- 2 min: show parallel coordination and worktree isolation.
- 1 min: show the SaaS control plane boundaries.

## One-Sentence Pitch

This project is a production-style control plane and harness for computer-use
agents: it turns a goal into a bounded, observable loop with evidence, memory,
eval gates, budgets, worker isolation, and recovery.

## Preflight

```bash
make interview-check
```

If you do not want the full pytest suite during the live call, run this before
the interview and keep the terminal output available.

## 1. Spec-Driven Development

Open these files:

```text
specs/agentic-harness.md
specs/spec-kit/agentic-harness/spec.md
specs/spec-kit/agentic-harness/plan.md
specs/spec-kit/agentic-harness/tasks.md
specs/multi-agent-harness.md
specs/spec-kit/multi-agent-harness/spec.md
```

Talk track:

- The repo keeps original brownfield specs and Spec Kit versions side by side.
- Original specs are faster for evolving an existing codebase.
- Spec Kit is cleaner for greenfield feature shape: `spec.md`, `plan.md`,
  `tasks.md`.
- The implementation is traceable from spec to tests.

Quick map:

```bash
python3 scripts/interview_demo.py map
```

## 2. Durable Agent Loop

```bash
python3 scripts/interview_demo.py loop
```

What to point out:

- `Goal -> Plan -> Action -> Observation -> Evidence -> Evaluation`.
- The loop checkpoints frequently under `data/interview_checkpoints/`.
- The loop can run inside tmux with `scripts/run_harness_tmux.sh`.
- Checkpointing is separate from semantic memory.

Optional tmux form:

```bash
scripts/run_harness_tmux.sh harness-demo tokyo-run "search Tokyo weather"
```

## 3. Memory Recall

```bash
python3 scripts/interview_demo.py memory
```

Expected signal:

```text
memory recall query='search Osaka weather' -> 1 matches found
```

Talk track:

- Local demo uses file-backed memory by default.
- Memories are deduplicated by semantic evidence signature.
- mem0 is optional when a valid OpenAI key exists.
- This is flat memory, not a temporal knowledge graph.
- For a temporal knowledge graph, use something like Zep + Graphiti to track
  entities, relationships, timestamps, and changing facts.

## 4. Evals

```bash
python3 scripts/interview_demo.py eval
```

Talk track:

- The agent saying “done” is not enough.
- The eval checks evidence, terminal loop state, budgets, tool grants, and
  emitted triggers.
- This is the shape of `modification -> benchmark -> production`.

## 5. Parallel Orchestration

Safe queue demo without tmux:

```bash
python3 scripts/interview_demo.py agents
```

Real tmux/worktree demo:

```bash
scripts/spawn_agents.sh 3
```

Talk track:

- Each code-writing agent needs a separate git worktree.
- Worktree isolation prevents write conflicts in the filesystem.
- Shared work must go through a single-writer coordination point.
- The SQLite queue uses `BEGIN IMMEDIATE` so two agents cannot claim the same
  task.

## 6. SaaS Control Plane

If Docker and Anthropic API are ready:

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
http://127.0.0.1:9000/admin/retention
```

Demo task:

```text
Open a browser, search for the current weather in Tokyo, and tell me the temperature.
```

Talk track:

- FastAPI orchestrator owns session lifecycle, tenancy, quotas, SSE, noVNC
  access, persistence, metrics, and retention.
- `WorkerLauncher` keeps Docker-specific details behind a boundary.
- Production would replace local auth, local Docker, local artifacts, and
  development trust boundaries.

## Requirement Map

| Vacancy requirement | Repo signal | Demo command |
| --- | --- | --- |
| Spec-driven dev | `specs/` and `specs/spec-kit/` | `python3 scripts/interview_demo.py map` |
| Agentic scaffolding | `computer_use_demo/harness/loop.py` | `python3 scripts/interview_demo.py loop` |
| Memory layer | `computer_use_demo/harness/memory.py` | `python3 scripts/interview_demo.py memory` |
| Evals | `evals/run_eval.py` | `python3 scripts/interview_demo.py eval` |
| Parallel agents | worktrees + SQLite queue | `python3 scripts/interview_demo.py agents` |
| Persistence | tmux + checkpoints | `scripts/run_harness_tmux.sh ...` |
| SaaS orchestration | FastAPI + WorkerLauncher | `make run-api`, `make run-web` |

## Honest Limitations

- This is not a hosted SaaS yet.
- Local dev auth is not production auth.
- Local Docker is a trust boundary.
- File-backed memory is flat keyword memory, not a temporal knowledge graph.
- The multi-agent demo shows coordination substrate, not independent reasoning
  agents.
- Object storage, hosted deployment, billing, compliance, and remote worker
  launchers remain production work.
