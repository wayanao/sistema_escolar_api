# Capa 0: línea base y calidad

Última revisión: 2026-08-10.

## Control

- Estado: Activa; subcapas 0.0 y 0.1 cerradas.
- Commit base: `b8c7653445a50bc1e230a19e0ca8bb088c47cb69`.
- Rama observada al documentar: `main`, alineada con `origin/main`.
- Rama de trabajo acordada por el usuario: `main`.
- Commit observado al ejecutar 0.1:
  `d5d9f80424c2c2683e45941f6583e0367ac54295`.
- Primera subcapa pendiente: 0.2, comando global local de verificación.
- Código de producto modificado: Ninguno.

## Objetivo

Establecer una línea base confiable antes de tocar conexiones, concurrencia,
migraciones o dominios. Al cerrar esta capa, cualquier chat o desarrollador debe
poder ejecutar una sola compuerta y distinguir un fallo nuevo de uno preexistente.

## Alcance autorizado

- Inventario de contratos HTTP que deberán conservar las capas posteriores.
- Caracterización reproducible del estado actual de pruebas y herramientas.
- Corrección de las tres pruebas identificadas como sensibles a la fecha real.
- Un comando global de verificación local.
- CI que ejecute la misma compuerta en un entorno limpio.
- Documentación estrictamente relacionada.

## Fuera de alcance

- Mover rutas, controladores, services o repositories.
- Cambiar conexiones, pool, transacciones o timeouts.
- Modificar comportamiento `async`, threadpool o `ContextVar`.
- Ejecutar o cambiar migraciones de tenants.
- Optimizar consultas, agregar índices o usar `EXPLAIN ANALYZE`.
- Agregar `response_model` o normalizar errores de producto.
- Corregir fallos funcionales ajenos a las tres pruebas temporales.

## Línea base conocida

Una auditoría previa registró estos resultados, que deben reproducirse y
detallarse en la subcapa 0.0 antes de modificar pruebas:

| Comprobación | Resultado previo |
|---|---|
| Descubrimiento de pytest | 192 pruebas |
| Suite consolidada | 189 pasaron; 3 fallaron por sensibilidad temporal |
| Uploads con temporal controlado | 6 pasaron |
| Ruff global sin caché | Correcto |
| `pip check` | Correcto |
| CI del repositorio | No encontrado |
| Comando global único | No encontrado |

Estos números son evidencia previa, no el resultado final de esta capa. La
bitácora debe registrar nombres de pruebas, comandos completos, entorno y salida
actual cuando comience la subcapa 0.0.

## Línea base reproducida en 0.0

Ejecución del 2026-08-10 sobre Windows, rama `main`, árbol inicialmente limpio
y `HEAD` en `a991ee205a3e6454f77edb7919d0c95e8080dc9a`:

| Herramienta | Versión observada |
|---|---|
| Python | 3.14.3 |
| pytest | 9.0.3 |
| Ruff | 0.15.12 |
| pip | 25.3 |

Comandos reproducibles desde la raíz del repositorio:

| Comprobación | Comando | Resultado observado |
|---|---|---|
| Descubrimiento | `.\venv\Scripts\python.exe -m pytest --collect-only -q` | Exit 0; 192 pruebas, 5 warnings, 1.41 s |
| Suite consolidada | `.\venv\Scripts\python.exe -m pytest -q` | Exit 1; 189 pasaron, 3 fallaron, 5 warnings, 1.25 s |
| Tres fallos conocidos | `.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_super_admin.py::test_listar_tenants_controller_reads_public_colegios tests\test_super_admin.py::test_actualizar_estado_tenant_controller_validates_status tests\test_super_admin.py::test_actualizar_estado_tenant_controller_same_status_does_not_audit` | Exit 1; 3 fallaron, 0.51 s |
| Uploads con temporal accesible | `.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp .tmp_pytest_uploads_00 tests\test_uploads_permissions.py` | Exit 0; 6 pasaron, 5 warnings, 0.74 s; temporal retirado después |
| Ruff global sin caché | `.\venv\Scripts\python.exe -m ruff check --no-cache app tests scripts apply_migration.py` | Exit 0; `All checks passed!`; no creó `.ruff_cache` |
| Dependencias instaladas | `.\venv\Scripts\python.exe -m pip check` | Exit 0; `No broken requirements found.` |

No existen configuración de pytest/Ruff en `pyproject.toml`, `pytest.ini`,
`ruff.toml`, `.ruff.toml`, `tox.ini` o `setup.cfg`; tampoco existe una compuerta
única local ni `.github/workflows`. Por ello los comandos anteriores son la
fuente reproducible provisional hasta ejecutar 0.2 y 0.3.

Los cinco warnings son uno deprecado de `asyncio.iscoroutinefunction` emitido
por SlowAPI y cuatro avisos de configuración Pydantic V2 en los schemas de
branding, planeador anual, plantilla y usuario. Se registran como línea base;
corregirlos no pertenece a 0.0.

### Tres fallos sensibles al reloj

Los fallos exactos son:

1. `tests/test_super_admin.py::test_listar_tenants_controller_reads_public_colegios`;
2. `tests/test_super_admin.py::test_actualizar_estado_tenant_controller_validates_status`;
3. `tests/test_super_admin.py::test_actualizar_estado_tenant_controller_same_status_does_not_audit`.

Las tres pruebas fijan `fecha_proximo_pago = date(2026, 7, 1)` y
`dias_gracia = 5`, pero no fijan el día actual. Los tres caminos llaman
`calculate_effective_tenant_status`, que usa `date.today()` cuando no recibe
`today`. El 2026-08-10 ya había pasado el límite 2026-07-06 y el estado efectivo
correctamente pasó a `suspendido`; las aserciones todavía esperaban `activo` o
`en_mora`. La evidencia está en `tests/test_super_admin.py`,
`app/controllers/super_admin_controller.py` y `app/core/tenant_status.py`.

Esto caracteriza datos de prueba dependientes del calendario, no una regresión
de producto. 0.1 deberá controlar explícitamente el reloj o usar datos relativos
sin relajar las aserciones. En el entorno restringido, `tmp_path` produjo además
seis `PermissionError` artificiales bajo el temporal del sistema; la ejecución
con un `--basetemp` accesible confirmó que las seis pruebas de uploads pasan.

## Contratos que la línea base debe registrar

No es necesario describir toda la implementación. Para cada familia de
endpoints se necesita como mínimo:

- método y path;
- actor y permiso;
- contexto tenant y ownership;
- entrada: query, path, JSON o multipart;
- status y forma de respuesta exitosa;
- errores observables relevantes;
- transacción, archivos u otros efectos;
- pruebas existentes que lo protegen.

El catálogo global `docs/API_ENDPOINTS.md` puede utilizarse como punto de
partida, pero la caracterización verificable debe enlazar pruebas o evidencia.

### Convenciones transversales observadas

- El catálogo de métodos y paths es `docs/API_ENDPOINTS.md`; el registro
  ejecutable está en `app/main.py` y `app/routes/*.py`.
- Ningún decorator de ruta declara `response_model` ni un `status_code` de
  éxito distinto. En la capa HTTP observada el éxito es, por tanto, `200` y la
  forma JSON heredada es el retorno directo del controlador, salvo descargas
  binarias. La validación de path, query y modelos Pydantic conserva `422`.
- Una sesión tenant acepta Bearer o cookie `token`. `get_current_user` valida
  firma, `sub`, rol y schema tenant, comprueba que el tenant siga habilitado,
  fija el `ContextVar` y revalida el usuario en su schema. Sus errores comunes
  son `401`; tenant bloqueado, rol insuficiente u ownership inválido producen
  `403` según el guard aplicable.
- `get_current_active_admin` restringe las rutas administrativas. Los guards
  de estudiante, profesor, asignación y plan de clases conservan ownership o
  pertenencia académica. Super admin usa exclusivamente el schema `public` y
  su propia revalidación.
- La columna de efectos identifica el límite observable que debe preservarse.
  La propiedad exacta de `commit`, `rollback`, cursor y conexión sigue en los
  controladores/repositorios existentes y no se modificó ni generalizó en 0.0.

### Inventario de contratos por familia

Cada enlace de la primera columna contiene la lista completa de métodos y paths.
Cuando no hay prueba dedicada se deja el hueco explícito y el router queda como
evidencia mínima, sin leer controladores no necesarios.

| Familia y métodos/paths | Actor, tenant y ownership | Entrada y éxito observable | Errores y efectos que deben preservarse | Evidencia existente |
|---|---|---|---|---|
| [Auth](../API_ENDPOINTS.md#auth) | Login/logout públicos; cambio de password con sesión tenant de admin | JSON; login devuelve identidad/rol/tenant y fija cookie HttpOnly; logout elimina cookie; cambio devuelve mensaje y flag | `401`, tenant bloqueado `403`, límite 5/min; crea/elimina cookie y actualiza password | [router](../../app/routes/auth.py), [tests tenant](../../tests/test_auth_tenant.py), [tests super admin](../../tests/test_super_admin.py) |
| [Tenant](../API_ENDPOINTS.md#tenant) | Usuario tenant autenticado; solo su schema del JWT | Sin body; `200` con `estado`, `mostrar_aviso`, `mensaje` | `401/403`; lectura de estado efectivo en `public`, sin mutación | [router](../../app/routes/tenant.py), [tests](../../tests/test_auth_tenant.py) |
| [Super Admin](../API_ENDPOINTS.md#super-admin) | `super_admin` autenticado, tenant/schema `public` | Path y JSON; `200` con listas o ficha tenant/auditoría | `401`, `404`, `422`; alta crea colegio, schema/admin/suscripción y auditoría; cambio de estado es transaccional | [router](../../app/routes/super_admin.py), [tests](../../tests/test_super_admin.py) |
| [Uploads](../API_ENDPOINTS.md#uploads) | Usuario autenticado del mismo tenant; branding del tenant o plan de admin/profesor propietario | Path catch-all; `200` binario local o stream remoto | `401`, `403`, `404`; solo lectura de archivo, con consulta de ownership para planeadores | [ruta y guard](../../app/main.py), [6 pruebas](../../tests/test_uploads_permissions.py) |
| [Estudiantes](../API_ENDPOINTS.md#estudiantes) | Admin activo del tenant | JSON, path y filtros `estado/limit/offset`; `200` lista legacy, página o ficha | `404`, `422`; crea/actualiza y cambia estado; deudas es lectura financiera | [router](../../app/routes/estudiantes.py), [paginación/estado](../../tests/test_estudiantes_pagination.py); sin prueba HTTP dedicada para detalles/deudas |
| [Cuentas](../API_ENDPOINTS.md#cuentas) | Admin activo del tenant | `curso_id` o `estudiante_id`; `200` JSON heredado | Errores heredados del controlador; solo lectura de cartera | [router](../../app/routes/cuentas.py); sin prueba dedicada |
| [Pagos](../API_ENDPOINTS.md#pagos) | Admin activo del tenant | JSON, path y paginación; `200` conserva lista/página, opciones, pago o anulación | `400`, `409` por regla/migración; transacciones financieras, aplicaciones, saldos y anulaciones | [router](../../app/routes/pagos.py), [paginación](../../tests/test_pagos_pagination.py), [vencidos](../../tests/test_pagos_meses_vencidos.py), [adelantos](../../tests/test_pagos_adelantados.py), [anulaciones](../../tests/test_anulaciones_financieras.py) |
| [Cursos](../API_ENDPOINTS.md#cursos) | Admin activo del tenant | JSON, path y `estado/limit/offset`; `200` lista legacy/página o resultado | `404`, duplicado `409`, validación `422`; crea/actualiza/desactiva | [router](../../app/routes/cursos.py), [tests](../../tests/test_catalogos_pagination.py) |
| [Profesores](../API_ENDPOINTS.md#profesores) | Admin activo del tenant | JSON, path y `estado/limit/offset`; `200` lista legacy/página o resultado | `404`, duplicado `409`, validación `422`; crea/actualiza/desactiva y afecta login/asignación | [router](../../app/routes/profesores.py), [catálogos](../../tests/test_catalogos_pagination.py), [asignaciones](../../tests/test_asignaciones_activo.py) |
| [Asignaciones](../API_ENDPOINTS.md#asignaciones) | Mutaciones/listados administrativos con admin; lecturas docentes limitadas al profesor/asignación indicada | JSON, path, query y orden completo; `200` lista legacy/página, horarios o resultado | `400`, `403`, `404`, `409`; desactiva sin borrar historial y actualiza horarios/orden | [router](../../app/routes/asignaciones.py), [paginación](../../tests/test_asignaciones_pagination.py), [estado/validaciones](../../tests/test_asignaciones_activo.py), [guards](../../tests/test_permissions.py) |
| [Notas y boletín legacy](../API_ENDPOINTS.md#notas-y-boletin-legacy) | Usuario autenticado; admin o profesor con acceso al estudiante/asignación | JSON y path; `200` notas, boletín o planilla heredada | `403` de ownership/pertenencia; escritura/lectura académica | [router](../../app/routes/notas.py), [tests](../../tests/test_notas_permissions.py) |
| [Planilla](../API_ENDPOINTS.md#planilla) | Usuario autenticado con scope de asignación | JSON y path; `200` resultado JSON o archivo Excel | `403` y validación `422`; registra/elimina tipos de nota y genera archivo | [router](../../app/routes/planilla.py), [guards](../../tests/test_permissions.py); sin prueba HTTP dedicada |
| [Asistencia](../API_ENDPOINTS.md#asistencia) | Usuario autenticado con acceso a la asignación; estudiante debe pertenecer a ella | Lote JSON, path; `200` resultado/historial | `403`, lote inválido `422`; reemplazo parcial transaccional con rollback probado | [router](../../app/routes/asistencia.py), [tests](../../tests/test_asistencia_validaciones.py) |
| [Materias](../API_ENDPOINTS.md#materias) | Admin activo del tenant | JSON, path y `estado/limit/offset`; `200` lista legacy/página o resultado | `404`, duplicado `409`, validación `422`; crea/actualiza/desactiva | [router](../../app/routes/materias.py), [tests](../../tests/test_catalogos_pagination.py) |
| [Observaciones](../API_ENDPOINTS.md#observaciones) | Usuario autenticado con acceso a estudiante/asignación | JSON y path; `200` ficha/resultado con dimensiones normalizadas | `403`, contenido vacío `422`; crea o actualiza observación académica | [router](../../app/routes/observaciones.py), [tests](../../tests/test_observaciones_validaciones.py) |
| [Plan de clases](../API_ENDPOINTS.md#plan-de-clases) | Profesor propietario para su plan/observaciones; admin activo para bandeja y revisión | Multipart/JSON, path y query; `200` ficha/lista/resultado | `400`, `403`, conflicto de versión `409`, fallos de archivo `500`; DB, notificaciones e imágenes con limpieza en conflicto | [router](../../app/routes/plan_de_clases.py), [integridad](../../tests/test_plan_de_clases_integridad.py), [revisión](../../tests/test_plan_de_clases_revision.py), [guards](../../tests/test_permissions.py) |
| [Planeador anual](../API_ENDPOINTS.md#planeador-anual) | Usuario autenticado con scope de asignación | Path y lista JSON por slots; `200` lista/resultado | Validación `422`, errores mapeados a `500`; upsert/eliminación transaccional de slots | [router](../../app/routes/planeador_anual.py), [tests](../../tests/test_planeador_anual_validaciones.py) |
| [Dashboard](../API_ENDPOINTS.md#dashboard) | Admin o profesor autenticado; profesor limitado a sí mismo, sus cursos y asignaciones | Path/query; `200` listas/rankings | `400`, ownership `403`, combinación inválida `422`; solo consultas académicas | [router](../../app/routes/dashboard.py), [guards](../../tests/test_permissions.py); sin prueba HTTP dedicada de dashboard |
| [Usuarios](../API_ENDPOINTS.md#usuarios) | Admin activo del tenant | JSON, path y paginación; `200` lista legacy/página o resultado | `400`, listado puede mapear fallo a `500`; CRUD de usuarios | [router](../../app/routes/usuario.py), [tests](../../tests/test_catalogos_pagination.py) |
| [Reportes](../API_ENDPOINTS.md#reportes) | Admin activo del tenant | Path/query y paginación; `200` JSON legacy o página | Errores de controlador `400`; consultas financieras sin mutación | [router](../../app/routes/reportes.py), [paginación](../../tests/test_reportes_pagination.py), [anulados](../../tests/test_anulaciones_financieras.py) |
| [Tipos de pagos](../API_ENDPOINTS.md#tipos-de-pagos) | Admin activo del tenant | JSON/path; `200` listas, detalle o resultado | `400`, `404`, `409`, borrado de tipo `405`; configura conceptos, cursos y excepciones personales; delete de excepción desactiva | [router](../../app/routes/tipos_pagos.py), [delete bloqueado](../../tests/test_catalogos_pagination.py), [flujos de pago](../../tests/test_pagos_meses_vencidos.py) |
| [Inventario](../API_ENDPOINTS.md#inventario) | Admin activo del tenant | JSON, path y `estado/limit/offset`; `200` lista legacy/página o resultado | `404`, borrado `405`, filtro `422`; crea/actualiza/desactiva, stock ligado a ventas | [router](../../app/routes/inventario.py), [tests](../../tests/test_inventario_pagination.py), [anulaciones](../../tests/test_anulaciones_financieras.py) |
| [Egresos](../API_ENDPOINTS.md#egresos) | Admin activo del tenant | JSON y rango de fechas; `200` lista/resultado | `400`, no manual `403`, borrado `405`, rango inválido `422`; escritura financiera, nómina no editable | [router](../../app/routes/egresos.py), [tests](../../tests/test_egresos_fechas.py) |
| [Préstamos](../API_ENDPOINTS.md#prestamos) | Admin activo del tenant | JSON, path y filtro `profesor_id`; `200` lista/resultado | `400`, `404`, borrado `405`, validación `422`; crea préstamo y solo transiciona a pagado | [router](../../app/routes/prestamos.py), [tests](../../tests/test_prestamos_validaciones.py) |
| [Ventas](../API_ENDPOINTS.md#ventas) | Admin activo del tenant | JSON, path, filtros y paginación compatible; `200` lista/página/resultado | `400`, delete `405`; transacción financiera, stock, pagos asociados y anulación | [router](../../app/routes/ventas.py), [paginación](../../tests/test_ventas_pagination.py), [anulaciones](../../tests/test_anulaciones_financieras.py) |
| [Nómina](../API_ENDPOINTS.md#nomina) | Admin activo del tenant | JSON/path bajo `/api/nomina`; `200` listas/resultado | Pago puede mapear fallo a `500`; registra nómina y egreso automático | [router](../../app/routes/nomina.py); sin prueba dedicada |
| [Boletines](../API_ENDPOINTS.md#boletines) | Usuario autenticado; guardado/referencia con scope académico y generación administrativa con admin | JSON/path bajo `/boletines`; `200` resultado, boletín o reporte | `403`, estudiante `404`, fallos mapeados a `500`; guarda definitivas o consulta respaldo/planilla vigente | [router](../../app/routes/boletines.py), [reporte parcial](../../tests/test_boletines_reporte_parcial.py) |
| [Branding](../API_ENDPOINTS.md#branding) | Lectura para usuario tenant; mutaciones solo admin | JSON, multipart y query `slot`; `200` ficha/resultado | `401/403` y validación; actualiza datos y logo tenant en almacenamiento | [router](../../app/routes/branding.py), [acceso a archivos](../../tests/test_uploads_permissions.py); sin prueba HTTP dedicada de mutación |
| [Plantillas](../API_ENDPOINTS.md#plantillas) | Lectura para usuario tenant; mutaciones solo admin | JSON, query y path; `200` listas/ficha/resultado | `401/403` y errores heredados; crea, activa, duplica y elimina plantillas | [router](../../app/routes/plantillas.py); sin prueba dedicada |
| [Cartera](../API_ENDPOINTS.md#cartera) | Admin activo del tenant | Query opcional `curso_id`; `200` mora o resumen JSON | Errores heredados; solo lectura financiera | [router](../../app/routes/cartera.py); sin prueba dedicada |

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 0.0 | Inventario reproducible de comandos, fallos y contratos | Cerrada |
| 0.1 | Tres pruebas temporales convertidas en deterministas | Cerrada |
| 0.2 | Comando global local de verificación | Pendiente |
| 0.3 | CI ejecutando la misma compuerta | Pendiente |
| 0.4 | Cierre documental y validación completa | Pendiente |

Solo se ejecuta una subcapa por turno salvo orden explícita del usuario.

## Subcapa 0.0: trabajo exacto

Trabajo ejecutado y cerrado en esta entrega:

1. Confirmar rama, estado limpio y commit base.
2. Identificar las tres pruebas temporales exactas y explicar por qué dependen
   del reloj, sin corregirlas todavía.
3. Registrar los comandos válidos para pytest, Ruff y `pip check` usando el
   entorno del repositorio.
4. Ejecutar y documentar la línea base sin modificar código.
5. Inventariar los contratos por familias usando `docs/API_ENDPOINTS.md`, las
   rutas y las pruebas, sin leer controladores no requeridos.
6. Actualizar esta bitácora y detenerse.

## Criterios para cerrar 0.0

- Los tres fallos tienen nombre, causa y evidencia.
- Los comandos de verificación se pueden copiar y repetir.
- Los fallos genuinos se distinguen de problemas del entorno local.
- Cada familia HTTP tiene al menos la ficha mínima de contrato o un enlace
  concreto a evidencia existente.
- No hay cambios en código de producto ni en comportamiento.
- Pruebas específicas aplicables y `git diff --check` están registrados.

## Subcapa 0.1: resultado

Las tres pruebas de `tests/test_super_admin.py` usan ahora la fixture
`fixed_tenant_status_today`. La fixture conserva la implementación real de
`calculate_effective_tenant_status` y solo proporciona explícitamente
`today = date(2026, 6, 15)` cuando el controlador la invoca. Esa fecha está
después del inicio del tenant y antes de `fecha_proximo_pago`, por lo que la
intención original de las tres pruebas ya no depende del calendario del host.

No se cambiaron las fechas de negocio, las aserciones, el controlador ni
`app/core/tenant_status.py`. La fixture tiene exactamente tres consumidores y
se aplica solo a los casos previamente identificados.

Resultados observados el 2026-08-10:

| Comprobación | Resultado |
|---|---|
| Tres nodos temporales con `-p no:cacheprovider` | 3 pasaron en 0.40 s |
| `.\venv\Scripts\python.exe -m pytest -q` | 192 pasaron, 5 warnings conocidos, 1.09 s |
| `.\venv\Scripts\python.exe -m ruff check --no-cache app tests scripts apply_migration.py` | `All checks passed!` |
| `.\venv\Scripts\python.exe -m pip check` | `No broken requirements found.` |

La suite completa se ejecutó con temporales normales fuera del sandbox para no
reintroducir los seis `PermissionError` ambientales de uploads ya caracterizados
en 0.0.

## Criterios para cerrar toda la capa 0

- La suite completa termina correctamente sin depender de la fecha actual.
- Existe un comando global documentado y reproducible.
- CI ejecuta la misma compuerta desde un checkout limpio.
- No se cambió ningún contrato HTTP ni comportamiento funcional.
- El diff pertenece exclusivamente a calidad, CI y documentación.
- Se documentaron decisiones, riesgos y rollback.
- El usuario autorizó activar la capa 1.

## Decisiones vigentes

- Las tres pruebas controlan explícitamente el reloj mediante una fixture local
  que reutiliza la implementación real; no se relajaron aserciones.
- La compuerta local y CI deben llamar las mismas verificaciones, evitando dos
  definiciones divergentes.
- Instalar o fijar dependencias no se mezclará automáticamente con esta capa;
  cualquier cambio deberá justificarse por reproducibilidad.
- La capa 0 no se utilizará para comenzar la modularización de dominios.
- En 0.0, el status de éxito y la forma de respuesta se registran como contrato
  heredado del router/controlador; no se agregan `response_model` ni
  normalizaciones hasta que una capa posterior los caracterice con pruebas.
- La ausencia de prueba dedicada se registra como hueco de caracterización, no
  como autorización para ampliar las subcapas siguientes.

## Riesgos

- Que una prueba aparentemente temporal revele en realidad un defecto de
  negocio. En ese caso se detiene y se solicita decisión.
- Diferencias de Windows/Linux en temporales o paths de uploads.
- Que CI necesite secretos o PostgreSQL no disponibles; deberá separarse una
  suite hermética de cualquier integración externa.
- Convertir el comando global en un script que oculte fallos o dependa del
  estado local.
- Python, pytest y Ruff están acotados con mínimos en `requirements.txt`, no
  fijados a las versiones observadas; un entorno limpio puede resolver otras
  versiones y deberá comprobarse en 0.3.
- Permanecen cinco warnings de terceros/schemas y varias familias HTTP sin
  prueba dedicada. Son deuda conocida fuera de 0.1 y no deben mezclarse con el
  comando global de 0.2.

## Registro de ejecución

### 2026-08-10 — subcapa 0.0

- Rama acordada: `main`.
- Commit base verificado:
  `b8c7653445a50bc1e230a19e0ca8bb088c47cb69`.
- Commit observado:
  `a991ee205a3e6454f77edb7919d0c95e8080dc9a`.
- Trazabilidad: el único commit posterior al base contiene exclusivamente la
  documentación inicial de este programa; antes de editar, el árbol estaba
  limpio y `main` estaba alineada con `origin/main`.
- Archivo modificado: `docs/modularizacion/00_LINEA_BASE_CALIDAD.md`.
- Código, rutas, payloads, SQL, transacciones y comportamiento modificados:
  ninguno.
- Fuentes inspeccionadas: `docs/API_ENDPOINTS.md`, registro de routers en
  `app/main.py`, `app/routes/*.py`, guards tenant/permisos y únicamente el
  controlador super admin necesario para explicar los tres fallos.
- Pruebas inspeccionadas: catálogo de `tests/test_*.py` y contenido concreto de
  `tests/test_super_admin.py`; los enlaces por familia identifican la evidencia
  adicional existente.
- Comandos y resultados: registrados en «Línea base reproducida en 0.0»; suite
  189/192, tres fallos temporales exactos, uploads 6/6, Ruff correcto y
  `pip check` correcto.
- Verificación documental: los 55 destinos locales únicos enlazados desde esta
  bitácora existen; `git diff --check` terminó con exit 0 y sin errores de
  whitespace (Git avisó de la normalización futura LF a CRLF en Windows).
- Problema ambiental separado: `tmp_path` no pudo usar el temporal restringido
  del sandbox; una repetición autorizada con `--basetemp` accesible pasó y el
  directorio temporal generado fue retirado.
- Decisión: cerrar 0.0 solo con documentación; no se corrigió ninguna prueba ni
  se inició 0.1.
- Subcapa cerrada: 0.0, inventario reproducible.
- Siguiente acción exacta: en 0.1, hacer deterministas únicamente las tres
  pruebas listadas de `tests/test_super_admin.py`, conservando las aserciones de
  estado efectivo; ejecutar primero esos tres nodos y después la suite, Ruff,
  `pip check` y `git diff --check`. No iniciar 0.2 en ese turno.

### 2026-08-10 — subcapa 0.1

- Rama acordada: `main`; árbol limpio antes de editar.
- Commit observado:
  `d5d9f80424c2c2683e45941f6583e0367ac54295`.
- Trazabilidad: los dos commits posteriores al base corresponden a la creación
  documental del programa y al cierre documentado de 0.0. `main` estaba un
  commit por delante de `origin/main`, sin divergencia remota ni push nuevo.
- Archivos modificados: `tests/test_super_admin.py` y esta bitácora.
- Implementación: fixture `fixed_tenant_status_today`, consumida solo por los
  tres nodos temporales, que pasa `date(2026, 6, 15)` al parámetro `today` de la
  función real.
- Contratos, código de producto, SQL, transacciones, permisos, tenant y
  ownership modificados: ninguno.
- Pruebas específicas: 3 pasaron en 0.40 s.
- Suite completa: 192 pasaron y permanecen los 5 warnings conocidos, en 1.09 s.
- Ruff global sin caché: correcto.
- `pip check`: correcto.
- `git diff --check`: exit 0, sin errores de whitespace; Git conserva el aviso
  conocido de normalización LF a CRLF en Windows.
- Alcance final del diff: únicamente `tests/test_super_admin.py` y esta
  bitácora, ambos pertenecientes a 0.1.
- Decisión: fijar el reloj en el límite de la prueba y conservar tanto los datos
  históricos como todas las aserciones originales.
- Riesgo residual: la fixture intercepta el símbolo importado por el controlador;
  si cambia esa integración, la prueba fallará de forma visible en vez de
  ocultar el cambio.
- Subcapa cerrada: 0.1, pruebas temporales deterministas.
- Siguiente acción exacta: en 0.2, crear un único comando local que ejecute la
  suite, Ruff y `pip check` con propagación fiel del código de salida; documentar
  su uso y detenerse sin crear CI ni iniciar 0.3.

## Entrega al próximo chat

- Leer primero `docs/modularizacion/README.md` completo.
- Leer después este archivo completo.
- Capa activa: 0.
- Primera subcapa pendiente: 0.2.
- Siguiente acción exacta: crear y documentar una sola compuerta local que
  ejecute pytest, Ruff y `pip check`; detenerse sin iniciar CI (0.3).
