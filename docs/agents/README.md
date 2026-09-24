# Equipo de agentes · Global AI Missions

Este paquete define 12 agentes especializados para construir Global AI Missions en 10 horas. Cada agente tiene un brief con el formato **ROLE · MISSION · RESPONSIBILITIES · OUTPUT · CONSTRAINTS**, y todos comparten una única fuente de verdad: [`SHARED_CONTEXT.md`](SHARED_CONTEXT.md).

Los briefs y el contexto están en inglés, porque el código y el contenido de la app también lo están. Los documentos para los evaluadores (README, DECISIONS, INTERVIEW y AI_USAGE) se escriben en español.

---

## Cómo usarlos

**En Claude Code (recomendado).** Copia las carpetas `.claude/agents/` y `docs/agents/` a la raíz del repositorio. Cada brief queda disponible como subagente y se invoca así: *"Usa el subagente narrative-designer para escribir la misión."*

**En cualquier otra herramienta o sesión.** Abre una sesión por agente y pega, en este orden: `SHARED_CONTEXT.md`, el brief del agente y la instrucción de arranque del final de este documento.

---

## El equipo

| # | Agente | Entrega principal | Tiempo | Necesita antes |
|---|---|---|---|---|
| 00 | `product-architect` | PRODUCT.md, REQUIREMENTS_MAP.md, MAYA.md, catalog.json | 30 min | — |
| 01 | `tech-lead` | Esqueleto del repo, contratos (esquemas y API), DECISIONS.md, INTERVIEW.md | 60 + 45 min | — |
| 02 | `assessment-designer` | items.json, ASSESSMENT_SPEC.md | 40 min | 00, 01 |
| 03 | `narrative-designer` | mission.json, SCRIPT.md, BACKDROPS.md | 60 min | 02 |
| 04 | `story-graph-engineer` | Motor de búsqueda, Maya planificadora, validador, simulador, calibración | 90 min | 01 (y 03 para el contenido real) |
| 05 | `data-engineer` | Modelos, migración, repositorios, seed con usuarios demo | 60 + 15 min | 01 (y 04 para el historial del veterano) |
| 06 | `backend-api-engineer` | API completa, calificación, nivel sugerido, reporte, roles | 105 min | 04, 05 |
| 07 | `ai-coach-engineer` | Maya con LLM: puerto, Claude, mock, memoria | 60 min | 01 |
| 08 | `ux-ui-designer` | UI_SPEC.md, tokens, avatar de Maya | 45 min | 00 |
| 09 | `frontend-engineer` | Toda la app React | 150 min | 01, 08 (y 06 para integrar) |
| 10 | `qa-engineer` | Plan de pruebas, tests de seguridad, E2E, guion de la demo | 60 min | 06, 09 |
| 11 | `delivery-engineer` | Docker, CI, README, AI_USAGE.md, deploy opcional | 15 + 45 min | todos |

Los tiempos suman más de 10 horas porque varios agentes trabajan en paralelo.

---

## Plan de 10 horas

| Hora | Fase | Qué pasa | Control humano |
|---|---|---|---|
| 0:00–1:00 | 0 · Marco | `product-architect` ∥ `tech-lead` (esqueleto y contratos) ∥ `delivery-engineer` (docker-compose, .env.example, .gitignore, Makefile) | **G0** (1:00) — ¿Los contratos cubren todo el flujo? ¿Entiendes la estructura del repo? |
| 1:00–3:00 | 1 · Contenido y cimientos | `assessment-designer` → `narrative-designer` · `story-graph-engineer` (con un grafo de prueba) · `data-engineer` · `ux-ui-designer` · `backend-api-engineer` (auth y world desde las 2:00) · `frontend-engineer` (desde 1:45, con datos simulados) | **G1** (2:40) — Lee SCRIPT.md completo. ¿Los ítems cumplen 4/2/2/2 y los niveles? ¿El validador pasa con el contenido real? |
| 3:00–6:00 | 2 · Construcción | `backend-api-engineer` (intentos, calificación, reporte) · `ai-coach-engineer` · calibración con el simulador · nuevo seed con el veterano · `frontend-engineer` (integración) | **G2** (6:00) — Misión completa con `new@`. En DevTools, comprueba que no viajen respuestas. Recarga a mitad de misión. |
| 6:00–8:00 | 3 · Calidad | `qa-engineer` · correcciones de cada dueño · pase responsive y de accesibilidad · extras solo si todo está verde | **G3** (8:00) — Tests en verde. Primer ensayo de la demo con `veteran@` y `new@`. |
| 8:00–9:30 | 4 · Entrega | `delivery-engineer` (README, Docker, CI, deploy opcional) · `tech-lead` (DECISIONS.md, INTERVIEW.md) · AI_USAGE.md | — |
| 9:30–10:00 | Margen | Clon limpio siguiendo el README, ensayo final, tag v1.0.0 | **G4** — ¿Puedes explicar cada módulo? ¿AI_USAGE.md es fiel a lo que pasó? |

**Ruta crítica:** contratos → ítems → guion → validación del motor con el contenido real → intentos en el backend → integración del frontend → QA → entrega. Si algo se atrasa, se recortan los extras (vista de profesor, replay simulado, segundo proveedor de IA), nunca la ruta crítica.

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
- `backend/app/services/attempts.py` y la función `to_state_view`: ahí están las respuestas a las preguntas 2, 7 y 8 de la entrevista.
- `backend/app/ai/`: la respuesta a la pregunta 5.

---

## Instrucción de arranque

Plantilla para cualquier agente (reemplaza `<agent-name>`):

> You are the `<agent-name>` agent. Read `docs/agents/SHARED_CONTEXT.md` and your brief completely, then read the inputs your brief lists. Work only on the files you own. When you finish, check your Definition of done, append an entry to `docs/AI_USAGE_LOG.md`, and summarize what you delivered, what you assumed and what the next agent needs to know.
