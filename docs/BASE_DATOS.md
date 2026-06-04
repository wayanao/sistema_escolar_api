# Base de Datos

Estado documentado: 2026-05-25.

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
- `tipos_de_pagos`
- `tipos_pagos_cursos`
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

## Cursos y cobros

Estado actual:

- `cursos` queda como entidad academica.
- Los cobros academicos se definen desde `tipos_de_pagos`.
- La asignacion de cobros por curso se hace en `tipos_pagos_cursos`.
- `cursos` ya no debe contener ni alimentar:
  - `matricula`;
  - `mensualidad`;
  - `meses`.

Migracion relacionada:

- `migrations/20260526_cursos_solo_academicos.sql`

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
- `README.md`

Migraciones globales en `public`:

- `migrations/public/20260530_super_admins.sql`
- `migrations/public/20260601_tenant_suscripciones.sql`
- `migrations/public/20260601_tenant_eventos_auditoria.sql`
- `migrations/20260601_usuarios_password_obligatorio.sql`
- `migrations/public/20260601_tenant_estado_auditoria.sql`

## Riesgos pendientes documentados

- La consistencia de schemas depende de scripts/migraciones aplicados a todos los tenants.
- No hay configuracion Alembic inicializada como flujo principal, aunque `alembic` esta en `requirements.txt`.
- Muchos controllers ejecutan SQL directamente.
