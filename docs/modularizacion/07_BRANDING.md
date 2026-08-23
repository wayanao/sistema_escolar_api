# Capa 7: branding

Última revisión: 2026-08-22.

## Control

- Estado: **Cerrada** el 2026-08-22 por orden explícita del usuario.
- Commit base: `bb34cf6f31413fdbbd2c1866b43f2da71f8ea03b`.
- Rama acordada: `main`.
- Primera subcapa pendiente: **Ninguna**. 7.2 y 7.3 son **No aplica**.
- Código de producto modificado al activar: **Ninguno**.
- Código de producto modificado en 7.0: **Ninguno**. El diff funcional es un
  solo archivo nuevo de caracterización; los demás cambios son documentación.
- Código de producto modificado en 7.1: el controlador propio y el nuevo
  `branding_repository`; no se modificaron rutas, schemas, storage, migraciones
  ni otros dominios.
- Commit de 7.1: `5ddd50470875f4740581897708e90804d079d2f2`.
- Dominio de esta capa: **`branding`, y solo ese**. `profesores` y
  `super_admin` siguen en espera.
- Autorización: el usuario nombró `branding`, ordenó activarlo y, después de
  recibir la advertencia, confirmó continuar localmente aceptando que las
  verificaciones heredadas permanezcan pendientes.
- La activación fue exclusivamente documental. Las órdenes posteriores
  autorizaron 7.0 y 7.1 por separado; ninguna autoriza commit, push, deploy,
  migraciones reales ni acceso a producción.
- El cierre no activa otro dominio. `profesores` y `super_admin` permanecen en
  espera y requieren una orden nueva que nombre uno de ellos.

## Objetivo

Migrar el dominio de **branding** con contratos y pruebas, conservando su
comportamiento observable actual.

El índice maestro fija tres condiciones para esta capa:

1. trabajar **un dominio a la vez**;
2. agregar `response_model`, errores de dominio y pruebas HTTP o de integración
   solo después de caracterizar y conservar la respuesta existente;
3. no crear abstracciones compartidas sin dos consumidores reales.

La activación no inspecciona código ni infiere la frontera. La subcapa 7.0 debe
delimitarla con evidencia antes de proponer cualquier extracción.

## Dependencias de capas anteriores

- La capa 7 para `plan_de_clases` está cerrada: 7.0 y 7.1 completas, 7.2 y
  7.3 **No aplica**, compuerta final con **1011 pruebas**, Ruff correcto y
  dependencias íntegras.
- La verificación manual de `plan_de_clases` está completada de forma global
  con la reserva «aparentemente bien», sin entorno, artefacto ni desglose punto
  por punto.
- El commit base de esta capa es el `HEAD` limpio vigente,
  `bb34cf6f31413fdbbd2c1866b43f2da71f8ea03b`.
- Los cinco commits posteriores al base de `plan_de_clases` están explicados en
  su bitácora: `31b3f6b` activa la capa, `80f7f21` contiene 7.0, `98c438f`
  contiene 7.1, `d6eeecf` contiene el cierre documental y `bb34cf6` registra
  la verificación manual posterior. El último modifica únicamente la bitácora
  y el índice maestro, como declara ese registro.
- La referencia local `origin/main` coincide con el commit base. No se consultó
  el remoto real ni se atribuye publicación, despliegue o GitHub Actions.
- Siguen pendientes, sin marcarse como cumplidas: la calibración operativa
  final de `DB_STATEMENT_TIMEOUT_MS`; evidencia de GitHub Actions posterior a
  la capa 0; pasos manuales no confirmados heredados de `ventas`, `asistencia`,
  `boletin` y `observaciones`; y la rotación de la credencial privilegiada
  registrada en la capa 4.

## Supuestos documentales resueltos en 7.0

Los seis supuestos de la activación quedaron resueltos: **cuatro confirmados y
dos confirmados con matiz**.

| # | Supuesto documental | Resultado de 7.0 |
|---:|---|---|
| 1 | `branding` es una frontera pendiente y separable | **CONFIRMADO CON MATIZ.** Tiene tres archivos propios y cuatro rutas, pero el endpoint compartido `/uploads` sirve sus logos y `super_admin_controller.py` inserta la fila inicial al crear un tenant |
| 2 | Usa `app/services/storage.py` | **CONFIRMADO.** Branding guarda y elimina objetos; el servicio también lo consumen `plan_de_clases_controller.py` y `main.py` |
| 3 | La subida async descarga storage y DB a un worker preservando tenant | **CONFIRMADO.** Lee el `UploadFile` antes del offload y ejecuta save, URL, DB y limpieza dentro de `run_in_threadpool`; las pruebas heredadas demuestran workers concurrentes, `ContextVar` aislado y espera ante cancelación |
| 4 | Contratos, SQL, recursos y efectos estaban por determinar | **CONFIRMADO COMO TRABAJO Y RESUELTO.** El inventario y los conteos quedan fijados más abajo |
| 5 | Cantidad y ubicación de archivos, rutas, pruebas, consumidores y persistencia estaban por determinar | **CONFIRMADO COMO TRABAJO Y RESUELTO.** Son tres archivos propios, cuatro rutas propias más `/uploads`, siete SQL inline, dos consumidores compartidos directos y un escritor externo |
| 6 | Escrituras y posible N+1 no estaban verificados | **CONFIRMADO CON MATIZ.** Escribe una tabla y almacenamiento local o R2/S3; no hay N+1 de aplicación, pero sí dos conexiones constantes en el PUT |

## Inventario y contratos fijados en 7.0

La frontera propia tiene **tres archivos y 246 líneas**. No existe un
`branding_repository` y los **siete sitios `cursor.execute`** viven en el
controlador.

| Archivo | Líneas | SQL ejecutado | Responsabilidad |
|---|---:|---:|---|
| `app/routes/branding.py` | 36 | 0 | Cuatro entradas HTTP, autenticación, admin y multipart |
| `app/controllers/branding_controller.py` | 181 | 7 | Lectura, actualización, logos, DB, storage y offload |
| `app/schemas/branding.py` | 29 | 0 | Entrada permisiva y un esquema de respuesta no usado |

Participan además piezas compartidas relacionadas: `app/services/storage.py`
—150 líneas, local o R2/S3—; el acceso `/uploads/{file_path:path}` de
`app/main.py`; `get_current_user` y `get_current_active_admin`; `get_cursor` y
el `ContextVar` del tenant. `super_admin_controller.py` es un consumidor
externo: inserta una fila vacía al crear un tenant. La frontera no autoriza
modificarlo.

### Resultado de la extracción 7.1

La frontera propia queda en **cuatro archivos y 268 líneas**. Los siete usos
SQL originales salieron del controlador y viven en seis operaciones del nuevo
repositorio; la lectura de la columna de logo es una única operación con dos
consumidores reales —subida y borrado—. El controlador conserva
`get_cursor(commit=True)`, serialización, defaults, ensamblado de respuestas,
tenant, offload y todos los efectos de storage.

| Archivo | Líneas | SQL ejecutado | Responsabilidad tras 7.1 |
|---|---:|---:|---|
| `app/routes/branding.py` | 36 | 0 | Cuatro entradas HTTP, autenticación, admin y multipart |
| `app/controllers/branding_controller.py` | 137 | 0 | Orquestación, recursos, respuestas, logos, storage y offload |
| `app/repositories/branding_repository.py` | 66 | 6 | Siete usos originales: lectura/creación, actualización y operaciones de logo |
| `app/schemas/branding.py` | 29 | 0 | Entrada permisiva y un esquema de respuesta no usado |

El texto SQL, los parámetros y los retornos quedaron fijados literalmente en
la caracterización antes de mover producto. Los consumidores directos de la
tabla son ahora el repositorio y el escritor externo de `super_admin`; los
conteos de consultas, conexiones y almacenamiento no cambiaron.

### Entradas HTTP, permisos y respuestas

Ninguna entrada declara `response_model`. Las cuatro rutas propias requieren
usuario autenticado y tres exigen además admin activo:

| Método | Path | Permiso observable | Respuesta o efecto principal |
|---|---|---|---|
| GET | `/branding` | Cualquier usuario autenticado | Objeto de 14 campos; si no hay fila, la crea y devuelve valores por defecto |
| PUT | `/branding` | Admin activo | Actualiza la primera fila y la relee en otra conexión |
| POST | `/branding/logo` | Admin activo | Guarda logo principal o secundario y devuelve `{"url": ..., "slot": ...}` |
| DELETE | `/branding/logo` | Admin activo | Limpia el slot y devuelve `{"mensaje": "Logo eliminado", "slot": ...}` |
| GET | `/uploads/{file_path:path}` | Usuario autenticado del mismo tenant | Sirve el logo local o remoto; no exige admin |

La interfaz ASGI fijó 200 para lectura y actualización válidas, 403 para una
mutación como profesor, 422 para un cuerpo JSON incompatible y 400 para un
slot inválido. Las validaciones de logo producen 400 por slot, MIME, extensión
o tamaño; autenticación puede producir 401 y `/uploads` 403 o 404. Las rutas no
capturan fallos inesperados del controlador, DB o proveedor.

### Persistencia, conexiones, concurrencia y almacenamiento

- La tabla propia es `institucion_branding`. El DDL tiene clave primaria, pero
  **no impone una sola fila** ni declara `NOT NULL` en los campos de negocio;
  el seed `WHERE NOT EXISTS` no sustituye esa restricción.
- Las siete sentencias son: lectura e inserción inicial; actualización de datos;
  y dos pares dinámicos de lectura/actualización de la columna del logo. Los
  nombres dinámicos solo pueden ser los dos slots validados.
- Todos los bloques usan `get_cursor(commit=True)`: el context manager posee
  conexión, cursor, commit, rollback y cierre.
- GET usa **1 conexión y 1 consulta** con fila, o **1 y 2** si debe insertarla.
- PUT usa **2 conexiones y 2 consultas** con fila, o **2 y 3** si no existía.
- POST de logo usa **1 conexión y 2 consultas**, una escritura de archivo y
  hasta un borrado posterior. DELETE usa **1 conexión y 2 consultas** más un
  borrado posterior.
- No hay `execute` dentro de bucles: **no existe N+1 de aplicación** en
  consultas, conexiones ni operaciones de almacenamiento.
- La subida conserva el límite async/síncrono: validaciones y lectura del
  `UploadFile` ocurren antes de `run_in_threadpool`; save, URL, DB y borrado
  posterior corren en un worker con el tenant preservado.
- El key es `branding/{tenant}/logo_{slot}_{uuid}{ext}` y la URL observable es
  `/uploads/...`. La validación acepta PNG/JPEG/WebP hasta 2 MiB según MIME y
  extensión declarados.
- `/uploads` comprueba primero existencia y después tenant. En local no abre DB;
  en remoto puede hacer HEAD y luego GET. El handler es síncrono y FastAPI lo
  descarga a su threadpool.

## Hallazgos registrados en 7.0; ninguno corregido

1. **El GET escribe.** `GET /branding` abre una transacción con commit e inserta
   una fila si no existe; no es una lectura pura.
2. **La unicidad de la fila es solo una convención.** El DDL no impide varias
   filas y todo el dominio elige la primera por `ORDER BY id ASC LIMIT 1`.
3. **El PUT puede perder silenciosamente la entrada.** Si no existe fila, el
   `UPDATE` afecta cero registros; la relectura crea una fila vacía y responde
   200 con defaults, no con los datos enviados.
4. **La subida puede responder éxito sin asociar el logo.** Sin fila previa,
   guarda el archivo, el `UPDATE` afecta cero registros y devuelve la URL sin
   comprobar `rowcount`.
5. **DB y almacenamiento no comparten transacción.** Un fallo DB posterior al
   save deja el objeto nuevo huérfano. Tras confirmar DB, el borrado anterior
   puede fallar y `delete_file` absorbe el error; DELETE puede responder éxito
   dejando el archivo.
6. **La validación confía en declaraciones del cliente.** No inspecciona la
   firma del contenido y lee el archivo completo antes de aplicar el límite de
   2 MiB.
7. **`/uploads` revela existencia antes de autorizar.** Un path ajeno existente
   produce 403 y uno inexistente 404 porque el filesystem o proveedor se
   consulta antes de comprobar el tenant.
8. **El PUT no relee dentro de la transacción de escritura.** Confirma y abre
   una segunda conexión; una escritura concurrente puede cambiar lo que devuelve.
9. **Esquema y DDL son permisivos.** Email y colores no validan formato, los
   textos no tienen límites Pydantic y casi todos los campos admiten nulos en
   DB; el esquema normaliza algunos nulos solo al ensamblar la respuesta.
10. **Ninguna ruta usa `response_model`.** La clase `Branding` existe pero no
    protege ninguna respuesta; POST y DELETE tienen formas distintas.
11. **Los errores son heterogéneos.** Hay 400 propios y 422 de Pydantic, pero
    fallos inesperados de DB/storage se propagan; algunos borrados fallidos se
    silencian completamente.
12. **La tabla tiene un escritor fuera de la frontera.** El alta de tenant en
    `super_admin_controller.py` inserta la fila inicial y debe quedar protegida
    por la compuerta global si se extrae persistencia.
13. **Eliminar sin fila responde éxito.** Ejecuta SELECT y UPDATE, solicita
    `delete_file(None)` y devuelve «Logo eliminado» sin comprobar afectación.

Los trece hallazgos quedan registrados sin cambiar producto, expectativas ni
base de datos.

## Alcance autorizado

- Trabajar únicamente en el dominio `branding`.
- En 7.0, delimitar primero su frontera por rutas, llamadores, tablas,
  consumidores y efectos de almacenamiento, no solo por nombres de archivo.
- Inventariar entradas HTTP, permisos, ownership, tenant, payloads, status
  codes, respuestas, SQL, transacciones, conexiones, archivos y demás efectos
  laterales.
- Resolver uno por uno los supuestos documentales con evidencia.
- Agregar caracterización antes de cualquier extracción importante.
- Medir consultas, conexiones y operaciones de almacenamiento críticas antes
  y después de cualquier cambio de producto posterior.

## Fuera de alcance

- `profesores` y `super_admin`, que siguen en espera.
- Reabrir por inferencia `plan_de_clases` u otro dominio cerrado.
- Corregir hallazgos abiertos de las capas 1 a 7 o completar verificaciones
  heredadas dentro de esta activación.
- Cambiar rutas, payloads, status codes, permisos, roles, ownership, tenant,
  SQL observable, transacciones, archivos o comportamiento actual sin una
  autorización explícita apoyada en la caracterización.
- Cambiar PostgreSQL, `psycopg2`, schemas tenant, pool, timeouts, concurrencia,
  ORM, driver o proveedor de almacenamiento.
- Migraciones reales, acceso a producción, DDL, DML, deploy, commit o push.

## Invariantes

- Métodos, paths, status codes y forma exacta de las respuestas permanecen
  idénticos, incluidos orden, nulos y errores.
- Permisos, roles, ownership y aislamiento entre tenants se conservan.
- SQL, parámetros, número y orden observable de operaciones y límites de
  transacción se conservan.
- Se conserva quién posee conexión, cursor, `commit`, `rollback`, archivos y
  efectos de almacenamiento.
- Ninguna operación DB o de almacenamiento síncrona vuelve al event loop ni se
  altera la propagación del tenant sin caracterización y autorización.
- No se crea una abstracción compartida sin dos consumidores reales.

## Línea base

| Comprobación | Comando | Resultado |
|---|---|---|
| Pruebas específicas heredadas | `pytest` sobre controlador, upload boundary y permisos de uploads | **31 passed**, 5 warnings heredados |
| Compuerta heredada | `.\venv\Scripts\python.exe scripts\verify.py` | **1011 passed**, Ruff correcto, dependencias íntegras |
| Caracterización nueva | `pytest tests\test_branding_caracterizacion.py` | **19 passed**, 5 warnings heredados |
| Pruebas específicas finales | Las cuatro suites relacionadas | **50 passed**, 5 warnings heredados |
| Ruff de la caracterización | `.\venv\Scripts\python.exe -m ruff check tests\test_branding_caracterizacion.py` | **All checks passed** |
| Compuerta final | `.\venv\Scripts\python.exe scripts\verify.py` | **1030 passed**, Ruff correcto, dependencias íntegras |
| Línea base de 7.1 | Las cuatro suites relacionadas | **50 passed**, 5 warnings heredados |
| Señal previa a la extracción | `pytest tests\test_branding_caracterizacion.py -q` | **3 failed, 18 passed**; fallos esperados por siete SQL inline y repositorio ausente |
| Pruebas específicas de 7.1 | Las cuatro suites relacionadas | **52 passed**, 5 warnings heredados |
| Ruff de 7.1 | Ruff sobre controlador, repositorio y caracterización de branding | **All checks passed** |
| Compuerta de 7.1 | `.\venv\Scripts\python.exe scripts\verify.py` | **1032 passed**, Ruff correcto, dependencias íntegras |

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 7.0 | Inventario, contratos, almacenamiento y caracterización | **Cerrada el 2026-08-22** |
| 7.1 | Extracción protegida de los siete usos SQL a un repositorio sin recursos | **Cerrada el 2026-08-22** |
| 7.2 | Segunda extracción o cambio de contrato | **No aplica por cierre como refactorización pura** |
| 7.3 | Retiro heredado adicional | **No aplica; no existe retiro autorizado** |

Las subcapas se adaptan al trabajo real. Las innecesarias se marcan `No aplica`
con una explicación; nunca se ejecutan dos sin orden explícita.

## Subcapa cerrada: trabajo ejecutado en 7.0

1. Delimitar la frontera real de `branding` por entradas, llamadores, tablas,
   consumidores y efectos de almacenamiento antes de contar o modificar nada.
2. Inspeccionar únicamente la documentación, fuentes y pruebas relacionadas
   con esa frontera.
3. Inventariar métodos, paths, guards, permisos, payloads, status codes,
   respuestas, orden, nulos y errores de cada entrada.
4. Inventariar SQL inline y delegado, tablas, transacciones, propiedad de
   conexión/cursor y operaciones locales o remotas de almacenamiento.
5. Comprobar el límite async/síncrono, el offload y la propagación del tenant
   sin cambiar la concurrencia.
6. Medir consultas, conexiones y operaciones de almacenamiento por camino,
   buscando dependencia del tamaño de entrada o resultado.
7. Revisar solo las pruebas relacionadas y agregar caracterización sin cambiar
   expectativas heredadas.
8. Resolver los seis supuestos documentales y registrar hallazgos sin
   corregirlos.
9. Archivos modificables en 7.0: pruebas de caracterización del dominio, esta
   bitácora y el índice maestro. **Ningún archivo de producto se modifica.**
10. Ejecutar pruebas específicas, Ruff sobre la caracterización, la compuerta
    global, `git diff --check` y revisión de alcance.
11. Actualizar esta bitácora con archivos, comandos, resultados, decisiones,
    riesgos y la siguiente acción exacta.
12. **Detenerse al cerrar 7.0. No iniciar 7.1 en el mismo turno.**

## Criterios de cierre de 7.0

Todos quedaron cumplidos:

- La frontera queda delimitada con evidencia y sin reabrir otros dominios.
- Los seis supuestos quedan resueltos uno por uno.
- Existe caracterización ejecutable de contratos, SQL, transacciones,
  consultas, conexiones, archivos y efectos laterales aplicables.
- Pruebas específicas, Ruff, compuerta y dependencias correctas.
- `git diff --check` correcto y diff exclusivo de 7.0.
- Bitácora actualizada con resultados, decisiones, riesgos y siguiente acción.

## Subcapa cerrada: trabajo ejecutado en 7.1

1. Agregar primero guards finales del repositorio para texto SQL, parámetros,
   retornos, superficie, ubicación y ausencia de propiedad de recursos.
2. Confirmar la señal roja esperada antes de modificar producto.
3. Crear un único `branding_repository` con seis operaciones que representan
   los siete usos SQL originales; reutilizar la lectura de logo solo porque
   tiene dos consumidores reales.
4. Sustituir los siete `cursor.execute` del controlador sin mover
   `get_cursor(commit=True)`, serialización JSON, defaults, tenant, offload,
   storage, orden de efectos ni respuestas.
5. Conservar literalmente consultas y parámetros, y mantener constantes los
   conteos de conexiones, consultas y operaciones de almacenamiento.
6. Actualizar únicamente los cinco guards globales que enumeran de forma
   deliberada el conjunto exacto de repositorios.
7. Ejecutar las pruebas específicas, Ruff, compuerta global,
   `git diff --check` y revisión de alcance.
8. Actualizar bitácora e índice y detenerse antes de 7.2.

## Criterios de cierre de 7.1

Todos quedaron cumplidos:

- El controlador no contiene SQL y el repositorio no abre ni cierra recursos.
- Consultas, parámetros, retornos, orden y efectos permanecen caracterizados.
- Las cuatro suites específicas terminan con **52 passed**.
- La compuerta global termina con **1032 passed**, Ruff correcto y dependencias
  íntegras.
- `git diff --check` es correcto y el diff pertenece exclusivamente a 7.1.
- La bitácora registra resultados, decisiones, riesgos y siguiente acción.

## Punto de decisión resuelto: 7.2 y 7.3 No aplica

La primera extracción ya agotó la separación arquitectónica justificada: el
repositorio posee SQL y el controlador conserva recursos y orquestación. Los
trece hallazgos siguen vivos porque corregir cualquiera alteraría comportamiento
o ampliaría alcance. El usuario ordenó **«cierra branding»** y eligió cerrar la
capa como refactorización pura. No se agrega `response_model`, no se introducen
errores de dominio y no se corrige ningún hallazgo. 7.2 y 7.3 quedan **No
aplica**, sin haberse iniciado.

## Criterios de cierre de la capa

Todos quedaron cumplidos para el cierre documental:

- Todas las subcapas necesarias están cerradas; 7.2 y 7.3 son `No aplica`.
- Compuerta global correcta con **1032 passed**, Ruff correcto y dependencias
  íntegras sobre el commit limpio de 7.1.
- Contratos conservados; no se autorizó ni aplicó ningún cambio observable.
- Staging, rollback y verificación manual están documentados más abajo. La
  verificación manual propia permanece pendiente y no se marca como cumplida.
- La capa queda cerrada y los dos dominios siguientes permanecen en espera.

## Decisiones

- **Activar `branding` y solo ese dominio.** El usuario lo nombró y después
  ordenó activarlo explícitamente.
- **Continuar localmente con las verificaciones heredadas pendientes.** El
  usuario confirmó la alternativa después de recibir la advertencia; ninguna
  verificación se considera cumplida y sus riesgos permanecen vigentes.
- **Usar el `HEAD` limpio vigente como commit base.** Es el punto posterior al
  cierre y al registro de verificación manual de `plan_de_clases`; todos sus
  descendientes desde el base anterior están explicados.
- **Activación exclusivamente documental.** No se inspecciona ni implementa
  7.0 en este turno.
- **No inferir la frontera por nombres o referencias heredadas.** Los datos
  previos se registran como supuestos que 7.0 debe contrastar.
- **Ejecutar solo 7.0 por la orden «continua».** La subcapa agrega
  caracterización y documentación, sin cambios de producto ni inicio de 7.1.
- **Incluir `/uploads` y el storage en la frontera observable, pero no como
  archivos propios.** Ambos afectan el ciclo de vida y acceso de los logos;
  `super_admin_controller.py` queda registrado únicamente como escritor externo.
- **Conservar las 31 pruebas heredadas.** Ya protegen el orden storage/DB, el
  offload, la cancelación y el tenant; los 19 casos nuevos cubren los huecos sin
  cambiar una sola expectativa previa.
- **No corregir los trece hallazgos.** La ausencia de fila, unicidad, validación
  de contenido, autorización de uploads, response models, errores y
  compensaciones quedan fuera de una subcapa de inventario.
- **Al cerrar 7.0, dejar 7.1 sujeta a una orden nueva.** La evidencia permitió
  proponer la extracción, pero no autorizó producto hasta la orden posterior.
- **Ejecutar solo 7.1 por la nueva orden «continua».** No se inicia 7.2 ni se
  corrige ningún hallazgo.
- **Mantener los recursos en el controlador.** El repositorio recibe cursor y
  no conoce conexión, commit, rollback, cierre, tenant, threadpool ni storage.
- **Representar siete usos con seis operaciones.** La lectura de logo se
  comparte entre subida y borrado porque tiene exactamente dos usos reales;
  las otras cinco operaciones reflejan una sentencia cada una.
- **Fijar SQL y parámetros antes de extraer.** La caracterización falló primero
  por el estado previo y después protegió byte a byte las consultas movidas.
- **Conservar la severidad de los guards globales.** Los cinco inventarios del
  conjunto exacto se actualizaron para reconocer `branding_repository`; no se
  relajó ninguna aserción.
- **Dejar 7.2 como decisión explícita.** No hay una segunda extracción necesaria
  demostrada; cerrar como refactorización pura o cambiar un contrato requiere
  una orden posterior.
- **Cerrar `branding` como refactorización pura.** La orden explícita «cierra
  branding» resuelve el punto de decisión: 7.2 y 7.3 son `No aplica`.
- **No convertir los hallazgos en alcance de cierre.** `response_model`, errores
  de dominio, unicidad, ausencia de fila, validación de contenido y compensación
  DB/storage siguen sin cambios y no se presentan como deuda comprometida de
  esta capa.
- **No activar el siguiente dominio.** `profesores` y `super_admin` siguen en
  espera hasta que el usuario nombre uno explícitamente.

## Riesgos

- **Verificaciones heredadas pendientes.** Se aceptó continuar sin cerrarlas;
  conservan su riesgo y esta capa no puede presentarlas como cumplidas.
- **Almacenamiento con efectos externos.** Save ocurre antes de DB y los
  borrados después del commit; no hay transacción compartida ni compensación
  para un save seguido de fallo DB, y los errores de delete se absorben.
- **Límite async/síncrono y tenant.** El camino POST está correctamente
  protegido y 7.1 no movió `_guardar_logo_leido` fuera de su offload; un cambio
  posterior aún podría bloquear el event loop o perder el `ContextVar`.
- **Frontera compartida.** `/uploads`, `storage.py` y el insert de alta de tenant
  son consumidores externos que una prueba limitada a la frontera propia no
  protegería.
- **Integridad de fila débil.** DDL y controladores permiten ausencia o
  duplicados; los éxitos silenciosos medidos pueden producir datos o archivos
  no asociados.
- **Señal de autorización observable.** `/uploads` distingue 403 de 404 después
  de comprobar existencia, lo que revela si un path ajeno existe.
- **Publicación no comprobada contra el remoto real.** Al cerrar, la referencia
  local `origin/main` está tres commits por detrás de `HEAD`; no se consultó el
  remoto real ni se atribuye push, despliegue o GitHub Actions.

## Staging, rollback y verificación manual

### Staging propuesto; no ejecutado

1. Desplegar en un entorno no productivo el commit que contenga
   `5ddd50470875f4740581897708e90804d079d2f2` y el cierre documental.
2. Usar un tenant desechable con una fila de `institucion_branding` y logos de
   prueba; no reutilizar credenciales ni objetos de producción.
3. Verificar GET y PUT de `/branding`, incluidos el payload de 14 campos, los
   defaults y los permisos de usuario frente a admin.
4. Subir, reemplazar y eliminar ambos slots de logo; comprobar URL servida,
   aislamiento por tenant y el orden observable storage/DB.
5. Verificar los caminos caracterizados de fila ausente sin reinterpretarlos
   como correctos: creación implícita por GET, PUT que devuelve defaults, upload
   no asociado y DELETE exitoso.
6. Confirmar 400 por slot/MIME/extensión/tamaño inválidos, 403 en mutaciones sin
   admin y la distinción heredada 403/404 de `/uploads` ajenos.

Estos pasos no se ejecutaron en esta sesión y no autorizan deploy ni acceso a
producción.

### Rollback

- Punto anterior a la extracción de producto:
  `008323712bc686644d361195974f7337e1414eef`.
- Mientras los commits sigan solo locales, el usuario puede descartar o revertir
  `5ddd504` mediante su flujo Git habitual. Este asistente no ejecuta esa acción.
- Si 7.1 se publica, el rollback exige crear y publicar un revert de `5ddd504`,
  seguido del despliegue correspondiente; no basta cambiar archivos locales.
- No hay migraciones, DDL ni datos de backfill que revertir. Los logos o cambios
  de branding creados por pruebas manuales son efectos de negocio normales y
  deben limpiarse explícitamente en el tenant de staging si se desean retirar.

### Verificación manual propia

- Estado: **Pendiente**.
- No consta ejecución en local, staging ni despliegue para esta capa.
- La compuerta automática no sustituye la comprobación manual de GET/PUT,
  ciclo de logos, permisos, tenant y storage descrita arriba.
- Las verificaciones heredadas continúan pendientes y ninguna se marca como
  cumplida por este cierre.

## Registro de ejecución

### 2026-08-22 — activación de la capa para `branding`

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git y commits locales
  validados directamente.
- Documentos leídos completamente y en orden: índice maestro,
  `07_PLAN_DE_CLASES.md`, instrucciones locales —no se encontraron— y
  `PLANTILLA_CAPA.md`.
- Autorización: el usuario nombró `branding`, ordenó activarlo y confirmó
  continuar localmente aceptando las verificaciones heredadas pendientes.
- Rama acordada y observada: `main`.
- Estado antes de escribir: árbol limpio; `git status --porcelain=v1 --branch`
  mostró únicamente `## main...origin/main`.
- Commit base: `bb34cf6f31413fdbbd2c1866b43f2da71f8ea03b`, el `HEAD`
  limpio vigente y coincidente con la referencia local `origin/main`.
- Continuidad: el base `bfe80d4` de `plan_de_clases` es ancestro. Sus cinco
  descendientes son `31b3f6b` —activación—, `80f7f21` —7.0—, `98c438f`
  —7.1—, `d6eeecf` —cierre documental— y `bb34cf6` —registro de la
  verificación manual—. Todos están explicados en esa bitácora; el último toca
  únicamente esa bitácora y el índice, como declara su registro.
- Estado de publicación observado localmente: `HEAD` y la referencia local
  `origin/main` coinciden. No se consultó el remoto real ni se verificó GitHub
  Actions.
- Decisión heredada: permanecen pendientes la calibración de timeout, la
  evidencia de CI, los pasos manuales no confirmados y la rotación de la
  credencial privilegiada. El usuario aceptó continuar con sus riesgos.
- Archivos creados o modificados: esta bitácora y
  `docs/modularizacion/README.md`.
- Código de producto, pruebas, consultas, migraciones, esquemas, configuración
  y dependencias inspeccionados o modificados: **ninguno**.
- Pruebas, conexiones a PostgreSQL, acceso a producción, commit, push y deploy:
  **ninguno**.
- Verificación documental: `git diff --check` terminó en exit 0 para el índice;
  `git diff --no-index --check -- NUL docs/modularizacion/07_BRANDING.md` no
  reportó errores de whitespace —su exit 1 indica que el archivo nuevo difiere
  de `NUL`—. Los avisos fueron únicamente de normalización futura LF/CRLF.
- Revisión de alcance: `git status --short --branch` mostró exactamente el
  índice modificado y esta bitácora nueva sobre `main...origin/main`. La tabla
  del índice contiene una sola fila **Activa** y el conjunto de bitácoras una
  sola declaración de estado **Activa**, ambas para `branding`.
- Siguiente acción exacta: ejecutar únicamente 7.0 conforme al trabajo exacto
  de esta bitácora y detenerse antes de 7.1.

### 2026-08-22 — cierre de la subcapa 7.0

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git y commits locales
  validados directamente.
- Autorización: la orden «continua» habilitó únicamente la primera subcapa
  pendiente, 7.0.
- Precondiciones antes de modificar: rama `main`; árbol limpio según
  `git status --porcelain=v1 --branch`, que mostró
  `## main...origin/main [ahead 1]`; `HEAD`
  `f53711bbbe84977ed2e13279e655584a299807cc`; el commit base
  `bb34cf6f31413fdbbd2c1866b43f2da71f8ea03b` es ancestro.
- Continuidad desde el base: existe un solo commit posterior, `f53711b`
  (`feat(branding): add initial documentation and activate branding domain`).
  Su diff crea esta bitácora y modifica el índice maestro, exactamente como
  registra la activación. No había commits locales sin explicar.
- Estado de publicación observado: la referencia local `origin/main` está un
  commit por detrás. No se consultó el remoto real, no hubo push y no se
  atribuye GitHub Actions.
- Fuentes inspeccionadas: los tres archivos propios; `storage.py`; el montaje,
  autorización y servicio de `/uploads`; dependencias, `get_cursor` y
  `ContextVar` relacionados; el insert externo de alta de tenant; el DDL base y
  las dos migraciones de branding; y las tres suites heredadas relacionadas.
  No se inspeccionaron los dominios en espera.
- Línea base específica dentro del sandbox: **25 passed y 6 errores de setup**
  por `PermissionError` al directorio temporal global de pytest, no por fallos
  del producto. La repetición fuera de esa restricción terminó con **31
  passed** y 5 warnings heredados.
- Compuerta heredada dentro del sandbox: **982 passed y 29 errores de setup**
  por el mismo `PermissionError`; Ruff y dependencias sí pasaron. La repetición
  fuera de la restricción terminó con **1011 passed**, Ruff correcto y
  dependencias íntegras.
- Archivo funcional agregado: `tests/test_branding_caracterizacion.py`, con
  **19 pruebas** de frontera, rutas, permisos, HTTP ASGI, esquemas, SQL,
  conexiones, ausencia de fila, DDL, storage y autorización de `/uploads`.
  Código de producto modificado: **ninguno**.
- Verificación nueva: **19 passed**. Suite específica final: **50 passed** y 5
  warnings heredados. Ruff de la prueba nueva: **All checks passed**.
  Compuerta global final: **1030 passed**, Ruff correcto y dependencias
  íntegras.
- Los seis supuestos quedaron resueltos —cuatro confirmados y dos confirmados
  con matiz— y los trece hallazgos se registraron sin corregirlos.
- Archivos de la subcapa: la caracterización nueva, esta bitácora y
  `docs/modularizacion/README.md`. No hubo DB, migraciones, producción, commit,
  push ni deploy.
- Revisión final: `git diff --check` terminó en exit 0 para los dos documentos;
  `git diff --no-index --check -- NUL tests/test_branding_caracterizacion.py`
  no reportó errores de whitespace —exit 1 porque el archivo nuevo difiere de
  `NUL`—. Los avisos fueron únicamente de normalización futura LF/CRLF.
  `git status --short --branch` mostró exactamente esos tres archivos sobre
  `main...origin/main [ahead 1]`; no hay archivos de producto, configuración,
  migraciones ni otros dominios. El índice y las bitácoras conservan una sola
  capa **Activa**, `branding`.
- Siguiente acción exacta: presentar para autorización el alcance de 7.1 —la
  extracción de los siete sitios SQL a un único repositorio conservando
  recursos, storage, offload y contratos— y detenerse. No iniciar la extracción
  por inferencia.

### 2026-08-22 — cierre de la subcapa 7.1

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git y commits locales
  validados directamente.
- Autorización: la nueva orden «continua» habilitó únicamente la primera
  subcapa pendiente, 7.1.
- Precondiciones antes de modificar: rama `main`; árbol limpio según
  `git status --porcelain=v1 --branch`, que mostró
  `## main...origin/main [ahead 2]`; `HEAD`
  `008323712bc686644d361195974f7337e1414eef`; el commit base
  `bb34cf6f31413fdbbd2c1866b43f2da71f8ea03b` es ancestro.
- Continuidad desde el base: hay dos commits posteriores, `f53711b`
  —activación documental— y `0083237` —cierre de 7.0 y caracterización—.
  Ambos están explicados en esta bitácora y sus diffs coinciden con lo
  registrado; no había commits locales sin explicar.
- Estado de publicación observado: la referencia local `origin/main` está dos
  commits por detrás. No se consultó el remoto real, no hubo push y no se
  atribuye GitHub Actions.
- Inspección limitada: bitácora activa, controlador, caracterización de
  branding y los cinco guards exactos de repositorios que la compuerta señaló.
  No se inspeccionó ni modificó código de `profesores`, `super_admin` u otra
  capa en espera.
- Línea base específica antes de modificar: `pytest` sobre
  `test_branding_controlador.py`, `test_branding_upload_boundary.py`,
  `test_uploads_permissions.py` y `test_branding_caracterizacion.py` terminó
  con **50 passed** y 5 warnings heredados.
- Caracterización agregada antes de producto: superficie final del repositorio,
  ausencia de propiedad de recursos y comparación literal de SQL, parámetros y
  retornos. `pytest tests/test_branding_caracterizacion.py -q` terminó con **3
  failed, 18 passed**: siete
  `execute` aún inline y repositorio ausente, exactamente el estado que debía
  cambiar.
- Producto: se creó `app/repositories/branding_repository.py` con seis
  operaciones y se sustituyeron los siete usos SQL de
  `app/controllers/branding_controller.py`. La lectura de logo sirve a subida y
  borrado; `get_cursor(commit=True)`, JSON, defaults, tenant, offload, storage,
  orden y respuestas permanecen en el controlador.
- La primera repetición de la caracterización tras extraer terminó con **1
  failed, 20 passed** únicamente porque el guard de líneas aún conservaba 181;
  se actualizó al valor final 137 y se agregó el repositorio de 66 líneas al
  inventario. El mismo comando de las cuatro suites específicas terminó con
  **52 passed** y 5 warnings heredados.
- `ruff check` sobre controlador, repositorio y caracterización terminó con
  **All checks passed**.
- La primera compuerta global posterior a la extracción terminó con **5 failed,
  1027 passed**; los cinco fallos enumeraban el conjunto exacto de repositorios
  y señalaban exclusivamente `branding_repository`. Se añadió el nombre a esos
  cinco guards y se cambió el único conteo explícito de 13 a 14. La validación
  dirigida terminó con **5 passed**.
- Compuerta global final, `.\venv\Scripts\python.exe scripts\verify.py`:
  **1032 passed**, 5 warnings heredados, Ruff correcto y dependencias íntegras.
- Archivos funcionales: controlador y repositorio propios, caracterización de
  branding y los cinco guards exactos. Documentación: esta bitácora y el índice
  maestro. No se modificaron rutas, schemas, storage, migraciones,
  configuración ni producto de otros dominios.
- Revisión final: `git diff --check` terminó en exit 0; la comprobación
  independiente del repositorio nuevo no reportó errores de whitespace —exit 1
  porque difiere de `NUL`—. Los avisos fueron solo de normalización futura
  LF/CRLF. El diff contiene exclusivamente los diez archivos de 7.1 sobre
  `main...origin/main [ahead 2]`.
- No hubo DB, migraciones reales, producción, commit, push ni deploy.
- Siguiente acción exacta: presentar una decisión explícita entre cerrar esta
  capa como refactorización pura —7.2 y 7.3 `No aplica`— o autorizar una 7.2
  concreta. Detenerse sin iniciar 7.2.

### 2026-08-22 — cierre de la capa para `branding`

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git y commits locales
  validados directamente.
- Autorización explícita: el usuario ordenó **«cierra branding»** después de que
  se le presentaran las dos salidas registradas al terminar 7.1.
- Precondiciones: rama `main`; árbol limpio según
  `git status --porcelain=v1 --branch`, que mostró
  `## main...origin/main [ahead 3]`; `HEAD`
  `5ddd50470875f4740581897708e90804d079d2f2`; el commit base
  `bb34cf6f31413fdbbd2c1866b43f2da71f8ea03b` es ancestro.
- Continuidad desde el base: `f53711b` activa documentalmente, `0083237` cierra
  7.0 y `5ddd504` contiene 7.1. El último modifica exactamente los diez archivos
  que registra la ejecución anterior y no introduce trabajo sin explicar.
- Pruebas específicas de cierre sobre el commit limpio: **52 passed**, 5
  warnings heredados.
- Compuerta global de cierre, `.\venv\Scripts\python.exe scripts\verify.py`:
  **1032 passed**, 5 warnings heredados, Ruff correcto y dependencias íntegras.
- Decisión: cerrar como refactorización pura. 7.2 y 7.3 son **No aplica**; no se
  añadió `response_model`, error de dominio, corrección funcional ni retiro
  adicional.
- Staging y rollback quedaron documentados. La verificación manual propia queda
  **pendiente** y las verificaciones heredadas conservan su estado y riesgo.
- Cambios de este cierre: únicamente esta bitácora y el índice maestro. No se
  modificó producto, prueba, configuración, migración, schema ni dependencia.
- Estado de publicación observado localmente: `origin/main` está tres commits
  por detrás de `HEAD`. No se consultó el remoto real, no hubo push ni deploy y
  no se atribuye GitHub Actions.
- No hubo DB, migraciones reales, producción, commit, push ni deploy.
- Siguiente acción exacta: mantener **ninguna capa activa**. Antes de activar
  otra, elegir explícitamente `profesores` o `super_admin`, decidir si se
  continúa aceptando las verificaciones pendientes y crear su bitácora en un
  turno exclusivamente documental.

## Entrega al próximo chat

- Capa activa: **Ninguna**.
- Última capa cerrada: **7 para `branding`**, el 2026-08-22.
- Subcapas: 7.0 y 7.1 cerradas; 7.2 y 7.3 **No aplica**.
- Producto modificado en 7.1: controlador propio y nuevo repositorio; siete
  usos SQL originales quedan representados por seis operaciones sin recursos.
- Resultado: cuatro archivos propios y 268 líneas; rutas, contratos, SQL,
  parámetros, conexiones, transacciones, tenant, offload, storage y ausencia de
  N+1 conservados. Específicas **52 passed**; compuerta **1032 passed**.
- Hallazgos: trece registrados y ninguno corregido.
- Verificación manual propia de `branding`: **Pendiente**.
- Verificaciones heredadas: pendientes por decisión explícita del usuario.
- Dominios en espera: `profesores` y `super_admin`.
- Bloqueos: ninguno.
- Siguiente acción exacta: informar que no hay capa activa y esperar una orden
  que nombre el siguiente dominio; no activarlo ni inspeccionarlo por inferencia.
