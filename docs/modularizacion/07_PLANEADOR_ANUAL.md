# Capa 7: planeador anual

Última revisión: 2026-08-21.

## Control

- Estado: **Activa** desde el 2026-08-21.
- Commit base: `235672ea609444a46003175940376c37bfe191c4`.
- Rama acordada: `main`.
- Primera subcapa pendiente: **7.1**, no iniciada.
- Código de producto modificado al activar: **Ninguno**.
- Código de producto modificado en 7.0: **Ninguno**. El diff funcional de la
  subcapa es un solo archivo nuevo de caracterización; los demás cambios son
  documentación.
- Dominio de esta capa: **`planeador_anual`, y solo ese**. Los otros cuatro
  dominios en espera necesitan su propia bitácora y su propia orden.
- Autorización: el usuario eligió la opción 2 —continuar localmente aceptando
  las verificaciones heredadas pendientes— y ordenó expresamente activar el
  dominio «planeador anual».
- La autorización cubre **solo esta activación documental**. No autoriza
  inspeccionar código del dominio, ejecutar 7.0, modificar producto, hacer
  commit, push, deploy, migraciones reales ni acceso a producción.

## Objetivo

Migrar el dominio de **planeador anual** con contratos y pruebas, conservando
su comportamiento observable actual.

El índice maestro fija tres condiciones para esta capa:

1. trabajar **un dominio a la vez**;
2. agregar `response_model`, errores de dominio y pruebas HTTP o de integración
   solo después de caracterizar y conservar la respuesta existente;
3. no crear abstracciones compartidas sin dos consumidores reales.

La activación no inspeccionó código. Por eso no afirma qué archivos, rutas,
consultas, escrituras, permisos, fórmulas o pruebas pertenecen al dominio.
Determinarlo es el primer trabajo de 7.0.

## Dependencias de capas anteriores

- La capa 7 para `planilla` está cerrada: 7.0 y 7.1 completas, 7.2 **No
  aplica**, compuerta final con **957 pruebas**, Ruff correcto y dependencias
  íntegras.
- La verificación manual propia de `planilla` quedó completada y correcta con
  8 de 8 puntos reportados; el entorno no fue especificado.
- El commit base de esta capa es el `HEAD` limpio vigente,
  `235672ea609444a46003175940376c37bfe191c4`.
- Los seis commits posteriores al base de `planilla` están explicados en su
  bitácora: activación, 7.0, 7.1, cierre y dos actualizaciones documentales de
  la verificación manual.
- La referencia local `origin/main` coincide con el commit base. No se consultó
  el remoto real ni se atribuye ninguna ejecución de GitHub Actions.
- Por decisión explícita del usuario, siguen pendientes y aceptadas: la
  calibración operativa final de `DB_STATEMENT_TIMEOUT_MS`; evidencia de GitHub
  Actions posterior a la capa 0; pasos manuales no confirmados de `ventas`,
  `asistencia`, `boletin` y `observaciones`; y la rotación de la credencial
  privilegiada registrada en la capa 4.

## Lo que el programa creía saber y 7.0 comprobó

La documentación de continuidad solo confirmaba que `planeador_anual` era uno
de los cinco dominios en espera. **Los diez supuestos quedaron resueltos en
7.0: seis confirmados, uno confirmado con matiz, dos refutados y uno mixto.**

| # | Supuesto documental | Resultado de 7.0 |
|---:|---|---|
| 1 | `planeador_anual` era un dominio pendiente de la capa 7 | **CONFIRMADO.** El usuario lo activó y su frontera propia son tres archivos y 206 líneas |
| 2 | Su frontera coincide con archivos que llevan ese nombre | **CONFIRMADO CON MATIZ.** Ruta, controlador y esquema son propios; `/notificaciones/planeadores` pertenece por completo a `plan_de_clases` |
| 3 | Tiene entradas HTTP propias | **CONFIRMADO.** Son dos: un `GET` y un `PUT` sobre el mismo path |
| 4 | Lee o escribe datos | **CONFIRMADO: escribe.** El `GET` lee y el `PUT` borra o hace upsert sobre `planeador_anual` |
| 5 | Abre transacciones o produce efectos laterales | **CONFIRMADO.** El `PUT` posee una transacción manual con `commit`/`rollback`; dos funciones sin consumidor también escriben con `get_cursor(commit=True)` |
| 6 | Sus permisos y reglas de ownership son uniformes | **CONFIRMADO.** Ambas rutas usan `get_current_user` y `require_asignacion_access` |
| 7 | Tiene servicio o repositorio propio | **REFUTADO.** No existe ninguno; los cinco SQL están inline en el controlador |
| 8 | Contiene cálculos o fórmulas observables | **CONFIRMADO.** La posición del lote fija `slot = i + 1`; cuatro campos deciden borrar o hacer upsert |
| 9 | Presenta N+1 de consultas o conexiones | **REFUTADO COMO LECTURA, CONFIRMADO EN LA ENTRADA.** El `GET` es constante; el `PUT` emite una operación por fila, `1+N` como admin y `2+N` como profesor, con conexiones constantes |
| 10 | Sus pruebas actuales bastan para proteger una extracción | **REFUTADO.** Había ocho casos útiles, pero no fijaban frontera, HTTP real, DDL, conteos, ownership denegado ni varias rarezas; 7.0 añadió 29 |

La semejanza con `plan_de_clases` quedó resuelta: la ruta vecina llama a su
propio controlador y servicio, no importa `planeador_anual_controller` y no
toca esta frontera. No se modificó ese dominio.

## Alcance autorizado

- Trabajar únicamente en el dominio `planeador_anual`.
- En 7.0, delimitar primero su frontera por rutas, llamadas, tablas y
  consumidores, no solo por nombres de archivo.
- Inventariar entradas HTTP, archivos, permisos, ownership, tenant, payloads,
  status codes, respuestas, cálculos, SQL, tablas, transacciones, conexiones,
  efectos laterales, pruebas y consumidores del dominio.
- Resolver uno por uno los supuestos documentales, indicando si quedan
  confirmados, incompletos, refutados o mal atribuidos.
- Agregar caracterización antes de cualquier extracción importante.
- Medir consultas y conexiones críticas antes y después de cualquier cambio de
  producto posterior.

## Fuera de alcance

- `plan_de_clases`, `branding`, `profesores` y `super_admin`, que siguen en
  espera.
- Reabrir por inferencia `planilla` u otro dominio cerrado.
- Corregir hallazgos abiertos de las capas 1 a 7 o completar verificaciones
  heredadas dentro de esta activación.
- Cambiar rutas, payloads, status codes, permisos, roles, ownership, tenant,
  fórmulas, SQL observable, transacciones o comportamiento actual sin una
  autorización explícita apoyada en la caracterización.
- Cambiar PostgreSQL, `psycopg2`, el modelo de schemas tenant, el pool, los
  timeouts, la concurrencia, el ORM, el driver o el almacenamiento.
- Migraciones reales, acceso a producción, DDL, DML, deploy, commit o push.

## Invariantes

- Métodos, paths, status codes y forma exacta de respuestas permanecen
  idénticos, incluidos orden, nulos y errores.
- Permisos, roles, ownership y aislamiento entre tenants se conservan.
- Las fórmulas y cifras que 7.0 encuentre forman parte del contrato hasta que
  el usuario autorice expresamente un cambio.
- Se conservan texto SQL, parámetros, número y orden observable de operaciones
  y límites de transacción.
- Se conserva quién es dueño de conexión, cursor, `commit` y `rollback`.
- Ninguna operación DB síncrona vuelve al event loop ni se cambia el limitador
  compartido sin una medición de capacidad propia.
- No se crea una abstracción compartida sin dos consumidores reales.

## Línea base

| Comprobación | Comando | Resultado |
|---|---|---|
| Pruebas heredadas antes de modificar | `.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_planeador_anual_validaciones.py` | **8 pasaron**, 1 warning heredada |
| Compuerta heredada antes de modificar | `.\venv\Scripts\python.exe scripts\verify.py` | Primer intento dentro del sandbox: 928 pasaron y 29 errores de setup por permisos del temporal; repetida fuera: **957 pruebas**, 5 warnings heredadas, exit 0 |
| Caracterización nueva | `.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_planeador_anual_caracterizacion.py` | **29 pasaron**, 1 warning heredada |
| Pruebas específicas completas | Caracterización nueva más `test_planeador_anual_validaciones.py` | **37 pasaron**, 1 warning heredada |
| Suite global final | `.\venv\Scripts\python.exe scripts\verify.py` | **986 pruebas**, 5 warnings heredadas, exit 0 |
| Ruff | `.\venv\Scripts\python.exe -m ruff check tests\test_planeador_anual_caracterizacion.py` | **Correcto** |
| Dependencias | Incluido en `scripts\verify.py` | **Íntegras antes y después** |

## Inventario y contratos fijados en 7.0

La frontera propia son **tres archivos y 206 líneas**, sin servicio ni
repositorio y con **cinco sentencias SQL inline**:

| Archivo | Líneas | SQL inline | Responsabilidad |
|---|---:|---:|---|
| `app/routes/planeador_anual.py` | 38 | 0 | Dos entradas HTTP, autenticación y permiso de asignación |
| `app/controllers/planeador_anual_controller.py` | 114 | 5 | Lectura, reemplazo por slots y dos escrituras sin consumidor HTTP |
| `app/schemas/planeador_anual.py` | 54 | 0 | Normalización y validación de contenido/fecha |

`app/main.py` monta el router, el DDL base define la tabla y las funciones
compartidas de permiso y resolución académica participan en los caminos, pero
ninguno de esos archivos pertenece a la frontera propia. La ruta
`GET /notificaciones/planeadores` pertenece a `plan_de_clases`: el nombre es la
única coincidencia.

### Entradas HTTP, permisos y respuestas

Las dos entradas tienen **el mismo modelo de permiso**: la dependencia
`get_current_user` y `require_asignacion_access`. FastAPI evalúa una sola vez la
dependencia repetida en el router y el parámetro. Admin retorna sin consultar;
profesor abre una conexión y valida `asignaciones.id/profesor_id`; otro rol o un
profesor sin ownership recibe 403 antes del controlador.

| Método | Path | Entrada | Respuesta exitosa actual |
|---|---|---|---|
| GET | `/planeador-anual/{asignacion_id}/{periodo}` | Dos enteros de path | `200`, `{"planeadores": [...]}`; `fecha` se serializa como ISO |
| PUT | `/planeador-anual/{asignacion_id}/{periodo}` | Lista de `PlaneadorAnualUpdate` | `200`, `{"message": "Planeador actualizado correctamente"}` |

Ninguna declara `response_model`. Un path no entero y una fila con contenido
sin fecha producen 422. El guard produce 403 con `{"detail": "No autorizado"}`.
Una excepción del controlador produce 500 y expone `str(e)` en `detail`.

### Persistencia, transacciones y cálculos

- La única tabla propia leída y escrita es **`planeador_anual`**.
- El DDL exige `periodo` 1..4 y `slot` 1..8, conserva unicidad sobre
  `(asignacion_id, periodo, slot)` y una FK a `asignaciones` con
  `ON DELETE CASCADE`.
- El `GET` usa `get_cursor()` sin commit, resuelve la asignación académica,
  selecciona nueve columnas y ordena por `slot`.
- El `PUT` conserva una conexión manual y una sola transacción. Resuelve la
  asignación una vez; para cada posición calcula `slot = i + 1`, hace `DELETE`
  si los cuatro campos de contenido están vacíos y hace `INSERT ... ON
  CONFLICT ... DO UPDATE` en caso contrario. Confirma una vez; ante cualquier
  error revierte y siempre cierra cursor y conexión.
- Un lote vacío resuelve la asignación y confirma, pero no ejecuta ningún
  `DELETE`; un lote más corto tampoco toca los slots posteriores.
- `crear_planeador_anual_controller` y
  `actualizar_planeador_anual_controller` no tienen consumidores en `app/`.
  Contienen las otras dos sentencias y usan `get_cursor(commit=True)`.

### Línea base de consultas y conexiones

Los conteos incluyen permiso y resolutor, pero no autenticación ni los
round-trips de configuración al abrir una conexión:

| Camino | Consultas admin/profesor | Conexiones admin/profesor | Transacción |
|---|---:|---:|---|
| GET, con una o tres filas | **2 / 3** | **1 / 2** | No |
| PUT con N filas | **1+N / 2+N** | **1 / 2** | Sí, una |
| PUT vacío | **1 / 2** | **1 / 2** | Sí, confirma sin DML |
| Profesor sin ownership | **1** | **1** | No; termina en 403 |
| Otro rol | **0** | **0** | No; termina en 403 |

No hay N+1 de lectura ni de conexiones. Sí hay un **N+1 respecto del tamaño de
la entrada** en el `PUT`: una operación DML por fila, con conexiones constantes.

## Hallazgos de 7.0, registrados y sin corregir

1. **Dos de las cuatro funciones del controlador están muertas.** Crear y
   actualizar individualmente no tienen consumidor en `app/`; concentran dos
   de los cinco SQL inline.
2. **La función muerta de crear no encaja con su tipo anotado.** Accede a
   `planeador.periodo` y `planeador.slot`, pero `PlaneadorAnualCreate` no
   declara esos campos y Pydantic los descarta como extras.
3. **El esquema de respuesta también omite `periodo` y `slot`.** Hoy no se usa
   como `response_model`; añadirlo por inferencia recortaría dos campos del
   payload actual.
4. **`PUT []` responde éxito y no limpia nada.** Resuelve la asignación y hace
   commit sin ejecutar un solo `DELETE`.
5. **Un lote más corto deja slots posteriores intactos.** La operación solo
   visita las posiciones presentes; no implementa un reemplazo total.
6. **La capa HTTP no limita el lote a ocho filas.** Nueve filas válidas llegan
   al controlador, mientras el DDL rechaza `slot > 8`; una novena fila con
   contenido termina en rollback y 500, no en 422.
7. **`periodo` no tiene límites HTTP.** El `GET` acepta, por ejemplo, periodo 5
   y consulta normalmente; las restricciones 1..4 solo actúan al escribir en
   PostgreSQL.
8. **El `PUT` es `1+N` en consultas.** El número de conexiones es constante,
   pero una lista arbitrariamente larga —especialmente de filas vacías que no
   chocan con el `CHECK`— produce DML secuencial innecesario.
9. **Las dos rutas exponen el texto interno de cualquier excepción como 500 y
   no registran el fallo.** Conservado como contrato actual.
10. **Permiso y resolutor no filtran `asignaciones.activo`.** Un profesor puede
    conservar acceso si ownership e id coinciden con una asignación
    desactivada, patrón ya registrado en otros dominios.
11. **Conviven dos idiomas de recursos DB.** Tres funciones usan `get_cursor`,
    mientras el `PUT` administra conexión, cursor, commit y rollback a mano.
    Unificarlos cambiaría ownership y queda fuera de 7.0.

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 7.0 | Delimitar la frontera, inventariar contratos y caracterizar el comportamiento y la línea base | **Cerrada** el 2026-08-22 |
| 7.1 | Extraer los cinco SQL a un único repositorio conservando recursos, funciones muertas y contratos | **Pendiente y no iniciada** |
| 7.2 | Cambio adicional posterior, solo si resulta necesario y autorizado | En espera; alcance por definir |

Las subcapas se adaptan al trabajo real. Las innecesarias se marcan `No
aplica` con una explicación. Nunca se ejecutan dos en el mismo turno.

## Subcapa 7.0: trabajo exacto ejecutado y cerrado

1. Delimitar la frontera real de `planeador_anual` por entradas, llamadores,
   tablas y consumidores antes de contar o modificar nada.
2. Inventariar métodos, paths, guards, permisos, payloads, status codes,
   respuestas, orden, nulos y errores de cada entrada del dominio.
3. Inventariar archivos y contar SQL inline en rutas, controladores, servicios
   y repositorios que pertenezcan realmente a la frontera.
4. Determinar si el dominio escribe, qué tablas toca, qué transacciones abre y
   quién posee conexión, cursor, `commit` y `rollback`.
5. Identificar y fijar por prueba cálculos, fórmulas, archivos y otros efectos
   observables antes de una extracción.
6. Medir consultas y conexiones por camino, buscando N+1 y dependencia del
   tamaño de la entrada o del resultado.
7. Revisar solo las pruebas relacionadas y crear o ampliar caracterización sin
   cambiar expectativas heredadas salvo autorización explícita.
8. Resolver los diez supuestos de esta bitácora y registrar los hallazgos sin
   corregirlos.
9. Archivos modificables en 7.0: pruebas de caracterización del dominio, esta
   bitácora y el estado correspondiente del índice maestro. **Ningún archivo de
   producto se modifica.**
10. Ejecutar pruebas específicas, Ruff sobre la caracterización, la compuerta
    global, `git diff --check` y revisión de alcance.
11. Actualizar la bitácora con archivos, comandos, resultados, decisiones,
    riesgos y la siguiente acción exacta.
12. **Detenerse al cerrar 7.0. No iniciar 7.1 en el mismo turno.**

## Alcance propuesto de 7.1, no iniciado

La extracción protegida que la evidencia permite es un único
`planeador_anual_repository.py` con las cinco sentencias. Sus funciones
recibirían el cursor existente; los tres llamadores con `get_cursor` y el
`PUT` con conexión manual conservarían íntegramente la propiedad de recursos,
transacciones, resolutor, bucle, cálculos, retornos y errores.

Las dos funciones muertas **se conservarían sin reanimarlas ni corregir sus
esquemas**. Mover también sus SQL mantiene el conjunto byte a byte y evita
cerrar solo tres quintos de la persistencia; retirarlas sería otra decisión y
no forma parte de una extracción pura. Este alcance debe presentarse y
autorizarse antes de modificar producto.

## Criterios de cierre de la subcapa 7.0

- La frontera queda delimitada con evidencia y sin reabrir otros dominios.
- Los diez supuestos quedan resueltos uno por uno.
- Existe caracterización ejecutable de contratos, fórmulas, SQL,
  transacciones, consultas y conexiones aplicables.
- Pruebas específicas, Ruff, compuerta y dependencias correctas.
- `git diff --check` correcto y diff exclusivo de 7.0.
- Bitácora actualizada con resultados, decisiones, riesgos y siguiente acción.

## Criterios de cierre de la capa

- Todas las subcapas necesarias están cerradas.
- Compuerta global correcta.
- Contratos conservados o cambios explícitamente aprobados.
- Staging, rollback y verificación manual documentados.
- La capa queda cerrada y el siguiente dominio permanece en espera hasta una
  nueva orden explícita.

## Decisiones

- **Activar `planeador_anual` y solo ese dominio.** Motivo: el usuario lo
  nombró explícitamente y el índice exige trabajar uno por uno.
- **Continuar localmente aceptando las verificaciones heredadas.** El usuario
  eligió expresamente la opción 2. Ninguna se marca como cumplida.
- **Usar el `HEAD` limpio vigente como commit base.** Motivo: es el punto
  posterior al cierre y a la actualización de la verificación manual de
  `planilla`; toda su historia posterior al base anterior está explicada.
- **Activación exclusivamente documental.** No se inspecciona ni implementa
  7.0 en este turno.
- **No inferir la frontera por el nombre.** La semejanza con
  `plan_de_clases` se registra como riesgo, no como autorización para incluirlo.
- **Frontera resuelta en 7.0.** Los tres archivos con nombre anual forman el
  dominio propio; la notificación vecina se queda en `plan_de_clases`.
- **No corregir los once hallazgos.** 7.0 solo los caracteriza; no cambia
  esquemas, status codes, límites, transacciones ni funciones muertas.
- **Proponer un único repositorio para los cinco SQL en 7.1.** La extracción
  preservaría las funciones muertas y los dos idiomas de recursos. No se inicia
  sin una nueva orden.

## Riesgos

- **Frontera todavía desconocida.** El nombre del dominio puede no coincidir
  con archivos, rutas o tablas. Mitigación: delimitar por comportamiento y
  consumidores en el primer paso de 7.0.
- **Perfil de escritura desconocido.** No se sabe aún si el dominio modifica
  datos, archivos o ambos. Mitigación: resolverlo antes de decidir una
  extracción.
- **Cifras o estructura anual como contrato.** Cualquier cálculo u orden que
  aparezca debe caracterizarse antes de moverlo.
- **Verificaciones heredadas pendientes y aceptadas.** Conservan sus riesgos y
  no se consideran cumplidas por activar este dominio.
- **Posible vecindad con `plan_de_clases`.** Compartir vocabulario no demuestra
  dos usos reales ni una frontera común. 7.0 confirmó que es otro dominio y no
  lo incluyó.
- **Código muerto y esquema incompatible.** Mover o retirar las dos funciones
  sin conservar evidencia podría convertir una extracción en una corrección
  funcional. Mitigación: mantenerlas intactas en 7.1 y decidir su retiro aparte.
- **N+1 de entrada.** El `PUT` hace una operación por fila y la capa HTTP no
  limita el lote. Se conserva en 7.1; optimizarlo cambiaría los conteos fijados.

## Registro de ejecución

### 2026-08-21 — activación de la capa para `planeador_anual`

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git validado directamente.
- Documentos leídos completamente y en orden: índice maestro,
  `07_PLANILLA.md`, instrucciones locales —no se encontraron— y
  `PLANTILLA_CAPA.md`.
- Autorización: el usuario eligió la opción 2, aceptó continuar localmente con
  las verificaciones heredadas pendientes y nombró «planeador anual».
- Rama acordada y observada: `main`.
- Estado antes de escribir: árbol limpio; `git status --porcelain=v1` produjo
  salida vacía.
- Commit base: `235672ea609444a46003175940376c37bfe191c4`, el `HEAD`
  limpio vigente.
- Continuidad: `580c0ad`, base de `planilla`, es ancestro de `HEAD`. Sus seis
  descendientes corresponden a `50d6d41` —activación—, `e8e3336` —7.0—,
  `5019fd2` —7.1—, `838b71b` —cierre—, `485ed78` —registro documental de la
  verificación manual— y `235672e` —ajuste final del índice sobre esa misma
  verificación—. Todos pertenecen a la continuidad descrita en la bitácora.
- Estado de publicación observado localmente: `HEAD` y la referencia local
  `origin/main` coinciden en `235672e`, con cero commits a favor o en contra.
  No se consultó el remoto real ni se verificó GitHub Actions.
- Decisión heredada: las verificaciones pendientes continúan aceptadas con su
  riesgo y ninguna se marca como cumplida.
- Archivos creados o modificados: esta bitácora y
  `docs/modularizacion/README.md`.
- Código de producto, pruebas, consultas, migraciones, esquemas, configuración
  y dependencias inspeccionados o modificados: **ninguno**.
- Pruebas, conexiones a PostgreSQL, acceso a producción, commit, push y deploy:
  **ninguno**.
- Verificación documental: `git diff --check` terminó en exit 0 para el archivo
  rastreado; la comprobación `--no-index --check` de esta bitácora nueva no
  reportó errores de whitespace —su exit 1 indica que el archivo difiere de
  `NUL`—. Los avisos fueron únicamente de normalización futura LF/CRLF.
  `git status --short` mostró exactamente esta bitácora nueva y el índice
  maestro modificado. La tabla del índice contiene exactamente una fila
  marcada **Activa**, la de `planeador_anual`.
- Siguiente acción exacta: ejecutar únicamente 7.0 conforme al trabajo exacto
  de esta bitácora y detenerse antes de 7.1.

### 2026-08-22 — cierre de 7.0

- Modo de acceso: mismo checkout local; rama `main` y árbol limpio antes de
  modificar, comprobado con `git status --porcelain=v1` sin salida.
- `HEAD` observado: `6358c5a39c051b6c4e75f09beda531ac550b815f`.
  El commit base `235672e` es ancestro y el único descendiente contiene
  exactamente la bitácora de activación y el índice, tal como está explicado.
- Archivos inspeccionados sin modificar: los tres archivos propios; las pruebas
  heredadas; el montaje del router; únicamente las funciones compartidas de
  permiso y resolución, el DDL de la tabla y los fragmentos con nombre
  `planeadores` necesarios para separar `plan_de_clases`. No se leyó el resto
  del repositorio.
- Archivos modificados: `tests/test_planeador_anual_caracterizacion.py` —nuevo—,
  esta bitácora y el estado de 7.0 en el índice maestro. **Ningún archivo de
  producto fue modificado.**
- Pruebas antes: ocho casos heredados. Cubrían normalización, validación,
  transacciones básicas y las tres funciones migradas a `get_cursor`, pero no
  frontera, HTTP real, DDL, conteos, ownership denegado, lote vacío o esquemas
  incompletos.
- Cambio realizado: **solo caracterización**. Veintinueve casos nuevos fijan
  frontera, dos contratos HTTP por ASGI, permisos, status codes, payloads,
  cinco SQL, DDL, transacciones, rollback, recursos y conteos.
- Compuerta heredada: el intento dentro del sandbox terminó con 928 pruebas
  pasadas y 29 errores de setup por `PermissionError` sobre el temporal de
  pytest. Repetida fuera del sandbox, sin cambiar archivos: **957 pruebas,
  exit 0**, Ruff correcto y `pip check` íntegro.
- Comandos y resultados:
  - caracterización nueva: **29 pasaron**;
  - caracterización más las ocho heredadas: **37 pasaron**;
  - Ruff sobre el archivo nuevo: **correcto**;
  - compuerta final: **986 pruebas, 5 warnings heredadas, exit 0**, Ruff
    correcto y `pip check` íntegro;
  - `git diff --check`: exit 0; la comprobación `--no-index --check` del archivo
    de prueba nuevo no reportó errores de whitespace —su exit 1 indica que
    difiere de `NUL`—; los avisos son solo de normalización futura LF/CRLF;
  - revisión de alcance: exactamente la caracterización nueva, esta bitácora y
    el índice maestro; ningún archivo de producto.
- Los diez supuestos quedaron resueltos: seis confirmados, uno confirmado con
  matiz, dos refutados y uno mixto.
- Riesgos: permanecen los once hallazgos, encabezados por las funciones muertas
  incompatibles con sus esquemas, el falso reemplazo de lotes vacíos o cortos y
  el `1+N` de escrituras.
- Siguiente acción exacta: presentar y autorizar el alcance propuesto de 7.1;
  no iniciar la extracción en este turno.

## Entrega al próximo chat

- Capa activa: **7 para `planeador_anual`**.
- Última capa cerrada: **7 para `planilla`**.
- Última subcapa terminada: **7.0**, cerrada el 2026-08-22.
- Primera subcapa pendiente: **7.1**, no iniciada.
- Código de producto modificado en 7.0: ninguno; se añadió solo
  caracterización.
- Frontera actual: tres archivos propios, dos entradas HTTP, un modelo de
  permiso, cinco SQL inline, una tabla escrita y un `1+N` respecto del lote.
- Pruebas: 29 nuevas, 37 específicas y compuerta final con **986 pruebas**.
- Verificaciones heredadas: pendientes y aceptadas por decisión explícita.
- Bloqueos: ninguno.
- Siguiente acción exacta: autorizar o ajustar 7.1 para extraer los cinco SQL a
  un único repositorio conservando recursos, funciones muertas y contratos.
