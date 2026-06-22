# Project Status Audit Update - 2026-06-21

Este documento es un anexo al audit original:

- [PROJECT_STATUS_AUDIT.md](PROJECT_STATUS_AUDIT.md)

No reemplaza el audit original ni lo edita retroactivamente. Solo documenta
evidencia nueva verificada en vivo después de aquel snapshot.

## 1. Resumen de cambios de estado

| Área | Estado en audit original | Evidencia nueva | Estado actualizado |
| --- | --- | --- | --- |
| tmux persistence | Parcial: checkpoints probados, tmux/reboot no verificado en el sandbox | Sesión `harness-demo` restaurada automáticamente después de reboot real de macOS con tmux-resurrect + tmux-continuum; checkpoint `data/checkpoints/tokyo-run.json` intacto | Cerrado para demo local: reboot real verificado en macOS |
| GitHub Spec Kit CLI oficial | Parcial: Spec Kit-style escrito a mano, sin CLI oficial | `specify-cli` instalado vía `uv tool install`; `specify init --here --force --integration claude` generó `.specify/`; `/speckit.specify` generó `specs/001-multi-agent-orchestration/spec.md` | Cerrado para evidencia de uso real del CLI oficial; constitución generada existe, pero no está customizada como política madura |
| Claude Code Agent Teams | No cumplido: sin evidencia de Claude Code Agent Teams | `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` usado sobre este repo con 3 agentes, cada uno en su git worktree, coordinados por la shared task list nativa de Claude Code | Cerrado como ejercicio aislado de aprendizaje/evidencia; no integrado al runtime del repo |

## 2. tmux persistence: reboot real de macOS

### Qué se verificó

Se verificó fuera del sandbox que la persistencia del harness sobrevive un
reboot real de macOS, no solo detach/re-attach de terminal o SSH.

### Cómo se verificó

Evidencia reportada por el operador:

1. Se instaló tmux-resurrect y tmux-continuum bajo:

```text
~/.tmux/plugins/
```

2. Se inició una sesión tmux llamada:

```text
harness-demo
```

3. Dentro de esa sesión estaba corriendo el runner del harness.

4. Se confirmó un snapshot de tmux-resurrect en:

```text
~/.local/share/tmux/resurrect/
```

5. Se ejecutó un reboot real de la Mac.

6. Al volver, la sesión tmux se restauró automáticamente.

7. El checkpoint del harness seguía intacto:

```text
data/checkpoints/tokyo-run.json
```

### Qué queda limitado

- La evidencia es local a macOS y a la configuración tmux-resurrect/continuum
  del operador.
- No se verificó zellij.
- No se verificó reanudación automática de workers Docker activos del FastAPI
  orchestrator después de reboot. Lo verificado es el runner CLI del harness y
  su checkpoint.
- No cambia el roadmap de `Worker reattachment/reconciliation after
  orchestrator restart` para el backend FastAPI/Docker.

### Claim defendible en entrevista

```text
The standalone harness runner now survives a real macOS reboot via tmux-resurrect
and tmux-continuum, with the AgentLoopState checkpoint intact. This is separate
from FastAPI worker reattachment, which remains roadmap.
```

## 3. GitHub Spec Kit CLI oficial

### Qué se verificó

Se verificó uso real del CLI oficial de GitHub Spec Kit sobre este repositorio.
Esto cierra la brecha anterior donde solo existían specs propias y archivos
Spec Kit-style escritos manualmente.

### Cómo se verificó

Evidencia reportada por el operador y archivos presentes en el repo:

1. Se instaló `specify-cli` vía:

```bash
uv tool install
```

2. Se ejecutó:

```bash
specify init --here --force --integration claude
```

3. Ese comando generó `.specify/`, incluyendo:

```text
.specify/init-options.json
.specify/integration.json
.specify/memory/constitution.md
.specify/workflows/speckit/workflow.yml
```

4. Se ejecutó `/speckit.specify` para generar una spec oficial retroactiva para
la feature multi-agente existente:

```text
specs/001-multi-agent-orchestration/spec.md
specs/001-multi-agent-orchestration/checklists/requirements.md
```

5. La spec generada documenta:

- 3 user stories priorizadas.
- 14 functional requirements.
- criterios de éxito medibles.
- edge cases y assumptions.
- checklist de validación completo.

### Qué queda limitado

- La spec `001-multi-agent-orchestration` es retroactiva: documenta una feature
  que ya existía, no condujo la implementación desde cero.
- La checklist generada valida calidad/completitud de la especificación; no debe
  confundirse con un load test ejecutado para todos los success criteria. En
  particular, los criterios sobre 10+ agentes y 100+ tareas quedan como objetivo
  especificado hasta que se ejecute y documente esa prueba.
- `.specify/memory/constitution.md` existe como archivo generado, pero todavía
  conserva contenido de plantilla; no debe presentarse como una constitución de
  ingeniería madura o ratificada.
- No se usaron OpenSpec, GStack ni Kiro.
- Las specs manuales anteriores siguen existiendo y siguen siendo útiles como
  comparación brownfield/manual vs Spec Kit oficial.

### Claim defendible en entrevista

```text
This repo now contains both manually written brownfield specs and a real
GitHub Spec Kit CLI artifact. I ran the official specify workflow and generated
specs/001-multi-agent-orchestration as a retroactive official Spec Kit spec for
the implemented multi-agent orchestration feature.
```

## 4. Claude Code Agent Teams

### Qué se verificó

Se probó Claude Code Agent Teams directamente sobre este repositorio como
ejercicio aislado de aprendizaje y evidencia.

### Cómo se verificó

Evidencia reportada por el operador:

1. Se habilitó:

```bash
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

2. Se lanzó un equipo de 3 agentes.

3. Cada agente operó en su propio git worktree.

4. La coordinación usó la shared task list nativa de Claude Code.

5. El objetivo fue auditar sin modificar código:

- cobertura de tests.
- consistencia specs-vs-código.
- contradicciones de documentación.

6. Los worktrees de esa prueba fueron eliminados después.

### Qué queda limitado

- Claude Code Agent Teams no está integrado en el runtime del repo.
- No hay wrapper propio en `computer_use_demo/harness/` para controlar Claude
  Code Agent Teams.
- No hay tests automatizados que reproduzcan ese ejercicio.
- Esto no reemplaza la demo local propia de `scripts/spawn_agents.sh` +
  `shared_task_queue.py`; es evidencia separada de experiencia con un harness
  externo.
- No cierra los requisitos relacionados con OpenHands, OpenCode u OMA.

### Claim defendible en entrevista

```text
I also tested Claude Code Agent Teams separately on this repo: three agents in
separate git worktrees, coordinated by Claude Code's native shared task list, to
audit tests and documentation. I did not integrate it into my runtime; it was an
isolated evidence and learning exercise.
```

## 5. Brechas que siguen abiertas

Las siguientes brechas del audit original siguen abiertas y no deben
presentarse como cerradas:

- mem0 real end-to-end con OpenAI key válida no está verificado.
- Letta no está implementado ni probado.
- Zep + Graphiti / temporal knowledge graph sigue siendo roadmap.
- OpenHands no está integrado ni probado.
- OpenCode no está integrado ni probado.
- OMA no está integrado ni probado.
- Orquestación production-grade con scheduler durable/multi-host sigue roadmap.
- La concurrencia de 6 agentes (>5) ya fue verificada en el demo thread-based
  con 24/24 tareas completadas y sin duplicados; lo que sigue pendiente es el
  umbral mayor de 10+ agentes / 100+ tareas y métricas production-grade.
- Load test documentado de 10+ agentes / 100+ tareas sigue pendiente aunque la
  spec oficial lo incluya como success criterion.
- Reattachment de workers Docker/FastAPI después de reboot sigue roadmap.
- Object storage, hosted auth, billing, deployment hardening y compliance siguen
  fuera de alcance.

## 6. Recomendación de wording para la entrevista

Versión corta y honesta:

```text
Since the original audit, I closed three evidence gaps: the standalone harness
runner survived a real macOS reboot through tmux-resurrect/continuum; I ran the
official GitHub Spec Kit CLI and generated a real Spec Kit spec for the existing
multi-agent orchestration feature; and I tested Claude Code Agent Teams as a
separate three-agent worktree-based audit exercise. None of that changes the
remaining roadmap: mem0 real, Zep/Graphiti, Letta, OpenHands/OpenCode/OMA,
remote worker launcher, and production-grade scheduling are still not claimed.
```
