# BOS.PRO: 30-минутный гайд для интервью

Этот сценарий рассчитан на техническое интервью в формате live screen-share на
30 минут. Это не презентация: это terminal-first рассказ, чтобы защищать проект
как Agentic Harness for Computer-Use Agents.

Главный принцип: каждое утверждение должно подтверждаться кодом, документацией,
тестом, исполняемой командой или задокументированной live-проверкой. Не
продавать roadmap как уже реализованную функциональность.

## Preflight перед звонком

Сделать до интервью, не тратить на это время во время звонка:

```bash
cd /Users/duvi18/computer-use-orchestrator
scripts/clean_demo_state.sh
make interview-check
python3 -B -m pytest -q
ruff check computer_use_demo tests scripts
```

Если планируешь показывать настоящий tmux:

```bash
tmux list-sessions
```

Если уже есть старая сессия `harness-demo` или `agent-harness-demo`, заранее
реши: сохранить ее как evidence или остановить вручную. Не импровизировать с
грязным состоянием во время интервью.

## Блок 1 - Открытие и фрейминг (3 мин)

Пока не открывай код. Начни в терминале или README, но сначала проговори рамку.

Дословный текст:

> Я хочу начать с концептуальной рамки, потому что для этой роли главный вопрос
> не в том, что я "написал приложение на FastAPI". Главный вопрос - harness
> engineering.
>
> В одном из подготовительных видео есть очень точная формулировка: [VIDEO 1]
> "Agent equals model plus harness." Если я не обучаю веса модели, значит моя
> зона инженерной работы - harness: что модель видит, когда она это видит, какие
> инструменты ей доступны, какое состояние сохраняется, какая evidence считается
> прогрессом, и когда агент должен продолжать, остановиться или эскалировать.
>
> В видео была аналогия с операционной системой: LLM - это как CPU, мощный, но
> сам по себе инертный. Context window - это RAM. Внешняя память - это disk.
> Tool integrations - это device drivers. А harness - это операционная система,
> которая координирует, что CPU получает и когда.
>
> Там же был тезис про 6x gap: одна и та же модель, один и тот же benchmark, но
> до шести раз разницы из-за orchestration вокруг модели. Поэтому этот проект не
> про "какую модель выбрать", а про то, как управлять работой агента.
>
> То, что я построил здесь, - это Agentic Harness для computer-use agents.
> FastAPI/Docker/noVNC backend существует, но в этой демо-версии я показываю его
> как runtime surface. Главная история - control plane: specs, execution
> contracts, loop state, evidence, eval gates, traces, memory, persistence и
> multi-agent orchestration.

Открой README только после этого:

```bash
sed -n '1,90p' README.md
```

Пока появляется output:

> Здесь видно текущее позиционирование репозитория. Я не представляю это как
> готовый hosted SaaS. Я представляю это как production-style agentic harness
> prototype. Эта честность важна: часть компонентов реализована и проверена
> локально, а часть явно помечена как roadmap.

## Блок 2 - Spec-Driven Dev: как я определяю работу (5 мин)

Открой VS Code или используй терминал:

```bash
ls specs
find specs/001-multi-agent-orchestration -maxdepth 2 -type f | sort
find .specify -maxdepth 3 -type f | sort | head -20
python3 scripts/interview_demo.py map
```

Дословный текст перед `map`:

> Для меня spec-driven dev - это не написать красивые документы после
> реализации. Это оставить breadcrumbs для агента и для команды. В видео Ryan
> Lopopolo есть фраза, через которую я много думал об этом проекте: [VIDEO 2 -
> Lopopolo] "The important thing is not the code but the prompt and the
> guardrails that got you there."
>
> Иначе говоря, если код становится все дешевле производить, reusable asset -
> это спецификация, guardrails, ADRs и описание того, что значит хороший
> результат.

Пока выполняется:

```bash
python3 scripts/interview_demo.py map
```

Говорить во время output:

> Эта команда не делает магию. Это быстрый map для интервью: где лежит evidence
> по каждому блоку harness. Здесь видны specs, loop, memory, evals, runtime
> adapter, parallel orchestration и persistence.
>
> В `specs/` у меня собственные specs, полезные для brownfield, потому что они
> позволяют эволюционировать уже существующий repo без тяжелой церемонии. В
> `specs/spec-kit/` есть вручную написанная версия в стиле Spec Kit. И дополнительно,
> после аудита, я реально прогнал официальный GitHub Spec Kit CLI: `specify init
> --here --force --integration claude`, и сгенерировал
> `specs/001-multi-agent-orchestration/spec.md` через настоящий flow.

Открой официальную spec:

```bash
sed -n '1,140p' specs/001-multi-agent-orchestration/spec.md
```

Дословный текст:

> Здесь важно быть точным. Spec Kit, на мой взгляд, силен для greenfield: он
> заставляет с самого начала описать user stories, functional requirements, edge
> cases и success criteria. Для brownfield что-то вроде OpenSpec или собственных
> specs часто удобнее, потому что можно описывать уже существующее поведение и
> менять его инкрементально. В этом repo есть оба подхода: ручные specs для
> brownfield evolution и официальная retroactive Spec Kit spec для уже
> реализованной multi-agent feature.
>
> Я не буду продавать это как три месяца production-опыта со Spec Kit. То, что я
> могу показать, - это реальное использование CLI, реальные artifacts и ясный
> способ переводить требования в проверяемые задачи.

Если спросят про OpenSpec:

> Моя оценка: OpenSpec выигрывает, когда уже есть живой brownfield-system и
> нужно управлять изменениями инкрементально. Spec Kit выигрывает, когда feature
> новая и нужна сильная структура с нуля. В этом repo пример конкретный:
> multi-agent orchestration уже существовала, поэтому официальная spec
> ретроактивная; я не утверждаю, что она управляла всей первоначальной
> реализацией.

## Блок 3 - Agent loop: goal -> plan -> action -> evidence (6 мин)

Команды:

```bash
python3 scripts/interview_demo.py loop
python3 scripts/interview_demo.py eval
python3 scripts/interview_demo.py session-harness
```

Перед первой командой:

> Это центральная часть. В видео про harness engineering сказано: [VIDEO 1]
> "Execution contracts turn fuzzy LLM completions into bounded agent calls." И
> там перечислены пять элементов: required outputs, budgets, permissions,
> completion conditions и output paths.
>
> В этом repo это смоделировано как `ExecutionContract`, `SessionBudgets`,
> `ToolGrantPolicy`, `EvalGate` и `TraceStore`. Это не chat wrapper. Это
> минимальная state machine: goal, plan, action, observation, evidence,
> evaluation, next_step или escalation.

Запусти:

```bash
python3 scripts/interview_demo.py loop
```

Пока появляется output:

> Обрати внимание на фазы: `goal`, `plan`, `action`, `observation`,
> `evaluation`, `next_step`. Это специально простая модель. Я не притворяюсь,
> что этот CLI реально решает browser task. Он демонстрирует control plane:
> state меняется, checkpoint пишется, run можно восстановить.
>
> Во время подготовки я исправил важный баг: разделил checkpoint и semantic
> memory. Checkpoint можно писать часто ради resiliency, но это не должно
> создавать новую evidence memory на каждый tick. Иначе память превращается в
> шум. Этот баг был найден live и задокументирован.

Если есть время, открой файл:

```bash
sed -n '1,260p' computer_use_demo/harness/runner.py
```

Дословный текст:

> Я также добавил defensive handling: если checkpoint JSON corrupt, demo не
> падает. Файл переименовывается в `.corrupted-<timestamp>`, и runner стартует
> fresh. Для интервью это важно: harness, который не может восстановиться после
> partial state, не выглядит надежным.

Запусти:

```bash
python3 scripts/interview_demo.py eval
```

Пока появляется output:

> Этот eval offline. Он не вызывает Anthropic и Docker. Его задача - проверить
> принцип: не доверять self-reporting агента. Failure mode из видео - "premature
> completion": агент говорит "done" до того, как есть evidence. Здесь gate
> `require_evidence` требует evidence перед success.

Запусти:

```bash
python3 scripts/interview_demo.py session-harness
```

Пока появляется output:

> Эта команда показывает adapter `SessionHarness`: worker-style events
> превращаются в observations, evidence, eval results и trace. Важно: в этой
> команде events синтетические, их генерирует demo script. Реальная интеграция с
> FastAPI orchestrator есть в коде через `_persist_worker_event()`, но в этой
> верификационной сессии я не прогонял end-to-end stream от Docker worker,
> который реально запускает Claude Computer Use. Я говорю это явно, потому что
> хочу, чтобы каждый claim был защищаемым.

Открой architecture doc:

```bash
sed -n '1,180p' docs/HARNESS_ARCHITECTURE.md
```

Дословный текст:

> Этот документ резюмирует flow: Spec -> ExecutionContract -> AgentLoopState ->
> Worker Events -> Observation/Evidence -> EvalGates -> Traces/Memory -> Next
> Step/Escalation.

## Блок 4 - Persistence: runs переживают reboots (4 мин)

Точные команды:

```bash
scripts/run_harness_tmux.sh harness-demo tokyo-run "search Tokyo weather"
```

Внутри tmux:

```text
Ctrl-b d
```

Переподключиться:

```bash
scripts/run_harness_tmux.sh harness-demo tokyo-run "search Tokyo weather"
```

Потом:

```text
Ctrl-C
```

Запустить снова:

```bash
scripts/run_harness_tmux.sh harness-demo tokyo-run "search Tokyo weather"
```

Опционально:

```bash
ls -lt ~/.local/share/tmux/resurrect/ | head
cat data/checkpoints/tokyo-run.json | head -40
```

Перед стартом:

> Persistence для меня означает, что run не зависит от моей терминальной
> сессии. Ryan говорит очень сильную фразу: [VIDEO 2 - Lopopolo] "Every time I
> have to type continue to the agent is a failure of the harness to provide
> enough context." Эта мысль прямо применима здесь. Runner пишет
> `AgentLoopState` на диск, а tmux держит процесс живым даже если я закрою
> терминал или потеряю SSH.

Пока работает tmux:

> Здесь процесс живет внутри tmux. Каждый tick печатает phase и checkpoint.
> Важная часть не tmux сам по себе; tmux - это operational container для run.
> Семантика продолжения находится в checkpoint JSON.

Когда делаешь `Ctrl-b d`:

> Это симулирует закрытие терминала или потерю SSH. Процесс остается живым вне
> моей interactive session.

При переподключении:

> Этот же script idempotent: если сессия уже существует, он делает attach, а не
> создает вторую. Это защищает от accidental duplicate runs.

После `Ctrl-C` и нового запуска:

> Теперь я действительно остановил процесс. При новом запуске я ищу строку
> `resumed checkpoint`. Это доказывает, что продолжение не зависит от памяти
> предыдущего процесса.

Опционально про reboot:

> Дополнительно я проверил это вне sandbox через tmux-resurrect и
> tmux-continuum. Был настоящий reboot macOS, сессия `harness-demo`
> восстановилась, и `data/checkpoints/tokyo-run.json` остался intact. Это
> задокументировано как local evidence, не как гарантия reattachment Docker
> workers.

## Блок 5 - Параллельная оркестрация: >5 агентов, worktrees, single-writer lock (6 мин)

Команды:

```bash
python3 scripts/interview_demo.py agents --agents 6 --tasks 24
TASK_QUEUE_DB=data/task_queue_demo.db TMUX_SESSION_NAME=agent-harness-demo SEED_TASKS=18 scripts/spawn_agents.sh 3
git worktree list
sqlite3 data/task_queue_demo.db "select assigned_agent, count(*) from tasks group by assigned_agent;"
```

Перед первой командой:

> Multi-agent часть связана с еще одной фразой из видео: [VIDEO 1] "Roughly 90%
> of all compute flows through delegated child agents, not the parent. The
> harness is an orchestration pattern, not a reasoning pattern. It decomposes,
> delegates, and verifies."
>
> Поэтому здесь я не пытаюсь заставить шесть агентов свободно договориться между
> собой. Я даю им isolation через git worktree и shared task list с
> single-writer claim.

Запусти:

```bash
python3 scripts/interview_demo.py agents --agents 6 --tasks 24
```

Пока появляется output:

> Это safe thread-based demo: шесть агентов, двадцать четыре задачи,
> распределение между всеми агентами, zero duplicate claims. Это evidence для
> claim `>5 agents`. Это еще не load test на 10+ агентов и 100+ задач из
> official spec; это остается pending success criterion.

Открой queue:

```bash
sed -n '1,180p' computer_use_demo/harness/shared_task_queue.py
```

Дословный текст:

> Техническая точка здесь - `BEGIN IMMEDIATE`. SQLite разрешает одного writer за
> раз. `claim_next_task(agent_id)` открывает immediate transaction, берет
> следующую pending task, помечает ее claimed и делает commit. Это предотвращает
> double assignment. Я также добавил понятное сообщение, если DB locked, потому
> что silent SQLite timeout во время demo выглядит очень плохо.

Запусти tmux/worktree версию:

```bash
TASK_QUEUE_DB=data/task_queue_demo.db TMUX_SESSION_NAME=agent-harness-demo SEED_TASKS=18 scripts/spawn_agents.sh 3
```

Пока появляется output:

> Эта версия создает настоящие worktrees: `worktrees/agent-1`, `agent-2`,
> `agent-3`. Каждый pane запускает `scripts/agent_worker.py` из своего
> worktree. Это предотвращает filesystem write conflicts, когда агент изменяет
> файлы.
>
> Там есть start-signal barrier, чтобы один быстрый агент не начал раньше
> остальных. Это был реальный fix: lock работал, но при instant tasks один агент
> успевал опустошить очередь до старта остальных, и это выглядело как плохая
> concurrency.

После detach или в другом терминале:

```bash
git worktree list
sqlite3 data/task_queue_demo.db "select assigned_agent, count(*) from tasks group by assigned_agent;"
```

Дословный текст:

> Это демонстрирует worktree isolation и shared task queue. Также я отдельно
> пробовал Claude Code Agent Teams с `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`:
> три агента в отдельных worktrees, shared task list нативно от Claude Code. Это
> не интегрировано в runtime этого repo; это было отдельное learning/evidence
> exercise, чтобы сравнить тот же паттерн в другом harness.

## Блок 6 - Memory layer (4 мин)

Команда:

```bash
python3 scripts/interview_demo.py memory
```

Перед запуском:

> Memory здесь намеренно узкая. В видео есть фраза [VIDEO 1] "file-backed state
> externalizes memory to path-addressable files surviving truncation, restarts
> and delegation." Мое local demo по умолчанию использует file-backed memory.
> mem0 подключен как optional backend, но он активируется только с валидным
> OpenAI key, и я не продаю его как проверенный end-to-end.

Пока выполняется:

> Первый run сохраняет evidence для Tokyo. Второй run спрашивает про Osaka и
> должен напечатать `memory recall query='search Osaka weather' -> 1 matches
> found`. Это важно: агент не начинает каждую сессию полностью с нуля.
>
> Но здесь тоже нужна дисциплина: я не сохраняю каждый checkpoint tick как
> memory. Я сохраняю только semantic evidence с dedupe. Это был реальный fix:
> раньше `harness_memory.json` наполнялся десятками почти одинаковых записей.

Объяснение flat-vector vs temporal graph:

> Это flat recall: keyword/local memory. Optional mem0 был бы ближе к
> flat-vector semantic recall. Temporal knowledge graph типа Zep + Graphiti -
> это другая категория: entities, relations, temporal events и state changes.
> Например, не просто "Tokyo weather", а "goal A produced evidence B, then
> observation C contradicted it, then run D updated it." Это остается roadmap в
> этом repo.

## Блок 7 - Bugs, найденные live: главный meta-point (4 мин)

Не обязательно открывать код. Говори как engineer.

Дословный текст:

> Для меня самая важная часть подготовки была не в том, чтобы написать больше
> кода. Самое важное было прогнать систему live и найти реальные failure modes.
> Ryan описывает этот процесс как [VIDEO 2 - Lopopolo] observe, refine, and make
> additional choices around non-functional requirements. А первое видео говорит
> похожую мысль: harness не только растет, он еще и упрощается; mature harness
> work is pruning structure down.
>
> Я нашел несколько реальных bugs.
>
> Первый: в multi-agent claiming казалось, что нет настоящей concurrency. Причина
> была не в lock: `BEGIN IMMEDIATE` корректно предотвращал double claim. Причина
> была в timing: мало задач и instant work, поэтому один быстрый агент
> опустошал очередь. Fix: больше seed tasks, реалистичный sleep и start barrier,
> чтобы все panes стартовали вместе. Это показывает, что я смотрел не только на
> tests, но и на operational behavior.
>
> Второй: mem0. Я настроил HuggingFace embeddings, но mem0 все равно пытался
> использовать OpenAI LLM в `add()`. Плюс если `OPENAI_API_KEY` содержал
> Anthropic key `sk-ant-...`, ошибка была misleading. Fix: если нет валидного
> OpenAI key, я не инициализирую real mem0; использую FileBackedMemory. Если
> mem0 падает runtime, деградирую в fallback.
>
> Третий: evidence spam. Runner часто писал checkpoints, что правильно для
> resiliency, но одновременно записывал evidence memory на каждый tick. Это
> превращало memory в noise. Fix: разделить checkpoint и semantic memory, и
> дедуплицировать по evidence signature.
>
> Четвертый: dedupe против checkpoint. Если checkpoint был, но memory file
> отсутствовал, казалось, что semantic state уже есть, но recall был пустой. Я
> добавил test на восстановление memory, когда checkpoint есть, а memory file
> отсутствует.
>
> И наконец, после code quality audit я добавил recovery для corrupt JSON:
> corrupt checkpoint переезжает в `.corrupted-<timestamp>`, а corrupt memory
> считается empty с warning. Это маленькая вещь, но в live demo она не дает
> грязному local file сломать всю историю.

Что это говорит обо мне:

> Я хочу, чтобы было видно: я не пытаюсь показать идеальное demo. Я строю
> observable harness, потом ломаю его live, документирую ограничения и уменьшаю
> failure modes, которые блокируют автономное выполнение.

## Блок 8 - Честное закрытие и roadmap (2 мин)

Дословный текст:

> В конце: [VIDEO 1] "The reusable asset isn't the model, it's the harness."
> Это идея этого repo. Я не соревнуюсь с frontier models; я строю структуру
> вокруг модели: specs, contracts, budgets, memory, task queues, eval gates,
> traces, persistence и runtime boundaries.
>
> Что есть и проверено: local loop, checkpoints, tmux persistence с настоящим
> reboot на моей Mac, file-backed memory, eval gates, SessionHarness adapter с
> синтетическими events, 6 thread-based agents with 24 tasks без duplicates, 3
> agents в tmux/worktree, официальный Spec Kit CLI retroactive spec, и
> FastAPI/Docker runtime backend.
>
> Что я не буду продавать как готовое: mem0 real end-to-end, Letta,
> Zep+Graphiti, OpenHands, OpenCode, OMA, 10+ agents with 100+ tasks, object
> storage, hosted auth, remote worker launcher и reattachment Docker workers
> после reboot.
>
> И это совпадает с вакансией: вы строите Business Operating System, а не
> поддерживаете CRUD. Мой вклад - думать о harness как о дисциплине: какую
> структуру добавить, какую убрать, и как сделать так, чтобы агент двигался
> вперед без того, чтобы человек писал "continue".

## Сложные вопросы

### 1. "Что такое harness, твоими словами?"

Ответ:

> Harness - это control plane вокруг модели. Если модель - CPU, harness решает,
> какой context идет в RAM, какая внешняя memory работает как disk, какие tools
> являются drivers, какие budgets ограничивают выполнение, какая evidence
> позволяет завершить задачу и какие eval gates запрещают self-reporting. В этом
> repo это смоделировано через `ExecutionContract`, `AgentLoopState`,
> `EvalGate`, `TraceStore`, `HarnessMemory` и `SessionHarness`.

### 2. "Твой loop реально управляет Claude Computer Use?"

Ответ:

> Частично. Claude Computer Use worker продолжает свой обычный execution path.
> `SessionHarness` adapter потребляет worker-style events и превращает их в
> observations/evidence/evals/traces. В demo `session-harness` эти events
> synthetic; реальная интеграция с FastAPI есть через `_persist_worker_event()`,
> но я не продаю ее как end-to-end verified в этой проверке. Защищаемый claim:
> у меня есть adapter и runtime backend; внутренний loop worker не заменен.

### 3. "Почему не Zep + Graphiti, если в вакансии temporal KG?"

Ответ:

> Я не хотел добавлять infra, которую не успею честно проверить перед интервью.
> Я реализовал local file-backed memory и optional mem0, и явно документирую
> temporal KG как roadmap. Разница такая: моя текущая memory достает related
> memories через keywords/flat recall; Zep+Graphiti моделировал бы entities,
> relations, temporal changes и causality между runs.

### 4. "mem0 реально работает?"

Ответ:

> mem0 backend подключен и покрыт mock/config tests, но не проверен end-to-end с
> валидным OpenAI key. Более того, я обнаружил, что mem0 может вызывать OpenAI
> LLM даже при local embeddings. Поэтому defendable local behavior -
> FileBackedMemory, а mem0 остается optional при валидной key.

### 5. "Почему SQLite для shared queue?"

Ответ:

> Цель была показать local single-writer claim pattern без Redis/Celery/Postgres
> distributed locking. `BEGIN IMMEDIATE` дает транзакцию с одним writer в SQLite:
> задача не может быть claimed дважды. Для production multi-host это нужно
> переносить в durable queue или DB с более сильными locking/retry semantics.

### 6. "Ты реально запускал больше 5 агентов?"

Ответ:

> Да. Проверенная команда: `python3 scripts/interview_demo.py agents --agents 6
> --tasks 24`: 24/24 completed, распределение между шестью агентами, без
> duplicate claims. Также есть tmux/worktree версия на 3 агента. Чего я еще не
> запускал - больший success criterion из spec: 10+ agents и 100+ tasks.

### 7. "Чем thread-based demo отличается от настоящих агентов?"

Ответ:

> Thread-based demo быстро и воспроизводимо проверяет queue и concurrent claim.
> Tmux/worktree версия проверяет operational isolation: processes/panes и
> filesystem. Ни одна из них не доказывает глубокое независимое reasoning шести
> LLMs; она доказывает orchestration substrate: isolation, task queue и
> single-writer locks.

### 8. "Как ты предотвращаешь premature completion?"

Ответ:

> Я не доверяю только тому, что агент сказал "done". В `SessionHarness`, `done`
> event производит `Evidence`; потом `EvalGate` проверяет, например,
> `require_evidence("answer")` и `require_terminal_status`. Это базовый вариант,
> но направление правильное: completion зависит от artifacts/evidence, а не от
> self-reporting.

### 9. "Какая часть ближе к production, а какая prototype?"

Ответ:

> Ближе к production: FastAPI ownership checks, session lifecycle, limits, UI
> tokens, WorkerLauncher abstraction, metrics/readiness, SQLite/Postgres
> foundation, retention/artifact metadata. Более prototype: harness memory,
> local evals, SessionHarness persistence, multi-agent scheduler fairness и
> remote worker orchestration.

### 10. "Почему Spec Kit vs OpenSpec?"

Ответ:

> Spec Kit отлично подходит для greenfield, потому что заставляет с нуля
> описать user stories, functional requirements, success criteria и tasks.
> OpenSpec обычно удобнее для brownfield, потому что описывает и управляет
> изменениями в живой системе. В этом repo я сделал оба: manual specs для
> brownfield evolution, а затем использовал официальный Spec Kit CLI, чтобы
> retroactively задокументировать multi-agent orchestration.

### 11. "Что ты понял из bugs, которые нашел?"

Ответ:

> Важные harness bugs не всегда являются чисто logic bugs. Часто это operational
> bugs: timing, dirty state, noisy memory, плохие recoveries, claims, которые
> корректны в tests, но плохо выглядят live. Это изменило проект: я добавил
> start barrier, semantic dedupe, fallback memory, clear lock errors и corrupt
> checkpoint recovery.

### 12. "Как ты сравнишь этот repo с OpenHands/OpenCode/OMA?"

Ответ:

> Честно: я не интегрировал OpenHands/OpenCode/OMA в этот repo, поэтому не буду
> притворяться, что здесь есть direct experience. Концептуально я сравнивал бы
> три слоя: agent loop, tool API и orchestration model. Этот repo фокусируется
> на control plane: specs, contracts, state, evals, memory, queue and traces. Для
> формальной оценки OpenHands/OpenCode/OMA я бы сделал comparison spec и прогнал
> один и тот же benchmark harness на каждом.

## Fallback, если что-то ломается live

Если tmux ломается:

```bash
python3 scripts/interview_demo.py loop
cat data/interview_checkpoints/interview-loop.json
```

Говорить:

> tmux - это operational wrapper. Смысл harness persistence находится в
> checkpoint. Если tmux шумит на экране, я показываю bounded CLI mode.

Если Docker/FastAPI не готов:

> Мне не нужен Docker, чтобы защитить harness. Docker - это runtime backend.
> Интервью про specs, loop, memory, eval gates, queue, traces и persistence.

Если memory demo ничего не находит:

```bash
scripts/clean_demo_state.sh
python3 scripts/interview_demo.py memory
```

Говорить:

> Я лучше reset-ну состояние и повторю clean demo, чем буду объяснять грязный
> local file.

Если спрашивают про не реализованные claims:

> Это задокументировано как roadmap. Я предпочитаю занизить claim и подтвердить
> его кодом, чем overpromise на интервью по harness engineering.

