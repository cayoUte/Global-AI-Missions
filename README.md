# Global AI Missions

**Una historia que juegas en inglés y que, por dentro, es una evaluación.** Prototipo de la prueba técnica *Mini Global AI Assessment* (Full Stack Developer, Global AI).

*LONDON — 21:47. You have 18 minutes before the last train leaves.* El estudiante y **Maya**, su compañera de IA, tienen que llegar al andén antes de las 22:05. En el camino escucha un anuncio, lee un cartel, habla con un guardia y decide qué hacer. Nunca ve "Pregunta 3 de 10 · Listening": cada decisión es, por dentro, un ítem con nivel CEFR y habilidad, calificado en el servidor. La historia siempre sigue, acierte o no; el error cuesta minutos de historia, no una cruz roja. Al final envía la misión y recibe el **Mission Report**: primero los números que pide el enunciado (`A2 · The Last Train — 70%`, % por habilidad, aciertos, errores, nivel sugerido y su motivo), después la lectura de Maya y el diario de la noche. Maya recuerda al estudiante y en la siguiente visita lo saluda con lo que aprendió de él.

| English World (Leo, alumno veterano) | Un checkpoint dentro de la escena | Mission Report |
|---|---|---|
| ![English World](docs/img/english-world.png) | ![Mission Player](docs/img/mission-player.png) | ![Mission Report](docs/img/mission-report.png) |

---

## Para evaluadores

**Demo en línea:** [URL de Render — pendiente]. Con el plan gratuito de Render la primera carga tras un rato sin uso tarda alrededor de un minuto (el servicio "despierta").
**En local:** tres comandos con Docker, ver [Inicio rápido](#inicio-rápido-docker-3-comandos).

**Credenciales de prueba** (contraseña de demo, igual para las tres cuentas: `LastTrain2026!`). Con `DEMO_MODE=true` la pantalla de Check-in las muestra en el panel "Demo accounts".

| Cuenta | Quién | Qué muestra |
|---|---|---|
| `new@globalai.test` | Ana, estudiante | Primer encuentro con Maya. English World vacío → jugar *The Last Train* completa (10 ítems) → Submit mission → Mission Report → Progress. |
| `veteran@globalai.test` | Leo, estudiante | 4 intentos previos (generados con el estudiante simulado): saludo con memoria, "Maya's pick", tendencia 40 → 50 → 60 → 70 % en Progress, notas de Maya. |
| `teacher@globalai.test` | Ms. Clarke, profesora | Vista de profesor de solo lectura: su clase "Evening B1" con Ana y Leo (último resultado, % por habilidad, misiones jugadas, última actividad). Los permisos también se ven en la API (`/api/teacher/classes` 200 para ella, 403 para un estudiante, 404 para otra clase). |

**Documentos para leer** (en español):

- [docs/DECISIONS.md](docs/DECISIONS.md) — decisiones técnicas (máx. 2 páginas): stack, arquitectura, modelo de datos, protección de respuestas, escala, roles, IA y los próximos tres meses.
- [docs/INTERVIEW.md](docs/INTERVIEW.md) — respuestas preparadas a las 10 preguntas de la entrevista (versión PDF: [docs/INTERVIEW.pdf](docs/INTERVIEW.pdf)).
- [docs/ai/AI_ARCHITECTURE.md](docs/ai/AI_ARCHITECTURE.md) — Maya: feedback con LLM, proveedores intercambiables y hoja de ruta de IA.
- [docs/AI_USAGE.md](docs/AI_USAGE.md) — qué herramientas de IA se usaron para construir esto y qué hizo personalmente el candidato.
- [docs/qa/DEMO_SCRIPT.md](docs/qa/DEMO_SCRIPT.md) — guion de la demo de 10 minutos.

El resto de `docs/` (producto, contratos, diseño, QA, motor) son **notas internas de trabajo**, en inglés, escritas durante la construcción.

**Cómo cubre el enunciado:**

1. **Flujo completo:** login → dashboard (English World) → misión con 10 ítems (4 opción múltiple, 2 completar, 2 comprensión, 2 vocabulario) → Submit → puntaje global y por habilidad, aciertos/errores, nivel sugerido, registro del intento → Progress.
2. **Técnico:** React + FastAPI + PostgreSQL separados; preguntas y claves solo en el servidor (nunca viajan mientras el intento está abierto); JWT en cookie httpOnly; validación y errores uniformes; Docker, CI y 329 tests automatizados (297 de backend, 26 de frontend y 6 E2E).
3. **IA:** Maya da feedback educativo al terminar (mock determinista por defecto; Claude o cualquier API compatible con OpenAI, como Groq o Grok, por variables de entorno) y el documento de arquitectura explica cómo un LLM acompañaría al estudiante después.

---

## La evaluación: las 10 preguntas

Los ítems viven en [`content/missions/the-last-train/items.json`](content/missions/the-last-train/items.json) (nunca en el frontend) y su diseño está en [`docs/assessment/ASSESSMENT_SPEC.md`](docs/assessment/ASSESSMENT_SPEC.md). El nivel sube con el reloj de la historia.

| Id | Tipo | Habilidad | CEFR | Estímulo en la escena |
|---|---|---|---|---|
| q01 | multiple_choice | grammar | A1 | diálogo |
| q02 | multiple_choice | listening | A1 | anuncio por altavoz (audio) |
| q03 | comprehension | reading | A2 | aviso |
| q04 | vocabulary | vocabulary | A2 | diálogo |
| q05 | fill_blank | grammar | A2 | diálogo |
| q06 | fill_blank | grammar | B1 | diálogo |
| q07 | multiple_choice | listening | B1 | anuncio por altavoz (audio) |
| q08 | vocabulary | vocabulary | B1 | diálogo |
| q09 | multiple_choice | grammar | B2 | diálogo |
| q10 | comprehension | reading | B2 | mensaje de texto |

- **Totales:** 4 `multiple_choice` (2 grammar + 2 listening) · 2 `fill_blank` · 2 `comprehension` · 2 `vocabulary`. Niveles: A1 ×2, A2 ×3, B1 ×3, B2 ×2.
- **Puntaje** (determinista, solo en el servidor): global = aciertos / 10; por habilidad = aciertos / ítems de esa habilidad; aciertos + errores = 10 siempre (no hay "saltar"). Las pistas de Maya no cambian el puntaje.
- **Nivel sugerido:** banda por el % global (0–29 Pre-A1 · 30–49 A1 · 50–69 A2 · 70–84 B1 · 85–100 B2) con un tope por evidencia: para sugerir un nivel hay que acertar al menos la mitad de sus ítems; si no, baja un nivel. El reporte muestra la regla aplicada en una frase.
- Speaking existe en el modelo de datos pero no se mide en esta misión (el reporte lo dice).

---

## Inicio rápido (Docker, 3 comandos)

Requisitos: Docker con Compose v2 (Docker Desktop o Docker Engine) y Git.

```bash
git clone https://github.com/cayoUte/Global-AI-Missions.git && cd Global-AI-Missions
```

```bash
cp .env.example .env
docker compose up -d --build
```

Abre **http://localhost:8000** y entra con una de las cuentas de arriba.

La primera vez construye la imagen (unos minutos, según la conexión). El contenedor `api` espera a que PostgreSQL esté sano, aplica las migraciones, carga el contenido y los usuarios demo (idempotente) y sirve la API y el SPA en el mismo origen. `.env.example` trae valores locales que funcionan tal cual: coach `mock` (sin clave), `DEMO_MODE=true` y un `JWT_SECRET` solo para desarrollo.

```bash
docker compose ps                  # api y db en estado "healthy"
docker compose logs -f api         # migraciones, seed y peticiones
docker compose down                # parar (los datos se conservan)
docker compose down -v             # parar y borrar la base de datos
```

**Volver a los datos demo iniciales** (por ejemplo, para que Ana vuelva a ser un primer encuentro): `docker compose down -v` y luego `docker compose up -d --build`.

Puertos: la app en 8000 y PostgreSQL en **5433** del host (no 5432, para no chocar con un PostgreSQL instalado). Si están ocupados, cambia `API_HOST_PORT` o `POSTGRES_HOST_PORT` en `.env` (si cambias el de PostgreSQL, cambia también `DATABASE_URL`).

---

## Desarrollo local (sin el contenedor de la app)

Requisitos: Docker (solo para PostgreSQL), Python 3.12+ con [uv](https://docs.astral.sh/uv/), Node 22 y GNU make (en Windows, desde Git Bash). Cada `make` equivale a un comando visible en el [`Makefile`](Makefile).

```bash
cp .env.example .env
make install          # uv sync (backend) + npm ci (frontend)
make up               # PostgreSQL 16 en 127.0.0.1:5433, espera el healthcheck
make migrate          # alembic upgrade head
make seed             # contenido, usuarios demo e historial de Leo (idempotente)
```

Luego, en dos terminales:

```bash
make dev-backend      # FastAPI con recarga en http://127.0.0.1:8000 (Swagger en /api/docs)
```

```bash
make dev-frontend     # Vite en http://localhost:5173, con proxy de /api al backend
```

Abre **http://localhost:5173**. Si el contenedor `api` de Docker está corriendo, detenlo antes (`docker compose stop api`) porque usa el mismo puerto 8000. `make reset` borra la base, migra y siembra de nuevo. `make help` lista todos los comandos.

Usa `127.0.0.1`, no `localhost`, en `DATABASE_URL`: en algunas máquinas Windows `localhost` resuelve primero a IPv6 y la conexión se cuelga.

---

## Tests

| Qué | Comando | Resultado al 2026-09-25 |
|---|---|---|
| Backend: unitarios, API, motor, datos, IA, contratos (pytest) | `make test-backend` (o `cd backend && uv run pytest`) | 322 passed |
| Frontend (Vitest + Testing Library) | `make test-frontend` (o `cd frontend && npm test`) | 45 passed |
| E2E con Playwright sobre la app real | `make e2e` | 10 passed, 1 skipped (un test solo de móvil) |
| Lint, formato y tipos (ruff, ESLint, Prettier, tsc) | `make lint` | limpio |

- Los tests de backend que usan PostgreSQL necesitan `make up` (base `gam_test`, creada por el script de inicio de compose). Sin base de datos se **omiten** con el motivo impreso, y el resto pasa.
- E2E: la primera vez, `cd frontend && npx playwright install chromium`. `make e2e` compila el SPA, recrea una base desechable `gam_e2e`, la migra y la siembra, levanta FastAPI en `127.0.0.1:8765` y juega la misión con el teclado a 1280 px y 360 px. Nunca toca la base demo `gam`.
- `make test E2E=1` corre todo.
- **CI** ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)), en cada push y pull request: ruff + pytest con un servicio PostgreSQL 16 (falla si los tests de base de datos se omiten), lint/typecheck/format/Vitest/build del frontend, E2E con Playwright y un job que construye la imagen Docker y la arranca con una URL `postgresql://` como la de Render.

Qué se prueba primero y por qué: integridad del puntaje, fuga de claves de respuesta, manipulación desde el cliente, propiedad de los intentos y roles, invariantes del motor en los 1.024 caminos posibles, concurrencia y reanudación.

---

## IA: Maya

- **Durante la misión no hay LLM.** Un planificador determinista (búsqueda en el grafo de la historia, heurística = minutos mínimos hasta un final) decide si Maya calla, da una pista de estrategia o rescata una vez.
- **Después de calificar**, una sola llamada a un LLM escribe la interpretación de Maya, su nota de memoria y el próximo saludo. Se ejecuta después del commit de la calificación, con 8 s de presupuesto; cualquier fallo sirve el mock determinista. **El LLM nunca cambia puntaje, nivel ni desbloqueos**, y nunca ve claves de un intento abierto.
- Proveedor por variable de entorno (`COACH_PROVIDER`); el pie del reporte dice cuál escribió el feedback ("Written by Maya using …" o "from her notebook").

| `COACH_PROVIDER` | Qué usa | Variables |
|---|---|---|
| `mock` (por defecto) | plantillas + memoria, sin red ni clave | — |
| `openai_compatible` | Groq, xAI Grok o cualquier API compatible con OpenAI | `OPENAI_COMPAT_BASE_URL`, `OPENAI_COMPAT_API_KEY`, `OPENAI_COMPAT_MODEL`, opcional `OPENAI_COMPAT_LABEL` |
| `anthropic` | Claude, con el SDK oficial | `ANTHROPIC_API_KEY`, opcional `ANTHROPIC_MODEL` |

Para activar Groq, xAI Grok o Claude, descomenta el bloque correspondiente en tu `.env` (en [`.env.example`](.env.example) están los ejemplos completos de Groq y xAI con su URL base) y reinicia la app (`docker compose up -d` o `make dev-backend`). Comprueba la llamada real, sin fallback, con:

```bash
cd backend && uv run python scripts/coach_smoke.py
```

Imprime proveedor, modelo, latencia, tokens y el JSON validado, y termina con error si la clave, el modelo o la salida fallan. Nunca imprime la clave. **Estado:** los tres adaptadores tienen tests con clientes falsos, pero desde el entorno de construcción no se pudo hacer ninguna llamada real a un LLM (la red lo bloqueaba); esa verificación queda para `coach_smoke.py` con una clave real. Detalle y costos: [docs/ai/AI_ARCHITECTURE.md](docs/ai/AI_ARCHITECTURE.md).

---

## Stack (y por qué)

Detalle y alternativas descartadas en [docs/DECISIONS.md](docs/DECISIONS.md).

| Capa | Elección | Por qué, en una línea |
|---|---|---|
| Frontend | React 19 + TypeScript 5.9 + Vite | ecosistema estándar, tipado de punta a punta con los tipos generados desde OpenAPI. |
| UI | Tailwind CSS v4 + Framer Motion | tokens de diseño en CSS y transiciones de escena sin una librería de componentes pesada. |
| Estado de servidor | TanStack Query + React Router | caché y reintentos de la API sin estado global a mano. |
| Audio | Web Speech API (`speechSynthesis`) | ítems de escucha sin archivos de audio en el MVP (con texto de respaldo si no hay voz). |
| Backend | Python 3.12 + FastAPI + Pydantic v2 | validación estricta de entrada (`extra="forbid"`) y OpenAPI gratis; Python conviene al motor de búsqueda y a la IA. |
| Persistencia | PostgreSQL 16 + SQLAlchemy 2 + Alembic | relacional con invariantes en la base (índices únicos parciales, CHECK, bloqueos de fila) y JSONB para el grafo versionado. |
| Auth | JWT HS256 en cookie httpOnly SameSite=Lax + argon2 | el token nunca toca JavaScript; roles `student`, `teacher`, `admin`. |
| IA | puerto `CoachProvider` + adaptadores (mock, Claude, compatible con OpenAI) | la plataforma no depende de un proveedor; el mock es el default y el fallback. |
| Tests | pytest, Vitest + Testing Library, Playwright | una herramienta por capa, todas en CI. |
| Entrega | Docker multi-stage, Docker Compose, GitHub Actions, Render | la misma imagen en local y en el deploy; un solo origen, sin CORS. |

---

## Arquitectura

```
 Navegador (React SPA)                                   un solo origen: FastAPI sirve /api y el SPA
   │  cookie httpOnly gam_session · solo ve StateView (sin claves, sin aristas, sin nodos futuros)
   ▼
 FastAPI  app/api/routers ─▶ app/services ─────────────▶ app/repositories ─▶ PostgreSQL 16
   │  auth · world · attempts   attempts, grading,           SQLAlchemy 2        usuarios, misiones versionadas
   │  progress · teacher        leveling, state_view,                            (JSONB), intentos, pasos,
   │                            report, world                                    respuestas, feedback, memoria
   │                               │            │
   │                               ▼            ▼
   │                        app/engine      app/ai  (después del commit de la calificación)
   │                        grafo, RESULT,  CoachProvider ─┬─ mock (por defecto y fallback)
   │                        heurística h,                  ├─ anthropic (Claude)
   │                        Maya planner,                  └─ openai_compatible (Groq, xAI…)
   │                        validador, simulador
   ▼
 content/  catalog.json · missions/the-last-train/{items.json, mission.json}  → validados y sembrados
```

- **Un intento es una búsqueda:** cada paso persistido es un nodo (estado, padre, acción, costo); seguir los punteros al padre desde el final **es el Diario** del reporte. Motor explicado en [backend/app/engine/README.md](backend/app/engine/README.md).
- **Submit en dos fases:** (1) calificar y fijar nivel bajo bloqueo de fila y commit; (2) el coach, fuera de toda transacción. El reporte siempre se muestra, aunque el LLM falle.
- **Seguridad:** las claves nunca salen del servidor mientras el intento está abierto; el cliente nunca envía puntajes ni aciertos; cada checkpoint se bloquea al primer envío (un segundo envío da 409); los intentos de otro usuario dan 404; un solo intento abierto por estudiante y misión (recargar o perder la conexión retoma el mismo).
- IA: [docs/ai/AI_ARCHITECTURE.md](docs/ai/AI_ARCHITECTURE.md) · decisiones: [docs/DECISIONS.md](docs/DECISIONS.md).

API (Swagger en `/api/docs`): `GET /api/health`, `GET /api/config`, `POST /api/auth/login|logout`, `GET /api/auth/me`, `GET /api/world`, `POST /api/missions/{id}/attempts`, `GET /api/attempts/{id}`, `POST /api/attempts/{id}/advance|answer|submit`, `GET /api/attempts/{id}/report`, `GET /api/me/progress`, `GET /api/teacher/classes`, `GET /api/teacher/classes/{id}/progress`, `GET /api/missions/{id}/simulate` (solo modo demo).

---

## Deploy en Render (plan gratuito)

El repositorio trae un Blueprint, [`render.yaml`](render.yaml): un servicio web Docker (la misma imagen que en local) y un PostgreSQL 16 gestionado, ambos en plan **free**.

1. Sube el repositorio a GitHub (o usa el tuyo) y entra en [dashboard.render.com](https://dashboard.render.com).
2. **New → Blueprint**, conecta el repositorio y elige la rama. Render lee `render.yaml` y muestra el servicio `global-ai-missions` y la base `global-ai-missions-db`.
3. Render pide los valores secretos: pega tu clave de Groq en `OPENAI_COMPAT_API_KEY` (se crea gratis en [console.groq.com](https://console.groq.com), sin tarjeta) y deja vacías las `ANTHROPIC_*`. **Apply**. Sin clave, Maya usa el mock.
4. Espera el build y el primer arranque (el entrypoint convierte la URL `postgresql://` de Render a `postgresql+psycopg://`, migra y siembra). Comprueba `https://<tu-servicio>.onrender.com/api/health` → `{"status":"ok"}` y entra con `new@globalai.test` / `LastTrain2026!`.
5. Comprueba la IA real: juega una misión y, al enviarla, el pie del reporte debe decir "Written by Maya using Groq · Llama". Si dice "from her notebook (offline feedback)", Groq falló y se usó el mock: revisa en **Logs** la línea `coach.openai_compatible` o el error (401 clave, 404 modelo, 429 límite del plan gratuito). Para cambiar de modelo o usar Claude: **Environment** → edita `OPENAI_COMPAT_MODEL` (o `COACH_PROVIDER=anthropic` y sus variables) → **Save changes**.
6. Copia la URL pública en la sección [Para evaluadores](#para-evaluadores).

Ya configurado en el Blueprint: `JWT_SECRET` aleatorio generado por Render, `COOKIE_SECURE=true` (Render sirve solo HTTPS), `DEMO_MODE=true`, `COACH_PROVIDER=openai_compatible` con Groq (URL base, modelo y etiqueta; la clave la pones tú), health check en `/api/health` y la base accesible solo desde la red privada de Render (`ipAllowList: []`).

**Límites del plan gratuito:** el servicio web se duerme tras ~15 minutos sin tráfico y la siguiente visita tarda alrededor de un minuto en despertarlo; la base PostgreSQL gratuita **caduca a los 30 días** de creada (hay que recrearla o pasar a un plan de pago); 512 MB de RAM.

**Reiniciar los datos demo en Render** (Ana vuelve a ser primer encuentro). El seed es idempotente pero no borra intentos, así que hay que vaciar la base y reiniciar el servicio:

1. En la base, **Networking/Access Control**: agrega tu IP temporalmente y copia la **External Database URL**.
2. `psql "<External Database URL>" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"`
3. En el servicio web, **Manual Deploy → Restart service** (o **Deploy latest commit**): al arrancar migra y siembra de nuevo.
4. Quita tu IP del Access Control.

---

## Variables de entorno

Todas documentadas en [`.env.example`](.env.example); `backend/app/core/config.py` es el único lector.

| Variable | Por defecto en `.env.example` | Para qué |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://gam:gam@127.0.0.1:5433/gam` | URL de SQLAlchemy con psycopg 3. En Docker y en Render la fija compose / el Blueprint. |
| `JWT_SECRET` | valor solo para desarrollo | clave HS256, mínimo 32 caracteres (si no, la app no arranca). En Render, generada. |
| `JWT_TTL_MINUTES` | 60 | duración de la sesión. |
| `COOKIE_SECURE` | `false` | `true` en cualquier deploy con HTTPS. |
| `COACH_PROVIDER` | `mock` | `mock`, `anthropic` u `openai_compatible` (cualquier otro valor → mock). |
| `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` | comentadas | solo con `anthropic`. |
| `OPENAI_COMPAT_BASE_URL`, `OPENAI_COMPAT_API_KEY`, `OPENAI_COMPAT_MODEL`, `OPENAI_COMPAT_LABEL` | comentadas | solo con `openai_compatible` (Groq, xAI…). |
| `DEMO_MODE` | `true` | muestra las cuentas demo en el Check-in. El valor seguro por defecto de la app es `false`. |
| `POSTGRES_HOST_PORT`, `API_HOST_PORT` | 5433, 8000 | puertos del host en docker compose. |
| `PORT` | 8000 | puerto de uvicorn dentro del contenedor (Render lo fija). |
| `SPA_DIST_DIR` | `frontend/dist` si existe | carpeta del SPA compilado que sirve FastAPI. |
| `FORWARDED_ALLOW_IPS` | solo loopback (valor de uvicorn) | desde qué proxies se aceptan `X-Forwarded-For/-Proto`. |

`.env` nunca se sube al repositorio (está en `.gitignore`); las claves reales solo van en `.env` o en el panel de Render.

---

## Estructura del proyecto

```
├── backend/                 FastAPI (Python 3.12, uv)
│   ├── app/api/             routers, dependencias (auth, roles), middleware, SPA
│   ├── app/services/        ciclo del intento, calificación, nivel, StateView, reporte, mundo, progreso
│   ├── app/engine/          motor del grafo: RESULT, heurística, Maya planificadora, validador, simulador
│   ├── app/ai/              puerto del coach, adaptadores (mock, Claude, compatible con OpenAI), prompt versionado
│   ├── app/models/, app/repositories/   SQLAlchemy 2 y acceso a datos
│   ├── alembic/, seed/      migraciones y seed idempotente (usuarios demo, historial de Leo)
│   ├── scripts/             validación de contenido, export de OpenAPI, smoke test del LLM
│   └── tests/               pytest
├── frontend/                React 19 + TypeScript + Vite + Tailwind v4
│   ├── src/features/        auth, world, mission (player), report, progress, teacher, replay
│   └── e2e/                 Playwright
├── content/                 catálogo y misión: items.json (evaluación) y mission.json (historia)
├── docs/                    documentos para evaluadores (español) y notas internas de trabajo
├── docker/                  entrypoint del contenedor e init de PostgreSQL
├── Dockerfile, docker-compose.yml, render.yaml, Makefile, .env.example
└── .github/workflows/ci.yml
```

---

## Limitaciones conocidas

- **El guion de escucha llega al navegador:** los ítems de listening usan `speechSynthesis`, así que el texto del anuncio viaja al cliente (sin la respuesta). En producción: audio pregenerado detrás de URLs firmadas. Si el dispositivo no tiene voz en inglés, el anuncio se muestra como texto para que la historia no se bloquee.
- **Repetir la misma misión no es una reevaluación segura:** tras leer el reporte, el estudiante conoce los ítems. "Play again" es práctica; en producción haría falta un banco de ítems con variantes.
- **El límite de intentos de login** (5 por minuto por IP y email) vive en memoria de cada proceso: con varias instancias cuenta por separado y se reinicia al redesplegar (en producción: Redis o el API gateway). En Render, mientras `FORWARDED_ALLOW_IPS` no incluya el proxy de Render, todas las peticiones llegan con la IP del proxy y el límite queda, en la práctica, por email.
- **Vista de profesor de solo lectura:** muestra sus clases y el progreso de cada alumno, sin entrar al reporte individual ni acciones (asignar, editar, exportar quedan para producción).
- **Replay simulado solo en modo demo:** desde el English World, "Watch a simulated run" abre `/replay`, donde se elige un nivel (A1, A2, B1, B2, A2 weak listening) y una semilla. Muestra el camino, el reloj, understood/missed por checkpoint, las decisiones y el ánimo de Maya y el final; nunca preguntas ni respuestas (`GET /api/missions/{id}/simulate`, 404 con `DEMO_MODE=false`). El mismo estudiante simulado (`uv run python -m app.engine.cli simulate --profile B1`) generó el historial de Leo.
- **Una sola misión jugable.** Las otras cuatro del catálogo muestran su regla de desbloqueo o "Maya is preparing this mission".
- **Speaking** no se mide en esta misión.
- **Fuentes desde Google Fonts** (CDN); sin conexión se ven las fuentes de respaldo. Autohospedarlas queda para producción.
- **IA real sin verificar en vivo** desde el entorno de construcción (ver [IA: Maya](#ia-maya)).
- **Demo en Render con plan gratuito:** arranque en frío lento y base de datos que caduca a los 30 días.

---

## Licencia

[MIT](LICENSE).
