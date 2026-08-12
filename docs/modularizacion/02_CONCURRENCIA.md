# Capa 2: concurrencia

Última revisión: 2026-08-12.

## Control

- Estado: **Activa**.
- Commit base: `b24cb8d3f1a8fa1d48699ed5732d4013ab6fe7f9`.
- Rama acordada: `main`.
- Estado al activar: árbol limpio; `HEAD` coincidente con la referencia local
  `origin/main`.
- Primera subcapa pendiente: **2.0**, inventario, contratos y línea base de
  concurrencia.
- Código de producto modificado al activar: **ninguno**.
- Autorización: orden explícita del usuario el 2026-08-12, después de cerrar la
  capa 1 y commitear su reconciliación documental.

## Objetivo

Evitar que las operaciones síncronas de PostgreSQL bloqueen el event loop en los
caminos de petición asíncronos, mediante un threadpool controlado, preservando el
`ContextVar` del tenant y todos los contratos observables. El cierre debe incluir
una medición reproducible de concurrencia antes y después.

## Dependencias de capas anteriores

- Compuerta única `scripts/verify.py`, heredada de la capa 0.
- Capa 1 cerrada con 334 pruebas, Ruff y `pip check` correctos en su última
  compuerta registrada.
- Contrato explícito de propiedad de conexión, cursor, `commit`, `rollback` y
  devolución al pool, protegido por pruebas herméticas.
- Cincuenta aperturas sin cierre garantizado migradas y ninguna ruta abriendo
  conexiones directamente.
- Timeouts y comportamiento del pool definidos; el mecanismo fue verificado
  contra el endpoint agrupado real.
- La calibración de `DB_STATEMENT_TIMEOUT_MS` continúa como verificación
  operativa pendiente y aceptada de la capa 1. No se considera cumplida ni se
  incorpora por inferencia al alcance de esta capa.

## Alcance autorizado

- Inventariar qué trabajo síncrono de base de datos es alcanzable desde caminos
  de petición asíncronos y dónde se ejecuta actualmente.
- Identificar y fijar el contrato de propagación del `ContextVar` del tenant a
  través del límite de ejecución en threads.
- Definir e introducir de forma progresiva un mecanismo de offload controlado,
  compatible con la tecnología actual y sin cambiar el driver.
- Migrar en tandas pequeñas los consumidores que el inventario demuestre que
  bloquean el event loop.
- Agregar pruebas de caracterización y regresión para contexto, aislamiento,
  errores y concurrencia.
- Medir con un procedimiento reproducible la concurrencia antes y después, sin
  usar producción.

## Fuera de alcance

- Cambiar PostgreSQL, `psycopg2`, el modelo de schemas tenant o introducir un
  ORM o un driver asíncrono.
- Modificar rutas, payloads, status codes, permisos, roles, ownership o reglas de
  negocio.
- Cambiar SQL observable, orden transaccional, `commit`, `rollback`, timeouts o
  tamaño del pool, salvo una autorización explícita ante un bloqueo demostrado.
- Ejecutar migraciones o rediseñar el alta y versionado de tenants; corresponde
  a la capa 3.
- Modularizar dominios, eliminar N+1, optimizar consultas o crear índices;
  corresponde a las capas 4 en adelante.
- Crear una abstracción compartida sin dos usos reales demostrados.
- Ejecutar cargas contra producción, desplegar o cambiar configuración real.

## Invariantes

- Métodos, paths, status codes y formas de respuesta permanecen idénticos.
- Permisos, roles, ownership y aislamiento entre tenants se conservan sin
  excepción.
- Cada trabajo enviado a otro thread observa el tenant de su petición y no puede
  heredar ni filtrar el de otra petición concurrente.
- SQL, parámetros, orden de operaciones y fronteras transaccionales permanecen
  iguales.
- La propiedad de cursor, conexión, `commit`, `rollback` y devolución al pool
  definida en la capa 1 no cambia.
- El mecanismo de offload no crea threads sin límite ni oculta la saturación del
  pool de conexiones.
- Una excepción conserva su tipo y traducción HTTP actuales; la cancelación y el
  trabajo que ya esté ejecutándose en un thread deben quedar caracterizados antes
  de modificar el camino correspondiente.

## Línea base

La activación no ejecuta verificaciones: la subcapa 2.0 debe reproducirlas desde
el commit base antes de inventariar o medir.

| Comprobación | Comando | Resultado |
|---|---|---|
| Pruebas específicas | Se define en 2.0 tras localizar la cobertura existente | Pendiente |
| Compuerta global | `.\venv\Scripts\python.exe scripts\verify.py` | Pendiente; 334 pruebas heredadas |
| Ruff | `.\venv\Scripts\python.exe -m ruff check --no-cache app tests scripts apply_migration.py` | Pendiente |
| Dependencias | `.\venv\Scripts\python.exe -m pip check` | Pendiente |
| Medición de concurrencia | Procedimiento reproducible por definir en 2.0 | Pendiente |

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 2.0 | Inventario, contratos, estrategia de verificación y línea base medible | **Pendiente** |
| 2.1 | Propagación del tenant caracterizada y primer límite de offload protegido | Pendiente |
| 2.2 | Primera tanda pequeña de caminos bloqueantes migrada | Pendiente |
| 2.3 | Tandas restantes definidas por el inventario | Pendiente |
| 2.4 | Medición posterior, compuerta global y cierre | Pendiente |

El desglose posterior a 2.0 es provisional porque se definió sin inspeccionar el
código de esta capa. El inventario puede dividir, fusionar o marcar subcapas
`No aplica` con justificación escrita. Nunca se ejecutan dos subcapas en el mismo
turno ni se amplía el alcance sin autorización.

## Subcapa activa: 2.0, trabajo exacto

1. Reproducir la compuerta heredada desde el commit base y registrar el resultado
   real.
2. Inventariar, sin modificar código, las fronteras `async`/síncronas de los
   caminos de petición que alcanzan PostgreSQL. Clasificar qué trabajo puede
   bloquear el event loop y qué trabajo ya se ejecuta fuera de él.
3. Trazar el ciclo del tenant desde la entrada de la petición hasta la preparación
   de la conexión y cualquier frontera de thread existente. Registrar el
   comportamiento observado y las incógnitas; no implementar todavía.
4. Localizar solo las pruebas relacionadas con tenant, `ContextVar`, sesión de
   base de datos, concurrencia o threadpool y determinar qué contratos ya fijan.
5. Definir una prueba que falle si el tenant no se propaga o se mezcla entre dos
   trabajos concurrentes, y un procedimiento reproducible para medir la línea
   base antes de cambiar el mecanismo. Si exige infraestructura externa o una
   decisión de alcance, presentarla al usuario antes de 2.1.
6. Actualizar esta bitácora con inventario, comandos, resultados, decisión de
   verificación, riesgos y la siguiente acción exacta; detenerse sin iniciar 2.1.

Lectura permitida en 2.0:

- `app/main.py`, `app/dependencies.py`, `app/db/session.py` y
  `app/db/tenant.py`, si conservan esas responsabilidades;
- coincidencias dirigidas en `app/routes/`, `app/controllers/` y
  `app/services/` para `async def`, `get_cursor`, `get_connection`,
  `ContextVar`, `run_in_threadpool`, `to_thread` o equivalentes;
- solo los archivos de pruebas devueltos por búsquedas de tenant, contexto,
  sesión, concurrencia o threadpool;
- manifiestos de dependencias, únicamente para identificar las versiones del
  stack que gobiernan la ejecución en threads.

Archivos que 2.0 puede modificar: **únicamente esta bitácora**. Sus comandos de
verificación son la compuerta global y `git diff --check`.

## Criterios de cierre de la subcapa 2.0

- Cada frontera relevante entre petición asíncrona y DB síncrona está localizada
  y clasificada con evidencia.
- El ciclo del `ContextVar` del tenant está trazado y sus riesgos están
  documentados.
- Existe una estrategia de prueba capaz de discriminar propagación correcta,
  pérdida y mezcla de tenant.
- Existe un procedimiento reproducible para medir concurrencia antes y después.
- La compuerta heredada y `git diff --check` terminan correctamente.
- El diff contiene exclusivamente esta bitácora y no se inició 2.1.

## Criterios de cierre de la capa

- Todas las subcapas necesarias están cerradas o marcadas `No aplica` con
  justificación.
- Ninguna operación síncrona inventariada bloquea el event loop sin una decisión
  explícita y documentada.
- La propagación y el aislamiento del tenant están protegidos por pruebas de
  concurrencia que fallan ante una implementación rota.
- El mecanismo usa capacidad de threads controlada y su relación con el pool de
  conexiones está medida y documentada.
- Las mediciones antes y después son reproducibles y muestran el resultado real,
  sin usar producción.
- La compuerta global, Ruff, dependencias y `git diff --check` terminan
  correctamente.
- Contratos HTTP, seguridad, tenant, SQL y transacciones permanecen conservados.
- Staging, rollback y verificación manual están documentados.
- La capa 3 queda en espera y no se activa sin orden explícita del usuario.

## Decisiones

- La capa se activa con `b24cb8d` como base porque es el `HEAD` limpio vigente
  después de la reconciliación documental de la capa 1. No se reutiliza el base
  anterior del programa.
- La activación crea solo esta bitácora y actualiza el índice. No inspecciona ni
  modifica código, conforme a la orden de detenerse antes de 2.0.
- 2.0 es primero una subcapa de inventario y medición. Elegir una API de
  threadpool o convertir funciones antes de conocer las fronteras reales fijaría
  una solución sin evidencia.
- Las subcapas posteriores son provisionales hasta completar 2.0.
- La calibración pendiente de `DB_STATEMENT_TIMEOUT_MS` permanece registrada en
  la capa 1 y no se da por cumplida al activar esta capa.

## Riesgos

- Un mecanismo de offload puede copiar el contexto correctamente en una API y
  perderlo en otra. El tenant podría caer al schema equivocado sin un error
  visible; por eso la propagación debe probarse antes de migrar consumidores.
- Un límite de threads mayor que el pool puede trasladar el bloqueo del event
  loop a una cola de conexiones; uno menor puede reducir el rendimiento. Deben
  medirse juntos.
- Cancelar una coroutine no detiene necesariamente una llamada síncrona que ya
  corre en otro thread. La propiedad de la conexión y los timeouts de la capa 1
  mitigan el riesgo, pero el comportamiento debe caracterizarse.
- Las pruebas herméticas pueden demostrar aislamiento de contexto, pero no por sí
  solas el rendimiento bajo carga ni el comportamiento de un endpoint agrupado
  real.
- `DB_STATEMENT_TIMEOUT_MS` sigue sin calibrarse contra consultas pesadas. Es un
  riesgo operativo heredado, no evidencia de que la capa 2 esté incompleta.

## Registro de ejecución

### 2026-08-12 — activación de la capa

- Modo de acceso del asistente: mismo checkout local; Git validado directamente.
- Autorización: orden explícita del usuario, «activa la capa 2».
- Rama acordada: `main`.
- Estado verificado antes de escribir: árbol limpio; `HEAD` y la referencia
  local `origin/main` en `b24cb8d3f1a8fa1d48699ed5732d4013ab6fe7f9`.
- Commit base registrado: `b24cb8d3f1a8fa1d48699ed5732d4013ab6fe7f9`.
- Continuidad auditada: 20 commits posteriores al base de la capa 1, todos
  explicados; 19 materializaron su cierre y `b24cb8d` reconcilió después la
  documentación, tal como registra su bitácora.
- Archivos creados o modificados: esta bitácora y
  `docs/modularizacion/README.md`.
- Código de producto, pruebas, configuración, dependencias y workflow
  modificados: ninguno.
- Código de concurrencia inspeccionado: **ninguno**. La activación se definió
  solo desde el índice, la bitácora de continuidad y la plantilla.
- Compuerta global: no ejecutada durante la activación; 2.0 debe reproducir desde
  el base las 334 pruebas y verificaciones heredadas.
- Verificación documental: `git diff --check` correcto; comprobación equivalente
  sobre esta bitácora nueva correcta; el índice contiene exactamente una capa
  marcada como `Activa` y el diff se limita a los dos documentos de activación.
- Verificación operativa heredada: la calibración de
  `DB_STATEMENT_TIMEOUT_MS` permanece pendiente y aceptada.
- Siguiente acción exacta: ejecutar **2.0**, reproduciendo la línea base e
  inventariando las fronteras async/síncronas, la propagación del tenant, la
  estrategia de prueba y el procedimiento de medición. Actualizar únicamente esta
  bitácora y detenerse sin iniciar 2.1.

## Entrega al próximo chat

- Capa activa: **2, concurrencia**.
- Última subcapa terminada: ninguna; solo se activó la capa.
- Primera subcapa pendiente: **2.0**, inventario, contratos y línea base medible.
- Bloqueos: ninguno para 2.0. La calibración operativa heredada de
  `DB_STATEMENT_TIMEOUT_MS` continúa pendiente y no debe marcarse como cumplida.
- Siguiente acción exacta: ejecutar 2.0 con el alcance de lectura y documentación
  definido arriba; no modificar código ni iniciar 2.1.
