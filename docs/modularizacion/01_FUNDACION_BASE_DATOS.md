# Capa 1: fundación de base de datos

Última revisión: 2026-08-11.

## Control

- Estado: **Activa**.
- Commit base: `6754e4aad59c1e428ea97d31fe8e96fdbba7694d`.
- Rama acordada: `main`.
- Estado al activar: árbol limpio; `main` sincronizada con `origin/main`.
- Primera subcapa pendiente: **1.4b**, siguiente tanda de migración.
- Código de producto modificado hasta ahora: servicios de validación (1.2), tres
  funciones del planeador anual (1.3) y cuatro del controlador de usuarios (1.4).
  Sin cambio de comportamiento observable, salvo la fuga determinista corregida
  en 1.4, documentada allí.
- Progreso de la capa: **39 sitios** sin cierre garantizado, de 50 iniciales.
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
| 1.4b | Tandas restantes hasta agotar los 39 sitios pendientes | Pendiente |
| 1.5 | Timeouts y manejo del pool definidos con evidencia medida | Pendiente |
| 1.6 | Cierre: compuerta global, staging, rollback y verificación manual | Pendiente |

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

## Entrega al próximo chat

- Capa activa: **1, fundación de base de datos**.
- Última subcapa terminada: **1.4**, tercera tanda: las 4 funciones desprotegidas
  de `usuario_controller.py`, incluida la corrección de la primera fuga
  determinista encontrada.
- Primera subcapa pendiente: **1.4b**, siguiente tanda de migración.
- Progreso: **39 de 50** sitios desprotegidos siguen pendientes; de ellos, 38
  fugan solo ante excepción y **1 fuga en camino normal**.
- Prioridad siguiente: `app/controllers/asignacion_controller.py:642`,
  `eliminar_asignacion_controller`, la única fuga determinista que queda.
- Orden vigente: primero completar la migración, después los timeouts. Reordenado
  por instrucción explícita del usuario el 2026-08-11.
- Bloqueos: ninguno. La estrategia de verificación quedó decidida el 2026-08-11:
  pruebas de contrato con pool falso. La guardia estática y PostgreSQL en CI se
  descartaron para esta capa.
- Dato que gobierna la capa: 146 aperturas en `app/`, de las cuales 50 pierden la
  conexión ante excepción, con `maxconn = 10` y sin ningún timeout configurado.
- Riesgo aceptado: la verificación elegida cubre la infraestructura, no cada uno
  de los 146 sitios; la corrección de cada sitio dependerá de la revisión del
  diff.
- Cadencia de publicación: acordada. Se trabaja y se verifica en local; el
  usuario decide cuándo publicar.
- Siguiente acción exacta: ejecutar **1.4b** empezando por
  `eliminar_asignacion_controller` en `app/controllers/asignacion_controller.py`,
  la única fuga determinista pendiente. El archivo tiene 6 sitios desprotegidos;
  acordar con el usuario si se migran todos o solo el crítico. `pagos`, `ventas`
  y `estudiantes` quedan para el final.
