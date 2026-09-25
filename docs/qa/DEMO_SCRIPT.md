# GUION DE LA DEMO (10 minutos) — Global AI Missions

> Responsable: `qa-engineer`. Sigue la forma de `docs/product/PRODUCT.md` §12. El contenido de la app se cita en inglés, tal como aparece en pantalla.
> Secuencia de respuestas verificada el 2026-09-25 sobre una base recién sembrada (vía API y con el E2E): 9 de 10, **90 %**, nivel **B2**, final **Made It**, siguiente misión **Night Radio**.
> Ensayo con cronómetro en G3: pendiente (ver `CHECKLIST.md`, M-13).

## 0. Preparación (antes de que entren los evaluadores)

1. `make reset` — base de datos limpia: Ana (`new@`) debe ser un **primer encuentro**. Cada ensayo la "gasta"; repetir `make reset` después de ensayar.
2. Arrancar la app como indica el README (FastAPI sirviendo el SPA en un solo origen) y abrir **Chrome** a 1280 px o más, zoom 110 %, en una ventana sin extensiones.
3. Comprobar la voz sin tocar la misión: en la consola de DevTools, `speechSynthesis.getVoices().filter(v => v.lang.startsWith('en')).length` debe ser > 0. Si es 0, la demo sigue igual: el checkpoint de escucha muestra el anuncio escrito ("Audio isn't available on this device"), y se explica como limitación documentada (PD-014).
4. Tener a mano, en otra pestaña cerrada o en un bloc de notas, estas URLs (se usan en el minuto 9:30):
   - `/api/teacher/classes`
   - `/api/teacher/classes/00000000-0000-4000-8000-000000000000/progress`
   - `/api/world`
5. DevTools cerrado al empezar. Volumen del portátil encendido.
6. Contraseña de las tres cuentas: `LastTrain2026!` (también aparece en el panel "Demo accounts" de la pantalla de Check-in, porque `DEMO_MODE=true`).

Ojo: el login tiene un límite de 5 intentos por minuto por email. Si se equivoca la contraseña varias veces, esperar 60 s.

## 1. 0:00–0:45 · Ana entra (login, dashboard, catálogo)

**Hacer**
- Pantalla **Check-in**: en el panel "Demo accounts", pulsar **Use this account** en `new@globalai.test` (Ana) y luego **Check in** (o Enter).
- Aterriza en el **English World**: "Welcome, Ana." y el saludo de primer encuentro de Maya: *"Hi, I'm Maya. Tonight we have one job: get you on the last train home. Ready when you are."*
- Señalar el tablero: *The Last Train* disponible y las otras cuatro misiones bloqueadas con su pista ("Opens after your first Mission Report on The Last Train."). El resumen de progreso vacío: "Your story starts tonight…".

**Decir**
- "Esto es un assessment de inglés de 10 ítems, pero el alumno no ve 'pregunta 3 de 10': ve una historia. Por dentro, cada decisión es un ítem con nivel CEFR y skill."
- "El login es un JWT en cookie httpOnly; el frontend nunca toca el token."

## 2. 0:45–5:30 · La misión completa (10 ítems, un error deliberado, un checkpoint de escucha)

**Hacer**: **Start mission**. Avanzar con **Continue** (o Enter) en las escenas; si el texto aún se está escribiendo, el primer Enter lo completa y el segundo avanza. En cada checkpoint: elegir con clic o con la tecla 1–4 y pulsar **Confirm** (o Enter). En los huecos, escribir y Enter.

| # | Lugar (en pantalla) | Maya dice (inicio) | Elegir | Nota para el presentador |
|---|---|---|---|---|
| 1 | Station concourse | "Let's ask her. A short, polite question…" | **1 · Is** | Gramática A1. "Select, then Confirm: un misclick no cuesta un checkpoint." |
| 2 | Station concourse | "That's the announcer. Let's catch every word…" | Pulsar **Listen** (o L). Luego **1 · Platform 5** ← **error deliberado** | Es el checkpoint de **escucha** (A1). El anunciador dice 7. Maya reacciona: *"Hm. There were two numbers in that. Let's make sure we have ours."* y la escena se desvía a **The far platform**: el reloj salta de 17 a **14 min**. "La historia sigue: nunca decimos 'incorrecto', ni rojo, ni sonido de fallo. El error cuesta minutos de historia, no humillación." |
| 3 | Ticket hall | "The office is closed. Let's see what the notice says…" | **2 · From the machines next to the main entrance** | Comprensión lectora A2 (el cartel es un objeto del mundo). |
| 4 | Ticket machines | "So many buttons…" | **1 · A single** | Vocabulario A2. |
| 5 | Ticket barriers | "He's pointing at a sign. Let's say sorry…" | escribir **didn't see** | Fill-in-the-blank A2. "La normalización (mayúsculas, espacios, apóstrofo curvo) está en una sola función del servidor." |
| 6 | The far gates | "This station really likes hiding our platform." | escribir **have been looking** | Fill-in-the-blank B1. |
| 7 | Passage to the platforms | "It's about our train again…" | **1 · The barriers were out of order…** | Escucha B1 (se puede pulsar Listen otra vez: repeticiones ilimitadas, PD-013). |
| 8 | Side gate, platform 7 | "Look who it is. Our friend from the barriers." | **1 · Wait for a moment.** | Vocabulario B1. |
| 9 | Platform 7 | "Catch your breath first. Then answer her." | **1 · had left** | Gramática B2. |
| 10 | At the train door | "Sam writes a lot. Let's read the whole thing, calmly." | **2 · Go to the café on George Street…** | Comprensión B2. |

Final: **Made It**, "21:59 · 6 min to departure", Maya: *"We made it! And you got us here."* — sin números en el final (PD-004).

**Decir durante la misión** (elegir 2–3, sin frenar el ritmo)
- "El reloj de la historia sustituye al contador de preguntas: solo avanza por el coste del camino."
- "El grafo está trenzado: los 1.024 caminos posibles visitan los mismos 10 checkpoints en el mismo orden, con la distribución exigida (4 opción múltiple, 2 huecos, 2 comprensión, 2 vocabulario). Lo prueba un test que enumera todos los caminos."
- "Maya es un planificador: con un A* inverso sabe cuántos minutos faltan como mínimo; si el margen baja de 3 da una pista de estrategia, y si un error haría perder el tren, puede rescatar una sola vez. El LLM no controla nada de esto."
- Si la voz falla: "Sin voz inglesa en el dispositivo, el anuncio se muestra escrito y la misión sigue; en producción serían audios pregenerados."

## 3. 5:30–7:00 · Submit y Mission Report

**Hacer**: **Submit mission** ("Maya is reading your Diary…"). En el informe, sin hacer scroll al principio, señalar de arriba abajo:
- Encabezado **`B2 · The Last Train — 90%`** (el formato del enunciado), **Global score 90%**, **Correct 9**, **Incorrect 1**.
- **Result per skill**: Grammar 100 % (4 of 4), Listening 50 % (1 of 2), Reading 100 % (2 of 2), Vocabulary 100 % (2 of 2); "Speaking isn't measured in this mission yet."
- **Suggested level** B2 con su regla: *"90% points to B2. B2 needs 1 of 2 B2 checkpoints — you had 2 — so your suggested level is B2."*
- **Attempt record**: Attempt 1, fecha, ending Made It, story-minutes 12, Maya's shortcut Not used, Hints 0.
- Bajar: interpretación de Maya ("To practise next: Listening"), el pie **"About this feedback: Written by Maya from her notebook (offline feedback)."**, la tarjeta **"Maya has prepared your next mission" → Night Radio** (listening), el **Diary** con etiquetas tipo · skill · nivel, y **Checkpoints to revisit**: q02 con tu respuesta "Platform 5", la correcta "Platform 7", la explicación y la transcripción del anuncio.

**Decir**
- "Toda la nota se calcula en el servidor, en una transacción, y es idempotente: dos submits concurrentes dan un único informe (hay test con PostgreSQL real)."
- "La respuesta correcta solo aparece ahora, con el intento cerrado."
- "El feedback lo escribe Maya con Claude si hay API key; si el proveedor falla, tarda más de 8 s o devuelve algo inválido, cae a un mock determinista y el pie lo dice con honestidad. El LLM corre después de calificar: nunca cambia nota, nivel ni desbloqueos."
- Volver al **English World**: la tarjeta *Night Radio* lleva la marca **Maya's pick**, y el saludo ya viene de la memoria.
- (Copiar la URL del informe de Ana: se usa en el paso 4.)

## 4. 7:00–8:30 · Leo, el alumno veterano (memoria, progreso, notas)

**Hacer**
- **Check out** → Check-in con `veteran@globalai.test` (Leo).
- English World: saludo de memoria *"Welcome back, Leo. Four nights in London now. Your reading is steady. Tonight, listen for the numbers first."*; **Maya's pick** en *Night Radio*; resumen: 4 misiones, último `A2 · The Last Train — 70%`.
- **See your progress** → **Progress**:
  - **Attempt history** (más reciente arriba): 40 % A1 (The Night Bus) → 50 % A2 (Made It Together, con rescate) → 60 % A2 → 70 % A2: la tendencia se lee bajando por las columnas de cada skill; Listening se queda baja.
  - **Your English today**: Grammar 75, Listening 33, Reading 67, Vocabulary 50 — "Based on your last 3 missions."
  - **Maya's notes**, la más reciente arriba (p. ej. "Strong in reading; listening needs practice (A2, 70%). Caught the last train.").
- (Opcional, 10 s) Pegar la URL del informe de Ana estando como Leo → **"We couldn't find this Mission Report."** (el intento de otro alumno es 404, no 403).

**Decir**
- "El historial de Leo lo generó el simulador de alumno con el perfil A2 con escucha débil; el perfil es el % por skill de los últimos 3 intentos, calculado por consulta, no almacenado."
- "La memoria de Maya (notas y saludo) es lo que Claude recibe la próxima vez: acompañamiento real, sin datos personales más allá del nombre."

## 5. 8:30–9:30 · DevTools: no viajan claves; recargar retoma

**Hacer**
- Como Leo, en *The Last Train* pulsar **Play again**; abrir DevTools → **Network** (filtro Fetch/XHR); **Continue** hasta el primer checkpoint.
- Abrir la respuesta de `attempts/…` o `advance`: el `StateView` trae prompt y opciones **sin** `is_correct`, `correct_option_id`, `accepted`, `explanation`, `hint`, `skill` ni `cefr`. Confirmar una opción y abrir la respuesta de `answer`: solo `{ maya_line, state }`.
- Buscar en Network (Ctrl+F) `correct_option_id` → 0 resultados.
- Pulsar **F5**: vuelve al mismo nodo, mismo reloj, el checkpoint contestado sigue bloqueado.

**Decir**
- "El cliente solo ve el nodo actual; la función de transición, la única que conoce las claves, vive en el servidor. Un test recorre misiones completas y escanea recursivamente cada respuesta, incluidas las de error 409."
- "Si se corta la conexión, el estado está en el servidor: reload, otra pestaña u otro dispositivo continúan en el mismo punto. Un Confirm repetido recibe 409 con el estado real y la UI se resincroniza en silencio."
- Trade-off honesto: "el guion de escucha sí llega al navegador porque usamos speechSynthesis; en producción, audio pregenerado con URLs firmadas."

## 6. 9:30–10:00 · Roles (teacher@ y API 403/404)

**Hacer**
- **Check out** → Check-in con `teacher@globalai.test` (Ms. Clarke): vista de profesor de solo lectura: clase "Evening B1" con Ana y Leo (último resultado, % por habilidad, misiones jugadas).
- En la barra de direcciones:
  - `/api/teacher/classes` → **200**, su clase "Evening B1" con 2 alumnos.
  - `/api/teacher/classes/00000000-0000-4000-8000-000000000000/progress` → **404 NOT_FOUND** (una clase que no es suya no existe para ella).
  - `/api/world` → **403 FORBIDDEN_ROLE** (un profesor no juega misiones).

**Decir**
- "Roles alumno, profesor y admin con dependencias de FastAPI; lo ajeno es 404 para no permitir enumerar; el admin ve todas las clases (hay un fixture de admin en los tests)."

## 7. Si sobra tiempo

- Replay simulado: como `new@` o `veteran@`, en el English World "Watch a simulated run" → A2, seed 7 → **Run simulation** → **Show all**. Decir: "el estudiante simulado del motor recorre el grafo; la respuesta trae resultados y decisiones de Maya, nunca preguntas ni respuestas".
- `make test` (≈ 45 s): 322 tests de backend y 45 de frontend; `make e2e` recorre la misión entera con teclado, a 1280 y 360 px, el rescate de Maya, dos pestañas y movimiento reducido.
- Enseñar el rescate: miss en q01, q02, q03, q04 y q07 → "Maya's shortcut" y el final **Made It Together** (automatizado en `frontend/e2e/resilience.spec.ts`).

## 8. Plan B

| Si pasa esto | Hacer |
|---|---|
| No suena la voz | Seguir: se muestra el anuncio escrito (PD-014). Decirlo como limitación documentada. |
| Ana ya no es "primer encuentro" (se ensayó sin reset) | `make reset` (1 min). Si no hay tiempo, contar el primer encuentro y seguir con **Play again**. |
| "Too many tries. Wait a minute…" en Check-in | Límite de 5 intentos/min por email: pasar a otra cuenta y volver luego. |
| Error de red en la misión | "The signal dropped. Your place in the story is saved." → **Try again**; o F5 (retoma igual). |
| El proveedor de IA real falla | No pasa nada: el informe sale con el feedback de respaldo y el pie lo dice. |
