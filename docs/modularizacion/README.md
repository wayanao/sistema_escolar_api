# Guía maestra de evolución segura del backend

Última revisión: 2026-08-14.

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
| 4 | Reportes financieros | Dominio modular, N+1 eliminado y consultas medidas | **Activa**; 4.0 y 4.1 cerradas, 4.2 pendiente | [04_REPORTES_FINANCIEROS.md](./04_REPORTES_FINANCIEROS.md) |
| 5 | Pagos y tipos de pago | Dominio financiero modularizado y protegido | En espera | Se crea al activarla |
| 6 | Asignaciones y estudiantes | Dominios grandes separados con contratos estables | En espera | Se crea al activarla |
| 7 | Resto de dominios | Migración individual con contratos y pruebas | En espera | Una bitácora por dominio al activarlo |

No se crea por anticipado un documento por cada dominio. Cuando una capa se
cierre y el usuario ordene continuar, se crea su sucesora desde
`PLANTILLA_CAPA.md`, se registra el commit base vigente y se actualiza esta
tabla.

Las capas 0, 1, 2 y 3 están cerradas. La capa 4 está **activa** desde el
2026-08-14, cerró 4.0 y 4.1, y su primera subcapa pendiente es 4.2. La capa 3
se abrió y se cerró el 2026-08-13, y es la única del programa que modificó la
base de datos real, con autorización explícita del usuario para cada paso. No
se atribuye ningún resultado de GitHub Actions sin evidencia del run
correspondiente.

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
- Capa activa: **4, reportes financieros**. Primera subcapa pendiente: **4.2**.
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
- Capa 4 activa; 4.0 y 4.1 cerradas y primera subcapa pendiente: 4.2,
  eliminación agrupada del N+1 de `/reportes/estado-cuenta/{curso_id}`.
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

- [04_REPORTES_FINANCIEROS.md](./04_REPORTES_FINANCIEROS.md): **bitácora
  activa** de la capa 4 y fuente de continuidad. Registra el commit base, las
  verificaciones heredadas aceptadas como pendientes y el trabajo exacto de
  4.2, además de 4.1 cerrada y del inventario, N+1 y medición no productiva
  registrados en 4.0. Es el documento que un chat nuevo debe leer después de
  este índice.
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
  iniciar o continuar en otro chat, más un resumen del estado del programa. La
  autorización puntual para activar la capa 4 fue consumida y retirada. Incluye
  las tres trampas que dejó la capa 3: el endpoint `-pooler`, los nombres sin
  cualificar que resuelve el `search_path`, y que los ensayos necesitan una rama
  de Neon creada desde producción.
- [PLANTILLA_CAPA.md](./PLANTILLA_CAPA.md): estructura de la siguiente bitácora.
