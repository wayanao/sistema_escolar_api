# Capa 7: ventas

Última revisión: 2026-08-20.

## Control

- Estado: **Activa** desde el 2026-08-20.
- Commit base: `58c5233afc4772ba040da690f4d719b518bb1b0a`.
- Rama acordada: `main`.
- Primera subcapa pendiente: **7.0**, no iniciada.
- Código de producto modificado al activar: **ninguno**.
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

Ninguno de los de abajo procede de haber leído el código de `ventas`. Todos son
restos de lo que las capas 3, 4, 5 y 6 observaron desde fuera, **más una
inferencia de patrón marcada como tal**.

| # | Supuesto | Estado | Origen |
|---:|---|---|---|
| 1 | El dominio vive en `app/routes/` y `app/controllers/venta_controller.py` | **No verificado.** La lección de `notas` es que el recuento de archivos por su nombre **falla**: allí faltaba `app/services/nota_service.py` con un tercio de la persistencia. 7.0 debe buscar servicios, esquemas y utilidades, no solo ruta y controlador | Decisión de 5.2 |
| 2 | **`venta_controller.py` tiene SQL inline propio** | **No verificado.** Es una afirmación de la capa 5, cierta entonces; ninguna capa posterior lo ha tocado, pero no se ha vuelto a comprobar | Decisión de 5.2 |
| 3 | **No tiene repositorio propio** | **No verificado.** El programa lleva **siete** repositorios tras 7.1 de notas —asignaciones, dashboard, estudiantes, notas, pagos, plan de clases y reportes— y ninguno es de ventas. Fijarlo por prueba, como hizo 7.0 de notas | Decisiones de 5.2 y 7.1 de notas |
| 4 | **`pagos_repository` contiene cinco sentencias que tocan `ventas`** | **No verificado.** Es el supuesto que sostiene el punto de decisión de esta capa. 7.0 debe contarlas y clasificarlas una a una: cuáles son el efecto de un pago sobre un cargo y cuáles, si alguna, son persistencia general de ventas | Resultado de 5.2 |
| 5 | **La tabla `ventas` se escribe** | **No verificado como propiedad del dominio.** 5.0 la contó entre las seis tablas escritas del dominio de **pagos**. 7.0 debe determinar si `ventas` **también** la escribe desde sus propias entradas, y si hay `UPDATE` o `DELETE`, que `notas` no tenía | Resultado de 5.0 |
| 6 | **`estudiantes_repository` lee `ventas`** | **No verificado.** 6.2 movió al expediente cuatro lecturas y una era de `ventas`. Es un consumidor ya migrado: romper su contrato **no haría fallar las pruebas de ventas**, solo la compuerta global. Es la misma trampa que 7.1 de notas pisó con una guardia de dashboard | Resultado de 6.2 |
| 7 | **Existe un «cargo de inventario»** que cuesta 4 consultas y sale antes que el pago simple | **No verificado.** 5.0 lo midió desde el lado de pagos. Sugiere que `ventas` participa en el camino de cobro, pero no dice qué parte le pertenece | Resultado de 5.0 |
| 8 | **No escribe archivos** | **No verificado.** 6.0 estableció que solo `branding` y `plan de clases` usan `app/services/storage.py`. Si se confirma, el rollback no necesita cubrir archivos. **Es exactamente el supuesto que la capa 6 se activó creyendo al revés**, así que se comprueba, no se hereda | Resultado de 6.0 |
| 9 | **Los permisos no son uniformes** | **No verificado.** Inferencia de patrón, marcada como tal: dashboard usó cuatro modelos en siete entradas y notas dos en cinco. Ninguna de las tres capas de dominio encontró permisos uniformes | Inferencia |
| 10 | **Otros dominios en espera leen sus tablas** | **No verificado.** `notas_detalle` resultó ser la tabla más compartida del programa, con siete módulos lectores. 7.0 debe hacer el mismo recuento para `ventas` antes de mover nada | Resultado de 7.0 de notas |
| 11 | **`ventas` no estuvo entre las ocho tablas averiadas de la capa 3** | **Verificado documentalmente**, no por inspección: la lista de las ocho está cerrada en `03_MIGRACIONES_TENANTS.md` y en el índice, y `ventas` no figura. Es el único de esta tabla que no exige comprobación en código | Resultado de 3.4a |
| 12 | **La cifra es el contrato** | **No verificado para este dominio.** El sistema lleva **cuatro fórmulas de promedio** distintas. En un dominio financiero el riesgo equivalente son **importes, saldos y redondeos de dinero**, donde un decimal cambia lo que el usuario paga | Riesgo propio de la capa 7 y resultado de 7.0 de notas |

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

## Línea base

| Comprobación | Comando | Resultado |
|---|---|---|
| Pruebas específicas | Por determinar en 7.0 | **Pendiente** |
| Suite global | `.\venv\Scripts\python.exe scripts\verify.py` | **Pendiente.** Último valor registrado al cerrar la capa 7 para `notas`: **791 pruebas, exit 0** |
| Ruff | Ejecutado por la compuerta global | **Pendiente** |
| Dependencias | Ejecutado por la compuerta global | **Pendiente** |

La compuerta heredada **debe reproducirse antes de tocar nada**, como hicieron
las dos capas 7 anteriores. Si no da 791, hay que explicar la diferencia antes
de continuar.

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 7.0 | Inventario, contratos, caracterización y línea base de consultas y conexiones | **Pendiente**, no iniciada |
| 7.1 | Primera extracción protegida | **Sin definir**: depende de la evidencia de 7.0 |
| 7.2 | Segunda extracción, punto de decisión o cierre | **Sin definir** |

El desglose se deja deliberadamente sin decidir hasta tener la evidencia del
inventario, igual que hicieron la capa 6 y las dos capas 7. Las subcapas
innecesarias se marcarán `No aplica` con explicación. **Nunca se ejecutan dos
subcapas en el mismo turno.**

## Subcapa activa: 7.0, trabajo exacto

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
  arriba y detenerse antes de 7.1.

## Entrega al próximo chat

- Capa activa: **7, para el dominio `ventas` y solo ese.** Activada el
  2026-08-20.
- Última subcapa terminada: **ninguna** en esta bitácora. La anterior del
  programa es 7.1 de `notas`, cerrada el 2026-08-19 en `07_NOTAS.md`.
- Primera subcapa pendiente: **7.0**, no iniciada. Su trabajo exacto está
  arriba, en doce puntos.
- Commit base: `58c5233afc4772ba040da690f4d719b518bb1b0a`, rama `main`,
  **publicado y desplegado**, comprobado contra el remoto real.
- Bloqueos: ninguno. Verificaciones heredadas **pendientes y aceptadas** por
  decisión explícita del usuario: valor operativo final de
  `DB_STATEMENT_TIMEOUT_MS` (capa 1) y evidencia de GitHub Actions posterior a
  la capa 0. La credencial privilegiada de la capa 4 sigue **sin rotar**.
- Compuerta heredada a reproducir antes de tocar nada: **791 pruebas, exit 0**,
  Ruff correcto y `pip check` íntegro.
- Lo que hay que recordar antes de tocar nada:
  1. **Un solo dominio.** `dashboard` y `notas` ya están cerrados en sus propias
     bitácoras y los otros ocho siguen en espera.
  2. **Es el dominio financiero.** Los contratos de la capa 4 y la frontera de
     pagos de la capa 5 rodean este código. Un error aquí es dinero, no una
     cifra rara.
  3. **La frontera ajena ya existe**: cinco sentencias sobre `ventas` viven en
     `pagos_repository` y al menos una lectura en `estudiantes_repository`.
     **Leerlas sí, moverlas no**, sin una orden explícita posterior a la
     evidencia de 7.0.
  4. **No fiarse de los nombres de archivo.** Es la lección que `notas` pagó:
     allí faltaba un servicio con un tercio de la persistencia.
  5. **Romper un contrato ajeno no haría fallar las pruebas de `ventas`**, solo
     la compuerta global. Ejecutarla siempre completa.
  6. **No corregir ningún hallazgo**, ni los que 7.0 encuentre ni los veintidós
     que dashboard y notas dejaron abiertos.
  7. **Buscar expresamente el patrón del falso éxito** de `POST /notas` en las
     escrituras de este dominio. Buscarlo, no corregirlo.
- **Residuo documental abierto**: `07_NOTAS.md` y el índice describen la capa de
  `notas` como no publicada, y **sí lo está** desde el 2026-08-20. Corregirlo
  exige una orden explícita del usuario y no se hizo aquí.
- Siguiente acción exacta: **ejecutar únicamente 7.0** y detenerse antes de 7.1.
