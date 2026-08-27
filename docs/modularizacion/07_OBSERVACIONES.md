# Capa 7: observaciones

Última revisión: 2026-08-21.

## Control

- Estado: **Cerrada** el 2026-08-21, con sus dos subcapas **7.0 y 7.1**
  completas —ambas del mismo día— y la **verificación manual ejecutada por el
  usuario con resultado correcto**. Activada el 2026-08-21.
- Commit base: `fd3f93a2ad97daa0a34081eb2f95504dd1a9e4df`.
- Rama acordada: `main`.
- Primera subcapa pendiente: **ninguna definida**. Con 7.1 la **frontera de
  persistencia del dominio quedó cerrada**. **El usuario decidió cerrar la capa
  aquí**, sin abrir 7.2. Ver «Punto de decisión, resuelto el 2026-08-21».
- Código de producto modificado al activar: **Ninguno**. Tampoco en 7.0: su diff
  es **un solo archivo de prueba nuevo** y ningún archivo rastreado modificado,
  igual que los de 5.0, 6.0 y las cinco 7.0 anteriores. **7.1 sí modifica
  producto**: la ruta, el controlador y un repositorio nuevo.
- Estado de publicación, corregido el 2026-08-21 por orden explícita del
  usuario: **publicada**. `HEAD` y la referencia local `origin/main` coinciden
  en `580c0ad6f0d14d16af5cbd8b2a4a9e4532485b89`, y el reflog registra
  `update by push` a las 15:58:27 -0500. En este turno no se consultó el remoto
  real ni se atribuye ningún run de GitHub Actions.
- Dominio de esta capa: **observaciones, y solo ese**. La capa 7 del índice es
  «resto de dominios» y ordena expresamente **priorizar uno a la vez**, así que
  esta bitácora cubre un único dominio. Los demás quedan fuera y necesitarán su
  propia bitácora y su propia orden.
- Autorización: orden explícita del usuario el 2026-08-21, **nombrando el
  dominio**: «activa el dominio observaciones». Lo eligió de la lista de los
  siete que quedaban en espera. No se dedujo por inferencia.
- La autorización permite **solamente la activación documental**. No autoriza
  inspeccionar código del dominio, implementar 7.0, tocar la base de datos,
  hacer deploy, commit ni push.

### Relación con las cinco bitácoras cerradas de la capa 7

`07_DASHBOARD.md`, `07_NOTAS.md`, `07_VENTAS.md`, `07_ASISTENCIA.md` y
`07_BOLETIN.md` son las bitácoras **cerradas** de los cinco primeros dominios
migrados bajo la capa 7. Esta es la sexta, y es **independiente**: su commit
base, sus subcapas, su compuerta y su cierre son propios. Cerrar `observaciones`
no reabre ninguna de las cinco, ni al revés.

**Las subcapas se numeran por bitácora**, así que esta capa vuelve a empezar en
**7.0**. En prosa deben citarse siempre con el nombre del dominio; el número
solo no identifica una subcapa.

## Objetivo

Migrar el dominio de **observaciones** con contratos y pruebas, conservando su
comportamiento observable actual.

El objetivo procede exclusivamente del índice maestro, que para esta capa fija
tres cosas y ninguna más:

1. priorizar **un dominio a la vez**;
2. agregar `response_model`, errores de dominio y pruebas HTTP o de integración
   **solo después** de caracterizar y **conservar** la respuesta existente;
3. **no crear abstracciones compartidas sin dos consumidores reales**.

La activación **no inspeccionó el código** y por eso **no afirma todavía** qué
endpoints, archivos, consultas, escrituras, cálculos, permisos o pruebas forman
este dominio. Esa determinación es trabajo de 7.0.

## Por qué este dominio es distinto de los cinco anteriores

**Es el primero que llega con persistencia en la capa HTTP.** La subcapa 1.4
registró que `app/routes/observaciones.py` **abría su propia conexión** dentro de
la función `obtener_observacion`, que ejecuta un `SELECT` y llama al resolver de
asignación académica. La capa 1 la migró a `get_cursor()`, pero **la consulta
sigue viviendo en la ruta**, no en un controlador.

Ninguno de los cinco dominios anteriores tuvo eso:

- en `dashboard`, `notas`, `ventas`, `asistencia` y `boletin` la persistencia
  estaba **toda** en el controlador;
- la 7.0 de `dashboard` registró como hallazgo que **una** consulta de permiso
  se hacía desde rutas, y lo trató como defecto;
- aquí no es un permiso: es **la lectura principal de un endpoint**.

**Consecuencia para 7.0**: el inventario tiene que contar SQL en **tres** sitios
—ruta, controlador y lo que aparezca— y decidir con evidencia si la consulta de
la ruta se mueve, y adónde. Esa decisión **no se toma en la activación**.

Dos diferencias más, registradas y sin verificar:

- **Colisión de nombres con `plan_de_clases`, un dominio en espera.** La capa 2
  inventarió `crear_observacion_plan`, `listar_observaciones_plan` y
  `marcar_observacion_vista` entre los once handlers de `plan_de_clases`. Son
  **observaciones de planes de clase**, no observaciones académicas. Es la misma
  trampa que tuvo `boletin`, pero al revés: allí el nombre estaba en un dominio
  **cerrado**, y aquí en uno **en espera**. **7.0 debe delimitarlo con evidencia
  antes de contar nada.**
- **Diferencia favorable frente a `boletin`**: la tabla `observaciones` **no
  estuvo entre las ocho averiadas** de `tenant_2005` que reparó la capa 3, y
  **no aparece** ni entre las 7 claves foráneas que apuntan a `asignaciones` ni
  entre las 9 que apuntan a `estudiantes` que inventarió la capa 6. Si eso se
  confirma, la tabla estaría **sin restricciones de integridad hacia sus dos
  padres naturales**, lo que es a la vez menos frágil ante un `DELETE` y menos
  protegido ante datos huérfanos. Es el supuesto 10.

## Perfil de riesgo esperado, **no verificado**

La capa 0 registró que el dominio **«crea o actualiza observación académica»**.
Si 7.0 lo confirma, **el dominio escribe** y su perfil de riesgo es el de la
capa 5, como `notas`, `ventas`, `asistencia` y `boletin`. La activación **no lo
da por cierto**: es el supuesto 2.

El «crea o actualiza» sugiere además un **`UPSERT`**, el mismo patrón que
`boletin` confirmó en su cabecera. Sugerir no es saber: 7.0 debe comprobarlo.

## Dependencias de capas anteriores

- **Capa 0**: el inventario de contratos incluye la fila «Observaciones», con su
  router, su prueba y sus status codes, incluido un **`422` por contenido
  vacío**. Es el punto de partida documental de 7.0.
- **Capa 1**: migró a `get_cursor()` la apertura de conexión que vivía en
  `app/routes/observaciones.py`, sustituyó un **import local** de
  `get_connection` y **creó** `tests/test_observaciones_ruta.py` porque la ruta
  no tenía cobertura.
- **Capa 2**: inventarió los once handlers de `plan_de_clases`, tres de ellos
  con «observacion» en el nombre. Sirve para separar los dos dominios.
- **Capa 6**: `observacion_controller` es uno de los nueve consumidores de
  `resolver_asignacion_academica_id_cursor`, **y `routes/observaciones.py` es un
  consumidor adicional**; `estudiantes_repository` lee `observaciones` en el
  bloque del expediente.
- Evidencia de que la capa anterior está cerrada: `07_BOLETIN.md` marca Estado
  **Cerrada** el 2026-08-21, con compuerta **exit 0 y 898 pruebas** y
  verificación manual ejecutada; el índice lo confirma y no marca ninguna otra
  capa activa.

## Lo que el programa cree saber de `observaciones`, y que 7.0 debe verificar

Aplica la lección 12 que dejó la capa 6 y que las cinco capas 7 confirmaron:
**un supuesto heredado se marca como no verificado y se comprueba en la subcapa
0**. De los siete de `dashboard` **uno resultó falso**; de los diez de `notas`
**uno incompleto**, y era el que fijaba la frontera; de los doce de `ventas`
**uno falso**; de los doce de `asistencia` **dos incompletos**; y de los trece de
`boletin` **uno incompleto, pero cinco describían código de otro dominio**.

**Esa última es la lección más reciente y la más relevante aquí**: un supuesto
puede ser cierto y estar **mal atribuido**. Con la colisión de nombres de
`plan_de_clases` encima, 7.0 debe comprobar no solo si cada supuesto es cierto,
sino **de qué dominio habla**.

Ninguno de los de abajo procede de haber leído el código de `observaciones`.
Todos son restos de lo que las capas 0, 1, 2, 3 y 6 observaron desde fuera. La
columna de origen dice de dónde sale cada uno.

**Los once quedaron resueltos en 7.0**, uno por uno y con evidencia. **Diez se
confirmaron y uno resultó incompleto.** **Ninguno resultó falso**, como en
`asistencia`.

**Y esta vez ninguno estaba mal atribuido**, a diferencia de `boletin`, donde
cinco de trece describían código de `notas`. La colisión con `plan_de_clases`
resultó ser **limpia**: dos routers distintos, dos tablas distintas, cero
solapamiento.

| # | Supuesto | Origen documental | Resultado en 7.0 |
|---:|---|---|---|
| 1 | El dominio vive en `app/routes/observaciones.py` y en un `observacion_controller` | Inventario de contratos de 0.0 (router) y subcapa 6.0 | **INCOMPLETO, y es el único.** Son **tres archivos**: el router (41 líneas), `app/controllers/observacion_controller.py` (43) y `app/schemas/observacion.py` (20). **No existe repositorio ni servicio.** Es la **tercera vez seguida** —tras `asistencia` y `boletin`— que el supuesto de frontera se queda corto **por el esquema**: conviene darlo por sabido y dejar de contarlo como sorpresa |
| 2 | **El dominio escribe**: «crea o actualiza observación académica» | Inventario de contratos de 0.0 | **CONFIRMADO, y el `UPSERT` que se sospechaba existe.** `guardar_observacion_controller` emite **una sola sentencia**: `INSERT … ON CONFLICT (estudiante_id, asignacion_id, periodo) DO UPDATE` sobre las tres dimensiones, en **una transacción propia** con `commit` y `rollback` explícitos. **Una sola tabla escrita.** Perfil de riesgo de la capa 5, confirmado |
| 3 | **La ruta ejecuta persistencia** | Subcapa 1.4 | **CONFIRMADO.** `obtener_observacion` resuelve la asignación académica y ejecuta el `SELECT` **dentro de la propia ruta**, en un `with get_cursor()`. Es **la diferencia que manda en esta capa** y ningún dominio anterior de la capa 7 la tuvo |
| 4 | **El resolver se consume desde DOS sitios del dominio** | Subcapa 6.0 | **CONFIRMADO.** Línea 28 de la ruta y línea 10 del controlador. Cada uno cuesta **1 consulta** sobre el cursor que ya existe: ninguno abre conexión propia |
| 5 | `require_estudiante_in_asignacion` tiene **dos puntos de llamada**, **ninguno en bucle** | Medición del N+1 en conexiones de `asistencia` | **CONFIRMADO y cuantificado.** Uno por entrada, líneas 14 y 25, **fuera de todo bucle**. El coste **no crece con nada**, pero el suelo es más alto que el de `boletin`: **2 conexiones como admin y 3 como profesor en las DOS entradas** |
| 6 | `200` con **dimensiones normalizadas**, `403` y **`422` con contenido vacío** | Inventario de contratos de 0.0 | **CONFIRMADO y por fin explicado.** Las **dimensiones** son `conductual`, `cognitivo` y `lenguaje`. **Normalizar** es `str(valor or "").strip()`, un `field_validator` del esquema. El **`422`** lo produce un `model_validator` que rechaza las tres vacías con «Escribe al menos una observación antes de guardar.». Es **el primer 422 propio de un dominio de la capa 7** |
| 7 | La ruta devuelve **`None`** sin observación guardada, y **los guards corren antes de tocar la base** | Subcapa 1.4 | **CONFIRMADO.** Ya lo fijaban las 4 pruebas de 1.4; 7.0 añade el **orden exacto** en el código, para que una extracción no lo invierta sin que nadie lo note |
| 8 | Pruebas heredadas en `test_observaciones_validaciones.py` y `test_observaciones_ruta.py`, **4** de este último | Inventario de 0.0 y subcapa 1.4 | **CONFIRMADO y cuantificado, sin quedarse corto por una vez.** Son **8 heredadas**: 4 y 4. **El hueco sí era real**: ninguna medía conteos de consultas ni de conexiones, ninguna fijaba la frontera, ninguna miraba la forma del `UPSERT` ni el camino de `rollback`, y ninguna dejaba guardias estructurales |
| 9 | `estudiantes_repository` **lee `observaciones`** | Subcapa 6.2 | **CONFIRMADO.** Una sola lectura, `leer_observaciones`, con `JOIN` a `asignaciones`, `materias` y `profesor` y `ORDER BY o.periodo DESC` |
| 10 | La tabla **no tiene** las claves foráneas que la capa 6 inventarió | Capas 3 y 6, **por ausencia** | **CONFIRMADO, y por la razón fuerte, no por la débil.** El DDL de `migrations/base/` demuestra que la tabla **no tiene ninguna clave foránea**: `estudiante_id` y `asignacion_id` son `integer` sueltos. No es que la capa 6 la omitiera: es que **no hay nada que listar**. Lo único que la tabla garantiza es `UNIQUE (estudiante_id, asignacion_id, periodo)`, que es justo lo que sostiene el `UPSERT` |
| 11 | **`plan_de_clases` tiene tres handlers con «observacion» en el nombre** que no son de este dominio | Subcapa 2.0 | **CONFIRMADO, y la frontera resultó limpia.** Son tres rutas bajo `/plan-de-clases` y `/admin/plan-de-clases`, **paths disjuntos** de las dos propias, y **escriben otra tabla**: `plan_de_clases_observaciones`. No hay ambigüedad que resolver, al contrario que en `boletin` |

## Alcance autorizado

- **Delimitar la frontera con `plan_de_clases` antes que ningún otro trabajo**, y
  registrarla con evidencia. Es el paso 1 de 7.0, como lo fue en `boletin`.
- Inventariar entradas HTTP, reglas, cálculos, consultas, escrituras, archivos,
  pruebas y consumidores **de observaciones** mediante búsquedas dirigidas,
  **contando el SQL de la ruta además del del controlador**.
- Caracterizar antes de extraer: rutas, métodos, payloads, status codes
  —incluido el `422`—, permisos, roles, tenant, ownership, orden, nulos, **el
  `None` de la observación ausente y las «dimensiones normalizadas»**,
  transacciones y errores.
- Separar progresivamente HTTP, reglas, servicios y persistencia siguiendo el
  patrón ya probado nueve veces, con pruebas de caracterización previas a cada
  extracción importante.
- Contar y comparar consultas **y conexiones** críticas antes y después,
  distinguiendo las que abren los **dos** guards de permiso de las del dominio.
- **Leer** `app/core/permissions.py`, `estudiantes_repository.py` y lo
  indispensable de `plan_de_clases` para clasificar la frontera y documentar el
  punto de decisión. **Leer no es mover**: modificarlos exige una orden
  explícita posterior a la evidencia de 7.0.
- Agregar `response_model`, errores de dominio y pruebas HTTP o de integración
  **solo después** de caracterizar y demostrando que la respuesta existente se
  conserva.
- Medir con `EXPLAIN ANALYZE` conforme al criterio corregido en la capa 4:
  `SELECT` en producción bajo transacción `READ ONLY` cerrada con `rollback`.
  Ninguna medición puede escribir.

## Fuera de alcance

- **Todos los demás dominios de la capa 7**: planilla, planeador anual, plan de
  clases, branding, profesores, super admin y cualquier otro. Esta capa es de un
  solo dominio. Se permite la lectura mínima indispensable para caracterizar un
  contrato que `observaciones` consuma o que consuma de `observaciones`, sin
  modificarlo. **`plan_de_clases` queda fuera aunque tres de sus handlers se
  llamen «observacion».**
- **`pagos`, `estudiantes`, `asignaciones`, `dashboard`, `notas`, `ventas`,
  `asistencia` y `boletin`, ya migrados.** Sus fronteras de persistencia están
  cerradas y sus pruebas de caracterización deben seguir pasando. **Mover
  cualquier sentencia fuera de `estudiantes_repository` no está autorizado por
  esta activación.**
- `app/services/asignacion_academica.py`, del que dependen nueve módulos: se lee
  si hace falta, **no se toca**.
- `app/core/permissions.py`. Es infraestructura compartida que las seis capas
  anteriores declararon expresamente fuera de alcance. **Incluye el N+1 en
  conexiones que dejó `asistencia`**, con plan de corrección ya diseñado y
  aplazado, y **la función `require_estudiante_in_asignacion` que este dominio
  llama dos veces**.
- Los hallazgos abiertos de las capas 5, 6 y 7: el **paso 2 de la clave de
  idempotencia** de `POST /pagos`, la **ausencia de lock** en asignaciones, los
  **diez de dashboard**, **doce de notas**, **once de ventas**, **ocho de
  asistencia** y **diez de boletin** —empezando por el emparejamiento por
  posición—. Son **cincuenta y uno**. **No entran por inferencia.**
- El trabajo registrado en `PROMPT_CONTINUACION.md` bajo «trabajo fuera del
  alcance de cualquier capa activa».
- Cambiar rutas, payloads, status codes, permisos, roles, ownership, reglas de
  cálculo, normalización de dimensiones, orden o semántica transaccional.
- Cambiar PostgreSQL, `psycopg2`, el modelo de schemas tenant, el pool, los
  timeouts, el limitador de concurrencia, el ORM, el driver o el almacenamiento
  de archivos.
- Migraciones reales, DDL, DML, deploy, commit o push.

## Invariantes

- Métodos, paths, status codes y forma exacta de las respuestas permanecen
  idénticos, incluidos el **orden**, los **nulos** y el **`None` que devuelve la
  ruta cuando no hay observación guardada**.
- **El `422` por contenido vacío se conserva.** Es un status code que ningún
  dominio migrado tenía, y perderlo cambiaría el contrato del frontend sin que
  ninguna prueba de los otros dominios lo notara.
- Permisos, roles, ownership y aislamiento entre tenants se conservan sin
  excepción, **incluido que los guards corran antes de abrir cursor**: 1.4 fijó
  por prueba que un rechazo no ejecuta consulta.
- Los límites de transacción se conservan: qué se confirma junto, qué se
  revierte junto y quién es dueño de `commit`, `rollback`, cursor y conexión,
  conforme a la capa 1.
- Ninguna operación DB síncrona vuelve al event loop ni se altera el limitador
  compartido sin medir de nuevo su capacidad.
- Los contratos de los dominios ya migrados que leen esta tabla siguen pasando
  su caracterización: el expediente de `estudiantes_repository`.
- El SQL de dominio se conserva hasta que una subcapa autorice, con
  caracterización previa, un cambio concreto.

## Línea base registrada en 7.0

| Comprobación | Comando | Resultado |
|---|---|---|
| Compuerta heredada, **antes de tocar nada** | `.\venv\Scripts\python.exe scripts\verify.py` | **898 pruebas, exit 0.** Coincide exactamente con lo registrado al cerrar `boletin`: **no había deriva** |
| Pruebas específicas nuevas | `.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_observaciones_caracterizacion.py` | **25 pasaron** en 0,59 s |
| Suite global | `.\venv\Scripts\python.exe scripts\verify.py` | **923 pasaron**, 5 warnings heredadas, exit 0 |
| Ruff | Ejecutado por la compuerta global y sobre la prueba nueva | **Correcto** |
| Dependencias | Ejecutado por la compuerta global | **Íntegras** |

La suite pasó de **898 a 923** con la caracterización de 7.0.

## Inventario y contratos fijados en 7.0

**El dominio son tres archivos y 104 líneas**, y es **el que menos SQL tiene de
todos los que ha migrado el programa**: 2 sentencias, frente a las 3 de
`asistencia`, que era el récord anterior.

| Archivo | Líneas | SQL inline |
|---|---:|---:|
| `app/routes/observaciones.py` | 41 | **1** |
| `app/controllers/observacion_controller.py` | 43 | **1** |
| `app/schemas/observacion.py` | 20 | 0 |

**Dos entradas HTTP con un único modelo de permiso.** Es el **segundo dominio de
la capa 7 con permisos uniformes**, después de `ventas`:

| Método | Path | Permisos | Destino |
|---|---|---|---|
| POST | `/observaciones` | `get_current_user` + `require_asignacion_access` + `require_estudiante_in_asignacion` | `guardar_observacion_controller` |
| GET | `/observaciones/{estudiante_id}/{asignacion_id}/{periodo}` | los mismos tres | **la propia ruta** |

### Frontera, decidida con evidencia

| Vive en | Rutas | Tabla |
|---|---|---|
| **`observaciones`**, este dominio | `POST /observaciones`, `GET /observaciones/{…}/{…}/{…}` | `observaciones` |
| **`plan_de_clases`**, en espera | `POST /admin/plan-de-clases/{plan_id}/observaciones`, `GET /plan-de-clases/{plan_id}/observaciones`, `PATCH /plan-de-clases/{plan_id}/observaciones/{observacion_id}/vista` | `plan_de_clases_observaciones` |

Los conjuntos de paths son **disjuntos** y las tablas son **distintas**. La
frontera **queda donde está** y `plan_de_clases` no se toca.

### Propiedad transaccional y los dos idiomas

`guardar_observacion_controller` es la **única escritura**. Abre con
`get_connection()`, es dueño de `commit` y `rollback`, cierra cursor y conexión
en `finally` y **propaga la excepción** tras revertir. La lectura, en cambio,
usa `with get_cursor()` **dentro de la ruta**. **Dos idiomas conviviendo**, la
misma herencia que tuvo `asistencia`, y aquí además repartidos entre dos capas
distintas.

## Línea base de consultas y conexiones

Medida herméticamente con dobles y **fijada por aserción**. Las consultas
excluyen los dos round-trips que la apertura de conexión emite siempre.

| Camino | Consultas | Conexiones (admin) | Conexiones (profesor) |
|---|---:|---:|---:|
| `POST /observaciones` | **2** — resolver + `UPSERT` | **2** | **3** |
| `GET /observaciones/…` | **2** — resolver + `SELECT` | **2** | **3** |

**Ningún camino tiene N+1**, ni en consultas ni en conexiones. Los dos guards se
llaman **una vez cada uno y fuera de todo bucle**; `require_asignacion_access`
**no abre conexión** siendo admin, porque retorna antes.

El suelo es **más alto que el de `boletin`** —que gastaba 1 conexión de permisos
en tres de sus cuatro entradas— porque aquí **las dos entradas** pagan los dos
guards. No es un defecto: es el precio de comprobar la pertenencia del
estudiante también en la lectura, que `boletin` no hace.

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 7.0 | Frontera con `plan_de_clases`, inventario en ruta y controlador, contratos, caracterización y línea base de consultas y conexiones | **Cerrada** el 2026-08-21 |
| 7.1 | Extraer las 2 sentencias a `observaciones_repository` sin cambiar SQL, conteos ni ciclo de vida | **Cerrada** el 2026-08-21 |
| 7.2 | Punto de decisión: `response_model`, errores de dominio y los nueve hallazgos | **Sin decidir**: es un punto de decisión, no una subcapa pendiente |

El desglose se deja deliberadamente **sin decidir** hasta tener la evidencia del
inventario, igual que hicieron la capa 6 y las cinco capas 7 anteriores. Las
subcapas innecesarias se marcarán `No aplica` con explicación. **Nunca se
ejecutan dos subcapas en el mismo turno.**

## Hallazgos de 7.0, registrados y sin corregir

Son **nueve**. Ninguno se corrige desde esta capa; corregir cualquiera exige una
orden explícita. Van ordenados por gravedad.

> **AUDITADOS UNO A UNO EL 2026-08-25, por orden explícita del usuario.** Se
> comprobaron contra el código, el esquema y peticiones reales, después de que
> la campaña de `dashboard` demostrara que **un hallazgo registrado puede estar
> mal diagnosticado**: allí dos de diez lo estaban.
>
> **Resultado: ocho de los nueve se sostienen y uno quedó obsoleto.** El
> veredicto de cada uno va marcado en su propio punto. Es una tasa mucho mejor
> que la de `dashboard`, y la diferencia tiene una causa identificable: la 7.0 de
> `observaciones` verificó sus supuestos con pruebas, y su propia bitácora ya
> registraba que **ningún supuesto quedó mal atribuido**.
>
> El único obsoleto es el **3**, y **no por un error de 7.0**: era cierto cuando
> se escribió y **lo corrigió la propia 7.1** al mover el SQL al repositorio. Lo
> que falla es que siga listado como «sin corregir». Es el mismo desfase que
> `dashboard` tenía entre sus hallazgos y sus correcciones.

1. **[CONFIRMADO, y se queda corto]** **La tabla no tiene ninguna clave foránea.** `estudiante_id` y
   `asignacion_id` son `integer` sueltos: nada en la base impide una observación
   huérfana, ni apuntando a un estudiante inexistente, ni sobreviviendo al
   borrado de una asignación. **La integridad depende enteramente del código de
   aplicación**, y ese código no la comprueba: el `UPSERT` escribe lo que le
   den. Es el hallazgo más grave y el único de todo el programa sobre una tabla
   sin restricciones hacia sus dos padres naturales.
2. **[CONFIRMADO literalmente]** **Las tres dimensiones son `text` sin límite y
   la tabla no tiene ningún `CHECK`.** Contrasta con `plan_de_clases_observaciones`, la tabla del dominio
   vecino, que **sí** acota su texto entre 1 y 3000 caracteres. El dominio
   académico está **menos protegido que el de planes de clase**, y nada impide
   almacenar una observación de megabytes.
3. **[OBSOLETO desde 7.1]** **La lectura vive en la capa HTTP.** El `SELECT` y el resolver están en
   `obtener_observacion`, dentro del router. Es el único caso del programa y la
   razón por la que un inventario que solo mirara el controlador contaría **1 de
   2** sentencias.
4. **[CONFIRMADO con una respuesta real]** **El `422` depende del esquema y es
   frágil.** Lo produce el `model_validator`
   de `ObservacionCreate`, no el dominio. Si esa validación se moviera al
   controlador en una extracción posterior, el status **pasaría de 422 a 500**
   sin que ninguna prueba heredada lo notara. Ahora sí hay una que lo fija.
5. **[CONFIRMADO exactamente]** **La normalización convierte cualquier valor
   falsy en cadena vacía.**
   `str(valor or "").strip()` no distingue tipos: un **`0` numérico llega como
   `""`, no como `"0"`**, y lo mismo `False` y las listas vacías. Un valor
   truthy sí conserva su representación: `7` llega como `"7"`.
6. **[CORREGIDO LOCALMENTE EL 2026-08-27]** **El `UPSERT` no comprobaba
   que la asignación siguiera activa.** Es el mismo
   hallazgo que dejaron abiertos `dashboard`, `notas` y `boletin`.
7. **[CORREGIDO LOCALMENTE EL 2026-08-27]** **Ninguna de las dos entradas
   registraba nada ante un fallo.** No hay
   `try/except` ni `logger` en el router: una excepción sube y FastAPI la
   convierte en un 500 genérico. **No se filtra el texto de la excepción**, que
   es mejor que `dashboard` y `asistencia`, pero **tampoco queda traza**, que es
   peor que `boletin`.
8. **[CONFIRMADO]** **`periodo` es un `int` sin cota**, ni en el esquema ni en la base: nada
   impide un periodo 99 ni negativo.
9. **[CONFIRMADO]** **Defensa duplicada en el controlador.** Usa
   `data.get("conductual", "")` para las tres dimensiones, pero el esquema ya
   garantiza que las tres claves existen con default `""`. El `.get` solo
   actuaría si alguien llamara al controlador **sin pasar por la ruta**, porque
   recibe un `dict` y no el modelo.

### Lo que 7.0 buscó expresamente y **no** encontró

- **Ningún N+1**, ni en consultas ni en conexiones. Es el segundo dominio
  seguido que sale limpio en esto, tras `boletin`.
- **Ninguna fuga de conexión**: la escritura cierra en `finally` y la lectura
  usa el gestor de contexto de la capa 1.
- **Ninguna colisión de paths ni de tablas** con `plan_de_clases`. La trampa de
  frontera que la activación anticipó **resultó limpia**, al contrario que la de
  `boletin`.
- **Ninguna filtración del texto de la excepción** al cliente.
- **Ningún f-string en SQL** ni interpolación de parámetros.
- **Ningún supuesto mal atribuido**, a diferencia de `boletin`.

## Subcapa 7.0 — trabajo exacto, ejecutado y cerrado

1. **Delimitar la frontera con `plan_de_clases` antes que nada.** Listar las
   rutas declaradas por `app/routes/observaciones.py` y las de
   `plan_de_clases` que llevan «observacion» en el nombre. Registrar cuáles
   pertenecen a cada dominio y comprobar que **no hay colisión de paths**.
   Registrar el borde **con evidencia**, no por nombre de archivo ni de función.
2. Inventariar entradas HTTP del dominio: método, path, permisos, payload de
   entrada, forma exacta de la respuesta y status codes, **incluido el `422`**.
3. Inventariar archivos y **contar sentencias SQL inline por archivo, la ruta
   incluida**. Es el único dominio de la capa 7 donde la ruta puede aportar SQL.
4. Determinar **si el dominio escribe**, qué tablas y con qué semántica
   transaccional; si hay `UPSERT`; quién es dueño de `commit`, `rollback`,
   cursor y conexión en **cada** camino.
5. Averiguar qué son las **«dimensiones normalizadas»** del contrato de 0.0 y
   fijarlas por prueba.
6. Fijar por prueba el **`None`** de la observación ausente y que **los guards
   corren antes de tocar la base**.
7. Medir **línea base de consultas y de conexiones** por camino, con dobles
   herméticos, separando las de los **dos** `require_estudiante_in_asignacion`
   de las del dominio.
8. Resolver **los once supuestos** uno por uno, con evidencia, registrando cuál
   se confirma, cuál es incompleto, cuál es falso y **cuál habla de otro
   dominio**.
9. Escribir la caracterización en `tests/test_observaciones_caracterizacion.py`,
   un archivo nuevo. **No se reescriben ni se retiran** las pruebas heredadas.
10. Registrar hallazgos **sin corregir ninguno**.
11. Archivos permitidos: **un solo archivo de prueba nuevo** y esta bitácora. El
    diff de 7.0 **no debe modificar ningún archivo rastreado de producto**,
    igual que los de 5.0, 6.0 y las cinco 7.0 anteriores.
12. Comandos de verificación: la compuerta global antes y después, las pruebas
    específicas, Ruff sobre el archivo nuevo y `git diff --check`.
13. **Punto exacto donde debe detenerse**: al cerrar 7.0 con su registro
    escrito. **No iniciar 7.1 en el mismo turno.**

## Criterios de cierre de la subcapa 7.0

- La frontera con `plan_de_clases` queda registrada con evidencia.
- Los once supuestos quedan resueltos uno por uno, con su atribución de dominio.
- Existe caracterización ejecutable que fija contratos, status codes y línea
  base de consultas y conexiones, **contando la ruta**.
- Compuerta global correcta y Ruff correcto.
- Diff exclusivo de la subcapa y sin duplicación heredada.
- Bitácora actualizada con archivos, comandos, resultados, decisiones y riesgos.

## Criterios de cierre de la capa

- Todas las subcapas necesarias están cerradas.
- Compuerta global correcta.
- Contratos conservados o cambios explícitamente aprobados.
- Staging, rollback y verificación manual documentados. **Atención**: el commit
  base **ya está publicado y desplegado**, así que si esta capa llega a
  publicarse su rollback **no será local**.
- Siguiente capa autorizada por el usuario.

## Decisiones

- **Decisión de la activación: el dominio es `observaciones` y solo ese.**
  Motivo: el índice ordena «uno a la vez». Alternativa descartada: activarlo
  junto a `plan_de_clases` por compartir el nombre; se descarta porque son
  dominios distintos y ninguna capa del programa ha activado dos a la vez.
- **Decisión de la activación: continuar aceptando las verificaciones heredadas
  como pendientes.** Motivo: el usuario ordenó activar tras leer la lista de
  pendientes en el informe de cierre de `boletin`. **Ninguna se marca como
  cumplida** y su riesgo queda registrado abajo.
- **Decisión aplazada a 7.0: dónde vive la consulta de la ruta.** No se toma por
  inferencia en la activación. Que 1.4 la dejara en `app/routes/observaciones.py`
  no significa que deba quedarse ni que deba moverse.

## Riesgos

- **SQL en la capa HTTP.** Evidencia: subcapa 1.4. Mitigación: contarlo en 7.0 y
  decidir con evidencia, no por analogía con los cinco dominios anteriores.
  Responsable de validarlo: 7.0.
- **Colisión de nombres con `plan_de_clases`.** Evidencia: inventario de la capa
  2. Mitigación: delimitar la frontera como paso 1. Responsable: 7.0.
- **Un supuesto puede estar bien y mal atribuido.** Evidencia: en `boletin`,
  cinco de trece describían código de `notas`. Mitigación: cada supuesto se
  resuelve indicando **de qué dominio habla**. Responsable: 7.0.
- **El supuesto 10 es una inferencia por ausencia** y no debe leerse como un
  hecho en ninguna dirección. Responsable: 7.0.
- **El `422` es un contrato que ninguna prueba ajena protege.** Mitigación:
  fijarlo por prueba en 7.0 antes de tocar nada. Responsable: 7.0.
- **Consumidor ajeno ya migrado.** Evidencia: `estudiantes_repository` lee esta
  tabla. Mitigación: ejecutar siempre la compuerta **completa**. Responsable:
  7.0 y cada subcapa posterior.
- **El commit base ya está en producción.** Evidencia: `git ls-remote` del
  2026-08-21. Mitigación: documentar el rollback como no local desde el primer
  día si la capa se publica. Responsable: el cierre de la capa.
- **Verificaciones heredadas pendientes**, aceptadas por decisión explícita:
  valor operativo final de `DB_STATEMENT_TIMEOUT_MS` de la capa 1; ausencia de
  evidencia de GitHub Actions desde la capa 0; los pasos no confirmados de los
  guiones de `ventas`, `asistencia` y `boletin`; y la **credencial privilegiada
  de la capa 4 sin rotar**. Ninguna se marca como cumplida.

## Registro de ejecución

### 2026-08-21 — activación de la capa para `observaciones`

- Modo de acceso: mismo checkout local; Git validado directamente en
  `C:\Users\David\Documents\sistema_escolar_api`. No se usó GitHub para inferir
  el estado local; el remoto se comprobó además contra el remoto real.
- Autorización: orden explícita del usuario en este turno, **nombrando el
  dominio**: «activa el dominio observaciones». **No se pegó el bloque
  preparado** de `PROMPT_CONTINUACION.md`; la autorización llegó en
  conversación. La condición que ese bloque exige —nombrar el dominio
  explícitamente y no deducirlo— **se cumplió**.
- **Verificaciones heredadas**: el informe de cierre de `boletin` las listó por
  escrito en el turno inmediatamente anterior y el usuario ordenó activar sin
  cerrarlas. Quedan registradas con su riesgo y **ninguna se marca como
  cumplida**.
- Rama acordada: `main`.
- Estado antes de escribir: árbol limpio, verificado con
  `git status --porcelain=v1` con salida vacía; `HEAD` real
  `fd3f93a2ad97daa0a34081eb2f95504dd1a9e4df`, comprobado y no recordado.
- Continuidad: el base de la capa 7 para `boletin`,
  `8e61170f32a6d6a23ca23f9ead89d17bc209e7b6`, es ancestro de `HEAD`. Sus
  **cuatro** commits posteriores forman una historia lineal y **todos quedan
  explicados** en `07_BOLETIN.md`: la activación `0f351c8`, el cierre de 7.0
  `100de58`, la extracción de 7.1 `865a062` y el cierre `fd3f93a`.
- **Estado remoto comprobado, no supuesto**: `origin/main` está en
  `fd3f93a2ad97daa0a34081eb2f95504dd1a9e4df`, el mismo commit que `HEAD`,
  confirmado contra el remoto real con `git ls-remote origin main`. El commit
  base de esta capa está por tanto **publicado y desplegado**. **No se consultó
  ni se atribuye ningún run de GitHub Actions**; esa evidencia sigue sin
  obtenerse desde la capa 0.
- **Desfase documental detectado y NO corregido.** `07_BOLETIN.md` y el índice
  declaran la capa 7 de `boletin` **«NO publicada»** y su rollback «puramente
  local». **Ya no es cierto**: producción corre ese código desde el push que
  dejó `origin/main` en `fd3f93a`. Es el **cuarto desfase consecutivo** del
  mismo tipo, tras `notas`, `ventas` y `asistencia`, y el segundo que el propio
  índice había anticipado por escrito. **La autorización de este turno cubría
  activar `observaciones`, no corregir el estado de publicación de `boletin`**,
  así que queda anotado y sin tocar: exige una orden propia. Esta bitácora **sí**
  registra el hecho comprobado, porque su commit base es ese mismo commit y
  describirlo como no publicado sería falso.
- **Segundo residuo documental, detectado y NO corregido**: el índice conserva,
  después de las líneas que cierran `ventas`, un párrafo que describe su punto de
  decisión como **abierto** y su verificación manual como **pendiente**, cuando
  las dos cosas se resolvieron. Ya estaba anotado al activar `asistencia` y al
  activar `boletin`, y sigue sin tocarse.
- Archivos creados o modificados: esta bitácora y
  `docs/modularizacion/README.md`.
- Código de producto, pruebas, consultas, configuración, dependencias y workflow
  inspeccionados o modificados: **ninguno**. **No se inspeccionó código de
  `observaciones`** ni de ningún otro dominio, ni siquiera el listado de nombres
  de archivo. Los once supuestos de la tabla de arriba salen **exclusivamente de
  la documentación del programa** —`00_LINEA_BASE_CALIDAD.md`,
  `01_FUNDACION_BASE_DATOS.md`, `02_CONCURRENCIA.md`,
  `06_ASIGNACIONES_ESTUDIANTES.md` y el índice—, y cada uno lleva su origen
  anotado para que 7.0 pueda contrastarlo.
- Pruebas, migraciones, conexiones a PostgreSQL, acceso a producción, commit,
  push y deploy: **ninguno**.
- Comandos de precondición: `git branch --show-current`,
  `git status --porcelain=v1`, `git rev-parse HEAD`, `git log --oneline`,
  `git ls-remote origin main`; todos con resultado coherente con la activación.
- Estado al cerrar el turno de activación: capa 7 **activa** para el dominio
  `observaciones`; **7.0 pendiente y no iniciada**.
- Siguiente acción exacta: ejecutar únicamente **7.0** conforme al trabajo
  exacto de arriba y detenerse antes de 7.1. *(Ejecutada en el turno siguiente;
  ver el cierre de 7.0 más abajo.)*

### 2026-08-21 — cierre de 7.0

- Commit observado: `dac6425`, el de activación, que el usuario creó entre los
  dos turnos. Árbol limpio, verificado con `git status --porcelain=v1` con
  salida vacía. El commit base `fd3f93a` sigue siendo el registrado y `dac6425`
  es su único descendiente, explicado en esta bitácora.
- Estado remoto: `origin/main` sigue en `fd3f93a`. **La activación y 7.0 están
  sin publicar.**
- Archivos modificados: **`tests/test_observaciones_caracterizacion.py`,
  nuevo**, y esta bitácora. **Ningún archivo rastreado de producto fue
  modificado**, verificado con `git status --porcelain=v1`, cuya única entrada
  de código es `?? tests/test_observaciones_caracterizacion.py`.
- Archivos inspeccionados sin modificar: `app/routes/observaciones.py`,
  `app/controllers/observacion_controller.py`, `app/schemas/observacion.py`,
  `tests/test_observaciones_ruta.py`, `tests/test_observaciones_validaciones.py`
  y, **solo para delimitar la frontera y clasificar consumidores**,
  `app/routes/plan_de_clases.py`, `app/core/permissions.py`,
  `app/repositories/estudiantes_repository.py` y
  `migrations/base/20260813_esquema_base_tenant.sql`. **Leer no fue mover**:
  ninguno se tocó.
- Pruebas antes: **8 heredadas**, 4 en `test_observaciones_ruta.py` y 4 en
  `test_observaciones_validaciones.py`. **Ninguna** medía conteos de consultas o
  conexiones, fijaba la frontera, miraba la forma del `UPSERT`, cubría el camino
  de `rollback` ni dejaba guardias estructurales.
- Cambio realizado: **solo caracterización**. 25 pruebas nuevas que fijan la
  frontera con `plan_de_clases`, las dos entradas con su único modelo de
  permiso, el `422` y su origen en el esquema, el `None` de la lectura y el
  orden de los guards, la semántica transaccional completa incluida la
  reversión, la normalización de las tres dimensiones con su rareza de los
  valores falsy, la línea base de consultas y de conexiones, **el DDL de la
  tabla y sus ausencias**, y **seis guardias estructurales**: número de
  archivos, ausencia de repositorio y servicio, reparto 1+1 del SQL entre ruta y
  controlador, los dos idiomas de conexión, el resolver en los dos lados y la
  lectura ajena de `estudiantes_repository`.
- Comandos y resultados:
  - `.\venv\Scripts\python.exe scripts\verify.py` **antes**: **898 pruebas,
    exit 0**, Ruff correcto, `pip check` íntegro. **Sin deriva** respecto al
    cierre de `boletin`.
  - `.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_observaciones_caracterizacion.py`:
    **25 pasaron** en 0,59 s, **a la primera**.
  - Las **8 heredadas** ejecutadas junto a las nuevas: **33 pasaron**, sin tocar
    ninguna aserción.
  - `.\venv\Scripts\python.exe -m ruff check tests\test_observaciones_caracterizacion.py`:
    **correcto**.
  - `.\venv\Scripts\python.exe scripts\verify.py` **después**: **923 pruebas,
    exit 0**, Ruff correcto, `pip check` íntegro.
  - `git diff --check`: **sin problemas**.
- **Ninguna prueba falló durante 7.0**, ni propia ni ajena. Es la primera 7.0 de
  la capa 7 que no produce ninguna señal roja; en `boletin` hubo tres fallos de
  andamiaje. Se afinó **un doble** después de que pasara, para que el resolver
  recibiera un id plausible en vez de reutilizar la fila del `SELECT`: **no se
  relajó ninguna aserción**, se añadió una sobre los parámetros.
- Decisiones:
  1. **La frontera se queda donde está.** Las tres rutas de observaciones de
     `plan_de_clases` no se tocan: son otro dominio, otro router y **otra
     tabla**. Motivo: `plan_de_clases` sigue en espera y tendrá su propia
     bitácora.
  2. **Los dos idiomas de conexión se conservan.** Unificarlos cambiaría los
     conteos que 7.0 acaba de fijar por aserción, y no está autorizado.
  3. **No se corrige la ausencia de claves foráneas**, pese a ser el hallazgo
     más grave. Motivo: exigiría una migración real sobre la base, que esta capa
     tiene expresamente fuera de alcance, y una decisión sobre qué hacer con las
     filas huérfanas que ya existan.
- Riesgos: el hallazgo 4 —el `422` que depende del esquema— **es un riesgo para
  7.1**. Si la extracción tocara la validación, el status cambiaría en silencio.
  Ahora hay una prueba que lo fija, y es la que debe protegerlo.
- Siguiente acción exacta: **esperar la definición y la orden de 7.1.** No se
  inició ni se decidió su alcance. *(Decidida y ejecutada en el turno siguiente;
  ver el cierre de 7.1 más abajo.)*

### 2026-08-21 — cierre de 7.1

- **La decisión de alcance la tomó el usuario, no el asistente.** Se le
  ofrecieron **tres** salidas para la sentencia que vivía en la ruta —bajarla
  antes a un controlador nuevo, llevar las dos directas al repositorio, o
  extraer solo el `UPSERT` dejando la de la ruta donde estaba— y eligió
  **llevar las dos al repositorio conservando cada llamador su propia capa**.
  Una instrucción genérica de continuar **no** habría bastado para fijarlo, y
  por eso se preguntó antes de tocar nada.
- Commit observado: `eaa8115`, el de 7.0, que el usuario creó entre los turnos.
  Árbol limpio, verificado con `git status --porcelain=v1` con salida vacía.
- Estado remoto: `origin/main` sigue en `fd3f93a`. **La activación, 7.0 y 7.1
  están sin publicar.**
- **La comparación byte a byte SÍ se pudo sostener aquí.** Se comprobó **antes**
  de mover nada que ni la ruta ni el controlador tenían **una sola línea con
  espacios finales**, así que no hizo falta la limpieza autorizada que necesitó
  `boletin` ni su cadena de dos pasos. Vuelve el criterio estricto de las cuatro
  7.1 anteriores a `boletin`.
- Resultado: nace `app/repositories/observaciones_repository.py`, **el undécimo
  repositorio del proyecto**, con **2 funciones** que reciben el cursor. La ruta
  pasó de **41 a 38 líneas** y de 1 sentencia inline a **0**; el controlador, de
  **43 a 30** y de 1 a **0**. **La capa HTTP se queda sin SQL**, que es lo que
  resuelve el hallazgo 3.
- **Los dos llamadores son de capas distintas, y se conservó así.**
  `leer_observacion` la llama la **ruta** desde su `with get_cursor()`;
  `guardar_observacion`, el **controlador** desde su `get_connection()`. **No se
  unificaron los idiomas ni se movió la propiedad del cursor**: hacerlo habría
  cambiado los conteos de conexiones que 7.0 fijó por aserción.
- **Comparador AST contra el commit base**: **2 literales antes y 2 después**,
  **2 de 2 idénticos byte a byte**, sin una sola autorización de cambio de
  texto. Reparto nuevo: ruta **0**, controlador **0**, repositorio **2**.
- **Equivalencia en tiempo de ejecución, los dos caminos.** Se ejecutó la ruta y
  el controlador del commit base y los de hoy contra dobles idénticos,
  comparando la secuencia de **`(SQL normalizado, parámetros)`** —con los guards
  instrumentados dentro de la secuencia, para fijar también su **orden**—, el
  **valor devuelto**, las **conexiones** y los **cierres**:

  | Camino | Pasos | Conexiones | `commit` | Resultado |
  |---|---:|---:|---:|---|
  | `GET` con observación guardada | 4 | 1 | 0 | **idéntico** |
  | `GET` sin observación —devuelve `None`— | 4 | 1 | 0 | **idéntico** |
  | `POST` `UPSERT` | 2 | 1 | 1 | **idéntico** |

- **Las siete guardias que fallaron, que era la señal esperada.** Cuatro son
  ajenas y confirman el patrón que `asistencia` dejó anotado —**cada migración
  añade una enumeración de repositorios**—: las de `asistencia`, `dashboard`,
  `notas` y `ventas`. Se les añadió `observaciones_repository` y, en la de
  `asistencia`, el conteo pasó de **10 a 11**. Las otras tres son **propias de
  7.0**: la ausencia de repositorio, el reparto 1+1 del SQL y la ubicación del
  `UPSERT`. Las tres se sustituyeron por sus versiones positivas.
- **Una guardia nueva falló por un defecto propio, y la lección ya estaba
  escrita.** `test_el_repositorio_no_es_dueno_de_ningun_recurso` buscaba
  `get_connection` y `get_cursor` en el texto del módulo, y **el docstring del
  repositorio los nombra justamente para explicar que no los usa**. Es la
  **lección 13 de la capa 6** —excluir docstrings antes de comparar— y se aplicó
  añadiendo `_codigo_sin_docstrings`. **La regla que fija no cambió.**
- Archivos modificados: `app/routes/observaciones.py`,
  `app/controllers/observacion_controller.py`,
  `app/repositories/observaciones_repository.py` (nuevo),
  `tests/test_observaciones_caracterizacion.py` y **una línea** en cada uno de
  `tests/test_asistencia_caracterizacion.py`,
  `tests/test_dashboard_caracterizacion.py`,
  `tests/test_notas_caracterizacion.py` y
  `tests/test_ventas_caracterizacion.py`.
- **Lo que 7.1 no tocó, y estaba prohibido tocar**: `app/schemas/observacion.py`
  —y con él la normalización y el **`422`**—, `app/core/permissions.py`, el
  resolver de asignación académica, `estudiantes_repository`, `plan_de_clases` y
  **los nueve hallazgos de 7.0**, empezando por la ausencia de claves foráneas.
  Las **8 pruebas heredadas no se tocaron** y siguen pasando.
- Comandos y resultados:
  - Comparador AST base vs. hoy: **2 de 2 idénticos byte a byte**.
  - Equivalencia en ejecución de los dos caminos, tres escenarios:
    **idéntica** en SQL, parámetros, orden de guards, retorno, conexiones y
    cierres.
  - `.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_observaciones_caracterizacion.py tests\test_observaciones_ruta.py tests\test_observaciones_validaciones.py`:
    **35 pasaron**.
  - `.\venv\Scripts\python.exe -m ruff check` sobre los cuatro archivos:
    **correcto**.
  - `.\venv\Scripts\python.exe scripts\verify.py`: **925 pruebas, exit 0**,
    Ruff correcto, `pip check` íntegro.
  - `git diff --check`: **sin problemas**.
- Decisiones:
  1. **El repositorio se llama `observaciones_repository`**, en plural, como el
     router y como la tabla, aunque el controlador y el esquema vayan en
     singular. Motivo: coincide con la tabla que gobierna y con
     `asignaciones_repository` y `estudiantes_repository`.
  2. **No se unifican los dos idiomas de conexión.** Motivo: cambiaría los
     conteos que 7.0 fijó y no está autorizado. Alternativa descartada: bajar la
     lectura a un controlador nuevo, que el usuario descartó expresamente al
     elegir entre las tres salidas.
  3. **La normalización y el `422` se quedan en el esquema.** Traerlos al
     repositorio convertiría el 422 en un 500. Es el hallazgo 4 y hay una prueba
     que lo protege.
- Riesgos: ninguno nuevo. Los **nueve hallazgos** siguen vivos y sin corregir.
- Siguiente acción exacta: **esperar la decisión del usuario** sobre el punto de
  decisión y la verificación manual. Una instrucción genérica de continuar no la
  sustituye.

### 2026-08-21 — verificación manual y cierre de la capa

- Commit observado: `4bceabb`, el de 7.1. Árbol limpio, verificado con
  `git status --porcelain=v1` con salida vacía. Los tres commits posteriores al
  base —`dac6425` la activación, `eaa8115` la 7.0 y `4bceabb` la 7.1— están
  explicados en esta bitácora.
- **Estado remoto comprobado, no supuesto**: `origin/main` sigue en
  `fd3f93a2ad97daa0a34081eb2f95504dd1a9e4df`, el commit base, confirmado contra
  el remoto real con `git ls-remote origin main`. **La capa no está publicada.**
- Compuerta de cierre: `.\venv\Scripts\python.exe scripts\verify.py` →
  **925 pruebas, exit 0**, Ruff correcto, `pip check` íntegro.
- `git diff --check`: sin problemas. Sin cambios de producto en este turno: el
  cierre toca **solo documentación**.
- **Verificación manual: hecha por el usuario, con resultado correcto**, el
  2026-08-21, en local. **Registrada sin inflarla**: el usuario la reportó **de
  forma global y con una reserva explícita** —«ya comprobé, y aparentemente está
  bien»—. **No consta ningún paso del guion confirmado uno por uno**, porque no
  se preguntó punto por punto antes de cerrar. **Es el segundo dominio
  consecutivo en el tramo más débil**, tras `boletin`, y con la misma reserva
  literal. `notas` sigue siendo la más fuerte; `asistencia` dejó constancia de
  un paso de cuatro; `ventas`, `boletin` y ahora `observaciones`, de ninguno.
- **Lo que más habría valido confirmar, y no consta**: guardar una observación
  **sobre una que ya existía**, para ver el `UPSERT` sustituyendo las tres
  dimensiones; y **enviar las tres vacías** para comprobar que sigue saliendo un
  **422** y no un 500. El segundo importa especialmente porque **ese status lo
  sostiene solo el esquema** —el hallazgo 4— y es lo que una extracción
  descuidada habría roto en silencio.
- **Atenuante registrado, que no sustituye a la verificación**: 7.1 demostró la
  equivalencia **en ejecución** de los dos caminos y tres escenarios —lectura
  con fila, lectura sin fila y `UPSERT`— contra el código del commit base,
  incluyendo el **orden de los guards** dentro de la secuencia. Es la evidencia
  automática más completa de las seis 7.1 del programa, pero **no observa la
  base de datos real ni el frontend**, así que el hueco del guion sigue siendo
  un hueco.
- Decisiones: cerrar la capa sin abrir 7.2, registrada abajo.
- Riesgos: los nueve hallazgos de 7.0 siguen vivos y sin corregir.
- Siguiente acción exacta: **ninguna dentro de esta capa**. Queda cerrada. El
  siguiente dominio de la capa 7 **no se activa sin orden explícita**.

## Punto de decisión, resuelto el 2026-08-21

La frontera de persistencia del dominio **quedó cerrada** con 7.1 y, a
diferencia de los cinco dominios anteriores, **la capa HTTP se quedó sin SQL**.
Lo que quedaba del objetivo de la capa era la parte condicional del índice, que
**no entra por inferencia**. Se ofrecieron **tres** salidas y **el usuario
eligió cerrar la capa aquí**, sin abrir 7.2:

1. **Cerrar la capa aquí**, como refactorización pura, igual que hicieron las
   capas 5 y 6 y los cinco dominios anteriores. ← **elegida**.
2. **Abrir una 7.2 con `response_model`.** Aquí era **la más barata de todo el
   programa**: las dos respuestas son planas —un diccionario de tres cadenas y
   un `{"mensaje": …}`— y no hay anidamiento. El único matiz era el `None` de la
   observación ausente, que obliga a un `Optional`.
3. **Abrir una 7.2 con los errores de dominio.** Era **la más cara aquí**, y por
   una razón concreta: el dominio **no usa `HTTPException` en ninguna parte**.
   Introducirla cambiaría cómo salen los fallos, que hoy suben desnudos hasta el
   500 genérico de FastAPI. No habría sido una refactorización pura.

**`response_model` y los errores de dominio no se añaden y no quedan como deuda
de esta capa.** Son trabajo disponible que exigiría una orden propia. Queda
anotado que la salida 2 era **la más barata que ha tenido ninguna capa 7**: si
alguna vez se quiere probar `response_model` en el programa, este es el dominio
donde menos cuesta.

**Ninguno de los nueve hallazgos se corrigió**, ni siquiera la ausencia de
claves foráneas, que es el más grave: exigiría una migración real sobre la base
—fuera del alcance de esta capa— y una decisión sobre las filas huérfanas que ya
existan. **Los pasos del guion que no constan siguen sin constar.**

## Staging, rollback y verificación manual

### Lo que esta capa hizo y no hizo

- **Hizo**: inventariar el dominio contando el SQL de la ruta además del del
  controlador, delimitar la frontera con `plan_de_clases`, añadir 25 pruebas de
  caracterización y extraer las 2 sentencias a `observaciones_repository`.
- **No hizo**: tocar el esquema, los permisos, las rutas, los payloads, los
  status codes, la normalización de las dimensiones, el `422` ni la semántica
  transaccional. **No corrigió ningún hallazgo.**
- **La capa no tocó la base de datos**, ni siquiera para leer; solo leyó el
  fichero de la migración base para inventariar el DDL. Es la **octava
  consecutiva** que no abre una conexión a PostgreSQL, y la **quinta de esas
  ocho cuyo dominio sí escribe**.

### Rollback

Al cerrar la capa, el rollback era puramente local porque sus tres commits de
implementación aún no estaban publicados. **Ese estado cambió después.**

`HEAD` y la referencia local `origin/main` coinciden ahora en `580c0ad`, el
commit de cierre, y el reflog registra `update by push`. Revertir a `fd3f93a`
seguiría devolviendo la sentencia a la ruta y el `UPSERT` al controlador, y
eliminaría el repositorio nuevo y la caracterización, pero **ya no es una
operación puramente local**: requiere otro push y otro despliegue. No se
consultó el remoto real en el turno de corrección y no se atribuye ninguna
ejecución de GitHub Actions.

### Staging

No hay entorno de staging para código de aplicación en este programa. El
equivalente disponible es lo ya ejecutado: la compuerta global en local, la
comparación AST byte a byte del conjunto de SQL y la equivalencia en ejecución
de los dos caminos contra el código del commit base.

### Verificación manual: **hecha, con la cobertura que el usuario reportó**

El usuario la ejecutó en local el 2026-08-21 y reportó **resultado correcto**.
**Lo hizo de forma global y con una reserva explícita**: «ya comprobé, y
aparentemente está bien». **No consta ningún paso del guion confirmado uno por
uno.**

Es el **segundo dominio consecutivo** en el tramo más débil de la capa 7. No se
presenta como más fuerte de lo que es, y **no se marca como cumplido ningún paso
concreto**.

## Guion de verificación manual propuesto

Se conserva íntegro por si se quiere cerrar el hueco. Ninguno de estos pasos
consta como ejecutado.

1. **Guardar una observación sobre una que ya existía**, para el mismo
   estudiante, asignación y periodo, cambiando las tres dimensiones. Comprobar
   que se sustituyen y que **no aparece una fila duplicada**. **Es el paso que
   más vale**: única escritura, única transacción, y el `UPSERT` se apoya en la
   única restricción que la tabla tiene.
2. **Enviar las tres dimensiones vacías** y comprobar que responde **422**, no
   500 ni 200. Ese status lo sostiene **solo el esquema** y es lo que una
   extracción descuidada rompería en silencio.
3. **Guardar rellenando una sola dimensión** y comprobar que las otras dos
   quedan como cadena vacía, no como `null`.
4. **Consultar una observación que no existe** y comprobar que la respuesta es
   **`null` con 200**, no un `404` ni un `{}`. Es un contrato con el frontend.
5. **Comprobar el 403** por partida doble: un profesor pidiendo una observación
   de una asignación que no es suya, y un guardado con un estudiante que no
   pertenece a la asignación. Las **dos** entradas exigen los **dos** guards.
6. **Comprobar que no se cruzan con las observaciones de plan de clases**: crear
   una observación académica y una de un plan, y verificar que cada pantalla
   muestra la suya. Son tablas distintas y no deberían mezclarse.
7. **Aislamiento entre tenants**: repetir el paso 1 en los dos colegios y
   comprobar que ninguno ve datos del otro.

## Cierre de la capa 7 para `observaciones`

### Resultado frente a su objetivo

El objetivo era migrar el dominio conservando su comportamiento observable.
**Cumplido**: la persistencia vive en `observaciones_repository`, la ruta pasó
de **41 a 38 líneas** y el controlador de **43 a 30**, los dos de **1 sentencia
inline a 0**, y los dos caminos emiten el mismo SQL con los mismos parámetros,
en el mismo orden respecto a los guards, devuelven lo mismo y abren las mismas
conexiones que el commit base.

### Lo que esta capa aporta al programa, más allá de su dominio

- **La primera extracción que saca SQL de la capa HTTP.** Ningún dominio
  anterior lo necesitó, y demuestra que se puede hacer **sin mover la propiedad
  del cursor**: la ruta sigue abriendo y cerrando lo suyo y llama al repositorio
  directamente, sin inventar un controlador intermedio.
- **La confirmación de que el criterio estricto vuelve cuando el archivo lo
  permite.** `boletin` necesitó una limpieza autorizada y una cadena de dos
  pasos; aquí, comprobado que no había espacios finales, la comparación byte a
  byte se sostuvo entera.
- **La segunda mordedura de la lección 13 de la capa 6.** Excluir docstrings
  antes de comparar texto de un módulo no es una precaución teórica: ha fallado
  dos veces, y la segunda con un docstring escrito para negar justo lo que la
  prueba buscaba.

### Estado de publicación

**Publicada, corrección autorizada el 2026-08-21.** `HEAD` y la referencia local
`origin/main` están en `580c0ad6f0d14d16af5cbd8b2a4a9e4532485b89`, el
commit de cierre. El reflog de esa referencia registra `update by push` el
2026-08-21 a las 15:58:27 -0500. Conforme al flujo documentado del repositorio,
el rollback exige otro push y otro despliegue. No se presenta GitHub Actions
como verificada.

### Riesgos que la capa deja abiertos

- Los **nueve hallazgos de 7.0**, encabezados por **la ausencia total de claves
  foráneas** en la tabla.
- La **verificación manual sin ningún paso que conste**, la segunda seguida.
- **El `422` depende del esquema.** Cualquier trabajo futuro que toque
  `app/schemas/observacion.py` puede convertirlo en un 500 sin que nada más
  falle. Hay una prueba que lo protege y **no debe retirarse**.
- Las verificaciones heredadas del programa, todas **pendientes y aceptadas**.

## Entrega al próximo chat

- Capa activa: **7 para `planilla`, y solo ese dominio**. La capa 7 quedó
  **cerrada para `observaciones`** el 2026-08-21, el mismo día en que se activó.
  Los otros cinco dominios siguen en espera.
- Última subcapa terminada: **7.1**, cerrada el 2026-08-21. Con ella la frontera
  de persistencia del dominio quedó cerrada **y la capa HTTP se quedó sin SQL**.
- **Capa cerrada** el 2026-08-21. No quedan bloqueos.
- Primera subcapa pendiente: **ninguna.** El usuario decidió **cerrar la capa
  aquí**, sin abrir 7.2: `response_model` y los errores de dominio **no se
  abordan** y pasan a ser trabajo disponible que exigiría una orden explícita.
  Queda anotado que **`response_model` era aquí la salida más barata de todo el
  programa**, por si alguna vez se quiere probar en algún dominio.
- **Verificación manual: hecha** el 2026-08-21, en local y con resultado
  correcto, **reportada de forma global y con la reserva «aparentemente»**.
  **No consta ningún paso del guion confirmado uno por uno**: es el **segundo
  dominio consecutivo** en el tramo más débil, tras `boletin`. El guion íntegro
  se conserva; los pasos que más valían son el **1**, guardar sobre una
  observación existente, y el **2**, comprobar que las tres dimensiones vacías
  siguen dando **422**.
- Commit base: `fd3f93a2ad97daa0a34081eb2f95504dd1a9e4df`, rama `main`,
  **publicado y desplegado**, comprobado contra el remoto real al activar. Los
  cuatro commits de la capa —`dac6425` la activación, `eaa8115` la 7.0,
  `4bceabb` la 7.1 y `580c0ad` el cierre— están ahora alcanzados por la
  referencia local `origin/main`; su reflog registra el cierre como
  `update by push`.
- Compuerta al cerrar 7.1: **925 pruebas, exit 0**, Ruff correcto y `pip check`
  íntegro. La suite pasó de **898 al activar la capa a 925**.
- Lo que consiguió 7.1: la ruta pasó de **41 a 38 líneas** y el controlador de
  **43 a 30**, los dos de **1 sentencia SQL inline a 0**; la persistencia vive
  en `app/repositories/observaciones_repository.py`, **2 funciones** que reciben
  el cursor y **el undécimo repositorio** del proyecto. Comparador AST contra el
  commit base: **2 de 2 literales idénticos byte a byte**, sin ninguna
  autorización de cambio de texto —**la comparación estricta sí se sostuvo
  aquí**, al contrario que en `boletin`—. **Los dos caminos emiten la misma
  secuencia de `(SQL, parámetros)`, en el mismo orden respecto a los guards,
  devuelven lo mismo y abren las mismas conexiones** que el commit base.
  **Ninguna prueba cambió de expectativa** salvo las siete que debían fallar, y
  **las ocho heredadas no se tocaron**.
- **El alcance de 7.1 lo decidió el usuario entre tres salidas**, no el
  asistente: se preguntó antes de tocar nada qué hacer con la sentencia que
  vivía en la ruta.
- Lo que 7.0 dejó medido: el dominio son **tres archivos y 104 líneas**; **2
  entradas HTTP** con **un único modelo de permiso**; **una sola tabla
  escrita**; **una transacción propia**; **2 sentencias SQL**, **una en la ruta
  y otra en el controlador**; **8 pruebas heredadas** más **25 nuevas**. **Es el
  dominio con menos SQL que ha migrado el programa**, por debajo de las 3 de
  `asistencia`. **Ningún N+1.**
- **Los once supuestos quedaron resueltos**: **diez confirmados y uno
  incompleto**, ninguno falso, y **ninguno mal atribuido** —la diferencia con
  `boletin`—. El incompleto es el de siempre: el esquema como tercer archivo,
  **tercera vez seguida**.
- **El hallazgo que manda es que la tabla no tiene ninguna clave foránea.**
  `estudiante_id` y `asignacion_id` son enteros sueltos y el `UPSERT` escribe lo
  que le den: la integridad depende **enteramente** del código, que no la
  comprueba.
- Bloqueos: ninguno. Verificaciones heredadas **pendientes y aceptadas** por
  decisión explícita del usuario: valor operativo final de
  `DB_STATEMENT_TIMEOUT_MS` (capa 1), evidencia de GitHub Actions posterior a la
  capa 0, y los pasos no confirmados de los guiones de `ventas`, `asistencia` y
  `boletin`. La credencial privilegiada de la capa 4 sigue **sin rotar**.
- Lo que hay que recordar antes de tocar nada:
  1. **Un solo dominio.** `planilla` está activa en su propia bitácora.
     `dashboard`, `notas`, `ventas`, `asistencia`, `boletin` y `observaciones`
     están cerrados; los otros cinco dominios siguen en espera.
  2. **La ruta YA NO contiene SQL.** Lo contenía —era lo que distinguía a este
     dominio— y 7.1 lo movió al repositorio por decisión explícita del usuario.
     **Pero la ruta sigue siendo dueña de su cursor** y llama al repositorio
     directamente, sin pasar por un controlador. Eso es deliberado.
  3. **La frontera con `plan_de_clases` quedó decidida y es limpia**: paths
     disjuntos y **tablas distintas**, `observaciones` frente a
     `plan_de_clases_observaciones`. No se toca.
  4. **El `422` por contenido vacío lo produce el ESQUEMA**, no el dominio. Si
     7.1 mueve esa validación, el status pasa a **500** en silencio. Hay una
     prueba que lo fija y es la que debe protegerlo.
  5. **El `None` de la observación ausente es un contrato con el frontend**, no
     un descuido: 1.4 lo fijó por prueba y 7.0 añadió el orden de los guards.
  6. **`app/core/permissions.py` está fuera de alcance**, incluida
     `require_estudiante_in_asignacion`, que este dominio llama **dos veces**.
  7. **El commit base ya está en producción.** El rollback de esta capa, si se
     publica, **no será local**.
  8. **No corregir ninguno de los nueve hallazgos propios**, empezando por la
     ausencia de claves foráneas, ni los cincuenta y uno que dashboard, notas,
     ventas, asistencia y boletin dejaron abiertos.
  9. **Ejecutar siempre la compuerta completa**: `estudiantes_repository` lee
     esta tabla y no fallaría con las pruebas de este dominio.
  10. **Los dos idiomas de conexión se conservan.** Unificarlos cambiaría los
      conteos que 7.0 fijó por aserción.
  11. **Los repositorios son ya once.** Cada migración añade una enumeración y
      el número crece en uno: es el patrón registrado desde `asistencia`, y en
      7.1 volvieron a fallar **cuatro** guardias ajenas por ese motivo.
  12. **Al comparar texto de un módulo, excluir los docstrings.** Es la lección
      13 de la capa 6 y en 7.1 volvió a morder: el docstring del repositorio
      nombra `get_connection` justo para explicar que no lo usa.
  13. **El `422` lo sostiene solo el esquema.** Cualquier trabajo futuro sobre
      `app/schemas/observacion.py` puede convertirlo en un 500 sin que nada más
      falle. La prueba que lo protege **no debe retirarse**.
- **Publicación corregida:** la referencia local `origin/main` alcanza el commit
  de cierre `580c0ad` y su reflog registra `update by push`. El rollback ya no
  es puramente local. No se atribuye ningún run de GitHub Actions.
- Siguiente acción exacta: **ninguna dentro de esta capa.** Queda cerrada. El
  siguiente paso del programa es **7.0 de `planilla`**, pendiente y no iniciada,
  conforme a `07_PLANILLA.md`.

## 2026-08-25 — auditoría de los nueve hallazgos

El usuario ordenó revisar los hallazgos de este dominio y **comprobar cuáles son
reales**, después de que la campaña de `dashboard` destapara dos diagnósticos
falsos entre diez. Esta entrada registra la comprobación. **No modificó producto
ni pruebas.**

- Modo de acceso: mismo checkout local; Git y el árbol comprobados
  directamente.
- Precondiciones: rama `main`, árbol **limpio**, `HEAD`
  `007a0cd7ccf49d557d1dbac90c60c7f505ff322f`. **`origin/main` está en
  `8a72cc8`**, así que hay **un commit local sin publicar**, el cierre
  documental de la campaña de dashboard.
- Método: cada hallazgo se contrastó contra su fuente real —el esquema de
  `migrations/base/`, el código del dominio, o una petición HTTP conducida por
  **ASGI**—, sin fiarse del texto de la bitácora.

### Veredicto: **ocho confirmados, uno obsoleto**

| # | Hallazgo | Veredicto | Evidencia |
|---:|---|---|---|
| 1 | Sin claves foráneas | **CONFIRMADO, y se queda corto** | La tabla solo tiene `observaciones_pkey` y `unique_observacion`. Un barrido del esquema base demuestra que **es la única tabla del programa** con `estudiante_id`/`asignacion_id` sin clave foránea hacia ellos: las otras dieciséis sí la tienen. Y las columnas son además **nullable**, que la bitácora no decía |
| 2 | `text` sin `CHECK`, frente al vecino | **CONFIRMADO literalmente** | `plan_de_clases_observaciones` tiene `ck_plan_observacion_texto CHECK (length BETWEEN 1 AND 3000)`; `observaciones` no tiene ninguno |
| 3 | La lectura vive en la capa HTTP | **OBSOLETO** | Ver abajo |
| 4 | El `422` lo produce el esquema | **CONFIRMADO con una respuesta real** | Un cuerpo sin las tres dimensiones devuelve **422** con `"type":"value_error"` del `model_validator` |
| 5 | Falsy → cadena vacía | **CONFIRMADO exactamente** | `0`, `False` y `[]` llegan como `""`; `7` llega como `"7"`. Y con las tres dimensiones en `0` la petición se rechaza con el 422 del hallazgo 4 |
| 6 | El `UPSERT` no comprueba `activo` | **CONFIRMADO, y alcanza más lejos** | Ni el `UPSERT`, ni `require_asignacion_access`, ni `require_estudiante_in_asignacion` filtran `activo`. **Ninguna de las tres capas lo comprueba** |
| 7 | No se registra nada ante un fallo | **CONFIRMADO en lo esencial** | Ver el matiz abajo |
| 8 | `periodo` sin cota | **CONFIRMADO** | El esquema acepta `99`, `-5` y `0` |
| 9 | Defensa duplicada con `.get` | **CONFIRMADO** | `model_dump()` devuelve siempre las seis claves, así que el `.get` solo actuaría fuera de la ruta |

### El hallazgo 3 está obsoleto, y no por un error de 7.0

Decía: «el `SELECT` y el resolver están en `obtener_observacion`, dentro del
router». **Era cierto cuando se escribió**, y **lo corrigió la propia 7.1** al
mover el SQL al repositorio. Medido hoy: **0 sentencias en la ruta**, 0 en el
controlador y **2 en el repositorio**.

Lo que **sigue siendo cierto** del hallazgo es la parte que 7.1 decidió no
tocar: la ruta **abre su propio cursor** con `get_cursor()` y **llama al
resolver** directamente, así que la capa HTTP sigue tocando la base. Eso es
deliberado y está registrado en la decisión de 7.1 sobre los dos idiomas de
conexión.

**Lo que falla es el índice de hallazgos**, que lo sigue listando bajo
«registrados y **sin corregir**» cuando la subcapa siguiente lo corrigió a
medias. Es el mismo desfase que `dashboard` arrastraba, y queda corregido con la
marca del veredicto.

### El matiz del hallazgo 7

La parte central es **cierta**: no hay `try/except` ni `logger` en el router, y
un fallo del controlador **no deja ninguna traza de la aplicación**. Comprobado
conduciendo la ruta por ASGI con un controlador que lanza un error de
credenciales de PostgreSQL: **cero registros del módulo**.

Su afirmación de que **no se filtra el texto de la excepción también es cierta**,
y se comprobó como es debido: observando **lo que se envía al cliente**, no lo
que le llega al arnés de pruebas. El cliente recibe **500 con el cuerpo
`Internal Server Error` en texto plano**, y la credencial **no aparece en él**.

**Dos precisiones que la bitácora no hacía**, ninguna de ellas un hallazgo
nuevo:

- decir que «tampoco queda traza» **se pasa de frenada**: la excepción se propaga
  al servidor ASGI, que **sí registra el traceback**. Lo que no existe es traza
  del *módulo*, con su contexto de dominio;
- el cuerpo de ese 500 es **texto plano**, no el `{"detail": …}` que devuelve el
  resto de la API. Es una **incoherencia de forma** con todos los demás errores
  del sistema.

### Lo que la auditoría comprobó expresamente y **no** era un hallazgo

- **Se valida un `asignacion_id` y se escribe otro.** Las dos guardas validan el
  id **crudo**, y el controlador escribe el **resuelto**. Parecía un hueco, y
  **no lo es**: el `CASE` de `resolver_asignacion_academica_id_cursor` solo
  devuelve el padre académico cuando **coinciden profesor, curso y materia**, así
  que la validación se transfiere íntegra. Queda registrado para que nadie lo
  levante como hallazgo.
- **El resolver ante una asignación inexistente** devuelve el id de entrada sin
  tocarlo, pero por HTTP ese caso no llega: `require_estudiante_in_asignacion`
  hace `JOIN asignaciones a ON ... a.id = %s` y responde **403** si no existe.

### Consecuencia

**Ocho hallazgos reales siguen abiertos** en este dominio, encabezados por la
ausencia total de claves foráneas, que es **el hallazgo más grave que el
programa ha registrado sobre el esquema**. Ninguno se corrige en este turno:
corregir cualquiera exige una orden explícita, y el 1, el 2 y el 8 **tocarían la
base de datos**, que solo la capa 3 hizo y con autorización por paso.

- Archivos modificados en este turno: **solo esta bitácora**. Producto y
  pruebas: **ninguno**.
- Compuerta global: **1125 pruebas, exit 0**, Ruff correcto, dependencias
  íntegras.
- PostgreSQL real, migraciones, staging, producción, deploy, commit y push:
  **ninguno**. La auditoría leyó `migrations/base/` como texto, **no consultó la
  base**.
- Siguiente acción exacta: **esperar una orden explícita del usuario.** Los ocho
  hallazgos siguen abiertos y ninguno se inicia por inferencia.

## 2026-08-25 — hallazgo 1: migración preparada, **no aplicada**

El usuario ordenó atacar el hallazgo 1, la ausencia total de claves foráneas.
**Este turno no toca la base de datos**: deja escrita la migración y su
comprobación previa, y se detiene antes de cualquier cosa que escriba.

- Modo de acceso: mismo checkout local; Git y el árbol comprobados
  directamente.
- Precondiciones: rama `main`, `HEAD` `007a0cd`, con **un commit local sin
  publicar** —el cierre de la campaña de dashboard—.
- **Este es el segundo cambio de esquema real de todo el programa.** El primero
  y único hasta hoy fue la capa 3, que lo hizo con ensayo en una rama de Neon,
  `--dry-run` y **autorización explícita por paso**. Se sigue ese mismo camino.

### Lo que se escribió

- **`migrations/20260825_observaciones_claves_foraneas.sql`**. Repone las dos
  claves con las definiciones **copiadas exactamente** de `asistencia` y
  `notas_detalle`, que son las gemelas estructurales de esta tabla —mismo trío
  estudiante/asignación/periodo— y ya usan esta convención:
  `asignacion_id → asignaciones(id) ON DELETE CASCADE` y
  `estudiante_id → estudiantes(id)` sin acción de borrado. **No se inventó
  ninguna semántica nueva.**
- **`scripts/auditar_huerfanos_observaciones.py`**. Informe **de solo lectura**:
  abre la transacción como `READ ONLY`, no escribe nada y termina con
  `rollback`, el criterio que fijó la capa 4. Recorre **todos** los schemas de
  tenant, porque el runner aplica a todos y basta uno con huérfanas para
  detener la migración.

### Decisiones de diseño, con su motivo

- **No destructiva.** Si encuentra filas huérfanas, la migración se **detiene
  con el recuento** y no borra ni modifica ninguna. Es el patrón de
  `20260722_plan_de_clases_integridad.sql`. Reparar datos es una decisión del
  usuario, no de una migración.
- **Idempotente.** No existe `ADD CONSTRAINT IF NOT EXISTS`, así que comprueba
  `pg_constraint` antes de cada una. Permite reejecutarla sobre un tenant que ya
  la tenga.
- **No cambia la nulabilidad**, y esto es una limitación que conviene no
  disimular: **una clave foránea no restringe `NULL`**. Una fila con
  `estudiante_id` nulo seguirá siendo válida después de aplicarla, exactamente
  como hoy lo es en `asistencia`. Añadir `NOT NULL` es otro cambio y exige su
  propia decisión.
- **Solo el hallazgo 1.** No se tocan el `CHECK` de texto —hallazgo 2— ni la
  cota de `periodo` —hallazgo 8—, aunque irían en una migración de esta misma
  familia. Ampliar el alcance sin orden es lo que el índice prohíbe.

### La compuerta queda **en rojo, y es lo correcto**

`tests/test_esquema_base.py` falla con:
«El archivo base no incorpora 1 migracion(es):
`20260825_observaciones_claves_foraneas.sql`».

**Es la guarda que instaló la capa 3 y está haciendo su trabajo.** El
procedimiento de `docs/MIGRACIONES.md` regenera el archivo base **después** de
aplicar a los tenants y nunca antes, porque el generador lee la estructura real
del schema de referencia. Así que entre añadir la migración y aplicarla existe
**una ventana documentada en la que la compuerta está roja a propósito**. Ruff y
`pip check` siguen correctos, y las otras **1124 pruebas pasan**.

**No se debe silenciar esa prueba ni regenerar la base para calmarla**: hacerlo
capturaría el esquema anterior sin avisar, que es justo lo que su mensaje
advierte.

### Secuencia pendiente, que decide y ejecuta el usuario

1. **Ver los números primero**, sin escribir nada:
   `python scripts/auditar_huerfanos_observaciones.py`. Sale 0 si no hay
   huérfanas y 2 si las hay.
2. Si hay huérfanas: **decidir qué hacer con ellas**. La migración no las toca.
3. **Ensayar en una rama de Neon**, no en producción, apuntando ahí
   `DATABASE_URL`.
4. `apply_migration.py migrations/20260825_observaciones_claves_foraneas.sql
   --dry-run` y luego sin `--dry-run`, con el **endpoint directo**, no el
   `-pooler`.
5. **Regenerar la base**:
   `scripts/generar_esquema_base.py --schema tenant_colegio_1`. Solo después del
   paso 4.
6. **Ejecutar la compuerta**, que debe volver a verde.
7. Commitear migración y base **juntas**.

### Lo que este turno NO hizo

- **No conectó con PostgreSQL.** Ni lectura, ni `--dry-run`, ni medición. El
  esquema se leyó de `migrations/base/` como texto.
- **No aplicó ninguna migración**, no regeneró la base, no commiteó ni publicó.
- **No modificó código de producto ni pruebas.** El diff son **dos archivos
  nuevos** y esta bitácora.
- No tocó los otros siete hallazgos.

### Riesgos de la operación, para cuando se decida

- **La migración puede fallar por datos**, y es su comportamiento correcto. El
  paso 1 lo anticipa sin intentarlo.
- **`ON DELETE CASCADE` hacia asignaciones es un cambio de comportamiento
  real**: a partir de aplicarla, borrar una asignación **borrará sus
  observaciones**. Hoy quedarían huérfanas. Es la semántica que ya tienen
  `asistencia` y `notas_detalle`, pero **es nueva para esta tabla** y conviene
  decirla en voz alta. La capa 6 registró que asignaciones **desactiva con
  `UPDATE` y nunca borra**, así que en la práctica no debería dispararse.
- **El rollback es de esquema**: `ALTER TABLE observaciones DROP CONSTRAINT` las
  dos. No hay rollback de datos, porque la migración no los toca.
- Estado: la capa sigue **Cerrada**. El hallazgo 1 pasa de «registrado» a
  **«migración preparada, sin aplicar»**. Los otros siete siguen abiertos.
- Siguiente acción exacta: **el usuario ejecuta el paso 1** y decide. **Nada se
  aplica sin su orden.**

## 2026-08-25 — ensayo de la migración en una rama de Neon

Es el **paso 3** del procedimiento de `docs/MIGRACIONES.md` y el mismo camino
que siguió la capa 3. **Producción no se tocó en ningún momento.**

- Autorización: el usuario facilitó la cadena de conexión de una rama de Neon
  para el ensayo, tras preguntar expresamente **qué busca el cambio y si es
  necesario**.
- **Comprobación previa a conectar, no formal**: se verificó que el host
  **no es el endpoint de producción** —`ep-late-smoke-aip41j6x`—, que **no es el
  agrupado `-pooler`** —donde el runner se niega, trampa de la capa 3— y que no
  coincide con el del `.env`. Solo después se conectó.
- La rama contiene **los dos schemas reales**, `tenant_2005` y
  `tenant_colegio_1`, así que sus datos son representativos.

### Paso 1: la pregunta que decidía si el cambio hace falta

`scripts/auditar_huerfanos_observaciones.py`, en transacción `READ ONLY` con
`rollback`:

| Schema | Filas | `estudiante_id` huérfano | `asignacion_id` huérfano | Nulos |
|---|---:|---:|---:|---:|
| `tenant_2005` | 39 | **0** | **0** | 0 y 0 |
| `tenant_colegio_1` | 5 | **0** | **0** | 0 y 0 |

**Cero huérfanas sobre 44 filas reales, y cero nulos.** Exit 0.

**Esto confirma el análisis previo**: el cambio es **endurecimiento, no
reparación**. La integridad se ha mantenido porque la guarda de permisos
`require_estudiante_in_asignacion` demuestra que ambos ids existen antes de
escribir, porque **hay un solo escritor** en todo el repositorio, y porque
**nada borra estudiantes ni asignaciones**. Los tres extremos se verificaron
por código antes del ensayo.

### Pasos 2 y 3: dry-run y aplicación, solo en la rama

- `--dry-run`: los dos tenants **PENDIENTE**, sin aplicar nada. Exit 0.
- Aplicación real: los dos tenants **OK**. Exit 0.

### Verificación del resultado, que es lo que importa

No basta con que no fallara. Se comprobó qué quedó:

| Schema | Claves creadas | Validadas | Filas |
|---|---|---|---:|
| `tenant_2005` | `observaciones_asignacion_id_fkey` → `asignaciones` **ON DELETE CASCADE**; `observaciones_estudiante_id_fkey` → `estudiantes` **ON DELETE NO ACTION** | **sí** | 39, intactas |
| `tenant_colegio_1` | las mismas dos | **sí** | 5, intactas |

Las dos semánticas coinciden **exactamente** con las de `asistencia` y
`notas_detalle`, que era el objetivo.

**Prueba de fuego**, con todo revertido después:

| Intento | Resultado |
|---|---|
| `INSERT` con `estudiante_id` inexistente | **RECHAZADO** por la clave foránea |
| `INSERT` con `asignacion_id` inexistente | **RECHAZADO** por la clave foránea |
| `INSERT` legítimo | **ACEPTADO** |

Las 39 filas seguían siendo 39 al terminar: **nada quedó escrito**.

### Lo que este turno NO hizo

- **No tocó producción.** Todo ocurrió contra la rama.
- **No regeneró el archivo base.** Hacerlo desde la rama capturaría el esquema
  equivocado; el procedimiento lo regenera desde `tenant_colegio_1` **después**
  de aplicar a los tenants reales. **Por eso la compuerta sigue en rojo**, y es
  lo correcto.
- No commiteó, no publicó, no modificó código de producto ni pruebas.

### Incidente de seguridad, registrado

Un error de conexión **volcó la contraseña de la rama** en la salida, porque el
DSN venía entre comillas y la extracción en shell no las quitó. A partir de ahí
todas las salidas se filtraron para ocultar el DSN. **La credencial de la rama
debe rotarse**; no afecta a producción, cuyo `.env` no se tocó en ningún
momento.

### Estado del hallazgo 1

Pasa de «migración preparada» a **«migración ensayada con éxito, sin aplicar a
producción»**. Lo que queda es **decisión del usuario**, con dos datos en la
mano: **no hay nada roto que arreglar**, y **la migración funciona y protege**.

Nota práctica que conviene no perder de vista: mientras la migración esté en
`migrations/` sin aplicarse a los tenants reales, **la compuerta seguirá en
rojo**. Aplazar el cambio exige por tanto **retirar el archivo** hasta que se
decida, no simplemente dejarlo ahí.

## 2026-08-25 — hallazgo 1 **aplicado a producción**

Es el **segundo cambio del esquema real en todo el programa**, después de las
tres reparaciones de la capa 3. Se hizo con orden explícita del usuario y
siguiendo el procedimiento de `docs/MIGRACIONES.md` paso por paso.

**Lo ejecutó el usuario, no el asistente.** El sistema de permisos bloqueó la
conexión del asistente a producción; en vez de rodearlo, se le entregaron los
comandos y él los lanzó, pasando la salida de cada paso antes de continuar. Para
un cambio de esquema es además la práctica correcta: la mano que lanza el punto
de no retorno es la que decide.

### Secuencia ejecutada, con su evidencia

| Paso | Comando | Resultado |
|---|---|---|
| 0 | Derivar el endpoint **directo** desde el `.env` | `HOST: ep-late-smoke-aip41j6x...` **sin `-pooler`**. Era imprescindible: el runner rechaza el agrupado |
| 1 | `auditar_huerfanos_observaciones.py` | **0 huérfanas y 0 nulos** en los dos schemas; 39 filas en `tenant_2005` y 5 en `tenant_colegio_1` |
| 2 | `apply_migration.py … --dry-run` | Los dos tenants **PENDIENTE**; sin cambios |
| 3 | `apply_migration.py …` | Los dos tenants **OK** |
| 4 | `generar_esquema_base.py --schema tenant_colegio_1` | «el contenido CAMBIO»; 30 tablas, 1 función, 1 disparador |
| 5 | Auditoría de nuevo | «claves foraneas actuales: `observaciones_asignacion_id_fkey`, `observaciones_estudiante_id_fkey`» **en los dos schemas** |
| 6 | `scripts/verify.py` | **1125 pruebas, exit 0**, Ruff correcto, `pip check` íntegro |

**Las 44 filas siguen ahí**, 39 y 5, las mismas antes y después. **Ningún dato
se modificó.**

### La coincidencia que dio confianza

Producción tenía **exactamente los mismos recuentos que la rama** —39 y 5, cero
huérfanas—, así que el ensayo se había hecho sobre una foto fiel y lo verificado
allí era lo que iba a ocurrir aquí. En la rama se comprobó además, con todo
revertido, que las claves **rechazan de verdad**: inserción con estudiante
inexistente rechazada, con asignación inexistente rechazada, legítima aceptada.

### La compuerta pasó de roja a verde, como estaba previsto

Al escribir la migración, `test_esquema_base.py` empezó a fallar: es la guarda
que instaló la capa 3 y **debía** fallar hasta que el archivo base incorporara
la migración. El paso 4 la regeneró y la compuerta volvió a **1125 pruebas, exit
0**. El diff del archivo base son **cinco líneas**: el registro de la migración
y las dos `ALTER TABLE`.

### Qué cambia en producción, medido

- **Durante la aplicación**: `ShareRowExclusiveLock` sobre `observaciones`,
  `estudiantes` y `asignaciones` durante **~172 ms por tenant**. Bloquea
  escrituras, **no lecturas**. Medido en la rama, no estimado.
- **Permanente**: **+0,43 ms** por cada observación guardada, medido con
  `EXPLAIN ANALYZE`. Borrar una asignación ahora arrastra sus observaciones, y
  borrar un estudiante con observaciones queda bloqueado; **ninguna de las dos
  ocurre hoy**, porque nada en la aplicación borra ninguna de las dos entidades.
- **Nada más**: ni endpoints, ni payloads, ni status codes, ni cifras. El
  frontend no se entera.

### Qué mejoró de verdad, sin adornos

La garantía de que una observación apunta a un estudiante y una asignación
reales **pasa del código a la base**. Antes dependía de
`require_estudiante_in_asignacion`, una guarda de permisos que existe para otra
cosa y que un refactor podría mover o sustituir sin que nadie lo notara. Ahora
no se puede refactorizar por accidente.

**No arregló nada roto**: había cero huérfanas. Fue **prevención, no
reparación**, y así quedó dicho antes de aplicarlo.

### Rollback

`ALTER TABLE observaciones DROP CONSTRAINT observaciones_estudiante_id_fkey` y
lo mismo con `observaciones_asignacion_id_fkey`, en cada schema. Instantáneo y
**sin datos de por medio**, porque la migración no tocó ninguno. Habría que
regenerar el archivo base después.

### Incidente registrado

Durante el ensayo, un error de conexión **volcó la contraseña de la rama** en la
salida, antes de que se filtraran los mensajes. **No afectó a producción**,
cuyo `.env` no se leyó en voz alta en ningún momento. La credencial de la rama
**debe rotarse**.

### Estado

- **Hallazgo 1: CORREGIDO Y APLICADO A PRODUCCIÓN.** Es el primero de los nueve
  de este dominio que se resuelve, y el primero de todo el programa que se
  resuelve **en el esquema** en vez de en el código.
- Quedan **siete abiertos** —el 3 estaba obsoleto—, entre ellos el `CHECK` de
  texto y la cota de `periodo`, que son de esta misma familia y **irían por
  migración**. Ninguno se inicia sin orden.
- **Pendiente de commitear y publicar.** La migración y el archivo base deben ir
  **en el mismo commit**, para que el repositorio nunca diga dos cosas
  distintas. El código de la aplicación **no cambió**: no hay nada que
  desplegar.

## 2026-08-27 — hallazgos 2 y 8, verificados antes de tocar nada

El usuario ordenó continuar con los dos hallazgos de la familia del 1 —los que
irían por migración— y **comprobar bien si son reales**. La comprobación
concluye que **los hechos son ciertos pero el encuadre de los dos es
engañoso**, y que **no procede aplicar nada**. Este turno no modificó producto,
pruebas ni base de datos.

### Lo que dicen y lo que se midió

Los dos afirman un hecho verdadero: `observaciones` no acota la longitud de sus
tres textos ni el rango de `periodo`. Eso se confirmó en la auditoría del
2026-08-25 y sigue siendo cierto.

Lo que **no** se había comprobado es si eso convierte a este dominio en
deficiente. Se midió sobre el esquema completo:

| Medida | Resultado |
|---|---:|
| Columnas `text` en todo el esquema | **34** |
| De ellas, con acotación de longitud | **1** |
| Columnas `periodo integer` | **7** |
| De ellas, con `CHECK` de rango | **1** |

**`observaciones` no es la excepción: es la norma.** La única columna de texto
acotada de toda la base es `plan_de_clases_observaciones.observacion`, y el
único `periodo` acotado es el de `planeador_anual`.

### Por qué el encuadre del hallazgo 2 es engañoso

Dice que «el dominio académico está **menos protegido** que el de planes de
clase». La comparación es cierta en el punto que elige y **falsa en conjunto**:
`plan_de_clases` tiene **ocho columnas `text` y ninguna acotada**. El dominio
que se presenta como mejor protegido tiene, él solo, **más columnas de texto sin
acotar que `observaciones`**. Lo que existe es **una** columna acotada en todo
el sistema, no un dominio vecino más riguroso.

### Por qué el encuadre del hallazgo 8 es engañoso

`observaciones` comparte su `periodo` sin cota con **`asistencia`, `notas`,
`notas_detalle`, `boletin_cabecera` y `plan_de_clases`**. Son seis tablas
iguales y **una** distinta. Acotar solo esta no cerraría una brecha: crearía una
séptima variante.

### El riesgo sí es real, y alcanza al frontend

Ninguno de los dos es inofensivo, y esto también se comprobó:

- **Los tres campos son `<textarea>` sin `maxLength`** en
  `FormularioObservacionEstudiante.jsx`. No hay límite en el navegador, ni en el
  esquema Pydantic, ni en la base: **una observación de megabytes es
  almacenable hoy** sin salir de la interfaz.
- El contraste es exacto y elocuente: `DetallePlaneacionAdmin.jsx` **sí** pone
  `maxLength={3000}`, que es justo el límite de su `CHECK`. Ese dominio está
  protegido en las dos capas; este, en ninguna.
- **`periodo` sale de `localStorage`.** `obtenerPeriodoProfesor` lee
  `periodo_profesor_<id>` o `periodo` **sin validar el rango**, y el componente
  solo hace `parseInt(...) || 1`, que descarta lo no numérico pero **acepta 99 o
  -5**. Es editable desde el navegador.

### Conclusión: no se aplica nada

**La diferencia con el hallazgo 1 es la que decide.** Aquel era real *y*
específico: `observaciones` era **la única de diecisiete tablas** sin claves
foráneas hacia sus dos padres, y reponerlas cerró una anomalía. Estos dos son
reales *pero no específicos*: la anomalía sería **crearla**.

Aplicar un `CHECK` solo aquí tendría además un coste que el hallazgo 1 no tuvo:
**hay que elegir un número** —¿3000 caracteres? ¿1 a 4 periodos?— y ese número
es una **regla académica del colegio, no una decisión técnica**. Es el mismo
motivo por el que el usuario dejó registrada y sin corregir la divergencia de
redondeo de `dashboard`.

**Los dos quedan abiertos y sin corregir**, con su encuadre rectificado. Lo que
sí queda como trabajo disponible, y es **barato y sin riesgo**, es poner
`maxLength` en los tres `<textarea>` del frontend, que no toca la base ni el
backend. Exigiría su propia orden.

- Archivos modificados en este turno: **solo esta bitácora**. Producto, pruebas
  y base de datos: **ninguno**.
- Compuerta: **1125 pruebas, exit 0**.
- Siguiente acción exacta: **esperar orden explícita**. Ni estos dos hallazgos ni
  los otros cinco se inician por inferencia.

## 2026-08-27 — hallazgo 7 corregido: se registra el fallo y se devuelve una constante

- Autorización: el usuario ordenó continuar. Se eligió **este** hallazgo y no el
  6 —el `activo`— por una razón que la comprobación destapó: **están
  enlazados**. Añadir la comprobación de `activo` sin manejador haría que el
  rechazo saliera como **500**, así que el registro va primero.
- Precondiciones: rama `main`, árbol limpio, `HEAD` `7d08293`, publicado.

### El dato que cambió el diseño

**El frontend muestra el campo `detail` literalmente al usuario.**
`Observaciones.jsx` hace
`typeof resultado.detalle === "string" ? resultado.detalle : "Revisa la conexión…"`.

Hoy el usuario ve el mensaje genérico **por accidente**: como no hay manejador,
el cuerpo del 500 es texto plano y `detail` queda `undefined`. Es decir, la
propiedad que 7.0 celebró —«no se filtra el texto de la excepción»— **no venía
de una decisión sino de una ausencia**.

La consecuencia es seria y queda registrada como advertencia: **si alguien
«corrigiera» este hallazgo copiando el patrón viejo de `dashboard`
—`HTTPException(400, str(e))`— un error de PostgreSQL aparecería en un aviso en
pantalla**. Por eso el `detail` son **constantes** y hay una prueba que lo fija.

### Lo que cambió

`app/routes/observaciones.py`, y **solo ese archivo de producto**:

- `logging`, un `logger` de módulo y **dos constantes**, `_ERROR_GUARDAR` y
  `_ERROR_CONSULTAR`, redactadas para que sean legibles por el usuario final,
  porque **se muestran**.
- Las dos entradas envuelven su trabajo en `try`, registran con
  `logger.exception` —que conserva el traceback e identifica estudiante,
  asignación y periodo— y responden **500** con la constante.
- **`except HTTPException: raise` delante del genérico** en las dos. Aquí el
  controlador no lanza ninguna, pero se pone igual: es la lección que costó una
  regresión en `dashboard`, donde un 403 lanzado desde dentro acabó convertido
  en 500.
- **Las dos guardas de permiso siguen fuera del `try`**, por el mismo motivo.

### Qué cambia para el cliente

| | Antes | Ahora |
|---|---|---|
| Status | 500 | **500**, igual |
| Cuerpo | `Internal Server Error`, texto plano | `{"detail": …}`, como el resto de la API |
| Traza de la aplicación | **ninguna** | `logger.exception` con traceback |
| Lo que ve el usuario | «Revisa la conexión e intenta nuevamente» | «No se pudo guardar la observacion. Intenta de nuevo.» |

**El status code no cambia**, que es la diferencia con la corrección equivalente
de `dashboard`. Lo que cambia es la forma del cuerpo y el mensaje visible, y
este último **a mejor**: ahora dice qué falló.

### Verificación

- La guardia de línea base `test_ninguna_de_las_dos_entradas_envuelve_el_fallo_en_un_try`
  exigía **lo contrario** —que no hubiera `try`, `HTTPException` ni `logger`— y
  **falló al corregir**, que era la señal esperada. **Fue el único fallo**: las
  demás pruebas del dominio no cambiaron de expectativa.
- Se sustituyó por dos: una estructural y otra **por ASGI con una respuesta HTTP
  real**, que comprueba status **500**, cuerpo exactamente
  `{"detail": _ERROR_GUARDAR}`, que la credencial de PostgreSQL **no aparece en
  la respuesta**, y que **sí queda en el log con su `exc_info`**.
- **Dos aserciones propias se escribieron mal y se corrigieron**, ninguna de
  producto: una buscaba `str(e)` en el archivo y la disparaba el propio
  comentario que advierte de ello; otra rompió la sintaxis al escapar mal un
  salto de línea en una expresión regular. Se sustituyeron por comprobaciones
  directas sobre los dos `detail=`.
- Compuerta: **1126 pruebas, exit 0**, Ruff correcto, dependencias íntegras.

### Estado

- **Hallazgo 7: corregido, sin publicar.** No toca la base de datos: es código.
- **Hallazgo 6 desbloqueado.** Ahora que existe manejador, la comprobación de
  `activo` puede rechazar con un status razonable en vez de un 500.
- Abiertos: **cuatro** —el 4, el 5, el 6 y el 9—, más los dos aparcados con su
  encuadre rectificado.
- Rollback: retirar el `try/except`, el logger y las constantes de la ruta, y
  restaurar la guardia anterior. Sin rollback de datos.

## 2026-08-27 — hallazgo 6 corregido: no se escribe contra una asignación de baja

- Autorización: orden explícita del usuario, que señaló este hallazgo por su
  nombre. Se hizo **después** del 7 porque sin manejador de errores el rechazo
  habría salido como 500.
- **Verificado antes de corregir**, conforme a su instrucción: desactivar una
  asignación **es su baja real**. `asignaciones_repository` lo deja escrito —«no
  borra nunca: el historial académico cuelga de esta fila por seis claves
  foráneas»—, así que `activo = FALSE` es el equivalente a borrarla. Escribir
  observaciones nuevas ahí es escribir en una clase eliminada. **El hallazgo es
  real.**

### Decisión de alcance: se arregla dentro del dominio, no en el código compartido

Las dos guardas que fallan el filtro, `require_asignacion_access` y
`require_estudiante_in_asignacion`, viven en `app/core/permissions.py` y las
usan **17 llamadas en 8 archivos de ruta**. Cambiarlas ahí arreglaría todos los
dominios de golpe **y los afectaría a todos de golpe**, que es un trabajo con su
propio alcance y su propia orden.

Por eso la comprobación se añade **dentro de `observaciones`**, que es el dominio
autorizado. El hueco sigue abierto para los demás y queda registrado.

### Lo que cambió

- `observaciones_repository.asignacion_esta_activa(cursor, asignacion_id)`,
  función nueva.
- `observacion_controller`: comprueba antes del `UPSERT` y lanza
  `AsignacionInactivaError`, una clase propia.
- `app/routes/observaciones.py`: traduce ese error a **403** con
  `_ERROR_INACTIVA`, un mensaje redactado para el usuario final **porque el
  frontend lo muestra**.

**La clase de error propia está justificada**, a diferencia de la que se
descartó en `dashboard`: aquí sí hay dos cosas que distinguir —un rechazo de
permiso, que es 403, y un fallo de infraestructura, que es 500—. Sin ella el
rechazo caería en el `except Exception` y saldría como error del servidor.

### Decisión: solo se bloquea la escritura

**La lectura no se toca.** Consultar una observación antigua de una asignación ya
dada de baja es legítimo, y bloquearlo escondería historial. Hay una prueba que
fija que la ruta de lectura no llama a la comprobación.

### Coste, y qué guardias saltaron

La escritura pasa de **2 consultas a 3** —resolver, comprobar `activo`,
`UPSERT`—, todas sobre **el mismo cursor**: **no añade ninguna conexión**.

Saltaron **seis** pruebas, todas previsibles y ninguna por rotura de
comportamiento:

- tres porque los dobles no devolvían fila para `activo` y el controlador, con
  razón, rechazaba la escritura. Se actualizaron para declarar la asignación
  activa, que es el camino normal;
- dos por los conteos que 7.0 fijó por aserción: 2 sentencias en el repositorio
  ahora son 3, y 2 consultas en la escritura ahora son 3;
- una por indexar `cursor.calls[0]`, que ya no es el `UPSERT`. Se apuntaron al
  último, que es más robusto.

Se añadieron **tres pruebas**: que una asignación de baja hace fallar la
escritura sin escribir ni confirmar, que el rechazo sale como **403 y antes del
manejador genérico**, y que la lectura no queda bloqueada.

### Estado

- **Hallazgo 6: corregido, sin publicar.** No toca la base de datos.
- Compuerta: **1129 pruebas, exit 0**.
- Abiertos: **tres**, todos menores —el 422 frágil, el `0` que se normaliza a
  cadena vacía y el `.get` defensivo—, más los dos aparcados.
- **Queda registrado fuera de alcance**: las guardas de `app/core/permissions.py`
  siguen sin filtrar `activo` para los otros dominios.
- Rollback: retirar la comprobación, la clase de error y su traducción a 403.
