# BOS.PRO 30-Minute Interview Guide

Guion para una entrevista técnica live screen-share de 30 minutos. La idea no
es hacer una presentación: es conducir una demo terminal-first y defender el
proyecto como un **Agentic Harness for Computer-Use Agents**.

Principio rector: cada afirmación debe poder defenderse con código, docs,
tests, comandos ejecutables o evidencia real. Si algo es roadmap, se dice como
roadmap.

## Preflight antes de la llamada

Haz esto antes de entrar a la reunión, no durante los 30 minutos:

```bash
cd /Users/duvi18/computer-use-orchestrator
scripts/clean_demo_state.sh
make interview-check
python3 -B -m pytest -q
ruff check computer_use_demo tests scripts
```

Si vas a enseñar tmux real:

```bash
tmux list-sessions
```

Si existe una sesión vieja `harness-demo` o `agent-harness-demo`, decide si la
quieres preservar como evidencia o matarla manualmente antes. No improvises ese
estado en vivo.

## Bloque 1: Apertura y encuadre (3 min)

**Haz esto:**

Empieza en la terminal o en README, pero habla primero. No abras código todavía.

**Di esto:**

> Quiero empezar con el marco conceptual, porque para esta entrevista el punto
> no es "hice una app con FastAPI". El punto es harness engineering.
>
> Para mí, un agente no es solo un modelo. Un agente es modelo más harness. Si
> yo no estoy entrenando el modelo, entonces mi trabajo está alrededor del
> modelo: qué contexto ve, qué herramientas puede usar, qué estado persiste, qué
> evidencia cuenta como progreso, qué budgets limitan ejecución, y cuándo debe
> reintentar, replanificar o escalar.
>
> Me gusta pensar el LLM como una CPU: potente, pero inerte. El contexto es
> RAM, la memoria externa es disco, las tools son device drivers, y el harness
> es el sistema operativo que coordina todo.
>
> Por eso este proyecto no está centrado en "qué modelo uso". Está centrado en
> cómo controlo el trabajo del agente. Lo construí como un Agentic Harness para
> computer-use agents. El backend FastAPI/Docker/noVNC existe, pero en esta demo
> es una runtime surface secundaria. La historia principal es el control plane:
> specs, execution contracts, loop state, dynamic workflow, evidence, eval
> gates, traces, memory, tmux persistence y multi-agent orchestration.

**Haz esto:**

```bash
sed -n '1,120p' README.md
```

**Mientras aparece:**

> Aquí se ve el framing actual del repo. No lo presento como un SaaS terminado.
> Lo presento como un production-style agentic harness prototype. Esa honestidad
> importa porque varias piezas están implementadas y verificadas localmente, y
> otras están marcadas explícitamente como roadmap.

## Bloque 2: Spec-Driven Dev (5 min)

**Haz esto:**

```bash
ls specs
find specs/001-multi-agent-orchestration -maxdepth 2 -type f | sort
find .specify -maxdepth 3 -type f | sort | head -20
```

**Di esto:**

> Para mí, spec-driven dev no es escribir documentos bonitos después. Es dejarle
> breadcrumbs al agente y al equipo. Si el código se vuelve cada vez más barato
> de producir, el activo reusable es la especificación: qué queremos, qué no
> queremos, cuáles son los guardrails, cuáles son las condiciones de éxito, y
> qué comportamiento no se puede romper.
>
> En este repo hay tres capas. Primero, specs propias en `specs/`, útiles para
> brownfield porque evolucionan un sistema existente sin ceremonia pesada.
> Segundo, una versión estilo GitHub Spec Kit escrita manualmente en
> `specs/spec-kit/`, para mostrar el mismo trabajo en formato `spec.md`,
> `plan.md`, `tasks.md`. Tercero, evidencia real del CLI oficial de GitHub Spec
> Kit: corrí `specify init --here --force --integration claude` y generé
> `specs/001-multi-agent-orchestration/spec.md` con el flujo real.

**Haz esto:**

```bash
python3 scripts/interview_demo.py map
```

**Mientras aparece:**

> Este comando es un mapa rápido para la entrevista. No hace magia: muestra
> dónde está cada evidencia del harness. Aquí aparecen specs, loop, memory,
> evals, runtime adapter, parallel orchestration y persistence.

**Haz esto:**

```bash
sed -n '1,160p' specs/001-multi-agent-orchestration/spec.md
```

**Mientras aparece:**

> Esta spec fue generada con el flujo oficial de Spec Kit de forma retroactiva
> para documentar una feature ya implementada: multi-agent orchestration. Quiero
> ser preciso: no voy a vender esto como tres meses de Spec Kit en producción.
> Lo que puedo mostrar es uso real del CLI, artifacts reales y una manera clara
> de convertir requisitos en criterios verificables.
>
> Mi lectura sobre herramientas es esta: Spec Kit gana cuando la feature es
> greenfield porque te fuerza a user stories, functional requirements y success
> criteria desde el inicio. Para brownfield, algo tipo OpenSpec o specs propias
> suele ser más cómodo porque puedes gobernar cambios incrementales sobre un
> sistema vivo. Este repo tiene ambos estilos porque el objetivo de la
> entrevista es mostrar cómo pienso, no fingir una ceremonia única.

## Bloque 3: El loop de agentes + DYNAMIC WORKFLOW (7 min)

**Di esto:**

> Esta es la pieza central del demo. Un loop básico de agente no es suficiente
> si solo avanza fases mecánicamente. Lo importante es que la evaluación cambie
> el comportamiento. Cada vez que tengo que escribir "continue" al agente, es un
> fallo del harness de no haber dado suficiente contexto o una política de
> continuación clara.
>
> En este repo el runner ahora tiene un dynamic workflow mínimo y real. En fase
> `evaluation`, corre eval gates reales. Si fallan y quedan retries, llama
> `set_plan()`, crea un plan de retry, incrementa `retry_count` y vuelve a
> `action`. Si se agotan retries, crea un `EscalationDecision` y cambia a
> `escalation`. Si pasan, continúa a `next_step`.
>
> Esto todavía no es un LLM reescribiendo planes complejos. Es una policy simple
> y verificable: gate result -> retry/replan/escalate. Para mí eso es mejor que
> fingir autonomía. Primero hago explícita la máquina de control; después puedo
> cambiar la policy para que un modelo proponga el nuevo plan.

**Haz esto:**

```bash
python3 scripts/interview_demo.py loop
```

**Mientras aparece:**

> Este primer comando muestra el loop básico: `goal`, `plan`, `action`,
> `observation`, `evaluation`, `next_step`. No intenta resolver una tarea real
> de browser. Demuestra el control plane: estado explícito, checkpoint y fases
> observables.

**Haz esto:**

```bash
python3 -m computer_use_demo.harness.runner \
  --goal-id dynamic-pass-demo \
  --goal-text "test dynamic replanning pass" \
  --checkpoint-dir /tmp/dynamic-pass-checkpoints \
  --disable-memory \
  --max-iterations 10 \
  --max-retries 2 \
  --interval-seconds 0.1
```

**Mientras aparece:**

> Este es el caso más visual: el gate puede fallar al principio porque todavía
> no hay suficientes observations; el runner replanifica con `set_plan()`,
> incrementa `retry_count`, vuelve a `action`, genera nueva observation/evidence
> y luego el gate pasa. Busca en pantalla `eval gate failed`, `retry_count=1`,
> y después `eval gate passed -> continuing`.
>
> Ese es el punto defendible: la evaluación ya no es decorativa. Cambia el
> camino del loop.

**Haz esto:**

```bash
python3 -m computer_use_demo.harness.runner \
  --goal-id dynamic-demo \
  --goal-text "test dynamic replanning" \
  --checkpoint-dir /tmp/dynamic-demo-checkpoints \
  --disable-memory \
  --max-iterations 12 \
  --max-retries 2 \
  --min-observations-for-pass 999 \
  --interval-seconds 0.1
```

**Mientras aparece:**

> Ahora fuerzo el gate para que no pueda pasar: pido 999 observations. Esto
> muestra el otro branch: retry uno, retry dos, y después `max retries exceeded
> -> escalating`. Aquí el harness no se queda en loop infinito y tampoco marca
> éxito falso. Escala con una decisión explícita.

**Haz esto:**

```bash
python3 scripts/interview_demo.py eval
```

**Mientras aparece:**

> Este eval es offline. No llama Anthropic ni Docker. Su trabajo es probar un
> principio: no confiar en el self-reporting del agente. El failure mode clásico
> es premature completion: el agente dice "done" antes de tener evidencia. Aquí
> los gates hacen que completion dependa de evidence y estado, no solo de texto.

**Haz esto:**

```bash
python3 scripts/interview_demo.py session-harness
```

**Mientras aparece:**

> Este comando muestra el adapter `SessionHarness`: worker-style events se
> convierten en observations, evidence, eval results y traces. Importante: en
> este demo los eventos son sintéticos, generados por el script. La integración
> real con FastAPI existe en código vía `_persist_worker_event()`, pero esta
> ronda no ejercitó end-to-end un stream real desde un worker Docker corriendo
> Claude Computer Use.

## Bloque 4: Persistence tmux (4 min)

**Di esto:**

> Persistence significa que el run no depende de mi terminal. El runner escribe
> `AgentLoopState` a disco, y tmux lo mantiene vivo aunque cierre terminal o
> pierda SSH. La parte importante no es tmux por sí mismo; tmux es el wrapper
> operacional. La semántica de continuidad está en el checkpoint JSON.

**Haz esto:**

```bash
scripts/run_harness_tmux.sh harness-demo tokyo-run "search Tokyo weather"
```

Dentro de tmux:

```text
Ctrl-b d
```

Reconectar:

```bash
scripts/run_harness_tmux.sh harness-demo tokyo-run "search Tokyo weather"
```

Parar y relanzar:

```text
Ctrl-C
```

```bash
scripts/run_harness_tmux.sh harness-demo tokyo-run "search Tokyo weather"
```

Opcional:

```bash
ls -lt ~/.local/share/tmux/resurrect/ | head
cat data/checkpoints/tokyo-run.json | head -40
```

**Mientras aparece:**

> El script es idempotente: si la sesión tmux existe, hace attach en vez de
> crear otra. Eso evita duplicar runs por accidente. Al relanzar después de
> parar el proceso, busco la línea `resumed checkpoint`. Eso prueba que no
> depende de la memoria del proceso anterior.
>
> Además lo probé fuera del sandbox con tmux-resurrect y tmux-continuum: hubo un
> reboot real de macOS, la sesión `harness-demo` se restauró y
> `data/checkpoints/tokyo-run.json` seguía intacto. Lo digo como evidencia local
> verificada, no como garantía de reattachment de Docker workers después de
> reboot.

## Bloque 5: Orquestación paralela (6 min)

**Di esto:**

> La parte multi-agente demuestra un patrón de orquestación, no una charla libre
> entre agentes. La idea es descomponer, delegar y verificar. Para que eso no se
> vuelva caos, necesito dos cosas: aislamiento de escritura y una shared task
> list con single-writer lock.
>
> El aislamiento por git worktree evita que dos agentes escriban encima del
> mismo árbol de trabajo. La cola compartida evita doble asignación. Y la regla
> importante es que no confío en coordinación social entre agentes; confío en
> contratos operacionales.

**Haz esto:**

```bash
python3 scripts/interview_demo.py agents --agents 6 --tasks 24
```

**Mientras aparece:**

> Este es el demo seguro thread-based: seis agentes, veinticuatro tareas,
> distribución entre todos, cero duplicate claims. Esta es la evidencia que
> respalda el claim de más de cinco agentes. Todavía no es el load test grande
> de 10+ agentes y 100+ tareas; eso sigue como success criterion pendiente.

**Haz esto:**

```bash
sed -n '1,220p' computer_use_demo/harness/shared_task_queue.py
```

**Mientras aparece:**

> El punto técnico está en `BEGIN IMMEDIATE`. SQLite permite un writer a la vez.
> `claim_next_task(agent_id)` abre una transacción inmediata, toma la siguiente
> tarea pending, la marca claimed y hace commit. Eso evita doble asignación.
>
> Una corrección real fue fair claiming. El lock funcionaba, pero con pocas
> tareas y trabajo instantáneo un agente rápido vaciaba la cola antes de que los
> demás arrancaran. Agregué más tareas demo, sleep realista y una start barrier
> para que todos empiecen juntos.

**Haz esto:**

```bash
TASK_QUEUE_DB=data/task_queue_demo.db TMUX_SESSION_NAME=agent-harness-demo SEED_TASKS=18 scripts/spawn_agents.sh 3
git worktree list
sqlite3 data/task_queue_demo.db "select assigned_agent, count(*) from tasks group by assigned_agent;"
```

**Mientras aparece:**

> Esta versión crea worktrees reales: `worktrees/agent-1`, `agent-2`,
> `agent-3`. Cada pane corre `scripts/agent_worker.py` desde su propio
> worktree. Eso evita conflictos de escritura si el trabajo real fuera editar
> archivos.
>
> También probé Claude Code Agent Teams con
> `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` como ejercicio aislado: tres agentes
> en worktrees separados y shared task list nativa de Claude Code. No está
> integrado al repo; lo menciono como evidencia externa de haber practicado el
> mismo patrón en otro harness.

## Bloque 6: Memory layer (3 min)

**Haz esto:**

```bash
python3 scripts/interview_demo.py memory
```

**Mientras aparece:**

> Memoria aquí es intencionalmente estrecha. El demo local usa file-backed
> memory por defecto para no depender de OpenAI. El primer run guarda evidence
> para Tokyo. El segundo run pregunta por Osaka y debe imprimir algo como
> `memory recall query='search Osaka weather' -> 1 matches found`.
>
> Esto importa porque el agente no empieza cada sesión desde cero. Pero también
> hay disciplina: no guardo cada checkpoint como memoria semántica. Solo guardo
> evidence deduplicada. Antes se llenaba `harness_memory.json` con entradas casi
> idénticas; lo corregí porque memoria ruidosa es peor que no tener memoria.
>
> mem0 está cableado como backend opcional, pero solo se activa con una OpenAI
> key válida. No lo vendo como probado end-to-end. La diferencia con un temporal
> knowledge graph tipo Zep + Graphiti es que mi capa actual recupera recuerdos
> relacionados; un temporal KG modelaría entidades, relaciones, eventos y
> cambios de estado entre runs.

## Bloque 7: Bugs encontrados en vivo (4 min)

**Di esto:**

> La parte más importante de la preparación no fue escribir más código. Fue
> verificar en vivo y encontrar fallos. Para mí, harness engineering maduro no
> es acumular capas; también es podar estructura y reducir failure modes.
>
> Encontré varios bugs reales.
>
> Primero, en multi-agent claiming parecía que no había concurrencia. La causa
> no era el lock: `BEGIN IMMEDIATE` evitaba doble claim correctamente. La causa
> era timing: con pocas tareas y trabajo instantáneo, un agente rápido vaciaba
> la cola. El fix fue subir seed de tareas, agregar sleep realista y una start
> barrier para que todos los panes arrancaran juntos.
>
> Segundo, mem0. Configuré embeddings locales, pero mem0 igual podía intentar
> usar OpenAI LLM en `add()`. Además si `OPENAI_API_KEY` contenía una Anthropic
> key `sk-ant-...`, fallaba de forma engañosa. El fix fue: si no hay OpenAI key
> válida, no inicializo mem0 real; uso FileBackedMemory. Y si mem0 falla en
> runtime, degrado a fallback.
>
> Tercero, evidence spam. El runner estaba checkpointing frecuentemente, que es
> correcto para resiliencia, pero también grababa evidence memory en cada tick.
> Eso convertía la memoria en ruido. El fix fue separar checkpoint de semantic
> memory y deduplicar por signature de evidence.
>
> Cuarto, dedupe contra checkpoint. Si había checkpoint pero el archivo real de
> memoria faltaba, parecía que ya había estado semántico, pero no había memoria
> recuperable. Agregué test para reconstrucción de memoria cuando checkpoint
> existe pero memory file falta.
>
> Quinto, recuperación de estado corrupto. Si un checkpoint JSON está corrupto,
> ahora se mueve a `.corrupted-<timestamp>` y el runner arranca fresco. Si la
> memoria JSON está corrupta, el recall no crashea; imprime warning y trata la
> memoria como vacía. Eso es pequeño, pero en un demo live evita que estado
> local sucio tumbe toda la narrativa.
>
> Lo que quiero mostrar con esto es cómo trabajo: construyo el harness, lo corro
> en vivo, observo dónde se rompe, documento límites y convierto bugs
> operacionales en guardrails.

## Bloque 8: Cierre y roadmap (2 min)

**Di esto:**

> Para cerrar: el reusable asset no es el modelo, es el harness. Este repo no
> compite con frontier models. Construye estructura alrededor del modelo:
> specs, contracts, budgets, memory, task queues, eval gates, dynamic workflow,
> traces, persistence y runtime boundaries.
>
> Lo que existe y está verificado: loop local, dynamic replanning mínimo,
> checkpoints, tmux persistence con reboot real en mi Mac, memory file-backed,
> eval gates, SessionHarness adapter con eventos sintéticos, seis agentes
> thread-based con veinticuatro tareas sin duplicados, tres agentes
> tmux/worktree, Spec Kit CLI oficial retroactivo y FastAPI/Docker runtime
> backend.
>
> Lo que no voy a vender como hecho: mem0 real end-to-end, Letta,
> Zep+Graphiti, OpenHands, OpenCode, OMA, load test de 10+ agentes con 100+
> tareas, object storage, hosted auth, remote worker launcher y reattachment de
> Docker workers después de reboot.
>
> Mi aporte aquí es pensar en harness como disciplina: qué estructura agregar,
> qué estructura quitar, y cómo hacer que el agente avance sin depender de que
> un humano escriba "continue".

## Preguntas difíciles

### 1. "¿Qué es un harness, en tus palabras?"

> Un harness es el control plane alrededor del modelo. Si el modelo es la CPU,
> el harness decide qué contexto entra como RAM, qué memoria externa funciona
> como disco, qué tools son drivers, qué budgets limitan la ejecución, qué
> evidence permite completar, y qué eval gates impiden self-reporting. En este
> repo eso está modelado en `ExecutionContract`, `AgentLoopState`, `EvalGate`,
> `TraceStore`, `HarnessMemory` y `SessionHarness`.

### 2. "¿Cómo funciona el dynamic workflow en tu harness?"

> En el runner, la fase `evaluation` ya no es decorativa. Corre eval gates
> reales: `require_evidence("checkpoint")` y un gate simple de cantidad mínima
> de observations. Si un gate falla y quedan retries, el runner llama
> `set_plan()`, crea un plan de retry con la razón del fallo, incrementa
> `retry_count` y vuelve a `action`. Si se agotan retries, crea un
> `EscalationDecision` con `reason="max retries exceeded"` y cambia a
> `escalation`. Si los gates pasan, continúa a `next_step`.

### 3. "¿La replanificación es autónoma o manual?"

> El trigger es automático: viene del resultado del eval gate. La policy también
> corre automáticamente: retry hasta `max_retries`, luego escalation. Lo honesto
> es que el nuevo plan lo genera el runner con una plantilla simple, no un LLM.
> El siguiente paso real sería que un LLM generara el nuevo plan basándose en la
> razón del fallo, pero dentro de budgets y contracts explícitos.

### 4. "¿Tu loop realmente controla Claude Computer Use?"

> Parcialmente. El worker Claude Computer Use sigue su ejecución normal. El
> `SessionHarness` adapter consume worker-style events y los transforma en
> observations/evidence/evals/traces. En el demo `session-harness`, esos eventos
> son sintéticos; la integración real con FastAPI existe vía
> `_persist_worker_event()`, pero no la vendo como verificada end-to-end con un
> worker Docker real en esta ronda.

### 5. "¿Por qué no usaste Zep + Graphiti si la vacante habla de temporal KG?"

> Porque preferí no inflar el proyecto con infra que no iba a poder verificar
> bien antes de la entrevista. Implementé file-backed memory local y mem0
> opcional, y documento explícitamente que temporal KG es roadmap. La diferencia
> es que mi memoria actual recupera recuerdos relacionados; Zep+Graphiti
> modelaría entidades, relaciones, cambios temporales y causalidad entre runs.

### 6. "¿Mem0 está funcionando realmente?"

> El backend mem0 está cableado y probado con mocks/config, pero no está probado
> end-to-end con OpenAI key válida. De hecho encontré que mem0 puede llamar a
> OpenAI LLM aunque uses embeddings locales. Por eso el comportamiento local
> defendible es FileBackedMemory, y mem0 queda opcional si hay key válida.

### 7. "¿Por qué SQLite para la shared queue?"

> Porque el objetivo era demostrar el patrón de single-writer claim local sin
> meter Redis/Celery/Postgres distributed locking. `BEGIN IMMEDIATE` me da una
> transacción de writer único en SQLite: una tarea no puede ser reclamada dos
> veces. Para production multi-host, esto debe migrar a una cola durable o DB
> con locking/retry semantics más fuertes.

### 8. "¿Realmente corriste más de 5 agentes?"

> Sí. La evidencia verificada fue `python3 scripts/interview_demo.py agents
> --agents 6 --tasks 24`: veinticuatro de veinticuatro tareas completadas,
> distribución entre seis agentes y cero duplicate claims. También tengo versión
> tmux/worktree de tres agentes. Lo que no corrí todavía es el success criterion
> mayor de la spec: diez o más agentes y cien o más tareas.

### 9. "¿Qué diferencia hay entre tu demo thread-based y agentes reales?"

> El demo thread-based prueba la cola y el claim concurrente de forma rápida y
> reproducible. La versión tmux/worktree prueba aislamiento operacional por
> procesos, panes y filesystem. Ninguna de las dos demuestra razonamiento
> independiente profundo de seis LLMs; demuestra orchestration substrate:
> aislamiento, task queue y single-writer locks.

### 10. "¿Cómo evitas premature completion?"

> No confío solo en que el agente diga "done". En `SessionHarness`, un `done`
> event produce `Evidence`; luego `EvalGate` valida, por ejemplo,
> `require_evidence("answer")` y `require_terminal_status`. En el runner, la
> fase `evaluation` también decide si continúa, reintenta o escala. Completion
> debe depender de artifacts/evidence y gates, no de self-reporting.

### 11. "¿Qué parte está más cerca de producción y cuál es prototipo?"

> Más cerca de producción: FastAPI ownership checks, session lifecycle, limits,
> UI tokens, WorkerLauncher abstraction, metrics/readiness, SQLite/Postgres
> foundation, retention/artifact metadata. Más prototipo: harness memory,
> dynamic workflow con policy simple, local evals, SessionHarness persistence,
> multi-agent scheduler fairness y remote worker orchestration.

### 12. "¿Por qué Spec Kit vs OpenSpec?"

> Spec Kit es excelente para greenfield porque fuerza estructura desde cero:
> user stories, functional requirements, success criteria y tasks. OpenSpec
> suele ser más cómodo para brownfield porque describe y gobierna cambios en un
> sistema vivo. En este repo hice ambas cosas: specs manuales para evolucionar
> el brownfield, y luego usé el CLI oficial de Spec Kit para documentar
> retroactivamente multi-agent orchestration.

### 13. "¿Qué aprendiste de los bugs que encontraste?"

> Que los bugs importantes de harness no siempre son bugs de lógica pura. A
> veces son bugs de operación: timing, estado sucio, memoria ruidosa, recovery
> mala, claims que se ven correctos en tests pero mal en vivo. Eso cambió el
> proyecto: agregué start barrier, dedupe semántico, fallback memory, clear lock
> errors, corrupt checkpoint recovery y dynamic workflow real en evaluation.

### 14. "¿Cómo compararías este repo con OpenHands/OpenCode/OMA?"

> Honestamente: no integré OpenHands/OpenCode/OMA en este repo, así que no voy a
> fingir experiencia directa aquí. Conceptualmente, compararía tres capas:
> agent loop, tool API y orchestration model. Este repo se enfoca en el control
> plane: specs, contracts, state, evals, memory, queue y traces. Para una
> evaluación formal de OpenHands/OpenCode/OMA, haría una spec comparativa y
> correría el mismo benchmark harness en cada uno.

## Fallback si algo falla en vivo

Si tmux falla:

```bash
python3 scripts/interview_demo.py loop
cat data/interview_checkpoints/interview-loop.json
```

**Di esto:**

> tmux es el wrapper operacional. El punto del harness persistence está en el
> checkpoint. Si tmux molesta en pantalla, muestro el modo bounded CLI.

Si Docker/FastAPI no está listo:

**Di esto:**

> No necesito Docker para defender el harness. Docker es runtime backend. La
> entrevista es sobre specs, loop, dynamic workflow, memory, eval gates, queue,
> traces y persistence.

Si la memory demo no encuentra nada:

```bash
scripts/clean_demo_state.sh
python3 scripts/interview_demo.py memory
```

**Di esto:**

> Prefiero resetear estado y repetir un demo limpio antes que explicar un
> archivo local sucio.

Si preguntan por claims no implementados:

**Di esto:**

> Lo tengo documentado como roadmap. Prefiero subestimar el claim y que el
> código lo respalde, que sobreprometer en una entrevista de harness
> engineering.
