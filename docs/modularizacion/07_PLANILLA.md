# Capa 7: planilla

Última revisión: 2026-08-21.

## Control

- Estado: **Activa** desde el 2026-08-21.
- Commit base: `580c0ad6f0d14d16af5cbd8b2a4a9e4532485b89`.
- Rama acordada: `main`.
- Primera subcapa pendiente: **7.0**, inventario, frontera, contratos y
  caracterización. **No iniciada**.
- Código de producto modificado al activar: **Ninguno**.
- Dominio de esta capa: **planilla, y solo ese**. Los otros cinco dominios que
  siguen en espera necesitan su propia bitácora y su propia orden.
- Autorización: orden explícita del usuario el 2026-08-21, nombrando el dominio:
  «el dominio es planilla».
- La autorización de este turno cubre **solo la activación documental**. No
  autoriza inspeccionar código de `planilla`, ejecutar 7.0, modificar producto,
  tocar la base de datos, hacer commit, push ni deploy.

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

| # | Supuesto documental | Origen | Estado al activar |
|---:|---|---|---|
| 1 | `planilla` es uno de los dominios pendientes de la capa 7 | Índice maestro | **Confirmado documentalmente; no delimita archivos** |
| 2 | `notas` posee `/planilla/{asignacion_id}` | Cierre de 7.0 de `notas`, resumido por el índice | **No verificado contra el código vigente** |
| 3 | `boletin_controller` conserva `obtener_notas_planilla_controller`, sin consumidores, con una sentencia inline | Cierre de 7.1 de `boletin`, resumido por el índice | **No verificado contra el código vigente** |
| 4 | La frontera real de `planilla` atraviesa más de un archivo o dominio nominal | Consecuencia de los dos registros anteriores | **Inferencia; 7.0 debe confirmarla o refutarla** |
| 5 | El dominio lee o escribe datos | No determinado por la documentación de continuidad | **Desconocido** |
| 6 | Existen transacciones, cálculos o fórmulas que deban preservarse | No determinado | **Desconocido** |
| 7 | Los permisos y modelos de ownership son uniformes | No determinado | **Desconocido** |
| 8 | Existe repositorio o servicio propio de `planilla` | No determinado | **Desconocido** |
| 9 | Hay N+1 de consultas o conexiones | No determinado | **Desconocido** |
| 10 | Existen pruebas propias suficientes para una extracción | No determinado | **Desconocido** |

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
| Pruebas específicas | Se determinará en 7.0 a partir de las pruebas existentes del dominio | Pendiente; 7.0 no iniciada |
| Suite global | `.\venv\Scripts\python.exe scripts\verify.py` | Pendiente; no se ejecuta en la activación documental |
| Ruff | `.\venv\Scripts\python.exe -m ruff check` sobre el alcance de 7.0 | Pendiente |
| Dependencias | Incluido en `scripts\verify.py` | Pendiente |

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 7.0 | Delimitar la frontera, inventariar contratos y caracterizar el comportamiento y la línea base | **Pendiente y no iniciada** |
| 7.1 | Primera extracción protegida | **Sin definir hasta cerrar 7.0** |
| 7.2 | Segunda extracción, integración o punto de decisión | **Sin definir hasta cerrar 7.0** |

Las subcapas se adaptarán a la evidencia. Las innecesarias se marcarán `No
aplica` con explicación. Nunca se ejecutan dos en el mismo turno.

## Subcapa activa: trabajo exacto de 7.0

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
9. Archivos permitidos en 7.0: pruebas de caracterización del dominio y esta
   bitácora. **Ningún archivo de producto se modifica.**
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

## Criterios de cierre de la capa

- Todas las subcapas necesarias están cerradas.
- Compuerta global correcta.
- Contratos conservados o cambios explícitamente aprobados.
- Staging, rollback y verificación manual documentados.
- La capa queda cerrada y el siguiente dominio permanece en espera hasta una
  nueva orden explícita.

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

## Riesgos

- **Frontera partida.** Evidencia: la documentación atribuye piezas con nombre
  de planilla a dos dominios cerrados. Mitigación: delimitar antes de contar o
  extraer. Responsable: 7.0.
- **Código documentado como muerto dentro de un dominio cerrado.** Moverlo por
  nombre podría crear una función sin consumidor o reabrir `boletin`.
  Mitigación: confirmar consumidores antes de decidir. Responsable: 7.0.
- **Perfil de riesgo desconocido.** La activación no sabe aún si `planilla`
  escribe ni qué cálculos realiza. Mitigación: no modificar producto en 7.0.
- **Las cifras pueden ser el contrato.** Las capas anteriores encontraron
  varias fórmulas de promedio. Mitigación: caracterizar cada cálculo antes de
  moverlo. Responsable: 7.0.
- **Verificaciones pendientes aceptadas**, sin marcarlas como cumplidas:
  calibración operativa final de `DB_STATEMENT_TIMEOUT_MS`; evidencia de GitHub
  Actions posterior a la capa 0; pasos manuales no confirmados de `ventas`,
  `asistencia`, `boletin` y `observaciones`; y la credencial privilegiada de la
  capa 4 sin rotar.

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

## Entrega al próximo chat

- Capa activa: **7 para `planilla`, y solo ese dominio**.
- Última capa cerrada: **7 para `observaciones`**, con 7.0 y 7.1 completas.
- Commit base: `580c0ad6f0d14d16af5cbd8b2a4a9e4532485b89`.
- Primera subcapa pendiente: **7.0 de `planilla`, no iniciada**.
- Código de `planilla` inspeccionado al activar: **ninguno**.
- Verificaciones heredadas: pendientes y aceptadas; ninguna se marca como
  cumplida.
- Bloqueos: ninguno.
- Siguiente acción exacta: ejecutar solo 7.0, actualizar esta bitácora y
  detenerse antes de 7.1.
