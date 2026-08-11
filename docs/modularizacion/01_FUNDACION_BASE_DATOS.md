# Capa 1: fundación de base de datos

Última revisión: 2026-08-11.

## Control

- Estado: **Cerrada** el 2026-08-11. Conserva una verificación operativa
  pendiente y aceptada: la calibración de `DB_STATEMENT_TIMEOUT_MS`.
- Commit base: `6754e4aad59c1e428ea97d31fe8e96fdbba7694d`.
- Rama acordada: `main`.
- Estado al activar: árbol limpio; `main` sincronizada con `origin/main`.
- Primera subcapa pendiente: **1.6**, el cierre de la capa.
- Código de producto modificado hasta ahora: **los 50 sitios desprotegidos**,
  repartidos en quince tandas, desde los servicios de validación (1.2) hasta
  estudiantes (1.4m), más los timeouts y el pool en 1.5. Sin cambio de
  comportamiento observable, salvo las dos fugas deterministas corregidas, la
  confirmación de transacciones de solo lectura y los timeouts nuevos, todos
  documentados en su subcapa.
- Progreso de la capa: **0 sitios** sin cierre garantizado, de 50 iniciales.
  **Cero fugas deterministas.** Ninguna ruta abre conexiones. Timeouts definidos
  y comportamiento del pool medido. Falta únicamente el cierre 1.6.
- Verificación pendiente registrada en 1.5: calibrar `DB_STATEMENT_TIMEOUT_MS`
  contra los tiempos reales de las consultas pesadas. No darla por cumplida.
- Autorización: orden explícita del usuario el 2026-08-11, después de cerrar la
  capa 0 con la CI remota verificada.

## Objetivo

Que la propiedad de la conexión, el cursor, el `commit` y el `rollback` sea
explícita y verificable, y que el pool y los timeouts estén definidos con
evidencia, sin cambiar ningún contrato observable.

Al cerrar esta capa debe poder responderse, para cualquier ruta: quién abre la
conexión, quién la devuelve al pool, quién confirma y quién revierte.

## Dependencias de capas anteriores

- Compuerta única `scripts/verify.py`, cerrada en 0.2.
- CI `Backend quality` ejecutando esa compuerta desde un checkout limpio,
  verificada en remoto el 2026-08-11 sobre
  `b20dcbe43a64c25e2ece7a7a99782983e2626160`.
- 192 pruebas deterministas, sin dependencia del calendario, cerradas en 0.1.
- Inventario de contratos HTTP por familia, cerrado en 0.0. Esta capa **no**
  puede alterar ninguna de las filas de ese inventario.

## Alcance autorizado

- Inventariar cómo se abren, usan y cierran conexiones y cursores hoy.
- Definir y documentar la propiedad de `commit`, `rollback`, cursor y conexión.
- Sustituir aperturas manuales de forma progresiva, un consumidor a la vez.
- Establecer timeouts y manejo del pool con evidencia medida.
- Agregar pruebas de caracterización que protejan lo anterior.

## Fuera de alcance

- Cambiar `psycopg2` por otro driver o introducir un ORM.
- Modificar rutas, payloads, status codes, permisos, roles, tenant u ownership.
- Cambiar el SQL observable, salvo que una subcapa lo autorice de forma explícita
  y con equivalencia demostrada.
- Mover controladores, services o repositories entre módulos: eso pertenece a las
  capas de dominio, de la 4 en adelante.
- Sacar la DB síncrona del event loop: eso es la capa 2 y no se adelanta aquí.
- Ejecutar o modificar migraciones de tenants: eso es la capa 3.
- Optimizar consultas, agregar índices o corregir N+1.

## Invariantes

- Todas las familias del inventario de contratos de 0.0 conservan método, path,
  status code y forma de respuesta.
- Permisos, roles, ownership y aislamiento entre tenants se conservan sin
  excepción, incluida la propagación del `ContextVar` del tenant.
- El SQL observable y el orden de las operaciones dentro de cada transacción se
  conservan salvo autorización explícita.
- Los efectos laterales registrados en 0.0 —auditoría, archivos, notificaciones—
  se conservan.
- La compuerta `scripts/verify.py` debe terminar en exit 0 al cerrar cada
  subcapa.

## Línea base

Heredada del cierre de la capa 0. La subcapa 1.0 debe reproducirla desde el
commit base antes de inventariar nada.

| Comprobación | Comando | Resultado heredado |
|---|---|---|
| Compuerta global | `.\venv\Scripts\python.exe scripts\verify.py` | Exit 0 |
| Suite global | `.\venv\Scripts\python.exe -m pytest -q` | 192 pasaron, 5 warnings conocidos |
| Ruff | `.\venv\Scripts\python.exe -m ruff check --no-cache app tests scripts apply_migration.py` | `All checks passed!` |
| Dependencias | `.\venv\Scripts\python.exe -m pip check` | `No broken requirements found.` |
| CI remota | Workflow `Backend quality`, evento `push` | Correcta sobre `b20dcbe` |

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 1.0 | Inventario de conexiones, cursores y transacciones; decisión sobre cómo verificar | **Cerrada** |
| 1.1 | Contrato explícito de propiedad de conexión/cursor/commit/rollback | **Cerrada** |
| 1.2 | Primera tanda: servicios de validación, 4 sitios | **Cerrada** |
| 1.3 | Segunda tanda: planeador anual, 3 sitios, estrena escritura | **Cerrada** |
| 1.4 | Tercera tanda: usuarios, 4 sitios, incluye la primera fuga determinista | **Cerrada** |
| 1.4b | Cuarta tanda: asignaciones, 6 sitios, elimina la última fuga determinista | **Cerrada** |
| 1.4c | Quinta tanda: branding, 4 sitios, primer archivo que abandona `get_connection` | **Cerrada** |
| 1.4d | Sexta tanda: dashboard, 4 sitios, todos de solo lectura | **Cerrada** |
| 1.4e | Séptima tanda: inventario, 3 sitios, primer archivo con aritmética de dinero | **Cerrada** |
| 1.4f | Octava tanda: profesores, 1 sitio | **Cerrada** |
| 1.4g | Novena tanda: asistencia, 1 sitio | **Cerrada** |
| 1.4h | Décima tanda: notas, 5 sitios, archivo completo | **Cerrada** |
| 1.4i | Undécima tanda: plantillas, 7 sitios, archivo completo | **Cerrada** |
| 1.4j | Duodécima tanda: dominio planilla, 3 sitios en 2 archivos | **Cerrada** |
| 1.4k | Decimotercera tanda: las 2 aperturas en la capa HTTP | **Cerrada** |
| 1.4l | Decimocuarta tanda: historial de pagos, 1 sitio | **Cerrada** |
| 1.4m | Decimoquinta tanda: estudiantes, 2 sitios. **Migración completa** | **Cerrada** |
| 1.5 | Timeouts y manejo del pool definidos con evidencia medida | **Cerrada**, verificada contra el endpoint agrupado real |
| 1.6 | Cierre: compuerta global, staging, rollback y verificación manual | **Cerrada** |

**Reordenación autorizada el 2026-08-11.** El plan original situaba los timeouts
antes de completar la migración. El usuario ordenó de forma explícita continuar
migrando primero. Motivo registrado: el patrón de migración quedó validado en
1.2, el riesgo de fuga está medido y activo en los sitios restantes, y modificar
la creación del pool afecta a todas las conexiones a la vez, por lo que conviene
hacerlo con menos deuda encima.

**Este desglose es provisional a partir de 1.1.** Se definió desde el alcance
aprobado en el índice maestro, sin inspeccionar el código de conexiones, porque
las reglas del programa prohíben leer una capa antes de activarla. El inventario
de 1.0 podrá dividir, fusionar o marcar `No aplica` las subcapas posteriores con
justificación escrita. Lo que no puede es ampliarse a asuntos fuera del alcance.

## Subcapa activa: 1.0, trabajo exacto

1. Reproducir la línea base desde el commit base y registrar el resultado real.
2. Inventariar dónde se abren conexiones y cursores hoy, y quién ejecuta
   `commit`, `rollback` y el cierre en cada caso. Registrar el patrón observado,
   no el deseado.
3. Registrar la configuración vigente del pool y de los timeouts, incluyendo los
   valores por defecto de `app/config.py` ya conocidos
   (`DB_POOL_MIN_CONNECTIONS`, `DB_POOL_MAX_CONNECTIONS`).
4. Identificar patrones divergentes y marcar los que representen riesgo real de
   fuga de conexión o de transacción a medio aplicar. Documentarlos; **no
   corregirlos en 1.0**.
5. **Resolver la pregunta de verificación** descrita en Riesgos: proponer al
   usuario cómo se comprobarán los cambios de conexión, dado que la suite actual
   es hermética. Registrar la decisión antes de tocar código en 1.1.
6. Actualizar esta bitácora y detenerse. No iniciar 1.1.

Archivos permitidos en 1.0: **únicamente esta bitácora**. La subcapa es de
lectura y documentación; no modifica código, pruebas ni configuración.

Comandos de verificación de 1.0: la compuerta global y `git diff --check`.

## Subcapa 1.0: resultado

### Línea base reproducida

Ejecutada el 2026-08-11 desde el commit base, con la activación de la capa aún
sin commitear en el árbol:

| Comprobación | Resultado |
|---|---|
| `.\venv\Scripts\python.exe scripts\verify.py` | Exit 0 |
| pytest | 192 pasaron, 5 warnings conocidos, 2,01 s |
| Ruff | `All checks passed!` |
| `pip check` | `No broken requirements found.` |

### Arquitectura observada

`app/database.py` es solo un reexport de `app/db/session.py`, que concentra toda
la infraestructura:

- Pool `ThreadedConnectionPool` perezoso, creado bajo `Lock` con doble
  comprobación en `get_pool()`.
- `PooledConnection` envuelve la conexión real y delega por `__getattr__`. Su
  `close()` **no cierra**: hace `rollback()` y devuelve la conexión al pool con
  `putconn()`. `real_close()` sí cierra de verdad.
- `get_connection()` toma del pool, fija `autocommit = False` y aplica el
  `search_path` del tenant. Si eso falla, revierte, devuelve la conexión y
  relanza.
- `get_cursor(commit=False)` es un `contextmanager` que sí gobierna el ciclo
  completo: hace `commit` si se le pide, `rollback` ante excepción y en `finally`
  cierra cursor y devuelve la conexión.
- `close_pool()` se invoca una sola vez desde `app/main.py:66`.

`app/db/tenant.py` lee el tenant del `ContextVar`, lo valida contra
`INTERNAL_SCHEMA_PATTERN` y ejecuta `SET search_path` con `sql.Identifier`, es
decir con identificador escapado.

### Inventario cuantitativo

Medido con un análisis AST sobre `app/`, no con `grep`: para cada llamada a
`get_connection()` se localizó la función contenedora y se determinó si el cierre
está garantizado por un `try/finally`.

| Patrón | Sitios | Significado |
|---|---:|---|
| `get_cursor(...)` | 15 | La infraestructura posee `commit`, `rollback` y cierre |
| `get_connection()` con `try/finally` | 94 | El llamador posee el ciclo y lo protege |
| `get_connection()` que cierra **fuera** de `finally` | 50 | El llamador posee el ciclo y **no** lo protege |
| `get_connection()` en helper que delega el cierre | 2 | Propiedad delegada al llamador |
| **Total de aperturas en `app/`** | **146** | |

Distribución de las 146: 131 en `controllers`, 6 en `core`, 5 en `services`, 2 en
`routes`, 1 en `dependencies.py` y 1 en `main.py`.

Los 2 casos de propiedad delegada son `app/core/super_admin.py:20`
(`_with_public_connection`) y `app/controllers/super_admin_controller.py:24`
(`_public_connection`): abren, devuelven `(token, conn)` y el llamador cierra. No
son fugas; son un patrón distinto que debe quedar nombrado.

### Riesgo principal: 50 sitios pierden la conexión ante excepción

Patrón confirmado leyendo el código, por ejemplo en
`app/controllers/notas_controller.py:26`, `crear_nota_controller`:

```python
conn = get_connection()
cursor = conn.cursor()
asignacion_id = resolver_asignacion_academica_id_cursor(cursor, ...)
cursor.execute("INSERT INTO notas_detalle ...")
nota_id = cursor.fetchone()[0]
conn.commit()
cursor.close()
conn.close()
```

No hay `try`. Si `cursor.execute` falla —violación de constraint, dato inválido,
corte de red— nunca se llega a `conn.close()`, la conexión **no vuelve al pool** y
además queda con una transacción abierta reteniendo locks.

El impacto es acotado y calculable: el pool usa los valores por defecto de
`app/config.py`, `DB_POOL_MIN_CONNECTIONS = 1` y `DB_POOL_MAX_CONNECTIONS = 10`,
y `.env` no los sobreescribe. **Diez fallos acumulados en rutas no protegidas
agotan el pool y la aplicación deja de responder** hasta reiniciarse. No es
hipotético: son 50 sitios, varios en escritura financiera y académica.

### Timeouts: no existe ninguno

No hay `connect_timeout`, `statement_timeout` ni `lock_timeout` en `app/`, ni en
la creación del pool, ni en `.env`. `_create_pool()` solo pasa `minconn`,
`maxconn` y `dsn`. Una consulta lenta o un lock retenido puede ocupar una
conexión de forma indefinida, lo que se combina de forma multiplicativa con el
riesgo anterior. Esto es material para la subcapa 1.3.

### Aperturas manuales: ninguna en el camino de petición

`psycopg2.connect` directo aparece 15 veces, **todas fuera de `app/`**:
`apply_migration.py` y `scripts/`, incluido `scripts/legacy/`. Son herramientas
de operación y migración, no código servido.

Esto corrige de forma favorable la expectativa del índice maestro, que anticipaba
«eliminar aperturas manuales progresivamente»: en el camino de petición ese
trabajo ya está hecho. Lo que queda no es centralizar la apertura, sino **hacer
explícita y obligatoria la propiedad del cierre**. Las aperturas de `scripts/` y
las migraciones pertenecen a la capa 3 y no se tocan aquí.

### Decisión pendiente: cómo verificar

La suite es hermética y no levanta PostgreSQL, así que ninguna de las 192 pruebas
puede detectar hoy una conexión que no vuelve al pool. Opciones identificadas,
para decisión del usuario antes de 1.1:

1. **Pruebas de contrato con pool falso.** Inyectar un pool y una conexión de
   mentira y afirmar que, tras una excepción, la conexión fue devuelta. Prueba el
   mecanismo real, es hermética, rápida y no toca CI.
2. **Guardia estática de regresión.** Una prueba que recorra el AST y falle si
   aparece un `get_connection()` sin cierre garantizado. Protege los 146 sitios a
   la vez e impide que el problema reaparezca. El análisis de esta subcapa ya
   demuestra que es viable.
3. **PostgreSQL real en CI.** Lo más fiel, pero agrega un servicio al workflow,
   alarga cada run y exige decidir migraciones y datos de prueba. La bitácora de
   0.3 registró que añadir ese servicio sería una decisión explícita.

Las opciones 1 y 2 son complementarias y no requieren tocar la infraestructura de
CI; la 3 es independiente y de mayor alcance.

**Decisión del usuario, 2026-08-11: opción 1, pruebas de contrato con pool
falso.** Las opciones 2 y 3 quedan descartadas para esta capa; no se implementan
ni se preparan por anticipado.

Consecuencia que debe quedar registrada: la opción 1 verifica que *la
infraestructura* devuelve la conexión ante excepción, pero **no** comprueba que
cada uno de los 146 sitios la use correctamente. Cuando 1.2 y 1.4 migren los 50
sitios desprotegidos, la corrección de cada sitio se apoyará en revisión del diff
y en las pruebas existentes, no en una guardia automática. Un sitio nuevo escrito
mal en el futuro tampoco fallará solo. Queda como riesgo aceptado y reevaluable.

## Subcapa 1.1: resultado

### El contrato, declarado

`app/db/session.py` ofrece dos puntos de entrada con **propiedad opuesta**. Esta
es la distinción que gobierna toda la capa y que 1.2 en adelante debe respetar.

**A. `get_cursor(commit=False, cursor_factory=None)` — la infraestructura posee
el ciclo.**

- Abre la conexión y el cursor.
- Confirma **solo** si se le pasa `commit=True`.
- Ante excepción revierte y relanza, conservando la excepción original.
- Siempre, en `finally`, cierra el cursor y devuelve la conexión al pool.
- El llamador **no debe** hacer `commit`, `rollback` ni `close`.

**B. `get_connection()` — el llamador posee el ciclo.**

- Devuelve una `PooledConnection` ya preparada, con `autocommit = False` y el
  `search_path` del tenant aplicado.
- Si la preparación falla, la conexión **ya volvió al pool** antes de relanzar;
  el llamador no debe intentar devolverla.
- A partir de ese punto el llamador **debe** garantizar `close()` en un
  `finally`. Nada más lo hace por él.
- `close()` no cierra la conexión: hace `rollback` y la devuelve al pool. Es
  idempotente, así que llamarlo dos veces no la devuelve dos veces.
- Como `close()` revierte, **omitir `commit()` descarta los cambios en silencio**.
- `real_close()` cierra de verdad y **no** devuelve la conexión al pool.

El riesgo inventariado en 1.0 es exactamente el incumplimiento del punto B por
parte de 50 llamadores: obtienen la propiedad y no la protegen con `finally`.

### Pruebas agregadas

`tests/test_db_session_contrato.py`, 9 pruebas con pool falso. No requieren
PostgreSQL ni tocan CI. Fijan cada punto del contrato anterior, incluida la
garantía central: **la conexión vuelve al pool aunque el bloque protegido lance
una excepción.**

Los dobles son tres clases locales —`CursorFalso`, `ConexionFalsa`,
`PoolFalso`— que llevan la cuenta de `getconn`, `putconn`, `commit`, `rollback`
y cierres. El pool se inyecta con `monkeypatch.setattr(session, "_pool", ...)`,
que lo restaura al terminar; el `ContextVar` del tenant se fija y se libera con
su token para no filtrar estado a otras pruebas.

### Comprobación de que las pruebas no son vacuas

Una prueba que pasa no demuestra nada si también pasaría con el código roto. Se
ejecutó una comprobación de mutación desde el directorio temporal de trabajo, sin
modificar el repositorio: se reprodujo la aserción crítica contra una variante de
`get_cursor` **sin `finally`**.

| Variante | Conexiones devueltas al pool | Aserción |
|---|---:|---|
| `get_cursor` real | 1 | Pasa |
| `get_cursor` sin `finally` | 0 | **Falla** |

La prueba distingue el contrato correcto del roto. Es la misma clase de evidencia
que 0.2 registró al simular códigos de salida de la compuerta.

### Alcance real: no se tocó código de producto

1.1 resultó ser **caracterización pura**. El contrato ya existía en el código;
lo que faltaba era declararlo y fijarlo con pruebas. `app/` no se modificó en
absoluto, así que esta subcapa no puede alterar el comportamiento en producción.

La primera subcapa que realmente modifique `app/` será 1.2.

### Verificación

| Comprobación | Resultado |
|---|---|
| Pruebas específicas | 9 pasaron en 0,18 s |
| Compuerta global | Exit 0 |
| Suite completa | **201** pasaron, 5 warnings conocidos, 1,19 s |
| Ruff | `All checks passed!` |
| `pip check` | `No broken requirements found.` |
| `git diff --check` | Exit 0 |

Ruff detectó en la primera pasada un `F841` real —una variable `cursor` enlazada
y no usada— que se corrigió eliminando el enlace. Queda registrado como evidencia
de que la compuerta heredada de la capa 0 está cumpliendo su función sobre código
nuevo.

## Subcapa 1.2: resultado

### Tanda elegida

Los cuatro sitios de servicios, no de controladores:

| Archivo | Funciones migradas |
|---|---|
| `app/services/nota_service.py` | `validar_asignacion`, `validar_estudiante`, `validar_estudiante_en_curso` |
| `app/services/planilla_service.py` | `validar_estudiante_asignacion` |

Criterio de selección: son de **solo lectura**, sin `commit` ni escritura, con
forma idéntica entre sí, y su diff cabe entero en una pantalla. `pagos`, `ventas`
y `estudiantes` se dejan deliberadamente para el final, cuando el patrón esté
rodado.

### Transformación aplicada

Las cuatro funciones tenían exactamente la misma forma desprotegida:

```python
conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT ...")
existe = cursor.fetchone()
cursor.close()
conn.close()          # no se ejecuta si execute() lanza
```

y pasaron al régimen que la infraestructura gobierna:

```python
with get_cursor() as cursor:
    cursor.execute("SELECT ...")
    existe = cursor.fetchone()
```

No se creó ninguna abstracción nueva. `get_cursor()` ya existía con 15
consumidores, e incluso el idioma `with get_cursor() as cursor:` ya estaba en uso
en `app/controllers/estudiante_controller.py:388`. La migración adopta un patrón
existente del propio repositorio.

Equivalencia de comportamiento: `get_cursor()` sin `commit` no confirma, igual
que el código anterior, que tampoco confirmaba. Ante excepción revierte y
**relanza la misma excepción**, así que el llamador observa lo mismo que antes.
La única diferencia observable es la deseada: la conexión ahora vuelve al pool.

Único cambio en los literales SQL: la indentación, por quedar un nivel más
adentro. Tablas, columnas, joins, condiciones y parámetros son idénticos. Ambos
archivos ganaron además el salto de línea final que les faltaba.

### Caracterización

`tests/test_servicios_validacion.py`, 8 pruebas. Las cuatro funciones **no tenían
ninguna prueba** antes de esta subcapa; se verificó buscando referencias en
`tests/`.

Fijan lo observable: qué sentencia y qué parámetros se ejecutan, y que el retorno
es `True` con fila y `False` sin ella.

**Se comprobó que describen también el comportamiento anterior.** Desde el
directorio temporal de trabajo, sin tocar el repositorio, se recuperó con
`git show HEAD:` la versión original de ambos servicios, se ejecutó con un doble
de `get_connection` y se repitieron las 8 aserciones:

| Versión | Resultado |
|---|---|
| Código anterior, con `get_connection` | 8 de 8 se cumplen |
| Código migrado, con `get_cursor` | 8 de 8 se cumplen |

Por eso son pruebas de caracterización y no pruebas escritas a medida de la
implementación nueva.

### Efecto medido sobre el inventario

| Métrica | Antes de 1.2 | Después de 1.2 |
|---|---:|---:|
| Llamadas a `get_connection()` en `app/` | 146 | 142 |
| Protegidas con `try/finally` | 94 | 94 |
| **Sin cierre garantizado** | **50** | **46** |
| Propiedad delegada | 2 | 2 |

Los 4 sitios migrados salen del recuento porque ya no llaman `get_connection()`:
pasaron al régimen donde la infraestructura garantiza la devolución al pool.

### Verificación

| Comprobación | Resultado |
|---|---|
| Pruebas específicas | 8 pasaron en 0,16 s |
| Compuerta global | Exit 0 |
| Suite completa | **209** pasaron, 5 warnings conocidos, 1,20 s |
| Ruff | `All checks passed!` |
| `pip check` | `No broken requirements found.` |
| `git diff --check` | Exit 0 |

## Subcapa 1.3: resultado

### Tanda elegida

`app/controllers/planeador_anual_controller.py`. El archivo tiene 4 llamadas a
`get_connection()`, pero **solo 3 están desprotegidas**:

| Función | Operación | Acción |
|---|---|---|
| `crear_planeador_anual_controller` | `INSERT` + `commit` | Migrada a `get_cursor(commit=True)` |
| `obtener_planeadores_anual_controller` | `SELECT` | Migrada a `get_cursor()` |
| `actualizar_planeador_anual_controller` | `UPDATE` + `commit` | Migrada a `get_cursor(commit=True)` |
| `bulk_actualizar_planeadores_controller` | `INSERT`/`DELETE` en lote | **No tocada**: ya tiene `try/except/finally` con `rollback` |

La cuarta pertenece a los 94 sitios correctos y se dejó intacta. Su prueba
existente parchea `get_connection` en el módulo, por lo que el import de
`get_connection` se conserva junto al nuevo de `get_cursor`, con la misma forma
que ya usa `estudiante_controller.py`.

### Primera migración de escritura

1.2 solo tenía `SELECT`. Esta tanda estrena el camino con `commit`, donde el
error es más caro: si la migración perdiera el `commit`, `get_cursor` revertiría
al cerrar y **los datos se descartarían en silencio**, sin excepción ni error
visible.

Por eso la caracterización de esta subcapa no se conforma con el valor de
retorno: afirma explícitamente qué valor de `commit` recibe `get_cursor` en cada
función —`True`, `False`, `True`— además del SQL y los parámetros.

### Caracterización

Tres pruebas nuevas en `tests/test_planeador_anual_validaciones.py`, que ya era
el hogar de las pruebas de este controlador. No se creó un archivo aparte para
no fragmentar la cobertura del dominio.

**Verificación contra la versión anterior.** Igual que en 1.2, se recuperó el
controlador original con `git show HEAD:` y se repitieron las aserciones con un
doble de `get_connection`:

| Función | Código anterior | Código migrado |
|---|---|---|
| `crear` | id 501, `commit` sí | id 501, `commit=True` |
| `obtener` | 1 fila, `commit` no | 1 fila, `commit=False` |
| `actualizar` | `commit` sí | `commit=True` |

La primera ejecución de esa comprobación marcó dos discrepancias. Investigadas,
resultaron ser un defecto del propio script de verificación —no neutralizaba el
import de `resolver_asignacion_academica_id_cursor`, así que el resolver real
insertaba su consulta antes de la esperada—, no de la migración. Se corrigió el
script y las tres funciones quedaron en verde. Se registra porque demuestra que
la comprobación discrimina de verdad en lugar de aprobar por defecto.

### Efecto medido sobre el inventario

| Métrica | Tras 1.2 | Tras 1.3 |
|---|---:|---:|
| Llamadas a `get_connection()` en `app/` | 142 | 139 |
| Protegidas con `try/finally` | 94 | 94 |
| **Sin cierre garantizado** | **46** | **43** |

### Verificación

| Comprobación | Resultado |
|---|---|
| Pruebas del archivo | 8 pasaron en 0,20 s, 5 previas más 3 nuevas |
| Compuerta global | Exit 0 |
| Suite completa | **212** pasaron, 5 warnings conocidos, 1,07 s |
| Ruff | `All checks passed!` |
| `pip check` | `No broken requirements found.` |
| `git diff --check` | Exit 0 |

## Subcapa 1.4: resultado

### Tanda elegida

`app/controllers/usuario_controller.py`, 4 de sus 5 llamadas.
`obtener_usuarios_paginado_controller` ya tiene `try/finally` y se dejó intacta,
por lo que el import de `get_connection` se conserva junto al de `get_cursor`.

| Función | Operación | Destino |
|---|---|---|
| `crear_usuario_controller` | `INSERT` + `commit` | `get_cursor(commit=True)` |
| `obtener_usuarios_controller` | `SELECT` | `get_cursor()` |
| `actualizar_usuario_controller` | `UPDATE` + `commit` | `get_cursor(commit=True)` |
| `eliminar_usuario_controller` | `DELETE` + `commit` | `get_cursor(commit=True)` |

### Hallazgo: la primera fuga determinista

`actualizar_usuario_controller` no fugaba solo ante excepción. Abría la conexión
en su primera línea y salía por un `return` temprano cuando la petición no traía
campos que actualizar, **sin cerrar nunca**:

```python
conn = get_connection()          # abre
cursor = conn.cursor()
...                              # arma la lista de campos
if not updates:
    return {"error": "No hay campos para actualizar"}   # sale sin cerrar
```

Es un camino normal y trivialmente alcanzable: basta un `PATCH` con cuerpo vacío.
Diez peticiones así agotan el pool de 10. La conexión ni siquiera se usaba antes
del `return`.

Verificado empíricamente contra la versión anterior: en ese camino el código
original registró **1 conexión adquirida y 0 cerradas**.

La corrección mueve la construcción de la actualización delante del `with`, de
modo que el camino sin campos no adquiere ninguna conexión. Es la **única
diferencia de comportamiento intencional** de la subcapa: la respuesta devuelta
es idéntica, pero deja de ejecutarse el `SET search_path` que `get_connection()`
emitía sobre una conexión que se abandonaba de inmediato.

### Barrido de fugas deterministas en el resto del código

El hallazgo motivó revisar si el patrón se repetía. Se recorrió el AST de `app/`
buscando, entre las aperturas sin `try/finally`, aquellas con un `return` o
`raise` que salte el cierre en un camino normal:

| Gravedad | Sitios |
|---|---:|
| Fuga **condicional**, solo ante excepción | 38 |
| Fuga **determinista**, en camino normal | **1** |

El único caso restante es
`app/controllers/asignacion_controller.py:642`, `eliminar_asignacion_controller`:
si la asignación no existe, sale en la línea 655 sin cerrar. Un doble clic en
eliminar, o reintentar un borrado ya aplicado, basta para fugar.

**Debe ser la próxima tanda**, por delante de archivos con más sitios pero de
gravedad condicional. Corrige el inventario de 1.0, que clasificaba los 50 en un
único cajón sin distinguir gravedad.

### Caracterización

`tests/test_usuarios_controlador.py`, 7 pruebas. Las cuatro funciones no tenían
cobertura: `test_catalogos_pagination.py` prueba la **ruta** sustituyendo los
controladores por dobles.

Dos aserciones merecen mención:

- que la contraseña que llega al SQL sea la hasheada y nunca la original, en alta
  y en actualización;
- que la actualización sin campos **no pida conexión**, que es exactamente la
  fuga corregida.

Verificación contra la versión anterior recuperada con `git show HEAD:`: SQL,
parámetros, semántica de `commit` y respuesta coinciden en las cuatro funciones.

### Efecto medido sobre el inventario

| Métrica | Tras 1.3 | Tras 1.4 |
|---|---:|---:|
| Llamadas a `get_connection()` en `app/` | 139 | 135 |
| Protegidas con `try/finally` | 94 | 94 |
| **Sin cierre garantizado** | **43** | **39** |
| De ellas, deterministas | 2 | **1** |

### Verificación

| Comprobación | Resultado |
|---|---|
| Pruebas específicas | 7 pasaron en 0,22 s |
| Compuerta global | Exit 0 |
| Suite completa | **219** pasaron, 5 warnings conocidos, 1,12 s |
| Ruff | `All checks passed!` |
| `pip check` | `No broken requirements found.` |
| `git diff --check` | Exit 0 |

## Subcapa 1.4b: resultado

Tanda revisada con especial detalle a petición del usuario. Se migró el archivo
completo `app/controllers/asignacion_controller.py`: **6 sitios desprotegidos de
13**. Los otros 7 ya tenían `try/finally` y se dejaron intactos, por lo que el
import de `get_connection` se conserva.

| Función | Operación | Destino |
|---|---|---|
| `cursos_por_profesor_controller` | `SELECT` | `get_cursor()` |
| `profesor_por_curso_controller` | `SELECT` | `get_cursor()` |
| `obtener_horarios_admin_controller` | `SELECT` | `get_cursor()` |
| `eliminar_asignacion_controller` | `SELECT` + `UPDATE` + `commit` | `get_cursor(commit=True)` |
| `obtener_clases_profesor_controller` | `SELECT` | `get_cursor()` |
| `obtener_todas_asignaciones_controller` | `SELECT` | `get_cursor()` |

### Descubrimiento sobre `get_cursor` y el `return` temprano

`eliminar_asignacion_controller` sale por un `return` a mitad del bloque cuando
la asignación no existe. Antes de migrarla se comprobó **empíricamente**, no por
intuición, qué hace `get_cursor` en ese caso:

```
retorno            : salida temprana
commits ejecutados : 1
devuelta al pool   : True
```

Un `return` dentro del `with` invoca `__exit__(None, None, None)`, que en un
`@contextmanager` reanuda el generador después del `yield`. Por tanto **la línea
`if commit: connection.commit()` sí se ejecuta**.

Consecuencia registrada: en el camino «no encontrada» la versión migrada emite un
`COMMIT` sobre una transacción que solo hizo `SELECT`. La versión anterior no
emitía `COMMIT`, pero tampoco cerraba: abandonaba la conexión **con la
transacción abierta**. El `COMMIT` sobre una transacción de solo lectura no altera
ningún dato y sustituye a una fuga, por lo que se acepta y se documenta como
diferencia intencional.

Se descartó dividir la función en dos bloques `get_cursor` —uno de lectura y otro
de escritura— porque habría usado dos conexiones y roto la atomicidad entre la
comprobación y la actualización, abriendo una ventana de carrera. La corrección
de una fuga no justifica introducir un problema de concurrencia.

### La última fuga determinista

Con esta subcapa desaparece la única fuga en camino normal que quedaba en el
código:

| Gravedad | Tras 1.4 | Tras 1.4b |
|---|---:|---:|
| Fuga condicional, solo ante excepción | 38 | 33 |
| Fuga **determinista**, en camino normal | **1** | **0** |

Antes, intentar eliminar una asignación inexistente —un doble clic en el botón, o
reintentar un borrado ya aplicado— perdía una conexión de forma permanente.
Verificado contra la versión anterior: `adquiridas=1 cerradas=False commit=False`.

### Caracterización

`tests/test_asignaciones_controlador.py`, 7 pruebas. Ninguna de las seis
funciones tenía cobertura real previa.

Las dos rutas de `eliminar_asignacion_controller` se prueban por separado: la que
encuentra la asignación debe ejecutar `SELECT` y `UPDATE` y confirmar; la que no
la encuentra debe ejecutar **solo** el `SELECT` y devolver el mensaje sin tocar
nada.

Verificación contra la versión anterior recuperada con `git show HEAD:`: SQL,
parámetros, respuesta y semántica de `commit` coinciden en las seis funciones,
incluidos los dos caminos de la crítica.

### Nota sobre el SQL

Además de la indentación, en tres literales se eliminaron espacios en blanco al
final de línea que el código anterior arrastraba —`SELECT `, `ORDER BY `,
`WHERE a.dia IS NOT NULL `—. No era opcional: `git diff --check` rechaza líneas
nuevas con espacios finales, y la compuerta lo ejecuta. Tablas, columnas, joins,
condiciones, orden y parámetros son idénticos.

### Efecto medido sobre el inventario

| Métrica | Tras 1.4 | Tras 1.4b |
|---|---:|---:|
| Llamadas a `get_connection()` en `app/` | 135 | 129 |
| Protegidas con `try/finally` | 94 | 94 |
| **Sin cierre garantizado** | **39** | **33** |
| De ellas, deterministas | 1 | **0** |

### Verificación

| Comprobación | Resultado |
|---|---|
| Pruebas específicas | 7 pasaron en 0,18 s |
| Compuerta global | Exit 0 |
| Suite completa | **226** pasaron, 5 warnings conocidos, 1,18 s |
| Ruff | `All checks passed!` |
| `pip check` | `No broken requirements found.` |
| `git diff --check` | Exit 0 |
| Volumen del diff en `app/` | 117 inserciones, 148 supresiones, un archivo |

## Subcapa 1.4c: resultado

`app/controllers/branding_controller.py`, sus **4 sitios**, que eran todas sus
aperturas. Es el primer archivo del programa que deja de usar `get_connection`
por completo: el import quedó reducido a `get_cursor`.

| Función | Operación | Destino |
|---|---|---|
| `obtener_branding_controller` | `SELECT`, e `INSERT` si no hay fila | `get_cursor(commit=True)` |
| `actualizar_branding_controller` | `UPDATE` + `commit` | `get_cursor(commit=True)` |
| `subir_logo_controller` | `SELECT` + `UPDATE` + `commit`, con archivo | `get_cursor(commit=True)` |
| `eliminar_logo_controller` | `SELECT` + `UPDATE` + `commit`, con archivo | `get_cursor(commit=True)` |

### El commit condicional

`obtener_branding_controller` es un caso que no se había presentado: **confirmaba
solo a veces**. Lee la fila de branding y, si no existe, la crea con un `INSERT`
y entonces confirma. En el camino de lectura no confirmaba nada.

`get_cursor(commit=True)` confirma siempre. La diferencia quedó medida contra la
versión anterior:

| Camino | Código anterior | Código migrado |
|---|---|---|
| La fila existe, solo lectura | `commit=False` | `commit=True` |
| La fila no existe, la crea | `commit=True` | `commit=True` |

En el camino de lectura la versión anterior terminaba la transacción con el
`ROLLBACK` que `PooledConnection.close()` ejecuta siempre; la migrada la termina
con `COMMIT`. Sobre una transacción que solo hizo `SELECT` ambas son
equivalentes: no hay nada que confirmar ni que revertir. **Ningún dato cambia de
comportamiento**, y el camino de creación —el único que escribe— conserva su
confirmación.

Se descartó conservar `get_connection()` con `try/finally` para replicar el
condicional al pie de la letra. Habría sido válido según el contrato, pero añade
una tercera forma de escribir lo mismo sin corregir ningún riesgo real.

### El orden del borrado de archivos

`subir_logo_controller` y `eliminar_logo_controller` mezclan base de datos con
almacenamiento: tras actualizar la columna, borran el archivo anterior. Ese orden
importa y se conservó estrictamente: **el borrado ocurre después de cerrar el
bloque de base de datos**, no dentro.

Si se borrara dentro, un fallo entre el borrado y la confirmación dejaría el
archivo eliminado y la fila apuntando a él. Ambas pruebas lo fijan comprobando la
secuencia exacta de eventos:

```
['sql', 'sql', 'cierre_bloque', 'delete_file']
```

`eliminar_logo_controller` llama a `delete_file` incluso cuando no había logo
previo, es decir con `None`. Se conservó tal cual: cambiarlo habría sido corregir
un asunto ajeno a esta capa.

### Caracterización

`tests/test_branding_controlador.py`, 8 pruebas. Cubren los dos caminos de
`obtener_branding_controller`, los valores por defecto de color y
`configuracion_extra`, la doble conexión de `actualizar_branding_controller`
—escribe y después relee—, el rechazo de `slot` inválido con `400`, y el orden de
borrado en las dos funciones de logo.

`subir_logo_controller` es `async`; la prueba lo ejecuta con `asyncio.run`, sin
añadir `pytest-asyncio` ni ninguna dependencia.

Verificación contra la versión anterior recuperada con `git show HEAD:`:
respuesta, SQL, parámetros y orden de borrado coinciden en las cuatro funciones.
La única divergencia es la del commit condicional, descrita arriba y esperada.

### Efecto medido sobre el inventario

| Métrica | Tras 1.4b | Tras 1.4c |
|---|---:|---:|
| Llamadas a `get_connection()` en `app/` | 129 | 125 |
| Protegidas con `try/finally` | 94 | 94 |
| **Sin cierre garantizado** | **33** | **29** |
| Fugas deterministas | 0 | 0 |

### Verificación

| Comprobación | Resultado |
|---|---|
| Pruebas específicas | 8 pasaron en 0,35 s |
| Compuerta global | Exit 0 |
| Suite completa | **234** pasaron, 5 warnings conocidos, 1,15 s |
| Ruff | `All checks passed!` |
| `pip check` | `No broken requirements found.` |
| `git diff --check` | Exit 0 |

## Subcapa 1.4d: resultado

`app/controllers/dashboard_controller.py`, **4 sitios de 8**. Los otros 4 ya
tenían `try/finally`, por lo que el import conserva `get_connection`.

| Función | Operación | Destino |
|---|---|---|
| `obtener_inasistencias_profesor_controller` | `SELECT` con CTE y `ROW_NUMBER` | `get_cursor()` |
| `_obtener_notas_profesor` | `SELECT` con SQL dinámico | `get_cursor()` |
| `obtener_ranking_rendimiento_controller` | `SELECT` | `get_cursor()` |
| `obtener_ranking_mejor_rendimiento_controller` | `SELECT` | `get_cursor()` |

Las cuatro son de solo lectura y ninguna confirmaba. Se migraron a `get_cursor()`
sin `commit`, por lo que esta tanda **no tiene ninguna diferencia de
comportamiento**, ni siquiera de las inocuas que aparecieron en 1.4b y 1.4c.

### El caso con SQL dinámico

`_obtener_notas_profesor` es la función más delicada migrada hasta ahora en
cuanto a construcción de consulta: arma el SQL en función de dos ejes.

| Eje | Valores | Efecto |
|---|---|---|
| `altas` | `True` / `False` | `HAVING ... >= 3.0` con `ORDER BY promedio DESC`, o `< 3.0` con `ASC` |
| `asignacion_id` | presente / ausente | Agrega `AND asi.id = %s` y resuelve el id académico, o no |

Son cuatro combinaciones. El resolver `resolver_asignacion_academica_id_cursor`
se invoca **solo** cuando llega `asignacion_id`, y usa el mismo cursor, por lo
que la llamada permanece dentro del bloque.

También se fijó el color que la función asigna a cada fila, que no es simétrico:
`altas` siempre da `green`, mientras que en el caso de notas bajas da `red` si el
promedio baja de 3.0 y **`yellow` si no**. Ese último caso es alcanzable porque
el promedio mostrado se trunca por separado del filtro, y no tenía prueba.

### Caracterización

`tests/test_dashboard_controlador.py`, 7 pruebas. Ninguna de las cuatro funciones
tenía cobertura previa. Cubren las cuatro combinaciones de SQL dinámico, los tres
colores, el límite `posicion_curso <= 3` de inasistencias y los dos rankings.

Verificación contra la versión anterior recuperada con `git show HEAD:`: SQL,
parámetros, invocación del resolver, colores y respuesta coinciden en las cuatro
funciones, **sin ninguna divergencia**.

### Efecto medido sobre el inventario

| Métrica | Tras 1.4c | Tras 1.4d |
|---|---:|---:|
| Llamadas a `get_connection()` en `app/` | 125 | 121 |
| Protegidas con `try/finally` | 94 | 94 |
| **Sin cierre garantizado** | **29** | **25** |
| Fugas deterministas | 0 | 0 |

La mitad del trabajo de migración está hecha: de los 50 sitios iniciales quedan
25.

### Verificación

| Comprobación | Resultado |
|---|---|
| Pruebas específicas | 7 pasaron en 0,18 s |
| Compuerta global | Exit 0 |
| Suite completa | **241** pasaron, 5 warnings conocidos, 1,29 s |
| Ruff | `All checks passed!` |
| `pip check` | `No broken requirements found.` |
| `git diff --check` | Exit 0 |

## Subcapa 1.4e: resultado

`app/controllers/inventario_controller.py`, **3 sitios de 5**. Los otros 2 ya
tenían `try/finally`, por lo que el import conserva `get_connection`.

| Función | Operación | Destino |
|---|---|---|
| `obtener_inventario_controller` | `SELECT` con `WHERE` dinámico | `get_cursor()` |
| `crear_inventario_controller` | `INSERT` + `commit` | `get_cursor(commit=True)` |
| `actualizar_inventario_controller` | `UPDATE` + `commit` | `get_cursor(commit=True)` |

Es el primer archivo migrado que calcula dinero. No toca ventas ni saldos —el
stock se descuenta en `venta_controller`, que sigue reservado para el final—,
pero sí produce las cifras de costo, precio, utilidad y margen que el frontend
muestra al administrador.

### Aritmética fijada en pruebas

`_formatear_producto` no se tocó, pero al no tener prueba previa se caracterizó
junto con la migración, porque un cambio ahí sería visible como dinero incorrecto:

| Entrada | Resultado fijado |
|---|---|
| costo 1000, precio 1500, stock 4 | `utilidad_unitaria` 500,0; `utilidad_total_proyectada` 2000,0; `margen_utilidad` 33,33 |
| costo 0, precio 0, stock 1 | `margen_utilidad` 0, sin división por cero |

El segundo caso es una guarda real del código —`if precio > 0 else 0`— que ahora
queda protegida.

### Filtro de estado

`obtener_inventario_controller` arma el `WHERE` en tres variantes, todas
cubiertas:

| `estado` recibido | Comportamiento |
|---|---|
| Ausente, por defecto `activo` | Agrega el filtro con `activo` |
| `"todos"` | **No agrega `WHERE`** |
| Valor desconocido, p. ej. `descatalogado` | Normaliza a `activo` |

La normalización también se conserva en el `INSERT` y el `UPDATE`: un estado
inválido se guarda como `activo`.

### Caracterización

`tests/test_inventario_controlador.py`, 8 pruebas. Las existentes en
`test_inventario_pagination.py` cubren la función paginada, que está protegida y
no se migró.

Verificación contra la versión anterior recuperada con `git show HEAD:`: SQL,
parámetros, normalización de estado, aritmética de utilidad y semántica de
`commit` coinciden en las tres funciones, **sin divergencias**.

### Nota sobre el SQL

Se eliminaron espacios finales de línea que el código anterior arrastraba en
`UPDATE inventario ` y en dos líneas en blanco con sangría. Obligatorio: la
compuerta ejecuta `git diff --check`, que rechaza líneas nuevas con espacios
finales. Tablas, columnas, condiciones y parámetros son idénticos.

### Efecto medido sobre el inventario

| Métrica | Tras 1.4d | Tras 1.4e |
|---|---:|---:|
| Llamadas a `get_connection()` en `app/` | 121 | 118 |
| Protegidas con `try/finally` | 94 | 94 |
| **Sin cierre garantizado** | **25** | **22** |
| Fugas deterministas | 0 | 0 |

### Verificación

| Comprobación | Resultado |
|---|---|
| Pruebas específicas | 8 pasaron en 0,16 s |
| Compuerta global | Exit 0 |
| Suite completa | **249** pasaron, 5 warnings conocidos |
| Ruff | `All checks passed!` |
| `pip check` | `No broken requirements found.` |
| `git diff --check` | Exit 0 |

## Subcapa 1.4f: resultado

`app/controllers/profesor_controller.py`, **1 sitio de 6**. Los otros 5 ya
tenían `try/finally`, por lo que el import conserva `get_connection`.

| Función | Operación | Destino |
|---|---|---|
| `obtener_clases_profesor_controller` | `SELECT` | `get_cursor()` |

Tanda pequeña y sin ninguna diferencia de comportamiento: la función es de solo
lectura y no confirmaba.

### Una homonimia que conviene no confundir

Existe otra función llamada `obtener_clases_profesor_controller` en
`asignacion_controller.py`, migrada en 1.4b. Consultan lo mismo, pero **no son
equivalentes**:

| Versión | Filtros |
|---|---|
| `asignacion_controller` | `a.activo = TRUE` y estado activo de curso y materia |
| `profesor_controller` | **Ninguno** |

La de este archivo devuelve también asignaciones desactivadas y de cursos o
materias inactivos. La diferencia es anterior a la migración y se conservó tal
cual: corregirla sería un cambio funcional ajeno al alcance de la capa.

Se agregó una prueba que afirma explícitamente que esta consulta **no** filtra,
para que la ausencia quede registrada como comportamiento observado y no se
confunda con un descuido de la migración. Queda anotado como deuda conocida para
quien decida más adelante si las dos funciones deben unificarse.

### Caracterización

`tests/test_profesores_controlador.py`, 3 pruebas: la forma de la respuesta, la
ausencia de filtros y el caso sin asignaciones.

Verificación contra la versión anterior recuperada con `git show HEAD:`: SQL,
parámetros y respuesta coinciden, y la ausencia de filtros se confirmó también en
el código original.

### Efecto medido sobre el inventario

| Métrica | Tras 1.4e | Tras 1.4f |
|---|---:|---:|
| Llamadas a `get_connection()` en `app/` | 118 | 117 |
| Protegidas con `try/finally` | 94 | 94 |
| **Sin cierre garantizado** | **22** | **21** |
| Fugas deterministas | 0 | 0 |

### Verificación

| Comprobación | Resultado |
|---|---|
| Pruebas específicas | 3 pasaron en 0,22 s |
| Compuerta global | Exit 0 |
| Suite completa | **252** pasaron, 5 warnings conocidos, 1,32 s |
| Ruff | `All checks passed!` |
| `pip check` | `No broken requirements found.` |
| `git diff --check` | Exit 0 |

## Subcapa 1.4g: resultado

`app/controllers/asistencia_controller.py`, **1 sitio de 2**.

| Función | Estado |
|---|---|
| `guardar_asistencia_controller` | **No tocada.** Ya protegida con `try/except/finally`; es el reemplazo parcial transaccional con `rollback` que el inventario de contratos de 0.0 registró como efecto a preservar |
| `obtener_historial_asistencia` | Migrada a `get_cursor()` |

Sin diferencias de comportamiento: la función migrada es de solo lectura y no
confirmaba.

### Detalles de la transformación

- **La agrupación se movió fuera del bloque.** La función construye un
  diccionario por estudiante a partir de las filas ya traídas; hacerlo después de
  cerrar es cálculo puro sobre memoria, sin diferencia observable, y libera la
  conexión antes.
- **Las líneas en blanco dentro del literal SQL se conservaron vacías.** El
  `SELECT` tiene saltos sueltos entre el `FROM` y el `JOIN`; al reindentar había
  que dejarlas sin sangría, porque `git diff --check` rechaza líneas nuevas con
  espacios finales y la compuerta lo ejecuta.

### Comportamiento conservado que no era evidente

La función solo añade una entrada al historial cuando la fila trae fecha. Un
estudiante cuya fila tiene `fecha` nula **aparece igualmente en la respuesta, con
el historial vacío**. Es anterior a la migración; se fijó en pruebas tal cual, sin
cambiarlo.

También se fijó que el `periodo` toma el valor 1 por defecto y que la agrupación
reúne varias fechas del mismo estudiante en una sola entrada.

### Caracterización

`tests/test_asistencia_historial.py`, 5 pruebas. Las existentes en
`test_asistencia_validaciones.py` cubren el guardado transaccional, que no se
tocó.

Verificación contra la versión anterior recuperada con `git show HEAD:`: SQL,
parámetros, resolución de la asignación, agrupación y respuesta coinciden, **sin
divergencias**.

### Efecto medido sobre el inventario

| Métrica | Tras 1.4f | Tras 1.4g |
|---|---:|---:|
| Llamadas a `get_connection()` en `app/` | 117 | 116 |
| Protegidas con `try/finally` | 94 | 94 |
| **Sin cierre garantizado** | **21** | **20** |
| Fugas deterministas | 0 | 0 |

### Verificación

| Comprobación | Resultado |
|---|---|
| Pruebas específicas | 5 pasaron en 0,16 s |
| Compuerta global | Exit 0 |
| Suite completa | **257** pasaron, 5 warnings conocidos, 1,22 s |
| Ruff | `All checks passed!` |
| `pip check` | `No broken requirements found.` |
| `git diff --check` | Exit 0 |

## Subcapa 1.4h: resultado

Tanda revisada con especial detalle a petición del usuario.
`app/controllers/notas_controller.py`, **5 sitios de 5**: el archivo entero
estaba desprotegido. Segundo archivo del programa que abandona `get_connection`
por completo.

| Función | Operación | Destino |
|---|---|---|
| `crear_nota_controller` | `INSERT` + `commit` | `get_cursor(commit=True)` |
| `notas_estudiante_controller` | `SELECT` | `get_cursor()` |
| `boletin_estudiante_controller` | `SELECT` con CTE | `get_cursor()` |
| `planilla_asignacion_controller` | `SELECT` con CTE y resolver | `get_cursor()` |
| `boletin_detallado_controller` | `SELECT` + N+1 en bucle | `get_cursor()` |

### Dos imports locales redundantes eliminados

`boletin_estudiante_controller` y `boletin_detallado_controller` repetían
`from app.database import get_connection` **dentro del cuerpo de la función**,
además del import del módulo. Al migrar quedaban muertos, así que se retiraron.
No era opcional: Ruff habría marcado el import sin usar y la compuerta habría
fallado.

### El patrón N+1 se conserva

`boletin_detallado_controller` consulta las asignaciones del estudiante y después
ejecuta **una consulta por cada asignación** dentro del bucle. Un boletín de doce
materias son trece consultas.

Se conservó tal cual y se fijó en una prueba que cuenta las consultas: dos
asignaciones producen tres llamadas a `execute`. Optimizarlo pertenece a la capa
4, que es la que autoriza eliminar N+1 mediante consultas agrupadas equivalentes;
hacerlo aquí sería ampliar el alcance.

La ventaja de migrarlo ahora es que las trece consultas comparten una sola
conexión gobernada por `get_cursor`, en vez de una conexión que se perdía entera
si cualquiera de las trece fallaba.

### Comportamientos que no eran evidentes y quedaron fijados

- **`crear_nota_controller` no pide conexión si falla una validación.** Sus tres
  comprobaciones —asignación, estudiante y pertenencia al curso— devuelven un
  error antes de abrir nada. Verificado: en ese camino la versión anterior
  registró **cero conexiones adquiridas**, así que no fugaba.
- **`boletin_detallado_controller` sí cerraba en su salida temprana.** Cuando el
  estudiante no tiene asignaciones, la versión anterior cerraba cursor y conexión
  antes de devolver `[]`. No era una fuga determinista; el barrido de 1.4 ya lo
  había clasificado bien.
- **Los ids de las actividades en blanco son sintéticos.** Cuando una materia no
  tiene notas, el boletín fabrica tres actividades cuyo id se arma concatenando
  cadenas: materia 5 produce 501, 502 y 503. Puede colisionar con ids reales de
  `notas_detalle`. Se conserva sin cambios y queda anotado como deuda conocida.
- **El corte Aprobado/Reprobado está en 3.0 inclusive** y el promedio general no
  tiene guarda de división por cero, aunque el `return` previo por resultado
  vacío la hace inalcanzable.
- **`notas_estudiante_controller` devuelve promedio 0 sin notas**, por su guarda
  `if cantidad > 0`.

### Caracterización

`tests/test_notas_controlador.py`, 14 pruebas. Ninguna de las cinco funciones
tenía cobertura: las pruebas existentes de notas cubren permisos en la ruta, no
estos cálculos.

Verificación contra la versión anterior recuperada con `git show HEAD:`: 12
comprobaciones sobre SQL, parámetros, promedios, redondeos, corte
Aprobado/Reprobado, ids sintéticos, conteo de consultas del N+1 y semántica de
`commit`. Todas coinciden, **sin divergencias**.

### Efecto medido sobre el inventario

| Métrica | Tras 1.4g | Tras 1.4h |
|---|---:|---:|
| Llamadas a `get_connection()` en `app/` | 116 | 111 |
| Protegidas con `try/finally` | 94 | 94 |
| **Sin cierre garantizado** | **20** | **15** |
| Fugas deterministas | 0 | 0 |

### Verificación

| Comprobación | Resultado |
|---|---|
| Pruebas específicas | 14 pasaron en 0,19 s |
| Compuerta global | Exit 0 |
| Suite completa | **271** pasaron, 5 warnings conocidos, 1,15 s |
| Ruff | `All checks passed!` |
| `pip check` | `No broken requirements found.` |
| `git diff --check` | Exit 0 |
| Volumen del diff en `app/` | 157 inserciones, 186 supresiones, un archivo |

## Subcapa 1.4i: resultado

`app/controllers/plantilla_controller.py`, **7 sitios de 7**: el archivo entero.
Tercer archivo del programa que abandona `get_connection` por completo.

| Función | Operación | Destino |
|---|---|---|
| `listar_plantillas_controller` | `SELECT` con o sin filtro | `get_cursor()` |
| `obtener_plantilla_activa_controller` | `SELECT` + fallback | `get_cursor()` |
| `crear_plantilla_controller` | `INSERT` + `commit` | `get_cursor(commit=True)` |
| `actualizar_plantilla_controller` | `SELECT` + `UPDATE` + `commit` | `get_cursor(commit=True)` |
| `activar_plantilla_controller` | `SELECT` + dos `UPDATE` + `commit` | `get_cursor(commit=True)` |
| `duplicar_plantilla_controller` | `SELECT` + `INSERT` + `commit` | `get_cursor(commit=True)` |
| `eliminar_plantilla_controller` | `SELECT` + `DELETE` + `commit` | `get_cursor(commit=True)` |

### Un archivo que ya estaba bien escrito

A diferencia de tandas anteriores, este autor **cerraba explícitamente antes de
cada salida temprana**: los `raise HTTPException` de 404 y 400 van precedidos de
`cursor.close()` y `conn.close()` en los siete casos. Por eso el barrido de fugas
deterministas de 1.4 no marcó este archivo.

Se verificó contra la versión anterior: en el camino de tipo inválido de
`listar_plantillas_controller`, el código original registró **1 conexión
adquirida y cerrada**. No fugaba.

Lo que aporta la migración aquí no es tapar una fuga existente, sino garantizar
el cierre cuando un `execute` lance: ese camino sí quedaba descubierto, y además
elimina 14 líneas de cierre manual repetido.

### La única diferencia de comportamiento

`actualizar_plantilla_controller` tiene un camino «Sin cambios»: si la petición no
trae ni nombre ni configuración, devuelve ese mensaje sin ejecutar el `UPDATE`.
La versión anterior no confirmaba ahí; la migrada sí, porque el bloque se abre con
`commit=True` y sale de forma normal.

Es una transacción que solo ejecutó un `SELECT`, así que el `COMMIT` no altera
ningún dato y sustituye al `ROLLBACK` implícito de `PooledConnection.close()`. Es
la misma situación ya registrada en 1.4b y 1.4c.

### Comportamientos fijados en pruebas

- **Fallback de plantilla activa**: si no hay ninguna marcada activa para el tipo,
  cae a la primera predefinida; si tampoco existe, `404`.
- **Atomicidad de la activación**: los dos `UPDATE` —desactivar las demás del tipo
  y activar esta— viajan en la **misma transacción**. Partirlos habría permitido
  dejar el tipo sin ninguna plantilla activa.
- **Las plantillas predefinidas están protegidas**: `400` al editarlas y `400` al
  eliminarlas, con el mensaje que invita a duplicar.
- **Al duplicar sin nombre** se genera `"<origen> (copia)"`.
- **Las plantillas nuevas nacen inactivas y no predefinidas**, con
  `VALUES (%s, %s, FALSE, FALSE, %s)`.
- Los tipos inválidos responden `400` **sin consultar la base**, salvo en
  `listar_plantillas_controller`, donde la validación ocurre ya dentro del bloque.
  Se conservó esa asimetría; moverla sería un cambio ajeno al alcance.

### Caracterización

`tests/test_plantillas_controlador.py`, 19 pruebas. Ninguna de las siete
funciones tenía cobertura previa.

Verificación contra la versión anterior recuperada con `git show HEAD:`: 18
comprobaciones sobre SQL, parámetros, códigos de estado, fallback, atomicidad,
nombre por defecto y `commit`. Todas coinciden salvo la diferencia del camino
«Sin cambios», que estaba prevista.

### Efecto medido sobre el inventario

| Métrica | Tras 1.4h | Tras 1.4i |
|---|---:|---:|
| Llamadas a `get_connection()` en `app/` | 111 | 104 |
| Protegidas con `try/finally` | 94 | 94 |
| **Sin cierre garantizado** | **15** | **8** |
| Fugas deterministas | 0 | 0 |

### Reparto real de los 8 sitios restantes

Al localizarlos se corrigió una expectativa equivocada: **no todos pertenecen a
dominios financieros**, y `ventas` ya no tiene ninguno.

| Archivo | Sitios | Dominio |
|---|---:|---|
| `app/controllers/planilla_controller.py` | 2 | Académico |
| `app/controllers/estudiante_controller.py` | 2 | Reservado |
| `app/controllers/planilla_excel_controller.py` | 1 | Académico, genera Excel |
| `app/routes/asignaciones.py` | 1 | Académico, apertura en una ruta |
| `app/routes/observaciones.py` | 1 | Académico, apertura en una ruta |
| `app/controllers/pagos_controller.py` | 1 | Reservado, `historial_pagos_controller` |

Solo **3 de los 8** están en dominios reservados. Los otros 5 son académicos, y
dos de ellos son las únicas aperturas que quedan **fuera de controllers y
services**: están en archivos de rutas.

Siguen aparte los 2 sitios de propiedad delegada en `super_admin`, que desde 1.0
no cuentan como desprotegidos: abren y devuelven la conexión para que el llamador
la cierre.

### Verificación

| Comprobación | Resultado |
|---|---|
| Pruebas específicas | 19 pasaron en 0,37 s |
| Compuerta global | Exit 0 |
| Suite completa | **290** pasaron, 5 warnings conocidos, 1,23 s |
| Ruff | `All checks passed!` |
| `pip check` | `No broken requirements found.` |
| `git diff --check` | Exit 0 |
| Volumen del diff en `app/` | 129 inserciones, 166 supresiones, un archivo |

## Subcapa 1.4j: resultado

Dominio planilla completo, **3 sitios en 2 archivos**. Ambos archivos abandonan
`get_connection` por completo.

| Archivo y función | Operación | Destino |
|---|---|---|
| `planilla_controller.registrar_nota_planilla_controller` | `DELETE` + `INSERT` + `commit` | `get_cursor(commit=True)` |
| `planilla_controller.eliminar_tipo_controller` | `DELETE` + `commit` | `get_cursor(commit=True)` |
| `planilla_excel_controller.planilla_excel_controller` | `SELECT` | `get_cursor()` |

Sin diferencias de comportamiento: los dos que escriben ya confirmaban siempre y
el de lectura nunca confirmaba.

### El par borrar/insertar debe seguir siendo atómico

`registrar_nota_planilla_controller` evita notas duplicadas borrando primero la
nota existente con la misma descripción y luego insertando la nueva. Los dos
`execute` viajan en **una sola transacción**, y así se conservó.

Partirlos en dos bloques `get_cursor` habría abierto una ventana en la que un
fallo entre el borrado y la inserción deja al estudiante **sin la nota anterior y
sin la nueva**. Es el mismo criterio aplicado en 1.4b con
`eliminar_asignacion_controller` y en 1.4i con la activación de plantillas.

### Dos rarezas heredadas que quedaron documentadas

`planilla_excel_controller`, pese al nombre, **no genera ningún Excel**: devuelve
un diccionario con columnas y datos, y es la ruta quien arma el archivo.

Dentro tiene dos comportamientos que no eran evidentes y ahora están fijados en
pruebas:

- **Descarta la descripción `"Desde React"`.** Es una cadena mágica heredada: las
  notas con esa descripción no aparecen como columna ni en el detalle del
  estudiante.
- **Devuelve `promedio` como cadena vacía**, no como `0` ni `None`, cuando el
  estudiante no tiene ninguna nota de tipo numérico. El campo cambia de tipo
  según los datos, lo que el frontend debe estar tolerando hoy.

Solo se caracterizaron; cambiarlas sería un cambio funcional ajeno al alcance.

También se fijó que las notas de tipo `desarrollo` **no entran en el promedio**, y
que en ese tipo se guarda `valoracion` y se descarta `nota`.

### Caracterización

`tests/test_planilla_controlador.py`, 10 pruebas. Ninguno de los tres sitios
tenía cobertura previa.

Verificación contra la versión anterior recuperada con `git show HEAD:`: 10
comprobaciones sobre SQL, parámetros, el par borrar/insertar, la distinción entre
evaluación numérica y de desarrollo, el filtro heredado, el promedio como cadena
vacía, el orden por apellido y la semántica de `commit`. Todas coinciden, **sin
divergencias**.

### Efecto medido sobre el inventario

| Métrica | Tras 1.4i | Tras 1.4j |
|---|---:|---:|
| Llamadas a `get_connection()` en `app/` | 104 | 101 |
| Protegidas con `try/finally` | 94 | 94 |
| **Sin cierre garantizado** | **8** | **5** |
| Fugas deterministas | 0 | 0 |

### Los 5 sitios que quedan

| Archivo | Sitios | Nota |
|---|---:|---|
| `app/controllers/estudiante_controller.py` | 2 | Dominio reservado |
| `app/controllers/pagos_controller.py` | 1 | Dominio reservado, `historial_pagos_controller` |
| `app/routes/asignaciones.py` | 1 | Apertura en la capa HTTP |
| `app/routes/observaciones.py` | 1 | Apertura en la capa HTTP |

### Verificación

| Comprobación | Resultado |
|---|---|
| Pruebas específicas | 10 pasaron en 0,19 s |
| Compuerta global | Exit 0 |
| Suite completa | **300** pasaron, 5 warnings conocidos |
| Ruff | `All checks passed!` |
| `pip check` | `No broken requirements found.` |
| `git diff --check` | Exit 0 |

## Subcapa 1.4k: resultado

Las **2 aperturas que vivían en la capa HTTP**, únicas de su tipo en todo el
código. Con esta tanda, **ninguna ruta abre conexiones**: todas las aperturas
restantes están en controllers.

| Archivo y función | Operación | Destino |
|---|---|---|
| `app/routes/asignaciones.py`, `obtener_clases_profesor` | `SELECT` | `get_cursor()` |
| `app/routes/observaciones.py`, `obtener_observacion` | `SELECT` + resolver | `get_cursor()` |

En `observaciones.py` había además un **import local** de `get_connection` dentro
de la función; se sustituyó por el import del módulo, como ya se hizo en 1.4h.

### Una prueba existente se puso en rojo

Al migrar `obtener_clases_profesor`, la prueba
`test_mis_clases_incluye_jornada_del_curso` de
`tests/test_asignaciones_pagination.py` falló: parcheaba
`asignaciones.get_connection`, un símbolo que dejó de existir en el módulo.

Es exactamente el comportamiento deseado de la red de seguridad: el cambio de
régimen quedó visible de inmediato en vez de pasar inadvertido.

Se adaptó **solo el mecanismo de sustitución**, cambiando el doble de conexión
por un doble de `get_cursor`. Las aserciones de la prueba se conservaron palabra
por palabra: la forma completa de la respuesta y la presencia de `c.jornada` en
la consulta. `FakeConnection`, que quedaba sin uso, se retiró.

Queda como precedente: al migrar un módulo, hay que comprobar si alguna prueba
existente parchea `get_connection` sobre él.

### Caracterización

`tests/test_observaciones_ruta.py`, 4 pruebas. La ruta de observaciones no tenía
cobertura: las pruebas existentes cubren las validaciones del controlador, no
esta consulta.

Se fija que **los guards de permiso se ejecutan antes de tocar la base** —y que
si uno rechaza, no se abre cursor ni se ejecuta consulta— y que la ruta devuelve
`None` cuando no hay observación guardada, en vez de un `404` o un diccionario
vacío. Ese `None` es el contrato que el frontend está consumiendo hoy.

Verificación contra la versión anterior recuperada con `git show HEAD:`: SQL,
parámetros, orden de los guards, respuesta y cierre coinciden en ambas rutas.

### Efecto medido sobre el inventario

| Métrica | Tras 1.4j | Tras 1.4k |
|---|---:|---:|
| Llamadas a `get_connection()` en `app/` | 101 | 99 |
| Protegidas con `try/finally` | 94 | 94 |
| **Sin cierre garantizado** | **5** | **3** |
| Aperturas fuera de controllers y services | 2 | **0** |
| Fugas deterministas | 0 | 0 |

### Verificación

| Comprobación | Resultado |
|---|---|
| Pruebas específicas | 7 pasaron, incluida la existente adaptada |
| Compuerta global | Exit 0 |
| Suite completa | **304** pasaron, 5 warnings conocidos, 1,56 s |
| Ruff | `All checks passed!` |
| `pip check` | `No broken requirements found.` |
| `git diff --check` | Exit 0 |

## Subcapa 1.4l: resultado

Primer dominio financiero reservado. `app/controllers/pagos_controller.py`,
**1 sitio de 7**: los otros seis ya tenían `try/finally`, incluidos los que
mueven montos, aplican saldos y anulan. El import conserva `get_connection`.

| Función | Operación | Destino |
|---|---|---|
| `historial_pagos_controller` | `SELECT` | `get_cursor()` |

Es de solo lectura y no confirmaba, así que **no hay ninguna diferencia de
comportamiento**. Que el único sitio desprotegido del dominio de pagos fuera una
consulta —y no una escritura de dinero— es un hallazgo tranquilizador: las rutas
que tocan saldos ya estaban protegidas antes de este programa.

### El formato del dinero, fijado en pruebas

`_formatear_pago` no se modificó, pero se caracterizó porque produce lo que el
administrador ve en pantalla y no tenía ninguna prueba:

| Campo | Comportamiento fijado |
|---|---|
| `monto` | Se convierte a `float` |
| `fecha` | `"%d/%m/%Y %I:%M %p"`, p. ej. `03/08/2026 02:30 PM` |
| `fecha` nula | Cadena vacía, no `None` |
| `estado` ausente | Se asume `"Pagado"` |
| `anulado` | Derivado del estado, ignorando mayúsculas y espacios: `"  ANULADO  "` cuenta |
| `fecha_anulacion` nula | `None`, no cadena vacía |

La asimetría entre `fecha` vacía y `fecha_anulacion` nula es heredada; se
conserva tal cual.

Los campos de auditoría de anulación —motivo, fecha y responsable— también
quedaron fijados, por ser el rastro de una operación financiera reversible.

### Caracterización

`tests/test_pagos_historial.py`, 6 pruebas. La función no tenía cobertura real:
`test_pagos_pagination.py` sustituye el controlador al probar la ruta.

Verificación contra la versión anterior recuperada con `git show HEAD:`: SQL,
parámetros, monto, formato de fechas, estado por defecto, bandera de anulación y
campos de auditoría coinciden, **sin divergencias**.

### Efecto medido sobre el inventario

| Métrica | Tras 1.4k | Tras 1.4l |
|---|---:|---:|
| Llamadas a `get_connection()` en `app/` | 99 | 98 |
| Protegidas con `try/finally` | 94 | 94 |
| **Sin cierre garantizado** | **3** | **2** |
| Fugas deterministas | 0 | 0 |

Quedan **2 sitios**, ambos en `app/controllers/estudiante_controller.py`:
`crear_estudiante_controller` y `actualizar_estudiante_controller`.

### Verificación

| Comprobación | Resultado |
|---|---|
| Pruebas específicas | 6 pasaron en 0,19 s |
| Compuerta global | Exit 0 |
| Suite completa | **310** pasaron, 5 warnings conocidos, 1,40 s |
| Ruff | `All checks passed!` |
| `pip check` | `No broken requirements found.` |
| `git diff --check` | Exit 0 |

## Subcapa 1.4m: resultado — migración completa

Los **2 últimos sitios**, ambos en `app/controllers/estudiante_controller.py`.
Con ellos, el recuento de aperturas sin cierre garantizado llega a **cero**.

| Función | Operación | Destino |
|---|---|---|
| `crear_estudiante_controller` | `INSERT` de 35 columnas + `commit` | `get_cursor(commit=True)` |
| `actualizar_estudiante_controller` | `UPDATE` de 35 columnas + `commit` | `get_cursor(commit=True)` |

Sin diferencias de comportamiento: ambas confirmaban siempre y siguen haciéndolo,
incluido el camino en que la actualización no encuentra al estudiante.

### El riesgo real de estas dos: el orden de 35 parámetros

Ninguna de las dos valida nada por posición. Un desplazamiento silencioso en la
lista guardaría el teléfono del padre en el campo de la madre **sin lanzar ningún
error** y sin que ninguna prueba anterior lo notara.

Por eso la caracterización no comprueba solo que el SQL contenga `INSERT`: cada
campo lleva **su propio nombre como valor**, y la prueba afirma que la tupla de
parámetros es exactamente la lista de los 34 campos en orden, más el estado, más
el id en la actualización.

### La regla de estado al actualizar

La consulta usa `estado = COALESCE(%s, estado, 'activo')`. El controlador envía
`None` cuando la petición no trae estado, y ese `None` hace que **se conserve el
estado ya guardado** en vez de sobrescribirlo. No es evidente leyendo solo el
Python; quedó fijado en prueba junto con el fragmento de SQL que lo implementa.

Al crear, en cambio, el estado siempre se normaliza: `"  ACTIVO  "` se guarda
como `activo`.

### Caracterización

`tests/test_estudiantes_controlador.py`, 5 pruebas. Ninguna de las dos funciones
tenía cobertura: `test_estudiantes_pagination.py` cubre el listado paginado, que
ya estaba protegido.

Verificación contra la versión anterior recuperada con `git show HEAD:`: SQL,
orden completo de los parámetros, normalización de estado, regla `COALESCE`,
respuestas y `commit` coinciden, **sin divergencias**.

### Estado final del inventario

| Métrica | Al abrir la capa | Ahora |
|---|---:|---:|
| Llamadas a `get_connection()` en `app/` | 146 | **96** |
| Protegidas con `try/finally` | 94 | 94 |
| **Sin cierre garantizado** | **50** | **0** |
| De ellas, deterministas | 2 | **0** |
| Propiedad delegada | 2 | 2 |
| Aperturas fuera de controllers y services | 2 | 0 |
| Pruebas de la suite | 192 | **315** |

Los 2 sitios de propiedad delegada —`_public_connection` en
`super_admin_controller` y `_with_public_connection` en `core/super_admin`— no
son fugas: abren y devuelven la conexión para que el llamador la cierre, tal como
se clasificó en 1.0. Quedan como el único patrón de apertura que no usa
`get_cursor`.

### Verificación

| Comprobación | Resultado |
|---|---|
| Pruebas específicas | 5 pasaron en 0,19 s |
| Compuerta global | Exit 0 |
| Suite completa | **315** pasaron, 5 warnings conocidos |
| Ruff | `All checks passed!` |
| `pip check` | `No broken requirements found.` |
| `git diff --check` | Exit 0 |

## Subcapa 1.5: resultado

Antes de esta subcapa **no existía ningún timeout** en el proyecto: ni en `app/`,
ni en la creación del pool, ni en `.env`. Una consulta lenta o un lock retenido
podían ocupar una conexión de forma indefinida.

### Lo que se añadió

Cuatro ajustes en `app/config.py`, todos configurables por entorno:

| Ajuste | Valor por defecto | Qué protege |
|---|---:|---|
| `DB_CONNECT_TIMEOUT_SECONDS` | 10 s | Que la app no cuelgue si la base no responde |
| `DB_STATEMENT_TIMEOUT_MS` | 30 000 ms | Que una consulta lenta no ocupe una conexión sin límite |
| `DB_LOCK_TIMEOUT_MS` | 10 000 ms | Que esperar un lock no bloquee un worker indefinidamente |
| `DB_IDLE_IN_TRANSACTION_TIMEOUT_MS` | 60 000 ms | Que una transacción abandonada libere su conexión |

El último se eligió deliberadamente: es la defensa del servidor contra la clase
de fallo que 1.4 corrigió en el código. Si alguna vez vuelve a quedar una
conexión con transacción abierta, PostgreSQL la reclama en un minuto en vez de
retenerla para siempre.

### Cómo se aplican, y por qué no de la forma obvia

El primer intento los envió en el parámetro `options` del paquete de arranque, en
`_create_pool()`. **Rompió el arranque contra la base real** y está documentado
como incidente más abajo. La forma correcta resultó ser otra:

| Ajuste | Dónde se aplica | Por qué |
|---|---|---|
| `connect_timeout` | Parámetro del pool | Es de **libpq**, se resuelve en el cliente y nunca viaja al servidor. Compatible con cualquier endpoint |
| Los otros tres | `set_config(nombre, valor, TRUE)` al tomar la conexión | Son GUCs de servidor. Van como consulta normal, no en el arranque |

El tercer argumento de `set_config` en `TRUE` equivale a **`SET LOCAL`**: el
ajuste dura lo que dura la transacción y se revierte al terminarla. Eso es
justamente lo que lo hace seguro detrás de un endpoint agrupado en modo
transacción, donde una conexión se recicla entre clientes y un `SET` de sesión
podría filtrarse al siguiente.

Los tres viajan en **una sola sentencia**, con los valores ligados como
parámetros en vez de interpolados:

```sql
SELECT set_config(%s, %s, TRUE), set_config(%s, %s, TRUE), set_config(%s, %s, TRUE)
```

Coste: un viaje extra a la base al tomar cada conexión, sumado al que ya hacía
para fijar el `search_path`.

### La decisión que más importa: 0 omite, no desactiva

`_timeouts_de_sesion()` **omite** cualquier ajuste con valor 0 en lugar de
enviarlo.

Es una diferencia con consecuencias reales. Enviar `statement_timeout = 0`
significa «sin límite» de forma explícita y **pisaría cualquier valor por
defecto que el proveedor de hosting tenga configurado**. Omitirlo deja que ese
valor prevalezca. Con esta forma, poner 0 en el `.env` significa «no opines», que
es lo que uno espera de una configuración.

Lo mismo con `connect_timeout`: si vale 0, no se pasa el parámetro.

### Comportamiento del pool, medido y no supuesto

El índice maestro pide evidencia, no descripción. Se midió construyendo un
`ThreadedConnectionPool` **auténtico** de psycopg2 con `psycopg2.connect`
sustituido por un doble, de modo que no hace falta PostgreSQL.

| Comportamiento observado | Resultado |
|---|---|
| Pool agotado | Lanza `PoolError("connection pool exhausted")` **de inmediato**; no espera |
| Devolver una conexión | Vuelve a estar disponible y se reutiliza la misma instancia |
| Máximo respetado | Nunca se abren más conexiones que `maxconn` |
| Devolución con transacción abierta | **El pool ejecuta `rollback()`** antes de reutilizarla |
| Devolución en estado desconocido | El pool **cierra** la conexión en vez de reutilizarla |
| `closeall()` | Cierra todas las conexiones creadas |
| `get_pool()` | Devuelve siempre la misma instancia; solo crea una vez |

Que el pool **falle rápido** en vez de esperar es la propiedad más importante de
la tabla: significa que agotar el pool produce peticiones con error, no workers
colgados. Un fallo visible es preferible a una aplicación que deja de responder
sin decir por qué.

Los dos comportamientos de `putconn` —revertir si hay transacción abierta,
cerrar si el estado es desconocido— se descubrieron al fallar el primer intento
de prueba: el doble de conexión no tenía `info.transaction_status` y psycopg2 lo
consultaba. La corrección reveló que **el pool tiene su propia red de seguridad**,
independiente de la de `get_cursor`. Se registra porque no estaba documentado en
ninguna parte del proyecto.

### Riesgo asumido y evidencia que falta

`statement_timeout` es el único ajuste que puede **romper algo que hoy
funciona**: una consulta legítima que tarde más de 30 s pasará a fallar. Se eligió
30 s por ser muy holgado para una petición HTTP —un cliente web normalmente ya
abandonó antes—, pero **no está calibrado contra los tiempos reales de este
sistema**.

Esa calibración no puede hacerse con pruebas herméticas: exige medir la duración
de las consultas pesadas —boletines, planillas, reportes financieros— sobre datos
comparables a producción. Queda como **verificación pendiente**, del mismo tipo
que la ejecución remota de CI en la capa 0: registrada, no dada por cumplida.

Mitigación disponible sin tocar código: subir `DB_STATEMENT_TIMEOUT_MS` en el
`.env`, o ponerlo en 0 para volver al comportamiento anterior.

Es además el primer cambio del programa que afecta a **todas las conexiones a la
vez**, no a un controlador. Merece más atención al publicarlo que las quince
tandas de migración.

### Incidente: el primer intento rompió el arranque contra la base real

El usuario probó el login local contra la base real y `_create_pool()` falló al
inicializar:

```
unsupported startup parameter in options: statement_timeout
```

La `DATABASE_URL` de este proyecto usa el endpoint `-pooler` de Neon. Investigado
antes de tocar nada:

- El endpoint agrupado de Neon es **PgBouncer en modo transacción**.
- PgBouncer solo admite cinco parámetros en el paquete de arranque:
  `client_encoding`, `datestyle`, `timezone`, `standard_conforming_strings` y
  `application_name`. Cualquier otro hace fallar **la conexión entera**.
- Los `SET` de sesión tampoco son fiables ahí: la conexión se recicla entre
  transacciones y el ajuste puede filtrarse al siguiente cliente.
- El patrón recomendado para modo transacción es **`SET LOCAL` dentro de la
  transacción**, que es lo que `set_config(..., TRUE)` implementa.

Gravedad: la aplicación no arrancaba. No era una degradación sutil, era una caída
completa, y la habría provocado el primer despliegue.

Lo que **no** se hizo: quitar los timeouts para que el login volviera a pasar.
`connect_timeout` se conservó porque es compatible por naturaleza, y los otros
tres se reimplementaron con un mecanismo que funciona igual contra un endpoint
agrupado que contra uno directo.

Por qué las pruebas no lo detectaron: todas eran herméticas y ninguna hablaba con
un servidor. La diferencia entre endpoint agrupado y directo **solo existe en una
conexión real**. Es el límite exacto de la estrategia de verificación elegida en
1.0, y esta es la primera vez que ese límite cuesta algo.

### Verificaciones añadidas por el incidente

Dos capas distintas, porque una sola no basta:

1. **Guardia hermética de regresión**, en `tests/test_db_pool_timeouts.py`:
   afirma que `_create_pool()` **no** envía `options`, que ningún GUC de servidor
   aparece en sus parámetros, y que los que usa son un subconjunto de los que un
   endpoint agrupado tolera. Si alguien vuelve a meter un timeout en el arranque,
   la suite se pone roja sin necesidad de base de datos.
2. **Comprobación operativa real**, en `scripts/check_db_timeouts.py`: abre una
   conexión con la `DATABASE_URL` configurada, informa si el endpoint es agrupado
   o directo, y lee con `SHOW` los valores efectivos de los tres timeouts. Es la
   única forma de cubrir la diferencia de verdad. Solo lee y no imprime
   credenciales.

Una prueba existente de 1.1 también se puso en rojo:
`test_get_connection_prepara_la_conexion_y_la_retiene` afirmaba que preparar una
conexión ejecutaba **una** sentencia, y ahora son dos. Se actualizó reforzando la
aserción —comprueba el número y que la segunda sea la de `set_config`— en vez de
relajarla.

### Verificación

| Comprobación | Resultado |
|---|---|
| Pruebas específicas | 19 pasaron en 0,24 s |
| `Settings(_env_file=None)` con el entorno de CI | Los cuatro valores por defecto se resuelven correctamente |
| Compuerta global | Exit 0 |
| Suite completa | **334** pasaron, 5 warnings conocidos, 1,50 s |
| Ruff | `All checks passed!` |
| `pip check` | `No broken requirements found.` |
| `git diff --check` | Exit 0 |
| **Verificación contra la base real** | **Correcta**, detallada abajo |

### Evidencia medida contra el endpoint agrupado real

Ejecutada por el usuario el 2026-08-11 contra la base real, con la
`DATABASE_URL` de producción apuntando al endpoint `-pooler` de Neon. Son tres
evidencias distintas y hacen falta las tres:

| Evidencia | Qué demuestra | Resultado |
|---|---|---|
| El login local funciona | `_create_pool()` inicializa y `set_config(..., TRUE)` se ejecuta sin error tras PgBouncer | Correcto |
| `SHOW` de los tres ajustes | Los valores **están fijados** en la sesión | `statement_timeout = 30s`, `lock_timeout = 10s`, `idle_in_transaction_session_timeout = 1min` |
| Timeout forzado con `--forzar` | PostgreSQL **los hace cumplir**, no solo los registra | Consulta cancelada tras **1,11 s** con un límite de 1 s |

El endpoint quedó identificado por el propio script como
`AGRUPADO (pooler) · ...-pooler.c-4.us-east-1.aws.neon.tech`, es decir el mismo
que provocó el fallo original.

La tercera evidencia es la que convierte «configurado» en «verificado» y la que
satisface la exigencia del índice maestro de definir los timeouts **con evidencia
medida**. Se obtiene bajando `statement_timeout` a un segundo solo para esa
transacción y lanzando un `pg_sleep` más largo: recorre exactamente el mismo
camino que el valor real —`set_config` local, PgBouncer, cancelación de
PostgreSQL— sin obligar a esperar treinta segundos.

Con esto la subcapa queda **cerrada**.

### Lo que sigue sin estar verificado

La **calibración** de `DB_STATEMENT_TIMEOUT_MS`. Que el límite se cumpla está
probado; que 30 s sea el número correcto para este sistema, no. Sigue haciendo
falta medir la duración de las consultas pesadas —boletines, planillas, reportes
financieros— sobre datos comparables a producción.

Son dos preguntas distintas y conviene no confundirlas: el mecanismo funciona, el
valor es una apuesta razonable pero no medida.

## Subcapa 1.6: cierre de la capa

Sin cambios funcionales. Solo compuerta global, auditoría, documentación de
publicación y actualización del índice maestro, por instrucción explícita del
usuario.

### Compuerta global

| Comprobación | Resultado |
|---|---|
| `.\venv\Scripts\python.exe scripts\verify.py` | **Exit 0** |
| Suite completa | **334** pruebas correctas, 5 warnings conocidos |
| Ruff sobre `app tests scripts apply_migration.py` | `All checks passed!` |
| `pip check` | `No broken requirements found.` |
| `git diff --check` | Exit 0 |

Se parte de 192 pruebas al abrir la capa: **142 pruebas nuevas**.

### Auditoría del diff completo desde el commit base

Rango auditado: `6754e4aad59c1e428ea97d31fe8e96fdbba7694d` hasta el árbol de
trabajo. **17 commits**, cada uno correspondiente a una subcapa registrada en
este documento, sin ninguno inexplicado.

**Categorías prohibidas: ninguna tocada.** El diff no contiene `migrations/`,
`requirements.txt`, `.github/`, archivos `.sql`, `apply_migration.py` ni
`scripts/verify.py`.

**Análisis semántico del diff de `app/`.** No basta con contar líneas: casi todo
el volumen es reindentación por meter código dentro de un `with`. Se normalizaron
los espacios de cada línea y se compararon los conjuntos:

| Medida | Líneas |
|---|---:|
| Quitadas en `app/` | 1229 |
| Añadidas en `app/` | 1064 |
| **Idénticas salvo espacios** (reindentación) | **938** |
| Cambio semántico real: quitadas | 291 |
| Cambio semántico real: añadidas | 126 |

Clasificación de lo realmente quitado:

| Concepto | Líneas |
|---|---:|
| Cierres manuales `cursor.close()` / `conn.close()` | 118 |
| Aperturas manuales `get_connection()` / `conn.cursor()` | 100 |
| Líneas en blanco | 28 |
| `conn.commit()` manuales | 22 |
| Imports viejos de `get_connection` | 19 |
| Sin clasificar | **4** |

Clasificación de lo realmente añadido:

| Concepto | Líneas |
|---|---:|
| `with get_cursor(...)` | 50 |
| Imports nuevos | 17 |
| Sin clasificar | **59** |

Las 4 quitadas y las 59 añadidas sin clasificar se revisaron una por una:
**todas pertenecen a la subcapa 1.5** —los cuatro ajustes de `app/config.py` y
las tres funciones nuevas de `app/db/session.py` con sus comentarios—. No hay ni
una línea del diff que no corresponda a la sustitución del ciclo manual de
conexión o al trabajo de timeouts.

**Contratos HTTP.** Ninguna línea del diff modifica un decorador `@router`, un
`response_model` o un `status_code`. Los únicos `status_code` que aparecen en el
diff son los `400` y `404` de `plantilla_controller`, y en todos los casos la
línea quitada y la añadida son idénticas salvo la sangría, por haber quedado
dentro de un `with`.

### Estado final medido

| Métrica | Al abrir la capa | Al cerrarla |
|---|---:|---:|
| Aperturas sin cierre garantizado | **50** | **0** |
| De ellas, fugas deterministas | 2 | **0** |
| Aperturas fuera de controllers y services | 2 | **0** |
| Llamadas a `get_connection()` en `app/` | 146 | 96 |
| Timeouts configurados | **ninguno** | 4, verificados contra Neon real |
| Pruebas | 192 | **334** |

### Hallazgo de la auditoría: `.env.example` incompleto

`.env.example` documenta `DB_POOL_MIN_CONNECTIONS` y `DB_POOL_MAX_CONNECTIONS`
pero **no los cuatro ajustes de timeout añadidos en 1.5**. Quien prepare un
entorno nuevo no sabrá que existen, ni que un 0 significa «no fijar nada» en vez
de «sin límite».

No se corrigió: el usuario pidió expresamente no introducir cambios durante 1.6.
Queda como tarea de documentación pendiente, de riesgo bajo y sin efecto en el
comportamiento.

### Staging y publicación

Este programa no despliega. La publicación la controla el usuario y en este
proyecto tiene una consecuencia inmediata: **`main` despliega a producción de
forma automática**, sin paso intermedio de staging.

Por eso el equivalente a staging aquí fue la verificación local contra la base
real, ya ejecutada en 1.5: endpoint agrupado identificado, timeouts efectivos
leídos con `SHOW` y cumplimiento medido con una cancelación real. Es la única
comprobación que distingue un endpoint agrupado de uno directo, y la que faltó en
el primer intento.

Orden de publicación acordado:

1. Commit de 1.5 y de este cierre.
2. Push a `main`, que dispara el despliegue.
3. Verificación manual de la lista de abajo.

### Rollback

Ninguna migración de base de datos, ningún cambio de esquema, ningún dato
tocado. El rollback es exclusivamente de código.

- **Rollback total de la capa**: `git revert` en orden inverso de los commits
  posteriores a `6754e4aa`, sin revertir el propio base. Devuelve las 50
  aperturas desprotegidas y elimina los timeouts.
- **Rollback selectivo por tanda**: cada subcapa es un commit independiente y
  autocontenido —código y pruebas juntos—, así que puede revertirse una sola sin
  tocar las demás. Es la ventaja de haber migrado en quince tandas en vez de una.
- **Mitigación sin rollback, para el riesgo más probable**: si
  `statement_timeout` corta una consulta legítima, basta con subir
  `DB_STATEMENT_TIMEOUT_MS` en el `.env`, o ponerlo en 0 para volver exactamente
  al comportamiento anterior. **No requiere desplegar código.** Es la primera
  palanca a usar ante un incidente.
- **Rollback de la infraestructura sin perder la migración**: revertir solo el
  commit de 1.5 deja los 50 sitios migrados y quita los timeouts.

### Verificación manual después de publicar

1. Confirmar que el despliegue terminó y el servicio está vivo.
2. Iniciar sesión. Es el camino que ya detectó el fallo de 1.5 y atraviesa
   `get_connection()` completo.
3. Ejecutar `.\venv\Scripts\python.exe scripts\check_db_timeouts.py --forzar`
   apuntando al entorno publicado y confirmar los tres valores y la cancelación.
4. Probar una operación de escritura sencilla —crear o actualizar un usuario— y
   comprobar que persiste. Verifica que el `commit` sigue ocurriendo.
5. Probar una lectura pesada —un boletín o una planilla con datos reales— y
   confirmar que **no** se corta a los 30 s. Es la comprobación que sustituye a
   la calibración formal y la que más probablemente revele un problema.
6. Revisar los logs en busca de `canceling statement due to statement timeout`.
   Su aparición indica que el valor está mal calibrado, no que el código falle.

### Verificación pendiente aceptada

La **calibración** de `DB_STATEMENT_TIMEOUT_MS` no se completó. El usuario la
aceptó de forma explícita como pendiente operativa registrada, con dos motivos:
el mecanismo ya está verificado contra Neon real, y el valor puede ajustarse por
entorno sin desplegar código.

Se registra sin darla por cumplida. Distinción que debe conservarse: **el
mecanismo está probado; el valor de 30 s es una apuesta razonable, no una
medición.**

## Criterios de cierre de la subcapa 1.0

- La línea base está reproducida desde el commit base con resultados reales.
- Cada punto de apertura de conexión o cursor está localizado con archivo y
  línea.
- Para cada patrón se identifica quién posee `commit`, `rollback` y el cierre.
- Los patrones divergentes están documentados y clasificados por riesgo, sin
  corregirse.
- Existe una decisión registrada sobre cómo se verificarán los cambios de 1.1 en
  adelante.
- El diff contiene exclusivamente esta bitácora.

## Criterios de cierre de la capa

- Todas las subcapas necesarias están cerradas o marcadas `No aplica` con
  justificación.
- La propiedad de conexión, cursor, `commit` y `rollback` es explícita y está
  documentada.
- Los timeouts y el pool están definidos con evidencia medida, no supuesta.
- La compuerta global termina en exit 0 y la CI remota lo confirma.
- Ningún contrato del inventario de 0.0 cambió.
- Staging, rollback y verificación manual documentados, incluyendo por primera
  vez un plan para cambios que sí afectan el comportamiento en producción.
- La capa 2 permanece en espera hasta orden explícita del usuario.

## Decisiones

- Se activa la capa 1 con `6754e4aa` como commit base, que es el `HEAD` limpio
  vigente y no el base original del programa. Motivo: el commit base debe ser el
  punto anterior a esta capa, no el del programa completo.
- El desglose de subcapas posterior a 1.0 se registra como provisional en vez de
  dejarse vacío, para que el usuario vea la forma esperada del trabajo. La
  alternativa descartada era definirlo tras el inventario, que habría dejado la
  capa activa sin plan visible.
- 1.0 no modifica código. La alternativa descartada era empezar migrando un
  consumidor pequeño, que habría fijado un contrato de propiedad antes de saber
  cuántos patrones distintos existen.
- La verificación de esta capa será por **pruebas de contrato con pool falso**,
  decidido por el usuario el 2026-08-11. Motivo: comprueba el mecanismo real,
  es hermética y no obliga a ampliar la infraestructura de CI. Alternativas
  descartadas: la guardia estática de regresión sobre el AST, que habría
  protegido los 146 sitios a la vez, y añadir PostgreSQL real al workflow, que
  habría sido lo más fiel pero amplía el alcance de la capa.
- La decisión se ratificó el 2026-08-11 tras exponer el asistente que
  recomendaba añadir además la guardia estática con trinquete. El usuario optó
  por conservar solo el contrato con pool falso y reevaluarlo más adelante si la
  migración lo justifica. La guardia queda disponible y no requiere trabajo
  previo: el análisis AST usado en 1.0 ya está validado.
- **Cadencia de publicación acordada el 2026-08-11**: el trabajo se hace y se
  verifica en local; el usuario decide cuándo publicar. No se publica de forma
  automática al cerrar una subcapa. Motivo: `main` despliega a producción sin
  intervención, y desde 1.1 los cambios dejan de ser documentales.

## Riesgos

- **La suite es hermética y no levanta PostgreSQL.** Registrado en 0.3: *«no
  levanta PostgreSQL: el pool es lazy y la suite actual es hermética»*. Las 192
  pruebas pueden pasar en verde aunque una conexión no se devuelva al pool o un
  `commit` se pierda. Es el riesgo central de esta capa: la red de seguridad
  construida en la capa 0 es más débil justo para el trabajo que viene. Mitigación
  pendiente de decidir en 1.0; responsable de aprobarla: el usuario.
- Primera capa que modifica código de producto. `main` despliega a producción de
  forma automática, así que cada push deja de ser inocuo. Debe acordarse la
  cadencia de publicación antes de la primera subcapa que toque `app/`.
- Un cambio en el manejo de transacciones puede alterar el aislamiento entre
  tenants si se comparte una conexión donde antes no se compartía. El
  `ContextVar` del tenant forma parte del contrato de seguridad.
- Una extracción prematura podría crear una abstracción compartida sin dos
  consumidores reales. El programa lo prohíbe explícitamente.
- Los errores de fuga de conexión se manifiestan bajo carga, no en pruebas
  unitarias. Puede que la evidencia de 1.3 exija medición y no solo aserciones.

## Registro de ejecución

### 2026-08-11 — activación de la capa

- Modo de acceso del asistente: mismo checkout local; Git validado directamente.
- Autorización: orden explícita del usuario, «activa la capa 1», emitida después
  de informarle el alcance, el ritmo y el riesgo de la suite hermética.
- Rama acordada: `main`.
- Estado verificado antes de escribir: `git status` sin entradas, `HEAD` y
  `origin/main` ambos en `6754e4aad59c1e428ea97d31fe8e96fdbba7694d`.
- Commit base registrado: `6754e4aad59c1e428ea97d31fe8e96fdbba7694d`.
- Archivos creados o modificados: esta bitácora y
  `docs/modularizacion/README.md`.
- Código de producto, pruebas, configuración, dependencias y workflow
  modificados: ninguno.
- Código de la capa inspeccionado: **ninguno**. La activación se documentó desde
  el alcance aprobado en el índice maestro; leer las conexiones corresponde a
  1.0.
- Siguiente acción exacta: ejecutar la subcapa **1.0** —reproducir la línea base,
  inventariar conexiones, cursores y transacciones, clasificar patrones
  divergentes por riesgo y proponer la estrategia de verificación— actualizando
  únicamente esta bitácora. No iniciar 1.1 en ese turno.

### 2026-08-11 — subcapa 1.0

- Rama acordada: `main`. `HEAD` en el commit base
  `6754e4aad59c1e428ea97d31fe8e96fdbba7694d`.
- Estado del árbol al iniciar: **no limpio**. Contenía la activación de esta capa
  —`README.md` modificado y esta bitácora sin versionar— pendiente de commit. Se
  registra como desviación menor y explicada: el único cambio previo es la
  activación documentada en la entrada anterior, y 1.0 modifica exactamente el
  mismo archivo. El diff resultante contiene activación y 1.0 juntas.
- Archivos modificados: únicamente esta bitácora.
- Código de producto, pruebas, configuración, dependencias y workflow
  modificados: **ninguno**. La subcapa es de lectura.
- Línea base reproducida: compuerta exit 0; 192 pruebas, Ruff y `pip check`
  correctos.
- Fuentes inspeccionadas: `app/database.py`, `app/db/session.py`,
  `app/db/tenant.py`, `app/dependencies.py`, `app/config.py`, muestras de
  `app/controllers/notas_controller.py` y `app/core/super_admin.py`, y un
  recuento AST sobre todo `app/`.
- Método: el inventario se hizo con un script AST ejecutado desde el directorio
  temporal de trabajo, no desde el repositorio; no se agregó ningún archivo al
  proyecto.
- Hallazgo principal: 146 aperturas en `app/`; 94 protegidas con `try/finally`,
  **50 que cierran fuera de `finally`** y 2 con propiedad delegada. Las 50
  pierden la conexión ante excepción y el pool tiene `maxconn = 10`.
- Hallazgo secundario: no existe ningún timeout configurado.
- Hallazgo que reduce alcance: no hay aperturas manuales de `psycopg2.connect` en
  el camino de petición; las 15 existentes están en `scripts/` y
  `apply_migration.py`, fuera de esta capa.
- Decisiones: no se corrigió ningún sitio, conforme al alcance de 1.0; no se
  eligió estrategia de verificación, que corresponde al usuario.
- Riesgos: los 50 sitios permanecen tal cual hasta 1.1; hasta entonces el riesgo
  de agotamiento del pool sigue vigente en producción, igual que antes de esta
  subcapa. La subcapa no lo introdujo ni lo agravó.
- `git diff --check`: exit 0.
- Siguiente acción exacta: el usuario elige la estrategia de verificación entre
  las tres opciones registradas. Con esa decisión, **1.1** define el contrato
  explícito de propiedad de conexión, cursor, `commit` y `rollback`, y agrega las
  pruebas que lo protejan, sin migrar todavía los 50 sitios.

### 2026-08-11 — subcapa 1.1

- Rama acordada: `main`; árbol **limpio** antes de editar, con la activación y
  1.0 ya commiteadas.
- Commit observado: `08e617b`, un commit por delante de `origin/main` conforme a
  la cadencia local acordada.
- Archivo creado: `tests/test_db_session_contrato.py`.
- Archivo modificado: esta bitácora.
- **Código de producto modificado: ninguno.** La subcapa resultó ser
  caracterización pura: el contrato ya estaba implementado y solo faltaba
  declararlo y fijarlo. `app/` no aparece en el diff.
- Contratos HTTP, rutas, payloads, status codes, permisos, tenant, ownership,
  SQL, transacciones y dependencias modificados: ninguno.
- Implementación: 9 pruebas con pool falso que fijan los dos regímenes de
  propiedad, la idempotencia de `close()`, la diferencia entre `close()` y
  `real_close()`, y la garantía de devolución al pool ante excepción.
- Aislamiento de estado: el pool se inyecta con `monkeypatch`, que lo restaura; el
  `ContextVar` del tenant se libera con su token en un `finally`.
- Comprobación de mutación: contra un `get_cursor` sin `finally`, la aserción
  crítica falla —0 conexiones devueltas frente a 1—. Las pruebas no son vacuas.
- Pruebas específicas: 9 pasaron en 0,18 s.
- Compuerta global: exit 0; 201 pruebas correctas con los 5 warnings conocidos en
  1,19 s, Ruff correcto y dependencias íntegras.
- Incidencia menor: Ruff marcó un `F841` legítimo en la primera pasada, una
  variable `cursor` enlazada y no usada. Se corrigió quitando el enlace y la
  compuerta volvió a verde. Evidencia de que la compuerta de la capa 0 protege
  también el código nuevo.
- `git diff --check`: exit 0.
- Alcance final del diff: únicamente el archivo de pruebas nuevo y esta bitácora.
- Decisión: declarar el contrato tal como existe hoy en lugar de rediseñarlo. Se
  descartó introducir un gestor de contexto nuevo sobre `get_connection()` porque
  el destino de migración ya existe —`get_cursor()`, con 15 consumidores reales—
  y el programa prohíbe crear abstracciones sin necesidad demostrada.
- Riesgo residual: las pruebas cubren la infraestructura, no los 146 llamadores.
  La corrección de cada sitio migrado en 1.2 dependerá de la revisión del diff,
  conforme a la estrategia de verificación elegida por el usuario.
- Siguiente acción exacta: ejecutar **1.2**, migrando una tanda pequeña y
  revisable de los 50 sitios desprotegidos al régimen correcto, con la suite
  existente como red de comportamiento. Es la primera subcapa que modifica
  `app/`. Debe acordarse antes el tamaño de la tanda y por qué controlador
  empezar.

### 2026-08-11 — subcapa 1.2

- Rama acordada: `main`; árbol **limpio** antes de editar, con 1.1 ya commiteada.
- Commit observado: `4bccc84`, dos commits por delante de `origin/main` conforme
  a la cadencia local acordada.
- Archivos modificados: `app/services/nota_service.py` y
  `app/services/planilla_service.py`. **Primera modificación de código de
  producto del programa completo.**
- Archivo creado: `tests/test_servicios_validacion.py`.
- Archivo actualizado: esta bitácora.
- Sitios migrados: 4, todos de solo lectura, del régimen `get_connection()` sin
  `finally` al régimen `get_cursor()`.
- Contratos HTTP, rutas, payloads, status codes, permisos, tenant, ownership,
  transacciones y dependencias modificados: ninguno.
- SQL: idéntico en tablas, columnas, joins, condiciones y parámetros. Solo cambió
  la indentación de los literales al quedar un nivel más adentro.
- Caracterización previa: las 8 aserciones se verificaron contra la versión
  original recuperada con `git show HEAD:`, ejecutada con un doble de
  `get_connection` desde el directorio temporal. Se cumplen en ambas versiones,
  por lo que la migración preservó el comportamiento observable.
- Pruebas específicas: 8 pasaron en 0,16 s.
- Compuerta global: exit 0; 209 pruebas correctas con los 5 warnings conocidos en
  1,20 s, Ruff correcto y dependencias íntegras.
- Efecto medido: sitios sin cierre garantizado de **50 a 46**; llamadas a
  `get_connection()` en `app/` de 146 a 142.
- `git diff --check`: exit 0.
- Alcance final del diff: los dos servicios, el archivo de pruebas nuevo y esta
  bitácora.
- Decisión: adoptar `get_cursor()` como destino de migración en vez de crear un
  gestor de contexto nuevo sobre `get_connection()`. Motivo: ya existe, tiene 15
  consumidores y su idioma ya aparece en `estudiante_controller.py:388`. El
  programa prohíbe crear abstracciones compartidas sin necesidad demostrada.
- Decisión: empezar por servicios de solo lectura en vez de un controlador
  completo, para validar el patrón con el diff más pequeño posible y sin
  escrituras de por medio.
- Riesgo residual: quedan 46 sitios. Los de `pagos`, `ventas` y `estudiantes`
  implican escritura financiera y deben migrarse cuando el patrón esté rodado, en
  tandas propias y con caracterización específica; su forma no será tan uniforme
  como la de estos cuatro.
- Riesgo conocido: no todos los 46 restantes tendrán esta forma trivial. Los que
  hacen `commit` o abren varios cursores requerirán decidir entre
  `get_cursor(commit=True)` y conservar `get_connection()` con `try/finally`.
- Siguiente acción exacta: la bitácora planificó **1.3**, timeouts y pool. El
  usuario puede reordenar y continuar antes con las tandas de migración, dado que
  el patrón acaba de validarse y quedan 46 sitios con riesgo activo. Requiere su
  decisión explícita; no se reordena por inferencia.

### 2026-08-11 — subcapa 1.3

- Rama acordada: `main`; árbol **limpio** antes de editar, con 1.2 ya commiteada.
- Commit observado: `076c497`, tres commits por delante de `origin/main` conforme
  a la cadencia local acordada.
- Reordenación: el usuario ordenó de forma explícita continuar migrando antes de
  abordar los timeouts. La tabla de subcapas se renumeró en consecuencia y la
  decisión quedó registrada allí.
- Archivos modificados: `app/controllers/planeador_anual_controller.py` y
  `tests/test_planeador_anual_validaciones.py`.
- Sitios migrados: 3 de los 4 del archivo. `bulk_actualizar_planeadores_controller`
  se dejó intacta por estar ya protegida con `try/except/finally`.
- Contratos HTTP, rutas, payloads, status codes, permisos, tenant, ownership y
  dependencias modificados: ninguno.
- SQL: idéntico en tablas, columnas, condiciones y parámetros; solo cambió la
  indentación de los literales al quedar un nivel más adentro.
- Semántica transaccional: preservada y verificada explícitamente. `crear` y
  `actualizar` confirman; `obtener` no. Es la garantía crítica de esta tanda,
  porque perder un `commit` descartaría datos sin error visible.
- Import: se conserva `get_connection` junto a `get_cursor` porque la función no
  migrada y su prueba existente lo siguen usando.
- Caracterización previa: las tres aserciones se verificaron contra el
  controlador original recuperado con `git show HEAD:`. Se cumplen en ambas
  versiones.
- Incidencia de utillaje: la primera pasada de esa comprobación marcó dos
  discrepancias que resultaron ser un defecto del script de verificación, que no
  neutralizaba el import del resolver de asignación académica. Corregido el
  script, las tres funciones quedaron en verde. El código migrado nunca estuvo en
  duda, pero se registra como evidencia de que la comprobación discrimina.
- Pruebas del archivo: 8 pasaron en 0,20 s.
- Compuerta global: exit 0; 212 pruebas correctas con los 5 warnings conocidos en
  1,07 s, Ruff correcto y dependencias íntegras.
- Efecto medido: sitios sin cierre garantizado de **46 a 43**; llamadas a
  `get_connection()` en `app/` de 142 a 139.
- `git diff --check`: exit 0.
- Alcance final del diff: el controlador y su archivo de pruebas.
- Decisión: migrar solo las funciones desprotegidas y no uniformar la que ya
  cumple el contrato. Motivo: el alcance de la capa es garantizar el cierre, no
  homogeneizar estilo, y tocarla habría ampliado el diff sin reducir riesgo.
- Riesgo residual: quedan 43 sitios. Los de `pagos`, `ventas` y `estudiantes`
  siguen reservados para el final.
- Siguiente acción exacta: continuar con **1.4**, la siguiente tanda de
  migración. Acordar antes con el usuario qué archivo tomar; candidatos sin
  escritura financiera son `plantilla_controller.py` con 7 sitios,
  `usuario_controller.py` con 4 y `branding_controller.py` con 4.

### 2026-08-11 — subcapa 1.4

- Rama acordada: `main`; árbol **limpio** antes de editar, con 1.3 ya commiteada.
- Commit observado: `7d0cf86`, cuatro commits por delante de `origin/main`
  conforme a la cadencia local acordada.
- Archivos modificados: `app/controllers/usuario_controller.py`.
- Archivo creado: `tests/test_usuarios_controlador.py`.
- Sitios migrados: 4 de 5. `obtener_usuarios_paginado_controller` se dejó intacta
  por estar ya protegida; el import de `get_connection` se conserva por ella.
- Contratos HTTP, rutas, payloads, status codes, permisos, tenant, ownership y
  dependencias modificados: ninguno.
- SQL: idéntico en tablas, columnas, condiciones y parámetros. Se conserva la
  construcción dinámica del `SET` de la actualización tal cual estaba.
- Semántica transaccional: preservada y verificada. `crear`, `actualizar` y
  `eliminar` confirman; `obtener` no.
- **Diferencia intencional**: el camino «sin campos que actualizar» ya no
  adquiere conexión. Antes la abría, ejecutaba el `SET search_path` implícito de
  `get_connection()` y la perdía al salir por el `return` temprano. La respuesta
  devuelta es idéntica. Es una fuga determinista corregida, no un cambio de
  contrato.
- Evidencia de la fuga previa: ejecutando el controlador original con un doble de
  `get_connection`, ese camino registró 1 conexión adquirida y 0 cerradas.
- Caracterización previa: SQL, parámetros, `commit` y respuesta verificados
  contra la versión anterior en las cuatro funciones. Se fijó además que la
  contraseña llega hasheada al SQL, propiedad de seguridad que no tenía prueba.
- Barrido adicional autorizado por el hallazgo: se recorrió el AST de `app/` para
  separar fugas deterministas de condicionales. Resultado: 38 condicionales y
  **1 determinista** restante, en
  `app/controllers/asignacion_controller.py:642`, `eliminar_asignacion_controller`,
  con salida temprana en la línea 655 cuando la asignación no existe. Solo se
  documentó; no se corrigió en esta subcapa.
- Pruebas específicas: 7 pasaron en 0,22 s.
- Compuerta global: exit 0; 219 pruebas correctas con los 5 warnings conocidos en
  1,12 s, Ruff correcto y dependencias íntegras.
- Efecto medido: sitios sin cierre garantizado de **43 a 39**; llamadas a
  `get_connection()` en `app/` de 139 a 135.
- `git diff --check`: exit 0.
- Alcance final del diff: el controlador, su archivo de pruebas nuevo y esta
  bitácora.
- Decisión: mover la construcción de la actualización delante del `with` en vez
  de envolver todo el cuerpo. Motivo: envolverlo habría conservado la apertura
  inútil en el camino sin campos, es decir habría mantenido la fuga con otra
  forma.
- Riesgo residual: quedan 39 sitios, uno de ellos con fuga determinista y
  prioridad alta. `pagos`, `ventas` y `estudiantes` siguen reservados para el
  final.
- Siguiente acción exacta: ejecutar la siguiente tanda empezando por
  `eliminar_asignacion_controller` en `app/controllers/asignacion_controller.py`,
  por ser la única fuga determinista pendiente. El archivo tiene 6 sitios
  desprotegidos en total; decidir con el usuario si se migran todos o solo el
  crítico.

### 2026-08-11 — subcapa 1.4b

- Rama acordada: `main`; árbol **limpio** antes de editar, con 1.4 ya commiteada.
- Commit observado: `2f4f848`, cinco commits por delante de `origin/main`
  conforme a la cadencia local acordada.
- Alcance decidido por el usuario: archivo completo y con revisión detallada.
- Archivos modificados: `app/controllers/asignacion_controller.py`.
- Archivo creado: `tests/test_asignaciones_controlador.py`.
- Sitios migrados: 6 de los 13 del archivo. Los 7 restantes ya estaban protegidos
  con `try/finally` y no se tocaron; el import de `get_connection` se conserva.
- Contratos HTTP, rutas, payloads, status codes, permisos, tenant, ownership y
  dependencias modificados: ninguno.
- Comprobación previa al cambio: se verificó de forma empírica que un `return`
  dentro de un `with get_cursor(commit=True)` **sí ejecuta el `commit`**, porque
  `@contextmanager` reanuda el generador tras el `yield`. El resultado gobernó el
  diseño de la migración de `eliminar_asignacion_controller`.
- **Diferencia intencional**: en el camino «asignación no encontrada» la versión
  migrada emite un `COMMIT` sobre una transacción de solo lectura. La anterior no
  confirmaba, pero abandonaba la conexión con la transacción abierta. Se acepta:
  no altera datos y sustituye una fuga permanente.
- Alternativa descartada: partir la función en dos bloques `get_cursor`, uno de
  lectura y otro de escritura. Habría usado dos conexiones y roto la atomicidad
  entre la comprobación y la actualización, introduciendo una ventana de carrera.
- SQL: idéntico en tablas, columnas, joins, condiciones, orden y parámetros.
  Además de la indentación, se eliminaron espacios finales de línea en tres
  literales, obligatorio porque `git diff --check` los rechaza y la compuerta lo
  ejecuta.
- Caracterización previa: SQL, parámetros, respuesta y `commit` verificados
  contra la versión anterior en las seis funciones, con los dos caminos de
  `eliminar_asignacion_controller` comprobados por separado.
- Evidencia de la fuga previa: en el camino «no encontrada», el código original
  registró `adquiridas=1 cerradas=False commit=False`.
- Pruebas específicas: 7 pasaron en 0,18 s.
- Compuerta global: exit 0; 226 pruebas correctas con los 5 warnings conocidos en
  1,18 s, Ruff correcto y dependencias íntegras.
- Efecto medido: sitios sin cierre garantizado de **39 a 33**; llamadas a
  `get_connection()` en `app/` de 135 a 129. **Fugas deterministas: de 1 a 0.**
- `git diff --check`: exit 0.
- Volumen del diff en `app/`: 117 inserciones y 148 supresiones en un solo
  archivo.
- Alcance final del diff: el controlador, su archivo de pruebas nuevo y esta
  bitácora.
- Riesgo residual: quedan 33 sitios, todos de fuga condicional. `pagos`,
  `ventas` y `estudiantes` siguen reservados para el final.
- Siguiente acción exacta: continuar con **1.4c**. Candidatos por volumen son
  `plantilla_controller.py` con 7 sitios, `notas_controller.py` con 5 y
  `branding_controller.py` con 4. Acordar con el usuario cuál tomar.

### 2026-08-11 — subcapa 1.4c

- Rama acordada: `main`; árbol **limpio** antes de editar, con 1.4b ya
  commiteada.
- Commit observado: `b92f16d`, seis commits por delante de `origin/main` conforme
  a la cadencia local acordada.
- Archivo elegido por el usuario: `app/controllers/branding_controller.py`.
- Archivos modificados: ese controlador.
- Archivo creado: `tests/test_branding_controlador.py`.
- Sitios migrados: 4 de 4. Es el primer archivo que abandona `get_connection`
  por completo; el import quedó reducido a `get_cursor`.
- Contratos HTTP, rutas, payloads, status codes, permisos, tenant, ownership y
  dependencias modificados: ninguno.
- SQL: idéntico en tablas, columnas, condiciones y parámetros; solo cambió la
  indentación de los literales.
- Caso nuevo: `obtener_branding_controller` confirmaba de forma **condicional**,
  solo cuando tenía que crear la fila de branding. `get_cursor(commit=True)`
  confirma siempre.
- **Diferencia intencional**: en el camino de lectura la versión anterior
  terminaba la transacción con el `ROLLBACK` implícito de
  `PooledConnection.close()`; la migrada la termina con `COMMIT`. Sobre una
  transacción que solo ejecutó `SELECT` son equivalentes. El camino de creación,
  el único que escribe, conserva su confirmación. Medido contra la versión
  anterior: lectura `commit=False → True`, creación `commit=True → True`.
- Alternativa descartada: conservar `get_connection()` con `try/finally` para
  replicar el condicional literalmente. Es válido según el contrato, pero añade
  una tercera forma de escribir lo mismo sin reducir ningún riesgo.
- Orden de efectos preservado: en `subir_logo_controller` y
  `eliminar_logo_controller`, el borrado del archivo anterior ocurre **después**
  de cerrar el bloque de base de datos. Fijado en pruebas con la secuencia exacta
  `['sql', 'sql', 'cierre_bloque', 'delete_file']`.
- Se conservó sin tocar que `eliminar_logo_controller` invoque `delete_file` aun
  cuando no había logo previo. Corregirlo sería un asunto ajeno a esta capa.
- `subir_logo_controller` es `async`; su prueba usa `asyncio.run` y no se añadió
  `pytest-asyncio` ni ninguna dependencia.
- Caracterización previa: respuesta, SQL, parámetros y orden de borrado
  verificados contra la versión anterior en las cuatro funciones.
- Pruebas específicas: 8 pasaron en 0,35 s.
- Compuerta global: exit 0; 234 pruebas correctas con los 5 warnings conocidos en
  1,15 s, Ruff correcto y dependencias íntegras.
- Efecto medido: sitios sin cierre garantizado de **33 a 29**; llamadas a
  `get_connection()` en `app/` de 129 a 125. Fugas deterministas: 0.
- `git diff --check`: exit 0.
- Alcance final del diff: el controlador, su archivo de pruebas nuevo y esta
  bitácora.
- Riesgo residual: quedan 29 sitios, todos de fuga condicional. `pagos`,
  `ventas` y `estudiantes` siguen reservados para el final.
- Siguiente acción exacta: continuar con **1.4d**. Candidatos por volumen son
  `plantilla_controller.py` con 7 sitios, `notas_controller.py` con 5 y
  `dashboard_controller.py` con 4. Acordar con el usuario cuál tomar.

### 2026-08-11 — subcapa 1.4d

- Rama acordada: `main`; árbol **limpio** antes de editar, con 1.4c ya
  commiteada.
- Commit observado: `a3c6038`, siete commits por delante de `origin/main`
  conforme a la cadencia local acordada.
- Archivo elegido por el usuario: `app/controllers/dashboard_controller.py`.
- Archivos modificados: ese controlador.
- Archivo creado: `tests/test_dashboard_controlador.py`.
- Sitios migrados: 4 de 8. Los otros 4 ya estaban protegidos; el import conserva
  `get_connection`.
- Contratos HTTP, rutas, payloads, status codes, permisos, tenant, ownership y
  dependencias modificados: ninguno.
- SQL: idéntico en tablas, columnas, joins, condiciones, agregados, `HAVING`,
  orden y parámetros; solo cambió la indentación de los literales.
- Semántica transaccional: las cuatro funciones son de solo lectura y ninguna
  confirmaba. Se migraron a `get_cursor()` sin `commit`. **Esta tanda no
  introduce ninguna diferencia de comportamiento**, ni siquiera de las inocuas
  registradas en 1.4b y 1.4c.
- Caso destacado: `_obtener_notas_profesor` construye el SQL según dos ejes
  —notas altas o bajas, y con o sin `asignacion_id`—, lo que da cuatro
  combinaciones. El resolver del id académico se invoca solo cuando llega
  `asignacion_id` y usa el mismo cursor, por lo que permanece dentro del bloque.
- Se fijó además el color asignado a cada fila, que no es simétrico: `altas` da
  siempre `green`, mientras que en notas bajas da `red` bajo 3.0 y `yellow` si
  no. Ese último caso es alcanzable y no tenía prueba.
- Caracterización previa: SQL, parámetros, invocación del resolver, colores y
  respuesta verificados contra la versión anterior en las cuatro funciones, sin
  ninguna divergencia.
- Pruebas específicas: 7 pasaron en 0,18 s.
- Compuerta global: exit 0; 241 pruebas correctas con los 5 warnings conocidos en
  1,29 s, Ruff correcto y dependencias íntegras.
- Efecto medido: sitios sin cierre garantizado de **29 a 25**; llamadas a
  `get_connection()` en `app/` de 125 a 121. Fugas deterministas: 0.
- `git diff --check`: exit 0.
- Alcance final del diff: el controlador, su archivo de pruebas nuevo y esta
  bitácora.
- Hito: se superó la mitad de la migración. De los 50 sitios iniciales quedan 25.
- Riesgo residual: los 25 restantes son todos de fuga condicional. `pagos`,
  `ventas` y `estudiantes` siguen reservados para el final.
- Siguiente acción exacta: continuar con **1.4e**. Candidatos por volumen son
  `plantilla_controller.py` con 7 sitios, `notas_controller.py` con 5 e
  `inventario_controller.py` con 3. Acordar con el usuario cuál tomar.

### 2026-08-11 — subcapa 1.4e

- Rama acordada: `main`; árbol **limpio** antes de editar, con 1.4d ya
  commiteada.
- Commit observado: `0a271c0`, ocho commits por delante de `origin/main` conforme
  a la cadencia local acordada.
- Archivo elegido por el usuario: `app/controllers/inventario_controller.py`.
- Archivos modificados: ese controlador.
- Archivo creado: `tests/test_inventario_controlador.py`.
- Sitios migrados: 3 de 5. Los otros 2 ya estaban protegidos; el import conserva
  `get_connection`.
- Contratos HTTP, rutas, payloads, status codes, permisos, tenant, ownership y
  dependencias modificados: ninguno.
- SQL: idéntico en tablas, columnas, condiciones y parámetros. Además de la
  indentación, se eliminaron espacios finales de línea heredados en
  `UPDATE inventario ` y en dos líneas en blanco con sangría, obligatorio porque
  `git diff --check` los rechaza.
- Semántica transaccional: preservada. `crear` y `actualizar` confirman;
  `obtener` no.
- Primer archivo migrado con aritmética de dinero. No toca ventas ni saldos —el
  descuento de stock vive en `venta_controller`, reservado para el final—, pero
  produce las cifras de utilidad y margen que ve el administrador.
- `_formatear_producto` no se modificó, pero se caracterizó al no tener prueba
  previa: utilidad unitaria, utilidad total proyectada, margen redondeado a dos
  decimales, y la guarda que evita dividir por cero cuando el precio es 0.
- Filtro de estado fijado en sus tres variantes: por defecto `activo`, `"todos"`
  sin `WHERE`, y valor desconocido normalizado a `activo`. La misma normalización
  se conserva en `INSERT` y `UPDATE`.
- Caracterización previa: SQL, parámetros, normalización, aritmética y `commit`
  verificados contra la versión anterior en las tres funciones, sin divergencias.
- Pruebas específicas: 8 pasaron en 0,16 s.
- Compuerta global: exit 0; 249 pruebas correctas con los 5 warnings conocidos,
  Ruff correcto y dependencias íntegras.
- Efecto medido: sitios sin cierre garantizado de **25 a 22**; llamadas a
  `get_connection()` en `app/` de 121 a 118. Fugas deterministas: 0.
- `git diff --check`: exit 0.
- Alcance final del diff: el controlador, su archivo de pruebas nuevo y esta
  bitácora.
- Riesgo residual: quedan 22 sitios, todos de fuga condicional. `pagos`,
  `ventas` y `estudiantes` siguen reservados para el final.
- Siguiente acción exacta: continuar con **1.4f**. Candidatos por volumen son
  `plantilla_controller.py` con 7 sitios, `notas_controller.py` con 5 y
  `profesor_controller.py` con 1. Acordar con el usuario cuál tomar.

### 2026-08-11 — subcapa 1.4f

- Rama acordada: `main`; árbol **limpio** antes de editar, con 1.4e ya
  commiteada.
- Commit observado: `0df3d1e`, nueve commits por delante de `origin/main`
  conforme a la cadencia local acordada.
- Archivo elegido por el usuario: `app/controllers/profesor_controller.py`.
- Archivos modificados: ese controlador.
- Archivo creado: `tests/test_profesores_controlador.py`.
- Sitios migrados: 1 de 6. Los otros 5 ya estaban protegidos; el import conserva
  `get_connection`.
- Contratos HTTP, rutas, payloads, status codes, permisos, tenant, ownership y
  dependencias modificados: ninguno.
- SQL: idéntico; además de la indentación se eliminó un espacio final de línea
  heredado en `SELECT `.
- Semántica transaccional: la función es de solo lectura y no confirmaba. Migrada
  a `get_cursor()` sin `commit`. **Sin diferencias de comportamiento.**
- Observación registrada, no corregida: existe una función homónima en
  `asignacion_controller.py`, migrada en 1.4b, que consulta lo mismo pero filtra
  por `a.activo = TRUE` y por estado activo de curso y materia. La de
  `profesor_controller` no filtra nada y devuelve también asignaciones
  desactivadas. La divergencia es anterior a la migración; unificarlas sería un
  cambio funcional ajeno al alcance de esta capa. Se añadió una prueba que fija
  explícitamente la ausencia de filtros para que quede como comportamiento
  observado y no se confunda con un descuido.
- Caracterización previa: SQL, parámetros, respuesta y ausencia de filtros
  verificados contra la versión anterior, sin divergencias.
- Pruebas específicas: 3 pasaron en 0,22 s.
- Compuerta global: exit 0; 252 pruebas correctas con los 5 warnings conocidos en
  1,32 s, Ruff correcto y dependencias íntegras.
- Efecto medido: sitios sin cierre garantizado de **22 a 21**; llamadas a
  `get_connection()` en `app/` de 118 a 117. Fugas deterministas: 0.
- `git diff --check`: exit 0.
- Alcance final del diff: el controlador, su archivo de pruebas nuevo y esta
  bitácora.
- Riesgo residual: quedan 21 sitios, todos de fuga condicional. `pagos`,
  `ventas` y `estudiantes` siguen reservados para el final.
- Siguiente acción exacta: continuar con **1.4g**. Candidatos por volumen son
  `plantilla_controller.py` con 7 sitios, `notas_controller.py` con 5 y
  `asistencia_controller.py` con 1. Acordar con el usuario cuál tomar.

### 2026-08-11 — subcapa 1.4g

- Rama acordada: `main`; árbol **limpio** antes de editar, con 1.4f ya
  commiteada.
- Commit observado: `4d0e434`, diez commits por delante de `origin/main` conforme
  a la cadencia local acordada.
- Archivo elegido por el usuario: `app/controllers/asistencia_controller.py`.
- Archivos modificados: ese controlador.
- Archivo creado: `tests/test_asistencia_historial.py`.
- Sitios migrados: 1 de 2. `guardar_asistencia_controller` no se tocó: ya estaba
  protegida y es el reemplazo parcial transaccional con `rollback` que el
  inventario de contratos de 0.0 registró como efecto a preservar.
- Contratos HTTP, rutas, payloads, status codes, permisos, tenant, ownership y
  dependencias modificados: ninguno.
- SQL: idéntico. Las líneas en blanco sueltas dentro del literal se conservaron
  vacías y sin sangría, obligatorio porque `git diff --check` rechaza espacios
  finales.
- Semántica transaccional: la función es de solo lectura y no confirmaba. Migrada
  a `get_cursor()` sin `commit`. **Sin diferencias de comportamiento.**
- La agrupación por estudiante se movió fuera del bloque: es cálculo puro sobre
  filas ya traídas, sin diferencia observable, y libera la conexión antes.
- Comportamiento conservado y fijado en pruebas: un estudiante cuya fila trae
  `fecha` nula aparece igual en la respuesta con el historial vacío; el `periodo`
  vale 1 por defecto; varias fechas del mismo estudiante se agrupan en una sola
  entrada.
- Caracterización previa: SQL, parámetros, resolución de asignación, agrupación y
  respuesta verificados contra la versión anterior, sin divergencias.
- Pruebas específicas: 5 pasaron en 0,16 s.
- Compuerta global: exit 0; 257 pruebas correctas con los 5 warnings conocidos en
  1,22 s, Ruff correcto y dependencias íntegras.
- Efecto medido: sitios sin cierre garantizado de **21 a 20**; llamadas a
  `get_connection()` en `app/` de 117 a 116. Fugas deterministas: 0.
- `git diff --check`: exit 0.
- Alcance final del diff: el controlador, su archivo de pruebas nuevo y esta
  bitácora.
- Riesgo residual: quedan 20 sitios, todos de fuga condicional.
- Siguiente acción exacta: continuar con **1.4h**. Quedan pocos archivos sin
  tocar: `plantilla_controller.py` con 7 sitios y `notas_controller.py` con 5 son
  los grandes; después vienen los reservados `pagos`, `ventas` y `estudiantes`.
  Acordar con el usuario cuál tomar.

### 2026-08-11 — subcapa 1.4h

- Rama acordada: `main`; árbol **limpio** antes de editar, con 1.4g ya
  commiteada.
- Commit observado: `49eb1a7`, once commits por delante de `origin/main` conforme
  a la cadencia local acordada.
- Archivo elegido por el usuario: `app/controllers/notas_controller.py`, con
  revisión detallada solicitada expresamente.
- Archivos modificados: ese controlador.
- Archivo creado: `tests/test_notas_controlador.py`.
- Sitios migrados: 5 de 5. El archivo entero estaba desprotegido; es el segundo
  del programa que abandona `get_connection` por completo.
- Contratos HTTP, rutas, payloads, status codes, permisos, tenant, ownership y
  dependencias modificados: ninguno.
- SQL: idéntico en tablas, columnas, CTE, joins, condiciones, agrupaciones y
  orden. Además de la indentación se eliminaron espacios finales de línea
  heredados en varios literales, obligatorio por `git diff --check`.
- Semántica transaccional: preservada. Solo `crear_nota_controller` confirma.
- Se retiraron **dos imports locales redundantes** de `get_connection` dentro de
  `boletin_estudiante_controller` y `boletin_detallado_controller`. Al migrar
  quedaban muertos y Ruff habría marcado el import sin usar.
- **Patrón N+1 conservado**: `boletin_detallado_controller` ejecuta una consulta
  por asignación dentro del bucle. Optimizarlo pertenece a la capa 4; hacerlo
  aquí ampliaría el alcance. Se fijó en prueba contando las consultas: dos
  asignaciones producen tres `execute`. La migración sí mejora su seguridad: las
  N+1 consultas comparten ahora una conexión gobernada, en vez de perderse entera
  si cualquiera fallaba.
- Comportamientos verificados y fijados que no eran evidentes: las tres
  validaciones de `crear_nota_controller` devuelven error **sin adquirir
  conexión** —confirmado con cero conexiones en la versión anterior—; la salida
  temprana de `boletin_detallado_controller` **sí cerraba**, por lo que nunca fue
  fuga determinista; los ids de las actividades en blanco se fabrican
  concatenando cadenas y pueden colisionar con ids reales; el corte
  Aprobado/Reprobado está en 3,0 inclusive; y el promedio es 0 cuando no hay
  notas.
- Deuda conocida anotada, no corregida: los ids sintéticos del boletín detallado
  y el N+1.
- Caracterización previa: 12 comprobaciones contra la versión anterior sobre SQL,
  parámetros, promedios, redondeos, corte de aprobación, ids sintéticos, conteo
  de consultas y `commit`. Todas coinciden, sin divergencias.
- Pruebas específicas: 14 pasaron en 0,19 s.
- Compuerta global: exit 0; 271 pruebas correctas con los 5 warnings conocidos en
  1,15 s, Ruff correcto y dependencias íntegras.
- Efecto medido: sitios sin cierre garantizado de **20 a 15**; llamadas a
  `get_connection()` en `app/` de 116 a 111. Fugas deterministas: 0.
- `git diff --check`: exit 0.
- Volumen del diff en `app/`: 157 inserciones y 186 supresiones en un archivo.
- Alcance final del diff: el controlador, su archivo de pruebas nuevo y esta
  bitácora.
- Riesgo residual: quedan 15 sitios. `plantilla_controller.py` con 7 es el último
  archivo grande sin dinero; después solo quedan los reservados `pagos`, `ventas`
  y `estudiantes`.
- Siguiente acción exacta: continuar con **1.4i**, previsiblemente
  `plantilla_controller.py`. Acordar con el usuario.

### 2026-08-11 — subcapa 1.4i

- Rama acordada: `main`; árbol **limpio** antes de editar, con 1.4h ya
  commiteada.
- Commit observado: `4ea0723`, doce commits por delante de `origin/main` conforme
  a la cadencia local acordada.
- Archivo elegido por el usuario: `app/controllers/plantilla_controller.py`.
- Archivos modificados: ese controlador.
- Archivo creado: `tests/test_plantillas_controlador.py`.
- Sitios migrados: 7 de 7. Tercer archivo del programa que abandona
  `get_connection` por completo.
- Contratos HTTP, rutas, payloads, status codes, permisos, tenant, ownership y
  dependencias modificados: ninguno. Los `400` y `404` se conservan idénticos,
  incluidos sus mensajes.
- SQL: idéntico en tablas, columnas, condiciones, orden y parámetros; solo cambió
  la indentación.
- Semántica transaccional: preservada salvo el camino «Sin cambios» de
  `actualizar_plantilla_controller`, que ahora confirma una transacción de solo
  lectura donde antes revertía al cerrar. Misma situación registrada en 1.4b y
  1.4c; no altera datos.
- Observación relevante: este archivo **ya cerraba explícitamente antes de cada
  salida temprana**, en los siete casos. Verificado contra la versión anterior:
  el camino de tipo inválido registró 1 conexión adquirida y cerrada. No fugaba;
  por eso el barrido de 1.4 no lo marcó. La migración cubre el hueco que sí tenía
  —una excepción durante `execute`— y elimina 14 líneas de cierre manual.
- Se conservó una asimetría existente: `obtener_plantilla_activa_controller` y
  `crear_plantilla_controller` validan el tipo **antes** de abrir conexión,
  mientras `listar_plantillas_controller` lo valida ya dentro del bloque.
  Uniformarlo sería un cambio ajeno al alcance.
- Atomicidad preservada: los dos `UPDATE` de `activar_plantilla_controller`
  viajan en la misma transacción. Partirlos habría permitido dejar un tipo sin
  ninguna plantilla activa.
- Caracterización previa: 18 comprobaciones contra la versión anterior sobre SQL,
  parámetros, códigos de estado, fallback a predefinida, atomicidad, nombre por
  defecto al duplicar y `commit`. Todas coinciden salvo la diferencia prevista.
- Pruebas específicas: 19 pasaron en 0,37 s.
- Compuerta global: exit 0; 290 pruebas correctas con los 5 warnings conocidos en
  1,23 s, Ruff correcto y dependencias íntegras.
- Efecto medido: sitios sin cierre garantizado de **15 a 8**; llamadas a
  `get_connection()` en `app/` de 111 a 104. Fugas deterministas: 0.
- `git diff --check`: exit 0.
- Volumen del diff en `app/`: 129 inserciones y 166 supresiones en un archivo.
- Alcance final del diff: el controlador, su archivo de pruebas nuevo y esta
  bitácora.
- **Corrección de una expectativa previa**: se venía anotando que los sitios
  restantes serían todos financieros. Al localizarlos resultó falso. De los 8,
  solo 3 están en dominios reservados —2 en `estudiante_controller` y 1 en
  `pagos_controller`— y `ventas` **ya no tiene ninguno**. Los otros 5 son
  académicos: 2 en `planilla_controller`, 1 en `planilla_excel_controller` y 2 en
  archivos de rutas, `asignaciones.py` y `observaciones.py`.
- Dato nuevo: esos 2 de rutas son las únicas aperturas que quedan fuera de
  controllers y services. Conviene mirarlos aparte, porque una apertura en la
  capa HTTP es un patrón distinto al de los demás.
- Siguiente acción exacta: ejecutar **1.4j**. Los candidatos académicos
  —`planilla_controller` con 2, `planilla_excel_controller` con 1 y las 2 rutas—
  pueden tomarse antes que los reservados. Los 3 de `estudiantes` y `pagos` se
  recomiendan **de uno en uno y con revisión detallada**. Acordar con el usuario
  por cuál empezar.

### 2026-08-11 — subcapa 1.4j

- Rama acordada: `main`; árbol **limpio** antes de editar, con 1.4i ya
  commiteada.
- Commit observado: `a6038c8`, trece commits por delante de `origin/main`
  conforme a la cadencia local acordada.
- Alcance decidido por el asistente a petición del usuario, que delegó la
  elección: dominio planilla completo, agrupando los dos archivos por coherencia
  de revisión.
- Archivos modificados: `app/controllers/planilla_controller.py` y
  `app/controllers/planilla_excel_controller.py`.
- Archivo creado: `tests/test_planilla_controlador.py`.
- Sitios migrados: 3 de 3. Ambos archivos abandonan `get_connection` por
  completo.
- Contratos HTTP, rutas, payloads, status codes, permisos, tenant, ownership y
  dependencias modificados: ninguno.
- SQL: idéntico en tablas, columnas, joins, condiciones y parámetros; solo cambió
  la indentación y se eliminaron espacios finales heredados.
- Semántica transaccional: preservada. Los dos que escriben confirmaban siempre y
  el de lectura nunca lo hacía. **Sin diferencias de comportamiento.**
- Atomicidad preservada: el par `DELETE` + `INSERT` de
  `registrar_nota_planilla_controller` viaja en una sola transacción. Partirlo
  habría permitido perder la nota anterior sin escribir la nueva.
- La validación de pertenencia del estudiante devuelve error **sin abrir
  conexión**; verificado con cero conexiones adquiridas en la versión anterior.
- Rarezas heredadas documentadas, no corregidas: `planilla_excel_controller` no
  genera ningún Excel pese a su nombre; descarta la descripción mágica
  `"Desde React"`; y devuelve `promedio` como **cadena vacía** cuando el
  estudiante no tiene notas numéricas, en vez de `0` o `None`. También se fijó
  que las notas de tipo `desarrollo` no entran en el promedio y que en ese tipo
  se guarda `valoracion` descartando `nota`.
- Caracterización previa: 10 comprobaciones contra la versión anterior. Todas
  coinciden, sin divergencias.
- Pruebas específicas: 10 pasaron en 0,19 s.
- Compuerta global: exit 0; 300 pruebas correctas con los 5 warnings conocidos,
  Ruff correcto y dependencias íntegras.
- Efecto medido: sitios sin cierre garantizado de **8 a 5**; llamadas a
  `get_connection()` en `app/` de 104 a 101. Fugas deterministas: 0.
- `git diff --check`: exit 0.
- Alcance final del diff: los dos controladores, el archivo de pruebas nuevo y
  esta bitácora.
- Siguiente acción exacta: ejecutar **1.4k** con los 5 sitios restantes: 2 en
  `estudiante_controller`, 1 en `pagos_controller` y 2 en archivos de rutas. Los
  de rutas conviene mirarlos juntos por ser el único patrón de apertura en la
  capa HTTP; los 3 reservados, de uno en uno y con revisión detallada. Acordar
  con el usuario.

### 2026-08-11 — subcapa 1.4k

- Rama acordada: `main`; árbol **limpio** antes de editar, con 1.4j ya
  commiteada.
- Commit observado: `f68f16a`, catorce commits por delante de `origin/main`
  conforme a la cadencia local acordada.
- Alcance decidido por el asistente, con el usuario delegando la elección: las 2
  aperturas de la capa HTTP, por ser el único patrón de su tipo.
- Archivos modificados: `app/routes/asignaciones.py`,
  `app/routes/observaciones.py` y `tests/test_asignaciones_pagination.py`.
- Archivo creado: `tests/test_observaciones_ruta.py`.
- Sitios migrados: 2 de 2. **Ninguna ruta abre ya conexiones**; todas las
  aperturas restantes están en controllers.
- En `observaciones.py` se sustituyó un **import local** de `get_connection`
  dentro de la función por el import del módulo, como en 1.4h.
- Contratos HTTP, rutas, payloads, status codes, permisos, tenant, ownership y
  dependencias modificados: ninguno.
- SQL: idéntico; solo cambió la indentación y se eliminaron espacios finales
  heredados.
- Semántica transaccional: ambas son de solo lectura y no confirmaban. Migradas a
  `get_cursor()` sin `commit`. **Sin diferencias de comportamiento.**
- **Incidencia relevante**: la prueba existente
  `test_mis_clases_incluye_jornada_del_curso` se puso en rojo porque parcheaba
  `asignaciones.get_connection`, símbolo que dejó de existir en el módulo. Es el
  comportamiento deseado de la red: el cambio de régimen se hizo visible en el
  acto. Se adaptó **solo el mecanismo de sustitución** —doble de `get_cursor` en
  lugar de doble de conexión— y se conservaron las aserciones palabra por
  palabra. `FakeConnection`, ya sin uso, se retiró.
- Precedente registrado: al migrar un módulo hay que comprobar si alguna prueba
  existente parchea `get_connection` sobre él. Es la primera vez que ocurre en 13
  tandas.
- Caracterización: 4 pruebas nuevas para la ruta de observaciones, que no tenía
  cobertura. Fijan que los guards de permiso corren **antes** de tocar la base, y
  que la ruta devuelve `None` cuando no hay observación, no un `404` ni un
  diccionario vacío.
- Caracterización previa: SQL, parámetros, orden de guards, respuesta y cierre
  verificados contra la versión anterior en ambas rutas.
- Incidencia de utillaje: el primer intento del script de verificación falló al
  intentar recortar los imports del módulo de rutas por líneas, rompiendo un
  import multilínea. Se corrigió extrayendo la función con AST. El código migrado
  no estuvo en duda.
- Compuerta global: exit 0; 304 pruebas correctas con los 5 warnings conocidos en
  1,56 s, Ruff correcto y dependencias íntegras.
- Efecto medido: sitios sin cierre garantizado de **5 a 3**; llamadas a
  `get_connection()` en `app/` de 101 a 99. Aperturas fuera de controllers y
  services: de 2 a **0**. Fugas deterministas: 0.
- `git diff --check`: exit 0.
- Alcance final del diff: las dos rutas, la prueba existente adaptada, el archivo
  de pruebas nuevo y esta bitácora.
- Siguiente acción exacta: ejecutar **1.4l**, los 3 sitios reservados: 2 en
  `estudiante_controller` y 1 en `pagos_controller`. Se recomienda tomarlos de
  uno en uno y con revisión detallada. Acordar con el usuario por cuál empezar.

### 2026-08-11 — subcapa 1.4l

- Rama acordada: `main`; árbol **limpio** antes de editar, con 1.4k ya
  commiteada.
- Commit observado: `bdaf266`, quince commits por delante de `origin/main`
  conforme a la cadencia local acordada.
- Alcance decidido por el asistente con revisión detallada, según la delegación
  del usuario: `pagos_controller.py`, el más pequeño de los reservados.
- Archivos modificados: ese controlador.
- Archivo creado: `tests/test_pagos_historial.py`.
- Sitios migrados: 1 de 7. Los otros seis ya estaban protegidos; el import
  conserva `get_connection`.
- Hallazgo tranquilizador: el único sitio desprotegido del dominio de pagos era
  una **consulta**, no una escritura. Las rutas que mueven montos, aplican saldos
  y anulan ya tenían `try/finally` antes de este programa.
- Contratos HTTP, rutas, payloads, status codes, permisos, tenant, ownership y
  dependencias modificados: ninguno.
- SQL: idéntico; solo indentación y eliminación de espacios finales heredados.
- Semántica transaccional: de solo lectura, no confirmaba ni antes ni ahora.
  **Sin diferencias de comportamiento.**
- `_formatear_pago` no se modificó, pero se caracterizó por producir lo que ve el
  administrador y no tener prueba: `monto` como `float`; `fecha` en
  `"%d/%m/%Y %I:%M %p"`; `fecha` nula como **cadena vacía** mientras
  `fecha_anulacion` nula queda como `None`, asimetría heredada que se conserva;
  `estado` ausente asumido como `"Pagado"`; y la bandera `anulado` derivada del
  estado ignorando mayúsculas y espacios. También se fijaron los campos de
  auditoría de anulación, por ser el rastro de una operación reversible.
- Caracterización previa: 6 comprobaciones contra la versión anterior, extrayendo
  con AST solo la función migrada y su formateador. Todas coinciden.
- Pruebas específicas: 6 pasaron en 0,19 s.
- Compuerta global: exit 0; 310 pruebas correctas con los 5 warnings conocidos en
  1,40 s, Ruff correcto y dependencias íntegras.
- Efecto medido: sitios sin cierre garantizado de **3 a 2**; llamadas a
  `get_connection()` en `app/` de 99 a 98. Fugas deterministas: 0.
- `git diff --check`: exit 0.
- Alcance final del diff: el controlador, su archivo de pruebas nuevo y esta
  bitácora.
- Siguiente acción exacta: ejecutar **1.4m**, los 2 últimos sitios, ambos en
  `app/controllers/estudiante_controller.py`: `crear_estudiante_controller` y
  `actualizar_estudiante_controller`. Con eso se agota la migración y la capa
  puede pasar a los timeouts y el pool.

### 2026-08-11 — subcapa 1.4m, migración completa

- Rama acordada: `main`; árbol **limpio** antes de editar, con 1.4l ya
  commiteada.
- Commit observado: `e9536e3`, dieciséis commits por delante de `origin/main`
  conforme a la cadencia local acordada.
- Alcance: los 2 últimos sitios, con revisión detallada solicitada por el
  usuario.
- Archivos modificados: `app/controllers/estudiante_controller.py`.
- Archivo creado: `tests/test_estudiantes_controlador.py`.
- Sitios migrados: 2. **El recuento de aperturas sin cierre garantizado llega a
  cero.**
- Contratos HTTP, rutas, payloads, status codes, permisos, tenant, ownership y
  dependencias modificados: ninguno.
- SQL: idéntico en columnas, orden de parámetros y `COALESCE`; solo cambió la
  indentación y se eliminaron espacios finales heredados.
- Semántica transaccional: ambas confirmaban siempre y siguen haciéndolo,
  incluido el camino en que la actualización no encuentra al estudiante. **Sin
  diferencias de comportamiento.**
- Riesgo específico atendido: las dos escriben 35 columnas posicionalmente. Un
  desplazamiento silencioso guardaría un dato en el campo equivocado sin error.
  La caracterización usa el nombre de cada campo como su propio valor y afirma la
  tupla completa en orden.
- Regla fijada: `estado = COALESCE(%s, estado, 'activo')` hace que enviar `None`
  **conserve** el estado guardado en vez de sobrescribirlo. Al crear, en cambio,
  el estado siempre se normaliza.
- Caracterización previa: 5 comprobaciones contra la versión anterior,
  extrayendo con AST solo las dos funciones. Todas coinciden.
- Pruebas específicas: 5 pasaron en 0,19 s.
- Compuerta global: exit 0; **315** pruebas correctas con los 5 warnings
  conocidos, Ruff correcto y dependencias íntegras.
- Efecto medido: sitios sin cierre garantizado de **2 a 0**; llamadas a
  `get_connection()` en `app/` de 98 a 96.
- `git diff --check`: exit 0.
- Alcance final del diff: el controlador, su archivo de pruebas nuevo y esta
  bitácora.
- **Cierre de la migración**: quince tandas, 50 sitios migrados, 123 pruebas
  nuevas, ninguna regresión y la compuerta en verde en cada paso. Quedan los 2
  sitios de propiedad delegada de `super_admin`, que no son fugas y se
  clasificaron como tales desde 1.0.
- Siguiente acción exacta: ejecutar **1.5**, timeouts y manejo del pool con
  evidencia medida. Es la parte que el usuario reordenó al final en 1.3 y la
  única del alcance de la capa que sigue pendiente. Antes de empezar conviene
  decidir qué timeouts se fijan —`connect_timeout`, `statement_timeout`,
  `lock_timeout`— y cómo se mide la evidencia, porque tocar `_create_pool()`
  afecta a **todas** las conexiones a la vez.

### 2026-08-11 — subcapa 1.5

- Rama acordada: `main`; árbol **limpio** antes de editar, con 1.4m ya
  commiteada.
- Commit observado: `e3acb6f`, diecisiete commits por delante de `origin/main`
  conforme a la cadencia local acordada.
- Archivos modificados: `app/config.py` y `app/db/session.py`.
- Archivo creado: `tests/test_db_pool_timeouts.py`.
- Contratos HTTP, rutas, payloads, status codes, permisos, tenant, ownership,
  SQL de producto y dependencias modificados: ninguno.
- Se añadieron cuatro ajustes configurables: `DB_CONNECT_TIMEOUT_SECONDS` (10 s),
  `DB_STATEMENT_TIMEOUT_MS` (30 000), `DB_LOCK_TIMEOUT_MS` (10 000) y
  `DB_IDLE_IN_TRANSACTION_TIMEOUT_MS` (60 000). Antes no existía **ninguno**.
- Se aplican en `_create_pool()` vía `connect_timeout` y `options`, al nacer cada
  conexión física. No añaden viajes extra a la base.
- Decisión de diseño: un ajuste con valor **0 se omite**, no se envía. Enviar
  `-c statement_timeout=0` desactivaría el timeout de forma explícita y pisaría
  el valor por defecto del proveedor; omitirlo lo respeta. Poner 0 en el `.env`
  significa «no opines».
- `DB_IDLE_IN_TRANSACTION_TIMEOUT_MS` se eligió deliberadamente como defensa del
  servidor frente a la clase de fallo corregida en 1.4: si vuelve a quedar una
  conexión con transacción abierta, PostgreSQL la reclama.
- **Evidencia medida del pool**, no supuesta: se construyó un
  `ThreadedConnectionPool` auténtico con `psycopg2.connect` sustituido por un
  doble. Resultados: el pool agotado lanza `PoolError` **de inmediato** sin
  esperar; devolver una conexión permite reutilizar la misma instancia; nunca se
  superan `maxconn` conexiones; `putconn` **revierte** una conexión devuelta con
  transacción abierta y **cierra** la que está en estado desconocido;
  `closeall()` cierra todas; y `get_pool()` crea el pool una sola vez.
- Hallazgo no documentado antes en el proyecto: el pool tiene su **propia red de
  seguridad** en `putconn`, independiente de la de `get_cursor`. Se descubrió
  porque el primer doble de conexión carecía de `info.transaction_status` y la
  prueba falló; investigarlo reveló el comportamiento real.
- Riesgo asumido: `statement_timeout` es el único ajuste capaz de romper algo que
  hoy funciona. 30 s es holgado para una petición HTTP, pero **no está calibrado
  contra los tiempos reales de este sistema**.
- **Verificación pendiente**: medir la duración de las consultas pesadas
  —boletines, planillas, reportes financieros— sobre datos comparables a
  producción y ajustar `DB_STATEMENT_TIMEOUT_MS` en consecuencia. No puede
  hacerse con pruebas herméticas. Se registra sin darla por cumplida, igual que
  la ejecución remota de CI en la capa 0.
- Mitigación sin tocar código: subir el valor en el `.env`, o ponerlo en 0 para
  volver exactamente al comportamiento anterior.
- Primer cambio del programa que afecta a **todas las conexiones a la vez**.
  Merece más atención al publicarlo que las quince tandas de migración.
- Pruebas específicas: 13 pasaron en 0,20 s.
- `Settings(_env_file=None)` con el entorno de CI resuelve los cuatro valores por
  defecto correctamente.
- Compuerta global: exit 0; **328** pruebas correctas con los 5 warnings
  conocidos en 1,48 s, Ruff correcto y dependencias íntegras.
- `git diff --check`: exit 0.
- Alcance final del diff: `app/config.py`, `app/db/session.py`, el archivo de
  pruebas nuevo y esta bitácora.
- Siguiente acción exacta: ejecutar **1.6**, el cierre de la capa: compuerta
  global, auditoría del diff completo desde el commit base, staging, rollback y
  verificación manual. Antes conviene decidir con el usuario si la calibración de
  `statement_timeout` se completa o se acepta como pendiente registrada, igual
  que se hizo al cerrar la capa 0.

### 2026-08-11 — subcapa 1.5, corrección: incompatibilidad con endpoint agrupado

- **La subcapa 1.5 no quedó cerrada.** El usuario probó el login local contra la
  base real y `_create_pool()` falló al inicializar con
  `unsupported startup parameter in options: statement_timeout`. La aplicación no
  arrancaba.
- Causa: el primer intento envió los tres GUCs en el parámetro `options` del
  paquete de arranque. La `DATABASE_URL` usa el endpoint `-pooler` de Neon, que
  es **PgBouncer en modo transacción** y solo admite cinco parámetros de arranque
  —`client_encoding`, `datestyle`, `timezone`, `standard_conforming_strings`,
  `application_name`—; cualquier otro hace fallar la conexión entera.
- Investigación previa a tocar código, por instrucción explícita del usuario:
  documentación de Neon sobre agrupación de conexiones y errores de conexión, y
  material de PgBouncer sobre modo transacción. Conclusiones: los `SET` de sesión
  tampoco son fiables tras un endpoint agrupado porque la conexión se recicla
  entre transacciones; el patrón recomendado es **`SET LOCAL` dentro de la
  transacción**.
- Compatibilidad de cada timeout, establecida y no supuesta:
  `connect_timeout` es de **libpq**, se resuelve en el cliente y **nunca viaja al
  servidor**, así que es compatible con endpoint agrupado y directo por igual;
  `statement_timeout`, `lock_timeout` e `idle_in_transaction_session_timeout` son
  GUCs de servidor y **no pueden ir en el arranque**.
- Corrección aplicada: `connect_timeout` se **conserva** como parámetro del pool.
  Los otros tres pasan a aplicarse con
  `set_config(nombre, valor, TRUE)` al tomar la conexión, en la misma preparación
  que ya fijaba el `search_path`. El tercer argumento en `TRUE` equivale a
  `SET LOCAL`: dura lo que la transacción y no puede filtrarse al siguiente
  cliente. Los tres viajan en una sola sentencia, con valores ligados como
  parámetros en vez de interpolados.
- El mecanismo elegido funciona igual contra un endpoint agrupado que contra uno
  directo, así que **no hizo falta detectar el tipo de endpoint ni bifurcar el
  código**.
- Lo que **no** se hizo: eliminar timeouts para que el login volviera a pasar.
- Coste asumido: un viaje extra a la base al tomar cada conexión, sumado al que
  ya se hacía para el `search_path`.
- Por qué las pruebas no lo detectaron: todas eran herméticas. La diferencia
  entre endpoint agrupado y directo solo existe en una conexión real. Es el
  límite exacto de la estrategia de verificación elegida en 1.0 y la primera vez
  que ese límite cuesta algo.
- **Verificación añadida, en dos capas**: una guardia hermética de regresión en
  `tests/test_db_pool_timeouts.py`, que afirma que `_create_pool()` no envía
  `options`, que ningún GUC de servidor aparece en sus parámetros y que los que
  usa son un subconjunto de los que un endpoint agrupado tolera; y una
  comprobación operativa real en `scripts/check_db_timeouts.py`, que abre una
  conexión con la `DATABASE_URL` configurada, informa si el endpoint es agrupado
  o directo y lee con `SHOW` los valores efectivos. Solo lee y no imprime
  credenciales.
- Prueba existente adaptada: `test_get_connection_prepara_la_conexion_y_la_retiene`
  de 1.1 se puso en rojo porque preparar una conexión pasó de una sentencia a
  dos. Se actualizó **reforzando** la aserción —número y forma de la segunda— en
  vez de relajarla.
- Archivos modificados: `app/config.py`, `app/db/session.py` y
  `tests/test_db_session_contrato.py`.
- Archivos creados: `tests/test_db_pool_timeouts.py` y
  `scripts/check_db_timeouts.py`.
- Compuerta global: exit 0; **334** pruebas correctas con los 5 warnings
  conocidos en 1,50 s, Ruff correcto y dependencias íntegras.
- `git diff --check`: exit 0.
- Lección registrada para el resto del programa: un cambio en la creación del
  pool o en la preparación de la conexión **no puede considerarse verificado solo
  con pruebas herméticas**. Debe probarse contra la base real antes de darlo por
  cerrado.

### 2026-08-11 — subcapa 1.5, verificación contra la base real y cierre

- Verificación ejecutada por el usuario contra la base real, con la
  `DATABASE_URL` de producción apuntando al endpoint `-pooler` de Neon. El script
  identificó el endpoint como `AGRUPADO (pooler)`, es decir el mismo que provocó
  el fallo original.
- **Evidencia 1, arranque**: el login local funciona de nuevo. Demuestra que
  `_create_pool()` inicializa y que `set_config(..., TRUE)` se ejecuta sin error
  tras PgBouncer, que era la incógnita real de la corrección.
- **Evidencia 2, valores efectivos**: `SHOW` devolvió `statement_timeout = 30s`,
  `lock_timeout = 10s` e `idle_in_transaction_session_timeout = 1min`.
- **Evidencia 3, cumplimiento medido**: con `--forzar`, PostgreSQL canceló la
  consulta tras **1,11 s** frente a un límite de 1 s. Es la evidencia que
  convierte «configurado» en «verificado» y la que satisface la exigencia del
  índice maestro de definir los timeouts con evidencia medida.
- Se amplió `scripts/check_db_timeouts.py` con la opción `--forzar`, que baja
  `statement_timeout` a un segundo solo para esa transacción y lanza un
  `pg_sleep` más largo. Recorre el mismo camino que el valor real sin obligar a
  esperar treinta segundos. Sigue sin escribir nada: `pg_sleep` solo duerme.
- Distinción registrada para no confundir dos cosas: el **mecanismo** está
  verificado; el **valor** de 30 s no está calibrado. Que el límite se cumpla no
  dice que 30 s sea el número correcto para este sistema.
- Ruff sobre el script ampliado: correcto.
- Estado de la subcapa: **cerrada**.
- Verificación que permanece pendiente, heredada a 1.6: calibrar
  `DB_STATEMENT_TIMEOUT_MS` midiendo la duración de las consultas pesadas
  —boletines, planillas, reportes financieros— sobre datos comparables a
  producción. No puede resolverse con pruebas herméticas ni con el script
  actual.

### 2026-08-11 — subcapa 1.6, cierre de la capa

- Rama acordada: `main`. Auditoría ejecutada sobre commits más árbol de trabajo,
  con 1.5 aún sin commitear en ese momento.
- Instrucción del usuario: **no introducir cambios funcionales durante 1.6**. Se
  cumplió: esta subcapa solo verifica y documenta.
- Decisión del usuario, registrada: la calibración de `DB_STATEMENT_TIMEOUT_MS`
  se **acepta como pendiente operativa** y no bloquea el cierre. Motivos dados: el
  mecanismo ya está verificado contra Neon real y el valor puede ajustarse por
  entorno sin desplegar código.
- Compuerta global: exit 0; 334 pruebas correctas, Ruff correcto, `pip check`
  correcto, `git diff --check` exit 0.
- Auditoría del rango `6754e4aa..árbol`: **17 commits, todos explicados** en este
  documento, uno por subcapa.
- Categorías prohibidas: **ninguna tocada**. Sin `migrations/`,
  `requirements.txt`, `.github/`, `.sql`, `apply_migration.py` ni
  `scripts/verify.py`.
- Análisis semántico del diff de `app/`, normalizando espacios: de 1229 líneas
  quitadas y 1064 añadidas, **938 son idénticas salvo sangría**. El cambio real
  son 291 quitadas y 126 añadidas. Lo quitado se clasifica en 118 cierres
  manuales, 100 aperturas manuales, 28 líneas en blanco, 22 `commit` manuales y
  19 imports viejos. Lo añadido, en 50 `with get_cursor` y 17 imports nuevos. Las
  4 y 59 líneas restantes se revisaron una por una y **todas pertenecen a 1.5**.
- Contratos HTTP: ninguna línea del diff modifica un decorador `@router`, un
  `response_model` ni un `status_code`. Los `status_code` que aparecen son
  idénticos salvo sangría.
- Hallazgo registrado y **no corregido** por la instrucción de no cambiar nada:
  `.env.example` documenta los dos ajustes de tamaño del pool pero **no los
  cuatro timeouts** añadidos en 1.5. Riesgo bajo, sin efecto en comportamiento,
  pero quien prepare un entorno nuevo no sabrá que existen ni que 0 significa «no
  fijar nada».
- Staging: este proyecto no tiene entorno intermedio; `main` despliega a
  producción de forma automática. El equivalente aplicable fue la verificación
  local contra la base real ya ejecutada en 1.5.
- Rollback documentado en cuatro niveles: total por `git revert` inverso;
  selectivo por tanda, posible porque cada subcapa es un commit autocontenido;
  **mitigación sin desplegar** subiendo o anulando `DB_STATEMENT_TIMEOUT_MS` en
  el `.env`, que es la primera palanca ante un incidente; y reversión solo de 1.5
  conservando la migración.
- Verificación manual posterior a la publicación: seis pasos documentados, con
  énfasis en probar una lectura pesada real, que es lo que más probablemente
  revele una calibración incorrecta.
- Estado: **capa 1 cerrada**, con una verificación operativa pendiente y
  aceptada.
- Siguiente acción exacta: el usuario commitea 1.5 y este cierre, y publica. La
  capa 2, concurrencia, **queda en espera** y no se activa sin orden explícita.

## Entrega al próximo chat

- Capa activa: **ninguna**. La capa 1 quedó **cerrada** el 2026-08-11.
- Última subcapa terminada: **1.6**, el cierre. Compuerta global en exit 0,
  auditoría del diff de 17 commits sin hallazgos de alcance, staging, rollback y
  verificación manual documentados.
- Resultado de la capa: las 50 aperturas sin cierre garantizado llegaron a **0**,
  las 2 fugas deterministas a **0**, ninguna ruta abre conexiones, hay 4 timeouts
  donde antes no había ninguno, y la suite pasó de 192 a **334** pruebas.
- Siguiente capa: **2, concurrencia**. En espera. No activarla sin orden
  explícita del usuario.
- **Verificación operativa pendiente y aceptada**: calibrar
  `DB_STATEMENT_TIMEOUT_MS` contra la duración real de las consultas pesadas. El
  usuario la aceptó como pendiente para no bloquear el cierre. **No marcarla como
  cumplida.** Si aparece `canceling statement due to statement timeout` en los
  logs, el valor está mal calibrado, no el código.
- Tarea de documentación pendiente, detectada en la auditoría de 1.6:
  `.env.example` no documenta los cuatro ajustes de timeout. No se corrigió por
  la instrucción de no cambiar nada durante el cierre.
- Herramienta disponible: `scripts/check_db_timeouts.py`, con `--forzar` para
  comprobar que el timeout se cumple y no solo que está fijado. Es la única
  verificación que distingue un endpoint agrupado de uno directo.
- Lección registrada en 1.5: un cambio en la creación del pool o en la
  preparación de la conexión **no se puede dar por verificado solo con pruebas
  herméticas**.
- Lección registrada en 1.5: un cambio en la creación del pool o en la
  preparación de la conexión **no se puede dar por verificado solo con pruebas
  herméticas**. La diferencia entre endpoint agrupado y directo solo existe en
  una conexión real.
- Estado de la migración: **completa**. Los 50 sitios sin cierre garantizado
  llegaron a cero en quince tandas, con 136 pruebas nuevas y sin regresiones.
  Ninguna ruta abre conexiones.
- Timeouts: antes no existía ninguno. Ahora hay cuatro configurables por entorno,
  con 0 como «no opines» en vez de «sin límite».
- **Verificación pendiente que 1.6 debe tratar explícitamente**: calibrar
  `DB_STATEMENT_TIMEOUT_MS` contra la duración real de las consultas pesadas
  —boletines, planillas, reportes financieros—. No puede resolverse con pruebas
  herméticas. Debe decidirse si se completa o se acepta como pendiente
  registrada, como se hizo con la CI remota al cerrar la capa 0. **No darla por
  cumplida.**
- Riesgo vivo asociado: `statement_timeout` en 30 s es el único ajuste capaz de
  romper algo que hoy funciona. Mitigación sin tocar código: subir el valor en el
  `.env` o ponerlo en 0.
- Cadencia de publicación acordada: se trabaja y se verifica en local; el usuario
  decide cuándo publicar. `main` despliega a producción de forma automática.
- Quedan los 2 sitios de propiedad delegada en `super_admin`, que no son fugas y
  se clasificaron como tales desde 1.0. Son el único patrón de apertura que no
  usa `get_cursor`.
- Deudas conocidas anotadas y **no** corregidas, por estar fuera del alcance de
  esta capa: el N+1 de `boletin_detallado_controller`, que pertenece a la capa 4;
  los ids sintéticos que ese mismo boletín fabrica por concatenación de cadenas;
  las dos funciones homónimas `obtener_clases_profesor_controller` con filtros
  distintos; y la cadena mágica `"Desde React"` de `planilla_excel_controller`.
- Precedente útil: al migrar un módulo, comprobar si alguna prueba existente
  parchea `get_connection` sobre él. Ocurrió una vez en quince tandas.
