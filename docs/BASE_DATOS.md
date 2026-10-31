# Base de Datos

Ultima revision documental: 2026-10-21.

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
  (desde el 2026-10-30, con `usa_entrevista_admision`: si el colegio usa la
  entrevista de admisión; ver `docs/MIGRACIONES.md`)

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
- `anios_lectivos`
- `cursos`
- `materias`
- `estudiantes`
- `matriculas`
- `asignaciones`
- `notas`
- `notas_detalle`
- `planilla_subnotas`
- `planilla_subnotas_valores`
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

Nota sobre SISBÉN y lugar de residencia en `estudiantes` (migración
`20261019_estudiantes_sisben_residencia.sql`, ver
`docs/funcionalidades/SISBEN_RESIDENCIA.md`):

- Ocho columnas opcionales: `sisben` (boolean; `NULL` es sin dato),
  `sisben_grupo`, `sisben_subgrupo`, `sisben_nivel`, `barrio`, `municipio`,
  `zona_residencia` y `punto_referencia`. `direccion` sigue igual.
- Reglas: `chk_estudiantes_sisben_grupo`, `chk_estudiantes_sisben_subgrupo`
  (exige el grupo y empieza por su letra), `chk_estudiantes_sisben_nivel` (1 a
  3), `chk_estudiantes_sisben_clasificacion` (sin SISBÉN no hay grupo,
  subgrupo ni nivel) y `chk_estudiantes_zona_residencia` (`urbana` o
  `rural`). El rango exacto de cada subgrupo lo valida la API.
- Se escriben con `estudiantes_repository.guardar_sisben_y_residencia`, aparte
  de los 34 datos globales, y solo si el cuerpo trae alguno de los ocho.

Nota sobre las subnotas de la planilla (migración
`20261021_planilla_subnotas.sql`, ver
`docs/funcionalidades/SUBNOTAS_PLANILLA.md`):

- `planilla_subnotas`: una fila por subnota de un tipo de nota ("Taller 1" de
  "Cognitivo"), la misma para todo el curso. `asignacion_id` (la académica ya
  resuelta, `ON DELETE CASCADE`), `periodo`, `tipo_nota` (el mismo texto de
  `notas_detalle.descripcion`, sin clave foránea porque los tipos no tienen
  tabla), `nombre` (60) y `creada_en`, que da el orden. Índice único
  `idx_planilla_subnotas_nombre_unico` por asignación, periodo, tipo y nombre,
  sin distinguir mayúsculas ni espacios en los extremos.
- `planilla_subnotas_valores`: una calificación por estudiante y subnota
  (`UNIQUE (subnota_id, estudiante_id)`). Es una `nota` de 1 a 5 o una
  `valoracion` (carita), nunca las dos ni ninguna
  (`chk_planilla_subnotas_valores_un_solo_valor`). Borra en cascada con su
  subnota, no con el estudiante, igual que `notas_detalle`.
- **Las subnotas no van en `notas_detalle`**, a propósito: el boletín, el
  reporte parcial, los tableros y la ficha promedian todas sus filas. La celda
  (el promedio) sí se sigue guardando allí, y solo la escribe el servidor.

Nota sobre los porcentajes por tipo de nota (migración
`20261022_planilla_tipos_porcentaje.sql`, escrita el 2026-10-22 y **todavía
sin aplicar**; ver la parte B de `docs/funcionalidades/SUBNOTAS_PLANILLA.md`):

- `planilla_tipos_porcentaje`: una fila por tipo de nota con porcentaje, por
  clase y periodo. `asignacion_id` (la académica ya resuelta, `ON DELETE
  CASCADE`), `periodo`, `tipo_nota` (el mismo texto de
  `notas_detalle.descripcion`), `porcentaje` entero de 1 a 100 y
  `actualizado_en`. Índice único `idx_planilla_tipos_porcentaje_tipo_unico`
  por asignación, periodo y tipo, sin distinguir mayúsculas ni espacios.
- Un tipo sin porcentaje no tiene fila. Los porcentajes cuentan solo cuando
  todos los tipos de la clase y el periodo tienen el suyo y suman 100; la
  suma no pasa de 100 porque lo controla la API, no un `CHECK`.

Nota sobre año lectivo y matrículas:

- `matriculas` guarda el curso del estudiante en cada año lectivo y es la
  fuente de verdad.
- `estudiantes.curso_id` conserva solo una copia del curso del año activo para
  que las pantallas existentes y los permisos de profesores sigan funcionando.
- Solo `sincronizar_curso_vigente` puede escribir esa copia. Crear o editar un
  estudiante primero hace el upsert de su matrícula activa y después la
  sincroniza, en la misma transacción.
- La consulta de control documentada en
  `docs/funcionalidades/ANIO_LECTIVO.md` debe devolver 0 filas.
- La migración `20261006_anios_lectivos_origenes.sql` añade las referencias
  opcionales `cursos.curso_origen_id` y
  `tipos_de_pagos.tipo_pago_origen_id`. Permitirán saber de qué registro del
  año anterior salió una copia; los registros creados desde cero tendrán
  `NULL`. El 2026-10-06 el usuario la probó y aplicó en una rama de Neon,
  regeneró desde allí el esquema base y después la aplicó y verificó en los
  dos tenants de producción.

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
- `plan_de_clases_cuadros` (migración `20261031_plan_de_clases_cuadros.sql`,
  escrita el 2026-10-31, probada en una rama de Neon y **todavía sin aplicar
  en producción**; ver
  `docs/funcionalidades/NOMBRES_CUADROS_PLAN.md`): los cuadros del plan que
  el colegio renombró, una fila por cuadro (`clave` es la llave primaria) con
  `nombre`, `ayuda`, `actualizado_en` y `actualizado_por`. Un cuadro sin fila
  usa su nombre original, que vive en el frontend. No se relaciona con
  `plan_de_clases`: renombrar no cambia ningún plan.

## Cursos y cobros

Estado actual:

- `cursos` queda como entidad academica.
- Los cobros academicos se definen desde `tipos_de_pagos`.
- La asignacion de cobros por curso se hace en `tipos_pagos_cursos`.
- Las excepciones por estudiante se guardan en `tipos_pagos_estudiantes`.
- La regla de valor vigente es: valor activo del estudiante > valor activo del curso > valor base del tipo de pago.
- Los conceptos recurrentes usan `mes_inicial`, `mes_final` y
  `frecuencia_meses`. `mes_final` es `SMALLINT NOT NULL DEFAULT 12`, debe estar
  entre `1` y `12` (`chk_mes_final`) y, cuando `tipo_cobro = 'mensual'` y existe
  `mes_inicial`, no puede ser menor. La restriccion
  `chk_rango_meses_recurrencia` equivale a
  `tipo_cobro <> 'mensual' OR mes_inicial IS NULL OR mes_final >= mes_inicial`.
- `20260910_tipos_pagos_mes_final.sql` agrega esa columna y rellena con `12`
  todos los conceptos existentes. Esto habilita la capacidad sin cambiar el
  calendario de ningun colegio; un limite distinto se guarda despues como dato
  de configuracion del concepto.
- Cartera, cuotas vencidas y periodos de adelanto dejan de generar opciones al
  superar `mes_final`. Los pagos y aplicaciones ya registrados se conservan.
- `cursos` ya no debe contener ni alimentar:
  - `matricula`;
  - `mensualidad`;
  - `meses`.
- `cursos.director_grupo_id` (nullable, `REFERENCES profesor(id) ON DELETE
  SET NULL`) guarda el profesor asignado como director de grupo del curso.
  Sin uso previo: se agrega para que el boletin muestre su nombre como dato
  informativo aparte de la firma a mano. Ver
  `docs/funcionalidades/DIRECTOR_GRUPO.md`.

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

