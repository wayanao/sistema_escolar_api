# Migraciones

Ultima revision documental: 2026-09-15.

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
- `20260825_observaciones_claves_foraneas.sql`
- `20260901_cursos_nivel_academico.sql`
- `20260908_observador_anotaciones.sql`
- `20260908_observador_anotaciones_historicas.sql`
- `20260908_observador_anotaciones_materia.sql`
- `20260910_tipos_pagos_mes_final.sql`
- `20260915_cursos_director_grupo.sql`
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

## Migracion de mes final de mensualidades

`20260910_tipos_pagos_mes_final.sql` es una migracion tenant incremental. Agrega
`tipos_de_pagos.mes_final`, rellena los registros existentes con `12`, fija
`DEFAULT 12` y `NOT NULL`, valida el rango `1..12` y exige que el final no sea
anterior a `mes_inicial` cuando la fila es de tipo `mensual`. Los tipos `unico`,
`anual` y `opcional` no quedan sujetos a esa relacion.

Hay dos efectos distintos que no deben confundirse:

- **Capacidad:** los tenants operativos existentes (`activo` y `en_mora`)
  recibiran la columna con diciembre cuando se ejecute el runner, y los tenants
  nuevos la reciben desde
  `migrations/base/20260813_esquema_base_tenant.sql`.
- **Dato institucional:** un colegio solo deja de cobrar antes de diciembre
  cuando un administrador cambia `mes_final` en su concepto mensual. Para
  `tenant_2005`, la operacion prevista es establecer noviembre (`11`) como mes
  final y conservar el mes inicial y la frecuencia que realmente correspondan;
  no viene incluida en la migracion.

### Orden de despliegue seguro

1. Probar la migracion y la aplicacion en una rama/copia no productiva.
2. Con `DATABASE_URL` apuntando al endpoint directo, ejecutar y revisar:

   ```powershell
   python apply_migration.py migrations/20260910_tipos_pagos_mes_final.sql --dry-run
   ```

   El runner debe listar cada schema operativo pendiente sin modificarlo.
3. Aplicar el mismo archivo, una sola vez:

   ```powershell
   python apply_migration.py migrations/20260910_tipos_pagos_mes_final.sql
   ```

4. Repetir el `--dry-run`; todos los destinos aplicados deben aparecer como
   omitidos por historial. Verificar tambien columna, default y constraints.
5. Desplegar backend y luego frontend. La columna es aditiva, por lo que el
   backend anterior puede convivir durante el paso 3.
6. Hacer pruebas de humo con un concepto que conserve diciembre y, solo despues,
   guardar noviembre como mes final de la mensualidad de `tenant_2005` desde
   Tipos de Pago, sin alterar por suposicion el inicio o la frecuencia vigentes.
   Revisar cartera, cuotas vencidas y adelantos sin registrar cobros de prueba
   sobre estudiantes reales.

Fallback: el backend actualizado lee `12` cuando la columna aun no existe. Sus
calculadores internos tambien se protegen con `12` ante un valor ausente o fuera
de rango, mientras que la API rechaza ese valor invalido. Cualquier intento de
guardar `mes_final` sin la migracion responde `409`; por eso el frontend no debe
publicarse antes del paso 3. Si se revierte la aplicacion, la columna aditiva
puede conservarse con valor `12`; no se recomienda borrarla ni eliminar
historial como rollback.

Estado al documentar: migracion, esquema base y codigo validados localmente; 128
pruebas enfocadas y la suite completa de 1293 pruebas pasaron (6 warnings
preexistentes). **No se ejecuto** `apply_migration.py`, no se conecto a Neon ni
se modifico `tenant_2005` o cualquier otro tenant.

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
- **construye el schema aplicando `migrations/base/20260813_esquema_base_tenant.sql`**,
  ya no copiando tablas desde `DEFAULT_TENANT_SCHEMA`;
- inserta admin inicial con password hasheada y cambio obligatorio;
- copia las plantillas de impresion predefinidas desde `DEFAULT_TENANT_SCHEMA`;
- siembra en `public.schema_migrations` lo que la plantilla tiene registrado;
- registra suscripcion y auditoria de creacion.

Hasta agosto de 2026 el schema se copiaba con `CREATE TABLE (LIKE … INCLUDING
ALL)`. Esa copia **no reproduce las claves foraneas** y hace que las columnas
`serial` sigan usando las secuencias del schema origen. Los tenants creados asi
nacian sin integridad referencial y compartiendo los contadores de id de la
plantilla. Ver `docs/modularizacion/03_MIGRACIONES_TENANTS.md`.

## Anadir una migracion nueva

El esquema de un tenant esta descrito en dos sitios: las migraciones
incrementales de `migrations/`, que se aplican a los tenants existentes, y el
archivo base de `migrations/base/`, que se aplica a los nuevos. **Hay que
actualizar los dos.**

1. **Escribe la migracion** en `migrations/AAAAMMDD_nombre.sql`, con nombres sin
   cualificar: el runner fija el `search_path` a cada tenant.

2. **Pruebala en una rama de Neon**, no en produccion. Apunta `DATABASE_URL` al
   endpoint de la rama y ejecuta el runner ahi. Si algo sale mal, se borra la
   rama y no ha pasado nada.

3. **Aplicala a los tenants existentes**:

   ```powershell
   .\venv\Scripts\python.exe apply_migration.py migrations/AAAAMMDD_nombre.sql --dry-run
   .\venv\Scripts\python.exe apply_migration.py migrations/AAAAMMDD_nombre.sql
   ```

   `DATABASE_URL` debe apuntar al **endpoint directo**, sin `-pooler`: el runner
   se niega sobre el agrupado porque alli su lock de sesion no impide dos
   ejecuciones simultaneas.

4. **Regenera el archivo base**, despues del paso 3 y nunca antes:

   ```powershell
   .\venv\Scripts\python.exe scripts\generar_esquema_base.py --schema tenant_colegio_1
   ```

   El script lee la estructura real de ese schema, asi que si todavia no tiene
   la migracion capturara el esquema anterior sin avisar.

5. **Ejecuta la compuerta**. `tests/test_esquema_base.py` compara las
   migraciones que el archivo base declara incorporar con las que hay en
   `migrations/`, y falla si anadiste una y no regeneraste.

6. **Commitea la migracion y la base juntas**, para que el repositorio nunca
   quede diciendo dos cosas distintas.

Entre los pasos 3 y 4 hay una ventana en la que la plantilla ya tiene la
migracion y el archivo base todavia no. Un alta de colegio en ese rato nacera
con la estructura vieja y el historial nuevo. Son minutos y las altas son raras,
pero conviene hacer los dos pasos seguidos.

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

## Migracion 20260915_cursos_director_grupo.sql

Objetivo:

- Permitir asignar un profesor como director de grupo de un curso.
- Que el boletin muestre su nombre como dato informativo, sin reemplazar la
  linea de firma a mano existente.

Columna agregada a `cursos`:

- `director_grupo_id` (INTEGER, `REFERENCES profesor(id) ON DELETE SET NULL`,
  nullable).

Indice creado:

- `idx_cursos_director_grupo`.

Detalle completo (motivacion, decisiones, invariantes, orden de despliegue):

- `docs/funcionalidades/DIRECTOR_GRUPO.md`.

Estado:

- Codigo y pruebas locales completos (`scripts/verify.py`: 1307 pasan, 1
  falla esperada de `test_esquema_base.py` hasta aplicar la migracion real).
- **No aplicada** a Neon ni a ningun tenant. Pendiente de que el usuario la
  aplique con `apply_migration.py` y regenere el esquema base.

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
