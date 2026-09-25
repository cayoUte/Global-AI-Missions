# Uso de IA en el desarrollo — Global AI Missions

> Declaración pedida en el §10 del enunciado: qué herramientas de IA se usaron y qué partes hizo personalmente el candidato.
> Fuentes: el registro de trabajo [`docs/AI_USAGE_LOG.md`](AI_USAGE_LOG.md) (una entrada por entrega de cada agente), el historial de Git, [`docs/product/DECISIONS_LOG.md`](product/DECISIONS_LOG.md) y [`docs/contracts/CHANGE_REQUESTS.md`](contracts/CHANGE_REQUESTS.md).

> [CONFIRMA O AJUSTA: el candidato revisa este documento completo, en especial la sección 3, antes de entregar]

## 1. Herramientas

| Herramienta | Para qué |
|---|---|
| **Claude Code (Anthropic)**, CLI local y sesiones en la nube | Única herramienta de IA usada para construir el proyecto. Una sesión principal hizo de orquestador y delegó el trabajo en **12 subagentes especializados** definidos en [`.claude/agents/`](../.claude/agents/), todos con el mismo contexto compartido ([`docs/agents/SHARED_CONTEXT.md`](agents/SHARED_CONTEXT.md)). |

- Las primeras fases (marco, esqueleto, contenido, backend, frontend) se trabajaron en la máquina del candidato (Windows con Docker Desktop) y el candidato hizo esos commits. Desde la tarde del 25/09, la calidad y la entrega (QA, segundo proveedor de IA, correcciones de bugs, documentos finales, Docker, CI y deploy) se hicieron en sesiones de Claude Code en la nube, que firmaron sus propios commits (autor `Claude`, con la línea `Co-Authored-By`).
- Los agentes también escribieron scripts auxiliares desechables (para generar JSON, SVG o capturas de pantalla), que no están en el repositorio.

**La IA que usa la aplicación es otra cosa.** Maya, la coach, escribe el feedback del reporte con un LLM en tiempo de ejecución: por defecto un mock determinista sin red, y opcionalmente Claude (API de Anthropic) o cualquier API compatible con OpenAI, como Groq o xAI Grok (ver [`docs/ai/AI_ARCHITECTURE.md`](ai/AI_ARCHITECTURE.md)). Esa parte es producto; este documento trata de la IA usada para construirlo.

## 2. Cómo se organizó el trabajo

- **Un contexto único** (`SHARED_CONTEXT.md`) con el enunciado, el concepto, las invariantes de evaluación y de seguridad, el stack y quién es dueño de cada carpeta. Cada agente editaba solo sus archivos; cualquier cambio en un contrato congelado pasaba por una *change request* que decidía el candidato.
- **Controles humanos (gates)** en el plan de 8 horas ([`docs/agents/README.md`](agents/README.md)): G0 contratos, G1 esqueleto que recorre todo el flujo, G2 misión real completa, G3 tests y ensayo, G4 entrega.
- **Registro obligatorio**: cada agente, al terminar, añadía a `AI_USAGE_LOG.md` qué archivos tocó, qué hizo y qué comandos corrió para verificarlo.

| # | Agente | Qué produjo |
|---|---|---|
| 00 | `product-architect` | Especificación de producto (recorridos, criterios de aceptación por pantalla, alcance), la biblia de Maya, el mapa de requisitos contra el enunciado y el catálogo de 5 misiones con reglas de desbloqueo. |
| 01 | `tech-lead` | Esqueleto de backend y frontend, contratos congelados (JSON Schemas del contenido, contrato de la API, convenciones), y al final `DECISIONS.md` e `INTERVIEW.md`. |
| 02 | `assessment-designer` | Los 10 ítems originales (`items.json`) y `ASSESSMENT_SPEC.md`: blueprint, puntaje, regla de nivel con tope por evidencia, 9 ejemplos resueltos, normalización y plantillas de interpretación. |
| 03 | `narrative-designer` | La historia *The Last Train*: guion, `mission.json` (37 nodos, 53 aristas, 3 finales, variantes por banderas y el plan B del autobús nocturno) y los fondos de escena. |
| 04 | `story-graph-engineer` | Motor en Python puro: grafo, `RESULT`, heurística exacta por Dijkstra inverso, Maya planificadora (pista y rescate), validador de los 1.024 caminos, estudiante simulado, Diario; misión fixture para el esqueleto. |
| 05 | `data-engineer` | Modelo de datos (16 tablas), migración Alembic, repositorios y seed idempotente con usuarios demo y el historial simulado de Leo. |
| 06 | `backend-api-engineer` | Todos los endpoints: auth con cookie httpOnly, ciclo del intento, calificación, nivel, reporte, progreso, profesor; `StateView` como único mapeo hacia el cliente; submit en dos fases. |
| 07 | `ai-coach-engineer` | Puerto `CoachProvider`, adaptadores mock, Claude y compatible con OpenAI (Groq, xAI), memoria de Maya, prompt versionado, script de verificación en vivo y `AI_ARCHITECTURE.md`. |
| 08 | `ux-ui-designer` | Lenguaje visual, tokens de diseño con contraste WCAG calculado, especificación de pantallas y el avatar SVG de Maya en cuatro estados de ánimo. |
| 09 | `frontend-engineer` | Toda la app React: Check-in, English World, reproductor de misión (máquina de estados), renderizadores por tipo de ítem, Ending, Mission Report y Progress. |
| 10 | `qa-engineer` | Plan de pruebas por riesgo, tests de huecos (fugas, roles, concurrencia en PostgreSQL), E2E con Playwright, verificaciones en navegador, lista de bugs y guion de la demo. |
| 11 | `delivery-engineer` | docker-compose y Makefile al inicio; al final Dockerfile, Blueprint de Render, CI, este documento y el README. |

La sesión orquestadora también aplicó directamente algunos cambios pequeños: las correcciones de BUG-001 a BUG-004 encontrados por QA y los cambios aceptados en CR-007 y CR-008.

## 3. Qué hizo personalmente el candidato

Según los registros (el candidato lo confirma o lo corrige):

- **Concepto y dirección de producto.** La idea central ("no un sistema de evaluación con elementos de juego, sino una experiencia narrativa que por dentro es una evaluación"), Maya como compañera y la misión *The Last Train* vienen fijadas en el contexto compartido que el candidato preparó para los agentes antes de que empezaran.
- **Diseño del equipo de agentes.** Los 12 briefs, el contexto compartido, las reglas de propiedad de carpetas y el plan por fases con gates (commit `agents` del 24/09). _[El candidato indica si los redactó solo o con ayuda de un asistente de IA, y cuál.]_
- **Auditoría y revisión de la especificación** antes de construir (entrada 2 del registro, hecha con un asistente de IA): el reporte empieza por los números del enunciado (PD-001), se eliminó el botón de saltar (PD-011), presupuesto de 8 horas con un esqueleto que recorre el flujo a las 2:30 (PD-027) y los cambios de contrato de §6–§12.
- **Decisiones tomadas por el candidato** (marcadas "human" en los registros): PD-008 (reglas de desbloqueo deterministas), PD-009 (perfil sobre los últimos 3 intentos), PD-011 (sin botón de saltar, rechazando la propuesta del agente), PD-014 (texto de respaldo si no hay voz), PD-018 (panel de cuentas demo), PD-023 (nombres de los usuarios demo), PD-025 (formato del catálogo), PD-027 (8 horas), PD-031 (sin campo `outcome` en la respuesta y la etiqueta "Departing now"), PD-032 (valores por defecto de UI) y PD-033 (adaptador compatible con OpenAI y Groq para la demo en vivo); PD-001 lo delegó.
- **Change requests** aceptadas por el candidato: CR-001 (puerto 5433 para tests), CR-002 (Maya solo rescata si el rescate aún salva el tren), CR-003 (una sola función de normalización), CR-005 (`127.0.0.1` en vez de `localhost`), CR-007 (cualquier nombre de proveedor cae al mock), CR-008 (`/api/auth/me` anónimo → `200 null`) y CR-009 (variables del adaptador compatible con OpenAI).
- **Orquestación e integración:** lanzar cada agente con su tarea, pasar el trabajo entre fases, decidir qué entraba y qué se recortaba (la vista de profesor y el replay simulado se dejaron para el final y se construyeron solo cuando todo estaba en verde), y organizar los commits de las fases 0–2.
- **Verificación manual:** revisión en los gates y pruebas de la app en local. _[El candidato detalla qué revisó en cada gate y qué probó a mano.]_
- **Código escrito o reescrito a mano:** los registros no muestran módulos reescritos a mano por el candidato. _[Si reescribió o ajustó algo, lo indica aquí con el archivo.]_

> [CONFIRMA O AJUSTA: el candidato revisa esta sección antes de entregar]

## 4. Cómo se verificó lo que produjo la IA

- **Tests automáticos escritos por los agentes y ejecutados en cada entrega** (los resultados de cada corrida están en el registro): pytest del backend (unitarios, API sobre un doble en memoria y sobre PostgreSQL real, motor, datos, IA, contratos), Vitest en el frontend y Playwright sobre la app real. Al cierre: 297 tests de backend, 26 de frontend y 6 E2E en verde.
- **Verificación cruzada entre agentes:** QA escribió tests independientes de los de cada dueño (por ejemplo, recorrer los 1.024 caminos de la misión real sin usar el validador del motor, y buscar claves de respuesta en cada respuesta HTTP y en el bundle del SPA), encontró 5 bugs y 4 se corrigieron (el quinto era de redacción del contrato y se resolvió en CR-010).
- **Invariantes en la base de datos** (índices únicos parciales, CHECK) además de en el código, y validación del contenido con JSON Schema y con el validador del motor antes de sembrar.
- **Pruebas en navegador real** (Chromium sin interfaz): recorrido completo con teclado a 1280 y 360 px, recarga a mitad de misión, dos pestañas, sin voz, movimiento reducido y el pie del reporte con un proveedor que falla.
- **Entrega:** la imagen Docker se construyó y se arrancó de verdad (base vacía → migraciones → seed → login → API y SPA respondiendo), y el Makefile, la CI y el README se revisaron contra esos comandos.
- **Lo que no se pudo verificar desde el entorno de construcción:** una llamada real a un LLM (la red lo bloqueaba; queda `backend/scripts/coach_smoke.py` para hacerla con una clave), la voz del navegador en Chrome, Safari y Firefox, un lector de pantalla real, la ejecución de GitHub Actions y el deploy en Render.

## 5. Horas reales invertidas

**Aproximadamente 7 horas**, en un día, dentro del presupuesto de 6–8 horas del enunciado (dato del candidato). Varios agentes trabajaron en paralelo, por eso la suma de sus tiempos estimados supera ese número.
