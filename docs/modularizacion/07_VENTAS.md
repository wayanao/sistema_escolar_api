# Capa 7: ventas

Última revisión: 2026-08-20.

## Control

- Estado: **Cerrada** el 2026-08-20, con sus dos subcapas **7.0 y 7.1**
  completas y la **verificación manual ejecutada por el usuario con resultado
  correcto**. Activada el mismo 2026-08-20.
- Commit base: `58c5233afc4772ba040da690f4d719b518bb1b0a`.
- Rama acordada: `main`.
- Primera subcapa pendiente: **ninguna definida**. Las subcapas **7.0 y 7.1**
  quedaron **cerradas** el 2026-08-20, y con 7.1 la frontera de persistencia del
  dominio quedó cerrada. **El usuario decidió cerrar la capa aquí**, sin abrir
  7.2. Ver «Punto de decisión, resuelto el 2026-08-20».
- Código de producto modificado al activar: **ninguno**. Tampoco en 7.0: su diff
  es **un solo archivo de prueba nuevo** y ningún archivo rastreado modificado,
  igual que los de 5.0, 6.0, 7.0 de dashboard y 7.0 de notas. **7.1 sí modifica
  producto**: el controlador y un repositorio nuevo.
- Dominio de esta capa: **ventas, y solo ese**. La capa 7 del índice es «resto
  de dominios» y ordena expresamente **priorizar uno a la vez**, así que esta
  bitácora cubre un único dominio. Los demás quedan fuera y necesitarán su
  propia bitácora y su propia orden.
- Autorización: orden explícita del usuario el 2026-08-20. **El dominio lo
  nombró el usuario**, eligiéndolo de la lista de los diez que quedaban en
  espera y tras recibir las tres advertencias que las bitácoras cerradas ya
  registraban sobre esa lista. No se dedujo por inferencia.
- La autorización permite **solamente la activación documental**. No autoriza
  inspeccionar código del dominio, implementar 7.0, tocar la base de datos,
  hacer deploy, commit ni push.

### Relación con las bitácoras de `dashboard` y `notas`

`07_DASHBOARD.md` y `07_NOTAS.md` son las bitácoras **cerradas** de los dos
primeros dominios migrados bajo la capa 7. Esta es la tercera, y es
**independiente**: su commit base, sus subcapas, su compuerta y su cierre son
propios. Cerrar `ventas` no reabre ninguna de las dos, ni al revés.

**Las subcapas se numeran por bitácora**, así que esta capa vuelve a empezar en
**7.0**. Existen por tanto una «7.0 de dashboard» y una «7.0 de notas», ambas
cerradas, y una «7.0 de ventas», que es la pendiente. En prosa deben citarse
siempre con el nombre del dominio; el número solo no identifica una subcapa.

## Objetivo

Migrar el dominio de **ventas** con contratos y pruebas, conservando su
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

## Por qué este dominio es distinto de los dos anteriores

`dashboard` llegó sin deudas ajenas: ninguna capa anterior había tocado su
código. `notas` llegó casi igual: lo único heredado era que otros módulos leían
su tabla.

**`ventas` llega con frontera ajena ya construida.** La capa 5 tomó una decisión
explícita sobre él y la registró con evidencia: las cinco sentencias que tocan
la tabla `ventas` viven hoy en `app/repositories/pagos_repository.py`, en un
bloque rotulado como **el efecto de un pago sobre un cargo**, no como
persistencia general de ventas. El motivo registrado entonces fue que
`venta_controller.py` ya tenía su propio SQL inline, que no existía un
`ventas_repository`, que crear uno habría tenido **un solo consumidor real**, y
que migrar `venta_controller` estaba **fuera del alcance de la capa 5**.

Ese aplazamiento es lo que esta capa recoge. Y trae consigo **el punto de
decisión propio y más importante de esta bitácora**, que 7.0 debe dejar
documentado y que **no se resuelve por inferencia**: si aparece un
`ventas_repository`, hay que decidir con evidencia si esas cinco sentencias de
`pagos_repository` **se quedan donde están** o **se mueven**. Las dos salidas
tienen precedente en el programa y ninguna es automática:

- **se quedan**: es lo que 5.2 decidió con evidencia, lo que 6.2 repitió con las
  cuatro lecturas del expediente de estudiantes y lo que 7.1 de dashboard y 7.1
  de notas volvieron a aplicar. El criterio constante es que la vecindad no
  manda: una consulta vive donde está el código que la necesita, y **poner una
  consulta junto a otras parecidas invita a «arreglarla»**;
- **se mueven**: solo si 7.0 demuestra que son persistencia general de ventas y
  no el efecto de un pago, y **aun así ampliaría el diff a un módulo que la capa
  5 cerró**, que es exactamente lo que 7.1 de dashboard rechazó hacer.

**Mover código de `pagos_repository` no está autorizado por esta activación.**
Requeriría una orden explícita después de que 7.0 presente la evidencia.

## Perfil de riesgo esperado, **no verificado**

Si el dominio escribe, su perfil es el de la capa 5 y el de `notas`, no el de
`dashboard`. Hay un indicio fuerte pero **indirecto**: 5.0 contó `ventas` entre
las **seis tablas escritas** del dominio de pagos. Eso demuestra que **la tabla**
se escribe; **no** demuestra que la escriba el dominio `ventas`. 7.0 debe
separar las dos cosas.

Una diferencia favorable frente a `notas`, y esta sí es un hecho registrado:
**`ventas` no fue una de las ocho tablas averiadas** de `tenant_2005` que la
capa 3 reparó. Esas ocho eran `estudiantes`, `profesor`, `asignaciones`,
`asistencia`, `notas_detalle`, `pagos`, `boletin_cabecera` y `boletin_detalles`.
La capa 7 de `notas` cargó con ese antecedente porque `notas_detalle` sí estaba
en la lista; esta no.

Lo que sí comparte con `notas`: las **26 claves foráneas repuestas por la capa
3** siguen vigentes en `tenant_2005`, así que una inserción que antes pasaba en
silencio puede fallar hoy en cualquier dominio que escriba.

## Dependencias de capas anteriores

- Compuerta única `scripts/verify.py`, heredada de la capa 0. El último
  resultado registrado, al cerrar la capa 7 para `notas`, es **791 pruebas,
  exit 0**, Ruff correcto y `pip check` íntegro; **no se reprodujo durante esta
  activación documental**. 7.0 debe reproducirlo antes de tocar nada.
- Ciclo de vida de conexiones, transacciones y timeouts definido en la capa 1.
  El valor operativo final de `DB_STATEMENT_TIMEOUT_MS` sigue **pendiente y
  aceptado**: el candidato de 15000 ms está documentado y **no aplicado**, y
  continúa vigente 30000.
- DB síncrona fuera del event loop y limitador compartido de capacidad
  establecidos en la capa 2. Esta capa no puede reintroducir trabajo bloqueante
  en el event loop ni cambiar esa capacidad sin una auditoría propia. Sobre
  `MAX_DB_CONNECTIONS_PER_THREADPOOL_WORKER = 2` sigue pesando el pendiente del
  2026-08-17: se quedó sin ejemplo real que la respalde y se conserva como
  margen. Las capas 7 de dashboard y de notas encontraron caminos de **cuatro
  conexiones en serie sin anidamiento**, evidencia relevante que quedó
  registrada **sin actuar**. Si `ventas` aporta un tercer caso, se registra
  igual: **no se toca la constante**.
- Tenants versionados y alta reproducible cerrados en la capa 3. Quedan dos
  schemas, `tenant_2005` —el único de producción— y `tenant_colegio_1`
  —plantilla y demo—, ambos con 37 claves foráneas, 30 secuencias propias y 30
  migraciones registradas.
- Contratos de lectura financieros fijados por la capa 4 y protegidos por su
  caracterización, con los conteos **6/15** del estado de cuenta de reportes,
  **1/13/37** de cuentas y **5/12/12** de cartera. Dependen de `cobros.py`.
  **Esta es la dependencia más peligrosa de la capa**: es el dominio financiero
  y `ventas` está dentro de él.
- Frontera de persistencia de pagos establecida en la capa 5, con
  `pagos_repository` en **16 funciones** y `pagos_controller.py` reducido a **3
  sentencias inline**. **Cinco de esas funciones tocan la tabla `ventas`.**
- Fronteras de estudiantes y asignaciones cerradas por la capa 6.
  `estudiantes_repository` **lee `ventas`** dentro del bloque rotulado como el
  expediente de un estudiante: es un consumidor **ya migrado** cuyo contrato
  esta capa no puede romper.
- Fronteras de dashboard y notas cerradas por la capa 7, con
  `dashboard_repository` en 8 funciones y `notas_repository` en 9. Sus 42 y 34
  pruebas de caracterización deben seguir pasando.

## Lo que el programa cree saber de `ventas`, y que 7.0 debe verificar

Aplica la lección 12 que dejó la capa 6 y que las dos capas 7 confirmaron: **un
supuesto heredado se marca como no verificado y se comprueba en la subcapa 0**.
La capa 6 se activó anticipando que sus dominios escribían archivos, y era
falso. De los siete supuestos de dashboard **uno resultó falso**; de los diez de
`notas` **uno resultó incompleto**, y era precisamente el que fijaba la frontera
del dominio: daba por hechos dos archivos y eran cuatro.

Ninguno de los de abajo procedía de haber leído el código de `ventas`. Todos
eran restos de lo que las capas 3, 4, 5 y 6 observaron desde fuera, **más una
inferencia de patrón marcada como tal**.

**Los doce quedaron resueltos en 7.0**, uno por uno y con evidencia. **Once se
confirmaron y uno resultó falso**, el que procedía de la inferencia de patrón.

| # | Supuesto | Resultado en 7.0 |
|---:|---|---|
| 1 | El dominio vive en `app/routes/ventas.py` y `app/controllers/venta_controller.py` | **Confirmado, y esta vez el recuento sale al revés que en `notas`: son exactamente DOS archivos, no cuatro.** No existe `app/services/venta_service.py` ni `app/schemas/venta.py`. Matiz que la búsqueda destapó: los tres modelos Pydantic —`VentaDetalleCreate`, `VentaCreate` y `VentaAnular`— **viven dentro de la ruta**, y es el **único dominio del programa** cuyos esquemas no están en `app/schemas/` |
| 2 | **`venta_controller.py` tiene SQL inline propio** | **Confirmado y cuantificado: 17 sentencias**, todas en el controlador y **0 en la ruta**. Es más SQL inline del que tenía `notas` —9— y del que tenía `dashboard` —8— |
| 3 | **No tiene repositorio propio** | **Confirmado.** Hay siete repositorios —asignaciones, dashboard, estudiantes, notas, pagos, plan de clases y reportes— y ninguno es de ventas. Fijado por prueba |
| 4 | **`pagos_repository` contiene cinco sentencias que tocan `ventas`** | **Confirmado exactamente, con un matiz que importa.** Clasificando **por tabla** son cinco: `leer_saldo_de_venta`, `leer_venta_para_anular`, `abonar_a_venta`, `marcar_venta_pagada` y `ajustar_venta_tras_anulacion`. Clasificando **por nombre** saldrían seis, porque `asignar_venta_a_pago` lleva «venta» en el nombre y **escribe `pagos`**. Esa sexta función es además la que delata el vínculo por texto: su docstring dice que rellena `venta_id` «en un pago heredado que solo lo tenía en el texto» |
| 5 | **La tabla `ventas` se escribe** | **Confirmado y muy ampliado.** No es que la tabla se escriba desde pagos: **el dominio escribe CUATRO tablas** —`ventas`, `ventas_detalle`, `inventario` y **`pagos`**—, tiene **dos transacciones propias** —`crear_venta` y `anular_venta`—, y a diferencia de `notas` **sí tiene `UPDATE` y hasta un `DELETE`** |
| 6 | **`estudiantes_repository` lee `ventas`** | **Confirmado.** Una lectura del expediente que cruza `ventas`, `ventas_detalle` e `inventario` a la vez |
| 7 | **Existe un «cargo de inventario»** que cuesta 4 consultas | **Confirmado desde este lado.** La descripción «Cargo de Inventario #N» la **fabrica este dominio**, en `obtener_ventas_pendientes`, y es la que `anular_venta` intenta reconocer después con `ILIKE`. Ver el hallazgo 2 |
| 8 | **No escribe archivos** | **Confirmado.** Ninguno de los dos archivos del dominio menciona `storage`. El rollback no necesita cubrir archivos |
| 9 | **Los permisos no son uniformes** | **REFUTADO, y es el supuesto que resultó falso.** Las **cinco entradas** usan el **mismo y único** modelo: `get_current_active_admin`, admin estricto con 403. **Es el primer dominio del programa con permisos uniformes**, frente a los cuatro modelos de dashboard y los dos de notas. La inferencia de patrón estaba marcada como tal precisamente para esto |
| 10 | **Otros módulos leen sus tablas** | **Confirmado y cuantificado.** `ventas` la tocan **cinco** módulos además del propio —`pagos_repository`, `estudiantes_repository`, `cartera_mora_controller` y las referencias de `main` y de la ruta—; `ventas_detalle`, **dos**; e `inventario`, **ocho**. Menos compartida que `notas_detalle`, que tenía siete lectores, pero con la diferencia de que aquí **dos módulos ajenos la escriben o la bloquean** |
| 11 | **`ventas` no estuvo entre las ocho tablas averiadas de la capa 3** | **Confirmado documentalmente**, sin cambio |
| 12 | **La cifra es el contrato** | **Confirmado y agravado.** El dominio maneja dinero con **`float` de Python** y no usa `Decimal` en ningún punto; el saldo pendiente se resta en Python sin redondear; y el `total` de la venta **lo fija el cliente** en el payload y **no se compara** con la suma de los subtotales |

## Alcance autorizado

- Inventariar entradas HTTP, reglas, cálculos, consultas, escrituras, archivos,
  pruebas y consumidores **de ventas** mediante búsquedas dirigidas.
- Caracterizar antes de extraer: rutas, métodos, payloads, status codes,
  permisos, roles, tenant, ownership, orden, nulos, **importes, redondeos y
  decimales**, transacciones y errores.
- Separar progresivamente HTTP, reglas, servicios y persistencia siguiendo el
  patrón ya probado cinco veces, con pruebas de caracterización previas a cada
  extracción importante.
- Contar y comparar consultas **y conexiones** críticas antes y después. Las dos
  capas 7 anteriores demostraron que medir solo consultas esconde el coste real.
- **Leer** `pagos_repository.py` y `estudiantes_repository.py` lo indispensable
  para clasificar sus sentencias sobre `ventas` y documentar el punto de
  decisión. **Leer no es mover**: modificarlos exige una orden explícita
  posterior a la evidencia de 7.0.
- Agregar `response_model`, errores de dominio y pruebas HTTP o de integración
  **solo después** de caracterizar y demostrando que la respuesta existente se
  conserva.
- Medir con `EXPLAIN ANALYZE` conforme al criterio corregido en la capa 4:
  `SELECT` en producción bajo transacción `READ ONLY` cerrada con `rollback`.
  Ninguna medición puede escribir.

## Fuera de alcance

- **Todos los demás dominios de la capa 7**: boletín, asistencia,
  observaciones, planilla, planeador anual, plan de clases, branding,
  profesores, super admin y cualquier otro. Esta capa es de un solo dominio. Se
  permite la lectura mínima indispensable para caracterizar un contrato que
  `ventas` consuma o que consuma de `ventas`, sin modificarlo.
- **`pagos`, `estudiantes`, `asignaciones`, `dashboard` y `notas`, ya
  migrados.** Sus fronteras de persistencia están cerradas y sus pruebas de
  caracterización deben seguir pasando. **Mover cualquier sentencia fuera de
  `pagos_repository` no está autorizado por esta activación.**
- `app/services/cobros.py`, del que dependen los contratos financieros de la
  capa 4, y `app/services/asignacion_academica.py`, del que dependen nueve
  módulos: se leen si hace falta, **no se tocan**.
- Los hallazgos abiertos de las capas 5, 6 y 7. En particular el **paso 2 de la
  clave de idempotencia** de `POST /pagos`, los status codes 500 de
  `tipos_pagos_controller`, la **ausencia de lock en el alta y la edición de
  asignaciones**, el `SELECT *` de `GET /estudiantes/{id}`, los **diez hallazgos
  de dashboard** y los **doce de notas**, empezando por el falso éxito de
  `POST /notas`. **No entran por inferencia**, por cerca que queden del código
  que esta capa toque.
- El trabajo registrado en `PROMPT_CONTINUACION.md` bajo «trabajo fuera del
  alcance de cualquier capa activa».
- Cambiar rutas, payloads, status codes, permisos, roles, ownership, reglas de
  cálculo, **importes**, redondeos, orden o semántica transaccional.
- Cambiar PostgreSQL, `psycopg2`, el modelo de schemas tenant, el pool, los
  timeouts, el limitador de concurrencia, el ORM, el driver o el almacenamiento
  de archivos.
- Migraciones reales, DDL, DML, deploy, commit o push.

## Invariantes

- Métodos, paths, status codes y forma exacta de las respuestas permanecen
  idénticos, incluidos los **importes, redondeos y número de decimales** de
  cualquier monto, saldo o total que el dominio presente.
- Permisos, roles, ownership y aislamiento entre tenants se conservan sin
  excepción.
- Los límites de transacción se conservan: qué se confirma junto, qué se
  revierte junto y quién es dueño de `commit`, `rollback`, cursor y conexión,
  conforme a la capa 1. **Si el dominio escribe, esta invariante es la más
  delicada de la capa.**
- Ninguna operación DB síncrona vuelve al event loop ni se altera el limitador
  compartido sin medir de nuevo su capacidad.
- Los contratos de lectura financieros fijados por la capa 4 siguen pasando su
  caracterización, incluidos los conteos 6/15, 1/13/37 y 5/12/12.
- Las fronteras de persistencia de las capas 5, 6 y 7 no se alteran: si `ventas`
  necesita una lectura que ya existe allí, se decide **con evidencia** y sin
  duplicarla a ciegas.
- El SQL de dominio se conserva hasta que una subcapa autorice, con
  caracterización previa, un cambio concreto.
- Ninguna escritura de archivos cambia de momento, de nombre ni de destino sin
  una decisión explícita y un rollback documentado.

## Línea base registrada en 7.0

| Comprobación | Comando | Resultado |
|---|---|---|
| Pruebas específicas | `.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_ventas_caracterizacion.py` | **41 pasaron** en 0,96 s |
| Suite global | `.\venv\Scripts\python.exe scripts\verify.py` | **832 pasaron**, 5 warnings heredadas, exit 0 |
| Ruff | Ejecutado por la compuerta global y sobre la prueba nueva | **Correcto** |
| Dependencias | Ejecutado por la compuerta global | **Íntegras** |

La compuerta heredada se reprodujo **antes de tocar nada**: **791 pruebas,
exit 0**, coincidiendo exactamente con lo registrado al cerrar la capa 7 para
`notas`. La suite pasó de **791 a 832** con la caracterización de 7.0.

## Inventario y contratos fijados en 7.0

**El dominio son dos archivos**, y es el más pequeño en superficie de los tres
migrados bajo la capa 7:

| Archivo | Líneas | Sentencias SQL |
|---|---:|---:|
| `app/routes/ventas.py` | 79 | **0** |
| `app/controllers/venta_controller.py` | 363 | **17** |

**Cinco entradas HTTP**, todas bajo el prefijo `/api/ventas`:

| Método y path | Controlador | Escribe |
|---|---|---|
| `GET /api/ventas/` | `obtener_ventas` u `obtener_ventas_paginado` según `limit` | no |
| `GET /api/ventas/pendientes/{estudiante_id}` | `obtener_ventas_pendientes` | no |
| `POST /api/ventas/` | `crear_venta` | **sí** |
| `DELETE /api/ventas/{venta_id}` | **ninguno**: responde 405 fijo | no |
| `POST /api/ventas/{venta_id}/anular` | `anular_venta` | **sí** |

**Permisos: un solo modelo.** Las cinco entradas usan
`Depends(get_current_active_admin)`, que exige `rol == 'admin'` estricto y
responde 403. Es el primer dominio del programa sin permisos heterogéneos.

### Propiedad transaccional

El dominio abre la conexión con **`get_connection()`**, no con el `get_cursor()`
que usan los dominios migrados después de la capa 1. Las cinco funciones que
consultan siguen el patrón de la capa 1 —`try` / `finally` con `cursor.close()`
y `conn.close()`— así que **no hay fugas**, pero el idioma es el antiguo. Es un
dato para 7.1: el repositorio recibirá el cursor existente, y **quien conserva
la propiedad de conexión, `commit` y `rollback` es el controlador**.

Hay **dos transacciones propias** —`crear_venta` y `anular_venta`, ambas con
`commit` y `rollback` explícitos— más una tercera en `eliminar_venta`, que
commitea pero **no tiene consumidor**.

### Tablas escritas: cuatro

| Tabla | Desde | Operación |
|---|---|---|
| `ventas` | `crear_venta`, `anular_venta`, `eliminar_venta` | `INSERT`, `UPDATE`, `DELETE` |
| `ventas_detalle` | `crear_venta` | `INSERT` |
| `inventario` | `crear_venta`, `anular_venta` | `UPDATE` de stock |
| **`pagos`** | `anular_venta` | `UPDATE` |

La cuarta es el hallazgo estructural de la subcapa: **`pagos` tiene repositorio
propio desde la capa 5 y aun así se escribe desde aquí con SQL inline.**

## Línea base de consultas y conexiones

Medida con dobles, a través del controlador. **Todos los caminos abren una sola
conexión**, que es mejor que las cuatro de `notas` y las cuatro de `dashboard`.

| Camino | Conexiones | Consultas |
|---|---:|---|
| `obtener_ventas` | 1 | **2** fijas, **sin `LIMIT`** |
| `obtener_ventas_paginado` | 1 | **3**, o 2 si la página sale vacía |
| `obtener_ventas_pendientes` | 1 | **2**, o 1 si el estudiante no tiene cargos |
| `crear_venta` | 1 | **1 por producto distinto + 1 + 2 por detalle** |
| `anular_venta` | 1 | **4 + 1 por detalle** |

**No hay N+1 por estudiante.** Los dos conteos variables dependen del tamaño del
carrito o del número de líneas de la venta, no del número de estudiantes ni de
materias. Es el mismo criterio con que 5.0 concluyó que pagos no tenía N+1, y el
contraste con `notas`, que sí lo tiene.

Detalle medido: `crear_venta` **agrega las cantidades por producto antes de
validar**, así que dos líneas del mismo artículo cuestan **una sola** validación
y no dos.

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 7.0 | Inventario, contratos, caracterización y línea base de consultas y conexiones | **Cerrada** el 2026-08-20 |
| 7.1 | Extraer las 17 sentencias a `ventas_repository` sin cambiar SQL, conteos ni ciclo de vida | **Cerrada** el 2026-08-20 |
| 7.2 | Punto de decisión sobre las cinco sentencias de `pagos_repository`, `response_model` y errores de dominio | **Sin decidir**: es un punto de decisión, no una subcapa pendiente |

El desglose se dejó deliberadamente sin decidir hasta tener la evidencia del
inventario, igual que hicieron la capa 6 y las dos capas 7 anteriores. Con esa
evidencia, **7.1 queda definida** y el resto sigue abierto. Las subcapas
innecesarias se marcarán `No aplica` con explicación. **Nunca se ejecutan dos
subcapas en el mismo turno.**

## Hallazgos de 7.0, registrados y sin corregir

Son **once**. Ninguno se corrige en esta capa: 7.0 inventaría y caracteriza, no
arregla. Todos quedan fijados por aserción para que una extracción posterior no
los cambie sin que alguien lo note.

1. **`anular_venta` escribe `pagos` con SQL inline.** La capa 5 cerró la
   frontera de pagos y dejó su persistencia en `pagos_repository`; este
   `UPDATE pagos` de siete líneas vive en `venta_controller.py` y **el
   controlador ni siquiera importa el repositorio**. La frontera que la capa 5
   dio por cerrada tiene un escritor fuera de sí misma. Es el hallazgo
   estructural de la subcapa.
2. **El vínculo entre un pago y su cargo es por texto, con `ILIKE` sin
   delimitar.** `anular_venta` alcanza los pagos con
   `descripcion ILIKE '%Cargo #N%'`. Como el número no está delimitado por
   ningún carácter de cierre, **anular la venta 4 alcanza los pagos de la venta
   40**, cuya descripción es «Abono a Cargo #40 (…)». Es dinero: marca como
   anulados pagos de otra venta. Verificado por aserción.
3. **Y el mismo patrón no reconoce su propia otra forma.** El dominio fabrica
   dos descripciones en `obtener_ventas_pendientes`: «Abono a Cargo #N (…)» y
   «Cargo de Inventario #N: …». La segunda **no contiene** la subcadena
   «Cargo #N», así que el `ILIKE` no la ve y esos pagos solo se alcanzan por
   `venta_id`. Los hallazgos 2 y 3 son el mismo defecto por los dos lados: de
   más y de menos.
4. **`eliminar_venta` es código muerto que borra físicamente.** No tiene ningún
   consumidor —ni en `app/` ni en `tests/`—, hace `DELETE FROM ventas` y
   commitea, y es **la única sentencia `DELETE` del dominio**. La ruta
   `DELETE /api/ventas/{id}` responde 405 diciendo expresamente que «las ventas
   no se eliminan físicamente». La función contradice la política que declara su
   propia ruta. **No se retira**: la capa 6 sentó el precedente de dejar el
   código muerto registrado en vez de borrarlo, por decisión explícita del
   usuario.
5. **`obtener_ventas()` no tiene `LIMIT`.** La lectura sin paginar trae la tabla
   entera con sus detalles. Hoy la ruta solo la usa cuando el cliente no manda
   `limit`, así que el frontend desplegado decide el coste.
6. **El `total` de la venta lo fija el cliente.** Viaja en el payload y se
   inserta sin compararlo con la suma de los subtotales, que también vienen del
   cliente. Una petición puede declarar un total de 1 con líneas por 999999.
7. **El dinero se maneja como `float` de Python.** El controlador convierte con
   `float()` y **no usa `Decimal` en ningún punto**; el saldo pendiente se resta
   en Python sin redondear. Es la instancia financiera del riesgo que la capa 7
   viene registrando como «la cifra es el contrato».
8. **No se comprueba que el estudiante exista ni su ownership.**
   `estudiante_id` entra tal cual y ninguna consulta del alta toca la tabla
   `estudiantes`. El aislamiento entre colegios lo da el `search_path`, no el
   dominio. Es el mismo criterio que la capa 5 registró para pagos, y aquí queda
   anotado sin levantarlo como hueco.
9. **`_formatear_venta` lee la fila por posición con guardas defensivas**
   —`row[9] if len(row) > 9`—, así que el contrato de la fila no está fijado por
   tipo y depende del orden del `SELECT`. Cualquier reordenación de columnas en
   7.1 cambiaría la respuesta en silencio; por eso 7.0 lo fija por aserción.
10. **La ruta declara un endpoint que nunca hace nada.**
    `DELETE /api/ventas/{venta_id}` está registrado, aparece en el OpenAPI y
    solo levanta 405. No es un defecto de comportamiento, pero sí de contrato
    publicado.
11. **Los esquemas Pydantic viven dentro de la ruta**, no en `app/schemas/`. Es
    el único dominio del programa así. No afecta al comportamiento; afecta a
    dónde tendría que mirar quien busque el contrato de entrada.

### Lo que 7.0 buscó expresamente y **no** encontró

La entrega de `notas` pedía buscar aquí el patrón de su hallazgo más grave: una
escritura que responde 200 sin haber escrito. **No está.** Y el contraste quedó
fijado con peticiones HTTP reales:

- `POST /api/ventas/` con una validación fallida responde **400**, no 200: la
  ruta traduce `ValueError` a `HTTPException`, así que el cliente **sí se entera**
  de que no se guardó nada;
- su campo `id` es **un entero plano**, no un diccionario como el de
  `POST /notas`;
- un payload inválido responde **422**, y un motivo de anulación corto, **400**.

Este dominio usa el mecanismo de error de FastAPI donde `notas` no lo usaba.

## Subcapa 7.0 — trabajo exacto, ejecutado y cerrado

1. **Reproducir la compuerta heredada antes de tocar nada** y comprobar que da
   791 pruebas y exit 0.
2. **Determinar la frontera real del dominio** por búsqueda dirigida, sin
   fiarse de los nombres de archivo. Es la lección directa de `notas`: allí el
   supuesto de dos archivos escondía un tercio de la persistencia en un
   servicio.
3. **Inventariar las entradas HTTP** con su método, path, permisos, roles,
   payload de entrada y forma exacta de la respuesta.
4. **Determinar si el dominio escribe**, qué tablas, con qué transacción y quién
   es dueño de `commit`, `rollback`, cursor y conexión. Distinguir lo que
   escribe `ventas` de lo que escribe `pagos` sobre la misma tabla.
5. **Contar y clasificar las sentencias que tocan `ventas` fuera del dominio**,
   en `pagos_repository` y en `estudiantes_repository`, para documentar el punto
   de decisión. **Sin mover ninguna.**
6. **Contar las sentencias SQL inline** del dominio, por archivo.
7. **Fijar la línea base de consultas y conexiones** de cada camino, con
   dobles, como hicieron 7.0 de dashboard y 7.0 de notas.
8. **Resolver los doce supuestos** de la tabla de arriba, uno a uno y con
   evidencia, dejando constancia de cuáles se confirman, cuáles se refutan y
   cuáles resultan incompletos.
9. **Registrar los hallazgos sin corregir ninguno.**
10. Archivos permitidos: **un archivo de prueba nuevo** y esta bitácora. Ningún
    archivo de producto, como en 5.0, 6.0, 7.0 de dashboard y 7.0 de notas.
11. Verificación: pruebas específicas, compuerta global, Ruff, `pip check`,
    `git diff --check` y revisión del alcance del diff.
12. **Punto exacto donde detenerse**: con 7.0 cerrada y su bitácora actualizada.
    **No iniciar 7.1**, ni siquiera si la extracción parece evidente.

Nota sobre la evidencia HTTP: 7.0 de `notas` descubrió que **no existe ni un
solo `TestClient`** en `tests/`, y que las capas 4 a 7 registraron status codes
a partir de pruebas que solo invocan funciones. Consiguió medirlos conduciendo
la aplicación por su **interfaz ASGI cruda**, porque `httpx` no está instalado y
una subcapa de inventario no cambia dependencias. **En un dominio financiero esa
técnica vale la pena**: si aquí hay una entrada que responde 200 sin haber
escrito, como `POST /notas`, el daño es de dinero.

## Criterios de cierre de la subcapa 7.0

- El dominio queda inventariado: archivos, entradas HTTP, permisos, tablas
  leídas y escritas, transacciones y sentencias inline.
- Los doce supuestos quedan resueltos uno a uno, con evidencia.
- La línea base de consultas **y conexiones** queda fijada por aserción.
- El punto de decisión sobre las sentencias de `pagos_repository` queda
  documentado con evidencia, **y sin resolver por inferencia**.
- Los hallazgos quedan registrados **sin corregir**.
- Pruebas específicas, compuerta global, Ruff y dependencias correctos.
- Diff exclusivo de la subcapa: un archivo de prueba nuevo y esta bitácora.
- `git diff --check` correcto.

Estado de los ocho criterios al 2026-08-20:

| Criterio | Estado |
|---|---|
| Dominio inventariado | **Cumplido**: 2 archivos, 5 entradas, 1 modelo de permiso, 4 tablas escritas, 2 transacciones propias y 17 sentencias inline |
| Doce supuestos resueltos | **Cumplido**: once confirmados y **uno refutado**, el de los permisos |
| Línea base de consultas y conexiones | **Cumplido**: cinco caminos fijados por aserción, una conexión cada uno |
| Punto de decisión documentado sin resolver | **Cumplido**: las cinco funciones quedan clasificadas por tabla y fijadas por prueba; **no se movió ninguna** |
| Hallazgos registrados sin corregir | **Cumplido**: once, ninguno corregido |
| Pruebas, compuerta, Ruff y dependencias | **Cumplido**: 41 específicas y **832 globales, exit 0** |
| Diff exclusivo | **Cumplido**: un archivo de prueba nuevo y esta bitácora; **ningún archivo de producto** |
| `git diff --check` | **Cumplido**: limpio |

**Los ocho criterios quedan resueltos. La subcapa 7.0 queda cerrada.**

## Resultado de 7.1

**Las 17 sentencias salieron del controlador a
`app/repositories/ventas_repository.py`, 17 funciones que reciben el cursor
existente y el octavo repositorio del proyecto.**

| Métrica | Antes | Después |
|---|---:|---:|
| `venta_controller.py`, líneas | **363** | **278** |
| `venta_controller.py`, sentencias SQL inline | **17** | **0** |
| `app/routes/ventas.py`, sentencias SQL inline | 0 | 0 |
| Repositorios del proyecto | 7 | **8** |

**Comparador AST contra el commit base `58c5233`: 17 literales SQL distintos
antes y después, conjunto idéntico, con 17 de 17 byte a byte**, y 17 puntos de
llamada antes y después. **No hizo falta autorizar ningún cambio de texto SQL**,
como en la capa 6 y en las dos capas 7 anteriores, y a diferencia de la 5, que
necesitó dos.

Conservar los literales byte a byte exigió reproducir la sangría interior de
cada uno en su nueva ubicación, aunque quede visualmente rara, y **escribir con
un escape explícito `\x20` los tres espacios finales** que traían los literales
de `leer_ventas_pendientes_de_estudiante`, `insertar_venta` e
`insertar_detalle_de_venta`. Es la misma solución que 5.1 adoptó en
`pagos_repository.abonar_a_venta`: el valor en tiempo de ejecución no cambia y
`git diff --check` sigue limpio.

**El controlador conserva la propiedad del ciclo de vida**: seis aperturas de
conexión, seis cierres, tres `commit` y dos `rollback`, fijados por aserción. El
repositorio **no abre, no cierra, no confirma y no revierte** nada, y también
está fijado por prueba. Son seis y no cinco porque `eliminar_venta` —el código
muerto del hallazgo 4— también abre su conexión y commitea; **7.1 no lo retira**.

### Equivalencia en tiempo de ejecución, incluida la de parámetros

**El comparador AST compara texto SQL, no parámetros.** Un intercambio de
argumentos al extraer —pasar `inventario_id` donde iba `cantidad`, por
ejemplo— produciría un conjunto de literales idéntico y **no lo detectaría**. Es
un hueco de evidencia que arrastran todas las extracciones del programa, porque
todas se apoyaron en ese comparador.

Se cerró para esta subcapa con una comprobación adicional: **ejecutar el
controlador del commit base y el actual con las mismas entradas y comparar la
secuencia exacta de `(SQL, parámetros)` y el valor devuelto**. Se cargó
`git show 58c5233:app/controllers/venta_controller.py` como módulo aparte, se
doblaron `get_connection` y el reloj, y se recorrieron los seis caminos.

| Camino | Consultas | `(SQL, parámetros)` idénticos | Retorno idéntico |
|---|---:|---|---|
| `obtener_ventas` | 2 | sí | sí |
| `obtener_ventas_paginado` | 3 | sí | sí |
| `obtener_ventas_pendientes` | 2 | sí | sí |
| `crear_venta`, dos productos distintos | 7 | sí | sí |
| `eliminar_venta` | 1 | sí | sí |
| `anular_venta`, dos líneas | 6 | sí | sí |

**Los seis idénticos.** Es la evidencia más fuerte que ha producido una
extracción en este programa, porque cubre lo que el comparador AST no ve. **Es
una comprobación de un solo uso, no una prueba permanente**: fijarla en la suite
exigiría conservar el archivo del commit base, y hacerlo queda como trabajo
disponible.

### Las guardias que fallaron, que era la señal esperada

**Fallaron seis pruebas al extraer**, y las seis eran previsibles. Es la lección
14 de la capa 6, aplicada por cuarta vez.

| Prueba | Por qué falló |
|---|---|
| `test_el_dominio_todavia_no_tiene_repositorio_propio` | Guardia de línea base declarada. Apareció el octavo repositorio |
| `test_las_diecisiete_sentencias_viven_hoy_en_el_controlador` | Guardia de línea base declarada. El controlador bajó a 0 |
| `test_la_escritura_de_pagos_vive_inline_en_el_dominio_de_ventas` | **No estaba declarada como guardia**: 7.0 la escribió como prueba de hallazgo, y describía el `UPDATE pagos` en el controlador |
| `test_eliminar_venta_es_codigo_muerto_que_borra_fisicamente` | Igual que la anterior: buscaba el `DELETE` entre los literales del controlador |
| `test_dashboard_caracterizacion.py::test_el_dominio_tiene_su_repositorio` | **Fuera del dominio.** Enumera el conjunto exacto de repositorios |
| `test_notas_caracterizacion.py::test_el_repositorio_de_notas_es_el_septimo` | **Fuera del dominio.** Mismo motivo |

**Corrección de lo que 7.1 había previsto**: la bitácora anunciaba que fallarían
**dos** guardias, las dos declaradas como tales en el bloque 1. Fallaron
**cuatro** dentro del dominio, porque **dos pruebas de hallazgo también estaban
ancladas al controlador** sin que 7.0 las hubiera clasificado como guardias de
línea base. No cambiaron de expectativa: se reapuntaron al repositorio
**conservando exactamente lo que denuncian**, que es que el dominio de ventas
sigue siendo quien escribe `pagos` y que el `DELETE` sigue sin consumidor.
Es una lección para la próxima subcapa 0: **una prueba de hallazgo anclada a un
archivo concreto es también una guardia de línea base**, aunque no se rotule así.

**Las otras 37 pruebas del dominio pasaron sin cambiar de expectativa**,
incluidos los ocho conteos de consultas y conexiones y las cinco de contrato
HTTP real. Esa es la evidencia de que nada observable cambió.

**Consecuencia fuera del dominio, por segunda vez en el programa**: las dos
guardias que enumeran el conjunto exacto de repositorios fallaron al aparecer el
octavo. **No era una rotura de contrato**; se actualizaron conservando su
severidad, porque esa severidad es deliberada y obliga a reconocer cada
migración nueva. Lo detectó **la compuerta global, no las pruebas de `ventas`**,
que es exactamente el riesgo que 7.0 había registrado. En 7.1 de `notas` ocurrió
lo mismo con una sola guardia; ahora son dos, porque `notas` añadió la suya.

### Decisión de 7.1 sobre el `UPDATE pagos`

Era la decisión difícil que 7.0 dejó planteada. **La sentencia vive en
`ventas_repository`, no en `pagos_repository`**, en un bloque rotulado como **el
efecto de anular una venta sobre sus pagos**.

Evidencia:

- es **simetría exacta** con lo que la capa 5 dejó escrito. `pagos_repository`
  tiene un bloque rotulado «el efecto de un pago sobre una venta» que conserva
  cinco sentencias sobre la tabla `ventas`, precisamente porque no son
  persistencia general de ventas. Esta es la operación inversa y responde al
  mismo criterio;
- llevarla a `pagos_repository` **ampliaría el diff a un módulo que la capa 5
  cerró**, que es lo que 7.1 de dashboard rechazó hacer con las precondiciones
  de permiso;
- y obligaría a `venta_controller` a **importar `pagos_repository`**, creando
  una dependencia entre dominios que 7.1 no está autorizada a introducir.

Alternativa descartada y **no cerrada**: moverla a `pagos_repository`, que es su
dueño natural por tabla. Sigue siendo defendible y **exigiría orden explícita**.
Queda en el punto de decisión.

El bloque lleva además una advertencia en el propio código sobre el `ILIKE` sin
delimitar, para que nadie lo «arregle» por vecindad. Es el criterio que 7.1 de
dashboard fijó y que 7.1 de notas repitió.

## Staging, rollback y verificación manual

### Lo que esta capa hizo y no hizo

Hasta 7.1, la capa 7 para `ventas` es **exclusivamente una refactorización**,
igual que la 5, la 6 y las dos capas 7 anteriores. No añadió funciones, no
cambió reglas, no tocó rutas, payloads, status codes, permisos, tenant,
ownership, transacciones, timeouts, dependencias ni configuración. Y **no abrió
una sola conexión a PostgreSQL**: ni migraciones, ni DDL, ni DML, ni lecturas de
medición. Toda la caracterización se hizo con dobles.

Es la **quinta capa consecutiva** que no abre una conexión a PostgreSQL, y la
segunda de esas cinco cuyo dominio escribe.

### Rollback

**Es puramente de código.** No hay nada que deshacer en datos ni en esquema.
Revertir los commits de la capa hasta
`58c5233afc4772ba040da690f4d719b518bb1b0a` devuelve el controlador a su versión
anterior y elimina el repositorio nuevo.

**Mientras la capa siga sin publicar, el rollback es una operación puramente
local.** Esa ventaja desaparece en cuanto se publique, porque un push a `main`
dispara el despliegue. Es la misma advertencia que `notas` registró, y que en su
caso dejó de aplicar al día siguiente.

No cambiar los timeouts durante el rollback.

### Staging

No se usó un entorno de staging y **no se considera necesario** para esta capa,
por la misma razón que hace trivial el rollback: no hay cambio de esquema, de
datos ni de SQL. Un despliegue prudente solo necesita comprobar que la
aplicación arranca y lo que cubre el guion de abajo.

### Verificación manual: **hecha, con la cobertura que el usuario reportó**

**Ejecutada por el usuario el 2026-08-20, en local, con resultado correcto.**

**Artefacto confirmado antes de registrarla**, conforme a la lección 10 de la
capa 5, y **sin ambigüedad**: el árbol estaba limpio y `HEAD` era
`8948e409075115d1bf5f4ee1a1769396fbeaa029`; el código de 7.1 vive en
`76f76e7`, que es ancestro suyo. Lo ejercitado y lo commiteado son el mismo
contenido.

**Alcance real de la evidencia, registrado sin inflarlo.** El usuario informó el
resultado **de forma global** —«ya verifiqué y se ve bien por ahora»— y **no
punto por punto contra los once pasos** del guion. Es una diferencia real con
`notas`, donde la respuesta se dio sobre un guion explícito y por eso su
bitácora pudo afirmar que no se infirió nada. Aquí **no consta** cuáles de los
once pasos se recorrieron ni si se comprobaron los dos tenants, la prueba
cruzada contra el expediente y la cartera, o el retorno exacto del stock tras
anular.

**Qué respalda entonces la capa**, y es bastante:

- la evidencia automática, que en esta subcapa es la más fuerte del programa:
  **17 de 17 literales SQL byte a byte** y, sobre todo, **los seis caminos
  emitiendo la misma secuencia de `(SQL, parámetros)` y devolviendo lo mismo**
  que el commit base;
- **835 pruebas en verde**, con los conteos de consultas y conexiones y los
  contratos HTTP fijados por aserción, y ninguna que cambiara de expectativa;
- el uso real que el usuario le dio a la aplicación, sin encontrar nada raro.

**Qué no respalda.** Que la aplicación «se vea bien» en un recorrido general
**no equivale** a haber comprobado el retorno exacto del stock tras una
anulación con abono parcial, ni la prueba cruzada de importes, ni el aislamiento
entre los dos tenants. Son los tres puntos del guion que más valor tenían en
este dominio, y **quedan sin evidencia registrada**.

**Limitación adicional**: la verificación fue **en local** y **este código no
está publicado**. Nadie lo ha ejercitado desplegado, ni puede: producción sigue
corriendo el código anterior a la capa.

Es aceptable por lo que la capa es —una refactorización con SQL y parámetros
demostrados equivalentes y sin ningún acceso a la base de datos—; no lo sería en
una capa que cambiara comportamiento o tocara datos. **El guion completo se
conserva abajo** por si el usuario quiere completar los pasos que no consten.

### Guion entregado

Es la única evidencia que no puede delegarse en un asistente. En este dominio
pesa más que en `dashboard` y algo más que en `notas`, por una razón concreta:
si la extracción hubiera roto algo, la consecuencia no sería un panel con cifras
raras ni una calificación perdida, sino **dinero mal contado y stock
descuadrado**.

Este es el guion que se entregó el 2026-08-20. Se conserva íntegro: la
verificación se reportó de forma global y no contra sus pasos, así que sigue
siendo la lista de lo que faltaría comprobar si se quisiera cerrar ese hueco.

Lo que la evidencia automática ya cubre, y que por tanto el guion **no** tiene
que buscar: que el SQL es el mismo —17 de 17 byte a byte—, que los parámetros y
los valores devueltos son los mismos en los seis caminos, y que los conteos de
consultas y conexiones no cambiaron. Lo que **solo** puede ver una persona es lo
que ocurre contra PostgreSQL real, con las claves foráneas de la capa 3 puestas
y con los dos tenants.

**Antes de empezar, confirmar el artefacto**: qué commit o árbol se está
ejercitando. Si el árbol tiene cambios sin commitear, lo verificado es el árbol,
no `HEAD`. Es la lección 10 de la capa 5.

Guion, en once pasos:

1. **Arranque.** La aplicación levanta sin error de importación. El repositorio
   nuevo es un módulo más y un error de import sería inmediato.
2. **Alta a crédito, ida y vuelta.** Crear una venta a crédito para un
   estudiante con **dos productos distintos** y cantidades distintas.
   Comprobar: responde `{"id": N, "mensaje": "Venta exitosa registrada!"}` con
   `id` **entero**; la venta aparece en el listado con su cliente, total y
   estado `Pendiente`; **el stock de los dos productos bajó exactamente lo
   vendido**; y el cargo aparece en los pendientes del estudiante con la
   descripción «Cargo de Inventario #N: …».
3. **Alta de contado.** La misma operación con `tipo_venta: "Contado"` queda en
   estado **`Pagado`** y **no** aparece en pendientes.
4. **Las tres validaciones y su rollback.** Intentar vender un producto
   **inactivo**, uno con **stock insuficiente** y uno con **cantidad 0**. Las
   tres deben responder **400** con el mensaje correspondiente, y en las tres
   hay que comprobar después que **no se creó ninguna venta y que el stock no se
   movió**. Es lo que ejercita el `rollback`, que sigue siendo del controlador.
5. **Dos líneas del mismo producto.** Una venta con dos líneas del mismo
   artículo debe descontar **la suma** de las dos cantidades, y respetar el
   stock disponible para el total agregado, no para cada línea por separado.
6. **Paginación y filtros.** Probar `limit` y `offset`, y los filtros por
   `busqueda` —que mira nombre, apellido y notas—, `estudiante_id` y `estado`.
   Comprobar que el campo `total` de la respuesta cuadra con el número real de
   filas que cumplen el filtro, y que el orden es por fecha descendente.
7. **Anulación completa**, el paso más delicado. Anular una venta a crédito que
   **tenga un abono parcial registrado**. Comprobar: responde 200; la venta
   queda en estado **`Anulada`** con `pagado` en **0** y con motivo, fecha y
   responsable puestos; **el stock vuelve exactamente** a lo que había antes de
   la venta; y **los pagos de esa venta quedan en estado `Anulado`** con su
   motivo.
   **Elegir para esta prueba una venta cuyo id no sea prefijo de otro id
   existente** —por ejemplo, no usar la venta 4 si existe una venta 40—. Si se
   usa un id que sí es prefijo, se verá el hallazgo 2 y **no es un fallo de esta
   refactorización**: ver la lista de abajo.
8. **Los dos rechazos de la anulación.** Un motivo de menos de 5 caracteres
   responde **400**; anular una venta **ya anulada** responde **400**. En los dos
   casos comprobar que el stock **no** se movió una segunda vez.
9. **El borrado.** `DELETE /api/ventas/{id}` responde **405** con el mensaje que
   remite al endpoint de anulación. No borra nada.
10. **Permisos y consumidores ajenos.** Con un usuario **profesor**, las cinco
    entradas responden **403**. Y con admin, comprobar que los importes de esta
    venta coinciden **al céntimo** en los dos sitios ajenos que leen estas
    tablas: el **expediente del estudiante** y el reporte de **cartera vencida**.
    La extracción no los tocó, pero leen lo mismo y son la mejor prueba cruzada.
11. **Los dos tenants.** Repetir el alta y la anulación en el segundo colegio y
    comprobar que **no se mezclan datos**: las ventas de uno no aparecen en el
    otro y el stock de cada uno es independiente.

**Lo que NO debe interpretarse como fallo de la refactorización.** Son hallazgos
abiertos y **anteriores** a esta capa; están en la lista de los once:

- que anular la venta 4 alcance pagos de la venta 40, por el `ILIKE` sin
  delimitar —hallazgo 2—, y que en cambio no alcance por texto los cargos cuya
  descripción es «Cargo de Inventario #N» —hallazgo 3—;
- que el listado sin `limit` traiga la tabla entera y tarde —hallazgo 5—;
- que se pueda crear una venta con un `total` que no cuadre con la suma de sus
  líneas, si se manda a mano —hallazgo 6—;
- que se pueda crear una venta con un `estudiante_id` inexistente, si la clave
  foránea lo permite —hallazgo 8—;
- que `DELETE /api/ventas/{id}` aparezca en la documentación de la API aunque
  solo responda 405 —hallazgo 10—.

## Punto de decisión, resuelto el 2026-08-20

**La frontera de persistencia de `ventas` ya está cerrada**: ni el controlador
ni la ruta tienen SQL, y el repositorio existe. Lo que quedaba del objetivo que
el índice fijó para la capa 7 era la parte condicional, más una decisión propia
de este dominio que no tenían las dos bitácoras anteriores.

Eran tres cosas, y **ninguna entra por inferencia**:

1. **Dónde vive el `UPDATE pagos`.** Está en `ventas_repository` por las tres
   razones registradas en la decisión de 7.1. Moverlo a `pagos_repository` era
   la alternativa descartada, sigue siendo defendible y **exige orden
   explícita** porque toca un módulo cerrado.
2. **`response_model`.** Las cuatro entradas de lectura podrían declararlo
   demostrando payload por payload que la respuesta no cambia. Riesgo propio: en
   este dominio los payloads llevan **importes**, y `response_model` **filtra**
   los campos que no declara, así que un campo recortado puede ser un saldo.
3. **Errores de dominio.** Aquí el dilema era **menor que en `notas`**, y esa es
   la diferencia importante: `ventas` **ya usa** el mecanismo de error —responde
   400 ante una validación fallida— así que convertir sus `ValueError` en
   errores de dominio **no cambiaría ningún status code**. Era la única de las
   tres que habría sido una refactorización pura.

**El usuario eligió cerrar la capa aquí**, el 2026-08-20 y de forma explícita,
entre cuatro opciones planteadas —cerrar, abrir una 7.2 con los errores de
dominio, abrir una 7.2 que moviera el `UPDATE pagos`, o completar antes los tres
pasos del guion que no constan—. Consecuencias registradas, ninguna de ellas una
deuda oculta:

- La capa 7 para `ventas` es, como la 5, la 6 y las dos capas 7 anteriores,
  **exclusivamente una refactorización**. Ningún contrato observable cambió.
- **El `UPDATE pagos` se queda en `ventas_repository`.** La alternativa no se
  descarta para siempre: queda como trabajo disponible que exigiría una orden.
- **`response_model` y los errores de dominio no se añaden.** No quedan como
  trabajo pendiente de esta capa: quedan registrados como trabajo disponible.
- Los **once hallazgos de 7.0 siguen vivos y sin corregir**, incluidos los tres
  que hoy tienen efecto real sobre dinero: la colisión del `ILIKE` al anular, el
  `total` que fija el cliente y el `DELETE` muerto. Cerrar la capa **no los
  resuelve ni los cancela**, y **tampoco los introdujo**: los once son
  anteriores a este trabajo.
- **Los tres pasos del guion que no constan siguen sin constar.** El usuario
  eligió cerrar sin completarlos, sabiendo que la evidencia manual queda más
  débil que la de `notas`. No se marcan como cumplidos.

## Subcapa 7.1 — trabajo exacto, ejecutado y cerrado

1. Crear `app/repositories/ventas_repository.py`, **el octavo repositorio** del
   proyecto, con funciones que **reciben el cursor existente** y no abren ni
   cierran nada. La propiedad de conexión, `commit` y `rollback` **se queda en
   el controlador**.
2. Mover las **17 sentencias** conservando su texto **byte a byte**, incluidas
   las dos que se construyen con f-string en `obtener_ventas_paginado`. Si
   alguna necesitara cambiar de texto, **pedir autorización explícita**, como
   hizo 5.1 y como no necesitaron la capa 6 ni las dos capas 7.
3. **Decidir con evidencia dónde vive el `UPDATE pagos`** de `anular_venta`. Es
   el hallazgo 1 y no tiene respuesta obvia: podría ir a `ventas_repository`
   —porque es el efecto de una anulación de venta sobre los pagos, simétrico al
   criterio que la capa 5 aplicó al revés— o a `pagos_repository`, que ya es su
   dueño natural. **Mover algo a `pagos_repository` amplía el diff a un módulo
   cerrado y exige orden explícita del usuario.**
4. **No mover las cinco funciones** que ya viven en `pagos_repository`. Ese es
   el punto de decisión de 7.2, no de 7.1.
5. Conservar los **conteos de consultas y de conexiones** exactamente como 7.0
   los fijó. Reducirlos es una mejora real y **cambiaría aserciones**: queda
   como trabajo disponible.
6. Ejecutar el **comparador AST contra el commit base** `58c5233` para demostrar
   conjunto de SQL idéntico y literales byte a byte.
7. Las **cuatro guardias de línea base** que 7.0 dejó puestas
   —`test_el_dominio_todavia_no_tiene_repositorio_propio`,
   `test_las_diecisiete_sentencias_viven_hoy_en_el_controlador`,
   `test_la_ruta_no_contiene_sql` y
   `test_el_bloque_de_ventas_de_pagos_repository_conserva_sus_cinco_funciones`—
   **deben fallar las dos primeras y seguir en verde las dos últimas**. Es la
   señal esperada, lección 14 de la capa 6, aplicada por cuarta vez. Se
   sustituyen por versiones positivas.
8. **Ejecutar la compuerta completa**, no solo las pruebas del dominio: hay al
   menos una guardia en `test_dashboard_caracterizacion.py` que enumera el
   conjunto exacto de repositorios y **volverá a fallar al aparecer el octavo**,
   igual que falló en 7.1 de `notas` al aparecer el séptimo.
9. **No corregir ninguno de los once hallazgos.**
10. Punto exacto donde detenerse: con 7.1 cerrada y su bitácora actualizada.

## Criterios de cierre de la capa

- Todas las subcapas necesarias están cerradas o marcadas `No aplica` con
  justificación.
- El dominio queda migrado con contratos estables y pruebas, **sin arrastrar
  otros dominios**.
- `response_model`, errores de dominio y pruebas HTTP, si se añadieron, llegaron
  **después** de caracterizar y conservando la respuesta existente, demostrado.
- No se creó ninguna abstracción compartida sin dos consumidores reales.
- Los contratos del frontend y de la base de datos permanecen intactos, y
  también los de los cinco dominios ya migrados que leen o escriben estas
  tablas.
- **El punto de decisión sobre `pagos_repository` queda resuelto de forma
  explícita**, se mueva o no se mueva nada, con su evidencia y su alternativa
  descartada.
- La compuerta global, Ruff, dependencias y `git diff --check` terminan
  correctamente.
- Staging, rollback y verificación manual están documentados. **Si 7.0 descubre
  que el dominio escribe, el rollback debe cubrir datos explícitamente** y no
  puede declararse «puramente de código» sin comprobarlo.
- El índice maestro queda actualizado y **ningún otro dominio se activa sin
  orden explícita del usuario**.

Estado de los ocho criterios al 2026-08-20:

| Criterio | Estado |
|---|---|
| Subcapas cerradas o `No aplica` | **Cumplido**: 7.0 y 7.1 cerradas; no hubo más |
| Dominio migrado sin arrastrar otros | **Cumplido**: los únicos archivos tocados fuera del dominio son dos guardias de `test_dashboard_caracterizacion.py` y `test_notas_caracterizacion.py` que enumeran repositorios, y **no son código de producto** |
| `response_model` solo tras caracterizar | **No aplica**: el usuario decidió no añadirlo |
| Ninguna abstracción sin dos consumidores | **Cumplido**: el repositorio por módulo es la convención de `app/repositories/README.md`, con siete precedentes |
| Contratos del frontend y de la base intactos | **Cumplido**: comparador AST 17 de 17, **equivalencia de `(SQL, parámetros)` y de retorno en los seis caminos**, y 37 pruebas del dominio sin cambio de expectativa, incluidas las cinco de contrato HTTP real |
| Punto de decisión sobre `pagos_repository` resuelto | **Cumplido**: el `UPDATE pagos` vive en `ventas_repository`, con su evidencia y su alternativa descartada registradas; **las cinco funciones de `pagos_repository` no se movieron** |
| Compuerta, Ruff, dependencias y `git diff --check` | **Cumplido**: 835 pruebas, exit 0 |
| Staging, rollback y verificación manual documentados | **Cumplido con matiz.** El criterio exigía que, por tratarse de un dominio que escribe, el rollback cubriera datos explícitamente: **se comprobó, y es de código**, porque la capa no ejecutó nada contra la base. La verificación manual está documentada **con su cobertura real**, que es más débil de lo que el guion pedía |
| Índice actualizado y ningún dominio activado | **Cumplido** |

**Los ocho criterios quedan resueltos**, el último con su matiz registrado.

## Cierre de la capa 7 para `ventas`

### Resultado frente a su objetivo

| Objetivo | Resultado |
|---|---|
| Migrar el dominio con contratos y pruebas | `venta_controller.py` pasó de **363 a 278 líneas** y de **17 sentencias SQL inline a 0**; la persistencia vive en `ventas_repository`, **17 funciones** que reciben el cursor. **41 pruebas de caracterización** nuevas fijan payloads, permisos, conteos de consultas **y de conexiones**, ciclo de vida, aritmética del dinero y **status codes HTTP reales** |
| Un dominio a la vez | **Cumplido**: no se tocó código de producto de ningún otro dominio. Los ocho restantes siguen en espera |
| `response_model` solo tras caracterizar | **No se añadió**, por decisión explícita del usuario. No queda como deuda |
| Sin abstracciones sin dos consumidores | **Cumplido**: el repositorio por módulo es la convención documentada, con siete precedentes |

La suite pasó de **791 a 835** pruebas. Compuerta de cierre: **exit 0 con 835
pruebas**, Ruff correcto y `pip check` íntegro.

### Lo que esta capa NO hizo

- **No tocó la base de datos**, ni siquiera para leer. Es la **quinta capa
  consecutiva** que no abre una sola conexión a PostgreSQL, y la **segunda de
  esas cinco cuyo dominio sí escribe**.
- **No tocó archivos.** 7.0 lo comprobó: ninguno de los dos archivos del dominio
  menciona `storage`.
- No cambió rutas, payloads, status codes, permisos, tenant, ownership,
  transacciones, timeouts, dependencias ni configuración.
- **No corrigió ninguno de los once hallazgos** de 7.0. Siguen vivos.
- **No movió las cinco funciones** que la capa 5 dejó en `pagos_repository`, ni
  retiró el código muerto de `eliminar_venta`.
- **No necesitó autorizar ni un solo cambio de texto SQL**, como la capa 6 y las
  dos capas 7 anteriores.

### Lo que esta capa aporta al programa, más allá de su dominio

**Descubrió un hueco de evidencia que afecta a las capas 4 a 7 enteras**: el
comparador AST en que se apoyaron todas las extracciones compara **texto SQL
pero no parámetros**, así que un intercambio de argumentos habría pasado
inadvertido. 7.1 lo cerró **para esta capa** comparando la secuencia de
`(SQL, parámetros)` y el retorno de los seis caminos contra el commit base.
**Las extracciones anteriores no tienen esa evidencia**, y revisarlas es trabajo
ajeno a esta capa que queda anotado.

### Estado de publicación

**No publicada.** `origin/main` sigue en `58c5233`, el commit base de la capa, y
hay **cuatro commits locales por delante** —`040b027`, `2fbe83f`, `76f76e7` y
`8948e40`—, más el del cierre. **Producción no corre este código**: sigue con el
anterior a la capa.

Mientras siga así, **el rollback es una operación puramente local**. En cuanto
se publique, y como un push a `main` dispara el despliegue, esa ventaja
desaparece y revertir exigirá otro push. La publicación la decide y la ejecuta
el usuario.

**No se atribuye ningún run de GitHub Actions**: esa evidencia sigue sin
obtenerse desde la capa 0.

### Riesgos que la capa deja abiertos

- **Anular una venta alcanza los pagos de otra.** El `ILIKE '%Cargo #N%'` no
  delimita el número, así que anular la venta 4 marca como anulados los pagos de
  la venta 40. Es el riesgo más directo que deja esta capa, es **dinero**, está
  activo en producción y es **anterior a este trabajo**.
- **El mismo patrón no reconoce la otra descripción** que el propio dominio
  fabrica, «Cargo de Inventario #N», que solo se alcanza por `venta_id`.
- **`eliminar_venta` sigue siendo código muerto que borra físicamente**, con su
  `DELETE FROM ventas` y su `commit`, mientras su ruta responde 405.
- **El `total` de la venta lo fija el cliente** y no se compara con la suma de
  los subtotales.
- **El dinero se maneja como `float`**, nunca `Decimal`.
- **`anular_venta` escribe `pagos`** desde fuera de la frontera que la capa 5
  dio por cerrada. La extracción lo movió de sitio pero **no lo cambió**.
- **Tres pasos del guion de verificación manual no constan**: retorno del stock
  tras anular con abono parcial, prueba cruzada de importes y aislamiento entre
  tenants.
- El resto de los once hallazgos de 7.0, más `response_model` sin añadir.
- **Hueco de evidencia heredado**: las extracciones de las capas 4 a 7 anteriores
  no comprobaron equivalencia de parámetros, solo de texto SQL.
- Heredados: calibración de `DB_STATEMENT_TIMEOUT_MS` de la capa 1, ausencia de
  evidencia de GitHub Actions desde la capa 0, la credencial privilegiada de la
  capa 4 sin rotar, y los hallazgos abiertos de las capas 5, 6 y 7 —incluidas la
  clave de idempotencia, la ausencia de lock frente a horarios solapados, los
  diez de dashboard y los doce de notas—.

## Decisiones

- Se usa `58c5233afc4772ba040da690f4d719b518bb1b0a` como commit base porque es
  el `HEAD` limpio vigente de `main`, coincide con `origin/main` y el reflog lo
  registra como publicado por push. Alternativa descartada: reutilizar el base
  de `notas`, `eee8aec`, que dejaría fuera de auditoría los cuatro commits de
  esa capa.
- **El dominio lo eligió el usuario.** Se le presentó la lista de los diez que
  quedaban en espera junto a tres advertencias tomadas de las bitácoras
  cerradas: que `boletin` y `planilla` no son fronteras limpias porque `notas`
  ya posee esas rutas; que `ventas` es el único con un aplazamiento documentado;
  y que `branding` y `super_admin` cambian el perfil de riesgo, el primero por
  `storage.py` y el segundo por ser territorio de la capa 3. Eligió `ventas`.
  Alternativa descartada: deducir el dominio del aplazamiento de la capa 5, que
  habría sido justo la inferencia que el índice prohíbe.
- **Verificaciones heredadas: continuar aceptándolas pendientes.** Se preguntó
  explícitamente antes de escribir nada, ofreciendo también intentar cerrar la
  de CI, que hoy sí sería obtenible porque existe un push reciente sobre `main`.
  El usuario eligió continuar. **Ninguna se marca como cumplida** y ambas
  conservan su riesgo.
- **No se mueve nada de `pagos_repository` en esta capa sin una orden explícita
  posterior a la evidencia de 7.0.** Motivo: el criterio que 5.2, 6.2, 7.1 de
  dashboard y 7.1 de notas aplicaron cuatro veces es que la vecindad no manda y
  que una consulta vive donde está el código que la necesita. Alternativa
  descartada: dar por hecho que un `ventas_repository` debe recibirlas, que
  ampliaría el diff a un módulo que la capa 5 cerró.

## Riesgos

- **Es el dominio financiero.** Los contratos de la capa 4 —6/15, 1/13/37 y
  5/12/12— y la frontera de pagos de la capa 5 están alrededor de este código.
  Un error aquí no da una cifra rara en un panel: da **dinero mal contado**.
  Mitigación: caracterizar antes de mover, comparador AST contra el commit base
  y compuerta global completa en cada subcapa. Responsable de validarlo: el
  usuario, en la verificación manual.
- **La frontera ajena ya construida.** Cinco sentencias sobre `ventas` viven en
  `pagos_repository` y al menos una lectura en `estudiantes_repository`. Romper
  cualquiera de esos contratos **no haría fallar las pruebas de `ventas`**: solo
  la compuerta global. Es exactamente lo que ocurrió en 7.1 de notas con una
  guardia de dashboard. Mitigación: **ejecutar siempre la compuerta completa**,
  nunca solo las pruebas del dominio.
- **El supuesto de la frontera del dominio.** Es el que falló en `notas` y el
  que más daño hace, porque un inventario incompleto invalida todo lo que se
  construye encima. Mitigación: 7.0 busca por tabla y por símbolo, no por nombre
  de archivo.
- **Si el dominio escribe**, las 26 claves foráneas repuestas por la capa 3
  pueden hacer fallar inserciones que antes pasaban en silencio. Mitigación:
  no ejecutar nada contra la base; caracterizar con dobles, como las cuatro
  capas anteriores.
- **`response_model` filtra** en FastAPI los campos que no declara, así que
  añadirlo puede recortar un payload sin que falle nada. El índice solo lo
  autoriza tras caracterizar y conservar la respuesta existente. En un dominio
  de dinero, un campo recortado puede ser un saldo.
- **Riesgo heredado que sigue vivo**: `POST /notas` responde 200 «Nota
  registrada» aunque no registre nada. Si `ventas` tiene el mismo patrón —una
  validación propia que no usa el mecanismo de error de FastAPI—, aquí sería una
  **venta o un cargo que se da por registrado y no existe**. 7.0 debe buscarlo
  expresamente. **Buscarlo, no corregirlo.**
- Heredados y aceptados como pendientes: calibración de
  `DB_STATEMENT_TIMEOUT_MS` de la capa 1, ausencia de evidencia de GitHub
  Actions desde la capa 0, y la credencial privilegiada de la capa 4 **sin
  rotar**.

## Registro de ejecución

### 2026-08-20 — activación de la capa para `ventas`

- Modo de acceso: mismo checkout local; Git validado directamente en
  `C:\Users\David\Documents\sistema_escolar_api`, comprobado con
  `git rev-parse --show-toplevel`. No se usó GitHub para inferir el estado
  local.
- Autorización: orden explícita del usuario en este turno, nombrando el dominio
  `ventas` al elegirlo de la lista de los diez en espera. **No se pegó el bloque
  preparado** de `PROMPT_CONTINUACION.md`; la autorización llegó en
  conversación. La condición que ese bloque exige —nombrar el dominio
  explícitamente y no deducirlo— **se cumplió**.
- **Verificaciones heredadas**: se preguntó explícitamente al usuario, antes de
  escribir nada, si quería completarlas o continuar aceptándolas pendientes,
  ofreciendo también intentar cerrar la de CI. **Eligió continuar
  aceptándolas.** Quedan registradas con su riesgo y **ninguna se marca como
  cumplida**.
- Rama acordada: `main`.
- Estado antes de escribir: árbol limpio, verificado con
  `git status --porcelain=v1` con salida vacía; `HEAD` real
  `58c5233afc4772ba040da690f4d719b518bb1b0a`, comprobado y no recordado.
- Continuidad: el base de la capa 7 para `notas`,
  `eee8aec8725fc0bdd4a98fd2fd29cb88502c56e1`, existe y es ancestro de `HEAD`,
  verificado con `git merge-base --is-ancestor`. Sus **cuatro** commits
  posteriores forman una historia lineal y **todos están explicados** en
  `07_NOTAS.md`: la activación `a56d55f`, el cierre de 7.0 `a8bcf0a`, la
  extracción de 7.1 `ade4c10` y el cierre de la capa `58c5233`.
- **Matiz de continuidad, comprobado**: `07_NOTAS.md` enumera **tres** commits
  posteriores al base, no cuatro. El cuarto es su propio commit de cierre, que
  la bitácora no podía registrar sobre sí misma. Su contenido **sí está
  explicado** en el registro del 2026-08-19, que declara «archivos modificados
  en este turno: esta bitácora y `docs/modularizacion/README.md`», y se verificó
  con `git show --stat`: toca **exactamente esos dos archivos de
  documentación**, ningún código ni prueba. **No es una divergencia de
  producto.**
- Estado remoto **comprobado, no supuesto**: `origin/main` está en
  `58c5233afc4772ba040da690f4d719b518bb1b0a`, el mismo commit que `HEAD`,
  confirmado con `git rev-parse origin/main` y contra el remoto real con
  `git ls-remote origin main`. El reflog registra `update by push` de `58c5233`
  y, antes, de `eee8aec`. **No se consultó ni se atribuye ningún run de GitHub
  Actions**; esa evidencia sigue sin obtenerse desde la capa 0.
- **Residuo documental detectado y no corregido, más consecuente que el de la
  activación anterior**: `07_NOTAS.md` y el índice afirman en varios lugares que
  la capa 7 para `notas` **no está publicada**, que `origin/main` sigue en
  `eee8aec` y que su rollback es «una operación puramente local». **Ya no es
  cierto.** El push ocurrió el 2026-08-20; la referencia remota se escribió a
  las 14:03 y `ls-remote` lo confirma. **Producción corre el código de `notas`**
  y revertir a `eee8aec` exigiría otro push y otro despliegue. Las líneas
  fechadas del 2026-08-19 eran ciertas cuando se escribieron y **se conservan
  intactas**, conforme al criterio que la capa 4 fijó; lo que falta es la línea
  que registre el cambio de estado. Corregirlo es **ajeno a una activación** y
  cambia el perfil de rollback registrado de una capa cerrada, así que **queda
  anotado y no se toca**: exige una orden explícita del usuario. Es el mismo
  tipo de anotación que la activación de `notas` dejó sobre el índice, pero
  aquella describía una contradicción de prosa y esta describe **un hecho
  operativo distinto del documentado**.
- Archivos creados o modificados: esta bitácora y
  `docs/modularizacion/README.md`.
- Código de producto, pruebas, consultas, configuración, dependencias y workflow
  inspeccionados o modificados: **ninguno**. **No se inspeccionó código de
  `ventas`** ni de ningún otro dominio, ni siquiera el listado de nombres de
  archivo: la lista de dominios en espera se tomó de `07_NOTAS.md`.
- Pruebas, migraciones, conexiones a PostgreSQL, acceso a producción, commit,
  push y deploy: **ninguno**.
- Comandos de precondición: `git rev-parse --show-toplevel`,
  `git branch --show-current`, `git status --porcelain=v1`, `git rev-parse HEAD`,
  `git rev-parse origin/main`, `git ls-remote origin main`,
  `git merge-base --is-ancestor`, `git log --reverse --oneline` desde el base de
  `notas`, `git reflog show origin/main` y `git show --stat`; todos con
  resultado coherente con la activación.
- Estado al cerrar el turno de activación: capa 7 **activa** para el dominio
  `ventas`; 7.0 **pendiente y no iniciada**.
- Siguiente acción exacta: ejecutar únicamente 7.0 conforme al trabajo exacto de
  arriba y detenerse antes de 7.1. *(Ejecutada en el turno siguiente; ver el
  cierre de 7.0 más abajo.)*

### 2026-08-20 — cierre de 7.0

- Modo de acceso: mismo checkout local; Git validado directamente en
  `C:\Users\David\Documents\sistema_escolar_api`.
- Autorización: el usuario ordenó continuar. **Con capa activa esa orden sí
  autoriza**, porque el índice manda ejecutar la primera subcapa pendiente de la
  bitácora activa; lo que una instrucción genérica no autoriza es **activar** una
  capa cuando no hay ninguna, que era el caso del turno anterior.
- Precondición Git: rama `main`, **árbol limpio**, `HEAD`
  `040b027d01728a957d48963e0dd5ce1427e39c68`, el commit de activación que el
  usuario hizo entre turnos. El commit base `58c5233` existe y es ancestro, y el
  único commit posterior es esa activación, explicada en esta bitácora.
- **Compuerta heredada reproducida antes de tocar nada**:
  `.\venv\Scripts\python.exe scripts\verify.py` → **791 pruebas, exit 0**, Ruff
  correcto, `pip check` íntegro. Coincide exactamente con lo registrado al
  cerrar la capa 7 para `notas`, así que la línea base no tenía deriva.
- Archivos creados: `tests/test_ventas_caracterizacion.py`, **41 pruebas**.
  Archivos modificados: esta bitácora y `docs/modularizacion/README.md`.
  **Código de producto: ninguno.** `git status` mostró un solo archivo sin
  rastrear y **ningún archivo rastreado modificado**.
- Compuerta tras la caracterización: **832 pruebas, exit 0**, Ruff correcto,
  `pip check` íntegro. La suite pasó de **791 a 832**.
- `git diff --check`: **limpio**.
- **Dos aserciones se escribieron mal y se corrigieron antes de cerrar**, y las
  dos correcciones produjeron evidencia mejor que la hipótesis inicial:
  1. el bloque de `pagos_repository` se clasificó primero **por nombre**, lo que
     daba **seis** funciones y contradecía a la capa 5. Clasificado **por tabla**
     da **cinco**, exactamente las que 5.2 registró. La sexta,
     `asignar_venta_a_pago`, escribe `pagos`, y su docstring resultó ser la
     prueba documental del vínculo por texto;
  2. la colisión del `ILIKE` se planteó contra la descripción «Cargo de
     Inventario #N», que **no** contiene la subcadena buscada. Comprobado, la
     colisión real ocurre con «Abono a Cargo #N», y la otra forma revela un
     segundo defecto simétrico: el patrón **no reconoce** su propia otra
     descripción. Los hallazgos 2 y 3 salen de ahí.
- **El supuesto que resultó falso fue el 9**, el de los permisos, y era el único
  que la activación había marcado como **inferencia de patrón** en vez de como
  resto de una capa anterior. Marcarlo así fue lo que permitió refutarlo sin
  arrastrar la conclusión.
- Hallazgos: **once**, todos **registrados y sin corregir**.
- PostgreSQL, migraciones, producción, commit, push y deploy: **ninguno por
  parte del asistente**.
- Estado al cerrar el turno: capa 7 **activa** para `ventas`; **7.0 cerrada**;
  **7.1 pendiente y no iniciada**.
- Siguiente acción exacta: ejecutar únicamente **7.1** conforme a su trabajo
  exacto y detenerse antes de cualquier otra subcapa. **No se inició en este
  turno.** *(Ejecutada en el turno siguiente; ver el cierre de 7.1 más abajo.)*

### 2026-08-20 — cierre de 7.1

- Modo de acceso: mismo checkout local; Git validado directamente.
- Autorización: el usuario ordenó continuar. Con capa activa y 7.1 como primera
  subcapa pendiente, esa orden autoriza ejecutarla.
- Precondición Git: rama `main`, **árbol limpio**, `HEAD`
  `2fbe83f8900fc6a9d817441492b72556a1eb24a6`, el commit de 7.0 que el usuario
  hizo entre turnos. El commit base `58c5233` existe y es ancestro, y los **dos**
  commits posteriores están explicados aquí: la activación `040b027` y el cierre
  de 7.0 `2fbe83f`.
- Archivos modificados: `app/controllers/venta_controller.py`,
  `tests/test_ventas_caracterizacion.py`,
  `tests/test_dashboard_caracterizacion.py` y
  `tests/test_notas_caracterizacion.py`. Creado:
  `app/repositories/ventas_repository.py`. Más esta bitácora y
  `docs/modularizacion/README.md`. **Siete archivos**, ninguno fuera del
  alcance de la subcapa.
- **Comparador AST contra el commit base**: 17 literales SQL distintos antes y
  después, **conjunto idéntico**, **17 de 17 byte a byte**, y 17 puntos de
  llamada antes y después. Ningún cambio de texto SQL autorizado ni necesario.
- Compuerta global: `.\venv\Scripts\python.exe scripts\verify.py` → **835
  pruebas, exit 0**, Ruff correcto, `pip check` íntegro. La suite pasó de 832 a
  835: se retiraron las dos guardias de línea base y se añadieron cinco pruebas
  positivas.
- `git diff --check`: **limpio**, incluidos los tres literales con espacio final,
  que se escriben con escape `\x20`.
- **Seis pruebas fallaron al extraer y las seis eran previsibles**: dos guardias
  de línea base declaradas, **dos pruebas de hallazgo que también estaban
  ancladas al controlador sin estar rotuladas como guardias**, y las dos
  enumeraciones de repositorios de dashboard y notas. **Ninguna otra cambió de
  expectativa.**
- **Dos aserciones propias se escribieron mal y se corrigieron**, ninguna de
  producto: el recuento del ciclo de vida decía cinco aperturas y son **seis**
  —porque `eliminar_venta` también abre la suya—, y una comprobación de
  independencia respecto de `pagos_repository` estaba escrita de forma tan
  gruesa que la prosa del propio comentario la hacía fallar.
- Hallazgos: **ninguno nuevo**. Los once de 7.0 siguen vivos y **ninguno se
  corrigió**.
- PostgreSQL, migraciones, producción, commit, push y deploy: **ninguno por
  parte del asistente**.
- Estado al cerrar el turno: capa 7 **activa** para `ventas`; **7.0 y 7.1
  cerradas**; **punto de decisión abierto** con tres salidas.
- Siguiente acción exacta: **esperar una decisión explícita del usuario** sobre
  el punto de decisión. Ninguna de sus tres opciones se inicia por inferencia.

### 2026-08-20 — verificación manual registrada

- Modo de acceso: mismo checkout local; Git validado directamente.
- **Artefacto confirmado antes de registrar la verificación**, conforme a la
  lección 10 de la capa 5 y **sin ambigüedad**: rama `main`, árbol **limpio**,
  `HEAD` `8948e409075115d1bf5f4ee1a1769396fbeaa029`. Los **cuatro** commits
  posteriores al base están explicados en esta bitácora: la activación
  `040b027`, el cierre de 7.0 `2fbe83f`, la extracción de 7.1 `76f76e7` y la
  documentación del guion `8948e40`.
- **Verificación manual**: el usuario informó el 2026-08-20 haberla ejecutado
  con resultado correcto. **Lo reportó de forma global** —«ya verifiqué y se ve
  bien por ahora»— **y no punto por punto contra los once pasos del guion**. Se
  registra así, sin inflarla: **no consta** qué pasos se recorrieron, y en
  concreto no consta el retorno exacto del stock tras una anulación con abono
  parcial, la prueba cruzada de importes contra el expediente y la cartera, ni
  el aislamiento entre los dos tenants. Es evidencia **más débil** que la de
  `notas`, cuya bitácora sí pudo afirmar que la respuesta se dio sobre un guion
  explícito.
- **Estado de publicación comprobado, no supuesto**: `origin/main` está en
  `58c5233`, el commit base. Hay **cuatro commits locales sin publicar** y
  **producción no corre este código**. Mientras siga así, el rollback es una
  operación **puramente local**. No se consulta ni se atribuye ningún run de
  GitHub Actions.
- Archivos modificados en este turno: esta bitácora. **Código de producto y
  pruebas: ninguno.**
- Estado: capa 7 **activa** para `ventas`, con **7.0 y 7.1 cerradas** y la
  verificación manual registrada con su limitación. **La capa no está cerrada**:
  falta resolver el punto de decisión.
- Siguiente acción exacta: **esperar la decisión del usuario** entre las tres
  salidas del punto de decisión. Una instrucción genérica de continuar no la
  sustituye. *(Tomada en el mismo turno; ver el cierre más abajo.)*

### 2026-08-20 — cierre de la capa 7 para `ventas`

Con la verificación manual registrada y el punto de decisión resuelto, la capa
queda cerrada.

- Modo de acceso: mismo checkout local; Git validado directamente.
- **Decisión del usuario, explícita**: cerrar la capa aquí, sin abrir 7.2. Se le
  ofrecieron **cuatro** salidas —cerrar, una 7.2 con los errores de dominio, una
  7.2 que moviera el `UPDATE pagos`, o completar antes los tres pasos del guion
  que no constan— y eligió cerrar. La capa queda siendo una refactorización
  pura, como la 5, la 6 y las dos capas 7 anteriores.
- Precondición Git: rama `main`, `HEAD`
  `8948e409075115d1bf5f4ee1a1769396fbeaa029`. El commit base `58c5233` existe y
  es ancestro, y los **cuatro** commits posteriores están explicados aquí: la
  activación `040b027`, el cierre de 7.0 `2fbe83f`, la extracción de 7.1
  `76f76e7` y la documentación del guion `8948e40`.
- **Compuerta global de cierre**: `.\venv\Scripts\python.exe scripts\verify.py`;
  **835 pruebas pasaron**, 5 warnings heredadas, Ruff correcto, `pip check`
  íntegro y exit 0. La suite pasó de 791 al activar la capa a 835.
- `git diff --check`: **limpio**.
- **Estado de publicación comprobado, no supuesto**: `origin/main` está en
  `58c5233`, el commit base. **Producción no corre este código** y el rollback
  sigue siendo **puramente local**. El reflog remoto no registra ningún push
  posterior a `58c5233`. **No se consultó ni se atribuye ningún run de GitHub
  Actions.**
- **Lo que el cierre NO marca como cumplido**: los tres pasos del guion que no
  constan, y las verificaciones heredadas de las capas 0 y 1. Ninguno cambia de
  estado por cerrar la capa.
- Archivos modificados en este turno: esta bitácora y
  `docs/modularizacion/README.md`. **Código de producto y pruebas: ninguno.**
- **Dos residuos del índice corregidos al cerrar, y se registran.** Primero, un
  recuento propio: se había escrito «los ocho dominios restantes» y son
  **nueve** —`boletin`, `asistencia`, `observaciones`, `planilla`,
  `planeador_anual`, `plan_de_clases`, `branding`, `profesores` y
  `super_admin`—. Segundo, un residuo **anterior a esta capa**: las entradas de
  continuidad de las capas 5 y 6 seguían declarándose «el documento que un chat
  nuevo debe leer después de este índice», de modo que **tres documentos lo
  afirmaban a la vez**. Se marcaron como fuentes de continuidad superadas, sin
  tocar el resto de su texto ni sus bitácoras. Corregirlo entra en el criterio
  de cierre «el índice maestro queda actualizado», y sin ello el índice quedaba
  ambiguo sobre qué leer.
- PostgreSQL, migraciones, producción, commit, push y deploy: **ninguno por
  parte del asistente**, ni en este turno ni en toda la capa.
- Estado: **capa 7 cerrada para el dominio `ventas`**. Los **nueve** dominios
  restantes de la capa 7 quedan **en espera** y **ninguno fue activado**.
- Siguiente acción exacta: esperar una orden explícita del usuario. Una
  instrucción genérica de continuar no autoriza activar otro dominio. Queda
  además **pendiente la publicación**, que decide y ejecuta el usuario.

## Entrega al próximo chat

- Capa activa: **ninguna.** La capa 7 quedó **cerrada para `ventas`** el
  2026-08-20, el mismo día en que se activó.
- Última subcapa terminada: **7.1**, cerrada el 2026-08-20. Con ella la frontera
  de persistencia del dominio quedó cerrada.
- **Capa cerrada** el 2026-08-20. No quedan bloqueos.
- Primera subcapa pendiente: **ninguna.** El usuario decidió **cerrar la capa
  aquí**, sin abrir 7.2: el `UPDATE pagos` se queda en `ventas_repository`, y
  `response_model` y los errores de dominio **no se añaden**. Los tres pasan a
  ser trabajo disponible que exigiría una orden explícita.
- **Verificación manual: hecha** el 2026-08-20, en local y con resultado
  correcto, pero **reportada de forma global y no contra los once pasos del
  guion**. No consta el retorno del stock tras anular con abono parcial, la
  prueba cruzada de importes ni el aislamiento entre tenants. El guion íntegro
  se conserva por si se quiere cerrar ese hueco.
- Commit base: `58c5233afc4772ba040da690f4d719b518bb1b0a`, rama `main`,
  **publicado y desplegado**, comprobado contra el remoto real.
- Bloqueos: ninguno. Verificaciones heredadas **pendientes y aceptadas** por
  decisión explícita del usuario: valor operativo final de
  `DB_STATEMENT_TIMEOUT_MS` (capa 1) y evidencia de GitHub Actions posterior a
  la capa 0. La credencial privilegiada de la capa 4 sigue **sin rotar**.
- Compuerta al cerrar 7.1: **835 pruebas, exit 0**, Ruff correcto y `pip check`
  íntegro. La suite pasó de **791 al activar la capa a 835**.
- Lo que consiguió 7.1: `venta_controller.py` pasó de **363 a 278 líneas** y de
  **17 sentencias SQL inline a 0**; la persistencia vive en
  `app/repositories/ventas_repository.py`, **17 funciones** que reciben el
  cursor y **el octavo repositorio** del proyecto. Comparador AST contra el
  commit base: **conjunto de SQL idéntico, 17 de 17 literales byte a byte**, sin
  una sola autorización de cambio de texto. **Ninguna prueba cambió de
  expectativa** salvo las seis que debían fallar.
- **Decisión de 7.1 que sigue abierta a revisión**: el `UPDATE pagos` vive en
  `ventas_repository`, por simetría con el bloque que la capa 5 dejó en
  `pagos_repository`. Moverlo allí es la alternativa descartada y **exigiría
  orden explícita**, porque toca un módulo cerrado.
- Lo que 7.0 dejó medido: el dominio son **dos archivos**; **5 entradas HTTP**
  con **un solo modelo de permiso**, admin estricto; **cuatro tablas escritas**
  —`ventas`, `ventas_detalle`, `inventario` y **`pagos`**—; **dos transacciones
  propias**; **17 sentencias SQL inline**, todas en el controlador y 0 en la
  ruta; **41 pruebas de caracterización** nuevas y los conteos de cinco caminos.
  **Todos los caminos abren una sola conexión** y **no hay N+1**.
- **Los doce supuestos quedaron resueltos**: once confirmados y **uno refutado**,
  el de los permisos. Es el primer dominio del programa con permisos uniformes.
- **El contrato HTTP de las tres respuestas de escritura está fijado con status
  codes reales**, medidos por ASGI: 200 al crear, 400 ante validación fallida,
  405 en el borrado y 422 ante payload inválido.
- Lo que hay que recordar antes de tocar nada:
  1. **Un solo dominio.** `dashboard` y `notas` ya están cerrados en sus propias
     bitácoras y los otros nueve siguen en espera.
  2. **Es el dominio financiero.** Los contratos de la capa 4 y la frontera de
     pagos de la capa 5 rodean este código. Un error aquí es dinero, no una
     cifra rara.
  3. **La frontera ajena existe en los dos sentidos.** Cinco funciones de
     `pagos_repository` tocan `ventas` —**no se mueven en 7.1**— y `anular_venta`
     **escribe `pagos`** con SQL inline. Dónde vive ese `UPDATE pagos` es la
     decisión difícil de 7.1, y llevarlo a `pagos_repository` **amplía el diff a
     un módulo cerrado y exige orden explícita**.
  4. **No fiarse de los nombres.** Aquí falló dos veces en un mismo turno:
     clasificar las funciones de `pagos_repository` por su nombre daba seis en
     vez de cinco, y el patrón `ILIKE` no casa con la descripción que su propio
     dominio fabrica.
  5. **Romper un contrato ajeno no haría fallar las pruebas de `ventas`**, solo
     la compuerta global. Ejecutarla siempre completa: al aparecer el octavo
     repositorio, la guardia de `test_dashboard_caracterizacion.py` **volverá a
     fallar**, igual que con el séptimo.
  6. **No corregir ninguno de los once hallazgos**, ni los veintidós que
     dashboard y notas dejaron abiertos.
  7. **El patrón del falso éxito de `POST /notas` no está aquí**, se buscó
     expresamente: esta escritura responde 400 y su `id` es un entero plano.
  8. **Una prueba de hallazgo anclada a un archivo concreto es también una
     guardia de línea base**, aunque no se rotule así. 7.1 lo aprendió: preveía
     dos fallos dentro del dominio y fueron cuatro.
- **Lo más grave que 7.0 encontró**: anular una venta alcanza los pagos por
  `descripcion ILIKE '%Cargo #N%'`, sin delimitar el número, así que **anular la
  venta 4 marca como anulados los pagos de la venta 40**. Es dinero, está activo
  en producción y es **anterior a esta capa**. No se corrige desde aquí.
- **Residuo documental abierto**: `07_NOTAS.md` describe la capa de `notas` como
  no publicada, y **sí lo está** desde el 2026-08-20. El índice ya lo registra;
  la bitácora cerrada no se editó. Corregirla exige una orden explícita.
- **Pendiente la publicación.** Los commits siguen en local; `origin/main` está
  en el commit base. Publicar dispara el despliegue, así que es decisión y
  acción del usuario.
- Siguiente acción exacta: **esperar una orden explícita del usuario**. La capa
  7 sigue teniendo dominios en espera —`boletin`, `asistencia`,
  `observaciones`, `planilla`, `planeador_anual`, `plan_de_clases`, `branding`,
  `profesores` y `super_admin`— y **ninguno se activa sin orden**. Una
  instrucción genérica de continuar no la autoriza.
