# Capa 7: dashboard

Última revisión: 2026-08-17.

## Control

- Estado: **Activa** desde el 2026-08-17.
- Commit base: `123637ee80895023ecece9c32df526ef4eddd1e5`.
- Rama acordada: `main`.
- Primera subcapa pendiente: **7.0**, no iniciada.
- Código de producto modificado al activar: **ninguno**.
- Dominio de esta capa: **dashboard, y solo ese**. La capa 7 del índice es
  «resto de dominios» y ordena expresamente **priorizar uno a la vez**, así que
  esta bitácora cubre un único dominio. Los demás quedan fuera y necesitarán su
  propia bitácora y su propia orden.
- Autorización: orden explícita del usuario el 2026-08-17, con el texto que
  `PROMPT_CONTINUACION.md` conservaba preparado para la capa 7 y cuya condición
  de caducidad se cumplía —el índice seguía sin capa activa y con la 7 en
  espera—. El marcador `DOMINIO` llegó **sin rellenar**; se preguntó y el
  usuario eligió `dashboard`. No se dedujo por inferencia.
- La autorización permite **solamente la activación documental**. No autoriza
  inspeccionar código del dominio, implementar 7.0, tocar la base de datos,
  hacer deploy, commit ni push.

## Objetivo

Migrar el dominio de **dashboard** con contratos y pruebas, conservando su
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

## Diferencia de objetivo respecto a las capas 4, 5 y 6

Es la primera capa del programa cuyo objetivo **contempla añadir algo** y no
solo mover código. Las capas 5 y 6 fueron refactorizaciones puras que no
cambiaron ni un contrato; aquí el índice autoriza `response_model`, errores de
dominio y pruebas HTTP, pero **subordinados a caracterizar y conservar primero**.

Esto no relaja la regla, la ordena: sin caracterización previa que demuestre la
respuesta actual, no se añade nada. Ver el riesgo registrado sobre
`response_model`, que en FastAPI **filtra** los campos no declarados y puede
cambiar el payload en silencio.

## Dependencias de capas anteriores

- Compuerta única `scripts/verify.py`, heredada de la capa 0. El último
  resultado registrado, al cerrar la capa 6, es **714 pruebas, exit 0**, Ruff
  correcto y `pip check` íntegro; **no se reprodujo durante esta activación
  documental**. 7.0 debe reproducirlo antes de tocar nada.
- Ciclo de vida de conexiones, transacciones y timeouts definido en la capa 1.
  El valor operativo final de `DB_STATEMENT_TIMEOUT_MS` sigue **pendiente y
  aceptado**: el candidato de 15000 ms está documentado y **no aplicado**, y
  continúa vigente 30000.
- DB síncrona fuera del event loop y limitador compartido de capacidad
  establecidos en la capa 2. Esta capa no puede reintroducir trabajo bloqueante
  en el event loop ni cambiar esa capacidad sin una auditoría propia. Sobre
  `MAX_DB_CONNECTIONS_PER_THREADPOOL_WORKER = 2` pesa el pendiente del
  2026-08-17: se quedó sin ejemplo real que la respalde y se conserva como
  margen.
- Tenants versionados y alta reproducible cerrados en la capa 3. Quedan dos
  schemas, `tenant_2005` —el único de producción— y `tenant_colegio_1`
  —plantilla y demo—, ambos con 37 claves foráneas, 30 secuencias propias y 30
  migraciones registradas.
- Contratos de lectura financieros fijados por la capa 4 y protegidos por su
  caracterización, con los conteos 6/15 del estado de cuenta de reportes,
  1/13/37 de cuentas y 5/12/12 de cartera. Dependen de `cobros.py`.
- Frontera de persistencia de pagos establecida en la capa 5:
  `app/repositories/pagos_repository.py` con 16 funciones que reciben el cursor.
- Frontera de persistencia de asignaciones y estudiantes establecida en la capa
  6: `estudiantes_repository` con 11 funciones y `asignaciones_repository` con
  33, ambas con el mismo patrón —funciones que **reciben el cursor existente** y
  no abren, cierran, confirman ni revierten recursos—. Es el patrón que esta
  capa debe seguir si extrae persistencia.
- La última evidencia de GitHub Actions corresponde a la capa 0. Hubo pushes
  autorizados el 2026-08-15 y el 2026-08-17, pero **no se ha obtenido evidencia
  de ningún run**; esa verificación permanece **pendiente y aceptada**. No se
  atribuye CI remota porque `HEAD` coincida con `origin/main`.

## Lo que el programa cree saber de dashboard, y que 7.0 debe verificar

Aplica la lección 12 que dejó la capa 6: **un supuesto heredado se marca como no
verificado y se comprueba en la subcapa 0**. La capa 6 se activó anticipando que
sus dominios escribían archivos, y era falso. Nada de lo que sigue se da por
bueno.

| Supuesto | Origen | Estado |
|---|---|---|
| Dashboard **no tiene repositorio propio** | La capa 6 enumeró los existentes: asignaciones, estudiantes, pagos, plan de clases y reportes | **No verificado** para este dominio |
| Dashboard **consume `resolver_asignacion_academica_id_cursor`** | 6.0 lo listó entre los nueve módulos consumidores, verificado desde el lado de asignaciones | **A reconfirmar desde el lado de dashboard** |
| Dashboard **lee `notas_detalle` y tablas académicas con SQL inline**, y promedia con `TRUNC(AVG(CAST(... AS numeric)), 2)` por estudiante | 6.2 leyó esos literales, sin modificarlos, para decidir dónde vivían las lecturas del expediente | **Registrado, no reinspeccionado** |
| Dashboard **concentra los cálculos más caros**, con varias consultas de promedios por estudiante | Visto **de pasada** en las capas 4 y 6 | **No medido.** Que huela a N+1 no es evidencia de N+1 |
| Dashboard **no escribe archivos** vía `app/services/storage.py` | Solo se demostró que branding y plan de clases **sí** lo usan | **No verificado.** Si resultara que escribe, el rollback deja de ser reversible y hay que documentarlo antes de tocar nada |
| Dashboard **es de solo lectura** | Nadie lo ha comprobado | **No verificado.** Si escribe alguna tabla, cambia el perfil de riesgo entero |
| Los permisos **no son uniformes** en el sistema: hay rutas con `require_profesor_scope` y `require_asignacion_access`, no solo admin | Capa 6 | **No verificado** para las entradas de dashboard. El inventario de roles es contrato de seguridad, no un detalle |

## Alcance autorizado

- Inventariar entradas HTTP, reglas, cálculos, consultas, escrituras, archivos,
  pruebas y consumidores **de dashboard** mediante búsquedas dirigidas.
- Caracterizar antes de extraer: rutas, métodos, payloads, status codes,
  permisos, roles, tenant, ownership, orden, nulos, redondeos, transacciones y
  errores.
- Separar progresivamente HTTP, reglas, servicios y persistencia siguiendo el
  patrón ya probado tres veces, con pruebas de caracterización previas a cada
  extracción importante.
- Contar y comparar consultas críticas antes y después.
- Agregar `response_model`, errores de dominio y pruebas HTTP o de integración
  **solo después** de caracterizar y demostrando que la respuesta existente se
  conserva.
- Medir con `EXPLAIN ANALYZE` conforme al criterio corregido en la capa 4:
  `SELECT` en producción bajo transacción `READ ONLY` cerrada con `rollback`.
  Ninguna medición puede escribir.

## Fuera de alcance

- **Todos los demás dominios de la capa 7**: notas, boletín, asistencia,
  observaciones, planilla, planeador anual, plan de clases, ventas, branding,
  profesores, super admin y cualquier otro. Esta capa es de un solo dominio.
  Se permite la lectura mínima indispensable para caracterizar un contrato que
  dashboard consuma, sin modificarlo.
- `app/services/asignacion_academica.py`, del que dependen nueve módulos, y
  `cobros.py`, del que dependen los contratos financieros de la capa 4: se leen
  si hace falta, **no se tocan**.
- Los hallazgos abiertos de las capas 5 y 6, incluidos el **paso 2 de la clave
  de idempotencia** de `POST /pagos`, los status codes 500 de
  `tipos_pagos_controller`, la **ausencia de lock en el alta y la edición de
  asignaciones**, el `SELECT *` de `GET /estudiantes/{id}`, las dos rarezas de
  status code, las tres parejas de literales gemelos y el código muerto
  duplicado que el usuario decidió conservar. **No entran por inferencia.**
- El trabajo registrado en `PROMPT_CONTINUACION.md` bajo «trabajo fuera del
  alcance de cualquier capa activa»: la colisión de mayúsculas en reportes,
  `/estado-cuenta/curso`, los 14 índices duplicados, la deduplicación de
  `_tabla_pagos_aplicaciones_existe`, `_obtener_saldo_concepto` y la auditoría
  de capacidad de la capa 2.
- Cambiar rutas, payloads, status codes, permisos, roles, ownership, reglas de
  cálculo, redondeos, orden o semántica transaccional.
- Cambiar PostgreSQL, `psycopg2`, el modelo de schemas tenant, el pool, los
  timeouts, el limitador de concurrencia, el ORM, el driver o el almacenamiento
  de archivos.
- Migraciones reales, DDL, DML, deploy, commit o push.

## Invariantes

- Métodos, paths, status codes y forma exacta de las respuestas permanecen
  idénticos, incluidos los **redondeos y el número de decimales** de cualquier
  promedio o total que el dashboard presente.
- Permisos, roles, ownership y aislamiento entre tenants se conservan sin
  excepción.
- Los límites de transacción se conservan: qué se confirma junto, qué se
  revierte junto y quién es dueño de `commit`, `rollback`, cursor y conexión,
  conforme a la capa 1.
- Ninguna operación DB síncrona vuelve al event loop ni se altera el limitador
  compartido sin medir de nuevo su capacidad.
- Los contratos de lectura financieros fijados por la capa 4 siguen pasando su
  caracterización, incluidos los conteos 6/15, 1/13/37 y 5/12/12.
- Las fronteras de persistencia de las capas 5 y 6 no se alteran: si dashboard
  necesita una lectura que ya existe allí, se decide **con evidencia** y sin
  duplicarla a ciegas.
- El SQL de dominio se conserva hasta que una subcapa autorice, con
  caracterización previa, un cambio concreto.
- Ninguna escritura de archivos cambia de momento, de nombre ni de destino sin
  una decisión explícita y un rollback documentado.

## Línea base

Pendiente: la establece 7.0. Ningún valor de esta tabla se rellena por memoria.

| Comprobación | Comando | Resultado |
|---|---|---|
| Pruebas específicas | Lo determina 7.0 tras inventariar el dominio | Pendiente |
| Suite global | `.\venv\Scripts\python.exe scripts\verify.py` | Pendiente. Última registrada al cerrar la capa 6: **714 pruebas, exit 0** |
| Ruff | Ejecutado por la compuerta global y sobre el alcance modificado | Pendiente |
| Dependencias | Ejecutado por la compuerta global | Pendiente |

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 7.0 | Inventario, contratos, caracterización y línea base de consultas | **Pendiente**, no iniciada |
| 7.1 en adelante | **Sin decidir** | — |

El desglose posterior a 7.0 **se deja deliberadamente sin decidir**, igual que
hizo la capa 6. Definirlo ahora exigiría inventar detalles de implementación de
un dominio que esta activación no ha inspeccionado. Se define con la evidencia
que produzca 7.0.

Las subcapas innecesarias se marcarán `No aplica` con explicación. Nunca se
ejecutan dos subcapas en el mismo turno.

## Subcapa activa: trabajo exacto de 7.0

1. Confirmar `main`, árbol limpio y que todo commit posterior al base
   `123637ee80895023ecece9c32df526ef4eddd1e5` esté explicado en esta bitácora.
2. Reproducir la compuerta heredada y determinar las pruebas específicas sin
   ampliar el alcance.
3. Localizar mediante búsquedas dirigidas únicamente la documentación, entradas
   HTTP, archivos fuente y pruebas **de dashboard**. No leer historia global ni
   código de los demás dominios de la capa 7.
4. Inventariar responsabilidades y dependencias actuales sin mover código:
   HTTP, reglas, cálculos, persistencia, escrituras, archivos y efectos
   laterales.
5. Registrar los contratos observables exactos: rutas, métodos, payloads,
   status codes, permisos por rol, tenant, ownership, orden, nulos, **redondeos
   y decimales**, transacciones y errores.
6. Comprobar con evidencia **los siete supuestos que esta activación registra
   sin verificar**, uno por uno, y corregir la tabla con lo que se encuentre.
   Que un supuesto venga de la capa 6 no lo convierte en evidencia sobre este
   dominio.
7. Caracterizar con pruebas los caminos que una extracción posterior pueda
   alterar. 7.0 **no autoriza** una extracción ni un cambio de producto.
8. Medir o instrumentar herméticamente el número de consultas de los caminos
   críticos, en particular los promedios por estudiante, y **determinar si hay
   N+1 o no**; no optimizarlos todavía.
9. Ejecutar las pruebas específicas, Ruff del alcance, la compuerta global y
   `git diff --check`; revisar que el diff pertenezca solo a 7.0.
10. Actualizar esta bitácora, definir 7.1 con la evidencia obtenida y detenerse
    sin iniciarla.

## Criterios de cierre de la subcapa 7.0

- El dominio y sus consumidores están inventariados con archivos y puntos de
  entrada concretos, sin lectura global innecesaria, y con su frontera clara
  frente a los dominios que **no** entran en esta capa.
- Los contratos HTTP, de permisos por rol, tenant, ownership, de cálculo y de
  transacción están enumerados y protegidos por caracterización suficiente,
  incluidos los redondeos.
- Los siete supuestos heredados están **resueltos con evidencia**, confirmados o
  refutados, y la tabla queda corregida.
- Las consultas críticas tienen una línea base reproducible, fijada por
  aserciones y no anotada en prosa, y la pregunta del N+1 queda respondida con
  medición.
- No se modificó producto ni se inició una extracción.
- Pruebas específicas, Ruff, compuerta global y `git diff --check` terminan
  correctamente, y el diff es exclusivo de 7.0.
- La subcapa 7.1 queda definida y no iniciada.

## Criterios de cierre de la capa

- Todas las subcapas necesarias están cerradas o marcadas `No aplica` con
  justificación.
- El dominio quedó migrado con contratos estables y pruebas, **sin arrastrar
  otros dominios**.
- `response_model`, errores de dominio y pruebas HTTP, si se añadieron, llegaron
  **después** de caracterizar y conservando la respuesta existente, demostrado.
- No se creó ninguna abstracción compartida sin dos consumidores reales.
- Los contratos del frontend y de la base de datos permanecen intactos.
- La compuerta global, Ruff, dependencias y `git diff --check` terminan
  correctamente.
- Staging, rollback y verificación manual están documentados; si 7.0 descubre
  que el dominio escribe archivos, el rollback debe cubrirlos explícitamente.
- El índice maestro queda actualizado y **ningún otro dominio se activa sin
  orden explícita del usuario**.

## Decisiones

- Se usa `123637ee80895023ecece9c32df526ef4eddd1e5` como commit base porque es
  el `HEAD` limpio vigente de `main` y coincide con la referencia local
  `origin/main`. **No se reutilizó ningún hash de memoria**: se comprobó el
  `HEAD` real antes de registrarlo. Es el commit siguiente a `bf075a0`, que
  cerró la capa 6, y es documental.
- **El dominio es `dashboard` y lo eligió el usuario.** La autorización llegó
  con el marcador `DOMINIO` sin rellenar; se le preguntó explicando qué es un
  dominio y por qué la capa exige nombrar uno, y eligió. **No se dedujo por
  inferencia**, que es exactamente lo que el propio texto de la autorización
  prohíbe al decir que activar sin nombrarlo dejaría el alcance abierto.
- El usuario eligió explícitamente **continuar manteniendo pendientes** la
  calibración de `DB_STATEMENT_TIMEOUT_MS` y la evidencia remota de GitHub
  Actions. Ninguna se marca como cumplida y ambas conservan su riesgo.
- La activación consume la autorización puntual que `PROMPT_CONTINUACION.md`
  guardaba para la capa 7; queda retirada de ese archivo con el mismo criterio
  aplicado a las capas 3, 4, 5 y 6. **Esa retirada no se hace en este turno**:
  el alcance autorizado del turno de activación es exclusivamente el índice y
  esta bitácora nueva. Se hará en el turno de 7.0, que ya toca documentación.
- El commit base **está publicado y desplegado**, como el de la capa 6. Es por
  tanto un punto de rollback real, pero revertir a él exigiría otro push y otro
  despliegue, no una operación local.
- **El desglose de subcapas posteriores a 7.0 se deja sin decidir** hasta tener
  la evidencia del inventario. Alternativa descartada: proponer ya un 7.1 y un
  7.2 por analogía con las capas 5 y 6, que habría fijado un plan sobre un
  dominio no inspeccionado. La capa 6 hizo lo mismo y le funcionó.
- **Los supuestos heredados se registran como no verificados**, no como hechos.
  Es la lección 12 de la capa 6, donde el supuesto de los archivos resultó
  falso y solo se detectó porque estaba marcado así.

## Riesgos

- **`response_model` puede cambiar el payload en silencio.** En FastAPI, un
  `response_model` **filtra** los campos que no declara: si el modelo se queda
  corto respecto a lo que hoy devuelve el endpoint, el cliente deja de recibir
  datos sin que falle nada. El índice lo autoriza solo tras caracterizar y
  conservar la respuesta; si la equivalencia no se puede demostrar, **no se
  añade**. Es el riesgo propio y nuevo de esta capa.
- **El dominio no está inspeccionado.** Todo lo que esta bitácora dice de
  dashboard son supuestos heredados marcados como tales. Un riesgo copiado de un
  documento anterior no es evidencia; 7.0 los comprueba o los refuta.
- **Si dashboard resulta escribir archivos o filas**, el perfil de riesgo cambia
  por completo y esta bitácora debe actualizarse antes de cualquier extracción.
  Hoy nadie lo ha comprobado.
- **Los cálculos son el contrato.** En un panel de estadísticas, el resultado
  observable no es solo la forma del payload sino la cifra: un redondeo, un
  `TRUNC` frente a un `ROUND`, un `COALESCE` o un `AVG` de promedios cambian el
  número que ve el usuario sin romper ninguna estructura. La capa 6 ya encontró
  que el promedio general de estudiantes es el promedio de los promedios
  redondeado en Python —4,5 y 3,0 dan 3,8—, y que dashboard usa **otra fórmula
  distinta** para lo suyo. La caracterización debe fijar cifras, no formas.
- **Dashboard probablemente lee tablas de dominios que esta capa no puede
  tocar.** Si es así, se aplica el criterio ya usado en 5.2 y 6.2: decidir con
  evidencia dónde vive cada lectura y **no crear un repositorio nuevo que
  tendría un solo consumidor real**.
- Los contratos de lectura financieros de la capa 4 dependen de `cobros.py`.
  Pueden romperse desde aquí sin que fallen las pruebas del dominio que se está
  tocando. La mitigación es verificar sus conteos y payloads en cada subcapa.
- Los permisos no son uniformes en el sistema: intervienen roles distintos de
  `admin`. Un inventario incompleto de roles es un riesgo de seguridad, no de
  calidad.
- Heredado de la capa 1: `DB_STATEMENT_TIMEOUT_MS` sigue sin calibrar contra
  volumen representativo y el deadline HTTP/proxy externo.
- Heredado de la capa 0: no hay evidencia de GitHub Actions posterior a esa
  capa. Las verificaciones locales no se presentarán como CI remota.
- Heredado de la capa 2: `MAX_DB_CONNECTIONS_PER_THREADPOOL_WORKER = 2` se quedó
  sin ejemplo real que la respalde y se conserva como margen. Si esta capa
  encontrara un camino que anida conexiones, es evidencia relevante y debe
  registrarse, no actuarse.
- Heredado de la capa 4: la credencial privilegiada compartida en chat sigue
  **sin rotar** y no debe reutilizarse.
- Heredado de las capas 5 y 6: sus hallazgos abiertos siguen vivos, incluida la
  ausencia de lock en el alta y la edición de asignaciones, que es el riesgo más
  directo del backend hoy. **No se corrigen desde aquí.**
- **El commit base ya está desplegado**, como en las capas 5 y 6. Un push a
  `main` en este repositorio dispara el despliegue, así que la publicación de
  esta capa afectará a producción en cuanto ocurra.

## Registro de ejecución

### 2026-08-17 — activación de la capa

- Modo de acceso: mismo checkout local; Git validado directamente en
  `C:\Users\David\Documents\sistema_escolar_api`. No se usó GitHub para inferir
  el estado local.
- Autorización: orden explícita del usuario en este turno, con el texto
  preparado en `PROMPT_CONTINUACION.md` para la capa 7. Su condición de
  caducidad se comprobó y **se cumplía**: el índice seguía marcando que no
  existe capa activa y que la capa 7 está en espera.
- **Marcador sin rellenar, detectado y no resuelto por inferencia**: la
  autorización llegó con `DOMINIO` literal. Se detuvo el trabajo, se explicó al
  usuario qué es un dominio y por qué esta capa obliga a nombrar uno, y el
  usuario eligió **dashboard**. Solo entonces se activó.
- Rama acordada: `main`.
- Estado antes de escribir: árbol limpio, verificado con
  `git status --porcelain=v1` con salida vacía; `HEAD` real
  `123637ee80895023ecece9c32df526ef4eddd1e5`, comprobado y no recordado.
- Continuidad: el base de la capa 6,
  `589cb6d1391161c692a6f24aee9d523317cbb1ce`, existe y es ancestro de `HEAD`,
  verificado con `git merge-base --is-ancestor`. Sus **ocho** commits
  posteriores forman una historia lineal y **todos están explicados**: siete son
  la capa 6 —`2881b03`, `9e9b4dc`, `69c0033`, `c477516`, `be725c8`, `d04a455` y
  el cierre `bf075a0`—, registrados uno a uno en
  `06_ASIGNACIONES_ESTUDIANTES.md`; el octavo, `123637e`, es documental —tres
  archivos de `docs/modularizacion/`, +191/−31— y su contenido está registrado
  en la corrección del estado de publicación que conserva esa misma bitácora y
  en el índice.
- Estado remoto **comprobado, no supuesto**: `origin/main` está en
  `123637ee80895023ecece9c32df526ef4eddd1e5`, el mismo commit que `HEAD`. El
  reflog registra `update by push` de `123637e` y, antes, de `bf075a0`. La capa
  6 **está publicada y desplegada**, y también lo está el commit documental
  posterior. **No se consultó ni se atribuye ningún run de GitHub Actions**; esa
  evidencia sigue sin obtenerse desde la capa 0.
- Archivos creados o modificados: esta bitácora y
  `docs/modularizacion/README.md`.
- Código de producto, pruebas, consultas, configuración, dependencias y workflow
  inspeccionados o modificados: **ninguno**. **No se inspeccionó código de
  dashboard** ni de ningún otro dominio.
- Pruebas, migraciones, conexiones a PostgreSQL, acceso a producción, commit,
  push y deploy: **ninguno**.
- Comandos de precondición: `git rev-parse --show-toplevel`,
  `git branch --show-current`, `git status`, `git status --porcelain=v1`,
  `git rev-parse HEAD`, `git rev-parse origin/main`,
  `git merge-base --is-ancestor`, `git log --reverse --oneline` desde el base de
  la capa 6, `git show --stat 123637e` y `git reflog show origin/main`; todos
  con resultado coherente con la activación.
- Estado al cerrar el turno de activación: capa 7 **activa** para el dominio
  dashboard; 7.0 **pendiente y no iniciada**.
- Siguiente acción exacta: ejecutar únicamente 7.0 conforme al trabajo exacto de
  arriba y detenerse antes de 7.1.

## Entrega al próximo chat

- Capa activa: **7, dashboard**, y solo ese dominio. Activada el 2026-08-17.
- Última subcapa terminada: **ninguna**.
- Primera subcapa pendiente: **7.0**, inventario, contratos y caracterización.
- Commit base: `123637ee80895023ecece9c32df526ef4eddd1e5`, rama `main`, árbol
  limpio al activar, **publicado y desplegado**.
- Bloqueos: ninguno. Verificaciones heredadas **pendientes y aceptadas**: valor
  operativo final de `DB_STATEMENT_TIMEOUT_MS` (capa 1) y evidencia de GitHub
  Actions posterior a la capa 0. La credencial privilegiada de la capa 4 sigue
  **sin rotar**.
- Lo que esta capa debe recordar antes de tocar nada:
  1. **Nada de lo que esta bitácora dice de dashboard está verificado.** Son
     siete supuestos heredados, marcados como tales en su tabla. 7.0 los
     comprueba o los refuta, uno por uno.
  2. **Un solo dominio.** La capa 7 es «uno a la vez»; los demás necesitan su
     propia bitácora y su propia orden.
  3. **`response_model` filtra campos.** Solo después de caracterizar y
     demostrando que la respuesta se conserva.
  4. **En un panel, la cifra es el contrato**, no solo la forma del payload.
  5. **No crear abstracciones compartidas sin dos consumidores reales**, el
     criterio que ya aplicaron 5.2, 6.2 y 6.4.
- Siguiente acción exacta: ejecutar únicamente **7.0** y detenerse antes de 7.1.
  No inspeccionar los demás dominios de la capa 7.
