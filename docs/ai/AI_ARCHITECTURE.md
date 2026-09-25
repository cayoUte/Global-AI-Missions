# Arquitectura de IA — Maya, la coach

> Responde al §7 del enunciado: feedback educativo tras la evaluación y cómo Claude u otro LLM impulsaría feedback personalizado, acompañamiento, recordatorios y asistencia al aprendizaje, sin acoplar la plataforma a un proveedor.

## 1. Planificador y narrador: dos cerebros separados

- **Planificador (durante la misión, sin LLM).** `backend/app/engine` modela la misión como un problema de búsqueda. Maya decide *qué hace* (callar, dar una pista de estrategia, rescatar una vez) con una heurística admisible (`h` = minutos mínimos hasta un final). Es determinista, gratis, instantáneo y testeable. El LLM nunca controla el flujo.
- **Narrador (después de calificar, con LLM).** `backend/app/ai` decide *cómo habla* Maya en el reporte y *qué recuerda*. Se ejecuta en la fase 2 de `submit`, **después del commit de la calificación** y sin transacción ni lock abiertos. Recibe puntajes ya guardados: no puede cambiar puntaje, nivel ni desbloqueos.

## 2. El puerto de proveedor

```
submit ─ fase 1: calificar + nivel (COMMIT) ─ fase 2: coach ──▶ CoachProvider.generate(CoachContext) → CoachFeedback
                                                               ├─ anthropic_provider.py          (Claude, SDK oficial)
                                                               ├─ openai_compatible_provider.py  (Groq, xAI Grok u otra API compatible con OpenAI, httpx)
                                                               └─ mock_provider.py               (plantillas + memoria, sin red)
```

- `ports.py`: `CoachContext` (entrada), `CoachFeedback` (salida JSON estricta: `summary`, `strength`, `challenge`, `recommendation`, `next_mission_id`, `memory_note`, `next_greeting`) y el `Protocol` `CoachProvider`. Pydantic valida códigos de habilidad, longitudes por campo, palabras prohibidas por el personaje (nunca "wrong", "fail", XP…), y contra el contexto: `strength`/`challenge` deben repetir los valores deterministas y `next_mission_id` debe ser uno de los candidatos.
- `factory.py`: elige por `COACH_PROVIDER` (`mock` por defecto | `anthropic` | `openai_compatible`). Sin clave, sin URL base o sin modelo, con un valor desconocido o si el constructor falla → mock (con un aviso en el log).
- `service.py`: `build_context`, `generate_feedback` (presupuesto total de **8 s**; timeout, error de API, JSON malformado, rechazo o validación fallida → mock con `status: "fallback"`) y `update_memory` (+1 sesión, últimas 5 notas, próximo saludo).
- El reporte siempre se muestra: si no hay fila de feedback, se renderiza el mock. `feedback_source.provider_label` ("Claude", "Groq", "Grok (xAI)" o "Maya's notebook") lo pone el adaptador; la UI nunca escribe el nombre del proveedor.
- Cada feedback guarda `provider`, `model`, `prompt_version` y `latency_ms`. El prompt es un archivo versionado (`prompts/maya_feedback_v1.md`).

**Cambiar de modelo o de proveedor.** Cambiar Claude por otro modelo de Claude = `ANTHROPIC_MODEL`. Otro proveedor = un archivo `<nombre>_provider.py` que implemente `generate(context) → CoachFeedback` (reutilizando `prompting.py`: prompt, esquema JSON y parser), una línea en `factory.PROVIDERS` y `COACH_PROVIDER=<nombre>`. El SDK del proveedor solo se importa dentro de `app/ai` (hay un test que lo verifica).

**La prueba: tres adaptadores, un puerto.** `openai_compatible_provider.py` se agregó así, sin tocar nada fuera de `app/ai` salvo las variables en `config.py` y `.env.example` (CR-009). Un solo archivo sin SDK nuevo (httpx) habla con cualquier API compatible con OpenAI: `POST {base_url}/chat/completions` con el **mismo prompt versionado** y el mismo mensaje delimitado que Claude, modo JSON (`response_format: json_object`), temperatura baja, `max_tokens` acotado, timeout de 7 s sin reintentos y la **misma validación Pydantic**. Como no todas estas APIs aceptan un esquema JSON, la salida no viene restringida por enums: si el modelo cambia una habilidad o inventa una misión, la validación lo rechaza y se sirve el mock. Cambiar de proveedor es solo configuración:

| Proveedor | `COACH_PROVIDER` | `OPENAI_COMPAT_BASE_URL` | `OPENAI_COMPAT_MODEL` (ejemplo) |
|---|---|---|---|
| Groq (capa gratuita, demo en vivo) | `openai_compatible` | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| xAI Grok | `openai_compatible` | `https://api.x.ai/v1` | `grok-4-fast-non-reasoning` |

Más `OPENAI_COMPAT_API_KEY` (la clave del proveedor, solo en `.env`) y, opcional, `OPENAI_COMPAT_LABEL` (el pie del reporte; por defecto "Groq", "Grok (xAI)" o "AI coach" según el host). No hay modelo por defecto: los ids cambian, hay que revisar la lista de modelos del proveedor. La llamada real se verifica con `cd backend && uv run python scripts/coach_smoke.py`: llama al proveedor configurado **directamente** (sin fallback), imprime proveedor, modelo, latencia, tokens y el JSON validado, y termina con error si la clave, el modelo o la salida fallan o si tarda más de 8 s. Nunca imprime la clave.

## 3. Seguridad y privacidad

- Al LLM solo le llegan: nombre de pila (saneado), nivel, puntajes, fortaleza/desafío, ítems fallados con su explicación (el intento ya está cerrado), resumen del recorrido, notas de memoria y misiones candidatas. Nunca emails, ids ni claves de respuesta de un intento abierto.
- Anti-inyección: todo texto que proviene del usuario (nombre, notas, respuestas escritas) va como JSON dentro de `<mission_result>`, con `<` y `>` escapados; el prompt de sistema dice que ese bloque es dato, no instrucción. La salida se valida igual: aunque el modelo "obedezca" algo, no puede cambiar habilidades ni misión (enums en el esquema + Pydantic) ni usar lenguaje prohibido.

## 4. Lo que un LLM haría después (hoja de ruta)

**Feedback personalizado.** Ya implementado: Claude escribe el reporte adaptado al nivel CEFR (frases cortas en A1–A2) y, desde la segunda sesión, menciona una observación concreta de su cuaderno ("You usually do well with vocabulary. You still hesitate when someone speaks quickly."). El siguiente paso es darle las respuestas escritas del estudiante (como dato delimitado) para comentar patrones de error, y evaluar la calidad con un conjunto de casos fijo antes de cambiar de prompt o de modelo.

**Acompañamiento.** La memoria de Maya (`coach_memory`: sesiones, últimas 5 notas, próximo saludo) convierte cada misión en una relación: el saludo del English World sale de esa memoria y la voz cambia por etapa (primer encuentro, conociéndote, compañera habitual). Con más misiones, un resumen periódico de la memoria (generado por el LLM, validado igual) mantendría el contexto corto y útil.

**Recordatorios.** Un job programado (cron o cola) lee `coach_memory` y el progreso, y pide al LLM un mensaje breve con el mismo puerto y las mismas reglas ("Tonight, listen for the numbers first."). Como no es urgente, puede ir por la Batch API (≈50 % del costo) y reutilizar el mock si el LLM falla. El envío (email/push) queda fuera del LLM y respeta las preferencias del estudiante.

**Asistencia al aprendizaje.** Un modo de práctica guiada **solo fuera de intentos abiertos** y **nunca con claves de respuesta** de un intento en curso, coherente con la regla de "sin chat libre" (PRODUCT §8): ejercicios cortos sobre la habilidad de desafío, generados o explicados por el LLM a partir de ítems ya enviados y de un banco de ítems de práctica distinto al de evaluación.

## 5. Costo y latencia

- Controles: un solo llamado por intento; presupuesto total de 8 s (timeout HTTP de 7 s, sin reintentos); `max_tokens` = 1500; `effort: "low"` (Claude) o temperatura 0,3 (compatibles con OpenAI); salida JSON validada (sin reintentos por formato); fallback determinista gratuito. Se registran latencia y tokens de entrada/salida en los logs (`coach.anthropic …` / `coach.openai_compatible host=… input_tokens … output_tokens … latency_ms`).
- Estimación por feedback (≈2.000–2.500 tokens de entrada: prompt de sistema ≈1.300 + contexto ≈800; ≈300–550 de salida): **Claude Opus 5** (modelo por defecto, $5/$25 por millón) ≈ **US$0,02–0,03**; **Claude Haiku 4.5** ($1/$5) ≈ **US$0,005** con `ANTHROPIC_MODEL=claude-haiku-4-5`. Con 100.000 estudiantes y 4 misiones al mes: ≈ US$8.000–10.000/mes con Opus o ≈ US$2.000/mes con Haiku; el mock cuesta cero. **Groq**: US$0 dentro de la capa gratuita (límites por minuto y por día; un 429 cae al mock) y, en la capa de pago, del orden de décimas de centavo por feedback con un modelo Llama de 70B; también suele ser el más rápido. Verificar precios vigentes en la página de cada proveedor.
- A escala: la fase 2 pasa a una cola (el reporte ya se renderiza sin fila de feedback), cache de prompt cuando el prefijo supere el mínimo cacheable, Batch API para recordatorios y un límite de gasto por estudiante.

Ejemplos reales de entrada y salida: `docs/ai/samples/new_student.json` (Ana, primera sesión) y `docs/ai/samples/veteran.json` (Leo, quinta sesión). Se regeneran con `cd backend && uv run python -m app.ai.samples` (incluye el LLM configurado —Claude, Groq o Grok— si su clave está en `.env`).
