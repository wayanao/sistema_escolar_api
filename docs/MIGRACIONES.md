# Migraciones

Ultima revision documental: 2026-07-22.

## Carpeta de migraciones

Ruta:

- `migrations/`

Archivos actuales:

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
- `20260624_asignaciones_orden_boletin.sql`
- `20260623_institucion_branding_codigo_dane.sql`
- `20260713_tipos_pagos_estudiantes.sql`
- `20260715_plan_de_clases_textos_largos.sql`
- `20260715_plan_de_clases_estandar_dba_text.sql`
- `20260715_reparar_asignacion_academica_invalida.sql`
- `20260716_pagos_adelantados.sql`
- `20260716_pagos_aplicaciones_parciales.sql`
- `20260722_plan_de_clases_integridad.sql`
- `20260722_plan_de_clases_notificaciones.sql`
- `20260722_plan_de_clases_revision.sql`
- `README.md`

Migraciones globales `public`:

- `public/20260530_super_admins.sql`
- `public/20260601_tenant_suscripciones.sql`
- `public/20260601_tenant_estado_auditoria.sql`
- `public/20260601_tenant_eventos_auditoria.sql`

## Runner actual

Archivo:

- `apply_migration.py`

Uso documentado en el propio archivo:

```powershell
python apply_migration.py migrations/<archivo>.sql --dry-run
python apply_migration.py migrations/<archivo>.sql
```

Comportamiento actual:

- lee el archivo SQL;
- calcula checksum SHA-256;
- carga `.env`;
- usa `DATABASE_URL`;
- crea/verifica `public.schema_migrations`;
- busca tenants operativos (`activo` y `en_mora`) en `public.colegios`;
- por tenant, valida si la migracion ya fue aplicada;
- si el archivo esta en `migrations/public/`, usa `public` como unico target;
- si el mismo nombre existe con checksum diferente, bloquea ese tenant;
- en `--dry-run` imprime `PENDIENTE` sin aplicar;
- al aplicar, ejecuta `SET search_path TO <schema>, public`;
- ejecuta SQL;
- registra migracion en `public.schema_migrations`.

## Integridad previa del plan de clases

Antes de aplicar `20260722_plan_de_clases_integridad.sql` se debe ejecutar:

```powershell
.\venv\Scripts\python.exe scripts\auditar_plan_de_clases_integridad.py
```

La auditoria es de solo lectura y revisa todos los tenants registrados, ademas
del schema definido por `DEFAULT_TENANT_SCHEMA`. Reporta:

- planes sin `asignacion_id` o sin `fecha`;
- grupos duplicados por `asignacion_id + fecha`.

La migracion no elimina ni fusiona informacion. Si encuentra alguno de esos
casos, falla y revierte la transaccion del tenant para exigir revision manual.
Cuando la auditoria queda limpia, la migracion establece ambas columnas como
obligatorias y crea el indice unico
`uq_plan_de_clases_asignacion_fecha`.

Orden obligatorio de despliegue:

1. Ejecutar la auditoria de solo lectura.
2. Resolver manualmente cualquier inconsistencia respaldando la informacion.
3. Aplicar la migracion con `apply_migration.py`.
4. Desplegar el repositorio que usa `ON CONFLICT (asignacion_id, fecha)`.

Estado productivo al 2026-07-22:

- auditoria previa correcta en los 4 schemas operativos;
- migracion aplicada y registrada en los 4 schemas;
- auditoria posterior correcta y segunda simulacion marcada como `OMITIDA
  (ya aplicada)` para todos los destinos.

La migracion `20260722_plan_de_clases_revision.sql` depende de la integridad
anterior. Agrega estados y versiones al plan, y crea la tabla historica
`plan_de_clases_observaciones`. No elimina ni reemplaza contenido existente;
los planes previos se inicializan como `pendiente`, version `1`, usando su
ultima fecha disponible como fecha de envio.

Estado productivo al 2026-07-22:

- aplicada y registrada en los 4 schemas operativos;
- verificada con `scripts/auditar_plan_de_clases_revision.py` mediante una
  conexion de solo lectura;
- columnas, tabla historica y planes inicializados sin inconsistencias.

La migracion `20260722_plan_de_clases_notificaciones.sql` depende del flujo de
revision anterior y crea `plan_de_clases_notificaciones_admin`, con unicidad
por plan y version e indice parcial para pendientes. No inserta eventos para
planes historicos; el primer evento se crea con el siguiente guardado del
profesor.

Estado productivo al 2026-07-22:

- aplicada y registrada en los 4 schemas operativos;
- auditoria estructural correcta en los 4 schemas;
- segunda simulacion marcada como `OMITIDA (ya aplicada)` para todos los
  destinos.

## Historial de migraciones

Tabla:

- `public.schema_migrations`

Columnas creadas por el runner:

- `id`
- `migration_name`
- `target_schema`
- `checksum`
- `applied_at`

Restriccion:

- `UNIQUE (migration_name, target_schema)`

Nota:

- Las migraciones dentro de `migrations/public/` son globales; desde
  2026-06-01 el runner las detecta y las aplica contra `public` como target
  unico.

## Scripts de migracion/operacion existentes

Carpeta:

- `scripts/`

Archivos actuales:

- `add_boletin_desarrollo_columns.py`
- `add_notas_desarrollo_columns.py`
- `apply_pagos_tipo_pago_migration.py`
- `apply_plan_de_clases_migration.py`
- `apply_tenant_indexes.py`
- `apply_tipos_pagos_avanzado_migration.py`
- `check_tenant_schemas.py`

## Indices por tenant

Script:

- `scripts/apply_tenant_indexes.py`

Soporta:

- `--dry-run`

Lee tenants operativos (`activo` y `en_mora`) de:

- `public.colegios`

## Estado de Alembic

- `alembic` existe en `requirements.txt`.
- No se observo carpeta/configuracion Alembic inicializada como flujo activo en la raiz.
- `migrations/README.md` menciona una futura adopcion formal de Alembic.

## Provisionamiento de tenant

Flujo oficial:

- `/super-admin` -> `Crear colegio`
- `POST /super-admin/tenants`

Estado actual:

- crea tenants desde el panel super admin;
- copia tablas desde `DEFAULT_TENANT_SCHEMA`;
- inserta admin inicial con password hasheada y cambio obligatorio;
- registra suscripcion y auditoria de creacion.

## Riesgos pendientes documentados

- Hay varios scripts historicos ademas del runner principal.
- El flujo actual depende de ejecutar correctamente scripts por tenant.
- Alembic aun no aparece como fuente formal de verdad.
- `scripts/legacy/crear_cliente.py` y `scripts/legacy/setup_saas.py` son
  referencia antigua, no flujo de deploy actual.
- Antes de crear colegios reales, `DEFAULT_TENANT_SCHEMA` debe tener aplicadas
  las migraciones tenant actuales.

## Historial operativo relacionado

El historial detallado de migraciones, indices y scripts seguros usados durante la auditoria esta consolidado en:

- `docs/CAMBIOS_BACKEND.md`

Puntos relevantes documentados alli:

- `apply_migration.py` con historial en `public.schema_migrations`;
- checksum SHA-256 por migracion;
- modo `--dry-run`;
- script `scripts/apply_tenant_indexes.py` con validacion de tablas/columnas;
- indices aplicados/verificados en tenants operativos;
- paginacion compatible agregada en endpoints principales.

## Migracion 20260526_cursos_solo_academicos.sql

Objetivo:

- Dejar `cursos` como entidad academica.
- Quitar las columnas financieras legacy:
  - `matricula`;
  - `mensualidad`;
  - `meses`.
- Mantener `tipos_de_pagos` y `tipos_pagos_cursos` como fuente de cobros por curso.

Estado:

- Aplicada en los tenants operativos existentes durante la auditoria.
- Registrada en `public.schema_migrations`.

## Migraciones publicas SaaS

Las migraciones dentro de `migrations/public/` se aplican contra el schema
`public`.

Archivos actuales:

- `20260530_super_admins.sql`
- `20260601_tenant_estado_auditoria.sql`
- `20260601_tenant_suscripciones.sql`
- `20260601_tenant_eventos_auditoria.sql`

Desde 2026-06-01, `apply_migration.py` detecta estos archivos y los aplica como
target `public`, incluso si no existen colegios registrados.

## Migracion 20260713_tipos_pagos_estudiantes.sql

Objetivo:

- Agregar excepciones de valor por estudiante para conceptos de cartera.
- Mantener `tipos_de_pagos` como valor base y `tipos_pagos_cursos` como valor por curso.
- Permitir que la regla central de cobros use prioridad: estudiante > curso > base.

Tabla creada:

- `tipos_pagos_estudiantes`

Campos principales:

- `tipo_pago_id`
- `estudiante_id`
- `valor`
- `motivo`
- `activo`
- `created_at`
- `updated_at`

Estado esperado:

- Aplicar sobre el schema plantilla (`DEFAULT_TENANT_SCHEMA`) antes de crear nuevos colegios.
- Aplicar sobre tenants existentes para habilitar los endpoints de valores personalizados.
- Si no esta aplicada, el backend responde `409` en los endpoints de valores personalizados.

## Migracion 20260601_usuarios_password_obligatorio.sql

Objetivo:

- Agregar `usuarios.debe_cambiar_password`.
- Forzar cambio de password en primer ingreso del admin inicial creado desde
  super admin.

SQL:

- `ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS debe_cambiar_password BOOLEAN NOT NULL DEFAULT FALSE;`

Estado esperado:

- Aplicar sobre el schema plantilla (`DEFAULT_TENANT_SCHEMA`) antes de crear
  nuevos colegios.
- Aplicar sobre tenants existentes cuando ya haya colegios en produccion.

## Migracion 20260527_pagos_anulacion.sql

Objetivo:

- Permitir anular pagos sin eliminarlos fisicamente.
- Mantener huella financiera de pagos anulados.
- Hacer que cartera, estado de cuenta y reportes sumen solo pagos validos.

Columnas agregadas a `pagos`:

- `estado`
- `motivo_anulacion`
- `fecha_anulacion`
- `anulado_por`

Estado:

- Aplicada en los tenants operativos existentes durante la auditoria.
- Registrada en `public.schema_migrations`.

## Migracion 20260527_pagos_venta_id.sql

Objetivo:

- Vincular pagos con ventas de inventario.
- Permitir que al anular un pago de inventario se reverse el abono de la venta.

Columnas agregadas a `pagos`:

- `venta_id`

Estado:

- Aplicada en los tenants operativos existentes durante la auditoria.
- Registrada en `public.schema_migrations`.

## Migracion 20260527_ventas_anulacion.sql

Objetivo:

- Permitir anular ventas de inventario sin eliminarlas.
- Mantener huella de anulacion.
- Devolver stock y anular pagos asociados desde backend.

Columnas agregadas a `ventas`:

- `motivo_anulacion`
- `fecha_anulacion`
- `anulado_por`

Estado:

- Aplicada en los tenants operativos existentes durante la auditoria.
- Registrada en `public.schema_migrations`.

## Migracion 20260604_egresos_origen.sql

Objetivo:

- Diferenciar egresos manuales de egresos automaticos.
- Permitir editar solo egresos creados desde el modulo administrativo de
  Egresos.
- Bloquear la edicion de egresos generados por nomina u otros flujos
  automaticos.

Columnas agregadas a `egresos`:

- `origen`

Valores:

- `manual`: egreso creado desde `/api/egresos/`.
- `nomina`: egreso automatico creado por el pago de nomina.

Estado:

- Aplicada en `tenant_colegio_1`, `tenant_3333` y `tenant_4444`.
- Registrada en `public.schema_migrations`.




