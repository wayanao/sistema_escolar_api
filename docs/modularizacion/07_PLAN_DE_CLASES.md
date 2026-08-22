# Capa 7: plan_de_clases

Última revisión: 2026-08-22.

## Control

- Estado: **Cerrada** el 2026-08-22 por orden explícita del usuario.
- Commit base: `bfe80d4152b802aeb22f4c5a2c5aab9265ba7630`.
- Rama acordada: `main`.
- Primera subcapa pendiente: **Ninguna**. 7.2 y 7.3 quedaron **No aplica** al
  cerrarse la capa como refactorización pura.
- Código de producto modificado al activar: **Ninguno**.
- Código de producto modificado en 7.0: **Ninguno**. El diff funcional de la
  subcapa es un solo archivo nuevo de caracterización; los demás cambios son
  documentación.
- Código de producto modificado en 7.1: **tres archivos**. Las dos consultas
  externas pasaron al repositorio existente; `permissions.py` y `main.py`
  conservan conexión, cursor, cierre y decisiones de acceso.
- Dominio de esta capa: **`plan_de_clases`, y solo ese**. `branding`,
  `profesores` y `super_admin` siguen en espera.
- Autorización: el usuario informó «planeador revisado» y ordenó «sigue con
  plan de clases». La verificación manual de `planeador_anual` se registra como
  completada de forma global, sin atribuir entorno ni confirmación individual
  de los siete puntos que no fueron reportados.
- La orden posterior «continua» autorizó ejecutar **únicamente 7.0**. No
  autoriza 7.1, commit, push, deploy, migraciones reales ni acceso a
  producción.
- Tras presentarse el alcance exacto de 7.1, la nueva orden «continua» autorizó
  **únicamente esa extracción**. No autoriza 7.2 ni corregir otros hallazgos.
- La orden posterior «cierra», reanudada con «sigue» después de consolidar 7.1
  en un commit local limpio, autoriza únicamente cerrar esta capa. No activa
  otro dominio ni autoriza commit, push, deploy, migraciones reales o acceso a
  producción.

## Objetivo

Migrar el dominio de **plan de clases** con contratos y pruebas, conservando su
comportamiento observable actual.

El índice maestro fija tres condiciones para esta capa:

1. trabajar **un dominio a la vez**;
2. agregar `response_model`, errores de dominio y pruebas HTTP o de integración
   solo después de caracterizar y conservar la respuesta existente;
3. no crear abstracciones compartidas sin dos consumidores reales.

La activación no inspeccionó código ni infirió esa frontera. La caracterización
7.0 posterior la delimitó con la evidencia inventariada en esta bitácora y sin
modificar producto.

## Dependencias de capas anteriores

- La capa 7 para `planeador_anual` está cerrada: 7.0 y 7.1 completas, 7.2
  **No aplica**, compuerta final con **987 pruebas**, Ruff correcto y
  dependencias íntegras.
- El usuario reportó después «planeador revisado». La verificación manual se
  considera completada de forma global y suficiente para continuar, pero no se
  conoce el entorno ni consta el resultado separado de los siete puntos.
- El commit base de esta capa es el `HEAD` limpio vigente,
  `bfe80d4152b802aeb22f4c5a2c5aab9265ba7630`.
- Los cuatro commits posteriores al base de `planeador_anual` están explicados:
  `6358c5a` activa el dominio, `2a8d3c3` contiene 7.0, `51203da` contiene 7.1 y
  `bfe80d4` cierra la capa y documenta la verificación manual entonces
  pendiente. Este último toca únicamente la bitácora y el índice maestro.
- La referencia local `origin/main` coincide con el commit base. No se consultó
  el remoto real ni se atribuye publicación, despliegue o GitHub Actions.
- Siguen pendientes, sin marcarse como cumplidas: la calibración operativa
  final de `DB_STATEMENT_TIMEOUT_MS`; evidencia de GitHub Actions posterior a
  la capa 0; pasos manuales no confirmados heredados de `ventas`, `asistencia`,
  `boletin` y `observaciones`; y la rotación de la credencial privilegiada
  registrada en la capa 4.

## Supuestos documentales resueltos en 7.0

Los ocho supuestos de la activación quedaron resueltos: **seis confirmados, uno
confirmado con matiz y uno refutado**.

| # | Supuesto documental | Resultado de 7.0 |
|---:|---|---|
| 1 | Frontera propia separada de `planeador_anual` | **CONFIRMADO.** Son cinco archivos propios y 1334 líneas; no importan ni llaman el dominio anual |
| 2 | `/notificaciones/planeadores` pertenece aquí y usa controlador/servicio propios | **CONFIRMADO.** Es una de las once entradas y termina en las consultas de notificación del repositorio propio |
| 3 | Existe repositorio propio, con cobertura por determinar | **CONFIRMADO CON MATIZ.** Contiene los 25 sitios `cursor.execute` del API, pero dos consultas específicas del dominio siguen fuera: el guard en `permissions.py` y el acceso a imágenes en `main.py` |
| 4 | Los tres handlers con «observacion» son de este dominio | **CONFIRMADO.** Son crear, listar y marcar vista; no importan ni tocan el dominio cerrado `observaciones` |
| 5 | Escriben `plan_de_clases_observaciones` | **CONFIRMADO.** El dominio posee además `plan_de_clases` y `plan_de_clases_notificaciones_admin` |
| 6 | Usa `storage.py` | **CONFIRMADO.** Guarda y elimina hasta dos imágenes en almacenamiento local o R2/S3; el endpoint compartido `/uploads` también forma parte del comportamiento observable |
| 7 | Contratos, SQL, recursos y efectos no determinados | **CONFIRMADO COMO TRABAJO Y RESUELTO.** El inventario y la línea base quedan fijados más abajo |
| 8 | Las pruebas existentes bastan | **REFUTADO.** Había 105 casos útiles, pero no una guardia de frontera completa, HTTP real por ASGI, localización total del SQL, desajuste del esquema de respuesta ni conteos de conexiones; 7.0 añadió 22 casos |

El matiz del supuesto 3 era el estado exacto al cerrar 7.0. **7.1 lo resolvió**
extrayendo esas dos consultas sin cambiar sus contratos.

## Inventario y contratos fijados en 7.0

La frontera propia tiene **cinco archivos y 1334 líneas**. La persistencia del
API ya estaba separada antes de esta capa; no se modificó ninguno:

| Archivo | Líneas | SQL ejecutado | Responsabilidad |
|---|---:|---:|---|
| `app/routes/plan_de_clases.py` | 213 | 0 | Once entradas HTTP, autenticación, guards, parsing multipart y traducción de algunos errores |
| `app/controllers/plan_de_clases_controller.py` | 200 | 0 | Orquestación, validación y ciclo de vida de imágenes, conflictos y errores de revisión |
| `app/services/plan_de_clases_service.py` | 88 | 0 | Mensajes, selección por rol y delegación entre controlador y repositorio |
| `app/repositories/plan_de_clases_repository.py` | 753 | 25 sitios `cursor.execute` | Doce operaciones con cursor propio: siete lecturas y cinco transacciones de escritura |
| `app/schemas/plan_de_clases.py` | 80 | 0 | Entrada de plan, revisión, observación y un esquema de respuesta no usado |

Participan además cuatro piezas compartidas, sin pertenecer a la frontera
propia: el montaje y el acceso a `/uploads` en `app/main.py`, los dos guards de
`app/core/permissions.py`, el resolutor académico y `app/services/storage.py`.
Las dos consultas específicas fuera del repositorio viven en `main.py` y
`permissions.py`; el resolutor añade una consulta compartida dentro de varias
operaciones del repositorio.

Tras 7.1, la frontera propia conserva los mismos cinco archivos y pasa a
**1365 líneas**: el repositorio tiene **784 líneas y 27 sitios
`cursor.execute`**. Las dos consultas específicas viven ahora en dos funciones
que reciben el cursor existente; `main.py` y `permissions.py` ya no contienen
SQL de `plan_de_clases`.

### Entradas HTTP, permisos y respuestas

Son **once entradas síncronas**, ninguna con `response_model`:

| Método | Path | Permiso observable | Respuesta o efecto principal |
|---|---|---|---|
| GET | `/notificaciones/planeadores` | Usuario; solo rol admin o profesor | Conteo e items no leídos según rol |
| POST | `/plan-de-clases` | Usuario más acceso a asignación | Upsert, cero a dos imágenes y mensaje; conflicto opcional 409 |
| GET | `/plan-de-clases/{asignacion_id}` | Usuario más acceso a asignación | Un plan por fecha o historial, sin límite por defecto |
| DELETE | `/plan-de-clases/{plan_id}/imagen` | Usuario más ownership del plan | Limpia un slot, reinicia revisión cuando aplica y elimina archivo |
| GET | `/admin/plan-de-clases` | Admin activo | `{"total": ..., "items": [...]}` con filtros y paginación |
| GET | `/admin/plan-de-clases/{plan_id}` | Admin activo | Plan o 404 |
| PATCH | `/admin/plan-de-clases/{plan_id}/revision` | Admin activo | Estado de revisión o conflicto 409 |
| POST | `/admin/plan-de-clases/{plan_id}/observaciones` | Admin activo | Observación versionada o conflicto 409 |
| GET | `/plan-de-clases/{plan_id}/observaciones` | Usuario más ownership del plan | Lista completa, sin paginación |
| PATCH | `/plan-de-clases/{plan_id}/observaciones/{observacion_id}/vista` | Profesor estricto más ownership | Marca vista o 404 |
| DELETE | `/admin/plan-de-clases/{plan_id}/imagen` | Admin activo | Limpia un slot sin reiniciar revisión y elimina archivo |

La interfaz ASGI real fijó 403 para el rol no autorizado en notificaciones,
422 para parámetros Query y esquemas JSON inválidos, 400 para la fecha
multipart inválida y serialización ISO de `date`/`datetime`. El esquema
`PlanDeClasesResponse` **no se usa** y omite `created_at` y `updated_at`, dos
campos que `_row_to_plan` sí devuelve; añadirlo hoy recortaría el payload.

### Persistencia, transacciones y archivos

- Las tres tablas propias son `plan_de_clases`,
  `plan_de_clases_observaciones` y
  `plan_de_clases_notificaciones_admin`.
- El DDL conserva unicidad sobre `(asignacion_id, fecha)`, FK a
  `asignaciones`, FK en cascada desde observaciones y notificaciones, estados
  de revisión limitados y observaciones de 1 a 3000 caracteres.
- El repositorio tiene **doce operaciones dueñas de cursor**: siete abren
  `get_cursor()` de lectura y cinco `get_cursor(commit=True)`. Los helpers de
  lock y notificación reciben el cursor de su llamador.
- El guard de plan y el acceso compartido a imágenes abren cada uno una
  conexión manual adicional y poseen cursor y cierre. Ninguno filtra
  `asignaciones.activo`.
- El guardado usa un upsert atómico. `version_esperada` es opcional: cuando se
  omite, no hay control de versión previo; cuando llega, el repositorio bloquea
  y compara dentro de la transacción.
- Se admiten hasta dos imágenes PNG/JPEG/WebP de 5 MiB por el MIME y la
  extensión declarados. Se guardan **antes** de la transacción DB y se intentan
  borrar si la segunda imagen o la base fallan.
- La eliminación confirma primero el cambio DB y después llama `delete_file`.
  Ese adaptador absorbe errores de borrado locales o remotos, por lo que el
  endpoint puede responder éxito con un archivo huérfano.

### Línea base de consultas, conexiones y almacenamiento

Los conteos no incluyen autenticación ni los dos round-trips de configuración
de cada conexión. No existe un `cursor.execute` dentro de un bucle Python, así
que **no hay N+1 emitido por la aplicación**. `PLAN_SELECT` sí contiene tres
subconsultas correlacionadas por cada fila devuelta, riesgo SQL distinto que se
registra sin corregir.

| Camino | Consultas admin/profesor | Conexiones admin/profesor | Archivos |
|---|---:|---:|---:|
| Notificaciones | **2 / 2** | **1 / 1** | 0 |
| Plan por día o historial | **2 / 3** | **1 / 2** | 0 |
| Crear/actualizar sin versión, resultado pendiente | **3 / 4** | **1 / 2** | 0 a 2 escrituras antes de DB |
| Crear/actualizar con versión vigente | **4 / 5** | **1 / 2** | 0 a 2 escrituras antes de DB |
| Listado admin | **2** | **1** | 0 |
| Detalle admin | **1** | **1** | 0 |
| Listar observaciones | **2 / 3** | **2 / 3** | 0 |
| Marcar visto | No aplica / **2** | No aplica / **2** | 0 |
| Revisar sin/con comentario | **3 / 4** | **1** | 0 |
| Crear observación | **4** | **1** | 0 |
| Eliminar imagen admin | **2** | **1** | 1 borrado posterior a DB |
| Eliminar imagen profesor | **3 o 4** | **2** | 1 borrado posterior a DB |
| Servir imagen compartida | **0 / 1** | **0 / 1** | 1 lectura local o remota |

## Hallazgos registrados en 7.0; uno resuelto en 7.1

1. **RESUELTO EN 7.1 — la frontera de persistencia no estaba totalmente
   cerrada.** Los dos SQL específicos del dominio salieron de `permissions.py`
   y `main.py` al repositorio existente, conservando recursos y contratos.
2. **Ninguna de las once rutas declara `response_model`.** El esquema existente
   no puede añadirse mecánicamente: omite `created_at` y `updated_at` que hoy se
   devuelven y no representa notificaciones ni mutaciones.
3. **El control de concurrencia es optativo.** `version_esperada=None` permite
   que clientes antiguos hagan upsert sin detectar una actualización perdida.
4. **`periodo` no tiene límites en Pydantic ni en el DDL**, y los textos del plan
   no tienen longitud máxima. Se caracterizó que incluso un periodo negativo y
   4000 caracteres son aceptados por el esquema.
5. **Dos listas pueden ser ilimitadas:** el historial usa `limit=None` por
   defecto y las observaciones no admiten paginación.
6. **Las lecturas agregadas esconden trabajo por fila en PostgreSQL.**
   `PLAN_SELECT` ejecuta conceptualmente tres subconsultas correlacionadas para
   conteo, no vistas y última observación; no es N+1 de red, pero puede escalar
   con el resultado ilimitado.
7. **Los dos guards específicos ignoran `asignaciones.activo`.** Un profesor
   que conserve ownership puede acceder al plan y a su archivo aunque la
   asignación esté desactivada, patrón ya visto en otros dominios.
8. **Base y almacenamiento no comparten transacción.** Una imagen nueva se
   guarda antes del upsert; reemplazarla no elimina el archivo anterior, y el
   borrado explícito confirma DB antes de un `delete_file` que absorbe fallos.
9. **La validación de imágenes confía en MIME y extensión declarados.** No
   inspecciona la firma real del contenido.
10. **Los errores HTTP no siguen un solo modelo.** La creación y el historial
    exponen `str(e)` como 400; los listados admin y borrados ocultan el detalle
    como 500; revisión, observaciones y notificaciones dejan propagar sus
    excepciones.
11. **Listar observaciones abre dos conexiones de repositorio en serie**, una
    para comprobar que el plan existe y otra para leer la lista; como profesor
    el guard añade una tercera. Es constante, no N+1.
12. **El endpoint compartido `/uploads/{file_path}` forma parte del contrato del
    dominio sin vivir en su router.** Una caracterización limitada a los cinco
    archivos propios habría omitido tanto esa entrada como uno de los dos SQL
    externos.

Quedan **once hallazgos sin corregir**. El primero es el único resuelto por la
extracción autorizada de 7.1.

## Alcance autorizado

- Trabajar únicamente en el dominio `plan_de_clases`.
- En 7.0, delimitar primero su frontera por rutas, llamadores, tablas,
  consumidores y efectos de almacenamiento, no solo por nombres de archivo.
- Inventariar entradas HTTP, permisos, ownership, tenant, payloads, status
  codes, respuestas, cálculos, SQL, tablas, transacciones, conexiones, archivos
  y otros efectos laterales.
- Resolver uno por uno los supuestos documentales indicando si quedan
  confirmados, incompletos, refutados o mal atribuidos.
- Agregar caracterización antes de cualquier extracción importante.
- Medir consultas, conexiones y operaciones de almacenamiento críticas antes y
  después de cualquier cambio de producto posterior.

## Fuera de alcance

- `branding`, `profesores` y `super_admin`, que siguen en espera.
- Reabrir por inferencia `planeador_anual`, `observaciones` u otro dominio
  cerrado.
- Corregir hallazgos abiertos de las capas 1 a 7 o completar verificaciones
  heredadas dentro de esta activación.
- Cambiar rutas, payloads, status codes, permisos, roles, ownership, tenant,
  cálculos, SQL observable, transacciones, archivos o comportamiento actual sin
  una autorización explícita apoyada en la caracterización.
- Cambiar PostgreSQL, `psycopg2`, el modelo de schemas tenant, el pool, los
  timeouts, la concurrencia, el ORM, el driver o el proveedor de almacenamiento.
- Migraciones reales, acceso a producción, DDL, DML, deploy, commit o push.

## Invariantes

- Métodos, paths, status codes y forma exacta de las respuestas permanecen
  idénticos, incluidos orden, nulos y errores.
- Permisos, roles, ownership y aislamiento entre tenants se conservan.
- SQL, parámetros, número y orden observable de operaciones y límites de
  transacción se conservan.
- Se conserva quién posee conexión, cursor, `commit`, `rollback`, archivos y
  efectos de almacenamiento.
- Ninguna operación DB síncrona vuelve al event loop ni se cambia el limitador
  compartido sin una medición de capacidad propia.
- No se crea una abstracción compartida sin dos consumidores reales.

## Línea base

| Comprobación | Comando | Resultado |
|---|---|---|
| Específicas heredadas antes de agregar caracterización | `.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_plan_de_clases_routes.py tests\test_plan_de_clases_effect_routes.py tests\test_plan_de_clases_revision.py tests\test_plan_de_clases_integridad.py tests\test_permissions.py tests\test_uploads_permissions.py` | **105 passed**, 5 warnings heredados |
| Compuerta heredada | `.\venv\Scripts\python.exe scripts\verify.py` | **987 passed**, Ruff correcto, dependencias íntegras |
| Caracterización nueva | `.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_plan_de_clases_caracterizacion.py` | **22 passed** |
| Específicas finales | El comando específico anterior más `tests\test_plan_de_clases_caracterizacion.py` | **127 passed**, 5 warnings heredados |
| Ruff de la caracterización | `.\venv\Scripts\python.exe -m ruff check tests\test_plan_de_clases_caracterizacion.py` | **All checks passed** |
| Compuerta final | `.\venv\Scripts\python.exe scripts\verify.py` | **1009 passed**, Ruff correcto, dependencias íntegras |
| Línea base específica de 7.1 | Caracterización, permisos y uploads | **42 passed**, 5 warnings heredados |
| Caracterización final de 7.1 | `tests\test_plan_de_clases_caracterizacion.py` | **24 passed** |
| Específicas finales de 7.1 | Las siete suites relacionadas de `plan_de_clases`, permisos y uploads | **129 passed**, 5 warnings heredados |
| Ruff de 7.1 | Los tres archivos de producto y la caracterización modificados | **All checks passed** |
| Compuerta global de 7.1 | `.\venv\Scripts\python.exe scripts\verify.py` | **1011 passed**, Ruff correcto, dependencias íntegras |
| Específicas de cierre | Las siete suites relacionadas de `plan_de_clases`, permisos y uploads | **129 passed**, 5 warnings heredados |
| Compuerta global de cierre | `.\venv\Scripts\python.exe scripts\verify.py` | **1011 passed**, Ruff correcto, dependencias íntegras |

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 7.0 | Delimitar la frontera, inventariar contratos y caracterizar el comportamiento y la línea base | **Cerrada el 2026-08-22** |
| 7.1 | Extraer las dos consultas específicas externas al repositorio existente, conservando los recursos de sus llamadores | **Cerrada el 2026-08-22** |
| 7.2 | No se autorizó otro cambio de comportamiento ni otra extracción; `response_model` y errores de dominio quedan fuera de esta refactorización | **No aplica** |
| 7.3 | No apareció código heredado que retirar para cerrar la capa | **No aplica** |

Las subcapas se adaptan al trabajo real. Las innecesarias se marcan `No
aplica` con una explicación; nunca se ejecutan dos en el mismo turno.

## Subcapa cerrada: trabajo ejecutado en 7.0

La orden «continua» se interpretó conforme al protocolo como autorización para
la primera subcapa pendiente y para ninguna otra. Se ejecutaron estos pasos:

1. Delimitar la frontera real de `plan_de_clases` por entradas, llamadores,
   tablas, consumidores y efectos de almacenamiento antes de contar o modificar
   nada.
2. Inspeccionar únicamente la documentación, fuentes y pruebas relacionadas
   con esa frontera; separar expresamente las piezas nominales de
   `planeador_anual` y `observaciones`.
3. Inventariar métodos, paths, guards, permisos, payloads, status codes,
   respuestas, orden, nulos y errores de cada entrada.
4. Inventariar SQL inline y delegado, tablas, transacciones, propiedad de
   conexión/cursor y operaciones sobre archivos o servicios externos.
5. Identificar y fijar por prueba cálculos, orden, nombres, contenido y otros
   efectos observables antes de cualquier extracción.
6. Medir consultas, conexiones y operaciones de almacenamiento por camino,
   buscando N+1 o dependencia del tamaño de entrada o resultado.
7. Revisar solo las pruebas relacionadas y agregar caracterización sin cambiar
   expectativas heredadas salvo autorización explícita.
8. Resolver los ocho supuestos documentales y registrar hallazgos sin
   corregirlos.
9. Archivos modificables en 7.0: pruebas de caracterización del dominio, esta
   bitácora y el índice maestro. **Ningún archivo de producto se modifica.**
10. Ejecutar pruebas específicas, Ruff sobre la caracterización, la compuerta
    global, `git diff --check` y revisión de alcance.
11. Actualizar esta bitácora con archivos, comandos, resultados, decisiones,
    riesgos y la siguiente acción exacta.
12. **Detenerse al cerrar 7.0. No iniciar 7.1 en el mismo turno.**

## Criterios de cierre de 7.0

Todos quedaron cumplidos en 7.0:

- La frontera queda delimitada con evidencia y sin reabrir otros dominios.
- Los ocho supuestos quedan resueltos uno por uno.
- Existe caracterización ejecutable de contratos, SQL, transacciones,
  consultas, conexiones, archivos y efectos laterales aplicables.
- Pruebas específicas, Ruff, compuerta y dependencias correctas.
- `git diff --check` correcto y diff exclusivo de 7.0.
- Bitácora actualizada con resultados, decisiones, riesgos y siguiente acción.

## Subcapa cerrada: trabajo ejecutado en 7.1

1. Interpretar la nueva orden «continua» como respuesta al alcance presentado:
   extraer únicamente las dos consultas externas.
2. Ejecutar la línea base específica antes de editar producto.
3. Agregar primero dos casos parametrizados que fijan el texto SQL y los
   parámetros exactos, y convertir las guardias de ubicación para exigir la
   frontera final.
4. Confirmar que esas guardias fallen contra el producto anterior como señal
   esperada.
5. Crear dos operaciones específicas en
   `plan_de_clases_repository.py`. Ambas reciben el cursor de su llamador; no
   abren conexiones ni crean una abstracción genérica compartida.
6. Sustituir únicamente los bloques `execute`/`fetchone` de
   `require_plan_de_clases_access` y `_validar_acceso_archivo_upload` por esas
   llamadas.
7. Conservar byte a byte los dos SQL, sus parámetros, orden, valor booleano,
   permisos y ausencia del filtro `activo`.
8. Conservar en `permissions.py` y `main.py` la apertura y cierre manuales de
   conexión/cursor, además del retorno permitido y el 403 denegado.
9. No corregir almacenamiento, concurrencia, paginación, validaciones,
   `response_model`, errores ni los otros once hallazgos.
10. Ejecutar caracterización, pruebas específicas, Ruff, compuerta global,
    `git diff --check` y revisión de alcance.
11. Actualizar esta bitácora y el índice, y detenerse antes de 7.2.

## Criterios de cierre de 7.1

Todos quedaron cumplidos:

- `permissions.py` y `main.py` no contienen SQL de `plan_de_clases`.
- El repositorio contiene los 27 sitios `cursor.execute`, incluidos los dos
  nuevos helpers que reciben cursor.
- Los dos textos SQL y sus parámetros están fijados y conservados exactamente.
- Conexiones, cursores, cierres, retornos, permisos y conteos permanecen en sus
  llamadores y sin cambios observables.
- Pruebas específicas, Ruff, compuerta y dependencias son correctas.
- El diff pertenece únicamente a 7.1 y la documentación de continuidad.

## Criterios de cierre de la capa

- Todas las subcapas necesarias están cerradas.
- Compuerta global correcta.
- Contratos conservados o cambios explícitamente aprobados.
- Staging, rollback y verificación manual documentados.
- La capa queda cerrada y el siguiente dominio permanece en espera hasta una
  nueva orden explícita.

## Decisiones

- **Activar `plan_de_clases` y solo ese dominio.** Motivo: el usuario lo nombró
  explícitamente y el índice exige trabajar uno por uno.
- **Registrar la verificación manual de `planeador_anual` como completada de
  forma global.** Motivo: el usuario informó «planeador revisado» y ordenó
  seguir. No se inventan entorno ni resultados punto por punto.
- **Mantener pendientes las verificaciones heredadas.** La orden no aporta
  evidencia nueva sobre ellas y ninguna se marca como cumplida.
- **Usar el `HEAD` limpio vigente como commit base.** Es el punto posterior al
  cierre documental de `planeador_anual`; sus cuatro commits están explicados.
- **Activación exclusivamente documental.** No se inspecciona ni implementa
  7.0 en este turno.
- **No inferir la frontera por nombres o referencias heredadas.** Los datos
  previos se registran como supuestos que 7.0 debe contrastar.
- **Ejecutar solo 7.0 por la orden «continua».** La subcapa agrega
  caracterización y documentación, sin cambios de producto ni inicio de 7.1.
- **Considerar propia una frontera de cinco archivos y compartidas cuatro
  piezas relacionadas.** El endpoint `/uploads`, su guard SQL, el guard de
  ownership, el resolutor académico y el almacenamiento son parte del contrato
  observable aunque no todos pertenezcan al módulo.
- **No declarar completa la frontera de persistencia.** Los 25
  `cursor.execute` del API viven en el repositorio, pero las dos consultas
  específicas de acceso siguen en `permissions.py` y `main.py`.
- **No corregir los doce hallazgos de caracterización.** Cambiar concurrencia,
  filtros, paginación, almacenamiento, validaciones, errores o modelos de
  respuesta alteraría contratos o ampliaría 7.0.
- **Distinguir N+1 de red de trabajo SQL por fila.** No hay consultas emitidas
  desde bucles Python; las tres subconsultas correlacionadas de `PLAN_SELECT`
  quedan registradas como un riesgo separado.
- **Dejar 7.1 sujeta a decisión expresa.** La evidencia permite presentar una
  extracción limitada de las dos consultas externas, pero no autoriza a
  ejecutarla ni a cambiar sus propietarios de conexión o sus contratos.
- **Interpretar la segunda orden «continua» como autorización exacta de 7.1.**
  Respondió inmediatamente a la propuesta de extraer las dos consultas y no
  amplía el alcance a 7.2.
- **Usar dos operaciones específicas que reciben cursor.** No se creó un helper
  genérico: cada consulta conserva un contrato y un único llamador distintos.
- **Mantener los recursos en infraestructura compartida.** `permissions.py` y
  `main.py` siguen abriendo y cerrando sus conexiones/cursor; moverlos habría
  alterado los conteos fijados en 7.0.
- **Conservar los dos literales SQL byte a byte.** La sangría heredada dentro de
  los strings se mantuvo deliberadamente y dos pruebas parametrizadas fijan
  además los parámetros exactos.
- **Resolver solo el primer hallazgo.** Los otros once siguen vivos y 7.1 no
  añade filtros, modelos, validaciones, paginación ni cambios de errores.
- **Dejar el cierre de capa como decisión.** 7.2 y 7.3 no se ejecutan por
  inferencia; el usuario puede cerrar como refactorización pura o autorizar una
  7.2 concreta después de revisar alternativas y riesgo.
- **Cerrar como refactorización pura.** El usuario eligió «cierra» y reanudó el
  cierre con «sigue» después de consolidar 7.1. 7.2 y 7.3 son **No aplica**;
  no se añaden `response_model`, errores de dominio, validaciones, filtros ni
  correcciones de los once hallazgos vivos.
- **Mantener la verificación manual propia como pendiente.** No se recibió
  evidencia de ejecución del guion de `plan_de_clases`; el cierre documental
  no la convierte en cumplida.
- **No activar el dominio siguiente.** `branding`, `profesores` y
  `super_admin` continúan en espera y necesitarán una orden explícita que
  nombre uno de ellos.

## Riesgos

- **Dependencia explícita desde infraestructura compartida.** `permissions.py`
  y `main.py` importan ahora dos operaciones específicas del repositorio de
  planes. Es el coste de cerrar la frontera SQL sin mover recursos ni crear una
  abstracción genérica; la compuerta global protege ambos llamadores.
- **Almacenamiento no transaccional.** La base y los archivos pueden divergir;
  además, los reemplazos no retiran la imagen anterior y los fallos de borrado
  se absorben. No se corrigió.
- **Contratos permisivos o incompletos.** La versión es opcional, `periodo` y
  textos carecen de algunos límites, dos listas son ilimitadas y el esquema de
  respuesta existente recortaría campos. No se corrigió.
- **Carga SQL no visible como N+1 de aplicación.** Las tres subconsultas
  correlacionadas por fila pueden combinarse con el historial ilimitado. No se
  optimizó ni se modificó SQL.
- **Acceso heredado a asignaciones inactivas.** Los guards específicos fijados
  por las pruebas no filtran `asignaciones.activo`. No se cambió ownership ni
  permisos.
- **Validación y errores heterogéneos.** La imagen se valida por declaraciones
  del cliente y las rutas no comparten un único modelo de error. Quedan fuera
  de 7.0.
- **Verificaciones heredadas pendientes.** Conservan sus riesgos y esta
  activación no las considera cumplidas.
- **Cobertura manual de `planeador_anual` sin desglose.** La revisión reportada
  permite continuar, pero no demuestra individualmente los siete escenarios ni
  un entorno desplegado.
- **Verificación manual de `plan_de_clases` pendiente.** Las pruebas automáticas
  protegen contratos y equivalencia, pero no sustituyen un recorrido con la
  aplicación y un almacenamiento configurado.
- **Publicación no comprobada.** La referencia local `origin/main` permanece
  tres commits detrás de `HEAD`; no se consultó el remoto real y no se atribuye
  despliegue ni GitHub Actions.

## Staging

No se hizo staging ni deploy en este cierre. Cuando el usuario autorice la
publicación, el artefacto revisado debe incluir el commit local de 7.1
`98c438fb6621bcc337c928f2f60238ca2c05d949` y el futuro commit documental de
cierre. En un entorno no productivo con tenant y almacenamiento representativos
se deben recorrer las once entradas y `/uploads`, observando respuestas,
permisos, conteos de consultas y ciclo de vida de las imágenes. La compuerta
automática debe ejecutarse sobre exactamente el artefacto que vaya a desplegarse.

## Rollback

- Punto anterior a toda la capa:
  `bfe80d4152b802aeb22f4c5a2c5aab9265ba7630`.
- Antes de cualquier publicación, el usuario puede revertir los commits locales
  de esta capa mediante su flujo normal de Git. Este cierre no ejecuta esa
  operación.
- Si la capa se publica, el rollback exige un commit de reversión, push y nuevo
  despliegue autorizados; ya no sería una operación solo local.
- La capa no ejecutó migraciones, DDL, DML, conexiones a PostgreSQL ni cambios
  reales de almacenamiento. No existe rollback de datos; las pruebas de archivos
  usaron dobles y no crearon objetos reales.

## Verificación manual

Estado: **Pendiente**. El usuario no reportó todavía la ejecución del guion.
Debe realizarse contra un artefacto identificado y registrar el entorno:

1. Como profesor, crear, actualizar y consultar un plan con cero, una y dos
   imágenes, confirmando payload, fechas y campos `created_at`/`updated_at`.
2. Repetir una actualización con `version_esperada` vigente y otra obsoleta,
   confirmando el conflicto 409 sin pérdida de datos.
3. Como admin, listar y abrir el detalle con filtros y paginación; revisar el
   plan y crear una observación.
4. Como profesor dueño, listar observaciones y marcar una como vista; comprobar
   el conteo y los items de `/notificaciones/planeadores` para ambos roles.
5. Servir y borrar cada slot de imagen como profesor y como admin, verificando
   el proveedor de almacenamiento configurado y que el otro slot no cambie.
6. Confirmar 403 para rol u ownership no autorizado y aislamiento entre dos
   tenants, incluida la lectura de `/uploads`.
7. Confirmar los 400, 404, 409 y 422 caracterizados para entradas inválidas,
   ausentes o en conflicto, sin cambios en los mensajes observables.
8. Revisar logs y métricas del entorno sin atribuir a esta capa correcciones de
   concurrencia, paginación, validación de contenido o almacenamiento.

## Registro de ejecución

### 2026-08-22 — activación de la capa para `plan_de_clases`

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git validado directamente.
- Documentos leídos completamente y en orden: índice maestro,
  `07_PLANEADOR_ANUAL.md`, instrucciones locales —no se encontraron— y
  `PLANTILLA_CAPA.md`.
- Autorización: el usuario informó «planeador revisado» y ordenó «sigue con plan
  de clases», nombrando el dominio.
- Rama acordada y observada: `main`.
- Estado antes de escribir: árbol limpio; `git status --porcelain=v1 --branch`
  mostró únicamente `## main...origin/main`.
- Commit base: `bfe80d4152b802aeb22f4c5a2c5aab9265ba7630`, el `HEAD`
  limpio vigente y coincidente con la referencia local `origin/main`.
- Continuidad: el base `235672e` de `planeador_anual` es ancestro. Sus cuatro
  descendientes son `6358c5a` —activación—, `2a8d3c3` —7.0—, `51203da` —7.1—
  y `bfe80d4` —cierre documental—. El último modifica únicamente la bitácora y
  el índice, tal como describe el cierre.
- Estado de publicación observado localmente: `HEAD` y la referencia local
  `origin/main` coinciden. No se consultó el remoto real ni se verificó GitHub
  Actions.
- Verificación manual anterior: registrada como completada de forma global a
  partir del reporte «planeador revisado»; entorno y desglose no especificados.
- Decisión heredada: las demás verificaciones pendientes siguen abiertas con
  su riesgo y ninguna se marca como cumplida.
- Archivos creados o modificados: esta bitácora,
  `07_PLANEADOR_ANUAL.md` y `docs/modularizacion/README.md`.
- Código de producto, pruebas, consultas, migraciones, esquemas, configuración
  y dependencias inspeccionados o modificados: **ninguno**.
- Pruebas, conexiones a PostgreSQL, acceso a producción, commit, push y deploy:
  **ninguno**.
- Verificación documental: `git diff --check` terminó en exit 0 para los dos
  archivos rastreados; la comprobación `--no-index --check` de esta bitácora
  nueva no reportó errores de whitespace —su exit 1 indica que difiere de
  `NUL`—. Los avisos fueron únicamente de normalización futura LF/CRLF.
  `git status --short` mostró exactamente esta bitácora nueva y los otros dos
  documentos modificados. La tabla del índice y el conjunto de bitácoras
  contienen exactamente una capa marcada **Activa**, `plan_de_clases`.
- Siguiente acción exacta: ejecutar únicamente 7.0 conforme al trabajo exacto
  de esta bitácora y detenerse antes de 7.1.

### 2026-08-22 — cierre de la subcapa 7.0

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git y commits locales
  validados directamente.
- Autorización: la orden posterior «continua» habilitó únicamente la primera
  subcapa pendiente, 7.0.
- Precondiciones antes de modificar: rama `main`; árbol limpio según
  `git status --porcelain=v1 --branch`, que mostró
  `## main...origin/main [ahead 1]`; `HEAD`
  `31b3f6b4924dbec475a229d6f9d4a67bcbbd2336`; el commit base
  `bfe80d4152b802aeb22f4c5a2c5aab9265ba7630` es ancestro.
- Continuidad desde el base: existe un solo commit posterior, `31b3f6b`
  (`feat(plan_de_clases): add initial documentation for plan_de_clases domain
  and update README`). Su diff modifica `07_PLANEADOR_ANUAL.md`, crea esta
  bitácora y actualiza el índice, exactamente como registra la activación. No
  hay commits locales sin explicar.
- Estado de publicación: la referencia local `origin/main` está un commit por
  detrás. No se consultó el remoto real, no hubo push y no se atribuye una
  ejecución de GitHub Actions.
- Fuentes inspeccionadas: los cinco archivos propios inventariados; el montaje
  y acceso compartido a `/uploads`; guards de permisos; resolutor académico;
  almacenamiento; DDL base y seis migraciones específicas; y las seis suites
  heredadas relacionadas. No se inspeccionaron dominios siguientes.
- Archivo funcional agregado:
  `tests/test_plan_de_clases_caracterizacion.py`, con **22 pruebas** para
  frontera, once rutas, esquemas, localización del SQL, recursos, DDL, ASGI,
  conteos y consultas ilimitadas. Código de producto modificado: **ninguno**.
- Línea base heredada específica: los dos primeros intentos dentro del sandbox
  terminaron con **99 passed y 6 errores de setup** por `PermissionError` al
  directorio temporal global de pytest, no por fallos del producto. La misma
  ejecución fuera de esa restricción terminó con **105 passed** y 5 warnings
  heredados.
- Línea base global heredada: `scripts\verify.py` terminó con **987 passed**,
  Ruff correcto y dependencias íntegras.
- Durante el desarrollo fallaron tres expectativas de la prueba nueva —formato
  UTC y clasificación de dos dobles SQL—; se corrigió solo la caracterización,
  sin cambiar producto.
- Verificación nueva: **22 passed**. Suite específica final: **127 passed** y 5
  warnings heredados. Ruff de la prueba nueva: **All checks passed**.
  Compuerta global final: **1009 passed**, Ruff correcto y dependencias
  íntegras.
- Los ocho supuestos quedaron resueltos —seis confirmados, uno con matiz y uno
  refutado— y los doce hallazgos se registraron sin corregirlos.
- Archivos de la subcapa: la caracterización nueva, esta bitácora y
  `docs/modularizacion/README.md`. No hubo DB, migraciones, producción, commit,
  push ni deploy.
- Revisión final de alcance: `git diff --check` terminó en exit 0 para los dos
  documentos rastreados; `git diff --no-index --check -- NUL
  tests/test_plan_de_clases_caracterizacion.py` no reportó errores de
  whitespace —exit 1 porque el archivo nuevo difiere de `NUL`—. Los avisos son
  únicamente de normalización futura LF/CRLF. `git status --short --branch`
  mostró exactamente ambos documentos modificados y la prueba nueva, sobre
  `main...origin/main [ahead 1]`; no hay archivos de producto. El índice y las
  bitácoras conservan exactamente una capa **Activa**, `plan_de_clases`.
- Siguiente acción exacta: presentar para autorización el alcance de 7.1 a
  partir de las dos consultas específicas externas y detenerse. No iniciar la
  extracción por inferencia.

### 2026-08-22 — cierre de la subcapa 7.1

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git y commits locales
  validados directamente.
- Autorización: la respuesta «continua» llegó inmediatamente después de
  presentar la extracción exacta de las dos consultas externas y autorizó solo
  7.1.
- Precondiciones antes de modificar: rama `main`; árbol limpio según
  `git status --porcelain=v1 --branch`, que mostró
  `## main...origin/main [ahead 2]`; `HEAD`
  `80f7f21de0f2a77d40fb710cc1cc9fd4dc911fde`; el commit base
  `bfe80d4152b802aeb22f4c5a2c5aab9265ba7630` es ancestro.
- Continuidad desde el base: exactamente dos commits posteriores. `31b3f6b`
  contiene la activación documental; `80f7f21` contiene los tres archivos
  registrados de 7.0 —bitácora, índice y caracterización—. Ambos están
  explicados y no había divergencia ni cambios previos.
- Estado de publicación observado: la referencia local `origin/main` estaba
  dos commits detrás. No se consultó el remoto real, no hubo push y no se
  atribuye GitHub Actions.
- Archivos inspeccionados para 7.1: las dos funciones llamadoras, el repositorio
  existente, la caracterización y las pruebas específicas de permisos y
  uploads; además se comprobó que el resolutor importado por el repositorio no
  crea un ciclo. No se abrió código de los dominios siguientes.
- Línea base específica: el sandbox produjo **36 passed y 6 errores de setup**
  por el mismo `PermissionError` del directorio temporal de pytest. La
  repetición fuera de esa restricción terminó con **42 passed** y 5 warnings
  heredados.
- Caracterización previa al producto: se agregaron dos casos parametrizados
  para SQL/parámetros y se cambiaron las guardias de ubicación. Contra el
  producto anterior hubo **4 fallos y 20 casos correctos**: 25 en vez de 27
  ejecuciones, dos funciones ausentes y ownership aún externo. Fue la señal
  esperada.
- Producto modificado: `app/repositories/plan_de_clases_repository.py` añadió
  dos funciones que reciben cursor; `app/core/permissions.py` y `app/main.py`
  delegan solo su consulta/fetch. El repositorio pasó de 753 a **784 líneas** y
  de 25 a **27 sitios `cursor.execute`**; los cinco archivos propios suman
  **1365 líneas**.
- Equivalencia: los dos literales SQL se conservaron byte a byte, incluidos sus
  espacios heredados; también sus tuplas de parámetros. Los llamadores
  conservan conexión, cursor, `finally`, cierres, orden, retornos y 403. No se
  añadió `activo` ni se cambió otro hallazgo.
- La primera ejecución posterior dejó **23 passed y un fallo esperado** por el
  recuento estructural anterior de 1334 líneas. Tras actualizarlo a 1365, la
  caracterización terminó con **24 passed**.
- Suite específica final: **129 passed** y 5 warnings heredados. Ruff sobre los
  cuatro archivos funcionales modificados: **All checks passed**. Compuerta
  global: **1011 passed**, Ruff correcto y dependencias íntegras.
- Archivos de 7.1: tres archivos de producto, la caracterización, esta bitácora
  y el índice maestro. No hubo DB, migraciones, producción, commit, push ni
  deploy.
- Revisión final: `git diff --check` terminó en exit 0; los avisos fueron solo
  de normalización futura LF/CRLF. `git status --short --branch` mostró
  exactamente los seis archivos de 7.1 sobre `main...origin/main [ahead 2]`:
  los tres de producto, la caracterización, esta bitácora y el índice. La
  revisión completa del diff no encontró migraciones, configuración, otros
  dominios ni cambios ajenos. El índice y las bitácoras conservan exactamente
  una capa **Activa**, `plan_de_clases`.
- Siguiente acción exacta: presentar la decisión entre cerrar la capa como
  refactorización pura —7.2/7.3 No aplica— o autorizar una única 7.2 concreta.
  No iniciar ninguna alternativa por inferencia.

### 2026-08-22 — cierre de la capa para `plan_de_clases`

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git y commits locales
  validados directamente.
- Documentos leídos completamente y en orden: índice maestro, esta bitácora e
  instrucciones locales —no se encontraron—. No se inspeccionó código de los
  dominios siguientes.
- Autorización: el usuario ordenó «cierra». El primer intento se detuvo porque
  los seis cambios de 7.1 seguían preparados en el índice de Git. Tras
  consolidarlos, «sigue» reanudó únicamente el cierre ya autorizado.
- Precondiciones antes de modificar documentación: rama `main`; árbol limpio
  según `git status --porcelain=v1 --branch`, que mostró solo
  `## main...origin/main [ahead 3]`; `HEAD`
  `98c438fb6621bcc337c928f2f60238ca2c05d949`; el commit base
  `bfe80d4152b802aeb22f4c5a2c5aab9265ba7630` es ancestro.
- Continuidad desde el base: exactamente tres commits posteriores, todos
  explicados. `31b3f6b` activa documentalmente la capa; `80f7f21` contiene 7.0;
  `98c438f` contiene 7.1. `git show --name-status` confirmó que el último toca
  exactamente los seis archivos registrados: tres de producto, la
  caracterización, esta bitácora y el índice maestro.
- Estado de publicación observado: la referencia local `origin/main` está tres
  commits detrás. No se consultó el remoto real, no hubo push ni deploy y no se
  atribuye una ejecución de GitHub Actions.
- Suite específica de cierre: **129 passed** y 5 warnings heredados.
- Compuerta global de cierre: **1011 passed** y 5 warnings heredados; Ruff
  terminó con **All checks passed** y `pip check` con **No broken requirements
  found**.
- Decisión: cerrar como refactorización pura. 7.2 y 7.3 son **No aplica**; los
  once hallazgos abiertos permanecen registrados y no se añadió
  `response_model`, error de dominio, filtro, validación ni otra corrección.
- Archivos del cierre: esta bitácora y
  `docs/modularizacion/README.md`. Código de producto, pruebas, configuración,
  migraciones y dependencias modificados durante el cierre: **ninguno**.
- Staging y rollback: documentados en sus secciones. No se ejecutaron acciones
  externas ni cambios reales de base o almacenamiento.
- Verificación manual propia: **pendiente**; el guion quedó documentado sin
  atribuir ningún resultado no reportado.
- Revisión de alcance: `git diff --check` terminó en exit 0; los avisos fueron
  solo de normalización futura LF/CRLF. `git status --short --branch` mostró
  únicamente los dos documentos del cierre sobre `main...origin/main [ahead
  3]`. El índice y las bitácoras dejan **cero capas activas**.
- Siguiente acción exacta: elegir entre completar la verificación manual de
  `plan_de_clases` o autorizar explícitamente continuar localmente aceptando que
  quede pendiente; para activar otra capa, la misma orden debe nombrar además
  uno de `branding`, `profesores` o `super_admin`.

## Entrega al próximo chat

- Capa activa: **ninguna**.
- Última capa cerrada: **7 para `plan_de_clases`**, el 2026-08-22.
- Subcapas: **7.0 y 7.1 cerradas**; **7.2 y 7.3 No aplica**.
- Código de producto modificado en 7.1: repositorio, guard de plan y guard del
  endpoint compartido de uploads; el cierre posterior es solo documental.
- Caracterización: **24 pruebas**; específicas de cierre **129 passed**;
  compuerta global de cierre **1011 passed**, Ruff correcto y dependencias
  íntegras.
- Resultado estructural: cinco archivos propios y 1365 líneas, once entradas,
  tres tablas y los **27 sitios `cursor.execute`** dentro del repositorio. Los
  dos llamadores compartidos ya no tienen SQL de este dominio y conservan sus
  recursos. De los doce hallazgos, el primero está resuelto y **once siguen
  vivos**.
- Verificación manual de `planeador_anual`: completada de forma global, sin
  entorno ni desglose punto por punto reportados.
- Verificación manual propia de `plan_de_clases`: **pendiente**; no marcarla
  como cumplida sin un reporte del usuario.
- Verificaciones heredadas: pendientes; ninguna se marca como cumplida.
- Dominios en espera: `branding`, `profesores` y `super_admin`; ninguno está
  activado.
- Publicación: no comprobada; la referencia local `origin/main` está tres
  commits detrás del `HEAD` de 7.1 y no se consultó el remoto real.
- Bloqueos técnicos: ninguno.
- Siguiente acción exacta: pedir al usuario una decisión explícita entre
  completar la verificación manual propia o continuar aceptando que permanezca
  pendiente. Solo después, y si además nombra el dominio, se puede activar uno
  de los tres dominios en espera.
