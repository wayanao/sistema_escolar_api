# Funcionalidad: SISBÉN y lugar de residencia — Backend

## Control

- Estado: **Backend completo y en producción el 2026-10-20.** S0 (diseño) en
  `2d01025`, S1 (backend) en `9a18945` y S2 (rama de Neon y esquema base) en
  `d256a93`, los tres en GitHub; migración aplicada en producción por el
  usuario. Siguiente: S3 (frontend), con su autorización.
- Tipo: Función nueva de producto. No es una capa del programa de
  modularización de `docs/modularizacion/` y no debe confundirse con una.
- Repos afectados: este repo (`sistema_escolar_api`) y `frontend-react`. Ver
  también `frontend-react/docs/funcionalidades/SISBEN_RESIDENCIA.md`, que
  cubre la pantalla.
- Riesgo: **Medio.** Hay migración en la tabla `estudiantes` de todos los
  tenants, pero son columnas nuevas, vacías y opcionales: no cambia ningún
  cobro, permiso ni dato existente.
- Fecha deseada: **antes de las matrículas de noviembre de 2026**, para no
  volver a pedirle estos datos a cada familia después.
- Última actualización: 2026-10-19.

## Objetivo

Que la ficha del estudiante (la que se llena al crear, al editar y al
matricular desde una admisión) guarde:

1. Si la familia tiene SISBÉN y su clasificación.
2. El lugar donde vive el estudiante, por partes, en vez de una sola caja de
   "Dirección".

## Diagnóstico (verificado en el código el 2026-10-19)

- `estudiantes` no tiene nada de SISBÉN. `grep -ri sisben` en los dos repos
  no encuentra nada.
- La dirección es una sola columna libre: `estudiantes.direccion`,
  `varchar(255)`.
- Todo el router `app/routes/estudiantes.py` exige admin
  (`get_current_active_admin`): el profesor no ve estos datos.
- `GET /estudiantes/{id}` lee con `SELECT *` (`estudiantes_repository.
  obtener_estudiante`) y nombra las columnas con `cursor.description`: las
  columnas nuevas salen solas en la respuesta, sin tocar esa ruta.
- `POST` y `PUT /estudiantes` usan `EstudianteCreate` y escriben **34 valores
  por posición** (`insertar_estudiante`, `actualizar_estudiante`). La misma
  tupla la arman `estudiante_controller.py` (crear y editar) y
  `anios_lectivos_controller._valores_globales_estudiante` (matricular desde
  una admisión, nuevo o exalumno). Un desplazamiento en esa tupla guardaría un
  dato en la columna de otro sin ningún error.
- `PUT /estudiantes/{id}` reemplaza la ficha entera: lo que no llega queda
  vacío. El frontend, al editar, devuelve todo lo que leyó del `GET`
  (`normalizarEstudianteParaEdicion`), pero una pestaña abierta antes del
  cambio, o el formulario viejo al matricular a un exalumno, no traería los
  campos nuevos.

## Decisiones ya tomadas (con el usuario, 2026-10-19)

1. **SISBÉN con grupo, subgrupo y nivel** (el usuario eligió "los dos"):
   - ¿Tiene SISBÉN?: sin dato, sí o no.
   - Grupo del SISBÉN IV: A, B, C o D.
   - Subgrupo del SISBÉN IV, según el grupo: A1 a A5, B1 a B7, C1 a C18,
     D1 a D21.
   - Nivel del SISBÉN III (el anterior), para quien solo tenga ese
     certificado: 1, 2 o 3 (confirmado por el usuario el 2026-10-19).
2. **Lugar de residencia en campos separados**: dirección (calle o carrera y
   número), barrio o vereda, municipio, zona (urbana o rural) y punto de
   referencia. **Sin departamento** (confirmado por el usuario el
   2026-10-19).
3. **Lo que ya está escrito en `direccion` no se toca.** No se parte
   automáticamente en barrio y municipio: cada quien lo escribió a su manera.
4. **Una pestaña vieja no borra los datos nuevos** (propuesta aceptada con la
   del diseño): si en el cuerpo no llega **ninguno** de los ocho campos
   nuevos, se quedan como estaban. Si llega alguno, se reemplazan los ocho
   (lo que falte queda vacío), para que el SISBÉN nunca quede a medias. Es la
   misma idea que protege `cuestionario` en las admisiones.

## Diseño de datos

Migración nueva `migrations/<fecha>_estudiantes_sisben_residencia.sql`, solo
`ADD COLUMN IF NOT EXISTS` y `CHECK`, todo opcional (`NULL` = sin dato):

| Columna | Tipo | Regla |
|---|---|---|
| `sisben` | `boolean` | `NULL` sin dato, `TRUE` sí, `FALSE` no |
| `sisben_grupo` | `varchar(1)` | `A`, `B`, `C` o `D` |
| `sisben_subgrupo` | `varchar(3)` | empieza por la letra del grupo |
| `sisben_nivel` | `smallint` | 1, 2 o 3 |
| `barrio` | `varchar(150)` | texto libre |
| `municipio` | `varchar(100)` | texto libre |
| `zona_residencia` | `varchar(10)` | `urbana` o `rural` |
| `punto_referencia` | `varchar(255)` | texto libre |

Reglas en la base (`CHECK`), como defensa por si algo salta la API:

- valores permitidos de grupo, nivel y zona;
- el subgrupo exige grupo y empieza por su letra;
- sin SISBÉN (`sisben` distinto de `TRUE`) no hay grupo, subgrupo ni nivel.

El rango exacto de cada subgrupo (A1 a A5, etc.) lo valida la API, con
mensaje en español; en la base basta el formato.

`direccion` no cambia: sigue siendo la calle o carrera y el número.

## Contrato de la API

- `EstudianteCreate` suma los ocho campos opcionales. Un `model_validator`
  aplica las reglas de arriba y el rango del subgrupo, con mensajes claros
  (por ejemplo, "El subgrupo B9 no existe: el grupo B va de B1 a B7").
- `POST /estudiantes`: si llegan, se guardan; si no, quedan vacíos.
- `PUT /estudiantes/{id}`: decisión 4 (ninguno llega → se quedan como
  estaban; alguno llega → se reemplazan los ocho).
- `POST /admisiones/{id}/matricular`: igual que el `PUT` para el exalumno que
  vuelve, e igual que el `POST` para el aspirante nuevo.
- `GET /estudiantes/{id}`: trae las columnas nuevas sin cambios de código
  (`SELECT *`). Respuesta solo con claves de más: no rompe a nadie.

**Cómo se escribe sin tocar la tupla de 34.** Las dos sentencias de hoy
(`insertar_estudiante` y `actualizar_estudiante`) quedan letra por letra. Se
agrega una sola función de repositorio, `guardar_sisben_y_residencia`, que
hace un `UPDATE` de las ocho columnas, y se llama en la misma transacción
**solo si llegó alguno de los ocho campos** (`model_fields_set`). Se usa en
los cuatro caminos que escriben la ficha: crear, editar, aspirante nuevo y
exalumno que vuelve. Motivos:

- no se arriesga el orden de la tupla, que es el punto más frágil;
- mientras el frontend viejo siga publicado, nadie manda los campos nuevos y
  ninguna petición toca las columnas nuevas. Eso permite subir el backend
  **antes** de aplicar la migración en producción sin que nada falle (ver
  "Orden de publicación").

## Plan por pasos (cada uno con autorización explícita)

- **S0 — Diseño** (este documento). Sin código.
- **S1 — Backend.** Pruebas primero (deben fallar), después la migración, el
  esquema, el validador, `guardar_sisben_y_residencia` y las cuatro llamadas.
  Documentar en `docs/API_ENDPOINTS.md`, `docs/BASE_DATOS.md` y
  `docs/CAMBIOS_BACKEND.md`. `tests/test_esquema_base.py` fallará a propósito
  hasta el S2: es la compuerta que exige aplicar y regenerar.
- **S2 — Base de datos (lo hace el usuario).** Probar la migración en una
  rama de Neon (`PENDIENTE` → `OK` → `OMITIDA`), regenerar el esquema base
  desde esa rama, commit de migración, esquema base y código juntos. Después,
  ver "Orden de publicación".
- **S3 — Frontend.** Los campos en el formulario del estudiante. Detalle en el
  documento del frontend.

## Orden de publicación

1. Push del backend (S1 + S2) y esperar a que Render quede **Live**.
2. Aplicar la migración en `tenant_colegio_1` y `tenant_2005` con
   `apply_migration.py` y el `DATABASE_URL` directo.
3. Push del frontend (S3).

Por qué el push va antes de aplicar (igual que el paso E1 de la entrevista de
admisión): un colegio nuevo nace del esquema base y copia el historial de
migraciones de la plantilla. Y por qué no se rompe nada en el rato entre 1 y
2: con el frontend viejo, ninguna petición manda los campos nuevos (ver
"Contrato de la API").

## Avance del paso S1 (backend), 2026-10-19

Autorizado por el usuario el 2026-10-19, después de responder las dos
preguntas abiertas. Al empezar, los dos repos estaban en `main`, limpios
(`ahead 1` con el S0). Se leyó completa `docs/MIGRACIONES.md`.

**Pruebas primero.** Se escribieron antes del código y fallaron todas (58
fallos y 10 errores; las 26 que pasaron eran las de Admisiones que ya
existían):

- `tests/test_migracion_estudiantes_sisben_residencia.py` (19): el texto del
  SQL. Las ocho columnas con su tipo, sin `NOT NULL` ni `DEFAULT`; las cinco
  reglas, cada una solo si falta; solo toca `estudiantes`; no menciona
  `direccion`; reejecutable; no cambia datos.
- `tests/test_estudiantes_sisben_residencia.py` (46): lo que acepta y rechaza
  la ficha (subgrupos en el borde, como A5, C18 y D21, y fuera de él, como A6,
  B9, A0 y A01; subgrupo sin grupo o de otro grupo; clasificación sin SISBÉN;
  nivel 0 y 4; zona; largo de los textos), el `UPDATE` del repositorio y el
  controlador al crear y editar (con los ocho, sin ninguno, con uno solo, con
  todos en `null` y con un estudiante que no existe).
- `tests/test_admisiones_matricular.py` (+3): aspirante nuevo y exalumno que
  vuelve guardan los ocho en la misma transacción, y el formulario de antes no
  borra los del exalumno.
- Después del código se agregaron 3 más en el segundo archivo que pasan por
  la ruta HTTP real (`PUT /estudiantes/55`, con el controlador doblado): un
  cuerpo viejo no trae ninguno de los ocho, el nuevo los trae todos, y un
  subgrupo equivocado responde `422` con el motivo. No fallaron antes, porque
  confirman cómo se comporta FastAPI y no código nuevo.

**Código:**

- `migrations/20261019_estudiantes_sisben_residencia.sql`: las ocho columnas
  y las cinco reglas de "Diseño de datos".
- `app/schemas/estudiante.py`: los ocho campos en `EstudianteCreate` (grupo y
  zona como lista cerrada, nivel de 1 a 3, largos de cada texto) y el
  validador `revisar_sisben`, con mensajes en español.
- `app/repositories/estudiantes_repository.py`:
  `COLUMNAS_SISBEN_Y_RESIDENCIA` y `guardar_sisben_y_residencia`.
- `app/controllers/estudiante_controller.py`:
  `guardar_sisben_y_residencia_si_llegaron`, llamado al crear y al editar (solo
  si el estudiante existe), antes de guardar el curso vigente.
- `app/controllers/anios_lectivos_controller.py`: la misma llamada al
  matricular a un aspirante nuevo y a un exalumno que vuelve. `model_copy`
  (que pone el estado `activo`) conserva qué campos llegaron: se comprobó.
- La tupla de 34 valores no cambió: las pruebas que la fijan
  (`test_estudiantes_controlador.py`) siguen pasando sin tocarlas.

**Verificación**, con una `DATABASE_URL` ficticia y el `venv` del proyecto:
`scripts/verify.py` → **2603 pasan y 1 falla, la esperada**:
`test_esquema_base.py` avisa que el esquema base no incorpora
`20261019_estudiantes_sisben_residencia.sql`. Se apaga en el S2. Ruff y `pip
check` limpios; `git diff --check` limpio. Documentado en
`docs/API_ENDPOINTS.md`, `docs/BASE_DATOS.md`, `docs/CAMBIOS_BACKEND.md` y
`docs/MIGRACIONES.md`. No se accedió a Neon ni a producción.

## Paso S2: lista de comprobación en una rama de Neon

La hace el usuario; el asistente no se conecta a Neon.

1. En console.neon.tech → Branches → **Create branch** desde `production`,
   con los datos actuales. Nombre sugerido: `prueba-sisben`.
2. En la rama nueva → **Connect**: copiar la cadena de conexión **directa**
   (con "Connection pooling" apagado; el host no debe tener `-pooler`). No
   pegarla en el chat.
3. En una terminal de PowerShell, en la carpeta del backend. La variable
   solo vive en esa ventana y gana sobre el `.env`:

   ```powershell
   $env:DATABASE_URL = "<cadena directa de la rama>"
   ([uri]$env:DATABASE_URL).Host
   .\venv\Scripts\python.exe apply_migration.py migrations/20261019_estudiantes_sisben_residencia.sql --dry-run
   .\venv\Scripts\python.exe apply_migration.py migrations/20261019_estudiantes_sisben_residencia.sql
   .\venv\Scripts\python.exe apply_migration.py migrations/20261019_estudiantes_sisben_residencia.sql --dry-run
   ```

   El host que se imprime debe ser el de la rama, **no**
   `ep-late-smoke-aip41j6x` (producción). Esperado: `PENDIENTE` → `OK` →
   `OMITIDA (ya aplicada)` en `tenant_colegio_1` y `tenant_2005`.
4. En la misma terminal, regenerar el esquema base desde la rama:

   ```powershell
   .\venv\Scripts\python.exe scripts\generar_esquema_base.py --schema tenant_colegio_1
   ```

   Esperado en el diff: la migración en la cabecera, las ocho columnas de
   `estudiantes` y sus cinco reglas, y nada más. Después, cerrar esa terminal.
5. En el SQL Editor de Neon, **con la rama de prueba elegida**, pegar todo
   esto junto y correrlo una vez. Prueba 11 cambios sobre un estudiante de
   `tenant_colegio_1`; cada uno se deshace al instante, así que no queda nada
   guardado. La columna `bien` debe salir `true` en las 11 filas:

   ```sql
   SET search_path TO tenant_colegio_1, public;

   CREATE TEMP TABLE prueba_sisben (orden INT, caso TEXT, debe TEXT, obtuvo TEXT);

   DO $$
   DECLARE
       estudiante INTEGER := (SELECT MIN(id) FROM estudiantes);
       fila RECORD;
   BEGIN
       FOR fila IN
           SELECT * FROM (VALUES
               (1, 'Ficha completa', 'aceptar',
                $q$UPDATE estudiantes SET sisben = TRUE, sisben_grupo = 'B', sisben_subgrupo = 'B4',
                   sisben_nivel = 2, barrio = 'El Carmen', municipio = 'Galapa',
                   zona_residencia = 'urbana', punto_referencia = 'Frente a la tienda' WHERE id = {est}$q$),
               (2, 'No tiene SISBÉN', 'aceptar',
                $q$UPDATE estudiantes SET sisben = FALSE WHERE id = {est}$q$),
               (3, 'Grupo inventado', 'chk_estudiantes_sisben_grupo',
                $q$UPDATE estudiantes SET sisben = TRUE, sisben_grupo = 'E' WHERE id = {est}$q$),
               (4, 'Subgrupo sin grupo', 'chk_estudiantes_sisben_subgrupo',
                $q$UPDATE estudiantes SET sisben = TRUE, sisben_subgrupo = 'B4' WHERE id = {est}$q$),
               (5, 'Subgrupo de otro grupo', 'chk_estudiantes_sisben_subgrupo',
                $q$UPDATE estudiantes SET sisben = TRUE, sisben_grupo = 'A', sisben_subgrupo = 'B2' WHERE id = {est}$q$),
               (6, 'Subgrupo mal escrito', 'chk_estudiantes_sisben_subgrupo',
                $q$UPDATE estudiantes SET sisben = TRUE, sisben_grupo = 'A', sisben_subgrupo = 'A0' WHERE id = {est}$q$),
               (7, 'Nivel 4', 'chk_estudiantes_sisben_nivel',
                $q$UPDATE estudiantes SET sisben = TRUE, sisben_nivel = 4 WHERE id = {est}$q$),
               (8, 'Grupo sin SISBÉN', 'chk_estudiantes_sisben_clasificacion',
                $q$UPDATE estudiantes SET sisben = FALSE, sisben_grupo = 'A' WHERE id = {est}$q$),
               (9, 'Nivel sin dato de SISBÉN', 'chk_estudiantes_sisben_clasificacion',
                $q$UPDATE estudiantes SET sisben = NULL, sisben_nivel = 1 WHERE id = {est}$q$),
               (10, 'Zona inventada', 'chk_estudiantes_zona_residencia',
                $q$UPDATE estudiantes SET zona_residencia = 'centro' WHERE id = {est}$q$),
               (11, 'Barrio demasiado largo', 'character varying(150)',
                $q$UPDATE estudiantes SET barrio = repeat('x', 151) WHERE id = {est}$q$)
           ) AS c (orden, caso, debe, sentencia)
           ORDER BY orden
       LOOP
           IF estudiante IS NULL THEN
               INSERT INTO prueba_sisben
               VALUES (fila.orden, fila.caso, fila.debe, 'no se pudo probar: el colegio no tiene estudiantes');
               CONTINUE;
           END IF;
           BEGIN
               EXECUTE replace(fila.sentencia, '{est}', estudiante::text);
               RAISE EXCEPTION 'aceptada';
           EXCEPTION
               WHEN raise_exception THEN
                   INSERT INTO prueba_sisben VALUES (fila.orden, fila.caso, fila.debe, 'aceptada');
               WHEN OTHERS THEN
                   INSERT INTO prueba_sisben VALUES (fila.orden, fila.caso, fila.debe, SQLERRM);
           END;
       END LOOP;
   END
   $$;

   SELECT orden, caso, debe, obtuvo,
          CASE WHEN debe = 'aceptar' THEN obtuvo = 'aceptada'
               ELSE position(debe IN obtuvo) > 0 END AS bien
   FROM prueba_sisben
   ORDER BY orden;
   ```

   Cómo funciona: cada cambio corre en un bloque que, si la base lo acepta,
   se deshace a propósito con `RAISE EXCEPTION 'aceptada'`; si la base lo
   rechaza, también se deshace. Solo queda el resultado en una tabla temporal,
   que desaparece al cerrar la sesión.
6. En el mismo SQL Editor, comprobar que nadie quedó con datos nuevos (debe
   dar 0 en los dos colegios):

   ```sql
   SELECT 'tenant_colegio_1' AS colegio, count(*) AS con_datos_nuevos
   FROM tenant_colegio_1.estudiantes
   WHERE sisben IS NOT NULL OR sisben_grupo IS NOT NULL OR sisben_subgrupo IS NOT NULL
      OR sisben_nivel IS NOT NULL OR barrio IS NOT NULL OR municipio IS NOT NULL
      OR zona_residencia IS NOT NULL OR punto_referencia IS NOT NULL
   UNION ALL
   SELECT 'tenant_2005', count(*)
   FROM tenant_2005.estudiantes
   WHERE sisben IS NOT NULL OR sisben_grupo IS NOT NULL OR sisben_subgrupo IS NOT NULL
      OR sisben_nivel IS NOT NULL OR barrio IS NOT NULL OR municipio IS NOT NULL
      OR zona_residencia IS NOT NULL OR punto_referencia IS NOT NULL;
   ```

7. Contarle al asistente lo que salió en los puntos 3 a 6, sin cadenas de
   conexión. Con eso se cierra el S2 en el documento, `test_esquema_base.py`
   vuelve a pasar y el usuario hace un solo commit con migración, esquema base,
   código y pruebas. Después se puede borrar la rama.

Después del S2, el orden de "Orden de publicación": push del backend y
Render **Live**, aplicar en producción (los mismos tres comandos del punto 3,
con el `DATABASE_URL` **directo de producción** en esa terminal) y, al final,
el frontend (S3).

## Avance del paso S2, 2026-10-20

Lo hizo el usuario; el asistente no se conectó a Neon ni a producción.

- El S1 quedó en el commit `9a18945` (sin el esquema base, que todavía no se
  había regenerado; no se ha subido).
- Puntos 1 a 3: el usuario creó la rama, simuló, aplicó y volvió a simular:
  la última simulación sale `OMITIDA` (informado por el usuario, sin pegar
  la salida).
- Punto 4: esquema base regenerado desde `tenant_colegio_1` en la rama: **36
  tablas, 1 función y 1 disparador** (las mismas de antes). El diff, revisado
  por el asistente, trae solo la fecha y la migración 45 en la cabecera, las
  ocho columnas de `estudiantes` y sus cinco reglas, como las escribió
  PostgreSQL.
- Con el esquema base regenerado, `scripts/verify.py` → **2604 pasan, 0
  fallan**; Ruff y `pip check` limpios; `git diff --check` limpio. La falla
  esperada de `test_esquema_base.py` se apagó.
- Punto 5: la consulta del SQL Editor, en la rama y en `tenant_colegio_1`,
  dio **`bien = true` en los 11 casos** (salida pegada por el usuario). Se
  aceptaron la ficha completa y "no tiene SISBÉN"; cada regla rechazó su caso
  con su propio nombre (`chk_estudiantes_sisben_grupo`, `_subgrupo` en sus
  tres casos, `_nivel`, `_clasificacion` en sus dos casos y
  `chk_estudiantes_zona_residencia`), y el barrio de 151 letras dio "value
  too long for type character varying(150)".
- Punto 6: el conteo de estudiantes con algún dato nuevo dio **0 en
  `tenant_colegio_1` y 0 en `tenant_2005`** (salida pegada por el usuario):
  la prueba no dejó nada guardado y ningún estudiante cambió.
- **Con esto, el S2 queda completo** en la rama. Ya se puede borrar la rama
  `prueba-sisben`.
- El esquema base y este registro quedaron en el commit `d256a93`. El
  usuario subió los dos commits juntos (`origin/main` en `d256a93`, visto con
  `git fetch`).
- **Migración aplicada en producción el 2026-10-20** por el usuario
  (informado por él, sin pegar la salida del runner). Que Render haya quedado
  **Live** antes no se ve desde el repo.
- Después de aplicarla, el `DATABASE_URL` del `.env` quedó en el endpoint
  directo de producción (sin `-pooler`; comprobado leyendo solo el servidor).
  Se le pidió al usuario devolverlo al `-pooler`.

## Fuera de alcance

- Departamento de residencia (decidido el 2026-10-19: solo el municipio).
- Mostrar SISBÉN o barrio en impresos: factura, certificados, boletín. La
  factura sigue mostrando solo `direccion`.
- Filtros, reportes o conteos por SISBÉN o por zona.
- Pedir estos datos en el registro del aspirante (Admisiones): se llenan en
  el formulario de matricular, que es la misma ficha.
- Borrar o partir `direccion`.

## Preguntas abiertas

- ~~Antes del S1: ¿qué valores tiene el "nivel"?~~ **Respondida el
  2026-10-19: 1, 2 o 3.**
- ~~Antes del S1: ¿se pide también el departamento?~~ **Respondida el
  2026-10-19: no, solo el municipio.**

## Entrega para el siguiente chat

- Hecho: S0, S1 y S2 (commits `2d01025`, `9a18945` y `d256a93`, en GitHub)
  y la migración en producción el 2026-10-20. **El backend de esta
  funcionalidad está completo.** Ver "Avance del paso S2".
- Pendiente del usuario: devolver el `DATABASE_URL` del `.env` al endpoint
  `-pooler` y borrar la rama `prueba-sisben` en Neon, si no se borró.
- Siguiente acción exacta: el **S3 (frontend)**, con autorización explícita.
  Se puede probar en local porque la migración ya está en producción (el
  backend local escribe en la base real): con el Colegio Demo, nunca con
  estudiantes de `tenant_2005`.
- El S3 se puede escribir antes de terminar el S2, pero no probar en local
  con la pantalla: el backend local escribe en la base real (`production`) y
  allí todavía no existen las columnas.
- Prompt para retomar: `docs/funcionalidades/PROMPT_CONTINUACION_SISBEN_RESIDENCIA.md`.
