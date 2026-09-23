# Funcionalidad: Listas de Seguimiento por Curso — Backend

## Control

- Estado: **Backend completo (2026-09-22)** y frontend también. Migración
  aplicada a los dos tenants operativos, esquema base regenerado, los cuatro
  endpoints en pie con 96 pruebas propias más un ensayo del SQL contra
  PostgreSQL real, y la pantalla probada a mano en el navegador. Ver
  `frontend-react/docs/funcionalidades/LISTAS_SEGUIMIENTO.md`.
- **Hay una ampliación en diseño, sin código todavía:** crear una columna en
  todos los cursos de una vez. Ver la sección "Ampliación" más abajo. No
  toca las tablas ni lo ya construido.
- Tipo: Función nueva de producto. No es una capa del programa de
  modularización de `docs/modularizacion/` y no debe confundirse con una.
- Repos afectados: este repo (`sistema_escolar_api`) y `frontend-react`. Ver
  también `frontend-react/docs/funcionalidades/LISTAS_SEGUIMIENTO.md`, que
  cubre la parte de pantallas.
- Riesgo inicial: Bajo. Tablas enteramente nuevas — a diferencia de
  `NIVEL_ACADEMICO.md`/`DIRECTOR_GRUPO.md`, que agregan una columna a
  `cursos` (una tabla que ya leen y escriben endpoints existentes), acá nada
  del código actual toca las tablas nuevas. Si se publicara antes de aplicar
  la migración, solo fallarían los endpoints nuevos de este router
  (`relation does not exist`), no el resto del sistema. Aun así, el orden de
  despliegue de abajo aplica igual.
- Última actualización: 2026-09-22.

## Objetivo

Que el administrador pueda, por curso, definir columnas con el nombre que
quiera (ej. "Asistió a la cumbre", "Compró el libro") y marcar cada alumno
con un check + una nota corta opcional por columna. No es notas ni
asistencia: es un registro libre para cualquier seguimiento administrativo
que no encaje en lo que ya existe.

## Motivación

El usuario pidió una vista tipo hoja de cálculo por curso (a partir de una
planilla de sueldos como referencia visual), configurable por él mismo, para
llevar registros que hoy no tienen dónde vivir. Se investigó primero si el
dato ya existía en otra forma:

- `notas_detalle` (planilla del profesor) tiene columnas de nombre libre,
  pero atadas a `asignacion_id` (materia+profesor+horario), no a curso
  directo, y una columna solo existe una vez que ya tiene al menos una fila
  — no sirve para "definir la columna primero, marcar después".
- `asistencia` es una fila por alumno por fecha, sin entidad de columna
  propia — la "columna" es una fecha, no un nombre libre elegido por el
  admin.
- `tipos_de_pagos` / `tipos_pagos_estudiantes` es el precedente más parecido
  (nombre definido por el admin + valor por alumno, con upsert), pero está
  pensado para plata: usa baja lógica (`activo`) para preservar historial
  financiero y una tabla puente a cursos que acá no hace falta (ver
  "Decisiones ya tomadas").
- No existe ningún mecanismo genérico de "campo personalizado" en todo el
  backend — se revisó a fondo: la única columna JSON de todo el esquema es
  `institucion_branding.configuracion_extra`, un blob de configuración por
  colegio, no una mecánica fila por fila reutilizable.

## Fuera de alcance

- Notas, boletines, asistencia, pagos: sin cambios en esta propuesta.
- Reutilizar una columna entre varios cursos: decisión explícita del
  usuario, cada curso tiene su propia lista independiente (ver "Decisiones
  ya tomadas"). **Matizado el 2026-09-22**, sin cambiar el modelo: se
  añadirá una forma de crear la misma columna en todos los cursos de golpe,
  pero como **copias independientes**, no como una columna compartida. Ver
  "Ampliación". Una columna sigue perteneciendo a un solo curso.
- Un corte por período o año lectivo: no existe esa dimensión en este
  diseño; una columna vive mientras exista el curso, hasta que el admin la
  borre a mano.
- Reordenar columnas a mano (drag and drop): no se pidió; se listan en el
  orden en que se crean.

## Decisiones ya tomadas (con el usuario, en la conversación de origen)

- Columnas **independientes por curso**, sin compartir ni reutilizar entre
  cursos — no hace falta una tabla puente como `tipos_pagos_cursos`. **Sigue
  siendo cierto después de la ampliación del 2026-09-22**: crear "en todos
  los cursos" crea N filas independientes, una por curso, no una fila
  compartida. El modelo de datos no cambia.
- Cada celda guarda **`marcado` (booleano) + `nota` (texto corto,
  opcional)**, no solo un check.
- Nombre visible para el admin: **"Listas de Seguimiento"** — a propósito
  distinto de "Planilla" (que en este sistema significa notas del profesor)
  y de `VistaPlanillaObservador` (que es otra cosa: un buscador de alumnos
  del observador, no una grilla).
- Borrado de columna es **definitivo** (no baja lógica): no hay historial
  financiero que proteger acá, a diferencia de tipos de pago.
- Guardado de marcas **en lote**, con un botón "Guardar cambios" y
  confirmación previa — no una petición por click ni por tecla. Detalle de
  UX en el documento del frontend.

## Diseño de datos

### Tabla `listas_seguimiento_columnas`

```sql
CREATE TABLE IF NOT EXISTS listas_seguimiento_columnas (
    id SERIAL PRIMARY KEY,
    curso_id INTEGER NOT NULL REFERENCES cursos(id) ON DELETE CASCADE,
    nombre VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Nombre único por curso, ignorando mayúsculas/espacios — mismo patrón que
-- idx_cursos_nombre_jornada_unico en 20260623_admin_unicos_academicos.sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_listas_seguimiento_columnas_nombre_unico
ON listas_seguimiento_columnas (
    curso_id,
    (UPPER(REGEXP_REPLACE(TRIM(nombre), '[[:space:]]+', ' ', 'g')))
);
CREATE INDEX IF NOT EXISTS idx_listas_seguimiento_columnas_curso
    ON listas_seguimiento_columnas(curso_id);
```

### Tabla `listas_seguimiento_marcas`

```sql
CREATE TABLE IF NOT EXISTS listas_seguimiento_marcas (
    id SERIAL PRIMARY KEY,
    columna_id INTEGER NOT NULL REFERENCES listas_seguimiento_columnas(id) ON DELETE CASCADE,
    estudiante_id INTEGER NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
    marcado BOOLEAN NOT NULL DEFAULT FALSE,
    nota TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (columna_id, estudiante_id),
    -- Dentro del CREATE TABLE y no en un ALTER aparte (cambio hecho al
    -- escribir la migración real): así el archivo entero se puede reejecutar
    -- sin error, igual que hace 20260908_observador_anotaciones.sql.
    CONSTRAINT chk_listas_seguimiento_marcas_nota_longitud
        CHECK (nota IS NULL OR char_length(nota) <= 240)
);
CREATE INDEX IF NOT EXISTS idx_listas_seguimiento_marcas_columna
    ON listas_seguimiento_marcas(columna_id);
CREATE INDEX IF NOT EXISTS idx_listas_seguimiento_marcas_estudiante
    ON listas_seguimiento_marcas(estudiante_id);
```

`UNIQUE (columna_id, estudiante_id)` + upsert (`ON CONFLICT ... DO UPDATE`)
copia el patrón ya probado en `tipos_pagos_estudiantes`
(`app/controllers/tipos_pagos_controller.py:639-651`).

## Capas (mismo layout que el resto del repo)

- `app/schemas/listas_seguimiento.py` — `ColumnaSeguimientoCreate {nombre}`,
  `MarcaSeguimientoItem {columna_id, estudiante_id, marcado, nota}`. **Hecho
  (2026-09-22)**, con `tests/test_listas_seguimiento_esquemas.py` (22
  pruebas). El criterio, copiado de `observador.py`: **toda regla que la base
  ya impone se repite aquí**, para que salga como 422 con mensaje útil en vez
  de reventar dentro de PostgreSQL y llegar como 500. Tres cosas a saber:
    - **Se agregó un tercer objeto, `LoteDeMarcas`**, que no estaba en esta
      lista: es el tipo del cuerpo de `POST .../marcas`, una lista pelada con
      dos reglas encima — no vacía y sin celdas repetidas. Son dos de los 422
      que la tabla de "Cambios de API" ya promete. La de celdas repetidas es
      la que **impide un 500**: `guardar_marcas` escribe el lote en una sola
      sentencia con `ON CONFLICT DO UPDATE`, y PostgreSQL aborta si la misma
      celda viene dos veces. Viven en el esquema y no en la ruta a propósito;
      `app/routes/asistencia.py` las tiene en la ruta, pero eso está
      documentado como defecto conocido de esa capa, no como patrón a copiar.
    - **El recorte de espacios corre antes de medir la longitud**, en `nombre`
      y en `nota`. Así lo que se mide es lo que se va a guardar, y un texto
      que solo se pasa por espacios sobrantes se acepta en vez de rechazarse
      por largo. Los espacios interiores no se tocan: que "a  b" y "a b"
      cuenten como el mismo nombre lo resuelve el índice único.
    - **`marcado` es obligatorio, sin valor por defecto.** Con un defecto de
      `False`, un cliente que se olvidara del campo borraría la marca en vez
      de dejarla como estaba, porque el lote se guarda con upsert: lo que
      llega pisa lo que había. `nota` sí admite faltar, y admite `null`, que
      es lo que manda un formulario vacío desde JavaScript; las dos formas se
      guardan como cadena vacía.
- `app/repositories/listas_seguimiento_repository.py` — SQL puro: leer
  columnas de un curso, leer el roster del curso (`SELECT id, nombre,
  apellido FROM estudiantes WHERE curso_id = %s ORDER BY apellido, nombre`
  — misma consulta que ya usa, para otro fin,
  `estado_cuenta_curso_controller` en
  `app/controllers/estado_cuenta_controller.py:40-51`, replicada acá sin la
  parte de deudas porque la original está privada dentro de un controlador
  de cartera), leer marcas por columnas, chequear nombre duplicado,
  crear/borrar columna, upsert de marca. **Hecho (2026-09-22).** Ocho
  funciones: `existe_curso`, `leer_columnas_del_curso`,
  `leer_estudiantes_del_curso`, `leer_marcas_de_columnas`,
  `existe_columna_con_ese_nombre`, `crear_columna`, `eliminar_columna`,
  `guardar_marcas`. Tres decisiones que conviene conocer antes de escribir el
  controlador:
    - **`existe_curso` no estaba en esta lista y se agregó.** El controlador
      tiene que devolver 404 para un curso inexistente, y sin esa consulta un
      curso inventado y un curso real recién creado se ven igual: los dos
      devuelven cero columnas y cero alumnos. No es una función de producto
      nueva, es lo que el 404 ya prometido necesita.
    - **`guardar_marcas` escribe el lote entero en una sola sentencia**, con
      `UNNEST` sobre cuatro arrays en paralelo, y no una sentencia por celda.
      Contra Neon cada ida y vuelta cuesta ~180 ms: marcar una columna de 30
      alumnos serían 30 viajes, unos 5,4 s, con el patrón por fila que
      todavía tiene `asistencia_repository`. Es la misma lección que dejó
      escrita `observador_repository`. Consecuencia para el paso 4:
      **PostgreSQL aborta la sentencia entera si el lote trae la misma celda
      dos veces** (error `ON CONFLICT DO UPDATE command cannot affect row a
      second time`), así que el 422 por celdas repetidas no es cosmético, es
      lo que evita ese error.
    - **La comprobación de nombre duplicado normaliza en SQL, no en Python**,
      con la misma expresión del índice único y aplicada a los dos lados de
      la comparación. Así hay una sola definición de "mismo nombre" y no dos
      que puedan separarse; una prueba lo verifica leyendo el propio archivo
      de migración. Aun así el controlador **también** tiene que atrapar el
      error de unicidad: entre ese `SELECT` y el `INSERT` hay una ventana por
      la que otra petición puede colarse.
- `app/controllers/listas_seguimiento_controller.py` — arma la respuesta
  combinada, valida curso existente (404), nombre duplicado (409), y que
  cada `columna_id`/`estudiante_id` de un lote de marcas realmente
  pertenezca al curso antes de guardar nada. **Hecho (2026-09-22)**, con
  `tests/test_listas_seguimiento_controlador.py` (23 pruebas). Cuatro cosas a
  saber:
    - **No conoce HTTP.** Lanza `CursoNoEncontradoError`,
      `ColumnaDuplicadaError`, `ColumnaNoEncontradaError` y
      `MarcasFueraDelCursoError`; traducirlos a 404/409/422 es trabajo de la
      ruta, igual que hace `curso_controller` con `CursoDuplicadoError`. Hay
      prueba que lo fija.
    - **El duplicado se atrapa dos veces, y las dos hacen falta.** La consulta
      previa da el 409 legible; el `except IntegrityError` recoge la carrera
      —dos pestañas, un doble clic— que el índice único rechaza. Sin el
      segundo, esa carrera sería un 500.
    - **Los mensajes de error son constantes**, nunca `str(exc)` de la base.
      El frontend los muestra tal cual, y el texto de un `IntegrityError`
      pondría nombres de tablas e índices en la pantalla de una secretaria.
      Es la lección que dejó escrita `app/routes/observador.py`, y hay prueba
      que lo verifica.
    - **Coste fijo en consultas**, que es lo que se degrada en silencio: el
      `GET` cuesta 4 (o 3 si el curso no tiene columnas), crear 3, borrar 1 y
      guardar el lote 3. **Ninguno crece con la cantidad de alumnos ni de
      columnas.** Cada operación usa una sola conexión, y en las escrituras
      validar y escribir van dentro de la misma transacción: si se validara en
      una conexión y se escribiera en otra, entre las dos podrían borrar la
      columna que se acaba de dar por buena.
- `app/routes/listas_seguimiento.py` — `APIRouter(prefix="/listas-seguimiento",
  dependencies=[Depends(get_current_active_admin)])`, igual que
  `tipos_pagos.py`/`cursos.py`: solo admin a nivel de router, sin necesidad
  de los helpers de `app/core/permissions.py` (esos acotan a un profesor a
  sus propias asignaciones; acá no aplica). **Hecho (2026-09-22)**, con
  `tests/test_listas_seguimiento_routes.py` (23 pruebas). Tres cosas a saber:
    - **La protección va en el `APIRouter`, no en cada función.** Así un
      endpoint nuevo nace protegido en vez de nacer abierto y depender de que
      alguien se acuerde. Hay prueba que lo fija, y otra que comprueba que un
      profesor recibe 403 en las cuatro rutas.
    - **El cuerpo del `POST` de marcas se declara `LoteDeMarcas`**, no
      `list[MarcaSeguimientoItem]`. Parecen lo mismo y no lo son: con el
      segundo se pierden las dos reglas del lote y una celda repetida llegaría
      a PostgreSQL, que aborta la sentencia entera — un 500 donde el documento
      promete un 422. Hay prueba que lo fija **pasando por FastAPI**, porque
      hasta el paso 5 ese tipo solo se había ejercitado por separado.
    - `str(exc)` **sí** es seguro en esta capa, al contrario de lo que avisa
      `observador.py`: los cuatro errores que traduce llevan mensajes que son
      constantes escritas a mano en el controlador, nunca texto de PostgreSQL.
- Registrar el router en `app/main.py`, junto a los demás. **Hecho.** Hay
  prueba de que está registrado: sin ella el módulo existiría, pasaría sus
  pruebas y no respondería a nadie.

## Cambios de API

| Método | Ruta | Body | Notas |
|---|---|---|---|
| `GET` | `/listas-seguimiento/{curso_id}` | — | columnas + roster + marcas en una sola respuesta; 404 si el curso no existe |
| `POST` | `/listas-seguimiento/{curso_id}/columnas` | `{"nombre": "..."}` | 201; 409 si el nombre ya existe en ese curso |
| `DELETE` | `/listas-seguimiento/{curso_id}/columnas/{columna_id}` | — | borra en cascada sus marcas |
| `POST` | `/listas-seguimiento/{curso_id}/marcas` | lista `[{columna_id, estudiante_id, marcado, nota}]` (mismo formato de lista que ya usa `POST /asistencia`) | 422 si el lote viene vacío, con celdas repetidas, o referencia algo fuera del curso |

Forma de la respuesta de `GET /listas-seguimiento/{curso_id}`:

```jsonc
{
  "curso_id": 12,
  "columnas": [{"id": 5, "nombre": "Asistió a la cumbre"}],
  "estudiantes": [
    {
      "estudiante_id": 101, "nombre": "Juan", "apellido": "Pérez",
      "marcas": {"5": {"marcado": true, "nota": "Llegó tarde"}}
    }
  ]
}
```

Las claves de `marcas` son el id de columna (como texto, por cómo serializa
JSON). Un alumno sin fila para una columna simplemente no aparece ahí — el
frontend le pone el default (`marcado: false, nota: ""`), igual que ya hace
con `notas`/`valoraciones` ausentes en la respuesta de planilla.

## Invariantes

- Un curso sin columnas definidas se ve exactamente igual que hoy: nada que
  mostrar, sin error.
- No se toca `notas_detalle`, `asistencia`, `tipos_de_pagos` ni ninguna
  tabla existente.
- Permisos, roles y aislamiento por tenant no cambian: el router es
  admin-only, igual que `tipos_pagos`/`cursos`; el aislamiento entre
  colegios lo sigue dando el `search_path` por schema, como en el resto del
  sistema.

## Riesgos y mitigación

| Riesgo | Mitigación |
|---|---|
| Publicar el router antes de aplicar la migración | Solo fallan los endpoints nuevos (`relation does not exist`); no afecta nada existente. Aun así, ver "Orden de despliegue obligatorio". |
| Nombre de columna duplicado por una carrera de condición (dos requests casi simultáneos) | El índice único (`idx_listas_seguimiento_columnas_nombre_unico`) es la garantía real; el chequeo previo en el controlador es solo para devolver un 409 legible en el caso normal. |
| Migración multi-tenant | Se aplica con el runner ya probado (`apply_migration.py`), igual que las migraciones anteriores. |

### Orden de despliegue obligatorio

1. Aplicar `migrations/20260921_listas_seguimiento.sql` a todos los tenants
   activos con `apply_migration.py` (`--dry-run` primero).
2. Regenerar `migrations/base/20260813_esquema_base_tenant.sql` con
   `scripts/generar_esquema_base.py`, después del paso 1.
3. Confirmar que `tests/test_esquema_base.py` pasa.
4. Recién después, `git push origin main` — en este repositorio un push a
   `main` despliega producción automáticamente.

## Plan de fases (backend)

1. Migración: las dos tablas de arriba. **Hecho (2026-09-22)** en
   `migrations/20260921_listas_seguimiento.sql`. Escrita, no aplicada.
2. `app/repositories/listas_seguimiento_repository.py`. **Hecho
   (2026-09-22)**, con `tests/test_listas_seguimiento_repositorio.py`
   (27 pruebas).
3. `app/schemas/listas_seguimiento.py`. **Hecho (2026-09-22)**, con
   `tests/test_listas_seguimiento_esquemas.py` (22 pruebas).
4. `app/controllers/listas_seguimiento_controller.py`. **Hecho
   (2026-09-22)**, con `tests/test_listas_seguimiento_controlador.py`
   (23 pruebas).
5. `app/routes/listas_seguimiento.py` + registro en `app/main.py`. **Hecho
   (2026-09-22)**, con `tests/test_listas_seguimiento_routes.py`
   (23 pruebas).
6. Pruebas (`tests/test_listas_seguimiento_controlador.py`,
   `tests/test_listas_seguimiento_routes.py`). **Hecho (2026-09-22).** Cada
   capa llevó las suyas en su propio paso, en vez de dejarlas todas al final:
   una prueba escrita tres pasos después ya no atrapa el error mientras se
   comete. Total: 96 pruebas propias — 27 del repositorio, 22 de los
   esquemas, 24 del controlador y 23 de las rutas.
7. Aplicar la migración real a los tenants y regenerar el esquema base.
   **Hecho (2026-09-22)**, fuera de orden y a propósito: el "Orden de
   despliegue obligatorio" de más arriba manda aplicar antes de publicar, no
   al final del código. Aplicada a `tenant_colegio_1` y `tenant_2005`;
   esquema base regenerado desde `tenant_colegio_1`. Detalle en
   `docs/MIGRACIONES.md`.

## Ampliación: crear una columna en todos los cursos (2026-09-22)

**En diseño. Sin código escrito todavía.**

### De dónde sale

El usuario preguntó si una columna podía "replicarse" en todos los cursos.
Se aclaró primero el alcance: se refiere a **todos los cursos de su colegio**,
no a los dos colegios de la plataforma. Cruzar tenants sería otra cosa muy
distinta —solo tendría sentido desde el super admin, con una tabla de
plantillas en `public`— y **no** es lo que se pide.

Después se le ofrecieron dos caminos y eligió el primero:

1. **Copiar al crear**, que es este. Se crean N columnas iguales, una por
   curso, independientes a partir de ese momento.
2. Una columna compartida de verdad, que viviría en todos los cursos a la
   vez. **Descartada** por ahora: pide migración, tocar las cuatro capas y
   resolver que el índice único no protege igual cuando `curso_id` queda
   vacío.

Esto **reabre a propósito** la decisión "cada curso tiene su propia lista
independiente". Se reabre sin romperla: las columnas siguen siendo de un solo
curso; lo único que se añade es la comodidad de no teclear el mismo nombre
once veces.

### Lo que NO cambia

- **Ninguna migración.** Las tablas se quedan exactamente como están. Es lo
  que hace barato este camino, y también lo que lo hace seguro:
  `20260921_listas_seguimiento.sql` ya está aplicada y su checksum guardado,
  así que no se puede editar.
- Los cuatro endpoints actuales siguen igual.
- Una columna sigue perteneciendo a un solo curso, y sus marcas a esa columna.

### El endpoint nuevo

| Método | Ruta | Body | Notas |
|---|---|---|---|
| `POST` | `/listas-seguimiento/columnas-en-todos-los-cursos` | `{"nombre": "..."}` | Crea la columna en todos los cursos activos que aún no la tengan |

Sin `curso_id` en la ruta, a propósito: no actúa sobre un curso sino sobre
todos. Respuesta:

```jsonc
{"creadas": 9, "omitidas": 2, "total": 11}
```

`omitidas` son los cursos que ya tenían una columna con ese nombre. Con eso
la pantalla puede decir algo honesto: "Creada en 9 cursos. 2 ya la tenían."

### Decisiones de diseño

1. **Solo cursos activos.** No es un capricho: `GET /cursos` devuelve solo
   los activos por defecto (`app/routes/cursos.py`), así que el selector de
   esta pantalla ya solo muestra esos. Crear columnas en cursos que el admin
   no ve sería crear basura invisible.
2. **Los cursos que ya la tienen se saltan, no dan error.** Eso vuelve el
   botón **repetible**, y con eso se cubre el caso del curso nuevo: se crea
   4C en marzo, se vuelve a pulsar con el mismo nombre y solo se crea en 4C.
   Sin esto, un curso creado después se quedaría sin la columna para siempre.
3. **Una sola sentencia**, no una por curso. Con once cursos, el camino
   ingenuo —leer cursos, preguntar por cada uno si ya la tiene, insertar—
   serían 23 idas y vueltas, unos 4 s contra Neon. La forma correcta es un
   `INSERT ... SELECT ... WHERE NOT EXISTS` sobre `cursos`, que hace el
   filtro y la inserción de golpe y devuelve `rowcount`. Es la misma lección
   que ya está escrita en `listas_seguimiento_repository.py`.
4. **El índice único sigue siendo la garantía real.** El `NOT EXISTS` evita
   el error en el caso normal; si dos peticiones entran a la vez, quien
   rechaza es el índice, igual que en el alta normal.

### Fuera de alcance de esta ampliación

Se cierran a propósito, igual que las otras puertas del documento:

- **Borrar en todos los cursos.** No se pidió. Hoy se borra curso por curso.
- **Elegir un subconjunto de cursos.** El pedido es "todos", no "estos".
- **Renombrar una columna**, ni suelta ni en todos los cursos.
- **Columna compartida de verdad**, que es el camino 2 de arriba.

### Plan de fases (ampliación)

Backend primero, como siempre:

1. `crear_columna_en_cursos_activos` en
   `app/repositories/listas_seguimiento_repository.py`, con sus pruebas.
   **Hecho (2026-09-22).** Se agregaron dos funciones, no una:
   `crear_columna_en_cursos_activos` y `contar_cursos_activos`, esta última
   solo para que el mensaje de la pantalla pueda decir "9 de 11" sin decidir
   nada. Diez pruebas nuevas.
   - **Se extrajo `_nombre_normalizado(expresion)`**, un cambio pequeño al
     código del paso 2 original. La regla que iguala dos nombres ya la
     necesitan dos consultas, y una tercera copia literal sería una tercera
     cosa capaz de separarse del índice sin que nadie lo note. Las pruebas
     que ya existían pasaron sin tocarlas, que es lo que confirma que el
     cambio no altera el SQL que se envía.
   - **Ensayada contra PostgreSQL real el 2026-09-22**, en `tenant_colegio_1`,
     con el mismo método que la vez anterior: una transacción que termina en
     `ROLLBACK` y no deja ni una fila. Las once comprobaciones pasaron. Tres
     valían el viaje porque ninguna prueba con cursor falso puede darlas: que
     repetir el alta **no duplica nada** (segunda pasada, 0 creadas), que con
     otras mayúsculas y espacios de sobra **tampoco** crea nada, y que
     rellenar un solo hueco crea exactamente una. También se comprobó el
     filtro de estado poniendo un curso en `inactivo` —queda fuera— y luego
     con `estado` nulo —sí entra—, revirtiendo las dos cosas y verificando
     después, con una conexión nueva, que los estados quedaron intactos.
   - **Dato medido, no supuesto: `tenant_colegio_1` tiene 25 cursos.** Yo
     había escrito "once" en los comentarios. Con 25, el camino ingenuo serían
     51 idas y vueltas, unos 9 s: el argumento de hacerlo en una sola
     sentencia es más fuerte de lo que decía. Los números del código se
     corrigieron con la medida real.
   - **La regla de "curso activo" se copió tal cual del resto del sistema**:
     `COALESCE(LOWER(estado), 'activo') = 'activo'`. Ojo al detalle, que no
     es evidente: `cursos.estado` admite nulos y un NULL **cuenta como
     activo**. Es la misma expresión que usa `_agregar_filtro_estado` en
     `curso_controller`, que decide qué devuelve `GET /cursos` y con ello qué
     ve el selector de la pantalla. Hay prueba que lee el controlador y falla
     si las dos se separan.
2. `crear_columna_en_todos_los_cursos_controller` en el controlador, con sus
   pruebas. **Hecho (2026-09-22).** Devuelve
   `{creadas, omitidas, total}`. Ocho pruebas nuevas. Tres decisiones:
   - **Crear que no crea nada no es un error.** Si todos los cursos ya la
     tenían, `creadas` vale 0 y la respuesta es un éxito. Es la consecuencia
     de que el alta salte en silencio los que ya la tienen, que es lo que
     vuelve repetible el botón. Un colegio sin cursos activos tampoco falla.
   - **Primero se crea y después se cuenta**, no al revés. Si se contara
     antes, un curso creado por otra persona entre las dos consultas entraría
     en el alta pero no en el conteo, `creadas` podría superar a `total` y la
     pantalla mostraría un número **negativo** de omitidas. En este orden todo
     curso en el que se insertó existe y está activo al contar. El
     `max(..., 0)` cubre el último resquicio —que borren un curso justo en
     medio— y solo impide un número imposible en pantalla.
   - **La carrera del índice lleva mensaje propio**, no el de "ya existe esa
     columna": el usuario pidió rellenar los cursos que faltaran, no crear
     una sola. Reintentar funciona, porque a la segunda el `NOT EXISTS` ya la
     ve. Sin ese `except` sería un 500.
3. La ruta nueva en `app/routes/listas_seguimiento.py` —el router ya existe y
   ya es admin-only—, con sus pruebas. **Hecho (2026-09-22).** Ocho pruebas
   nuevas. Dos decisiones:
   - **Responde 200, no 201**, al contrario que el alta de una sola columna.
     Que no cree nada es un resultado válido y frecuente —si todos los cursos
     ya la tenían— y un 201 fijo estaría mintiendo la mitad de las veces. El
     cuerpo dice lo que pasó de verdad.
   - **Se comprobó que la ruta nueva no ensombrece a las que llevan curso.**
     `/listas-seguimiento/columnas-en-todos-los-cursos` encaja también en el
     molde de `/listas-seguimiento/{curso_id}`. Son métodos distintos, así que
     no debería haber choque, pero eso es razonarlo y no verlo: hay una prueba
     que ejercita las tres conviviendo.
   Con esto **el backend de la ampliación está completo**: quedan las fases 4
   a 6, todas de frontend y documentación.
4. Frontend: servicio y hook de comando, con sus pruebas. **Pendiente.**
5. Frontend: la casilla en `GestionColumnasSeguimiento` y el cableado en la
   página, con pruebas de integración. **Pendiente.**
6. Documentación transversal de los dos repos. **Pendiente.**

## Preguntas abiertas

- ¿Un `curso_id` se reutiliza de un año lectivo a otro, o cada año se crea
  un curso nuevo? Define si en el futuro hace falta un corte por
  período/año para estas columnas. **Sigue sin responder al 2026-09-22:** el
  usuario contestó que todavía no ha vivido un cambio de año lectivo
  completo, así que no lo sabe. No bloquea nada; el diseño actual no depende
  de la respuesta. Dato verificado en el esquema: `cursos` no tiene ninguna
  columna de año ni de período, o sea que hoy el sistema no modela años
  lectivos en absoluto. Si mañana se reutiliza el mismo curso, las columnas
  del año anterior seguirán apareciendo y habrá que borrarlas a mano.
- ¿Hace falta poder reordenar columnas a mano? **Respondida el 2026-09-22:
  no.** El usuario confirmó que le sirve el orden de creación. Sigue en
  "Fuera de alcance"; la tabla no lleva columna de orden.

## Entrega para el siguiente chat

- Última acción terminada: **paso 5, y con él todo el backend**, el
  2026-09-22.
- Commits ya hechos por el usuario, **ninguno pusheado**:
  - `8d9fa09` — la migración y su documentación (paso 1).
  - `02b9d2e` — el repositorio y sus 27 pruebas (paso 2).
  - `23737bc` — la migración aplicada y el esquema base regenerado (paso 7).
  - `535200c` — los esquemas de entrada y sus 22 pruebas (paso 3).
  - El paso 4 (controlador, 23 pruebas) y el paso 5 (rutas, registro en
    `app/main.py`, 23 pruebas) están **sin commit todavía**, junto con la
    documentación de cierre.
- Verificación del paso 5, con las variables de CI (`DATABASE_URL` falsa,
  para no poder alcanzar ninguna base real):
  - `scripts/verify.py`: **1406 pruebas pasan, 0 fallan.** Ruff y `pip check`
    limpios.
  - `git diff --check`: limpio.
  - Las pruebas de ruta conducen la aplicación **real** por su interfaz ASGI,
    no llaman a las funciones de ruta a mano: llamarlas directamente no
    observa el código de estado, lo infiere, y el código es justo lo que esa
    capa decide. No se usa `TestClient` porque `httpx` no está instalado,
    igual que en `test_ventas_caracterizacion.py`.
  - No hubo que tocar ningún archivo de otro módulo. `app/main.py` sí se
    modifica, en dos líneas: el import y el `include_router`.
- Documentación transversal actualizada al cerrar el backend, como pide el
  `CLAUDE.md` del repo: `docs/API_ENDPOINTS.md` (los cuatro endpoints y sus
  respuestas), `docs/ROLES_PERMISOS_BACKEND.md` (el router en la lista de
  admin-only) y `docs/CAMBIOS_BACKEND.md` (la entrada del 2026-09-22).
- Lo que hubo que tocar de otros módulos en el paso 2, por si alguien lo
  revisa: los cinco censos de `app/repositories/` que viven en
  `tests/test_{asistencia,dashboard,notas,planilla,ventas}_caracterizacion.py`
  reconocen ahora el archivo nuevo. Son guardias que enumeran el conjunto
  exacto a propósito; no se tocó nada más de esos módulos. Aparecer ahí no
  mete esta funcionalidad en el programa de `docs/modularizacion/`.
- Riesgo abierto a tener presente: `20260921_listas_seguimiento.sql` **ya no
  se puede editar**, porque está aplicada y el runner guarda su checksum. Si
  los pasos 4 a 6 revelaran que a las tablas les falta algo, va en una
  migración nueva, como ya pasó con las tres del observador.
- **El SQL sí se ejecutó contra PostgreSQL real** (2026-09-22). Las 96
  pruebas usan dobles y no tocan la base, así que se hizo aparte un ensayo
  sobre `tenant_colegio_1` (Colegio Demo): una sola transacción que llama a
  **las ocho funciones reales del repositorio** y termina en `ROLLBACK`. No
  quedó ninguna fila; se comprobó reconectando. `tenant_2005`, el colegio
  real, no se tocó. Las 21 comprobaciones pasaron, y cuatro de ellas eran
  suposiciones escritas en el código que hasta entonces nadie había visto
  cumplirse:
    - el `UNNEST` con cuatro arrays escribe el lote entero de una vez, y los
      valores vuelven idénticos, incluidos `False` y la cadena vacía;
    - el upsert **pisa** la celda en vez de duplicarla;
    - el índice único rechaza `"  ensayo   TECNICO  "` frente a
      `"Ensayo tecnico"` (`pgcode 23505`), o sea que la normalización del 409
      y la del índice coinciden de verdad;
    - **PostgreSQL aborta el lote con la misma celda dos veces**, con el texto
      exacto `ON CONFLICT DO UPDATE command cannot affect row a second time`.
      Era una predicción escrita en el repositorio, el esquema y el documento;
      ahora está comprobada, y con ella el motivo de que el 422 por celdas
      repetidas no sea cosmético.
  También se comprobaron el `CHECK` de 240 caracteres (`pgcode 23514`), el
  borrado en cascada y que una columna no se puede borrar desde otro curso.
- **Se cerró además la suposición más peligrosa que quedaba**, con una prueba
  permanente en `tests/test_listas_seguimiento_controlador.py`:
  `crear_columna_controller` y `guardar_marcas_controller` devuelven su
  resultado **desde dentro** del `with get_cursor(commit=True)`. Si eso no
  confirmara la transacción, crear una columna no guardaría nada y todas las
  demás pruebas seguirían en verde, porque el `get_cursor` falso solo anota
  con qué valor de `commit` se le llamó, no si alguien lo honra.
  `tests/test_db_session_contrato.py` cubría el `with` que termina solo y el
  que termina en excepción, pero no este.
- Lo que **sigue sin probarse** es la cadena entera de una vez: ruta →
  controlador → repositorio → base real. Cada eslabón está probado por
  separado. Una prueba de humo a mano contra el servidor local, entrando como
  admin, lo cerraría del todo; el riesgo que queda es bajo pero no es cero.
- Siguiente acción exacta: **el frontend**, paso 1 de su propio plan de fases
  en `frontend-react/docs/funcionalidades/LISTAS_SEGUIMIENTO.md`
  (`listasSeguimientoApi.js` + utils + sus pruebas). La condición que ese
  documento ponía para empezar —que los cuatro endpoints existan y estén
  verificados— ya se cumple. **No iniciado.**
- Riesgo abierto que sigue en pie: `20260921_listas_seguimiento.sql` **no se
  puede editar**, porque está aplicada y el runner guarda su checksum.
  Cualquier cambio en las tablas va en una migración nueva.
