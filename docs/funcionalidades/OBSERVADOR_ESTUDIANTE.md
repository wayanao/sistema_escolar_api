# Funcionalidad: Observador del estudiante unificado — Backend

## Control

- Estado: **Fases 1, 2 y 3 terminadas el 2026-09-08.** El backend está
  completo: tabla, índice, leer, crear y editar. **No hay pantalla**, así que la
  bitácora sigue vacía y la pantalla vieja sigue siendo la única que los
  profesores usan. La fase 4 (copiar lo viejo) no ha empezado y sigue sin
  autorizarse.
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
| 11 | La columna `materia` **existe pero no se rellena** | Decidido el 2026-09-08, tras medir que el servidor no puede deducirla. Ver abajo |
| 12 | La pantalla muestra **el nivel del curso**, no la materia | Una vez en el título, en los dos niveles |

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
de edición. **No lo añadas.** Hay una prueba que lo impide
(`test_el_admin_no_puede_editar_la_anotacion_de_un_profesor`).

#### Y el admin tampoco CREA, descubierto al implementar la fase 3

Este documento se contradecía: la tabla de permisos decía que crear era «igual
que leer» —lo que incluye al admin— y la tabla de la API decía «profesor del
alumno». Se resolvió a favor de la segunda, y no por gusto:

**el `id` de un admin sale de la tabla `usuarios`, no de `profesor`.** Usarlo
como autor firmaría la anotación con el profesor que por casualidad tenga ese
mismo número. No es teórico: al comprobarlo, en `tenant_colegio_1` la
administradora **maristella polo** tiene `usuarios.id = 1`, y el profesor 1 es
**SINDY PAOLA VERGARA**. La anotación habría quedado a nombre de Sindy Paola,
sin error y sin aviso.

Una bitácora que atribuye a alguien lo que no escribió no sirve para lo único
que justifica su existencia. Lo impide `_profesor_que_escribe`, con prueba.

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

### La materia, añadida el 2026-09-08

`migrations/20260908_observador_anotaciones_materia.sql` añade:

```sql
ALTER TABLE observador_anotaciones
    ADD COLUMN IF NOT EXISTS materia character varying(100) NOT NULL DEFAULT '';
```

Va en **una migración aparte** porque la primera ya estaba aplicada en
producción, y el runner bloquea un archivo cuyo checksum cambie.

**Por qué existe.** El documento de frontend dibujaba «Prof. Ana · Matemáticas ·
20/mar», pero el diseño original quitó la materia de la tabla: la pantalla no
habría podido escribir esa columna del medio. La contradicción entre los dos
documentos se detectó al empezar la fase 2 y la resolvió el usuario.

> **Y el mismo día el usuario cambió de idea.** La columna se queda **vacía por
> ahora**: no se muestra la materia y no se le pide a nadie. El motivo está en
> «Por qué la columna no se rellena», más abajo. La columna **no es código
> muerto**: se conserva a propósito, lista si algún día se decide usarla.
> Quitarla exigiría otra migración y no gana nada.

**Por qué es texto copiado y no una clave foránea a `materias(id)`:**

- Un vínculo reintroduciría el defecto que esta tabla vino a corregir. Si mañana
  quitan esa materia del horario, la anotación perdería el dato o arrastraría la
  fila. Una etiqueta sobrevive a todo.
- Leer la bitácora no necesita entonces ninguna unión extra. A ~180 ms por ida
  y vuelta contra Neon, lo que se paga es el **número** de consultas.

Que la anotación lleve la materia **no** reabre la decisión 1: el observador
sigue siendo por estudiante. La materia es contexto de quién anotó, no la clave
del registro. `asignacion_id` sigue sin existir.

#### Por qué la columna no se rellena

Decidido el 2026-09-08, **después de medir**. Para etiquetar una anotación con
su materia hay que saber cuál es, y el servidor **no puede deducirla**:

| Materias que da un profesor en un mismo curso | `tenant_2005` | `tenant_colegio_1` |
|---|---|---|
| Una sola (deducible) | 9 casos, **27%** | 1 caso, **25%** |
| Varias (ambiguo) | 24 casos, **73%** | 3 casos, **75%** |

Casos reales: LILIANA da **9** materias en PRIMERO-A; ANGELICA, **5** en
JARDIN-B. No es un caso de borde, es la norma.

Las dos salidas posibles tenían coste:

- **Que la profesora la elija** al guardar: fricción en cada anotación, para un
  dato secundario.
- **Deducirla de la asignación desde la que entra**: sin fricción, pero **ata la
  página a una única puerta de entrada** —dejaría de poder abrirse desde un
  listado de alumnos—.

El usuario eligió **ninguna de las dos, por ahora**. La anotación no lleva
materia, nadie elige nada, y la pantalla muestra el nivel del curso en el
título. Consecuencia asumida: **no queda registrado en qué clase pasó**; el
nombre de la profesora sigue diciendo quién observó.

Por eso el `POST` de la fase 3 **no recibe `asignacion_id` ni `materia`**, y la
columna queda en su valor por defecto, la cadena vacía.

#### La lectura devuelve también el nivel del curso

Añadido el 2026-09-08. La pantalla muestra la materia **según el nivel**:
preescolar la omite y dice el nivel una vez en el título, primaria la lleva en
cápsula, y un curso **sin nivel** se comporta como primaria. El detalle de
presentación vive en el documento de frontend.

**La consulta arranca en `estudiantes`, no en las anotaciones**, y es lo único
que hay que entender de este endpoint:

```sql
FROM estudiantes e
LEFT JOIN cursos c ON c.id = e.curso_id
LEFT JOIN observador_anotaciones a ON a.estudiante_id = e.id
                                  [AND a.periodo = %s]
LEFT JOIN profesor p ON p.id = a.profesor_id
WHERE e.id = %s
```

Tres trampas, las tres reales y las tres con prueba:

1. **Un alumno sin anotaciones.** Arrancando en `observador_anotaciones`
   devolvería cero filas, y con ellas ningún nivel: la pantalla no podría ni
   escribir su título. **Hoy es el caso de todos los alumnos**, porque la
   escritura no existe todavía.
2. **`estudiantes.curso_id` es nulable.** Con una unión interna a `cursos`, un
   alumno sin curso desaparecería de su propia bitácora: sin error y sin aviso,
   la pantalla diría que no existe.
3. **El filtro de periodo va en el `ON`, no en el `WHERE`.** En el `WHERE`
   descartaría también la fila del estudiante cuando ese periodo no tuviera
   anotaciones, y cambiar de periodo dejaría la pantalla sin nivel.

Todo sigue siendo **una sola consulta**: las uniones no cuestan idas y vueltas,
que es lo único que se paga contra Neon.

Se eligió esto en vez de resolver la presentación al guardar, para que cambiar
cómo se ve no exija otra migración.

**Forma de la respuesta.** El `nivel` va **fuera** de las anotaciones, porque es
del alumno y no de cada anotación —y porque tiene que llegar aunque no haya
ninguna—:

```json
{
  "nivel": "primaria",
  "anotaciones": [ { "id": 12, "profesor_id": 7, "profesor": "Ana Gómez", ... } ]
}
```

**Cero filas solo significa que el estudiante no existe**, y entonces la ruta
responde `404`. Un alumno real sin anotaciones devuelve una fila de relleno, con
el nivel y el resto en `NULL`, que la ruta descarta. Esa diferencia es la que
permite distinguir «no existe» de «todavía no tiene nada escrito», que en
pantalla son mensajes distintos.

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
| Crear anotación | Profesor del alumno. **Admin no** | `_profesor_que_escribe` + `require_estudiante_access` |
| Editar anotación | **Solo el autor.** Admin **no** | `profesor_id` en el `WHERE` del `UPDATE`, en la misma sentencia que escribe |
| Borrar | Nadie | No existe el endpoint |

`require_estudiante_access` ya está en `app/core/permissions.py` y hace
exactamente lo que hace falta: comprueba que el profesor tenga una asignación
en el curso del estudiante. Ya la usa `GET /boletin/{estudiante_id}`. **No hay
que inventar un permiso nuevo para leer.**

## Cambios de API

| Método | Ruta | Quién | Nota |
|---|---|---|---|
| `GET` | `/observador/{estudiante_id}` | Profesor del alumno o admin | **Implementado (fase 2).** `{"nivel": ..., "anotaciones": [...]}`. `?periodo=N` opcional, validado entre 1 y 4; **sin él devuelve todas**, que es el caso por defecto. `404` solo si el estudiante no existe |
| `POST` | `/observador` | Profesor del alumno. **Admin no** | **Implementado (fase 3).** Crea una anotación y devuelve `{"id": N}` con `201`. `profesor_id` sale del token, **nunca del cuerpo** |
| `PUT` | `/observador/{anotacion_id}` | Solo el autor | **Implementado (fase 3).** Actualiza texto y `positiva`; fija `editada_en` y `editada_por`. `403` si no es tuya, `404` si no existe. No cambia estudiante ni periodo |

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

**Fase 2 — Lectura — TERMINADA el 2026-09-08**
5. ~~Repositorio y `GET /observador/{estudiante_id}`~~:
   `app/repositories/observador_repository.py` y `app/routes/observador.py`.
   Una sola consulta y **una sola conexión**, con el guard corriendo sobre el
   cursor que ya abrió la ruta. Hay prueba que lo fija por aserción: es el
   motivo de existir de la funcionalidad.
6. ~~Pruebas~~: 14 en `tests/test_observador_lectura.py`, verificadas con
   mutaciones.
7. `require_estudiante_access` acepta ahora `cursor=` opcional, replicando lo
   que la optimización del 2026-09-03 hizo con sus dos hermanos. Sin él conserva
   el comportamiento histórico, así que `app/routes/notas.py` no cambia.
8. La migración de `materia` **debe aplicarse antes de publicar** este código: la
   consulta de lectura la nombra.

**Fase 3 — Escritura — TERMINADA el 2026-09-08**
7. ~~`POST /observador`~~, con `profesor_id` desde el token y normalización de
   texto en `app/core/texto_observador.py`.
8. ~~`PUT /observador/{anotacion_id}`~~ solo para el autor. La autoría va en el
   `WHERE` del `UPDATE`, así que comprobar y escribir son **la misma
   sentencia**: no hay ventana entre una cosa y otra, y el camino normal cuesta
   una sola consulta. La segunda solo se paga al fallar, para distinguir un 404
   de un 403.
9. ~~Pruebas~~: 29 en `tests/test_observador_escritura.py`, verificadas con
   mutaciones.
10. Probado de extremo a extremo contra la base real, dentro de una transacción
    deshecha al final: crear, leer de vuelta, editar y los cuatro permisos. Ver
    `docs/CAMBIOS_BACKEND.md`.

**Fase 4 — Copia de lo viejo — LISTA, pendiente de ejecutar**
10. ~~Script de copia~~: `scripts/copiar_observaciones_al_observador.py`, con
    `--dry-run`. Autorizada por el usuario el 2026-09-08.

    Ensayado contra la base real con rollback: **las 68 se copian enteras**, 63
    en `tenant_2005` y 5 en `tenant_colegio_1`, **ninguna descartada**. Al
    repetir la copia inserta 0. Todas recuperan profesor y materia; 7 profesores
    distintos en `tenant_2005`.

    Requiere antes `migrations/20260908_observador_anotaciones_historicas.sql`.

El frontend no debe depender de nada de esto hasta que la fase 2 esté cerrada.

## Preguntas abiertas

1. ~~**¿Se copian las anotaciones actuales?**~~ **Sí, autorizado el
   2026-09-08.** La materia **sí** se recupera, por la asignación de la fila
   vieja, aunque la pantalla no la muestre: es dato real que se perdería si no
   se captura ahora. La **fecha no existe** en el modelo viejo, así que van con
   `creada_en` en `NULL` —«no se sabe»— y la lectura las manda al final con
   `NULLS LAST`. Inventar la fecha de la copia las haría parecer escritas hoy.
2. ~~**¿Qué `positiva` reciben las copiadas?**~~ **Ninguna, decidido el
   2026-09-08.** Van sin marcar (`NULL`). Solo las anotaciones nuevas la llevan,
   y ahí la sigue exigiendo el esquema de la API.
3. ~~**¿El texto normalizado se guarda ya corregido?**~~ **Resuelta el
   2026-09-08: se guarda corregido.** La profesora ve la corrección al salir del
   campo y puede rehacerla, así que lo que aprueba es lo que queda escrito —y lo
   que se imprime—. Vive en `app/core/texto_observador.py`.
4. ~~**¿De dónde sale la materia al crear una anotación?**~~ **Resuelta el
   2026-09-08: de ningún sitio, por ahora.** No se rellena y no se muestra. Ver
   «Por qué la columna no se rellena».

**No queda ninguna abierta en este repo.** Las del frontend siguen en su
documento.

## Entrega para el siguiente chat

- Última acción terminada: **Fase 4 escrita y ensayada, el 2026-09-08.** El
  backend está completo: tabla, índice, `GET`, `POST`, `PUT` y el script de
  copia. 73 pruebas propias, verificadas con mutaciones, más dos pruebas de
  extremo a extremo contra la base real deshechas con rollback.
- **Pendiente de ejecutar por el usuario:** la migración
  `20260908_observador_anotaciones_historicas.sql` y después
  `scripts/copiar_observaciones_al_observador.py`. Hasta entonces la bitácora
  está vacía. Comprobar con
  `SELECT count(*) FROM <tenant>.observador_anotaciones`.
- **No hay pantalla**, así que los profesores siguen usando la vieja.
- **El fallo original sigue vivo**, y seguirá hasta que exista la pantalla
  nueva: es ella la que convierte doce peticiones en una.
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
- Siguiente acción exacta: que el usuario **autorice la Fase 1 del frontend**
  (la pantalla). El backend ya no bloquea nada. La fase 4 de este repo —copiar
  las anotaciones viejas— sigue **sin autorizar** y depende de las preguntas
  abiertas 1 y 2. Una instrucción genérica como «continúa» no basta.
- Aviso operativo descubierto al aplicar: `apply_migration.py` **se niega** sobre
  el endpoint agrupado de Neon (`-pooler`), que es el que trae `.env`. Hay que
  apuntar `DATABASE_URL` al endpoint directo solo para ese comando. Está en
  `docs/MIGRACIONES.md`, pero se olvida.
- Recordatorio operativo: en este repositorio, `git push origin main`
  **despliega producción automáticamente**. La migración debe aplicarse antes
  de publicar código que dependa de ella.
