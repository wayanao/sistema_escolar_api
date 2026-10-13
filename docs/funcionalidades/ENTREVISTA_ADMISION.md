# Funcionalidad: Entrevista de admisión — Backend

## Control

- Estado: **Diseño y documentación (paso E0), 2026-10-12. No hay código de
  esta funcionalidad todavía.** El reparto de campos entre la ficha del
  estudiante y la entrevista es una propuesta del asistente que el usuario
  pidió ("ayúdame y ten una base de qué va en cada formulario") y falta que
  la confirme.
- Tipo: función nueva de producto. No es una capa del programa de
  modularización de `docs/modularizacion/`.
- Repos afectados: este repo (`sistema_escolar_api`) y `frontend-react`. Ver
  `frontend-react/docs/funcionalidades/ENTREVISTA_ADMISION.md`, que cubre las
  pantallas.
- Relación con el año lectivo: **vive en la preparación del año siguiente**
  (decisión del usuario). Depende de lo hecho en
  `docs/funcionalidades/ANIO_LECTIVO.md` (año en preparación, alta directa de
  estudiantes en ese año, guardia de escritura).
- Riesgo: **medio-alto.** Migración en todos los tenants, datos personales de
  menores (Ley 1581 de 2012) y cambia cómo se crea un estudiante nuevo en el
  año en preparación.
- Fecha límite: **principios de noviembre de 2026**, cuando el colegio
  empieza a matricular para 2027.
- Última actualización: 2026-10-12.

## Objetivo

Que, antes de matricular a un estudiante **nuevo** en el año en preparación,
el colegio registre al aspirante, haga la entrevista con la familia y deje un
resultado: **aprobado** o **no aprobado**. Solo un aspirante aprobado se puede
matricular, y al hacerlo no se vuelve a digitar lo que ya se escribió.

## Lo que se encontró (verificado en el código el 2026-10-12)

- En ningún repo existe nada de entrevista, admisión, aspirante ni
  inscripción (búsqueda en código y documentos).
- Hoy un estudiante nuevo en el año en preparación se crea directo con
  `POST /anios-lectivos/{id}/estudiantes`
  (`crear_estudiante_en_preparacion_controller`, paso 5.5 del año lectivo):
  datos globales del estudiante y su matrícula de ese año, en una sola
  transacción.
- Los campos que se proponen mover (estudios anteriores y ocupación de los
  padres) **solo se usan para crear, editar y leer al estudiante**
  (`schemas/estudiante.py`, `estudiante_controller.py`,
  `estudiantes_repository.py`, `_valores_globales_estudiante` en
  `anios_lectivos_controller.py`). Ningún certificado, boletín, reporte ni
  cálculo los usa. En el frontend solo están en el formulario del
  estudiante.
- `condicion_diagnostico` existe en el backend pero ninguna pantalla lo
  muestra; el formulario lo devuelve tal cual al editar. No se toca aquí.
- `descuento_matricula` y `descuento_mensualidad` ya salieron del formulario
  el 2026-10-12 (no los usa ningún cobro); las columnas siguen.

## Cómo funciona en los colegios (investigación del 2026-10-12)

- En colegios privados, la entrevista suele ser parte de la admisión:
  inscripción → (prueba diagnóstica en algunos grados) → entrevista con la
  familia (psicoorientación, coordinación o rectoría) → resultado → reserva de
  cupo → matrícula.
- En la entrevista se recoge la situación familiar, el colegio anterior y el
  motivo del retiro, salud o necesidades especiales, y el colegio explica
  horarios, normas y costos.
- En colegios oficiales el cupo se asigna por SIMAT (Resolución 7797 de 2015)
  y la entrevista no puede ser un filtro de acceso.
- Límites legales que el diseño respeta:
  - **No discriminación.** La Corte Constitucional (T-510 de 1994) ordenó
    aplicar a todos las mismas reglas de admisión; no se puede rechazar por la
    composición o el origen de la familia, su religión u otras razones así.
    El formulario no pregunta religión, estado civil de los padres ni
    orientación de la familia, y "No aprobado" exige escribir el motivo.
  - **Datos de menores y datos sensibles (Ley 1581 de 2012).** Hace falta la
    autorización expresa del representante legal; el acceso es solo del
    admin. El aspirante no se puede registrar sin marcar la autorización.

## Decisiones ya tomadas (con el usuario, 2026-10-12)

1. **Vive en la preparación del año lectivo.** Se usa mientras el año
   siguiente está en `preparacion`.
2. **Solo para estudiantes nuevos.** Quien ya estudia en el colegio pasa al
   año siguiente como hoy (promoción en "Matricular estudiantes").
3. **Bloquea:** un estudiante nuevo en el año en preparación solo se crea
   desde una entrevista **aprobada**. Quien continúa no se ve afectado.
4. **Resultados:** `pendiente` (mientras se decide), `aprobado` (deja
   matricular) y `no_aprobado` (no deja; exige el motivo).
5. Se quita del formulario del estudiante lo que pasa a la entrevista, y se
   añade la entrevista como formulario nuevo.

Propuestas del asistente, **a confirmar por el usuario**:

6. El reparto de campos de la tabla siguiente.
7. Los datos que se mueven **se copian** a las columnas que ya tiene el
   estudiante en el momento de matricularlo. Así la ficha los lee en un solo
   lugar para todos: los estudiantes de antes (que ya los tienen) y los
   nuevos. Después de matricular, la admisión queda de solo consulta, así que
   la copia no se desactualiza. Ninguna columna se borra.
8. Las admisiones van en una página propia, a la que se llega desde la
   preparación del año (la página de años lectivos ya es larga). Sigue
   "viviendo" en la preparación: solo se usa con un año en `preparacion`.
9. Una admisión que todavía no se matriculó se puede borrar (por un error, o
   si la familia pide retirar sus datos: derecho de supresión de la Ley
   1581). Una matriculada no.

## Qué va en cada formulario (propuesta, decisión 6)

Regla: en la **ficha del estudiante** queda lo que se necesita mientras
estudia (identidad, contacto, salud, a quién llamar) y lo que pide el SIMAT;
en la **entrevista** va lo que solo sirve para decidir la admisión.

| Dato | Dónde | Por qué |
|---|---|---|
| Nombre, apellidos, tipo y número de documento, lugar de expedición, fecha de nacimiento | Ficha (y el aspirante, que lo pasa a la ficha) | Identidad: certificados, boletines, SIMAT |
| Dirección, teléfono, email, estrato | Ficha | Contacto y residencia; el SIMAT pide el estrato |
| Curso y jornada | Ficha | Ya existen; no se tocan |
| EPS, datos médicos y alergias | Ficha | Emergencias mientras estudia |
| Padre y madre: nombre, tipo y número de documento, teléfono | Ficha | A quién llamar; acudientes |
| Contacto de emergencia | Ficha | A quién llamar |
| **Estudios anteriores:** colegio anterior, año cursado, preescolar, EBP, motivo del retiro, paz y salvo | **Entrevista** (se mueve) | Solo sirven para admitir |
| **Ocupación del padre y de la madre** | **Entrevista** (se mueve) | Situación familiar, no se usa después |
| Fecha, quién entrevistó, quiénes asistieron | Entrevista (nuevo) | Registro de la entrevista |
| Con quién vive el aspirante | Entrevista (nuevo) | Situación familiar |
| Por qué eligen el colegio / qué esperan | Entrevista (nuevo) | Expectativas de la familia |
| Observaciones de quien entrevista | Entrevista (nuevo) | Lo que se habló |
| Autorización de datos y quién autoriza | Aspirante (nuevo, obligatorio) | Ley 1581 |
| Resultado y motivo | Entrevista (nuevo) | La decisión |
| Curso del año siguiente al que aspira | Aspirante (nuevo) | Pasa a la matrícula |
| Acudiente: nombre, parentesco, teléfono | Aspirante (nuevo) | Contacto antes de matricular |

## El flujo

```text
Registrar aspirante (datos mínimos + autorización de datos)
        │  resultado = pendiente
        ▼
Entrevista (fecha, quién, asistentes, estudios anteriores, familia,
            expectativas, observaciones)
        ▼
Resultado ──► no_aprobado (con motivo): termina aquí; no se matricula
        │
        └──► aprobado ──► "Matricular": se abre la ficha del estudiante con
                          los datos del aspirante ya puestos; el admin
                          completa dirección, salud y padres; se crea el
                          estudiante con su matrícula del año en preparación
                          y la admisión queda enlazada (solo consulta)
```

## Diseño de datos (paso E1)

Tabla nueva por tenant. Una fila por aspirante y año: aspirante, entrevista y
resultado juntos (en este colegio, cada aspirante tiene una sola entrevista
por año).

```sql
CREATE TABLE IF NOT EXISTS admisiones (
    id SERIAL PRIMARY KEY,
    anio_lectivo_id INTEGER NOT NULL REFERENCES anios_lectivos (id),
    -- Aspirante
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    tipo_documento VARCHAR(50),
    documento_identidad VARCHAR(20),
    fecha_nacimiento DATE,
    curso_id INTEGER,
    acudiente_nombre VARCHAR(150),
    acudiente_parentesco VARCHAR(50),
    acudiente_telefono VARCHAR(50),
    autoriza_datos BOOLEAN NOT NULL,
    autoriza_nombre VARCHAR(150) NOT NULL,
    -- Entrevista
    fecha_entrevista DATE,
    entrevistador VARCHAR(150),
    asistentes VARCHAR(250),
    colegio_anterior VARCHAR(150),
    anio_cursado_anterior VARCHAR(50),
    pre_escolar_anterior VARCHAR(50),
    ebp_anterior VARCHAR(50),
    motivo_retiro_anterior TEXT,
    paz_salvo_anterior VARCHAR(10),
    ocupacion_padre VARCHAR(100),
    ocupacion_madre VARCHAR(100),
    vive_con VARCHAR(250),
    expectativas TEXT,
    observaciones TEXT,
    -- Resultado
    resultado VARCHAR(20) NOT NULL DEFAULT 'pendiente',
    motivo_resultado TEXT,
    decidido_en TIMESTAMPTZ,
    estudiante_id INTEGER UNIQUE REFERENCES estudiantes (id),
    creado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_admisiones_curso_del_anio
        FOREIGN KEY (curso_id, anio_lectivo_id)
        REFERENCES cursos (id, anio_lectivo_id),
    CONSTRAINT chk_admisiones_resultado
        CHECK (resultado IN ('pendiente', 'aprobado', 'no_aprobado')),
    CONSTRAINT chk_admisiones_autoriza CHECK (autoriza_datos),
    CONSTRAINT chk_admisiones_motivo_no_aprobado
        CHECK (resultado <> 'no_aprobado' OR NULLIF(TRIM(motivo_resultado), '') IS NOT NULL),
    CONSTRAINT chk_admisiones_matricula_aprobada
        CHECK (estudiante_id IS NULL OR resultado = 'aprobado')
);
CREATE INDEX IF NOT EXISTS idx_admisiones_anio ON admisiones (anio_lectivo_id, resultado);
CREATE UNIQUE INDEX IF NOT EXISTS idx_admisiones_documento_por_anio
    ON admisiones (anio_lectivo_id, documento_identidad)
    WHERE documento_identidad IS NOT NULL;
```

- La clave foránea compuesta impide que un aspirante de 2027 apunte a un
  curso de 2026 (igual que `matriculas`, que usa `UNIQUE (id,
  anio_lectivo_id)` de `cursos`, existente desde la fase 1 del año lectivo).
- Los `CHECK` hacen que la base misma exija la autorización, el motivo de un
  "no aprobado" y que solo un aprobado quede enlazado a un estudiante.
- Los tamaños de texto son los mismos de las columnas equivalentes de
  `estudiantes` en el esquema base (revisado el 2026-10-12), para que la copia
  al matricular nunca se corte.
- **Ojo, documento repetido:** `estudiantes.documento_identidad` es único en
  todo el colegio (`estudiantes_documento_identidad_key`). Si el aspirante ya
  fue estudiante antes (por ejemplo, se retiró y vuelve), matricularlo como
  nuevo chocaría. Por eso: al registrar el aspirante se avisa si su documento
  ya es de un estudiante, y matricular responde `409` con un mensaje claro en
  vez de un error de la base. Qué hacer con quien vuelve queda en "Preguntas
  abiertas".
- No toca datos existentes. Se prueba en una rama de Neon, se regenera el
  esquema base desde allí y el usuario la aplica en los tenants
  (`docs/MIGRACIONES.md`).

## Rutas (contrato propuesto; pasos E2 y E3)

Todas solo para admin. Las que escriben exigen que el año de la admisión esté
en `preparacion` (`409` con mensaje si no).

| Ruta | Qué hace |
|---|---|
| `GET /anios-lectivos/{id}/admisiones?resultado=` | Lista las admisiones del año (opcional, por resultado), con conteos |
| `POST /anios-lectivos/{id}/admisiones` | Registra un aspirante. Exige nombre, apellido y la autorización con quién autoriza. Queda `pendiente` |
| `GET /admisiones/{admision_id}` | Una admisión completa |
| `PUT /admisiones/{admision_id}` | Edita datos del aspirante y de la entrevista. No cambia el resultado. `409` si ya está matriculada |
| `PUT /admisiones/{admision_id}/resultado` | `{ resultado, motivo_resultado }`. `no_aprobado` exige motivo. `409` si ya está matriculada |
| `DELETE /admisiones/{admision_id}` | Borra una admisión no matriculada (decisión 9) |
| `POST /admisiones/{admision_id}/matricular` | Cuerpo: la ficha del estudiante (como `POST /anios-lectivos/{id}/estudiantes`). Solo si está `aprobado` y sin estudiante. En una transacción: crea el estudiante y su matrícula en el año de la admisión (reutiliza `crear_estudiante_en_preparacion_controller`), copia los datos movidos a sus columnas y enlaza `estudiante_id` |
| `POST /anios-lectivos/{id}/estudiantes` (existente) | Paso E7: responde `409` "Un estudiante nuevo en 2027 se matricula desde su entrevista aprobada (Admisiones)." |

## Plan por pasos (uno a la vez, con el visto bueno del usuario)

| Paso | Repo | Qué |
|---|---|---|
| E0 | ambos | Este diseño. **Hecho el 2026-10-12** |
| E1 | backend | Migración `admisiones` y esquema base (rama de Neon; la aplica el usuario) |
| E2 | backend | Registrar, listar, ver, editar y borrar admisiones; guardia del año; autorización obligatoria |
| E3 | backend | Resultado y matricular desde la admisión (con la copia de los datos movidos) |
| E4 | frontend | Página de admisiones: lista, nuevo aspirante, entrevista y resultado; acceso desde la preparación del año |
| E5 | frontend | Matricular desde una admisión aprobada (ficha con los datos ya puestos); quitar "Crear estudiante en 2027" de Estudiantes y de "Continuar la preparación" |
| E6 | frontend | Formulario del estudiante sin lo que pasó a la entrevista; "Datos de admisión" de solo lectura en la ficha |
| E7 | backend | Bloquear el alta directa en el año en preparación |

Orden de subida a producción: E1 (migración aplicada) → E2 y E3 (backend
Live) → E4 a E6 (frontend) → E7 (backend). **E7 va al final a propósito:** si
el bloqueo se subiera antes que el frontend nuevo, el botón de siempre "Crear
estudiante en 2027" fallaría en producción.

## Pruebas

- Caracterización antes de tocar: el alta directa en preparación y el
  formulario del estudiante (cuerpos y respuestas de hoy).
- Migración: que el esquema base la declare (`tests/test_esquema_base.py`) y
  que los `CHECK` rechacen lo que deben.
- Rutas: admin solo, año en `preparacion` (cerrado o activo → `409`),
  autorización obligatoria, motivo obligatorio en `no_aprobado`, no se puede
  matricular un pendiente ni un no aprobado, ni dos veces, no se puede editar
  ni borrar una matriculada, la copia de los datos movidos, todo o nada al
  matricular.
- Nunca reportar una prueba como pasada si no se corrió.

## Fuera de alcance

- Estudiantes que llegan a mitad del año activo (ver preguntas abiertas).
- Prueba diagnóstica, cobro de la inscripción y lista de espera.
- Formato impreso de la entrevista para firmar (posible después, con
  `DocumentoImprimible`).
- Borrar columnas de `estudiantes`: solo con permiso explícito.

## Preguntas abiertas

- **Antes de E1:** ¿el usuario confirma el reparto de campos de la tabla
  (decisión 6) y las decisiones 7, 8 y 9?
- Antes de E4: ¿quién entrevista se escribe a mano (propuesta) o se elige de
  los usuarios del sistema?
- Antes de E3: un aspirante que **ya fue estudiante** del colegio (se retiró y
  vuelve) ya existe en `estudiantes` con su documento. ¿Se le hace entrevista
  y, si se aprueba, se matricula el estudiante que ya existe (propuesta), o se
  deja fuera de este módulo?
- Más adelante: ¿los estudiantes nuevos que llegan a mitad del año activo
  también pasan por entrevista? Por ahora no: el módulo vive en la
  preparación del año.
- Más adelante: ¿se consultan las admisiones de años pasados (incluidas las no
  aprobadas)? Quedan guardadas; no hay pantalla para eso en este diseño.

## Entrega para el siguiente chat

- Estado al 2026-10-12: **diseño y documentación (E0)**. No hay código de
  esta funcionalidad. Al empezar, los dos repos estaban en `main` y limpios
  (backend `2295928`, frontend `8319356`). Verificación del paso documental:
  `scripts/verify.py` 2279 pruebas, Ruff y `pip check` limpios (con una
  `DATABASE_URL` ficticia); `pnpm run check:deploy` 2409 pruebas, lint y
  build; `git diff --check` limpio en los dos repos.
- Siguiente acción exacta: el usuario confirma el reparto de campos y las
  decisiones 7 a 9 (ver "Preguntas abiertas"). Con eso, y su autorización
  explícita, empieza E1 (la migración). La migración se prueba en una rama de
  Neon; el asistente no se conecta a ninguna base.
- Prompt para retomar: `docs/funcionalidades/PROMPT_CONTINUACION_ENTREVISTA_ADMISION.md`.
