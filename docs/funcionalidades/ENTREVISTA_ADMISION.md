# Funcionalidad: Entrevista de admisión — Backend

## Control

- Estado: **E1 a E6 en producción (2026-10-14, informado por el usuario).
  E7 en GitHub** (`24a9a3c`, visto con `git fetch` el 2026-10-14; que Render
  lo tenga **Live** no se ve desde el repo). Con el E7 quedó completo el
  plan original. **Ampliación pedida por el usuario el 2026-10-14: las
  preguntas del anexo del colegio** (salud, familia, inclusión,
  comportamiento…) como casillas para chulear. Paso E8 (diseño, solo
  documentos) terminado el 2026-10-14; ver "Preguntas del anexo (pasos E8 a
  E12)". **Paso E9 (la migración) terminado el 2026-10-14**: probado en una
  rama de Neon y aplicado en producción por el usuario (ver "Avance del paso
  E9"). Sigue el E10.
  Pantallas en `frontend-react/docs/funcionalidades/ENTREVISTA_ADMISION.md`.
  Decisiones del usuario del 2026-10-13: reparto de campos y decisiones 7 a
  9, quien entrevista a mano (10) y el exalumno que vuelve usa su mismo
  registro (11). Del 2026-10-14: decisiones 12 a 16.
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
- Última actualización: 2026-10-14.

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

Propuestas del asistente, **confirmadas por el usuario el 2026-10-13**:

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

Decidida por el usuario el 2026-10-13 (la pregunta estaba para antes de E4,
pero cambia la tabla de E1):

10. **Quien entrevista se escribe a mano** (`entrevistador`, texto), no se
    elige de los usuarios del sistema. Así sirve aunque quien entrevista
    (psicoorientación, rectoría) no tenga usuario.

Decidida por el usuario el 2026-10-13, al autorizar el E3:

11. **El exalumno que vuelve usa su mismo registro.** Se le hace la
    entrevista igual; al matricularlo, si el documento de la ficha ya es de
    un estudiante, se actualiza esa ficha, queda `activo`, se le crea la
    matrícula del año en preparación y conserva su historial (notas, pagos,
    boletines). Motivo: hoy un exalumno sin matrícula en el año activo no
    tiene ninguna forma de entrar al año siguiente (la promoción no lo
    muestra y el alta directa falla por el documento repetido).

Decididas por el usuario el 2026-10-14, al pedir las preguntas del anexo del
colegio (detalle en "Preguntas del anexo (pasos E8 a E12)"):

12. **Las preguntas del anexo se agregan a la entrevista**, con casillas
    para chulear donde el papel tiene cuadritos. Lo que ya existe (en la
    entrevista o en la ficha) no se repite.
13. **Todo queda en la entrevista, también salud e inclusión.** Después de
    matricular se consulta en la ficha, de solo lectura, con "Datos de
    admisión". Aceptado lo que cuesta: esas respuestas no se actualizan
    después de matricular y los estudiantes de antes no las tienen. Pasarlas
    a la ficha sería un cambio aparte.
14. **La ayuda de "No aprobado" se amplía**: además de religión, origen o
    composición de la familia, dice que un diagnóstico, una discapacidad, la
    salud o la situación familiar tampoco pueden ser el motivo (Decreto 1421
    de 2017, educación inclusiva; Ley 1581 de 2012, datos sensibles).
15. La pregunta que sale cortada en el anexo queda como **"¿Hace rabietas o
    muestra irrespeto en lugares públicos?"** (Sí / No).
16. **Estado civil de los padres y religión no se agregan**, aunque estén en
    el anexo: lo impide la regla de no discriminación de esta funcionalidad
    (T-510 de 1994). Solo entrarían si el usuario cambia esa regla a
    propósito.

Propuestas del asistente que el usuario aceptó al autorizar el E8 (no las
objetó y pidió seguir con ellas): las respuestas van en **una sola columna**
(`cuestionario`, un bloque JSON) en lugar de 55 columnas, y **la lista de
preguntas vive solo en el backend**, que la entrega al frontend para que arme
el formulario.

## Qué va en cada formulario (decisión 6, confirmada)

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
| **Preguntas del anexo** (55: familia, vivienda, nacimiento, alimentación, salud, inclusión, lenguaje, comportamiento, juego, escolar, opinión) | **Entrevista** (pasos E8 a E11) | Decisiones 12 y 13; se ven en la ficha de solo lectura |

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
por año). El SQL definitivo está en `migrations/20261013_admisiones.sql`;
este bloque es igual. Frente al diseño del E0 solo cambiaron nombres: las
claves foráneas siguen el patrón de la base (`admisiones_..._fkey`, como
`matriculas_curso_anio_lectivo_fkey`) y la regla del enlace único se llama
`admisiones_estudiante_id_key`.

```sql
CREATE TABLE IF NOT EXISTS admisiones (
    id SERIAL PRIMARY KEY,
    anio_lectivo_id INTEGER NOT NULL,
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
    estudiante_id INTEGER,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT admisiones_anio_lectivo_fkey
        FOREIGN KEY (anio_lectivo_id) REFERENCES anios_lectivos (id),
    CONSTRAINT admisiones_curso_anio_lectivo_fkey
        FOREIGN KEY (curso_id, anio_lectivo_id) REFERENCES cursos (id, anio_lectivo_id),
    CONSTRAINT admisiones_estudiante_id_key UNIQUE (estudiante_id),
    CONSTRAINT admisiones_estudiante_fkey
        FOREIGN KEY (estudiante_id) REFERENCES estudiantes (id),
    CONSTRAINT chk_admisiones_resultado
        CHECK (resultado IN ('pendiente', 'aprobado', 'no_aprobado')),
    CONSTRAINT chk_admisiones_autoriza CHECK (autoriza_datos),
    CONSTRAINT chk_admisiones_motivo_no_aprobado
        CHECK (resultado <> 'no_aprobado' OR NULLIF(TRIM(motivo_resultado), '') IS NOT NULL),
    CONSTRAINT chk_admisiones_matricula_aprobada
        CHECK (estudiante_id IS NULL OR resultado = 'aprobado')
);
CREATE INDEX IF NOT EXISTS idx_admisiones_anio
ON admisiones (anio_lectivo_id, resultado);

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
- Un documento vacío (`''`) sí contaría como repetido en el índice único;
  por eso, en E2, la API debe guardar un documento vacío como `NULL`.
- Nada se borra en cascada. Hoy no hay ninguna ruta que borre años, cursos ni
  estudiantes (revisado el 2026-10-13), así que las referencias sin cascada no
  chocan con nada existente; `matriculas` apunta igual a `estudiantes`.
- No toca datos existentes. Se prueba en una rama de Neon, se regenera el
  esquema base desde allí y el usuario la aplica en los tenants
  (`docs/MIGRACIONES.md`).

## Rutas (pasos E2 y E3)

Todas solo para admin. Las que escriben exigen que el año de la admisión esté
en `preparacion` (`409` con mensaje si no). Las del E2 y el E3 están hechas;
su contrato completo (cuerpos, respuestas y errores) está en
`docs/API_ENDPOINTS.md`, sección "Admisiones". La del E7 sigue siendo
propuesta.

| Ruta | Qué hace |
|---|---|
| `GET /anios-lectivos/{id}/admisiones?resultado=` | Lista las admisiones del año (opcional, por resultado), con conteos |
| `POST /anios-lectivos/{id}/admisiones` | Registra un aspirante. Exige nombre, apellido y la autorización con quién autoriza. Queda `pendiente` |
| `GET /admisiones/{admision_id}` | Una admisión completa |
| `PUT /admisiones/{admision_id}` | Edita datos del aspirante y de la entrevista. No cambia el resultado. `409` si ya está matriculada |
| `PUT /admisiones/{admision_id}/resultado` | `{ resultado, motivo_resultado }`. `no_aprobado` exige motivo. `409` si ya está matriculada |
| `DELETE /admisiones/{admision_id}` | Borra una admisión no matriculada (decisión 9) |
| `POST /admisiones/{admision_id}/matricular` | Cuerpo: la ficha del estudiante (como `POST /anios-lectivos/{id}/estudiantes`). Solo si está `aprobado` y sin estudiante. En una transacción: crea el estudiante (o usa el del exalumno, decisión 11) y su matrícula en el año de la admisión (`matricular_aspirante_en_preparacion`, que reutiliza lo del alta directa), copia los datos movidos a sus columnas y enlaza `estudiante_id` |
| `POST /anios-lectivos/{id}/estudiantes` (existente) | Paso E7 (hecho): con el año en preparación responde `409` "Un estudiante nuevo en 2027 se matricula desde su entrevista aprobada (Admisiones)." y no escribe nada |

## Preguntas del anexo (pasos E8 a E12)

Pedido del usuario el 2026-10-14: agregar a la entrevista las preguntas del
anexo que el colegio usa en papel, con "cuadritos para chulear" (casillas)
donde el papel los tiene, sin repetir lo que ya existe. Diseño escrito en el
E8; nada de esto tiene código todavía.

### Tipos de pregunta

| Tipo (nombre interno) | Cómo se ve | Qué se guarda |
|---|---|---|
| Sí / No (`si_no`) | Dos casillas; al chulear una se borra la otra | `{"respuesta": "si"}` |
| Sí / No con detalle (`si_no` con `detalle`) | Igual, y al chulear la respuesta que lo pide aparece un cuadro para escribir | `{"respuesta": "si", "detalle": "texto"}` |
| Una opción (`una`) | Casillas, pero solo se puede chulear una; "Otro" abre un cuadro | `{"opcion": "casa"}` o `{"opcion": "otro", "otro": "texto"}` |
| Varias (`varias`) | Se chulean todas las que apliquen; "Otro" abre un cuadro; "Ninguno" borra las demás | `{"marcadas": ["desayuno", "cena"], "otro": "texto"}` |
| Número (`numero`) | Cuadro solo para números enteros, con mínimo y máximo | `3` |
| Texto (`texto`, `texto_largo`) | Cuadro corto (150 caracteres) o grande (1000) | `"texto"` |

- **Sin responder = la pregunta no está en el bloque.** Ninguna es
  obligatoria, como el resto de la entrevista: el papel tampoco obliga.
- "Ninguno" o "Ninguna" (en las preguntas 5 y 21) existe para distinguir
  "la familia dijo que no" de "no se preguntó".
- Límites: detalle y "otro", 250 caracteres; texto corto, 150; texto
  largo, 1000.

### La lista de preguntas

Los textos son los del anexo, con la ortografía corregida. La clave es el
nombre interno de cada pregunta: **nunca se reutiliza ni cambia de
significado**. Si un año se quita una pregunta, se marca como retirada (deja
de preguntarse, pero sus respuestas viejas se siguen mostrando).

**1. Datos personales** (`datos_personales`)

| # | Pregunta | Cómo se responde | Clave |
|---|---|---|---|
| 1 | ¿Cómo lo llaman en casa? | Texto corto | `como_lo_llaman` |

**2. Familia** (`familia`)

| # | Pregunta | Cómo se responde | Clave |
|---|---|---|---|
| 2 | Número de hermanos | Número, 0 a 20 | `numero_hermanos` |
| 3 | Lugar que ocupa entre los hermanos (1 = el mayor) | Número, 1 a 21 | `lugar_entre_hermanos` |
| 4 | ¿En casa quiénes trabajan? | Texto corto | `quienes_trabajan` |
| 5 | En la familia, ¿hay algún caso de…? | Varias: Alcoholismo, Drogadicción, Violencia, Abuso, Ninguno, Otro (¿cuál?) | `situaciones_familia` |
| 6 | ¿Cómo solucionan sus conflictos familiares? | Texto largo | `solucion_conflictos` |

**3. Vivienda** (`vivienda`)

| # | Pregunta | Cómo se responde | Clave |
|---|---|---|---|
| 7 | Tipo de vivienda | Una: Casa, Apartamento, Compartida, Otro (¿cuál?) | `tipo_vivienda` |
| 8 | ¿Pasa el niño(a) algún tiempo solo? | Sí / No | `pasa_tiempo_solo` |
| 9 | ¿Con quién queda el niño(a) cuando los padres trabajan? | Varias: Empleada, Hermanos, Familiares, Otro (¿quién?) | `con_quien_queda` |

**4. Nacimiento** (`nacimiento`)

| # | Pregunta | Cómo se responde | Clave |
|---|---|---|---|
| 10 | ¿El proceso de gestación fue normal? | Sí / No; con "No": ¿Qué pasó? | `gestacion_normal` |
| 11 | ¿El parto fue normal? | Sí / No; con "No": ¿Qué pasó? | `parto_normal` |
| 12 | ¿Nació a término completo? | Sí / No; con "No": ¿Qué pasó? | `nacio_a_termino` |
| 13 | ¿Tuvo alguna dificultad al nacer? | Sí / No; con "Sí": ¿Cuál? | `dificultad_al_nacer` |

**5. Alimentación** (`alimentacion`)

| # | Pregunta | Cómo se responde | Clave |
|---|---|---|---|
| 14 | ¿Cuáles de las cuatro comidas del día hace? | Varias: Desayuno, Almuerzo, Merienda, Cena | `comidas_del_dia` |
| 15 | Alimentos preferidos | Texto corto | `alimentos_preferidos` |
| 16 | Alimentos prohibidos por el médico | Texto corto | `alimentos_prohibidos` |

**6. Control de esfínteres** (`esfinteres`)

| # | Pregunta | Cómo se responde | Clave |
|---|---|---|---|
| 17 | ¿A qué edad controló esfínteres? | Texto corto (por ejemplo, "2 años y medio") | `edad_control_esfinteres` |
| 18 | ¿Usa pañal desechable? | Sí / No | `usa_panal` |

**7. Salud** (`salud`)

| # | Pregunta | Cómo se responde | Clave |
|---|---|---|---|
| 19 | ¿Tiene alguna dificultad motora? | Sí / No; con "Sí": ¿Cuál? | `dificultad_motora` |
| 20 | ¿Sufrió algún accidente, convulsiones o enfermedades? | Sí / No; con "Sí": ¿Cuál? | `accidentes_enfermedades` |
| 21 | Enfermedades que padeció | Varias: Hepatitis, Paperas, Asma, Varicela, Ninguna, Otra (¿cuál?) | `enfermedades_padecidas` |
| 22 | ¿Qué lado predomina más? | Una: Izquierdo, Derecho, Ambidiestro | `lateralidad` |
| 23 | ¿Le tiene miedo a algo? | Sí / No; con "Sí": ¿A qué? | `miedos` |

**8. Inclusión y necesidades educativas** (`inclusion`)

| # | Pregunta | Cómo se responde | Clave |
|---|---|---|---|
| 24 | ¿El estudiante presenta actualmente algún diagnóstico médico, psicológico, neuropsicológico o condición que debamos conocer para acompañar adecuadamente su proceso escolar? | Sí / No; con "Sí": ¿Cuál? | `diagnostico` |
| 25 | ¿El estudiante ha recibido o recibe actualmente algún tipo de seguimiento o acompañamiento profesional? | Sí / No | `seguimiento_profesional` |
| 26 | En caso afirmativo, indique cuál | Varias: Psicología, Neuropsicología, Fonoaudiología, Terapia ocupacional, Fisioterapia, Psiquiatría, Otro (¿cuál?). **Solo aparece y solo se guarda si la 25 es "Sí"** | `profesionales` |
| 27 | ¿Actualmente cuenta con recomendaciones o indicaciones de profesionales para favorecer su desempeño y bienestar en el entorno escolar? | Sí / No; con "Sí": ¿Cuáles? | `recomendaciones_profesionales` |
| 28 | ¿El estudiante ha contado anteriormente con algún tipo de apoyo o ajuste en el ámbito escolar? | Sí / No; con "Sí": Describa brevemente | `apoyos_anteriores` |
| 29 | ¿Existe alguna situación, comportamiento, dificultad o necesidad particular que consideren importante que el colegio conozca para brindar un adecuado acompañamiento al estudiante? | Texto largo | `situacion_particular` |
| 30 | ¿El estudiante presenta alguna dificultad relacionada con el aprendizaje, comunicación, lenguaje, atención, comportamiento, interacción social, autonomía o manejo de emociones? | Sí / No; con "Sí": ¿Cuál(es)? | `dificultades` |
| 31 | ¿Cuenta actualmente con informes, valoraciones o recomendaciones de profesionales que puedan ser compartidos con la institución para orientar su proceso de acompañamiento? | Sí / No | `informes_profesionales` |
| 32 | ¿Hay alguna recomendación especial que la familia considere importante para favorecer la adaptación, participación y aprendizaje del estudiante en el colegio? | Texto largo | `recomendacion_familia` |

**9. Lenguaje** (`lenguaje`)

| # | Pregunta | Cómo se responde | Clave |
|---|---|---|---|
| 33 | ¿Su pronunciación es clara? | Sí / No | `pronunciacion_clara` |
| 34 | ¿Su vocabulario es amplio? | Sí / No | `vocabulario_amplio` |
| 35 | Cuando se equivoca al hablar, ¿es corregido? | Sí / No | `corregido_al_hablar` |
| 36 | ¿Comunica lo que siente? | Sí / No | `comunica_lo_que_siente` |

**10. Comportamiento** (`comportamiento`)

| # | Pregunta | Cómo se responde | Clave |
|---|---|---|---|
| 37 | ¿Manifiesta rabietas? | Sí / No | `rabietas` |
| 38 | ¿Rompe juguetes? | Sí / No | `rompe_juguetes` |
| 39 | ¿Cómo lo corrigen cuando presenta ese tipo de comportamiento? | Texto largo | `como_lo_corrigen` |
| 40 | ¿Pega sin causa? | Sí / No | `pega_sin_causa` |
| 41 | ¿A quién obedece más? | Texto corto | `a_quien_obedece` |
| 42 | ¿Le pega a los padres o mayores? | Sí / No | `pega_a_mayores` |
| 43 | ¿Hace rabietas o muestra irrespeto en lugares públicos? (decisión 15) | Sí / No | `irrespeto_lugares_publicos` |
| 44 | ¿Cuántas horas diarias usa el celular? | Número, 0 a 24 | `horas_celular` |
| 45 | ¿Usa el celular para comer? | Sí / No | `celular_para_comer` |
| 46 | ¿Muestra actitudes agresivas cuando le quitan el celular? | Sí / No | `agresivo_sin_celular` |

**11. Juego y vida social** (`juego_vida_social`)

| # | Pregunta | Cómo se responde | Clave |
|---|---|---|---|
| 47 | ¿Juega fuera de casa? | Sí / No | `juega_fuera_de_casa` |
| 48 | ¿Comparte con dificultad sus juguetes? | Sí / No | `comparte_con_dificultad` |
| 49 | ¿Tiene alguna mascota? | Sí / No; con "Sí": ¿Cuál? | `mascota` |
| 50 | ¿Se relaciona fácilmente con los demás? | Sí / No | `se_relaciona_facilmente` |

**12. Escolar** (`escolar`)

| # | Pregunta | Cómo se responde | Clave |
|---|---|---|---|
| 51 | ¿Cómo reaccionaría frente a situaciones escolares de su hijo(a)? (golpes, mordidas, etc.) | Texto largo | `reaccion_situaciones_escolares` |
| 52 | ¿Está dispuesto a dejar que la escuela y las docentes realicen un trabajo integral en su hijo(a)? | Sí / No | `acepta_trabajo_integral` |
| 53 | ¿Estuvieron ambos de acuerdo para colocar a su hijo(a) en esta escuela? | Una: Sí, No, No aplica | `ambos_de_acuerdo` |
| 54 | ¿Están en capacidad de sufragar los gastos de una escuela privada? | Sí / No | `capacidad_de_pago` |

**13. Opinión de la familia** (`opinion`)

| # | Pregunta | Cómo se responde | Clave |
|---|---|---|---|
| 55 | ¿Cómo cree usted que es nuestro edificio escolar y sus dependencias? | Una: Muy bueno, Regular, Pésimo | `opinion_edificio` |

Lo que el asistente agregó al pasar el papel a casillas (para que el usuario
lo revise antes del E10): "Ninguno" en la 5 y "Ninguna" en la 21; los cuadros
"¿Qué pasó?" de la 10 a la 12 y "¿Cuál?" de la 19 y la 49 (el papel tiene una
línea para escribir o solo casillas); y "No aplica" en la 53, porque una
familia de un solo padre o madre no puede responder "ambos".

### Lo que no se agrega (ya existe o no se puede)

| Del anexo | Por qué no |
|---|---|
| Nombre y apellido | Ya está en el aspirante |
| Ocupación de los padres | Ya está en la entrevista (`ocupacion_padre`, `ocupacion_madre`) |
| ¿Quiénes viven en la casa?, ¿con quién vive si los padres están separados?, integrantes de la familia | Ya está: "Con quién vive el aspirante" (`vive_con`) |
| ¿Cuál fue el motivo de su elección? | Ya está: "Por qué eligen el colegio y qué esperan" (`expectativas`) |
| Fecha de la entrevista | Ya está (`fecha_entrevista`) |
| Firma de la psicoorientadora | Ya está "Quién entrevistó" (`entrevistador`); la firma en papel sería el E12 |
| Enfermedad relacionada con la alimentación y la casilla "Alergias" | Ya está en la ficha: "Datos médicos / Alergias" (`estudiantes.datos_medicos`) |
| "En casa lo llaman" (el anexo lo tiene dos veces) | Va una sola vez (pregunta 1) |
| Estado civil de los padres; ¿qué religión practica la familia? | Decisión 16: regla de no discriminación |

### Cómo se guarda (paso E9)

Una columna nueva en `admisiones`, con las respuestas como un bloque (JSON).
Así no hacen falta 55 columnas, y si el colegio cambia el anexo otro año se
cambia la lista en el código, sin otra migración en todos los colegios. La
base ya guarda bloques así en la configuración de impresión
(`configuracion_extra`, `config_json`). Lo que se pierde, buscar por una
pregunta suelta en SQL, no se necesita.

Borrador (se ajusta a `docs/MIGRACIONES.md` en el E9):

```sql
ALTER TABLE admisiones
    ADD COLUMN IF NOT EXISTS cuestionario JSONB NOT NULL DEFAULT '{}'::jsonb;

-- PostgreSQL no ofrece ADD CONSTRAINT IF NOT EXISTS (mismo patrón que
-- 20261008_anios_lectivos_activacion.sql).
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'chk_admisiones_cuestionario_objeto'
          AND conrelid = 'admisiones'::regclass
    ) THEN
        ALTER TABLE admisiones
            ADD CONSTRAINT chk_admisiones_cuestionario_objeto
            CHECK (jsonb_typeof(cuestionario) = 'object');
    END IF;
END
$$;
```

- Las admisiones que ya existen quedan con el bloque vacío (`{}`): nada que
  rellenar. Agregar una columna con un valor fijo por defecto no reescribe la
  tabla.
- La base solo exige que sea un bloque; qué preguntas y qué respuestas son
  válidas lo revisa el backend (E10).

### Rutas (paso E10)

- **`GET /admisiones/cuestionario`** (nueva, solo admin): la lista de
  secciones y preguntas, con su tipo, opciones, detalle, límites y de qué
  pregunta dependen. El frontend la pide una vez al abrir Admisiones y arma
  el formulario con ella. Se declara **antes** de `/admisiones/{admision_id}`,
  o FastAPI intentaría leer "cuestionario" como un número.
- **`GET /admisiones/{admision_id}`**: devuelve además `cuestionario`.
- **`PUT /admisiones/{admision_id}`**: acepta `cuestionario`. **Excepción a
  propósito al "reemplazo completo"**: si `cuestionario` no llega, se deja
  como estaba. Si llega, reemplaza el bloque entero. Motivo: una pestaña
  abierta con el formulario de antes no trae el bloque y, con la regla de
  siempre, borraría las respuestas al guardar.
- **Lectura desde la ficha del estudiante** (nueva, solo admin; nombre a
  definir en el E10, por ejemplo `GET /estudiantes/{id}/admision`): las
  respuestas de la admisión enlazada al estudiante, para "Datos de admisión"
  (decisión 13). Un estudiante sin admisión responde vacío, no un error.
- Revisión de las respuestas (en el backend, con mensajes en español, `422`):
  solo preguntas de la lista; cada respuesta con la forma de su tipo; opciones
  que existen; números dentro de su rango; textos dentro de su límite;
  "detalle" solo con la respuesta que lo pide y "otro" solo si se chuleó
  "Otro"; "Ninguno" no se combina con otras; la 26 solo si la 25 es "Sí". Un
  texto vacío se quita del bloque, como los demás campos de la entrevista.
- No cambia: matricular (el bloque no se copia a `estudiantes`, decisión 13),
  el resultado, borrar, la lista y los conteos.

### Pantallas (paso E11)

Detalle en el documento del frontend: formulario por secciones que se abren
y se cierran, casillas para chulear, ayuda ampliada de "No aprobado"
(decisión 14) y respuestas en "Datos de admisión" de la ficha.

## Plan por pasos (uno a la vez, con el visto bueno del usuario)

| Paso | Repo | Qué |
|---|---|---|
| E0 | ambos | Este diseño. **Hecho el 2026-10-12** |
| E1 | backend | Migración `admisiones` y esquema base (rama de Neon; la aplica el usuario). **Hecho el 2026-10-13** (`4db1f15`, aplicada en producción) |
| E2 | backend | Registrar, listar, ver, editar y borrar admisiones; guardia del año; autorización obligatoria. **Hecho el 2026-10-13** (`ee8aba2`); en producción el 2026-10-14 |
| E3 | backend | Resultado y matricular desde la admisión (con la copia de los datos movidos). **Hecho el 2026-10-13** (`d099c29`); en producción el 2026-10-14 |
| E4 | frontend | Página de admisiones: lista, nuevo aspirante, entrevista y resultado; acceso desde la preparación del año. **Hecho el 2026-10-13** (frontend `22b3dcf`); en producción el 2026-10-14 |
| E5 | frontend | Matricular desde una admisión aprobada (ficha con los datos ya puestos); quitar "Crear estudiante en 2027" de Estudiantes y de "Continuar la preparación". **Hecho el 2026-10-13** (frontend `ae5240a`); en producción el 2026-10-14 |
| E6 | frontend | Formulario del estudiante sin lo que pasó a la entrevista; "Datos de admisión" de solo lectura en la ficha. **Hecho el 2026-10-13** (frontend `f50ef7b`; se piden con un botón, solo si se usan); en producción el 2026-10-14 |
| E7 | backend | Bloquear el alta directa en el año en preparación. **Hecho el 2026-10-14** (`24a9a3c`, en GitHub) |
| E8 | ambos | Diseño de las preguntas del anexo (solo documentos). **Hecho el 2026-10-14** |
| E9 | backend | Migración: columna `cuestionario` en `admisiones` y esquema base (rama de Neon; la aplica el usuario). **Hecho el 2026-10-14** (`9547721` y `3728dcb`); probada en una rama de Neon y aplicada en producción por el usuario |
| E10 | backend | La lista de preguntas, la revisión de respuestas y las rutas (`GET /admisiones/cuestionario`, `cuestionario` en ver y editar, lectura desde la ficha) |
| E11 | frontend | Formulario con secciones y casillas, ayuda ampliada de "No aprobado" y respuestas en "Datos de admisión" de la ficha |
| E12 | frontend | **Opcional, solo si el usuario lo pide:** imprimir la entrevista con las firmas (`DocumentoImprimible`) |

Orden de subida a producción: E1 (migración aplicada) → E2 y E3 (backend
Live) → E4 a E6 (frontend) → E7 (backend). **E7 va al final a propósito:** si
el bloqueo se subiera antes que el frontend nuevo, el botón de siempre "Crear
estudiante en 2027" fallaría en producción.

Para las preguntas del anexo: E9 (push primero y después la migración
aplicada, como el E1) → E10 (backend **Live**) → E11 (frontend). El E11 va
después porque pide rutas que antes no existen. El E10 no rompe el
formulario de hoy: si `cuestionario` no llega, nada cambia.

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
  `DocumentoImprimible`; quedó anotado como paso E12, opcional).
- Pasar las respuestas de salud e inclusión a la ficha del estudiante, para
  actualizarlas o tenerlas en estudiantes sin admisión (decisión 13: cambio
  aparte, si se quiere).
- Borrar columnas de `estudiantes`: solo con permiso explícito.

## Preguntas abiertas

- ~~Antes de E1: ¿el usuario confirma el reparto de campos de la tabla
  (decisión 6) y las decisiones 7, 8 y 9?~~ **Respondida el 2026-10-13: sí,
  las cuatro.**
- ~~Antes de E4: ¿quién entrevista se escribe a mano (propuesta) o se elige de
  los usuarios del sistema?~~ **Respondida el 2026-10-13, antes de E1 porque
  cambia la tabla: se escribe a mano** (decisión 10).
- ~~Antes de E3: un aspirante que **ya fue estudiante** del colegio (se retiró y
  vuelve) ya existe en `estudiantes` con su documento. ¿Se le hace entrevista
  y, si se aprueba, se matricula el estudiante que ya existe (propuesta), o se
  deja fuera de este módulo?~~ **Respondida el 2026-10-13: se usa el que ya
  existe** (decisión 11).
- Antes de la preparación de 2028 (encontrada en el E3): la tabla del E1 tiene
  `admisiones_estudiante_id_key UNIQUE (estudiante_id)`, es decir, **un
  estudiante solo puede enlazarse a una admisión en toda su vida**. Quien
  entre por admisión en 2027, se vaya y vuelva a entrar por admisión otro año
  chocaría; hoy responde `409` con un mensaje claro y no cambia nada. El
  arreglo es una migración nueva que cambie esa regla por una de un enlace
  por año (`UNIQUE (anio_lectivo_id, estudiante_id)`). No corre prisa: no
  puede pasar antes de preparar 2028.
- Más adelante: ¿los estudiantes nuevos que llegan a mitad del año activo
  también pasan por entrevista? Por ahora no: el módulo vive en la
  preparación del año.
- Más adelante: ¿se consultan las admisiones de años pasados (incluidas las no
  aprobadas)? Quedan guardadas; no hay pantalla para eso en este diseño.
- Más adelante, antes de activar 2027 (encontrada en el E2): según el
  contrato, borrar solo se puede con el año en `preparacion`. Cuando 2027 se
  active, los aspirantes no aprobados o que nunca se matricularon quedan
  guardados y ya **no se pueden borrar**, aunque la familia pida retirar sus
  datos (derecho de supresión de la Ley 1581, el motivo de la decisión 9).
  ¿Se permite borrar una admisión no matriculada de un año que ya no está en
  preparación, o se borran solas al activar el año? El E2 sigue el contrato
  (lo más estricto); aflojarlo después es quitar una comprobación.
- **Antes del E10 (la lista se escribe en código ahí):** el usuario revisa la
  lista de "Preguntas del anexo": los textos, cómo se responde cada una y lo
  que el asistente agregó al pasarla a casillas ("Ninguno", los cuadros de
  detalle y "No aprobado"). El E9 no depende de esta revisión: la columna es
  la misma con cualquier lista.

## Avance del paso E1 (2026-10-13)

- Al iniciar, los dos repos estaban en `main` y limpios: backend `7949de8`,
  frontend `f2dda8c`. El usuario confirmó el reparto de campos y las
  decisiones 7 a 9, decidió que quien entrevista se escribe a mano (decisión
  10) y autorizó explícitamente el paso E1.
- Pruebas primero: `tests/test_migracion_admisiones.py`, 15 pruebas sobre el
  texto del SQL; las 15 fallaron porque el archivo no existía. Comprueban
  cada columna; que los datos que se copian al matricular tengan el mismo
  tamaño que en `estudiantes` (leído del esquema base, para que la copia no
  se corte); que no haya columnas que puedan discriminar; la autorización
  obligatoria; los tres resultados; el motivo de "no aprobado"; el enlace
  único y solo de un aprobado; el curso del mismo año; que nada se borre en
  cascada; los dos índices; que sea reejecutable; y que no cambie datos ni
  tablas existentes.
- `migrations/20261013_admisiones.sql`: crea la tabla `admisiones`, sus
  reglas y sus dos índices. No toca ninguna tabla existente.
- Verificación local, con una `DATABASE_URL` ficticia: las 15 pruebas
  pasan; el bloque de migraciones y esquema base da 102 pasan y **1 falla
  esperada** (`test_esquema_base.py`: la base aún no declara la migración);
  `scripts/verify.py` → 2293 pasan y esa misma única falla, Ruff y
  `pip check` limpios; en el frontend (solo cambió su documento),
  `pnpm run check:deploy` → 2409 pruebas en 355 archivos, lint y build
  limpios; `git diff --check` limpio en los dos repos.
- La consulta de reglas de la lista de abajo y la migración se revisaron con
  `pglast` (el lector de SQL de PostgreSQL, instalado en una carpeta temporal
  fuera del proyecto): se leen bien, incluido el bloque `DO` y las 15 altas.
  Eso solo prueba que están bien escritas; que funcionen lo prueba la rama
  de Neon.
- No se ejecutó la migración, no se accedió a Neon ni a producción y no se
  regeneró ni editó a mano el esquema base. **El paso E1 todavía no está
  terminado.**
- Relación con una pregunta pendiente del año lectivo ("Quitar o cambiar la
  matrícula de 2027", al final de la fase 5 de `ANIO_LECTIVO.md`): si se
  hace, quitarle la matrícula a un estudiante que vino de una admisión deja
  la admisión enlazada a él. Tenerlo en cuenta al diseñarla.

**Lista de comprobación en una rama de Neon** (la hace el usuario; el
asistente no se conecta a Neon):

1. En console.neon.tech → Branches → **Create branch** desde `production`,
   con los datos actuales. Nombre sugerido: `prueba-admisiones`.
2. En la rama nueva → **Connect**: copiar la cadena de conexión **directa**
   (con "Connection pooling" apagado; el host no debe tener `-pooler`). No
   pegarla en el chat.
3. En una terminal de PowerShell, en la carpeta del backend. La variable
   solo vive en esa ventana y gana sobre el `.env`:

   ```powershell
   $env:DATABASE_URL = "<cadena directa de la rama>"
   ([uri]$env:DATABASE_URL).Host
   .\venv\Scripts\python.exe apply_migration.py migrations/20261013_admisiones.sql --dry-run
   .\venv\Scripts\python.exe apply_migration.py migrations/20261013_admisiones.sql
   .\venv\Scripts\python.exe apply_migration.py migrations/20261013_admisiones.sql --dry-run
   ```

   El host que se imprime debe ser el de la rama, **no**
   `ep-late-smoke-aip41j6x` (producción). Esperado: `PENDIENTE` → `OK` →
   `OMITIDA (ya aplicada)` en `tenant_colegio_1` y `tenant_2005`.
4. En la misma terminal, regenerar el esquema base desde la rama:

   ```powershell
   .\venv\Scripts\python.exe scripts\generar_esquema_base.py --schema tenant_colegio_1
   ```

   Esperado en el diff: la migración en la cabecera, la tabla `admisiones`
   con sus reglas, sus dos índices y sus tres claves foráneas, y nada más.
   Después, cerrar esa terminal.
5. En el SQL Editor de Neon, **con la rama de prueba elegida**, pegar todo
   esto junto y correrlo una vez. Intenta 15 altas en `tenant_colegio_1`;
   cada una se deshace al instante, así que no queda nada guardado. La
   columna `bien` debe salir `true` en las 15 filas:

   ```sql
   SET search_path TO tenant_colegio_1, public;

   CREATE TEMP TABLE prueba_admisiones (orden INT, caso TEXT, debe TEXT, obtuvo TEXT);

   DO $$
   DECLARE
       anio_id INTEGER := (SELECT id FROM anios_lectivos ORDER BY anio DESC LIMIT 1);
       estudiante INTEGER := (SELECT MIN(id) FROM estudiantes);
       curso_otro_anio INTEGER;
       fila RECORD;
       texto_sql TEXT;
   BEGIN
       SELECT MIN(id) INTO curso_otro_anio FROM cursos WHERE anio_lectivo_id <> anio_id;

       FOR fila IN
           SELECT * FROM (VALUES
               (1, 'Aspirante con lo mínimo', 'aceptar',
                $q$INSERT INTO admisiones (anio_lectivo_id, nombre, apellido, autoriza_datos, autoriza_nombre)
                   VALUES ({anio}, 'Prueba', 'Admision', TRUE, 'Acudiente')$q$),
               (2, 'Autorización en falso', 'chk_admisiones_autoriza',
                $q$INSERT INTO admisiones (anio_lectivo_id, nombre, apellido, autoriza_datos, autoriza_nombre)
                   VALUES ({anio}, 'Prueba', 'Admision', FALSE, 'Acudiente')$q$),
               (3, 'Autorización vacía', 'autoriza_datos',
                $q$INSERT INTO admisiones (anio_lectivo_id, nombre, apellido, autoriza_datos, autoriza_nombre)
                   VALUES ({anio}, 'Prueba', 'Admision', NULL, 'Acudiente')$q$),
               (4, 'Sin quién autoriza', 'autoriza_nombre',
                $q$INSERT INTO admisiones (anio_lectivo_id, nombre, apellido, autoriza_datos, autoriza_nombre)
                   VALUES ({anio}, 'Prueba', 'Admision', TRUE, NULL)$q$),
               (5, 'Resultado inventado', 'chk_admisiones_resultado',
                $q$INSERT INTO admisiones (anio_lectivo_id, nombre, apellido, autoriza_datos, autoriza_nombre, resultado)
                   VALUES ({anio}, 'Prueba', 'Admision', TRUE, 'Acudiente', 'tal_vez')$q$),
               (6, 'No aprobado sin motivo', 'chk_admisiones_motivo_no_aprobado',
                $q$INSERT INTO admisiones (anio_lectivo_id, nombre, apellido, autoriza_datos, autoriza_nombre, resultado)
                   VALUES ({anio}, 'Prueba', 'Admision', TRUE, 'Acudiente', 'no_aprobado')$q$),
               (7, 'No aprobado con motivo en blanco', 'chk_admisiones_motivo_no_aprobado',
                $q$INSERT INTO admisiones (anio_lectivo_id, nombre, apellido, autoriza_datos, autoriza_nombre, resultado, motivo_resultado)
                   VALUES ({anio}, 'Prueba', 'Admision', TRUE, 'Acudiente', 'no_aprobado', '   ')$q$),
               (8, 'No aprobado con motivo', 'aceptar',
                $q$INSERT INTO admisiones (anio_lectivo_id, nombre, apellido, autoriza_datos, autoriza_nombre, resultado, motivo_resultado)
                   VALUES ({anio}, 'Prueba', 'Admision', TRUE, 'Acudiente', 'no_aprobado', 'Motivo de prueba')$q$),
               (9, 'Pendiente enlazado a un estudiante', 'chk_admisiones_matricula_aprobada',
                $q$INSERT INTO admisiones (anio_lectivo_id, nombre, apellido, autoriza_datos, autoriza_nombre, estudiante_id)
                   VALUES ({anio}, 'Prueba', 'Admision', TRUE, 'Acudiente', {estudiante})$q$),
               (10, 'Aprobado enlazado a un estudiante', 'aceptar',
                $q$INSERT INTO admisiones (anio_lectivo_id, nombre, apellido, autoriza_datos, autoriza_nombre, resultado, estudiante_id)
                   VALUES ({anio}, 'Prueba', 'Admision', TRUE, 'Acudiente', 'aprobado', {estudiante})$q$),
               (11, 'Dos admisiones del mismo estudiante', 'admisiones_estudiante_id_key',
                $q$INSERT INTO admisiones (anio_lectivo_id, nombre, apellido, autoriza_datos, autoriza_nombre, resultado, estudiante_id)
                   VALUES ({anio}, 'Prueba', 'Uno', TRUE, 'Acudiente', 'aprobado', {estudiante}),
                          ({anio}, 'Prueba', 'Dos', TRUE, 'Acudiente', 'aprobado', {estudiante})$q$),
               (12, 'Mismo documento dos veces en el año', 'idx_admisiones_documento_por_anio',
                $q$INSERT INTO admisiones (anio_lectivo_id, nombre, apellido, autoriza_datos, autoriza_nombre, documento_identidad)
                   VALUES ({anio}, 'Prueba', 'Uno', TRUE, 'Acudiente', '0000000001'),
                          ({anio}, 'Prueba', 'Dos', TRUE, 'Acudiente', '0000000001')$q$),
               (13, 'Dos aspirantes sin documento', 'aceptar',
                $q$INSERT INTO admisiones (anio_lectivo_id, nombre, apellido, autoriza_datos, autoriza_nombre)
                   VALUES ({anio}, 'Prueba', 'Uno', TRUE, 'Acudiente'),
                          ({anio}, 'Prueba', 'Dos', TRUE, 'Acudiente')$q$),
               (14, 'Curso de otro año', 'admisiones_curso_anio_lectivo_fkey',
                $q$INSERT INTO admisiones (anio_lectivo_id, nombre, apellido, autoriza_datos, autoriza_nombre, curso_id)
                   VALUES ({anio}, 'Prueba', 'Admision', TRUE, 'Acudiente', {curso_otro_anio})$q$),
               (15, 'Año que no existe', 'admisiones_anio_lectivo_fkey',
                $q$INSERT INTO admisiones (anio_lectivo_id, nombre, apellido, autoriza_datos, autoriza_nombre)
                   VALUES (-1, 'Prueba', 'Admision', TRUE, 'Acudiente')$q$)
           ) AS c (orden, caso, debe, sentencia)
           ORDER BY orden
       LOOP
           IF (position('{estudiante}' IN fila.sentencia) > 0 AND estudiante IS NULL)
              OR (position('{curso_otro_anio}' IN fila.sentencia) > 0 AND curso_otro_anio IS NULL) THEN
               INSERT INTO prueba_admisiones
               VALUES (fila.orden, fila.caso, fila.debe, 'no se pudo probar: faltan datos en este colegio');
               CONTINUE;
           END IF;
           texto_sql := replace(replace(replace(fila.sentencia,
               '{anio}', anio_id::text),
               '{estudiante}', coalesce(estudiante::text, 'NULL')),
               '{curso_otro_anio}', coalesce(curso_otro_anio::text, 'NULL'));
           BEGIN
               EXECUTE texto_sql;
               RAISE EXCEPTION 'aceptada';
           EXCEPTION
               WHEN raise_exception THEN
                   INSERT INTO prueba_admisiones VALUES (fila.orden, fila.caso, fila.debe, 'aceptada');
               WHEN OTHERS THEN
                   INSERT INTO prueba_admisiones VALUES (fila.orden, fila.caso, fila.debe, SQLERRM);
           END;
       END LOOP;
   END
   $$;

   SELECT orden, caso, debe, obtuvo,
          CASE WHEN debe = 'aceptar' THEN obtuvo = 'aceptada'
               ELSE position(debe IN obtuvo) > 0 END AS bien
   FROM prueba_admisiones
   ORDER BY orden;
   ```

   Cómo funciona: cada alta corre en un bloque que, si la base la acepta, se
   deshace a propósito con `RAISE EXCEPTION 'aceptada'`; si la base la
   rechaza, también se deshace. Solo queda el resultado en una tabla
   temporal, que desaparece al cerrar la sesión. El caso 14 necesita dos
   años; `tenant_colegio_1` tiene 2026 y 2027 desde la prueba del usuario
   en el Colegio Demo (fase 6 del año lectivo). Si un caso dice "no se pudo
   probar", faltan datos en ese colegio, no es un error de la migración.
6. Contarle al asistente lo que salió en los puntos 3, 4 y 5, sin cadenas de
   conexión. Después se puede borrar la rama.

**Prueba en la rama de Neon, 2026-10-13** (rama `prueba-entrevista`, copia
de `production`; la hizo el usuario, el asistente no se conectó a Neon ni a
producción):

- `--dry-run`: `PENDIENTE` (informado por el usuario). Después el usuario
  informó que aplicó la migración en la rama.
- Esquema base regenerado desde `tenant_colegio_1` en la rama: 36 tablas, 1
  función y 1 disparador (antes 35). La revisión del diff confirmó solo lo
  esperado: cabecera con la fecha y 43 migraciones (antes 42), incluida
  `20261013_admisiones.sql`; la tabla `admisiones` con sus 33 columnas, las
  cuatro reglas `chk_admisiones_*`, la llave primaria y
  `admisiones_estudiante_id_key`; los dos índices; y las tres claves
  foráneas. La cabecera confirma que la migración quedó registrada en
  `tenant_colegio_1` de la rama.
- Consulta de reglas en el SQL Editor, sobre `tenant_colegio_1` de la rama:
  **las 15 filas con `bien = true`**. Se aceptaron el aspirante mínimo, el
  "no aprobado" con motivo, el aprobado enlazado a un estudiante y dos
  aspirantes sin documento. Se rechazaron, cada uno con la regla esperada:
  autorización en falso (`chk_admisiones_autoriza`), autorización vacía y sin
  quién autoriza (`NOT NULL`), resultado inventado
  (`chk_admisiones_resultado`), "no aprobado" sin motivo y con motivo en
  blanco (`chk_admisiones_motivo_no_aprobado`), pendiente enlazado
  (`chk_admisiones_matricula_aprobada`), dos admisiones del mismo estudiante
  (`admisiones_estudiante_id_key`), documento repetido en el año
  (`idx_admisiones_documento_por_anio`), curso de otro año
  (`admisiones_curso_anio_lectivo_fkey`) y año inexistente
  (`admisiones_anio_lectivo_fkey`). Ningún caso dijo "no se pudo probar":
  la rama tenía estudiantes y cursos de dos años.
- Verificación final, con una `DATABASE_URL` ficticia: 20 pruebas
  específicas pasan (las 15 de la migración y las 5 del esquema base);
  `scripts/verify.py` → **2294 pasan, 0 fallan**, Ruff y `pip check`
  limpios; `git diff --check` limpio.

**En producción, 2026-10-13** (lo hizo el usuario; el asistente no se conectó
a ninguna base):

- El usuario confirmó la migración, el esquema base, las pruebas y los
  documentos en el commit `4db1f15` (los 6 archivos juntos, revisado con
  `git show --stat`), lo subió junto con el del E0 (`7949de8`) y confirmó
  el despliegue en Render como **Live**. El commit no traía código de la
  app.
- Después, con `$env:DATABASE_URL` en el endpoint directo de producción, la
  simulación dio `PENDIENTE` (informado por el usuario), lo que descarta
  que la terminal apuntara a la rama de prueba, donde ya estaba aplicada. El
  usuario informó luego que la aplicó. La tabla se crea vacía; no se tocó
  ningún dato existente.
- A partir de aquí el archivo `20261013_admisiones.sql` **no se puede
  editar**: el runner guarda su checksum. Cualquier cambio posterior va en
  una migración nueva.
- **Paso E1 terminado.**

## Avance del paso E2 (2026-10-13)

- Autorizado explícitamente por el usuario ("continúa el E2"). Al iniciar, los
  dos repos estaban en `main` y limpios, cada uno con un commit de
  documentos sin subir: backend `c57cbb9`, frontend `09e85a8`.
- Pruebas primero, 80 en tres archivos; fallaron las tres al importar porque
  los módulos no existían:
  - `tests/test_admisiones_esquema.py`: campos en el orden de las columnas,
    obligatorios, autorización que no se puede quitar ni al editar, textos
    recortados y vacíos como `null`, cada texto cabe en su columna (leído de
    la migración) y uno más largo da `422`, y que ningún cuerpo cambie el
    resultado, el año ni el enlace al estudiante.
  - `tests/test_admisiones_controller.py`: las reglas con dobles de la base
    (año en preparación, curso activo del mismo año, documento repetido en el
    año, también cuando dos altas llegan a la vez, aviso si el documento es de
    un estudiante, matriculada de solo consulta, fila bloqueada al editar y
    borrar, todo o nada) y el SQL del repositorio.
  - `tests/test_admisiones_routes.py`: la aplicación real por ASGI. Solo admin
    y en el router (un profesor recibe `403` en las cinco), las rutas exactas
    del documento, registradas en la app, `201` al registrar, cada error con
    su código (`404`/`409`) y su mensaje, y que un cuerpo o filtro inválido dé
    `422` sin llegar al controlador.
- Código, con las capas del proyecto:
  - `app/schemas/admision.py`: `AdmisionCreate` (aspirante y autorización) y
    `AdmisionUpdate` (más la entrevista). Repite las reglas de la base para
    responder `422` y no `500`.
  - `app/repositories/admisiones_repository.py`: solo SQL.
  - `app/controllers/admisiones_controller.py`: las reglas y los mensajes.
  - `app/routes/admisiones.py`: router solo admin; traduce errores a `404` y
    `409`. Registrado en `app/main.py`.
- Decisiones de detalle (dentro del contrato, sin funciones nuevas):
  - Registrar recibe solo los datos del aspirante; la entrevista se escribe al
    editar, como en el flujo ("Registrar aspirante" → "Entrevista").
  - Editar reemplaza todo, como `PUT /estudiantes/{id}`.
  - Las respuestas traen `editable` (año en preparación y sin matricular)
    para que la pantalla oculte botones sin decidir la regla.
  - El aviso del documento sale en ver, registrar y editar, y no impide
    guardar (la pregunta del exalumno sigue abierta para el E3). Una
    matriculada no se avisa a sí misma.
  - La comprobación del curso usa `leer_curso_para_matricula` de
    `anios_lectivos_repository` (curso activo y su año), la misma del alta
    directa del paso 5.5.
- Ajustadas a propósito: las cinco guardias que enumeran todos los
  repositorios (`test_asistencia_caracterizacion.py`,
  `test_dashboard_caracterizacion.py`, `test_notas_caracterizacion.py`,
  `test_planilla_caracterizacion.py`, `test_ventas_caracterizacion.py`)
  reconocen `admisiones_repository`; la de asistencia también su total, de 19
  a 20. Están hechas para dispararse con cada repositorio nuevo.
- Verificación, con una `DATABASE_URL` ficticia: 80 pruebas nuevas pasan;
  `scripts/verify.py` → **2374 pasan, 0 fallan**, Ruff y `pip check`
  limpios; `git diff --check` limpio. Las 12 consultas del repositorio se
  revisaron con `pglast` (el lector de SQL de PostgreSQL, en una carpeta
  temporal fuera del proyecto): se leen bien. Que funcionen contra
  PostgreSQL no se ha probado todavía: es la primera vez que este SQL corre
  en una base real.
- Sin migración, sin frontend, sin acceso a bases reales.
- Encontrado en el E2 y anotado en "Preguntas abiertas": con el contrato
  actual, al activar 2027 ya no se podrán borrar los aspirantes que no se
  matricularon (derecho de supresión).

## Avance del paso E3 (2026-10-13)

- Autorizado explícitamente por el usuario ("continúa e3"). Antes de
  empezar respondió la pregunta del exalumno: se usa el que ya existe
  (decisión 11). Al iniciar, los dos repos estaban en `main` y limpios, sin
  subir: backend `ee8aba2` (el E2), frontend `d0b92d7`.
- Lo que se encontró antes de decidir (verificado en el código): un exalumno
  retirado durante el año activo todavía tiene su matrícula y aparece en la
  promoción; uno sin matrícula en el año activo no aparece en ningún lado, y
  el alta directa (`POST /anios-lectivos/{id}/estudiantes`) responde `500`
  por el documento repetido (`estudiantes_documento_identidad_key`; la ruta
  no traduce ese error). Al activar, quien sigue conserva su estado
  (`aplicar_marcas_de_salida`), así que un exalumno `retirado` matriculado en
  2027 seguiría `retirado` si nadie lo cambia: por eso queda `activo` al
  matricular.
- Pruebas primero, 52 nuevas; antes del código fallaban (las del controlador
  ni arrancaban porque el doble de `guardar_resultado` no tenía qué
  reemplazar). Antes del cambio pasaban las 19 del alta directa del paso 5.5
  (`test_anio_lectivo_matriculacion_preparacion.py`), que caracterizan lo que
  se iba a tocar.
  - `test_admisiones_esquema.py`: `no_aprobado` exige motivo no vacío,
    `aprobado` no, el motivo se recorta, un resultado inventado no vale.
  - `test_admisiones_controller.py`: poner el resultado con la fila
    bloqueada, volver a pendiente, no en una matriculada ni fuera de
    preparación, y su SQL (`decidido_en` y una matriculada intocable).
  - `test_admisiones_matricular.py` (nuevo): la matrícula de punta a punta
    con dobles de los repositorios. Aspirante nuevo (ficha, matrícula, copia
    y enlace en ese orden, una transacción, queda `activo`); exalumno que
    vuelve (su mismo registro, sin crear otro); quien estudia hoy va por la
    promoción; quien ya tiene matrícula en el año o está marcado como que no
    sigue no entra; solo un aprobado, una vez; año fuera de preparación;
    curso de otro año; cada choque de la base con su mensaje y todo
    deshecho; y el SQL nuevo (copia que no borra con vacíos, enlace solo de
    un aprobado sin estudiante, estudiante existente bloqueado con sus
    matrículas de los dos años).
  - `test_admisiones_routes.py`: las dos rutas nuevas (un profesor recibe
    `403`, `200` y `201`, `422` sin motivo o sin curso, y los errores nuevos
    con `409`).
- Código:
  - `app/schemas/admision.py`: `ResultadoAdmisionUpdate`.
  - `app/repositories/admisiones_repository.py`: `guardar_resultado`,
    `copiar_datos_a_estudiante` (las 8 columnas que pasaron a la entrevista;
    `COALESCE` para no borrar lo que ya había) y `enlazar_estudiante`.
  - `app/repositories/anios_lectivos_repository.py`:
    `leer_estudiante_para_reingreso`.
  - `app/controllers/anios_lectivos_controller.py`: lo que crea la ficha y la
    matrícula del alta directa pasó a `_crear_estudiante_en_preparacion`, sin
    cambiar lo que hace (sus 19 pruebas siguen pasando), y la nueva
    `matricular_aspirante_en_preparacion` lo reutiliza, o usa el registro del
    exalumno. Vive aquí porque es matrícula del año en preparación, con las
    mismas comprobaciones de año y curso.
  - `app/controllers/admisiones_controller.py`: `cambiar_resultado_controller`
    y `matricular_admision_controller`, con los choques de la base
    traducidos a mensajes.
  - `app/routes/admisiones.py`: `PUT /admisiones/{id}/resultado` y `POST
    /admisiones/{id}/matricular` (`201`).
- Decisiones de detalle (dentro del contrato):
  - Volver a "pendiente" se permite mientras no esté matriculada (el diseño
    dice que el resultado se puede cambiar); borra `decidido_en`.
  - La ficha manda en los datos del estudiante; lo que pasó a la entrevista
    lo pone la admisión (decisión 7), pero un dato vacío en la entrevista no
    borra el que ya había.
  - Para un exalumno, la ficha se reemplaza como en `PUT /estudiantes/{id}`:
    la pantalla del E5 tiene que llenarla con lo que el estudiante ya tiene,
    o se perderían datos como `condicion_diagnostico`.
  - Matricular no copia valores de pago especiales, como el alta directa.
- Verificación, con una `DATABASE_URL` ficticia: 151 pruebas de admisiones y
  del alta directa pasan; `scripts/verify.py` → **2426 pasan, 0 fallan**,
  Ruff y `pip check` limpios; `git diff --check` limpio. Las 4 consultas
  nuevas se revisaron con `pglast`: se leen bien. Como en el E2, este SQL
  todavía no ha corrido en un PostgreSQL de verdad.
- Sin migración, sin frontend, sin acceso a bases reales.
- Encontrado en el E3: la regla de un solo enlace por estudiante en toda su
  vida (anotada en "Preguntas abiertas", para antes de preparar 2028) y el
  `500` del alta directa con un documento repetido (no se toca: el E7 cierra
  esa ruta en el año en preparación).

## Avance del paso E7 (2026-10-14)

- Autorizado explícitamente por el usuario ("e7", después de aclarar que se
  refería a este paso y no a la fase 7 del año lectivo). Antes, el usuario
  informó que E1 a E6 estaban en producción: la condición del E7 (el
  frontend nuevo publicado) se cumple según él. Al iniciar, los dos repos en
  `main` y limpios, cada uno con un commit de documentos sin subir: backend
  `259f8d1`, frontend `05d35d8`.
- Pruebas primero, en `tests/test_anio_lectivo_matriculacion_preparacion.py`.
  La que fijaba el alta directa (creaba ficha y matrícula) se **reescribió a
  propósito** como prueba de `_crear_estudiante_en_preparacion`, que sigue
  viva para la matrícula desde una admisión: mismo orden, los 34 datos,
  solo la matrícula de preparación y el curso vigente sin tocar. Nuevas: el
  alta directa con el año en preparación responde con el mensaje y no
  escribe nada (sin ficha, matrícula ni sincronización, sin commit); con un
  año que no está en preparación, el mensaje de siempre; la ruta lo
  traduce a `409`. Antes del código fallaban las dos que dependían de él.
- Código: `AltaDirectaCerradaError` y `crear_estudiante_en_preparacion_controller`
  (valida el año como siempre y, si está en preparación, rechaza; ya no
  escribe) en `app/controllers/anios_lectivos_controller.py`; la ruta la
  traduce a `409` en `app/routes/anios_lectivos.py`. La ruta se conserva para
  que una pestaña vieja reciba un mensaje claro en lugar de un `404`.
- No cambia `POST /estudiantes` (alta en el año activo): un estudiante que
  llega a mitad del año activo se sigue creando desde Estudiantes. Con esto
  también desaparece el `500` del alta directa con un documento repetido
  (encontrado en el E3): la ruta ya no intenta crear.
- Verificación, con una `DATABASE_URL` ficticia: 80 pruebas de matrícula y
  admisiones pasan; `scripts/verify.py` → **2429 pasan, 0 fallan**, Ruff y
  `pip check` limpios; `git diff --check` limpio. Sin migración, sin
  acceso a bases reales.
- Pendiente de decisión del usuario: borrar del frontend
  `crearEstudianteEnPreparacion` (sin uso desde el E5). Recomendado; no se
  hizo sin su "sí".
- El usuario hizo el commit y el push: `24a9a3c`, en `origin/main` (visto con
  `git fetch` el 2026-10-14).

## Avance del paso E8 (2026-10-14)

- Pedido del usuario: agregar a la entrevista las preguntas del anexo del
  colegio (15 imágenes del formato en papel), con casillas para chulear y sin
  repetir lo que ya existe. Antes de diseñar se comparó cada pregunta con la
  tabla `admisiones` (`migrations/20261013_admisiones.sql`), el formulario de
  la entrevista (`FormularioEntrevistaView.jsx`) y la ficha del estudiante
  (`estudiantes` en el esquema base y `FormularioEstudianteAdmin.jsx`).
- El usuario respondió las tres preguntas que cambiaban la lista: todo en la
  entrevista (decisión 13), ampliar la ayuda de "No aprobado" (14) y el texto
  de la pregunta cortada (15). Estado civil y religión quedan fuera por la
  regla de la funcionalidad (16). Autorizó el E8 con "si".
- Hallado al diseñar: `PUT /admisiones/{id}` es un reemplazo completo
  (`AdmisionUpdate`, `actualizar_admision`): lo que no llega queda vacío. Por
  eso `cuestionario` es la excepción: si no llega, no se toca (ver "Rutas
  (paso E10)"). La ayuda de "No aprobado" ya existe desde el E4
  (`ResultadoAdmisionView.jsx`); el E11 solo la amplía.
- Escrito: decisiones 12 a 16, la sección "Preguntas del anexo (pasos E8 a
  E12)" (tipos, las 55 preguntas, lo que no se agrega, el borrador de la
  migración, las rutas), los pasos E8 a E12 en el plan, la pregunta abierta
  de revisar la lista antes del E10 y "Fuera de alcance". En el frontend, su
  documento con las pantallas del E11. Corregido el estado del E7 (ya en
  GitHub).
- Sin código, sin migración, sin acceso a bases. Verificación, aunque solo
  cambiaron documentos: `scripts/verify.py` con una `DATABASE_URL` ficticia →
  **2429 pasan, 0 fallan**, Ruff y `pip check` limpios; en el frontend,
  `pnpm run check:deploy` → **2524 pruebas en 364 archivos**, lint y build
  limpios; `git diff --check` limpio en los dos repos.
- El usuario hizo los commits del E8: backend `ff92f93`, frontend `df2e494`
  (sin subir al iniciar el E9).

## Avance del paso E9 (2026-10-14)

- Autorizado por el usuario con "continua", respondiendo a la propuesta del
  E9 como único paso siguiente; antes de tocar nada se le explicó qué cambia
  (una columna nueva, ningún dato existente) y qué le toca a él (rama de
  Neon, esquema base, aplicar). Al iniciar, los dos repos en `main` y
  limpios, con el commit del E8 sin subir: backend `ff92f93`, frontend
  `df2e494`. Se leyó completa `docs/MIGRACIONES.md`.
- Pruebas primero: `tests/test_migracion_admisiones_cuestionario.py`, 6
  pruebas sobre el texto del SQL; las 6 fallaron porque el archivo no
  existía. Comprueban la columna (`JSONB NOT NULL DEFAULT '{}'::jsonb`), la
  regla de que sea un objeto (con su comprobación previa en `pg_constraint`),
  que la regla vaya después de la columna, que solo toque `admisiones` (sin
  tablas ni índices nuevos), que sea reejecutable y que no cambie ni borre
  datos.
- `migrations/20261014_admisiones_cuestionario.sql`: `ADD COLUMN IF NOT
  EXISTS cuestionario` y `chk_admisiones_cuestionario_objeto` dentro de un
  `DO`, el mismo patrón de `20261008_anios_lectivos_activacion.sql`.
- Documentado en `docs/MIGRACIONES.md` (lista y sección propia) y
  `docs/CAMBIOS_BACKEND.md`.
- Verificación local en "Entrega para el siguiente chat".
- No se ejecutó la migración, no se accedió a Neon ni a producción y no se
  regeneró ni editó a mano el esquema base. **El paso E9 todavía no está
  terminado.**

**Lista de comprobación en una rama de Neon** (la hace el usuario; el
asistente no se conecta a Neon):

1. En console.neon.tech → Branches → **Create branch** desde `production`,
   con los datos actuales. Nombre sugerido: `prueba-cuestionario`.
2. En la rama nueva → **Connect**: copiar la cadena de conexión **directa**
   (con "Connection pooling" apagado; el host no debe tener `-pooler`). No
   pegarla en el chat.
3. En una terminal de PowerShell, en la carpeta del backend. La variable
   solo vive en esa ventana y gana sobre el `.env`:

   ```powershell
   $env:DATABASE_URL = "<cadena directa de la rama>"
   ([uri]$env:DATABASE_URL).Host
   .\venv\Scripts\python.exe apply_migration.py migrations/20261014_admisiones_cuestionario.sql --dry-run
   .\venv\Scripts\python.exe apply_migration.py migrations/20261014_admisiones_cuestionario.sql
   .\venv\Scripts\python.exe apply_migration.py migrations/20261014_admisiones_cuestionario.sql --dry-run
   ```

   El host que se imprime debe ser el de la rama, **no**
   `ep-late-smoke-aip41j6x` (producción). Esperado: `PENDIENTE` → `OK` →
   `OMITIDA (ya aplicada)` en `tenant_colegio_1` y `tenant_2005`.
4. En la misma terminal, regenerar el esquema base desde la rama:

   ```powershell
   .\venv\Scripts\python.exe scripts\generar_esquema_base.py --schema tenant_colegio_1
   ```

   Esperado en el diff: en la cabecera, 44 migraciones (antes 43), incluida
   `20261014_admisiones_cuestionario.sql`; en `admisiones`, la columna
   `cuestionario jsonb DEFAULT '{}'::jsonb NOT NULL` y la regla
   `chk_admisiones_cuestionario_objeto`; y nada más (siguen 36 tablas, 1
   función y 1 disparador). Después, cerrar esa terminal.
5. En el SQL Editor de Neon, **con la rama de prueba elegida**, pegar todo
   esto junto y correrlo una vez. Intenta 8 altas en `tenant_colegio_1`;
   cada una se deshace al instante, así que no queda nada guardado. La
   columna `bien` debe salir `true` en las 8 filas:

   ```sql
   SET search_path TO tenant_colegio_1, public;

   CREATE TEMP TABLE prueba_cuestionario (orden INT, caso TEXT, debe TEXT, obtuvo TEXT);

   DO $$
   DECLARE
       anio_id INTEGER := (SELECT id FROM anios_lectivos ORDER BY anio DESC LIMIT 1);
       fila RECORD;
   BEGIN
       FOR fila IN
           SELECT * FROM (VALUES
               (1, 'Sin cuestionario (queda vacío)', 'aceptar',
                $q$INSERT INTO admisiones (anio_lectivo_id, nombre, apellido, autoriza_datos, autoriza_nombre)
                   VALUES ({anio}, 'Prueba', 'Cuestionario', TRUE, 'Acudiente')$q$),
               (2, 'Cuestionario con una respuesta', 'aceptar',
                $q$INSERT INTO admisiones (anio_lectivo_id, nombre, apellido, autoriza_datos, autoriza_nombre, cuestionario)
                   VALUES ({anio}, 'Prueba', 'Cuestionario', TRUE, 'Acudiente', '{"usa_panal": {"respuesta": "no"}}')$q$),
               (3, 'Cuestionario vacío', 'aceptar',
                $q$INSERT INTO admisiones (anio_lectivo_id, nombre, apellido, autoriza_datos, autoriza_nombre, cuestionario)
                   VALUES ({anio}, 'Prueba', 'Cuestionario', TRUE, 'Acudiente', '{}')$q$),
               (4, 'Cuestionario en NULL', 'cuestionario',
                $q$INSERT INTO admisiones (anio_lectivo_id, nombre, apellido, autoriza_datos, autoriza_nombre, cuestionario)
                   VALUES ({anio}, 'Prueba', 'Cuestionario', TRUE, 'Acudiente', NULL)$q$),
               (5, 'Una lista en vez de un bloque', 'chk_admisiones_cuestionario_objeto',
                $q$INSERT INTO admisiones (anio_lectivo_id, nombre, apellido, autoriza_datos, autoriza_nombre, cuestionario)
                   VALUES ({anio}, 'Prueba', 'Cuestionario', TRUE, 'Acudiente', '[]')$q$),
               (6, 'Un texto en vez de un bloque', 'chk_admisiones_cuestionario_objeto',
                $q$INSERT INTO admisiones (anio_lectivo_id, nombre, apellido, autoriza_datos, autoriza_nombre, cuestionario)
                   VALUES ({anio}, 'Prueba', 'Cuestionario', TRUE, 'Acudiente', '"hola"')$q$),
               (7, 'Un número en vez de un bloque', 'chk_admisiones_cuestionario_objeto',
                $q$INSERT INTO admisiones (anio_lectivo_id, nombre, apellido, autoriza_datos, autoriza_nombre, cuestionario)
                   VALUES ({anio}, 'Prueba', 'Cuestionario', TRUE, 'Acudiente', '3')$q$),
               (8, 'JSON mal escrito', 'json',
                $q$INSERT INTO admisiones (anio_lectivo_id, nombre, apellido, autoriza_datos, autoriza_nombre, cuestionario)
                   VALUES ({anio}, 'Prueba', 'Cuestionario', TRUE, 'Acudiente', '{"usa_panal":')$q$)
           ) AS c (orden, caso, debe, sentencia)
           ORDER BY orden
       LOOP
           BEGIN
               EXECUTE replace(fila.sentencia, '{anio}', anio_id::text);
               RAISE EXCEPTION 'aceptada';
           EXCEPTION
               WHEN raise_exception THEN
                   INSERT INTO prueba_cuestionario VALUES (fila.orden, fila.caso, fila.debe, 'aceptada');
               WHEN OTHERS THEN
                   INSERT INTO prueba_cuestionario VALUES (fila.orden, fila.caso, fila.debe, SQLERRM);
           END;
       END LOOP;
   END
   $$;

   SELECT orden, caso, debe, obtuvo,
          CASE WHEN debe = 'aceptar' THEN obtuvo = 'aceptada'
               ELSE position(debe IN obtuvo) > 0 END AS bien
   FROM prueba_cuestionario
   ORDER BY orden;
   ```

   Mismo mecanismo que la consulta del E1: si la base acepta un alta, se
   deshace a propósito con `RAISE EXCEPTION 'aceptada'`; si la rechaza,
   también se deshace. Solo queda el resultado en una tabla temporal, que
   desaparece al cerrar la sesión.
6. En el mismo SQL Editor, también con la rama elegida (solo lectura): que
   las admisiones que ya existían quedaron con el bloque vacío. En cada fila
   los dos números deben ser iguales:

   ```sql
   SELECT 'tenant_colegio_1' AS colegio, COUNT(*) AS admisiones,
          COUNT(*) FILTER (WHERE cuestionario = '{}'::jsonb) AS con_bloque_vacio
   FROM tenant_colegio_1.admisiones
   UNION ALL
   SELECT 'tenant_2005', COUNT(*),
          COUNT(*) FILTER (WHERE cuestionario = '{}'::jsonb)
   FROM tenant_2005.admisiones;
   ```
7. Contarle al asistente lo que salió en los puntos 3 a 6, sin cadenas de
   conexión. Después se puede borrar la rama.

**Prueba en la rama de Neon, 2026-10-14** (rama `prueba-cuestionario`, copia
de `production`; la hizo el usuario, el asistente no se conectó a Neon ni a
producción):

- El usuario informó que hizo los puntos 1 a 4. Los resultados de los tres
  comandos del punto 3 no se pegaron en el chat; se le pidieron.
- Esquema base regenerado desde `tenant_colegio_1` en la rama: 36 tablas, 1
  función y 1 disparador (sin cambio), "el contenido CAMBIO". La revisión del
  diff confirmó solo lo esperado: la fecha y 44 migraciones en la cabecera
  (antes 43), incluida `20261014_admisiones_cuestionario.sql`; la columna
  `cuestionario jsonb DEFAULT '{}'::jsonb NOT NULL` y la regla
  `chk_admisiones_cuestionario_objeto`. La cabecera confirma que la migración
  quedó registrada en `tenant_colegio_1` de la rama.
- Verificación, con una `DATABASE_URL` ficticia: 26 pruebas específicas pasan
  (6 de esta migración, 15 del E1 y 5 del esquema base); `scripts/verify.py`
  → **2435 pasan, 0 fallan** (se apagó la falla esperada), Ruff y `pip
  check` limpios; `git diff --check` limpio.
- Consulta de la regla (punto 5) en el SQL Editor, sobre `tenant_colegio_1`
  de la rama: **las 8 filas con `bien = true`**. Se aceptaron la admisión sin
  cuestionario, con una respuesta y con el bloque vacío. Se rechazaron, cada
  uno con lo esperado: el bloque en `NULL` (`NOT NULL`), una lista, un texto y
  un número (`chk_admisiones_cuestionario_objeto`) y un JSON mal escrito
  ("invalid input syntax for type json").
- Consulta del punto 6 (solo lectura): `tenant_colegio_1` 1 admisión, 1 con
  el bloque vacío; `tenant_2005` 1 admisión, 1 con el bloque vacío. Las
  admisiones que ya existían quedaron con `{}`, y la consulta confirma que la
  columna existe también en `tenant_2005` de la rama. Dato: en la copia de
  producción, `tenant_2005` ya tenía una admisión registrada; el colegio real
  ya usa Admisiones.
- Los resultados de los tres comandos del punto 3 no se pegaron; la cabecera
  del esquema base (registro en `tenant_colegio_1`) y las consultas de los
  puntos 5 y 6 (la columna y su regla en los dos colegios) muestran que se
  aplicó en ambos.
- El usuario hizo el commit del E9 (`9547721`) antes de regenerar el esquema
  base, así que no lo traía. Prefirió un commit aparte con el esquema base y
  estos documentos, en vez de rehacer el del E9. Los dos se suben juntos en
  el mismo push: así lo que llega a GitHub y a Render tiene migración y base
  a la vez, aunque el commit `9547721` solo, sin el siguiente, fallaría
  `test_esquema_base.py`.
- **Prueba en la rama terminada, todo correcto.**

**En producción, 2026-10-14** (lo hizo el usuario; el asistente no se conectó
a ninguna base):

- El usuario hizo el commit aparte con el esquema base y los documentos
  (`3728dcb`) y subió los dos del E9 en el mismo push, junto con el del E8
  (`ff92f93`): `origin/main` en `3728dcb`, visto con `git fetch`. En el
  frontend, `origin/main` en `df2e494` (el E8).
- Después informó que aplicó la migración en producción. No pegó la salida de
  los comandos (`PENDIENTE` → `OK` → `OMITIDA`) ni dijo si esperó a Render
  **Live**; ninguna de las dos cosas se ve desde el repo. Ningún código usa
  la columna todavía, así que no cambia nada visible.
- Visto al cerrar (solo el servidor, sin la contraseña): el `DATABASE_URL`
  del `.env` del backend quedó en el endpoint **directo** de producción
  (`ep-late-smoke-aip41j6x`, sin `-pooler`). Así el runner ya no se niega a
  correr sin `$env:DATABASE_URL`, que es la protección acordada. Se le pidió
  devolverlo al endpoint `-pooler`.
- A partir de aquí el archivo `20261014_admisiones_cuestionario.sql` **no se
  puede editar**: el runner guarda su checksum. Cualquier cambio posterior va
  en una migración nueva.
- **Paso E9 terminado.**

## Entrega para el siguiente chat

- Estado al 2026-10-14: **E1 a E6 en producción**, según el usuario; **E7 en
  GitHub** (`24a9a3c`; que Render lo tenga **Live** no se ve desde el repo).
  Con el E7 se completó el plan original. **E8 terminado**: el diseño de las
  preguntas del anexo (ver "Preguntas del anexo (pasos E8 a E12)"), sin
  código. **E9 terminado y en producción** según el usuario: la columna
  `admisiones.cuestionario` (migración `20261014_admisiones_cuestionario.sql`,
  commits `9547721` y `3728dcb`, en GitHub). Ver "Avance del paso E9". Hasta
  donde consta en estos documentos, el SQL del E2 y el E3 no se probó en una
  rama de Neon antes de publicar.
- Verificación del E9, con una `DATABASE_URL` ficticia: `scripts/verify.py`
  → **2435 pasan, 0 fallan**, Ruff y `pip check` limpios; `git diff
  --check` limpio. El frontend no cambió en este paso.
- Pendiente del usuario: devolver el `DATABASE_URL` del `.env` del backend al
  endpoint `-pooler` (quedó en el directo de producción) y borrar las ramas
  `prueba-cuestionario` y `prueba-entrevista` de Neon, si no se borraron.
- Siguiente acción exacta: el usuario revisa la lista de las 55 preguntas
  (pregunta abierta "Antes del E10") y autoriza el **E10**: la lista de
  preguntas en el código, la revisión de respuestas y las rutas (`GET
  /admisiones/cuestionario`, `cuestionario` en ver y editar, lectura desde
  la ficha), con pruebas primero. Sigue recomendada la prueba de humo del E7
  en producción con el Colegio Demo (`tenant_colegio_1`, nunca
  `tenant_2005`): tarjeta →
  Admisiones → nuevo aspirante → entrevista → aprobar → matricular → ficha
  con "Datos de admisión". Pendiente: si se borra
  `crearEstudianteEnPreparacion` del frontend. Abiertas para más adelante:
  ver "Preguntas abiertas" (supresión de datos al activar 2027, un enlace
  por año para quien vuelve por admisión antes de preparar 2028, entrevista
  a mitad de año).
- Por qué el push del E1 fue antes de aplicar en producción (igual que el paso 5.2
  del año lectivo, `a6f3cc0`): un colegio nuevo nace del archivo base y
  copia el historial de migraciones de la plantilla
  (`copiar_historial_migraciones` en `super_admin_repository.py`). Si se
  aplicara primero, un colegio creado en ese rato nacería sin la tabla pero
  con la migración en su historial, y nadie la volvería a aplicar. Con el
  push primero, lo peor es que tenga la tabla sin el registro; el runner la
  aplicaría de nuevo y `CREATE TABLE IF NOT EXISTS` no haría nada.
- Pendiente del usuario: borrar la rama `prueba-entrevista` en Neon, si no
  se borró.
- Prompt para retomar: `docs/funcionalidades/PROMPT_CONTINUACION_ENTREVISTA_ADMISION.md`.
