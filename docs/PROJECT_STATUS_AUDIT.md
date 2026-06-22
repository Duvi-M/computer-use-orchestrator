# Project Status Audit

Este reporte es deliberadamente conservador. No intenta vender el proyecto;
intenta dejar claro qué se puede defender en vivo, qué solo está cubierto por
tests o mocks, y qué sigue siendo roadmap.

Fecha de auditoría: 2026-06-21.

Comandos seguros ejecutados durante esta auditoría:

```bash
python3 scripts/interview_demo.py map
python3 scripts/interview_demo.py memory
python3 scripts/interview_demo.py eval
python3 scripts/interview_demo.py session-harness
python3 scripts/interview_demo.py agents --agents 5 --tasks 20
git worktree list
command -v tmux
```

No se ejecutó Docker, no se llamó Anthropic, no se levantó FastAPI, y no se
probó mem0 real con una key de OpenAI.

## 1. Inventario de features, por estado real (3 categorías, no 2)

| Feature | Estado real | Evidencia y por qué |
| --- | --- | --- |
| Spec-driven specs | VERIFICADO EN VIVO | Se ejecutó `python3 scripts/interview_demo.py map`. Output observado: `Spec-driven dev: specs/*.md + specs/spec-kit/* — Show original spec and Spec Kit version.` Archivos presentes: `specs/agentic-harness.md`, `specs/multi-agent-harness.md`, `specs/spec-kit/agentic-harness/{spec.md,plan.md,tasks.md}`, `specs/spec-kit/multi-agent-harness/{spec.md,plan.md,tasks.md}`. Limitación: el formato Spec Kit fue escrito a mano; no hay evidencia de uso del CLI oficial de GitHub Spec Kit. |
| Goal/plan/action loop | VERIFICADO EN VIVO | Se ejecutó `python3 scripts/interview_demo.py memory`, que internamente corre `run_loop()`. Output observado: `before phase=goal`, luego `after phase=plan`, `after phase=action`, `after phase=observation`, `after phase=evaluation`, `after phase=next_step`. Código base: `computer_use_demo/harness/loop.py` y `computer_use_demo/harness/runner.py`. Limitación: el loop CLI simula acciones; no es todavía el mismo loop que decide cada acción dentro del Claude Computer Use worker. |
| Execution contracts | VERIFICADO EN VIVO | Se ejecutó `python3 scripts/interview_demo.py session-harness`. El comando crea un `SessionHarness`, que crea un `ExecutionContract` en `computer_use_demo/harness/session_harness.py`. Output observado: trace path `data/interview_session_harness_traces/interview-session-harness.json`, `eval_gates` con `require_evidence:answer` y `require_terminal_status`. Limitación: el contract se ejercita indirectamente; el output no muestra el contrato completo ni aplica tool grants reales dentro del worker. |
| Budgets | VERIFICADO EN VIVO | Se ejecutó `python3 scripts/interview_demo.py eval`. Output observado: `"budget": {"allowed": true, "exceeded": [], "reason": ""}`. Código: `computer_use_demo/harness/budgets.py`. Limitación: token/cost budget existen como campos y eval offline, pero no están conectados a uso real de proveedor Anthropic. |
| Eval gates | VERIFICADO EN VIVO | Se ejecutaron `python3 scripts/interview_demo.py eval` y `python3 scripts/interview_demo.py session-harness`. Output observado: gates `require_evidence:answer` y `require_terminal_status`, ambos `passed: true`. Código: `computer_use_demo/harness/eval_gates.py`. Limitación: los gates actuales son mínimos; no hay verifier independiente ni evaluación semántica fuerte. |
| Memory layer | VERIFICADO EN VIVO | Se ejecutó `python3 scripts/interview_demo.py memory`. Output observado: `using file-backed memory fallback`, `memory recall query='search Osaka weather' -> 1 matches found`, `retrieved memories: 1`, y memoria de `tokyo-run`. Esto verifica el backend local file-backed con keyword recall. Limitación importante: mem0 real no fue probado end-to-end; el backend mem0 solo se activa con `OPENAI_API_KEY` válida y existe principalmente como integración opcional/fail-soft. |
| Traces | VERIFICADO EN VIVO | Se ejecutó `python3 scripts/interview_demo.py session-harness`. Output observado: `trace_path: data/interview_session_harness_traces/interview-session-harness.json`. Código: `computer_use_demo/harness/traces.py` y `computer_use_demo/harness/session_harness.py`. Limitación: traces son JSON locales; no hay trace backend remoto, replay completo, ni object storage. |
| tmux persistence | SOLO TESTS / NUNCA CORRIDO EN VIVO | La persistencia por checkpoint sí se observó en vivo mediante `python3 scripts/interview_demo.py memory`, que escribió checkpoints bajo `data/interview_checkpoints/`. También hay tests de checkpoint/reload en `tests/test_harness_runner.py`. Pero en esta auditoría no se pudo verificar tmux: `tmux has-session` falló con `error connecting to /private/tmp/tmux-501/default (Operation not permitted)`. El script `scripts/run_harness_tmux.sh` existe y usa `tmux has-session`/`tmux new-session`, pero no se validó aquí como usuario real. Tampoco se probó supervivencia a reboot. |
| Worktree isolation | VERIFICADO EN VIVO | Se ejecutó `git worktree list`. Output observado con tres worktrees: `worktrees/agent-1`, `worktrees/agent-2`, `worktrees/agent-3`, en branches `agent/agent-1`, `agent/agent-2`, `agent/agent-3`. Código: `scripts/spawn_agents.sh` crea `./worktrees/agent-N` con `git worktree add`. Limitación: en esta auditoría no se relanzó el script tmux por restricciones de tmux; se verificó el estado existente de worktrees y el código. |
| Shared task queue | VERIFICADO EN VIVO | Se ejecutó `python3 scripts/interview_demo.py agents --agents 5 --tasks 20`. Output observado: `tasks_completed: 20` y distribución exacta `agent-1: 4`, `agent-2: 4`, `agent-3: 4`, `agent-4: 4`, `agent-5: 4`. Código: `computer_use_demo/harness/shared_task_queue.py`. Limitación: este comando usa threads locales en un proceso, no panes tmux ni procesos independientes. |
| Single-writer lock | VERIFICADO EN VIVO | La cola usa `BEGIN IMMEDIATE` en `claim_next_task()` (`computer_use_demo/harness/shared_task_queue.py`). El demo live `python3 scripts/interview_demo.py agents --agents 5 --tasks 20` completó 20 tareas sin señales de doble asignación. Tests más fuertes: `tests/test_shared_task_queue.py` lanza 5 claimers concurrentes y verifica que no hay IDs duplicados. Limitación: SQLite single-writer es válido para demo local en una máquina; no es un lock distribuido multi-host. |
| FastAPI/Docker runtime | SOLO TESTS / NUNCA CORRIDO EN VIVO | La arquitectura existe y los tests del orchestrator cubren auth, ownership, limits, UI tokens, launcher, metrics, migrations y retention. Archivos: `computer_use_demo/api/main.py`, `computer_use_demo/api/worker_launcher.py`, `web/app.js`. Pero durante esta auditoría no se ejecutó `make run-api`, `make run-web`, `make build-worker`, no se abrió noVNC, y no se lanzó un worker Docker real. No debe presentarse como verificado en esta sesión salvo que se corra antes de la entrevista. |
| Evals | VERIFICADO EN VIVO | Se ejecutó `python3 scripts/interview_demo.py eval`, que a su vez corrió `evals/run_eval.py --json`. Output observado: `"passed": true`, scenario `offline_session_lifecycle`, triggers `on_session_created`, `on_worker_ready`, `on_session_finished`. Limitación: eval offline, no llama Anthropic, Docker ni FastAPI live. |
| SessionHarness adapter | VERIFICADO EN VIVO | Aunque no estaba en la lista original, es relevante para la defensa del harness. Se ejecutó `python3 scripts/interview_demo.py session-harness`. Output observado: `observations: 2`, `evidence: 1`, eval gates passing, trace path local. Limitación: los eventos son worker-style sintéticos (`assistant_block`, `tool_result`, `done`) generados por el demo, no capturados desde una ejecución real del worker durante esta auditoría. |

## 2. Contradicciones o inconsistencias en la documentación

### 2.1 `specs/dynamic-workflows.md` todavía contradice el README actual

- Archivo: `specs/dynamic-workflows.md`, línea aproximada 53.
- Texto actual: `Roadmap includes goal graph, queue, memory, locks, and worktree isolation.`
- Contradicción: `README.md` ahora dice que file-backed memory, SQLite
  single-writer task claims, shared task queue local y worktree-isolated agents
  ya están implementados para demo local. El roadmap correcto debería hablar de
  durable distributed queue, temporal knowledge graph, production scheduling
  metrics, y multi-host locks, no de `queue/memory/locks/worktree isolation` en
  genérico.
- Severidad para entrevista: alta. Si alguien abre specs después del README,
  puede preguntar por qué algo implementado vuelve a aparecer como roadmap.

### 2.2 `specs/agentic-harness.md` está desactualizado respecto al multi-agent demo local

- Archivo: `specs/agentic-harness.md`, líneas aproximadas 20-22.
- Texto actual: `Add multi-agent scheduling yet` como non-goal.
- Matiz: no es una contradicción total si se interpreta `scheduling` como
  scheduler productivo, pero sí es ambiguo porque ya existe una demo local de
  multi-agent coordination con worktrees, tmux script y SQLite queue.
- Recomendación: cambiar a algo más preciso como `Production-grade multi-agent
  scheduling remains roadmap; local coordination demo exists separately`.

### 2.3 `docs/HARNESS_ARCHITECTURE.md` sobre-precisa "GitHub Spec Kit specs"

- Archivo: `docs/HARNESS_ARCHITECTURE.md`, línea aproximada 141.
- Texto actual: `custom specs and GitHub Spec Kit specs`.
- Inconsistencia: `README.md` aclara que `specs/spec-kit/` es GitHub Spec
  Kit-style y escrito manualmente, no generado con el CLI oficial. El doc de
  arquitectura debería usar la misma precisión para evitar que parezca que se
  usó el tooling oficial.

### 2.4 `specs/spec-kit/agentic-harness/plan.md` describe memoria como "local mem0"

- Archivo: `specs/spec-kit/agentic-harness/plan.md`, línea aproximada 79.
- Texto actual: `Define HarnessMemory wrapper around local mem0.`
- Inconsistencia: el comportamiento real por defecto es `FileBackedMemory`; mem0
  es opcional y solo se intenta con `OPENAI_API_KEY` válida. Además no se probó
  mem0 real end-to-end. La frase debería decir `file-backed local memory with
  optional mem0 backend`.

### 2.5 `specs/spec-kit/agentic-harness/tasks.md` marca validaciones como hechas

- Archivo: `specs/spec-kit/agentic-harness/tasks.md`, líneas aproximadas 53-57.
- Texto actual: T028-T032 están marcadas `[x]`, incluyendo `make db-migrate`.
- Riesgo: no es una contradicción si efectivamente se corrieron en una fase
  anterior, pero este audit no volvió a correr esos comandos. Si se quiere que
  el estado sea audit-grade, conviene anotar fecha/último output o mover esas
  líneas a "validated previously".

### 2.6 No se encontró contradicción directa ya restante en `README.md`

- Se revisó `README.md` después del fix anterior.
- La tabla BOS.PRO, `What Works Today`, `Known Limitations` y `Roadmap` ya
  distinguen mejor entre demo local implementado y producción pendiente.
- Riesgo restante: el README sigue siendo optimista en tono general, pero no se
  encontró la contradicción exacta de "implemented vs roadmap" para parallel
  agents/worktrees/shared queue.

## 3. Brechas conocidas vs requisitos de la vacante

### Spec-Driven Dev con OpenSpec, GStack, GitHub Spec Kit o Kiro (CLI real, no solo formato de archivo)

Estado: parcial.

Evidencia:

- Existe spec-driven shape en `specs/*.md`.
- Existe formato tipo Spec Kit en `specs/spec-kit/*/{spec.md,plan.md,tasks.md}`.
- `python3 scripts/interview_demo.py map` muestra `Spec-driven dev: specs/*.md + specs/spec-kit/*`.
- `README.md` aclara que es GitHub Spec Kit-style escrito manualmente, no generado con CLI oficial.

Brecha:

- No hay evidencia de uso real del CLI oficial de GitHub Spec Kit, OpenSpec,
  GStack o Kiro.
- En entrevista conviene decir: "Uso el formato Spec Kit para estructurar y
  enseñar el flujo, pero en este repo no corrí el CLI oficial."

### Memory layer con mem0, Letta, Zep+Graphiti o equivalente, en uso real (no solo wired-in con fallback)

Estado: parcial.

Evidencia:

- `computer_use_demo/harness/memory.py` implementa `HarnessMemory`,
  `FileBackedMemory`, y `Mem0Backend`.
- `python3 scripts/interview_demo.py memory` verificó file-backed memory en vivo:
  `memory recall query='search Osaka weather' -> 1 matches found`.
- Tests mockean mem0 y verifican `user_id`, config HuggingFace/Chroma y fallback.

Brecha:

- mem0 real no fue probado end-to-end con una key OpenAI válida.
- El fallback local usa keyword recall, no embeddings reales ni temporal
  knowledge graph.
- No hay Letta, Zep+Graphiti, Graphiti temporal graph, ni memory graph.

### Orquestación >5 agentes simultáneos

Estado: parcial tirando a no cumplido.

Evidencia:

- `python3 scripts/interview_demo.py agents --agents 5 --tasks 20` corrió en vivo
  y completó 20 tareas con 5 workers thread-locales, distribución 4/4/4/4/4.
- `scripts/spawn_agents.sh` soporta N panes tmux y N worktrees.
- `git worktree list` muestra tres worktrees existentes: agent-1, agent-2,
  agent-3.

Brecha:

- El requisito dice `>5`, no `5`.
- El demo verificado en vivo durante esta auditoría fue de 5 threads, no más de
  5 agentes reales/procesos/tmux panes.
- La demo tmux real documentada es `scripts/spawn_agents.sh 3`; 5+ tmux panes no
  fueron verificados en esta auditoría.
- Production-grade scheduling y fairness no están load-tested.

### Worktree isolation, shared task list, single-writer locks

Estado: cumplido para demo local; no cumplido para producción distribuida.

Evidencia:

- Worktrees: `git worktree list` muestra `worktrees/agent-1`, `agent-2`,
  `agent-3`.
- Spawn script: `scripts/spawn_agents.sh` crea/reusa worktrees con
  `git worktree add`.
- Shared queue: `computer_use_demo/harness/shared_task_queue.py`.
- Single writer: `claim_next_task()` ejecuta `BEGIN IMMEDIATE`.
- Test: `tests/test_shared_task_queue.py` verifica 5 claimers concurrentes sin
  double assignment.
- Demo live: `python3 scripts/interview_demo.py agents --agents 5 --tasks 20`
  completó 20 tareas.

Brecha:

- SQLite lock solo es una solución local single-host.
- No hay lock distribuido ni queue service.
- La demo no usa agentes LLM reales; son workers simples que reclaman tareas.

### Persistence en tmux/zellij sobreviviendo timeouts SSH y reboots

Estado: parcial.

Evidencia:

- `scripts/run_harness_tmux.sh` implementa `tmux has-session`, attach idempotente
  y `tmux new-session`.
- `computer_use_demo/harness/runner.py` escribe checkpoints JSON y recarga si
  existe checkpoint.
- `tests/test_harness_runner.py` cubre checkpoint write/reload.
- `python3 scripts/interview_demo.py memory` produjo checkpoints bajo
  `data/interview_checkpoints/`.

Brecha:

- En esta auditoría no se pudo consultar tmux por sandbox:
  `error connecting to /private/tmp/tmux-501/default (Operation not permitted)`.
- No se verificó zellij.
- No se verificó supervivencia a reboot.
- El FastAPI runtime todavía documenta worker reattachment after orchestrator
  restart como incompleto.

### Experiencia real con Opencode, Cline, Claude Squad, Conductor, o Claude Code Agent Teams

Estado: no cumplido.

Evidencia:

- No hay archivos, comandos, specs ni docs que demuestren uso de esas
  herramientas.
- El repo implementa una demo propia de harness/queue/worktree, no integración
  con esos harnesses.

Brecha:

- Para la entrevista, esto debe presentarse como experiencia conceptual o
  comparación preparada, no como experiencia demostrada por el repo.

### Experiencia real con 2+ de OpenHands, OpenCode, OMA

Estado: no cumplido.

Evidencia:

- No hay integración ni artefactos de OpenHands, OpenCode u OMA en el repo.
- No hay eval comparativo de agent loop/tool API/orchestration model contra
  esos sistemas.

Brecha:

- Si preguntan, hay que hablar desde análisis externo/preparación, no desde este
  proyecto.

## 4. Bugs encontrados y corregidos durante esta preparación

### 4.1 Protected noVNC UI no pedía token desde frontend

Síntoma observado:

- Con `PROTECT_SESSION_UI=true` y `UI_TOKEN_SECRET` configurado, el navegador
  abría `GET /sessions/{session_id}/ui` directamente.
- Backend devolvía `403 {"detail":"UI token is required"}`.
- Logs confirmaban que `POST /sessions/{session_id}/ui-token` no se llamaba.

Causa raíz:

- El botón `Open noVNC` del frontend usaba una URL vieja/directa y no negociaba
  token en modo protegido.

Fix aplicado:

- El flujo de frontend fue ajustado para pedir primero `/ui-token` y abrir la
  signed URL cuando protected UI está activo, manteniendo fallback local cuando
  protected mode no está activo o el endpoint no existe.

### 4.2 Test de métricas dependía del shell del developer

Síntoma observado:

- `test_metrics_endpoint_returns_expected_fields` esperaba
  `protected_ui_enabled is False`.
- Si el shell tenía `PROTECT_SESSION_UI=true`, `/metrics` devolvía
  `protected_ui_enabled=true` y el test fallaba.

Causa raíz:

- El test no controlaba explícitamente variables de entorno relevantes.

Fix aplicado:

- Tests config-dependent fueron ajustados con `monkeypatch` para fijar o limpiar
  `PROTECT_SESSION_UI` y `UI_TOKEN_SECRET`.
- Se mantuvo el comportamiento real de `/metrics`: refleja config actual.

### 4.3 Dependencia `psycopg[binary]==3.2.3` fallaba en Python 3.14

Síntoma observado:

- `python -m pip install -r computer_use_demo/requirements.txt` fallaba en macOS
  Python 3.14 con `No matching distribution found for psycopg-binary==3.2.3`.
- `make db-migrate` fallaba después porque Alembic no quedaba instalado en la
  venv.

Causa raíz:

- Pin de psycopg sin wheel compatible con el Python local.
- Makefile usaba ruta rígida a Alembic en algunos puntos.

Fix aplicado:

- Se cambió a un rango compatible tipo `psycopg[binary]>=3.2.13,<3.4`.
- Makefile migró a usar `python -m alembic upgrade head` vía `PYTHON`.
- README documenta Python 3.11 como versión más segura porque el worker usa 3.11.

### 4.4 mem0 fallaba por falta de `user_id`

Síntoma observado:

- `mem0.exceptions.ValidationError: At least one of 'user_id', 'agent_id', or
  'run_id' must be provided.`

Causa raíz:

- Las llamadas `add/search` hacia mem0 no pasaban namespace estable.

Fix aplicado:

- `HarnessMemory` usa `memory_user_id`, default `harness-demo`.
- `record_evidence()` y `recall_related()` pasan el mismo `user_id`.
- Tests verifican que store/search usan `DEFAULT_MEMORY_USER_ID` o el user
  configurable.

### 4.5 mem0/HuggingFace todavía llamaba OpenAI LLM

Síntoma observado:

- Aunque se configuró embedder local HuggingFace/Chroma, `mem0.add()` seguía
  intentando usar OpenAI LLM.
- Fallaba si `OPENAI_API_KEY` no existía o si accidentalmente tenía una key
  Anthropic `sk-ant-...`.

Causa raíz:

- mem0 no solo necesita vector store/embedder; su flujo puede invocar LLM.
- El código intentaba inicializar mem0 real aunque no hubiese una OpenAI key
  válida.

Fix aplicado:

- `has_valid_openai_key()` devuelve falso si `OPENAI_API_KEY` está ausente o
  empieza con `sk-ant-`.
- En ese caso `HarnessMemory` no inicializa mem0 y usa `FileBackedMemory`.
- Si mem0 falla en runtime durante `add` o `search`, degrada automáticamente al
  fallback.
- Runner imprime claramente `using file-backed memory fallback`.

### 4.6 Fair task claiming parecía roto aunque el lock funcionaba

Síntoma observado:

- Con pocas tareas y trabajo instantáneo, un agente rápido podía vaciar la cola
  antes de que los demás arrancaran.
- No había double-claim, pero la demo parecía no concurrente.

Causa raíz:

- El problema era fairness visual/startup timing, no atomicidad.
- `BEGIN IMMEDIATE` sí serializaba claims correctamente.

Fix aplicado:

- `scripts/spawn_agents.sh` ahora siembra por defecto 18 tareas (`SEED_TASKS`).
- `scripts/agent_worker.py` duerme `random.uniform(1.5, 3.5)` entre claim y
  complete.
- `spawn_agents.sh` crea un start-signal después de confirmar panes, y workers
  esperan ese archivo antes de reclamar.
- Test `test_concurrent_workers_complete_tasks_across_multiple_agents` exige
  distribución entre al menos 3 agentes.

### 4.7 Evidence spam en memoria

Síntoma observado:

- El runner llamaba `HarnessMemory.record_evidence()` en cada tick del loop.
- Con `--interval-seconds=0.1` durante ~20s se generaban muchas entradas casi
  idénticas en memoria.

Causa raíz:

- Checkpoint frecuente y memoria semántica estaban acoplados.
- Cada vuelta por `observation -> evaluation` generaba evidence con contenido
  repetido y lo persistía como memoria.

Fix aplicado:

- Checkpoint sigue escribiéndose frecuentemente.
- Memoria semántica solo registra si la firma de evidence no fue grabada ya.
- `FileBackedMemory` dedupea por `memory_signature`.
- Test `test_runner_dedupes_memory_records_while_checkpointing` valida que 12
  iteraciones solo dejan una memoria.

### 4.8 Recall no visible

Síntoma observado:

- Después de correr `tokyo-run`, al correr `osaka-run` no se veía claramente si
  el recall había encontrado algo o no.

Causa raíz:

- El runner no imprimía siempre un resumen explícito de recall.
- Si no había matches o si había fallback, el output podía ser ambiguo.

Fix aplicado:

- `print_related_memories()` imprime siempre:
  `memory recall query='...' -> N matches found`.
- Si hay matches, imprime `retrieved memories: ...` y cada memoria.
- Test end-to-end verifica que `search Osaka weather` recuerda memoria de
  `search Tokyo weather` por keywords compartidas.
- Auditoría live confirmó:
  `memory recall query='search Osaka weather' -> 1 matches found`.

### 4.9 Dedupe/checkpoint podía ocultar reconstrucción de memoria

Síntoma observado:

- El usuario vio checkpoints en `/tmp/harness-memory-checkpoints/...`, pero
  `data/harness_memory.json` no existía.
- El riesgo real: si existe checkpoint pero se borra o cambia el archivo de
  memoria, el loop puede parecer "resumido" pero sin memoria semántica local.

Causa raíz:

- Checkpoint y memoria son stores separados.
- Reanudar desde checkpoint no implica necesariamente que el archivo de memoria
  exista o esté sincronizado.

Fix aplicado:

- Se agregó test `test_runner_recreates_memory_when_checkpoint_exists_but_memory_file_is_missing`.
- El runner mantiene checkpoint frecuente, pero memory recording se vuelve a
  ejecutar cuando entra de nuevo en una transición con evidence no grabada en el
  archivo de memoria.

### 4.10 Contradicción README: implemented vs roadmap

Síntoma observado:

- La tabla BOS.PRO marcaba `Parallel agents`, `Worktree isolation` y `Shared
  task queue` como implementados.
- El `Roadmap` listaba esas mismas features genéricas como pendientes.

Causa raíz:

- El README mezclaba implementación local/demo con roadmap producción sin
  distinguir niveles.

Fix aplicado:

- Se eliminaron bullets genéricos del roadmap.
- Se reemplazaron por pendientes reales: 5+ load tests/fairness metrics,
  distributed queue/lock backend, explicit goal graph beyond SQLite demo queue.
- La tabla ahora aclara límites: 3 agentes live para tmux/worktrees, 5 workers
  thread-locales para demo seguro, mem0 no end-to-end.

## 5. Lista de acciones pendientes, priorizada

### P0 - Antes de la entrevista, verificar en vivo lo que quieres afirmar

1. Correr el demo completo y guardar outputs terminales recientes:

```bash
python3 scripts/interview_demo.py map
python3 scripts/interview_demo.py memory
python3 scripts/interview_demo.py eval
python3 scripts/interview_demo.py session-harness
python3 scripts/interview_demo.py agents --agents 5 --tasks 20
```

2. Verificar tmux fuera del sandbox de Codex:

```bash
scripts/run_harness_tmux.sh harness-demo tokyo-run "search Tokyo weather"
# Ctrl+B D para detach
tmux attach -t harness-demo
```

Qué debes observar:

- La sesión sigue corriendo tras detach.
- El runner imprime fases y checkpoints.
- `data/checkpoints/tokyo-run.json` existe.

3. Verificar worktree/tmux real fuera del sandbox:

```bash
TMUX_SESSION_NAME=agent-harness-demo \
TASK_QUEUE_DB=data/task_queue_demo.db \
AGENT_START_SIGNAL=data/agent_harness_demo.start \
SEED_TASKS=18 \
scripts/spawn_agents.sh 3
```

Después:

```bash
git worktree list
sqlite3 data/task_queue_demo.db \
  "select assigned_agent, count(*) from tasks group by assigned_agent;"
```

Qué debes observar:

- Tres worktrees.
- Tres panes tmux.
- Tareas repartidas entre varios agentes.
- Ninguna tarea duplicada.

4. Si quieres reclamar `>5 agentes`, verifica más de cinco, no exactamente cinco:

```bash
python3 scripts/interview_demo.py agents --agents 6 --tasks 24
```

Y si te animas con tmux:

```bash
SEED_TASKS=24 scripts/spawn_agents.sh 6
```

Sin esto, decir `>5 agents` es sobreprometer.

### P1 - Arreglar contradicciones documentales antes de mostrar specs

1. Actualizar `specs/dynamic-workflows.md` línea aproximada 53.

Cambiar de:

```text
Roadmap includes goal graph, queue, memory, locks, and worktree isolation.
```

A algo como:

```text
Roadmap includes explicit goal graph, durable distributed queue,
temporal knowledge graph memory, production scheduler fairness metrics,
and multi-host locking.
```

2. Actualizar `specs/agentic-harness.md` líneas 20-22 para decir que producción
multi-agent scheduling sigue roadmap, pero demo local multi-agent existe en
`specs/multi-agent-harness.md`.

3. Cambiar `docs/HARNESS_ARCHITECTURE.md` línea 141 de `GitHub Spec Kit specs`
a `GitHub Spec Kit-style specs written manually`.

4. Cambiar `specs/spec-kit/agentic-harness/plan.md` línea 79 de `local mem0` a
`file-backed local memory with optional mem0 backend`.

### P2 - Decidir claims de entrevista con precisión

Claims seguros:

- "Tengo un harness propio con Goal/Plan/Action/Observation/Evidence/Eval gates."
- "Tengo checkpoint persistence y wrapper tmux; debo demoarlo fuera del sandbox."
- "Tengo file-backed memory local verificada; mem0 está cableado pero no lo voy a vender como probado end-to-end."
- "Tengo shared queue local con SQLite `BEGIN IMMEDIATE`, test concurrente y demo de 5 workers thread-locales."
- "Tengo git worktree isolation local y script tmux para agentes."
- "Tengo SessionHarness que adapta worker-style events a AgentLoopState, Evidence, EvalGates y TraceStore."

Claims que NO debes decir sin matiz:

- "Uso GitHub Spec Kit oficial" si no corriste el CLI.
- "Uso mem0 en producción" o "memoria semántica vectorial real" si solo usas fallback file-backed.
- "Orquesto >5 agentes reales" si no corriste 6+ procesos/panes/agentes.
- "Sobrevive reboots" si solo demostraste checkpoint/detach/restart local.
- "Tengo temporal knowledge graph" si Zep+Graphiti está solo en roadmap.
- "El FastAPI/Docker runtime está production-ready" si no hay hosted auth,
  remote launcher, object storage, deployment hardening ni stronger isolation.

### P3 - Nice-to-have si sobra tiempo

1. Ejecutar una prueba real de mem0 con una OpenAI key válida en un entorno
controlado y documentar el output, o quitar todavía más peso al claim mem0.
2. Agregar un comando `python3 scripts/interview_demo.py agents --agents 6
--tasks 24` al demo script si quieres cubrir literalmente `>5`.
3. Agregar `docs/HARNESS_COMPARISONS.md` comparando conceptualmente OpenHands,
OpenCode y OMA, pero sin afirmar experiencia real si no la tienes.
4. Agregar screenshots o logs guardados en `docs/assets/` solo si son reales y
sin secretos.
5. Preparar una frase honesta para herramientas no usadas:

```text
I have not integrated OpenHands/OpenCode/OMA in this repo. What I can show is
the harness layer I built: contracts, evidence, eval gates, memory fallback,
trace store, tmux persistence, and local multi-agent queue/worktree isolation.
```

