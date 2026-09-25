# Equipo de agentes · Global AI Missions

Este paquete define 12 agentes especializados para construir Global AI Missions en 8 horas (el enunciado estima 6–8 horas en un día, sin trabajo nocturno). Cada agente tiene un brief con el formato **ROLE · MISSION · RESPONSIBILITIES · OUTPUT · CONSTRAINTS**, y todos comparten una única fuente de verdad: [`SHARED_CONTEXT.md`](SHARED_CONTEXT.md).

Los briefs y el contexto están en inglés, porque el código y el contenido de la app también lo están. Los documentos para los evaluadores (README, DECISIONS, INTERVIEW, AI_USAGE y AI_ARCHITECTURE) se escriben en español. El resto de `docs/` son notas internas de trabajo.

---

## Cómo usarlos

**En Claude Code (recomendado).** Copia las carpetas `.claude/agents/` y `docs/agents/` a la raíz del repositorio. Cada brief queda disponible como subagente y se invoca así: *"Usa el subagente narrative-designer para escribir la misión."*

**En cualquier otra herramienta o sesión.** Abre una sesión por agente y pega, en este orden: `SHARED_CONTEXT.md`, el brief del agente y la instrucción de arranque del final de este documento.

---

## El equipo

| # | Agente | Entrega principal | Tiempo | Necesita antes |
|---|---|---|---|---|
| 00 | `product-architect` | PRODUCT.md, REQUIREMENTS_MAP.md, MAYA.md, catalog.json | 20 min (hecho) | — |
| 01 | `tech-lead` | Esqueleto del repo, contratos (esquemas y API), DECISIONS.md, INTERVIEW.md | 45 + 40 min | — |
| 02 | `assessment-designer` | items.json, ASSESSMENT_SPEC.md | 35 min | 00, 01 |
| 03 | `narrative-designer` | mission.json, SCRIPT.md, BACKDROPS.md | 50 min | 02 |
| 04 | `story-graph-engineer` | Grafo fixture, motor de búsqueda, Maya planificadora, validador, simulador | 75 min | 01 (y 03 para el contenido real) |
| 05 | `data-engineer` | Modelos, migración, repositorios, seed con usuarios demo | 45 + 15 min | 01 (y 04 para el historial del veterano) |
| 06 | `backend-api-engineer` | API, ciclo del intento, reporte, progreso, roles | 90 min | 04, 05 |
| 07 | `ai-coach-engineer` | Maya con LLM: puerto, Claude, mock, memoria, AI_ARCHITECTURE.md | 45 min | 01 |
| 08 | `ux-ui-designer` | UI_SPEC.md, tokens, avatar de Maya | 30 min | 00 |
| 09 | `frontend-engineer` | Toda la app React | 135 min | 01, 08 (y 06 para integrar) |
| 10 | `qa-engineer` | Plan de pruebas, tests de seguridad, E2E, guion de la demo | 45 min | 06, 09 |
| 11 | `delivery-engineer` | Docker, CI, README, AI_USAGE.md, deploy | 15 + 40 min | todos |

Los tiempos suman más de 8 horas porque varios agentes trabajan en paralelo.

---

## Plan de 8 horas

| Hora | Fase | Qué pasa | Control humano |
|---|---|---|---|
| 0:00–0:45 | 0 · Marco | `tech-lead` (esqueleto y contratos) ∥ `delivery-engineer` (docker-compose, .env.example, .gitignore, Makefile) ∥ `story-graph-engineer` (grafo fixture en `content/missions/_fixture/`) | **G0** (0:45) — ¿Los contratos cubren todo el flujo? ¿Entiendes la estructura del repo? |
| 0:45–2:30 | 1 · Esqueleto que recorre el flujo | `data-engineer` (modelos, seed con el fixture) · `backend-api-engineer` (auth, world, intento, submit con coach mock) · `frontend-engineer` (pantallas y renderizadores sencillos) · en paralelo: `assessment-designer` → `narrative-designer`, `ux-ui-designer` | **G1** (2:30) — Con docker compose: check-in → English World → 10 checkpoints del fixture → Submit mission → números del reporte → fila en Progress. Lee SCRIPT.md: ¿ítems 4/2/2/2 y niveles? |
| 2:30–5:00 | 2 · Contenido real e inmersión | validador con el contenido real · seed con la misión y el veterano · Maya planificadora · `ai-coach-engineer` · `frontend-engineer` (UI_SPEC, reporte completo, Progress) | **G2** (5:00) — Misión real completa con `new@`. En DevTools, comprueba que no viajen respuestas. Recarga a mitad de misión y en el final. |
| 5:00–6:30 | 3 · Calidad | `qa-engineer` · correcciones de cada dueño · pase responsive (360 px) y de accesibilidad · deploy de la misma imagen · extras solo si todo está verde | **G3** (6:30) — Tests en verde. Ensayo de la demo con `new@` y `veteran@`. |
| 6:30–7:30 | 4 · Entrega | `delivery-engineer` (README, Docker, CI, redeploy) · `tech-lead` (DECISIONS.md, INTERVIEW.md) · AI_USAGE.md | — |
| 7:30–8:00 | Margen | Clon limpio siguiendo el README, ensayo final, tag v1.0.0 | **G4** — ¿Puedes explicar cada módulo? ¿AI_USAGE.md es fiel a lo que pasó, con las horas reales? |

**Ruta crítica:** contratos → esqueleto que recorre el flujo §1 con el fixture → contenido real → Maya e inmersión → QA → entrega. El esqueleto de G1 es la entrega mínima de respaldo. Si algo se atrasa, se recorta el pulido (animaciones, typewriter) y los extras (vista de profesor, replay simulado, segundo proveedor de IA), nunca el flujo.

---

## Reglas de colaboración

1. `SHARED_CONTEXT.md` manda. Si un brief lo contradice, gana el contexto.
2. Cada agente edita solo sus archivos (§11 del contexto). Los cambios en archivos ajenos o en los contratos se piden en `docs/contracts/CHANGE_REQUESTS.md`.
3. Los contratos se congelan en G0. Cambiarlos después exige anotar el impacto.
4. Cada entrega se registra en `docs/AI_USAGE_LOG.md`: qué agente la hizo, qué revisaste y qué cambiaste tú.
5. Commits pequeños y convencionales (`feat(engine): …`, `test(api): …`, `docs: …`).

---

## Tu papel

Eres el orquestador y el dueño de las decisiones. La prueba exige que puedas explicar y modificar el código en la entrevista, así que en cada control no apruebes nada que no entiendas.

Lo que más te conviene leer a fondo tú mismo:

- `backend/app/engine/` (el motor de búsqueda y la política de Maya).
- `backend/app/services/grading.py`, `leveling.py` y `state_view.py` (`to_state_view`): responden las preguntas 2 y 8 de la entrevista. Los escribe el `backend-api-engineer`; tú los revisas línea por línea en G1.
- `backend/app/services/attempts.py`: la pregunta 7 (reanudar tras perder la conexión).
- `backend/app/ai/`: la respuesta a la pregunta 5.

---

## Instrucción de arranque

Plantilla para cualquier agente (reemplaza `<agent-name>`):

> You are the `<agent-name>` agent. Read `docs/agents/SHARED_CONTEXT.md` and your brief completely, then read the inputs your brief lists. Work only on the files you own. When you finish, check your Definition of done, append an entry to `docs/AI_USAGE_LOG.md`, and summarize what you delivered, what you assumed and what the next agent needs to know.
