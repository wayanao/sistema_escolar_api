# Prompt universal para continuar la evolución del backend

Este mismo prompt puede reutilizarse en cualquier chat o LLM con acceso de
lectura y escritura al repositorio. No presupone que exista una capa activa: el
índice maestro puede señalar una capa activa o un intervalo seguro entre capas.

El prompt transmite el procedimiento, no una copia del proyecto. Si el LLM no
puede abrir los archivos mencionados, debe pedir acceso al repositorio o los
documentos necesarios y detenerse, sin reconstruir su contenido de memoria.

```text
Vamos a continuar el programa de evolución segura del backend.

Antes de actuar, identifica y declara tu modo de acceso:
- si estás dentro del mismo checkout local del repositorio, puedes validar Git
  y trabajar sobre los commits locales aunque no exista push;
- si solo ves GitHub, los commits locales no publicados son invisibles y no
  puedes confirmar el estado del checkout del usuario: informa la limitación y
  detente antes de modificar o activar una capa;
- si solo recibiste archivos adjuntos, puedes analizarlos, pero no afirmar que
  la rama o el árbol están validados ni modificar el proyecto de forma segura;
  solicita acceso al checkout correspondiente y detente.

Nunca declares que el árbol está limpio sin ejecutar git status en el checkout
local que contiene el trabajo.

Lee completamente y en este orden:
1. docs/modularizacion/README.md
2. determina el estado exclusivamente desde ese índice:
   - si marca exactamente una bitácora como Activa, léela completamente;
   - si no hay una capa activa, lee la bitácora cerrada más reciente que el
     índice conserve como fuente de continuidad o con verificaciones pendientes;
   - si el índice es ambiguo, marca varias capas activas o contradice la
     bitácora, informa el problema y detente;
3. las instrucciones locales del repositorio, si existen

Si no puedes abrir esos archivos, no adivines su contenido ni el estado del
programa. Pide acceso al repositorio o solicita los documentos y detente.

Si existe una capa activa, inspecciona únicamente la documentación, archivos
fuente y pruebas relacionados con su primera subcapa pendiente. Si no existe
una capa activa, no inspecciones código de la capa siguiente ni la actives por
inferencia. No leas historiales globales ni todo el repositorio salvo que la
bitácora correspondiente dirija a una sección concreta.

Antes de modificar:
1. Confirma la rama acordada.
2. Confirma que git status esté limpio.
3. Comprueba el commit base registrado en la bitácora relevante, activa o
   cerrada como fuente de continuidad.
4. Revisa que todo commit posterior al base esté explicado en esa bitácora.
5. Si hay cambios anteriores, una rama incorrecta o divergencia no documentada,
   informa el problema y no mezcles ni sobrescribas cambios.

Cuando no haya una capa activa:
- una instrucción genérica como "continúa" no autoriza a activar la siguiente:
  informa el estado y detente;
- informa qué capa se cerró, cuál sigue en espera y qué verificación permanece
  pendiente, si existe;
- si la capa cerrada conserva una verificación pendiente, no la marques como
  cumplida. Antes de activar la siguiente, pide una decisión explícita entre
  completar esa verificación o continuar localmente aceptando que siga
  pendiente, y registra la decisión y el riesgo;
- solo si el usuario autoriza explícitamente activar la capa siguiente, crea su
  bitácora desde docs/modularizacion/PLANTILLA_CAPA.md, registra el HEAD limpio
  vigente como commit base, actualiza el índice maestro y detente;
- no implementes la primera subcapa de la nueva capa en ese mismo turno, salvo
  que el usuario lo autorice de forma explícita e inequívoca.

Trabaja exclusivamente en la capa activa e implementa únicamente su primera
subcapa pendiente. No inicies otra subcapa en el mismo turno. Conserva rutas,
payloads, status codes, permisos, tenant, ownership, SQL observable,
transacciones y comportamiento actual, salvo que la bitácora autorice de forma
explícita un cambio concreto.

No agregues funciones nuevas, no hagas rediseños, no corrijas asuntos ajenos,
no cambies tecnologías y no crees abstracciones compartidas sin dos usos reales.
Antes de una extracción importante, agrega o conserva pruebas de
caracterización.

Al terminar la subcapa:
- ejecuta las pruebas específicas y las verificaciones exigidas;
- ejecuta git diff --check;
- revisa que el diff pertenezca exclusivamente a la subcapa;
- actualiza la bitácora activa con archivos, comandos y resultados;
- registra decisiones, riesgos y la siguiente acción exacta;
- informa cuál es la siguiente subcapa, pero no la inicies.

Cuando sea la última subcapa de una capa, ejecuta también la compuerta global,
documenta staging, rollback y verificación manual, y actualiza el índice maestro.
Marca la capa cerrada y deja la siguiente en espera. No actives la capa
siguiente sin mi orden explícita.

No hagas commit, push, deploy, migraciones reales ni acceso a producción.
Yo revisaré los cambios y controlaré la publicación.

Para transferir el trabajo entre LLM:
- otro LLM que abra este mismo checkout puede continuar desde un commit local
  sin push;
- un LLM que solo consulte GitHub verá únicamente los commits publicados;
- no presentes una ejecución de GitHub Actions como verificada hasta que exista
  un push autorizado y evidencia del run.
```

## Uso desde otro chat o LLM

1. Abrir un chat nuevo con acceso a la carpeta `sistema_escolar_api`.
2. Copiar el bloque anterior sin agregar el historial del chat viejo.
3. Si no hay una capa activa y se desea iniciar la siguiente, agregar una orden
   explícita como: "Autorizo activar la capa N; acepto mantener registrada la
   verificación remota pendiente de la capa anterior; crea su bitácora,
   actualiza el índice y detente sin implementar todavía una subcapa". Si no
   existe una verificación pendiente, se omite esa aceptación.
4. Verificar que el resumen del asistente coincida con el índice y la bitácora
   en rama, estado, capa, subcapa y commit base antes de permitir cambios.

Un commit local es suficiente para continuar con otro LLM que abra esta misma
carpeta; no requiere push. Un LLM que solo vea GitHub necesitará que los commits
se publiquen, y uno sin acceso al repositorio necesitará que se le compartan los
archivos requeridos.

Si dos asistentes indican capas diferentes, prevalece el estado guardado en
`README.md` y en la bitácora de continuidad, no la memoria de la conversación.

## Cómo se usan las autorizaciones puntuales

Este archivo llegó a contener autorizaciones de uso inmediato para activar las
capas 3, 4 y 5. Se consumieron el 2026-08-13, el 2026-08-14 y el 2026-08-15,
respectivamente, y se retiraron. La lección no fue «no guardar autorizaciones»,
sino que **una autorización guardada debe llevar su propia condición de
caducidad**: si el estado documental ya cambió, no debe aplicarse.

La de la capa 5 funcionó como estaba previsto: su condición era «válida solo
mientras el índice siga indicando que no existe una capa activa y que la capa 5
está en espera», se comprobó que se cumplía y el usuario la confirmó además de
forma explícita en el turno.

Al final de este archivo hay una preparada para la **capa 6**, con la misma
condición de caducidad. **No se dispara sola**: es un texto que el usuario decide
pegar. Si no la pega, la capa 6 sigue en espera.

## Estado del programa al 2026-08-16 (capa 5 cerrada)

Lo que sigue es un resumen para orientarse; **el estado vivo está en
`docs/modularizacion/README.md`**, que es lo que manda si algo no coincide.

- Capas 0, 1, 2, 3, 4 y 5 **cerradas**. **No hay capa activa.**
- Siguiente capa: **6, asignaciones y estudiantes, en espera**.
- La capa 5 cerró el 2026-08-16 modularizando pagos y tipos de pago:
  `pagos_controller.py` pasó de **717 a 633 líneas** y de **23 sentencias SQL
  inline a 3**; la persistencia vive en `app/repositories/pagos_repository.py`
  con 16 funciones que reciben el cursor. La suite pasó de 606 a **660**.
- La capa 5 es **exclusivamente una refactorización** y **no tocó la base de
  datos en absoluto**, ni siquiera para leer. Su rollback es puramente de código.
- Que nada observable cambió se demostró con dos evidencias: un comparador AST
  contra el commit base con **conjunto de SQL idéntico** y 19 de 21 literales
  byte a byte, y **54 pruebas de caracterización** escritas antes de cada
  extracción, ninguna de las cuales cambió de expectativa.
- Verificación manual de la capa 5: **hecha por el usuario y correcta**, en local
  contra el árbol de trabajo. **Al cerrar no había push ni despliegue.**
- Verificaciones heredadas que siguen **pendientes y aceptadas**: el valor
  operativo final de `DB_STATEMENT_TIMEOUT_MS` de la capa 1 y que GitHub Actions
  no se ha verificado desde la capa 0. Sigue sin rotar la credencial
  privilegiada que se compartió en la capa 4.

### Lo que quien continúe debe saber antes de tocar la base

1. **`apply_migration.py` se niega sobre el endpoint `-pooler`.** Allí su lock de
   sesión no impide dos ejecuciones simultáneas: se comprobó. Para migrar hay
   que apuntar `DATABASE_URL` al endpoint directo.
2. **`pg_get_constraintdef`, `pg_get_indexdef` y la migración base devuelven
   nombres sin cualificar**, que se resuelven con el `search_path`. Cualquier
   cosa que copie estructura entre schemas debe fijarlo al destino, o creará
   referencias cruzadas. Ya pasó una vez y falló por casualidad.
3. **Validar el SQL contra el schema real es barato y encuentra cosas.** Basta
   envolver el cursor para convertir cada `execute()` en su `EXPLAIN` y llamar a
   las funciones reales del repositorio: valida lo que el código ejecuta, no una
   transcripción. Así se demostró que el SQL anterior fallaba con `42703`. Sirve
   incluso sobre una rama **sin datos**.
4. **Para medir, producción en solo lectura es la mejor opción**, y esto corrige
   una recomendación anterior de este mismo archivo. `EXPLAIN ANALYZE` sobre
   `SELECT` no escribe y devuelve solo plan y tiempos, **sin ningún dato
   personal**. Una rama sin datos no mide nada —el planificador siempre elige
   recorridos secuenciales—, y una rama con datos reales expone información de
   menores sin añadir fidelidad. Si hace falta conectar, usar `service=` y
   `SET TRANSACTION READ ONLY` con `rollback`.
5. **No aceptar el resumen de otro asistente como estado.** Al retomar la capa 4
   desde otro chat, el resumen recibido decía «nueve archivos modificados, cinco
   commits» y la realidad era árbol limpio y seis commits. Validar siempre
   `git status`, el base y la continuidad por cuenta propia.
6. **Cuando se repara algo roto no hay un “antes” con el que comparar.** Las
   pruebas fijan lo que decidió quien escribió el código. En ese caso la
   verificación manual del usuario contra importes que conoce **es la evidencia
   decisiva** y no puede delegarse.
7. **Caracterizar antes de extraer se paga solo.** En la capa 5 las subcapas 5.1
   y 5.2 no tuvieron que cambiar ni una expectativa de prueba: las 54 pruebas
   escritas antes de mover ya demostraban que payloads, conteos, transacción y
   ciclo de vida seguían iguales. Si la extracción hubiera roto algo, habrían
   fallado solas.
8. **Comparar el SQL con AST, no a ojo.** Extraer literales con `ast` desde
   `git show BASE:archivo` y comparar el conjunto contra el código nuevo demuestra
   que no se perdió ni se inventó ninguna sentencia. Compara siempre contra el
   **commit base de la capa**, no contra el turno anterior, o los cambios se
   acumulan sin que nadie los vea.
9. **Dos literales SQL idénticos salvo la sangría son frecuentes** cuando una
   rama vive dentro de un bucle y otra fuera. Unificarlos cambia la cadena en
   memoria sin cambiar lo que recibe PostgreSQL. Es una decisión del usuario, no
   del asistente: en la capa 5 se pidió y se autorizó explícitamente. El espacio
   final de una línea se conserva con un escape explícito, para no alterar el
   valor y mantener `git diff --check` limpio.
10. **Preguntar contra qué artefacto se verificó.** Al cerrar la capa 5 el
    usuario dijo «ya verifiqué», pero el trabajo no estaba commiteado ni
    publicado: producción corría el código anterior. Verificación local y
    verificación en producción no son la misma evidencia; hay que confirmar cuál
    fue antes de registrarla.
11. **El nombre de un archivo de prueba no dice qué módulo parchea.** Un
    `monkeypatch` en `test_pagos_adelantados.py` puede apuntar a
    `reportes_controller`. En la capa 5 se registró un hallazgo falso por
    deducirlo del nombre; hay que leer el argumento de destino.

## Trabajo registrado fuera del alcance de la capa activa

Registrado y sin hacer. Nada de esto es urgente ni bloquea a la capa 5, y nada
de esto entra en ella por inferencia: requiere una orden explícita.

- **Colisión de mayúsculas en el servicio de reportes.**
  `app/services/reportes_financieros.py` indexa por `str(nombre).lower()` con
  asignación simple, mientras el SQL agrupa respetando mayúsculas. Si un
  estudiante tuviera dos pagos cuyo concepto solo difiera en el caso, un importe
  **desaparecería del informe en silencio**. Se midió sobre producción: **0
  casos hoy**, así que es latente. El arreglo limpio es agrupar por
  `LOWER(...)` en las dos consultas del repositorio, una línea cada una, y hoy
  sería un no-op verificable por comparación.
- **`/estado-cuenta/curso`**, consumidor distinto del de reportes, sigue
  repitiendo el cálculo y llega a doce consultas por estudiante.
- **14 índices duplicados** en `tenant_2005`, medidos y descartados
  deliberadamente en la capa 3.
- **`POST /pagos`: clave de idempotencia, paso 2 pendiente.** El 2026-08-17 se
  corrigió la mitad del problema con autorización explícita: el camino de pago
  normal ya toma un `pg_advisory_xact_lock` por estudiante como primera
  sentencia, así que **dos peticiones simultáneas ya no cobran dos veces** —la
  segunda espera, relee la deuda y se rechaza—. Lo que **sigue abierto** es el
  duplicado parcial separado en el tiempo: dos envíos idénticos de 50 sobre una
  deuda de 100 entran los dos, porque sin una clave de idempotencia el servidor
  no puede distinguir un reintento de una segunda cuota legítima. El paso 2
  —columna con `UNIQUE`, migración y cambio en `frontend-react`— está descrito en
  `05_PAGOS_TIPOS_PAGO.md` y **no se ha iniciado**.
- **No hay filtro de ownership por pago dentro del tenant**: `anular_pago` anula
  el `pago_id` que reciba sin comprobar de quién es. El aislamiento entre
  colegios sí lo garantiza el `search_path`.
- **Siete funciones de `tipos_pagos_controller` capturan `Exception` a secas** y
  devuelven `None`/`False`; un fallo de infraestructura llega al cliente como 400
  o 404 en vez de 500.
- **Los dos upsert de tipos de pago abren dos conexiones por petición**, porque
  releen el estado después del `commit` con una conexión propia.
- **Código duplicado byte a byte**: `pagos_controller._tabla_pagos_aplicaciones_existe`
  y `cobros.tabla_pagos_aplicaciones_existe` son la misma función. La pública ya
  tiene dos consumidores reales, así que deduplicar no crearía una abstracción
  nueva, y **ninguna prueba depende de que sigan separadas**.
- **`_obtener_saldo_concepto` es una indirección vacía** que solo reenvía a
  `cobros.obtener_saldo_concepto`. Un consumidor; borrarla es una línea.
- **Un pago simple cuesta 12 consultas, once de ellas lecturas** para recalcular
  la deuda entera del estudiante y compararla con el monto. No es un N+1 —no
  depende del número de estudiantes— pero es el camino de escritura más caro.
- **`actualizar_configuracion_tipo_pago` compone SQL con f-string.** Hoy **no hay
  nada que corregir**: los nombres de columna salen de la lista fija
  `_ADVANCED_COLUMNS` intersecada con el schema real, así que no es inyectable.
  Queda anotado como guarda: ninguna extracción futura debe abrir esa lista a
  entrada del cliente.
- Heredados: valor operativo final de `DB_STATEMENT_TIMEOUT_MS`, ausencia de
  evidencia de GitHub Actions desde la capa 0, y la credencial privilegiada de la
  capa 4 **sin rotar**.

## Autorización de uso inmediato: activar la capa 6

Válida **solo mientras el índice maestro siga indicando que no existe una capa
activa y que la capa 6 está en espera**. Si el estado ya cambió, no la
reutilices: vuelve a determinarlo desde el índice.

Se copia el bloque universal del principio y se añade inmediatamente después:

```text
Autorizo activar únicamente la capa 6, Asignaciones y estudiantes.

Acepto continuar manteniendo pendientes las verificaciones heredadas: el valor
operativo final de DB_STATEMENT_TIMEOUT_MS de la capa 1 y la ausencia de
evidencia de GitHub Actions desde la capa 0. Registralas como pendientes,
conserva su riesgo y no las marques como cumplidas.

Esta autorizacion permite solamente la activacion documental. No autoriza
inspeccionar codigo de la capa 6, implementar 6.0, tocar la base de datos, hacer
deploy, commit o push. Despues de activar la capa, detente.

En el mismo checkout local:

1. Lee y aplica completamente el protocolo universal anterior.
2. Valida main, git status, el HEAD limpio vigente, origin/main y la continuidad
   desde el commit base de la capa 5,
   f4d091329f84bcdd100b1bf0c70c02a0e32ee138, comprobando que todo commit
   posterior este explicado en 05_PAGOS_TIPOS_PAGO.md.
3. Confirma que la capa 5 esta cerrada, que la capa 6 sigue en espera y que no
   existe otra capa activa. Si hay divergencia o un commit sin explicar, detente.
4. No uses ningun hash de memoria: comprueba primero el HEAD limpio real.
5. No declares GitHub Actions verificada solo porque HEAD coincida con
   origin/main; exige evidencia del run.
6. Comprueba si la capa 5 llego a publicarse. Al cerrarla no habia push y
   produccion corria f4d0913. Informa lo que encuentres, no lo supongas.
7. Crea docs/modularizacion/06_ASIGNACIONES_ESTUDIANTES.md partiendo de
   docs/modularizacion/PLANTILLA_CAPA.md.
8. Registra el HEAD limpio vigente como commit base, rama main, estado Activa,
   primera subcapa pendiente 6.0 y codigo de producto modificado al activar:
   ninguno.
9. Define el objetivo solo desde el indice maestro: separar los dominios de
   asignaciones y estudiantes con contratos estables, trabajando cada uno en
   subcapas, evitando una extraccion conjunta masiva, y protegiendo permisos,
   relaciones academicas, archivos e historial.
10. Deja 6.0 como inventario, contratos y caracterizacion. No inventes detalles
    de implementacion sin inspeccionarlos en un turno posterior. No decidas aun
    el desglose de 6.1 en adelante.
11. Ten presente que estos dominios son mas grandes que los financieros y que
    tocan archivos, no solo filas:
    - la capa 3 anadio 26 claves foraneas a tenant_2005, asi que inserciones y
      borrados pueden fallar donde antes pasaban en silencio;
    - calcular_deudas_estudiante de cobros.py ya se usa desde estudiantes, y la
      capa 4 fijo contratos de lectura que dependen de el;
    - app/services/storage.py maneja archivos; un rollback de datos no deshace un
      archivo ya escrito, y eso cambia como hay que documentar el rollback.
12. Actualiza docs/modularizacion/README.md para marcar unicamente la capa 6
    como Activa, enlazar su bitacora y dejar 6.0 pendiente.
13. Ejecuta git diff --check, comprueba el whitespace del archivo nuevo y
    verifica que el alcance contenga exclusivamente README.md y
    06_ASIGNACIONES_ESTUDIANTES.md.
14. Informa el commit base, la primera subcapa pendiente, las verificaciones
    heredadas y cualquier evidencia remota disponible. Detente sin inspeccionar
    ni implementar 6.0.

No hagas commit, push, deploy, migraciones reales ni acceso a produccion. Yo
revisare los cambios y controlare su publicacion.
```
