# Capa 7: planilla

Última revisión: 2026-08-21.

## Control

- Estado: **Cerrada** el 2026-08-21, por orden explícita del usuario y sin abrir
  7.2.
- Commit base: `580c0ad6f0d14d16af5cbd8b2a4a9e4532485b89`.
- Rama acordada: `main`.
- Primera subcapa pendiente: **ninguna**. Las 7.0 y 7.1 quedaron cerradas y 7.2
  se marca **No aplica** por la decisión explícita de cerrar aquí.
- Código de producto modificado al activar: **Ninguno**.
- Código de producto modificado en 7.0: **Ninguno**. Su diff funcional es un
  solo archivo de caracterización nuevo; los demás cambios son documentación.
- Código de producto modificado en 7.1: los dos controladores y el servicio
  delegan sus cinco sentencias al nuevo
  `app/repositories/planilla_repository.py`; rutas y esquemas no cambiaron.
- Dominio de esta capa: **planilla, y solo ese**. Los otros cinco dominios que
  siguen en espera necesitan su propia bitácora y su propia orden.
- Autorización: orden explícita del usuario el 2026-08-21, nombrando el dominio:
  «el dominio es planilla».
- La autorización de activación cubrió **solo la activación documental**. No
  autoriza inspeccionar código de `planilla`, ejecutar 7.0, modificar producto,
  tocar la base de datos, hacer commit, push ni deploy.
- Autorización de 7.1: después de presentar el alcance exacto —un único
  repositorio para las cinco sentencias, conservando en los llamadores la
  propiedad de conexiones, cursores y transacciones—, el usuario confirmó que
  era lo siguiente y ordenó «sigue».

## Objetivo

Migrar el dominio de **planilla** con contratos y pruebas, conservando su
comportamiento observable actual.

El índice maestro fija tres condiciones para esta capa:

1. trabajar **un dominio a la vez**;
2. agregar `response_model`, errores de dominio y pruebas HTTP o de integración
   solo después de caracterizar y conservar la respuesta existente;
3. no crear abstracciones compartidas sin dos consumidores reales.

La activación **no inspeccionó código**. Por eso no afirma todavía qué archivos,
endpoints, consultas, escrituras, permisos, cálculos o pruebas pertenecen a
`planilla`. Determinarlo es el primer trabajo de 7.0.

## Frontera conocida documentalmente, todavía no verificada en código

`planilla` llega con una frontera que el programa ya advierte que **no es
limpia**:

- la bitácora cerrada de `notas`, resumida por el índice, atribuye a ese dominio
  la ruta `/planilla/{asignacion_id}`;
- la bitácora cerrada de `boletin`, también resumida por el índice, registra
  `obtener_notas_planilla_controller` como código muerto alojado en su
  controlador y conserva allí **una sentencia SQL inline** para no crear una
  falsa propiedad en un repositorio de `boletin`;
- `notas` y `boletin` son dominios cerrados. Leer lo mínimo para delimitar la
  frontera está permitido en 7.0; mover o modificar su código no lo está sin
  evidencia y una autorización explícita posterior.

Estas afirmaciones proceden exclusivamente de la documentación ya leída. La
activación no abrió rutas, controladores, servicios, repositorios, esquemas ni
pruebas de `planilla`.

## Dependencias de capas anteriores

- **`observaciones` está cerrada.** Su bitácora registra 7.0 y 7.1 completas,
  verificación manual ejecutada y compuerta de cierre con **925 pruebas**, Ruff
  correcto y `pip check` íntegro.
- El commit base de esta capa es el `HEAD` limpio vigente,
  `580c0ad6f0d14d16af5cbd8b2a4a9e4532485b89`, que cierra `observaciones`.
- Los cuatro commits posteriores al base de `observaciones` están explicados:
  `dac6425` activa el dominio, `eaa8115` cierra 7.0, `4bceabb` cierra 7.1 y
  `580c0ad` cierra la capa.
- La referencia local `origin/main` coincide con `580c0ad` y su reflog registra
  `update by push` el 2026-08-21 a las 15:58:27 -0500. En este turno no se
  consultó el remoto real ni se atribuye ninguna ejecución de GitHub Actions.
- `notas` posee documentalmente una entrada con nombre de `planilla`; su
  persistencia y contratos están cerrados y solo pueden leerse en 7.0 para
  clasificar la frontera.
- `boletin` dejó documentalmente una función muerta con una sentencia de
  `planilla`; su frontera también está cerrada y no se modifica por inferencia.

## Lo que el programa cree saber y 7.0 debe comprobar

Aplica la regla de las capas anteriores: cada supuesto heredado se marca como
**no verificado** hasta contrastarlo con el código y las pruebas del dominio.

**Los diez supuestos quedaron resueltos en 7.0:** siete confirmados, uno
incompleto y dos refutados. La frontera documental sí estaba partida, pero la
frontera ejecutable propia resultó nítida: cinco archivos, tres entradas HTTP y
cinco sentencias SQL.

| # | Supuesto documental | Origen | Resultado en 7.0 |
|---:|---|---|---|
| 1 | `planilla` es uno de los dominios pendientes de la capa 7 | Índice maestro | **CONFIRMADO.** El usuario lo activó y su frontera ejecutable propia son cinco archivos y 216 líneas |
| 2 | `notas` posee `/planilla/{asignacion_id}` | Cierre de 7.0 de `notas`, resumido por el índice | **CONFIRMADO y separado.** Es un `GET` del router de `notas`, llama a `notas_controller` y persiste mediante `notas_repository`; no pertenece a las tres entradas propias |
| 3 | `boletin_controller` conserva `obtener_notas_planilla_controller`, sin consumidores, con una sentencia inline | Cierre de 7.1 de `boletin`, resumido por el índice | **CONFIRMADO.** Tiene una sentencia SQL y cero llamadas AST en `app/`; sigue siendo código muerto dentro de un dominio cerrado |
| 4 | La frontera real de `planilla` atraviesa más de un archivo o dominio nominal | Consecuencia de los dos registros anteriores | **CONFIRMADO con matiz.** Los nombres atraviesan tres dominios, pero la frontera ejecutable propia es nítida; los dos bordes ajenos se registran y no se mueven |
| 5 | El dominio lee o escribe datos | No determinado por la documentación de continuidad | **CONFIRMADO: escribe.** `POST` borra e inserta y `DELETE` borra en `notas_detalle`; el `GET` lee cinco tablas |
| 6 | Existen transacciones, cálculos o fórmulas que deban preservarse | No determinado | **CONFIRMADO.** Dos caminos confirman transacción; el JSON calcula promedio numérico a dos decimales y usa cadena vacía si no hay nota numérica |
| 7 | Los permisos y modelos de ownership son uniformes | No determinado | **CONFIRMADO.** Las tres entradas usan `get_current_user` y `require_asignacion_access`; admin retorna temprano y profesor consulta ownership |
| 8 | Existe repositorio o servicio propio de `planilla` | No determinado | **INCOMPLETO.** Existe `planilla_service`, pero no repositorio; las cinco sentencias siguen inline en dos controladores y el servicio |
| 9 | Hay N+1 de consultas o conexiones | No determinado | **REFUTADO.** Los tres caminos tienen conteo constante; el Excel mantiene 2/3 consultas y 1/2 conexiones con uno o tres estudiantes |
| 10 | Existen pruebas propias suficientes para una extracción | No determinado | **REFUTADO.** Había doce casos heredados útiles, pero ninguno fijaba frontera, contrato HTTP, DDL, repositorios ni conteos; 7.0 añadió 30 |

## Alcance autorizado

- Trabajar únicamente en el dominio `planilla`.
- En 7.0, delimitar primero la frontera real entre `planilla`, la ruta que la
  documentación atribuye a `notas` y la función que atribuye a `boletin`.
- Inventariar entradas HTTP, archivos, permisos, ownership, tenant, payloads,
  status codes, respuestas, cálculos, SQL, tablas, transacciones, conexiones,
  efectos laterales, pruebas y consumidores del dominio.
- Resolver uno por uno los supuestos documentales, indicando si están
  confirmados, incompletos, refutados o mal atribuidos.
- Agregar caracterización antes de cualquier extracción importante.
- Medir consultas y conexiones críticas antes y después de cualquier cambio de
  producto posterior.
- Leer de `notas` y `boletin` solo lo indispensable para clasificar la frontera.
  Modificarlos requerirá evidencia de 7.0 y autorización explícita.

## Fuera de alcance

- `planeador_anual`, `plan_de_clases`, `branding`, `profesores` y
  `super_admin`, que siguen en espera.
- Reabrir por inferencia `notas`, `boletin`, `observaciones` o cualquier otro
  dominio cerrado.
- Corregir los hallazgos abiertos de las capas 1 a 7, incluidos la clave de
  idempotencia pendiente de pagos, la ausencia de lock en asignaciones y los
  hallazgos propios de los seis dominios ya cerrados de la capa 7.
- Cambiar rutas, payloads, status codes, permisos, roles, ownership, tenant,
  fórmulas, SQL observable, transacciones o comportamiento actual sin una
  autorización explícita que se apoye en la caracterización.
- Cambiar PostgreSQL, `psycopg2`, el modelo de schemas tenant, el pool, los
  timeouts, la concurrencia, el ORM, el driver o el almacenamiento.
- Migraciones reales, acceso a producción, DDL, DML, deploy, commit o push.

## Invariantes

- Métodos, paths, status codes y forma exacta de respuestas permanecen
  idénticos, incluidos orden, nulos y errores.
- Permisos, roles, ownership y aislamiento entre tenants se conservan.
- Las fórmulas y cifras que 7.0 encuentre forman parte del contrato hasta que el
  usuario autorice expresamente un cambio.
- Se conservan el texto SQL, sus parámetros, el número y orden observable de
  operaciones y los límites de transacción.
- Se conserva quién es dueño de conexión, cursor, `commit` y `rollback`.
- El código de `notas` y `boletin` no se mueve solo porque use el nombre
  `planilla`.
- Ninguna operación DB síncrona vuelve al event loop ni se cambia el limitador
  compartido sin una medición de capacidad propia.

## Línea base

| Comprobación | Comando | Resultado |
|---|---|---|
| Compuerta heredada, antes de modificar | `.\venv\Scripts\python.exe scripts\verify.py` | Primer intento bloqueado por permisos del temporal de pytest dentro del sandbox; repetida fuera del sandbox: **925 pruebas, 5 warnings heredadas, exit 0**, Ruff correcto y dependencias íntegras |
| Caracterización nueva | `.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_planilla_caracterizacion.py` | **30 pasaron**, 5 warnings heredadas |
| Pruebas específicas completas | `.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_planilla_caracterizacion.py tests\test_planilla_controlador.py tests\test_servicios_validacion.py tests\test_boletin_caracterizacion.py::test_obtener_notas_planilla_controller_es_codigo_muerto_de_otro_dominio` | **49 pasaron**, 5 warnings heredadas; incluye la guardia ya existente sobre el consumidor muerto sin duplicarla |
| Suite global después | `.\venv\Scripts\python.exe scripts\verify.py` | **955 pruebas, 5 warnings heredadas, exit 0**, Ruff correcto y dependencias íntegras |
| Ruff | `.\venv\Scripts\python.exe -m ruff check tests\test_planilla_caracterizacion.py` | **Correcto** |
| Dependencias | Incluido en `scripts\verify.py` | **Íntegras antes y después** |
| Señal de guardias al extraer 7.1 | `pytest` sobre la caracterización propia y las cuatro enumeraciones históricas | **8 fallaron y 26 pasaron**: cuatro guardias propias y cuatro enumeraciones; ninguna falla funcional inesperada |
| Pruebas específicas finales de 7.1 | Caracterización, pruebas heredadas de controlador/servicio, frontera de `boletin` y cuatro enumeraciones | **55 pasaron**, 5 warnings heredadas |
| Equivalencia SQL de 7.1 | Comparador AST contra `HEAD` limpio previo | **5 de 5 literales idénticos byte a byte**; el comparador final exige además el conteo exacto de cinco |
| Compuerta final de 7.1 | `.\venv\Scripts\python.exe scripts\verify.py` | Dentro del sandbox: 928 pasaron y 29 errores de setup por el temporal; repetida fuera: **957 pruebas, 5 warnings heredadas, exit 0**, Ruff correcto y dependencias íntegras |

## Inventario y contratos fijados en 7.0

La frontera ejecutable propia son **cinco archivos y 216 líneas**, sin
repositorio y con **cinco sentencias SQL inline**:

| Archivo | Líneas | SQL inline | Responsabilidad |
|---|---:|---:|---|
| `app/routes/planilla.py` | 38 | 0 | Tres entradas HTTP y permiso de asignación |
| `app/controllers/planilla_controller.py` | 68 | 3 | Registrar nota y eliminar un tipo de nota |
| `app/controllers/planilla_excel_controller.py` | 81 | 1 | Armar el JSON de la planilla por periodo |
| `app/schemas/planilla.py` | 12 | 0 | Entrada del registro de nota |
| `app/services/planilla_service.py` | 17 | 1 | Validar pertenencia del estudiante |

### Frontera, delimitada antes de contar

| Propietario | Entrada o artefacto | Decisión de 7.0 |
|---|---|---|
| **`planilla`** | `POST /planilla/nota`, `GET /planilla-excel/{asignacion_id}/{periodo}` y `DELETE /planilla/tipo` | Son las tres entradas ejecutables propias |
| **`notas`, cerrado** | `GET /planilla/{asignacion_id}` | Se queda en `notas`: llama a su controlador y a `notas_repository`; no se cuenta ni se mueve |
| **`boletin`, cerrado** | `obtener_notas_planilla_controller` | Es una función muerta con una sentencia y cero consumidores; se registra separada y no se mueve |

Los paths propios y el de `notas` son disjuntos como pares `(método, path)`.
La colisión era nominal y real en archivos, pero no obliga a reabrir ninguno de
los dos dominios cerrados.

### Entradas HTTP y permisos

Las tres entradas tienen **un único modelo de permiso**:
`get_current_user` más `require_asignacion_access`. Admin retorna sin consultar;
profesor abre una conexión y comprueba `asignaciones.id/profesor_id`; cualquier
otro rol recibe 403.

| Método | Path | Entrada | Respuesta exitosa actual |
|---|---|---|---|
| POST | `/planilla/nota` | `NotaPlanillaCreate` | `200`, `{"mensaje": "Nota registrada correctamente", "nota_id": int}` |
| GET | `/planilla-excel/{asignacion_id}/{periodo}` | Dos path params enteros | `200`, JSON con `columnas` y `data`; **no descarga un archivo** |
| DELETE | `/planilla/tipo` | `asignacion_id`, `descripcion` y `periodo` por query | `200`, `{"mensaje": "Tipo eliminado correctamente"}` |

Ninguna declara `response_model`. El 403 se propaga con `{"detail": "No
autorizado"}`. Pydantic produce 422 para una nota fuera de 1..5 y FastAPI
produce 422 si falta `descripcion` en el DELETE. Una validación interna fallida
del POST, en cambio, devuelve **200** con `{"error": "El estudiante no
pertenece a esta asignación"}`; la petición HTTP real lo confirma.

### Escrituras, lectura y cálculos

- La única tabla escrita es **`notas_detalle`**, compartida con el dominio
  cerrado `notas`.
- El POST valida al estudiante en una conexión separada y, si pasa, abre una
  transacción con `get_cursor(commit=True)`: resuelve la asignación, borra la
  fila del mismo estudiante/periodo/descripción e inserta la nueva.
- El DELETE abre una transacción propia y borra para **todos los estudiantes**
  de la asignación y periodo la descripción normalizada indicada.
- El GET abre solo lectura, cruza `asignaciones`, `cursos`, `materias`,
  `estudiantes` y `notas_detalle`, y devuelve JSON. Descarta la descripción
  mágica `Desde React`, ordena columnas y estudiantes, promedia solo notas
  numéricas con `round(..., 2)` y devuelve `""` si no hay ninguna.
- El DDL permite `periodo NULL`, limita `descripcion` a 100 caracteres y
  conserva las dos claves foráneas, pero **no tiene restricción única** sobre
  estudiante, asignación, periodo y descripción.

### Línea base de consultas y conexiones

Medida herméticamente a través de las funciones de ruta, incluyendo el resolver
y el permiso de profesor, pero sin autenticación ni round-trips de apertura:

| Camino | Consultas admin/profesor | Conexiones admin/profesor | Transacción |
|---|---:|---:|---|
| POST válido | **4 / 5** | **2 / 3** | Sí, una para DELETE + INSERT |
| POST rechazado por pertenencia, admin | **1** | **1** | No |
| GET Excel/JSON | **2 / 3** | **1 / 2** | No |
| DELETE tipo | **2 / 3** | **1 / 2** | Sí |

**No hay N+1** de consultas ni de conexiones: el GET mantiene exactamente el
mismo conteo con uno y con tres estudiantes.

## Hallazgos de 7.0, registrados y sin corregir

1. **El reemplazo borrar-e-insertar no tiene lock ni restricción única.** La
   transacción protege un intento aislado, pero dos peticiones concurrentes
   pueden borrar y luego insertar dos filas para la misma clave lógica.
2. **Una validación fallida responde 200.** El controlador devuelve un
   diccionario `error` y la ruta lo entrega como éxito HTTP; no es el falso
   mensaje de `POST /notas`, pero sí un falso status de éxito.
3. **`periodo` admite `null` de extremo a extremo.** Es `Optional[int]`, la
   tabla no lo declara `NOT NULL` y las comparaciones `periodo = NULL` no
   encuentran filas previas; el reemplazo puede dejar duplicados nulos.
4. **`tipo_evaluacion` admite cualquier cadena.** Todo valor distinto de
   `numerica` guarda `nota = NULL`, pero solo `desarrollo` conserva
   `valoracion`; un valor desconocido puede guardar ambas en `NULL`.
5. **La longitud se valida solo en PostgreSQL.** `descripcion`,
   `tipo_evaluacion` y `valoracion` no tienen límites Pydantic, aunque la tabla
   usa `varchar(100)`, `varchar(30)` y `varchar(30)`; un exceso termina como
   error de base, no 422.
6. **Una nota numérica también puede ser `None`.** El esquema la hace opcional
   incluso cuando `tipo_evaluacion` conserva el default `numerica`.
7. **El endpoint llamado Excel devuelve JSON.** No genera ni descarga un
   archivo; es contrato actual y no se renombra ni rediseña.
8. **La pertenencia se valida antes de abrir la transacción y en otra
   conexión.** El POST cuesta dos conexiones como admin y tres como profesor;
   no es N+1, pero la validación y la escritura no ven necesariamente el mismo
   snapshot.
9. **Las comprobaciones no filtran `asignaciones.activo`.** Tanto el permiso
   como la validación del servicio aceptan una asignación desactivada si sus ids
   y ownership coinciden, patrón ya visto en otros dominios.
10. **La tabla escrita pertenece también a un dominio cerrado.** `planilla`
    modifica `notas_detalle`, que leen varios módulos y cuya lectura principal
    ya vive en `notas_repository`; romper un contrato ajeno puede aparecer solo
    en la compuerta global.

### Lo que 7.0 buscó y no encontró

- Ningún N+1 de consultas o conexiones.
- Ninguna fuga de conexión en los cinco archivos propios.
- Ningún SQL en la ruta ni f-string SQL.
- Ninguna colisión efectiva de `(método, path)` con la lectura de `notas`.
- Ningún consumidor de la función muerta alojada en `boletin_controller`.

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 7.0 | Delimitar la frontera, inventariar contratos y caracterizar el comportamiento y la línea base | **Cerrada** el 2026-08-21 |
| 7.1 | Extraer las cinco sentencias propias a un único repositorio conservando recursos y contratos | **Cerrada** el 2026-08-21 |
| 7.2 | Cambio adicional posterior a la extracción | **No aplica**; el usuario eligió cerrar sin abrirla |

Las subcapas se adaptarán a la evidencia. Las innecesarias se marcarán `No
aplica` con explicación. Nunca se ejecutan dos en el mismo turno.

## Subcapa 7.0: trabajo exacto, ejecutado y cerrado

1. **Delimitar la frontera antes de contar nada**: identificar las entradas y
   archivos propios de `planilla`, la ruta atribuida a `notas` y la función
   atribuida a `boletin`; registrar ownership real por comportamiento, path,
   tablas y consumidores, no solo por nombre.
2. Inventariar métodos, paths, guards, permisos, payloads, status codes,
   respuestas, orden, nulos y errores de cada entrada del dominio.
3. Inventariar archivos y contar SQL inline por ruta, controlador, servicio y
   repositorio que realmente pertenezcan a la frontera.
4. Determinar si el dominio escribe, qué tablas toca, qué transacciones abre y
   quién es dueño de conexión, cursor, `commit` y `rollback`.
5. Identificar cálculos y fórmulas observables, y fijarlos por prueba antes de
   cualquier extracción.
6. Medir consultas y conexiones por camino, buscando explícitamente N+1.
7. Revisar las pruebas existentes y crear o ampliar una caracterización propia
   sin modificar expectativas heredadas salvo autorización explícita.
8. Resolver los diez supuestos de esta bitácora uno por uno y registrar
   hallazgos sin corregirlos.
9. Archivos permitidos en 7.0: pruebas de caracterización del dominio, esta
   bitácora y el estado correspondiente del índice maestro. **Ningún archivo de
   producto se modifica.**
10. Ejecutar pruebas específicas, Ruff sobre la caracterización, la compuerta
    global, `git diff --check` y revisar que el diff sea exclusivo de 7.0.
11. Actualizar esta bitácora con archivos, comandos, resultados, decisiones,
    riesgos y la siguiente acción exacta.
12. **Detenerse al cerrar 7.0. No iniciar 7.1 en el mismo turno.**

## Criterios de cierre de la subcapa 7.0

- La frontera queda delimitada con evidencia y sin reabrir dominios cerrados.
- Los diez supuestos quedan resueltos uno por uno.
- Existe caracterización ejecutable de contratos, fórmulas, SQL, transacciones,
  consultas y conexiones.
- Compuerta global, pruebas específicas, Ruff y dependencias correctos.
- `git diff --check` correcto y diff exclusivo de 7.0.
- Bitácora actualizada con resultados, decisiones, riesgos y siguiente acción.

## Subcapa 7.1: trabajo exacto, ejecutado y cerrado

1. Crear un único `planilla_repository.py` para las cinco sentencias propias;
   no crear repositorios para las piezas ajenas de `notas` o `boletin`.
2. Hacer que sus cinco funciones reciban el cursor existente y ejecuten una
   sentencia cada una.
3. Conservar en los dos controladores y el servicio la apertura y cierre de
   conexiones, la resolución académica, ambas transacciones, validaciones,
   cálculos, `fetch`, retornos y payloads.
4. Conservar texto SQL, parámetros y orden: borrar e insertar siguen dentro del
   mismo `get_cursor(commit=True)` y la validación sigue en conexión separada.
5. Convertir las cuatro guardias propias de 7.0 y las cuatro enumeraciones
   históricas a su estado positivo, sin cambiar expectativas funcionales.
6. Ejecutar pruebas específicas, comparador AST, Ruff, compuerta global,
   `git diff --check` y revisión de alcance.
7. Actualizar bitácora e índice y detenerse en el punto de decisión sin iniciar
   7.2 ni cerrar la capa por inferencia.

### Criterios de cierre de la subcapa 7.1

- Los controladores, el servicio y la ruta quedan sin SQL inline propio.
- El repositorio contiene exactamente cinco funciones y cinco sentencias; cada
  función recibe primero el cursor y no administra recursos.
- Los cinco literales SQL son idénticos byte a byte al `HEAD` limpio previo.
- Parámetros, retornos, conexiones, transacciones y contratos HTTP conservan
  las expectativas fijadas en 7.0 y en las pruebas heredadas.
- Pruebas específicas, Ruff, compuerta, dependencias y `git diff --check`
  correctos; diff exclusivo de 7.1 y su documentación.

## Criterios de cierre de la capa

- Todas las subcapas necesarias están cerradas.
- Compuerta global correcta.
- Contratos conservados o cambios explícitamente aprobados.
- Staging, rollback y verificación manual documentados.
- La capa queda cerrada y el siguiente dominio permanece en espera hasta una
  nueva orden explícita.

## Staging

No se ejecutó staging en este cierre. Guion documentado para un entorno no
productivo con schema tenant representativo:

1. desplegar el commit revisado que contenga 7.1, sin aplicar migraciones;
2. como admin y como profesor propietario, registrar una nota numérica y una de
   desarrollo, y comprobar status, payload e ids;
3. reemplazar la misma descripción y periodo, confirmando que queda una sola
   fila lógica y que la transacción conserva el dato anterior si el `INSERT`
   falla;
4. consultar `/planilla-excel/{asignacion_id}/{periodo}` y comparar columnas,
   orden, valoraciones, promedio a dos decimales y `""` sin nota numérica;
5. eliminar un tipo en un periodo y comprobar que otro periodo no cambia;
6. confirmar que un estudiante ajeno conserva el `200` con el diccionario de
   error actual y que los 403/422 no cambiaron;
7. comprobar la lectura relacionada de `notas`, el aislamiento entre dos
   tenants y la ausencia de errores nuevos en logs.

## Rollback

- La capa no modificó la base de datos, migraciones, configuración ni
  dependencias. No existe rollback de datos ni DDL.
- En el estado observado al cerrar, `HEAD` está en `5019fd2` y la referencia
  local `origin/main` sigue en el base `580c0ad`; no se consultó el remoto real.
  Por tanto el código de 7.1 todavía puede retirarse localmente mediante un
  **revert** controlado de `5019fd2`, sin reescribir historia.
- El punto de rollback completo del dominio es
  `580c0ad6f0d14d16af5cbd8b2a4a9e4532485b89`. Si la capa se publica, volver a
  él exigirá un commit de reversión, push y despliegue autorizados por el
  usuario; no debe usarse un reset destructivo sobre historia compartida.

## Verificación manual

- Estado al cerrar: **pendiente y no ejecutada ni reportada por el usuario**.
- El guion de staging anterior es también el guion manual de cierre. La
  compuerta automática sí cubre los tres contratos HTTP, parámetros, retornos,
  consultas, conexiones y transacciones, pero no sustituye una prueba contra un
  entorno desplegado representativo.
- Esta verificación no se marca como cumplida. Antes de activar otro dominio el
  usuario deberá elegir explícitamente entre completarla o continuar localmente
  aceptándola —junto con las heredadas— como pendiente.

## Decisiones

- **Activar `planilla` y solo ese dominio.** Motivo: el usuario lo nombró
  explícitamente y el índice exige trabajar uno por uno.
- **Continuar localmente aceptando todas las verificaciones pendientes.** El
  usuario eligió esta opción expresamente antes de activar. Ninguna se marca
  como cumplida.
- **Corregir el relevo documental de `observaciones`.** Se registra que 7.0 y
  7.1 están cerradas y que el reflog de la referencia local `origin/main`
  muestra el cierre publicado por push. No se atribuye un run de GitHub Actions.
- **No resolver la frontera en la activación.** La documentación muestra una
  ruta en `notas` y una función en `boletin`, pero decidir qué pertenece al
  dominio requiere la evidencia de 7.0.
- **Frontera resuelta en 7.0:** las tres entradas propias y sus cinco archivos
  forman el dominio ejecutable; el `GET` de `notas` y la función muerta de
  `boletin` quedan en sus dominios cerrados. Motivo: ownership, llamadores y
  persistencia lo demuestran; moverlos ampliaría el alcance sin consumidor.
- **No definir 7.1 por inferencia.** 7.0 demuestra que una extracción tendría
  que decidir si las cinco sentencias van a uno o más repositorios y qué hacer
  con el servicio. Esa decisión queda para el usuario antes de modificar
  producto.
- **Un único repositorio para las cinco sentencias.** Decisión autorizada por el
  usuario antes de ejecutar 7.1. El servicio forma parte de la frontera propia y
  dejar su consulta inline habría cerrado solo cuatro quintos de la persistencia;
  separarlo en otro repositorio no tendría una segunda frontera ni dos usos
  reales.
- **Los llamadores conservan los recursos.** Los controladores mantienen sus
  transacciones y el servicio su conexión separada. Unificarla reduciría
  conexiones, pero cambiaría la línea base de 7.0 y no estaba autorizado.
- **No mover las piezas de `notas` y `boletin`.** El repositorio nuevo contiene
  solo las cinco sentencias ejecutables propias ya delimitadas; la lectura de
  `notas` y la función muerta de `boletin` permanecen intactas.
- **No corregir los diez hallazgos.** En particular permanecen la carrera del
  reemplazo sin lock ni restricción única, el 200 de la validación fallida y el
  `periodo` nulo. 7.1 es una extracción, no una corrección funcional.
- **Cerrar la capa sin abrir 7.2.** El usuario ordenó «cierra» después de revisar
  el resultado de 7.1. `response_model`, errores de dominio y la carrera
  concurrente no se implementan y requerirán una orden propia si se retoman.
- **Cerrar con verificación manual pendiente.** No se inventa evidencia: no hubo
  reporte manual en este turno. El cierre conserva el guion y obliga a resolver
  o aceptar expresamente este pendiente antes de activar otro dominio.

## Riesgos

- **Frontera nominal partida, ya delimitada.** Las piezas de `notas` y
  `boletin` están clasificadas y no se mueven. Riesgo residual: una extracción
  guiada solo por nombres podría reabrir esos dominios; la caracterización lo
  impide.
- **Código documentado como muerto dentro de un dominio cerrado.** Moverlo por
  nombre podría crear una función sin consumidor o reabrir `boletin`.
  Mitigación: confirmar consumidores antes de decidir. Responsable: 7.0.
- **Perfil de riesgo resuelto: el dominio escribe.** Borra e inserta notas y
  elimina tipos para todos los estudiantes. 7.1 protegió transacciones,
  parámetros y retorno además del texto SQL; el riesgo residual es que una
  corrección futura confunda extracción con cambio funcional.
- **Las cifras pueden ser el contrato.** Las capas anteriores encontraron
  varias fórmulas de promedio. Mitigación: caracterizar cada cálculo antes de
  moverlo. Responsable: 7.0.
- **Verificaciones pendientes aceptadas**, sin marcarlas como cumplidas:
  calibración operativa final de `DB_STATEMENT_TIMEOUT_MS`; evidencia de GitHub
  Actions posterior a la capa 0; pasos manuales no confirmados de `ventas`,
  `asistencia`, `boletin` y `observaciones`; y la credencial privilegiada de la
  capa 4 sin rotar.
- **Verificación manual propia pendiente.** `planilla` se cierra con evidencia
  automática fuerte, pero sin ejecutar el guion de staging/manual. Riesgo: una
  diferencia exclusiva de un entorno desplegado no fue observada. No bloquea
  este cierre por orden explícita, pero sí exige una decisión antes de activar
  el siguiente dominio.

## Registro de ejecución

### 2026-08-21 — activación de la capa para `planilla`

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git validado directamente.
- Documentos leídos completamente y en orden: índice maestro,
  `07_OBSERVACIONES.md`, instrucciones locales —no se encontraron— y
  `PLANTILLA_CAPA.md`.
- Autorización: el usuario eligió continuar localmente aceptando las
  verificaciones pendientes y nombró expresamente `planilla`.
- Rama acordada y observada: `main`.
- Estado antes de escribir: árbol limpio; `git status --porcelain=v1` produjo
  salida vacía.
- Commit base: `580c0ad6f0d14d16af5cbd8b2a4a9e4532485b89`, el `HEAD` limpio vigente.
- Continuidad: `fd3f93a`, base de `observaciones`, es ancestro de `HEAD`; sus
  cuatro descendientes forman una historia lineal y corresponden a activación,
  7.0, 7.1 y cierre, todos explicados en la bitácora y el índice.
- Estado de publicación local: `HEAD` y la referencia local `origin/main`
  coinciden en `580c0ad`; el reflog registra `update by push`. No se consultó el
  remoto real ni se verificó GitHub Actions.
- Corrección documental autorizada: se retira el residuo que declaraba 7.0 de
  `observaciones` pendiente y se actualiza su estado de publicación con la
  evidencia local disponible.
- Archivos creados o modificados: esta bitácora,
  `docs/modularizacion/README.md` y
  `docs/modularizacion/07_OBSERVACIONES.md`.
- Código de producto, pruebas, consultas, migraciones, esquemas, configuración
  y dependencias inspeccionados o modificados: **ninguno**.
- Pruebas, conexiones a PostgreSQL, acceso a producción, commit, push y deploy:
  **ninguno**.
- Verificación documental: `git diff --check` no reportó errores de whitespace
  en los archivos rastreados; la comprobación `--no-index --check` de esta
  bitácora nueva no reportó errores de whitespace. Los avisos fueron únicamente
  de normalización futura LF/CRLF. `git status --short` mostró exactamente los
  tres documentos autorizados y ningún archivo de producto o prueba.
- Siguiente acción exacta: ejecutar únicamente 7.0 conforme al trabajo exacto
  de esta bitácora y detenerse antes de 7.1.

### 2026-08-21 — cierre de 7.0

- Commit observado: `50d6d4110a6aaffcd5bad6941ca993c512dbd036`, creado por
  el usuario después de la activación. Es el único descendiente del commit base
  y contiene exactamente los tres documentos explicados en el registro de
  activación.
- Estado antes de modificar: rama `main`, árbol limpio; confirmado con
  `git status --porcelain=v1` sin salida. El commit base `580c0ad` es ancestro
  de `HEAD`.
- Archivos inspeccionados sin modificar: los cinco archivos propios de
  `planilla`; `app/services/asignacion_academica.py`, la función de permiso y el
  DDL de `notas_detalle`; y únicamente los fragmentos de `notas` y `boletin`
  necesarios para delimitar la frontera. No se leyó el resto del repositorio.
- Archivos modificados: `tests/test_planilla_caracterizacion.py` —nuevo—, esta
  bitácora y el estado de 7.0 en el índice maestro. **Ningún archivo de producto
  fue modificado.**
- Pruebas antes: doce casos heredados propios —diez del controlador y dos del
  servicio—. Eran útiles para la transacción y el JSON, pero no fijaban
  frontera, HTTP real, DDL, repositorios, consultas ni conexiones.
- Cambio realizado: **solo caracterización**. Treinta casos nuevos fijan los
  cinco archivos y cinco SQL, los tres bordes nominales, los tres contratos
  HTTP por ASGI, el único modelo de permiso, las rarezas del esquema, la tabla
  escrita y sus restricciones, las dos transacciones, y la línea base completa
  de consultas y conexiones.
- Compuerta heredada antes de tocar pruebas: el primer intento dentro del
  sandbox terminó con 896 pruebas pasadas y 29 errores de setup por
  `PermissionError` al directorio temporal de pytest. Se repitió fuera del
  sandbox, sin cambiar archivos: **925 pruebas, exit 0**, Ruff correcto y
  `pip check` íntegro. El fallo inicial era del entorno, no del checkout.
- Comandos y resultados:
  - caracterización nueva: **30 pasaron**;
  - caracterización más pruebas heredadas relacionadas, incluida la guardia de
    frontera que ya existía en `boletin`: **49 pasaron**;
  - Ruff sobre el archivo nuevo: **correcto**;
  - compuerta final: **955 pruebas, exit 0**, Ruff correcto y `pip check`
    íntegro;
  - `git diff --check`: sin errores; los únicos avisos son la normalización
    futura LF/CRLF;
  - revisión de alcance: exclusivamente prueba nueva y documentación de 7.0.
- Los diez supuestos quedaron resueltos: **siete confirmados, uno incompleto y
  dos refutados**. El de N+1 quedó refutado y el de suficiencia de pruebas fue
  el segundo refutado.
- Decisiones: la frontera ejecutable propia son las tres entradas del router de
  `planilla`; el `GET` de `notas` y la función muerta de `boletin` no se mueven.
  No se define ni inicia 7.1 sin presentar primero su alcance.
- Riesgos: permanecen los diez hallazgos de 7.0, encabezados por la carrera del
  borrar-e-insertar sin lock ni restricción única y el 200 de la validación
  fallida. Ninguno se corrigió.
- Siguiente acción exacta: **esperar la definición y orden de 7.1**. No se
  inicia en este turno.

### 2026-08-21 — cierre de 7.1

- Modo de acceso: mismo checkout local; rama `main` y árbol limpio antes de
  modificar, comprobado con `git status --porcelain=v1` sin salida.
- `HEAD` previo: `e8e3336ddbec9a155f56ea245b968713e3f89aab`. El commit base
  `580c0ad6f0d14d16af5cbd8b2a4a9e4532485b89` es ancestro. Sus dos
  descendientes están explicados: `50d6d41` activa documentalmente `planilla` y
  `e8e3336` contiene exactamente la caracterización y documentación de 7.0.
- Autorización: después de presentar el alcance exacto de un único repositorio
  con los cinco SQL y recursos conservados en sus llamadores, el usuario
  confirmó que era el paso siguiente y ordenó «sigue».
- Cambio de producto: se creó `app/repositories/planilla_repository.py`, con
  cinco funciones que reciben cursor; los dos controladores y
  `planilla_service` delegan en él. Rutas, esquemas, permisos, resolutor,
  cálculos, payloads y transacciones no cambiaron.
- Alcance excluido: no se modificó `notas`, `boletin`, la base, migraciones,
  configuración ni dependencias; ninguno de los diez hallazgos de 7.0 se
  corrigió.
- Señal de guardias: al mover el SQL, **8 pruebas fallaron y 26 pasaron**.
  Fallaron exactamente las cuatro guardias estructurales propias y las cuatro
  enumeraciones históricas de repositorios; no apareció ninguna falla
  funcional inesperada. Se convirtieron a versiones positivas y se añadieron
  dos guardias de propiedad de cursor y recursos.
- Equivalencia de texto: el primer intento del comparador contó el docstring
  «Inserta» como si fuera `INSERT`; el segundo escapó mal el salto de línea y
  produjo un 0/0 no aceptable. La versión final excluye docstrings por forma y
  exige el conteo exacto: **5 de 5 literales SQL idénticos byte a byte** contra
  el `HEAD` limpio previo.
- Equivalencia observable: las pruebas heredadas y las de 7.0 conservan las
  secuencias y parámetros de las cinco ejecuciones, los retornos, los conteos
  de consultas y conexiones, los dos `commit=True`, el JSON y los tres
  contratos HTTP.
- Pruebas específicas finales: **55 pasaron**, con 5 warnings heredadas.
- Ruff sobre los nueve archivos de producto y pruebas tocados: **correcto**.
- Compuerta global: dentro del sandbox terminó con 928 pruebas pasadas y 29
  errores de setup por `PermissionError` sobre el temporal de pytest; repetida
  fuera del sandbox, sin cambiar archivos: **957 pruebas, 5 warnings heredadas,
  exit 0**, Ruff correcto y `pip check` íntegro.
- `git diff --check`: exit 0; los avisos son únicamente de normalización futura
  LF/CRLF. La revisión de alcance muestra solo el repositorio nuevo, sus tres
  llamadores, la caracterización propia, las cuatro enumeraciones históricas y
  los dos documentos de continuidad.
- Archivos de producto: repositorio nuevo y tres llamadores modificados.
  Pruebas: caracterización propia y cuatro enumeraciones históricas. Documentos:
  esta bitácora y el índice maestro.
- Commit, push, deploy, conexión a PostgreSQL, acceso a producción y migraciones
  reales: **ninguno**.
- La capa sigue **activa**. Siguiente acción exacta: elegir explícitamente entre
  cerrar `planilla` aquí como refactorización pura o definir una única 7.2 —por
  ejemplo `response_model`, errores de dominio o la carrera concurrente—. No
  iniciar ninguna opción por inferencia.

### 2026-08-21 — cierre de la capa para `planilla`

- Orden explícita del usuario: «cierra». Se eligió cerrar como refactorización
  pura y no abrir 7.2.
- Estado previo: rama `main`, árbol limpio y `HEAD` en
  `5019fd2eebd1fb8c3f1789b8e0e15a8fa6b95fed`, el commit local de 7.1.
- Auditoría del commit: contiene exactamente el repositorio nuevo, sus tres
  llamadores, la caracterización propia, las cuatro enumeraciones históricas y
  los dos documentos registrados en 7.1. No incluye archivos ajenos.
- Continuidad: los tres commits posteriores al base están explicados:
  `50d6d41` activa, `e8e3336` cierra 7.0 y `5019fd2` cierra 7.1. El base es
  ancestro y no existe divergencia local documentada.
- Publicación observada solo localmente: `origin/main` está en `580c0ad` y
  `HEAD` tiene tres commits a favor y cero en contra. No se consultó el remoto
  real, no se atribuye GitHub Actions y no se afirma que producción ejecute la
  capa.
- Compuerta sobre el `HEAD` limpio: **957 pruebas, 5 warnings heredadas, exit
  0**, Ruff correcto y `pip check` íntegro.
- `git diff --check` del cierre: exit 0; los avisos son únicamente de
  normalización futura LF/CRLF. El diff final de cierre contiene solo esta
  bitácora y el índice maestro.
- Staging y rollback quedaron documentados. Ninguno se ejecutó; no hubo base de
  datos, migraciones, producción, deploy, push ni commit por parte del
  asistente.
- Verificación manual de `planilla`: **pendiente**. No fue ejecutada ni
  reportada y no se marca como cumplida.
- Los diez hallazgos de 7.0 siguen vivos. Cerrarla no corrige la carrera del
  reemplazo, el 200 de validación fallida, el periodo nulo ni ningún otro.
- Resultado: capa 7 para `planilla` **cerrada**; 7.0 y 7.1 completas, 7.2 **No
  aplica**. Los cinco dominios restantes quedan en espera y ninguno se activa
  por esta orden.
- Siguiente acción exacta: antes de activar otro dominio, pedir una decisión
  explícita entre completar la verificación manual de `planilla` o continuar
  aceptándola junto con las heredadas como pendiente; después, el usuario debe
  nombrar uno de los cinco dominios en espera.

## Entrega al próximo chat

- Capa activa: **ninguna**.
- Última capa cerrada: **7 para `planilla`**, con 7.0 y 7.1 completas y 7.2 No
  aplica.
- Commit base: `580c0ad6f0d14d16af5cbd8b2a4a9e4532485b89`.
- Última subcapa terminada: **7.1 de `planilla`**, cerrada el 2026-08-21.
- Primera subcapa pendiente: **ninguna**; la capa está cerrada.
- Código de producto modificado en 7.1: repositorio nuevo y tres llamadores;
  cinco sentencias inline pasaron a **0** fuera del repositorio.
- Frontera actual: seis archivos propios, tres entradas HTTP, un modelo de
  permiso, cinco SQL en un único repositorio, una tabla escrita y ninguna forma
  de N+1.
- Pruebas: 32 de caracterización propia; compuerta final con **957 pruebas**,
  Ruff y dependencias correctos.
- Verificación manual propia: **pendiente**. Las verificaciones heredadas siguen
  también pendientes y aceptadas; ninguna se marca como cumplida.
- Bloqueos: ninguno.
- Dominios en espera: `planeador_anual`, `plan_de_clases`, `branding`,
  `profesores` y `super_admin`.
- Siguiente acción exacta: resolver o aceptar explícitamente la verificación
  manual pendiente y nombrar el siguiente dominio. No activar ninguno por una
  orden genérica de continuar.
