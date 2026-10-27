# Funcionalidad: Firma del acudiente en el observador — Backend

## Control

- Estado: **diseñado el 2026-10-27, nada implementado.** El paso 0 (este
  documento) está hecho y el paso 1 espera la orden del usuario.
- Tipo: función nueva de producto, construida encima del observador unificado
  (`docs/funcionalidades/OBSERVADOR_ESTUDIANTE.md`). No es un módulo de
  `docs/modularizacion/`.
- **Este es el documento principal.** Las pantallas y la impresión están en
  `frontend-react/docs/funcionalidades/FIRMA_OBSERVADOR.md`.
- Repos afectados: este (tabla, endpoints y permisos) y `frontend-react`
  (pantallas e impresión). **El backend va primero.**
- Riesgo: medio. Trae una migración nueva, una excepción de permisos para el
  admin y una regla nueva que bloquea la edición.
- Última actualización: 2026-10-27.

## Objetivo

Que el acudiente firme **en pantalla, en el colegio**, cada anotación del
observador que se le muestra, en el celular o la tablet de quien lo atiende.
Esa firma reemplaza la línea en blanco del observador impreso.

## Motivación

- Hoy el acudiente firma el observador **impreso**. El papel se pierde, y el
  sistema no guarda constancia de que el acudiente conoció una anotación.
- La firma en pantalla no necesita cuentas de padres, ni mensajes, ni una
  página pública, porque quien la toma ya tiene la sesión iniciada.

## Fuera de alcance

- La firma a distancia (un enlace por WhatsApp o SMS con un código). Si se
  pide, se construye encima de esta.
- La firma del estudiante. Se decidió "no por ahora"; se agregaría con el mismo
  mecanismo.
- Firmar varias anotaciones con un solo trazo. Se decidió una firma por
  anotación.
- Enviarle una copia al acudiente.
- Las observaciones de periodo (tabla `observaciones`, rutas `/observaciones/...`),
  que son otra cosa.

## Decisiones ya tomadas (con el usuario, 2026-10-27)

| # | Decisión |
|---|---|
| 1 | La firma es **presencial, en pantalla**, con el dedo |
| 2 | **Cada anotación se firma por separado** |
| 3 | Toma la firma el **profesor**, de sus propias anotaciones, y el **director de grupo** y el **admin**, de todas las del estudiante |
| 4 | Una anotación firmada queda **bloqueada para siempre**. Un error se corrige con una anotación nueva |
| 5 | Solo firma el **acudiente** |

### La decisión 3 abre una excepción para el admin, y es deliberada

`_profesor_que_escribe`, en `app/routes/observador.py`, deja claro que el admin
no escribe ni edita en el observador. Tomar una firma **no cambia el texto** de
la anotación: solo deja constancia de que el acudiente la leyó. Por eso el admin
puede tomarla sin romper esa regla. Escribir y editar siguen siendo solo del
profesor.

## Por qué la firma es válida (resumen, no es asesoría legal)

En Colombia, la Ley 527 de 1999 (art. 7) y el Decreto 2364 de 2012 (hoy dentro
del Decreto 1074 de 2015) aceptan una firma electrónica si identifica a quien
firma y permite detectar si el contenido cambió después. Este diseño cubre las
dos condiciones:

- **Quién firmó.** La firma se toma en persona, ante alguien con la sesión
  iniciada, que queda registrado como testigo. Además se guardan el nombre y el
  documento del firmante.
- **Que no cambió.** La anotación queda bloqueada, y se guarda una huella del
  contenido firmado que se vuelve a comprobar en cada lectura.

Fuera del código, el colegio debe incluir la firma en pantalla en su manual de
convivencia. Si es suficiente o no, lo decide el abogado o el rector del colegio.

## Diseño de datos

### Tabla nueva: `observador_firmas`

Guarda una fila por cada anotación firmada. Va en una tabla aparte, y no como
columnas de `observador_anotaciones`, para que la imagen no viaje en cada lectura
de la bitácora.

| Columna | Tipo | Nota |
|---|---|---|
| `id` | serial | PK |
| `anotacion_id` | integer NOT NULL **UNIQUE** | FK a `observador_anotaciones(id)`, sin cascada. El UNIQUE asegura que haya como máximo una firma |
| `estudiante_id` | integer NOT NULL | FK a `estudiantes(id)`. Tiene que coincidir con el de la anotación; lo verifica el servidor |
| `firmante_nombre` | varchar(150) NOT NULL | |
| `firmante_tipo_documento` | varchar(50) NOT NULL | |
| `firmante_documento` | varchar(50) NOT NULL | |
| `firmante_parentesco` | varchar(50) NOT NULL | Padre, madre u otro acudiente |
| `imagen_png` | bytea NOT NULL | PNG validado en el servidor, de máximo 100 KB |
| `tomada_por_profesor_id` | integer NULL | FK a `profesor(id)` |
| `tomada_por_usuario_id` | integer NULL | FK a `usuarios(id)`, para el admin |
| `tomada_por_nombre` | varchar(150) NOT NULL | Copia del nombre en ese momento |
| `firmada_en` | timestamptz NOT NULL | La pone el servidor |
| `huella` | char(64) NOT NULL | SHA-256; se explica abajo |

Un CHECK exige que exactamente una de las dos columnas `tomada_por_*` tenga
valor. Son dos columnas, y no un `id` más un `rol`, porque los profesores y los
admins viven en tablas distintas, y así cada columna conserva su clave foránea.

### La huella

Es un SHA-256 calculado **en el servidor** al firmar, sobre un texto canónico
con:

- el contenido de la anotación (`estudiante_id`, `profesor_id`, `periodo`,
  `conductual`, `cognitivo`, `lenguaje`, `creada_en`, `editada_en`);
- los datos del firmante;
- la imagen;
- quién tomó la firma;
- `firmada_en`.

Las fechas van en UTC y en formato ISO. En cada lectura la huella se recalcula,
y si no coincide la firma sale con `integra: false`. Solo un cambio hecho
directamente en la base, sin pasar por la API, podría hacerla fallar.

### Migración

`migrations/<fecha>_observador_firmas.sql`, junto con la base regenerada, como
indica `CLAUDE.md` ("two sources of truth"). Se prueba primero en una rama de
Neon y luego se aplica con `apply_migration.py` (`docs/MIGRACIONES.md`). El
índice por `estudiante_id`, que usa la consulta para imprimir, sigue el mismo
procedimiento que el de `observador_anotaciones`: va en
`scripts/apply_tenant_indexes.py` y en la base, **no** dentro de la migración
(la nota de `migrations/20260908_observador_anotaciones.sql` explica por qué).

## Permisos

Para **firmar** se tienen que cumplir dos cosas:

1. Pasar `require_estudiante_access` sobre el estudiante de la anotación. Es la
   misma puerta que para leer la bitácora.
2. Cumplir una de estas condiciones:
   - **profesor autor:** `anotacion.profesor_id` es el profesor de la sesión;
   - **director de grupo:** el profesor de la sesión es el
     `cursos.director_grupo_id` del curso del estudiante en el año lectivo de la
     anotación (`matriculas.curso_id` con `anotacion.anio_lectivo_id`). Se
     confirma en el paso 1 (P1);
   - **admin:** cualquier anotación del colegio.

Si no se cumple ninguna, responde 403.

Para **leer** las firmas valen las mismas reglas que para la bitácora. La imagen
y el documento completo del firmante solo salen en la consulta para imprimir.

## Cambios de API (propuesta, se fija en el paso 1)

- `POST /observador/anotaciones/{anotacion_id}/firma`, nuevo.
  - Cuerpo: `firmante_nombre`, `firmante_tipo_documento`, `firmante_documento`,
    `firmante_parentesco`, `imagen` (el PNG en base64) y `version` (la que el
    cliente mostró).
  - Respuestas:
    - `201`, con la firma sin la imagen;
    - `403`, sin permiso;
    - `404`, si la anotación no existe;
    - `409`, si ya está firmada o si cambió desde que se mostró;
    - `422`, si los datos o la imagen no son válidos.
- `GET /observador/{estudiante_id}`, que ya existe. Cada anotación suma tres
  campos:
  - `version`;
  - `puede_firmar`, calculado en el servidor (para el director de grupo la
    pantalla no tiene cómo calcularlo);
  - `firma`, que es `null` o `{firmante_nombre, firmante_parentesco,
    firmante_documento_enmascarado, firmada_en, tomada_por_nombre, integra}`.
- `GET /observador/{estudiante_id}/firmas`, nuevo, para imprimir. Devuelve en una
  sola petición las firmas completas, con su imagen, de las anotaciones del
  estudiante que el usuario puede ver.
- `GET /observador/{estudiante_id}/firmantes-sugeridos`, nuevo. Devuelve el padre
  y la madre de la ficha (`nombre_*`, `tipo_documento_*`, `documento_*`) para no
  escribirlos a mano.
- `PUT /observador/{anotacion_id}`, que ya existe, gana un **409 nuevo** cuando la
  anotación está firmada, con un mensaje que invita a escribir una anotación
  nueva. La regla va en `exigir_anotacion_editable`.

## Invariantes

1. Una anotación tiene **como máximo una firma** (UNIQUE).
2. Una anotación firmada **no se edita, por nadie**: responde 409. Borrar ya no
   existía.
3. Una firma **no se edita ni se borra**: no hay endpoints para eso.
4. La fecha, la hora y quién tomó la firma los pone **el servidor**, nunca el
   cliente.
5. Firmar y editar al mismo tiempo no puede dejar firmado un texto distinto del
   que se mostró. Para eso se bloquea la fila de la anotación (`FOR UPDATE`) y se
   compara la `version`.
6. La imagen y el documento del firmante **no se escriben en los logs**.
7. La bitácora sigue siendo **una sola petición**. Las imágenes solo se piden al
   imprimir.

## Riesgos y mitigación

| Riesgo | Mitigación |
|---|---|
| La migración daña datos de producción | Probarla antes en una rama de Neon, con `--dry-run`, y nunca directamente contra producción |
| Un profesor edita mientras el acudiente firma | Bloqueo de la fila y comparación de la `version` (invariante 5) |
| Las imágenes grandes llenan la base | PNG validado de máximo 100 KB. El frontend la reduce antes de enviarla |
| El admin gana un permiso nuevo | Solo puede firmar, nunca escribir ni editar. Hay pruebas que lo fijan |
| Datos personales del acudiente (Ley 1581 de 2012) | El mismo acceso que la bitácora, el documento enmascarado en pantalla y nada en los logs |
| La huella marca "alterada" por un cambio de formato legítimo | Texto canónico fijo, fechas en UTC e ISO, y pruebas de la huella |

## Plan de pasos y orden de publicación

| Paso | Repo | Qué | ¿Lo ven los colegios? |
|---|---|---|---|
| 0 | ambos | Este documento y el del frontend | No |
| 1 | backend | Migración, endpoints, regla de bloqueo y pruebas. La migración va a producción **antes** del push | No |
| 2 | frontend | Botón "Firmar con el acudiente", ventana de firma, sello de "firmada" y sin "Editar" en las firmadas | Sí |
| 3 | frontend | La firma en el observador impreso | Sí |
| 4 | ambos | Publicación y prueba real en el Colegio Demo | Sí |

## Preguntas abiertas

- **P1 (paso 1):** al director de grupo, ¿se le busca por el curso del año de la
  anotación o por el curso actual? Propuesta: por el del año de la anotación.
- **P2 (paso 3):** si todas las anotaciones impresas ya están firmadas, ¿el pie
  conserva la línea "Firma del Acudiente"?
- **P3 (paso 2):** el documento del firmante, ¿se muestra completo o enmascarado
  en pantalla? Propuesta: enmascarado en pantalla y completo en el impreso.

## Entrega para el siguiente chat

El siguiente es el **paso 1**, cuando el usuario lo ordene. Antes conviene leer
`CLAUDE.md`, `docs/MIGRACIONES.md`, `docs/funcionalidades/OBSERVADOR_ESTUDIANTE.md`
y `app/routes/observador.py`, sobre todo `_profesor_que_escribe` y
`exigir_anotacion_editable`.
