# Capa 3: migraciones y tenants

Última revisión: 2026-08-13.

## Control

- Estado: **Activa**.
- Commit base: `81882f3b1ee9e3b50076b0fc1fd93dcd9fd5ac70`.
- Rama acordada: `main`.
- Estado al activar: árbol limpio; `HEAD` coincidente con la referencia local
  `origin/main`.
- Primera subcapa pendiente: **3.2**.
- Progreso: **3.0 y 3.1 cerradas**. El inventario está registrado abajo y
  reemplaza el desglose provisional de la activación.
- Código de producto modificado al activar: **ninguno**.
- Código de producto modificado hasta ahora: `apply_migration.py`, que ahora toma
  un advisory lock de sesión antes de leer o escribir el historial. 3.0 fue una
  subcapa de solo lectura.
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
| 3.2 | Caracterización ejecutable del runner y del alta actual | **Pendiente** |
| 3.3 | Versionado verificable: detectar tenants atrasados y sembrar altas nuevas | Pendiente |
| 3.4 | Alta reproducible desde migraciones versionadas | Pendiente |
| 3.5 | Ensayo no productivo, rollback, verificación manual y cierre | Pendiente |

El inventario de 3.0 **confirmó y ajustó** el desglose provisional de la
activación. Los cambios respecto de aquella tabla y su motivo:

- se intercala una subcapa de caracterización ejecutable (3.2) porque la
  cobertura actual no ejercita ningún camino real del runner y una extracción
  sin ella no sería reversible con evidencia;
- el versionado (3.3) se separa del alta reproducible (3.4) porque el inventario
  mostró que son dos defectos distintos: los tenants omitidos mientras están
  suspendidos y las altas nuevas que nacen sin historial;
- 3.1 permanece primero porque es la única subcapa cuyo beneficio no depende de
  ninguna otra y reduce el riesgo de todas las siguientes.

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
- El lock de sesión de 3.1 supone una sesión real y estable. Si `DATABASE_URL`
  apunta al endpoint agrupado que la capa 1 documentó como PgBouncer, la
  conexión puede reasignarse entre sentencias y el lock deja de garantizar nada.
  No se verificó qué endpoint usa el runner; es una precondición del ensayo, no
  un hecho comprobado.
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

## Entrega al próximo chat

- Capa activa: **3, migraciones y tenants**.
- Última subcapa terminada: **3.1**, bloqueo del runner contra ejecuciones
  simultáneas.
- Primera subcapa pendiente: **3.2**, caracterización ejecutable del runner y
  del alta de tenant, sin modificar producto.
- Commit base: `81882f3b1ee9e3b50076b0fc1fd93dcd9fd5ac70`, rama `main`.
- Hallazgo central: seis puntos de entrada pueden mutar el esquema de un tenant
  y solo `apply_migration.py` registra lo que aplicó. El alta crea el schema
  copiando la plantilla sin sembrar historial, y los tenants suspendidos o
  cancelados quedan fuera del descubrimiento sin recuperar nada al reactivarse.
- Estado de 3.1: `apply_migration.py` toma un advisory lock de sesión antes de
  leer o escribir el historial y devuelve exit 2 si otra ejecución lo tiene. El
  lock **no** cubre los cuatro scripts ad-hoc.
- Verificación local vigente: compuerta global en exit 0 con **488 pruebas**,
  Ruff y dependencias correctos; 17 pruebas del runner y 48 dirigidas. La
  caracterización se comprobó además contra el runner anterior, con 8 pasadas.
- Bloqueos: ninguno para iniciar 3.2. Permanece pendiente y aceptada la
  calibración de `DB_STATEMENT_TIMEOUT_MS` de la capa 1, y GitHub Actions sigue
  sin evidencia de run.
- No medido todavía: el estado real de versionado por tenant, las cuatro
  hipótesis sobre `LIKE ... INCLUDING ALL` y si el runner usa el endpoint
  directo o el agrupado. Las tres cosas exigen acceso a una base y no deben
  darse por ciertas; la última condiciona que el lock sirva de algo en el
  entorno real.
- Siguiente acción exacta: ejecutar únicamente 3.2 según «Siguiente subcapa:
  3.2, trabajo exacto», sin modificar producto, sin tocar los scripts ad-hoc ni
  archivos existentes de `migrations/` y sin ejecutar ninguna migración.
