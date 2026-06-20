# Traces And Verification

## Problem

Summaries are not enough for debugging or evals. A harness needs raw traces that
survive context exhaustion and make completion evidence auditable.

## Goals

- Persist raw session traces as JSON.
- Include goal, actions, observations, tool events, budget usage, status,
  failure reason, and evidence paths.
- Support debugging, restarts, evals, and partial replay.
- Require evidence-based completion.

## Non-Goals

- S3/object storage.
- Full replay engine.
- Cryptographic attestation.

## Architecture

- `RawTrace` captures execution details.
- `TraceStore` writes JSON files under a caller-provided root.
- Local demos use `data/traces/...`, which is ignored by git.
- Future production can move traces to DB/object storage.

## Data Flow

1. Workflow starts and creates a trace.
2. Actions, observations, and tool events are appended.
3. Budget usage is recorded.
4. Final status and failure reason are written.
5. Eval/reporting code reads the trace.

## Edge Cases

- Process exits before final status is written.
- Trace file is corrupted.
- Evidence path points to deleted artifact.
- Trace contains sensitive screenshot metadata.

## Acceptance Criteria

- Tests can write and read a trace.
- Demo workflows produce one trace per session.
- Docs warn traces may contain sensitive data.
- Completion requires evidence or explicit escalation.
