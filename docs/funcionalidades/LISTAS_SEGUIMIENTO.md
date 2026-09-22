# Funcionalidad: Listas de Seguimiento por Curso — Backend

## Control

- Estado: **Pasos 1 y 2 de 7 hechos.** Existen
  `migrations/20260921_listas_seguimiento.sql` (commit `8d9fa09`) y
  `app/repositories/listas_seguimiento_repository.py` con sus 27 pruebas. No
  hay esquemas, controlador ni rutas todavía, y **la migración sigue sin
  aplicarse a ningún tenant ni a Neon**.
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
  ya tomadas").
- Un corte por período o año lectivo: no existe esa dimensión en este
  diseño; una columna vive mientras exista el curso, hasta que el admin la
  borre a mano.
- Reordenar columnas a mano (drag and drop): no se pidió; se listan en el
  orden en que se crean.

## Decisiones ya tomadas (con el usuario, en la conversación de origen)

- Columnas **independientes por curso**, sin compartir ni reutilizar entre
  cursos — no hace falta una tabla puente como `tipos_pagos_cursos`.
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
  `MarcaSeguimientoItem {columna_id, estudiante_id, marcado, nota}`.
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
  pertenezca al curso antes de guardar nada.
- `app/routes/listas_seguimiento.py` — `APIRouter(prefix="/listas-seguimiento",
  dependencies=[Depends(get_current_active_admin)])`, igual que
  `tipos_pagos.py`/`cursos.py`: solo admin a nivel de router, sin necesidad
  de los helpers de `app/core/permissions.py` (esos acotan a un profesor a
  sus propias asignaciones; acá no aplica).
- Registrar el router en `app/main.py`, junto a los demás.

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
3. `app/schemas/listas_seguimiento.py`. **Pendiente.**
4. `app/controllers/listas_seguimiento_controller.py`. **Pendiente.**
5. `app/routes/listas_seguimiento.py` + registro en `app/main.py`.
   **Pendiente.**
6. Pruebas (`tests/test_listas_seguimiento_controlador.py`,
   `tests/test_listas_seguimiento_routes.py`). **Pendiente.**
7. Aplicar la migración real a los tenants y regenerar el esquema base.
   **Pendiente.**

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

- Última acción terminada: **paso 2 del "Plan de fases"**, el 2026-09-22.
  - El paso 1 (la migración) quedó commiteado por el usuario como `8d9fa09`,
    junto con `docs/MIGRACIONES.md` y este documento. **Sin pushear.**
  - El paso 2 agrega `app/repositories/listas_seguimiento_repository.py` y
    `tests/test_listas_seguimiento_repositorio.py` (27 pruebas). Sin commit
    todavía.
- Archivos de otros módulos que hubo que tocar, y por qué:
  `tests/test_asistencia_caracterizacion.py`,
  `test_dashboard_caracterizacion.py`, `test_notas_caracterizacion.py`,
  `test_planilla_caracterizacion.py` y `test_ventas_caracterizacion.py`
  llevan un **censo con la lista exacta de los archivos de
  `app/repositories/`**, puesto a propósito para que un repositorio nuevo no
  se cuele sin que nadie lo note (lo dice el docstring del de asistencia). Se
  agregó `listas_seguimiento_repository` a las cinco listas y se subió de 17
  a 18 el conteo de `test_asistencia_caracterizacion.py:228`. **No se tocó
  ninguna otra línea ni el código de esos módulos**: es el reconocimiento que
  el propio guardián exige, no un cambio de su comportamiento. Ojo: aparecer
  en ese censo no significa que esta funcionalidad forme parte del programa
  de `docs/modularizacion/`, que no la incluye.
- Verificación del paso 2, con las variables de CI (`DATABASE_URL` falsa,
  para no poder alcanzar ninguna base real):
  - `scripts/verify.py`: **1336 pruebas pasan, 1 falla esperada**,
    `test_esquema_base.py::test_la_base_incorpora_todas_las_migraciones_de_tenant`.
    Ruff y `pip check` limpios.
  - Esa falla es el guardián del esquema base y es **correcta**: avisa que
    hay una migración en `migrations/` que
    `migrations/base/20260813_esquema_base_tenant.sql` todavía no declara.
    Se apaga sola al aplicar la migración a un schema de referencia y
    regenerar la base con `scripts/generar_esquema_base.py`, que lee la
    estructura desde una base real. Mismo estado documentado que tuvo
    `20260915_cursos_director_grupo.sql` en `docs/MIGRACIONES.md`.
  - `git diff --check`: limpio.
  - Lo que **no** se pudo verificar: no hay PostgreSQL local ni Docker en la
    máquina, así que ninguna sentencia SQL de esta funcionalidad se ha
    ejecutado nunca contra un motor real. Lo que sí se comprobó sin base: que
    psycopg2 traduce las listas de Python a `ARRAY[...]`, que es de lo que
    depende el `UNNEST` de `guardar_marcas`.
- **Riesgo abierto, y es el importante:** el commit `8d9fa09` ya existe sin
  que la migración se haya aplicado ni el esquema base regenerado. Si se
  pushea así, CI (`backend-quality.yml`, que corre `scripts/verify.py`) queda
  en rojo, y un colegio nuevo nacería sin estas dos tablas. Todavía se puede
  arreglar antes de publicar: aplicar la migración, regenerar la base y sumar
  eso en un commit antes del push.
- Siguiente acción exacta: paso 3 del "Plan de fases",
  `app/schemas/listas_seguimiento.py` — los modelos Pydantic
  `ColumnaSeguimientoCreate {nombre}` y
  `MarcaSeguimientoItem {columna_id, estudiante_id, marcado, nota}`, con sus
  pruebas. **No iniciado.**
- Sin más riesgos abiertos conocidos que ese y las preguntas abiertas de
  arriba, ninguna de las cuales bloquea seguir.
