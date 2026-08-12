# Capa 2: concurrencia

Última revisión: 2026-08-12.

## Control

- Estado: **Activa**.
- Commit base: `b24cb8d3f1a8fa1d48699ed5732d4013ab6fe7f9`.
- Rama acordada: `main`.
- Estado al activar: árbol limpio; `HEAD` coincidente con la referencia local
  `origin/main`.
- Primera subcapa pendiente: **2.3b**, seis escrituras o efectos de plan de
  clases.
- Código de producto modificado al activar: **ninguno**.
- Código de producto modificado hasta ahora: `app/routes/reportes.py`,
  `app/routes/dashboard.py` y `app/routes/plan_de_clases.py`; diecisiete handlers
  sin `await` pasaron de `async def` a `def`, sin cambiar sus cuerpos.
- Progreso: **2.0, 2.1, 2.2 y 2.3a cerradas**. Los cinco reportes, siete lecturas
  de dashboard y cinco lecturas de plan de clases ya ejecutan sus controllers DB
  síncronos en el threadpool gobernado por FastAPI; quedan 7 handlers async con
  una frontera bloqueante en su cuerpo: seis efectos de plan de clases y el caso
  especial de branding. La dependencia común de autenticación continúa
  bloqueando el event loop y se mantiene reservada para 2.5.
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
| 2.3b | Cuarta tanda: 6 escrituras o efectos de plan de clases | **Pendiente** |
| 2.4 | Caso especial de branding: lectura async más storage y DB síncronos | Pendiente |
| 2.5 | Dependencias async de usuario y super admin; límite compartido derivado y medido | Pendiente |
| 2.6 | Medición posterior, compuerta global, staging, rollback y cierre | Pendiente |

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
- La lectura de 2.0 se amplió solo a cinco funciones de `tenant_status.py` y
  `super_admin.py` descubiertas como dependencias HTTP opacas. No se leyó el
  resto de esos dominios.
- La calibración pendiente de `DB_STATEMENT_TIMEOUT_MS` permanece registrada en
  la capa 1 y no se da por cumplida al activar esta capa.

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

## Entrega al próximo chat

- Capa activa: **2, concurrencia**.
- Última subcapa terminada: **2.3a**, cinco lecturas de plan de clases.
- Primera subcapa pendiente: **2.3b**, seis escrituras o efectos de plan de
  clases.
- Hallazgo central: 137/139 handlers bloquean hoy el event loop durante una
  dependencia DB async; después de 2.3a, 7/139 vuelven a bloquearlo en su
  cuerpo. Reportes, dashboard y las cinco lecturas de plan de clases ya no
  forman parte de ese segundo grupo.
- Verificación vigente: compuerta en exit 0 con 395 pruebas, Ruff y dependencias
  correctos; 60 pruebas específicas ampliadas de 2.3a correctas.
- Bloqueos: ninguno para 2.3b. La calibración operativa heredada de
  `DB_STATEMENT_TIMEOUT_MS` continúa pendiente y no debe marcarse como cumplida.
- Nota de continuidad: el `README.md` conserva la frase de activación «2.0
  pendiente» porque 2.0 solo podía modificar esta bitácora. La tabla maestra
  sigue siendo correcta —capa 2 activa— y **esta bitácora gobierna la subcapa
  vigente: 2.3b**; no es una segunda capa activa ni una divergencia de Git.
- Siguiente acción exacta: ejecutar 2.3b con pruebas antes del cambio, migrar
  solo los seis efectos de plan de clases, verificar y detenerse antes de 2.4.
