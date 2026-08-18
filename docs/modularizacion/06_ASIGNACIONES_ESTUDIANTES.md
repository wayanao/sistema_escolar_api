# Capa 6: asignaciones y estudiantes

Última revisión: 2026-08-17.

## Control

- Estado: **Cerrada** el 2026-08-17. Sus tres objetivos quedaron cumplidos y
  verificados; los riesgos abiertos están registrados en el cierre.
- Commit base: `589cb6d1391161c692a6f24aee9d523317cbb1ce`.
- Rama acordada: `main`.
- Estado al activar: árbol limpio; `HEAD` coincidente con la referencia local
  `origin/main`, que el reflog registra como publicada por push el 2026-08-17.
  A diferencia de todas las activaciones anteriores salvo la de la capa 5, el
  commit base **ya está desplegado**: un push a `main` dispara el despliegue en
  este repositorio.
- Primera subcapa pendiente: **ninguna**. Las cinco subcapas, **6.0 a 6.5**,
  quedaron **cerradas** el 2026-08-17. El **cierre de la capa** queda supeditado
  a la verificación manual, que el usuario decidió ejecutar él mismo.
- Código de producto modificado al activar: **ninguno**. Tampoco en 6.0. En 6.1:
  `app/controllers/estudiante_controller.py` y el nuevo
  `app/repositories/estudiantes_repository.py`, sin cambios en rutas, payloads,
  status codes, permisos, tenant, ownership, transacciones ni SQL observable.
- Autorización: orden explícita del usuario el 2026-08-17, coincidente con la
  autorización puntual que `PROMPT_CONTINUACION.md` conservaba para la capa 6 y
  cuya condición de caducidad se cumplía. El usuario decidió además, de forma
  explícita, continuar aceptando las verificaciones heredadas pendientes. La
  activación **no** autoriza inspeccionar código de la capa 6 ni iniciar 6.0 en
  ese mismo turno.

## Objetivo

Separar los dominios de asignaciones y estudiantes con contratos estables,
trabajando cada dominio en subcapas y evitando una extracción conjunta masiva,
y protegiendo permisos, relaciones académicas, archivos e historial.

El objetivo procede exclusivamente del índice maestro. La activación no
inspeccionó el código y por eso **no afirma todavía** qué endpoints, archivos,
consultas, escrituras, archivos binarios o pruebas forman estos dominios. Esa
determinación es trabajo de 6.0.

## Dependencias de capas anteriores

- Compuerta única `scripts/verify.py`, heredada de la capa 0. El último
  resultado registrado, tras las tres correcciones puntuales posteriores al
  cierre de la capa 5, es **669 pruebas, exit 0**, Ruff correcto y `pip check`
  íntegro; no se reprodujo durante esta activación documental. 6.0 debe
  reproducirlo antes de tocar nada.
- Ciclo de vida de conexiones, transacciones y timeouts definido en la capa 1.
  El valor operativo final de `DB_STATEMENT_TIMEOUT_MS` sigue **pendiente y
  aceptado**: el candidato de 15000 ms está documentado y **no aplicado**, y
  continúa vigente 30000.
- DB síncrona fuera del event loop y limitador compartido de capacidad
  establecidos en la capa 2. Esta capa no puede reintroducir trabajo bloqueante
  en el event loop ni cambiar esa capacidad sin una nueva auditoría. Sobre esa
  constante pesa además el pendiente heredado del 2026-08-17: se quedó sin
  ejemplo real que la respalde y se conserva como margen.
- Tenants versionados y alta reproducible cerrados en la capa 3. Quedan dos
  schemas, `tenant_2005` —el único de producción— y `tenant_colegio_1`
  —plantilla y demo—, ambos con 37 claves foráneas, 30 secuencias propias y 30
  migraciones registradas.
- Contratos de lectura financieros fijados por la capa 4 y protegidos por su
  caracterización, con los conteos 6/15 del estado de cuenta de reportes,
  1/13/37 de cuentas y 5/12/12 de cartera.
- Frontera de persistencia de pagos establecida en la capa 5:
  `app/repositories/pagos_repository.py` con 16 funciones que reciben el cursor.
  Es el patrón que esta capa debe seguir si extrae persistencia, incluida la
  regla de no crear abstracciones compartidas sin dos usos reales.
- La última evidencia de GitHub Actions corresponde a la capa 0. Hubo pushes
  autorizados el 2026-08-15 y el 2026-08-17, pero **no se ha obtenido evidencia
  de ningún run**; esa verificación permanece **pendiente y aceptada**. No se
  atribuye CI remota porque `HEAD` coincida con `origin/main`.

## Perfil de riesgo propio de esta capa

Estos dominios son mayores que los financieros y su perfil de riesgo cambia en
un punto que ninguna capa anterior tuvo: **tocan archivos, no solo filas**.

- ~~**Un rollback de datos no deshace un archivo ya escrito.**~~ **Refutado en
  6.0.** La activación anticipó, desde `PROMPT_CONTINUACION.md` y marcándolo
  como no verificado, que estos dominios escribirían archivos vía
  `app/services/storage.py`. **No es cierto**: los únicos consumidores de
  `storage` son `branding_controller.py` y `plan_de_clases_controller.py`.
  Ni los controladores ni las rutas de asignaciones y estudiantes lo mencionan.
  El rollback de esta capa vuelve a ser, como en la capa 5, de código y filas.
  Queda fijado por prueba para que una subcapa futura no lo introduzca sin
  advertirlo. **Esto no exime a la capa 7**: plan de clases sí escribe archivos.
- **Las 26 claves foráneas repuestas en la capa 3** pueden hacer fallar
  inserciones y borrados que antes pasaban en silencio. Es más probable aquí que
  en pagos: asignaciones y estudiantes son precisamente las tablas que esas
  claves relacionan.
- **`cobros.calcular_deudas_estudiante` ya se consume desde estudiantes**, y la
  capa 4 fijó contratos de lectura que dependen de él. Mover o alterar ese
  camino puede romper informes financieros sin que fallen las pruebas del
  dominio que se está tocando. Registrado en documentación; a verificar en 6.0.
- **El historial académico no se recalcula.** Notas, asistencia y boletines son
  datos acumulados; un error de escritura no produce un informe equivocado sino
  un expediente equivocado.
- Los permisos aquí no son uniformes como en pagos, donde solo alcanzaba
  `rol == 'admin'` estricto. Estos dominios los consumen también profesores, así
  que el inventario de roles y ownership de 6.0 es parte del contrato de
  seguridad, no un detalle.

## Alcance autorizado

- Inventariar entradas HTTP, reglas, escrituras, consultas, archivos, pruebas y
  consumidores de asignaciones y estudiantes mediante búsquedas dirigidas.
- Caracterizar antes de extraer: rutas, métodos, payloads, status codes,
  permisos, roles, tenant, ownership, relaciones académicas, archivos,
  historial, orden, nulos, transacciones y errores.
- Separar progresivamente HTTP, reglas, servicios y persistencia, **un dominio a
  la vez y en subcapas**, con pruebas de caracterización previas a cada
  extracción importante.
- Contar y comparar consultas y escrituras críticas antes y después.
- Medir con `EXPLAIN ANALYZE` conforme al criterio corregido en la capa 4:
  `SELECT` en producción bajo transacción `READ ONLY` cerrada con `rollback`.
  Ninguna medición puede escribir.

## Fuera de alcance

- Una extracción conjunta de asignaciones y estudiantes. El índice lo prohíbe
  expresamente: cada dominio va en sus propias subcapas.
- El resto de dominios, que pertenecen a la capa 7, salvo la lectura mínima
  indispensable para caracterizar un contrato consumido desde aquí.
- Los siete hallazgos abiertos de la capa 5, incluido el **paso 2 de la clave de
  idempotencia** y el cambio de status codes a 500. Están registrados en
  `05_PAGOS_TIPOS_PAGO.md` y **no entran por inferencia**.
- El trabajo registrado en `PROMPT_CONTINUACION.md` bajo «trabajo fuera del
  alcance de la capa activa»: colisión de mayúsculas en reportes,
  `/estado-cuenta/curso`, los 14 índices duplicados, la deduplicación de
  `_tabla_pagos_aplicaciones_existe` y la auditoría de capacidad de la capa 2.
- Cambiar rutas, payloads, status codes, permisos, roles, ownership, reglas
  académicas, orden o semántica transaccional.
- Cambiar PostgreSQL, `psycopg2`, el modelo de schemas tenant, el pool, los
  timeouts, el limitador de concurrencia, el ORM, el driver o el almacenamiento
  de archivos.
- Migraciones reales, DDL, DML, deploy, commit o push.

## Invariantes

- Métodos, paths, status codes y forma exacta de las respuestas permanecen
  idénticos.
- Permisos, roles, ownership y aislamiento entre tenants se conservan sin
  excepción. Incluye los caminos de profesor, no solo los de admin.
- Relaciones académicas, historial, archivos adjuntos y su nomenclatura
  conservan su resultado actual.
- Los límites de transacción se conservan: qué se confirma junto, qué se
  revierte junto y quién es dueño de `commit`, `rollback`, cursor y conexión,
  conforme a la capa 1.
- Ninguna operación DB síncrona vuelve al event loop ni se altera el limitador
  compartido sin medir de nuevo su capacidad.
- Los contratos de lectura financieros fijados por la capa 4 siguen pasando su
  caracterización, incluidos los conteos 6/15, 1/13/37 y 5/12/12.
- El SQL de dominio se conserva hasta que una subcapa autorice, con
  caracterización previa, un cambio concreto.
- Ninguna escritura de archivos cambia de momento, de nombre ni de destino sin
  una decisión explícita y un rollback documentado.

## Línea base registrada en 6.0

| Comprobación | Comando | Resultado |
|---|---|---|
| Pruebas específicas | `.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_asignaciones_estudiantes_caracterizacion.py tests\test_asignaciones_activo.py tests\test_asignaciones_controlador.py tests\test_asignaciones_pagination.py tests\test_estudiantes_controlador.py tests\test_estudiantes_pagination.py tests\test_profesores_controlador.py` | **67 pasaron** en 0,68 s |
| Suite global | `.\venv\Scripts\python.exe scripts\verify.py` | **708 pasaron**, 5 warnings heredadas, exit 0 |
| Ruff | Ejecutado por la compuerta global y sobre la prueba nueva | **Correcto** |
| Dependencias | Ejecutado por la compuerta global | **Íntegras** |

La compuerta heredada se reprodujo antes de tocar nada: **669 pruebas, exit 0**,
coincidiendo con lo registrado tras las correcciones puntuales de la capa 5. La
suite pasó de **669 a 708** con la caracterización de 6.0.

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 6.0 | Inventario, contratos, caracterización y línea base de consultas y escrituras | **Cerrada** |
| 6.1 | Extraer la persistencia de **estudiantes** sin cambiar SQL, conteos ni transacción | **Cerrada** |
| 6.2 | Cerrar la frontera de estudiantes: las cuatro lecturas de otros dominios que quedan en `detalles` | **Cerrada** |
| 6.3 | Extraer la persistencia de las **escrituras de `asignaciones`** | **Cerrada** |
| 6.4 | Extraer las **lecturas de `asignaciones`**: validaciones, listados, disponibilidad y orden | **Cerrada** |
| 6.5 | El SQL inline de la ruta `/mis-clases`, el código heredado y el **cierre de la capa** | **Cerrada** |

6.1 quedó definida desde lo que 6.0 midió, y toma **estudiantes primero** por la
razón registrada en Decisiones. El desglose de asignaciones se deja sin decidir
para no inventar detalles antes de tiempo. Las subcapas innecesarias se marcarán
`No aplica` con explicación.

Nunca se ejecutan dos subcapas en el mismo turno.

## Subcapa activa: trabajo exacto de 6.0

1. Confirmar `main`, árbol limpio y que todo commit posterior al base
   `589cb6d1391161c692a6f24aee9d523317cbb1ce` esté explicado en esta bitácora.
2. Reproducir la compuerta heredada y determinar las pruebas específicas sin
   ampliar el alcance.
3. Localizar mediante búsquedas dirigidas únicamente la documentación, entradas
   HTTP, archivos fuente y pruebas de asignaciones y estudiantes.
4. Inventariar responsabilidades y dependencias actuales sin mover código:
   HTTP, reglas, persistencia, cálculos, escrituras, archivos y efectos
   laterales.
5. Registrar los contratos observables exactos: rutas, métodos, payloads, status
   codes, permisos por rol, tenant, ownership, relaciones académicas, historial,
   archivos, orden, nulos, transacciones y errores.
6. Comprobar con evidencia los tres puntos que esta activación registra **sin
   verificar**: si estos dominios escriben archivos vía `app/services/storage.py`
   y en qué momento respecto del `commit`; si `calcular_deudas_estudiante` se
   consume desde estudiantes y qué contratos de la capa 4 dependen de ello; y
   qué claves foráneas de la capa 3 afectan a estas tablas.
7. Caracterizar con pruebas los caminos que una extracción posterior pueda
   alterar, incluidas las escrituras y los archivos. 6.0 no autoriza una
   extracción ni un cambio de producto.
8. Medir o instrumentar herméticamente el número de consultas y escrituras de
   los caminos críticos; no optimizarlos todavía.
9. Ejecutar las pruebas específicas, Ruff del alcance, la compuerta global y
   `git diff --check`; revisar que el diff pertenezca solo a 6.0.
10. Actualizar esta bitácora, definir 6.1 con la evidencia obtenida y detenerse
    sin iniciarla.

## Inventario y contratos fijados en 6.0

La frontera son **19 entradas HTTP**: **12 de asignaciones** y **7 de
estudiantes**. Ninguna declara `response_model` ni `status_code` explícito.

**El modelo de permisos NO es uniforme, a diferencia de pagos.** El router de
estudiantes exige `get_current_active_admin` a nivel de router, igual que pagos.
El de asignaciones **no tiene dependencia de router**: cada entrada declara la
suya, y **dos de las doce** usan `get_current_user` con
`require_profesor_scope`. Ahí sí hay ownership real: un profesor solo puede
consultar lo suyo y recibe 403 si pide lo de otro; un admin pasa siempre.

| Entrada | Permiso | Contrato observable que debe conservarse |
|---|---|---|
| `GET /asignaciones/lista` | admin | Lista heredada sin `limit`; con `limit`, `{total,limit,offset,items}`. Filtros por profesor, curso, materia y búsqueda |
| `POST /asignaciones` | admin | `{mensaje, id}`; duplicada **409**, regla de negocio **400** |
| `PUT /asignaciones/{id}` | admin | `{mensaje}`; duplicada **409**, regla **400** |
| `DELETE /asignaciones/{id}` | admin | `{mensaje}`; inexistente **404**. **Desactiva, no borra** |
| `DELETE /asignaciones/{profesor_id}/{curso_id}` | admin | `{mensaje}` siempre 200, incluso si no encuentra nada |
| `GET /hora/horarios-admin` | admin | Lista ordenada por día de la semana y hora |
| `GET /profesores/{id}/disponibilidad` | admin | `{profesor_id, dia, jornadas}` con rangos libres calculados |
| `GET /profesores/{id}/cursos` | **profesor propio o admin** | Lista `{curso_id, nombre}` |
| `GET /cursos/{id}/profesores` | admin | Lista `{profesor_id, nombre, apellido}` |
| `GET /cursos/{id}/orden-boletin` | admin | `{curso_id, items}` agrupado por materia |
| `PUT /cursos/{id}/orden-boletin` | admin | `{mensaje, curso_id, items}`; **reemplaza** el orden completo. Regla **400** |
| `GET /mis-clases/{profesor_id}` | **profesor propio o admin** | Lista con `id`, `horario_id`, materia, curso, jornada y horario. **SQL inline en la ruta** |
| `POST /estudiantes` | admin | `{mensaje, id}`. La ruta reescribe el mensaje del controlador |
| `GET /estudiantes` | admin | Lista heredada sin `limit`; con `limit`, paginado. Filtro `estado`, **422** si es inválido |
| `GET /estudiantes/{id}` | admin | **Todas las columnas de la tabla** (`SELECT *`); inexistente devuelve `null` con 200 |
| `GET /estudiantes/{id}/detalles` | admin | `{notas, promedio_general, inasistencias, observaciones, deudas, total_deuda, productos_inventario}` y `errores` por sección fallida |
| `GET /estudiantes/{id}/deudas` | admin | `{estudiante_id, curso_id, deudas, total_deuda}`; **404** si `ValueError` |
| `PUT /estudiantes/{id}` | admin | `{mensaje, id}`; inexistente devuelve `{mensaje}` sin `id` y **200** |
| `PATCH /estudiantes/{id}/estado` | admin | `{mensaje, id, estado}`; inexistente **404** |

- Tenant por `search_path` desde el JWT, igual que en las capas anteriores.
- El orden de declaración importa en estudiantes: `/estudiantes/{id}/detalles` y
  `/estudiantes/{id}/deudas` se declaran **antes** que `/estudiantes/{id}`.
- Estados de estudiante: `activo`, `retirado`, `egresado`, `inactivo`, más
  `todos` solo como filtro de listado.

### Tablas escritas y propiedad transaccional

**Solo dos tablas reciben escritura**: `asignaciones` y `estudiantes`. Es un
dominio mucho más contenido de lo que su tamaño en líneas sugiere.

- **Ninguna de las dos se borra nunca.** Desactivar una asignación es
  `SET activo = FALSE`; retirar a un estudiante es `SET estado = ...`. No existe
  un solo `DELETE FROM` en ninguno de los dos controladores, y una prueba
  estructural lo fija.
- Conviven tres estilos de ciclo de vida: `get_cursor()`,
  `get_cursor(commit=True)` y `get_connection()` con `try/finally` manual. Los
  caminos de escritura complejos usan el tercero y son dueños de `commit` y
  `rollback`.
- Como en pagos, varios caminos salen con `return {"error": ...}` **sin
  `rollback` explícito**: confían en que la devolución al pool revierta.

### Claves foráneas que la capa 3 repuso sobre estos dominios

**7 apuntan a `asignaciones`** —una es la autorreferencia
`asignacion_academica_id`, y las otras seis son `asistencia`,
`boletin_cabecera`, `notas`, `notas_detalle`, `plan_de_clases` y
`planeador_anual`, todas con `ON DELETE CASCADE` salvo `plan_de_clases`—.
**9 apuntan a `estudiantes`**: `asistencia`, `boletin_cabecera`, `matriculas`,
`notas`, `notas_detalle`, `pagos`, `pagos_aplicaciones`,
`tipos_pagos_estudiantes` y `ventas`.

Que ambos dominios desactiven en vez de borrar es exactamente lo que hace
inocuas esas 16 claves. Un `DELETE` introducido por una extracción borraría en
cascada notas y boletines, o fallaría contra la clave.

### Dependencia con los contratos de la capa 4, verificada

`estudiante_controller` **importa y usa `cobros.calcular_deudas_estudiante`** en
dos sitios: `obtener_deudas_estudiante_controller` y la sección de deudas de
`obtener_detalles_estudiante_controller`. El supuesto que la activación registró
sin verificar queda **confirmado**. Los dos caminos reciben el cursor abierto por
estudiantes, así que una extracción que cambie la propiedad del cursor afecta al
cálculo financiero que la capa 4 fijó.

### Asignaciones es una dependencia transversal de todo el sistema académico

Es la diferencia más importante con la capa 5. `pagos` era un dominio terminal;
`asignaciones` no. `app/services/asignacion_academica.py` expone
`resolver_asignacion_academica_id_cursor` y lo consumen **nueve módulos**:
`boletin_controller`, `dashboard_controller`, `asistencia_controller`,
`notas_controller`, `observacion_controller`, `planilla_controller`,
`planilla_excel_controller`, `planeador_anual_controller` y
`plan_de_clases_repository`, además de `routes/observaciones.py`. Cambiar el
concepto de «asignación académica» afecta a todos.

## Línea base de consultas y escrituras

Medida herméticamente con dobles de cursor y conexión, y **fijada por pruebas**,
no escrita a mano. Los conteos excluyen autenticación, `search_path` y la
sentencia de timeouts de cada checkout.

| Camino | Consultas | de ellas escrituras |
|---|---:|---:|
| `POST /asignaciones`, con horario, primera del grupo | **12** | 2 |
| `POST /asignaciones`, heredando asignación académica | 11 | 1 |
| `POST /asignaciones`, sin horario | 8 | 2 |
| `PUT /asignaciones/{id}`, solo cambia el horario | 10 | 1 |
| `PUT /asignaciones/{id}`, bloqueado por historial | 6 | 0 |
| `PUT /cursos/{id}/orden-boletin`, dos materias | 6 | 3 |
| `GET /cursos/{id}/orden-boletin` | 1 | 0 |
| `GET /estudiantes` con `limit` | 2 | 0 |
| `GET /estudiantes/{id}/detalles` | 4 propias + las de cobros | 0 |
| `asignacion_tiene_historial`, ninguna tabla con la columna | 7 | 0 |
| `asignacion_tiene_historial`, todas con la columna | hasta **14** | 0 |

Lectura del resultado, sin optimizar todavía:

- **No hay N+1 por estudiante** en ninguno de los dos dominios, igual que en
  pagos. El coste está en la profundidad por petición.
- Sí hay dos costes **proporcionales a otra cosa**: el orden del boletín crece
  con el número de materias reordenadas —un `UPDATE` por materia—, y
  `asignacion_tiene_historial` cuesta **dos consultas por cada una de sus siete
  tablas**, una para preguntar si existe la columna y otra para buscar filas.
- Un alta de asignación gasta **diez de sus doce consultas en validar**: tres
  estados activos, dos unicidades, la asignación académica, el orden, la jornada
  del curso y los dos cruces de horario. Es el mismo perfil que el pago simple
  de la capa 5.

## Criterios de cierre de la subcapa 6.0

- Los dos dominios y sus consumidores están inventariados con archivos y puntos
  de entrada concretos, sin lectura global innecesaria, y **separados entre sí**:
  el inventario debe dejar claro dónde termina uno y empieza el otro.
- Los contratos HTTP, de permisos por rol, tenant, ownership, académicos, de
  archivos y de transacción están enumerados y protegidos por caracterización
  suficiente.
- Las escrituras críticas y las escrituras de archivos están identificadas con
  una línea base reproducible, no por inferencia.
- La dependencia con los contratos de lectura de la capa 4 está registrada con
  evidencia.
- No se modificó producto ni se inició una extracción.
- Pruebas específicas, Ruff, compuerta global y `git diff --check` terminan
  correctamente, y el diff es exclusivo de 6.0.
- La subcapa 6.1 queda definida y no iniciada.

Los siete criterios se cumplieron. El diff de 6.0 contiene **un solo archivo
nuevo** y **ningún archivo rastreado modificado**, igual que el de 5.0.

## Hallazgos de 6.0, registrados y sin corregir

Ninguno se corrige por inferencia: son hallazgos del inventario, no defectos de
la subcapa. Corregir cualquiera exige una decisión explícita del usuario.

- **Código muerto duplicado, y las dos copias divergen.**
  `obtener_clases_profesor_controller` está definida **dos veces**, en
  `asignacion_controller.py` y en `profesor_controller.py`, y **ninguna tiene
  consumidor de producción**: una guardia estructural recorre el AST de todo
  `app/` y no encuentra una sola llamada. La ruta `/mis-clases/{profesor_id}`,
  que sería su consumidora natural, lleva su propio SQL inline. Además **no son
  la misma función**: la de `profesor_controller` no filtra por `activo` ni por
  el estado del curso o la materia, y devuelve la clave `asignacion_id` donde la
  otra devuelve `id`. Las dos tienen pruebas propias que las mantienen vivas.
  Retirarlas exige decisión explícita; la guardia queda para que falle si
  alguien las conecta sin darse cuenta.
- **Hay SQL de dominio en la capa de rutas.** `GET /mis-clases/{profesor_id}`
  ejecuta en `app/routes/asignaciones.py` un `SELECT` de cuarenta líneas con
  tres `JOIN`, un `LEFT JOIN` reflexivo sobre `asignaciones` y el mismo `CASE`
  de ordenación por día que usa el controlador. Ningún dominio migrado antes
  tenía SQL fuera de controlador o repositorio. Qué hacer con él es decisión de
  una subcapa posterior; 6.0 solo lo fija con una prueba.
- **El alta y la edición de asignaciones no toman ningún lock.** La validación
  de cruce de horarios lee, decide y escribe sin `pg_advisory_xact_lock`, sin
  `FOR UPDATE` y bajo el `READ COMMITTED` por defecto. Dos peticiones
  simultáneas pueden validar contra el mismo estado y crear **dos clases
  solapadas** para el mismo profesor o el mismo salón. La restricción `UNIQUE`
  que existe en la base —cuyo `UNIQUE_VIOLATION` el controlador traduce a 409—
  solo cubre el duplicado exacto, **no el solapamiento**. Es el mismo patrón que
  el hueco de idempotencia que la capa 5 encontró en `POST /pagos`, y aquí no se
  ha corregido ni a medias.
- **`asignacion_tiene_historial` cuesta hasta catorce consultas** para responder
  sí o no: por cada una de sus siete tablas pregunta primero a
  `information_schema.columns` si existe la columna y después busca una fila.
  Ninguna de las dos se cachea entre tablas ni entre peticiones.
- **`GET /estudiantes/{id}` devuelve `SELECT *`.** El contrato observable de esa
  entrada es **el esquema entero de la tabla**: añadir una columna cambia la
  respuesta de la API sin tocar el código, y quitarla la rompe. Es el único
  endpoint de los diecinueve cuyo payload no está enumerado en el código.
- **Dos rarezas de status code**, conservadas: `PUT /estudiantes/{id}` sobre un
  estudiante inexistente responde **200** con `{"mensaje": "Estudiante no
  encontrado"}` y sin `id`, mientras que `PATCH .../estado` sobre el mismo
  estudiante responde **404**. Y `DELETE /asignaciones/{profesor_id}/{curso_id}`
  responde **200** aunque no encuentre nada, mientras que
  `DELETE /asignaciones/{id}` responde 404.
- **`POST /estudiantes` descarta el mensaje del controlador.** El controlador
  devuelve `{"mensaje": "Estudiante creado correctamente", "id": ...}` y la ruta
  construye su propia respuesta con `{"mensaje": "Estudiante creado", "id": ...}`.
  El cliente ve el segundo; el primero solo lo ven las pruebas.
- **`verificar_cruce_horario` y `verificar_cruce_horario_editar` son casi
  idénticas**: la segunda solo añade `AND id != %s`. Es el mismo caso de dos
  literales gemelos que la capa 5 resolvió con autorización explícita, y no se
  toca sin ella.
- **f-strings en SQL, hoy no inyectables.** `verificar_cruce_horario` interpola
  `campo_id`, validado antes contra un conjunto de dos valores;
  `asignacion_tiene_historial` interpola el nombre de tabla desde una lista fija;
  y los listados de estudiantes y asignaciones interpolan el `WHERE` construido
  a partir de literales del propio código, con los valores siempre
  parametrizados. Queda anotado como guarda: ninguna extracción futura debe
  abrir esas listas a entrada del cliente.
- **La comparación de horas es textual.** Los cruces comparan cadenas `HH:MM`
  con `<` y `>`, lo que funciona solo mientras el formato sea de 24 horas con
  cero a la izquierda. `normalizar_hora` lo garantiza cortando a cinco
  caracteres, pero un valor guardado como `7:00` rompería la comparación sin
  lanzar ningún error.

## Subcapa 6.1 — trabajo exacto, definido y NO iniciado

Extraer la persistencia de **estudiantes**, y solo de estudiantes, siguiendo el
patrón que la capa 5 dejó probado.

1. Revalidar Git y limitar la inspección a `estudiante_controller.py`, sus rutas
   y sus pruebas. **No inspeccionar asignaciones**: son de 6.2 en adelante.
2. Conservar la caracterización de 6.0 y ampliarla solo si una extracción
   concreta lo exige, antes de mover producto.
3. Extraer las sentencias SQL de `estudiantes` a
   `app/repositories/estudiantes_repository.py`, con funciones que **reciben el
   cursor existente** y no abren, cierran, confirman ni revierten recursos, igual
   que `pagos_repository`.
4. Conservar byte por byte las cadenas SQL, sus parámetros y su orden. Si
   aparecen dos literales idénticos salvo la sangría, **no unificarlos sin
   autorización explícita**: es una decisión del usuario, no del asistente.
5. Decidir **con evidencia** qué hacer con las dos consultas que hoy construyen
   su `WHERE` con f-string, y con el `SELECT *` de `obtener_estudiante_por_id`:
   moverlos tal cual es lo esperado, cambiarlos no está autorizado.
6. No tocar asignaciones, `cobros.py`, pagos, reportes, cartera, cuentas,
   timeouts ni la base de datos. **No corregir ninguno de los diez hallazgos de
   6.0**, ni las dos rarezas de status code, ni el mensaje que la ruta reescribe.
7. Verificar que los conteos de 6.0 no cambian y que los de la capa 4 siguen
   intactos, con el comparador AST contra el commit base de la capa exigiendo
   conjunto de SQL idéntico.
8. Ejecutar pruebas específicas, Ruff del alcance, compuerta global y
   `git diff --check`; documentar y detenerse antes de 6.2.

## Subcapa 6.2 — trabajo exacto, definido y NO iniciado

Cerrar la frontera de estudiantes antes de tocar asignaciones.

1. Revalidar Git y limitar la inspección a lo que 6.1 dejó fuera de
   `estudiante_controller.py`: las **cuatro lecturas** de
   `obtener_detalles_estudiante_controller` sobre `notas_detalle`, `asistencia`,
   `observaciones` y `ventas`/`ventas_detalle`/`inventario`.
2. Decidir **con evidencia, no por inferencia**, dónde viven. Son tablas de
   otros dominios leídas desde estudiantes, el mismo caso que `ventas` en la
   capa 5: pueden quedarse en `estudiantes_repository`, ir a una frontera propia
   o permanecer en el controlador. Comprobar antes si existe ya un repositorio
   de alguno de esos dominios y cuántos consumidores reales tendría.
3. Conservar la caracterización de 6.0 y ampliarla antes de mover producto si
   algún camino no está cubierto, en particular el promedio general de notas.
4. Conservar el texto SQL, sus parámetros y su orden. Mantener en el controlador
   la degradación por secciones: cada `except` con su `rollback` y su entrada en
   `errores` sigue siendo suya.
5. No tocar asignaciones, `cobros.py`, pagos, reportes ni la base de datos. **No
   corregir ninguno de los diez hallazgos de 6.0.**
6. Volver a ejecutar el comparador AST contra el commit base de la capa
   exigiendo conjunto de SQL idéntico, y verificar que los conteos de 6.0 y los
   de la capa 4 no cambian.
7. Ejecutar pruebas específicas, Ruff del alcance, compuerta global y
   `git diff --check`; documentar y detenerse antes de 6.3.

## Subcapa 6.3 — trabajo exacto, definido y NO iniciado

Primera subcapa del **segundo** dominio. Estudiantes queda terminado; ahora
empieza asignaciones, y empieza por sus escrituras.

1. Revalidar Git y limitar la inspección a las escrituras de `asignaciones` en
   `asignacion_controller.py`: el `INSERT` del alta, el `UPDATE` de
   autorreferencia, el `UPDATE` de la edición, los dos `UPDATE` de
   `SET activo = FALSE` y los dos `UPDATE` de `orden_boletin`.
2. Conservar la caracterización de 6.0 y ampliarla **antes** de mover si algún
   camino de escritura no está cubierto.
3. Extraer solo esas sentencias a `app/repositories/asignaciones_repository.py`,
   con funciones que **reciben el cursor existente**, siguiendo el patrón ya
   aplicado dos veces en esta capa.
4. Conservar byte por byte las cadenas SQL, sus parámetros y su orden. El
   controlador sigue siendo dueño de conexión, cursor, `commit`, `rollback`,
   cierres, validaciones de horario y jornada, y la traducción de
   `IntegrityError` a `AsignacionDuplicadaError`.
5. **No mover las lecturas** —validaciones de estado activo, unicidad, cruces,
   disponibilidad, listados y orden del boletín—: son de 6.4, y así el diff de
   esta subcapa se puede revisar entero.
6. No tocar `app/services/asignacion_academica.py`, del que dependen nueve
   módulos, ni el SQL inline de `app/routes/asignaciones.py`, ni estudiantes, ni
   la base de datos. **No corregir ninguno de los diez hallazgos de 6.0**, en
   particular ni el código muerto duplicado ni la ausencia de lock.
7. Volver a ejecutar el comparador AST contra el commit base de la capa
   exigiendo conjunto de SQL idéntico, y verificar que los conteos de 6.0 —12,
   11, 8, 10, 6 y 6— no cambian.
8. Ejecutar pruebas específicas, Ruff del alcance, compuerta global y
   `git diff --check`; documentar y detenerse antes de 6.4.

## Subcapa 6.4 — trabajo exacto, definido y NO iniciado

1. Revalidar Git y limitar la inspección a las **lecturas** de `asignaciones` en
   `asignacion_controller.py`: las tres guardas de estado activo —profesor, curso
   y materia—, `validar_profesor_responsable_materia`, `validar_horario_unico`,
   `obtener_asignacion_academica_id`, `obtener_orden_boletin_materia_curso`,
   `validar_jornada_curso`, los dos `verificar_cruce_horario`, la lectura del
   estado actual al editar, los dos listados, el conteo del paginado, la
   disponibilidad del profesor, el orden del boletín y las dos consultas de
   `asignacion_tiene_historial`.
2. Conservar la caracterización de 6.0 y ampliarla antes de mover si algún camino
   de lectura no está cubierto.
3. Decidir **con evidencia** qué hacer con las lecturas que interpolan un
   fragmento con f-string: `verificar_cruce_horario` y su gemela reciben el
   nombre de columna, `asignacion_tiene_historial` recibe el nombre de tabla, y
   los listados y validaciones construyen filtros opcionales. Lo esperado es
   moverlas conservando el texto; **abrir esas listas a entrada del cliente no
   está autorizado en ningún caso**.
4. Decidir **con evidencia** si las dos consultas de `asignacion_tiene_historial`
   pertenecen al repositorio o se quedan: la de `information_schema.columns` es
   introspección de esquema, y 5.3 decidió con evidencia que ese tipo de guarda
   vive junto al código que la necesita. Registrar la decisión antes de mover.
5. Conservar byte por byte las cadenas SQL, sus parámetros y su orden. El
   controlador sigue siendo dueño de conexión, cursor, `commit`, `rollback`,
   cierres, cálculo de rangos libres y traducción de errores.
6. No tocar `app/services/asignacion_academica.py`, del que dependen nueve
   módulos, ni el SQL inline de `app/routes/asignaciones.py`, ni estudiantes, ni
   la base de datos. **No corregir ninguno de los diez hallazgos de 6.0.**
7. Volver a ejecutar el comparador AST contra el commit base de la capa
   exigiendo conjunto de SQL idéntico, y verificar que los conteos de 6.0 no
   cambian.
8. Ejecutar pruebas específicas, Ruff del alcance, compuerta global y
   `git diff --check`; documentar y detenerse antes de 6.5.

## Subcapa 6.5 — trabajo exacto, definido y NO iniciado

Última subcapa prevista. Cierra la capa, así que ejecuta también la compuerta
global y documenta staging, rollback y verificación manual.

1. Revalidar Git y limitar la inspección a lo que queda: el `SELECT` inline de
   `GET /mis-clases/{profesor_id}` en `app/routes/asignaciones.py` y la única
   sentencia que conserva el controlador, la de `information_schema.columns`.
2. Decidir **con evidencia** qué hacer con el SQL de la ruta. Ningún dominio
   migrado antes tenía SQL en la capa HTTP. Es una consulta de dominio sobre
   `asignaciones`, así que moverla al repositorio es lo coherente, pero hay que
   comprobar antes si su texto coincide con alguna de las funciones que ya
   existen y caracterizar la ruta si no lo está.
3. Confirmar que `tabla_columna_existe` **se queda**, conforme a lo ya decidido
   en 6.4 y al precedente de 5.3, y dejarlo registrado como decisión firme y no
   como pendiente.
4. Buscar código heredado que haya quedado sin consumidores tras las cuatro
   extracciones y retirarlo **solo si se demuestra huérfano**. Las dos copias de
   `obtener_clases_profesor_controller` ya estaban muertas antes de la capa: su
   retirada es un hallazgo de 6.0 y **exige decisión explícita del usuario**, así
   que se le pregunta, no se decide.
5. No corregir el resto de hallazgos de 6.0 —la ausencia de lock, el `SELECT *`,
   las rarezas de status code— salvo autorización explícita.
6. Verificar que los conteos de 6.0 y los de la capa 4 no cambian, y ejecutar el
   comparador AST contra el commit base por última vez.
7. Ejecutar la **compuerta global completa**, `git diff --check` y la revisión de
   alcance.
8. Documentar staging, rollback y verificación manual de la capa; actualizar el
   índice maestro; marcar la capa **cerrada** y dejar la capa 7 **en espera**.
   **No activar la capa 7 sin orden explícita.**

## Staging, rollback y verificación manual de la capa 6

### Lo que esta capa hizo y no hizo

La capa 6 es **exclusivamente una refactorización**, igual que la 5. No añadió
funciones, no cambió reglas, no tocó rutas, payloads, status codes, permisos,
tenant, ownership, transacciones, timeouts, dependencias ni configuración. Y **no
abrió una sola conexión a PostgreSQL**: ni migraciones, ni DDL, ni DML, ni
lecturas de medición. Toda la caracterización se hizo con dobles.

La evidencia de que el comportamiento observable no cambió es doble:

1. un comparador AST contra el commit base `589cb6d` demuestra que las **42
   sentencias SQL distintas de asignaciones son las mismas**, ninguna perdida y
   ninguna nueva, con **42 de 42 literales byte a byte**; y las **11 de
   estudiantes**, con 11 de 11. En toda la capa **no hizo falta autorizar ni un
   solo cambio de texto SQL**, a diferencia de la capa 5, que necesitó dos;
2. **43 pruebas de caracterización** escritas antes de cada extracción fijan
   payloads, permisos por rol, conteos de consultas, `commit`, `rollback`,
   cierres y el historial académico. **Ninguna cambió de expectativa**; la única
   que falló fue la guardia que 6.0 dejó *deliberadamente* sobre el SQL inline de
   la ruta, que debía fallar cuando 6.5 lo moviera, y se sustituyó por su versión
   positiva.

### Rollback

**Es puramente de código.** No hay nada que deshacer en datos ni en esquema.
Revertir los commits de la capa hasta
`589cb6d1391161c692a6f24aee9d523317cbb1ce` devuelve los dos controladores y la
ruta a su versión anterior y elimina los dos repositorios nuevos. Como el SQL
ejecutado es equivalente, revertir no cambia el comportamiento observable.

**Diferencia con la capa 5**: el commit base de esta capa **ya está desplegado**,
así que revertir exigiría un push y un despliegue, no solo una operación local.

No cambiar los timeouts durante el rollback.

### Staging

No se usó un entorno de staging y **no se considera necesario** para esta capa,
por la misma razón que hace el rollback trivial: no hay cambio de esquema, de
datos ni de SQL. Un despliegue prudente solo necesita comprobar que la aplicación
arranca y que los caminos de escritura responden, que es lo que cubre la
verificación manual.

### Verificación manual: **hecha y correcta**

Es la única evidencia que no puede delegarse en un asistente, porque exige
reconocer datos reales. Se ofrecieron las tres opciones —ejecutarla, aceptarla
explícitamente como pendiente, o dejar la capa abierta sin decidir— y el usuario
**eligió ejecutarla**, igual que en las capas 4 y 5.

**Ejecutada por el usuario el 2026-08-17 y con resultado correcto.**

**Artefacto verificado**: la aplicación levantada **en local contra el árbol de
trabajo**, que incluía los cambios de 6.5 todavía sin commitear. Se confirmó
expresamente con el usuario contra qué código había probado **antes** de
registrarlo, porque el estado de Git admitía tres lecturas: `HEAD` en `d04a455`
sin 6.5, el árbol con 6.5 encima, y `origin/main` en `589cb6d`, que es lo que
corre en producción y **no contiene nada de esta capa**. Es la lección 10 que
dejó la capa 5, aplicada. Cubre por tanto **la capa 6 completa**, 6.0 a 6.5.

**Limitación registrada, no disimulada**: la verificación fue local. Al cerrar la
capa **no había push ni despliegue**: los seis commits viven solo en el checkout
y producción sigue corriendo `589cb6d`, el código anterior a la capa 6. La
verificación demuestra que el código refactorizado funciona ejercitado a mano;
**no** demuestra nada sobre el despliegue, que sigue pendiente y es
responsabilidad del usuario.

Esta limitación es aceptable aquí por lo que la capa es: una refactorización con
SQL equivalente demostrado y sin ningún acceso a la base de datos. En una capa
que cambiara comportamiento o tocara datos no lo sería.

Guion ejecutado, contra el árbol de trabajo local:

- **Asignaciones**: crear una asignación nueva y comprobar que aparece con su
  horario; crear una segunda del mismo profesor, curso y materia y comprobar que
  hereda el mismo grupo académico; intentar asignar la misma materia del curso a
  **otro** profesor y comprobar que sale el 409 con el nombre del responsable.
- **Horarios**: intentar una clase que se solape con otra del mismo profesor y
  otra del mismo salón, y comprobar los dos mensajes de error; intentar una clase
  fuera de la jornada del curso y comprobar el aviso.
- **Historial académico**, lo más importante: sobre una asignación que ya tenga
  notas, asistencia u observaciones, intentar cambiar profesor, curso o materia y
  comprobar que **se rechaza** pidiendo desactivar y crear otra; cambiar solo el
  horario de esa misma asignación y comprobar que **sí se permite**.
- **Desactivación**: desactivar una asignación con historial y comprobar que las
  notas y los boletines anteriores **siguen ahí**.
- **Orden del boletín**: reordenar las materias de un curso, guardar, recargar y
  comprobar que el orden persiste y que el boletín lo respeta.
- **Mis clases**: entrar como profesor y comprobar que `/mis-clases` sigue
  mostrando sus clases con jornada y horario, y que un profesor no puede
  consultar las de otro.
- **Estudiantes**: crear uno con todos sus campos y comprobar que **ninguno se
  desplaza** —el teléfono del padre en su sitio, no en el de la madre—; editarlo
  sin tocar el estado y comprobar que el estado se conserva; retirarlo y
  comprobar que desaparece del listado por defecto pero sigue en «todos».
- **Expediente**: abrir el detalle de un estudiante con notas, inasistencias,
  observaciones, deudas y cargos de inventario, y comprobar que las cinco
  secciones cuadran, en particular el promedio general y el saldo de un cargo
  abonado a medias.
- **Financiero**: abrir el estado de cuenta de la capa 4 y confirmar que las
  cifras siguen cuadrando.
- Comprobar todo en **los dos tenants**, sin mezclar datos.

## Criterios de cierre de la capa

- Todas las subcapas necesarias están cerradas o marcadas `No aplica` con
  justificación.
- Asignaciones y estudiantes quedaron separados **cada uno en sus subcapas**,
  con contratos estables, y no mediante una extracción conjunta.
- Permisos, relaciones académicas, archivos e historial están protegidos por
  caracterización y conservados.
- Los contratos del frontend y de la base de datos permanecen intactos.
- La compuerta global, Ruff, dependencias y `git diff --check` terminan
  correctamente.
- Staging, rollback y verificación manual están documentados; el rollback debe
  cubrir explícitamente los archivos, no solo las filas y el código.
- La capa 7 queda en espera y no se activa sin orden explícita del usuario.

## Decisiones

- Se usa `589cb6d1391161c692a6f24aee9d523317cbb1ce` como commit base porque es
  el `HEAD` limpio vigente de `main` y coincide con la referencia local
  `origin/main`. No se reutilizó ningún hash de memoria: se comprobó el `HEAD`
  real antes de registrarlo.
- El usuario eligió explícitamente continuar manteniendo pendientes la
  calibración de `DB_STATEMENT_TIMEOUT_MS` y la evidencia remota de GitHub
  Actions. Ninguna se marca como cumplida y ambas conservan su riesgo.
- La activación consume la autorización puntual que `PROMPT_CONTINUACION.md`
  guardaba para la capa 6; queda retirada de ese archivo con el mismo criterio
  aplicado a las capas 3, 4 y 5.
- El mismo turno corrigió, con autorización explícita, el estado de publicación
  de la capa 5, que el índice y su bitácora seguían declarando sin push. Ese
  trabajo es exclusivamente documental y está registrado en
  `05_PAGOS_TIPOS_PAGO.md`.
- El commit base **está publicado y desplegado**, no solo local. Es por tanto un
  punto de rollback real, pero revertir a él exigiría otro push y otro
  despliegue, no una operación local.
- El desglose de subcapas posteriores a 6.0 se dejó sin decidir hasta tener la
  evidencia del inventario. Con ella, 6.1 queda definida y el resto sigue
  abierto.
- **6.1 toma estudiantes primero, decidido en 6.0 con evidencia.** Los dos
  dominios no son comparables en riesgo: estudiantes escribe una sola tabla desde
  un controlador de 519 líneas y su única dependencia externa es
  `calcular_deudas_estudiante`; asignaciones escribe una tabla de la que
  **dependen nueve módulos** a través de `resolver_asignacion_academica_id_cursor`
  y concentra las reglas de horario, jornada, cruce e historial. Empezar por
  estudiantes valida el patrón de extracción sobre el dominio contenido antes de
  tocar el transversal. Alternativa descartada: empezar por asignaciones porque
  es «el dominio principal», que habría puesto el mayor riesgo en la primera
  extracción y contra la instrucción del índice de evitar una extracción masiva.
- **No se retiró el código muerto en 6.0**, aunque esté demostrado que no tiene
  consumidores. 6.0 es inventario y caracterización, y su diff debe ser un solo
  archivo nuevo. Retirar las dos copias de `obtener_clases_profesor_controller`
  toca dos módulos de producto y dos archivos de prueba, y exige una decisión
  explícita del usuario.
- **La caracterización se escribió con dobles, sin tocar PostgreSQL.** 6.0 no
  abrió una sola conexión a la base, igual que toda la capa 5.
- **6.1 no necesitó ninguna autorización de cambio de SQL.** A diferencia de 5.1
  y 5.2, donde dos pares de literales gemelos diferían solo en la sangría y hubo
  que pedir permiso para unificarlos, aquí **los once literales se conservan byte
  a byte**. Las cinco líneas del INSERT y el UPDATE que terminan en espacio se
  conservaron con `\x20` explícito, la técnica que 4.3 y 5.2 ya habían usado: el
  valor que recibe PostgreSQL no cambia y `git diff --check` queda limpio.
- **El filtro de estado se queda en el controlador, decidido en 6.1.**
  `_build_estado_filter` valida y lanza `ValueError`: es una regla de dominio,
  no persistencia. El repositorio recibe el `where_sql` ya construido y sus
  parámetros. Es la misma frontera que 5.3 fijó para las guardas de esquema.
  Alternativa descartada: mover el filtro al repositorio, que habría llevado
  allí una validación que produce el 422 de la ruta.
- **`obtener_estudiante` conserva el `SELECT *`.** Devuelve la fila y deja que el
  controlador lea `cursor.description` del cursor que él posee, porque es quien
  convierte columnas en payload. Cambiar el `SELECT *` por columnas explícitas
  sería un cambio de contrato observable y **no está autorizado** en esta capa.
- **Las cuatro lecturas de otros dominios NO se movieron en 6.1.** Las consultas
  de `obtener_detalles_estudiante_controller` sobre `notas_detalle`,
  `asistencia`, `observaciones` y `ventas` no tocan la tabla `estudiantes`. Es
  literalmente el caso que 5.1 dejó para 5.2 con `ventas`, y se resuelve igual:
  con evidencia, en la subcapa siguiente.
- **Dónde viven las cuatro lecturas del expediente, decidido en 6.2 con
  evidencia.** Van a `estudiantes_repository.py`, en un bloque propio rotulado
  como **el expediente de un estudiante**, no como persistencia de notas,
  asistencia, observaciones o ventas. Tres datos lo sostienen: existen cuatro
  repositorios —`estudiantes`, `pagos`, `plan_de_clases` y `reportes`— y **ninguno
  de esos dominios tiene el suyo**; esas tablas se leen hoy con SQL inline desde
  `dashboard`, `notas`, `planilla`, `boletin`, `asistencia` y `venta_controller`,
  cuya migración está **fuera del alcance de esta capa**, así que un repositorio
  nuevo tendría **un solo consumidor real**; y **ninguna de las cuatro consultas
  es un duplicado**, comprobado literal a literal: el promedio de estudiantes usa
  `ROUND(AVG(...), 1)` agrupando por materia, mientras dashboard usa
  `TRUNC(AVG(CAST(... AS numeric)), 2)` por estudiante y notas
  `COALESCE(AVG(...), 0)`. Es la misma decisión y el mismo criterio que 5.2
  aplicó al contacto de pagos con `ventas`. Si algún día existe un repositorio de
  esos dominios con dos consumidores reales, ese bloque es lo que se mueve.
  Alternativa descartada: dejarlas en el controlador, que habría dejado la
  frontera de estudiantes a medias sin ganar nada.
- **6.2 amplió la caracterización antes de mover**, de 39 a 43 casos. Los cuatro
  nuevos cubren lo que 6.0 no fijaba: que el promedio general es el promedio de
  los promedios por materia redondeado en Python —4,5 y 3,0 dan **3,8**, no 3,75—,
  el filtro `ILIKE 'ausente'` de la asistencia, la forma exacta y el orden de las
  observaciones, y que el saldo de un cargo **solo** se calcula si la venta está
  `Pendiente`. Se vieron pasar contra el producto anterior a mover.
- **Las dos formas de `SET activo = FALSE` NO se unificaron en 6.3.**
  `eliminar_asignacion_controller` la escribe en cuatro líneas y
  `eliminar_asignacion_por_id_controller` en una sola. Normalizando espacios son
  la misma sentencia, y el flujo de tokens que recibe PostgreSQL es idéntico, así
  que unificarlas sería legítimo —es el mismo caso que el usuario autorizó en 5.1
  y 5.2—. **No se hizo**, porque esta vez no se pidió la autorización: 6.3 no
  necesitaba el cambio para extraer, y conservar los dos literales mantiene el
  diff en lo estrictamente necesario. Quedan como dos funciones con una guardia
  de prueba que falla si alguien las unifica sin registrarlo.
- **`insertar_asignacion` y `actualizar_asignacion` no leen su `RETURNING`.**
  En el controlador el `execute` vive dentro de un `try/except IntegrityError` y
  el `fetchone` ocurre **después** del bloque, para que un duplicado se traduzca
  a 409 antes de intentar leer un resultado que no existe. Mover el `fetchone` al
  repositorio habría cambiado ese orden, así que se dejó donde estaba. Es la
  diferencia con `insertar_estudiante`, que sí devuelve el id porque allí no hay
  traducción de error en medio.
- **Las precondiciones sobre `profesor`, `cursos` y `materias` van al
  repositorio de asignaciones, decidido en 6.4 con evidencia.** No son
  persistencia de esos catálogos: son las preguntas que hay que responder antes
  de poder asignar. Se comprobó que **no existe** un repositorio de ninguno de
  los tres —hay cuatro: asignaciones, estudiantes, pagos, plan de clases y
  reportes— y que el patrón de estado activo que usan aparece **cuatro veces en
  este controlador y una sola vez fuera**, en `venta_controller` y con otro
  texto. Un repositorio de catálogos tendría por tanto un solo consumidor real.
  Es el criterio de 5.2 y 6.2. Alternativa descartada: dejarlas en el
  controlador, que habría partido la frontera sin motivo.
- **`tabla_columna_existe` se queda en el controlador, decidido en 6.4 con
  evidencia.** Consulta `information_schema.columns`, y la convención vigente del
  repositorio, fijada por 5.3 tras revisar `cobros.py` y
  `tipos_pagos_controller.py`, es que **la introspección de esquema vive junto al
  código que la necesita**, no en una frontera de persistencia. Es la única
  sentencia SQL que sigue inline en `asignacion_controller`.
- **Su pregunta hermana sí se movió.** `SELECT 1 FROM {tabla} WHERE
  asignacion_id` es una pregunta sobre **datos**, no sobre el esquema, así que
  pertenece al repositorio. Separar las dos mitades de
  `asignacion_tiene_historial` es deliberado: cada una va donde su naturaleza
  indica, y la función sigue orquestándolas en el controlador.
- **`buscar_curso_activo` y `buscar_curso_activo_para_orden` NO se unificaron.**
  Su texto solo difiere en la sangría, heredada de estar una en una función
  suelta y otra dentro de un `try`. Es el tercer par gemelo de la capa, y se
  trata igual que los dos anteriores: conservar ambos literales, porque unificar
  es una decisión del usuario.
- **El SQL de la función muerta también se movió.**
  `obtener_clases_profesor_controller` no tiene consumidores —6.0 lo demostró—,
  pero su lectura se extrajo igual para no dejar SQL inline a medias. Retirar la
  función sigue exigiendo decisión explícita y se plantea en 6.5.
- **La degradación por secciones se queda en el controlador**, decidido en 6.2.
  Los cinco `try/except` con su `rollback` y su entrada en `errores` son política
  de respuesta, no persistencia. El repositorio ejecuta y devuelve; quien decide
  que un fallo de notas no tumbe el expediente sigue siendo el controlador.

## Riesgos

- **Los archivos son el riesgo nuevo de esta capa.** Un rollback de código o de
  datos no deshace un archivo ya escrito ni recupera uno borrado. Cualquier
  subcapa que toque `storage` debe documentar su rollback de archivos **antes**
  de ejecutarse.
- Estos dominios son los más grandes del programa. El riesgo de una extracción
  conjunta masiva es real y el índice lo prohíbe; el desglose por dominio y
  subcapa es la mitigación, y debe respetarse aunque parezca más lento.
- Las 26 claves foráneas repuestas en la capa 3 relacionan precisamente estas
  tablas. Inserciones y borrados pueden fallar donde antes pasaban en silencio.
  Se documentará el comportamiento y no se cambiarán las claves por inferencia.
- Los contratos de lectura financieros de la capa 4 dependen de código que estos
  dominios consumen. Pueden romperse desde aquí sin que fallen las pruebas de
  asignaciones o estudiantes. La mitigación es verificar sus conteos y payloads
  en cada subcapa.
- Los permisos no son uniformes: intervienen roles distintos de `admin`. Un
  inventario incompleto de roles es un riesgo de seguridad, no de calidad.
- El historial académico es acumulado: un error de escritura produce un
  expediente equivocado, no un informe recalculable.
- Heredado de la capa 1: `DB_STATEMENT_TIMEOUT_MS` sigue sin calibrar contra
  volumen representativo y el deadline HTTP/proxy externo.
- Heredado de la capa 0: no hay evidencia de GitHub Actions posterior a esa
  capa. Las verificaciones locales no se presentarán como CI remota.
- Heredado de la capa 2: `MAX_DB_CONNECTIONS_PER_THREADPOOL_WORKER = 2` se
  quedó sin ejemplo real que la respalde y se conserva como margen. Si esta capa
  encontrara un camino que anida conexiones, es evidencia relevante y debe
  registrarse, no actuarse.
- Heredado de la capa 4: la credencial privilegiada compartida en chat sigue
  **sin rotar** y no debe reutilizarse.
- Heredado de la capa 5: siete hallazgos sin corregir, incluido `POST /pagos`
  sin clave de idempotencia. No se corrigen desde aquí.
- **Nuevo respecto a todas las capas anteriores salvo la 5**: el commit base ya
  está desplegado. Un push a `main` en este repositorio dispara el despliegue,
  así que la publicación de esta capa afectará a producción en cuanto ocurra.

## Registro de ejecución

### 2026-08-17 — activación de la capa

- Modo de acceso: mismo checkout local; Git validado directamente en
  `C:\Users\David\Documents\sistema_escolar_api`. No se usó GitHub para inferir
  el estado local.
- Autorización: orden explícita del usuario en este turno —«esta es la base
  589cb6d, solo documental, y activa la capa 6»—, coincidente con la
  autorización puntual que `PROMPT_CONTINUACION.md` conservaba para la capa 6 y
  cuya condición de caducidad se cumplía: el índice seguía sin capa activa y con
  la 6 en espera. La decisión sobre las verificaciones heredadas se pidió por
  separado y el usuario eligió **continuar aceptándolas como pendientes**.
- Rama acordada: `main`.
- Estado antes de escribir: árbol limpio, verificado con
  `git status --porcelain=v1`; `HEAD` y la referencia local `origin/main` en
  `589cb6d1391161c692a6f24aee9d523317cbb1ce`.
- Continuidad: el base de la capa 5,
  `f4d091329f84bcdd100b1bf0c70c02a0e32ee138`, existe y es ancestro de `HEAD`.
  Sus **diez** commits posteriores forman una historia lineal. Nueve estaban
  explicados en `05_PAGOS_TIPOS_PAGO.md`: activación `42c9960`, cierre de 5.0
  `7718c37`, 5.1 `ebc1bd8`, 5.2 `72fc12e`, 5.3 y cierre de la capa `dcf7ffd`,
  candado de registro `11565eb`, retiro del hallazgo de ownership `a464b59`,
  logger de fallos absorbidos `27df23c` y una sola conexión por upsert
  `544bd5c`. El décimo, `589cb6d`, **no tenía entrada**; se comprobó que es
  documental —un solo archivo, `PROMPT_CONTINUACION.md`, +21/−5— y quedó
  registrado en la bitácora de la capa 5 antes de activar.
- Estado remoto: el reflog registra `update by push` de `544bd5c` y de
  `589cb6d`. La capa 5 y sus tres correcciones puntuales **están publicadas**, al
  contrario de lo que el índice y su bitácora seguían afirmando. **No se
  consultó ni se atribuye ningún run de GitHub Actions**; esa evidencia sigue sin
  obtenerse.
- Ambigüedad encontrada y corregida antes de activar: el índice y la bitácora de
  la capa 5 declaraban «sin push ni despliegue» y dejaban «publicar la capa» como
  pendiente operativo, contradiciendo el reflog. Se informó al usuario, que
  autorizó explícitamente la corrección documental. Las líneas fechadas que
  describían el estado del 2026-08-16 se conservaron intactas, con una nota que
  advierte que ya no son el estado vigente.
- Archivos creados o modificados: esta bitácora,
  `docs/modularizacion/README.md`, `docs/modularizacion/05_PAGOS_TIPOS_PAGO.md`
  y `docs/modularizacion/PROMPT_CONTINUACION.md`.
- Código de producto, pruebas, consultas, configuración, dependencias y workflow
  inspeccionados o modificados: **ninguno**. No se inspeccionó código de
  asignaciones ni de estudiantes.
- Pruebas, migraciones, conexiones a PostgreSQL, acceso a producción, commit,
  push y deploy: **ninguno**.
- Comandos de precondición: `git rev-parse --show-toplevel`,
  `git branch --show-current`, `git status --porcelain=v1`, `git status -sb`,
  `git log --oneline`, `git rev-parse HEAD`, `git rev-parse origin/main`,
  `git merge-base --is-ancestor`, `git log --reverse` desde el base de la capa 5,
  `git show --stat 589cb6d` y `git reflog show origin/main`; todos con resultado
  coherente con la activación.
- Estado al cerrar el turno de activación: capa 6 **activa**; 6.0 **pendiente y
  no iniciada**.
- Siguiente acción exacta: ejecutar únicamente 6.0 conforme al trabajo exacto de
  arriba y detenerse antes de 6.1. *(Ejecutada en el turno siguiente; ver el
  cierre de 6.0 más abajo.)*

### 2026-08-17 — cierre de 6.0

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git validado directamente y no
  se usó GitHub para inferir el estado local.
- Precondición Git: rama `main`, **árbol limpio**, `HEAD`
  `2881b033b3d11f639117c84837a02e98060da079`. Entre la activación y este turno
  el usuario **commiteó** el trabajo documental: ese commit es exactamente la
  activación, cuatro archivos de `docs/modularizacion/`, y está explicado en
  esta bitácora. El commit base `589cb6d` existe y es ancestro; `origin/main`
  sigue en el base, así que hay **un commit local por delante, sin publicar**.
- Compuerta heredada reproducida antes de tocar nada: **669 pruebas, exit 0**,
  Ruff correcto y `pip check` íntegro. Coincide con lo registrado tras las
  correcciones puntuales de la capa 5.
- Inventario dirigido: `app/routes/asignaciones.py`, `app/routes/estudiantes.py`,
  `app/controllers/asignacion_controller.py`,
  `app/controllers/estudiante_controller.py`, `app/schemas/asignacion.py`,
  `app/services/asignacion_academica.py` y, solo para resolver la duplicación
  detectada, el fragmento de `app/controllers/profesor_controller.py` que define
  la función homónima. No se leyó historia global ni código de la capa 7.
- **Los tres supuestos que la activación registró sin verificar quedaron
  resueltos**: el de `storage` **refutado**, el de `calcular_deudas_estudiante`
  **confirmado** y el de las claves foráneas **confirmado y cuantificado** en 7
  hacia `asignaciones` y 9 hacia `estudiantes`.
- Caracterización añadida: `tests/test_asignaciones_estudiantes_caracterizacion.py`,
  **39 casos** sobre las 19 entradas, el historial académico, los conteos de
  consultas, el ciclo de vida transaccional y cuatro guardias estructurales.
  Código de producto y configuración modificados: **ninguno**.
- Las 39 pruebas se escribieron contra el código actual y **dos fallaron en su
  primera ejecución por un error del modelo de prueba, no del producto**: la
  secuencia de respuestas del doble no reflejaba que `validar_horario_unico`
  sale sin consultar cuando no hay horario, ni que la jornada del curso se valida
  después del rango institucional. Se corrigieron las pruebas, no el producto, y
  quedó fijado el conteo real de 8 consultas para el alta sin horario.
- Pruebas específicas: **67 pasaron** en 0,68 s sobre los siete archivos del
  dominio. La prueba nueva aislada: 39 pasaron en 0,35 s. Ruff del archivo
  nuevo: **correcto**.
- Compuerta global final: `.\venv\Scripts\python.exe scripts\verify.py`;
  **708 pruebas pasaron** en 2,33 s, 5 warnings heredadas, Ruff correcto,
  `pip check` sin dependencias rotas, exit 0. La suite pasó de 669 a 708.
- Medición: hermética, con dobles de cursor y conexión. Los conteos de once
  caminos quedan **fijados por aserciones**, no anotados en prosa. Los caminos
  que dependen de `cobros` se cuentan solo por sus consultas propias.
- Diff final: `git diff --check` en exit 0 y sin trailing whitespace en el
  archivo nuevo. El alcance es **un solo archivo nuevo** y **ningún archivo
  rastreado modificado**: no se tocó producto, rutas, payloads, status codes,
  permisos, tenant, ownership, SQL, transacciones, configuración ni
  dependencias.
- PostgreSQL, migraciones, producción, commit, push y deploy: **ninguno**. La
  evidencia de GitHub Actions posterior a la capa 0 continúa pendiente y no se
  atribuye CI remota.
- Estado: 6.0 **cerrada**; 6.1 **pendiente y no iniciada**.
- Siguiente acción exacta: ejecutar únicamente 6.1, extracción de la persistencia
  de estudiantes, y detenerse antes de 6.2. *(Ejecutada en el turno siguiente;
  ver el cierre de 6.1 más abajo.)*

### 2026-08-17 — cierre de 6.1

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git validado directamente y no
  se usó GitHub para inferir el estado local.
- Precondición Git: rama `main`, **árbol limpio**, `HEAD`
  `9e9b4dc`, el cierre de 6.0 que el usuario commiteó entre turnos y que
  contiene exactamente los tres archivos que 6.0 declaró. El commit base
  `589cb6d` existe y es ancestro; `origin/main` sigue en el base, así que hay
  **dos commits locales por delante, sin publicar**, ambos explicados aquí.
- Alcance inspeccionado y modificado: únicamente `estudiante_controller.py` y el
  repositorio nuevo. **No se inspeccionó asignaciones**, que es de 6.3 en
  adelante.
- Archivos de producto: `app/controllers/estudiante_controller.py` y el nuevo
  `app/repositories/estudiantes_repository.py`. **Pruebas modificadas: ninguna.**
- Implementación: **siete funciones** que reciben el cursor existente cubren los
  siete puntos de llamada contra la tabla `estudiantes`. El controlador pasó de
  **519 a 396 líneas** y ya no contiene SQL de esa tabla. Conserva conexión,
  cursor, `commit`, `rollback`, cierres, normalización de estado, construcción
  del filtro, formateo de payload y degradación por secciones.
- Equivalencia SQL verificada con un comparador AST **contra el commit base de la
  capa**, `589cb6d`: **11 sentencias distintas antes y 11 después, conjunto
  idéntico**, ninguna perdida y ninguna nueva, y **11 de 11 literales
  conservados byte a byte**. Doce puntos de llamada antes y doce después. No
  hizo falta ninguna autorización de cambio de texto SQL.
- El comparador dio un primer resultado con **cuatro falsos positivos**: contaba
  como SQL los docstrings del módulo nuevo, que mencionan `UPDATE` y `DELETE` en
  prosa. Se corrigió excluyendo los docstrings antes de comparar; el resultado
  de 11 de 11 es el de la versión corregida.
- SQL que queda inline en el controlador: **cuatro sentencias**, todas de
  `obtener_detalles_estudiante_controller` y **ninguna sobre la tabla
  `estudiantes`**: leen `notas_detalle`, `asistencia`, `observaciones` y
  `ventas`. Su ubicación se decide en 6.2 con evidencia.
- Conteos conservados: `GET /estudiantes` con `limit` sigue costando 2 consultas
  y `GET /estudiantes/{id}/detalles` 4 propias. Los de la capa 4 no se tocan.
- Pruebas específicas: **67 pasaron** en 0,67 s sobre los siete archivos del
  dominio, el mismo resultado que antes de extraer. **Ninguna prueba cambió de
  expectativa**, que es la señal de que caracterizar antes de extraer funcionó,
  igual que en 5.1.
- Ruff del alcance:
  `.\venv\Scripts\python.exe -m ruff check app\controllers\estudiante_controller.py app\repositories\estudiantes_repository.py`;
  **correcto**.
- Compuerta global final: `.\venv\Scripts\python.exe scripts\verify.py`;
  **708 pruebas pasaron** en 2,31 s, 5 warnings heredadas, Ruff correcto,
  `pip check` íntegro y exit 0. El total no cambia porque 6.1 no añadió pruebas.
- Revisión final: `git diff --check` en exit 0 y sin trailing whitespace en el
  archivo nuevo. El diff contiene exactamente dos archivos de producto, 13
  líneas añadidas y 135 eliminadas en el controlador. No hubo cambios en rutas,
  payloads, status codes, permisos, tenant, ownership, transacciones, timeouts,
  dependencias ni configuración.
- PostgreSQL, migraciones, producción, commit, push y deploy: **ninguno**. La
  evidencia de GitHub Actions posterior a la capa 0 continúa pendiente y no se
  atribuye CI remota.
- Estado: 6.1 **cerrada**; 6.2 **pendiente y no iniciada**.
- Siguiente acción exacta: ejecutar únicamente 6.2, decidir con evidencia dónde
  viven las cuatro lecturas de otros dominios, y detenerse antes de 6.3.
  *(Ejecutada en el turno siguiente; ver el cierre de 6.2 más abajo.)*

### 2026-08-17 — cierre de 6.2

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git validado directamente y no
  se usó GitHub para inferir el estado local.
- Precondición Git: rama `main`, **árbol limpio**, `HEAD` `69c0033`, el cierre de
  6.1 que el usuario commiteó entre turnos y que contiene exactamente los cuatro
  archivos que 6.1 declaró. El commit base `589cb6d` existe y es ancestro;
  `origin/main` sigue en el base, así que hay **tres commits locales por delante,
  sin publicar**, todos explicados aquí.
- Alcance inspeccionado y modificado: únicamente las cuatro lecturas de
  `obtener_detalles_estudiante_controller` y el repositorio de estudiantes. Se
  leyeron además, **solo para decidir con evidencia y sin modificarlos**, los
  literales SQL de `dashboard_controller`, `notas_controller`,
  `planilla_controller` y `boletin_controller`, y el listado de repositorios
  existentes. **No se inspeccionó asignaciones.**
- Decisión con evidencia sobre las cuatro lecturas: registrada en Decisiones.
  Viven en `estudiantes_repository.py`, en un bloque rotulado, porque no existe
  un repositorio de esos dominios, crear uno tendría un solo consumidor real y
  ninguna de las consultas es un duplicado.
- Caracterización añadida **antes** de mover producto:
  `tests/test_asignaciones_estudiantes_caracterizacion.py` pasó de 39 a **43
  casos**. Se vieron pasar contra el producto anterior.
- Archivos de producto: `app/controllers/estudiante_controller.py` y
  `app/repositories/estudiantes_repository.py`. Pruebas modificadas:
  `tests/test_asignaciones_estudiantes_caracterizacion.py`.
- Implementación: **cuatro funciones nuevas** en el repositorio, que llega a
  **once**. El controlador bajó de **396 a 381 líneas**; desde el commit base de
  la capa, de **519 a 381**. **Ya no contiene ni una sola sentencia SQL**: la
  frontera del dominio de estudiantes queda cerrada.
- Equivalencia SQL verificada con el comparador AST **contra el commit base de la
  capa**, `589cb6d`: **11 sentencias distintas antes y 11 después, conjunto
  idéntico**, doce puntos de llamada antes y doce después, y **11 de 11 literales
  conservados byte a byte**. Ninguna autorización de cambio de SQL fue necesaria
  en toda la extracción de estudiantes.
- Error detectado y corregido durante la subcapa: al mover la lectura de
  observaciones quedó un `for r in cursor.fetchall()` consumiendo el cursor en
  vez de la lista devuelta. Se detectó releyendo el resultado de la edición,
  antes de ejecutar nada, y se corrigió; las pruebas lo habrían atrapado igual.
- Conteos conservados: `GET /estudiantes/{id}/detalles` sigue costando **4
  consultas propias** más las de `cobros`, y `GET /estudiantes` con `limit` sigue
  costando 2. Los de la capa 4 no se tocan.
- Pruebas específicas: **71 pasaron** en 0,67 s sobre los siete archivos del
  dominio. Ruff del alcance: **correcto**.
- Compuerta global final: `.\venv\Scripts\python.exe scripts\verify.py`;
  **712 pruebas pasaron** en 2,08 s, 5 warnings heredadas, Ruff correcto,
  `pip check` íntegro y exit 0. La suite pasó de 708 a 712.
- Revisión final: `git diff --check` en exit 0. El diff contiene tres archivos:
  dos de producto y la prueba ampliada. No hubo cambios en rutas, payloads,
  status codes, permisos, tenant, ownership, transacciones, timeouts,
  dependencias ni configuración.
- PostgreSQL, migraciones, producción, commit, push y deploy: **ninguno**. La
  evidencia de GitHub Actions posterior a la capa 0 continúa pendiente y no se
  atribuye CI remota.
- Estado: 6.2 **cerrada** y con ella **el dominio de estudiantes**; 6.3
  **pendiente y no iniciada**.
- Siguiente acción exacta: ejecutar únicamente 6.3, extracción de las escrituras
  de `asignaciones`, y detenerse antes de 6.4. *(Ejecutada en el turno siguiente;
  ver el cierre de 6.3 más abajo.)*

### 2026-08-17 — cierre de 6.3

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git validado directamente y no
  se usó GitHub para inferir el estado local.
- Precondición Git: rama `main`, **árbol limpio**, `HEAD` `c477516`, el cierre de
  6.2 que el usuario commiteó entre turnos y que contiene exactamente los cinco
  archivos que 6.2 declaró. El commit base `589cb6d` existe y es ancestro;
  `origin/main` sigue en el base, así que hay **cuatro commits locales por
  delante, sin publicar**, todos explicados aquí.
- Alcance inspeccionado y modificado: únicamente las **siete escrituras** de
  `asignaciones` en `asignacion_controller.py`. No se inspeccionaron las
  lecturas, ni `asignacion_academica.py`, ni las rutas, ni estudiantes.
- Archivos de producto: `app/controllers/asignacion_controller.py` y el nuevo
  `app/repositories/asignaciones_repository.py`. Pruebas modificadas:
  `tests/test_asignaciones_estudiantes_caracterizacion.py`, solo para **añadir**
  la guardia de los dos literales gemelos; ninguna expectativa existente cambió.
- Caracterización: **no hizo falta ampliarla antes de mover**. Los siete caminos
  de escritura ya estaban cubiertos por 6.0 y por las pruebas heredadas: alta
  feliz con su `UPDATE` de autorreferencia, alta que hereda la asignación
  académica, traducción de `IntegrityError`, edición de horario, desactivación por
  id, desactivación por profesor y curso, y las tres escrituras del orden del
  boletín.
- Implementación: **siete funciones** que reciben el cursor existente cubren los
  siete puntos de llamada de escritura. El controlador pasó de **1093 a 1041
  líneas** y **ya no contiene ninguna escritura**: quedan 0 sentencias `INSERT`,
  `UPDATE` o `DELETE` inline y **34 lecturas distintas**, que son el trabajo de
  6.4.
- Equivalencia SQL verificada con el comparador AST **contra el commit base de la
  capa**, `589cb6d`: **41 sentencias distintas antes y 41 después, conjunto
  idéntico**, 42 puntos de llamada antes y 42 después, y **41 de 41 literales
  conservados byte a byte**. Ninguna autorización de cambio de SQL fue necesaria.
- Conteos conservados: alta con horario 12, heredando 11, sin horario 8, edición
  de horario 10, edición bloqueada por historial 6, orden del boletín 6. Los
  verifica la caracterización de 6.0 sin cambios.
- Pruebas específicas: **71 pasaron** en 0,78 s sobre los siete archivos del
  dominio, el mismo resultado que antes de extraer. Ruff del alcance:
  **correcto**.
- Compuerta global final: `.\venv\Scripts\python.exe scripts\verify.py`;
  **713 pruebas pasaron** en 2,40 s, 5 warnings heredadas, Ruff correcto,
  `pip check` íntegro y exit 0. La suite pasó de 712 a 713 por la guardia nueva.
- Revisión final: `git diff --check` en exit 0. El diff contiene tres archivos:
  dos de producto y la prueba ampliada. No hubo cambios en rutas, payloads,
  status codes, permisos, tenant, ownership, transacciones, timeouts,
  dependencias ni configuración.
- PostgreSQL, migraciones, producción, commit, push y deploy: **ninguno**. La
  evidencia de GitHub Actions posterior a la capa 0 continúa pendiente y no se
  atribuye CI remota.
- Estado: 6.3 **cerrada**; 6.4 **pendiente y no iniciada**.
- Siguiente acción exacta: ejecutar únicamente 6.4, extracción de las lecturas de
  `asignaciones`, y detenerse antes de 6.5. *(Ejecutada en el turno siguiente;
  ver el cierre de 6.4 más abajo.)*

### 2026-08-17 — cierre de 6.4

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git validado directamente y no
  se usó GitHub para inferir el estado local.
- Precondición Git: rama `main`, **árbol limpio**, `HEAD` `be725c8`, el cierre de
  6.3 que el usuario commiteó entre turnos y que contiene exactamente los cinco
  archivos que 6.3 declaró. El commit base `589cb6d` existe y es ancestro;
  `origin/main` sigue en el base, así que hay **cinco commits locales por
  delante, sin publicar**, todos explicados aquí.
- Alcance inspeccionado y modificado: las lecturas de `asignacion_controller.py`
  y el repositorio de asignaciones. Se leyeron además, **solo para decidir con
  evidencia y sin modificarlos**, `app/repositories/README.md` y el recuento de
  usos del patrón de estado activo en todo `app/`. No se tocaron
  `asignacion_academica.py`, las rutas ni estudiantes.
- Convención confirmada en `app/repositories/README.md`: consultas SQL por
  módulo, sin detalles HTTP, recibiendo y devolviendo datos simples. Es lo que ya
  venían haciendo las tres extracciones anteriores.
- Decisiones con evidencia, registradas arriba: las precondiciones sobre
  catálogos **van** al repositorio; `tabla_columna_existe` **se queda**; la
  consulta de historial sobre datos **se mueve**; el tercer par de literales
  gemelos **no se unifica**.
- Caracterización: **no hizo falta ampliarla**. Los caminos de lectura ya estaban
  cubiertos por 6.0 y por las pruebas heredadas, y **ninguna prueba cambió de
  expectativa**.
- Archivos de producto: `app/controllers/asignacion_controller.py` y
  `app/repositories/asignaciones_repository.py`. **Pruebas modificadas: ninguna.**
- Implementación: **veintiuna funciones nuevas** en el repositorio, repartidas en
  cuatro bloques rotulados —precondiciones, validaciones de unicidad y cruce,
  lecturas de asignaciones e historial académico—. El controlador pasó de **1041
  a 762 líneas**; desde el commit base de la capa, de **1093 a 762**, y conserva
  **una sola sentencia SQL**: la de `information_schema.columns`.
- Equivalencia SQL verificada con el comparador AST **contra el commit base de la
  capa**, `589cb6d`: **41 sentencias distintas antes y 41 después, conjunto
  idéntico**, 42 puntos de llamada antes y 42 después, y **41 de 41 literales
  conservados byte a byte**, incluidas las siete que se construyen con f-string.
  Ninguna autorización de cambio de SQL fue necesaria.
- Conteos conservados: alta con horario 12, heredando 11, sin horario 8, edición
  de horario 10, edición bloqueada por historial 6, orden del boletín 6,
  `asignacion_tiene_historial` 7 a 14. Los verifica la caracterización de 6.0.
- Pruebas específicas: **72 pasaron** en 0,97 s sobre los siete archivos del
  dominio. Ruff del alcance: **correcto**.
- Compuerta global final: `.\venv\Scripts\python.exe scripts\verify.py`;
  **713 pruebas pasaron** en 2,48 s, 5 warnings heredadas, Ruff correcto,
  `pip check` íntegro y exit 0. El total no cambia porque 6.4 no añadió pruebas.
- Revisión final: `git diff --check` en exit 0. El diff contiene exactamente dos
  archivos de producto. No hubo cambios en rutas, payloads, status codes,
  permisos, tenant, ownership, transacciones, timeouts, dependencias ni
  configuración.
- PostgreSQL, migraciones, producción, commit, push y deploy: **ninguno**. La
  evidencia de GitHub Actions posterior a la capa 0 continúa pendiente y no se
  atribuye CI remota.
- Estado: 6.4 **cerrada**; 6.5 **pendiente y no iniciada**.
- Siguiente acción exacta: ejecutar únicamente 6.5 y, por ser la última subcapa,
  aplicar la compuerta de cierre de la capa sin activar la capa 7. *(Ejecutada en
  el turno siguiente; ver el cierre de 6.5 más abajo.)*

### 2026-08-17 — cierre de 6.5

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git validado directamente y no
  se usó GitHub para inferir el estado local.
- Precondición Git: rama `main`, **árbol limpio**, `HEAD` `d04a455`, el cierre de
  6.4 que el usuario commiteó entre turnos. El commit base `589cb6d` existe y es
  ancestro; `origin/main` sigue en el base, así que hay **seis commits locales
  por delante, sin publicar**, todos explicados aquí.
- Alcance inspeccionado y modificado: el `SELECT` inline de
  `GET /mis-clases/{profesor_id}` en `app/routes/asignaciones.py` y el
  repositorio de asignaciones. No se tocó `asignacion_academica.py`.
- Decisión con evidencia sobre el SQL de la ruta: **se movió** al repositorio. Se
  comprobó antes que su texto **no coincide con ninguna** de las funciones ya
  extraídas —es la única consulta del dominio con `LEFT JOIN` reflexivo sobre
  `asignaciones` y con `c.jornada`— y que la ruta **ya estaba caracterizada** por
  `test_mis_clases_incluye_jornada_del_curso`, que fija su payload completo. La
  ruta conserva `get_cursor`, `require_profesor_scope` y el formateo.
- **Señal esperada, producida y atendida**: la guardia
  `test_la_ruta_mis_clases_conserva_su_sql_inline`, que 6.0 escribió para no
  perder de vista ese hallazgo, **falló** al moverlo. Era exactamente lo que
  debía ocurrir, igual que la prueba deliberada de 3.2 falló cuando 3.3b corrigió
  su defecto. Se sustituyó por dos pruebas positivas: una fija que **ninguna
  ruta** de la capa 6 contiene SQL, y otra que el controlador de asignaciones
  conserva **una sola sentencia**, la de `information_schema`.
- Código heredado: se recorrieron las **32 funciones** que define
  `asignacion_controller.py` y **ninguna quedó sin consumidores** tras las cuatro
  extracciones. Las dos copias de `obtener_clases_profesor_controller` ya estaban
  muertas **antes** de la capa; el usuario, preguntado explícitamente, decidió
  **dejarlas registradas y no retirarlas**, para que la capa cierre siendo una
  refactorización pura sin borrados de producto.
- Archivos de producto: `app/routes/asignaciones.py` y
  `app/repositories/asignaciones_repository.py`, que llega a **33 funciones**. La
  ruta bajó de 238 a **196 líneas**. Pruebas modificadas:
  `tests/test_asignaciones_estudiantes_caracterizacion.py`.
- Equivalencia SQL final, con el comparador ampliado a la ruta y contra el commit
  base: **42 sentencias distintas antes y 42 después, conjunto idéntico**, 43
  puntos de llamada antes y después, y **42 de 42 literales byte a byte**.
- Pruebas específicas: **73 pasaron** en 0,85 s. Ruff sobre `app/` completo y la
  prueba: **correcto**.
- **Compuerta global de cierre**: `.\venv\Scripts\python.exe scripts\verify.py`;
  **714 pruebas pasaron** en 2,57 s, 5 warnings heredadas, Ruff correcto,
  `pip check` íntegro y exit 0.
- Revisión final: `git diff --check` en exit 0. El diff contiene tres archivos.
- PostgreSQL, migraciones, producción, commit, push y deploy: **ninguno**, ni en
  esta subcapa ni en toda la capa.
- Estado: 6.5 **cerrada**. El cierre de la **capa** queda supeditado a la
  verificación manual, que el usuario **eligió ejecutar él mismo** y que está
  **definida y no ejecutada**.
- Siguiente acción exacta: obtener del usuario el resultado de la verificación
  manual. Solo entonces marcar la capa cerrada, actualizar el índice y dejar la
  capa 7 en espera. **No activar la capa 7.** *(La ejecutó y la capa se cerró el
  mismo 2026-08-17; ver el cierre de la capa más abajo.)*

### 2026-08-17 — cierre de la capa 6

Con la verificación manual ejecutada, la capa queda cerrada.

#### Resultado frente a su objetivo

El índice le pedía separar asignaciones y estudiantes con contratos estables,
trabajando cada dominio en subcapas, evitando una extracción conjunta masiva y
protegiendo permisos, relaciones académicas, archivos e historial.

| Objetivo | Resultado |
|---|---|
| Separar los dos dominios con contratos estables | Dos repositorios nuevos: `estudiantes_repository` con **11 funciones** y `asignaciones_repository` con **33**. Los controladores pasaron de **1612 líneas juntas a 1143** y de **52 sentencias SQL inline a 1** |
| Cada dominio en subcapas, sin extracción conjunta | Cinco subcapas: estudiantes en 6.1 y 6.2, **terminado antes de empezar** asignaciones en 6.3 y 6.4. En ningún turno se tocaron los dos |
| Proteger permisos, relaciones académicas, archivos e historial | **43 pruebas de caracterización** nuevas que fijan los permisos por rol —incluido `require_profesor_scope`—, el bloqueo de cambios sobre asignaciones con historial, y que **ningún camino borra filas** |

La suite pasó de **669 a 714** pruebas. Compuerta de cierre: **exit 0 con 714
pruebas**, Ruff correcto y `pip check` íntegro.

#### Lo que esta capa NO hizo

- **No tocó la base de datos**, ni siquiera para leer. Es la segunda capa del
  programa que no abre una sola conexión a PostgreSQL, después de la 5.
- **No tocó archivos.** El supuesto de `storage` con el que se activó la capa era
  falso y quedó refutado en 6.0 con prueba: solo branding y plan de clases usan
  ese servicio. El riesgo de rollback irreversible que se anticipó **no
  existía**.
- No cambió rutas, payloads, status codes, permisos, tenant, ownership, reglas
  académicas, transacciones, timeouts, dependencias ni configuración.
- **No corrigió ninguno de los diez hallazgos** de 6.0, ni retiró el código
  muerto: el usuario decidió expresamente dejarlo registrado.
- **No necesitó autorizar ni un solo cambio de texto SQL**, frente a los dos que
  necesitó la capa 5. Las tres parejas de literales gemelos que aparecieron se
  conservaron sin unificar.

#### Rollback

Puramente de código: revertir hasta
`589cb6d1391161c692a6f24aee9d523317cbb1ce`. No hay nada que deshacer en datos ni
en esquema. **Diferencia con la capa 5**: ese commit base **ya está desplegado**,
así que revertir exigiría un push y un despliegue, no una operación local.

#### Estado de publicación al cerrar

**Sin push ni despliegue.** Los seis commits de la capa viven solo en el checkout
local y producción sigue corriendo `589cb6d`. Publicar es decisión y
responsabilidad del usuario, y en este repositorio un push a `main` dispara el
despliegue.

> **Corrección del mismo 2026-08-17.** El párrafo anterior describía el momento
> del cierre y se conserva por eso. **Ya no es el estado vigente**: el usuario
> commiteó el cierre como `bf075a0` y **publicó la capa**. El reflog de
> `origin/main` registra `update by push` de ese commit, que incluye los
> **siete** de la capa —`2881b03` a `bf075a0`—. Como un push a `main` dispara el
> despliegue, **producción ya corre este código**. El punto de rollback pasa a ser
> `589cb6d` en remoto, y revertir exigiría otro push y otro despliegue.
> La corrección se hizo al detectar que `origin/main..HEAD` había quedado en 0,
> antes de dar por bueno lo que este documento afirmaba.

#### Riesgos que la capa deja abiertos

- **El alta y la edición de asignaciones no toman ningún lock.** Dos peticiones
  simultáneas pueden crear clases solapadas para el mismo profesor o salón. Es el
  riesgo más directo que deja la capa, y el análogo del hueco de idempotencia que
  la capa 5 encontró en `POST /pagos` —aquel se corrigió a medias; este sigue
  intacto—.
- `GET /estudiantes/{id}` devuelve `SELECT *`: su contrato es el esquema entero.
- `asignacion_tiene_historial` cuesta hasta 14 consultas.
- Dos rarezas de status code y las tres parejas de literales gemelos.
- Código muerto duplicado: las dos copias de
  `obtener_clases_profesor_controller`, que el usuario decidió conservar.
- Heredados: calibración de `DB_STATEMENT_TIMEOUT_MS` de la capa 1, ausencia de
  evidencia de GitHub Actions desde la capa 0, la credencial privilegiada de la
  capa 4 sin rotar, los siete hallazgos abiertos de la capa 5 —incluida la clave
  de idempotencia, paso 2— y la auditoría de capacidad de la capa 2.

- Estado: **capa 6 cerrada**. La capa 7, resto de dominios, queda **en espera** y
  no fue activada.
- Siguiente acción exacta: esperar una orden explícita del usuario. Una
  instrucción genérica de continuar no autoriza activar la capa 7.

## Entrega al próximo chat

- Capa activa: **ninguna**. La capa 6 quedó **cerrada** el 2026-08-17 y la capa
  7, resto de dominios, sigue en espera, sin activar.
- Última subcapa terminada: **6.5**, la última. Las cinco están cerradas.
- Primera subcapa pendiente: **ninguna**.
- **Capa cerrada.** La verificación manual la ejecutó el usuario el 2026-08-17,
  en local contra el árbol de trabajo, con resultado **correcto**. No quedan
  bloqueos.
- Commit base: `589cb6d1391161c692a6f24aee9d523317cbb1ce`, rama `main`,
  **publicado y desplegado**. Al cerrar 6.5, `HEAD` es `d04a455` —seis commits
  locales por delante de `origin/main`, **sin publicar**— más los tres archivos
  de 6.5 sin commitear.
- Lo que consiguió la capa, con sus cinco subcapas cerradas:
  `estudiante_controller.py` pasó de **519 a 381 líneas** y de 11 sentencias SQL
  inline a **0**; `asignacion_controller.py` de **1093 a 762** y de 41 a **1**, la
  introspección de esquema; `app/routes/asignaciones.py` perdió el **único SQL de
  dominio que vivía en la capa HTTP** de todo el programa. La persistencia vive
  en dos repositorios nuevos, `estudiantes_repository` con **11 funciones** y
  `asignaciones_repository` con **33**. El dominio quedó protegido por **43
  pruebas de caracterización** nuevas y la suite pasó de 669 a **714**.
- Evidencia de que nada observable cambió: comparadores AST contra el commit base
  con **conjunto de SQL idéntico** en los dos dominios —42 de 42 literales byte a
  byte en asignaciones, 11 de 11 en estudiantes— y ninguna prueba que cambiara de
  expectativa. **En toda la capa no hizo falta autorizar ni un cambio de texto
  SQL**, a diferencia de la capa 5.
- Lo que consiguieron 6.1 y 6.2: toda la persistencia de estudiantes salió del
  controlador a `app/repositories/estudiantes_repository.py`, **once funciones**
  que reciben el cursor —siete de la tabla `estudiantes` y cuatro del bloque del
  expediente—. `estudiante_controller.py` pasó de **519 a 381 líneas** y de
  **11 sentencias SQL inline a 0**. Comparador AST contra el commit base:
  **conjunto de SQL idéntico, 11 de 11 literales byte a byte**, sin una sola
  autorización de cambio de texto. Ninguna prueba cambió de expectativa; las
  cuatro añadidas en 6.2 cubren huecos, no correcciones.
- Lo que 6.0 dejó medido: **19 entradas HTTP** —12 de asignaciones y 7 de
  estudiantes—, **dos tablas escritas** y ninguna borrada, **39 pruebas de
  caracterización** nuevas y los conteos de once caminos. Un alta de asignación
  cuesta **12 consultas, diez de ellas de validación**; `asignacion_tiene_historial`
  cuesta hasta **14**. **No hay N+1** en ninguno de los dos dominios.
- Bloqueos: ninguno. Verificaciones heredadas pendientes y aceptadas: valor
  operativo final de `DB_STATEMENT_TIMEOUT_MS` (capa 1) y evidencia de GitHub
  Actions posterior a la capa 0. La credencial privilegiada de la capa 4 sigue
  sin rotar.
- Lo que esta capa debe recordar antes de tocar nada, **corregido por 6.0**:
  1. **No toca archivos.** El supuesto de `storage` era falso y quedó refutado
     con prueba. El rollback vuelve a ser de código y filas.
  2. **Asignaciones es transversal**: nueve módulos dependen de
     `resolver_asignacion_academica_id_cursor`. Por eso 6.1 empieza por
     estudiantes.
  3. **Los permisos no son uniformes**: dos entradas de asignaciones usan
     `require_profesor_scope` y admiten a un profesor, no solo a un admin.
  4. **Nada se borra**: los dos dominios desactivan con `UPDATE`, y eso es lo
     que hace inocuas las 16 claves foráneas que apuntan a sus tablas.
- Siguiente acción exacta: **esperar una orden explícita del usuario**. La capa 7,
  resto de dominios, sigue **en espera** y no se activa sin ella. Una instrucción
  genérica de continuar no la autoriza.
- Pendiente operativo del usuario: **resuelto**. La capa se publicó el 2026-08-17
  en `bf075a0`; el reflog de `origin/main` lo registra. Como un push a `main`
  dispara el despliegue, producción ya corre este código.
- Decisión ya tomada por el usuario el 2026-08-17: las dos copias muertas de
  `obtener_clases_profesor_controller` **se dejan**, registradas como hallazgo con
  su guardia de prueba. La capa cierra sin borrar código de producto.
- Hallazgos de 6.0 que siguen **vivos y sin corregir**: la ausencia de lock en el
  alta y la edición de asignaciones —dos peticiones simultáneas pueden crear
  clases solapadas—, el `SELECT *` de `GET /estudiantes/{id}`, las dos rarezas de
  status code, el coste de hasta 14 consultas de `asignacion_tiene_historial` y
  las tres parejas de literales gemelos sin unificar.
