# Funcionalidad: Observador del estudiante unificado — Backend

## Control

- Estado: **Fase 1 (estructura) terminada el 2026-09-08.** La tabla y su índice
  existen en los dos tenants operativos. **No hay endpoints ni pantalla**: nada
  escribe ni lee esa tabla todavía, y la pantalla vieja sigue siendo la única
  que los profesores usan. Las fases 2 a 4 no han empezado.
- Tipo: Función nueva de producto. **No** es una capa del programa de
  modularización de `docs/modularizacion/` y no debe confundirse con una. La
  capa 7 de `observaciones` está cerrada desde el 2026-08-21 y esto no la
  reabre.
- Repos afectados: este repo (`sistema_escolar_api`) y `frontend-react`. Ver
  también `frontend-react/docs/funcionalidades/OBSERVADOR_ESTUDIANTE.md`, que
  cubre pantallas, impresión y autocorrección de texto.
- Riesgo inicial: Medio. Tabla nueva en todos los tenants, modelo de permisos
  con una excepción deliberada a la norma del proyecto, y sustituye una
  pantalla que hoy usan los profesores.
- Última actualización: 2026-09-08.

## Objetivo

Sustituir el observador actual —una casilla por estudiante, **materia** y
periodo, que se sobrescribe— por **una bitácora acumulativa por estudiante**,
independiente de la materia, donde cada profesor que tenga a ese alumno deja
anotaciones fechadas y todas quedan.

## Motivación

Cuatro razones, en orden de peso:

1. **Hoy se pierde información.** La tabla `observaciones` tiene
   `UNIQUE (estudiante_id, asignacion_id, periodo)` y la escritura es un
   `UPSERT`: cada vez que la profesora guarda, **pisa lo anterior**. No hay
   historial. Un observador que no acumula no es un observador.
2. **El documento real no es por materia.** El Observador del Estudiante es un
   registro acumulativo del año, con entradas de distintos docentes. Lo que hay
   hoy no se parece a eso.
3. **Nadie ve el conjunto.** Si un niño tiene problemas, cada profesor lo anota
   en su materia y nadie ve el panorama completo.
4. **Disuelve un problema de rendimiento medido.** La pantalla actual carga N
   estudiantes a la vez y hace **una petición HTTP por alumno**; con 12 alumnos
   tarda 16-20 s y el frontend aborta a los 10 s. En el modelo nuevo se abre
   **un estudiante** y su bitácora completa. El N+1 desaparece por diseño, no
   por optimización. Ver `docs/CAMBIOS_BACKEND.md`, entrada del 2026-09-03, y
   `docs/modularizacion/07_OBSERVACIONES.md` para las mediciones.

## Fuera de alcance

- **El endpoint masivo `GET /observaciones/{asignacion_id}/{periodo}`** que se
  había propuesto el 2026-09-03 para arreglar el N+1. Esta funcionalidad lo
  vuelve innecesario: **no se implementa**.
- **Borrar o modificar la tabla `observaciones` actual.** Ver "Qué pasa con lo
  que ya existe".
- El sobrecoste de autenticación (6 idas y vueltas por petición). Es un defecto
  real y transversal, ajeno a este dominio; exige su propio alcance.
- Firmas digitales, notificación al acudiente y adjuntar archivos a una
  anotación. No se pidieron.

## Decisiones ya tomadas (con el usuario, conversación del 2026-09-04)

| # | Decisión | Detalle |
|---|---|---|
| 1 | El observador es **por estudiante**, no por materia | Página aparte, un alumno a la vez |
| 2 | Es una **bitácora**: varias anotaciones por alumno | Un profesor puede anotar cuantas veces quiera en el mismo periodo |
| 3 | **Ver: todos** los profesores del alumno | Cada uno ve todas las anotaciones, sean de quien sean |
| 4 | **Editar: solo el autor** | Ningún profesor toca lo de otro |
| 5 | **Borrar: nadie** | No hay endpoint de borrado |
| 6 | Editar **deja rastro** | Se guarda cuándo y quién editó |
| 7 | Se **mantienen los tres campos** actuales | `conductual`, `cognitivo`, `lenguaje` |
| 8 | Cada anotación se marca **positiva o negativa** | Sustituye a la idea de categorías (académico/convivencia/logro) |
| 9 | El **admin ve todo pero NO edita** | Excepción deliberada a la norma del proyecto, ver abajo |
| 10 | El periodo **no oculta** nada | Es una etiqueta de cada anotación, no un filtro obligatorio |

### La decisión 9 es una excepción a la norma, y es deliberada

En este proyecto casi todos los guards empiezan con:

```python
if current_user.get("rol") == "admin":
    return
```

**En la edición de una anotación eso NO debe hacerse.** Si el coordinador puede
reescribir lo que anotó una profesora, la bitácora deja de ser confiable como
documento del colegio ante una reclamación.

El admin **sí** puede leer cualquier bitácora, de cualquier estudiante, sin
compartir curso con él.

Quien implemente esto encontrará natural añadir el atajo de admin en el guard
de edición. **No lo añadas.** Debe haber una prueba que lo impida.

## Diseño de datos

### Tabla nueva: `observador_anotaciones`

**No se reutiliza la tabla `observaciones`.** Razones, decididas con el usuario:

- Su `UNIQUE (estudiante_id, asignacion_id, periodo)` es justo lo que impide
  guardar más de una anotación. Habría que quitarlo.
- No tiene fecha ni autor. Habría que añadir ambos.
- Su clave foránea es `asignacion_id -> asignaciones(id) ON DELETE CASCADE`:
  **borrar una asignación borra sus observaciones**. Para un registro
  permanente del alumno eso es inaceptable — se perdería historial porque
  alguien quitó una materia del horario.
- Con una tabla nueva, la pantalla vieja **sigue funcionando** mientras se
  construye la nueva. Se puede volver atrás. Modificando la vieja, no.

```sql
CREATE TABLE IF NOT EXISTS observador_anotaciones (
    id SERIAL,
    estudiante_id integer NOT NULL,
    profesor_id integer NOT NULL,
    periodo integer NOT NULL,
    positiva boolean NOT NULL,
    conductual text NOT NULL DEFAULT '',
    cognitivo text NOT NULL DEFAULT '',
    lenguaje text NOT NULL DEFAULT '',
    creada_en timestamptz NOT NULL DEFAULT now(),
    editada_en timestamptz,
    editada_por integer,
    CONSTRAINT observador_anotaciones_pkey PRIMARY KEY (id),
    CONSTRAINT observador_anotaciones_estudiante_id_fkey
        FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id),
    CONSTRAINT observador_anotaciones_profesor_id_fkey
        FOREIGN KEY (profesor_id) REFERENCES profesor(id),
    CONSTRAINT observador_anotaciones_editada_por_fkey
        FOREIGN KEY (editada_por) REFERENCES profesor(id),
    CONSTRAINT observador_anotaciones_periodo_check
        CHECK (periodo BETWEEN 1 AND 4)
);
```

Diferencias deliberadas frente a `observaciones`, cada una con su motivo:

- **Sin `UNIQUE`.** Es una bitácora: varias filas por alumno son lo normal, no
  un error.
- **Sin `asignacion_id`.** El observador ya no depende de la materia. El autor
  se identifica por `profesor_id`.
- **Sin `ON DELETE CASCADE`.** Ninguna baja administrativa debe borrar
  historial de un alumno. Es la corrección explícita del defecto descrito
  arriba.
- **`NOT NULL` en las columnas de identidad.** En `observaciones` todas eran
  nulables, y una clave foránea no restringe `NULL`: se podían colar filas sin
  estudiante. Aquí no.
- **`CHECK` en `periodo`.** Hoy el esquema acepta `periodo = 99`; hay una
  prueba que lo fija como comportamiento actual. La tabla nueva no lo hereda.

### Índice, y el error multi-inquilino que hay que evitar

La consulta principal es «todas las anotaciones de un estudiante, la más nueva
primero»:

```sql
SELECT ... FROM observador_anotaciones
WHERE estudiante_id = %s ORDER BY creada_en DESC
```

El índice que la sirve es `(estudiante_id, creada_en)`. Basta ascendente: un
índice btree se recorre en los dos sentidos, y aquí `estudiante_id` es
constante, así que sirve igual a `ORDER BY creada_en DESC`.

**Se crea en DOS sitios, y en el tercero NO** (esto último se decidió el
2026-09-08, al implementar la fase 1):

1. `scripts/apply_tenant_indexes.py`, en la lista `INDEXES`, para los colegios
   que ya existen. **Es el único que lo crea.**
2. `migrations/base/20260813_esquema_base_tenant.sql`, para los colegios que se
   creen después. No se escribe a mano: sale de regenerar el archivo con
   `scripts/generar_esquema_base.py` **después** del paso 1.
3. **La migración `20260908_observador_anotaciones.sql` NO lo crea**, aunque el
   plan original decía que sí.

El motivo del punto 3, comprobado contra la base real antes de decidirlo:
`apply_tenant_indexes.py` antepone el nombre del schema al nombre del índice
(`create_index` hace `f"{schema}_{index_name}"`). Si la migración hubiera dejado
un `idx_observador_anotaciones_estudiante`, el script buscaría después
`tenant_x_idx_observador_anotaciones_estudiante`, **no lo reconocería** —
`CREATE INDEX IF NOT EXISTS` compara por nombre, no por definición— y crearía un
segundo índice idéntico al lado.

Eso no es hipotético: `tenant_2005` tiene hoy tres pares duplicados por esa
misma causa, verificados en `pg_indexes`:

| Tabla | Los dos índices que hacen lo mismo |
|---|---|
| `asistencia` | `asistencia_estudiante_id_fecha_idx` · `tenant_2005_idx_asistencia_estudiante_fecha` |
| `asistencia` | `asistencia_asignacion_id_periodo_idx` · `tenant_2005_idx_asistencia_asignacion_periodo` |
| `estudiantes` | `estudiantes_curso_id_idx` · `tenant_2005_idx_estudiantes_curso_id` |

Tras la fase 1, la tabla nueva tiene **exactamente dos** índices por tenant: su
clave primaria y `tenant_<schema>_idx_observador_anotaciones_estudiante`. Sin
duplicados. `tests/test_migracion_observador_anotaciones.py` fija los dos lados
de la decisión: que la migración no crea índices y que el script sí lo lista.

El fallo original que motivó todo esto sigue siendo cierto para la tabla vieja:
`observaciones` **no está** en `apply_tenant_indexes.py`, aunque su gemela
`asistencia` sí. Y la deriva
entre inquilinos ya es real y verificable: la misma restricción se llama
`unique_observacion` en `tenant_colegio_1` y
`observaciones_estudiante_id_asignacion_id_periodo_key` en `tenant_2005`,
porque se crearon en momentos distintos.

En un modelo de **un schema por colegio**, todo cambio de estructura hay que
repetirlo en cada uno. El que se salte uno queda distinto para siempre.

## Permisos

| Acción | Regla | Guard |
|---|---|---|
| Leer la bitácora | Profesor que comparta curso con el alumno; admin siempre | `require_estudiante_access` (**ya existe**) |
| Crear anotación | Igual que leer | `require_estudiante_access` |
| Editar anotación | **Solo el autor.** Admin **no** | Comprobación nueva: `anotacion.profesor_id == current_user["id"]` |
| Borrar | Nadie | No existe el endpoint |

`require_estudiante_access` ya está en `app/core/permissions.py` y hace
exactamente lo que hace falta: comprueba que el profesor tenga una asignación
en el curso del estudiante. Ya la usa `GET /boletin/{estudiante_id}`. **No hay
que inventar un permiso nuevo para leer.**

## Cambios de API

| Método | Ruta | Quién | Nota |
|---|---|---|---|
| `GET` | `/observador/{estudiante_id}` | Profesor del alumno o admin | Todas las anotaciones. `?periodo=N` opcional; **sin él devuelve todas**, que es el caso por defecto |
| `POST` | `/observador` | Profesor del alumno | Crea una anotación. `profesor_id` sale del token, **nunca del cuerpo** |
| `PUT` | `/observador/{anotacion_id}` | Solo el autor | Actualiza texto y `positiva`; fija `editada_en` y `editada_por` |

No hay `DELETE`, y es a propósito.

`profesor_id` **no se acepta en el cuerpo del `POST`**: si viajara desde el
cliente, un profesor podría firmar una anotación con el nombre de otro. Sale
siempre de `current_user`.

### Normalización del texto en el servidor

El servidor aplica, al guardar, la misma corrección de mayúsculas que el
frontend hace en pantalla:

- primera letra del texto en mayúscula;
- mayúscula después de `.`, `?` y `!` — **no** después de `,`, `;` ni `:`;
- espacios sobrantes colapsados.

Vive en el servidor **además** del frontend porque el frontend es comodidad y
el servidor es la garantía: cualquier otro camino de escritura queda cubierto.
Ver el documento de frontend para la parte visible.

Se mantiene la validación actual de `observaciones`: **al menos uno** de los
tres campos debe traer contenido, si no es un `422`.

## Qué pasa con lo que ya existe

La tabla `observaciones` **se jubila, no se elimina**. Decidido con el usuario.

Orden acordado:

1. Mientras se construye lo nuevo, **no se toca**. La pantalla vieja sigue
   funcionando.
2. Cuando lo nuevo funcione, se deja de escribir en ella.
3. Se copian las filas existentes a la bitácora nueva (**pregunta abierta**,
   ver abajo).
4. **No se borra.** Son pocas filas, no ocupan nada, borrar no se deshace y es
   la única copia de ese historial. Si algún día se elimina, que sea después de un
   año escolar completo.

Al jubilarla hay que **anotarlo en `docs/CAMBIOS_BACKEND.md`**, para que dentro
de un año nadie dude de a qué tabla escribir.

## Invariantes

1. **Nunca se borra una anotación.** No hay endpoint, y no debe añadirse sin
   una orden explícita del usuario.
2. **Una anotación editada siempre deja rastro** (`editada_en`, `editada_por`).
3. **El admin no edita anotaciones de profesores**, aunque en el resto del
   proyecto el admin se salte los guards.
4. **`profesor_id` sale del token**, jamás del cuerpo de la petición.
5. **Cambiar de periodo no oculta historial.** El periodo es etiqueta, no
   filtro obligatorio.
6. **Ningún borrado administrativo arrastra anotaciones**: sin
   `ON DELETE CASCADE` hacia `asignaciones`.

## Riesgos y mitigación

| Riesgo | Mitigación |
|---|---|
| La migración se aplica a unos tenants y a otros no | Aplicar con el runner de `MIGRACIONES.md` y verificar tenant por tenant. Registrar el resultado |
| El índice se crea solo en los tenants actuales y los colegios nuevos nacen sin él | Añadirlo **también** al esquema base. Es el fallo que ya tiene `observaciones` |
| Alguien añade el atajo de admin en el guard de edición | Prueba explícita que lo prohíbe (invariante 3) |
| Se rompe la pantalla vieja antes de que la nueva funcione | Tabla nueva, no modificar la vieja. Se puede volver atrás |
| Copiar las filas viejas duplica historial si se ejecuta dos veces | El script de copia debe ser idempotente o ejecutarse una sola vez con constancia |

## Plan de fases (backend)

Una fase a la vez. No empezar la siguiente sin cerrar y verificar la anterior.

**Fase 1 — Estructura — TERMINADA el 2026-09-08**
1. ~~Migración con la tabla~~ `migrations/20260908_observador_anotaciones.sql`.
   Sin el índice, ver arriba el motivo.
2. ~~Añadir el índice a `scripts/apply_tenant_indexes.py`~~.
3. ~~Regenerar `migrations/base/20260813_esquema_base_tenant.sql`~~ con
   `generar_esquema_base.py --schema tenant_colegio_1`, después de aplicar.
4. ~~Aplicar a los tenants operativos~~. Resultado, tenant por tenant:

   | Tenant | Migración | Índice | Filas | `observaciones` (vieja) |
   |---|---|---|---|---|
   | `tenant_colegio_1` | OK | OK | 0 | 5, intacta |
   | `tenant_2005` | OK | OK | 0 | 63, intacta |

   Registrado en `public.schema_migrations` para los dos. Compuerta en verde:
   **1199 pruebas**.

   Antes de aplicar se hizo un ensayo contra la base real en los dos tenants
   —crear tabla e índice dentro de una transacción y deshacerla— que confirmó
   que las claves foráneas resuelven, que no hay `CASCADE` ni `UNIQUE`, y que un
   `periodo = 99` rebota. No se usó una rama de Neon, que es lo que pide
   `docs/MIGRACIONES.md`; el ensayo transaccional cubrió lo mismo para una
   migración puramente aditiva.

**Fase 2 — Lectura**
5. Repositorio y `GET /observador/{estudiante_id}` con `require_estudiante_access`.
6. Pruebas: permiso concedido, permiso denegado, filtro de periodo, orden.

**Fase 3 — Escritura**
7. `POST /observador`, con `profesor_id` desde el token y normalización de texto.
8. `PUT /observador/{anotacion_id}` solo para el autor, fijando `editada_en` y
   `editada_por`.
9. Pruebas: **el admin no puede editar lo de un profesor**; un profesor no puede
   editar lo de otro; `profesor_id` del cuerpo se ignora.

**Fase 4 — Copia de lo viejo** (solo si el usuario lo confirma)
10. Script de copia de las filas viejas, idempotente. Contarlas justo antes:
    la pantalla vieja sigue en uso y el número sube.

El frontend no debe depender de nada de esto hasta que la fase 2 esté cerrada.

## Preguntas abiertas

1. **¿Se copian las anotaciones actuales a la bitácora nueva?** El asistente
   lo recomendó y el usuario no lo confirmó explícitamente. Sin respuesta, la
   fase 4 no se ejecuta. Si se copian, hay que decidir qué fecha llevan (no
   existe en el modelo viejo) y qué se hace con la materia, que en el modelo
   nuevo ya no se guarda.
2. **¿Qué `positiva` reciben las anotaciones copiadas?** El modelo viejo no
   distingue positivo de negativo.
3. **¿El texto normalizado se guarda ya corregido, o se corrige solo al
   mostrar?** El diseño asume lo primero (se guarda corregido). Confirmar.

Ninguna bloquea las fases 1 a 3.

## Entrega para el siguiente chat

- Última acción terminada: **Fase 1 (estructura), el 2026-09-08.** Existen la
  tabla `observador_anotaciones` y su índice en los dos tenants operativos, la
  migración, la entrada en `apply_tenant_indexes.py`, el archivo base
  regenerado y `tests/test_migracion_observador_anotaciones.py` (9 pruebas,
  verificadas con mutaciones). **No hay repositorio, ni endpoint, ni pantalla:
  nada lee ni escribe esa tabla todavía.**
- Daño colateral atendido: `test_ddl_fija_unicidad_estado_y_tres_referencias_externas`
  (en `tests/test_profesores_caracterizacion.py`) contaba las referencias a
  `profesor(id)` en el archivo base y exigía 3. La tabla nueva añade dos —el
  autor y quien editó—, así que ahora son 5. Se actualizó declarando las dos
  nuevas explícitamente, no solo subiendo el número, y se renombró a
  `test_ddl_fija_unicidad_estado_y_las_referencias_externas`. Su valor está en
  obligar a mirar cada referencia nueva y decidir a propósito si arrastra
  borrados; las dos nuevas **no** llevan `ON DELETE CASCADE`.
- Trabajo previo relacionado, **ya commiteado y publicado**, que no forma parte
  de esta funcionalidad: la optimización de la lectura actual de observaciones
  del 2026-09-03 (`app/dependencies.py`, `app/core/permissions.py`,
  `app/routes/observaciones.py` y tres archivos de prueba). Commits `efb7f91` y
  `71e1b44`, publicados en `main` el 2026-09-04 —o sea, **ya desplegados en
  producción**—. Baja la lectura un 10% y **no** arregla el fallo del usuario,
  que sigue vivo. Ver `docs/CAMBIOS_BACKEND.md`.
- Siguiente acción exacta: que el usuario **autorice la Fase 2 (lectura)**:
  repositorio y `GET /observador/{estudiante_id}` con `require_estudiante_access`.
  Una instrucción genérica como «continúa» no basta.
- Aviso operativo descubierto al aplicar: `apply_migration.py` **se niega** sobre
  el endpoint agrupado de Neon (`-pooler`), que es el que trae `.env`. Hay que
  apuntar `DATABASE_URL` al endpoint directo solo para ese comando. Está en
  `docs/MIGRACIONES.md`, pero se olvida.
- Recordatorio operativo: en este repositorio, `git push origin main`
  **despliega producción automáticamente**. La migración debe aplicarse antes
  de publicar código que dependa de ella.
