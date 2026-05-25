# Migraciones

Estado documentado: 2026-05-25.

## Carpeta de migraciones

Ruta:

- `migrations/`

Archivos actuales:

- `20260429_pagos_tipo_pago_largo.sql`
- `20260429_plan_de_clases_reportes.sql`
- `20260509_branding_plantillas_impresion.sql`
- `20260517_tipos_pagos_avanzado.sql`
- `README.md`

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
- busca tenants activos en `public.colegios`;
- por tenant, valida si la migracion ya fue aplicada;
- si el mismo nombre existe con checksum diferente, bloquea ese tenant;
- en `--dry-run` imprime `PENDIENTE` sin aplicar;
- al aplicar, ejecuta `SET search_path TO <schema>, public`;
- ejecuta SQL;
- registra migracion en `public.schema_migrations`.

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

Lee tenants activos de:

- `public.colegios`

## Estado de Alembic

- `alembic` existe en `requirements.txt`.
- No se observo carpeta/configuracion Alembic inicializada como flujo activo en la raiz.
- `migrations/README.md` menciona una futura adopcion formal de Alembic.

## Provisionamiento de tenant

Archivo:

- `crear_cliente.py`

Estado actual:

- crea tenants desde terminal;
- copia tablas desde `DEFAULT_TENANT_SCHEMA`;
- inserta admin inicial con password hasheada.

## Riesgos pendientes documentados

- Hay varios scripts historicos ademas del runner principal.
- El flujo actual depende de ejecutar correctamente scripts por tenant.
- Alembic aun no aparece como fuente formal de verdad.

## Historial operativo relacionado

El historial detallado de migraciones, indices y scripts seguros usados durante la auditoria esta consolidado en:

- `docs/CAMBIOS_BACKEND.md`

Puntos relevantes documentados alli:

- `apply_migration.py` con historial en `public.schema_migrations`;
- checksum SHA-256 por migracion;
- modo `--dry-run`;
- script `scripts/apply_tenant_indexes.py` con validacion de tablas/columnas;
- indices aplicados/verificados en tenants activos;
- paginacion compatible agregada en endpoints principales.


