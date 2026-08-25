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
capas 3, 4, 5 y 6. Se consumieron el 2026-08-13, el 2026-08-14, el 2026-08-15 y
el 2026-08-17, respectivamente, y se retiraron. Al final de este archivo hay una
preparada para la **capa 7**. La lección no fue «no guardar autorizaciones», sino
que **una autorización guardada debe llevar su propia condición de caducidad**:
si el estado documental ya cambió, no debe aplicarse. **Ninguna se dispara
sola**: son textos que el usuario decide pegar.

La de la capa 5 funcionó como estaba previsto: su condición era «válida solo
mientras el índice siga indicando que no existe una capa activa y que la capa 5
está en espera», se comprobó que se cumplía y el usuario la confirmó además de
forma explícita en el turno.

La de la capa 6 funcionó igual el 2026-08-17: la condición se cumplía y el
usuario ordenó activarla de forma explícita. Se comprobó además, antes de
aplicarla, que uno de sus supuestos había quedado desfasado —el índice seguía
declarando la capa 5 sin publicar cuando el reflog ya registraba el push—, y esa
corrección documental se pidió y se autorizó por separado.

## Estado del programa al 2026-08-19 (capa 7 cerrada para `dashboard`)

Lo que sigue es un resumen para orientarse; **el estado vivo está en
`docs/modularizacion/README.md`**, que es lo que manda si algo no coincide.

- Capas 0 a 6 **cerradas**. La **capa 7 quedó cerrada para el dominio
  `dashboard`** el 2026-08-19. **No hay capa activa.**
- Sus dos subcapas, **7.0 y 7.1**, están cerradas, y el usuario decidió **cerrar
  la capa ahí** sin abrir una 7.2 para `response_model`. La **verificación manual
  la ejecutó él el 2026-08-19, en local, completa y con resultado correcto**; el
  artefacto se confirmó antes de registrarla y no había ambigüedad, porque `HEAD`
  coincidía con `origin/main`. Limitación que sigue vigente: **fue local**, así
  que nadie ha repetido el guion contra el despliegue.
- **La capa está publicada y desplegada**: el reflog de `origin/main` registra
  `update by push` de `8591816`, que arrastra sus cuatro commits. Producción ya
  corre este código.
- Resultado de la migración de `dashboard`: **7 entradas HTTP**, todas `GET` y
  todas de **solo lectura**, con **cero tablas escritas** y **cero transacciones
  propias**. `dashboard_controller.py` pasó de **336 a 146 líneas** y de **8
  sentencias SQL inline a 0**; la persistencia vive en
  `app/repositories/dashboard_repository.py`, ocho funciones que reciben el
  cursor más dos fragmentos privados. **42 pruebas de caracterización** nuevas y
  la suite de **714 a 756**.
- Como la 5 y la 6, **no tocó la base de datos**, ni siquiera para leer.
  Comparador AST contra el commit base: **16 de 16 literales byte a byte**, sin
  una sola autorización de cambio de texto SQL.
- **Un supuesto heredado resultó falso**: `dashboard` no concentraba «varias
  consultas de promedios por estudiante». Cada panel se resuelve con **una sola
  consulta agregada** y **no hay N+1**. La línea base más cara abría **cuatro
  conexiones en serie**; una corrección puntual las redujo a **dos** sin cambiar
  sus seis consultas. La asignación académica aún se resuelve **dos veces**.
- No hay capa activa. Las correcciones puntuales de `dashboard` no la
  reactivaron ni autorizan otro dominio. Una instrucción genérica de continuar
  tampoco activa la siguiente capa.
- Cerrar la capa no canceló sus diez hallazgos originales. Los dos primeros
  quedaron corregidos el 2026-08-25 con órdenes explícitas: las precondiciones
  exigen `activo = TRUE` —publicado en `9f19089`— y comparten una conexión —aún
  local—. La compuerta más reciente terminó con **1120 pruebas** y **ocho
  hallazgos siguen abiertos**. Staging y verificación manual de ambas, y
  publicación/CI de la segunda, permanecen pendientes.
- La capa 6 cerró el 2026-08-17 modularizando asignaciones y estudiantes en cinco
  subcapas, cada dominio por separado: `estudiante_controller.py` pasó de **519 a
  381 líneas** y de 11 sentencias SQL inline a **0**; `asignacion_controller.py`
  de **1093 a 762** y de 41 a **1**, la introspección de esquema que se decidió
  conservar; y `app/routes/asignaciones.py` perdió el **único SQL de dominio que
  vivía en la capa HTTP** de todo el programa. La persistencia vive en
  `estudiantes_repository` —11 funciones— y `asignaciones_repository` —33—.
- **El supuesto de los archivos era falso.** La capa 6 se activó anticipando que
  estos dominios escribirían archivos vía `app/services/storage.py` y que por eso
  el rollback dejaría de ser reversible. 6.0 lo **refutó con prueba**: solo
  branding y plan de clases usan ese servicio. Que la activación lo registrara
  como *no verificado* es lo que permitió corregirlo sin arrastrar el error.
  **Sigue siendo cierto para la capa 7**: plan de clases sí escribe archivos.
- Verificación manual de la capa 6: **hecha por el usuario y correcta**, en local
  contra el árbol de trabajo. Se confirmó el artefacto antes de registrarla.
  Al cerrarla no había push; **se publicó poco después**, el mismo 2026-08-17, en
  `bf075a0`. Como un push a `main` dispara el despliegue, **producción ya corre
  la capa 6**. La verificación siguió siendo local: nadie la ha repetido contra
  el despliegue.
- La capa 5 cerró el 2026-08-16 modularizando pagos y tipos de pago:
  `pagos_controller.py` pasó de **717 a 633 líneas** y de **23 sentencias SQL
  inline a 3**; la persistencia vive en `app/repositories/pagos_repository.py`
  con 16 funciones que reciben el cursor.
- La capa 5 es **exclusivamente una refactorización** y **no tocó la base de
  datos en absoluto**, ni siquiera para leer. Su rollback es puramente de código.
- Que nada observable cambió se demostró con dos evidencias: un comparador AST
  contra el commit base con **conjunto de SQL idéntico** y 19 de 21 literales
  byte a byte, y **54 pruebas de caracterización** escritas antes de cada
  extracción, ninguna de las cuales cambió de expectativa.
- Verificación manual de la capa 5: **hecha por el usuario y correcta**, en local
  contra el árbol de trabajo. Al cerrarla no había push; **se publicó después**,
  el 2026-08-17, junto con las tres primeras correcciones puntuales de abajo.
- **Cuatro correcciones puntuales posteriores al cierre**, cada una autorizada
  explícitamente y registrada en `05_PAGOS_TIPOS_PAGO.md`. La capa **no se
  reabrió**: son correcciones sobre hallazgos que la capa dejó anotados.
  1. **Candado de registro de pagos**: `registrar_pago_controller` toma un
     `pg_advisory_xact_lock` por estudiante, así que un doble clic ya no cobra
     dos veces. La clave de idempotencia sigue pendiente.
  2. **Registro de fallos absorbidos** en `tipos_pagos_controller`: los siete
     `except Exception` ya dejan traceback.
  3. **Una sola conexión por upsert**: los dos upsert de tipos de pago releen con
     su cursor antes de confirmar. Cerró además una ventana en la que un `commit`
     correcto se reportaba como 400.
  4. **Mapeo de infraestructura a 500**, corregido el 2026-08-24 tras
     revisar `frontend-react`: conserva los 400/404/409 de dominio y no filtra
     detalles internos. El reflog local de `origin/main` registra su push en
     `9a90462`; staging, despliegue comprobado y CI siguen pendientes.
- **Corrección puntual posterior al cierre de `asistencia`**, autorizada y
  ejecutada localmente el 2026-08-24 sin reabrir la capa: el permiso de asignación
  se valida una vez y la pertenencia de todo el lote en una consulta batch. El
  perfil pasó de `N+1`/`2N+1` a **2/3 conexiones totales** como admin/profesor.
  Conserva contratos y aislamiento tenant; `frontend-react` no cambió. El
  reflog local de `origin/main` registra su push en `bbf3bfb`; staging,
  verificación manual, despliegue comprobado y CI siguen pendientes.
- **Corrección puntual posterior al cierre de la capa 6**, autorizada y
  ejecutada localmente el 2026-08-24 sin reabrirla: las precondiciones existentes
  de profesor y curso toman `FOR NO KEY UPDATE` en orden fijo y serializan altas
  o ediciones que podrían solaparse. Conserva 12/10 consultas, contratos y
  aislamiento tenant; no requiere frontend ni migración. El reflog local de
  `origin/main` registra su push en `721f382`. La prueba concurrente con
  PostgreSQL real, staging, despliegue y renovación comprobada de workers y CI
  siguen pendientes.
- Suite al día: **1116 pruebas**, exit 0. Partió de 606 al activar la capa 5 y de
  669 al activar la capa 6.
- **Un hallazgo se retiró** tras revisarlo: el «filtro de ownership por pago» no
  era un hueco. Ver el detalle en la bitácora antes de volver a levantarlo.
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
12. **Un supuesto heredado se marca como no verificado y se comprueba en la
    subcapa 0.** La capa 6 se activó anticipando que sus dominios escribían
    archivos y que eso hacía irreversible el rollback. Era **falso**, y se supo
    porque la activación lo registró como *no verificado* en vez de darlo por
    bueno. Un riesgo copiado de un documento anterior no es evidencia.
13. **El comparador AST confunde docstrings con SQL.** Un docstring que mencione
    `UPDATE` o `DELETE` en prosa aparece como sentencia nueva. Hay que excluir
    los docstrings con `ast.get_docstring` antes de comparar, o se pierden
    minutos persiguiendo falsos positivos. Ocurrió en 6.1.
14. **Una guardia que fija un defecto debe fallar cuando se corrija.** 6.0 dejó
    una prueba que afirmaba que la ruta `/mis-clases` conservaba su SQL inline;
    6.5 lo movió y la prueba **falló**, que era exactamente la señal esperada, y
    se sustituyó por su versión positiva. Es el mismo patrón que 3.2 y 3.3b. Si
    una guardia así falla, hay que preguntarse primero si la corrección era el
    objetivo del turno, no «arreglarla» a ciegas.
15. **Cada mitad de una comprobación puede ir a un sitio distinto.** En 6.4,
    `asignacion_tiene_historial` se partió: la consulta a
    `information_schema.columns` **se quedó** en el controlador —convención de
    5.3: la introspección de esquema vive junto al código que la necesita— y la
    que busca filas **se movió** al repositorio. Preguntar por el esquema y
    preguntar por los datos no son lo mismo.
16. **Una autorización guardada puede llegar con su marcador sin rellenar.** La
    de la capa 7 exigía nombrar el dominio y se pegó con `DOMINIO` literal. Lo
    correcto es **detenerse y preguntar**, no deducirlo: activar sin nombrarlo
    habría dejado el alcance abierto, que es lo contrario de lo que hace segura
    una capa.
17. **Los literales SQL se copian por rango de líneas, no se transcriben.** En
    7.1 un script copió los rangos exactos del controlador al repositorio, así
    que cada cadena viaja con **su sangría original** aunque el código que la
    rodea cambie de nivel. Python permite cualquier indentación en una línea de
    continuación dentro de paréntesis, así que el literal no necesita moverse.
    Por eso el comparador dio 16 de 16 sin negociar un solo cambio de texto.
18. **El directorio de trabajo del shell puede volver al repositorio
    equivocado.** Al empezar 7.1, la primera comprobación de Git se ejecutó
    contra otro repositorio y devolvió un `HEAD` que no existe en esta historia.
    Se detectó porque el commit base «no era un nombre de commit válido».
    Comprobar `git rev-parse --show-toplevel`, no solo `git status`.
19. **Los finales de línea se comprueban con bytes, no con `grep`.** Un patrón
    mal escrito dio CRLF donde el repositorio usa LF, y los archivos generados
    quedaron mezclados. Contar `b'\r\n'` sobre los bytes del archivo es la
    comprobación fiable; el aviso de `git diff --check` sobre LF/CRLF es de
    `core.autocrlf` y **no** es un error de whitespace.
20. **Una excepción deliberada debe quedar aislada y documentada hasta que se
    autorice cambiarla.** Las dos precondiciones de permiso de `dashboard` se
    mantuvieron en `dashboard_repository`, separadas de las consultas activas de
    `asignaciones_repository`. El 2026-08-25 la orden explícita permitió añadir
    `activo = TRUE` sin mover recursos ni ampliar el cambio a otro dominio.

## Trabajo registrado fuera del alcance de cualquier capa activa

Registrado y sin hacer. Nada de esto bloquea a la capa que se active, y nada de
esto entra en ella por inferencia: requiere una orden explícita.

### Lo que dejó abierto la capa 7 en `dashboard`

7.0 registró diez hallazgos. Los dos primeros quedaron corregidos el
2026-08-25; **ocho siguen abiertos**. Cerrar la capa no los cancela.

- ~~**Las dos precondiciones de permiso ignoraban `activo`.**~~ **Corregido
  y publicado en `9f19089` el 2026-08-25**: `profesor_tiene_curso_controller` y
  `profesor_tiene_asignacion_en_curso_controller` exigen ahora
  `activo = TRUE`, conservando parámetros, conteos y mensajes 403. La guardia
  negativa se sustituyó por una positiva. No se amplió el cambio a la consulta
  agregada, rankings ni UX del frontend.
- ~~**Hasta cuatro conexiones por petición**, en serie y sin anidar, en el
  camino de notas con asignación.~~ **Corregido localmente el 2026-08-25**: las
  tres precondiciones comparten una conexión y la lectura final conserva otra;
  el máximo baja a **dos** y se mantienen 6/5 consultas para profesor/admin.
- **La asignación académica se resuelve dos veces** en ese camino. Se conservó
  a propósito porque eliminarla no era necesario para reducir conexiones y
  cambiaría el SQL observable. Es el siguiente hallazgo independiente.
- **Dos definiciones distintas de «promedio» en el mismo panel**: notas altas y
  bajas promedian **los promedios por clase**; los rankings promedian **las notas
  planas**. Con 4,0 en una clase de dos notas y 2,0 en otra de seis, la primera
  da 3,00 y la segunda 2,50. Estudiantes usa una **tercera**, `ROUND(..., 1)`.
- **Las siete entradas absorben `Exception`, responden 400 y devuelven
  `str(e)`** en el `detail`, sin registrar nada: un error de PostgreSQL puede
  llegar al navegador. Misma familia que el hallazgo de `tipos_pagos_controller`,
  pero aquí además **se devuelve el mensaje interno**.
- **El filtro de rendimiento consulta la base desde la capa de rutas** y **fuera**
  del `try/except`, así que un fallo de infraestructura ahí sale como **500** y
  no como el 400 del resto del endpoint.
- **`dias` se valida dos veces con criterios divergentes**: la ruta responde 422
  fuera de 0..31 y el controlador recorta en silencio. Por HTTP el recorte es
  inalcanzable.
- **Cuarta pareja de literales SQL gemelos** del programa: los dos rankings solo
  difieren en el signo y el orden. No se unifican sin autorización.
- **f-strings en SQL, hoy no inyectables**, en `leer_estudiantes_por_promedio` y
  en el fragmento del rango de cumpleaños. Guarda: no abrirlas a entrada del
  cliente.
- **`periodo: int = 1` es un parámetro de ruta con defecto inalcanzable** en los
  dos rankings.
- **`response_model` y los errores de dominio no se añadieron**, por decisión
  explícita del usuario al cerrar. No son deuda de la capa: son trabajo
  disponible que exigiría una orden.

### Lo que dejó abierto la capa 6

- ~~El alta y la edición de asignaciones no toman ningún lock.~~ **Corregido
  el 2026-08-24**, con autorización explícita y sin reabrir la capa:
  las lecturas existentes de profesor y curso activos toman `FOR NO KEY UPDATE`
  en orden profesor → curso. Esto conserva las 12/10 consultas de alta/edición,
  rutas, payloads y 400/409, y serializa a los escritores que comparten profesor
  o salón sin advisory keys ni migración. La compuerta terminó con **1116
  pruebas**. El reflog local de `origin/main` registra su push en `721f382`.
  Sigue pendiente demostrar la espera y revalidación con dos
  conexiones PostgreSQL reales en staging, renovar todos los workers al
  publicar y obtener evidencia posterior de CI; no atribuyas esas verificaciones
  todavía.
- **`GET /estudiantes/{id}` devuelve `SELECT *`**, así que su contrato observable
  es el esquema entero de la tabla: añadir una columna cambia la respuesta de la
  API sin tocar código.
- **`asignacion_tiene_historial` cuesta hasta 14 consultas** para responder sí o
  no: dos por cada una de sus siete tablas, sin caché entre tablas ni peticiones.
- **Dos rarezas de status code**: `PUT /estudiantes/{id}` sobre un inexistente
  responde 200 con un mensaje, mientras `PATCH .../estado` responde 404; y
  `DELETE /asignaciones/{profesor_id}/{curso_id}` responde 200 aunque no
  encuentre nada, mientras `DELETE /asignaciones/{id}` responde 404.
- **`obtener_clases_profesor_controller` está definida dos veces y ninguna tiene
  consumidores**, con SQL divergente entre copias. El usuario decidió el
  2026-08-17 **conservarlas**; una guardia de prueba falla si alguien las
  conecta. Retirarlas sigue siendo posible con una orden explícita.
- **Tres parejas de literales SQL gemelos sin unificar**, conservadas byte a
  byte: las dos formas de `SET activo = FALSE` y las dos de `buscar_curso_activo`.
  Unificarlas es legítimo y no cambia lo que recibe PostgreSQL, pero es decisión
  del usuario y no se pidió.
- **`POST /estudiantes` descarta el mensaje del controlador**: la ruta construye
  su propia respuesta. El cliente nunca ve el texto que devuelve el controlador.

### Lo que sigue abierto de capas anteriores

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
- ~~Filtro de ownership por pago~~. **Retirado el 2026-08-17: no era un hueco.**
  Solo alcanza el endpoint `rol == 'admin'` estricto, el `search_path` impide
  cruzar de colegio, dentro de un colegio no hay admins con alcance parcial, y la
  anulación queda auditada con motivo, fecha y responsable. No lo vuelvas a
  levantar.
- ~~Siete funciones de `tipos_pagos_controller` capturan `Exception` a secas y
  devuelven `None`/`False`.~~ Cinco acababan en 400 y dos en 404, y esos dos decían
  «no encontrado» cuando la base está caída. El 2026-08-17 se corrigió la mitad:
  ya **registran la excepción con su traceback**, que antes desaparecía sin
  rastro, y una guardia estructural en las pruebas impide que alguien vuelva a
  dejar un `except Exception` mudo. **Corregido localmente el 2026-08-24** tras
  revisar `frontend-react`: los siete caminos propagan un error específico y
  las rutas lo traducen a 500 con detalle fijo; los resultados de dominio
  conservan sus status. El reflog local de `origin/main` registra su push en
  `9a90462`; sigue pendiente staging, despliegue comprobado y evidencia de CI.
- ~~Los dos upsert de tipos de pago abren dos conexiones por petición.~~
  **Corregido el 2026-08-17**: releen con su propio cursor antes de confirmar.
  Eso cerró además una ventana peor que no se había visto: si la relectura
  fallaba tras el `commit`, la ruta respondía 400 sobre una escritura ya
  guardada.
- ~~`POST /asistencia` abre una conexión de pertenencia por estudiante y repite
  N veces el mismo permiso de asignación.~~ **Corregido localmente el
  2026-08-24**: una comprobación de asignación y una consulta batch dejan 2
  conexiones totales como admin y 3 como profesor para lotes de 1, 5 y 30. Los
  seis hallazgos restantes de `07_ASISTENCIA.md` siguen abiertos; esta corrección
  está publicada en `bbf3bfb` según el reflog local de `origin/main`, pero aún no
  tiene staging, despliegue comprobado ni evidencia de CI.
- ~~Auditar `MAX_DB_CONNECTIONS_PER_THREADPOOL_WORKER = 2`.~~ **Revalidado el
  2026-08-24**: el inventario intermodular acotado y las pruebas dirigidas no
  detectaron `H>1`; las conexiones múltiples de auth, dashboard, notas,
  asistencia, planilla y branding son secuenciales. `H=1` queda como hipótesis
  candidata, no como cota operativa demostrada. La constante **permanece en 2**
  y conserva 5 workers para el pool de 10. El modelo formal sigue en `R=0`; si
  el `H` real fuera 1, el factor adicional sería margen implícito. La decisión de
  mantener 2 está completa. Demostrar `H=1` para una futura ampliación no se ha
  iniciado y exige orden propia, instrumentación, reserva formal `R`, confirmar
  workers/réplicas/límite del proveedor y carga en staging.
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

## Autorización de uso inmediato: activar la capa 7 para OTRO dominio

La autorización anterior, la de `dashboard`, **se consumió el 2026-08-17** y
queda retirada, con el mismo criterio aplicado a las capas 3, 4, 5 y 6.

Válida **solo mientras el índice maestro indique que no existe una capa activa**.
Si `dashboard` sigue marcada como activa o con su verificación manual pendiente,
**no la reutilices**: vuelve a determinar el estado desde el índice.

**Antes de pegarla hay que rellenar el nombre del dominio.** La capa 7 es
explícitamente «uno a la vez»: cada dominio necesita su propia bitácora. La
primera vez que se usó, el marcador llegó **sin rellenar** y el asistente se
detuvo a preguntar en vez de deducirlo, que es lo correcto.

Se copia el bloque universal del principio y se añade inmediatamente después:

```text
Autorizo activar la capa 7 para el dominio DOMINIO, y solo ese. El dominio
dashboard ya se migro y su bitacora esta cerrada; este es un dominio nuevo con
su propia bitacora.

Acepto continuar manteniendo pendientes las verificaciones heredadas: el valor
operativo final de DB_STATEMENT_TIMEOUT_MS de la capa 1 y la ausencia de
evidencia de GitHub Actions desde la capa 0. Registralas como pendientes,
conserva su riesgo y no las marques como cumplidas.

Esta autorizacion permite solamente la activacion documental. No autoriza
inspeccionar codigo del dominio, implementar su subcapa 0, tocar la base de
datos, hacer deploy, commit o push. Despues de activar la capa, detente.

En el mismo checkout local:

1. Lee y aplica completamente el protocolo universal anterior.
2. Valida main, git status, el HEAD limpio vigente, origin/main y la continuidad
   desde el commit base registrado en la bitacora de dashboard, comprobando que
   todo commit posterior este explicado.
3. Confirma que la migracion de dashboard esta cerrada y que no existe otra capa
   activa. Si hay divergencia o un commit sin explicar, detente.
4. No uses ningun hash de memoria: comprueba primero el HEAD limpio real.
5. Comprueba el estado real de origin/main e informa lo que encuentres, no lo
   supongas. No presentes GitHub Actions como verificada en ningun caso.
6. Crea docs/modularizacion/07_DOMINIO.md partiendo de
   docs/modularizacion/PLANTILLA_CAPA.md, con un nombre de archivo que no pise
   el de dashboard.
7. Registra el HEAD limpio vigente como commit base, rama main, estado Activa,
   primera subcapa pendiente la 0 y codigo de producto modificado al activar:
   ninguno.
8. Define el objetivo solo desde el indice maestro y limitado a ese dominio.
9. Deja la subcapa 0 como inventario, contratos y caracterizacion. No decidas
   aun el desglose posterior.
10. Marca como NO VERIFICADO todo supuesto heredado sobre ese dominio y
    comprueba cada uno en la subcapa 0. En dashboard, de siete supuestos, uno
    resulto falso.
11. Actualiza docs/modularizacion/README.md para marcar unicamente esa capa como
    Activa, con su dominio, y enlazar su bitacora.
12. Ejecuta git diff --check y verifica que el alcance contenga exclusivamente
    README.md y la bitacora nueva.
13. Informa el commit base, la primera subcapa pendiente, las verificaciones
    heredadas y cualquier evidencia remota disponible. Detente sin inspeccionar
    ni implementar la subcapa 0.

No hagas commit, push, deploy, migraciones reales ni acceso a produccion. Yo
revisare los cambios y controlare su publicacion.
```

### Cómo elegir el siguiente dominio de la capa 7

El índice no fija el orden; dice «priorizar uno a la vez». `dashboard` ya está
hecho. Lo que el programa sabe del resto, sin haberlo inspeccionado:

- **Los más consumidos** son los que dependen de `asignacion_academica`:
  `notas`, `boletin`, `asistencia`, `observaciones`, `planilla` y
  `planeador_anual`. Tocar cualquiera afecta al resto por ese servicio
  compartido.
- **`plan_de_clases` ya tiene repositorio propio** —`plan_de_clases_repository`—,
  así que su migración empieza más cerca del final que las demás. **Pero escribe
  archivos** vía `app/services/storage.py`, así que un rollback de datos no
  deshace un archivo ya escrito y eso cambia cómo hay que documentar el rollback.
- **`venta_controller` es el único con SQL inline sobre `ventas`**, tabla que
  `pagos_repository` ya toca desde su bloque rotulado. Migrarlo daría por fin el
  segundo consumidor real que justificaría un `ventas_repository`, y cerraría una
  decisión que la capa 5 dejó explícitamente abierta.
- **`branding`** también escribe archivos, y **`profesor_controller`** conserva
  una de las dos copias muertas de `obtener_clases_profesor_controller` que el
  usuario decidió no retirar.

Nada de esto es una recomendación cerrada: es lo que hay registrado. La elección
es del usuario.
