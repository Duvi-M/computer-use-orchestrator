# Dynamic Workflows

## Problem

Some agent tasks need dynamic control flow, but unnecessary multi-agent
complexity makes systems harder to debug. The harness should support narrow,
verifiable workflow patterns without requiring a large framework.

## Goals

- Document common workflow patterns.
- Prefer narrow retry loops.
- Keep contract, budget, trace, and eval boundaries visible.
- Mark unimplemented live orchestration as roadmap.

## Non-Goals

- General workflow engine.
- Distributed queue.
- Multi-agent runtime.
- Autonomous high-risk actions.

## Architecture

- Pattern docs live in `examples/workflows/`.
- `scripts/demo_parallel_workflows.py` simulates parallel sessions with
  independent contracts, budgets, and traces.
- Future live workflows can reuse WorkerLauncher and session APIs.

## Data Flow

1. Choose workflow pattern.
2. Create one or more execution contracts.
3. Run attempts.
4. Evaluate evidence.
5. Patch/retry, synthesize, or escalate.
6. Persist traces.

## Edge Cases

- Agent promises too many subtasks and completes only some.
- Verifier shares the same bias as generator.
- Goal changes across retries.
- Context window loses original contract.
- Parallel branches write the same resource.

## Acceptance Criteria

- Examples document use case, shape, contract, evidence, failure handling, and
  when not to use each pattern.
- Demo parallel workflows write independent traces.
- Docs explain when not to use workflows or agents.
- Roadmap includes goal graph, queue, memory, locks, and worktree isolation.
