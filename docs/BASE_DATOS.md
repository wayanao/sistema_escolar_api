# Base de Datos

Ultima revision documental: 2026-07-16.

## Motor

- PostgreSQL.
- Acceso desde Python con `psycopg2`.
- Pool: `ThreadedConnectionPool`.

## Configuracion de conexion

Archivo:

- `app/db/session.py`

Variables:

- `DATABASE_URL`
- `DB_POOL_MIN_CONNECTIONS`
- `DB_POOL_MAX_CONNECTIONS`

`get_pool()` crea un pool global lazy.

`get_connection()`:

- toma conexion del pool;
- pone `autocommit = False`;
- ejecuta `SET search_path`;
- devuelve `PooledConnection`.

`PooledConnection.close()`:

- intenta `rollback()`;
- devuelve la conexion al pool;
- si hay error de psycopg2, cierra esa conexion del pool.

`get_cursor(commit=False, cursor_factory=None)`:

- entrega cursor por context manager;
- si `commit=True`, hace commit al salir;
- en exception hace rollback.

## Regla operativa del pool

El pool de conexiones es un recurso limitado en produccion.

Reglas obligatorias:

- Todo `get_connection()` debe terminar cerrando cursor y conexion en un
  bloque `finally`.
- Para codigo nuevo se prefiere `get_cursor()` porque cierra cursor y conexion
  automaticamente.
- No se debe guardar una conexion global ni compartirla entre requests.
- Si una request falla, tambien debe cerrar conexion; si queda abierta, el pool
  puede agotarse.

Incidente documentado:

- En Render se observo `psycopg2.pool.PoolError: connection pool exhausted`.
- El login fue revisado para cerrar las conexiones abiertas en
  `app/controllers/auth_controller.py`.
- Si vuelve a aparecer el error, revisar primero rutas tocadas recientemente
  que usen `get_connection()` sin `finally`.

## Modelo multi-schema

- `public`: datos globales.
- `tenant_*`: datos de cada colegio.

Tabla global usada por login y scripts:

- `public.colegios`

Tabla global usada por administracion de plataforma:

- `public.super_admins`
- `public.tenant_suscripciones`
- `public.tenant_eventos_auditoria`
- `public.tenant_estado_auditoria`

Tabla global de historial de migraciones:

- `public.schema_migrations`

## Tablas observadas por el codigo

El codigo consulta o modifica tablas como:

- `usuarios`
- `profesor`
- `cursos`
- `materias`
- `estudiantes`
- `asignaciones`
- `notas`
- `notas_detalle`
- `boletin_cabecera`
- `boletin_detalles`
- `pagos`
- `pagos_aplicaciones`
- `tipos_de_pagos`
- `tipos_pagos_cursos`
- `tipos_pagos_estudiantes`
- `inventario`
- `ventas`
- `ventas_detalle`
- `egresos`
- `prestamos`
- `nomina`
- `plan_de_clases`
- `planeador_anual`
- `institucion_branding`
- `plantilla_impresion`

Nota sobre `institucion_branding`:

- Guarda la identidad institucional usada por los impresos del tenant.
- Incluye `codigo_dane` como texto opcional para conservar ceros a la
  izquierda.

Nota sobre `egresos`:

- `egresos.origen` identifica la fuente del movimiento.
- `manual`: egreso creado desde el modulo administrativo de Egresos.
- `nomina`: egreso automatico creado al pagar nomina.
- Solo los egresos `manual` son editables desde `/api/egresos/{id}`.
- Los egresos automaticos conservan su trazabilidad en el modulo que los
  genero.

Nota sobre `asignaciones`:

- `asignaciones.activo` indica si la asignacion sigue vigente en horarios y
  listados actuales.
- El sistema no debe borrar fisicamente asignaciones con historial academico.
  Al "eliminar" desde administracion se marca `activo = FALSE`.
- Planes de clase, asistencia, notas, boletines y observaciones conservan su
  referencia historica a la asignacion original.
- `asignaciones.orden_boletin` define el orden de impresion de materias por
  curso. El valor por defecto `100` conserva el orden alfabetico cuando el
  colegio no ha configurado prioridades.
- Si una materia tiene varios horarios activos en el mismo curso, todos esos
  horarios deben compartir el mismo `orden_boletin`.

Nota sobre `plan_de_clases`:

- Cada asignacion admite un solo plan por fecha.
- La migracion `20260722_plan_de_clases_integridad.sql` exige
  `asignacion_id` y `fecha`, y crea un indice unico sobre ambas columnas.
- El guardado usa un `INSERT ... ON CONFLICT DO UPDATE` atomico; actualizar un
  plan conserva las imagenes existentes cuando no se envian archivos nuevos.
- Cuando el cliente informa `version_esperada`, el guardado bloquea y compara
  la versión dentro de la misma transacción. La condición adicional del
  `ON CONFLICT` cubre también dos creaciones simultáneas para la misma
  asignación y fecha.
- La migracion se detiene ante datos incompletos o duplicados y no realiza
  limpiezas automaticas.
- `20260722_plan_de_clases_revision.sql` agrega a cada plan el estado de
  revision, una version incremental y las fechas de envio, primera vista y
  revision administrativa.
- Los estados permitidos son `pendiente`, `visto`, `con_observaciones` y
  `revisado`.
- `plan_de_clases_observaciones` conserva cada observacion, el administrador,
  la version exacta del plan y la fecha en que el profesor la vio.
- `con_observaciones` se conserva como estado técnico para identificar una
  corrección solicitada. Al guardar esa corrección aumenta la versión, pero no
  se crea otra fila en `plan_de_clases_notificaciones_admin` ni se devuelve el
  plan a pendiente.
- Un plan en `revisado` conserva su estado al ser editado por el profesor,
  tenga o no filas históricas en `plan_de_clases_observaciones`; aumenta la
  versión sin crear otra notificación administrativa.
- Las observaciones son historicas: una nueva version del plan no las elimina.
- Las llaves foraneas eliminan observaciones junto con su plan y conservan la
  observacion si un usuario administrador deja de existir.
- `plan_de_clases_notificaciones_admin` registra una fila por `plan_id` y
  `plan_version` enviada despues de habilitar las notificaciones. `leida_at`
  se completa al abrir, observar o revisar esa version desde administracion.
- La migracion de notificaciones no crea eventos retroactivos para planes
  historicos. Las notificaciones del profesor se derivan directamente de
  `plan_de_clases_observaciones.vista_por_profesor_at`, por lo que no duplican
  el historial ni requieren otra tabla.

## Cursos y cobros

Estado actual:

- `cursos` queda como entidad academica.
- Los cobros academicos se definen desde `tipos_de_pagos`.
- La asignacion de cobros por curso se hace en `tipos_pagos_cursos`.
- Las excepciones por estudiante se guardan en `tipos_pagos_estudiantes`.
- La regla de valor vigente es: valor activo del estudiante > valor activo del curso > valor base del tipo de pago.
- `cursos` ya no debe contener ni alimentar:
  - `matricula`;
  - `mensualidad`;
  - `meses`.

Migracion relacionada:

- `migrations/20260526_cursos_solo_academicos.sql`
- `migrations/20260713_tipos_pagos_estudiantes.sql`
- `migrations/20260716_pagos_adelantados.sql`
- `migrations/20260716_pagos_aplicaciones_parciales.sql`

## Aplicaciones mensuales de pagos

- `pagos` sigue siendo la fuente del ingreso, del metodo y de la anulacion.
- `pagos_aplicaciones` relaciona un pago con estudiante, concepto mensual,
  periodo vencido o futuro y monto aplicado.
- `periodo` siempre representa el primer dia del mes cubierto.
- El indice unico parcial sobre pago, concepto y periodo evita duplicar una
  aplicacion dentro del mismo movimiento, pero permite abonos auditables desde
  pagos distintos y la distribucion de metodos mixtos.
- Un indice parcial por estudiante, concepto y periodo acelera el calculo del
  saldo acumulado de cada cuota.
- `activo = FALSE` conserva auditoria al anular y permite registrar nuevamente
  ese mes.
- Los registros existentes de `pagos` no requieren conversion ni backfill; al
  listar cuotas se asignan por FIFO sin reescribir el historico.

## Indices por tenant

Script:

- `scripts/apply_tenant_indexes.py`

Indices configurados actualmente:

- `estudiantes(curso_id)`
- `pagos(estudiante_id)`
- `pagos(fecha)`
- `pagos(fecha_pago)`
- `asistencia(estudiante_id, fecha)`
- `asistencia(asignacion_id, periodo)`
- `notas_detalle(estudiante_id, asignacion_id, periodo)`
- `boletin_cabecera(estudiante_id, asignacion_id, periodo)`
- `asignaciones(curso_id)`
- `asignaciones(profesor_id)`
- `ventas(estudiante_id, estado)`
- `plan_de_clases(asignacion_id, fecha)`

El script:

- lee tenants operativos (`activo` y `en_mora`) de `public.colegios`;
- valida existencia de tabla;
- valida existencia de columnas;
- crea indices con nombre prefijado por schema;
- soporta `--dry-run`.

## Migraciones existentes

Archivos en `migrations/`:

- `20260429_pagos_tipo_pago_largo.sql`
- `20260429_plan_de_clases_reportes.sql`
- `20260509_branding_plantillas_impresion.sql`
- `20260517_tipos_pagos_avanzado.sql`
- `20260526_cursos_solo_academicos.sql`
- `20260527_pagos_anulacion.sql`
- `20260527_pagos_venta_id.sql`
- `20260527_ventas_anulacion.sql`
- `20260601_usuarios_password_obligatorio.sql`
- `20260602_asignaciones_activo.sql`
- `20260604_profesor_estado.sql`
- `20260604_cursos_estado.sql`
- `20260604_materias_estado.sql`
- `20260604_inventario_estado.sql`
- `20260604_egresos_origen.sql`
- `20260623_admin_nombres_mayuscula.sql`
- `20260623_admin_unicos_academicos.sql`
- `20260623_asignaciones_unicas_activas.sql`
- `20260623_asignaciones_horarios_historial_unico.sql`
- `20260623_institucion_branding_codigo_dane.sql`
- `20260624_asignaciones_orden_boletin.sql`
- `20260713_tipos_pagos_estudiantes.sql`
- `20260715_plan_de_clases_textos_largos.sql`
- `README.md`

Migraciones globales en `public`:

- `migrations/public/20260530_super_admins.sql`
- `migrations/public/20260601_tenant_suscripciones.sql`
- `migrations/public/20260601_tenant_eventos_auditoria.sql`
- `migrations/public/20260601_tenant_estado_auditoria.sql`

## Riesgos pendientes documentados

- La consistencia de schemas depende de scripts/migraciones aplicados a todos los tenants.
- No hay configuracion Alembic inicializada como flujo principal, aunque `alembic` esta en `requirements.txt`.
- Muchos controllers ejecutan SQL directamente.
- Hay muchos usos directos de `get_connection()`; cada cambio en esos modulos
  debe revisar cierre de cursor/conexion para no agotar el pool.

