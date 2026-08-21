# Capa 7: observaciones

Última revisión: 2026-08-21.

## Control

- Estado: **Activa** desde el 2026-08-21.
- Commit base: `fd3f93a2ad97daa0a34081eb2f95504dd1a9e4df`.
- Rama acordada: `main`.
- Primera subcapa pendiente: **7.0**, pendiente y **no iniciada**.
- Código de producto modificado al activar: **Ninguno**.
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

**Los once están NO VERIFICADOS.**

| # | Supuesto | Origen documental | Estado |
|---:|---|---|---|
| 1 | El dominio vive en `app/routes/observaciones.py` y en un `observacion_controller` | Inventario de contratos de 0.0 (router) y subcapa 6.0, que nombra `observacion_controller` entre los nueve consumidores del resolver | **NO VERIFICADO.** No consta la ruta exacta del controlador, ni si existen esquema, servicio o repositorio. En `boletin` este mismo supuesto quedó confirmado pero hubo que precisarlo |
| 2 | **El dominio escribe**: «crea o actualiza observación académica» | Inventario de contratos de 0.0 | **NO VERIFICADO.** El «crea o actualiza» sugiere un `UPSERT`, como el de `boletin`. Si se confirma, perfil de riesgo de la capa 5 y la propiedad transaccional pasa a ser la invariante más delicada |
| 3 | **La ruta ejecuta persistencia**: `obtener_observacion` hace un `SELECT` más el resolver, y abría su propia conexión antes de que 1.4 la migrara a `get_cursor()` | Subcapa 1.4 | **NO VERIFICADO hoy.** Es **la diferencia que manda en esta capa**. Ningún dominio anterior de la capa 7 llegó con SQL en la capa HTTP |
| 4 | **El resolver se consume desde DOS sitios del dominio**: el controlador y la ruta | Subcapa 6.0, que enumeró nueve consumidores «además de `routes/observaciones.py`» | **NO VERIFICADO.** Refuerza el supuesto 3 y obliga a contar consultas en los dos sitios |
| 5 | `require_estudiante_in_asignacion` tiene **dos puntos de llamada** en `observaciones`, **ninguno en bucle** | Medición del N+1 en conexiones de `asistencia`, registrada en el índice el 2026-08-21 | **NO VERIFICADO.** Son **dos**, el doble que `boletines`. Cada uno abre una conexión propia, así que la línea base de conexiones puede ser mayor que la de `boletin` sin que haya N+1 |
| 6 | Contratos de 0.0: `200` con **dimensiones normalizadas**, `403` de ownership y **`422` con contenido vacío** | Inventario de contratos de 0.0 | **NO VERIFICADO.** El `422` sería **el primero propio de un dominio de la capa 7**; los cinco anteriores solo tenían 400, 403, 404 y 500. «Dimensiones normalizadas» no está definido en ninguna parte y 7.0 debe averiguar qué significa |
| 7 | La ruta devuelve **`None`** cuando no hay observación guardada, en vez de `404` o diccionario vacío; y **los guards corren antes de tocar la base**: si uno rechaza, no se abre cursor ni se ejecuta consulta | Subcapa 1.4, fijado por `tests/test_observaciones_ruta.py` | **NO VERIFICADO hoy.** Es un contrato con el frontend y hay que conservarlo tal cual |
| 8 | Pruebas heredadas: `tests/test_observaciones_validaciones.py`, que cubre **las validaciones del controlador**, y `tests/test_observaciones_ruta.py`, **4 pruebas** que creó 1.4 | Inventario de 0.0 y subcapa 1.4 | **NO VERIFICADO** el número total. En `asistencia` y `boletin` este supuesto quedó **incompleto** las dos veces |
| 9 | `estudiantes_repository` **lee `observaciones`** en el bloque del expediente | Subcapa 6.2 | **NO VERIFICADO.** La capa 6 registró que al mover esa lectura quedó un `for r in cursor.fetchall()` consumiendo el cursor en vez de la lista devuelta; se corrigió antes de ejecutar nada. **Romper su contrato no haría fallar las pruebas de este dominio**, solo la compuerta global |
| 10 | La tabla `observaciones` **no estuvo entre las ocho averiadas** de `tenant_2005` y **no aparece** entre las 7 claves foráneas a `asignaciones` ni entre las 9 a `estudiantes` | Capas 3 y 6, esta última **por ausencia** en sus dos listas | **NO VERIFICADO, y el más delicado de leer.** Es una inferencia por ausencia: que la capa 6 no la listara puede significar que no tiene esas claves, o que su inventario no la cubría. **7.0 no debe darlo por cierto en ninguna de las dos direcciones** |
| 11 | **`plan_de_clases` tiene tres handlers con «observacion» en el nombre** —`crear_observacion_plan`, `listar_observaciones_plan`, `marcar_observacion_vista`— que **no** pertenecen a este dominio | Subcapa 2.0, que inventarió los once handlers de plan de clases | **NO VERIFICADO.** Es la trampa de frontera de esta capa. `plan_de_clases` está **en espera**, así que aquí no hay una frontera ya cerrada que respetar, pero **tampoco se puede invadir** |

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

## Línea base

Se registrará al ejecutar 7.0. **No se ha ejecutado ningún comando de
verificación en la activación.**

| Comprobación | Comando | Resultado |
|---|---|---|
| Compuerta heredada, antes de tocar nada | `.\venv\Scripts\python.exe scripts\verify.py` | Pendiente. Al cerrar `boletin` fueron **898 pruebas, exit 0** |
| Pruebas específicas nuevas | `.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_observaciones_caracterizacion.py` | Pendiente |
| Suite global | `.\venv\Scripts\python.exe scripts\verify.py` | Pendiente |
| Ruff | Ejecutado por la compuerta global y sobre los archivos nuevos | Pendiente |
| Dependencias | Ejecutado por la compuerta global | Pendiente |

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 7.0 | Frontera con `plan_de_clases`, inventario en ruta y controlador, contratos, caracterización y línea base de consultas y conexiones | **Pendiente y no iniciada** |
| 7.1 | Primera extracción protegida | Sin definir: depende de la evidencia de 7.0 |
| 7.2 | Segunda extracción o punto de decisión | Sin definir |

El desglose se deja deliberadamente **sin decidir** hasta tener la evidencia del
inventario, igual que hicieron la capa 6 y las cinco capas 7 anteriores. Las
subcapas innecesarias se marcarán `No aplica` con explicación. **Nunca se
ejecutan dos subcapas en el mismo turno.**

## Subcapa 7.0 — trabajo exacto, pendiente y no iniciada

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
  exacto de arriba y detenerse antes de 7.1.

## Entrega al próximo chat

- Capa activa: **7, para el dominio `observaciones` y solo ese.** Los otros seis
  dominios siguen en espera.
- Última subcapa terminada: **ninguna** en esta bitácora. La anterior del
  programa fue la 7.1 de `boletin`, cerrada el 2026-08-21.
- Primera subcapa pendiente: **7.0**, pendiente y **no iniciada**.
- Commit base: `fd3f93a2ad97daa0a34081eb2f95504dd1a9e4df`, rama `main`,
  **publicado y desplegado**, comprobado contra el remoto real.
- Bloqueos: ninguno. Verificaciones heredadas **pendientes y aceptadas** por
  decisión explícita del usuario: valor operativo final de
  `DB_STATEMENT_TIMEOUT_MS` (capa 1), evidencia de GitHub Actions posterior a la
  capa 0, y los pasos no confirmados de los guiones de `ventas`, `asistencia` y
  `boletin`. La credencial privilegiada de la capa 4 sigue **sin rotar**.
- Lo que hay que recordar antes de tocar nada:
  1. **Un solo dominio.** `dashboard`, `notas`, `ventas`, `asistencia` y
     `boletin` están cerrados en sus propias bitácoras y los otros seis siguen
     en espera.
  2. **La ruta puede contener SQL.** Es lo que distingue a este dominio de los
     cinco anteriores. Contar el SQL solo en el controlador daría un inventario
     falso.
  3. **`plan_de_clases` tiene tres handlers con «observacion» en el nombre y no
     son de este dominio.** Delimitar la frontera es el **primer** paso de 7.0.
  4. **El `422` por contenido vacío es un contrato** que ninguna prueba ajena
     protege. Fijarlo por prueba antes de tocar nada.
  5. **El `None` de la observación ausente es un contrato con el frontend**, no
     un descuido: 1.4 lo fijó por prueba.
  6. **`app/core/permissions.py` está fuera de alcance**, incluida
     `require_estudiante_in_asignacion`, que este dominio llama **dos veces**.
  7. **El commit base ya está en producción.** El rollback de esta capa, si se
     publica, **no será local**.
  8. **No corregir ninguno de los cincuenta y un hallazgos** que dashboard,
     notas, ventas, asistencia y boletin dejaron abiertos.
  9. **Ejecutar siempre la compuerta completa**: `estudiantes_repository` lee
     esta tabla y no fallaría con las pruebas de este dominio.
  10. **Un supuesto puede ser cierto y estar mal atribuido.** Es la lección de
      `boletin`, donde cinco de trece hablaban de `notas`.
- Siguiente acción exacta: ejecutar únicamente **7.0** y detenerse antes de 7.1.
  Una instrucción genérica de continuar **sí** autoriza 7.0, porque la capa está
  activa y 7.0 es su primera subcapa pendiente.
