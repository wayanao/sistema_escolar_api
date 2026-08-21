# Capa 7: boletin

Última revisión: 2026-08-21.

## Control

- Estado: **Activa** desde el 2026-08-21.
- Commit base: `8e61170f32a6d6a23ca23f9ead89d17bc209e7b6`.
- Rama acordada: `main`.
- Primera subcapa pendiente: **7.0**, pendiente y **no iniciada**.
- Código de producto modificado al activar: **Ninguno**.
- Dominio de esta capa: **boletin, y solo ese**. La capa 7 del índice es «resto
  de dominios» y ordena expresamente **priorizar uno a la vez**, así que esta
  bitácora cubre un único dominio. Los demás quedan fuera y necesitarán su
  propia bitácora y su propia orden.
- Autorización: orden explícita del usuario el 2026-08-21. **El dominio lo
  nombró el usuario**, eligiéndolo de la lista de los ocho que quedaban en
  espera y **después de recibir en ese mismo turno la advertencia de que
  `boletin` no es una frontera limpia**. No se dedujo por inferencia.
- La autorización permite **solamente la activación documental**. No autoriza
  inspeccionar código del dominio, implementar 7.0, tocar la base de datos,
  hacer deploy, commit ni push.

### Relación con las bitácoras de `dashboard`, `notas`, `ventas` y `asistencia`

`07_DASHBOARD.md`, `07_NOTAS.md`, `07_VENTAS.md` y `07_ASISTENCIA.md` son las
bitácoras **cerradas** de los cuatro primeros dominios migrados bajo la capa 7.
Esta es la quinta, y es **independiente**: su commit base, sus subcapas, su
compuerta y su cierre son propios. Cerrar `boletin` no reabre ninguna de las
cuatro, ni al revés.

**Las subcapas se numeran por bitácora**, así que esta capa vuelve a empezar en
**7.0**. Existen por tanto una «7.0 de dashboard», una «7.0 de notas», una «7.0
de ventas» y una «7.0 de asistencia», las cuatro cerradas, y una «7.0 de
boletin», que es la pendiente. En prosa deben citarse siempre con el nombre del
dominio; el número solo no identifica una subcapa.

**`07_NOTAS.md` tiene aquí un peso que ninguna bitácora cerrada tuvo antes.** No
es solo un antecedente: **contiene parte de este dominio**. Su 7.0 fijó que
`notas` posee rutas de boletín, y su 7.1 cerró la frontera de persistencia de
esas rutas. Leerla no es opcional para 7.0, y **modificar lo que quedó dentro de
`notas` no está autorizado por esta activación**.

## Objetivo

Migrar el dominio de **boletin** con contratos y pruebas, conservando su
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

## Por qué este dominio es distinto de los cuatro anteriores

**Su frontera está partida, y se sabe antes de empezar.** Es la diferencia que
manda. `dashboard`, `notas`, `ventas` y `asistencia` se activaron sin saber
dónde terminaba el dominio; aquí el programa ya tiene registrado que **no
coincide con los nombres de archivo**:

- existe `app/routes/boletines.py`, inventariado por la capa 0;
- pero **`notas` posee `/boletin/{id}` y `/boletin/detallado/{id}`**, y sus
  controladores `boletin_estudiante_controller` y `boletin_detallado_controller`
  viven dentro de `notas_controller.py`, migrado y cerrado por la 7.1 de
  `notas`;
- **no hay colisión de paths**, comprobado por la 7.0 de `notas`, que listó las
  rutas de `boletines.py` justamente para descartarla.

La 7.0 de `notas` dejó escrito el aviso literal: «quien migre boletín o planilla
debe saber que **tres de sus rutas ya viven aquí**».

**Consecuencia práctica para 7.0**: el primer trabajo de esta subcapa no es
inventariar, es **decidir dónde está el borde** y registrarlo con evidencia. Las
rutas que ya viven en `notas` **están cerradas y no se mueven** sin una orden
explícita posterior a esa evidencia.

Otras dos diferencias, menores pero registradas:

- **Es el primer dominio de la capa 7 cuyo commit base ya está publicado y
  desplegado al activar.** `notas`, `ventas` y `asistencia` se activaron sobre
  bases que en algún momento estuvieron sin publicar. Aquí producción **ya
  corre** el código del commit base, así que un rollback de esta capa, si
  llegara a publicarse, **no sería local**.
- **Es el dominio con menos datos reales que ha tocado el programa.** La capa 3
  midió `tenant_2005`: `boletin_cabecera` tiene **3 filas** y `boletin_detalles`
  **4**. Eso hace la verificación manual más barata y, a la vez, **más pobre**:
  un error de agrupación o de promedio puede no manifestarse con cuatro filas.

## Perfil de riesgo esperado, **no verificado**

La capa 0 registró que las entradas bajo `/boletines` **guardan definitivas**.
Si 7.0 lo confirma, **el dominio escribe** y su perfil de riesgo es el de la
capa 5, como `notas`, `ventas` y `asistencia`. La activación **no lo da por
cierto**: es el supuesto 2 de la tabla de abajo.

Lo que sí está fijado y **no** es un supuesto de este dominio: el historial
académico **no se recalcula**. La capa 6 lo registró al tratar la desactivación
de asignaciones —«notas, asistencia y boletines son fotos del pasado»—, y esa
propiedad es un invariante que esta capa no puede alterar.

## Dependencias de capas anteriores

- **Capa 0**: el inventario de contratos incluye la fila «Boletines», con su
  router y su prueba. Es el punto de partida documental de 7.0.
- **Capa 1**: migró a `get_cursor()` los cinco sitios de `notas_controller.py`,
  dos de ellos de boletín, y **fijó por prueba** el N+1 de
  `boletin_detallado_controller`. Sus doce comprobaciones de caracterización
  siguen vivas.
- **Capa 3**: reparó `boletin_cabecera` y `boletin_detalles` en `tenant_2005`;
  las dos estaban entre las ocho tablas que no admitían inserciones.
- **Capa 4**: midió un camino de boletín de 13 materias en **4 consultas**.
- **Capa 6**: `boletin_controller` es uno de los nueve consumidores de
  `resolver_asignacion_academica_id_cursor`; las rutas `orden-boletin`
  pertenecen a `asignaciones`, ya migrado.
- **Capa 7 en `notas`**: cerró la persistencia de las rutas de boletín que
  `notas` posee y dejó el aviso de frontera partida.
- Evidencia de que la capa anterior está cerrada: `07_ASISTENCIA.md` marca
  Estado **Cerrada** el 2026-08-21, con compuerta **exit 0 y 872 pruebas** y
  verificación manual ejecutada; el índice lo confirma y no marca ninguna otra
  capa activa.

## Lo que el programa cree saber de `boletin`, y que 7.0 debe verificar

Aplica la lección 12 que dejó la capa 6 y que las cuatro capas 7 confirmaron:
**un supuesto heredado se marca como no verificado y se comprueba en la subcapa
0**. De los siete supuestos de `dashboard` **uno resultó falso**; de los diez de
`notas` **uno resultó incompleto**, y era el que fijaba la frontera del dominio;
de los doce de `ventas` **uno resultó falso**; de los doce de `asistencia`
**dos resultaron incompletos y ninguno falso**.

Ninguno de los de abajo procede de haber leído el código de `boletin`. Todos son
restos de lo que las capas 0, 1, 3, 4, 6 y 7 observaron desde fuera. La columna
de origen dice de dónde sale cada uno, para que 7.0 pueda contrastarlo.

**Los trece están NO VERIFICADOS.**

| # | Supuesto | Origen documental | Estado |
|---:|---|---|---|
| 1 | El dominio vive en `app/routes/boletines.py` y en un `boletin_controller` | Inventario de contratos de 0.0 y subcapa 6.0, que nombra `boletin_controller` entre los nueve consumidores del resolver | **NO VERIFICADO.** No consta la ruta exacta del controlador ni si existe esquema o servicio propio. Los cuatro dominios anteriores fallaron aquí dos veces |
| 2 | **El dominio escribe**: guarda notas definitivas | Inventario de contratos de 0.0: «guarda definitivas o consulta respaldo/planilla vigente» | **NO VERIFICADO.** Si se confirma, el perfil de riesgo es el de la capa 5 y la propiedad transaccional pasa a ser la invariante más delicada |
| 3 | **La frontera está partida**: `notas` posee `/boletin/{id}` y `/boletin/detallado/{id}` | Subcapa 7.0 de `notas`, supuesto 6, «confirmado y más fuerte de lo previsto» | **NO VERIFICADO en su alcance actual.** Lo confirmado es que esas rutas eran de `notas` en su 7.0. 7.0 debe re-comprobarlo sobre el código de hoy y **decidir el borde con evidencia** |
| 4 | **No hay colisión de paths** entre `boletines.py` y las rutas de boletín de `notas` | Subcapa 7.0 de `notas`, que listó las rutas de `boletines.py` para descartarla | **NO VERIFICADO hoy.** Se comprobó entonces; los métodos y las formas de path difieren |
| 5 | `boletin_estudiante_controller` y `boletin_detallado_controller` viven en `notas_controller.py` y usan `get_cursor()` | Subcapa 1.4, tabla de los cinco sitios | **NO VERIFICADO tras la 7.1 de `notas`**, que movió persistencia a `notas_repository`. El idioma de conexión pudo cambiar |
| 6 | **Hay N+1**: `boletin_detallado_controller` ejecuta una consulta por asignación | Subcapa 1.4, fijado por prueba: dos asignaciones producen tres `execute` | **NO VERIFICADO tras la 7.1 de `notas`.** Sería el tercer N+1 vivo del programa, tras el de la capa 4 y el de `asistencia` |
| 7 | Un camino de boletín de **13 materias cuesta 4 consultas** | Medición de 4.0 sobre producción | **NO VERIFICADO, y aparentemente en tensión con el supuesto 6.** 7.0 debe determinar **qué camino se midió**: 4 consultas no es un N+1 de 13 materias. Puede que se midiera `/boletin/{id}`, el del CTE, y no el detallado |
| 8 | **Los ids de las actividades en blanco son sintéticos** y pueden colisionar con ids reales de `notas_detalle`: materia 5 produce 501, 502 y 503 | Subcapa 1.4, anotado como deuda conocida no corregida | **NO VERIFICADO.** Es deuda registrada, **no se corrige desde esta capa** salvo orden explícita |
| 9 | **El corte Aprobado/Reprobado está en 3,0 inclusive**; el promedio general no tiene guarda de división por cero, inalcanzable por un `return` previo | Subcapa 1.4 | **NO VERIFICADO** |
| 10 | **El promedio general del boletín promedia valores sin redondear**, aunque muestre los redondeados: 3,0/4,0/4,0 → **3,67**, donde `TRUNC` daría 3,66. Y el boletín detallado devuelve **`promedio: 0` fijo**, con el comentario «El frontend recalcula luego» | Subcapa 7.0 de `notas`, supuestos 7 y hallazgos | **NO VERIFICADO.** Si se confirma, **parte del cálculo vive en el cliente**, y eso condiciona qué puede comprobar una prueba de servidor |
| 11 | `boletin_controller` **lee `notas_detalle`**, una de las siete lecturas de la tabla más compartida del programa | Subcapa 7.0 de `notas`, supuesto 5 | **NO VERIFICADO.** Relevante: `notas_detalle` ya tiene dueño migrado y cerrado |
| 12 | Las tablas son `boletin_cabecera` y `boletin_detalles`, con **3 y 4 filas** en `tenant_2005`, `boletin_cabecera → estudiantes`, `boletin_detalles → boletin_cabecera` **con cascada**, y ambas estuvieron entre las **ocho averiadas** que reparó la capa 3 | Capas 3 y 6 | **Confirmado documentalmente**, sin cambio. Relevante si el supuesto 2 se confirma: **borrar una cabecera se lleva sus detalles** |
| 13 | `require_estudiante_in_asignacion` tiene **un punto de llamada en `boletines`**, y **no está en un bucle** | Medición del N+1 en conexiones de `asistencia`, registrada en el índice el 2026-08-21 | **NO VERIFICADO.** Importa por partida doble: fija un modelo de permiso y dice que aquí **no** se repite el N+1 en conexiones de `asistencia` |

## Alcance autorizado

- **Determinar y registrar con evidencia dónde está la frontera del dominio**,
  antes que ningún otro trabajo. Es el primer paso de 7.0 y condiciona el resto.
- Inventariar entradas HTTP, reglas, cálculos, consultas, escrituras, archivos,
  pruebas y consumidores **de boletin** mediante búsquedas dirigidas.
- Caracterizar antes de extraer: rutas, métodos, payloads, status codes,
  permisos, roles, tenant, ownership, orden, nulos, **promedios, redondeos,
  cortes de aprobación e ids sintéticos**, transacciones y errores.
- Separar progresivamente HTTP, reglas, servicios y persistencia siguiendo el
  patrón ya probado siete veces, con pruebas de caracterización previas a cada
  extracción importante.
- Contar y comparar consultas **y conexiones** críticas antes y después. Las
  cuatro capas 7 anteriores demostraron que medir solo consultas esconde el
  coste real.
- **Leer** `notas_controller.py`, `notas_repository.py` y `app/routes/notas.py`
  lo indispensable para delimitar la frontera y documentar el punto de decisión.
  **Leer no es mover**: modificarlos exige una orden explícita posterior a la
  evidencia de 7.0.
- Agregar `response_model`, errores de dominio y pruebas HTTP o de integración
  **solo después** de caracterizar y demostrando que la respuesta existente se
  conserva.
- Medir con `EXPLAIN ANALYZE` conforme al criterio corregido en la capa 4:
  `SELECT` en producción bajo transacción `READ ONLY` cerrada con `rollback`.
  Ninguna medición puede escribir.

## Fuera de alcance

- **Todos los demás dominios de la capa 7**: observaciones, planilla, planeador
  anual, plan de clases, branding, profesores, super admin y cualquier otro.
  Esta capa es de un solo dominio. Se permite la lectura mínima indispensable
  para caracterizar un contrato que `boletin` consuma o que consuma de
  `boletin`, sin modificarlo. **`planilla` queda fuera aunque comparta el mismo
  tipo de frontera partida.**
- **`pagos`, `estudiantes`, `asignaciones`, `dashboard`, `notas`, `ventas` y
  `asistencia`, ya migrados.** Sus fronteras de persistencia están cerradas y
  sus pruebas de caracterización deben seguir pasando. **Mover cualquier
  sentencia fuera de `notas_repository` no está autorizado por esta
  activación**, por mucho que la sentencia sea de boletín.
- `app/services/asignacion_academica.py`, del que dependen nueve módulos: se lee
  si hace falta, **no se toca**.
- `app/core/permissions.py`. Es infraestructura compartida que las seis capas
  anteriores declararon expresamente fuera de alcance. **Incluye el N+1 en
  conexiones que dejó `asistencia`**, con plan de corrección ya diseñado y
  aplazado: exige bitácora propia y orden explícita.
- Los hallazgos abiertos de las capas 5, 6 y 7. En particular el **paso 2 de la
  clave de idempotencia** de `POST /pagos`, la **ausencia de lock en el alta y
  la edición de asignaciones**, los **diez hallazgos de dashboard**, los **doce
  de notas**, los **once de ventas** y los **ocho de asistencia**. **No entran
  por inferencia**, por cerca que queden del código que esta capa toque.
- **Los ids sintéticos del boletín detallado y su N+1** son deuda registrada por
  la capa 1 y **no se corrigen aquí** salvo decisión explícita con evidencia.
- El trabajo registrado en `PROMPT_CONTINUACION.md` bajo «trabajo fuera del
  alcance de cualquier capa activa».
- Cambiar rutas, payloads, status codes, permisos, roles, ownership, reglas de
  cálculo, **promedios, redondeos o cortes de aprobación**, orden o semántica
  transaccional.
- Cambiar PostgreSQL, `psycopg2`, el modelo de schemas tenant, el pool, los
  timeouts, el limitador de concurrencia, el ORM, el driver o el almacenamiento
  de archivos.
- Migraciones reales, DDL, DML, deploy, commit o push.

## Invariantes

- Métodos, paths, status codes y forma exacta de las respuestas permanecen
  idénticos, incluidos el **orden**, los **nulos** y la **agrupación**.
- Permisos, roles, ownership y aislamiento entre tenants se conservan sin
  excepción.
- **Las cifras son el contrato.** Promedios, redondeos, el corte
  Aprobado/Reprobado y los ids sintéticos se conservan exactamente, incluida la
  diferencia entre promediar valores redondeados y sin redondear. Un boletín es
  un documento que el colegio entrega: una cifra distinta no es un detalle.
- El historial académico **no se recalcula**: los boletines son fotos del
  pasado, conforme fijó la capa 6.
- Los límites de transacción se conservan: qué se confirma junto, qué se
  revierte junto y quién es dueño de `commit`, `rollback`, cursor y conexión,
  conforme a la capa 1.
- Ninguna operación DB síncrona vuelve al event loop ni se altera el limitador
  compartido sin medir de nuevo su capacidad.
- Los contratos de los dominios ya migrados que tocan estas tablas o estas rutas
  siguen pasando su caracterización, **empezando por `notas`**.
- El SQL de dominio se conserva hasta que una subcapa autorice, con
  caracterización previa, un cambio concreto.

## Línea base

Se registrará al ejecutar 7.0. **No se ha ejecutado ningún comando de
verificación en la activación.**

| Comprobación | Comando | Resultado |
|---|---|---|
| Compuerta heredada, antes de tocar nada | `.\venv\Scripts\python.exe scripts\verify.py` | Pendiente. Al cerrar `asistencia` fueron **872 pruebas, exit 0** |
| Pruebas específicas nuevas | `.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_boletin_caracterizacion.py` | Pendiente |
| Suite global | `.\venv\Scripts\python.exe scripts\verify.py` | Pendiente |
| Ruff | Ejecutado por la compuerta global y sobre los archivos nuevos | Pendiente |
| Dependencias | Ejecutado por la compuerta global | Pendiente |

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 7.0 | Frontera, inventario, contratos, caracterización y línea base de consultas y conexiones | **Pendiente y no iniciada** |
| 7.1 | Primera extracción protegida | Sin definir: depende de la evidencia de 7.0 |
| 7.2 | Segunda extracción o punto de decisión | Sin definir |

El desglose se deja deliberadamente **sin decidir** hasta tener la evidencia del
inventario, igual que hicieron la capa 6 y las cuatro capas 7 anteriores. Las
subcapas innecesarias se marcarán `No aplica` con explicación. **Nunca se
ejecutan dos subcapas en el mismo turno.**

## Subcapa 7.0 — trabajo exacto, pendiente y no iniciada

1. **Determinar la frontera antes que nada.** Listar las rutas declaradas por
   `app/routes/boletines.py` y las rutas de boletín declaradas por
   `app/routes/notas.py`, y registrar cuáles pertenecen a cada dominio.
   Comprobar de nuevo que **no hay colisión de paths**. Registrar el borde
   elegido **con evidencia**, no por nombre de archivo.
2. Inventariar entradas HTTP del dominio: método, path, permisos, payload de
   entrada, forma exacta de la respuesta y status codes, incluidos los de error.
3. Inventariar archivos: router, controlador, esquema, servicio y repositorio si
   existen. Contar sentencias SQL inline por archivo.
4. Determinar **si el dominio escribe**, qué tablas y con qué semántica
   transaccional; quién es dueño de `commit`, `rollback`, cursor y conexión.
5. Fijar por prueba las **cifras**: promedios, redondeos, corte
   Aprobado/Reprobado, ids sintéticos y el `promedio: 0` del detallado si
   persiste.
6. Medir **línea base de consultas y de conexiones** por camino, con dobles
   herméticos, y fijarla por aserción. Determinar si el N+1 del supuesto 6 sigue
   vivo y reconciliarlo con la medición de 4 consultas del supuesto 7.
7. Resolver **los trece supuestos** uno por uno, con evidencia, y registrar cuál
   se confirma, cuál es incompleto y cuál es falso.
8. Escribir la caracterización en `tests/test_boletin_caracterizacion.py`, un
   archivo nuevo. **No se reescriben ni se retiran** las pruebas heredadas.
9. Registrar hallazgos **sin corregir ninguno**.
10. Archivos permitidos: **un solo archivo de prueba nuevo** y esta bitácora. El
    diff de 7.0 **no debe modificar ningún archivo rastreado de producto**,
    igual que los de 5.0, 6.0 y las cuatro 7.0 anteriores.
11. Comandos de verificación: la compuerta global antes y después, las pruebas
    específicas, Ruff sobre el archivo nuevo y `git diff --check`.
12. **Punto exacto donde debe detenerse**: al cerrar 7.0 con su registro
    escrito. **No iniciar 7.1 en el mismo turno.**

## Criterios de cierre de la subcapa 7.0

- La frontera del dominio queda registrada con evidencia y no por inferencia.
- Los trece supuestos quedan resueltos uno por uno.
- Existe caracterización ejecutable que fija contratos, cifras y línea base de
  consultas y conexiones.
- Compuerta global correcta y Ruff correcto.
- Diff exclusivo de la subcapa y sin duplicación heredada.
- Bitácora actualizada con archivos, comandos, resultados, decisiones y riesgos.

## Criterios de cierre de la capa

- Todas las subcapas necesarias están cerradas.
- Compuerta global correcta.
- Contratos conservados o cambios explícitamente aprobados.
- Staging, rollback y verificación manual documentados. **Atención**: si esta
  capa llega a publicarse, el rollback **no será local**, a diferencia de las
  cuatro anteriores en el momento de su cierre.
- Siguiente capa autorizada por el usuario.

## Decisiones

- **Decisión de la activación: el dominio es `boletin` y solo ese.** Motivo: el
  índice ordena «uno a la vez». Alternativa descartada: activar `boletin` y
  `planilla` juntos por compartir el mismo tipo de frontera partida; se descarta
  porque duplicaría el alcance y ninguna capa del programa lo ha hecho.
- **Decisión de la activación: continuar aceptando las verificaciones heredadas
  como pendientes.** Motivo: el usuario eligió activar en vez de cerrarlas, tras
  recibir las cuatro salidas por escrito. **Ninguna se marca como cumplida** y
  su riesgo queda registrado abajo.
- **Decisión de la activación: no corregir `07_ASISTENCIA.md`.** Motivo:
  corregir una bitácora cerrada exige una orden propia. La autorización de este
  turno cubría **el índice**, y allí quedó registrado el cambio de estado de
  publicación.
- **Decisión aplazada a 7.0: dónde está el borde del dominio.** No se toma por
  inferencia en la activación. Las rutas de boletín que viven en `notas` están
  cerradas; moverlas exigiría una orden explícita posterior a la evidencia.

## Riesgos

- **Frontera partida.** Evidencia: 7.0 de `notas`, supuesto 6, confirmado.
  Mitigación: determinar el borde con evidencia como primer paso de 7.0 y no
  mover nada de `notas` sin orden. Responsable de validarlo: 7.0.
- **Las cifras son el contrato y aquí son varias.** Evidencia: capa 1 fijó el
  corte en 3,0 y los ids sintéticos; 7.0 de `notas` fijó el promedio sin
  redondear y el `promedio: 0` del detallado. Mitigación: fijarlas por prueba
  antes de tocar nada. Responsable: 7.0.
- **Parte del cálculo puede vivir en el frontend.** Evidencia: el comentario «El
  frontend recalcula luego» que registró la 7.0 de `notas`. Mitigación: una
  prueba de servidor no puede cubrir eso; debe quedar explícito en la
  verificación manual. Responsable: el usuario.
- **Pocos datos reales.** Evidencia: 3 y 4 filas en `tenant_2005`. Mitigación:
  la verificación manual debe usar un curso con notas reales, no el mínimo.
  Responsable: el usuario.
- **Consumidores ajenos ya migrados.** Evidencia: `notas_detalle` la leen siete
  módulos. Mitigación: ejecutar siempre la compuerta **completa**; romper un
  contrato ajeno no haría fallar las pruebas de `boletin`. Responsable: 7.0 y
  cada subcapa posterior.
- **El commit base ya está en producción.** Evidencia: `git ls-remote` del
  2026-08-21. Mitigación: documentar el rollback como no local desde el primer
  día. Responsable: el cierre de la capa.
- **Verificaciones heredadas pendientes**, aceptadas por decisión explícita:
  valor operativo final de `DB_STATEMENT_TIMEOUT_MS` de la capa 1; ausencia de
  evidencia de GitHub Actions desde la capa 0; los tres pasos del guion de
  `ventas` y los tres del de `asistencia` que no constan; y la **credencial
  privilegiada de la capa 4 sin rotar**. Ninguna se marca como cumplida.

## Registro de ejecución

### 2026-08-21 — activación de la capa para `boletin`

- Modo de acceso: mismo checkout local; Git validado directamente en
  `C:\Users\David\Documents\sistema_escolar_api`. No se usó GitHub para inferir
  el estado local; el remoto se comprobó además contra el remoto real.
- Autorización: orden explícita del usuario en este turno, nombrando el dominio
  `boletin` al elegirlo de la lista de los ocho en espera. **No se pegó el
  bloque preparado** de `PROMPT_CONTINUACION.md`; la autorización llegó en
  conversación, en la misma orden que autorizó la corrección documental. La
  condición que ese bloque exige —nombrar el dominio explícitamente y no
  deducirlo— **se cumplió**. **La advertencia de frontera partida se entregó
  antes de la elección**, en el informe de estado del turno anterior.
- **Verificaciones heredadas**: se ofrecieron por escrito cuatro salidas
  concretas antes de escribir nada, incluida la de cerrarlas. **El usuario
  eligió activar.** Quedan registradas con su riesgo y **ninguna se marca como
  cumplida**.
- Rama acordada: `main`.
- Estado antes de escribir: árbol limpio, verificado con
  `git status --porcelain=v1` con salida vacía **dos veces**; `HEAD` real
  `8e61170f32a6d6a23ca23f9ead89d17bc209e7b6`, comprobado y no recordado.
- Continuidad: el base de la capa 7 para `asistencia`,
  `a894441f8676b0486e3395f88179cdf6cba61430`, existe y es ancestro de `HEAD`,
  verificado con `git merge-base --is-ancestor`. Sus **cinco** commits
  posteriores forman una historia lineal y **todos quedan explicados**: la
  activación `4e38e6c`, el cierre de 7.0 `68ff9a4`, la extracción de 7.1
  `4a4d9e1` y el cierre `e5b74d2` están en `07_ASISTENCIA.md`; el quinto,
  `8e61170`, es la medición del N+1 en conexiones y **está explicado en el
  índice**, no en la bitácora, que ya estaba cerrada cuando se escribió. Se
  verificó con `git show --stat`: toca **exactamente un archivo de documentación
  y ningún código**. **No es una divergencia de producto.**
- **Estado remoto comprobado, no supuesto**: `origin/main` está en
  `8e61170f32a6d6a23ca23f9ead89d17bc209e7b6`, el mismo commit que `HEAD`,
  confirmado con `git rev-parse origin/main` y contra el remoto real con
  `git ls-remote origin main`. El reflog registra `update by push` de `e5b74d2`
  el 2026-08-21 a las **13:00:34 -0500** y de `8e61170` a las **13:03:27
  -0500**. **No se consultó ni se atribuye ningún run de GitHub Actions**; esa
  evidencia sigue sin obtenerse desde la capa 0.
- **Desfase documental corregido en el índice, con autorización explícita del
  usuario**: `07_ASISTENCIA.md` y el índice afirmaban que la capa 7 para
  `asistencia` **no estaba publicada** y que su rollback era «puramente local».
  **Ya no es cierto.** Producción corre ese código desde el push del 2026-08-21.
  Se preguntó al usuario antes de tocar nada y autorizó corregir **el índice**;
  la línea fechada se conserva intacta, conforme al criterio que la capa 4 fijó,
  y lo que se añade es la línea que registra el cambio de estado, colocada
  inmediatamente antes y marcada como sustituta. **`07_ASISTENCIA.md` no se
  editó.** Es el **tercer desfase consecutivo** del mismo tipo, tras `notas` y
  `ventas`, y el primero que el propio índice había anticipado por escrito.
- **Residuo documental corregido como parte de la activación**: el índice
  conservaba un encabezado que declaraba `asistencia` «en migración y activo».
  Dejarlo habría hecho que el índice marcara **dos** capas activas, lo que el
  protocolo obliga a tratar como ambigüedad y detenerse. Se corrigió a «migrado
  y cerrado» porque **marcar únicamente esta capa como activa es requisito de la
  propia activación**.
- **Residuo documental detectado y NO corregido**: el índice conserva, después
  de las líneas que cierran `ventas`, un párrafo que describe su punto de
  decisión como **abierto** y su verificación manual como **pendiente**, cuando
  las dos cosas se resolvieron. Ya estaba anotado al activar `asistencia` y
  sigue sin tocarse: **la autorización de este turno no lo cubría**.
- Archivos creados o modificados: esta bitácora y
  `docs/modularizacion/README.md`.
- Código de producto, pruebas, consultas, configuración, dependencias y workflow
  inspeccionados o modificados: **ninguno**. **No se inspeccionó código de
  `boletin`** ni de ningún otro dominio, ni siquiera el listado de nombres de
  archivo. Los trece supuestos de la tabla de arriba salen **exclusivamente de
  la documentación del programa** —`00_LINEA_BASE_CALIDAD.md`,
  `01_FUNDACION_BASE_DATOS.md`, `03_MIGRACIONES_TENANTS.md`,
  `04_REPORTES_FINANCIEROS.md`, `06_ASIGNACIONES_ESTUDIANTES.md`,
  `07_NOTAS.md`, `07_ASISTENCIA.md` y el índice—, y cada uno lleva su origen
  anotado para que 7.0 pueda contrastarlo.
- Pruebas, migraciones, conexiones a PostgreSQL, acceso a producción, commit,
  push y deploy: **ninguno**.
- Comandos de precondición: `git rev-parse --abbrev-ref HEAD`,
  `git status --porcelain=v1`, `git rev-parse HEAD`, `git rev-parse origin/main`,
  `git ls-remote origin main`, `git merge-base --is-ancestor`,
  `git log --oneline` desde el base de `asistencia`, `git reflog show
  origin/main` y `git show --stat`; todos con resultado coherente con la
  activación.
- Estado al cerrar el turno de activación: capa 7 **activa** para el dominio
  `boletin`; **7.0 pendiente y no iniciada**.
- Siguiente acción exacta: ejecutar únicamente **7.0** conforme al trabajo
  exacto de arriba y detenerse antes de 7.1.

## Entrega al próximo chat

- Capa activa: **7, para el dominio `boletin` y solo ese.** Los otros siete
  dominios siguen en espera.
- Última subcapa terminada: **ninguna** en esta bitácora. La anterior del
  programa fue la 7.1 de `asistencia`, cerrada el 2026-08-20.
- Primera subcapa pendiente: **7.0**, pendiente y **no iniciada**.
- Commit base: `8e61170f32a6d6a23ca23f9ead89d17bc209e7b6`, rama `main`,
  **publicado y desplegado**, comprobado contra el remoto real.
- Bloqueos: ninguno. Verificaciones heredadas **pendientes y aceptadas** por
  decisión explícita del usuario: valor operativo final de
  `DB_STATEMENT_TIMEOUT_MS` (capa 1), evidencia de GitHub Actions posterior a la
  capa 0, los **tres pasos del guion de `ventas`** y los **tres del de
  `asistencia`** que no constan. La credencial privilegiada de la capa 4 sigue
  **sin rotar**.
- Lo que hay que recordar antes de tocar nada:
  1. **Un solo dominio.** `dashboard`, `notas`, `ventas` y `asistencia` están
     cerrados en sus propias bitácoras y los otros siete siguen en espera.
  2. **La frontera está partida y eso se sabe de antemano.** `notas` posee
     `/boletin/{id}` y `/boletin/detallado/{id}`. Determinar el borde con
     evidencia es el **primer** paso de 7.0, no un detalle.
  3. **Nada de `notas` se mueve.** Su 7.1 cerró esa frontera de persistencia.
     Moverlo exige una orden explícita posterior a la evidencia.
  4. **Las cifras son el contrato**: promedio sin redondear, corte en 3,0
     inclusive, ids sintéticos y `promedio: 0` en el detallado. Fijarlas por
     prueba antes de tocar nada.
  5. **`app/core/permissions.py` está fuera de alcance**, incluido el N+1 en
     conexiones que dejó `asistencia`.
  6. **El commit base ya está en producción.** El rollback de esta capa, si se
     publica, **no será local**.
  7. **No corregir ninguno de los trece supuestos convertidos en hallazgos**, ni
     los cuarenta y uno que dashboard, notas, ventas y asistencia dejaron
     abiertos.
  8. **Ejecutar siempre la compuerta completa**: los consumidores de
     `notas_detalle` no fallan con las pruebas de este dominio.
- Siguiente acción exacta: ejecutar únicamente **7.0** y detenerse antes de 7.1.
  Una instrucción genérica de continuar **sí** autoriza 7.0, porque la capa está
  activa y 7.0 es su primera subcapa pendiente.
