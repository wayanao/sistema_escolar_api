# Capa 1: fundación de base de datos

Última revisión: 2026-08-11.

## Control

- Estado: **Activa**.
- Commit base: `6754e4aad59c1e428ea97d31fe8e96fdbba7694d`.
- Rama acordada: `main`.
- Estado al activar: árbol limpio; `main` sincronizada con `origin/main`.
- Primera subcapa pendiente: **1.2**, primera migración de sitios desprotegidos.
- Código de producto modificado hasta ahora: **Ninguno**. 1.0 y 1.1 no tocaron
  `app/`; 1.2 será la primera que sí.
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
| 1.2 | Primer consumidor migrado al contrato, con caracterización previa | Pendiente |
| 1.3 | Timeouts y manejo del pool definidos con evidencia medida | Pendiente |
| 1.4 | Migración progresiva del resto de aperturas manuales | Pendiente |
| 1.5 | Cierre: compuerta global, staging, rollback y verificación manual | Pendiente |

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

## Entrega al próximo chat

- Capa activa: **1, fundación de base de datos**.
- Última subcapa terminada: **1.1**, contrato declarado y fijado con 9 pruebas de
  pool falso. Sin tocar `app/`.
- Primera subcapa pendiente: **1.2**, primera tanda de migración. Es la primera
  que modifica código de producto.
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
- Siguiente acción exacta: ejecutar **1.2**, la primera tanda de migración de
  sitios desprotegidos al régimen correcto. Antes debe acordarse con el usuario
  el tamaño de la tanda y por qué controlador empezar, porque es la primera
  subcapa que modifica `app/` y la revisión del diff es la red de seguridad
  elegida.
