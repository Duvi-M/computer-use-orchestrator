# Code Quality Audit

Scope: read-only audit of `computer_use_demo/harness/`, `scripts/`, and
related tests/docs for live interview risk. No code was modified while producing
this report.

Commands run:

```bash
python3 -B -m pytest --cov=computer_use_demo.harness --cov-report=term-missing
ruff check computer_use_demo tests scripts --select ALL
ruff check computer_use_demo tests scripts --select ALL --statistics
python3 -B -m pytest -q
rg -n "TODO|FIXME|XXX|not implemented|placeholder|for now|temporary" computer_use_demo scripts tests --ignore-case
```

Results:

- `pytest-cov` is not installed in this environment, so real line/branch
  coverage could not be produced. Pytest rejected the `--cov` arguments.
- Full tests pass without coverage: `109 passed, 63 warnings in 1.83s`.
- Strict ruff mode reports `2407` findings. This is expectedly noisy because
  `--select ALL` enables docstring, annotation, test-assert, style, complexity,
  security, and exception-style rules at once.

## 1. Cobertura de tests real, módulo por módulo

Because `pytest-cov` is unavailable, percentages below are approximate direct
test coverage estimates based on test call sites and assertions. "Direct" means
the test names or assertions explicitly exercise that module's public behavior,
not just that another command happens to import it.

| Module | Approx direct function/class coverage | Direct tests | Untested branches / public gaps |
| --- | ---: | --- | --- |
| `loop.py` | ~85% | `tests/test_harness.py::test_agent_loop_records_goal_to_evidence_path`, `test_escalation_decision_marks_loop_phase` | Dataclass construction has no validation tests for empty `goal_id`, empty `text`, invalid `confidence`, or mismatched `goal_id`. `AgentLoopState.has_evidence(None)` and positive kind lookup are covered; negative kind lookup is only indirect. Public dataclasses are structurally tested but not edge-tested. |
| `contracts.py` | ~80% | `tests/test_harness.py::test_execution_contract_validates_outputs_budgets_and_grants` | `validate_outputs()` missing-output and success branches are covered. `validate_budget()` allowed/blocked branches are covered indirectly through one budget case. `require_tool()` allow/deny branches are covered. No test for custom `completion_conditions`, empty `required_outputs`, or malformed `ToolGrant` strings. |
| `budgets.py` | ~70% | `tests/test_harness.py::test_budget_decision_blocks_exceeded_limits` | Runtime and messages exceeded are covered. Idle, events, tokens, and cost exceeded branches are not directly asserted. Boundary semantics are only partly covered: messages/events use `>=`, runtime/idle use `>`, but equality behavior is not explicitly tested. |
| `tool_grants.py` | ~75% | `tests/test_harness.py::test_tool_grants_allow_and_deny_tools`, contract tests | `local_demo_default()`, `allows()`, and deny path through `require()` are covered. `locked_down()` has no direct test or real call site. Invalid grant string behavior is not tested and would raise before custom policy handling. |
| `eval_gates.py` | ~80% | `tests/test_harness.py::test_agent_loop_records_goal_to_evidence_path`, `tests/test_session_harness.py` | Passing evidence and terminal status are covered. Failing `require_evidence()` is not directly asserted. Failing `require_terminal_status()` is not directly asserted except indirectly if evals fail in future. Custom `EvalGate.evaluate()` is only exercised via generated gates. |
| `triggers.py` | ~70% | `tests/test_harness.py::test_trigger_dispatcher_records_and_calls_handlers`, eval/session tests indirectly | `register()` and `emit()` with one handler are covered. Multiple handlers, no handlers, string event conversion, invalid event values, and handler exceptions are not tested. |
| `traces.py` | ~80% | `tests/test_harness.py::test_trace_store_persists_raw_trace`, `tests/test_session_harness.py` | `RawTrace.record_*()`, `finish()`, `TraceStore.write()`, and `read()` are covered. `trace_path()` slash sanitization is not directly asserted. Corrupt JSON, missing trace file, and partial writes are not tested. |
| `memory.py` | ~75% | `tests/test_harness_memory.py` | File-backed store/search, dedupe, fallback without OpenAI key, Anthropic key rejection, mem0 config mock, and runtime degradation are covered. Untested: corrupt JSON file, empty/non-list payload shapes beyond happy-path object/list, lock contention, invalid metadata, `MemoryRecord` usage, real mem0 end-to-end with a valid OpenAI key, real Chroma/HuggingFace path, and partial-write recovery. |
| `runner.py` | ~60% | `tests/test_harness_runner.py` | Checkpoint write/reload, bounded loop, memory fallback print, memory dedupe, missing memory file after checkpoint, and recall output are covered. Untested: corrupt checkpoint JSON, missing required checkpoint fields, empty `goal_id`/`goal_text`, signal handling path, CLI `main()` argument errors, `--disable-memory`, `memory_recall_limit < 1`, invalid phase values, and action/observation list underflow if state is malformed. |
| `shared_task_queue.py` | ~70% | `tests/test_shared_task_queue.py` | Concurrent claim uniqueness and multi-agent completion are covered. Untested: SQLite locked beyond timeout, invalid/corrupt payload JSON, `complete_task()` on nonexistent task, repeated completion, queue initialization failures, filesystem permission errors, and retry/backoff behavior. There is no explicit retry logic beyond SQLite's connection timeout. |
| `session_harness.py` | ~65% | `tests/test_session_harness.py`, API session harness call sites | Worker-style happy path and error-to-escalation path are covered. Untested: screenshot/user_message branches, unknown event names, duplicate `done`, `done` with `ok=False`, eval failure branch, custom budgets, default trace directory env var, dispatcher handler errors, trace write failures, and large payload truncation boundaries. |

Public functions/classes with no clear direct test:

- `tool_grants.py`: `ToolGrantPolicy.locked_down()`.
- `memory.py`: `MemoryRecord`, `has_valid_openai_key()` as a direct unit,
  `tokenize()` as a direct unit, `Mem0Backend.add/search()` against real mem0.
- `runner.py`: `handle_signal()`, `main()`, CLI validation branches, malformed
  checkpoint loading.
- `session_harness.py`: `session_harness_trace_dir()` direct env behavior.
- `shared_task_queue.py`: `connect()` timeout/DB failure behavior as a direct
  unit; `init_queue()` schema idempotency is used indirectly but not asserted.

## 2. Código muerto o no usado

Findings are based on static search and call-site inspection. This is not a
full reachability analysis, but it catches obvious dead/demo-only code.

- `computer_use_demo/harness/memory.py::MemoryRecord`
  - Exported from `computer_use_demo/harness/__init__.py`.
  - No production/test call site constructs it.
  - Risk: low. It looks like a planned typed wrapper but current memory records
    are raw dictionaries.

- `ToolGrantPolicy.locked_down()`
  - Defined but no call site outside its own file.
  - Risk: low to medium. It is a useful concept for the interview, but if asked
    "where is locked-down mode used?", the honest answer is "not wired into the
    demo path yet."

- `memory.py::has_valid_openai_key()`
  - Used internally by `HarnessMemory._create_backend()`.
  - Not dead, but not directly unit tested.

- `memory.py::tokenize()`
  - Used internally by `FileBackedMemory.search()`.
  - Not dead, but not directly unit tested.

- `runner.py::memory_evidence_signature()`
  - Thin wrapper around `evidence_signature()`.
  - Used only by `advance_state()`. It exists mostly as a naming boundary.
  - Risk: low.

- `session_harness.py::session_harness_trace_dir()`
  - Used only by `SessionHarness.create()` default behavior.
  - No direct env-var test.
  - Risk: low.

- Scripts in `scripts/`:
  - `scripts/interview_demo.py`: primary demo script and documented.
  - `scripts/run_harness_tmux.sh`: documented in `docs/INTERVIEW_DEMO.md`.
  - `scripts/spawn_agents.sh`: documented in README/specs/interview docs.
  - `scripts/agent_worker.py`: used by `spawn_agents.sh`.
  - `scripts/clean_demo_state.sh`: documented in `docs/INTERVIEW_DEMO.md`.
  - `scripts/smoke_local.py`: used by `Makefile smoke-local`.
  - `scripts/demo_parallel_sessions.py`: documented in README and
    `docs/DEMO_SCRIPT.md`, but not part of the current BOS.PRO demo path.
  - `scripts/demo_parallel_workflows.py`: documented in README/specs and cleanup,
    but not part of the current BOS.PRO demo path.

Potentially stale/demo-secondary scripts:

- `scripts/demo_parallel_sessions.py`
- `scripts/demo_parallel_workflows.py`

They are not dead, but they can distract during interview code browsing because
the primary harness demo now flows through `scripts/interview_demo.py`.

Parameters rarely or never passed with non-default values in real call sites:

- `SessionHarness.create(budgets=...)` is used with custom budgets by API code,
  but tests use default budgets.
- `HarnessMemory(config=...)` has no direct non-test call site; it is mainly for
  mem0 configurability.
- `run_loop(enable_memory=False, memory_recall_limit=...)` is exposed by CLI but
  not directly covered by tests or interview demo defaults.
- `agent_worker.py --max-tasks` exists but is not passed by `spawn_agents.sh` or
  the main docs.

## 3. TODOs, FIXMEs, y placeholders olvidados

Search command:

```bash
rg -n "TODO|FIXME|XXX|not implemented|placeholder|for now|temporary" computer_use_demo scripts tests --ignore-case
```

Result: no matches in `computer_use_demo/`, `scripts/`, or `tests/`.

Interview risk:

- Low. There are no obvious TODO/FIXME markers in the code paths likely to be
  opened live.
- The absence of TODOs does not mean absence of roadmap work; roadmap is mostly
  documented in README/docs/specs instead of inline comments.

## 4. Manejo de errores y casos límite débiles

### `runner.py`

Current strengths:

- CLI validates `interval_seconds > 0`, `memory_recall_limit >= 1`, and
  `max_iterations >= 1`.
- `SIGINT`/`SIGTERM` set `RUNNING=False`, and the loop checkpoints before exit.
- Memory recall/write errors are caught and printed instead of crashing the
  runner.

Weak spots:

- Empty `--goal-id` and empty `--goal-text` are accepted. Empty `goal_id` writes
  a checkpoint named `.json`, which would look bad in a live demo.
- `load_checkpoint()` does not catch `json.JSONDecodeError`, missing keys, or
  malformed dataclass payloads. A corrupt checkpoint can crash startup.
- `save_checkpoint()` uses direct `Path.write_text()`, not atomic write/rename.
  A crash during write could leave a partial checkpoint.
- `advance_state()` assumes action/observation ordering is internally valid.
  A manually edited checkpoint with phase `action` but no actions would crash on
  `state.actions[-1]`.
- `recorded_memory_signatures` is process-local. On restart, dedupe relies on
  file-backed memory metadata; if memory backend changes, duplicate recording
  behavior could differ.

Demo risk:

- Medium. The happy path is stable, but a dirty or corrupt checkpoint in
  `data/checkpoints/` could break the demo before the first visible success.

### `shared_task_queue.py`

Current strengths:

- SQLite connection uses `timeout=30.0`.
- `claim_next_task()` uses `BEGIN IMMEDIATE`, which is correct for single-writer
  claim semantics on local SQLite.
- The rollback path is present for exceptions after `BEGIN IMMEDIATE`.

Weak spots:

- There is no explicit retry/backoff around `sqlite3.OperationalError:
  database is locked`. The call can wait up to 30 seconds and then raise.
- `complete_task()` does not verify that a row was updated. Completing a missing
  task silently succeeds from the caller perspective.
- Payload JSON decode errors are not caught in `claim_next_task()` or
  `list_tasks()`. A manually corrupted DB row can crash the demo.
- `init_queue()` is called by every operation. This is okay for local demo, but
  noisy/inefficient as a production pattern.
- There is no fairness metric in the queue itself; fairness is emergent from
  seeded tasks, start barrier, and simulated work delay.

Demo risk:

- Medium. Normal demo works, but a stale locked DB or corrupt `data/task_queue.db`
  could cause a long pause or crash. Running `scripts/clean_demo_state.sh`
  before the call matters.

### `memory.py`

Current strengths:

- If `OPENAI_API_KEY` is absent or starts with `sk-ant-`, the code defaults to
  file-backed memory and does not attempt real mem0.
- Runtime mem0 `add()`/`search()` failures degrade to file-backed memory.
- File-backed writes use `fcntl.flock()` exclusive lock.
- Search uses shared lock.
- Dedupe by `memory_signature` is implemented.

Weak spots:

- `_read_records_locked()` directly calls `json.loads(raw)` and does not catch
  corrupt or partial JSON.
- File-backed writes truncate and write the same file while holding the lock,
  but do not use atomic temp-file replacement. A process kill during write can
  leave corrupt JSON.
- `fcntl` is Unix/macOS-specific. That is fine for this interview machine, but
  not portable to Windows.
- `Mem0Backend` is wired, but real mem0 end-to-end remains unverified in tests
  and likely requires a valid OpenAI key for LLM behavior despite local
  HuggingFace embeddings.

Demo risk:

- Medium. A corrupted `data/interview_harness_memory.json` can crash the memory
  demo summary path in `scripts/interview_demo.py`, even though HarnessMemory can
  degrade from mem0 failures.

## 5. Consistencia de tipado y estilo

Strict ruff command:

```bash
ruff check computer_use_demo tests scripts --select ALL --statistics
```

Summary:

- Total: `2407` findings.
- Most common groups:
  - `S101` assert usage in tests: `485`.
  - Missing docstrings: `D103` `255`, `D102` `86`, `D101` `75`,
    `D100` `47`.
  - Missing annotations: `ANN001` `221`, `ANN201` `189`,
    `ANN202` `41`, `ANN204` `31`.
  - Line length: `E501` `204`.
  - Trailing comma/style: `COM812` `131`.
  - Magic values: `PLR2004` `102`.
  - Exception style: `TRY003` `80`, `EM102` `50`, `EM101` `31`.
  - Private member access in tests: `SLF001` `30`.
  - Broad exception catching: `BLE001` `13`.
  - Complexity: `C901` `12`, `PLR0912` `6`, `PLR0915` `4`.
  - Security/process warnings: `S603`, `S607`, `S602`, `S604`,
    `S310`, `S113`, `S311`.

Interpretation:

- This repo is not configured to satisfy `ruff --select ALL`; strict mode is
  useful as an audit lens, not as the current CI standard.
- Many findings are low-value for this project right now: pytest `assert`,
  missing docstrings, and style-only complaints.
- Real quality signals worth addressing before interview if time allows:
  - Missing return/argument annotations in public harness/script functions.
  - Broad `except Exception` in memory/runner/queue paths.
  - Non-atomic JSON writes for checkpoints/traces/memory.
  - Subprocess and URL warnings in scripts/API that could be explained as local
    demo tooling but should not be oversold as hardened production code.

Harness public type hints:

- Most harness public functions have useful argument/return annotations.
- Gaps or weak spots:
  - `MemoryBackend` uses `Any` for backend return values.
  - `FileBackedMemory._read_records_locked(handle: Any)` uses `Any`.
  - `HarnessMemory.record_evidence()` returns `Any`.
  - `Mem0Backend.add()` returns `Any`.
  - `runner.handle_signal(_frame: Any)` uses `Any`.
  - Scripts have several public functions with broad `dict[str, object]` or
    untyped nested structures.

## 6. Riesgos específicos para DEMO EN VIVO

Most important risks for screen-sharing:

1. Dirty local state can confuse the story.
   - `data/interview_checkpoints/`, `data/interview_harness_memory.json`,
     `data/interview_task_queue.db`, `data/checkpoints/`, and worktrees can
     contain old runs.
   - `docs/INTERVIEW_DEMO.md` says to optionally run
     `scripts/clean_demo_state.sh`. For a high-stakes interview, cleanup should
     be treated as mandatory unless preserving a reboot checkpoint is part of
     the demo.

2. `docs/INTERVIEW_DEMO.md` now demonstrates the verified `>5` path:

   ```bash
   python3 scripts/interview_demo.py agents --agents 6 --tasks 24
   ```

   This is now consistent with README evidence. Larger `10+ agents / 100+
   tasks` load testing remains future work.

3. `scripts/interview_demo.py check` runs ruff without `--select ALL`, tests,
   and evals. The strict audit ruff command fails massively. If asked live,
   explain the difference:
   - CI/project ruff profile is the maintained style gate.
   - `--select ALL` is intentionally a harsh audit mode, not current policy.

4. tmux paths are local-environment sensitive.
   - tmux/resurrect evidence is real on the developer's macOS setup, but it
     depends on `~/.tmux/plugins/` and `~/.local/share/tmux/resurrect/`.
   - In a different shell/sandbox, tmux can fail with socket permission errors.
   - Do not start the interview by relying on tmux if it is not already warmed
     up. Use bounded `interview_demo.py loop` first, then show tmux evidence.

5. `run_harness_tmux.sh` attaches interactively.
   - If the named session already exists, the script immediately `exec tmux
     attach-session`.
   - That is correct behavior, but during screen share it can surprise you by
     switching UI context.

6. `spawn_agents.sh` can attach to an old tmux session.
   - If `agent-harness` already exists, it attaches instead of resetting.
   - Good for idempotence, risky for demo freshness if panes show old output.

7. `agent_worker.py` can idle forever.
   - With no `--max-tasks`, workers continue printing "idle no pending task".
   - This is fine in tmux but noisy if an interviewer expects the command to
     terminate.

8. File-backed memory now treats corrupt JSON as empty memory.
   - It prints a warning and keeps the demo flow alive.
   - The file can still lose previous corrupt contents; this is acceptable for
     local demo fallback memory, not production-grade memory durability.

9. Checkpoint writes are now atomic and corrupt checkpoints are moved aside.
   - Startup prints a clear warning and starts fresh if a checkpoint cannot be
     parsed.
   - This protects the demo from bad local JSON, but it is still file-backed
     local persistence rather than a durable distributed state store.

10. `SessionHarness` demo uses synthetic worker-style events.
    - It maps `assistant_block`, `tool_result`, and `done` into state/evidence,
      but the live demo does not necessarily stream those from a real Docker
      worker.
    - The honest phrasing is: "adapter from worker event shape to harness state",
      not "fully integrated autonomous worker loop".

11. Local paths in docs are developer-machine specific.
    - `~/.tmux/plugins/`, `~/.local/share/tmux/resurrect/`, and local `data/*`
      paths are valid evidence for this machine, not portable setup guarantees.

12. Python version warnings could distract.
    - Tests passed under Python 3.14, but emitted deprecation warnings from
      Starlette/FastAPI and `on_event`.
    - Docs recommend Python 3.11 because the worker image uses 3.11; use that
      for a cleaner interview environment if possible.

## 7. Priorización

### CRÍTICO

- Treat demo cleanup as mandatory or explicitly choose preserved state.
  - Risk: old checkpoints/memory/task DB can make output look stale or
    contradictory.
  - Before interview: run `scripts/clean_demo_state.sh`, then regenerate only
    the exact evidence you want to show.

- Be explicit that `SessionHarness` consumes worker-style events, but the demo
  events are synthetic unless you also run the full FastAPI/Docker path.
  - Risk: overclaiming would hurt trust in a harness engineer interview.

### IMPORTANTE

- Add direct tests for negative eval gates, all budget branches, corrupt
  memory/checkpoint JSON, and SQLite locked behavior.
  - These are the main quality gaps in the harness layer.

- Make JSON writes atomic for checkpoints, traces, and file-backed memory.
  - This would improve the durability story substantially.

- Add validation for empty `goal_id` and `goal_text` in `runner.py`.
  - Prevents `.json` checkpoint names and bad demo state.

- Add explicit retry/backoff or clearer failure message around SQLite
  `database is locked`.
  - Prevents a confusing 30-second hang in multi-agent demos.

- Prune or label secondary demo scripts.
  - `demo_parallel_sessions.py` and `demo_parallel_workflows.py` are not wrong,
    but they are less central than `interview_demo.py`.

- Add focused type annotations for public harness APIs flagged by ruff.
  - Helps when an interviewer opens the code.

### COSMÉTICO

- Missing docstrings across modules/classes.
- `ruff --select ALL` style-only findings such as trailing commas, line length,
  pytest `assert`, and magic constants in tests.
- Thin wrapper functions such as `memory_evidence_signature()`.
- Old docs/audit snapshots that are explicitly marked historical.

Bottom line:

- The harness demo path is credible and tests pass.
- The largest live-demo risks are dirty state, mismatch between `5` vs `6`
  agent demo commands, non-atomic local JSON persistence, and unsupported claims
  around real mem0 / real worker integration.
- The code is acceptable as an interview prototype, but not yet hardened enough
  to describe as production-grade harness infrastructure without qualifiers.
