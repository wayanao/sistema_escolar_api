# Capa 3: migraciones y tenants

Última revisión: 2026-08-14.

## Control

- Estado: **Cerrada** el 2026-08-13. Los dos puntos que quedaron abiertos al
  cierre se resolvieron después: los schemas demo se eliminaron y la migración
  base quedó enlazada con `migrations/` mediante una guarda ejecutable.
- Commit base: `81882f3b1ee9e3b50076b0fc1fd93dcd9fd5ac70`.
- Rama acordada: `main`.
- Estado al activar: árbol limpio; `HEAD` coincidente con la referencia local
  `origin/main`.
- Primera subcapa pendiente: **ninguna**.
- Progreso: **3.0 a 3.6 cerradas**. El inventario está registrado abajo y
  reemplaza el desglose provisional de la activación.
- **Reparación de 3.4b aplicada a producción** el 2026-08-13, con autorización
  explícita del usuario y tras revisar juntos el `--dry-run`. Las ocho tablas
  bloqueadas de `tenant_2005` vuelven a admitir inserciones.
- **Siembra de 3.4e aplicada a producción** el 2026-08-13. El informe de 3.3a
  da `tenant_2005` como `OK`; `tenant_4444`, que era demo, se eliminó después
  por decisión del usuario y la auditoría final termina en exit 0.
- Código de producto modificado al activar: **ninguno**.
- Código de producto modificado hasta ahora: `apply_migration.py`, que toma un
  advisory lock de sesión antes de leer o escribir el historial, y
  `app/controllers/super_admin_controller.py`, donde el alta siembra el
  historial del tenant nuevo desde el schema plantilla. Se añadió además
  `scripts/auditar_migraciones_tenants.py`, de solo lectura. 3.0 y 3.2 fueron
  subcapas sin cambios de producto.
- Autorización: orden explícita del usuario el 2026-08-13, limitada a la
  activación documental de esta capa y con la instrucción de detenerse antes de
  3.0.

## Objetivo

Dejar todos los tenants reactivables versionados y verificables, un runner de
migraciones protegido contra ejecuciones simultáneas y un alta de tenant
reproducible a partir de migraciones versionadas en lugar de la copia de un
tenant plantilla, con un ensayo previo en un entorno no productivo y un
rollback preparado.

El objetivo procede exclusivamente del alcance registrado para la capa 3 en
`docs/modularizacion/README.md`. La activación no inspeccionó código, esquemas,
migraciones ni scripts, por lo que esta bitácora no afirma todavía qué
mecanismos existen hoy ni cómo están implementados. Esa descripción es trabajo
de 3.0.

## Dependencias de capas anteriores

- Compuerta única `scripts/verify.py`, heredada de la capa 0, con CI declarada
  en `.github/workflows/backend-quality.yml`.
- Capa 1 cerrada: propiedad definida de conexión, cursor, `commit`, `rollback` y
  devolución al pool; timeouts aplicados por transacción con
  `set_config(..., TRUE)` porque el endpoint agrupado rechaza parámetros de
  arranque que no sabe rastrear.
- Capa 2 cerrada: la DB síncrona del camino HTTP está fuera del event loop y el
  limitador compartido de AnyIO deriva `T=floor((DB_POOL_MAX_CONNECTIONS-R)/H)`
  con `H=2` y `R=0`, hoy cinco workers para un pool de diez conexiones.
- Compuerta local vigente registrada al cerrar la capa 2: **477 pruebas**, Ruff
  correcto y `pip check` correcto.
- La calibración operativa de `DB_STATEMENT_TIMEOUT_MS` sigue **pendiente y
  aceptada** desde la capa 1. No se considera cumplida, no se incorpora por
  inferencia al alcance de esta capa y su riesgo se conserva.

## Alcance autorizado

- Inventariar cómo se descubren los tenants, cómo se registra la versión de cada
  schema, qué ejecuta hoy las migraciones y cómo se da de alta un tenant nuevo.
- Definir con evidencia qué significa «tenant reactivable» y qué tenants entran
  en el alcance de la capa.
- Verificar y aplicar las migraciones pendientes a los tenants que el inventario
  demuestre incluidos, primero fuera de producción.
- Agregar un bloqueo que impida ejecuciones simultáneas del runner de
  migraciones.
- Sustituir de forma progresiva el alta por copia de un tenant plantilla por un
  alta basada en migraciones versionadas.
- Agregar o conservar pruebas de caracterización antes de cualquier extracción o
  sustitución.
- Ensayar en una base de prueba o staging y preparar un rollback aplicable a
  esquema y datos, no solo a la aplicación.

## Fuera de alcance

- Cambiar PostgreSQL, `psycopg2`, el modelo de schemas por tenant o introducir
  un ORM o un driver asíncrono.
- Modificar rutas, payloads, status codes, permisos, roles, ownership o reglas
  de negocio.
- Cambiar SQL observable de los dominios, orden transaccional, `commit`,
  `rollback`, timeouts o tamaño del pool sin una autorización explícita ante un
  bloqueo demostrado.
- Rediseñar la concurrencia cerrada en la capa 2 o alterar el limitador
  compartido sin reauditar `H` y `R`.
- Modularizar dominios, eliminar N+1, optimizar consultas o crear índices por
  rendimiento; corresponde a las capas 4 en adelante.
- Ejecutar migraciones reales contra producción, desplegar o cambiar
  configuración real.
- Crear una abstracción compartida sin dos usos reales demostrados.

## Invariantes

- Métodos, paths, status codes y formas de respuesta permanecen idénticos.
- Permisos, roles, ownership y aislamiento entre tenants se conservan sin
  excepción; una migración no puede filtrar datos entre schemas.
- Un tenant existente no pierde datos, columnas ni restricciones por efecto de
  esta capa.
- La propiedad de cursor, conexión, `commit`, `rollback` y devolución al pool
  definida en la capa 1 no cambia.
- Ninguna operación de esta capa reintroduce trabajo DB síncrono en el event
  loop ni consume el limitador compartido sin recalcular la capacidad.
- Un alta de tenant nueva produce un schema equivalente al que produce hoy el
  camino vigente, salvo diferencias que la bitácora autorice de forma explícita.
- Toda ejecución de migración es idempotente frente a una repetición y no queda
  a medias sin dejar constancia de su versión.

## Línea base

La activación no ejecuta verificaciones: la subcapa 3.0 debe reproducirlas desde
el commit base antes de inventariar, medir o cambiar nada.

| Comprobación | Comando | Resultado |
|---|---|---|
| Pruebas específicas | `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_apply_migration.py tests/test_super_admin.py tests/test_auth_tenant.py` | **33 pasaron** en 0,56 s |
| Específicas ampliadas | Las anteriores más `tests/test_apply_tenant_indexes.py` y `tests/test_tenant_context_concurrency.py` | **40 pasaron**, 5 warnings conocidos |
| Compuerta global | `.\venv\Scripts\python.exe scripts\verify.py` | **Exit 0**: 477 pruebas, 5 warnings conocidos |
| Ruff | Ejecutado por la compuerta | `All checks passed!` |
| Dependencias | Ejecutado por la compuerta | `No broken requirements found.` |
| Estado de versionado por tenant | No verificable sin base de datos | **No medido**; requiere el ensayo no productivo de 3.4 |

La compuerta se reprodujo sobre el árbol del commit base y coincide con la cifra
heredada del cierre de la capa 2. A diferencia de todas las subcapas de la capa
2, esta ejecución terminó en exit 0 **dentro del sandbox**: el `WinError 5` al
enumerar el temporal de pytest no se reprodujo. Se registra como observación
ambiental, no como corrección de nada; puede volver a aparecer.

El estado real de versionado por tenant **no se midió**. Requiere consultar
`public.schema_migrations` contra una base, y 3.0 es una subcapa de solo lectura
del repositorio sin acceso a datos.

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 3.0 | Inventario, contratos, criterio de tenant reactivable, estrategia de verificación y línea base | **Cerrada** |
| 3.1 | Bloqueo del runner contra ejecuciones simultáneas | **Cerrada** |
| 3.2 | Caracterización ejecutable del runner y del alta actual | **Cerrada** |
| 3.3a | Informe de solo lectura: qué migraciones le faltan a cada tenant | **Cerrada** |
| 3.3b | Siembra del historial en el alta de tenant | **Cerrada** |
| 3.4a | Ensayo no productivo: medición real y verificación de hipótesis | **Cerrada** |
| 3.4b | Reparación urgente: secuencias propias para `tenant_2005` | **Cerrada y aplicada en producción** |
| 3.4c | Migración base versionada extraída del DDL real | **Cerrada** |
| 3.4d | Guarda: el runner se niega sobre el endpoint agrupado | **Cerrada** |
| 3.4e | Siembra del historial ya aplicado de `tenant_2005` | **Cerrada y aplicada en producción** |
| 3.4f | Reposición de las 26 claves foráneas de `tenant_2005` | **Cerrada y aplicada en producción** |
| 3.5 | Alta reproducible desde la migración base versionada | **Cerrada** |
| 3.6 | Rollback, verificación manual, compuerta global y cierre | **Cerrada** |

El ensayo se dividió al ejecutarlo. 3.4a resultó ser una subcapa completa por sí
sola: sus hallazgos cambian qué debe contener la migración base, así que
extraerla en el mismo turno habría sido escribirla antes de saber qué tenía que
incluir. La migración base se define ahora con esa evidencia.

Después, la reclasificación que siguió a 3.4a —solo `tenant_2005` es producción—
mostró que había una avería en curso más urgente que cualquier trabajo de
futuro. Por eso **3.4b pasó a ser la reparación de secuencias** y la migración
base bajó a **3.4c**. Las entradas del registro de ejecución anteriores a ese
momento llaman «3.4b» a la migración base: se conservan tal como se escribieron,
porque son el registro de lo que se sabía entonces.

El inventario de 3.0 **confirmó y ajustó** el desglose provisional de la
activación. Los cambios respecto de aquella tabla y su motivo:

- se intercala una subcapa de caracterización ejecutable (3.2) porque la
  cobertura actual no ejercita ningún camino real del runner y una extracción
  sin ella no sería reversible con evidencia;
- el versionado (3.3) se separa del alta reproducible (3.4) porque el inventario
  mostró que son dos defectos distintos: los tenants omitidos mientras están
  suspendidos y las altas nuevas que nacen sin historial;
- 3.1 permanece primero porque es la única subcapa cuyo beneficio no depende de
  ninguna otra y reduce el riesgo de todas las siguientes;
- 3.2 dividió después el versionado en 3.3a y 3.3b, porque detectar tenants
  atrasados es de solo lectura y sembrar historial escribe en datos reales: no
  comparten riesgo ni deben compartir diff;
- 3.3b descubrió que el alta reproducible no tenía punto de partida y el usuario
  decidió **adelantar el ensayo no productivo**, que pasa a ser 3.4. El alta
  reproducible baja a 3.5 y el cierre a 3.6.

Nunca se ejecutan dos subcapas en el mismo turno.

## Subcapa 3.0: resultado

Inventario hecho con búsquedas dirigidas y lectura de los archivos implicados.
No se ejecutó ninguna migración, no se abrió ninguna conexión a PostgreSQL y no
se modificó producto. Todo lo que sigue está sostenido por un archivo y una
línea concretos del repositorio; las conjeturas que no pude verificar sin base
de datos están marcadas como hipótesis.

### Puntos de entrada que pueden mutar un schema de tenant

| Entrada | Descubre tenants | Registra versión | Bloqueo |
|---|---|---|---|
| `apply_migration.py` (raíz) | Sí | **Sí** | **No** |
| `scripts/apply_plan_de_clases_migration.py` | Sí | No | No |
| `scripts/apply_pagos_tipo_pago_migration.py` | Sí | No | No |
| `scripts/apply_tipos_pagos_avanzado_migration.py` | Sí | No | No |
| `scripts/apply_tenant_indexes.py` | Sí | No | No |
| `crear_tenant_controller` (HTTP, super admin) | No aplica | **No** | No |

Los cinco scripts repiten literalmente la misma consulta de descubrimiento
—`WHERE LOWER(estado) IN ('activo', 'en_mora')`— y abren su propia conexión con
`psycopg2.connect(DATABASE_URL)`. Una búsqueda de `schema_migrations` en todo el
repositorio devuelve únicamente `apply_migration.py`, su prueba y documentación:
**ningún otro punto de entrada registra lo que aplicó**.

Consecuencia inmediata: existen cuatro caminos capaces de cambiar la estructura
de un tenant sin dejar rastro en el historial, y un sexto camino —el alta— que
crea un schema completo también sin dejarlo.

### El runner

`apply_migration.py` recibe **un archivo por invocación**. No existe un modo
«aplicar todo lo pendiente» ni un orden declarado: el orden lo pone el operador
al elegir qué archivo ejecuta. Por archivo:

1. calcula SHA-256 del texto;
2. crea `public.schema_migrations` si falta;
3. si el archivo está en `migrations/public/`, el único destino es `public`;
4. si no, descubre tenants operativos y recorre uno por uno;
5. si ya hay registro con el mismo checksum, imprime `OMITIDA`; si el checksum
   difiere, marca fallo y no aplica;
6. aplica con `SET search_path TO <schema>, public`, ejecuta el SQL y registra;
7. `commit` por tenant; ante excepción, `rollback` de **ese** tenant y continúa
   con los demás; devuelve exit 2 si hubo algún fallo.

Corpus actual: **34 archivos** en `migrations/`, de los cuales **30** son de
tenant y **4** están en `migrations/public/`.

### El registro de versiones

`public.schema_migrations` tiene `id`, `migration_name`, `target_schema`,
`checksum`, `applied_at` y `UNIQUE (migration_name, target_schema)`.

Es un registro **por archivo y por schema**, no un número de versión ordenado.
No existe el concepto de «migración siguiente» ni de secuencia: solo se puede
responder «este archivo, ¿está aplicado en este schema?». Cualquier verificación
de que un tenant esté al día debe construirse comparando el directorio
`migrations/` contra esa tabla; hoy nada en el repositorio hace esa comparación.

### El alta de tenant

`crear_tenant_controller` (`app/controllers/super_admin_controller.py:216`), en
una sola transacción: inserta en `public.colegios` con estado `'activo'`, crea
el schema, y copia la estructura desde `settings.DEFAULT_TENANT_SCHEMA` con un
bloque `DO $$` que recorre `pg_tables` del schema plantilla ejecutando
`CREATE TABLE %I.%I (LIKE %I.%I INCLUDING ALL)`. Después inserta una fila de
`institucion_branding`, copia las `plantilla_impresion` predefinidas, crea el
usuario admin inicial y registra suscripción y auditoría.

`DEFAULT_TENANT_SCHEMA` vale `"tenant_colegio_1"` (`app/config.py:35`).

**Hallazgo central de la subcapa**: el alta **no inserta ninguna fila en
`public.schema_migrations`** para el schema nuevo. Un tenant recién creado nace
con la estructura actual de la plantilla y con historial vacío. Frente al
runner, ese tenant aparece como si le faltaran las 30 migraciones de tenant, y
la próxima ejecución intentará aplicárselas todas sobre tablas que ya tienen los
cambios. Que eso resulte en `OMITIDA`, en error o en un cambio no deseado
depende de si cada SQL es idempotente, lo cual no es un contrato declarado en
ningún sitio.

### Criterio de tenant reactivable, con evidencia

`app/core/tenant_status.py` define cuatro estados: `activo`, `en_mora`,
`suspendido` y `cancelado`. `LOGIN_ALLOWED_STATUSES` y `APP_ALLOWED_STATUSES`
son ambos `{activo, en_mora}`. El runner usa exactamente ese mismo par.

`super_admin_controller.py:160` permite mover un tenant a cualquier estado
normalizado con `UPDATE public.colegios SET estado = %s`, dejando auditoría en
`public.tenant_estado_auditoria`. Ese camino **no aplica migraciones**.

De ahí sale la definición operativa, no inventada: **tenant reactivable es el
que está en `suspendido` o `cancelado` y puede volver a `activo` o `en_mora` por
ese endpoint**. Es exactamente la población que el runner omite. Un tenant que
pase seis meses suspendido y sea reactivado vuelve al servicio con el esquema
congelado en el día de su suspensión, sin ninguna señal, y la aplicación
empezará a servirle peticiones de inmediato.

### Contratos observables que la capa debe conservar

- El descubrimiento `LOWER(estado) IN ('activo','en_mora')` y su `ORDER BY id`.
- La identidad de la migración: par `(migration_name, target_schema)` y checksum
  SHA-256 del texto exacto del archivo, sensible incluso a un salto de línea
  final.
- La semántica de salida: `OK`, `OMITIDA`, `PENDIENTE`, `FALLO`, exit 0 o 2, y
  `--dry-run` que no escribe nada.
- El aislamiento transaccional por tenant: un fallo revierte ese tenant y no
  detiene a los demás.
- `SET search_path TO <schema>, public` durante la aplicación.
- El payload y los status codes del alta de tenant, incluidas sus validaciones
  422 y la normalización de código y correo.
- El nombre derivado del schema, `tenant_<codigo>`, y `TENANT_CODE_PATTERN`.

### Cobertura existente y hueco exacto

`tests/test_apply_migration.py` tiene seis casos, todos con un `FakeCursor` que
solo acumula llamadas: estabilidad del checksum, presencia del `CREATE TABLE IF
NOT EXISTS`, parámetros de lectura y de inserción del historial, la cláusula
`WHERE` comparada **como subcadena literal** y `is_public_migration`.

`tests/test_super_admin.py` cubre `crear_tenant_controller` con dobles: verifica
los parámetros de `colegios`, admin, suscripción y auditoría, y que hubo commit.

Ninguna prueba ejecuta `apply_migration()` de principio a fin. En consecuencia
**no existe cobertura** de: la transacción por tenant, el `rollback` parcial, el
conteo de fallos, el exit 2, el camino `--dry-run`, la rama de migración
pública, el rechazo por checksum divergente ni el `search_path` efectivo.
Tampoco hay prueba alguna que observe el `CREATE SCHEMA`, el bloque `DO $$` de
copia ni la ausencia de siembra de historial en el alta.

El hueco discriminante que 3.2 debe cerrar es una prueba que falle si:

1. un tenant suspendido y luego reactivado queda sin migraciones aplicadas;
2. un tenant recién creado tiene historial vacío;
3. dos ejecuciones concurrentes del runner no se excluyen;
4. un fallo en el tenant *n* impide continuar con el *n+1* o pierde el conteo.

Las cuatro pueden probarse con un pool o conexiones falsas, sin PostgreSQL, como
ya se hizo en la capa 2 con `tests/test_threadpool_capacity.py`.

### Hipótesis que requieren base de datos y no se afirman aquí

No pude verificarlas leyendo el repositorio. Quedan como trabajo del ensayo no
productivo, **no** como hechos:

1. `LIKE ... INCLUDING ALL` no copia claves foráneas, por lo que un tenant nuevo
   podría carecer de las FK que sí tiene la plantilla.
2. Las columnas `SERIAL` copiadas por `INCLUDING DEFAULTS` podrían conservar un
   `nextval` apuntando a la secuencia del schema plantilla.
3. El bloque solo recorre `pg_tables`: vistas, funciones, disparadores y tipos
   del schema plantilla no se copiarían.
4. `tenant_colegio_1` sería además un tenant operativo real y no una plantilla
   inerte, de modo que cualquier cambio manual en él afectaría a las altas
   futuras. La existencia de `scripts/limpiar_tenant_colegio_1_operativo.py`
   sugiere esa tensión, pero no la demuestra.

### Ensayo no productivo y rollback de esquema

El procedimiento acordado para las subcapas siguientes, antes de tocar nada:

1. levantar una base desechable, nunca producción ni la base real de staging;
2. sembrar `public.colegios` con al menos un tenant `activo`, uno `en_mora`, uno
   `suspendido` y uno `cancelado`, y un schema plantilla;
3. capturar la estructura de referencia de cada schema con una consulta de solo
   lectura a `information_schema`, guardada como texto comparable;
4. ejecutar el camino bajo prueba;
5. volver a capturar y comparar contra la referencia;
6. reactivar el tenant suspendido y comprobar qué le falta.

El rollback de esta capa deja de ser solo de aplicación. Para cada subcapa que
toque esquema, la bitácora debe registrar antes: la sentencia inversa cuando
exista, el respaldo previo cuando no exista, y si la migración es reversible sin
pérdida. Ninguna subcapa puede aplicarse a un tenant real sin ese registro.

### Criterios de cierre de 3.0: estado real

Seis de los siete criterios quedaron cumplidos: el mecanismo está descrito con
evidencia citada, los contratos están enumerados, existe una estrategia de
prueba discriminante, existe un procedimiento de ensayo y una forma de rollback,
la compuerta y `git diff --check` terminaron correctamente, y no se inició 3.1.

Uno quedó **cumplido a medias y se declara así**: «el criterio de tenant
reactivable está definido y aplicado a un inventario concreto». El criterio está
definido con evidencia del código, pero **no se aplicó a un inventario real de
tenants** porque eso exige consultar `public.colegios` y 3.0 no abrió ninguna
conexión. Se cierra la subcapa con esa parte pendiente en lugar de darla por
cumplida; el recuento por estado debe hacerse en el ensayo de 3.5 o antes, en
cuanto exista una base desechable, y no debe leerse de `docs/MIGRACIONES.md`,
que describe cuatro schemas operativos a una fecha pasada.

### Siguiente subcapa: 3.1, trabajo exacto

1. Confirmar `main`, árbol limpio y que todo commit posterior al base esté
   explicado en esta bitácora.
2. Abrir únicamente `apply_migration.py` y `tests/test_apply_migration.py`.
3. Agregar primero la caracterización que fije el comportamiento actual del
   camino que se va a tocar, antes de introducir el bloqueo.
4. Añadir un bloqueo que impida dos ejecuciones simultáneas, usando el propio
   PostgreSQL y sin dependencias nuevas. Conservar sin cambios el
   descubrimiento, el checksum, la transacción por tenant, los mensajes, los
   códigos de salida y `--dry-run`.
5. No tocar los cuatro scripts ad-hoc, el alta de tenant, las migraciones
   existentes ni `app/`.
6. Ejecutar las pruebas específicas, Ruff del alcance, la compuerta global y
   `git diff --check`; revisar que el diff pertenezca solo a 3.1.
7. Actualizar esta bitácora y detenerse sin iniciar 3.2.

Archivos previstos para 3.1: `apply_migration.py`,
`tests/test_apply_migration.py` y esta bitácora.

## Subcapa 3.1: resultado

`apply_migration.py` gana una constante `MIGRATION_LOCK_KEY` y la función
`try_acquire_migration_lock`. El runner pide `pg_try_advisory_lock` justo
después de abrir la conexión y **antes** de `ensure_migration_history`; si otra
ejecución lo tiene, imprime un mensaje propio, cierra cursor y conexión y
devuelve exit 2 sin haber leído ni escrito nada.

Todo lo demás se conserva sin tocar: la consulta de descubrimiento y su
`ORDER BY id`, el checksum, la transacción por tenant con su `rollback` parcial
y el conteo de fallos, los mensajes `OK`, `OMITIDA`, `PENDIENTE` y `FALLO`, los
códigos de salida 0, 1 y 2, `--dry-run`, el `SET search_path TO <schema>, public`
y la rama de migración pública. No se tocaron los cuatro scripts ad-hoc, el alta
de tenant, `app/` ni ningún archivo de `migrations/`.

### Por qué un lock de sesión y no de transacción

`pg_advisory_xact_lock` se libera en cada `commit`, y el runner hace un `commit`
por tenant: el lock se soltaría a mitad de la ejecución y dos procesos podrían
intercalarse entre tenants. El lock de sesión sobrevive a los `commit` y
`rollback` por tenant.

No se añadió una liberación explícita. PostgreSQL libera los locks de sesión al
cerrarse la conexión, y se comprobó que **todos** los caminos de retorno
posteriores a `psycopg2.connect` cierran la conexión: el `finally` de la rama
pública, el retorno sin tenants y el cierre tras el bucle. Añadir un
`pg_advisory_unlock` en cada retorno habría agrandado el diff sin dar una
garantía que el motor ya da.

### Por qué exit 2 y no un código nuevo

Un conflicto de lock devuelve **2**, el código de fallo que ya existía, en vez
de introducir un 3. Los invariantes de esta capa exigen conservar los códigos de
salida, y cualquier automatización que trate «distinto de cero» como «no se
aplicó» sigue funcionando sin cambios. La señal que distingue el caso es el
mensaje, no el código.

### Por qué `--dry-run` también toma el lock

Se consideró eximirlo, porque una simulación no escribe. Se descartó: la
simulación lee la misma tabla que una ejecución real está escribiendo, así que
su respuesta `PENDIENTE`/`OMITIDA` durante una migración en curso no es
confiable. Se prefirió un solo camino de código y una respuesta conservadora.
El coste aceptado es que no se puede simular mientras otra ejecución corre.

### La caracterización se comprobó contra el runner anterior

No basta con que las pruebas pasen después del cambio: hay que demostrar que
describen el comportamiento que ya existía. Se retiró temporalmente solo el
cambio de producto con `git stash push -- apply_migration.py`, se ejecutó el
subconjunto que no menciona el lock y **8 pruebas pasaron sobre el runner
base**. Después se restauró el cambio con `git stash pop` y se verificó que el
lock volvía a estar presente.

Esas 8 fijan sobre el código anterior el camino completo: aplicar y registrar,
omitir una migración ya aplicada, rechazar el mismo nombre con checksum
distinto, y el caso sin tenants operativos. Las 3 restantes describen
comportamiento nuevo y por eso no se ejecutaron contra la base.

Las pruebas son herméticas: usan un cursor guionizado y una conexión falsa, sin
PostgreSQL, sin red y sin `.env` real. No demuestran que el lock funcione en un
motor real; demuestran que el runner lo pide antes de todo lo demás y que se
detiene sin efectos cuando no lo obtiene.

| Comprobación | Resultado |
|---|---|
| Caracterización sobre el runner base | **8 pasaron**, 9 deseleccionadas |
| Pruebas del archivo tras el cambio | **17 pasaron** |
| Dirigidas ampliadas con tenants, super admin e índices | **48 pasaron** |
| Compuerta global | **Exit 0**: 488 pruebas, 5 warnings conocidos |
| Ruff del alcance | `All checks passed!` |
| Dependencias | `No broken requirements found.` |

La suite pasó de 477 a **488** pruebas: 11 casos nuevos en
`tests/test_apply_migration.py`.

### Precondición no verificada que condiciona el valor del lock

Un advisory lock de sesión exige una sesión real. La capa 1 dejó registrado que
el endpoint `-pooler` de Neon es PgBouncer. Si `DATABASE_URL` apuntara a ese
endpoint, la conexión puede reasignarse entre sentencias y **un lock de sesión
dejaría de ser una garantía**.

No se verificó: 3.1 no leyó `.env` ni abrió ninguna conexión. Queda como
precondición explícita del ensayo: **el runner debe usar el endpoint directo, no
el agrupado**. Mientras no se compruebe, el bloqueo no debe presentarse como
efectivo en el entorno real.

### Siguiente subcapa: 3.2, trabajo exacto

1. Confirmar `main`, árbol limpio y que todo commit posterior al base esté
   explicado en esta bitácora.
2. Completar la caracterización ejecutable que 3.0 identificó como hueco y que
   3.1 solo cubrió en la parte que tocó: la rama de migración pública, el fallo
   de un tenant que no debe detener a los siguientes, el conteo de fallos y el
   exit 2 resultante, y el camino `--dry-run` sobre varios tenants.
3. Caracterizar el alta de tenant en lo que 3.3 y 3.4 van a necesitar: que el
   `CREATE SCHEMA` y el bloque de copia ocurren, y que **no** se siembra
   `public.schema_migrations`. Esa prueba debe fallar cuando 3.3 corrija el
   defecto, y ese fallo es la señal buscada.
4. No modificar producto en 3.2. Es una subcapa de solo pruebas.
5. Ejecutar pruebas específicas, Ruff del alcance, compuerta global y
   `git diff --check`; actualizar esta bitácora y detenerse antes de 3.3.

Archivos previstos para 3.2: `tests/test_apply_migration.py`,
`tests/test_super_admin.py` o un archivo de pruebas nuevo para el alta, y esta
bitácora.

## Subcapa 3.2: resultado

Subcapa de solo pruebas. **No se modificó producto**, lo que se verificó con
`git status --short -- app apply_migration.py scripts migrations` vacío al
terminar. Por construcción, entonces, todo lo que estas pruebas fijan es el
comportamiento que ya existía: no hizo falta retirar ningún cambio para
comprobarlo, como sí hizo 3.1.

### Runner: lo que faltaba del camino real

`tests/test_apply_migration.py` pasó de 17 a **28 casos**. Se cerraron las
cuatro zonas que 3.0 marcó sin cobertura y que 3.1 solo rozó:

- **Rama pública**: destino único `public`, `SET search_path TO public`, registro
  con `target_schema = "public"`, ausencia de consulta a `public.colegios`, el
  caso ya aplicado, el checksum divergente que devuelve 2 y su `--dry-run`. Se
  fijó además que la rama pública también pide el lock antes que nada.
- **Aislamiento del fallo por tenant**: con tres tenants y el segundo fallando,
  se intenta el SQL en los tres pero solo quedan registrados dos, y el runner
  devuelve 2. Una prueba gemela hace fallar al **primero** y comprueba que los
  otros dos siguen. Esto fija que un fallo revierte su tenant y no interrumpe la
  ejecución.
- **Qué tenant queda fuera del historial**: se afirma la lista exacta
  `["tenant_a", "tenant_c"]`, no solo el conteo. Un cambio que registrara al
  tenant equivocado no pasaría desapercibido.
- **`--dry-run` sobre varios tenants**: cero ejecuciones del SQL, cero registros
  y ni siquiera un `SET search_path`.
- Se añadieron también los dos retornos tempranos con código 1: archivo
  inexistente y `DATABASE_URL` ausente.

### Alta de tenant: archivo propio

Se creó `tests/test_tenant_provisioning.py` con **11 casos**, en vez de ampliar
`tests/test_super_admin.py`. El motivo es que 3.3 y 3.4 van a reescribir este
camino y conviene que su caracterización viva en un archivo cuyo diff se pueda
revisar aislado; `test_super_admin.py` cubre además listado, estados y auth, que
no se tocan. Sus dobles no servían tal cual porque guardan el objeto de consulta
sin convertirlo a texto, y el alta usa `sql.Composed`.

Lo que queda fijado: el schema derivado `tenant_<codigo>`, la copia de
estructura desde `settings.DEFAULT_TENANT_SCHEMA` vía `pg_tables` e
`INCLUDING ALL`, el orden colegio → `CREATE SCHEMA` → copia, la copia solo de
plantillas predefinidas, el estado inicial `activo`, el admin obligado a cambiar
password, el 409 por código o correo duplicado, el cierre del cursor ante fallo
y la restauración del `ContextVar` del tenant tanto en el camino correcto como
en el de error.

### La prueba que debe fallar en 3.3

`test_el_alta_todavia_no_siembra_el_historial_de_migraciones` afirma que el alta
**no** escribe en `public.schema_migrations`. Es deliberada: fija el defecto
central que encontró 3.0. Cuando 3.3 lo corrija, esta prueba fallará, y ese
fallo es la señal buscada, no una regresión. Su docstring lo dice para que nadie
la «arregle» borrándola.

Una aserción negativa puede pasar por el motivo equivocado —un fragmento mal
escrito, un cursor que no registró nada—, así que lleva un **control positivo**
en el mismo caso: se exige que el inspector sí encuentre
`INSERT INTO public.colegios`. Sin ese control, la prueba sería decorativa.

| Comprobación | Resultado |
|---|---|
| `tests/test_apply_migration.py` | **28 pasaron** (eran 17) |
| `tests/test_tenant_provisioning.py` | **11 pasaron**, archivo nuevo |
| Dirigidas ampliadas | **70 pasaron** |
| Compuerta global | **Exit 0**: 510 pruebas, 5 warnings conocidos |
| Ruff del alcance | `All checks passed!` |
| Dependencias | `No broken requirements found.` |
| Producto modificado | **ninguno**, verificado con `git status` acotado |

La suite pasó de 488 a **510** pruebas.

### Lo que 3.2 deliberadamente no cubre

- Los cuatro scripts ad-hoc siguen sin caracterización propia, salvo
  `scripts/apply_tenant_indexes.py`, que ya tenía la suya. No se amplió el
  alcance para cubrirlos porque su destino —extenderles el lock o retirarlos—
  es una decisión todavía no tomada.
- Nada de esto toca PostgreSQL. Son dobles: demuestran orden, parámetros y
  ramas, no que el SQL sea válido ni que el schema resultante sea correcto. Esa
  evidencia solo puede venir del ensayo no productivo.

### Siguiente subcapa: 3.3a, trabajo exacto

El inventario de 3.0 juntó en 3.3 dos cambios que no comparten riesgo: detectar
tenants atrasados es de solo lectura, mientras que sembrar historial escribe en
datos reales. Se separan siguiendo el precedente de 2.3a y 2.3b, para que cada
diff sea revisable por separado.

1. Confirmar `main`, árbol limpio y que todo commit posterior al base esté
   explicado en esta bitácora.
2. Añadir una comprobación de solo lectura que compare el directorio
   `migrations/` contra `public.schema_migrations` y reporte, por tenant, qué
   migraciones le faltan. Debe incluir explícitamente a los tenants
   `suspendido` y `cancelado`, que hoy el descubrimiento omite.
3. No aplicar nada, no escribir nada y no cambiar el runner existente: es un
   informe, no una corrección.
4. Cubrirla con pruebas herméticas, incluido el caso de un tenant reactivable
   atrasado y el de un tenant recién creado con historial vacío.
5. Ejecutar pruebas específicas, Ruff del alcance, compuerta global y
   `git diff --check`; actualizar esta bitácora y detenerse antes de 3.3b.

3.3b, que siembra el historial en el alta y hará fallar a propósito la prueba
descrita arriba, queda para su propio turno.

## Subcapa 3.3a: resultado

Se añadió `scripts/auditar_migraciones_tenants.py`, un informe que compara el
directorio `migrations/` contra `public.schema_migrations` y dice, por destino,
qué le falta. **No modifica nada** y no cambia el runner ni ningún archivo
existente de producto: el único cambio en `app/`, `apply_migration.py`,
`migrations/`, el workflow y `requirements.txt` es que no hay ninguno,
verificado con `git status` acotado.

### Cómo garantiza que es de solo lectura

No basta con no escribir por descuido; el script lo hace imposible por
construcción, siguiendo la convención de
`scripts/auditar_plan_de_clases_integridad.py`:

- abre la transacción con `SET TRANSACTION READ ONLY` como primera sentencia;
- termina siempre con `rollback` en el `finally`;
- comprueba la existencia del historial con `to_regclass`, **sin** el
  `CREATE TABLE IF NOT EXISTS` que sí hace el runner: si la tabla no existe, lo
  informa y devuelve 2 en vez de crearla.

Esa última diferencia importa. El runner crea el historial como efecto
colateral de auditarlo; una auditoría que hiciera lo mismo cambiaría el estado
que dice observar.

### Qué ve que el runner no ve

`fetch_tenants` consulta `public.colegios` **sin `WHERE`**. Ahí está el valor de
la subcapa: el runner solo alcanza `activo` y `en_mora`, mientras que el informe
incluye también `suspendido` y `cancelado` y los marca con
`[el runner lo omite]`. Cuando uno de esos está atrasado, imprime además una
línea propia advirtiendo que quedaría incompleto si se reactiva, que es
exactamente el defecto que 3.0 describió.

El informe distingue dos problemas, no uno:

- **faltantes**: la migración no está registrada para ese destino;
- **divergentes**: está registrada, pero con un checksum distinto al del archivo
  actual. 3.0 dejó anotado que el checksum es sensible al byte, así que un
  destino con divergencias no está al día aunque el nombre figure.

También incluye siempre el destino `public`, con las migraciones de
`migrations/public/`.

### Una sola definición de checksum

El script importa `calculate_checksum` de `apply_migration` en lugar de
reescribirlo. Como compara contra lo que el runner registró, ambas partes deben
usar la misma función: una copia podría divergir en silencio y producir
divergencias falsas. Para que funcione al ejecutarlo como script suelto
—donde `sys.path[0]` es `scripts/` y no la raíz— se inserta `ROOT_DIR` en
`sys.path` con un comentario que explica el motivo, y el `import` lleva
`# noqa: E402`.

Se descartó duplicar la función y protegerla con una prueba de igualdad: es
menos seguro que no tener dos definiciones. La prueba de igualdad se conservó de
todos modos, ahora como aserción de identidad, para que un cambio futuro que
rompa el enlace se vea.

### Verificación

Las pruebas están en `tests/test_auditar_migraciones_tenants.py`, **16 casos**
herméticos con un cursor falso y directorios de `tmp_path`. Cubren los dos casos
que esta bitácora exigía —un tenant reactivable atrasado y un tenant recién
creado con historial vacío— más el tenant `cancelado`, el activo atrasado que no
debe marcarse como omitido, el destino al día, el destino público, la
divergencia por checksum, el agrupado por schema, que `fetch_tenants` no lleva
`WHERE` y que `historial_existe` no ejecuta ningún `CREATE`.

Se comprobó aparte que el `import` resuelve al ejecutarlo como script suelto:
importando el módulo desde un directorio de trabajo fuera del repositorio, con
`sys.path[0]` apuntando a `scripts/`. Devolvió `IMPORT_OK` y confirmó que
`calculate_checksum` procede del módulo `apply_migration`. Ese ejercicio no
abrió ninguna conexión.

| Comprobación | Resultado |
|---|---|
| `tests/test_auditar_migraciones_tenants.py` | **16 pasaron**, archivo nuevo |
| Dirigidas ampliadas | **71 pasaron** |
| Compuerta global | **Exit 0**: 526 pruebas, 5 warnings conocidos |
| Ruff del alcance | `All checks passed!` |
| Dependencias | `No broken requirements found.` |
| Producto existente modificado | **ninguno**; solo se añadió un script |

La suite pasó de 510 a **526** pruebas.

### Límites de este informe

- **No se ejecutó contra ninguna base de datos.** Hacerlo habría significado
  conectarse a la base real, que está fuera de lo autorizado. Su ejecución con
  datos verdaderos pertenece al ensayo no productivo de 3.5, y solo entonces se
  sabrá cuántos tenants están realmente atrasados.
- El informe cree lo que dice `public.schema_migrations`, y 3.0 estableció que
  los cuatro scripts ad-hoc aplican DDL sin registrar nada. Un destino puede
  aparecer «faltante» aunque el cambio ya esté aplicado por esa vía. El informe
  acota el problema; no lo resuelve.
- Los nombres de archivo se comparan tal cual. Renombrar una migración ya
  aplicada la haría aparecer como faltante, igual que le ocurre al runner.

### Siguiente subcapa: 3.3b, trabajo exacto

1. Confirmar `main`, árbol limpio y que todo commit posterior al base esté
   explicado en esta bitácora.
2. Abrir únicamente `crear_tenant_controller` en
   `app/controllers/super_admin_controller.py` y
   `tests/test_tenant_provisioning.py`.
3. Sembrar `public.schema_migrations` para el schema nuevo **dentro de la misma
   transacción** del alta, copiando las filas del schema plantilla:
   `INSERT ... SELECT migration_name, <schema_nuevo>, checksum FROM
   public.schema_migrations WHERE target_schema = <plantilla>`. Se copia lo que
   la plantilla tiene aplicado, no el contenido del directorio `migrations/`,
   porque el schema nuevo es una copia estructural de la plantilla y hereda
   exactamente lo que ella lleva. Leer el directorio supondría que la plantilla
   está al día, cosa que nadie ha verificado.
4. Reemplazar `test_el_alta_todavia_no_siembra_el_historial_de_migraciones` por
   su versión positiva. Su fallo al aplicar el cambio es la señal esperada, no
   una regresión.
5. No tocar el runner, los scripts ad-hoc, el informe de 3.3a ni archivos
   existentes de `migrations/`.
6. Ejecutar pruebas específicas, Ruff del alcance, compuerta global y
   `git diff --check`; actualizar esta bitácora y detenerse antes de 3.4.

Archivos previstos para 3.3b: `app/controllers/super_admin_controller.py`,
`tests/test_tenant_provisioning.py` y esta bitácora.

## Subcapa 3.3b: resultado

`crear_tenant_controller` siembra ahora `public.schema_migrations` para el
schema nuevo, justo después de copiar la estructura y **dentro de la misma
transacción** del alta. El diff de producto son **19 líneas, todas añadidas,
cero eliminadas**, en un solo archivo de `app/`.

La sentencia copia las filas de la plantilla:

```sql
INSERT INTO public.schema_migrations (migration_name, target_schema, checksum)
SELECT migration_name, %s, checksum
FROM public.schema_migrations
WHERE target_schema = %s
```

### Por qué se copia la plantilla y no el directorio

Leer `migrations/` y registrar todo lo que hay allí habría supuesto que la
plantilla está al día, cosa que nadie ha verificado y que 3.3a existe
precisamente para averiguar. Copiar sus filas dice la verdad: el schema nuevo es
una copia estructural de la plantilla, así que hereda exactamente lo que la
plantilla lleva aplicado, ni más ni menos.

La consecuencia hay que decirla claro: **si la plantilla está atrasada, el
tenant nuevo hereda ese atraso**. Eso no es un defecto de la siembra, es el
comportamiento correcto —el schema realmente está atrasado— y ahora el informe
de 3.3a lo mostrará en lugar de ocultarlo tras un historial vacío que fingía que
faltaba todo.

### La guarda `to_regclass`

Una base que nunca ejecutó una migración no tiene `public.schema_migrations`.
Sin guarda, el alta pasaría de funcionar a devolver un error en ese entorno. Se
comprueba la existencia con `to_regclass` y, si falta, se omite la siembra y el
alta continúa como antes.

Se descartó crear la tabla desde el alta, como hace el runner: el alta de un
colegio no es el lugar donde debe nacer el historial de migraciones, y hacerlo
la convertiría en una vía más de escritura sobre el esquema global.

### La señal deliberada disparó

3.2 dejó `test_el_alta_todavia_no_siembra_el_historial_de_migraciones` fijando
el defecto, con la advertencia de que su fallo sería la señal de haberlo
corregido. Se reemplazó por cuatro pruebas positivas, y se comprobó que
**detectan realmente el cambio**: retirando solo el cambio de producto con
`git stash push -- app/controllers/super_admin_controller.py`, las cuatro
fallan contra el controlador anterior y las otras diez siguen pasando.

Esas diez son la prueba de que el resto del alta no se movió: paths, validación,
orden colegio → `CREATE SCHEMA` → copia, plantillas predefinidas, admin inicial,
409 por duplicado, cierre del cursor y restauración del `ContextVar`.

| Comprobación | Resultado |
|---|---|
| Pruebas nuevas contra el controlador **anterior** | **4 fallaron**, 10 pasaron: la señal esperada |
| `tests/test_tenant_provisioning.py` tras el cambio | **14 pasaron** (eran 11) |
| Dirigidas ampliadas | **99 pasaron** |
| Compuerta global | **Exit 0**: 529 pruebas, 5 warnings conocidos |
| Ruff del alcance | `All checks passed!` |
| Diff de producto | 19 líneas añadidas, 0 eliminadas, 1 archivo |

La suite pasó de 526 a **529** pruebas.

### Lo que sigue sin estar probado

Nada de esto tocó PostgreSQL. Que el `INSERT ... SELECT` sea válido, que la
restricción `UNIQUE (migration_name, target_schema)` no choque y que el tenant
nuevo quede efectivamente al mismo nivel que la plantilla son afirmaciones que
solo el ensayo no productivo puede sostener.

### Siguiente subcapa: 3.4, y un obstáculo que hay que decidir antes

3.4 debía sustituir la copia de la plantilla por un alta construida desde
migraciones versionadas. El inventario deja ver un problema de fondo que no se
puede resolver leyendo el repositorio:

**las 30 migraciones de tenant son incrementales.** Son `ALTER TABLE`, índices y
columnas que presuponen unas tablas base que ninguna migración crea. Hoy esa
estructura base solo existe dentro del schema plantilla, en la base de datos. No
se puede levantar un tenant desde `migrations/` sin un punto de partida.

Existe un candidato: `scripts/legacy/crear_cliente.py` contiene 14
`CREATE TABLE`. No se inspeccionó su contenido —queda fuera del alcance de
3.3b— y **no debe asumirse que coincide con la plantilla actual**: es legacy y
lo separan treinta migraciones de deriva posible.

Por eso 3.4 no puede empezar como estaba escrita. Las opciones son dos y la
decisión es del usuario:

1. **Adelantar el ensayo no productivo** (hoy 3.5) para extraer de una base
   desechable el DDL real de la plantilla, convertirlo en una migración base
   versionada y recién entonces ejecutar 3.4. Es el camino con evidencia.
2. **Reconstruir la base desde `scripts/legacy/crear_cliente.py`** y verificar
   después su equivalencia. Es más rápido y más frágil: si el legacy divergió,
   el error aparecería en tenants nuevos y quizá tarde.

La recomendación es la primera. En cualquier caso, la siguiente subcapa **no
debe iniciarse sin esa decisión explícita**, porque cambia qué se considera la
fuente de verdad del esquema de un tenant.

## Decisión sobre el esquema base

El 2026-08-13 el usuario eligió **adelantar el ensayo no productivo**. El
esquema base saldrá del DDL real extraído de una base desechable, no de
`scripts/legacy/crear_cliente.py`.

Consecuencias registradas:

- el ensayo pasa a ser **3.4** y deja de ser el cierre; el alta reproducible baja
  a **3.5** y el cierre de capa a **3.6**;
- la fuente de verdad del esquema de un tenant será el DDL observado en una base
  real, promovido a una migración base versionada dentro de `migrations/`;
- `scripts/legacy/crear_cliente.py` queda descartado como fuente. Podrá usarse
  como contraste para explicar diferencias, nunca como origen;
- riesgo aceptado: 3.5 queda bloqueada hasta que exista una base desechable. Es
  un coste deliberado, a cambio de no fundar el alta de todos los colegios
  futuros sobre un archivo legacy cuya equivalencia nadie ha comprobado.

### De dónde sale la estructura real: rama de Neon

Al preparar el requisito apareció un segundo problema que el usuario detectó
antes de gastarse un turno en él: **una base desechable vacía no sirve**. La
estructura verdadera de `tenant_colegio_1` no está en el repositorio; existe
únicamente en la base real. Si el asistente creara esas tablas para después
«extraer» su DDL, estaría midiendo lo que él mismo inventó, que es el mismo
defecto por el que se descartó `scripts/legacy/crear_cliente.py`.

El entorno tampoco ofrece salida local: se comprobó que en la máquina no hay
`pg_dump`, `psql`, Docker ni PostgreSQL instalado. El único cliente disponible
es `psycopg2` dentro del `venv`.

Decisión del usuario el 2026-08-13: **usar una rama de Neon**. Una rama es una
copia aislada de la base real que ya nace con el schema plantilla y su
estructura verdadera; escribir en ella no afecta al original y puede destruirse
después. Se descartaron:

- instalar herramientas cliente para un `pg_dump --schema-only`, por el coste de
  instalación, aunque habría dado el DDL más fiable;
- reconstruir el DDL con un script de introspección propio, porque rehacer a
  mano lo que hace `pg_dump` es frágil en claves foráneas, secuencias, defaults
  e índices, y un baseline incompleto no se notaría hasta tarde.

### Restricción de datos, vinculante para 3.4

Si la rama no es *schema-only*, contendrá datos reales de estudiantes. La
subcapa queda limitada a leer **estructura**: `information_schema` y
`pg_catalog`. No se consultan filas de las tablas de negocio, no se exportan y
no se copian a ningún archivo del repositorio.

La cadena de conexión de la rama **no se escribe en esta bitácora, ni en el
repositorio, ni en `.env`**. Se usa solo como variable de entorno durante la
ejecución. Aquí se registra que existió una rama desechable, nunca su
credencial.

### Requisito para poder ejecutar 3.4

1. Una rama de Neon creada desde la base real, preferentemente *schema-only* si
   el plan lo permite.
2. Su cadena de conexión con el endpoint **directo**, no el `-pooler`: la capa 1
   registró que el agrupado es PgBouncer, y 3.1 dejó pendiente comprobar si un
   advisory lock de sesión se sostiene sobre él.
3. Confirmación explícita de que esa cadena corresponde a la rama y **no** a
   producción.

Mientras no exista, 3.4 no puede empezar. Ninguna subcapa usará el
`DATABASE_URL` del `.env` del repositorio.

### Siguiente subcapa: 3.4, trabajo exacto

1. Confirmar `main`, árbol limpio y que todo commit posterior al base esté
   explicado en esta bitácora.
2. Confirmar que la conexión recibida es la rama desechable y no producción, y
   registrarlo. Comprobar antes de escribir nada que el destino no es la base
   real; ante cualquier duda, detenerse.
3. Partir de lo que la rama ya trae: el schema plantilla con su estructura
   verdadera y `public.colegios` con sus tenants. Solo se **añaden** los tenants
   de prueba que falten para cubrir los cuatro estados —`activo`, `en_mora`,
   `suspendido` y `cancelado`—, con schemas propios y nombres inequívocamente de
   prueba. No se modifican ni se borran las filas heredadas.
4. Ejecutar por primera vez con datos reales `scripts/auditar_migraciones_tenants.py`
   y registrar su salida: es la primera medición del versionado por tenant, que
   3.0 dejó explícitamente como no medida.
5. Verificar allí las cuatro hipótesis que 3.0 dejó abiertas sobre
   `LIKE ... INCLUDING ALL`: claves foráneas, secuencias `SERIAL`, objetos que no
   son tablas y si `tenant_colegio_1` es además un tenant operativo.
6. Comprobar la precondición de 3.1: si el lock de sesión se sostiene sobre el
   endpoint que use el runner, o si exige el endpoint directo.
7. Extraer el DDL de la plantilla y promoverlo a una migración base versionada
   en `migrations/`, sin tocar ningún archivo existente de ese directorio.
8. Documentar el rollback de esquema con la evidencia obtenida.
9. Actualizar esta bitácora y detenerse sin iniciar 3.5.

Archivos previstos para 3.4: una migración base nueva en `migrations/`, quizá un
script de apoyo para el ensayo, y esta bitácora. **No** se modifican archivos
existentes de `migrations/` ni el runner.

## Subcapa 3.4a: resultado

Ejecutada sobre la rama de Neon `ensayo-3-4-no-produccion`, creada por el
usuario desde `production` y confirmada por él como desechable. Antes de
conectar se comparó el host recibido con el de `.env` sin exponer su
contraseña: `ep-tiny-dream-aiceysjn…` frente a `ep-late-smoke-aip41j6x-pooler…`,
endpoints distintos. Los scripts del ensayo viven en el scratchpad, fuera del
repositorio, y todos llevan un guardarraíl que aborta si el DSN no contiene el
identificador de la rama.

**Ningún archivo del repositorio cambió en 3.4a salvo esta bitácora y el
índice.** El único objeto creado en la rama fue un schema de prueba destruido al
terminar; se verificó después que no quedaron restos y que los cuatro schemas
heredados, las 4 filas de `public.colegios` y las 100 de
`public.schema_migrations` siguen intactos.

### Primera medición real del versionado

`scripts/auditar_migraciones_tenants.py` se ejecutó por primera vez contra datos
verdaderos y terminó en exit 2, como debe cuando hay pendientes:

| Destino | Estado | Migraciones registradas | Faltan | Divergen |
|---|---|---:|---:|---:|
| `public` | — | 4 de 4 | 0 | 0 |
| `tenant_colegio_1` (Colegio Demo) | activo | 30 de 30 | 0 | 0 |
| `tenant_3333` (milagro) | activo | 30 de 30 | 0 | 0 |
| `tenant_4444` (la paz) | activo | 21 de 30 | **9** | 0 |
| `tenant_2005` (…la sabiduría de galapa) | activo | 15 de 30 | **15** | 0 |

Ningún tenant está hoy `suspendido` ni `cancelado`, así que el riesgo de
reactivación que motivó 3.3a existe como mecanismo pero no tiene víctimas
actuales. No hay ninguna divergencia de checksum.

Las que faltan son siempre **las más antiguas**, en bloque y sin huecos. Es la
firma de un tenant creado *después* de que esas migraciones se aplicaran: nació
copiando la plantilla, con la estructura ya puesta y el historial vacío. Es
exactamente el defecto que 3.3b corrigió para las altas futuras.

Y la comparación estructural lo confirma: frente a la plantilla, los tres
tenants tienen **las mismas 281 columnas y los mismos 89 índices**, sin
diferencias. No están estructuralmente atrasados; les falta el **registro**.
Aplicarles hoy esas migraciones con el runner intentaría repetir cambios ya
presentes.

### Las cuatro hipótesis de 3.0, resueltas

Se creó el schema de prueba `tenant_zzz_ensayo_3_4_borrame` y se le aplicó
**exactamente el mismo bloque `DO $$` del alta**, para atribuir causa y no solo
correlación. Resultado sobre 30 tablas copiadas:

| Hipótesis de 3.0 | Veredicto | Evidencia en la copia controlada |
|---|---|---|
| `LIKE INCLUDING ALL` no copia claves foráneas | **Confirmada** | **0 claves foráneas**; la plantilla tiene 37 |
| Los `SERIAL` pueden apuntar a la secuencia de la plantilla | **Confirmada** | **30 de 30** defaults apuntan a `tenant_colegio_1.<tabla>_id_seq` |
| Solo se copia `pg_tables` | **Confirmada** | 0 secuencias, 0 disparadores, 0 funciones; la plantilla tiene 30, 1 y 1 |
| La plantilla es además un tenant operativo | **Confirmada** | `tenant_colegio_1` figura en `public.colegios` como «Colegio Demo», estado `activo` |

### El daño ya está en producción

Esto no es una conjetura sobre altas futuras: los tres colegios reales lo
arrastran hoy.

| Schema | Claves foráneas | Secuencias propias | Columnas que usan secuencias de la plantilla |
|---|---:|---:|---:|
| `tenant_colegio_1` (plantilla) | 37 | 30 | — |
| `tenant_3333` | 14 | 7 | **23** |
| `tenant_4444` | 11 | 4 | **26** |
| `tenant_2005` | 11 | 4 | **26** |

Dos consecuencias, ambas reales:

1. **Sin integridad referencial.** A cada colegio le faltan entre 23 y 26 claves
   foráneas: `asignaciones → cursos/materias/profesor`,
   `asistencia → estudiantes`, `boletin_cabecera → estudiantes`,
   `boletin_detalles → boletin_cabecera` y otras. Hoy pueden existir filas
   huérfanas sin que la base lo impida. Las `CHECK`, `PRIMARY KEY` y `UNIQUE` sí
   se copiaron y coinciden.
2. **Los colegios comparten los contadores de ID de la plantilla.** Entre 23 y 26
   tablas por tenant generan su `id` con `nextval('tenant_colegio_1.…')`. Los
   tenants están acoplados a un schema que además es un colegio operativo: si
   alguien borrara `tenant_colegio_1` o sus secuencias, **todas las altas de
   todos los colegios fallarían**. Las secuencias propias que sí tienen son las
   de tablas creadas por migraciones posteriores, ejecutadas dentro de cada
   schema.

Nada de esto se corrigió en 3.4a. Es un hallazgo, y su reparación toca datos
reales.

### El lock de 3.1 no funciona sobre el endpoint que usa producción

3.1 dejó anotado como no verificado si un advisory lock de sesión se sostiene
sobre PgBouncer. Se probó sobre la rama, en sus dos endpoints:

| Endpoint | Conexión 1 | Conexión 2 | Exclusión mutua |
|---|---|---|---|
| Directo | obtiene el lock | **no** lo obtiene | **Se sostiene** |
| Agrupado (`-pooler`) | obtiene el lock | **también** lo obtiene | **No se sostiene** |

Y el `DATABASE_URL` de `.env` apunta al endpoint **agrupado**. Es decir: tal
como está configurado hoy, **la protección que añadió 3.1 no impediría dos
ejecuciones simultáneas del runner**. El riesgo que se registró como hipótesis
resultó ser el caso real.

### Reclasificación: solo `tenant_2005` es producción real

El usuario aclaró después del ensayo que **de los cuatro schemas, únicamente
`tenant_2005` corresponde a un colegio en producción**. `tenant_colegio_1`
(«Colegio Demo»), `tenant_3333` y `tenant_4444` son demo o prueba, aunque los
cuatro figuren como `activo` en `public.colegios` y el runner los trate igual.

Esto no reduce la gravedad: la invierte. Antes parecía «tres colegios comparten
secuencias con la plantilla». Ahora se lee así: **el único colegio real toma 26
de sus contadores de ID de un schema de demostración**, y su integridad depende
de que nadie limpie esa demo.

#### Hallazgo crítico: 8 tablas de `tenant_2005` no pueden insertar hoy

Al medir el estado real de las secuencias compartidas frente a los datos de
`tenant_2005`, ocho de ellas ya están **por debajo** del máximo `id` existente.
Como esas columnas tienen `PRIMARY KEY`, el próximo `nextval` devuelve un valor
que ya existe y la inserción falla con clave duplicada:

| Tabla de `tenant_2005` | Próximo id | Máximo id existente | Filas |
|---|---:|---:|---:|
| `estudiantes` | 9 | 685 | 172 |
| `profesor` | 3 | 48 | 10 |
| `asignaciones` | 6 | 353 | 225 |
| `asistencia` | 2.571 | 3.125 | 2.481 |
| `notas_detalle` | 1.092 | 20.366 | 608 |
| `pagos` | 51 | 10.111 | 74 |
| `boletin_cabecera` | 36 | 99 | 3 |
| `boletin_detalles` | 56 | 313 | 4 |

Matricular un estudiante, registrar un profesor, crear una asignación, tomar
asistencia, guardar notas o registrar un pago falla con clave duplicada. Cada
intento consume un `nextval`, así que el contador avanza de uno en uno: para
`estudiantes` harían falta unos 676 intentos fallidos antes de que uno pase, y
para `notas_detalle` más de 19.000. En la práctica, esas operaciones están rotas.

La explicación más plausible es que los datos del colegio se cargaran con `id`
explícitos —una importación—, cosa que **no** avanza la secuencia. Como además
la secuencia vive en la demo, solo avanzó con el uso de la demo. Nada de esto
requiere que alguien se equivoque: es el estado actual.

Solo se leyeron agregados `MAX(id)` y `COUNT(*)`. No se consultó ningún dato
personal.

#### El arma cargada: `limpiar_tenant_colegio_1_operativo.py`

3.0 anotó ese script como indicio de tensión sin abrirlo. Abierto ahora, hace:

```sql
TRUNCATE tenant_colegio_1.<20 tablas> RESTART IDENTITY
```

`RESTART IDENTITY` reinicia las secuencias de esas tablas. **19 de las 26
secuencias que usa `tenant_2005` pertenecen a tablas de esa lista.** Ejecutar la
limpieza de la demo —una operación que parece inocua, tiene respaldo propio y
está pensada para no tocar nada importante— devolvería a 1 los contadores del
colegio real y agravaría la rotura ya existente.

Las 7 que se salvan son `cursos`, `materias`, `usuarios`,
`institucion_branding`, `plantilla_impresion`, `tipos_de_pagos` y
`tipos_pagos_cursos`, precisamente porque el script las preserva.

#### Riesgos reordenados por gravedad real

| # | Riesgo | Alcance | Estado |
|---:|---|---|---|
| 1 | 8 tablas de `tenant_2005` fallan al insertar por secuencias agotadas | **Producción, ahora** | Sin reparar |
| 2 | Limpiar la demo reiniciaría 19 contadores del colegio real | **Producción, un comando de distancia** | Sin reparar |
| 3 | `tenant_2005` tiene 11 claves foráneas de 37: sin integridad referencial | **Producción** | Sin reparar |
| 4 | El lock de 3.1 no se sostiene sobre `-pooler`, que es lo que usa `.env` | Operativo | Sin reparar |
| 5 | A `tenant_2005` le faltan 15 registros en `schema_migrations` | Registro, no estructura | Sin reparar |
| 6 | El alta creaba tenants sin historial | Futuro | **Corregido en 3.3b** |

Los riesgos 1 y 2 no son deuda técnica: son una avería en curso y un detonante
al alcance de la mano. El 3 puede haber permitido filas huérfanas en el colegio
real, lo que condiciona su propia reparación. El 5 es el menos grave pese a ser
el que motivó la capa: `tenant_2005` tiene las mismas 281 columnas y 89 índices
que la plantilla, así que **no está estructuralmente atrasado**; aplicarle esas
15 migraciones repetiría cambios ya presentes, y lo correcto es sembrar su
historial.

#### Consecuencia para el orden de la capa

La migración base deja de ser lo más urgente y se pospone a **3.4c**. Antes
está reparar el colegio real, que pasa a ser **3.4b**. La reparación mínima y correcta del riesgo 1 es la misma que
resuelve el 2: dar a `tenant_2005` **secuencias propias**, inicializadas en el
`MAX(id)` real de cada tabla, y reapuntar sus `DEFAULT` a ellas. Eso corta de
raíz el acoplamiento con la demo. No se ejecutó nada de esto en 3.4a.

## Subcapa 3.4b: resultado

Reparación de la avería del riesgo 1, que desactiva de paso el riesgo 2. Se
añadió `scripts/reparar_secuencias_tenant.py`: da a un tenant secuencias propias,
las posiciona en el `MAX(id)` real y reapunta sus `DEFAULT`. **No modifica
ningún archivo de producto existente**; el runner, `app/`, `migrations/`, el
workflow y las dependencias quedaron intactos.

**Nada se aplicó a producción.** El script quedó ensayado y listo; aplicarlo es
decisión y acción del usuario.

### Tres propiedades que lo hacen seguro

- **Auto-medido**: calcula `MAX(id)` en el instante de ejecutarse. No lleva
  ningún valor precalculado, así que los números que se midieron en la rama no
  viajan al script. Esto es deliberado: la rama es una foto y producción sigue
  moviéndose.
- **Transaccional de verdad, tras una corrección**: todo ocurre en una
  transacción y la verificación corre antes del `commit`; si encuentra un solo
  problema, revierte y devuelve 2 sin confirmar nada. La primera versión
  posicionaba las secuencias con `setval()` y eso **no** era reversible; ver
  «La objeción sobre `setval()`» más abajo.
- **Idempotente**: solo actúa sobre columnas cuyo `DEFAULT` apunta todavía a
  otro schema. Sobre un tenant ya reparado imprime «Nada que reparar» y sale 0.

Acepta `--schema`, porque los tres schemas de demo tienen el mismo defecto y
podrán repararse igual, y `--dry-run`, siguiendo la convención del runner.
Las secuencias nuevas heredan el tipo de su columna —`bigint` donde la columna
lo es— y quedan `OWNED BY` la columna, de modo que pertenecen al tenant y ya no
a la demo.

### La objeción sobre `setval()`

La primera versión posicionaba cada secuencia con `setval()`. El usuario
advirtió, antes de aplicar nada, que **`setval()` no es transaccional**: su
efecto sobrevive a un `ROLLBACK`, de modo que presentar el procedimiento como
completamente reversible era incorrecto.

Se comprobó directamente contra el servidor de la rama, PostgreSQL 17.10, con
una secuencia de juguete:

| Operación dentro de una transacción revertida | Valor antes | Dentro | Tras el `ROLLBACK` |
|---|---:|---:|---:|
| `setval(seq, 5000)` | 100 | 5000 | **5000** — no se revirtió |
| `ALTER SEQUENCE … RESTART WITH 9000` | 5000 | 9000 | **5000** — sí se revirtió |

La objeción era correcta. El script pasó a usar
`ALTER SEQUENCE … RESTART WITH <máximo + 1>`, que además elimina la rama
especial para tablas vacías: `RESTART WITH 1` deja el siguiente `nextval` en 1,
que es justo lo que se quiere. Se añadió una prueba de regresión,
`test_no_se_usa_setval_porque_no_es_transaccional`, para que nadie lo
reintroduzca sin darse cuenta.

### Ensayo completo sobre la rama

El primer ensayo solo comprobaba `DEFAULT`, ownership y colisiones. A petición
del usuario se repitió comparando también el **estado efectivo de cada
secuencia** —`last_value` e `is_called`— y añadiendo un fallo simulado a mitad
de la transacción:

| Paso | Resultado |
|---|---|
| 1. Estado roto de partida | 26 columnas prestadas, 4 secuencias propias |
| 2. **Fallo simulado** antes del `commit` | exit 2; estado **idéntico** al de partida |
| 3. `--dry-run` | exit 0; estado **idéntico** |
| 4. Aplicación real | 26 reparadas, verificación correcta, exit 0 |
| 5. Estado posterior | 0 prestadas, 30 secuencias propias |
| 6. Rollback | estado **idéntico** al de partida |
| 7. Reaplicación e idempotencia | 0 prestadas; segunda pasada, «Nada que reparar» |

«Idéntico» aquí significa comparación exacta de tres cosas: el `DEFAULT` de las
30 columnas, la lista de secuencias del tenant y el `last_value`/`is_called` de
**las 30 secuencias de la plantilla**. Esas últimas no cambiaron en ningún
momento del ciclo, que era el punto que la primera versión no verificaba.

El paso 2 es el que sostiene la afirmación de reversibilidad: un fallo antes del
`commit` no deja rastro, ni en los `DEFAULT`, ni en las secuencias creadas, ni
en el estado de las secuencias ajenas.

### Rollback

La reparación no borra datos ni altera filas: solo crea secuencias y cambia
`DEFAULT`. Para revertirla después de confirmada, por cada columna:

```sql
ALTER TABLE <tenant>.<tabla> ALTER COLUMN <columna>
    SET DEFAULT nextval('<plantilla>.<tabla>_<columna>_seq'::regclass);
DROP SEQUENCE IF EXISTS <tenant>.<tabla>_<columna>_seq;
```

El script imprime el `DEFAULT anterior` de cada columna antes de tocarla,
precisamente para que ese listado sirva de guion de reversión. **Conviene
guardar esa salida al aplicarlo.** Revertir reintroduce la avería, así que solo
tiene sentido si la reparación causara un problema inesperado.

Ese rollback posterior al `commit` es **manual**: hay que ejecutarlo. Lo que sí
es automático es el caso de fallo *durante* la ejecución, que no requiere
ninguna acción porque la transacción no llega a confirmarse; se verificó con un
fallo simulado.

Las secuencias creadas se destruyen al revertir, así que su estado no importa.
Las de la plantilla nunca se tocan, ni al aplicar ni al revertir: se comprobó
comparando `last_value` e `is_called` de las 30 antes y después del ciclo
completo.

### Verificación

| Comprobación | Resultado |
|---|---|
| `tests/test_reparar_secuencias_tenant.py` | **14 pasaron**, archivo nuevo |
| Transaccionalidad de `setval` vs `ALTER SEQUENCE` | Probada contra PostgreSQL 17.10 |
| Compuerta global | **Exit 0**: 543 pruebas, 5 warnings conocidos |
| Ruff del alcance | `All checks passed!` |
| Producto existente modificado | **ninguno**; solo se añadió un script |

La suite pasó de 529 a **543** pruebas.

### Estado de la rama tras el ensayo

`tenant_2005` en la rama quedó **reparado**: ya no reproduce el estado de
producción. Para un ensayo de última hora antes de aplicar, hay que **crear una
rama nueva**; esta ya no sirve como espejo del problema.

### Cómo aplicarlo a producción

1. Confirmar que nadie está usando la aplicación.
2. `python scripts/reparar_secuencias_tenant.py --schema tenant_2005 --dry-run`
   y revisar que las 26 columnas y sus máximos tengan sentido.
3. **Guardar esa salida**: contiene el guion de reversión.
4. `python scripts/reparar_secuencias_tenant.py --schema tenant_2005`.
5. Comprobar que termina con «Verificacion correcta» y exit 0. Si devuelve 2, no
   confirmó nada y hay que leer los problemas que enumera.
6. Probar una inserción real: matricular un estudiante de prueba y borrarlo.

Los tres schemas de demo pueden repararse después con el mismo comando; no
corren prisa, pero mientras compartan secuencias con `tenant_colegio_1` el
script de limpieza sigue siendo peligroso para ellos.

### Lo que 3.4b deliberadamente no hace

- No toma el advisory lock del runner. Sería teatro: 3.4a demostró que no se
  sostiene sobre el endpoint agrupado que usa `.env`. Es una reparación manual y
  de un solo uso, pensada para una ventana sin tráfico.
- No repara claves foráneas ni siembra historial: son los riesgos 3 y 5, cada
  uno con su propio ensayo.
- No cambia el alta de tenants. Los tenants nuevos seguirán naciendo con
  secuencias prestadas hasta que 3.5 rehaga el alta desde la migración base.

### Siguiente subcapa: 3.4c, trabajo exacto

Los hallazgos cambian lo que la migración base debe contener: ya no basta con
las tablas, tiene que traer las 37 claves foráneas, las 30 secuencias propias,
el disparador y la función que la copia actual nunca reproduce.

1. Confirmar `main`, árbol limpio y continuidad.
2. Con la rama disponible, extraer el DDL completo de `tenant_colegio_1`:
   tablas, columnas, defaults con secuencias **propias del schema destino**,
   `PRIMARY KEY`, `UNIQUE`, `CHECK`, **claves foráneas**, índices, el disparador
   y la función.
3. Escribirlo como una migración base nueva en `migrations/`, sin tocar ninguno
   de los 34 archivos existentes.
4. Verificar la equivalencia creando en la rama un schema de prueba desde esa
   migración y comparándolo contra la plantilla con el mismo método de 3.4a:
   columnas, índices y restricciones por definición normalizada. La diferencia
   admisible es cero.
5. Destruir el schema de prueba y comprobar que no quedan restos.
6. Ejecutar compuerta global, Ruff y `git diff --check`; actualizar esta
   bitácora y detenerse antes de 3.5.

## Subcapa 3.4c: resultado

Se añadió `migrations/base/20260813_esquema_base_tenant.sql`, **568 líneas**
extraídas del catálogo real de `tenant_colegio_1` y verificadas creando un
schema desde ese archivo y comparándolo contra la plantilla. **Ninguno de los 34
archivos existentes de `migrations/` cambió**, ni el runner, ni `app/`.

### Corrección: esta rama sí servía

La bitácora decía que 3.4c necesitaba una rama nueva. Era demasiado estricto: el
ensayo de 3.4b solo modificó `tenant_2005`, y lo que 3.4c necesita es la
**plantilla**, que quedó intacta —se comprobó comparando `last_value` de sus 30
secuencias antes y después—. Se reutilizó la misma rama.

### Cómo se extrajo

`pg_get_constraintdef` y `pg_get_functiondef` omiten el schema cuando el objeto
está en el `search_path`, así que el generador fija `search_path` a la plantilla
y obtiene SQL portable. `pg_get_indexdef` es la excepción: cualifica la tabla
siempre, y hubo que quitarle el prefijo.

Dos decisiones de forma:

- las columnas `id` se emiten como `SERIAL`/`BIGSERIAL` en lugar de copiar el
  `DEFAULT nextval(...)` original. Así cada schema crea su **propia** secuencia,
  que es exactamente el defecto que arrastraba el alta por copia y que 3.4b tuvo
  que reparar a mano;
- las claves foráneas van al final, en `ALTER TABLE … ADD CONSTRAINT`, para no
  depender del orden de creación de las tablas.

### Verificación de equivalencia

Aplicando el archivo del repositorio a un schema nuevo y comparándolo contra la
plantilla:

| | Plantilla | Generado | Faltan | Sobran |
|---|---:|---:|---:|---:|
| Columnas | 281 | 281 | 0 | 0 |
| Índices | 93 | 92 | 1 | 0 |
| Restricciones | 94 | 94 | 3 | 3 |
| Secuencias | 30 | 30 | — | — |
| Disparadores | 1 | 1 | — | — |
| Funciones | 1 | 1 | — | — |
| **Defaults apuntando a la plantilla** | 30 | **0** | — | — |

Ninguna columna difiere: mismas 281, mismos tipos, mismos defaults una vez
normalizado el nombre del schema. El schema de prueba se destruyó y se comprobó
que no quedan restos.

### Las dos diferencias, explicadas

**El índice que falta es una duplicación de la plantilla.** `profesor` tiene
allí *dos* restricciones `UNIQUE` idénticas sobre `documento_identidad`:
`profesor_documento_identidad_key` y `unique_documento_identidad`. La migración
declara ambas y PostgreSQL descarta la segunda por ser idéntica —comprobado—,
de modo que el schema nuevo tiene un índice único en vez de dos iguales. Es una
mejora, no una pérdida: mismo contrato, la mitad de coste de escritura.

**Las tres restricciones difieren solo en cómo se imprimen.** Son `CHECK` con
listas de valores: la plantilla las guarda como `ANY ((ARRAY[…])::text[])` y, al
recrearlas desde su propio texto, PostgreSQL las reescribe como
`ANY (ARRAY[(…)::text, …])`. Afectan a las mismas tablas y tienen la misma
semántica; es un artefacto de ida y vuelta del formateador.

Es decir: la equivalencia **no es byte a byte**, y no debe presentarse como tal.
Es equivalencia de contrato, con una duplicación eliminada a propósito.

### Por qué `migrations/base/` y no `migrations/`

Si el archivo viviera en `migrations/`, `scripts/auditar_migraciones_tenants.py`
lo contaría como una migración más y reportaría a los cuatro tenants como si les
faltara, cuando ya tienen esas tablas. En `migrations/base/` queda fuera de ese
corpus —comprobado: la auditoría sigue viendo 30— y sigue siendo aplicable
explícitamente al dar de alta un tenant. El runner nunca lo aplicará por su
cuenta: recibe un archivo por invocación y no descubre nada.

### Lo que no cubre

El archivo reproduce la **estructura**, no los datos semilla. El alta actual
inserta además una fila de `institucion_branding`, copia las
`plantilla_impresion` predefinidas y crea el admin inicial. Eso es trabajo de
3.5, que decidirá qué parte de esa siembra pertenece a la migración base y cuál
al alta.

### Siguiente subcapa: 3.5, trabajo exacto

1. Confirmar `main`, árbol limpio y continuidad.
2. Sustituir en `crear_tenant_controller` el bloque `DO $$` con
   `LIKE INCLUDING ALL` por la aplicación de
   `migrations/base/20260813_esquema_base_tenant.sql` sobre el schema nuevo.
3. Decidir y documentar qué ocurre con la siembra: `institucion_branding`,
   `plantilla_impresion` predefinidas y admin inicial siguen en el controller
   salvo que haya motivo para moverlas.
4. Revisar qué debe sembrarse en `public.schema_migrations`: con una base
   versionada, copiar las filas de la plantilla como hace 3.3b puede dejar de
   ser lo correcto.
5. Ampliar `tests/test_tenant_provisioning.py` para fijar el camino nuevo.
6. Ensayar en una rama: dar de alta un tenant por el camino nuevo y compararlo
   contra la plantilla y contra uno dado de alta por el camino viejo.
7. Compuerta global, Ruff, `git diff --check`; actualizar esta bitácora y
   detenerse antes de 3.6.

## Subcapa 3.4d: guarda del endpoint agrupado

3.4a demostró que el advisory lock de 3.1 no se sostiene sobre PgBouncer y que
`.env` apunta justo a ese endpoint: la protección existía pero no protegía.

`apply_migration.py` gana `es_endpoint_agrupado()` y se niega a ejecutarse
—**exit 1, antes de conectar**— cuando el host del DSN contiene `-pooler`. Se
clasifica como error de configuración, no como fallo de migración, porque no se
intentó nada. Cuatro pruebas nuevas: detección por host, que no se confunda con
un `-pooler` que aparezca en el nombre de la base o en los parámetros, el
rechazo sin conectar y que el endpoint directo sí funcione.

Verificado además contra el `.env` real: el runner imprime el motivo y sale con
1 sin abrir conexión.

**Consecuencia operativa que hay que tener presente**: con la configuración
actual, `apply_migration.py` ya no se puede ejecutar. Para aplicar una migración
habrá que usar el endpoint directo. Es el efecto buscado —antes se ejecutaba sin
protección real—, pero es un cambio en una herramienta operativa.

No se añadió la guarda a la auditoría de 3.3a ni al reparador de secuencias: son
de solo lectura la primera y transaccional sin locks el segundo, y ambos
funcionan correctamente sobre el pooler.

## Subcapa 3.4e: siembra del historial

`scripts/sembrar_historial_tenant.py` copia al tenant los registros de
`public.schema_migrations` que la plantilla tiene y a él le faltan. No aplica
ninguna migración: solo escribe historial.

### No es un acto de fe

Antes de sembrar, el script **comprueba que el destino reproduce la estructura
de la plantilla** en columnas e índices, y se niega si no. Sembrar sin esa
comprobación afirmaría algo que podría ser falso.

Las claves foráneas se excluyen de la comparación a propósito: su ausencia viene
de la copia con `LIKE INCLUDING ALL`, que no las reproduce, no de una migración
sin aplicar. Está fijado con una prueba.

### Un falso positivo que obligó a corregir la comprobación

La primera versión comparaba la definición completa del índice, nombre incluido,
y **se negó a sembrar** alegando 32 diferencias. Investigado contra producción,
resultó ser cosmético: la plantilla nombra sus índices `idx_cursos_estado` y el
tenant los llama `cursos_estado_idx` —el nombre que PostgreSQL genera solo—.
Comparando por **función** —tabla, unicidad, columnas y condición— las
diferencias son **cero**.

La comprobación pasó a comparar por función y a ignorar el nombre, con dos
pruebas que lo fijan. Lo que una migración aporta es el índice, no cómo se
llama.

### Hallazgo colateral: 13 índices duplicados en `tenant_2005`

Al investigar lo anterior salió que `tenant_2005` tiene **106 índices frente a
los 93 de la plantilla**, y que ninguno aporta una función nueva: son 13
duplicados exactos bajo otro nombre. Cuestan escritura y espacio sin dar nada.
No se tocan aquí; queda anotado como limpieza posible.

### Ensayo y verificación

Ensayado en la rama sobre `tenant_2005`: `--dry-run` sin efectos; siembra real
que llevó los registros de **15 a 30**; el informe de 3.3a pasó de
`PENDIENTE … faltan 15` a **`OK`**; y una segunda ejecución informó «Nada que
sembrar». Once pruebas herméticas nuevas.

`--dry-run` contra producción: las mismas 15 migraciones, comprobación
estructural **sin diferencias**, nada escrito. Coincide con el ensayo.

**No se ha aplicado a producción.** Queda a la espera de la orden del usuario.

### Por qué sembrar y no ejecutar las migraciones

Se comprobó contra producción, migración por migración, que ninguna de las 15
cambiaría la estructura —ya está— y que de las diez que rellenan datos, nueve
tocarían **cero filas**. La única que cambiaría algo es
`20260527_pagos_anulacion`, que pondría `estado = 'Pagado'` en 73 de los 74
pagos que hoy lo tienen nulo. Es inocuo: la aplicación nunca lee ese campo en
crudo, usa `COALESCE(estado, 'Pagado')` en los cinco sitios que importan. La
prueba de que es deliberado: la propia plantilla, con las 30 migraciones
registradas, también tiene 12 pagos con `estado` nulo.

Ejecutar el runner además alcanzaría a los cuatro tenants, porque el
descubrimiento no distingue producción de demo.

## Subcapa 3.4f: reposición de claves foráneas

`scripts/reponer_claves_foraneas_tenant.py` copia al tenant las claves foráneas
que la plantilla tiene y a él le faltan, conservando `ON DELETE` y `ON UPDATE`.
Cuenta huérfanos antes y se niega si encuentra alguno.

### El error que casi introduce un acoplamiento entre schemas

Merece quedar escrito porque el ensayo lo cazó por casualidad.

`pg_get_constraintdef` devuelve la definición **sin cualificar**:
`FOREIGN KEY (curso_id) REFERENCES cursos(id)`. La primera versión leía las
definiciones con el `search_path` en la plantilla —correcto, para obtener ese
texto portable— pero **no lo cambiaba antes de crear**. PostgreSQL resolvía
`cursos` con el `search_path` vigente, de modo que iba a crear una clave desde
`tenant_2005.asignaciones` hacia **`tenant_colegio_1.cursos`**: exactamente el
acoplamiento entre schemas que 3.4b acababa de eliminar de las secuencias.

Falló con `ForeignKeyViolation` sobre `curso_id=33`, un curso que el colegio
real tiene y la demo no. **Si los identificadores hubieran coincidido, la clave
se habría creado en silencio apuntando al schema equivocado.**

Lo que delató el fallo fue la contradicción entre el recuento —0 huérfanos, con
nombres cualificados, correcto— y la violación al crear. Se comprobó en las dos
bases que el recuento era bueno antes de tocar el script.

Correcciones: se fija el `search_path` **al destino** antes de crear, y se añadió
`claves_que_apuntan_fuera()`, que tras crearlas verifica que ninguna referencia
salga del schema y revierte si alguna lo hace. Con su prueba, que documenta el
error real para que no vuelva.

### Ensayo

Sobre la rama: 11 → **37** claves, 26 → **0** ausentes, idempotente. Y dos
demostraciones funcionales en transacciones revertidas:

- **la cascada actúa**: borrar un `boletin_cabecera` se llevó sus 4 detalles;
- **lo que antes dejaba huérfanos ahora se bloquea**: borrar un curso con 28
  asignaciones falla con `23503`. Antes habría pasado sin más.

`--dry-run` contra producción: las 26 claves, todas **sin huérfanos**, nada
creado.

### Aplicado a producción

`>> Creadas 26 clave(s) foranea(s) en tenant_2005`, exit 0. Verificación
posterior, solo de catálogo:

| Comprobación | Resultado |
|---|---|
| Restricciones por tipo frente a la plantilla | `CHECK=15 FK=37 PK=30 UNIQUE=13` en ambos, **idénticas** |
| Claves que apuntan fuera del schema | **0** |
| Claves sin validar | **0** |
| Ausentes frente a la plantilla | **0** |
| Reparto `ON DELETE` | 16 `NO ACTION`, 16 `CASCADE`, 5 `SET NULL` |

Que las 37 estén **validadas** es una confirmación independiente de que no hay
huérfanos: PostgreSQL las comprobó contra los datos reales al crearlas. Ya no
depende de mi recuento.

No se hizo ninguna prueba de borrado sobre producción, ni siquiera revertida: el
comportamiento quedó demostrado sobre la rama, que tiene los mismos datos.

### Cambio de comportamiento declarado

Un `DELETE` físico que antes pasaba dejando huérfanos ahora falla. Es el
objetivo, y deja `tenant_2005` comportándose igual que la plantilla. La
aplicación no se ve afectada porque usa borrado lógico en todas partes —
`activo`, `estado`, `anulado`— y varios de sus endpoints `DELETE` devuelven 405.
Pero un script que borre directamente por SQL empezará a encontrar errores donde
antes no los había.

### Rollback

`ALTER TABLE <tabla> DROP CONSTRAINT <nombre>` para las 26. El `--dry-run`
imprime tabla, columnas y nombre de cada una. Revertir devuelve el schema a no
tener integridad referencial, así que solo procede ante un problema concreto.

## Subcapa 3.5: alta reproducible

`crear_tenant_controller` deja de copiar la plantilla con `LIKE INCLUDING ALL` y
aplica `migrations/base/20260813_esquema_base_tenant.sql` sobre el schema nuevo.
El diff de producto son **24 líneas añadidas y 25 eliminadas** en un solo
archivo: el bloque `DO $$` desaparece y en su lugar quedan un `SET LOCAL
search_path` y la ejecución del archivo.

### La trampa del `search_path`, ahora en el camino del alta

Es la misma que reventó en 3.4f. El archivo usa nombres sin cualificar, así que
sus `REFERENCES` se resuelven con el `search_path` vigente. Si la plantilla
estuviera en el camino, las claves foráneas del tenant nuevo naceran apuntando a
sus tablas.

Por eso se fija `SET LOCAL search_path TO <schema_nuevo>` —**solo** el schema
nuevo, sin `public`— antes de aplicar el archivo. `SET LOCAL` y no `SET` porque
la conexión vuelve a un pool y el ámbito debe morir con la transacción.

Hay una prueba dedicada que comprueba que el último `search_path` fijado antes
de aplicar la base nombra el schema nuevo y **no** el de la plantilla.

### Decisiones sobre la siembra

- **Los datos semilla siguen en el controller**: la fila de
  `institucion_branding`, la copia de las `plantilla_impresion` predefinidas y
  el admin inicial. La migración base describe estructura; mezclar datos de
  arranque dentro de ella la haría inaplicable a un tenant existente y ataría el
  esquema a un contenido concreto.
- **El historial se sigue copiando de la plantilla**, como dejó 3.3b. Con una
  base versionada podría parecer más natural leer el directorio `migrations/`,
  pero eso supondría que el directorio y la base están sincronizados, que es
  justo lo que no se puede afirmar.

### Riesgo que esta subcapa introduce y no resuelve

La migración base y el directorio `migrations/` no están enlazados por nada.
**Si alguien añade una migración nueva, la aplica a la plantilla y no regenera
el archivo base, un tenant nuevo nacerá con la estructura antigua pero con el
historial de la plantilla**: dirá tener una migración que no tiene.

No se construyó la guarda en esta subcapa para no ampliar el alcance. La
comprobación que la detectaría ya existe y está probada:
`diferencias_estructurales()` en `scripts/sembrar_historial_tenant.py`. Queda
como trabajo pendiente decidir si el alta debe verificarse contra la plantilla
antes de sembrar, o si conviene que la propia migración base declare qué
migraciones incorpora.

### Ensayo sobre la rama

Se dio de alta un tenant real por el camino nuevo y se comparó con la plantilla:

| | Plantilla | Tenant nuevo | Faltan | Sobran |
|---|---:|---:|---:|---:|
| Columnas | 281 | 281 | 0 | 0 |
| Índices | 89 | 89 | 0 | 0 |
| Restricciones | 94 | 94 | 3 | 3 |
| **Claves foráneas** | 37 | **37** | — | — |
| **Secuencias propias** | 30 | **30** | — | — |
| Disparadores | 1 | 1 | — | — |

Ninguna columna difiere. Las 3 restricciones son las mismas `CHECK` que 3.4c ya
explicó: se reimprimen con otra forma equivalente.

Y las dos comprobaciones que importan:

- **claves que apuntan fuera del schema nuevo: 0**;
- **defaults que apuntan a la plantilla: 0**.

El camino viejo producía **0 claves foráneas y 0 secuencias propias**. El nuevo
produce 37 y 30. Ese es el resultado de la capa.

La siembra siguió intacta: 1 fila de branding, 18 plantillas predefinidas, 1
usuario admin, y 30 migraciones registradas. El schema de prueba y sus filas en
`public` se eliminaron al terminar.

### Verificación

Compuerta global en **exit 0 con 570 pruebas**, Ruff correcto, ningún archivo de
`migrations/` modificado y el diff limitado a un controller y sus pruebas.

## Subcapa 3.6: resultado y cierre

### Estado de producción al cerrar

| Schema | Papel | Claves foráneas | Secuencias | Ajenas | Migraciones |
|---|---|---:|---:|---:|---:|
| `tenant_2005` | **Producción** | **37** | **30** | **0** | **30** |
| `tenant_colegio_1` | Plantilla y demo | 37 | 30 | 0 | 30 |
| `tenant_3333` | Demo | 14 | 7 | 23 | 30 |
| `tenant_4444` | Demo | 11 | 4 | 26 | 21 |

El único colegio real iguala a la plantilla en todo. Los dos demos conservan los
tres defectos originales.

### Qué cambió en producción

Tres reparaciones, cada una con su `--dry-run` revisado antes de aplicarla:

1. **3.4b**: 26 columnas de `tenant_2005` pasaron a usar secuencias propias
   posicionadas en su `MAX(id)`. Desbloqueó ocho tablas que no admitían
   inserciones.
2. **3.4e**: 15 registros de historial sembrados. El informe de 3.3a da el
   tenant como `OK`.
3. **3.4f**: 26 claves foráneas repuestas y validadas contra los datos.

Es la única vez en todo el programa que se modificó la base real, y solo con
autorización explícita para cada paso.

### Rollback

A diferencia de las capas anteriores, aquí el rollback no es solo de aplicación.
Hay dos planos y se revierten en orden inverso.

**Plano de código**, si hubiera que volver atrás:

1. revertir los commits de la capa hasta `81882f3`;
2. el alta vuelve a copiar la plantilla con `LIKE INCLUDING ALL` y los tenants
   nuevos vuelven a nacer sin claves foráneas ni secuencias propias;
3. `apply_migration.py` vuelve a admitir el endpoint agrupado, donde su lock no
   sirve.

**Plano de datos**, cada reparación por separado y solo ante un problema
concreto:

- claves foráneas: `ALTER TABLE <tabla> DROP CONSTRAINT <nombre>` para las 26.
  El `--dry-run` de `reponer_claves_foraneas_tenant.py` las lista;
- historial: `DELETE FROM public.schema_migrations WHERE target_schema =
  'tenant_2005' AND migration_name IN (…las 15…)`;
- secuencias: devolver los 26 `DEFAULT` a las secuencias de la plantilla y
  `DROP SEQUENCE` las creadas. El `--dry-run` de
  `reparar_secuencias_tenant.py` imprime el `DEFAULT anterior` de cada columna,
  y esa salida es el guion.

Revertir cualquiera de las tres **reintroduce el defecto que reparó**. La de
secuencias, además, devolvería al colegio a no poder insertar. Solo tienen
sentido ante un problema causado por la propia reparación.

Ninguna de las tres borra ni transforma datos del colegio: cambian metadatos de
esquema y registros de historial.

### Staging

No se usó un entorno de staging convencional. Se usó una **rama de Neon creada
desde producción**, que resultó mejor para este trabajo: contiene la estructura
y los datos reales, y es desechable. Todo lo que se aplicó a producción se
ejecutó antes ahí, con el ciclo completo incluido el rollback.

Para repetirlo en el futuro: crear una rama, apuntar `DATABASE_URL` a su
endpoint **directo** —no el `-pooler`—, ejecutar el `--dry-run`, aplicar,
verificar, y destruir la rama al terminar.

### Verificación manual

**Hecha por el usuario el 2026-08-13, con resultado correcto.** Lo informó tras
ejercitar la aplicación contra la base ya reparada. No se detalla aquí qué
pantallas recorrió, así que conviene leerlo como «el sistema respondió bien en
uso normal», no como una comprobación exhaustiva punto por punto.

La verificación automatizada que sí consta es de catálogo, más una inserción
controlada revertida que devolvió el id 686 en `estudiantes` y el 49 en
`profesor`.

Lista que se propuso comprobar:

- matricular un estudiante y que reciba un id por encima de 685;
- registrar un profesor, una asignación, asistencia, notas y un pago: las seis
  operaciones que estaban bloqueadas;
- que un intento de borrado que antes pasaba en silencio ahora falle donde debe;
- que el alta de un colegio nuevo funcione de extremo a extremo por el camino de
  3.5, cosa que se ensayó en la rama pero no en producción;
- que los reportes y el estado de cuenta sigan mostrando los mismos importes.

### Criterios de cierre: estado real

Se cumplen todos menos uno, y ese se declara en vez de darse por bueno:

| Criterio | Estado |
|---|---|
| Subcapas cerradas | Cumplido: 3.0 a 3.6 |
| Tenants del alcance versionados y verificables | **Parcial**: `tenant_2005` sí; `tenant_4444` sigue con 21 de 30 |
| Runner protegido contra ejecuciones simultáneas | Cumplido, con matiz: el lock funciona en el endpoint directo y el runner se niega sobre el agrupado |
| Alta reproducible y equivalente | Cumplido y ensayado |
| Contratos, permisos, tenant y SQL conservados | Cumplido |
| Ensayo fuera de producción | Cumplido, sobre una rama de Neon |
| Staging, rollback y verificación manual documentados | Cumplido |
| Compuerta global, Ruff, dependencias, `git diff --check` | Cumplido |
| Capa 4 en espera | Cumplido |

**El criterio parcial es deliberado y necesita una decisión.** `tenant_3333` y
`tenant_4444` son demo: conservan secuencias prestadas, faltan claves foráneas y
a uno le falta historial. Repararlos es un comando por script y por schema, con
las herramientas ya ensayadas. La capa se cierra con ese punto **abierto y
registrado**, no resuelto por inferencia.

### Riesgos que quedan abiertos

- Los dos schemas demo conservan los tres defectos. Mientras compartan
  secuencias con `tenant_colegio_1`, el script de limpieza de la demo sigue
  siendo peligroso **para ellos**.
- La migración base y `migrations/` no están enlazados: añadir una migración sin
  regenerar la base haría que un tenant nuevo declarara tener algo que no tiene.
- `apply_migration.py` ya no arranca con el `.env` actual. Es lo buscado, pero
  cambia una herramienta operativa.
- `tenant_2005` tiene 13 índices duplicados, sin función nueva.
- La calibración de `DB_STATEMENT_TIMEOUT_MS` sigue pendiente desde la capa 1.
- GitHub Actions no se ha verificado en ningún momento del programa desde la
  capa 0.
- La rama de Neon sigue viva y su credencial probablemente sirva también contra
  producción, porque las ramas heredan el rol del padre.

## Mantenimiento posterior al cierre — 2026-08-13

### Eliminación de los dos schemas demo

Tras cerrar la capa, el usuario decidió **eliminar `tenant_3333` y
`tenant_4444`** en lugar de repararlos. Ambos eran demo; sus datos no tenían
valor y arrastraban los tres defectos originales. `tenant_3333` tenía además 27
filas huérfanas —hijas de asignaciones borradas—, que son la demostración
concreta de lo que permite la ausencia de claves foráneas.

Antes de tocar nada se comprobó que **nada fuera de esos schemas dependía de
ellos**: 0 claves foráneas apuntándoles, 0 defaults usando sus secuencias, 0
vistas y 0 funciones mencionándolos.

La operación se hizo desde un script puntual del scratchpad, **no** añadiendo
una herramienta de borrado al repositorio: la capa estaba cerrada y no procede
dejar disponible algo así. Sus protecciones: lista blanca cerrada con los dos
nombres, lista negra explícita para `tenant_2005`, `tenant_colegio_1` y
`public`, exigencia de que el schema estuviera registrado en `public.colegios`,
todo en una transacción, y una verificación **dentro** de esa transacción que
revierte si los dos intocables no siguen presentes al terminar.

Se borraron los dos schemas y sus filas asociadas: 2 en `colegios`, 51 en
`schema_migrations`, 1 en `tenant_suscripciones`, 1 en
`tenant_eventos_auditoria` y 2 en `tenant_estado_auditoria`.

Ensayo previo en la rama: el ciclo completo, y después un alta de tenant nuevo
que salió correcta —281 columnas, 37 claves, 30 secuencias—, comprobando que
eliminar los demos no rompe el aprovisionamiento, que ya no depende de ellos.

**No consta que se hiciera copia de seguridad previa.** Se recomendó crear una
rama de Neon antes de ejecutar; el usuario ordenó aplicar sin confirmarla. Los
datos borrados no son recuperables desde la base.

### Estado de producción resultante

| Schema | Papel | Claves foráneas | Secuencias | Prestadas | Migraciones |
|---|---|---:|---:|---:|---:|
| `tenant_2005` | Producción | 37 | 30 | 0 | 30 |
| `tenant_colegio_1` | Plantilla y demo | 37 | 30 | 0 | 30 |

`scripts/auditar_migraciones_tenants.py` terminó por primera vez con
**«Auditoria finalizada: todos los destinos al dia»** y exit 0.

### Efecto sobre los criterios de cierre

El criterio que quedó **parcial** al cerrar la capa —«todos los tenants del
alcance versionados y verificables»— queda **cumplido**, por eliminación de los
tenants incompletos en vez de por reparación. Es una resolución legítima y se
registra como tal, no como si se hubieran reparado.

Con ello, el punto abierto nº 1 de la entrega desaparece. Siguen abiertos el
enlace entre la migración base y `migrations/`, la verificación manual, los 13
índices duplicados y la limpieza de la rama de Neon.

### Enlace entre la migración base y `migrations/`

El punto abierto nº 2 quedó resuelto el 2026-08-13, también tras el cierre.

El problema: el esquema de un tenant estaba descrito en dos sitios que no se
hablaban. Añadir una migración y olvidar regenerar la base habría hecho que los
colegios nuevos nacieran con la estructura vieja **y el historial nuevo**,
declarando tener algo que no tienen. Silencioso hasta que una consulta usara lo
que falta.

Se añadieron dos piezas, ninguna toca producción ni la base de datos:

- **`scripts/generar_esquema_base.py`**: regenera el archivo base leyendo la
  estructura real de un schema. Es de solo lectura sobre la base —`READ ONLY` y
  `rollback`—; lo único que escribe es el `.sql`. Sin esta herramienta el paso
  de «actualizar la base» era editar a mano 568 líneas, que es tanto como decir
  que no se haría.
- **`tests/test_esquema_base.py`**: cinco pruebas que comparan las migraciones
  que el archivo base **declara incorporar** —una lista en su cabecera, generada
  automáticamente desde `public.schema_migrations`— con las que hay en
  `migrations/`. Si falta alguna, la compuerta falla y el mensaje dice qué
  comando ejecutar.

Se comprobó que la guarda sirve: al añadir un `.sql` de prueba a `migrations/`
sin regenerar la base, la compuerta falló señalando el archivo por su nombre.
Retirado el archivo, volvió a pasar.

La regeneración es **idempotente**: ejecutarla dos veces seguidas informa «sin
cambios respecto al anterior». Al regenerar desde producción, el SQL resultó
idéntico byte a byte al que se había generado desde la rama; lo único que cambió
fue la cabecera nueva.

El flujo completo quedó escrito en `docs/MIGRACIONES.md`, sección «Añadir una
migración nueva», con los seis pasos, el orden entre aplicar y regenerar, y la
advertencia de que el runner exige el endpoint directo.

### Limpieza final y cierre del trabajo

**Rama de ensayo: eliminada** por el usuario el 2026-08-14. Cumplió su función:
sobre ella se ensayaron las tres reparaciones aplicadas a producción, el
borrado de los demos y el alta por el camino nuevo. Borrarla no afecta a
producción; las ramas de Neon son independientes de su madre.

Con la rama fuera, ya no hay dónde ensayar cambios sobre datos reales. **Si
hiciera falta otro ensayo, hay que crear una rama nueva**, que es instantáneo.

**Índices duplicados: no se tocan.** `tenant_2005` conserva 14 índices
redundantes —misma tabla, mismas columnas, misma unicidad, otro nombre—. Se
midieron uno a uno y se comprobó que ninguno respalda una restricción, así que
borrarlos sería seguro y reversible. Se decidió **no hacerlo**: sobre tablas de
como mucho 20.000 filas el ahorro es marginal, y no compensa una operación más
sobre producción ni crear una rama solo para ensayarla.

Queda registrado como limpieza cosmética disponible, no como defecto. Los 14
nombres están en el registro de ejecución de esta fecha; el criterio para
elegir cuál conservar de cada grupo es indiferente al rendimiento, lo único que
importa es que sobreviva exactamente uno y que ninguno respalde una restricción.

**Credencial de producción: verificada el 2026-08-14.** Al intentar conectar a
la rama tras su borrado, la autenticación falló, lo que abrió la duda de si se
había rotado también la contraseña del rol `neondb_owner`, compartido entre
ramas y producción. El usuario comprobó que **puede iniciar sesión en los dos
tenants**, así que la `DATABASE_URL` de `.env` sigue siendo válida y no hay nada
que actualizar. El fallo era propio de la rama eliminada.

Ese inicio de sesión sirve además como verificación adicional: los dos schemas
que quedan funcionan a través de la aplicación después de todas las
reparaciones.

### Reparaciones identificadas en 3.4a: estado final

La lista se escribió durante 3.4a. Al cerrar el mantenimiento posterior, todos
los defectos quedaron resueltos para los schemas conservados; los dos demos
incompletos se eliminaron por decisión del usuario.

- **Secuencias compartidas.** *Resuelta en 3.4b y **aplicada a producción** el
  2026-08-13* con `scripts/reparar_secuencias_tenant.py`. `tenant_2005` tiene
  ya sus 30 secuencias propias y las ocho tablas bloqueadas vuelven a insertar.
  Los demos defectuosos se eliminaron; no queda ningún schema conservado usando
  secuencias prestadas.
- **Runner sobre endpoint agrupado.** *Resuelto en 3.4d.*
  `apply_migration.py` se niega a ejecutarse contra un DSN con `-pooler` y exige
  el endpoint directo, donde el lock sí se sostiene.
- **Historial faltante de `tenant_2005` y `tenant_4444`.** *Resuelto.* El
  historial de `tenant_2005` se sembró en 3.4e; `tenant_4444` se eliminó por ser
  demo. La auditoría final termina en exit 0.
- **Claves foráneas ausentes.** *Resuelta en 3.4f y **aplicada a producción** el
  2026-08-13.* Las 26 se repusieron en `tenant_2005` y quedaron validadas. Los
  demos incompletos se eliminaron.

## Criterios de cierre de la subcapa 3.0

- El mecanismo actual de migraciones y de alta de tenants está descrito con
  evidencia citada, no supuesto.
- El criterio de tenant reactivable está definido y aplicado a un inventario
  concreto.
- Los contratos que la capa debe conservar están enumerados.
- Existe una estrategia de prueba capaz de detectar una migración no aplicada,
  una aplicación doble y una divergencia entre schemas.
- Existe un procedimiento de ensayo no productivo y una forma de rollback de
  esquema.
- La compuerta heredada y `git diff --check` terminan correctamente.
- El diff contiene exclusivamente esta bitácora y no se inició 3.1.

## Criterios de cierre de la capa

- Todas las subcapas necesarias están cerradas o marcadas `No aplica` con
  justificación.
- Todos los tenants incluidos en el alcance están versionados y verificables.
- El runner no puede ejecutarse dos veces en paralelo y esa protección está
  probada.
- El alta de un tenant se reproduce desde migraciones versionadas y su resultado
  es equivalente al camino anterior.
- Los contratos HTTP, permisos, tenant, ownership, SQL de dominio y
  transacciones permanecen conservados.
- Existe evidencia de un ensayo en base de prueba o staging, sin usar
  producción.
- Staging, rollback de esquema y verificación manual están documentados.
- La compuerta global, Ruff, dependencias y `git diff --check` terminan
  correctamente.
- La capa 4 queda en espera y no se activa sin orden explícita del usuario.

## Decisiones

- La capa se activa con `81882f3b1ee9e3b50076b0fc1fd93dcd9fd5ac70` como base
  porque es el `HEAD` limpio vigente y coincide con la referencia local
  `origin/main`. No se reutiliza el base de la capa 2 ni se asume el commit de
  cierre `8c3939a`, que quedó por detrás tras la publicación documental del
  relevo.
- La activación crea solo esta bitácora y actualiza el índice. No inspecciona ni
  modifica código, migraciones, esquemas o pruebas, conforme a la autorización
  explícita de detenerse antes de 3.0.
- 3.0 es una subcapa de inventario y caracterización. Elegir un mecanismo de
  bloqueo, un formato de versionado o una estrategia de alta antes de conocer el
  estado real fijaría una solución sin evidencia, como ya ocurrió y se evitó en
  la capa 2.
- El desglose posterior a 3.0 se registra como provisional en lugar de omitirlo,
  para que el índice tenga una forma esperada de la capa sin que ese esquema se
  confunda con un inventario verificado.
- La calibración de `DB_STATEMENT_TIMEOUT_MS` se mantiene registrada como
  verificación operativa pendiente de la capa 1 por decisión explícita del
  usuario al activar esta capa. No se da por cumplida ni se traslada al alcance
  de la capa 3.
- No se registra ningún resultado de GitHub Actions. El `HEAD` coincide con la
  referencia local `origin/main`, pero eso no es evidencia de un run; no hay
  cliente de GitHub disponible en este checkout para obtenerla.
- La autorización de uso inmediato que `PROMPT_CONTINUACION.md` guardaba para
  activar la capa 3 se retiró del archivo en el mismo turno que 3.0, por orden
  explícita y separada del usuario. Es un cambio documental **ajeno al alcance
  de 3.0** y se declara como tal para que el diff no se lea como parte del
  inventario. El motivo es que el propio texto decía no reutilizarse tras un
  cambio de estado, pero seguía siendo copiable y habría intentado recrear una
  bitácora existente con un commit base equivocado. Se descartó dejarlo con una
  nota de caducidad porque un lector apurado copia el bloque, no la advertencia.
- 3.0 no midió el estado real de versionado por tenant ni verificó el
  comportamiento de `LIKE ... INCLUDING ALL`. Se prefirió dejarlo explícitamente
  como no medido antes que deducirlo de la documentación existente, que describe
  el estado productivo a una fecha pasada y no puede confirmar el actual.

## Riesgos

- Es la primera capa del programa que puede tocar esquema y datos. Las capas 0 a
  2 tenían un rollback exclusivamente de aplicación; aquí un error puede dejar
  un schema a medias, por lo que el rollback debe diseñarse antes de cambiar
  nada y ensayarse fuera de producción.
- Una migración aplicada a un subconjunto de tenants produce divergencia
  silenciosa entre schemas. El inventario debe poder detectarla, no suponer que
  todos están al día.
- Sin bloqueo, dos ejecuciones simultáneas del runner pueden competir por el
  mismo schema. El propio índice señala esa protección como resultado de la
  capa, de modo que debe tratarse como carencia probable hasta que 3.0 lo
  confirme con evidencia.
- Un alta basada en migraciones puede no reproducir exactamente lo que produce
  hoy la copia de un tenant plantilla, incluidos objetos, permisos o datos
  semilla. La equivalencia debe demostrarse por comparación, no por confianza.
- Si esta capa introduce un consumidor de conexiones fuera del camino HTTP
  —runner, script o job en background—, la invariante `H=2`, `R=0` y el
  limitador de cinco workers derivados en la capa 2 dejan de estar justificados
  y deben reauditarse antes de desplegar.
- `DB_STATEMENT_TIMEOUT_MS` sigue sin calibrarse y permanece aceptado como
  pendiente. **3.0 corrigió el supuesto con que se activó esta capa**: los cinco
  scripts de migración abren su propia conexión con
  `psycopg2.connect(DATABASE_URL)` y no pasan por `app/database.py`, así que los
  timeouts por transacción de la capa 1 **no** se aplican a una migración. El
  riesgo real es el inverso al que se registró al activar: una migración larga
  no tiene límite de tiempo ni de espera de lock y puede bloquear tablas que la
  aplicación está sirviendo.
- Cuatro scripts ad-hoc en `scripts/` aplican DDL a los mismos tenants sin
  registrar nada en `public.schema_migrations`. Cualquier verificación de «al
  día» construida solo sobre esa tabla será ciega a lo que ellos hicieron.
- El alta crea schemas sin sembrar historial, de modo que la población de
  tenants está dividida en dos clases que el runner no distingue. Corregirlo
  sembrando el historial retroactivamente es una escritura sobre datos reales y
  necesita ensayo y rollback propios.
- El checksum es sensible al byte. Un archivo de `migrations/` reformateado, o
  convertido de LF a CRLF, cambia su checksum y convierte un `OMITIDA` en un
  `FALLO` para todos los tenants que ya lo tenían aplicado. Ninguna subcapa debe
  tocar los archivos existentes de `migrations/`.
- El lock añadido en 3.1 **solo protege `apply_migration.py`**. Los cuatro
  scripts ad-hoc siguen sin pedirlo, así que uno de ellos puede correr en
  paralelo con el runner y chocar sobre el mismo tenant. Extender el lock a esos
  scripts o retirarlos es una decisión pendiente; ninguna subcapa la ha tomado
  y no debe presentarse la exclusión mutua como completa.
- **Confirmado en 3.4a y mitigado en 3.4d**: el advisory lock de sesión no se
  sostiene sobre el endpoint agrupado, y `.env` apunta precisamente a él. Dos
  conexiones al `-pooler` obtuvieron el mismo lock. El runner rechaza ahora ese
  endpoint antes de conectar y solo puede ejecutarse con el directo.
- ~~**AVERÍA EN CURSO, producción.**~~ **RESUELTA el 2026-08-13.** Ocho tablas
  de `tenant_2005` tenían su secuencia compartida por debajo del `MAX(id)` y no
  admitían inserciones: `estudiantes`, `profesor`, `asignaciones`, `asistencia`,
  `notas_detalle`, `pagos`, `boletin_cabecera` y `boletin_detalles`. La
  reparación de 3.4b se aplicó a producción y se verificó con una inserción
  controlada. Se conserva el enunciado porque explica por qué existía la capa.
- ~~**DETONANTE A UN COMANDO.**~~ **RESUELTO el 2026-08-13.**
  `scripts/limpiar_tenant_colegio_1_operativo.py` ejecuta
  `TRUNCATE … RESTART IDENTITY` sobre 20 tablas de la demo. Ya no alcanza a
  `tenant_2005`, que tiene secuencias propias, y los otros dos demos que
  compartían esos contadores fueron eliminados.
- ~~**Confirmado en 3.4a, producción**: `tenant_2005` tiene 11 claves foráneas
  frente a las 37 de la plantilla.~~ **RESUELTO en 3.4f el 2026-08-13**: las 26
  ausentes se repusieron y quedaron validadas contra los datos reales, lo que
  confirma de paso que no había huérfanos. `tenant_2005` iguala ahora las
  restricciones de la plantilla.
- **Riesgo nuevo, de la propia reparación**: `pg_get_constraintdef` devuelve las
  definiciones sin cualificar y se resuelven con el `search_path`. Cualquier
  script que copie claves foráneas entre schemas debe apuntarlo al destino, o
  creará referencias cruzadas. Reapareció en 3.5 y quedó protegido allí con
  `SET LOCAL search_path` al destino; permanece como lección para cambios
  futuros.
- Los únicos schemas conservados son `tenant_2005` y `tenant_colegio_1`; ambos
  tienen secuencias propias, 37 claves foráneas y 30 migraciones registradas.
- ~~`tenant_2005` carece de 15 registros de historial.~~ **RESUELTO en 3.4e.**
  Se sembraron los registros tras verificar equivalencia estructural y la
  auditoría final lo da como `OK`.
- La CI remota no está verificada para los commits de la capa 2. Un fallo de
  entorno en GitHub Actions podría aparecer atribuido a esta capa; conviene
  obtener evidencia del run antes de acumular más cambios.
- Las versiones del stack están limitadas solo por mínimos. Una resolución
  distinta puede alterar el comportamiento observado y exige repetir la
  compuerta.

## Registro de ejecución

### 2026-08-13 — activación de la capa

- Modo de acceso del asistente: mismo checkout local; Git validado directamente
  en `c:\Users\David\Documents\sistema_escolar_api`.
- Autorización: orden explícita del usuario para activar únicamente la capa 3,
  con aceptación registrada de mantener pendiente la calibración de
  `DB_STATEMENT_TIMEOUT_MS`.
- Rama acordada: `main`.
- Estado verificado antes de escribir: árbol limpio, sin archivos sin rastrear;
  `HEAD` y la referencia local `origin/main` en
  `81882f3b1ee9e3b50076b0fc1fd93dcd9fd5ac70`, sin divergencia.
- Commit base registrado: `81882f3b1ee9e3b50076b0fc1fd93dcd9fd5ac70`.
- Continuidad auditada: diez commits posteriores al base de la capa 2, todos
  explicados en `02_CONCURRENCIA.md`. Ocho materializaron la activación y las
  subcapas 2.0 a 2.5, `8c3939a` cerró la capa con 2.6 y `81882f3` publicó el
  cierre y preparó el relevo. Se verificó que `b24cb8d` y `8c3939a` son
  ancestros de `HEAD` y que el alcance de `81882f3` contiene exactamente
  `02_CONCURRENCIA.md`, `README.md` y `PROMPT_CONTINUACION.md`, tal como declara
  su entrada de bitácora.
- Archivos creados o modificados: esta bitácora y
  `docs/modularizacion/README.md`.
- Código de producto, migraciones, esquemas, pruebas, configuración,
  dependencias y workflow modificados: **ninguno**.
- Código o migraciones inspeccionados: **ninguno**. La activación se definió solo
  desde el índice maestro, la bitácora de continuidad y la plantilla.
- Compuerta global: no ejecutada durante la activación; 3.0 debe reproducirla
  desde el base.
- Evidencia remota: no hay cliente de GitHub disponible en este checkout, por lo
  que **no** se obtuvo evidencia de ningún run. GitHub Actions continúa **no
  verificada** para la capa 2 y para este relevo. La coincidencia entre `HEAD` y
  la referencia local `origin/main` no se presenta como prueba de CI.
- Verificación operativa heredada: la calibración de `DB_STATEMENT_TIMEOUT_MS`
  permanece **pendiente y aceptada**, con su riesgo conservado.
- Siguiente acción exacta: ejecutar **3.0**, reproduciendo la línea base e
  inventariando migraciones, versionado por tenant, runner y alta de tenants,
  junto con sus contratos y la estrategia de verificación. Actualizar únicamente
  esta bitácora y detenerse sin iniciar 3.1 y sin ejecutar migraciones.

### 2026-08-13 — subcapa 3.0

- Modo de acceso: mismo checkout local; rama `main` y árbol limpio antes de
  editar.
- Commit observado: `38dc6b211f45229962826dbdc55079c354533ef8`, un commit local
  por delante de la referencia local `origin/main` y del base de la capa.
- Continuidad: `81882f3` es el base; el único commit posterior es la activación
  de la capa 3, explicada en la entrada anterior. Se verificó que su diff
  contiene exactamente `03_MIGRACIONES_TENANTS.md` y `README.md`, por lo que el
  árbol ejecutable probado es idéntico al base. No hay divergencia.
- Archivos modificados: únicamente esta bitácora y, por orden explícita y
  separada del usuario, `docs/modularizacion/PROMPT_CONTINUACION.md`.
- Código de producto, migraciones, esquemas, pruebas, configuración,
  dependencias y workflow modificados: **ninguno**.
- Migraciones ejecutadas, conexiones a PostgreSQL abiertas y accesos a
  producción: **ninguno**.
- Comandos ejecutados:
  - precondiciones y continuidad: `git status --short --branch`,
    `git rev-parse HEAD`, `git rev-parse origin/main`,
    `git log --oneline 81882f3..HEAD`, `git show --stat 38dc6b2`,
    `git status --short -- app scripts tests .github requirements.txt`;
  - compuerta global: `.\venv\Scripts\python.exe scripts\verify.py`;
  - pruebas específicas:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_apply_migration.py tests/test_super_admin.py tests/test_auth_tenant.py`;
  - específicas ampliadas: las anteriores más
    `tests/test_apply_tenant_indexes.py` y
    `tests/test_tenant_context_concurrency.py`;
  - inventario: búsquedas dirigidas de `schema_migrations`, `CREATE SCHEMA`,
    `esquema_db`, `DEFAULT_TENANT_SCHEMA` y los estados de tenant, más lectura
    de `apply_migration.py`, `tests/test_apply_migration.py`,
    `app/controllers/super_admin_controller.py`, `app/core/tenant_status.py`,
    `app/config.py`, los cuatro `scripts/apply_*.py` y `docs/MIGRACIONES.md`;
  - alcance y whitespace: `git diff --check`,
    `git diff --no-index --check` sobre el archivo nuevo y el barrido C0
    reproducible.
- Compuerta global: **exit 0**, 477 pruebas, 5 warnings conocidos, Ruff correcto
  y dependencias íntegras. Terminó correctamente **dentro del sandbox**; el
  `WinError 5` sobre el temporal de pytest, presente en toda la capa 2, no se
  reprodujo. Se registra como observación ambiental, no como corrección.
- Pruebas específicas: **33 pasaron** en 0,56 s; ampliadas, **40 pasaron**.
- Hallazgos principales: seis puntos de entrada pueden mutar el esquema de un
  tenant y solo uno registra historial; el alta crea schemas sin sembrar
  `public.schema_migrations`; los tenants `suspendido` y `cancelado` quedan
  fuera del descubrimiento y pueden reactivarse sin recuperar lo omitido; y el
  historial es un registro por par archivo/schema, no una versión ordenada.
- Corrección registrada: los scripts de migración no pasan por `app/database.py`
  y por tanto no heredan los timeouts de la capa 1. El riesgo anotado al activar
  estaba invertido y quedó rectificado en «Riesgos».
- Decisiones: se reordenó el desglose de subcapas con el motivo de cada cambio y
  se dejó 3.1, el bloqueo del runner, como siguiente por ser la única subcapa
  cuyo beneficio no depende de las demás.
- Riesgos: registrados en «Riesgos»; ninguno se marcó como resuelto y las cuatro
  conjeturas sobre `LIKE INCLUDING ALL` quedaron explícitamente como hipótesis
  pendientes de una base de datos desechable.
- Verificación operativa heredada: la calibración de `DB_STATEMENT_TIMEOUT_MS`
  permanece **pendiente y aceptada**.
- Evidencia remota: sigue sin haber cliente de GitHub en este checkout; GitHub
  Actions continúa **no verificada**.
- Estado: **3.0 cerrada**. No se inició 3.1.
- Siguiente acción exacta: ejecutar **3.1**, caracterizando primero el
  comportamiento actual y añadiendo después un bloqueo que impida dos
  ejecuciones simultáneas del runner; detenerse antes de 3.2.

### 2026-08-13 — subcapa 3.1

- Modo de acceso: mismo checkout local; rama `main` y árbol limpio antes de
  editar.
- Commit observado: `7d1386a0b7f38afba0bf022281cb354a4491600d`, dos commits
  locales por delante de la referencia local `origin/main`.
- Continuidad: `81882f3` es el base; los dos commits posteriores son `38dc6b2`
  (activación) y `7d1386a` (3.0), ambos documentales y explicados en esta
  bitácora. El árbol ejecutable probado seguía siendo idéntico al base al
  empezar. No había divergencia.
- Código de producto: únicamente `apply_migration.py`. Se añadieron la constante
  `MIGRATION_LOCK_KEY`, la función `try_acquire_migration_lock` y la guarda que
  la usa antes de `ensure_migration_history`. No cambió el descubrimiento, el
  checksum, la transacción por tenant, los mensajes, los códigos de salida,
  `--dry-run`, el `search_path` ni la rama pública.
- Pruebas: `tests/test_apply_migration.py` pasó de 6 a **17 casos**. Se añadió
  un cursor guionizado y una conexión falsa que permiten recorrer
  `apply_migration()` de principio a fin, algo que 3.0 registró como inexistente.
- Archivos modificados: `apply_migration.py`, `tests/test_apply_migration.py` y
  esta bitácora.
- Migraciones ejecutadas, conexiones a PostgreSQL abiertas y accesos a
  producción: **ninguno**.
- Comandos ejecutados:
  - precondiciones y continuidad: `git status --short --branch`,
    `git log --oneline -3`, `git log --oneline 81882f3..HEAD`;
  - caracterización sobre el runner base:
    `git stash push -- apply_migration.py`,
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_apply_migration.py -k "not lock and not dry_run"`,
    `git stash pop`;
  - pruebas del archivo:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_apply_migration.py`;
  - dirigidas ampliadas: las anteriores más
    `tests/test_apply_tenant_indexes.py`, `tests/test_super_admin.py` y
    `tests/test_auth_tenant.py`;
  - lint del alcance:
    `.\venv\Scripts\python.exe -m ruff check apply_migration.py tests/test_apply_migration.py`;
  - compuerta global: `.\venv\Scripts\python.exe scripts\verify.py`;
  - alcance y whitespace: `git status --short`, `git diff --check` y el barrido
    C0 reproducible.
- Caracterización sobre el runner base: **8 pasaron**, 9 deseleccionadas. Es la
  prueba de que describen el comportamiento anterior y no el nuevo.
- Verificación final: 17 pruebas del archivo, **48 dirigidas** y compuerta global
  en **exit 0 con 488 pruebas**, 5 warnings conocidos, Ruff correcto y
  dependencias íntegras.
- Decisiones: lock de sesión en vez de transaccional; sin `pg_advisory_unlock`
  explícito porque todos los retornos cierran la conexión; exit 2 en vez de un
  código nuevo; `--dry-run` también toma el lock. Cada una con su alternativa
  descartada, registrada arriba.
- Riesgos: el lock no cubre los cuatro scripts ad-hoc, y su validez depende de
  que el runner use el endpoint directo y no el agrupado. Ninguno se marcó como
  resuelto y ambos quedaron registrados en «Riesgos».
- Verificación operativa heredada: la calibración de `DB_STATEMENT_TIMEOUT_MS`
  permanece **pendiente y aceptada**.
- Evidencia remota: sigue sin haber cliente de GitHub en este checkout; GitHub
  Actions continúa **no verificada**.
- Estado: **3.1 cerrada**. No se inició 3.2.
- Siguiente acción exacta: ejecutar **3.2**, completando la caracterización
  ejecutable del runner y del alta de tenant, sin modificar producto; detenerse
  antes de 3.3.

### 2026-08-13 — subcapa 3.2

- Modo de acceso: mismo checkout local; rama `main` y árbol limpio antes de
  editar.
- Commit observado: `73a777d1ae529c816b490a0acdf3d757b69a22f8`, tres commits
  locales por delante de la referencia local `origin/main`.
- Continuidad: `81882f3` es el base; los tres commits posteriores son `38dc6b2`
  (activación), `7d1386a` (3.0) y `73a777d` (3.1), todos explicados en esta
  bitácora. No había cambios pendientes ni divergencia al iniciar.
- Código de producto modificado: **ninguno**. 3.2 es una subcapa de solo
  pruebas y se verificó al terminar con
  `git status --short -- app apply_migration.py scripts migrations` vacío.
- Pruebas: `tests/test_apply_migration.py` pasó de 17 a **28 casos** y se creó
  `tests/test_tenant_provisioning.py` con **11 casos**.
- Archivos modificados: `tests/test_apply_migration.py`,
  `tests/test_tenant_provisioning.py` y esta bitácora.
- Migraciones ejecutadas, conexiones a PostgreSQL abiertas y accesos a
  producción: **ninguno**.
- Comandos ejecutados:
  - precondiciones y continuidad: `git status --short --branch`,
    `git log --oneline 81882f3..HEAD`, `git rev-parse HEAD`;
  - pruebas por archivo:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_apply_migration.py`
    y el equivalente para `tests/test_tenant_provisioning.py`;
  - dirigidas ampliadas:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_apply_migration.py tests/test_tenant_provisioning.py tests/test_super_admin.py tests/test_apply_tenant_indexes.py tests/test_auth_tenant.py`;
  - lint del alcance:
    `.\venv\Scripts\python.exe -m ruff check tests/test_apply_migration.py tests/test_tenant_provisioning.py`;
  - compuerta global: `.\venv\Scripts\python.exe scripts\verify.py`;
  - alcance y whitespace: `git status --short`,
    `git status --short -- app apply_migration.py scripts migrations`,
    `git diff --check` y el barrido C0 reproducible.
- Verificación final: 28 y 11 pruebas por archivo, **70 dirigidas** y compuerta
  global en **exit 0 con 510 pruebas**, 5 warnings conocidos, Ruff correcto y
  dependencias íntegras.
- Cobertura añadida: rama pública completa, aislamiento del fallo por tenant con
  la lista exacta de schemas registrados, `--dry-run` sobre varios tenants, los
  dos retornos con código 1, y el camino completo del alta de tenant.
- Decisiones: archivo separado para el alta porque 3.3 y 3.4 lo van a reescribir
  y su diff debe poder revisarse aislado; control positivo dentro de la aserción
  negativa del historial para que no pueda pasar por un fragmento mal escrito.
- Riesgos: los cuatro scripts ad-hoc siguen sin caracterización propia y estas
  pruebas usan dobles, no PostgreSQL. Ninguno se marcó como resuelto.
- Señal deliberada: `test_el_alta_todavia_no_siembra_el_historial_de_migraciones`
  **debe fallar** cuando 3.3b corrija el defecto. Su docstring lo advierte para
  que no se borre por confusión.
- Verificación operativa heredada: la calibración de `DB_STATEMENT_TIMEOUT_MS`
  permanece **pendiente y aceptada**.
- Evidencia remota: sigue sin haber cliente de GitHub en este checkout; GitHub
  Actions continúa **no verificada**.
- Estado: **3.2 cerrada**. No se inició 3.3a.
- Siguiente acción exacta: ejecutar **3.3a**, un informe de solo lectura que
  compare `migrations/` con `public.schema_migrations` incluyendo a los tenants
  suspendidos y cancelados; detenerse antes de 3.3b.

### 2026-08-13 — subcapa 3.3a

- Modo de acceso: mismo checkout local; rama `main` y árbol limpio antes de
  editar.
- Commit observado: `cfd9e4c04f940d67c3338c00364f65912add5f35`, cuatro commits
  locales por delante de la referencia local `origin/main`.
- Continuidad: `81882f3` es el base; los cuatro commits posteriores son
  `38dc6b2` (activación), `7d1386a` (3.0), `73a777d` (3.1) y `cfd9e4c` (3.2),
  todos explicados en esta bitácora. No había cambios pendientes ni divergencia
  al iniciar.
- Código de producto existente modificado: **ninguno**. Se añadió un script
  nuevo, `scripts/auditar_migraciones_tenants.py`; el runner, `app/`, las
  migraciones, el workflow y las dependencias quedaron intactos, verificado con
  `git status --short -- app apply_migration.py migrations .github requirements.txt`
  vacío.
- Pruebas: se creó `tests/test_auditar_migraciones_tenants.py` con **16 casos**
  herméticos.
- Archivos modificados o creados: `scripts/auditar_migraciones_tenants.py`,
  `tests/test_auditar_migraciones_tenants.py` y esta bitácora.
- Migraciones ejecutadas, conexiones a PostgreSQL abiertas y accesos a
  producción: **ninguno**. El informe se escribió y se probó, pero **no se
  ejecutó contra ninguna base**.
- Comandos ejecutados:
  - precondiciones y continuidad: `git status --short --branch`,
    `git log --oneline 81882f3..HEAD`, `git rev-parse HEAD`;
  - pruebas del archivo nuevo:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_auditar_migraciones_tenants.py`;
  - dirigidas ampliadas:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_auditar_migraciones_tenants.py tests/test_apply_migration.py tests/test_tenant_provisioning.py tests/test_apply_tenant_indexes.py tests/test_super_admin.py`;
  - resolución del `import` como script suelto, desde un directorio de trabajo
    fuera del repositorio y con `sys.path[0]` en `scripts/`, sin abrir conexión;
  - lint del alcance:
    `.\venv\Scripts\python.exe -m ruff check scripts/auditar_migraciones_tenants.py tests/test_auditar_migraciones_tenants.py`;
  - compuerta global: `.\venv\Scripts\python.exe scripts\verify.py`;
  - alcance y whitespace: `git status --short`, `git diff --check`,
    `git diff --no-index --check` sobre los dos archivos nuevos y el barrido C0.
- Verificación final: 16 pruebas nuevas, **71 dirigidas** y compuerta global en
  **exit 0 con 526 pruebas**, 5 warnings conocidos, Ruff correcto y dependencias
  íntegras.
- Decisiones: `SET TRANSACTION READ ONLY` y `to_regclass` en vez del
  `CREATE TABLE IF NOT EXISTS` del runner, para no alterar el estado observado;
  consulta a `public.colegios` sin `WHERE`, que es lo que distingue el informe
  del descubrimiento del runner; una sola definición de checksum importada del
  runner, descartando duplicarla.
- Riesgos: el informe cree lo que dice el historial y los cuatro scripts ad-hoc
  no registran nada, así que puede señalar como faltante algo ya aplicado por
  esa vía. Registrado, no resuelto.
- Verificación operativa heredada: la calibración de `DB_STATEMENT_TIMEOUT_MS`
  permanece **pendiente y aceptada**.
- Evidencia remota: sigue sin haber cliente de GitHub en este checkout; GitHub
  Actions continúa **no verificada**.
- Estado: **3.3a cerrada**. No se inició 3.3b.
- Siguiente acción exacta: ejecutar **3.3b**, sembrando el historial en el alta
  de tenant desde las filas del schema plantilla y reemplazando la prueba
  deliberada por su versión positiva; detenerse antes de 3.4.

### 2026-08-13 — subcapa 3.3b

- Modo de acceso: mismo checkout local; rama `main` y árbol limpio antes de
  editar.
- Commit observado: `7aa1003a95a8ea1b585b8b9411054667b428b6dd`, cinco commits
  locales por delante de la referencia local `origin/main`.
- Continuidad: `81882f3` es el base; los cinco commits posteriores son
  `38dc6b2` (activación), `7d1386a` (3.0), `73a777d` (3.1), `cfd9e4c` (3.2) y
  `7aa1003` (3.3a), todos explicados en esta bitácora. No había cambios
  pendientes ni divergencia al iniciar.
- Código de producto: únicamente `app/controllers/super_admin_controller.py`,
  con 19 líneas añadidas y ninguna eliminada. Se añadió la guarda `to_regclass`
  y el `INSERT ... SELECT` que copia el historial de la plantilla, dentro de la
  transacción existente. No cambiaron validaciones, paths, payload, status
  codes, permisos, orden de efectos, el `CREATE SCHEMA`, la copia de estructura,
  las plantillas predefinidas, el admin inicial ni el manejo de errores.
- Fuera del cambio: el runner, los cuatro scripts ad-hoc, el informe de 3.3a,
  `migrations/`, el workflow y las dependencias. Verificado con
  `git status --short -- apply_migration.py scripts migrations .github requirements.txt`
  vacío.
- Pruebas: `tests/test_tenant_provisioning.py` pasó de 11 a **14 casos**. Se
  retiró la prueba deliberada de 3.2 y se pusieron en su lugar cuatro positivas:
  la siembra, su orden respecto de la copia de estructura, la omisión cuando el
  historial no existe todavía y su reversión si el alta falla después.
- Migraciones ejecutadas, conexiones a PostgreSQL abiertas y accesos a
  producción: **ninguno**.
- Comandos ejecutados:
  - precondiciones y continuidad: `git status --short --branch`,
    `git log --oneline 81882f3..HEAD`, `git rev-parse HEAD`;
  - verificación de la señal contra el controlador anterior:
    `git stash push -- app/controllers/super_admin_controller.py`,
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_tenant_provisioning.py`,
    `git stash pop`;
  - pruebas del archivo tras el cambio: el mismo comando de pytest;
  - dirigidas ampliadas:
    `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_tenant_provisioning.py tests/test_super_admin.py tests/test_auditar_migraciones_tenants.py tests/test_apply_migration.py tests/test_auth_tenant.py tests/test_permissions.py`;
  - lint del alcance:
    `.\venv\Scripts\python.exe -m ruff check app/controllers/super_admin_controller.py tests/test_tenant_provisioning.py`;
  - compuerta global: `.\venv\Scripts\python.exe scripts\verify.py`;
  - alcance y whitespace: `git status --short`, `git diff --stat -- app`,
    `git diff --check` y el barrido C0.
- Señal deliberada: contra el controlador anterior, **4 pruebas fallaron y 10
  pasaron**. Las cuatro son las nuevas, así que detectan realmente el cambio;
  las diez confirman que el resto del alta no se movió.
- Verificación final: 14 pruebas del archivo, **99 dirigidas** y compuerta global
  en **exit 0 con 529 pruebas**, 5 warnings conocidos, Ruff correcto y
  dependencias íntegras.
- Decisiones: copiar las filas de la plantilla en vez de leer `migrations/`,
  porque lo segundo supondría que la plantilla está al día; guarda `to_regclass`
  para no romper un alta que hoy funciona en una base sin historial; se descartó
  crear la tabla desde el alta.
- Riesgos: si la plantilla está atrasada, el tenant nuevo hereda ese atraso. Es
  el comportamiento correcto y ahora queda visible en el informe de 3.3a, pero
  no debe leerse como que un tenant sembrado está al día.
- Hallazgo que condiciona la subcapa siguiente: las 30 migraciones de tenant son
  incrementales y ninguna crea las tablas base, así que 3.4 no puede construir
  un tenant desde `migrations/` sin un punto de partida. Documentado arriba con
  las dos opciones y la recomendación.
- Verificación operativa heredada: la calibración de `DB_STATEMENT_TIMEOUT_MS`
  permanece **pendiente y aceptada**.
- Evidencia remota: sigue sin haber cliente de GitHub en este checkout; GitHub
  Actions continúa **no verificada**.
- Estado: **3.3b cerrada**. No se inició 3.4.
- Siguiente acción exacta: **pedir una decisión al usuario** entre adelantar el
  ensayo no productivo para extraer el DDL base real o reconstruirlo desde
  `scripts/legacy/crear_cliente.py`. No iniciar 3.4 sin esa decisión.

### 2026-08-13 — decisión sobre el esquema base

- No es una subcapa: es la decisión que 3.3b dejó pendiente y que desbloquea el
  resto de la capa. Se registra aparte para que su diff no se confunda con
  trabajo de implementación.
- Decisión del usuario: **adelantar el ensayo no productivo**. El esquema base
  saldrá del DDL real de una base desechable, no de
  `scripts/legacy/crear_cliente.py`.
- Reordenamiento: el ensayo pasa a **3.4**, el alta reproducible a **3.5** y el
  cierre de capa a **3.6**.
- Riesgo aceptado: 3.5 queda bloqueada hasta que exista una base desechable. Se
  acepta a cambio de no fundar el alta de todos los colegios futuros sobre un
  archivo legacy sin equivalencia comprobada.
- Archivos modificados: esta bitácora y `docs/modularizacion/README.md`. Sin
  cambios de producto, pruebas ni migraciones.
- Bloqueo declarado: 3.4 no puede iniciarse hasta recibir una base PostgreSQL
  desechable, su cadena de conexión y la confirmación explícita de que no es
  producción. Ninguna subcapa usará el `DATABASE_URL` del `.env`.
- Corrección posterior, el mismo día: el usuario preguntó quién crearía las
  tablas si solo entregaba una cadena de conexión. La pregunta destapó que el
  paso 3 estaba mal especificado: una base vacía no contiene la estructura real
  y fabricarla habría sido circular. Se comprobó además que la máquina no tiene
  `pg_dump`, `psql`, Docker ni PostgreSQL. El usuario decidió usar una **rama de
  Neon**, que ya nace con el schema plantilla verdadero. Se añadieron la
  restricción de leer solo estructura, la prohibición de registrar la
  credencial y la exigencia del endpoint directo.
- Siguiente acción exacta: esperar la cadena de conexión de la rama y su
  confirmación. Después, ejecutar únicamente 3.4 según su «trabajo exacto».

### 2026-08-13 — subcapa 3.4a

- Modo de acceso: mismo checkout local; rama `main` y árbol limpio antes de
  editar.
- Commit observado: `e33a6ee`, seis commits locales por delante de la referencia
  local `origin/main`. Los seis están explicados en esta bitácora.
- Base de datos: rama de Neon `ensayo-3-4-no-produccion`, creada por el usuario
  desde `production` y confirmada por él como desechable. Su credencial **no se
  registra aquí**; se guardó en el scratchpad, fuera del repositorio.
- Comprobación de destino antes de conectar: el host de la rama
  (`ep-tiny-dream-aiceysjn…`) difiere del de `.env`
  (`ep-late-smoke-aip41j6x-pooler…`). La comparación imprimió solo nombres de
  host, nunca contraseñas. Todos los scripts abortan si el DSN no contiene el
  identificador de la rama.
- Restricción cumplida: solo se leyeron `information_schema`, `pg_catalog` y las
  tablas de infraestructura `public.colegios` y `public.schema_migrations`. **No
  se leyó ninguna fila de tablas de negocio.**
- Escrituras: un único schema de prueba, `tenant_zzz_ensayo_3_4_borrame`, creado
  y destruido en el mismo script. No se modificó ni se borró nada heredado.
- Archivos del repositorio modificados: **solo esta bitácora y
  `docs/modularizacion/README.md`**. Sin cambios de producto, pruebas,
  migraciones ni dependencias.
- Comandos ejecutados, todos desde scripts del scratchpad salvo el informe:
  - comparación de hosts y `git status`/`git log` de continuidad;
  - inventario estructural de solo lectura;
  - `.\venv\Scripts\python.exe scripts\auditar_migraciones_tenants.py` con
    `DATABASE_URL` apuntando a la rama. Antes se comprobó que
    `load_dotenv(override=False)` no sustituye una variable ya definida, para
    que el script no pudiera alcanzar producción por accidente;
  - comparación estructural tenant a tenant contra la plantilla;
  - desglose de restricciones por tipo y detección de defaults que apuntan a
    otro schema;
  - prueba controlada del bloque `DO $$` del alta sobre un schema nuevo;
  - prueba del advisory lock en los endpoints directo y agrupado de la rama;
  - verificación final de limpieza.
- Resultados: el informe de 3.3a funcionó con datos reales y devolvió exit 2;
  `tenant_4444` y `tenant_2005` carecen de 9 y 15 registros, sin ninguna
  divergencia de checksum; los tres tenants tienen columnas e índices idénticos
  a la plantilla, así que el atraso es de registro, no estructural.
- Las cuatro hipótesis de 3.0 quedaron **confirmadas** con evidencia causal, y
  el daño está en producción: a cada colegio le faltan entre 23 y 26 claves
  foráneas, y entre 23 y 26 de sus tablas generan `id` con secuencias de
  `tenant_colegio_1`.
- El advisory lock de 3.1 **se sostiene en el endpoint directo y no en el
  agrupado**, que es el que usa `.env`. La protección de 3.1 es hoy inefectiva
  en el entorno real.
- Decisión: dividir el ensayo. 3.4a cierra con la medición y la verificación;
  3.4b escribirá la migración base, ahora que se sabe que debe incluir claves
  foráneas, secuencias propias, disparador y función. Extraerla en el mismo
  turno habría sido escribirla antes de saber qué debía contener.
- Riesgos: tres reparaciones quedaron identificadas y **no** abordadas —el
  runner sobre endpoint agrupado, el historial faltante de dos tenants y las
  claves foráneas y secuencias compartidas de los tres colegios—. Ninguna se
  marcó como resuelta.
- Verificación operativa heredada: la calibración de `DB_STATEMENT_TIMEOUT_MS`
  permanece **pendiente y aceptada**.
- Evidencia remota: sigue sin haber cliente de GitHub en este checkout; GitHub
  Actions continúa **no verificada**.
- Estado: **3.4a cerrada**. No se inició la subcapa siguiente.
- Siguiente acción exacta: extraer el DDL completo de la plantilla y escribirlo
  como migración base nueva, con verificación de equivalencia en la rama;
  detenerse antes de 3.5.

### 2026-08-13 — subcapa 3.4b

- Modo de acceso: mismo checkout local; rama `main`, árbol limpio y alineado con
  `origin/main` antes de editar, tras la publicación de los ocho commits.
- Commit observado: `4e8e1ba`, ocho commits después del base, todos explicados.
- Autorización: el usuario respondió «continúa» a la propuesta explícita de
  abrir esta subcapa con la renumeración descrita, e informó de que la
  aplicación ya no está en uso.
- Renumeración registrada: la reparación de secuencias pasa a ser **3.4b** y la
  migración base baja a **3.4c**. Las entradas anteriores del registro llaman
  «3.4b» a la migración base y se conservan sin retocar.
- Código añadido: `scripts/reparar_secuencias_tenant.py`. **Ningún archivo de
  producto existente cambió**, verificado con
  `git status --short -- app apply_migration.py migrations .github requirements.txt`
  vacío.
- Pruebas: `tests/test_reparar_secuencias_tenant.py`, **13 casos** herméticos con
  un cursor que normaliza `sql.Composed` para poder inspeccionar el SQL generado.
- Base de datos: la misma rama desechable de 3.4a. **No se tocó producción.**
- Ensayo completo sobre `tenant_2005` en la rama: 26 columnas prestadas y 8
  colisiones antes; `--dry-run` sin efectos; aplicación con verificación
  correcta; 0 y 0 después; **rollback que restauró exactamente 26 y 8**;
  reaplicación limpia; y una ejecución adicional que informó «Nada que reparar».
- Verificación: 13 pruebas nuevas, **71 dirigidas** y compuerta global en **exit
  0 con 542 pruebas**, 5 warnings conocidos, Ruff correcto y dependencias
  íntegras.
- Decisiones: el script se auto-mide en tiempo de ejecución en vez de llevar los
  máximos observados en la rama, porque la rama es una foto y producción avanza;
  la verificación corre antes del `commit` para que un fallo no confirme nada;
  acepta `--schema` porque los tres schemas de demo tienen el mismo defecto; no
  toma el advisory lock del runner porque 3.4a demostró que no se sostiene sobre
  el endpoint que usa `.env` y sería una garantía falsa.
- Riesgos: la rama ya no refleja el estado de producción, así que un ensayo de
  última hora necesita una rama nueva. Las claves foráneas, el historial
  faltante y el runner sobre `-pooler` siguen sin reparar.
- Verificación operativa heredada: la calibración de `DB_STATEMENT_TIMEOUT_MS`
  permanece **pendiente y aceptada**.
- Evidencia remota: sigue sin haber cliente de GitHub en este checkout; GitHub
  Actions continúa **no verificada**.
- Estado: **3.4b cerrada, pendiente de aplicar**. No se inició 3.4c.
- Siguiente acción exacta: que el usuario aplique la reparación a producción
  siguiendo el procedimiento documentado y guarde la salida del `--dry-run`.
  Después, ejecutar 3.4c sobre una rama nueva.

### 2026-08-13 — corrección de 3.4b: `setval()` no es transaccional

- Origen: el usuario, antes de aplicar nada a producción, advirtió que
  `setval()` no se revierte con un `ROLLBACK` y que por tanto no podía
  presentarse el procedimiento como completamente transaccional ni afirmarse que
  el rollback restauraba todo con exactitud. Pidió evaluar
  `ALTER SEQUENCE … RESTART`, documentar qué parte requiere reversión manual y
  repetir el ensayo comprobando también `last_value`.
- La objeción era **correcta**. Se comprobó contra el servidor de la rama,
  PostgreSQL 17.10: dentro de una transacción revertida, el valor puesto por
  `setval(seq, 5000)` persistió tras el `ROLLBACK`, mientras que el puesto por
  `ALTER SEQUENCE … RESTART WITH 9000` volvió atrás.
- Cambio en producto: `scripts/reparar_secuencias_tenant.py` pasa a usar
  `ALTER SEQUENCE … RESTART WITH <máximo + 1>`. Desaparece además la rama
  especial para tablas vacías, porque `RESTART WITH 1` ya deja el siguiente
  valor en 1. Ningún otro archivo cambió.
- Prueba de regresión añadida:
  `test_no_se_usa_setval_porque_no_es_transaccional`. El archivo pasó de 13 a
  **14 casos**.
- Ensayo repetido sobre la rama comparando, además de `DEFAULT` y ownership, el
  `last_value`/`is_called` de las 30 secuencias de la plantilla y la lista de
  secuencias del tenant. Se añadió un **fallo simulado** antes del `commit`.
  Resultados: un fallo no deja rastro, el `--dry-run` no deja rastro, el
  rollback restaura el estado de partida y las secuencias de la plantilla
  permanecen intactas durante todo el ciclo.
- Corrección de una afirmación anterior: el primer ensayo comprobaba solo
  `DEFAULT`, ownership y colisiones, así que la frase «el rollback restauró
  exactamente el estado previo» estaba sostenida por una verificación
  insuficiente. Ahora lo está por la comparación completa.
- Distinción documentada: el rollback **posterior al `commit` es manual** y hay
  que ejecutarlo; el fallo *durante* la ejecución no requiere ninguna acción.
- Verificación: 14 pruebas del archivo, Ruff correcto y compuerta global en
  **exit 0 con 543 pruebas**.
- **No se tocó producción.** La verificación quedó cerrada antes de aplicar, tal
  como pidió el usuario.
- Siguiente acción exacta: sin cambios; aplicar la reparación a producción y
  después 3.4c.

### 2026-08-13 — subcapa 3.4c

- Modo de acceso: mismo checkout local; rama `main`. **El árbol no estaba
  limpio**: contenía exactamente el trabajo de 3.4b sin commitear —dos
  documentos modificados y dos archivos nuevos—, todo explicado en esta
  bitácora, y ningún archivo de producto existente. Se hace constar en vez de
  declarar un árbol limpio que no lo estaba.
- Base de datos: la **misma** rama de 3.4a y 3.4b. Se corrigió la exigencia
  previa de una rama nueva: 3.4b solo alteró `tenant_2005` y lo que 3.4c
  necesita es la plantilla, verificada intacta.
- Archivo añadido: `migrations/base/20260813_esquema_base_tenant.sql`, 568
  líneas. Ningún archivo de producto existente cambió, y los 34 `.sql` previos
  siguen intactos.
- Generación: script de scratchpad que fija `search_path` a la plantilla para
  que `pg_get_constraintdef` y `pg_get_functiondef` emitan nombres sin
  cualificar; a `pg_get_indexdef`, que cualifica siempre, se le quita el
  prefijo. Las columnas `id` se emiten como `SERIAL` para que cada schema cree
  su propia secuencia, y las claves foráneas van al final.
- Verificación de equivalencia aplicando el archivo **del repositorio** a un
  schema nuevo: 281 columnas idénticas sin diferencias, 30 secuencias, un
  disparador, una función, y **cero** defaults apuntando a la plantilla frente a
  los 30 que tenía la copia por `LIKE`.
- Dos diferencias aceptadas y documentadas: falta el índice
  `unique_documento_identidad`, que duplicaba exactamente a
  `profesor_documento_identidad_key` y que PostgreSQL descarta al declararlas
  juntas; y tres `CHECK` se reimprimen con otra forma equivalente. La
  equivalencia **no es byte a byte** y no se presenta como tal.
- Ubicación: `migrations/base/` y no `migrations/`, para que la auditoría de
  3.3a no lo cuente como una migración pendiente de todos los tenants.
  Comprobado: sigue viendo 30.
- Limpieza: el schema de prueba se destruyó y se verificó que no quedan restos.
- Verificación: compuerta global en **exit 0 con 543 pruebas**, Ruff correcto,
  dependencias íntegras y `git diff --check` en exit 0.
- Riesgos: el archivo cubre estructura, no siembra de datos. Y las reparaciones
  pendientes de la capa siguen abiertas.
- Estado: **3.4c cerrada**. No se inició 3.5.
- Siguiente acción exacta: ejecutar **3.5**, sustituyendo en el alta la copia por
  `LIKE` por la aplicación de la migración base, con ensayo comparativo en una
  rama; detenerse antes de 3.6.

### 2026-08-13 — aplicación de 3.4b a producción

Primera y única vez en todo el programa que se modifica la base real. Se hace
constar aparte porque rompe la regla general de no tocar producción, y solo
ocurrió con autorización explícita del usuario para esta reparación concreta.

- Autorización: el usuario ordenó priorizar la reparación, exigió ejecutar
  primero `--dry-run`, revisarlo juntos y detenerse ante cualquier diferencia
  frente a lo ensayado. Después autorizó la aplicación de forma inequívoca.
- Comprobación de destino antes de conectar: el host de `.env`,
  `ep-late-smoke-aip41j6x-pooler…`, se contrastó con el de la rama,
  `ep-tiny-dream-aiceysjn…`. Distintos. Solo se imprimieron nombres de host.
- `--dry-run` contra producción: exit 0, sin escribir nada. Devolvió **las
  mismas 26 columnas** y **los 26 máximos idénticos** a los medidos en la rama,
  coherente con que la aplicación estuviera fuera de uso. Ninguna anomalía: nada
  apuntaba a un tercer schema y las 4 columnas que ya tenían secuencia propia
  siguieron fuera del plan.
- Aplicación: `python scripts/reparar_secuencias_tenant.py --schema tenant_2005`.
  Salida «Reparadas 26 columna(s). Verificacion correcta», **exit 0**.
- Sobre el endpoint agrupado: no afectó. El script no toma locks de sesión y
  todo su trabajo cabe en una transacción, que PgBouncer mantiene sobre la misma
  conexión de servidor.
- Verificación posterior:
  - columnas usando secuencias de otro schema: **0**;
  - problemas según `verificar()`: **0**;
  - secuencias propias del tenant: **30** —las 4 previas más las 26 nuevas—,
    las 30 con `OWNED BY` su columna;
  - las ocho tablas antes bloqueadas quedaron con el siguiente id por encima de
    su máximo: `estudiantes` 686 sobre 685, `profesor` 49/48, `asignaciones`
    354/353, `asistencia` 3126/3125, `notas_detalle` 20367/20366, `pagos`
    10112/10111, `boletin_cabecera` 100/99 y `boletin_detalles` 314/313.
- Prueba controlada de inserción, dentro de una transacción revertida:
  `estudiantes` recibió id **686** y `profesor` id **49**, ambos por encima de
  su máximo previo. Tras el `rollback`, los conteos y los máximos quedaron
  intactos: 172 y 10 filas, máximos 685 y 48. **No se creó ninguna fila.**
- Efecto residual declarado: cada inserción de prueba consumió un `nextval`, que
  no se revierte. `estudiantes_id_seq` y `profesor_id_seq` quedan un valor por
  delante, de modo que los ids 686 y 49 no se usarán. Es un hueco de un id en
  cada tabla, sin ninguna consecuencia.
- Rollback disponible: la salida del `--dry-run`, conservada en la conversación,
  lista el `DEFAULT anterior` de las 26 columnas y sirve de guion de reversión.
  Revertir reintroduciría la avería, así que solo procede ante un problema
  inesperado.
- Alcance: solo `tenant_2005`. Los tres schemas de demo siguen compartiendo
  secuencias con `tenant_colegio_1` y pueden repararse con el mismo comando
  cuando se quiera.
- Estado: **riesgo 1 resuelto en producción**. El riesgo 2 queda desactivado
  para el colegio real —el script de limpieza ya no puede reiniciar sus
  contadores—, pero sigue vivo para los tres schemas de demo.
- Siguiente acción exacta: sin cambios; ejecutar 3.5 cuando el usuario lo
  ordene. No se inició.

### 2026-08-13 — subcapas 3.4d y 3.4e

El usuario ordenó cerrar primero estas dos, antes de las claves foráneas. Se
hicieron en el mismo turno porque la primera no toca producción y la segunda se
detuvo en el `--dry-run` para su revisión, como en 3.4b.

**3.4d, guarda del endpoint agrupado.** Solo código: `apply_migration.py` gana
`es_endpoint_agrupado()` y devuelve 1 sin conectar si el host lleva `-pooler`.
Cuatro pruebas nuevas. Verificado contra el `.env` real: imprime el motivo y
sale con 1. Consecuencia operativa declarada: con la configuración actual el
runner ya no arranca y habrá que usar el endpoint directo. No se añadió la
guarda a la auditoría ni al reparador de secuencias, que funcionan bien sobre el
pooler.

**3.4e, siembra del historial.** `scripts/sembrar_historial_tenant.py` copia los
registros de la plantilla que le faltan al tenant, tras comprobar que reproduce
su estructura. Once pruebas herméticas.

- Falso positivo corregido: la primera comprobación comparaba el nombre del
  índice y se negó alegando 32 diferencias. Contra producción resultó cosmético
  —`idx_cursos_estado` frente a `cursos_estado_idx`, el nombre autogenerado—.
  Comparando por función las diferencias son cero. La comprobación pasó a
  ignorar el nombre, con dos pruebas que lo fijan.
- Hallazgo colateral, no reparado: `tenant_2005` tiene 106 índices frente a los
  93 de la plantilla y ninguno aporta función nueva. Son 13 duplicados exactos.
- Ensayo en la rama: dry-run sin efectos, siembra de 15 a 30, el informe de 3.3a
  pasó a `OK`, segunda ejecución «Nada que sembrar».
- `--dry-run` contra producción: mismas 15, estructura sin diferencias, nada
  escrito.
- **Aplicado a producción** con la orden del usuario: «Registradas 15
  migracion(es)», exit 0. Verificación posterior: el informe de 3.3a da
  `tenant_2005` como **OK** y solo deja `tenant_4444` pendiente con 9, que es
  demo. Reejecutar informó «Nada que sembrar».
- Rollback: `DELETE FROM public.schema_migrations WHERE target_schema =
  'tenant_2005' AND migration_name IN (…las 15…)`. No borra datos del colegio;
  solo deshace el registro.
- Verificación: compuerta global en **exit 0 con 558 pruebas**, Ruff correcto y
  `git diff --check` en exit 0.
- Estado: **3.4d y 3.4e cerradas**, ambas aplicadas donde correspondía. No se
  inició la reparación de claves foráneas ni 3.5.
- Siguiente acción exacta: reponer las 26 claves foráneas de `tenant_2005`, con
  0 huérfanos ya confirmados en producción; después 3.5.

## Entrega al próximo chat

- Capa activa: **4, reportes financieros**, activada el 2026-08-14. Esta
  bitácora corresponde a la capa 3, **cerrada** el 2026-08-13.
- Última subcapa terminada: **3.6**, cierre. Primera subcapa pendiente: ninguna.
- Commit base: `81882f3b1ee9e3b50076b0fc1fd93dcd9fd5ac70`, rama `main`, con 13
  commits posteriores, todos explicados en esta bitácora.
- Compuerta al cerrar: **exit 0 con 570 pruebas**, Ruff correcto y dependencias
  íntegras. La suite pasó de 477 al empezar la capa a 570.
### Lo primero que debe saber quien continúe

Quedan **dos schemas de tenant**: `tenant_2005`, el único de producción, y
`tenant_colegio_1`, que es a la vez plantilla y demo. Los dos demos anteriores,
`tenant_3333` y `tenant_4444`, se eliminaron el 2026-08-13 tras cerrar la capa.

`tenant_colegio_1` **no se puede borrar**: el alta sigue copiando de él las
`plantilla_impresion` predefinidas y los registros de `schema_migrations`.

### Qué dejó la capa

- El alta construye el schema desde `migrations/base/20260813_esquema_base_tenant.sql`.
  Un tenant nuevo nace con 37 claves foráneas y 30 secuencias propias; el camino
  anterior producía 0 y 0.
- `apply_migration.py` toma un advisory lock de sesión y **se niega a correr
  sobre el endpoint agrupado**, donde ese lock no se sostiene.
- Cuatro herramientas nuevas en `scripts/`: auditoría de migraciones faltantes,
  reparación de secuencias, siembra de historial y reposición de claves
  foráneas. Todas con `--dry-run`, idempotentes y transaccionales.
- Tres reparaciones **aplicadas a producción** sobre `tenant_2005`: secuencias
  propias, 15 registros de historial y 26 claves foráneas. Es la única
  modificación de la base real en todo el programa.

### Qué quedó abierto

1. ~~Los dos schemas demo sin reparar.~~ **Resuelto el 2026-08-13**: el usuario
   decidió eliminarlos en vez de repararlos. Quedan `tenant_2005` y
   `tenant_colegio_1`, ambos completos, y la auditoría termina en exit 0. Ver
   «Mantenimiento posterior al cierre».
2. ~~La migración base y `migrations/` no están enlazados.~~ **Resuelto el
   2026-08-13** con `scripts/generar_esquema_base.py` y
   `tests/test_esquema_base.py`. Ver «Enlace entre la migración base y
   `migrations/`».
3. ~~Verificación manual sin hacer.~~ **Hecha el 2026-08-13** por el usuario,
   con resultado correcto tras ejercitar la aplicación contra la base reparada.
4. **14 índices duplicados** en `tenant_2005`. Medidos y descartados
   deliberadamente: el ahorro no compensa otra operación sobre producción.
   Disponible como limpieza cosmética, no es un defecto.
5. ~~La rama de Neon sigue viva.~~ **Eliminada** por el usuario el 2026-08-14, y
   la credencial de producción **verificada**: inicia sesión en los dos tenants,
   así que `.env` sigue siendo válido.
6. Heredados: `DB_STATEMENT_TIMEOUT_MS` sin calibrar desde la capa 1 y GitHub
   Actions sin verificar desde la capa 0.

### Lecciones que se pagaron caro

- `setval()` **no** se revierte con un `ROLLBACK`; `ALTER SEQUENCE … RESTART`
  sí. Lo detectó el usuario antes de aplicar nada.
- `pg_get_constraintdef` y el propio archivo base devuelven nombres **sin
  cualificar**: se resuelven con el `search_path`. Cualquier script que copie
  estructura entre schemas debe apuntarlo al destino, o creará referencias
  cruzadas. Ocurrió en 3.4f y falló por casualidad.
- Comparar índices por su **nombre** da falsos positivos: la plantilla y los
  tenants siguen convenciones distintas. Hay que comparar por función.

### Siguiente acción exacta

Continuar exclusivamente desde `04_REPORTES_FINANCIEROS.md`. La primera
subcapa pendiente es 4.0; esta bitácora cerrada no autoriza inferir ni ejecutar
trabajo adicional de la capa 3.
