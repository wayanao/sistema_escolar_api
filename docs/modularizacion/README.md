# Guía maestra de evolución segura del backend

Última revisión: 2026-08-19.

## Propósito

Este directorio conserva el contexto operativo necesario para mejorar el
backend por capas y continuar el trabajo en chats o modelos distintos sin leer
todo el historial del proyecto.

Aunque la carpeta se llama `modularizacion`, el programa no contiene únicamente
movimientos arquitectónicos. Incluye primero calidad, base de datos,
concurrencia y migraciones; la modularización por dominios comienza después.

Este documento define el orden. La bitácora activa define el trabajo concreto.
Un asistente no debe cambiar el orden ni ampliar el alcance sin aprobación del
usuario.

## Resultado buscado

Evolucionar el monolito FastAPI para soportar más colegios y datos con menor
riesgo, conservando:

- endpoints, métodos, status codes y payloads;
- permisos, roles, ownership y aislamiento entre tenants;
- cálculos, transacciones y efectos laterales actuales;
- compatibilidad con el frontend desplegado;
- PostgreSQL, `psycopg2` y el modelo de schemas tenant durante este programa.

No se autoriza una reescritura, microservicios, cambio de driver, ORM, rediseño
funcional ni una corrección oportunista ajena a la capa activa.

## Orden aprobado

| Orden | Capa | Resultado principal | Estado | Bitácora |
|---:|---|---|---|---|
| 0 | Línea base y calidad | Pruebas deterministas, compuerta global y CI | **Cerrada**; CI verificada en remoto | [00_LINEA_BASE_CALIDAD.md](./00_LINEA_BASE_CALIDAD.md) |
| 1 | Fundación de base de datos | Conexiones, transacciones, timeouts y pool definidos | **Cerrada**; primera medición hecha, valor operativo final pendiente | [01_FUNDACION_BASE_DATOS.md](./01_FUNDACION_BASE_DATOS.md) |
| 2 | Concurrencia | DB síncrona fuera del event loop preservando `ContextVar` | **Cerrada** y publicada; CI posterior al cierre no verificada | [02_CONCURRENCIA.md](./02_CONCURRENCIA.md) |
| 3 | Migraciones y tenants | Todos los tenants versionados, runner bloqueado y alta reproducible | **Cerrada**; reparó producción y verificó en uso | [03_MIGRACIONES_TENANTS.md](./03_MIGRACIONES_TENANTS.md) |
| 4 | Reportes financieros | Dominio modular, N+1 eliminado y consultas medidas | **Cerrada**; N+1 de 5N a 15 constantes, medido en producción | [04_REPORTES_FINANCIEROS.md](./04_REPORTES_FINANCIEROS.md) |
| 5 | Pagos y tipos de pago | Dominio financiero modularizado y protegido | **Cerrada**; SQL inline de 23 a 3, sin tocar la base | [05_PAGOS_TIPOS_PAGO.md](./05_PAGOS_TIPOS_PAGO.md) |
| 6 | Asignaciones y estudiantes | Dominios grandes separados con contratos estables | **Cerrada**; SQL inline de 52 a 1, sin tocar la base | [06_ASIGNACIONES_ESTUDIANTES.md](./06_ASIGNACIONES_ESTUDIANTES.md) |
| 7 | Resto de dominios — **`dashboard` migrado** | Migración individual con contratos y pruebas | **Cerrada** para `dashboard` el 2026-08-19; publicada y verificada a mano | [07_DASHBOARD.md](./07_DASHBOARD.md) |
| 7 | Resto de dominios — **`notas` en curso** | Migración individual con contratos y pruebas | **Activa** para `notas` desde el 2026-08-19; **7.0 cerrada**, 7.1 definida y pendiente. Los demás dominios, **en espera** | [07_NOTAS.md](./07_NOTAS.md) |

No se crea por anticipado un documento por cada dominio. Cuando una capa se
cierre y el usuario ordene continuar, se crea su sucesora desde
`PLANTILLA_CAPA.md`, se registra el commit base vigente y se actualiza esta
tabla.

Las capas 0 a 6 están cerradas. **La capa 7 quedó cerrada para el dominio
`dashboard`** el 2026-08-19, con sus subcapas 7.0 y 7.1 completas y la
verificación manual hecha. **La capa activa es la 7 para el dominio `notas`**,
activada el 2026-08-19 por orden explícita del usuario, con su subcapa 7.0
**pendiente y no iniciada**.

La capa 7 se cierra **por dominio**, no de una vez: cada uno tiene su propia
bitácora, su propio commit base y su propio cierre, y **las subcapas se numeran
por bitácora**, así que existe una «7.0 de dashboard», cerrada, y una «7.0 de
notas», pendiente. En prosa deben citarse siempre con el nombre del dominio. Los
demás dominios de la capa 7 siguen **en espera** y cada uno necesitará su propia
bitácora y su propia orden; ninguno se activa sin orden explícita del usuario. La capa 3 es la única del programa
que modificó la base
de datos real, con autorización explícita del usuario para cada paso; la capa 4
solo la leyó; las capas 5 y 6 **no la tocaron en absoluto**, pese a ser las que
modularizaron caminos de escritura. No se atribuye ningún resultado de GitHub
Actions sin evidencia del run correspondiente.

## Alcance de cada capa

### 0. Línea base y calidad

- Documentar contratos que deberán conservarse.
- Corregir exclusivamente las tres pruebas sensibles al reloj.
- Crear un comando global y reproducible de verificación.
- Agregar CI que ejecute la misma compuerta.

### 1. Fundación de base de datos

- Eliminar aperturas manuales progresivamente, sin migración masiva.
- Definir propiedad de `commit`, `rollback`, cursor y conexión.
- Establecer timeouts y manejo del pool con evidencia.
- Mantener `psycopg2`.

### 2. Concurrencia

- Sacar operaciones DB síncronas del event loop mediante un threadpool
  controlado.
- Preservar y probar correctamente el `ContextVar` del tenant.
- Medir concurrencia antes y después.

No basta con convertir dependencias a `def`: la propagación del tenant forma
parte del contrato de seguridad.

### 3. Migraciones y tenants

- Verificar y aplicar migraciones a todos los tenants reactivables.
- Agregar bloqueo para impedir ejecuciones simultáneas.
- Sustituir progresivamente la copia de un tenant plantilla por un alta basada
  en migraciones versionadas.
- Ensayar primero en una base de prueba o staging y preparar rollback.

### 4. Reportes financieros

- Primer dominio que se modulariza.
- Separar HTTP, reglas, servicios y persistencia.
- Eliminar el N+1 mediante consultas agrupadas equivalentes.
- Medir consultas críticas con `EXPLAIN ANALYZE` sobre datos no productivos.

### 5. Pagos y tipos de pago

- Segundo dominio por criticidad financiera.
- Proteger montos, saldos, comprobantes, idempotencia y transacciones.
- Mantener contratos del frontend y de la base de datos.

### 6. Asignaciones y estudiantes

- Migrar después de estabilizar las capas financieras.
- Trabajar cada dominio en subcapas y evitar una extracción conjunta masiva.
- Proteger permisos, relaciones académicas, archivos e historial.

### 7. Resto de dominios

- Priorizar uno a la vez cuando llegue esta etapa.
- Agregar `response_model`, errores de dominio y pruebas HTTP o de integración
  solo después de caracterizar y conservar la respuesta existente.
- No crear abstracciones compartidas sin dos consumidores reales.

**Dominio migrado y cerrado: `dashboard`.** Lo eligió el usuario el 2026-08-17 y
su bitácora es [07_DASHBOARD.md](./07_DASHBOARD.md).

**Dominio activo: `notas`.** Lo eligió el usuario el 2026-08-19, tras pedir que
se le explicara qué es un dominio en este programa y qué quedaba en espera; **no
se dedujo por inferencia**. Su bitácora es [07_NOTAS.md](./07_NOTAS.md) y su
alcance se limita a ese dominio.

Ningún otro se activa por inferencia: boletín, asistencia, observaciones,
planilla, planeador anual, plan de clases, ventas, branding, profesores y super
admin siguen en espera, y cada uno exigirá su propia bitácora y una orden
explícita.

Advertencia de perfil, registrada al activar `notas` y **sin verificar**:
`dashboard` resultó ser de **solo lectura**, y no hay ninguna razón para esperar
lo mismo aquí. Si `notas` escribe —lo probable en un dominio de
calificaciones—, su perfil de riesgo es el de la **capa 5**, no el de dashboard.
Su subcapa 7.0 debe responderlo antes de cualquier extracción.

## Paquete mínimo de contexto para un chat nuevo

Un chat nuevo debe leer completamente y en este orden:

1. `docs/modularizacion/README.md`;
2. la bitácora marcada como `Activa` en la tabla o, si no existe una, la
   bitácora cerrada más reciente que conserve verificaciones pendientes;
3. las instrucciones locales del repositorio, si existen;
4. únicamente los archivos fuente y pruebas relacionados con la subcapa activa.

Si no hay una capa marcada como `Activa`, el asistente puede completar o
registrar las verificaciones pendientes de la última capa cerrada, pero no debe
iniciar una capa nueva sin orden expresa del usuario.

No necesita leer todo `docs/`, `CAMBIOS_BACKEND.md` ni bitácoras cerradas, salvo
que el documento activo señale una sección concreta.

El usuario puede copiar siempre el mismo archivo
`PROMPT_CONTINUACION.md`. El prompt no contiene el nombre fijo de una capa: el
índice maestro le indica al asistente cuál está activa.

## Comprobaciones antes de modificar

El asistente debe:

1. confirmar la rama acordada;
2. confirmar que `git status` esté limpio;
3. comparar `HEAD` con el commit base registrado en la bitácora activa;
4. revisar que los commits posteriores al base estén explicados allí;
5. detenerse ante cambios ajenos, divergencias o un base ambiguo.

El commit base es el punto anterior a la capa activa. Se actualiza al activar
una capa nueva; no se reutiliza automáticamente el base inicial del programa.

## Regla de ejecución por turnos

- Ejecutar únicamente la primera subcapa pendiente de la bitácora activa.
- Agregar o conservar pruebas antes de una extracción importante.
- No iniciar la siguiente subcapa en el mismo turno.
- Actualizar la bitácora con archivos, comandos, resultados y decisiones.
- Registrar riesgos y la siguiente acción exacta.
- No hacer commit, push, deploy, acceso a producción ni migraciones reales.

Si aparece un defecto ajeno, se documenta. Solo se corrige si impide verificar
la subcapa y el usuario aprueba la ampliación.

## Verificación proporcional

Cada subcapa debe ejecutar:

1. pruebas específicas;
2. Ruff sobre el alcance modificado;
3. la compuerta global cuando ya exista o al cerrar la capa;
4. `git diff --check`;
5. revisión del alcance del diff.

La última subcapa de una capa debe incluir pruebas completas, lint,
dependencias, instrucciones de staging, rollback y verificación manual aplicable.

## Estado inicial registrado

- Repositorio: `sistema_escolar_api`.
- Rama al crear esta guía: `main` alineada con `origin/main`.
- Commit: `b8c7653445a50bc1e230a19e0ca8bb088c47cb69`.
- Árbol de trabajo al crear esta guía: limpio.
- Capa activa: 0, línea base y calidad.
- Código de producto modificado por esta guía: ninguno.

## Estado actual

- Repositorio: `sistema_escolar_api`.
- Rama acordada: `main`.
- Capa 0 **cerrada** el 2026-08-11, sin verificaciones pendientes.
- Compuerta global: 192 pruebas correctas, Ruff correcto y `pip check` correcto,
  tanto en local como en un checkout limpio de GitHub Actions.
- Último commit publicado y verificado en remoto:
  `b20dcbe43a64c25e2ece7a7a99782983e2626160`.
- Ejecución remota de GitHub Actions: el primer run, sobre `23bce41`, **falló**.
  `pytest` y `pip check` terminaron en exit 0, pero Ruff reportó 460 errores
  porque la instalación limpia resolvió `ruff>=0.5.0` a una versión mayor con
  otro conjunto de reglas por defecto. Se corrigió con el tope
  `ruff>=0.5.0,<0.16` y el run sobre `b20dcbe` terminó **correctamente**.
- Capa 1 **cerrada** el 2026-08-11. Commit base:
  `6754e4aad59c1e428ea97d31fe8e96fdbba7694d`; historial final de 19 commits,
  todos explicados en su bitácora. La auditoría de cierre se ejecutó cuando 17
  estaban commiteados y los cambios finales aún permanecían en el árbol.
- Resultado de la capa 1: las 50 aperturas de conexión sin cierre garantizado
  llegaron a **0**, incluidas 2 que fugaban en un camino normal; ninguna ruta
  abre conexiones; hay 4 timeouts donde antes no existía ninguno; la suite pasó
  de 192 a **334** pruebas.
- Los timeouts se aplican con `set_config(..., TRUE)` por transacción, no en el
  paquete de arranque: el endpoint `-pooler` de Neon es PgBouncer y rechaza la
  conexión entera si recibe parámetros que no sabe rastrear. Verificado contra la
  base real.
- **Verificación operativa pendiente y aceptada** de la capa 1: calibrar
  `DB_STATEMENT_TIMEOUT_MS` contra la duración real de las consultas pesadas. El
  usuario la aceptó para no bloquear el cierre; el valor puede ajustarse por
  entorno sin desplegar código. No debe marcarse como cumplida.
- Capa 2 **cerrada** el 2026-08-13. Commit base:
  `b24cb8d3f1a8fa1d48699ed5732d4013ab6fe7f9`; al comenzar el cierre había ocho
  commits locales posteriores, todos explicados en su bitácora. El cierre
  documental quedó publicado en
  `8c3939ad5dc872b08e93464145369b3a1eea909e`; al preparar el relevo,
  `HEAD` y la referencia local `origin/main` coincidían en ese commit. No se
  presenta GitHub Actions como verificada para la capa 2 sin evidencia de un
  run asociado.
- Resultado de la capa 2: 23 handlers sin `await` pasan por el threadpool de
  FastAPI, branding conserva su lectura async y descarga storage/DB al worker,
  y las tres consultas de autenticación async usan el offload estándar sin
  perder el tenant. El limitador compartido deriva 5 workers para el pool actual
  de 10 conexiones a partir del pico inventariado de 2 conexiones por worker.
- Medición hermética final: mediana total 102,093 ms, heartbeat retrasado
  4,471 ms, solapamiento 2, trabajo DB simulado en workers y tenants/restauración
  correctos. La compuerta local cerró con **477 pruebas**, Ruff correcto y
  `pip check` correcto.
- Capa 3 **activada** el 2026-08-13 por orden explícita del usuario. Commit base:
  `81882f3b1ee9e3b50076b0fc1fd93dcd9fd5ac70`, el `HEAD` limpio vigente y
  coincidente con la referencia local `origin/main`. Los diez commits posteriores
  al base de la capa 2 quedaron auditados y explicados en su bitácora. La
  activación creó únicamente la bitácora nueva y este índice; no inspeccionó ni
  modificó código, migraciones, esquemas, pruebas ni configuración.
- Capa 3 **cerrada** el 2026-08-13, con sus subcapas 3.0 a 3.6 completas.
  Compuerta al cerrar: **exit 0 con 570 pruebas**, Ruff correcto y `pip check`
  correcto. La suite pasó de 477 al empezar la capa a 570.
- **Estado de los tenants**: quedan dos, `tenant_2005` —el único de producción—
  y `tenant_colegio_1` —plantilla y demo—, ambos con 37 claves foráneas, 30
  secuencias propias, ninguna prestada y las 30 migraciones registradas. Los
  demos `tenant_3333` y `tenant_4444` se **eliminaron** el 2026-08-13, tras
  cerrar la capa, por decisión del usuario y en vez de repararlos.
  `scripts/auditar_migraciones_tenants.py` termina en exit 0 con todos los
  destinos al día.
- **Punto abierto resuelto** el 2026-08-13, tras el cierre: la migración base y
  `migrations/` ya están enlazados. `scripts/generar_esquema_base.py` regenera
  la base en un comando y `tests/test_esquema_base.py` hace fallar la compuerta
  si alguien añade una migración y no la regenera. El flujo completo está en
  `docs/MIGRACIONES.md`, sección «Añadir una migración nueva».
- **Verificación manual hecha** el 2026-08-13 por el usuario, con resultado
  correcto tras ejercitar la aplicación contra la base ya reparada.
- Capa 4 **activada** el 2026-08-14 por orden explícita del usuario. Commit
  base: `46fad2c4c12482830cc58ac28ea2512f96155fb8`, el `HEAD` limpio vigente en
  `main` y coincidente con la referencia local `origin/main`. Los 13 commits
  posteriores al base de la capa 3 fueron auditados y están explicados en su
  bitácora. La activación es únicamente documental: no inspecciona ni modifica
  código, pruebas, consultas, configuración o base de datos.
- Decisión al activar la capa 4: continuar localmente aceptando que sigan
  pendientes la calibración operativa final de `DB_STATEMENT_TIMEOUT_MS` y la
  evidencia de GitHub Actions posterior a la capa 0. En 4.0 se comprobó READ
  ONLY, cancelación real y `EXPLAIN ANALYZE` en una rama de prueba; se propuso
  15000 ms sin aplicarlo porque el schema no era equivalente, el volumen
  financiero era limitado y falta conocer el deadline HTTP externo.
- Resultado de 4.0: nueve entradas financieras/consumidoras inventariadas y
  protegidas por diez pruebas nuevas. Línea base: `10 + 5N` consultas en el
  estado de cuenta de reportes, `1 + 12N` en el consumidor de cuentas y 12
  constantes en cartera. La compuerta local terminó con 585 pruebas, Ruff y
  dependencias correctas. No se modificó producto ni configuración.
- Resultado de 4.1: la persistencia de general, ingresos por mes/rango y
  egresos por rango quedó extraída a funciones que reciben el cursor existente.
  Se conservaron byte por byte las 13 cadenas SQL, sus conteos y parámetros,
  además de respuestas, fallbacks y lifecycle. La compuerta local terminó con
  598 pruebas, Ruff y dependencias correctas. No se tocó el N+1 ni la base de
  datos.
- Resultado de 4.2: el estado de cuenta de reportes sustituyó únicamente sus
  cinco lecturas por estudiante por cinco lecturas agrupadas fijas. El conteo
  hermético pasó de 6/15/25 a **6/15/15** para 0/1/3 estudiantes; la compuerta
  local terminó con **604 pruebas**, Ruff y dependencias correctas. No se tocó
  el `1 + 12N` del consumidor de cuentas ni se accedió a la base de datos.
- Avance de 4.3: el último SQL inline del estado de cuenta pasó al repositorio y
  el ensamblado financiero a un servicio puro. La revisión posterior demostró
  que `pagos.concepto_id` nunca existió en el schema ni en sus escritores; se
  eliminó esa dependencia usando `descripcion`, el fallback heredado por
  `tipo_pago` y `pagos_aplicaciones`, sin migraciones ni consultas adicionales.
  Reportes conservan 6/15, cuentas 1/13/37 y cartera 5/12/12; la compuerta local
  terminó con **606 pruebas**, Ruff y dependencias correctas. Faltan medir el
  SQL final con `EXPLAIN ANALYZE` y ejecutar la verificación manual sobre un
  schema no productivo equivalente; la ejecución de 4.0 no midió ese SQL porque
  el código de entonces falló antes por esa referencia.
- Capa 4 **cerrada** el 2026-08-15, con sus subcapas 4.0 a 4.3 completas.
  Compuerta al cerrar: **exit 0 con 606 pruebas**. Cumplió sus tres objetivos: la
  persistencia y las reglas quedaron separadas del controller, el N+1 pasó de
  **5N consultas por estudiante a 15 constantes**, y las tres consultas del
  estado de cuenta se midieron sobre producción en **menos de 1 ms** juntas.
- Hallazgo adicional de la capa 4: el estado de cuenta **estaba roto**.
  Referenciaba `pagos.concepto_id`, una columna que no existe, y fallaba con
  `42703` en cada llamada. Se comprobó midiendo el SQL anterior contra el schema
  real. El usuario verificó a mano que las cifras nuevas cuadran.
- La capa 4 **no modificó la base de datos**: todo lo ejecutado contra
  PostgreSQL fue lectura en transacciones `READ ONLY` con `rollback`. Su rollback
  es puramente de código.
- Capa 4 **publicada**: el reflog de `origin/main` registra `update by push` de
  `f4d0913` el 2026-08-15 a las 13:20:16. Ese commit es el punto de rollback
  vigente de la capa 4 y el commit base de la capa 5. La bitácora de la capa 4
  describía todavía el estado anterior, «seis commits por delante»; quedó
  corregida.
- Corrección de continuidad del 2026-08-15, autorizada explícitamente: el índice
  y la bitácora de la capa 4 conservaban líneas obsoletas que aún la declaraban
  activa y a 4.3 «en verificación», junto a las que las declaraban cerradas.
  Incluían una línea «Capa activa: 4» seguida en el renglón siguiente por «Capa
  activa: ninguna». Se eliminaron los residuos y se conservaron intactas las
  entradas de registro fechadas, que describen el estado de su momento.
- Capa 5 **activada** el 2026-08-15 por orden explícita del usuario. Commit
  base: `f4d091329f84bcdd100b1bf0c70c02a0e32ee138`, el `HEAD` limpio vigente en
  `main` y coincidente con la referencia local `origin/main`. Los siete commits
  posteriores al base de la capa 4 fueron auditados y están explicados en su
  bitácora. La activación es únicamente documental: no inspeccionó ni modificó
  código, pruebas, consultas, configuración o base de datos.
- Decisión al activar la capa 5: continuar aceptando que sigan pendientes la
  calibración operativa final de `DB_STATEMENT_TIMEOUT_MS` y la evidencia de
  GitHub Actions posterior a la capa 0. Ninguna se marca como cumplida.
  La credencial privilegiada compartida en la capa 4 sigue **sin rotar**.
- La capa 5 **escribe** donde las anteriores solo leían. Su bitácora registra el
  perfil de riesgo propio: las 26 claves foráneas repuestas en la capa 3 pueden
  hacer fallar inserciones que antes pasaban en silencio, los contratos de
  lectura de `pagos` fijados en la capa 4 pueden romperse desde la escritura, y
  `pagos.concepto_id` no existe.
- Resultado de 5.0: el dominio quedó inventariado en **19 entradas HTTP** y
  **seis tablas escritas** —`pagos`, `pagos_aplicaciones`, `ventas`,
  `tipos_de_pagos`, `tipos_pagos_cursos` y `tipos_pagos_estudiantes`—, protegido
  por **40 pruebas nuevas**. Línea base: un pago simple cuesta **12 consultas,
  once de ellas lecturas** para validar que no excede la deuda; un cargo de
  inventario cuesta **4** porque sale antes; anular cuesta 4 o 6. **No hay N+1**
  en este dominio: ningún conteo depende del número de estudiantes. La compuerta
  local terminó con **646 pruebas**, Ruff y dependencias correctas. No se
  modificó producto ni configuración: el diff es un solo archivo nuevo.
- Hallazgos de 5.0, **registrados y sin corregir** porque exigen decisión
  explícita: `POST /pagos` **no tenía clave de idempotencia** —el 2026-08-17 se
  corrigió la mitad con autorización explícita, añadiendo un advisory lock por
  estudiante que cierra el hueco concurrente; el duplicado parcial separado en el
  tiempo sigue abierto y necesita la clave, que es el paso 2 acordado y no
  iniciado—; siete funciones de tipos de pago absorben `Exception` y presentan un
  fallo de infraestructura como 400 o 404 —el 2026-08-17 se corrigió la mitad:
  ya registran el traceback, que antes se perdía; cambiar los códigos a 500 sigue
  pendiente—; y los dos upsert de tipos de pago abrían **dos
  conexiones por petición** —corregido el 2026-08-17: ahora releen con su propio
  cursor antes de confirmar, lo que cerró además una ventana en la que un
  `commit` correcto se reportaba como 400—.
- Hallazgo **retirado** el 2026-08-17: el «filtro de ownership por pago» que la
  capa 5 había anotado **no era un hueco**. Solo alcanza el endpoint quien tiene
  `rol == 'admin'` estricto, el `search_path` impide cruzar de colegio, dentro de
  un colegio no existen admins con alcance parcial, y la anulación queda auditada
  con motivo, fecha y responsable. Queda anotado en la bitácora para que no se
  vuelva a levantar.
- Resultado de 5.1: las ocho escrituras de `pagos` y `pagos_aplicaciones`
  salieron del controlador a `app/repositories/pagos_repository.py`, seis
  funciones que reciben el cursor existente. El controlador pasó de 717 a 701
  líneas y conserva conexión, cursor, `commit`, `rollback`, advisory lock,
  validaciones y traducción de errores. Un comparador AST confirmó **19
  sentencias distintas antes y después, conjunto idéntico**, con **20 de 21**
  literales conservados **byte a byte**. **5.1 no modificó ninguna prueba**: la
  caracterización de 5.0 bastó para demostrar que nada observable cambió.
  Compuerta local: 646 pruebas, Ruff y dependencias correctas.
- Único cambio de texto SQL autorizado en 5.1: los dos
  `INSERT INTO pagos (estudiante_id, venta_id, …)` de la rama de métodos y la
  rama simple eran idénticos salvo cuatro espacios de sangría. El usuario
  autorizó explícitamente unificarlos en una constante; el flujo de tokens que
  recibe PostgreSQL no cambia y quedó verificado. Las sentencias que tocan
  `ventas` **no se movieron**: son de otro dominio y su ubicación se decide en
  5.2 con evidencia.
- Resultado de 5.2: las cuatro lecturas de `pagos` y las cinco sentencias que
  tocan `ventas` salieron del controlador. El repositorio llega a **15
  funciones** y el controlador baja de **717 líneas al activar la capa a 644**,
  con solo **cuatro sentencias inline**: tres guardas de esquema y la lectura de
  `_periodos_disponibles`. El comparador AST **contra el commit base de la
  capa** confirmó 19 sentencias distintas antes y después, conjunto idéntico, con
  **19 de 21** literales byte a byte. Compuerta local: **657 pruebas**, Ruff y
  dependencias correctas.
- Decisión de 5.2, tomada con evidencia: el contacto con `ventas` vive en
  `pagos_repository.py`, en un bloque rotulado como **el efecto de un pago sobre
  un cargo**, no como persistencia general de ventas. `venta_controller.py` ya
  tiene su propio SQL inline y no existe un `ventas_repository`; crear uno
  tendría un solo consumidor real, y migrar `venta_controller` está fuera del
  alcance de esta capa.
- 5.2 amplió la caracterización **antes** de mover producto, de 40 a 51 casos: el
  historial paginado solo tenía prueba de ruta y la lectura de saldo de venta no
  tenía ninguna.
- Resultado de 5.3: la lectura de aplicaciones vigentes pasó al repositorio, que
  llega a **16 funciones**. Las **tres guardas de esquema y el advisory lock se
  quedan** en el controlador, decidido con evidencia: la convención del
  repositorio es que la introspección de esquema viva junto al código que la
  necesita —`cobros.py` y `tipos_pagos_controller.py` lo hacen así— y el lock es
  control de transacción. **No se retiró código heredado porque no lo hay**: los
  dieciocho helpers privados del controlador conservan consumidores.
- Resultado de la capa 5, con sus cuatro subcapas cerradas:
  `pagos_controller.py` pasó de **717 a 633 líneas** y de **23 sentencias SQL
  inline a 3**; la persistencia vive en `app/repositories/pagos_repository.py`.
  El dominio quedó protegido por **54 pruebas de caracterización** nuevas y la
  suite pasó de 606 a **660**. Compuerta de cierre: exit 0.
- La capa 5 es **exclusivamente una refactorización** y **no tocó la base de
  datos en absoluto**, ni siquiera para leer. Su rollback es puramente de código:
  revertir hasta `f4d0913`. Que nada observable cambió lo demuestran un
  comparador AST contra el commit base —conjunto de SQL idéntico, 19 de 21
  literales byte a byte— y que ninguna de las 54 pruebas cambió de expectativa.
- Hallazgos añadidos en 5.3, **registrados y sin corregir**:
  `pagos_controller._tabla_pagos_aplicaciones_existe` es un duplicado **byte a
  byte** de `cobros.tabla_pagos_aplicaciones_existe`, y `_obtener_saldo_concepto`
  es una indirección vacía. Ninguna está huérfana, así que retirarlas exige una
  decisión explícita. Ninguna prueba depende de que el duplicado siga separado:
  los tres `monkeypatch` de esa función apuntan a `reportes_controller`.
- **Verificación manual de la capa 5: hecha por el usuario y correcta.** La
  ejecutó en **local contra el árbol de trabajo**, que incluía 5.3; se confirmó
  expresamente el artefacto antes de registrarla. Cubre la capa completa.
  Limitación registrada: fue local, **sin push ni despliegue**. Aceptable en una
  refactorización con SQL equivalente demostrado y sin acceso a la base; no lo
  sería en una capa que cambiara comportamiento o tocara datos.
- Capa 5 **cerrada** el 2026-08-16, con sus subcapas 5.0 a 5.3 completas.
  Compuerta al cerrar: **exit 0 con 660 pruebas**, Ruff correcto y `pip check`
  correcto.
- **Estado de publicación de la capa 5**: al cerrarla el 2026-08-16 **no había
  push ni despliegue**, y así quedó registrado. **Se publicó después**, el
  2026-08-17, junto con las tres correcciones puntuales posteriores al cierre.
  Corregido el 2026-08-17 con autorización explícita: el reflog de `origin/main`
  registra `update by push` de `544bd5c` y de `589cb6d`, y `HEAD` coincide con
  esa referencia. Producción **ya no corre `f4d0913`**, porque en este
  repositorio un push a `main` dispara el despliegue. Las líneas fechadas que
  describen el estado del 2026-08-16 se conservan intactas: eran ciertas
  entonces.
- **Pendiente heredado que apareció el 2026-08-17**: al quitar el anidamiento de
  conexiones de los dos upsert, la constante
  `MAX_DB_CONNECTIONS_PER_THREADPOOL_WORKER = 2` de la capa 2 —de donde salen los
  5 workers para el pool de 10— **se quedó sin ningún ejemplo real que la
  respalde**. Se conserva como margen y **no se tocó**: cambiarla exige una
  auditoría de capacidad propia, no una inferencia. El barrido que lo detectó es
  estático y solo ve anidamiento dentro del mismo módulo.
- Capa 6 **activada** el 2026-08-17 por orden explícita del usuario. Commit
  base: `589cb6d1391161c692a6f24aee9d523317cbb1ce`, el `HEAD` limpio vigente en
  `main` y coincidente con la referencia local `origin/main`, que el reflog
  registra como publicada por push. Los diez commits posteriores al base de la
  capa 5 fueron auditados: nueve están explicados en `05_PAGOS_TIPOS_PAGO.md` y
  el décimo, `589cb6d`, es documental y quedó registrado al activar. La
  activación es únicamente documental: no inspeccionó ni modificó código,
  pruebas, consultas, configuración o base de datos.
- Decisión al activar la capa 6: continuar aceptando que sigan pendientes la
  calibración operativa final de `DB_STATEMENT_TIMEOUT_MS` y la evidencia de
  GitHub Actions posterior a la capa 0. Ninguna se marca como cumplida y ambas
  conservan su riesgo. La credencial privilegiada compartida en la capa 4 sigue
  **sin rotar**. Pendientes también, y fuera de la capa 6 salvo orden explícita:
  la clave de idempotencia de `POST /pagos` (paso 2), los status codes 500 de
  `tipos_pagos_controller` y la auditoría de capacidad de la capa 2.
- Resultado de 6.0: el dominio quedó inventariado en **19 entradas HTTP** —12 de
  asignaciones y 7 de estudiantes— y **dos tablas escritas**, `asignaciones` y
  `estudiantes`, protegido por **39 pruebas nuevas**. Línea base: un alta de
  asignación cuesta **12 consultas, diez de ellas de validación**;
  `asignacion_tiene_historial` cuesta hasta **14**, dos por cada una de sus siete
  tablas. **No hay N+1** en ninguno de los dos dominios. La compuerta local
  terminó con **708 pruebas**, Ruff y dependencias correctas. No se modificó
  producto: el diff es un solo archivo nuevo.
- **Los tres supuestos que la activación registró sin verificar quedaron
  resueltos en 6.0.** El de los archivos está **refutado**: ni asignaciones ni
  estudiantes usan `app/services/storage.py` —solo lo hacen branding y plan de
  clases—, así que el rollback de esta capa vuelve a ser de código y filas. El
  consumo de `cobros.calcular_deudas_estudiante` desde estudiantes está
  **confirmado**, y las claves foráneas también: **7 apuntan a `asignaciones` y
  9 a `estudiantes`**, inocuas porque ambos dominios desactivan con `UPDATE` y
  **nunca borran**.
- Diferencia estructural con la capa 5, registrada en 6.0: `pagos` era un dominio
  terminal, pero **`asignaciones` es transversal**. Nueve módulos dependen de
  `resolver_asignacion_academica_id_cursor`. Además los permisos **no son
  uniformes**: dos de las doce entradas de asignaciones usan
  `require_profesor_scope` y admiten a un profesor, no solo a un admin.
- Hallazgos de 6.0, **registrados y sin corregir**: `obtener_clases_profesor_controller`
  está definida **dos veces y ninguna tiene consumidor**, con SQL divergente
  entre copias; hay **SQL de dominio inline en la capa de rutas**, en
  `/mis-clases`; el alta y la edición de asignaciones **no toman ningún lock**,
  así que dos peticiones simultáneas pueden crear clases solapadas;
  `GET /estudiantes/{id}` devuelve `SELECT *`, de modo que su contrato es el
  esquema entero de la tabla; y quedan dos rarezas de status code y varias
  f-strings en SQL hoy no inyectables.
- Resultado de 6.1: la persistencia de la tabla `estudiantes` salió del
  controlador a `app/repositories/estudiantes_repository.py`, **siete funciones**
  que reciben el cursor existente. El controlador pasó de **519 a 396 líneas** y
  conserva conexión, cursor, `commit`, `rollback`, normalización de estado,
  construcción del filtro y degradación por secciones. Un comparador AST contra
  el commit base confirmó **11 sentencias distintas antes y después, conjunto
  idéntico**, con **11 de 11** literales conservados **byte a byte**: a
  diferencia de 5.1 y 5.2, no hizo falta autorizar ningún cambio de texto SQL.
  **6.1 no modificó ninguna prueba**: la caracterización de 6.0 bastó. Compuerta
  local: 708 pruebas, Ruff y dependencias correctas.
- Decisión de 6.1: el filtro de estado se **queda en el controlador** porque
  valida y produce el 422 de la ruta; el repositorio recibe el `where_sql` ya
  construido. Las cuatro lecturas de `detalles` sobre `notas_detalle`,
  `asistencia`, `observaciones` y `ventas` **no se movieron**: no tocan la tabla
  `estudiantes` y su ubicación se decide en 6.2 con evidencia, igual que 5.1
  dejó `ventas` para 5.2.
- Resultado de 6.2, que **termina el dominio de estudiantes**: las cuatro
  lecturas del expediente —`notas_detalle`, `asistencia`, `observaciones` y
  `ventas`— pasaron al repositorio, que llega a **once funciones**. El
  controlador baja de **519 líneas al activar la capa a 381** y de **11
  sentencias SQL inline a 0**. El comparador AST contra el commit base confirmó
  conjunto idéntico y **11 de 11 literales byte a byte**; en toda la extracción
  de estudiantes **no hizo falta autorizar ni un cambio de texto SQL**, a
  diferencia de la capa 5. Compuerta local: **712 pruebas**, Ruff y dependencias
  correctas.
- Decisión de 6.2, tomada con evidencia: las cuatro lecturas viven en
  `estudiantes_repository.py`, en un bloque rotulado como **el expediente de un
  estudiante**, no como persistencia de notas, asistencia u observaciones.
  Existen cuatro repositorios y **ninguno de esos dominios tiene el suyo**; crear
  uno tendría un solo consumidor real porque migrar dashboard, notas, planilla,
  boletín y ventas está fuera del alcance; y **ninguna de las consultas es un
  duplicado** —estudiantes promedia con `ROUND(...,1)` por materia, dashboard con
  `TRUNC(...,2)` por estudiante—. Es el criterio que 5.2 aplicó a `ventas`.
- 6.2 amplió la caracterización **antes** de mover, de 39 a 43 casos: el promedio
  general resultó ser el promedio de los promedios redondeado en Python —4,5 y
  3,0 dan **3,8**—, y no estaba fijado.
- Resultado de 6.3: las **siete escrituras** de `asignaciones` salieron a
  `app/repositories/asignaciones_repository.py`. El controlador pasó de **1093 a
  1041 líneas** y **ya no contiene ninguna escritura**; le quedan **34 lecturas
  distintas**, que son el trabajo de 6.4. El comparador AST contra el commit base
  confirmó **41 sentencias distintas antes y después, conjunto idéntico**, con
  **41 de 41** literales byte a byte. **6.3 no cambió ninguna expectativa de
  prueba**; solo añadió una guardia. Compuerta local: **713 pruebas**, Ruff y
  dependencias correctas.
- Decisiones de 6.3: las **dos formas de `SET activo = FALSE`** —una en cuatro
  líneas, otra en una— **no se unificaron**, porque esta vez no se pidió la
  autorización y la extracción no la necesitaba; una guardia de prueba falla si
  alguien lo hace sin registrarlo. Y `insertar_asignacion` y
  `actualizar_asignacion` **no leen su `RETURNING`**: en el controlador el
  `fetchone` ocurre después del `except IntegrityError`, para que un duplicado se
  traduzca a 409 antes de leer, y mover esa lectura habría cambiado el orden.
- Resultado de 6.4: las lecturas de `asignaciones` salieron al repositorio, que
  llega a **28 funciones** en cinco bloques rotulados. El controlador baja de
  **1093 líneas al activar la capa a 762** y de **41 sentencias SQL inline a 1**.
  El comparador AST contra el commit base confirmó conjunto idéntico y **41 de 41
  literales byte a byte**, incluidas las siete construidas con f-string; en toda
  la extracción de asignaciones **no hizo falta autorizar ni un cambio de texto
  SQL**. **Ninguna prueba cambió de expectativa.** Compuerta local: **713
  pruebas**, Ruff y dependencias correctas.
- Decisiones de 6.4, todas con evidencia: las precondiciones sobre `profesor`,
  `cursos` y `materias` **van** al repositorio, porque no existe repositorio de
  esos catálogos y el patrón que usan aparece cuatro veces en este controlador y
  una sola fuera; `tabla_columna_existe` **se queda**, por la convención que 5.3
  fijó de que la introspección de esquema vive junto al código que la necesita —es
  la única sentencia inline que sobrevive—; y su pregunta hermana sobre datos
  **sí se mueve**, porque pregunta por filas, no por el esquema.
- Resultado de 6.5: el `SELECT` de `GET /mis-clases` salió de
  `app/routes/asignaciones.py` al repositorio, que llega a **33 funciones**. Era
  **el único SQL de dominio que vivía en la capa HTTP** de todo el programa. La
  guardia que 6.0 había dejado sobre ese hallazgo **falló al moverlo**, que era la
  señal esperada, y se sustituyó por dos pruebas positivas. Se recorrieron las 32
  funciones del controlador y **ninguna quedó huérfana**. Compuerta de cierre:
  **714 pruebas, exit 0**.
- Decisión del usuario el 2026-08-17: las dos copias muertas de
  `obtener_clases_profesor_controller` **se dejan** registradas, sin retirar, para
  que la capa cierre siendo una refactorización pura sin borrados de producto.
- Resultado de la capa 6, con sus cinco subcapas cerradas:
  `estudiante_controller.py` pasó de **519 a 381 líneas** y de 11 sentencias SQL
  inline a **0**; `asignacion_controller.py` de **1093 a 762** y de 41 a **1**;
  la persistencia vive en `estudiantes_repository` —11 funciones— y
  `asignaciones_repository` —33—. El dominio quedó protegido por **43 pruebas de
  caracterización** nuevas y la suite pasó de 669 a **714**.
- La capa 6 es **exclusivamente una refactorización** y, como la 5, **no tocó la
  base de datos en absoluto**, ni siquiera para leer. Su rollback es de código:
  revertir hasta `589cb6d`; a diferencia de la capa 5, ese base **ya está
  desplegado**, así que revertir exigiría push y despliegue. Que nada observable
  cambió lo demuestran los comparadores AST contra el commit base —conjunto de
  SQL idéntico, **42 de 42** literales byte a byte en asignaciones y **11 de 11**
  en estudiantes— y que ninguna prueba cambió de expectativa. **En toda la capa
  no hizo falta autorizar ni un cambio de texto SQL**, frente a los dos que
  necesitó la capa 5.
- **Verificación manual de la capa 6: hecha por el usuario y correcta.** La
  ejecutó en **local contra el árbol de trabajo**, que incluía 6.5; se confirmó
  expresamente el artefacto **antes** de registrarla, porque el estado de Git
  admitía tres lecturas —`HEAD` sin 6.5, el árbol con 6.5, y `origin/main` con el
  código anterior a la capa—. Es la lección 10 de la capa 5, aplicada. Cubre la
  capa completa. Limitación que sigue vigente: **fue local**. La capa se publicó
  después, así que producción corre este código sin que nadie lo haya ejercitado
  a mano **ya desplegado**. Aceptable en una refactorización con SQL equivalente
  demostrado y sin acceso a la base; no lo sería en una capa que tocara datos.
- Capa 6 **cerrada** el 2026-08-17, con sus subcapas 6.0 a 6.5 completas.
  Compuerta al cerrar: **exit 0 con 714 pruebas**, Ruff correcto y `pip check`
  correcto.
- **Estado de publicación de la capa 6**: al cerrarla **no había push**, y así
  quedó registrado. **Se publicó el mismo 2026-08-17**, poco después: el reflog
  de `origin/main` registra `update by push` de `bf075a0`, el commit de cierre,
  que arrastra los **siete** de la capa —de `2881b03` a `bf075a0`—. Como un push
  a `main` dispara el despliegue, **producción ya corre este código**, y el
  rollback a `589cb6d` exigiría otro push y otro despliegue.
- Riesgo más directo que deja abierto la capa 6: **el alta y la edición de
  asignaciones no toman ningún lock**, así que dos peticiones simultáneas pueden
  crear clases solapadas para el mismo profesor o salón. Es el análogo del hueco
  de idempotencia de `POST /pagos`, que la capa 5 sí corrigió a medias; este
  sigue intacto.
- Capa 7 **activada** el 2026-08-17 por orden explícita del usuario, **para el
  dominio `dashboard` y solo ese**. Commit base:
  `123637ee80895023ecece9c32df526ef4eddd1e5`, el `HEAD` limpio vigente en `main`
  y coincidente con la referencia local `origin/main`, que el reflog registra
  como publicada por push. Los ocho commits posteriores al base de la capa 6
  fueron auditados: siete están explicados en `06_ASIGNACIONES_ESTUDIANTES.md` y
  el octavo, `123637e`, es documental y su contenido está registrado en esa
  misma bitácora y en este índice. La activación es únicamente documental: no
  inspeccionó ni modificó código, pruebas, consultas, configuración o base de
  datos.
- **El dominio lo eligió el usuario, no se dedujo.** La autorización preparada
  llegó con el marcador `DOMINIO` sin rellenar; se detuvo el trabajo, se explicó
  qué es un dominio y por qué esta capa obliga a nombrar uno, y el usuario
  eligió `dashboard`. Activarla sin nombrarlo habría dejado el alcance abierto,
  que es lo que el propio texto de la autorización prohíbe.
- Decisión al activar la capa 7: continuar aceptando que sigan pendientes la
  calibración operativa final de `DB_STATEMENT_TIMEOUT_MS` y la evidencia de
  GitHub Actions posterior a la capa 0. Ninguna se marca como cumplida y ambas
  conservan su riesgo. La credencial privilegiada compartida en la capa 4 sigue
  **sin rotar**. Pendientes también, y fuera de la capa 7 salvo orden explícita:
  la clave de idempotencia de `POST /pagos` (paso 2), los status codes 500 de
  `tipos_pagos_controller`, la auditoría de capacidad de la capa 2 y la ausencia
  de lock en el alta y la edición de asignaciones.
- **Nada de lo que la bitácora de la capa 7 dice de `dashboard` está
  verificado.** La activación no inspeccionó su código: registra **siete
  supuestos heredados marcados como no verificados** —que no tiene repositorio
  propio, que consume `resolver_asignacion_academica_id_cursor`, que lee tablas
  académicas con SQL inline, que concentra los cálculos más caros, que no
  escribe archivos, que es de solo lectura y que sus permisos no son
  uniformes—. 7.0 debe confirmarlos o refutarlos uno a uno. Es la lección 12 de
  la capa 6, donde un supuesto heredado resultó falso.
- Riesgo propio y nuevo de la capa 7: `response_model` **filtra** en FastAPI los
  campos que no declara, así que añadirlo puede recortar un payload sin que
  falle nada. El índice solo lo autoriza tras caracterizar y conservar la
  respuesta existente. Y en un panel de estadísticas **la cifra es el
  contrato**: un `TRUNC` frente a un `ROUND` cambia lo que ve el usuario sin
  romper la estructura.
- Resultado de 7.0: el dominio quedó inventariado en **7 entradas HTTP**, todas
  `GET` y todas de **solo lectura**, con **cero tablas escritas**, **cero
  transacciones propias** y **8 sentencias SQL inline** en el controlador,
  protegido por **41 pruebas nuevas**. Los permisos usan **cuatro modelos
  distintos** en siete entradas. La compuerta local terminó con **755 pruebas**,
  Ruff y dependencias correctas. No se modificó producto: el diff es un solo
  archivo nuevo.
- **Los siete supuestos que la activación registró sin verificar quedaron
  resueltos en 7.0**: seis confirmados y **uno refutado**. Dashboard **no
  concentra «varias consultas de promedios por estudiante»**: cada panel se
  resuelve con **una sola consulta agregada** y **no hay N+1**. Lo caro no son
  las consultas sino **las conexiones**: el camino de notas con asignación abre
  **cuatro en serie** —dos precondiciones de permiso, una comprobación de acceso
  y la consulta—, y resuelve la asignación académica **dos veces**. Es la
  evidencia real que le faltaba a la constante de capacidad de la capa 2, que se
  registra **sin actuar**.
- Resultado de 7.1: las **8 sentencias** salieron del controlador a
  `app/repositories/dashboard_repository.py`, **ocho funciones** que reciben el
  cursor existente más los **dos fragmentos** que componen las consultas de
  cumpleaños. `dashboard_controller.py` pasó de **336 a 146 líneas** y de **8
  sentencias SQL inline a 0**; la ruta ya tenía 0. El comparador AST contra el
  commit base confirmó **16 literales SQL distintos antes y después, conjunto
  idéntico**, con **16 de 16 byte a byte**: **no hizo falta autorizar ningún
  cambio de texto SQL**. Compuerta local: **756 pruebas**, Ruff y dependencias
  correctas.
- **Las dos guardias de línea base que 7.0 dejó puestas fallaron al extraer**,
  que era la señal esperada —lección 14 de la capa 6—, y solo esas dos: las otras
  **75 pruebas pasaron sin cambiar de expectativa**, incluidos los ocho conteos
  de consultas y conexiones. Se sustituyeron por versiones positivas.
- Decisión de 7.1, tomada con evidencia: las dos consultas de precondición de
  permiso viven en `dashboard_repository` y **no** en `asignaciones_repository`,
  aunque consulten esa tabla y ese repositorio exista. No son duplicados —las
  funciones vecinas **filtran por `activo` y estas no**—, moverlas ampliaría el
  diff a un módulo que la capa 6 cerró, y sobre todo **poner una consulta que no
  filtra al lado de las que sí filtran invita a "arreglarla"**, que es
  exactamente el hallazgo que esta capa tiene prohibido corregir.
- **Decisión del usuario el 2026-08-17: cerrar la capa aquí**, sin abrir 7.2.
  `response_model` y los errores de dominio **no se añaden** y **no quedan como
  deuda de esta capa**: pasan a ser trabajo disponible que exigiría una orden
  explícita. La capa 7 para `dashboard` es, como la 5 y la 6, **exclusivamente
  una refactorización**, y **no tocó la base de datos** ni siquiera para leer.
  Compuerta de cierre: **exit 0 con 756 pruebas**. Su rollback es de código,
  revertir hasta `123637e`; ese base **ya está desplegado**, así que revertir
  exigiría push y despliegue.
- **Verificación manual de la capa 7: hecha por el usuario y correcta**, el
  2026-08-19, **en local** y con cobertura completa del guion. El artefacto se
  confirmó **antes** de registrarla: a diferencia de la capa 6 no había
  ambigüedad, porque el árbol estaba limpio y `HEAD` coincidía con `origin/main`,
  así que lo ejercitado en local y lo publicado son **el mismo commit**. La
  limitación que queda es de **entorno**: nadie ha repetido el guion contra el
  despliegue.
- **Estado de publicación de la capa 7**: **publicada y desplegada**. El reflog de
  `origin/main` registra `update by push` de `8591816`, que arrastra los
  **cuatro** commits de la capa —`fb303d5`, `59efda6`, `c75a5b7` y `8591816`—.
  Producción ya corre este código y el rollback a `123637e` exigiría otro push y
  otro despliegue.
- Capa 7 **cerrada para `dashboard`** el 2026-08-19. Compuerta de cierre: **exit 0
  con 756 pruebas**, Ruff correcto y `pip check` íntegro. La suite pasó de 714 al
  activar la capa a 756. Cerrarla **no cancela los diez hallazgos de 7.0**, que
  siguen vivos, empezando por el `activo` ausente de las dos precondiciones de
  permiso: un profesor con la asignación desactivada conserva el acceso.
- Capa 7 **activada para el dominio `notas`** el 2026-08-19 por orden explícita
  del usuario, **y solo ese dominio**. Commit base:
  `eee8aec8725fc0bdd4a98fd2fd29cb88502c56e1`, el `HEAD` limpio vigente en `main`
  y coincidente con la referencia local `origin/main`, que el reflog registra
  como publicada por push. Los cinco commits posteriores al base de dashboard
  fueron auditados y **todos están explicados** en `07_DASHBOARD.md`. La
  activación es únicamente documental: no inspeccionó ni modificó código,
  pruebas, consultas, configuración o base de datos. **No se abrió ningún
  archivo de `notas`**; lo único observado fue el listado de nombres de archivo
  de `app/routes/` y `app/controllers/`, para responder al usuario qué dominios
  quedaban en espera.
- **El dominio lo eligió el usuario, no se dedujo**, igual que con `dashboard`.
  No se pegó el bloque de autorización preparado en `PROMPT_CONTINUACION.md`: la
  orden llegó en conversación, después de que el usuario preguntara qué
  significan «dominio» y «capa 7». La condición que ese bloque exige —nombrar el
  dominio explícitamente— **se cumplió**.
- Decisión al activar la capa 7 para `notas`: continuar aceptando que sigan
  pendientes la calibración operativa final de `DB_STATEMENT_TIMEOUT_MS` y la
  evidencia de GitHub Actions posterior a la capa 0. Se preguntó explícitamente
  antes de escribir nada, ofreciendo también completarlas; el usuario eligió
  continuar. Ninguna se marca como cumplida y ambas conservan su riesgo. La
  credencial privilegiada compartida en la capa 4 sigue **sin rotar**. Pendientes
  también, y fuera de esta capa salvo orden explícita: la clave de idempotencia
  de `POST /pagos` (paso 2), los status codes 500 de `tipos_pagos_controller`, la
  auditoría de capacidad de la capa 2, la ausencia de lock en el alta y la
  edición de asignaciones, y **los diez hallazgos de dashboard**, empezando por
  el `activo` ausente de sus dos precondiciones de permiso.
- **Nada de lo que la bitácora de `notas` dice de ese dominio está verificado.**
  La activación no inspeccionó su código: registra **diez supuestos heredados
  marcados como no verificados**, y el que manda es si **el dominio escribe**,
  porque de él depende el perfil de riesgo entero. Su 7.0 debe resolverlos uno a
  uno. Es la lección 12 de la capa 6, que ya sirvió dos veces.
- **Residuo documental detectado en este índice y no corregido**: el párrafo de
  más abajo sobre el punto de decisión de dashboard lo declara «ya resuelto» y en
  la misma frase dice que «no está tomada». **Sí se tomó**: cerrar sin abrir 7.2,
  como confirman la tabla de arriba y `07_DASHBOARD.md`. Es texto residual del
  mismo tipo que el que la capa 4 limpió con autorización explícita; corregirlo
  es ajeno a una activación y queda registrado para que nadie lo lea como una
  decisión abierta.
- Resultado de 7.0 de `notas`: el dominio quedó inventariado en **5 entradas
  HTTP** repartidas en **cuatro archivos**, con **una sola tabla escrita**
  —`notas_detalle`, solo `INSERT`—, **una sola transacción propia** y **9
  sentencias SQL inline** —6 en el controlador, **3 en el servicio** y 0 en la
  ruta—, protegido por **34 pruebas nuevas**. Los permisos usan **dos modelos**
  en cinco entradas. La compuerta local terminó con **790 pruebas**, Ruff y
  dependencias correctas. No se modificó producto: el diff es un solo archivo
  nuevo.
- **Los diez supuestos que la activación registró sin verificar quedaron
  resueltos en 7.0**: nueve confirmados y **uno incompleto**. El dominio **no
  eran dos archivos sino cuatro**: `app/services/nota_service.py` contiene **un
  tercio de la persistencia**, y un inventario que se hubiera fiado del supuesto
  lo habría dejado fuera. **El supuesto que mandaba quedó confirmado: `notas`
  escribe**, así que su perfil de riesgo es el de la capa 5 y no el de
  dashboard.
- **Hay N+1 en `notas`**, el primero que el programa encuentra desde la capa 4:
  `GET /boletin/detallado/{id}` emite **una consulta por materia**. Y escribir
  una nota cuesta **cuatro conexiones**, cinco como profesor, porque las tres
  validaciones abren cada una la suya. Ambas cosas se **registran sin actuar**:
  la primera es trabajo del tipo de la capa 4 y la segunda de la auditoría de
  capacidad de la capa 2.
- **Los dos hallazgos más graves de 7.0 de `notas` no tienen equivalente en
  dashboard, porque afectan a lo que el cliente recibe al escribir**:
  `POST /notas` responde **200 con «Nota registrada» aunque no registre nada**
  cuando falla una validación —el error viaja dentro del campo `id`—, y su campo
  **`id` no es un entero sino un diccionario**, porque la ruta envuelve la
  respuesta completa del controlador. **El frontend desplegado depende de lo que
  hoy recibe**, así que cambiarlos no es una corrección interna.
- **Los dos se verificaron con peticiones HTTP reales**, a petición explícita del
  usuario y tras detectar que la primera comprobación solo llamaba a la función
  de ruta y por tanto **nunca observaba un status code**. La verificación se hizo
  conduciendo la aplicación por su **interfaz ASGI cruda**, porque `httpx` no
  está instalado y una subcapa de inventario no cambia dependencias. El hallazgo
  quedó **confirmado**, y el status code **fijado por aserción**. El contraste
  que lo delimita: una `nota` fuera del rango 0..5 **sí** responde 422, así que
  el problema no es FastAPI sino que **las tres validaciones propias del dominio
  no usan su mecanismo de error**.
- **Limitación de evidencia que esto destapó y que afecta a todo el programa**:
  no existe **ni un solo `TestClient`** en `tests/`. Las capas 4 a 7 registraron
  status codes en sus bitácoras a partir de pruebas que **solo invocan
  funciones**, sin observar nunca una respuesta HTTP. `POST /notas` es hoy **la
  única entrada del programa** con esa evidencia. No se revisa el resto —es
  trabajo ajeno a la capa activa—, pero queda anotado que esa evidencia es más
  débil de lo que las bitácoras sugieren.
- Hallazgos de 7.0 de `notas`, **registrados y sin corregir**: son **doce**.
  Además de los dos anteriores y del N+1, la escritura **no fija `periodo`**
  mientras el boletín detallado **sí filtra por él** y las otras tres lecturas lo
  ignoran; `validar_asignacion` **no filtra por `activo`**, tercera instancia del
  patrón que dashboard registró dos veces, y aquí permite **escribir** contra una
  asignación desactivada; `require_estudiante_access` tampoco lo filtra, aunque
  vive en infraestructura compartida y queda fuera de alcance; el dominio **no
  tiene un solo `try/except`**, así que un fallo sale como **500** y no como 400;
  el boletín detallado **fabrica ids sintéticos por concatenación de cadenas**
  que pueden colisionar con ids reales; y **la frontera no coincide con los
  nombres de archivo**, porque `notas` posee `/boletin`, `/boletin/detallado` y
  `/planilla`, sin colisión de paths pero con consecuencias para quien migre esos
  dominios.
- **`notas_detalle` es la tabla más compartida del programa hasta hoy**: la leen
  **siete módulos**, tres de ellos ya migrados —asignaciones, dashboard y
  estudiantes—. Romper un contrato ajeno desde `notas` **no haría fallar sus
  propias pruebas**, solo la compuerta global.
- El punto de decisión que quedó abierto al terminar 7.1, ya resuelto, era: la frontera de persistencia de
  dashboard ya está cerrada. Lo que queda del objetivo de la capa es la parte
  condicional del índice —`response_model`, errores de dominio y pruebas HTTP—,
  que **no entra por inferencia**. Las dos salidas legítimas son cerrar la capa
  como refactorización pura, igual que la 5 y la 6, o abrir una **7.2** que añada
  `response_model` demostrando payload por payload que la respuesta no cambia. Es
  decisión del usuario y no está tomada.
- Hallazgos de 7.0, **registrados y sin corregir**: las dos precondiciones de
  permiso **ignoran `activo`**, así que un profesor con la asignación
  desactivada **conserva el acceso** al rendimiento de ese curso, mientras la
  consulta de cumpleaños del mismo controlador sí filtra; el dominio usa **dos
  definiciones distintas de promedio** —promedio de promedios por clase en notas
  altas y bajas, promedio plano en los rankings—, que con los mismos datos dan
  cifras distintas; las **siete entradas** absorben `Exception`, responden 400 y
  **devuelven el texto de la excepción al cliente** sin registrar nada; el filtro
  de rendimiento consulta la base **desde la capa de rutas** y fuera del
  `try/except`, así que un fallo ahí sale como 500; `dias` se valida dos veces
  con criterios divergentes; y quedan una cuarta pareja de literales gemelos y
  varias f-strings en SQL hoy no inyectables.
- Resultado de 3.5: el alta construye el schema desde la migración base en vez de
  copiar la plantilla. Un tenant nuevo nace con **37 claves foráneas y 30
  secuencias propias**, donde el camino anterior producía **0 y 0**. Ensayado
  dando de alta un tenant real en la rama: 281 columnas idénticas a la
  plantilla, 0 referencias cruzadas y 0 defaults apuntando a ella.
- Resultado de 3.4d: `apply_migration.py` se niega a ejecutarse sobre el endpoint
  agrupado, donde 3.4a demostró que el lock no se sostiene. Efecto operativo: con
  el `.env` actual el runner ya no arranca; hay que usar el endpoint directo.
- Resultado de 3.4e, **aplicado a producción** el 2026-08-13:
  `scripts/sembrar_historial_tenant.py` registró las 15 migraciones que
  `tenant_2005` ya tenía aplicadas, tras comprobar que reproduce la estructura
  de la plantilla. Al aplicarla solo quedó pendiente `tenant_4444`, que era
  demo; después se eliminó y la auditoría final pasó a exit 0. Se verificó antes
  que ninguna de las 15 cambiaría la estructura y que solo una tocaría datos,
  de forma inocua.
- Resultado de 3.4f, **aplicado a producción** el 2026-08-13: se repusieron las
  26 claves foráneas ausentes de `tenant_2005`, que ahora iguala las
  restricciones de la plantilla y las tiene todas validadas. El ensayo destapó
  que `pg_get_constraintdef` devuelve las definiciones sin cualificar: sin fijar
  el `search_path` al destino, las claves se habrían creado apuntando al schema
  de la plantilla. Corregido y protegido con una verificación posterior.
- Resultado de 3.4c: existe `migrations/base/20260813_esquema_base_tenant.sql`,
  extraído del catálogo real y verificado contra la plantilla —281 columnas
  idénticas y **cero** defaults apuntando a ella, porque las columnas se
  declaran `SERIAL`—. Vive en `migrations/base/` para no entrar en el corpus que
  audita el informe de 3.3a.
- **Reparación aplicada a producción el 2026-08-13**, con autorización explícita
  y tras revisar el `--dry-run`: `tenant_2005` tiene sus 30 secuencias propias y
  las ocho tablas que no admitían inserciones vuelven a funcionar, verificado con
  una inserción controlada que se revirtió sin dejar filas. Es la única
  modificación de la base real en todo el programa.
- **Resultado de 3.4a, el más importante de la capa.** De los cuatro schemas
  solo `tenant_2005` era producción real; los demás eran demo o prueba. El
  ensayo sobre una rama de Neon confirmó las cuatro hipótesis de 3.0 y encontró
  entonces una **avería en curso**: ocho tablas de ese colegio —`estudiantes`,
  `profesor`,
  `asignaciones`, `asistencia`, `notas_detalle`, `pagos`, `boletin_cabecera` y
  `boletin_detalles`— no pueden insertar, porque toman su `id` de secuencias que
  viven en el schema de demostración y ya están por debajo del `MAX(id)` real.
  Además, `scripts/limpiar_tenant_colegio_1_operativo.py` haría
  `TRUNCATE … RESTART IDENTITY` sobre 19 de esas secuencias. `tenant_2005` tiene
  también 11 claves foráneas de 37, y el advisory lock de 3.1 no se sostiene
  sobre el endpoint agrupado que usa `.env`. Las secuencias y claves quedaron
  reparadas después, y el runner pasó a rechazar ese endpoint.
- **Resultado de 3.4b**: `scripts/reparar_secuencias_tenant.py` da al tenant
  secuencias propias posicionadas en su `MAX(id)` real. Es auto-medido —calcula
  los máximos al ejecutarse, no lleva valores precalculados—, transaccional e
  idempotente. Una revisión del usuario detectó que la primera versión usaba
  `setval()`, que **no** se revierte con un `ROLLBACK`; se comprobó contra
  PostgreSQL 17.10 y se cambió a `ALTER SEQUENCE … RESTART`, que sí. El ensayo
  se repitió comparando también `last_value` de todas las secuencias e
  incluyendo un fallo simulado: 26 columnas y 8 colisiones reparadas a 0, y ni
  el fallo ni el rollback dejan rastro. Después del ensayo se aplicó a
  producción con autorización explícita; `tenant_2005` conserva 30 secuencias
  propias y cero prestadas.
- Decisión del 2026-08-13: las 30 migraciones de tenant son incrementales y
  ninguna crea las tablas base, que hoy solo existen dentro del schema
  plantilla. El usuario decidió adelantar el ensayo no productivo para extraer
  de una base desechable el DDL real y promoverlo a una migración base
  versionada, descartando `scripts/legacy/crear_cliente.py` como fuente. El
  ensayo pasó a ser 3.4, el alta reproducible bajó a 3.5 y el cierre a 3.6.
- Resultado de 3.0, de solo lectura: registró que seis puntos de entrada podían
  mutar el esquema de un tenant y solo `apply_migration.py` registraba lo
  aplicado; el alta copiaba entonces el schema plantilla sin sembrar
  `public.schema_migrations`. Las subcapas posteriores corrigieron el alta y
  añadieron una auditoría que incluye los estados omitidos por el runner.
- Resultado de 3.1: `apply_migration.py` toma un advisory lock de sesión antes
  de leer o escribir el historial y devuelve exit 2 si otra ejecución lo tiene.
  Se conservaron descubrimiento, checksum, transacción por tenant, mensajes,
  códigos de salida y `--dry-run`. El lock **no** cubre los cuatro scripts
  ad-hoc. 3.4a verificó que solo se sostiene sobre el endpoint directo y 3.4d
  hizo que el runner rechace el agrupado antes de conectar.
- Resultado de 3.2, solo pruebas: caracterización ejecutable del runner completo
  y del alta de tenant. Incluyó una prueba deliberada,
  `test_el_alta_todavia_no_siembra_el_historial_de_migraciones`, que **debe
  fallar** cuando 3.3b corrigiera el defecto; 3.3b produjo esa señal y la
  reemplazó por pruebas positivas.
- Resultado de 3.3a: se añadió `scripts/auditar_migraciones_tenants.py`, un
  informe de solo lectura que compara `migrations/` con
  `public.schema_migrations` e incluye a los tenants `suspendido` y `cancelado`
  que el runner omite. Abre la transacción como `READ ONLY` y no crea el
  historial si falta. Su primera ejecución real ocurrió en 3.4a; después de las
  reparaciones y la eliminación de los demos termina en exit 0 con todos los
  destinos al día.
- Resultado de 3.3b: el alta siembra `public.schema_migrations` copiando las
  filas del schema plantilla, en su misma transacción y con una guarda para no
  romper una base sin historial. Se verificó que las pruebas nuevas fallan
  contra el controlador anterior, que es la señal esperada. La compuerta cerró
  en exit 0 con **529 pruebas**.
- Subcapas de la capa 4: 4.0, 4.1, 4.2 y 4.3 **cerradas**. La separación, la
  compatibilidad con el schema canónico, la compuerta local, la medición y la
  verificación manual quedaron completas.
- Código de producto modificado durante la capa 0: ninguno.
- Código de producto modificado durante la capa 1: el ciclo de vida de las
  conexiones en 20 archivos de `app/`, más los timeouts. Sin cambios en rutas,
  payloads, status codes, permisos, tenant, ownership ni SQL observable.
- Código de producto modificado al activar la capa 3: ninguno.
- Limpieza final, 2026-08-14: la rama de ensayo de Neon quedó **eliminada**. Los
  14 índices duplicados de `tenant_2005` se midieron y se decidió **no
  borrarlos**: el ahorro no compensa otra operación sobre producción. La
  credencial de producción quedó verificada: el usuario inicia sesión en los dos
  tenants, así que `.env` sigue siendo válido.
- Código de producto modificado durante la capa 3: `apply_migration.py`, para el
  lock y la guarda del endpoint agrupado, y
  `app/controllers/super_admin_controller.py`, para sembrar historial y dar de
  alta desde la migración base. Sin cambios en rutas, payloads, status codes,
  permisos, tenant, ownership, SQL de dominio ni en los archivos existentes de
  `migrations/`.

## Archivos de continuidad

- [07_NOTAS.md](./07_NOTAS.md): **bitácora ACTIVA** de la capa 7 para el dominio
  `notas`. Registra el commit base
  `eee8aec8725fc0bdd4a98fd2fd29cb88502c56e1`, la autorización del usuario, el
  alcance limitado a un solo dominio y la decisión explícita de continuar
  aceptando las verificaciones heredadas como pendientes. Conserva el inventario
  de **7.0**, ya **cerrada**: sus 5 entradas HTTP en **cuatro** archivos con sus
  dos modelos de permiso, la línea base de consultas **y conexiones** de diez
  caminos, los **diez supuestos heredados resueltos** —nueve confirmados y uno
  incompleto, el que daba el dominio por dos archivos— y los **doce hallazgos
  sin corregir**, encabezados por el falso éxito de `POST /notas` y su campo
  `id` anidado. Registra que **el dominio escribe**, así que su perfil de riesgo
  es el de la capa 5; que **hay N+1**, el primero desde la capa 4; que la cifra
  es el contrato y este dominio añade la **cuarta** fórmula de promedio; y que
  `notas_detalle` la leen **siete módulos**, tres ya migrados, de modo que
  romper un contrato ajeno no haría fallar las pruebas de `notas`. Deja
  **7.1 definida y no iniciada**, con su punto de decisión propio: si las tres
  consultas de `nota_service` van al repositorio, que **no tiene precedente
  exacto**. **Es el documento que un chat nuevo debe leer después de este
  índice.**
- [07_DASHBOARD.md](./07_DASHBOARD.md): **bitácora cerrada** de la capa 7 para
  el dominio `dashboard`, y **fuente de continuidad**. Registra el commit base
  `123637ee80895023ecece9c32df526ef4eddd1e5`, la autorización y el marcador de
  dominio que llegó sin rellenar, el alcance limitado a un solo dominio, las
  verificaciones heredadas aceptadas como pendientes y el riesgo propio de
  `response_model`. Conserva el inventario de **7.0**, ya **cerrada**: sus 7
  entradas HTTP con sus cuatro modelos de permiso, la línea base de consultas y
  **conexiones** por camino, los **siete supuestos heredados resueltos** —seis
  confirmados y uno refutado— y los **diez hallazgos sin corregir**, entre ellos
  el `activo` ausente de las precondiciones de permiso y las dos fórmulas de
  promedio. Registra también el cierre de **7.1**, la extracción a
  `dashboard_repository` con su comparador AST de **16 de 16** literales, las
  dos guardias que fallaron como señal esperada y la decisión sobre dónde viven
  las precondiciones de permiso. Deja abierto el **punto de decisión** que
  cerró la capa sin abrir una 7.2, el cierre con su rollback, su staging, su
  verificación manual y su estado de publicación, y los **riesgos que deja
  abiertos**. Fue la fuente de continuidad **hasta que se activó `notas`**; sus
  diez hallazgos siguen vivos y **no se corrigen desde la capa activa**.
- [06_ASIGNACIONES_ESTUDIANTES.md](./06_ASIGNACIONES_ESTUDIANTES.md): **bitácora
  cerrada** de la capa 6 y fuente de continuidad **hasta que se activó la capa
  7**. Registra el commit base
  `589cb6d`, el inventario de 6.0 con sus 19 entradas HTTP, dos tablas escritas y
  16 claves foráneas, los **diez hallazgos sin corregir** —entre ellos la
  ausencia de lock frente a horarios solapados y el código muerto duplicado que el
  usuario decidió conservar—, las cuatro extracciones de 6.1 a 6.5 con sus
  decisiones tomadas con evidencia, el supuesto de `storage` **refutado**, y el
  cierre de la capa con su rollback, su verificación manual local y la advertencia
  de que **no llegó a publicarse**. Es el documento que un chat nuevo debe leer
  después de este índice.
- [05_PAGOS_TIPOS_PAGO.md](./05_PAGOS_TIPOS_PAGO.md): **bitácora cerrada** de la
  capa 5. Conserva los siete hallazgos registrados sin corregir y el paso 2
  acordado y no iniciado, la clave de idempotencia de `POST /pagos`.
  Registra el commit base `f4d0913`, las
  verificaciones heredadas aceptadas como pendientes, el inventario de 5.0 con
  sus 19 entradas HTTP, seis tablas escritas, contratos, idempotencia y línea
  base de consultas, los **ocho hallazgos registrados sin corregir**, las
  extracciones de 5.1 a 5.3 con la unificación SQL autorizada y la decisión sobre
  dónde vive el contacto con `ventas`, y el cierre de la capa con su rollback,
  su verificación manual local y la advertencia de que **no llegó a publicarse**.
  Es el documento que un chat nuevo debe leer después de este índice.
- [04_REPORTES_FINANCIEROS.md](./04_REPORTES_FINANCIEROS.md): **bitácora
  cerrada** de la capa 4. Conserva el cierre de 4.3 con su medición sobre
  producción y la verificación manual del usuario, el hallazgo de que el informe
  estaba roto por `pagos.concepto_id`, el punto de rollback vigente `f4d0913`,
  el cierre de 4.2 con su conteo fijo 6/15, la extracción de 4.1 y el inventario
  y medición limitada de 4.0. Sus riesgos abiertos siguen vigentes.
- [03_MIGRACIONES_TENANTS.md](./03_MIGRACIONES_TENANTS.md): **bitácora cerrada**
  de la capa 3. Conserva el inventario, las tres
  reparaciones aplicadas a producción con su rollback, el ensayo sobre una rama
  de Neon, la verificación manual ya realizada, la resolución de sus dos puntos
  abiertos y las lecciones sobre `setval`, el `search_path` y la comparación de
  índices.
- [02_CONCURRENCIA.md](./02_CONCURRENCIA.md): bitácora cerrada de la capa 2;
  conserva la medición, el límite de capacidad, staging, rollback, verificación
  manual y riesgos residuales.
- [01_FUNDACION_BASE_DATOS.md](./01_FUNDACION_BASE_DATOS.md): bitácora cerrada de
  la capa 1; conserva pendiente el valor operativo final de `statement_timeout`
  tras la primera medición de 4.0, y registra la lección de que un cambio en el
  pool no se verifica solo con pruebas herméticas.
- [00_LINEA_BASE_CALIDAD.md](./00_LINEA_BASE_CALIDAD.md): bitácora cerrada de
  la capa 0, sin verificaciones pendientes; conserva la compuerta, la CI y el
  inventario de contratos que la capa 1 debe preservar.
- [PROMPT_CONTINUACION.md](./PROMPT_CONTINUACION.md): texto universal para
  iniciar o continuar en otro chat, más un resumen del estado del programa. Las
  autorizaciones puntuales de las capas 3 a 6 fueron consumidas y retiradas;
  conserva **una preparada para la capa 7**, que exige rellenar antes qué dominio
  se aborda, porque esa capa es «uno a la vez» y no un bloque. Registra también
  lo que dejaron abiertas las capas 5 y 6 —la clave de idempotencia y la ausencia
  de lock frente a horarios solapados— y cuatro lecciones nuevas de la capa 6.
  Incluye
  las tres trampas que dejó la capa 3: el endpoint `-pooler`, los nombres sin
  cualificar que resuelve el `search_path`, y que los ensayos necesitan schema
  canónico, datos representativos y aislamiento no productivo; no requieren
  copiar datos de producción.
- [PLANTILLA_CAPA.md](./PLANTILLA_CAPA.md): estructura de la siguiente bitácora.
