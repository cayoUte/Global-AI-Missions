# Decisiones técnicas — Global AI Missions

Una misión narrativa (*The Last Train*) que por dentro es una evaluación de 10 ítems. Rutas relativas a la raíz.

## 1. Stack y por qué

| Capa | Elección | Motivo |
|---|---|---|
| Frontend | React + TypeScript + Vite + Tailwind, TanStack Query | Ecosistema estándar. Los tipos se generan desde `docs/contracts/openapi.json` |
| Backend | Python 3.12 + FastAPI + Pydantic v2 | Validación declarativa (`extra="forbid"`) y OpenAPI incluidos. Síncrono, fácil de explicar |
| Datos | PostgreSQL 16 + SQLAlchemy 2.0 + Alembic | Restricciones reales: índices únicos parciales, CHECK, `FOR UPDATE` |
| Auth | JWT en cookie `httpOnly` `SameSite=Lax`, argon2id | JavaScript no puede leer el token. Un solo origen, sin CORS |
| Entrega | Docker Compose; FastAPI sirve la SPA; GitHub Actions y Render | Un comando y una URL de demo |

Tecnología aburrida a propósito: sin microservicios, colas ni Redis en el MVP. Pruebas: 297 pytest, 26 Vitest y 6 E2E con Playwright.

**Qué está simulado.** El coach usa por defecto un mock determinista (sin clave ni costo). Los adaptadores reales se probaron con clientes falsos; **aún no se verificó una llamada en vivo** (`backend/scripts/coach_smoke.py`). *Listening* usa `speechSynthesis` (sin voz, se muestra el texto, PD-014). Las fuentes vienen de Google Fonts (`frontend/index.html`); en producción, de nuestro origen o CDN (PD-032).

## 2. Arquitectura

```
SPA React ──cookie httpOnly──▶ FastAPI (un proceso, un origen)
  app/api/routers   HTTP, validación, guardas de rol
  app/services      casos de uso y transacciones
     ├─▶ app/engine        grafo, RESULT, h, Maya (Python puro)
     ├─▶ app/repositories  ──▶ PostgreSQL
     └─▶ app/ai            CoachProvider: mock | anthropic | openai_compatible
```

- Capas estrictas (`docs/contracts/conventions.md`): el motor no importa FastAPI ni SQLAlchemy. Contrato congelado en `docs/contracts/api-contract.md`.
- **La misión es un problema de búsqueda.** Estado `(nodo, minutos, flags, rescate, ánimo)`; `RESULT(s, a)` solo en el servidor (`backend/app/engine/transition.py`); `h` exacta por Dijkstra inverso (`heuristic.py`). Maya da una pista si la holgura es menor que 3 y rescata una vez como máximo (`maya.py`). El LLM nunca decide el flujo.
- **Grafo trenzado:** todos los caminos pasan por los mismos 10 checkpoints (4/2/2/2, A1→B2); los 1.024 caminos se verifican en `backend/tests/engine/test_real_mission_invariants.py`.

## 3. Modelo de datos

Diagrama ER en `docs/data/DATA_MODEL.md`.

| Grupo | Tablas |
|---|---|
| Referencia e identidad | `cefr_levels` (PRE_A1…C1 con `rank`), `skills`, `users` (`role`), `classes`, `class_members` |
| Contenido | `missions`, `mission_versions` (grafo inmutable), `questions`, `question_options` (`is_correct`), `accepted_answers` |
| Ejecución e IA | `attempts`, `attempt_steps`, `attempt_answers`, `attempt_skill_scores`, `coach_feedback`, `coach_memory` |

- **Los niveles son datos.** Pre-A1…C1 son filas con `rank` referenciadas por FK: una misión C1 es contenido, no una migración. Solo el blueprint del validador y las bandas (tope B2) viven en código.
- **Los intentos son un árbol de búsqueda persistido.** Cada transición es una fila de `attempt_steps` con padre, acción y costo; seguir los punteros desde el final da el Diario (`engine/diary.py`).
- **El progreso se calcula, no se guarda.** Una consulta usa los 3 últimos intentos enviados (`repositories/progress.py::get_profile`).
- Solo hay un intento abierto por alumno y misión (índice parcial `uq_attempts_one_open`).

## 4. Protección de las respuestas correctas

- Las claves nunca salen del servidor; cada respuesta se califica allí al bloquearse.
- Durante la misión el cliente solo recibe un `StateView`, construido por lista blanca (`backend/app/services/state_view.py`): sin clave, `is_correct`, explicación, pista, `skill`, `cefr` ni nodos futuros. `answer` tampoco dice si acertó, y los 409 traen ese mismo `StateView` para resincronizar.
- Un escáner recursivo revisa cada respuesta y cada 409 (`backend/tests/api/test_qa_gaps.py`), y también el bundle de la SPA.
- La respuesta correcta y la explicación solo aparecen en el Reporte de un intento enviado.
- **Límites conocidos:** el guion de *listening* llega al navegador por `speechSynthesis` (producción: audio pregenerado con URLs firmadas), y repetir la misión tras ver su reporte no es una reevaluación segura (hace falta un banco de ítems).

## 5. Escalar de 100 a 50.000–100.000 estudiantes

| Pieza | Hoy | A escala |
|---|---|---|
| API | Sin estado (JWT en cookie, misión en BD) | Réplicas tras un balanceador. **Excepción:** el rate limit de login vive en memoria de cada proceso (`backend/app/core/rate_limit.py`); con una instancia sirve, a escala pasa a Redis o al gateway |
| Base de datos | Pool con `pool_pre_ping`, índices por usuario y fecha | PgBouncer, réplicas de lectura, particionar `attempt_steps` |
| Contenido | Versiones inmutables en caché (`services/content.py`) | Igual con N réplicas; SPA y audio en CDN |
| LLM | Fase 2 de `submit`: **tras el commit de la calificación**, 8 s y fallback (`services/attempts.py::submit`) | **Esa costura pasa a una cola con workers**; el reporte ya se muestra sin feedback |
| Costo | Una llamada por intento | Límites por alumno, tope de gasto, Batch API |
| Observabilidad | `X-Request-ID`, logs con latencia | Métricas, trazas, pruebas de carga |

## 6. Roles

- `users.role` es `student`, `teacher` o `admin`, y se lee de la BD en cada petición, no del token (`services/auth.py::session_user`). Las guardas son dependencias (`require_role`, `Student`, `TeacherOrAdmin` en `backend/app/api/deps.py`); un rol no permitido recibe 403.
- El docente solo ve las clases que enseña (`class_members`); otra clase da 404 (`services/world.py::_teacher_scope`). Un intento ajeno también da 404, para no revelar que existe.
- El admin ve todas las clases; en producción publicaría versiones de contenido validadas. La vista docente no se construyó: el RBAC se demuestra por la API.

## 7. IA sin depender de un proveedor

- Puerto `CoachProvider` (`backend/app/ai/ports.py`) con tres adaptadores: mock, Claude y una API compatible con OpenAI (Groq o xAI), elegidos con `COACH_PROVIDER` (`factory.py`).
- El prompt está versionado (`prompts/maya_feedback_v1.md`). La salida es JSON validado con Pydantic: la fortaleza y el desafío deben coincidir con los valores deterministas. Ante un error, un timeout o una salida inválida, se usa el mock.
- Cada feedback guarda `provider`, `model` y `prompt_version`; los SDK solo se importan en `app/ai` (hay un test). El LLM nunca toca puntaje, nivel ni desbloqueos. Falta un conjunto de evaluación fijo para comparar proveedores.

La visión del §7 del enunciado (feedback personalizado, acompañamiento, recordatorios y asistencia) y los costos estimados están en `docs/ai/AI_ARCHITECTURE.md`.

## 8. Con tres meses

1. **Banco de ítems y evaluación adaptativa**; bandas y blueprint como datos por misión, hasta C1.
2. **Speaking** con reconocimiento de voz; audio pregenerado para *listening*.
3. **Herramienta de autoría** que corra `backend/app/engine/validator.py` antes de publicar.
4. **Paneles docentes**: asignar misiones, progreso de la clase, exportar.
5. **Recordatorios y acompañamiento** desde `coach_memory`, con un job y el mismo puerto.
6. **Seguridad y operación**: refresh tokens, rate limit compartido, CSP, auditoría, privacidad de menores, pruebas de carga y la cola del coach.
