# Capa 2: concurrencia

Última revisión: 2026-08-13.

## Control

- Estado: **Cerrada**.
- Commit base: `b24cb8d3f1a8fa1d48699ed5732d4013ab6fe7f9`.
- Rama acordada: `main`.
- Estado al activar: árbol limpio; `HEAD` coincidente con la referencia local
  `origin/main`.
- Primera subcapa pendiente: **ninguna**.
- Código de producto modificado al activar: **ninguno**.
- Código de producto modificado hasta ahora: `app/routes/reportes.py`,
  `app/routes/dashboard.py`, `app/routes/plan_de_clases.py` y
  `app/controllers/branding_controller.py`, además de `app/dependencies.py`,
  `app/core/super_admin.py` y `app/main.py`; veintitrés handlers sin `await`
  pasaron de `async def` a `def`, sin cambiar sus cuerpos, y branding conserva
  su lectura async mientras envía únicamente storage y DB al threadpool.
- Progreso: **2.0, 2.1, 2.2, 2.3a, 2.3b, 2.4, 2.5 y 2.6 cerradas**. Los cinco reportes,
  siete lecturas de dashboard y once rutas de plan de clases ya ejecutan sus
  cuerpos síncronos en el threadpool gobernado por FastAPI; branding mantiene
  su handler async, pero ya no ejecuta storage ni PostgreSQL síncronos en el
  event loop. Las consultas de las dependencias async de usuario y super admin
  ya usan el offload estándar; el limitador compartido queda en cinco workers
  para el pool actual de diez conexiones, conforme al pico medido de dos
  conexiones retenidas por worker.
- Cierre: **2.0–2.6 cerradas** el 2026-08-13. La medición formal, la
  compuerta global, staging, rollback y verificación manual quedaron
  documentados; la capa 3 permanece en espera y no fue activada.
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
| Pruebas específicas | `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_auth_tenant.py tests/test_db_session_contrato.py tests/test_db_pool_timeouts.py` | **43 pasaron** en 0,43 s |
| Compuerta global | `.\venv\Scripts\python.exe scripts\verify.py` | **Exit 0** fuera del sandbox: 334 pruebas, 5 warnings conocidos |
| Ruff | Ejecutado por la compuerta | `All checks passed!` |
| Dependencias | Ejecutado por la compuerta | `No broken requirements found.` |
| Medición de concurrencia | Harness hermético en memoria descrito abajo | Línea base registrada |

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 2.0 | Inventario, contratos, estrategia de verificación y línea base medible | **Cerrada** |
| 2.1 | Contrato concurrente del tenant y primera tanda: 5 reportes de solo lectura | **Cerrada** |
| 2.2 | Segunda tanda: 7 lecturas de dashboard | **Cerrada** |
| 2.3a | Tercera tanda: 5 lecturas de plan de clases | **Cerrada** |
| 2.3b | Cuarta tanda: 6 escrituras o efectos de plan de clases | **Cerrada** |
| 2.4 | Caso especial de branding: lectura async más storage y DB síncronos | **Cerrada** |
| 2.5 | Dependencias async de usuario y super admin; límite compartido derivado y medido | **Cerrada** |
| 2.6 | Medición posterior, compuerta global, staging, rollback y cierre | **Cerrada** |

El inventario de 2.0 reemplaza el desglose provisional de la activación. Las
tandas separan lecturas, escrituras/efectos y autenticación para que cada diff sea
revisable. Nunca se ejecutan dos subcapas en el mismo turno.

## Subcapa 2.0: resultado

### Línea base reproducida

La primera ejecución de la compuerta dentro del sandbox terminó en exit 1: 328
pruebas pasaron y 6 casos de `tests/test_uploads_permissions.py` fallaron en
*setup* porque pytest no podía enumerar
`C:\Users\David\AppData\Local\Temp\pytest-of-David` (`WinError 5`). Ruff y
`pip check` sí terminaron correctamente. No fue una regresión del checkout.

La misma compuerta se repitió con autorización fuera del sandbox y terminó en
exit 0: **334 pruebas correctas**, los 5 warnings conocidos, Ruff correcto y
dependencias íntegras. Las 43 pruebas específicas de autenticación tenant,
sesión y pool también pasaron con el cache de pytest desactivado.

Stack efectivo de la medición, tomado del `venv` del repositorio:

| Componente | Versión |
|---|---:|
| Python | 3.14.3 |
| FastAPI | 0.136.1 |
| Starlette | 1.0.0 |
| AnyIO | 4.13.0 |
| psycopg2-binary | 2.9.12 |
| pytest | 9.0.3 |

`requirements.txt` declara límites inferiores, pero no fija versiones máximas ni
declara Starlette o AnyIO directamente. Las comparaciones antes/después de esta
capa deben usar el mismo `venv` y registrar estas versiones; si cambian, la
medición no es comparable sin repetir la línea base.

### Inventario cuantitativo de fronteras HTTP

Se hizo con búsquedas dirigidas y un análisis AST en memoria sobre
`app/routes/`, `app/controllers/` y `app/services/`; no se agregó ningún script
al repositorio.

| Patrón | Cantidad | Ejecución actual |
|---|---:|---|
| Handlers HTTP totales | 139 | — |
| Handlers `def` | 115 | FastAPI los envía al threadpool de AnyIO |
| Handlers `async def` | 24 | FastAPI los ejecuta en el event loop |
| Handlers async cuyo cuerpo alcanza DB síncrona | **24** | **Bloquean el event loop** |
| Handlers sync cuyo cuerpo alcanza DB | 109 | Ya están fuera del event loop |
| Handlers sync sin DB visible | 6 | No requieren migración por su cuerpo |
| Handlers que atraviesan `get_current_user` async | **133** | Su validación DB bloquea el event loop antes del handler |
| Handlers que atraviesan `get_current_super_admin` async | **4** | Su validación DB bloquea el event loop antes del handler |
| Mecanismos explícitos de offload en rutas/controllers/services | **0** | — |

Conclusión: **137 de los 139 handlers** atraviesan una dependencia async que
ejecuta PostgreSQL síncrono en el event loop. Los dos restantes son `login`, cuyo
handler sync ya se ejecuta en un worker, y `logout`, que no consulta DB. Además,
los 24 handlers async añaden una segunda frontera bloqueante después de la
autenticación. Convertir solo rutas no resolverá el cuello de botella común.

Los 24 handlers async se reparten así:

| Familia | Sitios | Funciones |
|---|---:|---|
| Branding | 1 | `subir_logo` |
| Dashboard | 7 | `obtener_cumpleanos_admin`, `obtener_cumpleanos_profesor`, `obtener_inasistencias_profesor`, `obtener_notas_bajas_profesor`, `obtener_notas_altas_profesor`, `obtener_ranking_rendimiento`, `obtener_ranking_mejor_rendimiento` |
| Plan de clases | 11 | `obtener_notificaciones_planeadores`, `crear_plan_de_clases`, `obtener_planes_por_asignacion`, `eliminar_imagen_plan_profesor`, `listar_planes_admin`, `obtener_plan_admin`, `actualizar_revision_plan`, `crear_observacion_plan`, `listar_observaciones_plan`, `marcar_observacion_vista`, `eliminar_imagen_plan_admin` |
| Reportes | 5 | `reporte_general`, `reporte_estado_cuenta_curso`, `reporte_ingresos_mes`, `reporte_ingresos_rango`, `reporte_egresos_rango` |

Veintitrés de los 24 no contienen ningún `await`: llaman directamente a un
controller o service síncrono. El caso distinto es `branding.subir_logo`, que
espera `UploadFile.read()` y luego llama al helper async
`subir_logo_controller`; este ejecuta storage síncrono, `get_cursor(commit=True)`
y borrado de archivo sin offload. Debe conservarse como caso separado por el
orden entre archivo y transacción.

Las cinco rutas de reportes llegan a controllers síncronos con
`get_connection`; las siete de dashboard llegan a `get_connection` o
`get_cursor`; y las once de plan de clases cruzan controllers y services
síncronos hasta su repository. La implementación interna del repository no se
abrió: para clasificar la frontera basta que el handler async lo invoque sin
`await`.

Entre los 115 handlers sync, 108 cadenas DB quedaron confirmadas dentro de
rutas/controllers/services y una adicional —`tenant_status`— llega a
`get_tenant_by_schema`, cuya consulta pública sí se confirmó en la revisión
dirigida. FastAPI ya gobierna correctamente esos cuerpos `def`; no deben
reescribirse solo para uniformar estilo. Los seis sin DB visible son `logout` y
cinco deletes deshabilitados.

### La frontera común de autenticación

`get_current_user` es `async def`, pero llama directamente a dos funciones sync
con DB:

1. `ensure_tenant_allowed_for_app` termina en `_query_public_colegio`, que fija
   temporalmente el schema `public`, toma conexión y consulta el colegio.
2. Después de fijar el tenant de la petición, `_validar_usuario_en_bd` toma otra
   conexión y valida existencia, rol y estado.

`get_current_active_admin` depende de esa misma función. El análisis de
dependencias a nivel de router, decorador y parámetro muestra **133 handlers** en
esta cadena.

Los cuatro handlers de super admin usan `get_current_super_admin`, también
`async def`; esta llama directamente a `validate_super_admin`, que toma conexión
pública y consulta `public.super_admins`. Son otros cuatro bloqueos del event
loop, no una frontera segura por ser dependencias.

### Contrato observado del tenant

1. `tenant_schema_var` es un `ContextVar` con valor por defecto `None`.
2. `tenant_middleware` fija primero `None`, si hay Bearer válido siembra el
   tenant, ejecuta el downstream y restaura siempre el token original.
3. La autenticación por cookie no puede ser sembrada por el middleware:
   `get_current_user` decodifica la cookie y fija el tenant dentro de la tarea
   downstream antes de validar al usuario.
4. Cada `get_connection()` lee ese contexto, rechaza `None` o un schema inválido
   y reaplica `search_path` antes de entregar la conexión. La pérdida de contexto
   falla cerrada antes del SQL de negocio.
5. Las consultas públicas cambian a `public` con token y lo restauran en
   `finally`.
6. `branding_controller` y `plan_de_clases_controller` leen el `ContextVar`
   directamente para construir rutas de storage. Ahí una pérdida podría formar
   un namespace con `None` antes de que la DB alcance su guarda.

FastAPI ejecuta handlers y dependencias normales `def` mediante el threadpool;
Starlette concreta ese límite con `anyio.to_thread.run_sync`. AnyIO copia el
contexto de la tarea al worker, pero las mutaciones hechas en el worker **no
regresan** al llamador. Se verificó empíricamente con el stack instalado:

- 1.000 pares concurrentes con tenants distintos mediante
  `starlette.concurrency.run_in_threadpool`: **1.000 correctos, 0 pérdidas, 0
  mezclas y 0 fugas**; 0,310 s.
- El control negativo con `asyncio.run_in_executor` crudo observó `None` en
  ambos workers.
- Fijar `tenant_worker` dentro de un worker devolvió ese valor allí, pero el
  llamador continuó viendo `None`.

Consecuencia de seguridad: **no se puede convertir `get_current_user` a `def`
sin más**. En autenticación por cookie, el tenant fijado dentro del worker no
volvería a la tarea que después lanza el handler. La dependencia debe conservar
una parte async que fije el tenant en el llamador antes de enviar DB al worker.

Referencias primarias usadas para contrastar el comportamiento instalado:

- [FastAPI: Concurrency and async / await](https://fastapi.tiangolo.com/async/).
- [Starlette: Thread Pool](https://www.starlette.io/threadpool/).
- [AnyIO: Working with threads](https://anyio.readthedocs.io/en/stable/threads.html).

### Capacidad y cancelación medidas

El limitador compartido por defecto de AnyIO tiene **40 tokens** y el pool DB
configurado tiene `minconn=1`, `maxconn=10`. El pool de la capa 1 falla de
inmediato al agotarse: si simplemente se liberan los 137 bloqueos hacia el
threadpool por defecto, hasta cuarenta workers podrían competir por diez
conexiones y convertir serialización en errores visibles.

Un limitador dedicado solo para nuevas llamadas explícitas no controla los
handlers `def` que FastAPI ya envía al limitador compartido. Por eso el objetivo
final es que todo el trabajo DB del camino HTTP use el límite compartido y,
cuando ya no quede DB en el event loop, derivar sus tokens a partir de
`DB_POOL_MAX_CONNECTIONS` **y del máximo de conexiones simultáneas que puede
retener un solo worker**. Diez tokens es un límite superior candidato, no un
valor correcto por definición: si una petición retiene dos conexiones a la vez,
sería demasiado alto. La política se aplicará al final de la migración, no en la
primera tanda, y medirá también el impacto sobre `FileResponse`, `UploadFile` y
otros usos internos que comparten tokens.

La cancelación también se caracterizó con un worker que duerme 100 ms y un
`CancelScope` de 20 ms:

| Variante | Retorno observado | Significado |
|---|---:|---|
| `anyio.to_thread.run_sync` por defecto | 102 ms | Espera al worker; no abandona recursos vivos |
| `run_in_threadpool` de Starlette | 101 ms | Misma semántica protegida |
| AnyIO con `abandon_on_cancel=True` | 21 ms | El llamador sale, pero el thread sigue trabajando |

Para DB se conserva la semántica por defecto. Abandonar un thread que todavía
posee conexión haría ambiguos el cierre, el rollback y el efecto de una
cancelación HTTP.

### Cobertura existente y hueco exacto

- `test_auth_tenant.py` comprueba una llamada aislada: el tenant se fija antes de
  la validación, pero todo ocurre en la misma tarea.
- `test_db_session_contrato.py` fija manualmente un tenant y protege preparación,
  devolución al pool, commit y rollback; el caso sin tenant exige
  `RuntimeError`.
- `test_db_pool_timeouts.py` fija que `search_path` se aplica antes de los
  timeouts, pero sus pruebas del pool son secuenciales.
- `test_plan_de_clases_integridad.py` simula un conflicto lógico concurrente con
  filas prefabricadas; no crea threads ni prueba `ContextVar`.

No existe una prueba que solape dos tenants, cruce un thread, detecte mezcla o
afirme restauración. Tampoco existe cobertura de cancelación del offload.

La prueba discriminante de 2.1 debe:

1. ejecutar dos tareas con tenants distintos y autenticación por cookie;
2. coordinarlas con una barrera dentro de dos workers reales;
3. observar el tenant antes del salto, dentro del worker y al volver;
4. exigir `A -> A`, `B -> B`, nunca `None` ni el tenant contrario;
5. verificar que el contexto exterior queda restaurado;
6. incluir un control de mutación contra un executor que no copie contexto;
7. fijar que la cancelación normal espera a que el trabajo DB libere sus
   recursos.

No necesita PostgreSQL, `httpx`, red ni una dependencia nueva. Una prueba HTTP
completa se descartó para esta tanda porque añadiría un cliente o harness cuando
la frontera puede discriminarse directamente con AnyIO/Starlette.

### Medición reproducible antes y después

Se ejecutó cinco veces un harness hermético contra la función real
`get_current_user`, sustituyendo JWT y DB por dobles. Dos autenticaciones
concurrentes realizan cada una una validación bloqueante de 100 ms, mientras una
tarea heartbeat intenta despertar a los 20 ms.

| Métrica actual | Resultado |
|---|---:|
| Mediana total del par | **224 ms** |
| Retraso mediano adicional del heartbeat | **204 ms** |
| Máximo de validaciones solapadas | **1** |
| Validaciones en el thread del event loop | **Sí, todas** |
| Tenants observados | A y B correctos, sin mezcla |

El mismo harness se repetirá después de migrar las dependencias. La compuerta
funcional no será un umbral temporal frágil: exigirá workers distintos del event
loop, solapamiento mediante barrera, cero pérdidas/mezclas/fugas y preservación
de excepciones. Las medianas de tiempo se registrarán como evidencia, usando el
mismo `venv`, demora, número de repeticiones y versiones.

### Siguiente subcapa: 2.1, trabajo exacto

1. Confirmar `main` limpia y que el único commit posterior al base sigue
   explicado por esta bitácora.
2. Agregar primero la prueba hermética concurrente del tenant descrita arriba y
   comprobar que pasa sobre el mecanismo actual de Starlette/AnyIO; ejecutar el
   control negativo sin incorporarlo como camino de producto.
3. Localizar y conservar las pruebas existentes de las cinco rutas de reportes;
   si falta caracterización, agregar solo la necesaria para forma de respuesta,
   errores y llamada al controller.
4. Convertir únicamente los cinco handlers de `app/routes/reportes.py` que no
   contienen `await` de `async def` a `def`, para que FastAPI envíe sus
   controllers DB síncronos al worker. No tocar controllers, SQL, permisos ni la
   dependencia de autenticación.
5. Ejecutar las pruebas nuevas y de reportes, Ruff del alcance, compuerta global
   y `git diff --check`; revisar que el diff pertenezca solo a 2.1.
6. Actualizar esta bitácora y detenerse sin iniciar 2.2.

Archivos previstos para 2.1: `app/routes/reportes.py`, las pruebas de reportes
existentes que corresponda, un archivo de contrato concurrente del tenant y esta
bitácora. No se modifica todavía `app/dependencies.py`, el limitador global ni
ninguna otra familia de rutas.

### Subcapa 2.1: resultado

Se agregó primero el contrato hermético del tenant y se ejecutó con los cinco
handlers todavía en `async def`: **16 pruebas pasaron**. Después se cambiaron
exclusivamente esas cinco declaraciones a `def`. FastAPI puede así enviar sus
cuerpos síncronos al threadpool de AnyIO sin introducir una abstracción nueva ni
modificar controllers.

El contrato concurrente invoca directamente la función real
`tenant_middleware` con dos tareas autenticadas solo por cookie. El middleware
fija `None`, `get_current_user` fija `tenant_alpha` o `tenant_beta`, y dos
workers distintos se solapan mediante barreras. Se exige A→A y B→B antes,
durante y después del trabajo síncrono, y el `finally` real del middleware debe
restaurar el contexto exterior. No es una prueba HTTP end-to-end ni usa red o
PostgreSQL.

El mismo archivo fija dos contratos adicionales:

- un `ThreadPoolExecutor` dedicado demuestra que el executor crudo no copia el
  tenant del llamador ni devuelve mutaciones del worker;
- un centinela dentro del mismo `CancelScope` confirma que la cancelación ya fue
  entregada mientras `run_in_threadpool` todavía espera a que el worker libere
  sus recursos.

Las pruebas de reportes conservan delegación, parámetros, respuesta legacy y
paginada, traducción de excepciones a HTTP 400 y la condición de que las cinco
funciones sean síncronas. Por inspección exacta del diff permanecen iguales los
decoradores GET, paths, restricciones `Query`, dependencia admin común, cuerpos
y llamadas a controllers.

Resultado verificado:

| Comprobación | Resultado |
|---|---|
| Estado previo, contrato + reportes | 16 pasaron |
| Estado posterior, contrato + reportes | 21 pasaron |
| Específicas ampliadas con dos controllers financieros | 23 pasaron |
| Estabilidad del contrato concurrente | 20 rondas; 60/60 casos pasaron |
| Compuerta global fuera del sandbox | 349 pruebas, 5 warnings conocidos |
| Ruff | `All checks passed!` |
| `pip check` | `No broken requirements found.` |

La primera compuerta global dentro del sandbox reprodujo la limitación ambiental
ya observada en 2.0: 343 pruebas pasaron y seis casos de uploads fallaron en
*setup* por `WinError 5` al enumerar el temporal de pytest. Ruff y `pip check`
pasaron en esa ejecución. La misma compuerta, autorizada fuera del sandbox,
terminó en exit 0.

### Siguiente subcapa: 2.2, trabajo exacto

1. Confirmar `main` limpia y que todo commit posterior al base esté explicado
   por esta bitácora.
2. Abrir únicamente las siete rutas de dashboard inventariadas, sus controllers
   síncronos inmediatos y sus pruebas existentes.
3. Agregar antes del cambio la caracterización mínima que falte para preservar
   delegación, parámetros, respuestas y traducción de errores.
4. Convertir solo los siete handlers de lectura de dashboard sin `await` de
   `async def` a `def`. No tocar reportes, plan de clases, branding,
   autenticación, SQL ni el limitador global.
5. Ejecutar pruebas específicas, Ruff del alcance, compuerta global y
   `git diff --check`; actualizar esta bitácora y detenerse antes de 2.3a.

### Subcapa 2.2: resultado

Se caracterizaron primero las siete rutas de dashboard mientras todavía eran
`async def`: **38 pruebas pasaron**. Después se eliminaron únicamente los siete
tokens `async` de sus declaraciones. Decoradores, firmas, guards, límites de los
`try`, cuerpos y llamadas a controllers permanecen byte a byte iguales.

Las pruebas nuevas fijan:

- delegación y respuesta sin transformación para las siete rutas;
- traducción de excepciones de controller a HTTP 400 con el mismo detalle;
- propagación sin traducción de los 403 de scope de profesor y asignación;
- orden y cortocircuito del filtro de rendimiento, incluidos sus 422 y 403;
- los siete paths GET, dependencias por identidad y parámetros representativos
  de OpenAPI;
- que los siete endpoints realmente registrados ya no son coroutines.

Los controllers no cambiaron. Sus consultas siguen siendo de solo lectura, con
el mismo SQL, parámetros, orden, resultados, conexiones y cursores. El contrato
concurrente agregado en 2.1 continúa probando que el tenant fijado por cookie se
copia de forma aislada a workers distintos y que el middleware restaura el
contexto exterior.

Resultado verificado:

| Comprobación | Resultado |
|---|---|
| Línea base dirigida existente | 10 pasaron |
| Caracterización previa | 38 pasaron |
| Caracterización posterior | 39 pasaron |
| Específicas ampliadas con permisos y tenant | 53 pasaron |
| Compuerta global fuera del sandbox | 378 pruebas, 5 warnings conocidos |
| Ruff | `All checks passed!` |
| `pip check` | `No broken requirements found.` |

La compuerta se ejecutó directamente fuera del sandbox porque 2.0 y 2.1 ya
demostraron que el temporal estándar de pytest produce `WinError 5` dentro del
sandbox. No hubo acceso a red, PostgreSQL ni producción.

La revisión estructural confirmó exactamente 14 líneas de contenido modificadas
en producto: siete pares `-async def` / `+def`. El AST final encuentra los siete
handlers como `FunctionDef`; bajo `app/` no cambió ningún otro archivo.

### Siguiente subcapa: 2.3a, trabajo exacto

1. Confirmar `main` limpia y que todo commit posterior al base esté explicado
   por esta bitácora.
2. Abrir únicamente los cinco handlers de lectura de plan de clases ya
   inventariados —`obtener_notificaciones_planeadores`,
   `obtener_planes_por_asignacion`, `listar_planes_admin`, `obtener_plan_admin`
   y `listar_observaciones_plan`—, sus fronteras síncronas inmediatas y pruebas
   relacionadas.
3. Agregar antes del cambio la caracterización mínima necesaria para preservar
   paths, parámetros, permisos, ownership, respuestas, storage y traducción de
   errores.
4. Convertir solo esos cinco handlers sin `await` de `async def` a `def`. No
   tocar los seis handlers con escrituras o efectos de 2.3b, branding,
   autenticación, SQL ni el limitador global.
5. Ejecutar pruebas específicas, Ruff del alcance, compuerta global y
   `git diff --check`; actualizar esta bitácora y detenerse antes de 2.3b.

### Subcapa 2.3a: resultado

Se caracterizaron primero los cinco GET de plan de clases mientras todavía eran
`async def`: **16 pruebas pasaron** y el conjunto dirigido con repositorios y
permisos terminó con **22 pruebas correctas**. Después se eliminaron únicamente
los cinco tokens `async` de sus declaraciones. No cambiaron decoradores, firmas,
guards, límites de los `try`, llamadas a controllers ni retornos.

Las pruebas nuevas fijan:

- los cinco paths GET, sus dependencias por identidad y los parámetros/defaults
  relevantes del esquema OpenAPI;
- los roles permitidos para notificaciones y la selección del profesor desde el
  usuario autenticado;
- el guard de asignación antes del `try`, las ramas exclusivas por fecha o
  historial paginado y la traducción de errores de lectura a HTTP 400;
- los filtros del listado admin y su error HTTP 500 genérico;
- la dependencia admin y el 404 sin traducción del detalle;
- el ownership del plan antes de listar observaciones, con sus 403 y 404
  conservados;
- la respuesta opaca, incluidas las referencias `imagen1` e `imagen2`, sin
  introducir I/O de storage; y
- que los cinco endpoints realmente registrados son síncronos después del
  cambio.

Sus controllers, services, repositorios y guards inmediatos continúan siendo
síncronos. Los cinco caminos solo leen PostgreSQL, materializan sus resultados y
no escriben archivos ni datos. El SQL, los parámetros, el orden de consultas,
las conexiones y las fronteras transaccionales permanecen iguales. La garantía
de 2.1 sigue cubriendo que el tenant fijado antes del handler se copia al worker
de Starlette/AnyIO; no se introdujo ningún executor crudo.

Resultado verificado:

| Comprobación | Resultado |
|---|---|
| Línea base relacionada existente | 43 pasaron |
| Caracterización previa nueva | 16 pasaron |
| Dirigidas antes del cambio | 22 pasaron |
| Caracterización posterior | 17 pasaron |
| Dirigidas posteriores | 23 pasaron |
| Específicas ampliadas con repositorios, permisos y tenant | 60 pasaron, 5 warnings conocidos |
| Compuerta global fuera del sandbox | 395 pruebas, 5 warnings conocidos |
| Ruff | `All checks passed!` |
| `pip check` | `No broken requirements found.` |

La primera compuerta global dentro del sandbox terminó en exit 1: **389 pruebas
pasaron** y los seis casos de uploads fallaron en *setup* por el `WinError 5`
conocido al enumerar el temporal de pytest. Ruff y `pip check` sí pasaron. La
misma compuerta, autorizada fuera del sandbox, terminó en exit 0 con las 395
pruebas correctas.

La revisión estructural confirmó exactamente 10 líneas de contenido modificadas
en producto: cinco pares `-async def` / `+def`. El AST final encuentra esos cinco
handlers como `FunctionDef`; los seis handlers de escrituras o efectos
reservados para 2.3b permanecen `AsyncFunctionDef`. Bajo `app/` no cambió ningún
otro archivo.

### Siguiente subcapa: 2.3b, trabajo exacto

1. Confirmar `main` limpia y que todo commit posterior al base esté explicado
   por esta bitácora.
2. Abrir únicamente los seis handlers de escrituras o efectos de plan de clases
   ya inventariados —`crear_plan_de_clases`,
   `eliminar_imagen_plan_profesor`, `actualizar_revision_plan`,
   `crear_observacion_plan`, `marcar_observacion_vista` y
   `eliminar_imagen_plan_admin`—, sus fronteras síncronas inmediatas y pruebas
   relacionadas.
3. Agregar antes del cambio la caracterización mínima de multipart, storage,
   permisos, ownership, revisión versionada, transacciones, cleanup y errores.
4. Migrar solo esos seis handlers de acuerdo con la evidencia obtenida. No
   tocar las cinco lecturas ya cerradas, branding, autenticación, SQL ni el
   limitador global.
5. Ejecutar pruebas específicas, Ruff del alcance, compuerta global y
   `git diff --check`; actualizar esta bitácora y detenerse antes de 2.4.

### Subcapa 2.3b: resultado

Se caracterizaron primero los seis endpoints con efectos mientras todavía eran
`async def`: **38 pruebas nuevas pasaron** y el conjunto dirigido con doce
regresores existentes de integridad, revisión, transacciones y permisos terminó
con **50 pruebas correctas**.
Después se eliminaron únicamente los seis tokens `async` de sus declaraciones.
No cambiaron decoradores, firmas, dependencias, guards, modelos, límites de los
`try`, llamadas a controllers ni retornos.

La caracterización nueva fija:

- los seis paths y métodos, dependencias por identidad, multipart, bodies JSON,
  parámetros path y el patrón de `slot` en OpenAPI;
- la construcción completa del plan, la fecha, los mismos objetos `UploadFile`,
  permisos de asignación/plan y respuestas sin transformación;
- los detalles canónicos de 400, 403, 404, 409 y 500 y el orden de los guards;
- la ruta de storage derivada del tenant, MIME, extensión, límite de 5 MiB,
  contenido, key y `UploadFile` real en el caso correcto;
- el orden imagen 1 → imagen 2 → escritura DB y el cleanup de la primera imagen
  si falla la segunda;
- la diferencia entre borrado profesor (`reiniciar_revision=True`) y admin
  (`False`), y el orden repository → borrado best-effort del archivo;
- `commit=True`, `FOR UPDATE` y la actualización simple del borrado admin;
- la transacción e idempotencia de marcar una observación vista; y
- que los seis endpoints realmente registrados son síncronos después del
  cambio.

El parseo y spooling multipart siguen ocurriendo en FastAPI antes de invocar el
handler. La conversión mueve al worker la lectura síncrona de `UploadFile.file`,
storage local o R2 y PostgreSQL ejecutados por el cuerpo; no se presenta como
offload de toda la request. La garantía de 2.1 sigue cubriendo que el tenant se
copia al worker y que la cancelación espera su cleanup.

Controllers, services, repositorios y storage no cambiaron. Se conserva el
orden preexistente de efectos: al crear, storage precede a la transacción DB y
los archivos nuevos se limpian best-effort ante error; al eliminar, la
transacción DB devuelve el path antes de intentar borrar el archivo. Las pruebas
son herméticas con dobles y `BytesIO`; no son una ejecución HTTP end-to-end ni
una validación contra PostgreSQL o R2 reales.

Resultado verificado:

| Comprobación | Resultado |
|---|---|
| Línea base relacionada fuera del sandbox | 66 pasaron, 5 warnings conocidos |
| Caracterización inicial previa | 38 pasaron |
| Dirigidas iniciales previas | 50 pasaron |
| Caracterización inicial posterior | 39 pasaron |
| Dirigidas iniciales posteriores | 51 pasaron |
| Caracterización final tras auditoría del arnés | 42 pasaron |
| Dirigidas finales con doce regresores | 54 pasaron |
| Específicas ampliadas | 108 pasaron, 5 warnings conocidos |
| Compuerta global fuera del sandbox | 437 pruebas, 5 warnings conocidos |
| Ruff | `All checks passed!` |
| `pip check` | `No broken requirements found.` |

La línea base relacionada intentada dentro del sandbox terminó con 60 pruebas
correctas y seis errores de setup de uploads por el `WinError 5` conocido sobre
el temporal de pytest. La repetición autorizada fuera del sandbox terminó en
66/66. La compuerta global se ejecutó fuera del sandbox para permitir esos
mismos temporales y terminó en exit 0.

La revisión estructural confirmó exactamente 12 líneas de contenido modificadas
en producto: seis pares `-async def` / `+def`. El AST final encuentra los seis
efectos y las cinco lecturas de plan de clases como `FunctionDef`; branding sigue
`AsyncFunctionDef` y no aparece en el diff. Bajo `app/` no cambió ningún otro
archivo.

### Siguiente subcapa: 2.4, trabajo exacto

1. Confirmar `main` limpia y que todo commit posterior al base esté explicado
   por esta bitácora.
2. Abrir únicamente el handler `subir_logo` de branding, su helper inmediato y
   sus pruebas relacionadas, preservando la lectura async del `UploadFile`.
3. Caracterizar antes del cambio el orden lectura → storage → DB → cleanup,
   tenant, permisos, payload y errores, además de la frontera de cancelación.
4. Enviar al threadpool estándar solo el tramo síncrono de storage y DB que la
   evidencia delimite. No convertir ciegamente todo el handler a `def`, no usar
   executor crudo y no tocar autenticación ni el limitador global.
5. Ejecutar pruebas específicas, Ruff del alcance, compuerta global y
   `git diff --check`; actualizar esta bitácora y detenerse antes de 2.5.

### Subcapa 2.4: resultado

`subir_logo` y `subir_logo_controller` permanecen `async def`. Se conservaron,
en el mismo orden, las validaciones de slot, MIME y extensión, la lectura
`await archivo.read()` y la comprobación posterior del límite de 2 MiB. Solo el
tramo que empezaba después de esa comprobación se extrajo a
`_guardar_logo_leido`, helper privado y síncrono del mismo controller, y se
espera con `starlette.concurrency.run_in_threadpool`.

El helper obtiene `tenant_schema_var` dentro del worker. Por tanto, el mismo
contexto copiado gobierna la key `branding/<tenant>/...` y el `search_path` que
aplica `get_cursor`. No se introdujo executor crudo, limitador propio ni opción
abandonable. La ruta, sus dependencias global y de admin activo, multipart,
query, payload, status y propagación de excepciones no cambiaron.

Se preservó literalmente el orden observable posterior a la lectura:

1. guardar el archivo nuevo;
2. formar su URL;
3. abrir `get_cursor(commit=True)`, leer la URL anterior y actualizar la columna;
4. salir del bloque, que confirma y libera los recursos;
5. intentar borrar el archivo anterior solo si existe y es distinto;
6. devolver el mismo `{"url": ..., "slot": ...}`.

Las pruebas nuevas caracterizan ambos slots, metadata OpenAPI y dependencias,
validaciones y detalles 400, lectura async, tenant A/B en workers simultáneos,
orden storage/DB/cleanup, fallos por frontera, ausencia de compensación si DB
falla y cancelación protegida. Usan dobles y `UploadFile` en memoria: no son una
petición HTTP end-to-end ni una ejecución contra PostgreSQL o R2 reales.

Resultado verificado:

| Comprobación | Resultado |
|---|---|
| Línea base relacionada fuera del sandbox | 17 pasaron, 5 warnings conocidos |
| Caracterización previa, arnés inicial | 22 pasaron, 2 poscondiciones excluidas |
| Mismo selector, arnés final | 23 pasaron, 2 poscondiciones excluidas |
| Específicas finales de branding | 25 pasaron, 1 warning conocido |
| Específicas ampliadas | 34 pasaron, 5 warnings conocidos |
| Estabilidad de worker y cancelación | 20 rondas; 40/40 casos correctos |
| Compuerta global fuera del sandbox | 454 pruebas, 5 warnings conocidos |
| Ruff | `All checks passed!` |
| `pip check` | `No broken requirements found.` |

### Siguiente subcapa: 2.5, trabajo exacto

Caracterizar y migrar únicamente la DB síncrona de las dependencias async de
usuario y super admin, conservando la fijación del tenant en la tarea llamadora,
y derivar con medición una capacidad de threads segura frente al pool de
conexiones. No iniciar la medición final ni el cierre 2.6 en el mismo turno.

### Subcapa 2.5: resultado

`get_current_user` conserva su envoltura async, la prioridad Bearer/cookie y la
validación JWT. Solo sus dos tramos síncronos de DB cruzan por separado con
`starlette.concurrency.run_in_threadpool`: primero el estado público del tenant;
después, tras fijar `tenant_schema_var` en la tarea llamadora, la revalidación
del usuario dentro del schema tenant. Esta separación es obligatoria porque una
mutación del `ContextVar` hecha en un worker no regresa al caller. La dependencia
de super admin también permanece async y envía únicamente
`validate_super_admin` al mismo offload estándar; su contexto `public` se fija y
restaura dentro del worker.

El inventario completo de los caminos HTTP registrados encontró un máximo
estático `H=2` conexiones simultáneas retenidas por un worker. Los dos casos son
`PUT /tipos-pagos/{id}/cursos` y
`PUT /estudiantes/{estudiante_id}/valores-pago-personalizados/{tipo_pago_id}`:
cada controller conserva la conexión exterior hasta evaluar una lectura final
que abre la segunda. No se corrigieron esos controllers porque sus contratos y
transacciones pertenecen a otro dominio. No se encontró un camino HTTP con tres
checkouts solapados, un generador que retenga DB ni un consumidor HTTP de DB
fuera del limitador compartido después de los tres offloads; la reserva HTTP
actual es por ello `R=0`.

La capacidad se deriva antes del `yield` del `lifespan` como
`T=floor((DB_POOL_MAX_CONNECTIONS-R)/H)`. Con el pool actual, `T=floor(10/2)=5`.
Se configura el limitador por defecto de AnyIO que comparten FastAPI, Starlette
y los offloads explícitos; no se creó un limitador privado. Un pool menor de dos
conexiones hace fallar el arranque porque no puede sostener el pico observado.
La garantía cubre las rutas registradas del proceso y su event loop. Llamadas
directas desde threads/scripts, varios event loops que compartan el mismo pool,
plugins o futuros consumidores background requieren reauditar `H` y `R`.

La prueba con `ThreadedConnectionPool` real y conexiones falsas confirmó dos
oleadas de cinco workers, dos leases por worker, pico diez, cero `PoolError` y
cero leases finales. El control con seis tokens reprodujo exactamente dos
`PoolError`. El mismo limitador también acota a cinco los trabajos sync sin DB,
incluidos potencialmente `UploadFile`, `FileResponse` y storage: evita competir
sin límite por DB, pero puede aumentar su tiempo de cola bajo carga y queda como
riesgo operativo a observar en staging.

La auditoría del runtime corrigió una omisión histórica de 2.0: existe
`GET /uploads/{file_path:path}` en `app/main.py`. El estado actual correcto es
**140 APIRoutes**, 139 sync y una async (`/branding/logo`); 134 atraviesan
`get_current_user`, cuatro `get_current_super_admin`, y solo login/logout quedan
fuera. Por tanto eran 138/140, no 137/139, los caminos con el bloqueo común de
autenticación antes de 2.5. Los números de 2.0 se conservan como registro de la
auditoría histórica y esta entrada los reconcilia sin reescribirla.

El arnés nuevo `scripts/measure_auth_concurrency.py` usa JWT real y dobles solo
para las dos operaciones DB. Antes del cambio reprodujo cinco rondas con mediana
total 223,811 ms, heartbeat retrasado 203,777 ms, solapamiento máximo uno y
ambas fronteras en el event loop. Después del cambio, el mismo arnés dio mediana
103,909 ms, retraso 6,667 ms, solapamiento dos y ambas fronteras en workers,
con tenants A/B y contexto exterior restaurados. Este par es evidencia dirigida
de 2.5; no se equipara a la línea base de 2.0, que usó un arnés distinto. La
medición final de cierre y su interpretación permanecen reservadas para 2.6.

| Comprobación | Resultado |
|---|---|
| Línea base existente dirigida | 58 pasaron, 5 warnings conocidos |
| Caracterización previa de contratos y pico anidado | 6 pasaron, 5 warnings conocidos |
| Pruebas nuevas finales | 23 pasaron, 5 warnings conocidos |
| Conjunto dirigido ampliado | 81 pasaron, 5 warnings conocidos |
| Estabilidad concurrente y capacidad | 10 rondas; 60/60 casos correctos antes del último caso Bearer |
| Compuerta global final fuera del sandbox | 477 pruebas, 5 warnings conocidos |
| Ruff | `All checks passed!` |
| `pip check` | `No broken requirements found.` |

### Siguiente subcapa: 2.6, trabajo exacto

Ejecutar únicamente la medición posterior formal y el cierre de capa: repetir y
analizar el procedimiento reproducible acordado, ejecutar la compuerta global,
documentar staging, rollback y verificación manual, actualizar el índice maestro
y dejar la capa 3 en espera. No activar la capa 3 ni implementar trabajo suyo.

### Subcapa 2.6: resultado y cierre

La medición formal se ejecutó sobre `main`, `HEAD 225f80e`, con el mismo stack
registrado en 2.0: Python 3.14.3, FastAPI 0.136.1, Starlette 1.0.0, AnyIO
4.13.0, psycopg2-binary 2.9.12 y pytest 9.0.3. El comando reproducible fue:

`.\venv\Scripts\python.exe -B scripts\measure_auth_concurrency.py --runs 5 --validation-ms 100 --heartbeat-ms 20 --json`

| Ronda | Total ms | Retardo heartbeat ms | Solapamiento | Estado y validación |
|---:|---:|---:|---:|---|
| 1 | 108,722 | 6,980 | 2 | worker / worker |
| 2 | 101,878 | 2,869 | 2 | worker / worker |
| 3 | 103,319 | 4,471 | 2 | worker / worker |
| 4 | 102,093 | 4,590 | 2 | worker / worker |
| 5 | 101,564 | 1,101 | 2 | worker / worker |

La mediana formal fue **102,093 ms** total y **4,471 ms** de retardo adicional
del heartbeat. Las cinco rondas preservaron A→A/B→B, el contexto exterior,
ambas fronteras en workers y solapamiento dos. Frente a la línea previa del
mismo arnés en 2.5 —223,811 ms y 203,777 ms, solapamiento uno en el event
loop— son reducciones observadas de 54,4 % y 97,8 %. Los tiempos no son un SLO
ni una prueba de rendimiento operativo: el arnés usa JWT y autenticación reales,
pero dobles de DB y ninguna red. La línea histórica de 2.0 usó otro arnés y no
se compara temporalmente con estas cifras.

La compuerta final fuera del sandbox terminó en exit 0: **477 pruebas**, los 5
warnings deprecatorios conocidos, Ruff correcto y `pip check` sin dependencias
rotas. Las 81 pruebas dirigidas de autenticación, tenant, sesión, pool y
capacidad también pasaron. No se modificó código, pruebas, scripts,
configuración ni workflow en 2.6; el cambio de cierre es exclusivamente esta
bitácora y el índice maestro.

#### Plan de staging

No fue ejecutado en este turno. Antes de publicar, usar un entorno no
productivo con la misma topología por proceso y variables representativas:

1. desplegar el commit revisado sin migraciones ni cambios de schema;
2. confirmar al arrancar el log `Shared threadpool limited to 5 workers for DB
   pool max 10` —o el valor derivado del `DB_POOL_MAX_CONNECTIONS` de staging—;
3. ejecutar autenticación Bearer y cookie en al menos dos tenants, además del
   flujo de super admin, y verificar 401/403/200 sin mezcla de datos;
4. probar reportes, dashboard, plan de clases y carga de branding, incluidos un
   error/rollback y un borrado de imagen;
5. aplicar carga controlada concurrente a autenticación y a las dos rutas que
   pueden retener dos conexiones, observando latencias, cola, `PoolError`, uso
   del pool y timeouts; no usar producción para esta prueba;
6. observar también descargas, multipart y storage porque comparten los cinco
   tokens aunque no consuman DB;
7. repetir `scripts/verify.py` en el artefacto exacto y conservar evidencia del
   run. GitHub Actions continúa **no verificada** para estos commits locales
   mientras no exista un push autorizado y un run asociado.

#### Rollback

No se ejecutó. La capa no agrega migraciones, tablas ni transformación de datos,
por lo que el rollback es de aplicación:

1. detener el rollout y volver al artefacto/commit anterior a la capa 2,
   `b24cb8d3f1a8fa1d48699ed5732d4013ab6fe7f9`, o revertir en orden inverso los
   commits posteriores de la capa una vez publicados;
2. reiniciar todos los procesos para restaurar el código y el limitador anterior;
3. no ejecutar migraciones ni manipular datos como parte del rollback;
4. repetir smoke tests de login cookie/Bearer, tenant A/B, super admin, una
   lectura DB, una escritura DB y un archivo;
5. si el problema es únicamente cola del threadpool, no elevar tokens por
   encima de `floor((maxconn-R)/H)` sin reauditar `H`, `R` y los consumidores;
   preferir rollback o una nueva calibración revisada.

Revertir solo `app/main.py` y conservar los nuevos offloads reabriría el riesgo
de hasta 40 workers compitiendo por 10 conexiones. Revertir solo los offloads
restauraría bloqueo del event loop. El rollback debe tratar la capa como una
unidad coherente.

#### Verificación manual posterior

No se ejecutó porque no hubo deploy. En staging, comprobar y conservar evidencia
de:

- cookie: middleware entra sin tenant, autenticación fija el tenant correcto y
  lo restaura al terminar;
- Bearer: el contexto sembrado se conserva durante la consulta pública y el
  worker tenant;
- dos tenants concurrentes no intercambian schema, payload ni rutas de storage;
- super admin consulta `public` sin filtrar ese contexto al caller;
- 403 de tenant suspendido no inicia validación tenant; usuario inválido sigue
  401 con `WWW-Authenticate`, y errores DB inesperados siguen como 500;
- cancelación/desconexión no devuelve una conexión al pool antes del cleanup;
- el pico de conexiones no supera el pool ni aparecen `PoolError`; y
- archivos, reportes, dashboard y plan de clases conservan payloads, permisos,
  orden de efectos y status codes observados.

#### Riesgos y verificaciones que permanecen abiertas

- `DB_STATEMENT_TIMEOUT_MS` sigue pendiente de calibración operativa desde la
  capa 1 y no se marca cumplido.
- `H=2` y `R=0` describen las rutas HTTP y el proceso/event loop inventariados;
  nuevos threads, background jobs, plugins, rutas o varios event loops exigen
  reauditar la fórmula.
- El límite compartido de cinco workers puede aumentar la cola de storage,
  multipart y archivos; solo staging con carga representativa puede cuantificarlo.
- La cancelación protegida puede completar trabajo después de una desconexión.
- Las ventanas TOCTOU y la no atomicidad entre storage y DB permanecen como
  contratos/riesgos preexistentes deliberadamente no rediseñados.
- Las versiones del stack están limitadas solo por mínimos; una resolución
  distinta exige repetir medición y compuerta.
- No hubo push, deploy, producción, migraciones ni ejecución de CI remoto.

La capa 2 queda **cerrada**. La capa 3 permanece en espera y no existe una capa
activa. Una orden genérica de continuar no autoriza activarla; su bitácora solo
puede crearse desde la plantilla tras una orden explícita del usuario.

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
- El inventario divide la migración por familia y tipo de efecto: reportes,
  dashboard, lecturas de plan de clases, escrituras/efectos de plan de clases,
  branding, dependencias y cierre. La alternativa de migrar los 24 handlers en
  una sola tanda se descarta por volumen y por mezclar lecturas, transacciones y
  storage.
- Los 23 handlers async sin `await` se migrarán a `def` para usar el offload que
  FastAPI ya gobierna. `branding.subir_logo` no admite esa transformación porque
  sí espera la lectura del archivo; su tramo síncrono se tratará aparte.
- La primitiva admitida para offload explícito será la que usa el propio stack:
  `starlette.concurrency.run_in_threadpool` / `anyio.to_thread.run_sync`. Se
  descarta `asyncio.run_in_executor` crudo porque el control empírico perdió los
  dos tenants.
- Las dependencias de autenticación conservarán una envoltura async que fije el
  tenant en la tarea llamadora antes del salto. Convertirlas simplemente a `def`
  queda descartado porque las mutaciones del `ContextVar` hechas en un worker no
  regresan y romperían la autenticación por cookie.
- Se conserva la cancelación protegida por defecto; no se usará
  `abandon_on_cancel=True` para trabajo que pueda poseer una conexión.
- El limitador compartido no se cambia durante las tandas parciales. Cuando toda
  la DB del camino HTTP esté fuera del event loop, 2.5 debe medir cuántas
  conexiones puede retener cada worker y derivar una capacidad segura frente a
  `DB_POOL_MAX_CONNECTIONS`; no se asumirá que diez conexiones implican diez
  tokens. Hacerlo antes mezclaría workers limitados con accesos DB todavía fuera
  del limitador.
- Reportes es la primera tanda porque son cinco handlers de solo lectura, ninguno
  contiene `await` y sus controllers ya son síncronos. Es el diff de producto más
  pequeño que prueba la transformación normal de FastAPI.
- Dashboard conserva la misma estrategia en 2.2: siete handlers de lectura sin
  `await` pasan a `def`, sin envolver controllers ni crear una abstracción. Sus
  guards permanecen en el mismo orden y fuera de los mismos bloques `try` para
  no convertir 403 o 422 en 400.
- La caracterización de dashboard usa las rutas registradas y compara
  dependencias por identidad, no por nombre u orden. Esto protege el wiring sin
  acoplarse innecesariamente al orden interno de FastAPI.
- Las cinco lecturas de plan de clases conservan en 2.3a la misma transformación
  declarativa: FastAPI gobierna el offload de sus cuerpos `def` y no se envuelve
  ningún controller, service, repositorio o guard.
- Las referencias de imágenes leídas por estas rutas son valores del payload;
  ninguno de los cinco caminos usa storage. Por eso la caracterización conserva
  esas referencias sin introducir mocks ni abstracciones de archivo. Los efectos
  reales permanecen reservados para 2.3b.
- Los seis efectos de plan de clases también se migran de forma declarativa en
  2.3b porque ninguno contiene `await`: lectura de `UploadFile.file`, storage,
  guards y PostgreSQL son síncronos. El parseo multipart del framework permanece
  antes del handler; no se cambia a `await UploadFile.read()` ni se crea una
  envoltura propia.
- El orden storage/DB se conserva aunque no sea atómico. Crear guarda archivos
  antes del UPSERT y limpia los nuevos best-effort ante error; eliminar confirma
  primero la mutación DB y luego intenta borrar el archivo. Rediseñar esa
  consistencia pertenece a otra decisión funcional, no a concurrencia.
- Branding conserva su frontera async real: validar y esperar
  `UploadFile.read()`. Solo bytes y metadatos ya leídos cruzan mediante
  `run_in_threadpool` a un helper privado local; allí se obtiene el tenant y se
  ejecutan storage, DB y borrado. Convertir toda la ruta a `def`, pasar el
  `UploadFile` al worker o crear una abstracción compartida cambiaría una
  frontera que no necesita rediseño.
- La lectura de 2.0 se amplió solo a cinco funciones de `tenant_status.py` y
  `super_admin.py` descubiertas como dependencias HTTP opacas. No se leyó el
  resto de esos dominios.
- La calibración pendiente de `DB_STATEMENT_TIMEOUT_MS` permanece registrada en
  la capa 1 y no se da por cumplida al activar esta capa.
- En 2.5 se preserva `get_current_user` como coroutine y se usan dos offloads
  separados. El `set(tenant)` debe ocurrir en el caller entre ambos; agrupar el
  chequeo público, la mutación y la validación en un solo worker rompería cookie.
- El limitador por defecto compartido se deriva con `H=2`, `R=0` y el máximo
  configurado del pool: `floor(maxconn/2)`. La invariante procede del inventario
  completo de rutas HTTP y debe reauditarse si cambia una cadena DB, aparece un
  consumidor fuera de AnyIO o se comparte el pool entre varios event loops.
- Se limita el threadpool común, no solo DB, porque únicamente esa frontera
  gobierna tanto handlers `def` como los offloads explícitos. Un limitador DB
  privado no habría protegido los handlers sync que comparten el mismo pool.

## Riesgos

- La propagación funciona con AnyIO/Starlette en el stack medido, pero no con un
  executor crudo. El riesgo se mitiga prohibiendo ese camino y fijándolo con una
  prueba de dos tenants concurrentes antes de la primera migración.
- AnyIO permite hoy 40 workers y el pool solo 10 conexiones. Liberar de golpe
  los 137 bloqueos de autenticación puede convertir el cuello de botella actual
  en `PoolError`; por eso autenticación y el límite global se dejan para 2.5,
  después de las rutas.
- Un worker puede retener más de una conexión si una cadena anidada abre otra
  antes de devolver la primera. Fijar diez tokens solo porque `maxconn=10` sería
  inseguro hasta medir ese máximo.
- Reducir el limitador compartido también afecta `FileResponse`, `UploadFile`,
  tareas background síncronas y otras operaciones internas. Un valor seguro para
  DB puede degradar storage; debe medirse y documentarse, no suponerse.
- Cancelar la coroutine no detiene un thread ya iniciado. Abandonarlo liberaría
  al llamador mientras la conexión sigue viva; se conserva el comportamiento
  protegido y los timeouts de la capa 1 como límite del trabajo bloqueante.
- Dos consumidores de storage leen el `ContextVar` sin la validación fail-closed
  de `get_connection`; una pérdida puede crear una ruta con `None`. Las pruebas
  deben observar también ese punto antes de tocar branding o plan de clases.
- Las versiones del stack flotan por límites inferiores. Una actualización de
  FastAPI, Starlette o AnyIO entre mediciones invalida la comparación aunque el
  código del repositorio no cambie.
- Las pruebas herméticas pueden demostrar aislamiento de contexto, pero no por sí
  solas el rendimiento bajo carga ni el comportamiento de un endpoint agrupado
  real.
- `DB_STATEMENT_TIMEOUT_MS` sigue sin calibrarse contra consultas pesadas. Es un
  riesgo operativo heredado, no evidencia de que la capa 2 esté incompleta.
- Después de 2.2, los cuerpos de dashboard ya no bloquean el event loop, pero
  sus dependencias async de autenticación todavía pueden hacerlo antes de entrar
  al worker. No debe presentarse esta tanda como la eliminación completa del
  bloqueo de una request.
- Después de 2.3a, también están fuera del event loop los guards y lecturas
  ejecutados dentro de sus cinco handlers, pero no la DB síncrona de las
  dependencias async previas. Las pruebas de ruta invocan handlers directamente;
  el cruce real de tenant al threadpool se sustenta por separado en el contrato
  concurrente de 2.1.
- Los pares guard/lectura, conteo/listado y existencia/observaciones conservan
  conexiones o consultas secuenciales y pueden observar cambios intermedios.
  Es una ventana preexistente que 2.3a no rediseña.
- En creación de plan, cada archivo se lee completo antes de verificar 5 MiB y
  `content_type` es metadata del cliente. Si falla el cleanup puede quedar un
  archivo huérfano; reemplazar una imagen tampoco elimina aquí el archivo
  anterior. Son riesgos heredados que 2.3b caracteriza pero no corrige.
- En borrado de imagen, DB y storage no forman una transacción distribuida. Un
  fallo del borrado físico puede dejar un huérfano después del commit; un slot
  ya nulo puede mutar versión/estado en el camino profesor y después producir el
  404 existente. El orden y la respuesta se conservan deliberadamente.
- Los guards de ownership y las mutaciones posteriores usan checkouts separados,
  por lo que mantienen ventanas TOCTOU preexistentes. Mover todo al worker no
  vuelve atómicas esas operaciones.
- Tras 2.3b, un cliente desconectado puede dejar completar una escritura en el
  worker porque la cancelación protegida espera cleanup. Es la semántica elegida
  para no abandonar conexiones o archivos vivos y no una garantía de cancelación
  de la mutación.
- En branding, el archivo completo se mantiene en memoria antes de comprobar
  2 MiB y `content_type` sigue siendo metadata del cliente. Storage precede a
  DB: si falla la transacción, el objeto nuevo puede quedar huérfano; si falta
  la fila de branding, el UPDATE puede no referenciarlo; cargas concurrentes al
  mismo slot tampoco se serializan. El borrado anterior continúa best-effort.
  Son riesgos preexistentes conservados por 2.4, no correcciones omitidas del
  offload.
- Después de 2.4 ya no queda storage o DB síncrona sin offload en los cuerpos
  async inventariados. Los 137 handlers que atraviesan autenticación async
  siguen expuestos al bloqueo común hasta 2.5; 2.4 no se presenta como solución
  completa de la request.
- Después de 2.5, la DB síncrona de autenticación ya no bloquea el event loop,
  pero hasta cinco workers pueden quedar esperando consultas o storage. La
  cancelación continúa protegida y una desconexión puede dejar completar el
  trabajo antes de liberar la conexión.
- El techo `H=2` y la reserva `R=0` son invariantes del inventario HTTP actual,
  no una garantía universal para llamadas directas, scripts, plugins, nuevos
  background jobs o varios event loops que compartan el pool. Cualquiera de
  esos cambios exige recalcular la capacidad antes de desplegarlo.
- Reducir el limitador compartido de 40 a 5 también serializa trabajo sync sin
  DB, como lectura de archivos, multipart y storage. El test confirma el límite;
  el impacto de cola bajo carga real debe observarse en staging.
- `DB_POOL_MAX_CONNECTIONS=1` deja de ser una configuración arrancable porque
  no soporta los dos leases simultáneos observados. Este fallo temprano evita
  publicar una capacidad que no puede ser segura.

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

### 2026-08-12 — subcapa 2.0

- Rama acordada: `main`; árbol **limpio** antes de editar.
- Commit observado: `c6483e483080c4e9961265765a8cc6a7d95ea041`,
  un commit local por delante de la referencia local `origin/main`.
- Comparación con el base: el único commit posterior a `b24cb8d` es la activación
  de la capa 2 y está explicado en la entrada anterior. Su diff contiene solo
  `README.md` y esta bitácora, por lo que el árbol ejecutable probado es idéntico
  al base. No hay divergencia.
- Archivos modificados: únicamente esta bitácora.
- Código de producto, pruebas, configuración, dependencias y workflow
  modificados: **ninguno**.
- Compuerta, primera pasada dentro del sandbox: exit 1 por seis errores de setup
  causados por `WinError 5` sobre el temporal de pytest; 328 pruebas sí pasaron,
  Ruff y `pip check` fueron correctos.
- Compuerta repetida con autorización fuera del sandbox: **exit 0**; 334 pruebas
  correctas, 5 warnings conocidos, Ruff correcto y dependencias íntegras.
- Pruebas específicas existentes: **43 pasaron** en 0,43 s.
- Inventario AST: 139 handlers; 115 sync, 24 async; 137 atraviesan una dependencia
  async con DB síncrona; los 24 async alcanzan además DB síncrona desde su cuerpo;
  cero mecanismos explícitos de offload.
- Contexto, stress de 1.000 pares con `run_in_threadpool`: 1.000 correctos, cero
  pérdidas, mezclas o fugas. Control con executor crudo: tenant perdido en ambos
  workers. Mutación dentro del worker: no regresó al llamador.
- Capacidad medida: 40 tokens AnyIO frente a 10 conexiones máximas del pool.
- Cancelación medida: AnyIO y Starlette esperaron ~101–102 ms por un worker de
  100 ms pese a un cancel scope de 20 ms; `abandon_on_cancel=True` volvió en 21
  ms y dejó el thread en ejecución. Se conserva la primera semántica.
- Línea base de bloqueo sobre `get_current_user`, cinco repeticiones con dobles:
  mediana total 224 ms, heartbeat retrasado 204 ms, máximo solapamiento 1 y todas
  las validaciones ejecutadas en el thread del event loop.
- `git diff --check`: exit 0; solo el aviso informativo de conversión LF a CRLF
  la próxima vez que Git toque el archivo.
- Alcance final del diff: exclusivamente esta bitácora.
- Estado: **2.0 cerrada**. No se inició 2.1.
- Siguiente acción exacta: ejecutar **2.1**, agregando primero el contrato
  concurrente del tenant y migrando solo las cinco rutas de reportes de
  `async def` sin `await` a `def`; detenerse antes de dashboard.

### 2026-08-12 — subcapa 2.1

- Modo de acceso: mismo checkout local; rama `main` y árbol limpio antes de
  editar.
- Commit observado: `e6301d06df7a4d04c94195702bb3d116c903a53d`, dos
  commits locales por delante de `origin/main` y del base de la capa.
- Continuidad: `b24cb8d` es ancestro. Los únicos commits posteriores son
  `c6483e4` (activación) y `e6301d0` (2.0), ambos documentales y explicados en
  esta bitácora; el diff acumulado previo no contenía código ejecutable.
- Caracterización previa: 16 pruebas pasaron con las rutas todavía async.
- Código de producto: solo `app/routes/reportes.py`; cinco declaraciones
  `async def` pasaron a `def`. Controllers, SQL, transacciones, autenticación,
  permisos, paths, payloads, status codes y parámetros no cambiaron.
- Pruebas: `tests/test_reportes_pagination.py` amplió cobertura de delegación,
  respuestas y errores; `tests/test_tenant_context_concurrency.py` fijó
  propagación, aislamiento, restauración del middleware, control negativo y
  cancelación protegida.
- Archivos modificados: `app/routes/reportes.py`,
  `tests/test_reportes_pagination.py`,
  `tests/test_tenant_context_concurrency.py` y esta bitácora.
- Comandos ejecutados:
  - caracterización previa y pruebas posteriores:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_reportes_pagination.py tests/test_tenant_context_concurrency.py`;
  - específicas ampliadas:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_reportes_pagination.py tests/test_tenant_context_concurrency.py tests/test_anulaciones_financieras.py::test_reporte_general_excluye_pagos_anulados_de_totales tests/test_pagos_adelantados.py::test_reporte_curso_aplica_solo_adelantos_maduros_y_no_los_duplica`;
  - estabilidad:
    `$testRuns = 1..20; foreach ($testRun in $testRuns) { .\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_tenant_context_concurrency.py; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }`;
  - lint del alcance:
    `.\venv\Scripts\python.exe -m ruff check app/routes/reportes.py tests/test_reportes_pagination.py tests/test_tenant_context_concurrency.py`;
  - compuerta global, que también ejecuta Ruff y `pip check`:
    `.\venv\Scripts\python.exe scripts\verify.py`;
  - alcance y whitespace: `git status --short --branch`,
    `git diff --name-only`, `git diff --check` y
    `git diff --no-index --check -- NUL tests/test_tenant_context_concurrency.py`.
- Pruebas específicas posteriores: 21 pasaron; con los dos casos existentes de
  controllers financieros, 23 pasaron.
- Estabilidad concurrente: 20 rondas consecutivas, **60/60 casos correctos**.
- Compuerta dentro del sandbox: 343 pasaron y seis errores de setup de uploads
  por el `WinError 5` conocido; Ruff y `pip check` correctos.
- Compuerta fuera del sandbox: **exit 0**, 349 pruebas, 5 warnings conocidos,
  Ruff correcto y dependencias íntegras.
- `git diff --check`: exit 0; únicamente avisos informativos LF→CRLF para
  archivos existentes. El alcance final contiene solo los cuatro archivos
  enumerados y no incluye dashboard. La comprobación `--no-index` del archivo
  nuevo terminó en exit 1 porque existe una diferencia frente a `NUL`, como es
  esperado, y no reportó errores de whitespace; solo el mismo aviso LF→CRLF.
- Auditoría independiente: sin hallazgos altos o medios; confirmó dos workers
  solapados, A→A/B→B, restauración mediante el middleware real, executor
  dedicado y cancelación determinista. La prueba invoca directamente la función
  real del middleware; no se presenta como prueba HTTP end-to-end.
- Estado: **2.1 cerrada**. No se inició dashboard ni 2.2.
- Siguiente acción exacta: ejecutar **2.2**, caracterizando y migrando únicamente
  las siete lecturas de dashboard de `async def` sin `await` a `def`.

### 2026-08-12 — subcapa 2.2

- Modo de acceso: mismo checkout local; rama `main` y árbol limpio antes de
  editar.
- Commit observado: `d2f7c9dfe260cdb11e1a2d51ad92fff6ff938e65`, tres
  commits locales por delante de `origin/main` y del base de la capa.
- Continuidad: `b24cb8d` es ancestro; `c6483e4`, `e6301d0` y `d2f7c9d`
  corresponden respectivamente a activación, 2.0 y 2.1. Sus archivos y
  resultados están explicados en esta bitácora; no había cambios pendientes ni
  divergencia antes de iniciar 2.2.
- Código de producto: solo `app/routes/dashboard.py`; siete declaraciones
  `async def` pasaron a `def`. No cambiaron controllers, SQL, transacciones,
  permisos, tenant, ownership, paths, parámetros, status codes ni payloads.
- Pruebas: se creó `tests/test_dashboard_routes.py`; se conservaron
  `tests/test_dashboard_controlador.py`, `tests/test_permissions.py` y el
  contrato concurrente tenant de 2.1.
- Archivos modificados: `app/routes/dashboard.py`,
  `tests/test_dashboard_routes.py` y esta bitácora.
- Comandos ejecutados:
  - línea base dirigida:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_dashboard_controlador.py tests/test_tenant_context_concurrency.py`;
  - caracterización previa y posterior:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_dashboard_routes.py tests/test_dashboard_controlador.py tests/test_tenant_context_concurrency.py`;
  - específicas ampliadas:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_dashboard_routes.py tests/test_dashboard_controlador.py tests/test_permissions.py tests/test_tenant_context_concurrency.py`;
  - lint del alcance:
    `.\venv\Scripts\python.exe -m ruff check app/routes/dashboard.py tests/test_dashboard_routes.py`;
  - compuerta global:
    `.\venv\Scripts\python.exe scripts\verify.py`;
  - estructura y alcance: `git diff --unified=0 -- app/routes/dashboard.py`,
    AST en memoria con `ast.parse`, `git status --short --branch`,
    `git diff --check` y
    `git diff --no-index --check -- NUL tests/test_dashboard_routes.py`.
- Línea base dirigida: 10 pasaron; caracterización previa: 38; posterior: 39;
  específicas ampliadas: **53 pasaron**.
- Compuerta fuera del sandbox: **exit 0**, 378 pruebas, 5 warnings conocidos,
  Ruff correcto y dependencias íntegras.
- `git diff --check`: exit 0; solo avisos informativos LF→CRLF para los archivos
  rastreados modificados. La comprobación `--no-index` del archivo nuevo terminó
  en exit 1 porque difiere de `NUL`, como es esperado, sin errores de
  whitespace.
- Auditorías independientes: sin hallazgos de producto. Confirmaron los siete
  pares exactos, el AST final, aislamiento tenant, orden de guards y ausencia de
  trabajo de 2.3a. Cuatro fragilidades iniciales del arnés fueron corregidas
  antes de la compuerta definitiva.
- Riesgos residuales: la autenticación async continúa haciendo DB síncrona antes
  de estos handlers; la capacidad 40 workers/10 conexiones se resolverá en 2.5
  y la cancelación protegida permanece como invariante. No se amplió ese
  alcance.
- Estado: **2.2 cerrada**. No se abrió ni modificó plan de clases ni 2.3a.
- Siguiente acción exacta: ejecutar **2.3a**, caracterizando y migrando solo los
  cinco handlers de lectura de plan de clases y deteniéndose antes de 2.3b.

### 2026-08-12 — subcapa 2.3a

- Modo de acceso: mismo checkout local; rama `main` y árbol limpio antes de
  editar.
- Commit observado: `b7d7c57a9ca5b6b8ba633d71cb4b9036a2c4b8fd`, cuatro
  commits locales por delante de `origin/main` y del base de la capa.
- Continuidad: `b24cb8d` es ancestro; `c6483e4`, `e6301d0`, `d2f7c9d` y
  `b7d7c57` corresponden respectivamente a activación, 2.0, 2.1 y 2.2. Sus
  archivos y resultados están explicados en esta bitácora; no había cambios
  pendientes ni divergencia antes de iniciar 2.3a.
- Código de producto: solo `app/routes/plan_de_clases.py`; cinco declaraciones
  `async def` pasaron a `def`: `obtener_notificaciones_planeadores`,
  `obtener_planes_por_asignacion`, `listar_planes_admin`,
  `obtener_plan_admin` y `listar_observaciones_plan`.
- Contratos conservados: paths y métodos GET, parámetros y validación,
  dependencias, roles, tenant, ownership, orden de guards, límites de excepción,
  status/detail, respuestas, SQL, conexiones y transacciones. No hubo I/O de
  storage; las referencias de imagen continúan como valores opacos del payload.
- Fuera del cambio: los seis handlers de efectos de 2.3b permanecen `async def`;
  no se modificaron controllers, services, repositorios, branding,
  autenticación, limitador, configuración ni dependencias.
- Pruebas: se creó `tests/test_plan_de_clases_routes.py`; se conservaron
  `tests/test_plan_de_clases_integridad.py`,
  `tests/test_plan_de_clases_revision.py`, `tests/test_permissions.py` y el
  contrato concurrente tenant de 2.1.
- Archivos modificados: `app/routes/plan_de_clases.py`,
  `tests/test_plan_de_clases_routes.py` y esta bitácora.
- Comandos ejecutados:
  - línea base relacionada:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider tests/test_plan_de_clases_integridad.py tests/test_plan_de_clases_revision.py tests/test_permissions.py tests/test_tenant_context_concurrency.py -q`;
  - caracterización previa y posterior:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider tests/test_plan_de_clases_routes.py -q`;
  - dirigidas antes y después del cambio:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider tests/test_plan_de_clases_routes.py tests/test_plan_de_clases_integridad.py::test_filtros_admin_agrupan_estados_internos tests/test_plan_de_clases_integridad.py::test_historial_asignacion_aplica_paginacion_opcional tests/test_plan_de_clases_revision.py::test_notificaciones_admin_agrupa_eventos_no_leidos_por_profesor tests/test_plan_de_clases_revision.py::test_notificaciones_profesor_solo_lista_observaciones_propias_no_leidas tests/test_permissions.py::test_require_asignacion_access_blocks_non_owner_profesor tests/test_permissions.py::test_require_plan_de_clases_access_blocks_non_owner_profesor -q`;
  - específicas ampliadas:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider tests/test_plan_de_clases_routes.py tests/test_plan_de_clases_integridad.py tests/test_plan_de_clases_revision.py tests/test_permissions.py tests/test_tenant_context_concurrency.py -q`;
  - lint del alcance:
    `.\venv\Scripts\python.exe -m ruff check app/routes/plan_de_clases.py tests/test_plan_de_clases_routes.py`;
  - compuerta global, que también ejecuta Ruff y `pip check`:
    `.\venv\Scripts\python.exe scripts\verify.py`;
  - estructura y alcance: `git diff --unified=0 -- app/routes/plan_de_clases.py`,
    AST en memoria con `ast.parse`, `git status --short --branch`,
    `git diff --name-only -- app`, `git diff --check` y
    `git diff --no-index --check -- NUL tests/test_plan_de_clases_routes.py`.
- Línea base relacionada: 43 pasaron; caracterización previa: 16; dirigidas
  previas: 22; caracterización posterior: 17; dirigidas posteriores: 23;
  específicas ampliadas: **60 pasaron**.
- Compuerta dentro del sandbox: 389 pasaron y seis errores de setup de uploads
  por el `WinError 5` conocido; Ruff y `pip check` correctos.
- Compuerta fuera del sandbox: **exit 0**, 395 pruebas, 5 warnings conocidos,
  Ruff correcto y dependencias íntegras.
- Auditoría estructural: exactamente cinco pares `async def`/`def`; los cinco
  endpoints objetivo son `FunctionDef`, los seis de 2.3b siguen
  `AsyncFunctionDef` y bajo `app/` solo cambió la ruta autorizada.
- `git diff --check`: exit 0; solo avisos informativos LF→CRLF para los archivos
  rastreados. La comprobación `--no-index` del test nuevo terminó en exit 1 porque
  difiere de `NUL`, como es esperado, sin errores de whitespace.
- Auditorías independientes: sin defectos de producto. La primera revisión del
  arnés detectó que algunos tipos y defaults opcionales de OpenAPI no estaban
  completamente fijados; se añadieron esas aserciones, el conjunto exacto de
  paths y la llamada keyword de `limit`, y la reejecución quedó verde.
- Riesgos residuales: la DB síncrona de autenticación sigue antes de estos
  handlers; la relación 40 workers/10 conexiones queda para 2.5; la cancelación
  protegida y las ventanas secuenciales guard/lectura permanecen como
  invariantes. No se amplió ese alcance.
- Estado: **2.3a cerrada**. No se inició 2.3b.
- Siguiente acción exacta: ejecutar **2.3b**, caracterizando y migrando solo los
  seis handlers de escrituras o efectos de plan de clases y deteniéndose antes
  de 2.4.

### 2026-08-12 — subcapa 2.3b

- Modo de acceso: mismo checkout local; rama `main` y árbol limpio antes de
  editar.
- Commit observado: `297aac67fb60a35180aa499024c29a247656fb45`, cinco
  commits locales por delante de `origin/main` y del base de la capa.
- Continuidad: `b24cb8d` es ancestro; `c6483e4`, `e6301d0`, `d2f7c9d`,
  `b7d7c57` y `297aac6` corresponden respectivamente a activación, 2.0, 2.1,
  2.2 y 2.3a. Sus archivos y resultados están explicados en esta bitácora; no
  había cambios pendientes ni divergencia antes de iniciar 2.3b.
- Código de producto: solo `app/routes/plan_de_clases.py`; seis declaraciones
  `async def` pasaron a `def`: `crear_plan_de_clases`,
  `eliminar_imagen_plan_profesor`, `actualizar_revision_plan`,
  `crear_observacion_plan`, `marcar_observacion_vista` y
  `eliminar_imagen_plan_admin`.
- Contratos conservados: paths y métodos, multipart y JSON, parámetros y
  validación, dependencias, roles, tenant, ownership, orden de guards y efectos,
  status/detail, payloads, storage, SQL, locks, commit/rollback y cleanup.
- Fuera del cambio: las cinco lecturas de 2.3a permanecen `def`; branding sigue
  `async def`. No se modificaron controllers, services, repositorios, storage,
  autenticación, limitador, configuración ni dependencias.
- Pruebas: se creó `tests/test_plan_de_clases_effect_routes.py`; se conservaron
  `tests/test_plan_de_clases_routes.py`,
  `tests/test_plan_de_clases_integridad.py`,
  `tests/test_plan_de_clases_revision.py`, `tests/test_permissions.py`,
  `tests/test_uploads_permissions.py` y el contrato concurrente tenant de 2.1.
- Archivos modificados: `app/routes/plan_de_clases.py`,
  `tests/test_plan_de_clases_effect_routes.py` y esta bitácora.
- Comandos ejecutados:
  - línea base relacionada, dentro y fuera del sandbox:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider tests/test_plan_de_clases_integridad.py tests/test_plan_de_clases_revision.py tests/test_permissions.py tests/test_uploads_permissions.py tests/test_tenant_context_concurrency.py tests/test_plan_de_clases_routes.py -q`;
  - caracterización previa y posterior:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider tests/test_plan_de_clases_effect_routes.py -q`;
  - dirigidas antes y después del cambio:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider tests/test_plan_de_clases_effect_routes.py tests/test_plan_de_clases_integridad.py::test_guardar_plan_usa_un_solo_upsert_atomico tests/test_plan_de_clases_integridad.py::test_guardar_plan_valida_la_version_esperada_dentro_de_la_transaccion tests/test_plan_de_clases_integridad.py::test_guardar_plan_rechaza_una_version_desactualizada_sin_escribir tests/test_plan_de_clases_integridad.py::test_controlador_limpia_imagenes_nuevas_si_hay_conflicto tests/test_plan_de_clases_integridad.py::test_eliminar_evidencia_de_correccion_no_notifica_de_nuevo tests/test_plan_de_clases_revision.py::test_marcar_plan_visto_bloquea_y_valida_version tests/test_plan_de_clases_revision.py::test_revision_rechaza_version_desactualizada_sin_actualizar tests/test_plan_de_clases_revision.py::test_revision_con_comentario_guarda_mensaje_y_aprobacion_juntos tests/test_plan_de_clases_revision.py::test_observacion_queda_ligada_a_version_y_actualiza_estado tests/test_plan_de_clases_revision.py::test_controlador_convierte_conflicto_de_version_en_http_409 tests/test_permissions.py::test_require_asignacion_access_blocks_non_owner_profesor tests/test_permissions.py::test_require_plan_de_clases_access_blocks_non_owner_profesor -q`;
  - específicas ampliadas:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider tests/test_plan_de_clases_effect_routes.py tests/test_plan_de_clases_integridad.py tests/test_plan_de_clases_revision.py tests/test_permissions.py tests/test_uploads_permissions.py tests/test_tenant_context_concurrency.py tests/test_plan_de_clases_routes.py -q`;
  - lint del alcance:
    `.\venv\Scripts\python.exe -m ruff check app/routes/plan_de_clases.py tests/test_plan_de_clases_effect_routes.py`;
  - compuerta global, que también ejecuta Ruff y `pip check`:
    `.\venv\Scripts\python.exe scripts\verify.py`;
  - estructura y alcance: `git diff --unified=0 -- app/routes/plan_de_clases.py`,
    AST en memoria con `ast.parse`, `git status --short --branch`,
    `git diff --name-only -- app`, `git diff --check` y
    `git diff --no-index --check -- NUL tests/test_plan_de_clases_effect_routes.py`.
- Línea base relacionada: intento en sandbox con 60 pasadas y seis errores de
  setup; repetición fuera del sandbox: 66 pasaron. Caracterización inicial
  previa: 38; dirigidas iniciales previas: 50; posterior inicial: 39/51. Tras
  endurecer detalles canónicos: **42 propias**, **54 dirigidas** y **108
  ampliadas**.
- Compuerta global fuera del sandbox: **exit 0**, 437 pruebas, 5 warnings
  conocidos, Ruff correcto y dependencias íntegras.
- Auditoría estructural: exactamente seis pares `async def`/`def`; los once
  endpoints de plan de clases son `FunctionDef`, branding sigue
  `AsyncFunctionDef` y bajo `app/` solo cambió la ruta autorizada.
- `git diff --check`: exit 0; solo avisos informativos LF→CRLF para los archivos
  rastreados modificados. La comprobación `--no-index` del test nuevo terminó en
  exit 1 porque difiere de `NUL`, como es esperado, sin errores de whitespace.
- Auditorías independientes: sin defectos de producto. La primera revisión del
  arnés pidió fijar métodos únicos y detalles canónicos completos de los 404/409;
  también se hizo más tolerante la lectura OpenAPI y se usó un `UploadFile` real
  en el happy path. La reauditoría quedó sin bloqueantes.
- Riesgos residuales: multipart se parsea antes del handler; storage y DB no son
  atómicos; cleanup y delete son best-effort; el archivo se lee completo antes
  del límite; ownership/mutación conservan checkouts separados; autenticación
  sigue bloqueando y la relación 40 workers/10 conexiones queda para 2.5.
- Estado: **2.3b cerrada**. No se inició 2.4.
- Siguiente acción exacta: ejecutar **2.4**, caracterizando y migrando solo el
  tramo síncrono de storage y DB de branding y deteniéndose antes de 2.5.

### 2026-08-12 — subcapa 2.4

- Modo de acceso: mismo checkout local; rama `main` y árbol limpio antes de
  editar.
- Commit observado: `d82c78fda482d3b5b91575780e0b5747a1ea9a4e`, seis
  commits locales por delante de `origin/main` y del base de la capa.
- Continuidad: `b24cb8d` es ancestro; `c6483e4`, `e6301d0`, `d2f7c9d`,
  `b7d7c57`, `297aac6` y `d82c78f` corresponden respectivamente a activación,
  2.0, 2.1, 2.2, 2.3a y 2.3b. Sus archivos y resultados están explicados en
  esta bitácora; no había cambios pendientes ni divergencia antes de iniciar
  2.4.
- Código de producto: solo `app/controllers/branding_controller.py`. La ruta y
  el controller permanecen async; las validaciones, `await archivo.read()` y el
  límite siguen en la tarea llamadora. Se extrajo únicamente la cola síncrona a
  `_guardar_logo_leido` y se la espera con
  `starlette.concurrency.run_in_threadpool`.
- Contratos conservados: `POST /branding/logo`, multipart, query, dependencias
  de usuario y admin activo, tenant, ambos slots y columnas, payload, status y
  detalles, SQL, parámetros, `commit`/`rollback`, orden storage/DB/borrado y
  propagación de errores.
- Fuera del cambio: `app/routes/branding.py`, storage compartido,
  autenticación, super admin, pool, limitador, configuración, dependencias y
  2.5. No se usó executor crudo ni cancelación abandonable.
- Pruebas: se creó `tests/test_branding_upload_boundary.py`; se conservaron
  `tests/test_branding_controlador.py`, `tests/test_uploads_permissions.py` y el
  contrato concurrente tenant/cancelación de 2.1.
- Archivos modificados: `app/controllers/branding_controller.py`,
  `tests/test_branding_upload_boundary.py` y esta bitácora.
- Comandos ejecutados:
  - línea base relacionada, dentro y fuera del sandbox:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_branding_controlador.py tests/test_uploads_permissions.py tests/test_tenant_context_concurrency.py`;
  - caracterización previa al cambio:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_branding_upload_boundary.py tests/test_branding_controlador.py -k "not real_workers and not worker_cancellation"`;
  - específicas finales:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_branding_upload_boundary.py tests/test_branding_controlador.py`;
  - conteo de la caracterización nueva:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider --collect-only -q tests/test_branding_upload_boundary.py`;
  - específicas ampliadas, fuera del sandbox:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_branding_upload_boundary.py tests/test_branding_controlador.py tests/test_uploads_permissions.py tests/test_tenant_context_concurrency.py`;
  - estabilidad de las fronteras sensibles:
    `$testRuns = 1..20; foreach ($testRun in $testRuns) { .\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_branding_upload_boundary.py::test_upload_sync_tail_runs_in_real_workers_with_isolated_tenants tests/test_branding_upload_boundary.py::test_upload_worker_cancellation_waits_for_db_and_cleanup; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }`;
  - lint del alcance:
    `.\venv\Scripts\python.exe -m ruff check app/controllers/branding_controller.py tests/test_branding_upload_boundary.py tests/test_branding_controlador.py`;
  - compuerta global, que también ejecuta Ruff y `pip check`, fuera del sandbox:
    `.\venv\Scripts\python.exe scripts\verify.py`;
  - estructura y alcance: AST en memoria con `ast.parse`,
    `git diff -- app/controllers/branding_controller.py`,
    `git diff -- app/routes/branding.py`, `git status --short --branch`,
    `git diff --name-only -- app`, `git diff --check` y
    `git diff --no-index --check -- NUL tests/test_branding_upload_boundary.py`.
- Línea base dentro del sandbox: 11 pasaron y seis errores de setup de uploads
  por el `WinError 5` conocido; repetición fuera: **17 pasaron**, 5 warnings
  conocidos. La caracterización previa sobre la versión inicial del arnés dio
  **22 pasadas**, con las dos poscondiciones de worker/cancelación excluidas
  antes del cambio. Después se añadió el caso del slot secundario; en el árbol
  final el mismo selector reproduce **23 pasadas y 2 deseleccionadas**.
- Verificación final: **17 casos nuevos**; junto con los ocho regresores de
  branding, **25 pasaron**. El conjunto ampliado terminó con **34 pasadas** y 5
  warnings conocidos. Las dos pruebas de scheduling completaron 20 rondas,
  **40/40 casos correctos**.
- Compuerta global fuera del sandbox: **exit 0**, 454 pruebas, 5 warnings
  conocidos, Ruff correcto y dependencias íntegras.
- Auditoría estructural: la ruta y el controller continúan
  `AsyncFunctionDef`; la ruta espera al controller y el controller conserva
  exactamente dos `await`: la lectura y el único `run_in_threadpool`. El helper
  es `FunctionDef`, obtiene el tenant dentro del worker y contiene la cola
  anterior sin cambiar su orden. Bajo `app/` solo cambió el controller
  autorizado.
- `git diff --check`: exit 0; solo avisos informativos LF→CRLF para los archivos
  rastreados modificados. La comprobación `--no-index` del test nuevo terminó en
  exit 1 porque difiere de `NUL`, como es esperado, sin errores de whitespace.
- Las pruebas son herméticas con dobles y un `UploadFile` en memoria; no se
  presentan como HTTP end-to-end ni como commit PostgreSQL o acceso R2 reales.
- Riesgos residuales: archivo completo antes del límite, storage/DB no atómicos,
  posible objeto nuevo huérfano, borrado anterior best-effort, carrera entre
  uploads, cancelación protegida que puede completar tras una desconexión y
  relación 40 workers/10 conexiones pendiente para 2.5.
- Estado: **2.4 cerrada**. No se inició 2.5.
- Siguiente acción exacta: ejecutar **2.5**, caracterizando y migrando solo la
  DB síncrona de las dependencias async de usuario/super admin y derivando una
  capacidad segura frente al pool; detenerse antes de 2.6.

### 2026-08-12 — subcapa 2.5

- Modo de acceso: mismo checkout local; rama `main` y árbol limpio antes de
  editar.
- Commit observado: `794bc7022c141b93e6f79b15390cb975d656b8b8`, siete
  commits locales por delante de `origin/main` y del base de la capa.
- Continuidad: `b24cb8d` es ancestro; `c6483e4`, `e6301d0`, `d2f7c9d`,
  `b7d7c57`, `297aac6`, `d82c78f` y `794bc70` corresponden a activación,
  2.0, 2.1, 2.2, 2.3a, 2.3b y 2.4. Sus alcances están explicados en esta
  bitácora; no había cambios pendientes ni divergencia antes de iniciar 2.5.
- Código de producto: únicamente `app/dependencies.py`,
  `app/core/super_admin.py` y `app/main.py`. Se añadieron dos offloads separados
  en usuario, uno en super admin y la capacidad del limitador compartido antes
  del `yield` del lifespan. No cambió ningún helper SQL, pool, timeout, ruta,
  controller, payload, status, permiso, tenant, transacción ni storage.
- Pruebas y medición: se crearon `tests/test_auth_threadpool.py`,
  `tests/test_threadpool_capacity.py` y
  `scripts/measure_auth_concurrency.py`. Son herméticos, usan conexiones falsas
  con un `ThreadedConnectionPool` real donde corresponde, y no acceden a red,
  PostgreSQL, R2 ni producción.
- Archivos modificados: `app/dependencies.py`, `app/core/super_admin.py`,
  `app/main.py`, `scripts/measure_auth_concurrency.py`,
  `tests/test_auth_threadpool.py`, `tests/test_threadpool_capacity.py` y esta
  bitácora.
- Comandos ejecutados:
  - precondiciones y continuidad: `git status --short --branch`,
    `git branch --show-current`, `git rev-parse HEAD`,
    `git rev-list --left-right --count origin/main...HEAD`,
    `git merge-base --is-ancestor b24cb8d3f1a8fa1d48699ed5732d4013ab6fe7f9 HEAD`,
    `git log --oneline --reverse b24cb8d3f1a8fa1d48699ed5732d4013ab6fe7f9..HEAD`;
  - línea base dirigida:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_auth_tenant.py tests/test_super_admin.py tests/test_tenant_context_concurrency.py tests/test_db_session_contrato.py tests/test_db_pool_timeouts.py`;
  - caracterización previa de contratos y pico:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_auth_threadpool.py::test_suspended_tenant_keeps_403_and_skips_user_validation tests/test_auth_threadpool.py::test_invalid_tenant_user_keeps_canonical_401 tests/test_auth_threadpool.py::test_unexpected_tenant_database_error_is_not_reclassified tests/test_auth_threadpool.py::test_inactive_super_admin_keeps_canonical_401 tests/test_threadpool_capacity.py::test_registered_nested_db_paths_hold_two_connections`;
  - medición comparable de 2.5, antes y después:
    `.\venv\Scripts\python.exe scripts/measure_auth_concurrency.py`;
  - pruebas nuevas finales:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_auth_threadpool.py tests/test_threadpool_capacity.py`;
  - conjunto dirigido ampliado:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_auth_tenant.py tests/test_super_admin.py tests/test_tenant_context_concurrency.py tests/test_db_session_contrato.py tests/test_db_pool_timeouts.py tests/test_auth_threadpool.py tests/test_threadpool_capacity.py`;
  - estabilidad de aislamiento, cancelación y capacidad:
    `$tests = @('tests/test_auth_threadpool.py::test_cookie_auth_threadpool_preserves_tenants_and_middleware_cleanup','tests/test_auth_threadpool.py::test_auth_threadpool_cancellation_waits_for_boundary_cleanup','tests/test_threadpool_capacity.py::test_threadpool_capacity_prevents_exhaustion_with_two_leases_per_worker','tests/test_threadpool_capacity.py::test_one_extra_threadpool_token_reproduces_pool_exhaustion'); 1..10 | ForEach-Object { .\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q @tests --disable-warnings; if ($LASTEXITCODE -ne 0) { throw "Fallo en ronda $_" }; Write-Output "ronda ${_}: OK" }`;
  - conteo de pruebas nuevas:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider --collect-only -q tests/test_auth_threadpool.py tests/test_threadpool_capacity.py`;
  - inventario runtime de `APIRoute` y dependencias mediante script Python en
    memoria: 140 totales, 139 sync, una async, 134 usuario, cuatro super admin y
    dos sin esas dependencias;
  - lint del alcance:
    `.\venv\Scripts\python.exe -m ruff check app/dependencies.py app/core/super_admin.py app/main.py scripts/measure_auth_concurrency.py tests/test_auth_threadpool.py tests/test_threadpool_capacity.py`;
  - compuerta global: `.\venv\Scripts\python.exe scripts/verify.py`;
  - alcance y estructura: AST en memoria, `rg` dirigido de primitivas prohibidas,
    `git diff --name-only -- app`, `git status --short`, `git diff --check` y
    `git diff --no-index --check NUL` para cada archivo nuevo.
- Línea base existente: **58 pasaron**, 5 warnings conocidos. La caracterización
  previa ejecutable dio **6 pasadas**; las poscondiciones nuevas de offload y
  limitador se habilitaron después del cambio.
- Verificación final: **23 casos nuevos** y **81 pruebas dirigidas** correctas,
  con 5 warnings conocidos. La estabilidad completó diez rondas, **60/60 casos
  correctos**; el caso Bearer añadido después pasó en el conjunto final y en la
  compuerta.
- Medición de 2.5: antes, 223,811 ms totales y 203,777 ms de retraso de
  heartbeat, solapamiento uno y event loop; después, 103,909 ms, 6,667 ms,
  solapamiento dos y workers. JWT y contratos funcionales reales se conservaron;
  solo las operaciones DB fueron dobles. No se presenta como la medición final
  de 2.6 ni como comparación directa con el arnés histórico de 2.0.
- Capacidad: inventario `H=2`, reserva HTTP `R=0`, fórmula
  `floor((maxconn-R)/H)` y resultado actual cinco tokens. Dos rutas reales
  caracterizan el doble checkout; el stress seguro alcanzó pico diez sin error y
  el control con seis tokens produjo dos `PoolError`. No se afirma seguridad
  fuera del proceso/event loop y rutas inventariadas.
- Primera compuerta dentro del sandbox: pytest alcanzó 470 pasadas, pero seis
  fixtures de uploads fallaron en setup por el `WinError 5` conocido sobre el
  temporal; Ruff y `pip check` fueron correctos. Repetición autorizada fuera del
  sandbox sobre el estado final: **exit 0, 477 pruebas**, 5 warnings conocidos,
  Ruff correcto y dependencias íntegras.
- Auditoría estructural: `get_current_user` y `get_current_super_admin` siguen
  `AsyncFunctionDef`; usuario tiene dos awaits con `set(tenant)` entre ellos y
  super admin uno. Bajo `app/` solo cambiaron los tres archivos autorizados;
  existen cuatro `run_in_threadpool` totales contando branding y ningún executor
  crudo, limitador privado o cancelación abandonable.
- `git diff --check`: exit 0, con avisos informativos LF→CRLF. Las tres
  comprobaciones `--no-index` terminan en exit 1 por diferir de `NUL`, esperado,
  sin errores de whitespace.
- Riesgos residuales: el limitador compartido también cola trabajo sin DB;
  `H=2` y `R=0` deben reauditarse ante nuevas rutas/threads/event loops; una
  cancelación espera cleanup y una desconexión puede dejar completar trabajo;
  la calibración de `DB_STATEMENT_TIMEOUT_MS` sigue pendiente y no se marcó
  cumplida.
- Estado: **2.5 cerrada**. No se inició 2.6.
- Siguiente acción exacta: ejecutar únicamente **2.6**, con medición final,
  compuerta, staging, rollback, verificación manual e índice de cierre; dejar la
  capa 3 en espera y no activarla.

### 2026-08-13 — subcapa 2.6 y cierre de la capa

- Modo de acceso: mismo checkout local; rama `main` y árbol limpio antes de
  editar.
- Commit observado: `225f80ec4f031c6bb7df6900c7fb91f4389a439e`, ocho
  commits locales por delante de `origin/main` y del base de la capa.
- Continuidad: `b24cb8d` es ancestro; los ocho commits lineales corresponden a
  activación y 2.0–2.5. El último commit contiene exactamente los siete archivos
  documentados de 2.5. No había cambios pendientes ni divergencia al iniciar.
- Alcance de 2.6: exclusivamente `docs/modularizacion/02_CONCURRENCIA.md` y
  `docs/modularizacion/README.md`. No cambió producto, pruebas, scripts,
  configuración, dependencias ni workflow; no se inició la capa 3.
- Comandos ejecutados:
  - precondiciones y continuidad: `git status --short --branch`,
    `git branch --show-current`, `git rev-parse HEAD`, `git rev-parse origin/main`,
    `git rev-list --left-right --count origin/main...HEAD`,
    `git merge-base --is-ancestor b24cb8d3f1a8fa1d48699ed5732d4013ab6fe7f9 HEAD`,
    `git log --oneline --decorate --reverse b24cb8d3f1a8fa1d48699ed5732d4013ab6fe7f9..HEAD`;
  - stack efectivo:
    `.\venv\Scripts\python.exe -c "import sys; from importlib.metadata import version; print('Python=' + sys.version.split()[0], *(name + '=' + version(name) for name in ('fastapi','starlette','anyio','psycopg2-binary','pytest')))"`;
  - medición formal:
    `.\venv\Scripts\python.exe -B scripts\measure_auth_concurrency.py --runs 5 --validation-ms 100 --heartbeat-ms 20 --json`;
  - pruebas dirigidas:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_auth_tenant.py tests/test_super_admin.py tests/test_tenant_context_concurrency.py tests/test_db_session_contrato.py tests/test_db_pool_timeouts.py tests/test_auth_threadpool.py tests/test_threadpool_capacity.py`;
  - compuerta final fuera del sandbox:
    `.\venv\Scripts\python.exe scripts\verify.py`;
  - alcance y documentación: `git diff --name-only`,
    `git diff --name-only -- app`, `git status --short --branch`,
    `git diff --check`, revisión del diff acumulado `b24cb8d..HEAD` y barrido C0
    reproducible:
    `.\venv\Scripts\python.exe -c "from pathlib import Path; paths=(Path('docs/modularizacion/README.md'),Path('docs/modularizacion/02_CONCURRENCIA.md')); bad=[(str(path),line_number,ord(char)) for path in paths for line_number,line in enumerate(path.read_text(encoding='utf-8').splitlines(),1) for char in line if ord(char)<32 and char not in '\t\r']; print('C0_OK' if not bad else bad)"`.
- Medición formal: cinco rondas correctas, mediana **102,093 ms** total y
  **4,471 ms** de retraso del heartbeat; solapamiento dos, estado y validación
  en workers, tenants A/B y contexto exterior restaurados. Frente al mismo arnés
  antes del cambio: 54,4 % menos tiempo total y 97,8 % menos bloqueo observado.
- Verificación: **81 pruebas dirigidas** y **477 pruebas globales** correctas;
  cinco warnings deprecatorios conocidos, Ruff correcto y dependencias íntegras.
- Verificación documental: `git diff --check` terminó en exit 0, solo con avisos
  informativos LF→CRLF; el alcance contiene exactamente esta bitácora y
  `README.md`, ningún archivo de `app/` ni archivo no rastreado. El barrido de
  caracteres de control terminó en `C0_OK`.
- Staging, rollback y verificación manual: documentados como planes no
  ejecutados en «Subcapa 2.6: resultado y cierre».
- Evidencia externa: no hubo push; GitHub Actions no puede considerarse
  verificada para los ocho commits locales. No hubo deploy, producción,
  migraciones ni cambios de datos.
- Riesgos abiertos: calibración de `DB_STATEMENT_TIMEOUT_MS`; cola compartida
  del limitador; reauditar `H/R` ante nuevas fronteras; cancelación protegida;
  storage/DB no atómicos; versiones flotantes. Ninguno se marcó como resuelto
  por inferencia.
- Estado: **capa 2 cerrada**. No existe una capa activa.
- Siguiente acción exacta: esperar una decisión explícita del usuario. Solo una
  orden inequívoca puede activar la capa 3; en ese caso se crea su bitácora desde
  `PLANTILLA_CAPA.md`, se registra el HEAD limpio vigente como base, se actualiza
  el índice y se detiene antes de implementar 3.0, salvo autorización adicional.

## Entrega al próximo chat

- Capa activa: **ninguna**.
- Última capa terminada: **2, concurrencia**; subcapas 2.0–2.6 cerradas.
- Primera subcapa pendiente: **ninguna**.
- Hallazgo central: el inventario actual correcto es 140 rutas; 138 atravesaban
  las dependencias async con DB síncrona. Sus tres llamadas DB ya usan el
  threadpool estándar. El pico HTTP inventariado es dos conexiones por worker y
  el limitador compartido deriva cinco tokens frente al pool de diez.
- Verificación local vigente: medición formal 5/5, 81 pruebas dirigidas y
  60/60 casos sensibles previos; compuerta global en exit 0 con 477 pruebas,
  Ruff y dependencias correctos.
  GitHub Actions no está verificada porque los commits siguen sin push.
- Verificación operativa pendiente: la calibración heredada de
  `DB_STATEMENT_TIMEOUT_MS` continúa pendiente y no debe marcarse como cumplida.
- Riesgos conservados: cola de cinco workers para trabajo sync compartido,
  invariante H/R por reauditar ante nuevas fronteras, cancelación protegida,
  storage/DB no atómicos y dependencias flotantes.
- Siguiente capa: **3, migraciones y tenants, en espera**. No tiene bitácora y no
  puede activarse con una instrucción genérica de continuar.
- Siguiente acción exacta: esperar una orden explícita entre mantener el programa
  cerrado o activar solo la capa 3. Si se autoriza activarla, crear únicamente
  su bitácora e índice y detenerse; no implementar 3.0 en ese mismo turno sin
  autorización inequívoca adicional.
