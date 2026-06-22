# BOS.PRO 30-Minute Interview Guide

Este guion está diseñado para una entrevista técnica live screen-share de 30
minutos. No es una presentación: es una narración terminal-first para defender
el proyecto como un Agentic Harness for Computer-Use Agents.

Principio rector: cada claim debe poder defenderse con código, docs, test,
comando ejecutable o evidencia documentada. No vender como implementado lo que
es roadmap.

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

## Bloque 1 - Apertura y encuadre (3 min)

No abras código todavía. Empieza en la terminal o en README, pero habla primero.

Narración literal:

> Quiero empezar con el marco conceptual, porque para esta entrevista el punto
> no es "hice una app con FastAPI". El punto es harness engineering.
>
> En uno de los videos aparece una frase que me parece la definición más limpia:
> [VIDEO 1] "Agent equals model plus harness." Si yo no estoy entrenando el
> modelo, entonces mi trabajo está en el harness: qué ve el modelo, cuándo lo ve,
> qué herramientas puede usar, qué estado persiste, qué evidencia cuenta como
> progreso y cuándo debe parar o escalar.
>
> La analogía del video es que el LLM es como una CPU: poderoso, pero inerte.
> El contexto es RAM, la memoria externa es disco, las herramientas son device
> drivers, y el harness es el sistema operativo que coordina todo eso.
>
> También mencionan el 6x gap: mismo modelo, mismo benchmark, hasta seis veces
> diferencia por la orquestación alrededor del modelo. Ese es el motivo por el
> cual este proyecto no está centrado en "qué modelo uso", sino en cómo controlo
> el trabajo del agente.
>
> Entonces lo que construí aquí es eso: un Agentic Harness para computer-use
> agents. El backend FastAPI/Docker/noVNC existe, pero en esta demo lo voy a
> tratar como runtime surface. La historia principal es el control plane:
> specs, execution contracts, loop state, evidence, eval gates, traces, memory,
> persistence y multi-agent orchestration.

Abre README solo después de decir lo anterior:

```bash
sed -n '1,90p' README.md
```

Mientras aparece el output:

> Aquí se ve el framing actual del repo. No lo presento como SaaS terminado. Lo
> presento como production-style agentic harness prototype. Esa honestidad es
> importante porque varias piezas están implementadas localmente, y otras están
> marcadas como roadmap.

## Bloque 2 - Spec-Driven Dev: cómo defines el trabajo (5 min)

Abre VS Code o usa terminal:

```bash
ls specs
find specs/001-multi-agent-orchestration -maxdepth 2 -type f | sort
find .specify -maxdepth 3 -type f | sort | head -20
python3 scripts/interview_demo.py map
```

Narración literal antes de correr `map`:

> Para mí, spec-driven dev no es escribir documentos bonitos después. Es dejarle
> breadcrumbs al agente y al equipo. En el video de Ryan Lopopolo hay una frase
> que usé mucho para pensar este repo: [VIDEO 2 - Lopopolo] "The important thing
> is not the code but the prompt and the guardrails that got you there."
>
> En otras palabras, si el código es cada vez más barato de producir, el activo
> reusable es la especificación, los guardrails, los ADRs, la definición de qué
> significa un buen resultado.

Mientras corre:

```bash
python3 scripts/interview_demo.py map
```

Narración mientras aparece el output:

> Este comando no hace magia. Es un mapa rápido para la entrevista: dónde está
> cada evidencia del harness. Aquí aparecen specs, loop, memory, evals, runtime
> adapter, parallel orchestration y persistence.
>
> En `specs/` tengo specs propias, útiles para brownfield porque evolucionan el
> repo existente sin forzar una ceremonia pesada. En `specs/spec-kit/` tengo una
> versión estilo Spec Kit escrita manualmente. Y además, después de la auditoría,
> corrí el CLI oficial de GitHub Spec Kit: `specify init --here --force
> --integration claude`, y generé `specs/001-multi-agent-orchestration/spec.md`
> con el flujo real.

Abre la spec oficial:

```bash
sed -n '1,140p' specs/001-multi-agent-orchestration/spec.md
```

Narración:

> Aquí hay una distinción que quiero ser preciso al defender: Spec Kit me parece
> muy fuerte para greenfield, porque te fuerza a user stories, functional
> requirements, edge cases y success criteria desde el inicio. Para brownfield,
> algo tipo OpenSpec o specs propias suele ganar porque puedes describir el
> comportamiento existente y cambiarlo incrementalmente. Este repo tiene ambos:
> specs manuales para evolución brownfield, y una spec oficial retroactiva de
> Spec Kit para la feature multi-agente ya implementada.
>
> No voy a vender esto como tres meses de Spec Kit en producción. Lo que puedo
> mostrar es uso real del CLI, artifacts reales, y una forma clara de convertir
> requisitos en tareas verificables.

Si preguntan por OpenSpec:

> Mi lectura: OpenSpec gana cuando ya existe un sistema vivo y necesitas gobernar
> cambios incrementales, porque se adapta mejor al brownfield. Spec Kit gana
> cuando partes de una feature nueva y quieres estructura fuerte desde cero.
> Aquí el ejemplo concreto es que la multi-agent orchestration ya existía; por
> eso la spec oficial es retroactiva, no pretendo que haya guiado toda la
> implementación original.

## Bloque 3 - El loop de agentes: goal -> plan -> action -> evidence (6 min)

Comandos:

```bash
python3 scripts/interview_demo.py loop
python3 scripts/interview_demo.py eval
python3 scripts/interview_demo.py session-harness
```

Antes del primer comando:

> Esta es la pieza central. En el video sobre harness engineering se dice:
> [VIDEO 1] "Execution contracts turn fuzzy LLM completions into bounded agent
> calls." Y enumera cinco elementos: required outputs, budgets, permissions,
> completion conditions y output paths.
>
> Eso está modelado aquí como `ExecutionContract`, `SessionBudgets`,
> `ToolGrantPolicy`, `EvalGate` y `TraceStore`. No es un wrapper de chat. Es una
> máquina de estado mínima: goal, plan, action, observation, evidence,
> evaluation, next_step o escalation.

Corre:

```bash
python3 scripts/interview_demo.py loop
```

Mientras aparece el output:

> Fíjate en las fases: `goal`, `plan`, `action`, `observation`, `evaluation`,
> `next_step`. Esto es deliberadamente simple. No estoy intentando fingir que
> este CLI resuelve una tarea real de browser. Lo que demuestra es el control
> plane: el estado avanza, se checkpointa y se puede reanudar.
>
> Una cosa que corregí durante la preparación fue separar checkpoint de memoria
> semántica. El checkpoint se puede escribir cada tick para resiliencia, pero no
> debe crear evidence memory duplicada cada tick. Si no, la memoria se vuelve
> ruido. Ese bug apareció en vivo y está documentado.

Abre el archivo relevante si hay tiempo:

```bash
sed -n '1,260p' computer_use_demo/harness/runner.py
```

Narración:

> También agregué manejo defensivo: si un checkpoint JSON está corrupto, no
> crashea la demo. Lo renombra con `.corrupted-<timestamp>` y arranca fresco.
> Para una entrevista eso importa porque un harness que no puede recuperarse de
> estado parcial no es un harness confiable.

Corre:

```bash
python3 scripts/interview_demo.py eval
```

Mientras aparece:

> Este eval es offline. No llama Anthropic ni Docker. Su trabajo es probar el
> principio: no confiar en el self-reporting del agente. El failure mode del
> video es "premature completion": el agente dice "done" antes de que exista
> evidencia suficiente. Aquí el gate `require_evidence` obliga a que haya
> evidence antes de marcar éxito.

Corre:

```bash
python3 scripts/interview_demo.py session-harness
```

Mientras aparece:

> Este comando muestra el adapter `SessionHarness`: worker-style events se
> convierten en observations, evidence, eval results y trace. Importante: en este
> comando los eventos son sintéticos, generados por el demo script. La integración
> real con el FastAPI orchestrator existe en código vía `_persist_worker_event()`,
> pero esta ronda de verificación no ejercitó end-to-end el stream real desde un
> worker Docker corriendo Claude Computer Use. Prefiero decirlo así porque quiero
> que cada claim sea defendible.

Abre arquitectura:

```bash
sed -n '1,180p' docs/HARNESS_ARCHITECTURE.md
```

Narración:

> Este documento resume el flujo: Spec -> ExecutionContract -> AgentLoopState ->
> Worker Events -> Observation/Evidence -> EvalGates -> Traces/Memory -> Next
> Step/Escalation.

## Bloque 4 - Persistence: runs que sobreviven reboots (4 min)

Comandos exactos:

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

Después:

```text
Ctrl-C
```

Relanzar:

```bash
scripts/run_harness_tmux.sh harness-demo tokyo-run "search Tokyo weather"
```

Opcional:

```bash
ls -lt ~/.local/share/tmux/resurrect/ | head
cat data/checkpoints/tokyo-run.json | head -40
```

Narración antes de iniciar:

> Persistence para mí significa que el run no depende de mi terminal. Ryan dice
> algo muy fuerte: [VIDEO 2 - Lopopolo] "Every time I have to type continue to
> the agent is a failure of the harness to provide enough context." Esa frase
> aplica directo aquí. El runner escribe `AgentLoopState` a disco, y tmux lo
> mantiene vivo aunque cierre terminal o pierda SSH.

Mientras corre tmux:

> Aquí el proceso está vivo dentro de tmux. Cada tick imprime fase y checkpoint.
> La parte importante no es tmux por sí mismo; tmux es el contenedor operacional
> del run. La semántica de continuidad está en el checkpoint JSON.

Al hacer `Ctrl-b d`:

> Esto simula cerrar terminal o perder SSH. El proceso sigue vivo fuera de mi
> sesión interactiva.

Al reconectar:

> El mismo script es idempotente: si la sesión existe, hace attach en vez de
> crear otra. Eso evita duplicar runs por accidente.

Al hacer `Ctrl-C` y relanzar:

> Ahora sí paro el proceso. Al relanzar, busco la línea `resumed checkpoint`.
> Eso prueba que no depende de memoria del proceso anterior.

Opcional reboot:

> Además lo probé fuera del sandbox con tmux-resurrect y tmux-continuum. Hubo un
> reboot real de macOS, la sesión `harness-demo` se restauró y
> `data/checkpoints/tokyo-run.json` seguía intacto. Eso está documentado como
> evidencia local, no como garantía de reattachment de Docker workers.

## Bloque 5 - Orquestación paralela: >5 agentes, worktrees, single-writer lock (6 min)

Comandos:

```bash
python3 scripts/interview_demo.py agents --agents 6 --tasks 24
TASK_QUEUE_DB=data/task_queue_demo.db TMUX_SESSION_NAME=agent-harness-demo SEED_TASKS=18 scripts/spawn_agents.sh 3
git worktree list
sqlite3 data/task_queue_demo.db "select assigned_agent, count(*) from tasks group by assigned_agent;"
```

Antes del primer comando:

> La parte multi-agente conecta con otra frase del video: [VIDEO 1] "Roughly 90%
> of all compute flows through delegated child agents, not the parent. The
> harness is an orchestration pattern, not a reasoning pattern. It decomposes,
> delegates, and verifies."
>
> Entonces aquí no intento que seis agentes conversen libremente y se pongan de
> acuerdo por vibes. Les doy aislamiento por git worktree y una shared task list
> con single-writer claim.

Corre:

```bash
python3 scripts/interview_demo.py agents --agents 6 --tasks 24
```

Mientras aparece:

> Este es el demo seguro thread-based: seis agentes, veinticuatro tareas,
> distribución entre todos, cero duplicate claims. Es la evidencia que respalda
> el claim `>5 agents`. No es todavía el load test de 10+ agentes y 100+ tareas
> de la spec oficial; eso sigue como success criterion pendiente.

Abre la queue:

```bash
sed -n '1,180p' computer_use_demo/harness/shared_task_queue.py
```

Narración:

> El punto técnico está en `BEGIN IMMEDIATE`. SQLite permite un writer a la vez.
> `claim_next_task(agent_id)` abre una transacción inmediata, toma la siguiente
> tarea pending, la marca claimed, y hace commit. Eso evita doble asignación.
> También agregué un mensaje claro si la DB está locked, porque en demo un
> timeout mudo de SQLite se ve fatal.

Corre la versión tmux/worktree:

```bash
TASK_QUEUE_DB=data/task_queue_demo.db TMUX_SESSION_NAME=agent-harness-demo SEED_TASKS=18 scripts/spawn_agents.sh 3
```

Mientras aparece:

> Esta versión crea worktrees reales: `worktrees/agent-1`, `agent-2`,
> `agent-3`. Cada pane corre `scripts/agent_worker.py` desde su propio
> worktree. Eso evita conflictos de escritura cuando un agente edita archivos.
>
> Hay una barrera de start signal para que no arranque un agente rápido antes de
> que los demás estén listos. Esa fue una corrección real: el lock funcionaba,
> pero con tareas instantáneas un agente vaciaba la cola antes de que los otros
> empezaran, y se veía como mala concurrencia.

Después de detach o en otra terminal:

```bash
git worktree list
sqlite3 data/task_queue_demo.db "select assigned_agent, count(*) from tasks group by assigned_agent;"
```

Narración:

> Esto demuestra worktree isolation y shared task queue. También probé Claude
> Code Agent Teams con `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` como evidencia
> externa: tres agentes en worktrees separados con shared task list nativa de
> Claude Code. No está integrado en este repo; fue un ejercicio aislado para
> comparar el mismo patrón en otro harness.

## Bloque 6 - Memory layer (4 min)

Comando:

```bash
python3 scripts/interview_demo.py memory
```

Narración antes:

> Memoria aquí es intencionalmente estrecha. En el video aparece [VIDEO 1]
> "file-backed state externalizes memory to path-addressable files surviving
> truncation, restarts and delegation." Mi demo local usa file-backed memory por
> defecto. mem0 está cableado como backend opcional, pero solo se activa con una
> OpenAI key válida y no lo vendo como probado end-to-end.

Mientras corre:

> El primer run guarda evidence para Tokyo. El segundo run pregunta por Osaka y
> debería imprimir `memory recall query='search Osaka weather' -> 1 matches
> found`. Eso importa porque el agente no empieza cada sesión desde cero.
>
> Pero también hay disciplina: no guardo cada checkpoint tick como memoria. Solo
> evidence semántica deduplicada. Esa fue otra corrección real: antes se llenaba
> `harness_memory.json` con decenas de entradas casi idénticas.

Explicación flat-vector vs temporal graph:

> Esto es flat recall: keyword/local memory, y mem0 opcional sería más cercano a
> flat-vector semantic recall. Un temporal knowledge graph tipo Zep + Graphiti es
> otra categoría: entidades, relaciones, eventos en el tiempo, y cambios de
> estado. Por ejemplo, no solo "Tokyo weather"; sino "goal A produjo evidence B,
> fue contradicho por observation C, y luego se actualizó por run D". Eso sigue
> roadmap real en este repo.

## Bloque 7 - Bugs encontrados en vivo: el meta-punto más importante (4 min)

No abras código si no hace falta. Habla como engineer.

Narración literal:

> Para mí, la parte más importante de la preparación no fue escribir más código.
> Fue verificar en vivo y encontrar fallos. Ryan lo dice como proceso:
> [VIDEO 2 - Lopopolo] observar, refinar y tomar decisiones adicionales sobre
> non-functional requirements. Y el otro video dice algo parecido: el harness no
> solo crece, también se poda; mature harness work is pruning structure down.
>
> Encontré varios bugs reales.
>
> Primero, en multi-agent claiming parecía que no había concurrencia. La causa
> no era el lock: `BEGIN IMMEDIATE` evitaba doble claim correctamente. La causa
> era timing: con pocas tareas y trabajo instantáneo, un agente rápido vaciaba la
> cola. El fix fue subir seed de tareas, agregar sleep realista y una start
> barrier para que todos los panes arrancaran juntos. Eso dice que no me quedé
> mirando solo tests; miré el comportamiento operativo.
>
> Segundo, mem0. Configuré HuggingFace embeddings, pero mem0 igual intentaba usar
> OpenAI LLM en `add()`. Además si `OPENAI_API_KEY` contenía una Anthropic key
> `sk-ant-...`, fallaba de forma engañosa. El fix fue: si no hay OpenAI key
> válida, no inicializo mem0 real; uso FileBackedMemory. Y si mem0 falla en
> runtime, degrado a fallback.
>
> Tercero, evidence spam. El runner estaba checkpointing frecuentemente, que es
> correcto para resiliencia, pero también estaba grabando evidence memory en cada
> tick. Eso convertía la memoria en ruido. El fix fue separar checkpoint de
> semantic memory y deduplicar por signature de evidence.
>
> Cuarto, dedupe contra checkpoint. Si había checkpoint pero el archivo real de
> memoria faltaba, parecía que ya había estado semántico, pero no había memoria
> recuperable. Agregué test para reconstrucción de memoria cuando checkpoint
> existe pero memory file falta.
>
> Y finalmente, después del code quality audit, agregué recuperación para JSON
> corrupto: checkpoint corrupto se mueve a `.corrupted-<timestamp>` y memoria
> corrupta se trata como vacía con warning. Eso es pequeño, pero en un demo live
> evita que un archivo local sucio tumbe la narrativa.

Qué dice de ti:

> Lo que quiero que veas de mi forma de trabajar es esto: no estoy intentando
> mostrar un demo perfecto. Estoy construyendo un harness observable, luego lo
> rompo en vivo, documento los límites, y reduzco los failure modes que pueden
> bloquear ejecución autónoma.

## Bloque 8 - Cierre honesto y roadmap (2 min)

Narración literal:

> Para cerrar: [VIDEO 1] "The reusable asset isn't the model, it's the harness."
> Esa es la idea de este repo. No estoy compitiendo con frontier models; estoy
> construyendo la estructura alrededor del modelo: specs, contracts, budgets,
> memory, task queues, eval gates, traces, persistence y runtime boundaries.
>
> Lo que existe y está verificado: loop local, checkpoints, tmux persistence con
> reboot real en mi Mac, memory file-backed, eval gates, SessionHarness adapter
> con eventos sintéticos, 6 agentes thread-based con 24 tareas sin duplicados,
> 3 agentes tmux/worktree, Spec Kit CLI oficial retroactivo, y FastAPI/Docker
> runtime backend.
>
> Lo que no voy a vender como hecho: mem0 real end-to-end, Letta,
> Zep+Graphiti, OpenHands, OpenCode, OMA, 10+ agentes con 100+ tareas,
> object storage, hosted auth, remote worker launcher y reattachment de Docker
> workers después de reboot.
>
> Y eso es coherente con la vacante: ustedes están construyendo un Business
> Operating System, no manteniendo CRUD. Mi aporte es pensar en harness como una
> disciplina: qué estructura agregar, qué estructura quitar, y cómo hacer que el
> agente avance sin depender de que un humano escriba "continue".

## Preguntas difíciles

### 1. "¿Qué es un harness, en tus palabras?"

Respuesta:

> Un harness es el control plane alrededor del modelo. Si el modelo es la CPU,
> el harness decide qué contexto entra como RAM, qué memoria externa funciona
> como disco, qué tools son drivers, qué budgets limitan la ejecución, qué
> evidence permite completar, y qué eval gates impiden self-reporting. En este
> repo eso está modelado en `ExecutionContract`, `AgentLoopState`, `EvalGate`,
> `TraceStore`, `HarnessMemory` y `SessionHarness`.

### 2. "¿Tu loop realmente controla Claude Computer Use?"

Respuesta:

> Parcialmente. El worker Claude Computer Use sigue su ejecución normal. El
> `SessionHarness` adapter consume worker-style events y los transforma en
> observations/evidence/evals/traces. En el demo `session-harness`, esos eventos
> son sintéticos; la integración real con FastAPI existe vía
> `_persist_worker_event()`, pero no la vendo como verificada end-to-end en esta
> ronda. Mi claim defendible es: tengo el adapter y el runtime backend; el loop
> interno del worker no fue reemplazado.

### 3. "¿Por qué no usaste Zep + Graphiti si la vacante habla de temporal KG?"

Respuesta:

> Porque preferí no inflar el proyecto con infra que no iba a poder verificar
> bien antes de la entrevista. Implementé file-backed memory local y mem0
> opcional, y documento explícitamente que temporal KG es roadmap. La diferencia:
> mi memoria actual recupera recuerdos relacionados por keywords/flat recall;
> Zep+Graphiti modelaría entidades, relaciones, cambios temporales y causalidad
> entre runs.

### 4. "¿Mem0 está funcionando realmente?"

Respuesta:

> El backend mem0 está cableado y probado con mocks/config, pero no está probado
> end-to-end con OpenAI key válida. De hecho encontré que mem0 puede llamar a
> OpenAI LLM aunque uses embeddings locales. Por eso el comportamiento local
> defendible es FileBackedMemory, y mem0 queda opcional si hay key válida.

### 5. "¿Por qué SQLite para la shared queue?"

Respuesta:

> Porque el objetivo era demostrar el patrón de single-writer claim local sin
> meter Redis/Celery/Postgres distributed locking. `BEGIN IMMEDIATE` me da una
> transacción de writer único en SQLite: una tarea no puede ser reclamada dos
> veces. Para production multi-host, esto debe migrar a una cola durable o DB
> con locking/retry semantics más fuertes.

### 6. "¿Realmente corriste más de 5 agentes?"

Respuesta:

> Sí. La evidencia verificada fue `python3 scripts/interview_demo.py agents
> --agents 6 --tasks 24`: 24/24 completadas, distribución entre los seis
> agentes, sin duplicate claims. También tengo versión tmux/worktree de 3
> agentes. Lo que no corrí todavía es el success criterion mayor de la spec:
> 10+ agentes y 100+ tareas.

### 7. "¿Qué diferencia hay entre tu demo thread-based y agentes reales?"

Respuesta:

> El demo thread-based prueba la cola y el claim concurrente de forma rápida y
> reproducible. La versión tmux/worktree prueba aislamiento operacional por
> procesos/panes y filesystem. Ninguna de las dos demuestra razonamiento
> independiente profundo de seis LLMs; demuestra orchestration substrate:
> aislamiento, task queue y single-writer locks.

### 8. "¿Cómo evitas premature completion?"

Respuesta:

> No confío solo en que el agente diga "done". En `SessionHarness`, un `done`
> event produce `Evidence`; luego `EvalGate` valida, por ejemplo,
> `require_evidence("answer")` y `require_terminal_status`. Es básico, pero
> muestra la dirección: completion debe depender de artifacts/evidence, no de
> self-reporting.

### 9. "¿Qué parte está más cerca de producción y cuál es prototipo?"

Respuesta:

> Más cerca de producción: FastAPI ownership checks, session lifecycle, limits,
> UI tokens, WorkerLauncher abstraction, metrics/readiness, SQLite/Postgres
> foundation, retention/artifact metadata. Más prototipo: harness memory,
> local evals, SessionHarness persistence, multi-agent scheduler fairness, and
> remote worker orchestration.

### 10. "¿Por qué Spec Kit vs OpenSpec?"

Respuesta:

> Spec Kit es excelente para greenfield porque fuerza estructura desde cero:
> user stories, functional requirements, success criteria, tasks. OpenSpec suele
> ser más cómodo para brownfield porque describe y gobierna cambios en un
> sistema vivo. En este repo hice ambas cosas: specs manuales para evolucionar
> el brownfield, y luego usé el CLI oficial de Spec Kit para documentar
> retroactivamente multi-agent orchestration.

### 11. "¿Qué aprendiste de los bugs que encontraste?"

Respuesta:

> Que los bugs importantes de harness no siempre son bugs de lógica pura. A
> veces son bugs de operación: timing, estado sucio, memoria ruidosa, recoveries
> malas, claims que se ven correctos en tests pero mal en vivo. Eso cambió el
> proyecto: agregué start barrier, dedupe semántico, fallback memory, clear lock
> errors y corrupt checkpoint recovery.

### 12. "¿Cómo compararías este repo con OpenHands/OpenCode/OMA?"

Respuesta:

> Honestamente: no integré OpenHands/OpenCode/OMA en este repo, así que no voy a
> fingir experiencia directa aquí. Conceptualmente, compararía tres capas:
> agent loop, tool API y orchestration model. Este repo se enfoca en el control
> plane: specs, contracts, state, evals, memory, queue and traces. Para una
> evaluación formal de OpenHands/OpenCode/OMA, haría una spec comparativa y
> correría el mismo benchmark harness en cada uno.

## Fallback si algo falla en vivo

Si tmux falla:

```bash
python3 scripts/interview_demo.py loop
cat data/interview_checkpoints/interview-loop.json
```

Narración:

> tmux es el wrapper operacional. El punto del harness persistence está en el
> checkpoint. Si tmux molesta en pantalla, muestro el modo bounded CLI.

Si Docker/FastAPI no está listo:

> No necesito Docker para defender el harness. Docker es runtime backend. La
> entrevista es sobre specs, loop, memory, eval gates, queue, traces y
> persistence.

Si la memory demo no encuentra nada:

```bash
scripts/clean_demo_state.sh
python3 scripts/interview_demo.py memory
```

Narración:

> Prefiero resetear estado y repetir un demo limpio antes que explicar un
> archivo local sucio.

Si preguntan por claims no implementados:

> Lo tengo documentado como roadmap. Prefiero subestimar el claim y que el código
> lo respalde, que sobreprometer en una entrevista de harness engineering.

