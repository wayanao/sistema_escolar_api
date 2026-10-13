# Migraciones

Ultima revision documental: 2026-10-13.

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
- `20260921_listas_seguimiento.sql`
- `20260930_anios_lectivos.sql`
- `20261001_anios_lectivos_obligatorio.sql`
- `20261006_anios_lectivos_origenes.sql`
- `20261008_anios_lectivos_activacion.sql`
- `20261013_admisiones.sql`
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

## Migracion 20260921_listas_seguimiento.sql

Objetivo:

- Dar al administrador un registro libre por curso: columnas con el nombre que
  el elija y, por alumno, un check mas una nota corta opcional.

Tablas creadas (ninguna existente se modifica):

- `listas_seguimiento_columnas`: una fila por columna de un curso.
  `curso_id` con `ON DELETE CASCADE`, `nombre` `VARCHAR(100) NOT NULL`.
- `listas_seguimiento_marcas`: una fila por celda.
  `UNIQUE (columna_id, estudiante_id)` para habilitar el upsert,
  `marcado BOOLEAN NOT NULL DEFAULT FALSE`, `nota TEXT` limitada a 240
  caracteres por `chk_listas_seguimiento_marcas_nota_longitud`. Borra en
  cascada con su columna y con el estudiante.

Indices creados:

- `idx_listas_seguimiento_columnas_nombre_unico` (unico): nombre por curso
  ignorando mayusculas y espacios repetidos, mismo patron que
  `idx_cursos_nombre_jornada_unico`.
- `idx_listas_seguimiento_columnas_curso`.
- `idx_listas_seguimiento_marcas_columna`.
- `idx_listas_seguimiento_marcas_estudiante`.

`scripts/apply_tenant_indexes.py` no se toca: su lista fija `INDEXES` no
incluye estas tablas, asi que los indices van en la migracion sin riesgo de
duplicarse.

Detalle completo (motivacion, decisiones, invariantes, orden de despliegue):

- `docs/funcionalidades/LISTAS_SEGUIMIENTO.md`.

Estado:

- **Aplicada el 2026-09-22** con `apply_migration.py` a los dos tenants
  operativos, `tenant_colegio_1` (Colegio Demo) y `tenant_2005` (centro
  educativo la sabiduria de galapa). Registrada en
  `public.schema_migrations`.
- Esquema base regenerado el mismo dia desde `tenant_colegio_1` con
  `scripts/generar_esquema_base.py`: 33 tablas. Los colegios nuevos ya nacen
  con las dos tablas.
- `scripts/verify.py`: **1337 pruebas pasan, 0 fallan**, ruff y pip check
  limpios.
- Lo que PostgreSQL creo coincide con lo escrito en la migracion. El detalle
  que solo se pudo confirmar al aplicarla: el indice unico por expresion es
  valido -`upper(regexp_replace(...))` es IMMUTABLE, que es lo que un indice
  exige- y el UNIQUE de la celda quedo con el nombre que genera PostgreSQL,
  `listas_seguimiento_marcas_columna_id_estudiante_id_key`, igual que el de
  `tipos_pagos_estudiantes`.
- A partir de aqui el archivo **no se puede editar**: el runner guarda su
  checksum y rechazaria una version distinta con el mismo nombre. Cualquier
  cambio posterior va en una migracion nueva.

## Migracion 20260930_anios_lectivos.sql

Objetivo:

- Fundacion del año lectivo (fase 1, migracion A): crear la tabla de años,
  registrar 2026 como activo y marcar con 2026 todo lo existente. Invisible:
  ningun endpoint actual lee las columnas nuevas.

Tabla creada:

- `anios_lectivos`: `anio SMALLINT UNIQUE`, `estado` en `preparacion`,
  `activo`, `cerrado` o `reabierto`, con indices unicos parciales que impiden
  dos años activos o dos en preparacion. Se inserta 2026 como `activo`,
  escrito como literal y no calculado con la fecha del dia.

Columnas agregadas (`anio_lectivo_id`, clave foranea a `anios_lectivos`,
**admiten NULL** hasta la migracion B), rellenas con 2026:

- `cursos`, `tipos_de_pagos`, `matriculas`, `pagos`,
  `observador_anotaciones`.

Reglas de unicidad reemplazadas por su version con año:

- `idx_cursos_nombre_jornada_unico` → `idx_cursos_anio_nombre_jornada_unico`
  (misma expresion, con `anio_lectivo_id` delante).
- `tipos_de_pagos_nombre_key` → `tipos_de_pagos_anio_nombre_key`
  `UNIQUE (anio_lectivo_id, nombre)`.

Matriculas:

- Una fila por estudiante con curso, en el año de su curso.
- `idx_matriculas_estudiante_anio_unico`: un curso por estudiante y año.
- `cursos_id_anio_lectivo_key UNIQUE (id, anio_lectivo_id)` y la clave
  foranea compuesta `matriculas_curso_anio_lectivo_fkey`: el curso de una
  matricula es siempre del mismo año.

Indices creados:

- `idx_cursos_anio_lectivo`, `idx_tipos_de_pagos_anio_lectivo`,
  `idx_pagos_estudiante_anio_lectivo`,
  `idx_observador_anotaciones_estudiante_anio`. No estan en la lista fija de
  `scripts/apply_tenant_indexes.py`, asi que no se duplican.

Frenos (abortan el tenant sin tocar nada):

- Al inicio: si `matriculas` tiene filas antiguas sin año.
- Al final: si queda en `cursos` o `tipos_de_pagos` una regla de unicidad
  sin el año (por ejemplo, con otro nombre en un tenant viejo).

Detalle completo (motivacion, decisiones, orden de despliegue y la lista de
comprobacion para la rama de Neon):

- `docs/funcionalidades/ANIO_LECTIVO.md`, fase 1.

Estado:

- Escrita el 2026-09-30, con `tests/test_migracion_anios_lectivos.py` (17
  pruebas sobre el texto del SQL). `scripts/verify.py`: 1467 pasan, **1
  falla esperada** de `test_esquema_base.py` hasta aplicar la migracion real
  y regenerar el esquema base.
- **Probada con exito el 2026-09-30 en una rama de Neon** (`prueba-anio-lectivo`,
  copia de `production` con datos): OK en `tenant_colegio_1` y `tenant_2005`,
  ningun freno salto, y la comprobacion de `tenant_2005` dio lo esperado
  (2026 activo, 0 filas sin año en las cinco tablas, 174/174 matriculas,
  control del curso vigente en 0, solo las reglas unicas nuevas). Detalle en
  `docs/funcionalidades/ANIO_LECTIVO.md`, fase 1.
- **Aplicada en produccion el 2026-09-30** con `apply_migration.py` a
  `tenant_colegio_1` y `tenant_2005` (OK en los dos). Registrada en
  `public.schema_migrations`.
- Esquema base regenerado el mismo dia desde `tenant_colegio_1`: 34 tablas.
  El cambio coincide con la migracion y nada mas. Ojo: el esquema base es
  solo estructura y no trae la fila del año; un colegio nuevo nace sin año
  activo hasta que el alta lo inserte (codigo de la fase 1).
- `scripts/verify.py`: **1468 pasan, 0 fallan**; se apago la falla esperada
  de `test_esquema_base.py`.
- A partir de aqui el archivo **no se puede editar**: el runner guarda su
  checksum. Cualquier cambio va en una migracion nueva (la B).

## Migracion 20261001_anios_lectivos_obligatorio.sql

Objetivo:

- Año lectivo, fase 1, migracion B: cerrar la ventana que abrio la A. Rellena
  lo que quedo sin año, pone al dia las matriculas del año activo y vuelve
  obligatorio `anio_lectivo_id` en `cursos`, `tipos_de_pagos`, `matriculas`,
  `pagos` y `observador_anotaciones`. Invisible: ninguna respuesta de la API
  cambia.

Que hace, en orden:

- Freno: se detiene si hay matriculas sin año.
- Inserta 2026 como año activo si el tenant no tiene ninguno (un colegio dado
  de alta entre la A y el despliegue del codigo). Freno si aun asi no hay.
- Rellena con el año activo las filas sin año de `cursos`, `tipos_de_pagos`,
  `pagos` y `observador_anotaciones`, con la misma subconsulta que usa el
  codigo (`ANIO_ACTIVO_ID_SQL`).
- Pone al dia las matriculas del año activo con `estudiantes.curso_id`: crea
  las que faltan y corrige las que no coinciden. No borra ninguna.
- Freno: la consulta de control del curso vigente debe dar 0.
- `SET NOT NULL` en las cinco columnas. No crea tablas, indices ni reglas.

Orden de despliegue (obligatorio):

- **Despues** de desplegar el codigo que escribe el año (commit `df53299`,
  fase 1, punto 2), nunca antes: con `NOT NULL`, el codigo anterior fallaria
  al crear cursos, conceptos, pagos o anotaciones.
- Fuera de `app/`, `scripts/copiar_observaciones_al_observador.py` y
  `scripts/seed_tenant_performance.py` insertan sin año y fallaran despues de
  esta migracion. No se tocan; si se vuelven a usar, hay que darles el año.

Detalle completo y lista de comprobacion (rama de Neon, Render, produccion):

- `docs/funcionalidades/ANIO_LECTIVO.md`, fase 1, punto 3.

Estado:

- Escrita el 2026-10-01, con `tests/test_migracion_anios_lectivos_obligatorio.py`
  (12 pruebas: 11 sobre el texto del SQL y 1 que exige que todo `INSERT` de
  `app/` en esas cinco tablas escriba el año).
- **Probada con exito el 2026-10-01 en una rama de Neon**
  (`prueba-anio-lectivo-b`, copia de `production` con datos): OK en los dos
  tenants, ningun freno salto, y la app local contra la rama creo y edito
  sin errores.
- **Aplicada en produccion el 2026-10-01** a `tenant_colegio_1` y
  `tenant_2005` (OK en los dos), despues de confirmar en Render el
  despliegue del codigo (`67b2d4b`, Live). Comprobacion en `tenant_2005`:
  nada sin año, control del curso vigente en 0, las cinco columnas
  `NOT NULL`. En la ventana no habia quedado nada sin año: B solo puso las
  reglas.
- Esquema base regenerado el mismo dia desde `tenant_colegio_1`: 34 tablas.
  Solo cambian las cinco columnas a `NOT NULL` y la lista de incorporadas.
- `scripts/verify.py`: **1500 pasan, 0 fallan**.
- A partir de aqui el archivo **no se puede editar**: el runner guarda su
  checksum.

## Migracion 20261006_anios_lectivos_origenes.sql

Objetivo:

- Año lectivo, fase 5, paso 5.2: recordar de qué curso o concepto del año
  anterior salió cada copia, para preparar 2027 y reutilizar después el
  planeador y los planes de clase.

Columnas opcionales:

- `cursos.curso_origen_id`, clave foranea autorreferente a `cursos(id)`;
- `tipos_de_pagos.tipo_pago_origen_id`, clave foranea autorreferente a
  `tipos_de_pagos(id)`.

`NULL` significa que el registro se creó desde cero. La migración no rellena
las filas existentes: los cursos y conceptos de 2026 no son copias de un año
anterior. Crea además `idx_cursos_curso_origen` e
`idx_tipos_de_pagos_tipo_pago_origen`. No usa borrado en cascada ni modifica
datos existentes.

Estado al 2026-10-06:

- SQL incremental y 7 pruebas de texto listos. Se escribieron primero y las
  siete fallaron antes de crear el archivo.
- El usuario la probó en una rama de Neon con endpoint directo: el primer
  `--dry-run` mostró los dos tenants `PENDIENTE`, la aplicación terminó `OK` en
  ambos y el segundo `--dry-run` los mostró `OMITIDA (ya aplicada)`.
- Esquema base regenerado desde `tenant_colegio_1`: 34 tablas, 1 función y 1
  disparador. El diff agregó únicamente la migración a la cabecera, las dos
  columnas, las dos claves foráneas y los dos índices.
- Verificación local final: 41 pruebas específicas y 2032 globales pasan; Ruff,
  `pip check` y `git diff --check` limpios.
- La migración y la base regenerada quedaron juntas en el commit `a6f3cc0`,
  confirmado `Live` en Render antes de la aplicación productiva.
- **Aplicada en producción el 2026-10-06** a `tenant_colegio_1` y
  `tenant_2005`: simulación `PENDIENTE`, aplicación `OK` y simulación posterior
  `OMITIDA (ya aplicada)` en ambos. No rellenó ni borró datos existentes.
- A partir de aquí el archivo no se puede editar: el runner guarda su checksum.
  Cualquier cambio posterior debe ir en una migración nueva.

## Migracion 20261008_anios_lectivos_activacion.sql

Objetivo:

- Año lectivo, fase 6, paso 6.1: guardar la decisión de quien no sigue el año
  siguiente (decisión 9) y las materias ocultas de un año al cerrarlo
  (decisión 13).

Cambios:

- `matriculas.estado_salida`, opcional, limitado a `retirado` o `egresado`
  por `chk_matriculas_estado_salida`. `NULL` significa sin decidir; una
  matrícula en el año siguiente significa que el estudiante continúa.
- Tabla `anios_lectivos_materias_ocultas (anio_lectivo_id, materia_id)`, con
  llave primaria compuesta, claves foráneas a `anios_lectivos` y `materias`
  sin borrado en cascada e índice `idx_anios_lectivos_materias_ocultas_materia`.

No rellena, actualiza ni borra datos existentes. Es reejecutable.

Estado al 2026-10-08:

- SQL y 9 pruebas de texto; las 9 fallaron antes de crear el archivo.
- El usuario la probó en una rama de Neon con endpoint directo: simulación
  `PENDIENTE` en los dos tenants y aplicación en la rama.
- Esquema base regenerado desde `tenant_colegio_1` en esa rama: 35 tablas, 1
  función y 1 disparador. El diff agregó solo la migración a la cabecera, la
  columna con su restricción, la tabla, su índice y sus dos claves foráneas.
- Verificación local: 50 pruebas específicas y 2105 globales pasan; Ruff,
  `pip check` y `git diff --check` limpios. Commit `6c6aabb`.
- **Aplicada en producción el 2026-10-08** a `tenant_colegio_1` y
  `tenant_2005`: aplicación `OK` y simulación posterior `OMITIDA (ya
  aplicada)` en ambos. Se aplicó antes del push de `6c6aabb`; no importa en
  este paso porque ningún código usaba todavía la columna ni la tabla.
- A partir de aquí el archivo no se puede editar: el runner guarda su checksum.

## Migracion 20261013_admisiones.sql

Objetivo:

- Entrevista de admisión, paso E1: crear la tabla `admisiones`, una fila por
  aspirante nuevo y año, con sus datos, su entrevista y el resultado
  (`pendiente`, `aprobado` o `no_aprobado`). Invisible: ningún código la usa
  todavía.

Reglas que exige la base:

- `chk_admisiones_autoriza`: la autorización de datos (Ley 1581 de 2012) es
  obligatoria; `autoriza_datos` y `autoriza_nombre` son `NOT NULL`.
- `chk_admisiones_resultado`: solo los tres resultados.
- `chk_admisiones_motivo_no_aprobado`: "no aprobado" exige un motivo que no
  esté en blanco.
- `chk_admisiones_matricula_aprobada` y `admisiones_estudiante_id_key`: solo
  un aprobado queda enlazado a un estudiante, y a uno solo.
- `admisiones_curso_anio_lectivo_fkey`: el curso es del mismo año que la
  admisión (contra `cursos_id_anio_lectivo_key`, igual que `matriculas`).
- Claves foráneas a `anios_lectivos`, `cursos` y `estudiantes` sin borrado en
  cascada.

Indices creados:

- `idx_admisiones_anio (anio_lectivo_id, resultado)`.
- `idx_admisiones_documento_por_anio` (único, parcial): un documento una
  sola vez por año, sin contar los que llegan sin documento.

No toca ninguna tabla ni dato existente. No quita columnas de `estudiantes`.
Es reejecutable.

Detalle completo (decisiones, reparto de campos, lista de comprobación para
la rama de Neon con una consulta que prueba las reglas):

- `docs/funcionalidades/ENTREVISTA_ADMISION.md`.

Estado al 2026-10-13:

- SQL y 15 pruebas de texto (`tests/test_migracion_admisiones.py`); las 15
  fallaron antes de crear el archivo.
- El usuario la probó en la rama de Neon `prueba-entrevista` (copia de
  `production`): simulación `PENDIENTE` y aplicación en la rama. Una
  consulta en el SQL Editor intentó 15 altas en `tenant_colegio_1`, cada una
  deshecha al instante: las 15 dieron lo esperado (cada regla rechazó lo que
  debía y se aceptaron los casos válidos).
- Esquema base regenerado desde `tenant_colegio_1` en esa rama: 36 tablas, 1
  función y 1 disparador. El diff agregó solo la migración a la cabecera, la
  tabla con sus reglas, sus dos índices y sus tres claves foráneas.
- `scripts/verify.py`: **2294 pasan, 0 fallan**; Ruff y `pip check` limpios.
- **No aplicada en producción** todavía. Orden: commit de migración y base
  juntas, push y Render **Live**, y después aplicar (ver "Entrega para el
  siguiente chat" en `docs/funcionalidades/ENTREVISTA_ADMISION.md`).
