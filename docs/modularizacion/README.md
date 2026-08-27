# Guía maestra de evolución segura del backend

Última revisión: 2026-08-27.

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
| 6 | Asignaciones y estudiantes | Dominios grandes separados con contratos estables | **Cerrada**; SQL inline de 52 a 1; lock de concurrencia corregido y publicado en `721f382`; verificación PostgreSQL real pendiente | [06_ASIGNACIONES_ESTUDIANTES.md](./06_ASIGNACIONES_ESTUDIANTES.md) |
| 7 | Resto de dominios — **`dashboard` migrado** | Migración individual con contratos y pruebas | **Cerrada** para `dashboard` el 2026-08-19; permiso activo publicado en `9f19089` y conexiones seriales reducidas localmente el 2026-08-25; staging pendiente | [07_DASHBOARD.md](./07_DASHBOARD.md) |
| 7 | Resto de dominios — **`notas` migrado** | Migración individual con contratos y pruebas | **Cerrada** para `notas` el 2026-08-19; verificada a mano. **Publicada el 2026-08-20**, después de escribirse su bitácora | [07_NOTAS.md](./07_NOTAS.md) |
| 7 | Resto de dominios — **`ventas` migrado** | Migración individual con contratos y pruebas | **Cerrada** para `ventas` el 2026-08-20; verificada a mano. **Publicada el 2026-08-20**, después de escribirse su bitácora | [07_VENTAS.md](./07_VENTAS.md) |
| 7 | Resto de dominios — **`asistencia` migrado** | Migración individual con contratos y pruebas | **Cerrada** para `asistencia` el 2026-08-21; verificada a mano y publicada. N+1 de permisos corregido y publicado en `bbf3bfb`; staging de la corrección pendiente | [07_ASISTENCIA.md](./07_ASISTENCIA.md) |
| 7 | Resto de dominios — **`boletin` migrado** | Migración individual con contratos y pruebas | **Cerrada** para `boletin` el 2026-08-21; verificada a mano y **sin publicar**. Ver la advertencia de desfase más abajo | [07_BOLETIN.md](./07_BOLETIN.md) |
| 7 | Resto de dominios — **`observaciones` migrado** | Migración individual con contratos y pruebas | **Cerrada** para `observaciones` el 2026-08-21; verificada a mano y publicada. **Campaña de hallazgos cerrada el 2026-08-27**: tres corregidos y publicados —uno de ellos en producción—, dos aparcados, tres notas y uno obsoleto | [07_OBSERVACIONES.md](./07_OBSERVACIONES.md) |
| 7 | Resto de dominios — **`planilla` migrado** | Migración individual con contratos y pruebas | **Cerrada** para `planilla` el 2026-08-21; verificación manual correcta y sin publicación comprobada | [07_PLANILLA.md](./07_PLANILLA.md) |
| 7 | Resto de dominios — **`planeador_anual` migrado** | Migración individual con contratos y pruebas | **Cerrada** el 2026-08-22; 7.2 No aplica, verificación manual global reportada y sin entorno especificado | [07_PLANEADOR_ANUAL.md](./07_PLANEADOR_ANUAL.md) |
| 7 | Resto de dominios — **`plan_de_clases` migrado** | Migración individual con contratos y pruebas | **Cerrada** el 2026-08-22; 7.2/7.3 No aplica, verificación manual global con reserva y sin publicación comprobada | [07_PLAN_DE_CLASES.md](./07_PLAN_DE_CLASES.md) |
| 7 | Resto de dominios — **`branding` migrado** | Migración individual con contratos y pruebas | **Cerrada** el 2026-08-22; 7.2/7.3 No aplica, verificación manual pendiente y sin publicación comprobada | [07_BRANDING.md](./07_BRANDING.md) |
| 7 | Resto de dominios — **`profesores` migrado** | Migración individual con contratos y pruebas | **Cerrada** el 2026-08-23; 7.2/7.3 No aplica, verificación manual pendiente y sin publicación comprobada | [07_PROFESORES.md](./07_PROFESORES.md) |
| 7 | Resto de dominios — **`super_admin` migrado** | Migración individual con contratos y pruebas | **Cerrada** el 2026-08-23; 7.0–7.3 completas, verificación manual pendiente y sin publicación comprobada | [07_SUPER_ADMIN.md](./07_SUPER_ADMIN.md) |

**Estado vigente:** no hay una capa activa. El 2026-08-24 se completaron tres
correcciones autorizadas sobre capas cerradas, sin reabrirlas: el mapeo
seguro a 500 de los siete fallos de infraestructura de
`tipos_pagos_controller`, el N+1 de conexiones de los permisos de `asistencia`
y la protección de concurrencia al crear o editar asignaciones. Esta última
añade `FOR NO KEY UPDATE` a las dos precondiciones existentes de profesor y
curso, conserva **12/10 consultas** en alta/edición y serializa los cruces sin
migración ni cambios de frontend. La compuerta local terminó con **1116
pruebas**. El reflog local de `origin/main` registra los pushes de esas
correcciones en `9a90462`, `bbf3bfb` y `721f382`; después se publicó la
consolidación exclusivamente documental `1ab8912` y la primera corrección de
dashboard en `9f19089`. Esto no demuestra despliegue ni CI: staging, la prueba
con dos conexiones PostgreSQL reales aplicable al lock, despliegue y evidencia
posterior de GitHub Actions siguen pendientes y bajo control del usuario. Las
menciones cronológicas anteriores que
presentan cualquiera de estos hallazgos como abierto describen el estado de su
fecha, no el vigente.

También el 2026-08-24 se completó la auditoría autorizada de
`MAX_DB_CONNECTIONS_PER_THREADPOOL_WORKER = 2`. El barrido acotado y las pruebas
dirigidas **no detectaron `H>1`**; las aperturas múltiples de dashboard, notas y
asistencia son secuenciales. Eso deja `H=1` como hipótesis candidata, no como
cota operativa demostrada. La constante **permanece en 2** y el pool de 10
conserva cinco tokens. El modelo formal continúa en `R=0`; si el `H` real fuera
1, el factor adicional aportaría margen implícito. No cambió producto ni
configuración. Una futura ampliación exige demostrar la cota, separar `H` de una
reserva formal `R`, confirmar procesos/réplicas y medir carga en staging; no es
una corrección pendiente para mantener el estado seguro actual.

El 2026-08-25 se corrigieron, con órdenes explícitas y sin reabrir la capa, los
dos primeros hallazgos de `dashboard`. Las dos precondiciones de rendimiento
exigen ahora `asignaciones.activo = TRUE`; esa corrección se publicó en
`9f19089`, aunque staging, verificación manual, despliegue comprobado y CI
siguen pendientes. Después, las tres precondiciones DB pasaron a compartir una
conexión: el camino con asignación bajó de **4 a 2 conexiones** como profesor y
de **3 a 2** como admin, conservando respectivamente **6 y 5 consultas**, sus
parámetros, orden, mensajes, tenant y ownership. La lectura final mantiene su
segunda conexión para preservar el límite observable 500/400, y la resolución
académica duplicada sigue abierta. Las pruebas relacionadas terminaron con
**99 passed** y la compuerta global con **1120 passed**, Ruff correcto y
dependencias íntegras. La primera ejecución global restringida fue inválida por
30 errores de setup al acceder al temporal de pytest; la repetición con acceso
válido fue la evidencia aceptada. No hubo PostgreSQL, migración, staging,
producción, deploy, commit ni push de la segunda corrección. Quedan **ocho
hallazgos de dashboard**; staging, verificación manual, publicación y CI de la
reducción de conexiones siguen pendientes.

**Tercera corrección puntual de dashboard, 2026-08-25, y auditoría posterior.**
La resolución académica duplicada quedó corregida: la validación devuelve el ID
que ya resolvió y la lectura final lo reutiliza, así que el profesor baja de
**6 a 5 consultas** y el admin de **5 a 4**, ambos con dos conexiones. Sigue
**sin commitear ni publicar**. La auditoría que el usuario pidió antes de
commitear confirmó que **no falta código**: la duplicación desaparece en las dos
entradas afectadas, **no quedan otros caminos con el mismo patrón** —los dos
rankings no lo tenían, porque `require_asignacion_access` consulta
`asignaciones` por id y no resuelve la académica—, los conteos están fijados por
aserción y los tres caminos de rechazo siguen lanzando. Compuerta con el árbol
tal cual: **1121 passed**, exit 0. **La auditoría encontró además un hallazgo
que no constaba y que no venía de 7.0: lo introdujeron las propias
correcciones.** `profesor_tiene_curso_controller` y
`profesor_tiene_asignacion_en_curso_controller` quedaron **sin consumidor en
producción** desde la reducción de conexiones, que **ya está publicada**, y cada
una **sigue abriendo su propia conexión**. Es el primer hallazgo del programa
**introducido por una corrección** en vez de heredado. **Decisión del usuario:
registrarlo sin retirar nada**, como la capa 6 hizo con su código muerto
duplicado; retirarlo exigiría una orden explícita. Hallazgos de dashboard
abiertos: **ocho** —siete heredados de 7.0 más el undécimo—.

**El hallazgo del promedio, refutado el 2026-08-25 antes de corregirlo.** Al ir
a atacarlo se comprobó que **el diagnóstico de 7.0 está equivocado en su parte
central**, y que corregirlo según ese texto habría sido una **regresión**. Los
rankings filtran **una sola asignatura**, y en ese ámbito promedio de promedios
y promedio plano son **matemáticamente idénticos**, porque el `AVG` exterior
recorre un único grupo y `promedio_clase` no se trunca antes; el **2,50** del
ejemplo **no lo calcula ninguna consulta**, porque exige cruzar asignaturas con
promedio plano y eso no existe; y el promedio de promedios **coincide con el del
boletín** que 7.0 de `notas` registró, así que es el criterio correcto para un
agregado multi-asignatura. **En su lugar se demostraron dos divergencias
reales**: `ROUND(…, 1)` en el expediente frente a `TRUNC(…, 2)` en el dashboard
**para el mismo ámbito** —cuatro ejemplos en los que el estudiante sale
**aprobado en una pantalla y en rojo en la otra**—, y que notas altas y bajas
**no filtran por `periodo`** mientras los rankings sí. **Decisión del usuario:
dejar las dos registradas y sin corregir**, la primera porque cruza a
`estudiantes`, un dominio ya migrado, y porque elegir el redondeo exige antes
**una decisión académica, no técnica**. Ninguna se marca como resuelta. El
recuento pasa a **nueve** hallazgos abiertos: seis heredados intactos, las dos
divergencias nuevas y el undécimo. **No se modificó producto ni pruebas.**

**Cuarta corrección puntual de dashboard, 2026-08-25: `Exception` absorbida y
`str(e)` filtrado al cliente.** Las siete entradas respondían **400 con el texto
de la excepción en el `detail`**, así que **un error de PostgreSQL podía llegar
al navegador**, y además **no se registraba nada**. Ahora responden **500** con
una constante única y registran el fallo con `logger.exception`, que conserva el
traceback. Los demás status codes **no cambian** —el 422 y los dos 403 se lanzan
fuera del `try`—. **El riesgo del cambio de status code se descartó con
evidencia antes de aplicarlo**: se comprobó en el **frontend desplegado** que
**ningún consumidor del dashboard lee `status` ni `detail`** —los cinco hooks
capturan de forma genérica y muestran su propia constante—, así que el cambio es
**invisible** para el cliente. Es la primera vez en el programa que una
corrección se valida contra el repositorio del frontend antes de aplicarse.
**Decisión: no se introdujo una excepción de dominio**, al contrario que en
`tipos_pagos`: allí distinguía infraestructura de errores de negocio, y aquí
dashboard es de solo lectura y **no tiene errores de negocio**, así que la clase
habría tenido un solo uso. **Verificado con una respuesta HTTP real por ASGI**,
la técnica de 7.0 de `notas` y la única que observa un status code de verdad: un
`RuntimeError` con una credencial de PostgreSQL sale como **500** con el cuerpo
genérico y **la credencial no aparece en la respuesta**, mientras el traceback
queda en el log. Compuerta: **1121 pruebas, exit 0**; el diff son **dos
archivos**. Sigue **sin commitear ni publicar**. Recuento: **cuatro** de los diez
hallazgos originales corregidos y **ocho abiertos**.

**Quinta corrección puntual de dashboard, 2026-08-25: la validación consultaba
la base fuera del `try`.** El diagnóstico de 7.0 **quedó obsoleto por partida
doble** y se midió por ASGI antes de corregir: decía un 500 frente a un 400, la
primera mitad murió con la corrección anterior, y la segunda **nunca fue
exacta** —no salía un 500 limpio, sino que **la excepción escapaba del endpoint
sin manejar**, así que el cliente no recibía el `{"detail": …}` del resto de la
API y el fallo no pasaba por el log del módulo—. Ahora la llamada que toca la
base va dentro de un `try` con **`except HTTPException: raise` delante** del
genérico, y los dos caminos producen el mismo 500 con la misma constante.
**Costó una regresión, atrapada en el acto por la caracterización**:
`HTTPException` **también es `Exception`**, y el controlador lanza una 403
propia desde dentro vía `require_asignacion_access`, así que la primera versión
la convertía en 500. Es la demostración de por qué esa validación vivía fuera
del `try`, y quedó fijada por una **guardia parametrizada nueva que falla si
alguien vuelve a ampliarlo**. Verificado por ASGI en **cinco caminos**: los dos
fallos dan 500 y los **tres rechazos legítimos** —403 curso ajeno, 422 sin curso
y 403 asignación ajena— siguen intactos. Compuerta: **1125 pruebas, exit 0**.
**Registrado y fuera de alcance**: `require_profesor_scope` y
`require_asignacion_access` también abren conexión fuera del `try`, pero viven en
`app/core/permissions.py`, **infraestructura compartida por varios dominios**, y
corregirlo exigiría una orden propia. Recuento: **cinco** de los diez hallazgos
originales corregidos y **siete abiertos**.

**Campaña de correcciones de dashboard CERRADA el 2026-08-25**, por orden
explícita del usuario y elegida entre cuatro salidas. **Las cinco correcciones
están publicadas y desplegadas**, comprobado contra el remoto real con
`git ls-remote`: `9f19089`, `1f1ffc9`, `6130ce2`, `bb46761` y `8a72cc8`.
Resolvieron los cinco hallazgos de más peso —el `activo` ausente en los
permisos, las cuatro conexiones en serie, la resolución académica duplicada, la
`Exception` absorbida que filtraba `str(e)` al navegador y la validación fuera
del `try`—. **Los cuatro hallazgos heredados que quedan no son defectos sino
notas**, y así quedó razonado uno a uno: el recorte de `dias` es **inalcanzable
por HTTP**, los literales gemelos son cosméticos y la capa 6 dejó tres parejas
iguales, las f-strings **no son inyectables** y su valor está en seguir escritas
como guarda, y el `periodo: int = 1` es un defecto inalcanzable. Corregirlos
sería una **corrección oportunista sobre código desplegado**, que este índice
prohíbe. Siguen abiertos y **registrados sin corregir por decisión explícita**
las dos divergencias de cifra y el hallazgo 11. **Queda fuera de alcance y
medido** que las guardas de permiso de `app/core/permissions.py` abren conexión
fuera del `try` —**26 usos en 9 archivos de ruta**, transversal a casi toda la
API—, que exigiría su propio alcance y su propia orden. **Staging, verificación
manual y CI de las cinco correcciones siguen pendientes**: se publicaron sin
ellas. Cinco lecciones quedan registradas en la bitácora, entre ellas que **un
hallazgo puede estar mal diagnosticado** —dos lo estaban—, que **una corrección
puede introducir un hallazgo nuevo** —el undécimo—, y que el contrato observable
**se puede verificar contra el repositorio del frontend** antes de cambiarlo.

**Campaña de correcciones de `observaciones` CERRADA el 2026-08-27**, por orden
explícita del usuario. Es la segunda campaña de este tipo, después de la de
`dashboard`, y se cierra con el mismo criterio: se corrige lo que pesa y se
razona por escrito lo que no se corrige. De sus **nueve** hallazgos, **tres
quedaron corregidos y publicados** —las claves foráneas ausentes, aplicadas **a
producción** por migración con ensayo previo en una rama de Neon; el fallo que no
dejaba ninguna traza; y el `UPSERT` que escribía contra asignaciones dadas de
baja—, **uno era obsoleto** porque lo había resuelto la propia 7.1, **dos
quedaron aparcados** con su encuadre rectificado —la longitud del texto y la cota
de `periodo`: son ciertos, pero acotar solo este dominio **crearía** la anomalía
en vez de cerrarla, y el número a elegir es una **decisión académica del colegio,
no técnica**— y **tres se clasificaron como notas**, razonadas una a una: el
`422` frágil **lo cierra su propia prueba**, que falla si alguien mueve la
validación; el `0` que se normaliza a cadena vacía es **inalcanzable desde el
frontend desplegado**, medido ejecutando el esquema y comprobado contra los
`<textarea>` reales; y el `.get` defensivo es cosmético, porque nunca llega a
actuar. **Ninguno queda como trabajo pendiente del dominio.** Los tres commits
—`7d08293`, `289fdd8` y `3439e2f`— están **publicados**, comprobado contra el
remoto real con `git ls-remote`, y la bitácora corrigió su propio registro, que
los daba por no publicados. **Staging, verificación manual y CI de los hallazgos
6 y 7 siguen pendientes.** Queda **fuera de alcance y medido** que las guardas de
`app/core/permissions.py` **no filtran `activo`** para los demás dominios —17
llamadas en 8 archivos de ruta—: `observaciones` se protegió por dentro, y
`dashboard`, `notas` y `boletin` conservan el hueco. Queda también disponible, y
en el repositorio del frontend, poner `maxLength` en los tres `<textarea>` que
hoy no tienen ninguno.

No se crea por anticipado un documento por cada dominio. Cuando una capa se
cierre y el usuario ordene continuar, se crea su sucesora desde
`PLANTILLA_CAPA.md`, se registra el commit base vigente y se actualiza esta
tabla.

Las capas 0 a 6 están cerradas. **La capa 7 quedó cerrada para el dominio
`dashboard`** el 2026-08-19, con sus subcapas 7.0 y 7.1 completas y la
verificación manual hecha. **La capa 7 quedó también cerrada para el dominio
`notas`** el 2026-08-19, el mismo día en que se activó, con sus subcapas 7.0 y
7.1 completas y la verificación manual hecha. **La capa 7 quedó también cerrada
para el dominio `ventas`** el 2026-08-20, el mismo día en que se activó, con sus
subcapas 7.0 y 7.1 completas y la verificación manual hecha. **La capa 7 quedó
activada para el dominio `asistencia`** el 2026-08-20, por orden explícita del
usuario, con su **7.0 pendiente y no iniciada**.

**La capa 7 quedó también cerrada para el dominio `asistencia`** el 2026-08-21,
al día siguiente de activarse, con sus subcapas 7.0 y 7.1 completas y la
verificación manual hecha.

**La capa 7 quedó activada para el dominio `boletin`** el 2026-08-21, por orden
explícita del usuario, y **cerrada el mismo día**, con sus subcapas 7.0 y 7.1
completas y la verificación manual hecha.

**La capa 7 quedó activada para el dominio `observaciones`** el 2026-08-21, por
orden explícita del usuario, y **cerrada el mismo día**, con sus subcapas 7.0 y
7.1 completas y la verificación manual hecha.

**La capa 7 quedó activada para el dominio `planilla`** el 2026-08-21, por orden
explícita del usuario, que nombró el dominio y aceptó continuar localmente con
las verificaciones heredadas pendientes. Su **7.0 quedó cerrada el mismo día**:
cinco archivos y cinco SQL inline, tres entradas HTTP, una tabla escrita, ningún
N+1 y 30 pruebas nuevas. La compuerta terminó con **955 pruebas**. Su 7.1 está
**cerrada**: las cinco sentencias pasaron a un único
`planilla_repository`, con 5 de 5 literales SQL idénticos byte a byte y sin
cambiar parámetros, retornos, conexiones ni transacciones. La compuerta terminó
con **957 pruebas**. El usuario ordenó cerrarla el mismo día: 7.2 quedó **No
aplica**, la compuerta sobre el commit limpio volvió a pasar con 957 pruebas y
la verificación manual propia quedó inicialmente pendiente. El usuario ejecutó
después los ocho puntos solicitados y reportó **todo correcto**; el entorno no
fue especificado.

La capa 7 se cierra **por dominio**, no de una vez: cada uno tiene su propia
bitácora, su propio commit base y su propio cierre, y **las subcapas se numeran
por bitácora**, así que existe una «7.0 de dashboard», cerrada, y una «7.0 de
planilla», también cerrada. En prosa deben citarse siempre con el nombre del dominio. Los
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

**Dominio migrado y cerrado: `notas`.** Lo eligió el usuario el 2026-08-19, tras
pedir que se le explicara qué es un dominio en este programa y qué quedaba en
espera; **no se dedujo por inferencia**. Su bitácora es
[07_NOTAS.md](./07_NOTAS.md) y quedó **cerrada el mismo día**.

**Dominio migrado y cerrado: `ventas`.** Lo eligió el usuario el 2026-08-20, de
la lista de los diez que quedaban en espera y tras recibir las advertencias que
las bitácoras cerradas ya registraban sobre esa lista; **no se dedujo por
inferencia**. Su bitácora es [07_VENTAS.md](./07_VENTAS.md) y quedó **cerrada el
mismo día**.

**Dominio migrado y cerrado: `asistencia`.** Lo eligió el usuario el
2026-08-20, de la lista de los nueve que quedaban en espera y tras recibir las
advertencias que las bitácoras cerradas ya registraban sobre esa lista; **no se
dedujo por inferencia**. Una primera instrucción de «activar otro dominio de la
capa» **no bastó**, porque no nombraba ninguno y habría dejado el alcance
abierto; el trabajo se detuvo hasta que el usuario lo nombró. Su bitácora es
[07_ASISTENCIA.md](./07_ASISTENCIA.md); sus subcapas **7.0 y 7.1 quedaron
cerradas el mismo día** y la capa quedó **cerrada al día siguiente**.

**Dominio migrado y cerrado: `boletin`.** Lo eligió el usuario el
2026-08-21, de la lista de los ocho que quedaban en espera y **nombrándolo
explícitamente** en la misma orden que autorizó corregir el estado de
publicación de `asistencia`; **no se dedujo por inferencia**. Recibió antes la
advertencia, que las bitácoras cerradas ya registraban y que el turno de
activación le repitió, de que **`boletin` no es una frontera limpia**: `notas`
posee ya las rutas `/boletin/{id}` y `/boletin/detallado/{id}`, como fijó su
7.0. Eligió `boletin` sabiéndolo. Su bitácora es
[07_BOLETIN.md](./07_BOLETIN.md) y quedó **cerrada el mismo día**.

**Dominio migrado y cerrado: `observaciones`.** Lo eligió el usuario el
2026-08-21, de la lista de los siete que quedaban en espera y **nombrándolo
explícitamente**; **no se dedujo por inferencia**. Su bitácora es
[07_OBSERVACIONES.md](./07_OBSERVACIONES.md) y quedó **cerrada el mismo día**.

**Dominio migrado y cerrado: `planilla`.** Lo eligió el usuario el 2026-08-21,
de la lista de los seis que quedaban en espera, y lo **nombró explícitamente** al aceptar
continuar localmente con las verificaciones pendientes. Su bitácora es
[07_PLANILLA.md](./07_PLANILLA.md); sus **7.0 y 7.1 están cerradas**, 7.2 es No
aplica y la capa quedó cerrada por orden explícita. Su verificación manual quedó
**completada y correcta**, con 8 de 8 puntos reportados por el usuario y entorno
no especificado.

**Dominio migrado y cerrado: `planeador_anual`.** El usuario lo eligió y nombró
explícitamente el 2026-08-21, aceptando continuar localmente con las
verificaciones heredadas pendientes. Su bitácora es
[07_PLANEADOR_ANUAL.md](./07_PLANEADOR_ANUAL.md); su **7.0 está cerrada**: tres
archivos propios, dos entradas HTTP, cinco SQL inline, una tabla escrita y 29
pruebas nuevas. El `GET` es constante y el `PUT` ejecuta `1+N` operaciones
como admin y `2+N` como profesor, con conexiones constantes. La compuerta
de 7.0 terminó con **986 pruebas**. Su **7.1 quedó cerrada** el 2026-08-22: las cinco sentencias pasaron al
decimotercer repositorio, con 5 de 5 literales SQL idénticos byte a byte y sin
mover conexiones, cursores ni transacciones. Las siete guardias que fallaron
eran la señal esperada —dos propias y cinco enumeraciones históricas—. La
compuerta terminó con **987 pruebas**. Al terminar 7.1 quedó pendiente decidir
explícitamente entre cerrar la capa como refactorización pura o autorizar una
7.2 concreta.
El usuario ordenó cerrarla el 2026-08-22: 7.2 quedó **No aplica**, la compuerta
sobre el commit limpio volvió a pasar con **987 pruebas** y la verificación
manual propia quedó inicialmente pendiente. El usuario informó después
«planeador revisado» y ordenó seguir con `plan_de_clases`; se registra como
verificación manual **completada de forma global**, sin entorno ni desglose de
los siete puntos reportados.

**Dominio migrado y cerrado: `plan_de_clases`.** El usuario lo nombró
explícitamente el 2026-08-22 después de reportar revisado `planeador_anual`.
Su bitácora es
[07_PLAN_DE_CLASES.md](./07_PLAN_DE_CLASES.md); la activación fue únicamente
documental y su **7.0 quedó cerrada el mismo día** sin modificar producto:
delimitó cinco archivos propios, once entradas propias más el endpoint
compartido `/uploads`, tres tablas, 25 sitios `cursor.execute` dentro del
repositorio y dos consultas específicas externas. Agregó 22 pruebas; las
específicas terminaron con **127 passed** y la compuerta con **1009 passed**,
Ruff correcto y dependencias íntegras. Su **7.1 quedó cerrada el mismo día**:
las dos consultas externas pasaron al repositorio existente como operaciones
que reciben cursor; `permissions.py` y `main.py` conservaron conexión, cursor,
cierre, permisos y retornos. Los dos SQL y parámetros quedaron fijados
exactamente. La caracterización subió a 24 casos, las específicas terminaron
con **129 passed** y la compuerta con **1011 passed**. De los doce hallazgos, el
primero está resuelto y once siguen vivos. Al terminar 7.1 quedó pendiente
decidir entre cerrar la capa como refactorización pura o autorizar una 7.2
concreta. El usuario ordenó cerrarla y reanudó el cierre después de consolidar
7.1: 7.2 y 7.3
quedaron **No aplica**. La compuerta sobre el commit limpio volvió a pasar con
**1011 pruebas**, Ruff correcto y dependencias íntegras. El usuario informó
después que ya verificó y que está «aparentemente bien»; la verificación manual
propia queda completada de forma global con esa reserva, sin entorno, artefacto
ni desglose punto por punto. No se comprobó publicación.

**Dominio migrado y cerrado: `branding`.** El usuario lo nombró, ordenó
activarlo y confirmó continuar localmente aceptando que las verificaciones
heredadas permanezcan pendientes. Su bitácora es
[07_BRANDING.md](./07_BRANDING.md); la
activación fue exclusivamente documental y su **7.0 quedó cerrada el mismo
día** sin modificar producto: delimitó tres archivos propios, cuatro rutas más
`/uploads`, una tabla, siete SQL inline, escrituras DB/storage y ningún N+1 de
aplicación. Conservó las 31 pruebas heredadas y agregó 19; las específicas
terminaron con **50 passed** y la compuerta con **1030 passed**, Ruff correcto
y dependencias íntegras. Registró trece hallazgos sin corregir. Su **7.1 quedó
cerrada**: los siete usos SQL se extrajeron a seis operaciones de un repositorio
sin recursos, con SQL y parámetros literales protegidos. Las específicas
terminaron con **52 passed** y la compuerta con **1032 passed**. Al terminar
7.1, 7.2 quedó pendiente y no iniciada; el usuario ordenó después cerrar como
refactorización pura, por lo que 7.2 y 7.3 quedaron **No aplica**. La compuerta
de cierre sobre el commit limpio volvió a pasar con **1032 pruebas**, Ruff correcto y
dependencias íntegras. Staging y rollback están documentados; la verificación
manual propia permanece pendiente y no se comprobó publicación.

**Dominio migrado y cerrado: `profesores`.** El usuario escribió «activa el dominio
proefesores» el 2026-08-23, después de recibir la decisión entre completar la
verificación manual pendiente de `branding` o continuar localmente aceptándola.
La errata inequívoca se registró como `profesores`; la activación es únicamente
documental y usa como base el `HEAD` limpio `58eb5c2`. Su **7.0 quedó cerrada
el 2026-08-23** sin modificar producto: delimitó tres archivos propios, cuatro
rutas admin y dos rutas externas de asignaciones bajo el mismo prefijo; contó
diez sitios SQL inline —nueve alcanzables y uno en una función sin
consumidores—, una tabla escrita y ningún N+1. Agregó 27 pruebas; las
específicas terminaron con **45 passed** y la compuerta con **1059 passed**,
Ruff correcto y dependencias íntegras. Registró doce hallazgos sin corregir.
Su **7.1 quedó cerrada el mismo día**: nueve sitios SQL alcanzables pasaron a
`profesores_repository`, cuyas nueve operaciones reciben el cursor y no
administran recursos; la consulta de clases sin consumidores quedó inline. El
comparador AST confirmó los diez argumentos SQL idénticos antes y después. La
caracterización subió a 29 casos, las específicas terminaron con **47 passed**
y la compuerta con **1061 passed**, Ruff correcto y dependencias íntegras. El
usuario ordenó cerrarlo como refactorización pura: 7.2 y 7.3 son **No aplica**
y la compuerta sobre el commit limpio volvió a pasar con **1061 pruebas**. El
staging y rollback están documentados; la verificación manual propia permanece
pendiente y no se comprobó publicación. La bitácora es
[07_PROFESORES.md](./07_PROFESORES.md).

**Dominio migrado y cerrado: `super_admin`.** El usuario escribió «sigue super admin» el
2026-08-23, después de recibir el cierre de `profesores`, el aviso de que su
verificación manual permanece pendiente y la indicación de que `super_admin`
seguía en espera. La orden nombra el dominio y autoriza continuar localmente
aceptando ese pendiente. La activación es exclusivamente documental, usa como
base el `HEAD` limpio `2ec924a`. Su 7.0 delimitó 20 sitios SQL propios —18 en
el controlador y 2 en autenticación—, agregó 27 casos de caracterización sin
modificar producto y cerró con 88 pruebas específicas y una compuerta global
de 1088 pruebas. Su 7.1 extrajo los cinco sitios de listar, auditar y cambiar
estado a `super_admin_repository`, con 5 de 5 SQL idénticos byte a byte; cerró
con 89 pruebas específicas y una compuerta global de 1089 pruebas. Su 7.2
extrajo las dos consultas de autenticación y revalidación al mismo repositorio,
con 2 de 2 SQL idénticos byte a byte, núcleo todavía dueño de seguridad y
recursos, 89 pruebas específicas y 1089 globales. Su 7.3 extrajo las 13
operaciones del provisionamiento, con 13 de 13 secuencias de SQL y parámetros
exactas, y cerró con 89 pruebas específicas y una compuerta de 1089 pruebas.
Staging y rollback están documentados; la verificación manual queda pendiente.
La bitácora es
[07_SUPER_ADMIN.md](./07_SUPER_ADMIN.md).

No hay una capa activa ni otro dominio enumerado en espera. Cualquier trabajo
posterior exige una orden explícita y no se inicia por inferencia.

La advertencia de perfil que se registró al activar `notas` **quedó confirmada**:
a diferencia de `dashboard`, que resultó de solo lectura, **`notas` escribe**, y
su perfil de riesgo es el de la capa 5. Aun así la capa **no tocó la base de
datos**, ni siquiera para leer, así que su rollback es de código —por el método
empleado, no por la naturaleza del dominio—.

**Cambio fuera del programa, 2026-08-27: endpoint de salud.** Con orden
explícita del usuario se agregó `GET /health` para monitoreo externo. **No es
una subcapa y no reabre ninguna capa cerrada**: el programa prohíbe agregar
funciones dentro de una capa, así que este trabajo queda registrado aquí solo
para que un asistente posterior no lo lea como divergencia sin explicar al
comparar `HEAD` contra el commit base. Su documentación viva está en
`docs/CAMBIOS_BACKEND.md`, `docs/API_ENDPOINTS.md`,
`docs/ARQUITECTURA_BACKEND.md` y `docs/PRODUCCION_BACKEND.md`, no en una
bitácora de capa.

Alcance real: tres archivos nuevos —`app/core/health.py`, `app/routes/health.py`
y `tests/test_health.py`— y tres líneas en `app/main.py` para importar y
registrar el router. **No se modificó ningún endpoint existente**, ni permisos,
ni SQL, ni tenant, ni migraciones. Compuerta global con el árbol tal cual:
**1141 pruebas correctas**, Ruff correcto, `pip check` correcto y
`git diff --check` limpio. Sin PostgreSQL real, sin commit, sin push y sin
despliegue: la verificación contra la base y el alta del monitor externo quedan
bajo control del usuario.

La revisión que originó el cambio dejó además **un hallazgo registrado y no
corregido**: `default_limits=["100/minute"]` en `app/main.py` es inerte porque
`slowapi` solo lo aplica con `SlowAPIMiddleware`, que la app no monta. Hoy solo
`POST /login` y `GET /health` están limitados de verdad. Corregirlo cambiaría el
comportamiento observable de los 139 endpoints, así que exige una orden
explícita y su propio alcance.

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
  iniciado—; siete funciones de tipos de pago absorbían `Exception` y presentaban
  un fallo de infraestructura como 400 o 404 —el 2026-08-17 se añadió el
  traceback y el 2026-08-24 se completó localmente el mapeo seguro a 500 tras
  revisar el frontend; staging y publicación siguen pendientes—; y los dos
  upsert de tipos de pago abrían **dos
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
- **Auditoría heredada completada el 2026-08-24**: al quitar el anidamiento de
  conexiones de los dos upsert, la constante
  `MAX_DB_CONNECTIONS_PER_THREADPOOL_WORKER = 2` de la capa 2 —de donde salen los
  5 workers para el pool de 10— se quedó sin un ejemplo real. La revisión
  intermodular acotada no detectó `H>1`, pero tampoco demuestra que el `H=1`
  candidato sea una cota operativa. **La constante no se tocó**: el modelo
  conserva `R=0` formal y cinco tokens; si el `H` real fuera 1, la diferencia
  sería margen implícito. Elevar capacidad requeriría una decisión propia,
  instrumentación, reserva explícita y carga en staging.
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
  evidencia del coste secuencial que faltaba, pero **no** prueba dos leases
  simultáneos por worker. Se registró **sin actuar**; la auditoría específica
  posterior no detectó `H>1`, sin convertir `H=1` en cota operativa demostrada.
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
  activar la capa a 756. Cerrarla no canceló los diez hallazgos originales. El
  primero —el `activo` ausente de las dos precondiciones— quedó corregido
  localmente el 2026-08-25 con orden explícita; **nueve siguen abiertos**.
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
- Resultado de 7.1 de `notas`: las **9 sentencias** salieron a
  `app/repositories/notas_repository.py`, **nueve funciones** que reciben el
  cursor existente y **el séptimo repositorio** del proyecto.
  `notas_controller.py` pasó de **273 a 170 líneas** y de 6 sentencias inline a
  **0**; `nota_service.py` de **46 a 31** y de 3 a **0**; la ruta ya tenía 0. El
  comparador AST contra el commit base confirmó **9 literales SQL distintos
  antes y después, conjunto idéntico**, con **9 de 9 byte a byte**: **no hizo
  falta autorizar ningún cambio de texto SQL**. Compuerta local: **791
  pruebas**, Ruff y dependencias correctas.
- **Las tres guardias de línea base que 7.0 dejó puestas fallaron al extraer**,
  que era la señal esperada —lección 14 de la capa 6, aplicada por tercera vez—,
  y solo esas tres: las otras **49 pruebas pasaron sin cambiar de expectativa**,
  incluidos los diez conteos de consultas y conexiones y las cinco de contrato
  HTTP. Se sustituyeron por cuatro versiones positivas.
- Decisión de 7.1, tomada con evidencia y **sin precedente exacto en el
  programa**: las tres consultas de `nota_service` **sí van al repositorio**,
  porque dejarlas fuera habría cerrado la frontera solo en dos tercios; y van al
  de `notas` y **no** a `asignaciones_repository` ni `estudiantes_repository`,
  porque `buscar_asignacion` **no filtra por `activo`** y sus vecinas allí sí, y
  porque una de las tres **cruza ambas tablas**. Es el criterio que 7.1 de
  dashboard fijó. **`nota_service` conserva la propiedad de sus tres
  conexiones**: unificarlas bajaría `POST /notas` de 4 conexiones a 1, que es
  una mejora real pero **cambiaría los conteos fijados por aserción** y queda
  como trabajo disponible. Es la **primera vez en el programa que el dueño del
  cursor no es un controlador**.
- **Consecuencia fuera del dominio, materializada en 7.1**: una guardia de
  `test_dashboard_caracterizacion.py` que enumera el conjunto **exacto** de
  repositorios falló al aparecer el séptimo. **No era una rotura de contrato**;
  se actualizó conservando su severidad, porque esa severidad es deliberada y
  obliga a reconocer cada migración nueva. Lo detectó **la compuerta global, no
  las pruebas de `notas`**, que es exactamente el riesgo que 7.0 había
  registrado.
- **Decisión del usuario el 2026-08-19: cerrar la capa aquí**, sin abrir 7.2. La
  tomó tras preguntar expresamente si cerrar así «daña algo» y recibir el
  detalle de qué conserva el cierre y qué no cura. El punto de decisión tenía
  **tres salidas y no dos**, a diferencia de dashboard, porque el contrato de la
  escritura estaba en juego: declarar un `response_model` para `POST /notas`
  habría obligado a decidir si el contrato es el `id` anidado o el entero, y
  convertir sus validaciones en errores de dominio **habría cambiado el 200 por
  un 4xx**. `response_model` y los errores de dominio **no se añaden** y **no
  quedan como deuda de esta capa**: pasan a ser trabajo disponible que exigiría
  una orden explícita.
- **Verificación manual de la capa 7 para `notas`: hecha por el usuario y
  correcta**, el 2026-08-19, **en local** y con cobertura completa del guion
  —viaje de ida y vuelta de la escritura, aritmética del promedio, las cuatro
  pantallas de lectura, permisos por rol y los dos tenants—. El artefacto se
  confirmó **antes** de registrarla: árbol limpio y `HEAD` en `ade4c10`, el
  commit de 7.1, que contiene exactamente los siete archivos de la subcapa.
  Pesaba más que en dashboard porque **este dominio escribe**: un fallo de la
  extracción no habría dado cifras raras sino **una calificación no guardada**.
- Capa 7 **cerrada para `notas`** el 2026-08-19, el mismo día en que se activó.
  Compuerta de cierre: **exit 0 con 791 pruebas**, Ruff correcto y `pip check`
  íntegro. La suite pasó de 756 al activar la capa a 791. Cerrarla **no cancela
  los doce hallazgos de 7.0**, que siguen vivos, empezando por el falso éxito de
  `POST /notas`.
- **Estado de publicación de la capa 7 para `notas`: NO publicada.**
  `origin/main` sigue en el commit base `eee8aec` y hay **tres commits locales
  por delante** —`a56d55f`, `a8bcf0a` y `ade4c10`—. **Producción no corre este
  código.** Es una diferencia real con las capas 5, 6 y 7 de dashboard, que
  estaban publicadas al cerrarse o poco después, y tiene una consecuencia
  favorable: mientras siga así, **el rollback es una operación puramente local**
  y no exige push ni despliegue. La publicación la decide y la ejecuta el
  usuario.
- **La capa 7 para `notas` no tocó la base de datos**, ni siquiera para leer. Es
  la cuarta consecutiva que no abre una conexión a PostgreSQL, y **la primera de
  esas cuatro cuyo dominio sí escribe**: la propiedad viene del método empleado,
  no de la naturaleza del dominio.
- Al cerrar `notas` el 2026-08-19 la capa activa pasó a ser **ninguna**, y el
  siguiente paso quedó como «otro dominio de la capa 7, sin elegir». **El
  2026-08-20 el usuario eligió `ventas`**, así que ese renglón ya no describe el
  estado vigente; se conserva porque era cierto entonces.
- **Estado de publicación de la capa 7 para `notas`, corregido el 2026-08-20:
  SÍ está publicada.** El reflog de `origin/main` registra `update by push` de
  `58c5233`, el commit de cierre, que arrastra los **cuatro** commits de la capa
  —`a56d55f`, `a8bcf0a`, `ade4c10` y `58c5233`—; `git ls-remote origin main` lo
  confirma contra el remoto real y `HEAD` coincide. **Producción ya corre el
  código de `notas`** y el rollback a `eee8aec` **ya no es una operación local**:
  exigiría otro push y otro despliegue. Las líneas de más arriba y las de
  `07_NOTAS.md` que lo declaran «no publicada» eran ciertas el 2026-08-19 y
  **se conservan intactas**; esta es la línea que registra el cambio. **La
  bitácora de `notas` no se editó**: corregir una capa cerrada es ajeno a una
  activación y exige una orden explícita, así que allí queda anotado como
  residuo abierto.
- Capa 7 **activada para el dominio `ventas`** el 2026-08-20 por orden explícita
  del usuario, **y solo ese dominio**. Commit base:
  `58c5233afc4772ba040da690f4d719b518bb1b0a`, el `HEAD` limpio vigente en `main`
  y coincidente con la referencia local `origin/main` y con el remoto real, que
  el reflog registra como publicada por push. Los **cuatro** commits posteriores
  al base de `notas` fueron auditados y **todos están explicados** en
  `07_NOTAS.md`; el cuarto es su propio commit de cierre, que la bitácora no
  podía registrar sobre sí misma y que se verificó con `git show --stat`: toca
  exactamente dos archivos de documentación y ningún código. La activación es
  únicamente documental: no inspeccionó ni modificó código, pruebas, consultas,
  configuración o base de datos. **No se abrió ningún archivo de `ventas`**, ni
  siquiera el listado de nombres de archivo: la lista de dominios en espera se
  tomó de `07_NOTAS.md`.
- **El dominio lo eligió el usuario, no se dedujo**, igual que con `dashboard` y
  `notas`. Se le presentaron los diez en espera con tres advertencias tomadas de
  las bitácoras cerradas: que `boletin` y `planilla` **no son fronteras limpias**
  porque `notas` ya posee esas rutas; que `ventas` es el **único con un
  aplazamiento documentado**, el de la capa 5; y que `branding` y `super_admin`
  cambian el perfil de riesgo, el primero por `storage.py` y el segundo por ser
  territorio de la capa 3. Eligió `ventas`.
- Decisión al activar la capa 7 para `ventas`: continuar aceptando que sigan
  pendientes la calibración operativa final de `DB_STATEMENT_TIMEOUT_MS` y la
  evidencia de GitHub Actions posterior a la capa 0. Se preguntó explícitamente
  antes de escribir nada, ofreciendo también intentar cerrar la de CI —que hoy
  sí sería obtenible, porque existe un push reciente sobre `main`—; el usuario
  eligió continuar. Ninguna se marca como cumplida y ambas conservan su riesgo.
  La credencial privilegiada compartida en la capa 4 sigue **sin rotar**.
  Pendientes también, y fuera de esta capa salvo orden explícita: la clave de
  idempotencia de `POST /pagos` (paso 2), los status codes 500 de
  `tipos_pagos_controller`, la auditoría de capacidad de la capa 2, la ausencia
  de lock en el alta y la edición de asignaciones, **los diez hallazgos de
  dashboard** y **los doce de notas**, empezando por el falso éxito de
  `POST /notas`.
- **`ventas` es el primer dominio de la capa 7 que llega con frontera ajena ya
  construida.** La capa 5 decidió con evidencia que las **cinco sentencias** que
  tocan esa tabla vivieran en `pagos_repository.py`, en un bloque rotulado como
  «el efecto de un pago sobre un cargo», y aplazó expresamente migrar
  `venta_controller`. Ese aplazamiento es lo que esta capa recoge, y trae el
  **punto de decisión propio** de la bitácora: si aparece un `ventas_repository`,
  hay que decidir **con evidencia** si esas cinco sentencias se quedan o se
  mueven. **Mover código de `pagos_repository` no está autorizado** por la
  activación: exigiría una orden explícita posterior a la evidencia de 7.0.
- **Nada de lo que la bitácora de `ventas` dice de ese dominio está
  verificado.** La activación no inspeccionó su código: registra **doce
  supuestos heredados**, once marcados como no verificados y uno verificado solo
  documentalmente. El que manda vuelve a ser **si el dominio escribe**: 5.0 contó
  `ventas` entre las seis tablas escritas **del dominio de pagos**, lo que
  demuestra que la tabla se escribe pero **no** que la escriba este dominio. Su
  7.0 debe separar las dos cosas. Es la lección 12 de la capa 6, que ya sirvió
  tres veces.
- Resultado de 7.0 de `ventas`: el dominio quedó inventariado en **2 archivos**
  —el recuento sale al revés que en `notas`, donde eran cuatro y no dos—, **5
  entradas HTTP**, **cuatro tablas escritas** —`ventas`, `ventas_detalle`,
  `inventario` y **`pagos`**—, **dos transacciones propias** y **17 sentencias
  SQL inline**, todas en el controlador y 0 en la ruta, protegido por **41
  pruebas nuevas**. La compuerta local terminó con **832 pruebas**, Ruff y
  dependencias correctas. No se modificó producto: el diff es un solo archivo
  nuevo.
- **Los doce supuestos que la activación registró quedaron resueltos en 7.0**:
  once confirmados y **uno refutado**. El refutado es el de los permisos, y era
  el único marcado como **inferencia de patrón** y no como resto de otra capa:
  las **cinco entradas usan un solo modelo**, `get_current_active_admin`, admin
  estricto. **Es el primer dominio del programa con permisos uniformes**, frente
  a los cuatro modelos de dashboard y los dos de notas.
- **No hay N+1 en `ventas`** y **todos sus caminos abren una sola conexión**,
  frente a las cuatro de dashboard y las cuatro o cinco de notas. Los dos
  conteos variables dependen del tamaño del carrito, no del número de
  estudiantes. Es el dominio más barato que ha medido el programa.
- **El hallazgo estructural de 7.0**: `anular_venta` **escribe `pagos` con SQL
  inline**, aunque la capa 5 diera esa frontera por cerrada y `pagos_repository`
  exista desde entonces. El controlador ni siquiera lo importa. Dónde vive ese
  `UPDATE` es la decisión difícil de 7.1, y llevarlo al repositorio de pagos
  **ampliaría el diff a un módulo cerrado** y exige orden explícita.
- **El hallazgo más grave de 7.0, y es dinero**: anular una venta alcanza los
  pagos por `descripcion ILIKE '%Cargo #N%'`, **sin delimitar el número**, así
  que **anular la venta 4 marca como anulados los pagos de la venta 40**. El
  mismo patrón tiene el defecto simétrico: **no reconoce** la otra descripción
  que el propio dominio fabrica, «Cargo de Inventario #N», que solo se alcanza
  por `venta_id`. Está activo en producción y es **anterior a esta capa**.
- Hallazgos de 7.0 de `ventas`, **registrados y sin corregir**: son **once**.
  Además de los dos anteriores, `eliminar_venta` es **código muerto que borra
  físicamente** mientras su propia ruta responde 405 diciendo que las ventas no
  se eliminan; `obtener_ventas()` **no tiene `LIMIT`**; el **`total` lo fija el
  cliente** y no se compara con la suma de subtotales; el dinero se maneja con
  **`float` de Python** y nunca `Decimal`; no se comprueba que el estudiante
  exista; y los **esquemas Pydantic viven dentro de la ruta**, único caso del
  programa.
- **Lo que 7.0 buscó expresamente y no encontró**: el patrón del falso éxito de
  `POST /notas` **no está aquí**. Medido por ASGI, `POST /api/ventas/` responde
  **400** ante una validación fallida y su campo `id` es **un entero plano**,
  no un diccionario. Este dominio sí usa el mecanismo de error de FastAPI.
- Resultado de 7.1 de `ventas`: las **17 sentencias** salieron del controlador a
  `app/repositories/ventas_repository.py`, **17 funciones** que reciben el
  cursor existente y **el octavo repositorio** del proyecto.
  `venta_controller.py` pasó de **363 a 278 líneas** y de 17 sentencias inline a
  **0**; la ruta ya tenía 0. El comparador AST contra el commit base confirmó
  **17 literales SQL distintos antes y después, conjunto idéntico**, con **17 de
  17 byte a byte**: **no hizo falta autorizar ningún cambio de texto SQL**.
  Compuerta local: **835 pruebas**, Ruff y dependencias correctas.
- **Fallaron seis pruebas al extraer y las seis eran previsibles**, que era la
  señal esperada —lección 14 de la capa 6, aplicada por cuarta vez—: las **dos**
  guardias de línea base declaradas, **dos pruebas de hallazgo que también
  estaban ancladas al controlador** sin estar rotuladas como guardias, y las
  **dos** enumeraciones de repositorios de dashboard y notas. Las otras **37
  pruebas del dominio pasaron sin cambiar de expectativa**, incluidos los ocho
  conteos de consultas y conexiones y las cinco de contrato HTTP real.
- **Lección nueva de 7.1, que corrige lo que la propia bitácora había previsto**:
  anunciaba dos fallos dentro del dominio y fueron cuatro, porque **una prueba
  de hallazgo anclada a un archivo concreto es también una guardia de línea
  base**, aunque no se rotule así. Las dos se reapuntaron al repositorio
  conservando exactamente lo que denuncian.
- **Consecuencia fuera del dominio, por segunda vez en el programa**: las dos
  guardias que enumeran el conjunto **exacto** de repositorios fallaron al
  aparecer el octavo. **No era una rotura de contrato**; se actualizaron
  conservando su severidad, que es deliberada. Lo detectó **la compuerta global,
  no las pruebas de `ventas`**. En 7.1 de notas ocurrió con una sola guardia;
  ahora son dos, porque notas añadió la suya.
- Decisión de 7.1, tomada con evidencia: el **`UPDATE pagos`** vive en
  `ventas_repository` y **no** en `pagos_repository`, en un bloque rotulado como
  «el efecto de anular una venta sobre sus pagos». Es **simetría exacta** con lo
  que la capa 5 dejó escrito al revés —un bloque en `pagos_repository` con cinco
  sentencias sobre `ventas`—; llevarlo allí ampliaría el diff a un módulo que
  esa capa cerró y obligaría al controlador de ventas a importarlo, creando una
  dependencia entre dominios que 7.1 no está autorizada a introducir. La
  alternativa **no queda cerrada**: sigue siendo defendible y exigiría orden
  explícita. El bloque lleva una advertencia en el propio código sobre el
  `ILIKE` sin delimitar, para que nadie lo «arregle» por vecindad.
- **Verificación manual de la capa 7 para `ventas`: hecha por el usuario y
  correcta**, el 2026-08-20, en local. El artefacto se confirmó **antes** de
  registrarla y **sin ambigüedad**: árbol limpio y `HEAD` en `8948e40`, con el
  código de 7.1 en `76f76e7`, que es ancestro. **Cobertura registrada sin
  inflarla**: el usuario la reportó **de forma global** y **no punto por punto
  contra los once pasos** del guion, así que **no consta** el retorno exacto del
  stock tras anular con abono parcial, la prueba cruzada de importes contra el
  expediente y la cartera, ni el aislamiento entre los dos tenants. Es evidencia
  **más débil** que la de `notas`, cuya respuesta sí se dio sobre un guion
  explícito. Lo que sí respalda la capa es la evidencia automática, que aquí es
  la más fuerte del programa.
- **Evidencia nueva que esta capa aporta al programa entero**: el comparador AST
  que usaron las capas 4 a 7 compara **texto SQL pero no parámetros**, así que
  un intercambio de argumentos al extraer **no se detectaría**. 7.1 cerró ese
  hueco ejecutando el controlador del commit base y el actual con las mismas
  entradas: **los seis caminos emiten la misma secuencia de `(SQL, parámetros)` y
  devuelven lo mismo**. Es una comprobación de un solo uso; fijarla como prueba
  permanente queda como trabajo disponible. **Las extracciones anteriores no
  tienen esa evidencia.**
- **Estado de publicación de la capa 7 para `ventas`: NO publicada.**
  `origin/main` sigue en el commit base `58c5233` y hay **cuatro commits
  locales** por delante, más el del cierre. **Producción no corre este código**,
  así que mientras siga así el rollback es **puramente local**. Es la misma
  situación en que quedó `notas` al cerrarse, y allí duró un día.
- **Estado de publicación de la capa 7 para `ventas`, corregido el 2026-08-20:
  SÍ está publicada.** El reflog de `origin/main` registra `update by push` de
  `a894441`, el commit de cierre, que arrastra los **cinco** commits de la capa
  —`040b027`, `2fbe83f`, `76f76e7`, `8948e40` y `a894441`—; el push quedó
  registrado a las **16:21:16 -0500**, diez segundos después de crearse el
  commit. `git ls-remote origin main` lo confirma contra el remoto real y `HEAD`
  coincide. **Producción ya corre el código de `ventas`** y el rollback a
  `58c5233` **ya no es una operación local**: exigiría otro push y otro
  despliegue. La verificación manual del usuario fue **en local y anterior al
  push**, así que nadie ha ejercitado este código **ya desplegado**, y es el
  dominio financiero. La línea de más arriba y las de `07_VENTAS.md` que lo
  declaran «no publicada» eran ciertas cuando se escribieron y **se conservan
  intactas**; esta es la línea que registra el cambio. **La bitácora de `ventas`
  no se editó**: corregir una capa cerrada exige una orden propia, así que allí
  queda como residuo abierto. Es el **segundo desfase consecutivo** de este
  tipo, después del de `notas`.
- **Decisión del usuario el 2026-08-20: cerrar la capa aquí**, sin abrir 7.2. Se
  le ofrecieron **cuatro** salidas —cerrar, una 7.2 con los errores de dominio,
  una 7.2 que moviera el `UPDATE pagos`, o completar antes los tres pasos del
  guion que no constan— y eligió cerrar. El `UPDATE pagos` **se queda** en
  `ventas_repository`; `response_model` y los errores de dominio **no se
  añaden** y **no quedan como deuda de esta capa**: pasan a ser trabajo
  disponible que exigiría una orden explícita. Los **tres pasos del guion que no
  constan siguen sin constar** y no se marcan como cumplidos.
- Capa 7 **cerrada para `ventas`** el 2026-08-20, el mismo día en que se activó.
  Compuerta de cierre: **exit 0 con 835 pruebas**, Ruff correcto y `pip check`
  íntegro. La suite pasó de 791 al activar la capa a 835. Cerrarla **no cancela
  los once hallazgos de 7.0**, que siguen vivos, empezando por la colisión del
  `ILIKE` que hace que anular una venta alcance los pagos de otra.
- **La capa 7 para `ventas` no tocó la base de datos**, ni siquiera para leer.
  Es la **quinta consecutiva** que no abre una conexión a PostgreSQL, y la
  **segunda de esas cinco cuyo dominio sí escribe**.
- Al cerrar `ventas` el 2026-08-20 la capa activa pasó a ser **ninguna**, y el
  siguiente paso quedó como «otro dominio de la capa 7, sin elegir», con
  **nueve** en espera. **El mismo 2026-08-20 el usuario eligió `asistencia`**,
  así que ese renglón ya no describe el estado vigente; se conserva porque era
  cierto entonces.
- Capa 7 **activada para el dominio `asistencia`** el 2026-08-20 por orden
  explícita del usuario, **y solo ese dominio**. Commit base:
  `a894441f8676b0486e3395f88179cdf6cba61430`, el `HEAD` limpio vigente en `main`
  y coincidente con la referencia local `origin/main` y con el remoto real, que
  el reflog registra como publicada por push. Los **cinco** commits posteriores
  al base de `ventas` fueron auditados: cuatro están explicados en
  `07_VENTAS.md` y el quinto es su propio commit de cierre, que la bitácora no
  podía registrar sobre sí misma y que se verificó con `git show --stat`: toca
  exactamente dos archivos de documentación y ningún código. La activación es
  únicamente documental: no inspeccionó ni modificó código, pruebas, consultas,
  configuración o base de datos. **No se abrió ningún archivo de `asistencia`**,
  ni siquiera el listado de nombres de archivo.
- **El dominio lo eligió el usuario, no se dedujo**, igual que con `dashboard`,
  `notas` y `ventas`. Con una diferencia que conviene registrar: la primera
  instrucción fue **«activar otro dominio de la capa»**, que **no nombra
  ninguno**. Se rechazó y el trabajo se detuvo, porque activar sobre esa orden
  habría dejado el alcance abierto, que es justo lo que la capa 7 prohíbe; es el
  mismo punto en que se detuvo la activación de `dashboard` cuando el marcador
  `DOMINIO` llegó sin rellenar. El usuario nombró después `asistencia`, de los
  nueve en espera y tras recibir las advertencias registradas: que `boletin` y
  `planilla` **no son fronteras limpias** porque `notas` ya posee esas rutas;
  que `branding` y `super_admin` cambian el perfil de riesgo; y que
  `plan_de_clases` **ya tiene repositorio propio**.
- Decisión al activar la capa 7 para `asistencia`: continuar aceptando que sigan
  pendientes la calibración operativa final de `DB_STATEMENT_TIMEOUT_MS` y la
  evidencia de GitHub Actions posterior a la capa 0. Se preguntó explícitamente
  antes de escribir nada, ofreciendo cuatro salidas —continuar, cerrar la de CI,
  completar los tres pasos del guion de `ventas` o calibrar el timeout—; el
  usuario eligió continuar. Ninguna se marca como cumplida y todas conservan su
  riesgo. La credencial privilegiada compartida en la capa 4 sigue **sin rotar**.
  Pendientes también, y fuera de esta capa salvo orden explícita: la clave de
  idempotencia de `POST /pagos` (paso 2), los status codes 500 de
  `tipos_pagos_controller`, la auditoría de capacidad de la capa 2, la ausencia
  de lock en el alta y la edición de asignaciones, **los diez hallazgos de
  dashboard**, **los doce de notas** y **los once de ventas**, y los **tres
  pasos del guion de `ventas`** que no constan.
- **`asistencia` es el primer dominio de la capa 7 que llega con trabajo previo
  de otra capa**, y por partida doble. Trae **pruebas ya escritas** —las 5 de
  `tests/test_asistencia_historial.py` que dejó 1.4g, más
  `test_asistencia_validaciones.py`—, cosa que no tuvo ninguno de los tres
  anteriores, y llega **parcialmente migrado**: 1.4g pasó
  `obtener_historial_asistencia` a `get_cursor()` y **no tocó**
  `guardar_asistencia_controller`, así que el dominio tiene **dos idiomas de
  conexión conviviendo**. Ninguna de las dos cosas adelanta trabajo por sí sola:
  las pruebas se escribieron para proteger el ciclo de vida, no el contrato
  HTTP, y su 7.0 debe **medir el hueco** antes de fiarse.
- **A diferencia de los tres dominios anteriores, el supuesto que manda no está
  abierto**: el inventario de contratos de 0.0 registra un **reemplazo parcial
  transaccional con `rollback` probado** como efecto a preservar, así que
  **`asistencia` escribe** y su perfil de riesgo es el de la capa 5. Lo que 7.0
  debe hacer no es descubrirlo sino **cuantificarlo**. Diferencia favorable
  frente a `ventas`: **no es el dominio financiero**; un error aquí no da dinero
  mal contado, da **historial académico incorrecto**, que la capa 6 registró que
  **no se recalcula**. Diferencia desfavorable frente a `ventas`: `asistencia`
  **sí fue una de las ocho tablas averiadas** de `tenant_2005` que reparó la
  capa 3.
- **Nada de lo que la bitácora de `asistencia` dice de ese dominio está
  verificado.** La activación no inspeccionó su código: registra **doce
  supuestos heredados**, once no verificados y uno confirmado solo
  documentalmente, **cada uno con su origen anotado** —capas 0, 1, 3, 6 y 7— para
  que 7.0 pueda contrastarlo. Uno va marcado como **inferencia de patrón**: que
  el controlador tenga exactamente dos funciones, deducido del «1 sitio de 2» de
  1.4g, donde «sitio» significaba apertura de conexión y **no** función. Es la
  lección 12 de la capa 6, que ya sirvió tres veces, y marcar la inferencia como
  tal es lo que permitió refutar limpiamente el supuesto de permisos en `ventas`.
- Resultado de 7.0 de `asistencia`: el dominio quedó inventariado en **3
  archivos** —el supuesto decía dos—, **2 entradas HTTP** con **dos modelos de
  permiso**, **una sola tabla escrita**, **una transacción propia** y **3
  sentencias SQL inline**, todas en el controlador y 0 en la ruta y el esquema,
  protegido por **34 pruebas nuevas** sobre las **12 heredadas** de la capa 1. Es
  **el dominio más pequeño que ha migrado el programa**: 3 sentencias frente a
  las 17 de `ventas`, las 9 de `notas` y las 8 de `dashboard`. La compuerta local
  terminó con **869 pruebas**, Ruff y dependencias correctas. No se modificó
  producto: el diff es un solo archivo nuevo.
- **Los doce supuestos quedaron resueltos en 7.0**: **diez confirmados y dos
  incompletos**, y **ninguno falso**. Es la primera vez en el programa que no
  cae ninguno: en dashboard, notas y ventas siempre hubo uno falso o incompleto
  que cambiaba algo importante. Los dos incompletos aquí son menores: el dominio
  son **tres archivos y no dos** —el tercero es el esquema, con cero SQL, no un
  tercio de la persistencia como en `notas`— y las pruebas heredadas son **doce
  y no cinco**. **La inferencia de patrón se confirmó**, por primera vez: el
  controlador sí tiene exactamente dos funciones, aunque acertó **por
  casualidad**, porque «sitio» en la capa 1 significaba apertura de conexión y
  no función.
- **El hallazgo que manda es un N+1 en CONEXIONES, y es el peor perfil que ha
  medido el programa.** `require_estudiante_in_asignacion` abre su propia
  conexión y la ruta la llama **una vez por estudiante del lote**: guardar la
  asistencia de un curso de 30 abre **31 conexiones en serie** siendo admin y
  **61** siendo profesor, contra un pool de **10** y **5 workers**. **No se ve
  midiendo el controlador**, que abre una sola conexión en sus dos caminos; solo
  aparece al medir el camino HTTP completo. Es el **tercer caso** de conexiones
  en serie tras los 4 de dashboard y los 4 o 5 de notas, y **el primero cuyo
  número crece con el tamaño de la entrada**. Esta evidencia mide conexiones
  **totales y secuenciales** por petición, no leases simultáneos por worker, por
  lo que no respalda `MAX_DB_CONNECTIONS_PER_THREADPOOL_WORKER = 2`. Se registró
  **sin actuar** y la auditoría específica del 2026-08-24 no detectó `H>1`, pero
  dejó `H=1` como hipótesis pendiente de demostración operativa; las dos
  funciones vivían en `app/core/permissions.py`, **fuera de aquel alcance**.
- Hallazgos de 7.0 de `asistencia`, **registrados y sin corregir**: son **ocho**.
  Además del N+1, el permiso de asignación **se comprueba N veces con el mismo
  argumento** pese a que la ruta ya validó que todos comparten asignación; las
  **tres validaciones de lote viven en la capa de rutas** y el controlador no las
  repite, de modo que el `DELETE` toma fecha y periodo de `data[0]` mientras cada
  `INSERT` usa los suyos; el controlador **no valida `estado`** y escribe lo que
  reciba; el `ILIKE 'ausente'` vive **enteramente fuera del dominio**, en los dos
  consumidores ya migrados; la lectura **no tiene `try/except`**, así que un
  fallo sale como 500; y ninguna entrada declara `response_model`.
- **Lo que 7.0 de `asistencia` buscó expresamente y no encontró**: el patrón del
  falso éxito de `POST /notas` **no está aquí**. Medido por ASGI,
  `POST /asistencia` responde **200** solo cuando la transacción confirma, y
  **422** ante lote vacío, lote heterogéneo o `estado` desconocido. Tampoco hay
  `SELECT *`, ni f-strings en SQL, ni código muerto, ni funciones duplicadas: el
  dominio está limpio en todo lo que las tres capas 7 anteriores hallaron sucio.
- **El hueco de las pruebas heredadas quedó medido punto por punto.** Las doce
  que dejó la capa 1 cubren bien los contratos de la respuesta y la transacción,
  pero **ninguna** mide conteos de consultas o conexiones, **ninguna** observa un
  status code HTTP —las cuatro que comprueban un 422 llaman a la función de ruta
  directamente— y **ninguna** deja guardias estructurales. **Ninguna se retiró ni
  se reescribió.** Es la limitación que 7.0 de `notas` destapó para todo el
  programa, y aquí se cierra para este dominio midiendo por interfaz ASGI cruda.
- Resultado de 7.1 de `asistencia`: las **3 sentencias** salieron del controlador
  a `app/repositories/asistencia_repository.py`, **3 funciones** que reciben el
  cursor existente y **el noveno repositorio** del proyecto.
  `asistencia_controller.py` pasó de **84 a 69 líneas** y de 3 sentencias inline
  a **0**; la ruta y el esquema ya tenían 0. El comparador AST contra el commit
  base confirmó **3 literales SQL distintos antes y después, conjunto idéntico**,
  con **3 de 3 byte a byte**: **no hizo falta autorizar ningún cambio de texto
  SQL**. Compuerta local: **872 pruebas**, Ruff y dependencias correctas.
- **7.1 repitió la comprobación de equivalencia en tiempo de ejecución** que
  `ventas` incorporó al programa, y con tres sentencias y dos caminos salió
  barata: **los dos caminos emiten la misma secuencia de `(SQL, parámetros)`,
  devuelven lo mismo, abren el mismo número de conexiones y producen los mismos
  eventos de ciclo de vida** que el commit base. Es la evidencia que el
  comparador AST no da, porque compara texto y **no parámetros**.
- **Fallaron cinco pruebas al extraer y las cinco eran previsibles**: las **dos**
  guardias de línea base declaradas y las **tres** enumeraciones de repositorios
  de dashboard, notas y ventas. **Dentro del dominio la previsión acertó**: no
  falló ninguna prueba de hallazgo, porque el paso 9 del trabajo exacto obligó a
  revisarlas **antes** de extraer. Es la lección de 7.1 de `ventas` aplicada por
  adelantado en vez de descubierta después. **Las otras 44 pruebas del dominio
  pasaron sin cambiar de expectativa**, incluidas **las doce heredadas de la
  capa 1, que no se tocaron**.
- **Patrón que conviene dejar escrito, y que esta subcapa corrigió sobre su
  propia previsión**: la bitácora anunciaba **dos** enumeraciones ajenas y fueron
  **tres**, porque `ventas` añadió la suya. **Cada dominio migrado añade una
  guardia que enumera el conjunto exacto de repositorios**, así que el número
  crece en uno con cada migración: una en 7.1 de notas, dos en la de ventas,
  tres en esta, cuatro en la próxima. Se actualizan conservando su severidad,
  que es deliberada.
- Decisión de 7.1, tomada con evidencia: las **tres** sentencias viven en
  `asistencia_repository` y la decisión fue **fácil**, a diferencia del
  `UPDATE pagos` de `ventas`, porque ninguna escribe una tabla ajena. El único
  matiz que la merecía: el `SELECT` del historial **arranca `FROM estudiantes e`**
  y hace `JOIN asistencia`, así que su tabla conductora pertenece a un dominio ya
  migrado. Vive aquí igual, por el criterio que 6.2 fijó con el expediente: es
  **el historial de asistencia de una asignación**, no persistencia general de
  estudiantes. **Las dos lecturas ajenas no se movieron.**
- **Verificación manual de la capa 7 para `asistencia`: hecha por el usuario y
  correcta**, el 2026-08-21, en local. El artefacto se confirmó **antes** de
  registrarla y **sin ambigüedad**: árbol limpio, `HEAD` en `4a4d9e1` —el commit
  de 7.1— y `origin/main` todavía en el commit base, comprobado contra el remoto
  real. **Cobertura registrada sin inflarla**: el usuario la reportó **de forma
  global** y, preguntado punto por punto por los cuatro pasos de más peso,
  confirmó **uno**, el **paso 3, el reemplazo parcial**. **No constan** el lote
  que no incluye a todo el curso, la prueba cruzada de ausencias contra el
  expediente y el dashboard, ni el aislamiento entre los dos tenants. Es
  evidencia **más fuerte que la de `ventas`** —donde ningún paso llegó a
  constar— y **más débil que la de `notas`**, con el matiz favorable de que el
  paso que sí consta es **el que más valor tenía**: el reemplazo parcial es la
  única escritura y la única transacción del dominio, y es justo lo que una
  extracción mal hecha habría roto.
- **Decisión del usuario el 2026-08-21: cerrar la capa aquí**, sin abrir 7.2. Se
  le ofrecieron **cuatro** salidas —cerrar, una 7.2 con el N+1 en conexiones,
  una con `response_model`, o una con los errores de dominio— y eligió cerrar.
  **El N+1 en conexiones se queda**, y era la salida con más valor operativo:
  no se descarta para siempre, pasa a ser trabajo disponible que exigiría una
  orden propia y probablemente la auditoría de capacidad de la capa 2.
  `response_model` y los errores de dominio **no se añaden** y **no quedan como
  deuda de esta capa**. Los **tres pasos del guion que no constan siguen sin
  constar**.
- Capa 7 **cerrada para `asistencia`** el 2026-08-21, al día siguiente de
  activarse. Compuerta de cierre: **exit 0 con 872 pruebas**, Ruff correcto y
  `pip check` íntegro. La suite pasó de 835 al activar la capa a 872. Cerrarla
  **no cancela los ocho hallazgos de 7.0**, que siguen vivos, empezando por el
  N+1 en conexiones.
- **La capa 7 para `asistencia` no tocó la base de datos**, ni siquiera para
  leer. Es la **sexta consecutiva** que no abre una conexión a PostgreSQL, y la
  **tercera de esas seis cuyo dominio sí escribe**.
- **Estado de publicación de la capa 7 para `asistencia`: PUBLICADA el
  2026-08-21.** Registrado el 2026-08-21 con autorización explícita del usuario.
  **Esta línea sustituye a la siguiente**, que se conserva intacta por ser
  fechada, conforme al criterio que fijó la capa 4. Comprobado, no supuesto:
  `git ls-remote origin main` devuelve `8e61170f32a6d6a23ca23f9ead89d17bc209e7b6`,
  el mismo commit que `HEAD`, y el reflog registra `update by push` de `e5b74d2`
  —el cierre— a las **13:00:34 -0500** y de `8e61170` —la medición del N+1— a las
  **13:03:27 -0500**. **Producción sí corre este código**, así que el rollback
  **ya no es una operación local**: revertir a `a894441` exigiría otro push y
  otro despliegue. Es el **tercer desfase consecutivo** del mismo tipo, después
  de `notas` y `ventas`, y esta vez el propio índice lo había anticipado por
  escrito. **`07_ASISTENCIA.md` no se editó**: corregir una bitácora cerrada
  exige una orden propia, y esta autorización cubría el índice.
- **Estado de publicación de la capa 7 para `asistencia`: NO publicada.**
  `origin/main` sigue en el commit base `a894441` y hay **tres commits locales**
  por delante, más el del cierre. **Producción no corre este código**, así que
  mientras siga así el rollback es **puramente local**. Es la misma situación en
  que quedaron `notas` y `ventas` al cerrarse, y en los dos casos duró poco: si
  se publica, **conviene volver aquí y registrar el cambio**, porque las dos
  veces anteriores la documentación quedó desfasada.
- **Medición del N+1 en conexiones de `asistencia`, hecha el 2026-08-21 y
  aplazada por decisión explícita del usuario a la ronda de defectos.** Se
  investigó a fondo a petición suya, sin tocar código. **Corrige una
  caracterización anterior demasiado alarmista**: este hallazgo **no puede
  agotar el pool ni tumbar la aplicación**. Las conexiones son **secuenciales,
  no simultáneas** —cada `require_estudiante_in_asignacion` abre, consulta y
  cierra en su `finally` antes de la siguiente—, `get_connection()` reutiliza
  del `ThreadedConnectionPool` sin handshake nuevo, y el limitador de la capa 2
  topa la concurrencia en **5 workers** contra un pool de **10**. El coste real
  es **latencia y throughput**, no caída.
- **Números de esa medición**, contando los round-trips reales e incluyendo los
  **dos que `get_connection()` emite siempre** —`SET search_path` y
  `SELECT set_config(...)`—: pasar lista a un curso de 30 cuesta **31 conexiones
  y 155 round-trips** siendo admin, y **61 y 275** siendo profesor. Contra Neon,
  a 2–5 ms por round-trip, son **0,5 a 1,4 s** por petición como profesor; con 5
  workers, del orden de **3–10 peticiones por segundo** en ese endpoint. El
  efecto esperable es **cola y lentitud** cuando varios profesores pasan lista a
  la vez, no un error.
- **Plan de corrección ya diseñado, para la ronda de defectos**, en dos pasos y
  equivalente en comportamiento —mismo 403, mismo mensaje, mismo orden de
  precedencia—: **(A)** llamar `require_asignacion_access` **una sola vez**,
  porque la ruta ya validó en el bucle anterior que los N registros comparten
  `asignacion_id`; solo toca `app/routes/asistencia.py` y elimina 30 de las 60
  conexiones del profesor. **(B)** comprobar la pertenencia del lote **en una
  consulta**, con una función **nueva** en `permissions.py` que use
  `estudiante_id = ANY(%s)` y compare el conteo, **sin cambiar la existente**,
  que tiene otros tres puntos de llamada —uno en `boletines` y dos en
  `observaciones`, **ninguno en bucle**—. Con A+B: **2 conexiones y ~39
  round-trips** como admin, **3 y ~43** como profesor.
- **Coste conocido de ese plan, para que no aparezca como sorpresa**: obligaría a
  cambiar tres aserciones de conteo de `test_asistencia_caracterizacion.py` y
  **una prueba heredada de la capa 1**, `test_guardar_asistencia_valida_permisos_y_envia_lote`,
  que hoy fija `asignaciones_validadas == [(10, 3), (10, 3)]`. **Sería la primera
  vez en el programa que se cambia la expectativa de una prueba heredada**; es
  legítimo porque fija un conteo y no una regla de seguridad, pero debe quedar
  como decisión registrada y no como efecto colateral.
- **Alternativa descartada** en esa misma medición: pasar el cursor a las
  funciones de permiso para que compartan la conexión del controlador. Es lo
  arquitectónicamente correcto, pero cambia la firma de funciones que usan otras
  cuatro rutas y obliga a abrir la conexión antes de validar. No compensa hoy.
- **Cómo debe abordarse cuando llegue esa ronda**: **no dentro de la migración de
  otro dominio**. Toca `app/core/permissions.py`, infraestructura compartida que
  las seis capas anteriores declararon expresamente fuera de alcance, así que
  exige **bitácora propia y orden explícita**. La caracterización necesaria ya
  existe: las 37 pruebas de `asistencia` más las 12 heredadas cubren este camino.
  **`07_ASISTENCIA.md` no se editó**: está cerrada y corregirla exige una orden
  propia; esta es la línea que conserva la evidencia.
- **Corrección ejecutada localmente el 2026-08-24 con orden explícita.** La capa
  sigue cerrada y ninguna otra se activó. Se aplicaron exactamente los pasos A y
  B: una sola llamada a `require_asignacion_access` y una guardia nueva que
  comprueba todo el lote con `ANY(%s)` y `COUNT(*)`, sin cambiar la función
  singular que consumen `boletines` y `observaciones`. Para lotes de 1, 5 y 30,
  las pruebas fijan **2 conexiones totales como admin y 3 como profesor**. Se
  preservaron los 422, ambos 403 y su precedencia, el tenant por `search_path`,
  el lote original, el SQL y la transacción del controlador. Esta es además la
  primera modificación autorizada de una expectativa heredada: el acceso a la
  asignación ahora se espera una vez, no N. Las específicas terminaron con **72
  passed** y la compuerta con **1116 passed**, Ruff correcto y dependencias
  íntegras. El primer intento de compuerta tuvo 30 errores de preparación por el
  directorio temporal restringido; la repetición fuera del sandbox pasó. No se
  modificó `frontend-react`; staging, verificación manual, commit, push y CI no
  constan. La bitácora cerrada se actualizó porque esta vez la orden propia sí
  llegó.
- Capa 7 **activada para el dominio `boletin`** el 2026-08-21 por orden
  explícita del usuario, en el mismo turno que autorizó corregir el estado de
  publicación de `asistencia`. Commit base:
  `8e61170f32a6d6a23ca23f9ead89d17bc209e7b6`, el `HEAD` limpio vigente,
  **comprobado y no recordado**, y coincidente con `origin/main` contra el
  remoto real. Es **el primer dominio de la capa 7 cuyo commit base ya está
  publicado y desplegado en el momento de activar**, porque `asistencia` se
  publicó antes de esta activación. Los **cinco** commits posteriores al base de
  `asistencia` quedan auditados y explicados: `4e38e6c` la activación,
  `68ff9a4` su 7.0, `4a4d9e1` su 7.1 y `e5b74d2` su cierre están en
  `07_ASISTENCIA.md`; el quinto, `8e61170`, es la medición del N+1 y **está
  explicado en este índice**, no en la bitácora, que ya estaba cerrada. Se
  verificó con `git show --stat` que toca **exactamente un archivo de
  documentación y ningún código**. La activación es únicamente documental: no
  inspeccionó ni modificó código, migraciones, esquemas, pruebas ni
  configuración. **No se abrió ningún archivo de `boletin`.**
- Decisión al activar la capa 7 para `boletin`: continuar aceptando que sigan
  pendientes las verificaciones heredadas. Se ofrecieron cuatro salidas y el
  usuario eligió activar sin cerrarlas. **Ninguna se marca como cumplida**:
  siguen pendientes el valor operativo final de `DB_STATEMENT_TIMEOUT_MS` de la
  capa 1, la evidencia de GitHub Actions desde la capa 0, los **tres pasos** del
  guion de `ventas` y los **tres** del de `asistencia` que no constan, y la
  **credencial privilegiada de la capa 4 sin rotar**.
- **`boletin` es el primer dominio de la capa 7 que se activa sabiendo de
  antemano que su frontera está partida.** `notas` posee ya `/boletin/{id}` y
  `/boletin/detallado/{id}`, y existe por separado `app/routes/boletines.py`.
  **No hay colisión de paths**, comprobado por la 7.0 de `notas`, pero la
  frontera **no coincide con los nombres de archivo**: parte del boletín vive en
  un dominio ya migrado y cerrado. Es el riesgo que manda en esta capa y el que
  su 7.0 debe delimitar antes que ningún otro.
- Resultado de 7.0 de `boletin`, **cerrada el 2026-08-21**, el mismo día en que
  se activó la capa: el dominio quedó inventariado en **3 archivos** —
  `app/routes/boletines.py`, `app/controllers/boletin_controller.py` y
  `app/schemas/boletin.py`—, **4 entradas HTTP** con **tres modelos de
  permiso**, **12 sentencias SQL inline** todas en el controlador, **dos tablas
  escritas** en **una transacción propia** y **3 pruebas heredadas** más **24
  nuevas**. Compuerta: **896 pruebas, exit 0**; la suite pasó de **872 al
  activar la capa a 896**. Diff de 7.0: **un solo archivo de prueba nuevo y
  ningún archivo rastreado modificado**.
- **El resultado más importante de esa 7.0 no es el inventario, es la
  frontera.** De los **trece supuestos heredados**, **doce se confirmaron y uno
  quedó incompleto**, ninguno falso; pero **cinco de los trece describían código
  que pertenece a `notas`**, no a este dominio: el N+1 del boletín detallado,
  los ids sintéticos, el corte Aprobado/Reprobado en 3,0 y el promedio sin
  redondear. **Más de un tercio de lo que el programa creía saber de `boletin`
  hablaba del boletín de otro dominio.** Ningún dominio anterior tuvo un desvío
  así, y justifica que la frontera fuera el paso 1.
- **`boletin` es el primer dominio de la capa 7 que se inventaría y sale sin
  N+1**, ni en consultas ni en conexiones. `require_estudiante_in_asignacion` se
  llama **una vez y fuera de todo bucle**, así que el coste **no crece con el
  número de estudiantes**: `POST /boletines/guardar` cuesta **2 conexiones**
  siendo admin y **3** siendo profesor, frente a las **31 y 61** de
  `asistencia`. La medición de la capa 4 —4 consultas para un boletín de 13
  materias— **quedó reconciliada**: era de este dominio, y no contradecía el N+1
  del detallado, que es de `notas`.
- Hallazgos de 7.0 de `boletin`, **registrados y sin corregir**: son **diez**.
  El que manda es que **las observaciones guardadas se emparejan por POSICIÓN y
  no por identidad**, así que añadir, borrar o reordenar una nota de la planilla
  **pega la observación a la nota equivocada**, en silencio. Le siguen que **la
  capa 1 no migró este archivo** —sigue entero en `get_connection()`—; que el
  dominio usa **dos formas de promediar**, `AVG()` en SQL y `sum()/len()` en
  Python sin redondear; que una **definitiva guardada como 0 se trata como
  ausente**; que **`obtener_notas_planilla_controller` es código muerto de
  `planilla`** alojado en este controlador y sin un solo consumidor; y que el
  reemplazo parcial **borra siempre**, aunque el lote venga vacío.
- **Riesgo que 7.0 deja apuntado para 7.1**: el controlador tiene **14 líneas
  con espacios finales**, una dentro de un literal SQL. `git diff --check`
  obliga a limpiarlos, y eso **rompería la comparación byte a byte** que las
  cuatro 7.1 anteriores exigieron. Hay que decidirlo **antes** de mover nada.
- **Lo que 7.0 de `boletin` buscó y no encontró**, y conviene no perder: las
  cuatro entradas mapean el fallo a **500 con un mensaje fijo** y **no devuelven
  el texto de la excepción al cliente**, al contrario que `dashboard` y
  `asistencia`; los guards corren **fuera del `try`**, así que un 403 nunca sale
  como 500; y no hay fugas de conexión ni f-strings en SQL.
- Resultado de 7.1 de `boletin`, **cerrada el 2026-08-21**: **11 de las 12
  sentencias** salieron del controlador a
  `app/repositories/boletin_repository.py`, **11 funciones** que reciben el
  cursor. Es **el décimo repositorio** del proyecto. `boletin_controller.py`
  pasó de **457 a 293 líneas** y de **12 sentencias inline a 1**. Compuerta:
  **898 pruebas, exit 0**; la suite pasó de **872 al activar la capa a 898**.
- **7.1 de `boletin` es la primera subcapa del programa que cambió texto SQL con
  autorización explícita.** El usuario ordenó «limpia pero que no dañe el
  funcionamiento actual», así que las **14 líneas con espacios finales** se
  limpiaron —una dentro de un literal SQL— y **la comparación byte a byte que
  las cuatro 7.1 anteriores exigieron dejó de poder sostenerse**. Se sustituyó
  por una cadena de dos pasos con evidencia propia: primero limpiar y demostrar
  que **los doce literales normalizados son idénticos** al commit base, después
  mover y demostrar que **el conjunto de SQL sigue siendo el mismo**. Es el
  precedente para cualquier archivo sucio que herede una subcapa futura:
  **limpiar primero, probar la inocuidad, mover después**.
- **Equivalencia de 7.1 comprobada en ejecución, no solo por texto**: se corrió
  el controlador del commit base y el de hoy contra dobles idénticos y **los
  cinco caminos** emiten la misma secuencia de `(SQL, parámetros)`, devuelven lo
  mismo y abren las mismas conexiones y cierres.
- **Decisión de 7.1: una sentencia se queda inline a propósito.** La de
  `obtener_notas_planilla_controller`, el código muerto de `planilla`. Llevarla
  al repositorio habría creado una función sin consumidores y una falsa
  propiedad sobre un dominio en espera. Se descartó el bloque rotulado que usó
  la capa 6 en `estudiantes_repository`, porque allí los consumidores eran
  reales. El dominio queda en **1 sentencia inline**, como `asignaciones`.
- **Cinco guardias fallaron en 7.1, que era la señal esperada.** Cuatro son
  ajenas y confirman el patrón que `asistencia` anotó —cada migración añade una
  enumeración de repositorios, así que **el número crece en uno cada vez**—: las
  de `asistencia`, `dashboard`, `notas` y `ventas`. En la de `asistencia` el
  conteo pasó de **9 a 10**.
- **Punto de decisión abierto al terminar 7.1 de `boletin`**, con **tres**
  salidas: cerrar la capa como refactorización pura, una 7.2 con
  `response_model` —**más cara aquí** por los payloads anidados de forma
  variable— o una 7.2 con errores de dominio, que es **la más barata de las
  tres**, porque las cuatro entradas ya mapean a `HTTPException` con mensajes
  fijos y no habría status code que cambiar. Ninguna entra por inferencia.
  Queda pendiente también la **verificación manual**.
- **Verificación manual de la capa 7 para `boletin`: hecha por el usuario y
  correcta**, el 2026-08-21, en local. El artefacto se confirmó antes de
  registrarla: árbol limpio, `HEAD` en `865a062` —el commit de 7.1— y
  `origin/main` todavía en el commit base, comprobado contra el remoto real.
  **Cobertura registrada sin inflarla**: el usuario la reportó **de forma global
  y con una reserva explícita**, «aparentemente está todo bien», y **no consta
  ningún paso del guion confirmado uno por uno**, porque no se preguntó punto
  por punto antes de cerrar. Es la evidencia **más débil de los cinco dominios
  de la capa 7**: `notas` fue la más fuerte, `asistencia` dejó constancia de un
  paso de cuatro y `ventas` de ninguno. **Lo que más habría valido confirmar, y
  no consta, es guardar un boletín que ya existía**: la única escritura y la
  única transacción del dominio.
- **Decisión del usuario el 2026-08-21: cerrar la capa aquí**, sin abrir 7.2. Se
  le ofrecieron **tres** salidas —cerrar, una 7.2 con `response_model` o una con
  los errores de dominio— y eligió cerrar. `response_model` y los errores de
  dominio **no se añaden** y **no quedan como deuda de esta capa**. Los **diez
  hallazgos siguen vivos**, empezando por el emparejamiento por posición.
- Capa 7 **cerrada para `boletin`** el 2026-08-21, el mismo día en que se
  activó. Compuerta de cierre: **exit 0 con 898 pruebas**, Ruff correcto y
  `pip check` íntegro. La suite pasó de **872 al activar la capa a 898**.
- **La capa 7 para `boletin` no tocó la base de datos**, ni siquiera para leer.
  Es la **séptima consecutiva** que no abre una conexión a PostgreSQL, y la
  **cuarta de esas siete cuyo dominio sí escribe**.
- **Estado de publicación de la capa 7 para `boletin`: NO publicada.**
  `origin/main` sigue en el commit base `8e61170` y hay **tres commits locales**
  por delante: `0f351c8` la activación, `100de58` la 7.0 y `865a062` la 7.1.
  **Producción no corre este código**, así que mientras siga así el rollback es
  **puramente local**. Es la misma situación en que quedaron `notas`, `ventas` y
  `asistencia` al cerrarse, y en los tres casos duró poco: si se publica,
  **conviene volver aquí y registrar el cambio**, porque las tres veces
  anteriores la documentación quedó desfasada.
- ⚠️ **Desfase de publicación de `boletin`, detectado el 2026-08-21 al activar
  `observaciones` y NO corregido.** El índice y `07_BOLETIN.md` declaran esa
  capa **«NO publicada»** y su rollback «puramente local». **Ya no es cierto**:
  `git ls-remote origin main` devuelve
  `fd3f93a2ad97daa0a34081eb2f95504dd1a9e4df`, el commit de cierre de `boletin`,
  así que **producción sí corre ese código** y revertir exigiría otro push y
  otro despliegue. Es el **cuarto desfase consecutivo** del mismo tipo, tras
  `notas`, `ventas` y `asistencia`. **La autorización del turno cubría activar
  `observaciones`, no corregir el estado de `boletin`**, así que las líneas de
  más arriba se conservan intactas y esta queda como la advertencia. Corregirlas
  exige una orden propia.
- Capa 7 **activada para el dominio `observaciones`** el 2026-08-21 por orden
  explícita del usuario, que lo nombró. Commit base:
  `fd3f93a2ad97daa0a34081eb2f95504dd1a9e4df`, el `HEAD` limpio vigente,
  **comprobado y no recordado**, y coincidente con `origin/main` contra el
  remoto real: **está publicado y desplegado**. Los **cuatro** commits
  posteriores al base de `boletin` quedan auditados y explicados en
  `07_BOLETIN.md`: `0f351c8` la activación, `100de58` su 7.0, `865a062` su 7.1 y
  `fd3f93a` su cierre. La activación es únicamente documental: no inspeccionó ni
  modificó código, migraciones, esquemas, pruebas ni configuración. **No se
  abrió ningún archivo de `observaciones`.**
- Decisión al activar la capa 7 para `observaciones`: continuar aceptando que
  sigan pendientes las verificaciones heredadas. El informe de cierre de
  `boletin` las listó por escrito en el turno anterior y el usuario ordenó
  activar sin cerrarlas. **Ninguna se marca como cumplida.**
- **`observaciones` es el primer dominio de la capa 7 que llega con persistencia
  en la capa HTTP.** La subcapa 1.4 registró que `app/routes/observaciones.py`
  abría su propia conexión dentro de `obtener_observacion`, que ejecuta un
  `SELECT` más el resolver; la capa 1 la migró a `get_cursor()`, pero **la
  consulta sigue en la ruta**. En los cinco dominios anteriores la persistencia
  estaba toda en el controlador. Su 7.0 tendrá que **contar SQL en la ruta
  además del controlador**, o el inventario saldrá falso.
- **Segunda trampa de frontera de la capa 7, y esta vez hacia un dominio en
  espera**: `plan_de_clases` tiene **tres handlers** con «observacion» en el
  nombre —`crear_observacion_plan`, `listar_observaciones_plan` y
  `marcar_observacion_vista`—, inventariados por la capa 2, que **no** son de
  este dominio. En `boletin` el nombre colisionaba con un dominio ya cerrado;
  aquí, con uno que sigue en espera. Delimitarlo es el paso 1 de su 7.0.
- Resultado de 7.0 de `observaciones`, **cerrada el 2026-08-21**, el mismo día
  en que se activó la capa: el dominio quedó inventariado en **3 archivos y 104
  líneas** —router, controlador y esquema—, **2 entradas HTTP** con **un único
  modelo de permiso**, **2 sentencias SQL** —**una en la ruta y otra en el
  controlador**—, **una sola tabla escrita** en **una transacción propia** y **8
  pruebas heredadas** más **25 nuevas**. Compuerta: **923 pruebas, exit 0**; la
  suite pasó de **898 al activar la capa a 923**. Diff de 7.0: **un solo archivo
  de prueba nuevo y ningún archivo rastreado modificado**.
- **`observaciones` es el dominio con menos SQL que ha migrado el programa**: 2
  sentencias, por debajo de las 3 de `asistencia`. Y **el segundo con permisos
  uniformes**, tras `ventas`: sus dos entradas exigen exactamente los mismos
  tres guards. **Ningún N+1**, ni de consultas ni de conexiones; es el segundo
  dominio seguido que sale limpio en esto.
- **Los once supuestos quedaron resueltos**: **diez confirmados y uno
  incompleto**, ninguno falso y **ninguno mal atribuido**, que era el riesgo que
  dejó `boletin`. **La trampa de frontera resultó limpia**: las tres rutas de
  observaciones de `plan_de_clases` tienen paths disjuntos y escriben **otra
  tabla**, `plan_de_clases_observaciones`. El incompleto es el de siempre —el
  esquema como tercer archivo—, y es la **tercera vez seguida** tras `asistencia`
  y `boletin`: conviene darlo por sabido y dejar de contarlo como sorpresa.
- **Quedó explicado por fin qué son las «dimensiones normalizadas»** que el
  inventario de 0.0 registró sin definir: las dimensiones son `conductual`,
  `cognitivo` y `lenguaje`, y normalizar es `str(valor or "").strip()` en un
  `field_validator`. El **`422`** lo produce un `model_validator` que rechaza las
  tres vacías. Es **el primer 422 propio de un dominio de la capa 7**.
- Hallazgos de 7.0 de `observaciones`, **registrados y sin corregir**: son
  **nueve**. El que manda es que **la tabla no tiene ninguna clave foránea**:
  `estudiante_id` y `asignacion_id` son enteros sueltos, nada impide una
  observación huérfana y el `UPSERT` escribe lo que le den, así que **la
  integridad depende enteramente de un código que no la comprueba**. Le siguen
  que las tres dimensiones son `text` **sin límite ni `CHECK`** —cuando la tabla
  del dominio vecino sí acota su texto entre 1 y 3000, de modo que **el dominio
  académico está menos protegido que el de planes de clase**—; que **la lectura
  vive en la capa HTTP**; que el **`422` depende del esquema** y una extracción
  que mueva esa validación lo convertiría en 500 en silencio; que la
  normalización **convierte cualquier valor falsy en cadena vacía**, así que un
  `0` numérico llega como `""`; y que **ninguna de las dos entradas registra
  nada** ante un fallo.
- Resultado de 7.1 de `observaciones`, **cerrada el 2026-08-21**: las **2
  sentencias** salieron a `app/repositories/observaciones_repository.py`, **2
  funciones** que reciben el cursor. Es **el undécimo repositorio** del
  proyecto. La ruta pasó de **41 a 38 líneas** y el controlador de **43 a 30**,
  los dos de **1 sentencia inline a 0**: **la capa HTTP se queda sin SQL**, que
  era el hallazgo 3. Compuerta: **925 pruebas, exit 0**; la suite pasó de **898
  al activar la capa a 925**.
- **El alcance de esa 7.1 lo decidió el usuario, no el asistente.** Se le
  ofrecieron **tres** salidas para la sentencia que vivía en la ruta —bajarla
  antes a un controlador nuevo, llevar las dos directas al repositorio, o
  extraer solo el `UPSERT`— y eligió la segunda. Una instrucción genérica de
  continuar no habría bastado para fijarlo.
- **La comparación byte a byte volvió al criterio estricto.** Se comprobó antes
  de mover nada que ni la ruta ni el controlador tenían **una sola línea con
  espacios finales**, así que no hizo falta la limpieza autorizada que necesitó
  `boletin`: **2 de 2 literales idénticos byte a byte**. La equivalencia se
  comprobó además **en ejecución** en los dos caminos y tres escenarios
  —lectura con fila, lectura sin fila y `UPSERT`—, con los guards instrumentados
  dentro de la secuencia para fijar también **su orden**.
- **Rasgo propio de esta 7.1, y no lo tuvo ninguna anterior**: sus dos llamadores
  son de **capas distintas**. La lectura llama al repositorio desde la **ruta**,
  con `get_cursor()`; la escritura, desde el **controlador**, con
  `get_connection()`. **No se unificaron los idiomas ni se movió la propiedad
  del cursor**, porque eso habría cambiado los conteos de conexiones que 7.0
  fijó por aserción.
- **Siete guardias fallaron en esa 7.1, que era la señal esperada.** Cuatro son
  ajenas —`asistencia`, `dashboard`, `notas` y `ventas`— y confirman de nuevo
  que cada migración añade una enumeración de repositorios: el conteo pasó de
  **10 a 11**. Las otras tres eran las de línea base que su propia 7.0 dejó
  puestas. Una guardia nueva falló además por un defecto propio y **volvió a
  morder la lección 13 de la capa 6**: buscaba `get_connection` en el texto del
  módulo y el docstring del repositorio lo nombra justo para explicar que no lo
  usa. Se corrigió excluyendo docstrings.
- **Punto de decisión abierto al terminar 7.1 de `observaciones`**, con **tres**
  salidas: cerrar la capa como refactorización pura, una 7.2 con
  `response_model` —**la más barata de todo el programa**, porque las dos
  respuestas son planas y sin anidamiento; el único matiz es el `None` de la
  observación ausente— o una 7.2 con errores de dominio, que aquí es **la más
  cara**, porque el dominio **no usa `HTTPException` en ninguna parte** e
  introducirla cambiaría cómo salen los fallos. Ninguna entra por inferencia.
  Queda pendiente también la **verificación manual**.
- **Verificación manual de la capa 7 para `observaciones`: hecha por el usuario
  y correcta**, el 2026-08-21, en local. El artefacto se confirmó antes de
  registrarla: árbol limpio, `HEAD` en `4bceabb` —el commit de 7.1— y
  `origin/main` todavía en el commit base, comprobado contra el remoto real.
  **Cobertura registrada sin inflarla**: el usuario la reportó **de forma global
  y con una reserva explícita**, «aparentemente está bien», y **no consta ningún
  paso del guion confirmado uno por uno**. Es el **segundo dominio consecutivo**
  en el tramo más débil, tras `boletin`, y con la misma reserva literal. **Lo
  que más habría valido confirmar, y no consta**: guardar sobre una observación
  que ya existía, y comprobar que las tres dimensiones vacías siguen dando
  **422** —ese status lo sostiene **solo el esquema**—.
- **Decisión del usuario el 2026-08-21: cerrar la capa aquí**, sin abrir 7.2. Se
  le ofrecieron **tres** salidas y eligió cerrar. `response_model` y los errores
  de dominio **no se añaden** y **no quedan como deuda de esta capa**. Queda
  anotado que **`response_model` era aquí la salida más barata de todo el
  programa** —respuestas planas, sin anidamiento—, por si alguna vez se quiere
  probar en algún dominio. Los **nueve hallazgos siguen vivos**.
- Capa 7 **cerrada para `observaciones`** el 2026-08-21, el mismo día en que se
  activó. Compuerta de cierre: **exit 0 con 925 pruebas**, Ruff correcto y
  `pip check` íntegro. La suite pasó de **898 al activar la capa a 925**.
- **La capa 7 para `observaciones` no tocó la base de datos**, ni siquiera para
  leer; solo leyó el fichero de la migración base para inventariar el DDL. Es la
  **octava consecutiva** que no abre una conexión a PostgreSQL, y la **quinta de
  esas ocho cuyo dominio sí escribe**.
- **Estado al cerrar `observaciones`: no publicada.** En ese momento
  `origin/main` seguía en `fd3f93a` y había tres commits locales por delante:
  `dac6425` la activación, `eaa8115` la 7.0 y `4bceabb` la 7.1. Esta línea
  conserva el hecho histórico del cierre.
- **Estado de publicación de `observaciones`, corregido el 2026-08-21:
  publicada.** `HEAD` y la referencia local `origin/main` coinciden en
  `580c0ad6f0d14d16af5cbd8b2a4a9e4532485b89`, el commit de cierre, y el reflog
  registra `update by push` a las **15:58:27 -0500**. El rollback ya no es una
  operación puramente local: conforme al flujo documentado del repositorio,
  exige otro push y otro despliegue. En este turno no se consultó el remoto real
  ni se atribuye ningún run de GitHub Actions.
- Última capa cerrada: **7 para `planilla`**. Quedó cerrada el
  2026-08-21 por orden explícita del usuario, sin abrir 7.2. Sus cinco
  sentencias propias viven en el duodécimo repositorio y los tres llamadores
  conservan sus recursos y comportamiento; las piezas nominales de `notas` y
  `boletin` permanecen intactas. Compuerta sobre el commit limpio: **957
  pruebas**, Ruff correcto y dependencias íntegras.
- **Verificación manual de `planilla`: completada y correcta.** El usuario
  reportó correctos los ocho puntos: escritura, reemplazo, desarrollo, lectura,
  borrado, permisos, validaciones y comprobación cruzada de notas/tenant. No
  especificó el entorno, así que no se atribuye a local, staging ni despliegue.
- Última capa cerrada: **7 para `planeador_anual`**, activada el 2026-08-21 y
  cerrada el 2026-08-22 por órdenes explícitas del usuario. Commit base limpio:
  `235672ea609444a46003175940376c37bfe191c4`. Su **7.0 quedó cerrada el
  2026-08-22** con 29 pruebas nuevas y **ningún cambio de producto**; delimitó
  tres archivos, dos rutas, cinco SQL y una tabla escrita. La compuerta terminó
  con **986 pruebas**, Ruff correcto y dependencias íntegras. Su **7.1 está
  cerrada**: extrajo los cinco SQL al decimotercer repositorio, conservó 5 de 5
  textos byte a byte, recursos y contratos, y terminó con **987 pruebas**. La
  compuerta de cierre sobre `51203da` volvió a pasar con 987 pruebas; 7.2 es
  **No aplica**. El usuario informó después «planeador revisado»; se registra
  la verificación manual como completada de forma global, sin entorno ni
  desglose punto por punto.
- Última capa cerrada: **7 para `plan_de_clases`**, activada y cerrada por
  órdenes explícitas del usuario el 2026-08-22. Commit base limpio:
  `bfe80d4152b802aeb22f4c5a2c5aab9265ba7630`. Su **7.0 está cerrada**: cinco
  archivos propios y 1334 líneas, once entradas propias más `/uploads`, tres
  tablas, 25 sitios `cursor.execute` en el repositorio y dos consultas
  específicas externas. Agregó 22 pruebas sin modificar producto; las
  específicas finalizaron con **127 passed** y la compuerta con **1009
  passed**, Ruff correcto y dependencias íntegras. Registró doce hallazgos sin
  corregir. Su **7.1 está cerrada**: extrajo las dos consultas externas al
  repositorio existente, que ahora suma **27 sitios `cursor.execute`**, sin
  mover conexión, cursor ni cierre de sus llamadores. Conservó ambos SQL byte a
  byte y sus parámetros; la frontera propia suma ahora 1365 líneas. La
  caracterización terminó con **24 passed**, las específicas con **129 passed**
  y la compuerta con **1011 passed**. El primer hallazgo está resuelto y once
  siguen vivos. El usuario eligió cerrar como refactorización pura: 7.2 y 7.3
  son **No aplica**. La compuerta de cierre sobre el commit limpio pasó con
  **1011 pruebas**, Ruff correcto y dependencias íntegras. La verificación
  manual propia quedó completada de forma global con la reserva
  «aparentemente bien», sin entorno, artefacto ni desglose punto por punto. No
  se comprobó publicación.
- Resultado de 7.0 de `branding`: tres archivos propios y 246 líneas, cuatro
  rutas propias más `/uploads`, una tabla, siete sitios SQL inline, escrituras
  DB/storage y ningún N+1 de aplicación. Agregó 19 pruebas sin modificar
  producto; las específicas terminaron con **50 passed** y la compuerta con
  **1030 passed**, Ruff correcto y dependencias íntegras. Los seis supuestos
  quedaron resueltos y los trece hallazgos se registraron sin corregir.
- Resultado de 7.1 de `branding`: cuatro archivos propios y 268 líneas; los
  siete usos SQL salieron del controlador y quedaron en seis operaciones de un
  repositorio sin recursos. SQL, parámetros, conexiones, transacciones,
  storage, offload, tenant y contratos se conservaron. Las específicas
  terminaron con **52 passed** y la compuerta con **1032 passed**, Ruff correcto
  y dependencias íntegras. Los trece hallazgos siguen vivos.
- Cierre de `branding`: el usuario ordenó cerrarla como refactorización pura;
  7.2 y 7.3 son **No aplica**. La compuerta sobre el commit limpio volvió a
  pasar con **1032 pruebas**, Ruff correcto y dependencias íntegras. Staging y
  rollback están documentados; la verificación manual propia queda pendiente.
- Capa activa: **ninguna**. La última capa cerrada es **7 para `super_admin`**;
  commit base limpio `2ec924a`, subcapas 7.0 a 7.3 completas, 20 sitios SQL en
  el repositorio y ninguno en controlador o núcleo. Las específicas y la
  compuerta terminaron con 89 y 1089 pruebas. Staging y rollback están
  documentados; su verificación manual queda pendiente.
- Decisión vigente al activar `profesores`: continuar localmente aceptando que
  sigan pendientes la verificación manual propia de `branding`, la
  calibración final de `DB_STATEMENT_TIMEOUT_MS`, la evidencia de GitHub
  Actions posterior a la capa 0, los pasos manuales no confirmados heredados y
  la rotación de la credencial privilegiada de la capa 4. Ninguna se marca como
  cumplida.
- No queda otro dominio enumerado en espera y no hay capa activa. `super_admin`
  está cerrado con 7.0–7.3 completas; cualquier trabajo posterior requiere una
  orden explícita.
- **Punto de decisión abierto al terminar 7.1**, con **tres** salidas y no dos:
  dónde vive el `UPDATE pagos`, `response_model` para las cuatro lecturas, y los
  errores de dominio. La tercera es **más fácil aquí que en `notas`**: este
  dominio **ya usa** el mecanismo de error de FastAPI, así que convertir sus
  `ValueError` en errores de dominio **no cambiaría ningún status code** y sería
  una refactorización pura. Ninguna de las tres entra por inferencia. Queda
  pendiente también la **verificación manual**.
- Diferencia favorable de `ventas` frente a `notas`, y es un hecho registrado:
  **`ventas` no estuvo entre las ocho tablas averiadas** de `tenant_2005` que la
  capa 3 reparó. Riesgo propio en contrapartida: **es el dominio financiero**,
  así que los contratos de la capa 4 —6/15, 1/13/37 y 5/12/12— y la frontera de
  pagos de la capa 5 rodean este código. Un error aquí no da una cifra rara en
  un panel: da **dinero mal contado**.
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

- [07_SUPER_ADMIN.md](./07_SUPER_ADMIN.md): **bitácora cerrada** de la capa 7
  para el dominio `super_admin`. Fue la fuente de continuidad **hasta la campaña
  de hallazgos de `dashboard`**; ese papel lo tiene hoy
  [07_OBSERVACIONES.md](./07_OBSERVACIONES.md). Registra
  el commit base limpio `2ec924a3308581b746a61fa24a44f71433034dbc`, la rama
  acordada `main`, la orden explícita «sigue super admin» y la decisión de
  continuar localmente aceptando las verificaciones manuales de `profesores` y
  `branding` y las heredadas pendientes. La activación fue exclusivamente
  documental. Después, 7.0 inventarió la frontera privilegiada, agregó 27
  casos sin modificar producto y pasó 88 pruebas específicas y la compuerta
  global con 1088 pruebas. 7.1 extrajo cinco SQL idénticos byte a byte a
  `super_admin_repository` y terminó con 89 pruebas específicas y 1089 globales.
  7.2 extrajo las dos consultas de autenticación y revalidación con 2 de 2 SQL
  idénticos, conservó seguridad y recursos en el núcleo y repitió los mismos
  resultados. 7.3 extrajo las 13 operaciones del provisionamiento con 13 de 13
  SQL y parámetros exactos, dejó los 20 sitios SQL en el repositorio y cerró
  con 89 pruebas específicas y 1089 globales. **7.0–7.3 están cerradas; no hay
  capa activa ni sucesora enumerada.** Staging y rollback están documentados;
  la verificación manual propia permanece pendiente.
- [07_PROFESORES.md](./07_PROFESORES.md): **bitácora cerrada** de la capa 7 para
  el dominio `profesores` y fuente de continuidad anterior. Registra el
  commit base limpio `58eb5c2eb43a9d20708b75ca8bd798e9f13b33e6`, la rama
  acordada `main`, la orden explícita del usuario —con la errata inequívoca
  `proefesores`— y la decisión de continuar localmente aceptando la
  verificación manual de `branding` y las verificaciones heredadas pendientes.
  La activación fue exclusivamente documental. Su **7.0 está cerrada**: tres
  archivos propios y 450 líneas, cuatro rutas admin, diez sitios SQL inline,
  una tabla escrita y ningún N+1. El prefijo contiene además dos rutas de
  asignaciones y una función de clases propia no tiene consumidores. Agregó 27
  pruebas sin modificar producto; las específicas terminaron con **45 passed**
  y la compuerta con **1059 passed**. Los seis supuestos quedaron resueltos y
  los doce hallazgos se registraron sin corregir. Su **7.1 está cerrada**: nueve
  SQL alcanzables pasaron a nueve operaciones de `profesores_repository` sin
  mover recursos; el décimo sigue inline en la función sin consumidores. La
  caracterización tiene 29 casos, las específicas terminaron con **47 passed**
  y la compuerta con **1061 passed**, Ruff correcto y dependencias íntegras. El
  usuario ordenó cerrar como refactorización pura: **7.2/7.3 son No aplica** y
  la compuerta de cierre volvió a pasar con 1061 pruebas. Staging y rollback
  están documentados; la verificación manual propia permanece pendiente.
  `super_admin` se activó después por orden explícita del usuario.
- [07_BRANDING.md](./07_BRANDING.md): **bitácora cerrada** de la capa 7 para el
  dominio `branding` y fuente de continuidad anterior. Registra el
  commit base limpio `bb34cf6f31413fdbbd2c1866b43f2da71f8ea03b`, la rama
  acordada `main`, la orden explícita de activar el dominio y la decisión de
  continuar localmente aceptando las verificaciones heredadas pendientes. Su
  **7.0 está cerrada**: delimitó tres archivos propios, cuatro rutas más el
  endpoint compartido `/uploads`, una tabla, siete sitios SQL inline,
  escrituras DB/storage y ningún N+1 de aplicación. Resolvió los seis supuestos,
  agregó 19 pruebas sin modificar producto y registró trece hallazgos. Las
  específicas terminaron con **50 passed** y la compuerta con **1030 passed**,
  Ruff correcto y dependencias íntegras. Su **7.1 está cerrada**: movió los
  siete usos SQL a seis operaciones de `branding_repository` sin mover recursos,
  storage, offload, tenant ni contratos. Las específicas terminaron con **52
  passed** y la compuerta con **1032 passed**. El usuario ordenó cerrar como
  refactorización pura: 7.2 y 7.3 son **No aplica** y la compuerta de cierre
  volvió a pasar con **1032 pruebas**. Staging y rollback están documentados;
  la verificación manual propia queda pendiente. `profesores` y `super_admin`
  se activaron después, cada uno por orden explícita.
- [07_PLAN_DE_CLASES.md](./07_PLAN_DE_CLASES.md): **bitácora cerrada** de la
  capa 7 para el dominio `plan_de_clases` y fuente de continuidad anterior.
  Registra el commit base limpio
  `bfe80d4152b802aeb22f4c5a2c5aab9265ba7630`, la orden explícita del usuario
  «sigue con plan de clases», la activación exclusivamente documental y el
  cierre posterior de **7.0** por la orden «continua». Delimitó cinco archivos
  propios, once entradas propias más `/uploads`, tres tablas, 25 sitios SQL en
  el repositorio y dos consultas específicas externas; resolvió los ocho
  supuestos, agregó 22 pruebas y registró doce hallazgos sin modificar
  producto. Las específicas terminaron con **127 passed** y la compuerta con
  **1009 passed**. **7.1 está cerrada**: las dos consultas externas pasaron al
  repositorio existente con SQL y parámetros exactos y sin mover los recursos
  de `permissions.py` ni `main.py`; la caracterización terminó con 24 casos,
  las específicas con **129 passed** y la compuerta con **1011 passed**. Quedan
  once hallazgos vivos. El usuario cerró la capa como refactorización pura;
  7.2/7.3 son **No aplica** y la compuerta de cierre volvió a pasar con **1011
  pruebas**. Staging y rollback están documentados; la verificación manual
  propia quedó completada globalmente con la reserva «aparentemente bien», sin
  entorno, artefacto ni desglose individual. `branding`, `profesores` y
  `super_admin` se activaron después, cada uno por orden explícita.
- [07_PLANEADOR_ANUAL.md](./07_PLANEADOR_ANUAL.md): **bitácora cerrada** de la
  capa 7 para el dominio `planeador_anual` y fuente de continuidad anterior.
  Registra el commit base limpio
  `235672ea609444a46003175940376c37bfe191c4`, la autorización explícita del
  usuario nombrando el dominio y la decisión de continuar localmente aceptando
  las verificaciones heredadas pendientes. Su **7.0 está cerrada**: delimitó
  tres archivos propios y dos rutas, contó cinco SQL inline, una tabla escrita
  y un `1+N` respecto del lote, y añadió 29 pruebas sin modificar producto. La
  compuerta de 7.0 terminó con **986 pruebas**. Deja once hallazgos sin corregir,
  encabezados por dos funciones muertas incompatibles con sus esquemas y el
  falso reemplazo de lotes vacíos o cortos. Su **7.1 está cerrada**: extrajo
  los cinco SQL al decimotercer repositorio con 5 de 5 literales byte a byte y
  la compuerta final pasó con **987 pruebas**. El usuario eligió cerrar sin 7.2;
  staging y rollback están documentados. El usuario informó después «planeador
  revisado»; la verificación manual propia queda completada de forma global,
  sin entorno ni desglose punto por punto. `plan_de_clases` se activó después y
  los otros tres dominios permanecen en espera.
- [07_PLANILLA.md](./07_PLANILLA.md): **bitácora cerrada** de la capa 7 para el
  dominio `planilla`, y fuente de continuidad anterior. Registra el commit base limpio
  `580c0ad6f0d14d16af5cbd8b2a4a9e4532485b89`, la orden explícita del usuario
  nombrando el dominio, la decisión de continuar localmente aceptando todas las
  verificaciones pendientes y la activación exclusivamente documental. Su
  **7.0 está cerrada**: delimitó cinco archivos propios y tres entradas HTTP,
  separó el `GET` de `notas` y la función muerta de `boletin`, contó cinco SQL,
  una tabla escrita y ninguna forma de N+1, y añadió 30 pruebas. La compuerta
  terminó con **955 pruebas**, Ruff correcto y dependencias íntegras. Deja diez
  hallazgos sin corregir, encabezados por la carrera del borrar-e-insertar sin
  lock ni restricción única y el 200 de la validación fallida. Su **7.1 está
  cerrada**: extrajo las cinco sentencias al duodécimo repositorio, conservó
  **5 de 5 literales SQL byte a byte**, parámetros, retornos, conexiones y
  transacciones, y dejó los controladores y el servicio sin SQL inline. Las
  ocho guardias que fallaron al extraer eran la señal esperada —cuatro propias
  y cuatro enumeraciones históricas—; la compuerta final terminó con **957
  pruebas**, Ruff correcto y dependencias íntegras. El usuario eligió cerrar sin
  7.2; staging y rollback están documentados, y la verificación manual quedó
  correcta con **8 de 8 puntos** reportados y entorno no especificado. Los cinco
  dominios restantes siguen en espera.
- [07_OBSERVACIONES.md](./07_OBSERVACIONES.md): **bitácora cerrada** de la capa
  7 para el dominio `observaciones` y **fuente de continuidad más reciente**.
  **Es el documento que un chat nuevo debe leer después de este índice**, porque
  contiene la última actividad del programa: la **campaña de corrección de
  hallazgos cerrada el 2026-08-27**, con el veredicto razonado de los nueve
  —tres corregidos y publicados, uno obsoleto, dos aparcados y tres notas—, sus
  cinco lecciones y las verificaciones que deja pendientes. Registra el
  cierre de **7.1**, la extracción a `observaciones_repository` —**el
  undécimo**— con su comparador AST de **2 de 2 literales byte a byte**, la
  equivalencia **en ejecución** de los dos caminos y tres escenarios, y el rasgo
  que ninguna 7.1 anterior tuvo: **sus dos llamadores son de capas distintas**,
  la ruta en la lectura y el controlador en la escritura, sin unificar idiomas
  ni mover la propiedad del cursor. Registra las **siete guardias** que fallaron
  como señal esperada y la **segunda mordedura de la lección 13 de la capa 6**.
  Deja resuelto el **punto de decisión** que cerró la capa sin abrir una 7.2
  —anotando que `response_model` era aquí **la salida más barata del
  programa**—, el cierre con el rollback que era local **en ese momento** y que
  dejó de serlo tras el push del cierre, su staging, su **verificación manual con la cobertura real que el
  usuario reportó** —**ningún paso consta**, segundo dominio seguido en el tramo
  más débil— y los **nueve hallazgos** que deja abiertos, encabezados por la
  **ausencia total de claves foráneas** en la tabla. Registra también el commit
  base
  `fd3f93a2ad97daa0a34081eb2f95504dd1a9e4df` —**publicado y desplegado**,
  comprobado contra el remoto real—, la autorización explícita del usuario
  nombrando el dominio, el alcance limitado a un solo dominio y las
  verificaciones heredadas aceptadas como pendientes. Sus **7.0 y 7.1 están
  cerradas**. Conserva los **once supuestos heredados** con el origen
  documental de cada uno, uno de ellos marcado como **inferencia por ausencia**,
  y las dos cosas que distinguen a este dominio: **SQL en la capa HTTP**, que
  ningún dominio anterior tuvo, y la **colisión de nombres con
  `plan_de_clases`**, que estaba en espera al cerrarse `observaciones` y ahora
  está activo en su propia bitácora. Registra también el desfase de
  publicación de `boletin` detectado al activar y **no corregido**.
- [07_BOLETIN.md](./07_BOLETIN.md): **bitácora cerrada** de la capa 7 para el
  dominio `boletin`. Fue la fuente de continuidad **hasta que se cerró
  `observaciones`**; sus diez hallazgos siguen vivos, encabezados por el
  **emparejamiento por posición**, y **no se corrigen desde la capa activa**.
  **Advertencia sobre este archivo**: su estado de publicación quedó desfasado,
  igual que les pasó a `07_NOTAS.md`, `07_VENTAS.md` y `07_ASISTENCIA.md`. Lo
  declara «no publicada» y describe su rollback como puramente local, y **ya no
  es cierto** desde el push que dejó `origin/main` en `fd3f93a`; la advertencia
  está en «Estado actual», más arriba. La bitácora **no se editó** porque
  corregir una capa cerrada exige una orden explícita. Registra el commit base
  `8e61170f32a6d6a23ca23f9ead89d17bc209e7b6` —publicado y desplegado, comprobado
  contra el remoto real—, la autorización explícita del usuario nombrando el
  dominio y la advertencia de frontera partida entregada **antes** de la
  elección, el alcance limitado a un solo dominio, y las verificaciones
  heredadas aceptadas como pendientes. Conserva los **trece supuestos
  heredados** con **el origen documental de cada uno**, y el resultado que da
  sentido a toda la capa: **doce confirmados y uno incompleto, pero cinco de los
  trece describían código de `notas`**, no de este dominio. Conserva el
  inventario de **7.0**: **3 archivos**, **4 entradas HTTP** con **tres modelos
  de permiso**, **12 sentencias inline**, **dos tablas escritas** —la primera
  vez en la capa 7— y **ningún N+1**, ni de consultas ni de conexiones. Registra
  el cierre de **7.1**, con **la primera limpieza de texto SQL autorizada del
  programa** —14 líneas con espacios finales, limpiadas antes de mover nada y
  demostradas inocuas— y la extracción a `boletin_repository`, **el décimo**,
  con **11 de 12 sentencias** y la **equivalencia en ejecución de los cinco
  caminos**; las **cinco guardias** que fallaron como señal esperada y el patrón
  de que cada migración añade una enumeración de repositorios; y la **decisión
  de dejar una sentencia inline a propósito**, la del código muerto de
  `planilla`. Deja resuelto el **punto de decisión** que cerró la capa sin abrir
  una 7.2, el cierre con su rollback —**local, porque la capa sigue sin
  publicar**—, su staging, su **verificación manual con la cobertura real que el
  usuario reportó** —**ningún paso consta**, la más débil de la capa 7— y los
  **diez hallazgos** que deja abiertos, encabezados por el emparejamiento por
  posición.
- [07_ASISTENCIA.md](./07_ASISTENCIA.md): **bitácora cerrada** de la capa 7 para
  el dominio `asistencia`. Fue la fuente de continuidad **hasta que se cerró
  `boletin`**. De sus ocho hallazgos, los dos ligados al N+1 de permisos quedaron
  **corregidos el 2026-08-24 con orden explícita y publicados en `bbf3bfb`**;
  seis siguen
  abiertos. La corrección deja 2 conexiones totales como admin y 3 como profesor
  para lotes de 1, 5 y 30, pasó 1116 pruebas y conserva pendientes staging,
  verificación manual, despliegue comprobado y CI. **Advertencia histórica sobre este
  archivo**: su bloque de cierre aún contiene el estado de publicación de su
  fecha —«no publicada» y rollback local—, que dejó de ser cierto con el push del
  2026-08-21 a las 13:00:34. La entrada nueva al final de la bitácora sustituye el
  estado del N+1, no reescribe esa cronología. Registra el commit base
  `a894441f8676b0486e3395f88179cdf6cba61430` —publicado y desplegado,
  comprobado contra el remoto real—, la autorización del usuario y el rechazo
  previo de la orden que no nombraba dominio, el alcance limitado a un solo
  dominio, y las verificaciones heredadas aceptadas como pendientes por decisión
  explícita. Conserva los **doce supuestos heredados** con **el origen
  documental de cada uno**, uno de ellos marcado como **inferencia de patrón**;
  las dos novedades que ningún dominio anterior tuvo —**pruebas ya escritas** por
  la capa 1 y **dos idiomas de conexión conviviendo**, porque 1.4g migró 1 sitio
  de 2—; el perfil de riesgo, que **llega resuelto**: el dominio **escribe**, y
  lo registró la capa 0 al inventariar su reemplazo parcial transaccional. Fija
  el **trabajo exacto de 7.0 en quince pasos**, sus criterios de cierre, los
  criterios de cierre de la capa y los riesgos, entre ellos que **dos
  consumidores ajenos ya migrados** —`estudiantes_repository` y
  `dashboard_repository`— leen esta tabla, de modo que romper su contrato **no
  haría fallar las pruebas del dominio**, solo la compuerta global. Registra el cierre de **7.1**, la extracción a
  `asistencia_repository` —**el noveno**— con su comparador AST de **3 de 3**
  literales y **la comprobación de equivalencia de `(SQL, parámetros)`, retorno y
  conexiones en los dos caminos**; las **cinco** guardias que fallaron y el
  patrón de que **cada migración añade una enumeración de repositorios**, así que
  el número crece en uno cada vez; el **punto de decisión resuelto** que cerró la
  capa sin abrir una 7.2 dejando entonces **el N+1 en conexiones sin tocar**; y el cierre
  con su rollback —**local, porque la capa sigue sin publicar**—, su staging, su
  **verificación manual con la cobertura real que el usuario reportó** —solo el
  paso 3 consta— y los **riesgos que deja abiertos**.
- [07_VENTAS.md](./07_VENTAS.md): **bitácora cerrada** de la capa 7 para el
  dominio `ventas`. Fue la fuente de continuidad **hasta que se cerró
  `asistencia`**; sus once hallazgos siguen vivos y **no se corrigen desde la
  capa activa**. **Advertencia sobre este archivo**: su estado de publicación
  quedó desfasado, igual que le pasó a `07_NOTAS.md`. Lo declara «no publicada»
  y describe su rollback como puramente local, y **ya no es cierto** desde el
  push del 2026-08-20 a las 16:21:16; el renglón corregido está en «Estado
  actual», más arriba. La bitácora **no se editó** porque corregir una capa
  cerrada exige una orden explícita. Conserva el inventario de
  **7.0**: sus **2 archivos** —el recuento sale al revés que en `notas`—, sus 5
  entradas HTTP con **un solo modelo de permiso**, las **cuatro tablas
  escritas** incluida `pagos`, la línea base de consultas y conexiones de cinco
  caminos, los **doce supuestos resueltos** —once confirmados y **uno
  refutado**, el de los permisos— y los **once hallazgos sin corregir**,
  encabezados por la colisión del `ILIKE` que hace que anular una venta alcance
  los pagos de otra. Registra el cierre de **7.1**, la extracción a
  `ventas_repository` con su comparador AST de **17 de 17** literales y, sobre
  todo, **la comprobación de equivalencia de `(SQL, parámetros)` y de retorno en
  los seis caminos**, que cierra un hueco de evidencia que arrastran las capas 4
  a 7. Registra las seis guardias que fallaron y la lección de que **una prueba
  de hallazgo anclada a un archivo es también una guardia de línea base**; la
  decisión sobre dónde vive el `UPDATE pagos` con su alternativa **abierta**; el
  **punto de decisión resuelto** que cerró la capa sin abrir una 7.2; el cierre
  con su rollback —**local, porque la capa sigue sin publicar**—, su staging, su
  verificación manual **con la cobertura real que el usuario reportó** y los
  **riesgos que deja abiertos**. **Fuente de continuidad superada**: ese papel lo
  tiene ahora `07_ASISTENCIA.md`, la bitácora activa.
- [07_NOTAS.md](./07_NOTAS.md): **bitácora cerrada** de la capa 7 para el
  dominio `notas`, y **fuente de continuidad**. Registra el commit base
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
  romper un contrato ajeno no haría fallar las pruebas de `notas`. Registra
  también el cierre de **7.1**, la extracción a `notas_repository` con su
  comparador AST de **9 de 9** literales, las tres guardias que fallaron como
  señal esperada, la guardia de dashboard que se disparó fuera del dominio, y la
  decisión **sin precedente exacto** de llevar al repositorio las tres consultas
  de `nota_service` conservando en el servicio la propiedad de sus conexiones.
  Deja resuelto el **punto de decisión** que cerró la capa sin abrir una 7.2, el
  cierre con su rollback —que describe como **local, porque la capa seguía sin
  publicar**—, su staging, su verificación manual y los **riesgos que deja
  abiertos**. Fue la fuente de continuidad **hasta que se activó `ventas`**; sus
  doce hallazgos siguen vivos y **no se corrigen desde la capa activa**.
  **Advertencia sobre este archivo**: su estado de publicación quedó desfasado.
  Lo declara «no publicada» y describe su rollback como puramente local, y **ya
  no es cierto** desde el push del 2026-08-20; el renglón corregido está en
  «Estado actual», más arriba. La bitácora **no se editó** porque corregir una
  capa cerrada exige una orden explícita.
- [07_DASHBOARD.md](./07_DASHBOARD.md): **bitácora cerrada** de la capa 7 para
  el dominio `dashboard`, y **fuente de continuidad**. Registra el commit base
  `123637ee80895023ecece9c32df526ef4eddd1e5`, la autorización y el marcador de
  dominio que llegó sin rellenar, el alcance limitado a un solo dominio, las
  verificaciones heredadas aceptadas como pendientes y el riesgo propio de
  `response_model`. Conserva el inventario de **7.0**, ya **cerrada**: sus 7
  entradas HTTP con sus cuatro modelos de permiso, la línea base de consultas y
  **conexiones** por camino, los **siete supuestos heredados resueltos** —seis
  confirmados y uno refutado— y los **diez hallazgos originalmente registrados**.
  El primero, el `activo` ausente de las precondiciones de permiso, quedó
  corregido y publicado en `9f19089`; el segundo, las cuatro conexiones
  seriales, quedó reducido localmente a dos sin cambiar sus consultas. La
  resolución académica duplicada, las dos fórmulas de promedio y otros seis
  siguen abiertos. Registra también el cierre de **7.1**, la extracción a
  `dashboard_repository` con su comparador AST de **16 de 16** literales, las
  dos guardias que fallaron como señal esperada y la decisión sobre dónde viven
  las precondiciones de permiso. Deja abierto el **punto de decisión** que
  cerró la capa sin abrir una 7.2, el cierre con su rollback, su staging, su
  verificación manual y su estado de publicación, y los **riesgos que deja
  abiertos**. Fue la fuente de continuidad **hasta que se activó `notas`**; hoy
  conserva **ocho hallazgos abiertos** y la capa continúa cerrada.
- [06_ASIGNACIONES_ESTUDIANTES.md](./06_ASIGNACIONES_ESTUDIANTES.md): **bitácora
  cerrada** de la capa 6 y fuente de continuidad **hasta que se activó la capa
  7**. Registra el commit base
  `589cb6d`, el inventario de 6.0 con sus 19 entradas HTTP, dos tablas escritas y
  16 claves foráneas, los diez hallazgos originales —el lock frente a horarios
  solapados quedó **corregido el 2026-08-24 y publicado en `721f382`** y el código muerto
  duplicado que el usuario decidió conservar sigue abierto—, las cuatro
  extracciones de 6.1 a 6.5 con sus
  decisiones tomadas con evidencia, el supuesto de `storage` **refutado**, y el
  cierre de la capa con su rollback, su verificación manual local y la advertencia
  de que **no llegó a publicarse**. Fue la fuente de continuidad **hasta que se
  activó la capa 7**; los demás hallazgos que la bitácora no marca como
  corregidos siguen vivos. La corrección del lock conserva pendiente una prueba
  concurrente con PostgreSQL real, staging, despliegue comprobado y CI posterior.
- [05_PAGOS_TIPOS_PAGO.md](./05_PAGOS_TIPOS_PAGO.md): **bitácora cerrada** de la
  capa 5. Conserva sus hallazgos y el paso 2 acordado y no iniciado, la clave de
  idempotencia de `POST /pagos`. Registra también las correcciones puntuales
  posteriores al cierre: el lock parcial, el logging de fallos, una conexión por
  upsert y, el 2026-08-24, el mapeo local de los siete fallos de infraestructura
  a 500 con revisión del frontend y compuerta de 1107 pruebas. Esta última se
  publicó en `9a90462` y conserva pendiente staging, despliegue comprobado y
  evidencia de CI.
  Registra el commit base `f4d0913`, las
  verificaciones heredadas aceptadas como pendientes, el inventario de 5.0 con
  sus 19 entradas HTTP, seis tablas escritas, contratos, idempotencia y línea
  base de consultas, los **ocho hallazgos originales con su estado posterior**,
  incluidas correcciones y un hallazgo retirado, las
  extracciones de 5.1 a 5.3 con la unificación SQL autorizada y la decisión sobre
  dónde vive el contacto con `ventas`, y el cierre de la capa con su rollback,
  su verificación manual local y la advertencia de que **no llegó a publicarse**.
  Fue la fuente de continuidad **hasta que se activó la capa 6**; siguen vivos
  únicamente los que la bitácora no marca como corregidos o retirados.
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
  manual y riesgos residuales. Registra además la revalidación autorizada del
  2026-08-24: no se detectó `H>1`, `H=1` sigue siendo una hipótesis candidata,
  el valor 2 conserva cinco tokens por proceso y no habrá ampliación sin cota
  demostrada, reserva explícita y staging.
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
  lo que dejaron abiertas las capas 5 y 6 —la clave de idempotencia y los
  hallazgos de asignaciones todavía vigentes— y cuatro lecciones nuevas de la
  capa 6. Registra que el lock frente a horarios solapados quedó corregido
  localmente y que su prueba concurrente en PostgreSQL real sigue pendiente.
  Incluye
  las tres trampas que dejó la capa 3: el endpoint `-pooler`, los nombres sin
  cualificar que resuelve el `search_path`, y que los ensayos necesitan schema
  canónico, datos representativos y aislamiento no productivo; no requieren
  copiar datos de producción.
- [PLANTILLA_CAPA.md](./PLANTILLA_CAPA.md): estructura de la siguiente bitácora.
