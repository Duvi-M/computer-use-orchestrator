# DoLoRA Interview Brief para Skoltech

Fecha de preparación: 2026-06-23.

Rol del documento: brief técnico para una segunda entrevista académica de 10 minutos. El objetivo es separar con claridad tres cosas:

1. Lo que sí existe y se puede defender en el repositorio actual.
2. Lo que no fue encontrado en el repositorio.
3. El marco conceptual de LoRA/DoLoRA que puede usarse para explicar la idea si el algoritmo existe fuera de este workspace.

Advertencia importante: en el repositorio actual `computer-use-orchestrator` no se encontró implementación, configuración experimental, dataset, métrica, notebook, script de entrenamiento ni resultados asociados a DoLoRA, LoRA, AdaLoRA o fine-tuning de Transformers. Las búsquedas por `DoLoRA`, `dolora`, `LoRA`, `AdaLoRA`, `rank`, `fine-tun`, `GLUE`, `SST`, `MRPC`, `QNLI`, `MNLI`, `CoLA`, `RTE`, `peft`, `adapter`, `bert`, `roberta` y términos relacionados no arrojaron evidencia de un proyecto DoLoRA. Por tanto, las secciones sobre DoLoRA se presentan como explicación conceptual y las secciones sobre evidencia experimental indican explícitamente "no encontrado en el repositorio" cuando corresponde.

## 1. Resumen ejecutivo

DoLoRA, según el objetivo declarado para la entrevista, debe presentarse como un método de fine-tuning eficiente basado en adaptadores de bajo rango para modelos Transformer. La idea general es evitar actualizar todos los pesos del modelo base y entrenar únicamente una parametrización compacta que modifica ciertas matrices lineales, típicamente en atención y/o capas feed-forward. El problema que intenta resolver es reducir memoria, coste computacional y almacenamiento de checkpoints durante la adaptación a nuevas tareas. Esto es relevante porque el fine-tuning completo de Transformers grandes es caro, difícil de reproducir en hardware limitado y genera una copia completa del modelo por tarea. Frente a LoRA estándar, DoLoRA debería justificar una mejora en asignación dinámica, selección o descomposición de rangos/parámetros. En este repositorio, sin embargo, no se encontró código que implemente DoLoRA ni resultados que lo validen.

Problema que resuelve:

- Fine-tuning más barato que actualizar todos los parámetros.
- Adaptación por tarea con menos memoria entrenable.
- Checkpoints pequeños y potencialmente intercambiables.
- Mejor uso del presupuesto de rango si el método adapta rangos de forma dinámica.

Relevancia para Transformers:

- Las capas lineales de atención y MLP concentran gran parte de la capacidad adaptativa.
- La parametrización de bajo rango permite modificar el comportamiento del modelo sin tocar el backbone.
- Facilita experimentos académicos con modelos grandes en GPUs limitadas.

## 2. Contexto del problema

### Limitaciones del fine-tuning completo

El fine-tuning completo actualiza todos los parámetros del modelo preentrenado. Esto tiene varias desventajas:

- Alto consumo de memoria porque se almacenan gradientes, estados del optimizador y pesos actualizados para todos los parámetros.
- Coste computacional elevado, especialmente con modelos Transformer grandes.
- Un checkpoint completo por tarea, lo que escala mal cuando se adaptan muchos modelos o dominios.
- Mayor riesgo de overfitting o catastrophic forgetting cuando el dataset específico es pequeño.
- Dificultad para comparar variantes si cada experimento requiere entrenar y almacenar una copia completa del modelo.

### Limitaciones de LoRA estándar

LoRA congela el peso base `W_0` y aprende una actualización de bajo rango `Delta W = B A`. Esto reduce mucho el número de parámetros entrenables, pero introduce limitaciones:

- El rango `r` suele ser fijo y elegido antes del entrenamiento.
- Un mismo rango puede ser excesivo para algunas capas e insuficiente para otras.
- La asignación de capacidad no necesariamente sigue la importancia real de cada módulo.
- Si el rango es demasiado bajo, puede limitar la adaptación; si es demasiado alto, pierde eficiencia.
- LoRA estándar no siempre incorpora una señal explícita para redistribuir capacidad durante el entrenamiento.

### Motivación de DoLoRA

La motivación natural para DoLoRA es mejorar la eficiencia de LoRA mediante una adaptación más inteligente del rango o de los parámetros de bajo rango. En una defensa académica, la hipótesis debe formularse así:

> No todas las capas ni todas las direcciones de actualización necesitan la misma capacidad. Si podemos asignar el presupuesto de bajo rango donde aporta más señal, podemos acercarnos al rendimiento del fine-tuning completo con menos parámetros entrenables.

No encontrado en el repositorio:

- Definición formal propia de DoLoRA.
- Implementación del algoritmo.
- Motivación escrita en README, docs o specs.
- Comparación experimental contra LoRA/AdaLoRA.

## 3. Idea principal del algoritmo

### Idea simple

LoRA estándar aprende una actualización de bajo rango para una matriz lineal:

```text
y = W_0 x + Delta W x
Delta W = B A
```

DoLoRA, si se entiende como una variante dinámica/optimizada de LoRA, debería modificar esta idea de una de estas formas:

- Adaptar qué matrices reciben adaptadores.
- Adaptar el rango `r` por capa.
- Reasignar presupuesto de parámetros durante el entrenamiento.
- Podar o activar componentes de bajo rango según una métrica de importancia.
- Separar dirección, magnitud o escala de la actualización para estabilizar el aprendizaje.

### Qué adapta

Conceptualmente, DoLoRA adaptaría las actualizaciones de bajo rango dentro de módulos Transformer, por ejemplo:

- Proyecciones de atención: `W_q`, `W_k`, `W_v`, `W_o`.
- Capas feed-forward: `W_up`, `W_down`, `W_gate`, según arquitectura.
- Opcionalmente embeddings o classification heads, si el proyecto lo permite.

No encontrado en el repositorio:

- Lista de módulos objetivo.
- Nombre de clases o funciones DoLoRA.
- Configuración de capas adaptadas.

### Cómo decide o modifica rangos/parámetros

Para que DoLoRA se diferencie de LoRA estándar, debe existir una regla de decisión. Ejemplos conceptuales defendibles, si se corresponden con tu implementación externa:

- Importancia por magnitud de parámetros de bajo rango.
- Importancia por norma de gradiente.
- Importancia por contribución al cambio `||Delta W||`.
- Presupuesto global de rangos redistribuido entre capas.
- Máscaras entrenables o programadas que activan/desactivan componentes.

No encontrado en el repositorio:

- Métrica de importancia concreta.
- Algoritmo de pruning, growing o redistribución.
- Scheduler de rango.

### Diferencias con LoRA, AdaLoRA y métodos relacionados

Comparación conceptual:

| Método | Idea | Diferencia principal |
| --- | --- | --- |
| Full fine-tuning | Actualiza todos los pesos | Máxima capacidad, máximo coste |
| LoRA | Aprende `Delta W = B A` con rango fijo | Eficiente, pero el rango se elige manualmente |
| AdaLoRA | Ajusta presupuesto/rangos mediante importancia | Redistribuye capacidad durante entrenamiento |
| DoRA | Descompone peso en magnitud y dirección | Mejora adaptación separando escala y dirección |
| DoLoRA | No encontrado en repo; presumiblemente variante dinámica/optimizada de LoRA | Debe demostrar qué señal usa y por qué mejora |

Advertencia: si "DoLoRA" en tu investigación significa algo específico distinto de "Dynamic/Optimized LoRA", conviene reemplazar esta sección con la definición exacta del paper/código.

## 4. Flujo paso a paso del algoritmo

El siguiente flujo describe cómo debería presentarse DoLoRA conceptualmente. Los pasos concretos no fueron encontrados implementados en el repositorio.

### 1. Entrada

Entrada esperada:

- Modelo Transformer preentrenado `f_theta`.
- Dataset supervisado o instruccional `D = {(x_i, y_i)}`.
- Conjunto de módulos objetivo `M`, por ejemplo proyecciones de atención.
- Presupuesto de parámetros o rango total.
- Hiperparámetros de entrenamiento: learning rate, batch size, epochs, warmup, weight decay.

No encontrado en el repositorio:

- Dataset real de DoLoRA.
- Modelo base usado.
- Config YAML/JSON de entrenamiento.

### 2. Inicialización

LoRA inicializa una actualización de bajo rango:

```text
Delta W_l = B_l A_l
A_l in R^{r_l x d_in}
B_l in R^{d_out x r_l}
```

Usualmente `A_l` se inicializa aleatoriamente y `B_l` en cero, o viceversa, para que al inicio `Delta W_l` no perturbe el modelo base.

En DoLoRA, la inicialización podría incluir:

- Rango inicial por capa `r_l`.
- Presupuesto total `R_total`.
- Máscaras o scores de importancia por componente.
- Escalas `alpha_l / r_l`.

No encontrado en el repositorio:

- Estrategia de inicialización real.

### 3. Cálculo de métricas/señales

Una variante dinámica calcula señales para decidir dónde asignar capacidad. Posibles señales:

- Norma de gradiente: componentes con gradientes mayores pueden ser más útiles.
- Norma de actualización: componentes con mayor `||B_l A_l||` pueden aportar más.
- Sensibilidad de pérdida: cuánto cambia la pérdida al retirar un componente.
- Importancia acumulada: media móvil de scores durante entrenamiento.

No encontrado en el repositorio:

- Cálculo de scores de importancia.
- Logging de métricas DoLoRA.

### 4. Adaptación/decisión

El algoritmo podría aplicar decisiones periódicas:

- Aumentar rango en capas importantes.
- Reducir o podar componentes poco usados.
- Mantener un presupuesto global constante.
- Reescalar adaptadores para conservar estabilidad.

No encontrado en el repositorio:

- Frecuencia de adaptación.
- Regla de redistribución.
- Restricciones de presupuesto.

### 5. Entrenamiento

Durante entrenamiento:

- El modelo base `W_0` permanece congelado.
- Solo se entrenan parámetros de adaptadores.
- Se optimiza la pérdida de la tarea.
- Si DoLoRA es dinámico, se recalculan scores y se ajusta la estructura en ciertos pasos.

No encontrado en el repositorio:

- Script de entrenamiento.
- Optimizer real.
- Loop de entrenamiento ML.

### 6. Salida final

Salida esperada:

- Adaptadores entrenados DoLoRA.
- Configuración final de rangos por capa.
- Métricas de validación/test.
- Checkpoint compacto.

No encontrado en el repositorio:

- Checkpoints DoLoRA.
- Tabla final de rangos.
- Métricas de accuracy/F1/perplexity.

## 5. Fórmulas importantes

Esta sección distingue entre fórmulas estándar de LoRA/PEFT y fórmulas encontradas en el proyecto. No se encontraron fórmulas DoLoRA específicas en el repositorio.

### 5.1 Transformación lineal base

```text
y = W_0 x
```

Significado:

- `x`: activación de entrada.
- `W_0`: matriz de pesos preentrenada.
- `y`: salida de la capa lineal.

Importancia:

- Es la operación que LoRA/DoLoRA modifica sin actualizar directamente `W_0`.

### 5.2 Actualización LoRA

```text
y = W_0 x + Delta W x
Delta W = B A
```

Variables:

- `W_0 in R^{d_out x d_in}`: peso congelado.
- `A in R^{r x d_in}`: proyección de entrada a rango bajo.
- `B in R^{d_out x r}`: proyección de rango bajo a salida.
- `r`: rango del adaptador.
- `Delta W`: actualización aprendida.

Importancia:

- Reduce parámetros entrenables de `d_out * d_in` a `r * (d_in + d_out)`.

### 5.3 Escalado LoRA

```text
y = W_0 x + (alpha / r) B A x
```

Variables:

- `alpha`: factor de escala.
- `r`: rango.

Importancia:

- Controla la magnitud de la actualización y estabiliza el entrenamiento.

### 5.4 Número de parámetros entrenables

```text
P_lora = r (d_in + d_out)
P_full = d_in d_out
```

Variables:

- `P_lora`: parámetros entrenables del adaptador para una capa.
- `P_full`: parámetros si se actualizara la matriz completa.

Importancia:

- Muestra por qué LoRA y variantes son eficientes.

### 5.5 Presupuesto total de rangos por capas

```text
P_total = sum_l r_l (d_in,l + d_out,l)
```

Variables:

- `l`: índice de capa o módulo.
- `r_l`: rango asignado a la capa `l`.

Importancia:

- Si DoLoRA adapta rangos, esta fórmula permite expresar el presupuesto total de parámetros entrenables.

Estado en repo:

- No encontrado en el repositorio como fórmula implementada.

### 5.6 Score conceptual de importancia

```text
I_{l,k} = ||A_{l,k}||_2 ||B_{l,k}||_2
```

Variables:

- `I_{l,k}`: importancia conceptual del componente de rango `k` en la capa `l`.
- `A_{l,k}`: fila/componente correspondiente en `A`.
- `B_{l,k}`: columna/componente correspondiente en `B`.

Importancia:

- Podría usarse para podar o reasignar componentes de bajo rango.

Estado en repo:

- No encontrado en el repositorio.
- Incluir solo si coincide con la implementación real externa.

### 5.7 Objetivo de entrenamiento

```text
min_phi (1 / |D|) sum_{(x,y) in D} L(f_{theta_0, phi}(x), y)
```

Variables:

- `theta_0`: pesos congelados del modelo base.
- `phi`: parámetros entrenables del adaptador.
- `D`: dataset de entrenamiento.
- `L`: función de pérdida, por ejemplo cross-entropy.

Importancia:

- Formaliza PEFT: se optimiza `phi`, no todo `theta`.

Estado en repo:

- No encontrado como entrenamiento DoLoRA.

## 6. Arquitectura del repositorio

El repositorio actual no es un repositorio ML/DoLoRA. Es un prototipo de harness para agentes de computer-use.

### Carpetas principales

| Ruta | Rol |
| --- | --- |
| `computer_use_demo/` | Código principal del sistema de computer-use y harness |
| `computer_use_demo/api/` | Orquestador FastAPI, sesiones, workers, config y persistencia |
| `computer_use_demo/harness/` | Primitivas de agentic harness: loop, contracts, budgets, eval gates, memory, traces, task queue |
| `computer_use_demo/tools/` | Herramientas de computer use: bash, edición, grupos, ejecución |
| `scripts/` | Demos y utilidades, incluyendo `interview_demo.py` y agentes paralelos |
| `docs/` | Documentación de arquitectura, auditoría, entrevista, seguridad y operaciones |
| `specs/` | Especificaciones manuales y estilo GitHub Spec Kit |
| `evals/` | Evaluación offline del harness |
| `tests/` | Tests unitarios e integración local |
| `web/` | Frontend HTML/JS/CSS del orquestador |
| `migrations/` | Migraciones Alembic para persistencia |
| `image/` | Archivos de imagen/worker/noVNC |

### Archivos clave

| Archivo | Qué hace |
| --- | --- |
| `README.md` | Describe el proyecto como agentic harness para sesiones Claude Computer Use |
| `docs/ARCHITECTURE.md` | Arquitectura del orquestador FastAPI, Docker workers y harness |
| `docs/PROJECT_STATUS_AUDIT.md` | Auditoría conservadora del estado verificable del proyecto |
| `docs/PROJECT_STATUS_AUDIT_UPDATE_2026-06-21.md` | Actualización de evidencia: tmux persistence, Spec Kit CLI y Claude Code Agent Teams |
| `scripts/interview_demo.py` | Script central de demo para entrevista del harness |
| `computer_use_demo/harness/loop.py` | Modelo de loop goal/plan/action/observation/evaluation |
| `computer_use_demo/harness/runner.py` | Runner con checkpoints |
| `computer_use_demo/harness/session_harness.py` | Adaptador de eventos worker-style hacia observaciones/evidencia/eval gates |
| `computer_use_demo/harness/eval_gates.py` | Eval gates mínimos |
| `computer_use_demo/harness/memory.py` | Memoria file-backed con backend mem0 opcional |
| `computer_use_demo/harness/shared_task_queue.py` | Cola SQLite con `BEGIN IMMEDIATE` para claims single-writer |
| `evals/run_eval.py` | Eval offline segura para CI/entrevista |

### Dónde está implementado DoLoRA

No encontrado en el repositorio.

No se encontraron:

- Directorios típicos de ML como `models/`, `training/`, `experiments/`, `configs/`, `notebooks/` o `results/` para DoLoRA.
- Dependencias como `torch`, `transformers`, `datasets`, `peft` o `accelerate` en `pyproject.toml`/requirements del proyecto principal que sugieran fine-tuning DoLoRA.
- Clases, funciones o configs llamadas `DoLoRA`, `dolora`, `lora`, `adalora`.

## 7. Pipeline experimental

### Datasets usados

No encontrado en el repositorio para DoLoRA.

No hay evidencia de datasets GLUE, SuperGLUE, instruction tuning, clasificación, QA, summarization o language modeling asociados al algoritmo.

### Modelos usados

No encontrado en el repositorio para DoLoRA.

No hay evidencia de BERT, RoBERTa, DeBERTa, T5, LLaMA, Mistral u otro Transformer usado para fine-tuning.

### Métricas

No encontrado en el repositorio para DoLoRA.

Métricas esperables para un proyecto DoLoRA, pero no verificadas aquí:

- Accuracy.
- F1.
- Matthews correlation para CoLA.
- Exact Match/F1 para QA.
- Perplexity para language modeling.
- Parámetros entrenables.
- Memoria GPU.
- Tiempo de entrenamiento.
- Tamaño de checkpoint.

### Configuración de experimentos

No encontrado en el repositorio para DoLoRA.

Faltan:

- Seeds.
- Learning rate.
- Batch size.
- Epochs.
- Warmup.
- Weight decay.
- Rango inicial/final.
- Target modules.
- Hardware usado.

### Qué se compara contra qué

No encontrado en el repositorio.

Comparaciones que deberían existir para una defensa fuerte:

| Comparación | Por qué importa |
| --- | --- |
| Full fine-tuning vs LoRA vs DoLoRA | Mide eficiencia vs rendimiento |
| LoRA fijo con varios rangos vs DoLoRA | Aísla el valor de la adaptación dinámica |
| DoLoRA vs AdaLoRA | Compara contra baseline dinámico directo |
| Ablation sin adaptación dinámica | Demuestra que la regla de decisión aporta |
| Distintos presupuestos de parámetros | Muestra robustez bajo restricciones |

## 8. Resultados principales

No encontrado en el repositorio para DoLoRA.

No se encontraron:

- Tablas de resultados.
- Logs de entrenamiento.
- CSV/JSON de métricas.
- Figuras de curvas de pérdida.
- Comparaciones LoRA/DoLoRA.
- Checkpoints o reportes experimentales.

Interpretación honesta:

- Con este repositorio solo no se puede afirmar que DoLoRA mejora accuracy, eficiencia, memoria o tiempo.
- Tampoco se puede afirmar que DoLoRA supera LoRA, AdaLoRA o fine-tuning completo.
- Para la entrevista, cualquier claim cuantitativo debe venir de otro repo, paper, notebook o resultados externos que no están en este workspace.

Tabla de resultados defendible desde este repo:

| Área | Resultado encontrado | Interpretación |
| --- | --- | --- |
| DoLoRA accuracy/F1 | No encontrado | No hay evidencia experimental |
| DoLoRA parámetros entrenables | No encontrado | No hay implementación ni config |
| DoLoRA memoria/tiempo | No encontrado | No hay logs |
| Repositorio actual | Harness multi-agente implementado parcialmente | Tema distinto a DoLoRA |

## 9. Qué está terminado actualmente

### Terminado en el repositorio actual

Según `README.md`, `docs/PROJECT_STATUS_AUDIT.md` y `docs/PROJECT_STATUS_AUDIT_UPDATE_2026-06-21.md`, el repositorio sí contiene:

- Prototipo de agentic harness para computer-use agents.
- Orquestador FastAPI con sesiones, mensajes, eventos, health/readiness, métricas, admin y retention.
- Worker runtime local vía Docker como backend.
- Primitivas de harness: goals, plans, actions, observations, evidence, eval gates, execution contracts, budgets, traces y triggers.
- Memoria local file-backed; mem0 opcional pero no verificado end-to-end con key real.
- Evals offline seguras para CI/entrevista.
- Demo de agentes paralelos con SQLite shared task queue.
- Worktree isolation para demo local.
- Checkpoints y evidencia de tmux persistence del runner standalone después de reboot real de macOS, según el audit update.
- Uso verificado de GitHub Spec Kit CLI de forma retroactiva para una spec del proyecto multi-agente.

### Terminado para DoLoRA

No encontrado en el repositorio.

No hay evidencia de que estén terminados:

- Implementación DoLoRA.
- Entrenamiento.
- Evaluación.
- Comparación contra baselines.
- Documentación algorítmica.
- Scripts reproducibles.

## 10. Limitaciones actuales

### Limitaciones técnicas del repositorio actual

Estas limitaciones pertenecen al proyecto `computer-use-orchestrator`, no a DoLoRA:

- No es SaaS hosted production-ready.
- No hay hosted auth, billing, object storage ni compliance controls.
- Worker reattachment/reconciliation después de restart del orquestador sigue en roadmap.
- mem0 real end-to-end no fue verificado con key válida.
- Zep/Graphiti, Letta, OpenHands, OpenCode y OMA no están implementados.
- La cola SQLite single-writer es válida para demo local, no para multi-host distribuido.
- Los eval gates actuales son mínimos; no hay verifier semántico fuerte.

### Limitaciones experimentales de DoLoRA

No encontrado en el repositorio:

- Datasets.
- Modelos.
- Baselines.
- Seeds.
- Runs repetidos.
- Métricas.
- Curvas.
- Ablations.
- Hardware.
- Código de entrenamiento.

### Qué falta mejorar para una defensa DoLoRA

Para que el trabajo sea defendible como investigación ML, faltaría añadir o enlazar:

- Código fuente del algoritmo.
- Configs reproducibles.
- Resultados cuantitativos.
- Comparación contra LoRA y al menos un método dinámico como AdaLoRA.
- Ablation de la regla de decisión de DoLoRA.
- Tabla de parámetros entrenables y coste.
- Análisis por capa/rango final.
- Seeds múltiples o al menos discusión de varianza.
- Limitaciones y casos donde no mejora.

## 11. Cómo explicarlo en una entrevista de Skoltech

Esta narrativa dura aproximadamente 10 minutos. Debe adaptarse según si vas a presentar DoLoRA externo o el repositorio actual. Si el comité revisa este workspace, hay que ser transparente desde el inicio.

### Minuto 0-1: introducción

"Mi objetivo fue estudiar fine-tuning eficiente de Transformers. El punto de partida es que el fine-tuning completo funciona bien, pero es caro: actualiza todos los pesos, requiere mucha memoria y produce un checkpoint completo por tarea. En modelos modernos, eso limita la experimentación y la transferencia a múltiples dominios."

### Minuto 1-2: problema

"Los métodos PEFT, especialmente LoRA, atacan este problema congelando el modelo base y aprendiendo una actualización de bajo rango en matrices lineales. Esto reduce mucho los parámetros entrenables. Pero LoRA estándar normalmente usa un rango fijo elegido manualmente. Esa elección no siempre es óptima: algunas capas necesitan más capacidad y otras menos."

### Minuto 2-4: solución

"DoLoRA se plantea como una mejora sobre LoRA: mantener la eficiencia de bajo rango, pero usar el presupuesto de parámetros de forma más inteligente. La hipótesis es que no todas las capas contribuyen igual durante la adaptación. Entonces el algoritmo debe medir alguna señal de importancia y asignar o modificar la capacidad de bajo rango de acuerdo con esa señal."

### Minuto 4-6: algoritmo

"El flujo es: primero tomo un Transformer preentrenado y congelo sus pesos. Luego inserto adaptadores de bajo rango en módulos objetivo, por ejemplo proyecciones de atención. Durante el entrenamiento, optimizo solo los parámetros del adaptador. Si el método es dinámico, periódicamente calculo una señal de importancia, como norma de gradiente o contribución de cada componente de rango, y uso esa señal para mantener, podar o reasignar componentes bajo un presupuesto total. Al final, obtengo un checkpoint pequeño y, si aplica, una distribución final de rangos por capa."

### Minuto 6-7: resultados

"En este workspace no hay resultados DoLoRA, así que no voy a inventar cifras. Para una defensa completa, aquí debería mostrar una tabla con full fine-tuning, LoRA, AdaLoRA y DoLoRA, reportando métrica de tarea, parámetros entrenables, memoria y tiempo. También mostraría una ablation para demostrar que la regla dinámica aporta, no solo el número de parámetros."

### Minuto 7-8: estado real del repositorio

"El repositorio que tengo aquí actualmente no contiene DoLoRA. Es un proyecto distinto: un agentic harness para computer-use agents. Tiene FastAPI, Docker workers, eval gates, memoria local, traces, task queue SQLite, demo de agentes paralelos y documentación de entrevista. Por eso separo el marco conceptual de DoLoRA de la evidencia real del repo."

### Minuto 8-9: limitaciones

"Las limitaciones principales para DoLoRA son experimentales: faltan runs reproducibles, baselines, seeds, ablations y análisis de coste. Sin eso, el claim debe ser conservador. La contribución debe defenderse por mecanismo y evidencia, no por promesa."

### Minuto 9-10: conclusión

"La forma fuerte de presentar DoLoRA es: fine-tuning completo es caro; LoRA es eficiente pero usa una asignación rígida de rango; DoLoRA busca asignar la capacidad adaptativa de manera más informada. Para cerrar la investigación, necesito enlazar esa idea con resultados reproducibles y comparaciones honestas contra baselines. Esa transparencia es importante en una entrevista académica porque muestra criterio experimental, no solo implementación."

## 12. Preguntas difíciles y respuestas

### 1. Qué diferencia a LoRA del fine-tuning completo?

LoRA congela los pesos base y aprende una actualización de bajo rango. Fine-tuning completo actualiza todos los pesos. LoRA reduce parámetros entrenables, memoria y tamaño de checkpoint.

### 2. Por qué una actualización de bajo rango puede funcionar?

Porque muchas adaptaciones por tarea parecen vivir en un subespacio de menor dimensión que el espacio completo de pesos. LoRA explota esa hipótesis parametrizando `Delta W` como `B A`.

### 3. Cuál es el principal hiperparámetro de LoRA?

El rango `r`, además de `alpha`, learning rate y módulos objetivo. `r` controla la capacidad y el número de parámetros entrenables.

### 4. Qué problema intenta resolver DoLoRA sobre LoRA?

Conceptualmente, evitar una asignación rígida o subóptima de capacidad de bajo rango. El repo no contiene la implementación concreta, así que la respuesta exacta depende del código externo.

### 5. Cómo justificarías adaptar rangos por capa?

Las capas no contribuyen igual a una tarea. Algunas requieren más capacidad de adaptación y otras pueden funcionar con menos. Adaptar rangos permite usar un presupuesto fijo de forma más eficiente.

### 6. Qué baseline mínimo necesitas para defender DoLoRA?

Full fine-tuning si es posible, LoRA con varios rangos, y un método dinámico como AdaLoRA. También una ablation de DoLoRA sin la regla dinámica.

### 7. Qué métrica principal usarías?

Depende de la tarea: accuracy/F1 para clasificación, Matthews para CoLA, EM/F1 para QA, perplexity para language modeling. Además reportaría parámetros entrenables, memoria, tiempo y tamaño de checkpoint.

### 8. Si DoLoRA mejora poco sobre LoRA, sigue siendo valioso?

Sí, si logra rendimiento comparable con menos parámetros, menor memoria o más estabilidad. Pero si no mejora ninguna dimensión, la contribución sería débil.

### 9. Cómo evitar overclaiming?

Separando claims cuantitativos de hipótesis. Si no hay resultados reproducibles, digo "no encontrado" o "pendiente", no "mejora".

### 10. Qué evidencia falta en este repositorio?

Falta todo lo específico de DoLoRA: implementación, configs, datasets, modelos, métricas, resultados y ablations.

### 11. Qué diferencia habría entre DoLoRA y AdaLoRA?

AdaLoRA es un baseline dinámico conocido que redistribuye presupuesto de rango usando importancia. DoLoRA debe explicar una regla, parametrización o señal distinta. Si no hay una diferencia clara, el comité puede verlo como reinvención.

### 12. Qué módulos Transformer adaptarías primero?

Normalmente `q_proj` y `v_proj` son un punto de partida común; para modelos decoder-only también pueden adaptarse `k_proj`, `o_proj` y MLP. La elección debe validarse experimentalmente.

### 13. Por qué no adaptar embeddings?

Los embeddings pueden ser grandes y no siempre son el cuello de botella adaptativo. Para muchas tareas, adaptar atención/MLP ofrece mejor trade-off, aunque depende del dominio.

### 14. Qué riesgos tiene una adaptación dinámica?

Puede introducir inestabilidad, overhead de decisión, sensibilidad a hiperparámetros y dificultad para reproducir resultados. También puede mejorar por presupuesto efectivo y no por la regla propuesta.

### 15. Cómo probarías que la regla de DoLoRA importa?

Con ablations: misma cantidad de parámetros con rango fijo, asignación aleatoria de rangos, DoLoRA sin actualización dinámica y DoLoRA completo.

### 16. Qué harías si el comité pregunta por resultados?

Respondería honestamente: "En este repositorio no hay resultados DoLoRA. Si hablamos del algoritmo, necesito traer la tabla externa o reproducir los experimentos. No voy a inventar números."

### 17. Cómo medirías eficiencia real?

Reportaría parámetros entrenables, memoria máxima GPU, tiempo por epoch, throughput, tamaño de checkpoint y rendimiento final. Un método PEFT debe evaluarse en calidad y coste.

### 18. Qué pasa si el rango dinámico termina parecido al rango fijo?

Entonces la dinámica quizá no aporta mucho. Aun así puede aportar interpretabilidad por capa, pero la mejora principal debería demostrarse con métricas.

### 19. Cómo conectarías esto con investigación académica?

Formularía una hipótesis clara: la capacidad adaptativa necesaria es heterogénea entre capas. Luego diseñaría un método, baselines, ablations y análisis estadístico para probarla.

### 20. Qué dirías sobre reproducibilidad?

Que es esencial: configs, seeds, versiones de librerías, hardware, datasets y scripts deben estar en el repo. Actualmente eso no existe para DoLoRA en este workspace.

## 13. Elementos visuales recomendados

### Imprescindible

1. Diagrama LoRA/DoLoRA: `W_0` congelado más rama `A -> B` de bajo rango.
2. Tabla comparativa: full fine-tuning vs LoRA vs AdaLoRA vs DoLoRA.
3. Tabla de parámetros entrenables: full matrix vs low-rank adapters.
4. Slide de honestidad experimental: "DoLoRA no encontrado en este repo; resultados pendientes o externos".

### Recomendado

1. Curva conceptual de rendimiento vs parámetros entrenables.
2. Heatmap de rangos por capa, si existe en resultados externos.
3. Diagrama del flujo: entrada, inicialización, score, adaptación, entrenamiento, salida.
4. Tabla de ablations: fixed rank, random allocation, dynamic allocation.

### Opcional

1. Captura del árbol del repo mostrando que actualmente es un harness, no un repo ML.
2. Diagrama de arquitectura del repositorio actual: FastAPI, Docker workers, harness, eval gates.
3. Slide de próximos pasos: implementar DoLoRA en repo, añadir configs y reproducir baselines.

## 14. Diferencia entre la versión anterior y la actual

### Cómo estaba el trabajo en la primera entrevista

No encontrado en el repositorio para DoLoRA.

El repositorio sí contiene documentación de entrevistas para el proyecto de agentic harness, pero no evidencia de una primera entrevista sobre DoLoRA ni un snapshot anterior del algoritmo.

### Qué se completó ahora

Para DoLoRA:

- No encontrado en el repositorio.
- No se puede afirmar que se completó implementación, entrenamiento o evaluación.

Para el repositorio actual de computer-use orchestrator:

- La documentación indica que se cerraron evidencias sobre tmux persistence del runner standalone después de reboot real de macOS.
- Se verificó uso del GitHub Spec Kit CLI de forma retroactiva.
- Se probó Claude Code Agent Teams como ejercicio aislado, no integrado al runtime.
- El harness contiene demos, evals offline, memory fallback, traces, shared queue y scripts de entrevista.

### Por qué la versión actual sería más fuerte

Si la entrevista es sobre el repositorio actual, la versión actual es más fuerte porque tiene mejor evidencia auditada, comandos de demo y distinción más honesta entre implementado, verificado y roadmap.

Si la entrevista es específicamente sobre DoLoRA, la versión actual todavía no es fuerte desde este repo porque falta la evidencia central. Para fortalecerla antes de Skoltech habría que añadir:

- `dolora/` o módulo equivalente con implementación.
- `configs/` con experimentos reproducibles.
- `scripts/train_dolora.py` y `scripts/evaluate_dolora.py`.
- `results/` con tablas y logs.
- README técnico del algoritmo.
- Comparación contra LoRA/AdaLoRA.
- Ablations.

## Cierre defendible

La frase más segura para la entrevista es:

> "DoLoRA es el algoritmo que quiero presentar como trabajo de fine-tuning eficiente, pero este workspace actual no contiene su implementación ni resultados. Lo que sí contiene es otro proyecto: un harness para agentes de computer-use. Para defender DoLoRA académicamente necesito traer o integrar el código, resultados y configs. Mientras tanto, puedo explicar claramente la motivación y el marco LoRA, pero no debo afirmar mejoras cuantitativas desde este repositorio."

