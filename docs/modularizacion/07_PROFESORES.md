# Capa 7: profesores

Última revisión: 2026-08-23.

## Control

- Estado: **Cerrada** el 2026-08-23 por orden explícita del usuario.
- Commit base: `58eb5c2eb43a9d20708b75ca8bd798e9f13b33e6`.
- Rama acordada: `main`.
- Última subcapa ejecutada: **7.1**. Las subcapas 7.2 y 7.3 son **No aplica**
  por decisión explícita de cerrar como refactorización pura.
- Siguiente dominio: `super_admin`, **en espera** y sin bitácora activa.
- Código de producto modificado al activar: **Ninguno**.
- Código de producto modificado en 7.0: **Ninguno**. El diff funcional es un
  solo archivo nuevo de caracterización; los demás cambios son documentación.
- Código de producto modificado en 7.1: el controlador propio y el nuevo
  `app/repositories/profesores_repository.py`; no se modificaron rutas, schemas,
  migraciones, configuración, dominios consumidores ni la función sin
  consumidores.
- Dominio de esta capa: **`profesores`, y solo ese**.
- Autorización: el usuario escribió «activa el dominio proefesores»; se
  interpreta la errata inequívoca como `profesores`, el dominio que estaba en
  espera y que había sido ofrecido expresamente en el turno anterior.
- Decisión sobre verificaciones pendientes: la orden respondió a la alternativa
  previamente planteada y autoriza continuar localmente aceptando que la
  verificación manual de `branding` y las verificaciones heredadas permanezcan
  pendientes. Ninguna se marca como cumplida.
- La activación es exclusivamente documental. No autoriza implementar 7.0,
  hacer commit, push, deploy, migraciones reales ni acceder a producción.

## Objetivo

Migrar el dominio de **profesores** con contratos y pruebas, conservando su
comportamiento observable actual.

El índice maestro fija tres condiciones para esta capa:

1. trabajar un dominio a la vez;
2. agregar `response_model`, errores de dominio y pruebas HTTP o de integración
   solo después de caracterizar y conservar la respuesta existente;
3. no crear abstracciones compartidas sin dos consumidores reales.

La activación no inspecciona código ni infiere la frontera. La subcapa 7.0 debe
delimitarla con evidencia antes de proponer cualquier extracción.

## Dependencias de capas anteriores

- La capa 7 para `branding` está cerrada: 7.0 y 7.1 completas, 7.2 y 7.3
  **No aplica**, compuerta final con **1032 pruebas**, Ruff correcto y
  dependencias íntegras.
- La verificación manual propia de `branding` permanece pendiente.
- El commit base de esta capa es el `HEAD` limpio vigente,
  `58eb5c2eb43a9d20708b75ca8bd798e9f13b33e6`.
- Los cuatro commits posteriores al base de `branding` están explicados en su
  bitácora: `f53711b` activa el dominio, `0083237` cierra 7.0, `5ddd504`
  contiene 7.1 y `58eb5c2` contiene el cierre documental. Sus archivos
  coinciden con el alcance registrado.
- `HEAD` y la referencia local `origin/main` coinciden en el commit base. No se
  consultó el remoto real ni se atribuye publicación, despliegue o GitHub
  Actions.
- Siguen pendientes, sin marcarse como cumplidas: la calibración operativa
  final de `DB_STATEMENT_TIMEOUT_MS`; evidencia de GitHub Actions posterior a
  la capa 0; pasos manuales no confirmados heredados de `ventas`, `asistencia`,
  `boletin` y `observaciones`; la verificación manual propia de `branding`; y
  la rotación de la credencial privilegiada registrada en la capa 4.

## Supuestos documentales resueltos en 7.0

Los seis supuestos de la activación quedaron resueltos con evidencia:

| # | Supuesto documental | Resultado de 7.0 |
|---:|---|---|
| 1 | Frontera, archivos y consumidores por determinar | **RESUELTO CON FRONTERA PARTIDA.** Son tres archivos propios y cuatro rutas, pero el prefijo `/profesores` contiene además dos rutas de `asignaciones`; una función homónima de clases dentro del controlador propio no tiene consumidores |
| 2 | Contratos HTTP y permisos por determinar | **RESUELTO.** Cuatro rutas síncronas, todas con admin activo, sin `response_model`; se fijaron 200, 403, 404, 409 y 422 por ASGI real |
| 3 | Persistencia y recursos por determinar | **RESUELTO.** Diez sitios SQL inline, una tabla propia escrita, recursos manuales en cinco funciones y `get_cursor()` en la función sin consumidores. El conteo «cuatro» registrado inicialmente en 7.0 se corrigió al fijar la guarda de 7.1 |
| 4 | Posible crecimiento por tamaño por determinar | **RESUELTO.** No existe `execute` dentro de bucles; cada camino propio usa una conexión y entre una y tres consultas constantes |
| 5 | Contratos compartidos por determinar | **RESUELTO.** Diez archivos externos acceden directamente a `profesor`; autenticación también actualiza su password, y tres tablas tienen clave foránea hacia ella |
| 6 | Cobertura heredada y HTTP real por determinar | **RESUELTO.** Las dos suites compartidas pasan con 18 casos; siete son propios de profesores, ninguno observaba HTTP real. Se agregaron 27 casos de caracterización, incluidos contratos ASGI |

## Inventario y contratos fijados en 7.0

La frontera propia tiene **tres archivos y 450 líneas**. No existe repositorio
de profesores y los **diez sitios `cursor.execute`** viven en el controlador.

Ese es el inventario histórico al cerrar 7.0. Tras 7.1, la frontera tiene
**cuatro archivos y 533 líneas**: el controlador pasó de 350 a 314 líneas, el
nuevo repositorio tiene 119, nueve sitios alcanzables viven allí y permanece
un solo `execute` inline en la función sin consumidores.

| Archivo | Líneas | SQL ejecutado | Responsabilidad |
|---|---:|---:|---|
| `app/routes/profesores.py` | 80 | 0 | Cuatro entradas HTTP, permiso admin, parámetros y traducción de errores |
| `app/controllers/profesor_controller.py` | 350 | 10 | Normalización, validación, hashing, persistencia, recursos y respuestas |
| `app/schemas/profesor.py` | 20 | 0 | Entrada de alta/edición y cambio de estado |

### Entradas HTTP, permisos y respuestas

Las cuatro rutas usan el `APIRouter` con dependencia uniforme
`get_current_active_admin`, son síncronas y no declaran `response_model`:

| Método | Path | Respuesta o efecto principal |
|---|---|---|
| POST | `/profesores` | 200 con mensaje e `id`; 409 por documento/email duplicado y 422 por validación del controlador o Pydantic |
| GET | `/profesores` | Lista legacy sin `limit`, o `{total, limit, offset, items}` al enviarlo; 422 por paginación o estado inválido |
| PUT | `/profesores/{profesor_id}` | 200 con mensaje; 404 ausente, 409 duplicado y 422 por validación |
| PATCH | `/profesores/{profesor_id}/estado` | 200 con mensaje, id y estado; 404 ausente y 422 fuera de `activo`/`inactivo` |

El prefijo no define por sí solo la frontera: `asignaciones` posee además
`GET /profesores/{profesor_id}/disponibilidad` y
`GET /profesores/{profesor_id}/cursos`. Permanecen fuera de esta capa.

### Persistencia, conexiones y conteos

- La tabla propia es `profesor`; POST, PUT y PATCH escriben en ella. El login
  es un escritor externo porque rehashea passwords legacy.
- Los diez sitios SQL son dos comprobaciones de unicidad, el INSERT, dos
  lecturas de listado, el conteo paginado, la consulta de clases sin consumidor,
  dos variantes de UPDATE según password y el UPDATE de estado.
- POST exitoso usa **1 conexión y 3 consultas**; un documento duplicado sale
  tras una, y un email duplicado tras dos.
- GET legacy usa **1 conexión y 1 consulta**. GET paginado usa **1 conexión y
  2 consultas**, con conteo y página.
- PUT usa **1 conexión y 3 consultas** tanto con password como sin ella; valida
  duplicados antes de saber si el id existe. PATCH usa **1 conexión y 1
  consulta**.
- La función `obtener_clases_profesor_controller` usa **1 conexión y 1
  consulta**, pero no tiene llamadores productivos; existe otra función
  homónima, con filtros diferentes, en el dominio cerrado de asignaciones.
- No hay `execute` dentro de bucles: **no existe N+1 de aplicación** en
  consultas o conexiones dentro de la frontera propia.
- Las escrituras conservan `commit` y `rollback` manuales; las lecturas cierran
  cursor y conexión sin confirmar. La función sin consumidores usa
  `get_cursor(commit=False)`.

### DDL y consumidores externos

- `profesor` tiene PK, email único y **dos restricciones únicas redundantes**
  sobre `documento_identidad`; los campos de negocio, incluido `estado`,
  admiten nulos y no hay `CHECK` de estado.
- `asignaciones`, `nomina` y `prestamos` referencian la tabla. Las dos últimas
  usan `ON DELETE CASCADE`; el dominio no expone DELETE y desactiva con estado.
- Diez archivos externos ejecutan SQL directo sobre la tabla: dependencias y
  autenticación; los controladores de nómina y préstamos; y los repositorios de
  asignaciones, boletín, estudiantes, notas, plan de clases y reportes.

## Hallazgos registrados en 7.0; ninguno corregido

1. **El prefijo HTTP está partido.** Dos rutas bajo `/profesores` pertenecen a
   asignaciones; moverlas por coincidencia nominal reabriría un dominio cerrado.
2. **Existe una función de clases sin consumidores.** Está en
   `profesor_controller`, duplica un nombre de asignaciones y conserva una
   consulta menos restrictiva, sin filtros de activo o estado.
3. **Búsqueda y offset se ignoran sin `limit`.** El GET elige la respuesta
   legacy y solo entrega `estado` al controlador.
4. **PUT exige siempre el campo `password`.** Un string vacío significa
   conservar el hash actual; omitirlo produce 422 antes del controlador.
5. **POST acepta password vacío.** Pydantic y el controlador no imponen
   fortaleza ni presencia no vacía y terminan hasheándolo.
6. **Las validaciones son parciales.** Nombre, apellido y documento solo se
   validan tras normalizar; teléfono y sueldo no tienen límites de negocio, y
   el esquema permite sueldo negativo.
7. **PUT valida duplicados antes de existencia.** Un id ausente puede responder
   409 por datos usados por otro profesor en vez de 404.
8. **La tabla tiene dos UNIQUE para el mismo documento.** Es redundancia de DDL
   heredada y no se toca en esta refactorización.
9. **Estado depende del código.** La DB acepta nulos y valores arbitrarios; los
   controladores propios restringen a activo/inactivo, pero los escritores
   externos no están cubiertos por un `CHECK`.
10. **La tabla es transversal.** Diez archivos externos leen o escriben
    `profesor`; una regresión de forma o semántica puede aparecer fuera de las
    pruebas propias y exige compuerta global.
11. **No hay `response_model`.** Las respuestas conservan formas distintas y
    el listado expone `documento` aunque la entrada use
    `documento_identidad`.
12. **Errores inesperados se propagan.** Las rutas traducen duplicados y
    validaciones conocidas, pero DB, hashing u otros fallos salen como 500 sin
    una traducción común.

Los doce hallazgos quedan registrados sin cambiar producto, expectativas ni
base de datos.

## Alcance autorizado

- Trabajar únicamente en el dominio `profesores`.
- En 7.0, delimitar primero la frontera real por rutas, llamadores, tablas,
  consumidores y efectos laterales, no solo por nombres de archivo.
- Inventariar métodos, paths, guards, permisos, ownership, tenant, payloads,
  status codes, respuestas, SQL, transacciones, conexiones y concurrencia.
- Resolver uno por uno los supuestos documentales con evidencia.
- Agregar o conservar pruebas de caracterización antes de cualquier extracción
  importante.
- Medir consultas y conexiones críticas antes y después de cualquier cambio de
  producto posterior.

## Fuera de alcance

- `super_admin`, que continúa en espera.
- Reabrir `branding` u otro dominio cerrado por inferencia.
- Corregir hallazgos abiertos de capas anteriores o completar verificaciones
  heredadas dentro de esta activación.
- Cambiar rutas, payloads, status codes, permisos, roles, ownership, tenant,
  SQL observable, transacciones o comportamiento actual sin autorización
  explícita apoyada en caracterización.
- Cambiar PostgreSQL, `psycopg2`, schemas tenant, pool, timeouts, concurrencia,
  ORM o driver.
- Migraciones reales, acceso a producción, DDL, DML, deploy, commit o push.

## Invariantes

- Métodos, paths, status codes y forma exacta de las respuestas permanecen
  idénticos.
- Permisos, roles, ownership y aislamiento entre tenants se conservan.
- SQL, parámetros, número y orden observable de operaciones y límites de
  transacción se conservan.
- Se conserva quién posee conexión, cursor, `commit`, `rollback` y demás
  efectos laterales.
- La DB síncrona permanece fuera del event loop y el `ContextVar` del tenant se
  preserva donde corresponda.
- No se crea una abstracción compartida sin dos consumidores reales.

## Línea base

| Comprobación | Comando | Resultado |
|---|---|---|
| Línea base heredada compartida | `pytest` sobre las dos suites relacionadas | **18 passed**, 2 warnings heredados |
| Caracterización nueva | `pytest tests\test_profesores_caracterizacion.py -q` | **27 passed**, 6 warnings heredados |
| Pruebas específicas finales de 7.0 | Las tres suites relacionadas | **45 passed**, 6 warnings heredados |
| Ruff de la caracterización | Ruff sobre `test_profesores_caracterizacion.py` | **All checks passed** |
| Compuerta dentro del sandbox | `.\venv\Scripts\python.exe scripts\verify.py` | **1029 passed y 30 errores de setup** por `PermissionError` del temporal global; Ruff y dependencias correctas |
| Compuerta final fuera del sandbox | El mismo comando, con aprobación | **1059 passed**, Ruff correcto, dependencias íntegras |
| Guardas rojas de 7.1 | Caracterización antes de producto | **5 failed, 24 passed**: cuatro señales de extracción pendiente y una imprecisión de 7.0 en el conteo de conexiones, corregida de cuatro a cinco |
| Pruebas específicas finales de 7.1 | Las tres suites relacionadas | **47 passed**, 6 warnings heredados |
| Guardas globales exactas | Cinco enumeraciones históricas de repositorios | **5 passed**, 1 warning de cache del entorno |
| Ruff de 7.1 | Ocho archivos Python modificados | **All checks passed** |
| Compuerta de 7.1 dentro del sandbox | `scripts\verify.py` | **1031 passed y 30 errores de setup** por `PermissionError` del temporal global; Ruff y dependencias correctas |
| Compuerta final de 7.1 fuera del sandbox | El mismo comando, con aprobación | **1061 passed**, 5 warnings heredados, Ruff correcto, dependencias íntegras |

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 7.0 | Inventario, contratos y caracterización | **Cerrada el 2026-08-23** |
| 7.1 | Extracción protegida del SQL alcanzable por las rutas propias | **Cerrada el 2026-08-23** |
| 7.2 | Segunda extracción o integración | **No aplica**: no existe otra extracción concreta justificada y el usuario ordenó cerrar |
| 7.3 | Retiro heredado | **No aplica**: no se autorizó retirar la función sin consumidores ni corregir hallazgos |

Las subcapas se adaptan al trabajo real. Las innecesarias se marcan `No aplica`
con una explicación; nunca se ejecutan dos sin orden explícita.

## Subcapa cerrada: trabajo ejecutado en 7.0

1. Delimitar la frontera real de `profesores` por entradas, llamadores, tablas,
   consumidores y efectos laterales antes de contar o modificar nada.
2. Inspeccionar únicamente la documentación, fuentes y pruebas relacionadas
   con esa frontera.
3. Inventariar contratos HTTP, permisos, roles, ownership, tenant, SQL,
   transacciones, recursos y comportamiento observable.
4. Medir consultas y conexiones por camino y buscar dependencias del tamaño de
   entrada o resultado.
5. Identificar consumidores y dependencias compartidas sin modificar dominios
   cerrados.
6. Revisar las pruebas relacionadas y agregar caracterización sin cambiar
   expectativas heredadas.
7. Resolver los seis supuestos documentales y registrar los hallazgos sin
   corregirlos.
8. Archivos modificables en 7.0: pruebas de caracterización del dominio, esta
   bitácora y el índice maestro. No se modifica producto durante el inventario.
9. Ejecutar pruebas específicas, Ruff sobre la caracterización, la compuerta
   global, `git diff --check` y revisión de alcance.
10. Actualizar esta bitácora con archivos, comandos, resultados, decisiones,
    riesgos y la siguiente acción exacta.
11. Detenerse al cerrar 7.0. No iniciar 7.1 en el mismo turno.

## Criterios de cierre de la subcapa

Todos quedaron cumplidos:

- La frontera quedó delimitada con evidencia y sin reabrir otros dominios.
- Los seis supuestos documentales quedaron resueltos uno por uno.
- Existe caracterización ejecutable de contratos, SQL, transacciones,
  consultas, conexiones y efectos laterales aplicables.
- Pruebas específicas, Ruff, compuerta y dependencias son correctas.
- `git diff --check` es correcto y el diff es exclusivo de 7.0.
- La bitácora registra resultados, decisiones, riesgos y siguiente acción.

## Subcapa cerrada: trabajo ejecutado en 7.1

La nueva orden «continua» autorizó exclusivamente esta extracción protegida:

1. Agregar primero guards finales para los nueve sitios SQL alcanzables desde
   las cuatro rutas propias, incluidos texto, parámetros, retornos y recursos.
2. Crear un único `profesores_repository.py` con operaciones que reciban el
   cursor existente y no administren conexión, commit, rollback ni cierre.
3. Mover las dos consultas de unicidad, INSERT, listados, conteo, las dos
   variantes de actualización y el cambio de estado sin alterar SQL ni orden.
4. Conservar normalización, validación, hashing, ensamblado, recursos y
   traducción de errores en controlador y ruta.
5. Dejar inline la consulta de `obtener_clases_profesor_controller` mientras
   siga sin consumidores; moverla crearía persistencia para código muerto y
   confundiría la frontera cerrada de asignaciones.
6. Actualizar solo los guards globales que enumeren exactamente repositorios y
   ejecutar específicas, Ruff, compuerta, `git diff --check` y alcance.
7. Actualizar bitácora e índice y detenerse antes de 7.2.

Todos los puntos quedaron ejecutados. Las nueve operaciones públicas reciben
el cursor existente y el repositorio no abre ni cierra recursos, no confirma y
no revierte. El controlador conserva normalización, validación, hashing,
ensamblado, cinco conexiones manuales, commits, rollbacks y cierres. Los diez
argumentos SQL del estado anterior y posterior forman el mismo multiconjunto
AST: nueve se movieron y la consulta de clases sin consumidores quedó inline.

## Decisión explícita de cierre

El usuario ordenó «cierra» después de recibir las dos alternativas. Se elige el
cierre como refactorización pura: 7.2 y 7.3 quedan **No aplica**. No se agregan
`response_model`, errores de dominio ni cambios de contrato; tampoco se retira
la función sin consumidores. La compuerta se ejecuta sobre el commit limpio de
7.1 y `super_admin` permanece en espera.

## Criterios de cierre de la capa

- Todas las subcapas necesarias están cerradas.
- Compuerta global correcta.
- Contratos conservados o cambios explícitamente aprobados.
- Staging, rollback y verificación manual documentados.
- El siguiente dominio queda en espera hasta una orden explícita del usuario.

Todos los criterios están cumplidos. La verificación manual está documentada y
permanece pendiente; no se presenta como realizada.

## Staging recomendado; no ejecutado

1. Desplegar el commit de 7.1 en un entorno no productivo con al menos dos
   tenants de prueba y conservar el commit anterior `3ae2884` disponible.
2. Ejecutar primero `scripts\verify.py` en el mismo artefacto desplegado.
3. Con un admin activo del tenant A, crear un profesor y comprobar los listados
   legacy y paginado, incluidos búsqueda y filtros de estado.
4. Editar el profesor con password vacío y no vacío; comprobar después el
   acceso del profesor y que el hash no se expone en respuestas.
5. Desactivar y reactivar al profesor; comprobar 409 para documento/email
   duplicado, 404 para ids ausentes, 422 para datos o estado inválidos y 403
   para un usuario sin permiso admin.
6. Repetir las lecturas desde el tenant B y confirmar que ningún profesor del
   tenant A resulta visible o modificable.

## Rollback

- Esta capa no contiene migraciones, DDL, DML operativo ni cambios de storage;
  no existe rollback de datos.
- Antes de publicar, el rollback de código consiste en conservar o volver al
  commit `3ae2884652b96e4bb3a10648466820e87010994d`, anterior a la extracción
  de 7.1. Los documentos de activación y caracterización pueden permanecer.
- Si 7.1 se publica después, crear un revert normal del commit
  `3eb6a44e6ba7e90a435d90792d76c71f95e1eed9`, ejecutar la compuerta y desplegar
  ese revert por el mecanismo habitual. No reescribir historia compartida.

## Verificación manual

- Estado: **Pendiente**.
- Guion: los pasos 3 a 6 de staging, sobre el mismo artefacto candidato a
  publicación.
- Riesgo aceptado al cerrar: la compuerta protege contratos y SQL, pero no
  sustituye una comprobación real de permisos, tenant, login tras actualizar el
  password y viaje completo de alta/listado/edición/estado.
- Esta verificación no se marcará como cumplida sin un reporte posterior del
  usuario que identifique el artefacto o entorno ejercitado.

## Decisiones

- **Activar `profesores` y solo ese dominio.** El usuario lo nombró —con la
  errata inequívoca `proefesores`— y ordenó activarlo.
- **Continuar localmente con verificaciones pendientes.** La orden responde a
  la alternativa presentada en el turno anterior; ninguna verificación se
  considera cumplida y sus riesgos permanecen vigentes.
- **Usar el `HEAD` limpio vigente como commit base.** Es el punto posterior al
  cierre de `branding`; todos sus descendientes desde el base anterior están
  explicados.
- **Activación exclusivamente documental.** No se inspecciona ni implementa
  7.0 en este turno.
- **No inferir la frontera.** Los datos del dominio se registran como preguntas
  que 7.0 debe resolver con evidencia.
- **Ejecutar solo 7.0 por la orden «continua».** La subcapa agrega
  caracterización y documentación, sin cambios de producto ni inicio de 7.1.
- **Separar prefijo de propiedad.** Las dos rutas de disponibilidad y cursos
  permanecen en asignaciones aunque sus paths empiecen por `/profesores`.
- **Tratar los accesos externos como consumidores, no como alcance.** La
  autenticación y los nueve lectores externos de la tabla quedan protegidos por
  la compuerta, pero no se mueven ni modifican desde esta capa.
- **No retirar la función de clases sin consumidores.** Su duplicación y falta
  de filtros quedan como hallazgo; borrarla o moverla no es caracterización.
- **Proponer 7.1 solo para nueve sitios alcanzables.** La consulta de la
  función muerta queda inline salvo una decisión posterior distinta apoyada en
  consumidores reales.
- **Al cerrar 7.0, dejar 7.1 sujeta a una orden nueva.** La evidencia permite
  proponer la extracción, pero no autoriza producto en este turno.
- **Ejecutar únicamente 7.1 por la nueva orden «continua».** No se inicia 7.2
  ni se cierra la capa por inferencia.
- **Crear un repositorio plural con nueve operaciones.** Cada función recibe el
  cursor existente y solo ejecuta y devuelve el resultado requerido por el
  controlador; no administra conexiones ni transacciones.
- **Conservar la consulta muerta inline.** Su única sentencia sigue en
  `obtener_clases_profesor_controller`; moverla habría confundido la frontera
  de asignaciones y creado persistencia para código sin consumidores.
- **Corregir el conteo de propietarios de conexión.** La guarda roja mostró
  que eran cinco funciones manuales, no cuatro. La corrección es documental y
  de prueba; el producto no cambió ese conteo.
- **Dejar 7.2 como decisión, no como implementación inferida.** La extracción
  no demuestra por sí sola que deba añadirse `response_model` o una jerarquía
  nueva de errores.
- **Cerrar como refactorización pura.** La orden «cierra» resuelve el punto de
  decisión: 7.2 y 7.3 son `No aplica`; los doce hallazgos permanecen sin
  corregir.
- **Cerrar con verificación manual pendiente.** Staging y el guion manual están
  documentados, pero no se ejecutaron ni se consideran cumplidos.
- **No activar `super_admin`.** Permanece en espera y requiere una orden nueva.

## Riesgos

- **Verificación manual de `profesores` pendiente.** El cierre automatizado no
  demuestra todavía el flujo real en staging de admin, tenant, login ni ciclo
  de alta/listado/edición/estado.
- **Verificación manual de `branding` pendiente.** Se aceptó continuar sin
  cerrarla; fallos de GET/PUT, permisos, tenant o ciclo de logos podrían no
  estar cubiertos por la compuerta automática.
- **Verificaciones heredadas pendientes.** Conservan los riesgos documentados
  en el índice y esta capa no puede presentarlas como cumplidas.
- **Dominio de escritura y tabla transversal.** Tres rutas escriben y diez
  archivos externos acceden directamente a `profesor`; una regresión puede
  aparecer fuera de las pruebas específicas.
- **Frontera HTTP partida.** Dos rutas nominales pertenecen a asignaciones; una
  extracción basada solo en paths reabriría un dominio cerrado.
- **Función muerta divergente.** `obtener_clases_profesor_controller` no tiene
  consumidores y consulta asignaciones sin los filtros de la función homónima.
- **Contratos permisivos.** Password vacío, sueldo sin regla de negocio, estado
  sin `CHECK`, duplicidad de UNIQUE y precedencia 409/404 permanecen intactos.
- **Recursos manuales.** Cinco funciones poseen conexión y cursor de forma
  explícita; una extracción debe conservar commits, rollbacks y cierres sin
  introducir `get_cursor()` por conveniencia.
- **Publicación de `branding` no comprobada contra el remoto real.** Al activar,
  `HEAD` coincide con la referencia local `origin/main`, pero no se consultó el
  remoto real ni se verificaron deploy o GitHub Actions.

## Registro de ejecución

### 2026-08-23 — activación de la capa para `profesores`

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git y commits locales
  validados directamente.
- Documentos leídos completamente y en orden: índice maestro,
  `07_BRANDING.md`, instrucciones locales —no se encontraron— y
  `PLANTILLA_CAPA.md`.
- Autorización: el usuario ordenó «activa el dominio proefesores» después de
  recibir la decisión explícita entre completar la verificación manual de
  `branding` o continuar localmente aceptándola como pendiente.
- Rama acordada y observada: `main`.
- Estado antes de escribir: árbol limpio; `git status --porcelain=v1 --branch`
  mostró únicamente `## main...origin/main`.
- Commit base: `58eb5c2eb43a9d20708b75ca8bd798e9f13b33e6`, el `HEAD`
  limpio vigente y coincidente con la referencia local `origin/main`.
- Continuidad: el base `bb34cf6` de `branding` es ancestro. Sus cuatro
  descendientes son `f53711b` —activación—, `0083237` —7.0—, `5ddd504`
  —7.1— y `58eb5c2` —cierre documental—. Todos están explicados en esa
  bitácora y sus archivos coinciden con lo registrado.
- Estado de publicación observado localmente: `HEAD` y la referencia local
  `origin/main` coinciden. No se consultó el remoto real ni se verificó GitHub
  Actions.
- Decisión heredada: permanecen pendientes la verificación manual propia de
  `branding`, la calibración de timeout, la evidencia de CI, los pasos manuales
  no confirmados y la rotación de la credencial privilegiada. El usuario
  aceptó continuar con sus riesgos.
- Archivos creados o modificados: esta bitácora y
  `docs/modularizacion/README.md`.
- Código de producto, pruebas, consultas, migraciones, esquemas, configuración
  y dependencias inspeccionados o modificados: **ninguno**.
- Pruebas, conexiones a PostgreSQL, acceso a producción, commit, push y deploy:
  **ninguno**.
- Verificación documental: `git diff --check` terminó en exit 0 para el índice;
  `git diff --no-index --check -- NUL docs/modularizacion/07_PROFESORES.md`
  no reportó errores de whitespace —su exit 1 indica que el archivo nuevo
  difiere de `NUL`—. Los avisos fueron únicamente de normalización futura
  LF/CRLF.
- Revisión de alcance: `git status --short --branch` mostró exactamente el
  índice modificado y esta bitácora nueva sobre `main...origin/main`. El índice
  contiene una sola fila de estado **Activa** y los encabezados de control de
  las bitácoras una sola declaración **Activa**, ambas para `profesores`.
- Siguiente acción exacta: ejecutar únicamente 7.0 conforme al trabajo exacto
  de esta bitácora y detenerse antes de 7.1.

### 2026-08-23 — cierre de la subcapa 7.0

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git y commits locales
  validados directamente.
- Autorización: la orden «continua» habilitó únicamente la primera subcapa
  pendiente, 7.0.
- Precondiciones antes de modificar: rama `main`; árbol limpio según
  `git status --porcelain=v1 --branch`, que mostró
  `## main...origin/main [ahead 1]`; `HEAD`
  `4f459c19094e61365a865e695b9e0065131b5b03`; el commit base
  `58eb5c2eb43a9d20708b75ca8bd798e9f13b33e6` es ancestro.
- Continuidad desde el base: existe un solo commit posterior, `4f459c1`, cuya
  creación de esta bitácora y modificación del índice coinciden exactamente
  con la activación registrada. No había commits locales sin explicar.
- Estado de publicación observado: la referencia local `origin/main` está un
  commit por detrás. No se consultó el remoto real, no hubo push y no se
  atribuye GitHub Actions.
- Fuentes inspeccionadas: los tres archivos propios; montaje en `main`;
  dependencias de admin, tenant y conexión relacionadas; DDL base y migración
  de estado; consumidores SQL directos de la tabla; y las dos suites heredadas
  relacionadas. No se inspeccionó ni modificó `super_admin` ni se reabrieron
  los dominios consumidores.
- Línea base compartida:
  `pytest tests\test_profesores_controlador.py tests\test_catalogos_pagination.py -q`
  terminó con **18 passed** y 2 warnings heredados.
- Archivo funcional agregado: `tests/test_profesores_caracterizacion.py`, con
  **27 pruebas** de frontera, montaje, permisos, HTTP ASGI, esquemas, SQL,
  parámetros, conexiones, transacciones, DDL y consumidores externos. Código
  de producto modificado: **ninguno**.
- La primera ejecución nueva terminó con **1 failed y 26 passed**: el montaje
  global mostró las dos rutas de asignaciones bajo `/profesores`. Se corrigió
  solo la expectativa para registrar la frontera partida; no se cambió
  producto. La repetición terminó con **27 passed**.
- Suite específica final sobre los tres archivos: **45 passed** y 6 warnings
  heredados. Ruff de la caracterización: **All checks passed**.
- La primera compuerta dentro del sandbox ejecutó **1029 pruebas** y produjo
  **30 errores de setup** exclusivamente por `PermissionError` al directorio
  temporal global de pytest; Ruff y dependencias pasaron. La repetición fuera
  del sandbox, con aprobación, terminó con **1059 passed**, Ruff correcto y
  dependencias íntegras.
- Los seis supuestos quedaron resueltos y los doce hallazgos se registraron sin
  corregirlos.
- Archivos de la subcapa: la caracterización nueva, esta bitácora y
  `docs/modularizacion/README.md`. No hubo DB, migraciones, producción, commit,
  push ni deploy.
- Revisión final: `git diff --check` terminó en exit 0 para los dos documentos;
  `git diff --no-index --check -- NUL tests/test_profesores_caracterizacion.py`
  no reportó errores de whitespace —exit 1 porque el archivo nuevo difiere de
  `NUL`—. Los avisos fueron únicamente de normalización futura LF/CRLF.
  `git status --short --branch` mostró exactamente la bitácora y el índice
  modificados y la caracterización nueva sobre `main...origin/main [ahead 1]`;
  no hay archivos de producto, configuración, migraciones ni otros dominios.
- Siguiente acción exacta: presentar para autorización el alcance de 7.1 —la
  extracción de los nueve sitios SQL alcanzables a un único
  `profesores_repository`, conservando recursos, orden y contratos, y dejando
  inline la consulta de la función sin consumidores— y detenerse. No iniciar
  la extracción por inferencia.

### 2026-08-23 — cierre de la subcapa 7.1

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git y commits locales
  validados directamente.
- Autorización: la nueva orden «continua» habilitó únicamente la primera
  subcapa pendiente, 7.1.
- Precondiciones antes de modificar: rama `main`; árbol limpio según
  `git status --porcelain=v1 --branch`, que mostró
  `## main...origin/main [ahead 2]`; `HEAD`
  `3ae2884652b96e4bb3a10648466820e87010994d`; el commit base
  `58eb5c2eb43a9d20708b75ca8bd798e9f13b33e6` es ancestro.
- Continuidad desde el base: los únicos commits posteriores son `4f459c1`, la
  activación documental, y `3ae2884`, el cierre de 7.0. El segundo contiene
  exactamente esta bitácora, el índice y la caracterización nueva; ambos están
  explicados y no había divergencia local sin documentar.
- Guardas antes de producto: se convirtieron a su forma final las expectativas
  de frontera, superficie pública, recursos, consumidores y ausencia de N+1,
  y se fijaron los textos SQL normalizados y parámetros de todos los caminos.
  La ejecución roja terminó con **5 failed y 24 passed**. Cuatro fallos eran las
  señales esperadas de extracción pendiente; el quinto reveló que 7.0 había
  contado cuatro propietarios manuales de conexión cuando son cinco. Se
  corrigió únicamente esa expectativa y este documento antes de extraer.
- Producto: se creó `app/repositories/profesores_repository.py` con nueve
  operaciones públicas que reciben cursor. Se actualizaron únicamente las
  llamadas alcanzables en `app/controllers/profesor_controller.py`. La función
  de clases sin consumidores conserva su SQL inline.
- Equivalencia estructural: un comparador AST entre el controlador de
  `3ae2884` y el controlador más repositorio actuales obtuvo
  `{'before': 10, 'after': 10, 'identical': True}` para los primeros argumentos
  de todos los `execute`.
- Recursos y contratos: el controlador conserva cinco aperturas y cierres de
  conexión, un `get_cursor()`, tres commits, seis rollbacks, normalización,
  hashing, ensamblado y precedencia de errores. Las pruebas conservan conteos,
  orden, parámetros, retornos, payloads, status codes y permiso admin.
- Guardas globales: se añadió `profesores_repository` —y solo ese elemento— a
  las cinco enumeraciones exactas heredadas de dashboard, notas, ventas,
  asistencia y planilla; sus cinco casos terminaron con **5 passed**.
- Pruebas específicas finales:
  `pytest tests\test_profesores_caracterizacion.py tests\test_profesores_controlador.py tests\test_catalogos_pagination.py -q`
  terminó con **47 passed** y 6 warnings heredados.
- Ruff sobre los dos archivos de producto y las seis pruebas modificadas:
  **All checks passed**.
- La primera compuerta dentro del sandbox ejecutó **1031 pruebas** y produjo
  **30 errores de setup** exclusivamente por `PermissionError` al directorio
  temporal global de pytest; Ruff y dependencias pasaron. Repetida fuera del
  sandbox con aprobación, terminó con **1061 passed**, 5 warnings heredados,
  Ruff correcto y dependencias íntegras.
- Archivos de producto de 7.1: el controlador y el nuevo repositorio. Pruebas:
  la caracterización propia y las cinco enumeraciones globales. Documentación:
  esta bitácora y el índice. No hubo DB, migraciones, producción, commit, push,
  deploy ni GitHub Actions.
- Revisión final: `git diff --check` terminó en exit 0 para todos los archivos
  rastreados. `git diff --no-index --check -- NUL
  app/repositories/profesores_repository.py` no reportó errores de whitespace;
  su exit 1 solo indica que el archivo nuevo difiere de `NUL`. Los avisos fueron
  exclusivamente de normalización futura LF/CRLF.
- Alcance final observado por `git status --short --branch`: dos archivos de
  producto, seis pruebas y dos documentos sobre
  `main...origin/main [ahead 2]`; no aparecen rutas, schemas, migraciones,
  configuración ni dominios consumidores modificados.
- Siguiente acción exacta: pedir una decisión explícita entre cerrar la capa
  como refactorización pura —7.2/7.3 `No aplica`— o autorizar una 7.2 concreta.
  Detenerse sin iniciar ninguna de las dos alternativas y sin activar
  `super_admin`.

### 2026-08-23 — cierre de la capa para `profesores`

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git y commits locales
  validados directamente.
- Autorización: el usuario ordenó «cierra» después de recibir la decisión entre
  cerrar como refactorización pura o autorizar una 7.2 concreta. Se eligió la
  primera alternativa; 7.2 y 7.3 son `No aplica`.
- Precondiciones antes de modificar: rama `main`; árbol limpio según
  `git status --porcelain=v1 --branch`, que mostró
  `## main...origin/main [ahead 3]`; `HEAD`
  `3eb6a44e6ba7e90a435d90792d76c71f95e1eed9`; el commit base
  `58eb5c2eb43a9d20708b75ca8bd798e9f13b33e6` es ancestro.
- Continuidad desde el base: `4f459c1` es la activación, `3ae2884` contiene el
  cierre de 7.0 y `3eb6a44` contiene 7.1. La inspección del último commit mostró
  exactamente dos archivos de producto, seis pruebas y los dos documentos que
  la bitácora registra; no existe commit local posterior sin explicar.
- Compuerta de cierre sobre el `HEAD` limpio, ejecutada fuera del sandbox para
  permitir el temporal de pytest: **1061 passed**, 5 warnings heredados, Ruff
  correcto y dependencias íntegras.
- Staging, rollback y guion manual quedaron documentados. No se ejecutó staging
  y la verificación manual propia permanece **pendiente**.
- Cambios de cierre: únicamente esta bitácora y
  `docs/modularizacion/README.md`. No se modificaron producto, pruebas,
  configuración, migraciones ni otros dominios.
- Revisión final: `git diff --check` terminó en exit 0; los avisos fueron solo
  de normalización futura LF/CRLF. `git status --short --branch` mostró
  exactamente los dos documentos modificados sobre
  `main...origin/main [ahead 3]`.
- Coherencia documental: el índice no contiene filas `Activa`, esta bitácora
  está `Cerrada`, no quedan referencias vigentes a 7.2 pendiente y
  `super_admin` sigue en espera.
- Estado de publicación observado: `main` está tres commits por delante de la
  referencia local `origin/main`. No se consultó el remoto real, no hubo push,
  deploy ni GitHub Actions y no se atribuye publicación.
- Siguiente dominio: `super_admin`, en espera. No se crea su bitácora ni se
  inspecciona o activa por esta orden.

## Entrega al próximo chat

- Capa activa: **ninguna**.
- Última capa cerrada: **7 para `profesores`**, el 2026-08-23.
- Última subcapa terminada: **7.1**, extracción protegida de los nueve sitios
  SQL alcanzables por las rutas propias.
- Subcapas 7.2 y 7.3: **No aplica** por cierre explícito como refactorización
  pura.
- Resultado acumulado: 7.0 delimitó tres archivos propios, cuatro rutas admin,
  diez SQL —nueve alcanzables y uno en una función sin consumidores—, una tabla
  escrita, ninguna forma de N+1 y doce hallazgos. En 7.1 los nueve alcanzables
  pasaron a un repositorio sin recursos; el controlador conserva el décimo y
  todo el ciclo de vida. La caracterización tiene 29 casos, las específicas
  terminaron con **47 passed** y la compuerta con **1061 passed**, Ruff correcto
  y dependencias íntegras.
- Verificaciones pendientes: la manual propia de `profesores`, la manual de
  `branding` y las heredadas registradas en el índice; ninguna se considera
  cumplida.
- Dominio en espera: `super_admin`.
- Bloqueos: ninguno.
- Siguiente acción exacta: esperar una orden explícita para completar la
  verificación manual de `profesores` o activar `super_admin`; una instrucción
  genérica de continuidad no activa el dominio en espera.
