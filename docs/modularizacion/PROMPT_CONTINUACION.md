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

## Autorización de uso inmediato: activar la capa 3

Esta sección es específica para el relevo posterior al cierre y publicación de
la capa 2. Mientras el índice maestro siga indicando que no existe una capa
activa y que la capa 3 está en espera, copia el bloque universal anterior y
agrega inmediatamente después el siguiente bloque. Si el estado documental ya
cambió, no reutilices esta autorización: vuelve a determinar el estado desde el
índice.

```text
Autorizo activar únicamente la capa 3, Migraciones y tenants.

Acepto continuar manteniendo pendiente la calibración operativa de
DB_STATEMENT_TIMEOUT_MS heredada de la capa 1. Regístrala como pendiente,
conserva su riesgo y no la marques como cumplida.

Esta autorización permite solamente la activación documental. No autoriza
inspeccionar código de la capa 3, implementar 3.0, ejecutar migraciones, acceder
a producción, hacer deploy, commit o push. Después de activar la capa, detente.

En el mismo checkout local:

1. Lee y aplica completamente el protocolo universal anterior.
2. Valida `main`, `git status`, el HEAD limpio vigente, `origin/main`, la
   continuidad desde el base de la capa 2
   `b24cb8d3f1a8fa1d48699ed5732d4013ab6fe7f9` y todos los commits posteriores.
3. Confirma que la capa 2 está cerrada, que la capa 3 sigue en espera y que no
   existe otra capa activa. Si hay divergencia o un commit sin explicar,
   detente.
4. El commit de cierre publicado de la capa 2 es
   `8c3939ad5dc872b08e93464145369b3a1eea909e`. Puede existir después un
   commit exclusivamente documental que prepare este relevo; debes verificar
   su alcance y su explicación en `02_CONCURRENCIA.md`. No uses ningún hash como
   base sin comprobar primero el HEAD limpio real.
5. No declares GitHub Actions verificada solo porque `HEAD` coincida con
   `origin/main`; exige evidencia del run asociado.
6. Crea `docs/modularizacion/03_MIGRACIONES_TENANTS.md` partiendo de
   `docs/modularizacion/PLANTILLA_CAPA.md`.
7. Registra el HEAD limpio vigente como commit base, rama `main`, estado
   `Activa`, primera subcapa pendiente `3.0` y código de producto modificado al
   activar: ninguno.
8. Define el objetivo solo desde el índice: tenants versionados, runner
   protegido contra ejecuciones simultáneas, alta reproducible mediante
   migraciones y ensayo posterior no productivo con rollback.
9. Deja 3.0 como inventario, contratos y caracterización. No inventes detalles
   de implementación sin inspeccionarlos en un turno posterior.
10. Actualiza `docs/modularizacion/README.md` para marcar únicamente la capa 3
    como Activa, enlazar su bitácora y dejar 3.0 pendiente.
11. Ejecuta `git diff --check`, comprueba también el whitespace del archivo
    nuevo y verifica que el alcance contenga exclusivamente `README.md` y
    `03_MIGRACIONES_TENANTS.md`.
12. Informa el commit base, la primera subcapa pendiente, la verificación
    operativa heredada y cualquier evidencia remota disponible. Detente sin
    inspeccionar ni implementar 3.0.

No hagas commit, push, deploy, migraciones reales ni acceso a producción. Yo
revisaré los cambios y controlaré su publicación.
```
