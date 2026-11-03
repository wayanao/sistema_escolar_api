# API Endpoints

Ultima revision documental: 2026-10-21.

## Routers

Los routers se incluyen en `app/main.py`.

Prefijos definidos en router:

- `boletines`: prefix `/boletines`
- `egresos`: prefix `/api/egresos`
- `listas_seguimiento`: prefix `/listas-seguimiento`
- `prestamos`: prefix `/api/prestamos`
- `super_admin`: prefix `/super-admin`
- `ventas`: prefix `/api/ventas`
- `nomina`: incluido en `main.py` con prefix `/api/nomina`

Los demas routers usan paths completos en cada decorator.

## Health

- `GET /ping`
- `GET /health`

`GET /ping`:

- Publico, sin autenticacion. Es la que llama el monitor externo.
- Responde `200` con `{"status": "ok"}` y **no toca la base**: si la
  consultara cada 5 minutos, Neon no se dormiria nunca y cobraria las 24 horas.
- No detecta fallos de la base ni el pool agotado.
- Limite: `60/minute` por IP.

`GET /health`:

- Publico, sin autenticacion. Con `/ping`, son las unicas rutas abiertas
  ademas de `login`. Queda para comprobar a mano, por ejemplo tras publicar.
- `200` cuando la API vive y PostgreSQL responde:

```json
{
  "status": "ok",
  "database": "ok"
}
```

- `503` cuando la base no responde o el pool esta agotado:

```json
{
  "status": "degraded",
  "database": "error"
}
```

- El chequeo fija el tenant en `public` y ejecuta `SELECT 1`. No lee ningun
  schema de colegio.
- La respuesta no expone version, host ni detalle del error; ese detalle va al
  log del servidor.
- Limite de `60/minute` por IP, declarado en el decorador de la ruta.
- No debe usarse como `Health Check Path` de Render: ver `PRODUCCION_BACKEND.md`.

## Auth

- `POST /login`
- `POST /logout`
- `POST /auth/cambiar-password`

## Tenant

- `GET /tenant/status`: `{ estado, mostrar_aviso, mensaje,
  usa_entrevista_admision }`. El último, desde el 2026-10-30, dice si el
  colegio usa la entrevista de admisión (`public.colegios`); ver
  `docs/funcionalidades/ENTREVISTA_ADMISION.md`, "Solo en los colegios que
  la usan".

## Super Admin

- `GET /super-admin/tenants`
- `POST /super-admin/tenants`
- `PATCH /super-admin/tenants/{tenant_id}/estado`
- `GET /super-admin/tenants/{tenant_id}/estado-auditoria`
- `POST /super-admin/tenants/{tenant_id}/pagos`

## Uploads

- `GET /uploads/{file_path:path}`

## Años lectivos

- `GET /anios-lectivos`
- `POST /anios-lectivos` (solo admin)
- `POST /anios-lectivos/{anio_lectivo_id}/copiar-configuracion` (solo admin)
- `GET /anios-lectivos/{anio_lectivo_id}/matriculas/candidatos` (solo admin)
- `POST /anios-lectivos/{anio_lectivo_id}/matriculas/promocion` (solo admin)
- `POST /anios-lectivos/{anio_lectivo_id}/estudiantes` (solo admin; **cerrada desde el 2026-10-14**, ver abajo)
- `GET /anios-lectivos/{anio_lectivo_id}/resumen` (solo admin)
- `GET /anios-lectivos/{anio_lectivo_id}/activacion/vista-previa` (solo admin)
- `PUT /anios-lectivos/{anio_lectivo_id}/matriculas/salida` (solo admin)
- `POST /anios-lectivos/{anio_lectivo_id}/activar` (solo admin)
- `POST /anios-lectivos/{anio_lectivo_id}/reabrir` (solo admin)
- `POST /anios-lectivos/{anio_lectivo_id}/cerrar` (solo admin)

Notas:

- Fase 3, paso 3.1, de `docs/funcionalidades/ANIO_LECTIVO.md`. Admin y
  profesor. El admin recibe todos los años; el profesor, solo el activo
  (lista vacia si el colegio no tuviera año activo).
- Respuesta: lista de `{ "id": 2, "anio": 2026, "estado": "activo" }`, el
  año mas reciente primero. Estados: `preparacion`, `activo`, `cerrado`,
  `reabierto`.
- Es la lista del selector de año del frontend (su fase 4). Los listados
  que acepten `?anio_lectivo_id=` (pasos 3.2 a 3.5) usan el activo si no
  llega; un profesor que pida otro año recibira 403.
- Fase 5, paso 5.3: `POST /anios-lectivos` no recibe cuerpo ni permite que el
  cliente elija el número. Toma el año activo `N`, crea exactamente `N+1` en
  estado `preparacion` y responde `201` con
  `{ "id": 3, "anio": 2027, "estado": "preparacion" }`.
- La creación responde `409` si ya hay un año en preparación, si falta un año
  activo o si el siguiente ya existe. La operación bloquea la fila activa y
  los índices únicos siguen siendo la última protección ante dos solicitudes
  simultáneas.
- Fase 5, paso 5.4: copiar la configuración recibe el id del año destino, que
  el backend exige que sea exactamente `N+1` y esté en `preparacion`. Cuerpo:

```json
{
  "copiar_precios": false,
  "copiar_carga_academica": false,
  "copiar_directores": false
}
```

- Las tres opciones son `false` por defecto. Los cursos activos del año
  vigente se copian siempre con nombre, jornada y nivel, nacen activos y
  guardan `curso_origen_id`. Los conceptos se copian siempre, también los
  inactivos, con valor y toda su configuración, y guardan
  `tipo_pago_origen_id`.
- Si se eligen, los precios apuntan a los cursos y conceptos nuevos; los
  directores se copian a su curso nuevo; y la carga académica conserva
  profesor, materia, día, horas, estado y orden de boletín. Las franjas
  reconstruyen `asignacion_academica_id` solo con ids del año nuevo.
- Respuesta de ejemplo:

```json
{
  "anio_origen_id": 2,
  "anio_origen": 2026,
  "anio_destino_id": 3,
  "anio_destino": 2027,
  "copiados": {
    "cursos": 12,
    "conceptos_pago": 2,
    "precios_curso": 24,
    "asignaciones": 267,
    "directores_grupo": 12
  }
}
```

- Todo ocurre en una transacción. Un curso o concepto repetido responde `409`
  identificándolo y revierte toda la copia. También responde `409` si el
  destino no es el siguiente en preparación o si una referencia del origen no
  puede reconstruirse; un id de año inexistente responde `404`.

- Fase 5, paso 5.5: candidatos recibe `curso_origen_id` como query. El curso
  debe ser del año activo y el id de la ruta debe ser exactamente `N+1` en
  preparación. Devuelve todos los estudiantes de la matrícula del curso,
  incluidos retirados o egresados, y marca `matriculado_en_destino` para no
  volver a promover a quien ya tenga matrícula allí. Desde la fase 6, paso
  6.5, cada candidato trae también `estado_salida` (`"retirado"`,
  `"egresado"` o `null`), la marca de su matrícula del año activo, para que
  la pantalla de promoción la muestre y la quite.
- La promoción recibe una selección explícita, sin ids vacíos ni repetidos:

```json
{
  "curso_origen_id": 10,
  "curso_destino_id": 20,
  "estudiante_ids": [1, 2]
}
```

- Solo esos estudiantes reciben matrícula en el destino. Sus valores de
  `tipos_pagos_estudiantes` se copian a los conceptos de `N+1` enlazados por
  `tipo_pago_origen_id`; la respuesta los incluye en
  `valores_especiales_copiados`, cada uno con `"estado": "revisar"`. Si un
  concepto equivalente falta, o un estudiante no es candidato o ya está
  matriculado, responde `409` y revierte la selección completa.
- El alta directa (`POST /anios-lectivos/{id}/estudiantes`) **está cerrada
  desde el paso E7 de la entrevista de admisión (2026-10-14)**: con el año en
  preparación responde `409` "Un estudiante nuevo en 2027 se matricula desde
  su entrevista aprobada (Admisiones)." y no escribe nada; con un año que no
  está en preparación, el `409` de siempre. Un estudiante nuevo entra por
  `POST /admisiones/{id}/matricular` (sección "Admisiones"), que crea la
  ficha y solo la matrícula del año en preparación, con
  `estudiantes.curso_id` sin cambiar mientras el año activo siga siendo 2026.
  Hasta el E7 la creaba esta ruta, con el cuerpo de `POST /estudiantes`.
  **Desde el 2026-10-30, en un colegio que no usa la entrevista**
  (`public.colegios.usa_entrevista_admision = FALSE`) vuelve a crearla así:
  `201` con `{ mensaje, id, matricula_id, anio_lectivo_id, curso_id,
  curso_vigente_id: null, valores_especiales_copiados: [] }`.
- Las tres rutas validan el año y los cursos en el backend. Un año inexistente
  responde `404`; un destino que no sea el siguiente en preparación responde
  `409`. No crean pagos ni calculan deudas.
- Fase 5, paso 5.6: el resumen también exige que el id sea exactamente `N+1`
  en preparación. Cuenta solo los registros de ese año y excluye pagos
  anulados. Respuesta de ejemplo:

```json
{
  "anio_lectivo": {"id": 3, "anio": 2027, "estado": "preparacion"},
  "resumen": {
    "cursos": 12,
    "conceptos_pago": 2,
    "estudiantes_matriculados": 174,
    "valores_especiales": 5,
    "pagos_registrados": 1,
    "total_pagado": 250000.0
  }
}
```

- Fase 6, paso 6.2a: la vista previa de activación solo lee. Exige que el id
  sea exactamente `N+1` en preparación (`404` si no existe, `409` si no es
  ese año o si falta el activo). Cuenta quién `continua` (matriculado en los
  dos años), quién llega `nuevo` (solo en el siguiente), y quién sale como
  `retirado` o `egresado` según `matriculas.estado_salida` del año activo.
  Una matrícula en el siguiente año gana sobre una marca de salida. Lista
  `sin_decidir`: estudiantes activos del año activo sin matrícula siguiente ni
  marca. `puede_activar` es `true` solo si esa lista está vacía; lo decide el
  backend. Respuesta de ejemplo:

```json
{
  "anio_origen": {"id": 2, "anio": 2026},
  "anio_destino": {"id": 3, "anio": 2027},
  "resumen": {
    "continuan": 170,
    "nuevos": 4,
    "retirados": 2,
    "egresados": 18,
    "sin_decidir": 1
  },
  "puede_activar": false,
  "sin_decidir": [
    {
      "id": 7,
      "nombre": "Ana",
      "apellido": "Pérez",
      "documento_identidad": "1001",
      "curso_id": 20,
      "curso_nombre": "Quinto A",
      "curso_jornada": "Mañana"
    }
  ]
}
```

- Fase 6, paso 6.2b: la marca de salida se guarda en la matrícula del año
  activo. El id de la ruta es el del siguiente año en preparación, como en la
  promoción, y la operación bloquea los dos años igual que ella. Cuerpo, con
  `estado_salida` obligatorio (`"retirado"`, `"egresado"` o `null` para
  quitarla):

```json
{
  "estudiante_ids": [7, 8],
  "estado_salida": "egresado"
}
```

- Se guarda todo o nada. `409` si algún estudiante no tiene matrícula en el
  año activo o, al marcar, si ya tiene matrícula en el siguiente. Quitar la
  marca (`null`) siempre se permite. No revisa el estado global del
  estudiante. Respuesta:

```json
{
  "anio_origen": {"id": 2, "anio": 2026},
  "anio_destino": {"id": 3, "anio": 2027},
  "estado_salida": "egresado",
  "estudiante_ids": [7, 8],
  "cantidad": 2
}
```

- Desde el 6.2b, la promoción responde `409` si algún seleccionado tiene una
  marca de salida: el admin la quita primero. La respuesta de candidatos no
  cambia.
- Fase 6, paso 6.3a: activar recibe el id del siguiente año en preparación y
  el año escrito por el admin, que el backend compara con el que se activa:

```json
{ "confirmar_anio": 2027 }
```

- En una sola transacción, con los dos años bloqueados: vuelve a revisar los
  pendientes, guarda las materias inactivas como ocultas del año que cierra,
  pasa a `retirado` o `egresado` a quien quedó marcado sin matrícula
  siguiente, cierra el activo (`cerrado_en`), activa el siguiente
  (`activado_en`), copia a cada estudiante el curso de su matrícula del año
  nuevo (o `null`) y corre la consulta de control. Si algo falla, no cambia
  nada. Quien sigue conserva su estado, aunque no sea `activo`.
- Si quedan pendientes, `409` con un objeto, como el aviso de materias:

```json
{
  "detail": {
    "codigo": "activacion_con_pendientes",
    "mensaje": "No se puede activar 2027: faltan 1 estudiantes por decidir.",
    "sin_decidir": [
      {"id": 7, "nombre": "Ana", "apellido": "Pérez", "documento_identidad": "1001",
       "curso_id": 20, "curso_nombre": "Quinto A", "curso_jornada": "Mañana"}
    ]
  }
}
```

- Los demás errores llegan como texto: `404` si el año no existe; `409` si
  no es el siguiente en preparación, si falta el activo, si el año escrito no
  coincide ("Para activar, escribe el año 2027.") o si una comprobación final
  falla ("... Nada cambió."). Respuesta:

```json
{
  "anio_cerrado": {"id": 2, "anio": 2026, "estado": "cerrado"},
  "anio_activo": {"id": 3, "anio": 2027, "estado": "activo"},
  "resumen": {
    "continuan": 170,
    "nuevos": 4,
    "retirados": 2,
    "egresados": 18,
    "materias_ocultas": 3,
    "cursos_vigentes_actualizados": 174
  }
}
```

- Fase 6, paso 6.4a: reabrir pasa un año `cerrado` a `reabierto`, para que
  el admin corrija algo puntual; cerrar lo devuelve a `cerrado`. Las dos
  reciben el año escrito, `{ "confirmar_anio": 2026 }`, y solo cambian el
  estado del año: no tocan estudiantes, cursos, la foto de materias ni
  `activado_en`/`cerrado_en` (la fecha de cierre sigue siendo la del primero).
  Solo puede haber un año reabierto a la vez. Bloquean el año activo, que
  hace de turno para todo cambio de estado, y luego el año pedido.
- Errores en texto: `404` si el año no existe; `409` si no está en el estado
  que corresponde ("Solo se puede reabrir un año cerrado.", "Solo se puede
  volver a cerrar un año reabierto."), si el año escrito no coincide ("Para
  reabrir, escribe el año 2026."), si ya hay otro reabierto ("Ya está
  reabierto el año 2025. Ciérralo antes de reabrir otro.") o si falta el año
  activo. Respuesta:

```json
{ "anio_lectivo": {"id": 1, "anio": 2026, "estado": "reabierto"} }
```

- En un año reabierto, la guardia del paso 3.7 deja escribir al admin y
  responde `403` al profesor, que tampoco lo ve en su lista de años.

### Guardia de escritura (paso 3.7)

Antes de guardar, el backend mira el año de lo que se guarda (el de la clase,
el del plan o el de la anotacion) y aplica esta regla:

| Estado del año | Admin | Profesor |
|---|---|---|
| `activo` | guarda | guarda |
| `preparacion` | guarda | `403` |
| `reabierto` | guarda | `403` |
| `cerrado` | `409` | `409` |

- `409`: `{"detail": "El año lectivo 2026 está cerrado. Solo se puede consultar."}`.
- `403`: `{"detail": "Solo se pueden guardar cambios en el año lectivo activo."}`.
- No se escribe nada: la guardia es lo primero de la transaccion. Con el año
  activo, la respuesta es la de siempre.
- Paso 3.7a (rutas que usa el profesor): `POST /notas`, `POST /planilla/nota`,
  `DELETE /planilla/tipo`, `POST /asistencia`, `POST /boletines/guardar`,
  `POST /observaciones`, `PUT /observador/{anotacion_id}`, `PUT
  /planeador-anual/{asignacion_id}/{periodo}`, `POST /plan-de-clases`,
  `DELETE /plan-de-clases/{plan_id}/imagen`, `PATCH
  /plan-de-clases/{plan_id}/observaciones/{observacion_id}/vista` y, porque
  comparte el guardado, `DELETE /admin/plan-de-clases/{plan_id}/imagen`.
- Paso 3.7b (rutas de solo admin; su router ya exige admin, asi que solo un
  año `cerrado` las frena con `409`): asignaciones (`POST /asignaciones`,
  `PUT /asignaciones/{id}` —mira el curso de antes y el nuevo—, `DELETE
  /asignaciones/{id}`, `DELETE /asignaciones/{profesor_id}/{curso_id}`, `PUT
  /cursos/{curso_id}/orden-boletin`), cursos (`PUT /cursos/{curso_id}`,
  `PATCH /cursos/{curso_id}/estado`), listas de seguimiento (crear y borrar
  columna, guardar marcas, y `POST
  /listas-seguimiento/columnas-en-todos-los-cursos?anio_lectivo_id=`),
  planes del admin (`PATCH .../revision`, `POST .../observaciones`),
  conceptos (`PUT /tipos-pagos/{id}`, `PUT .../configuracion`, `PUT` y
  `DELETE .../cursos`) y valores por estudiante (`PUT` y `DELETE
  /estudiantes/{id}/valores-pago-personalizados/{tipo_pago_id}`).
- En `POST /cursos` y `POST /tipos-pagos`, la guardia se aplica si el alta
  envía `anio_lectivo_id`; el admin puede crear en el activo, en preparación o
  reabierto, pero no en uno cerrado. Si se omite el campo, conservan el camino
  anterior y crean en el activo. Sin la guardia general, a propósito: materias
  (no tienen año; ver el aviso al renombrar) y pagos (un pago se registra en el
  año de la deuda, aunque esté cerrado: decisión 6). `POST /estudiantes` y
  `PUT /estudiantes/{id}` tienen
  desde la fase 5.1 una proteccion mas concreta: el curso enviado debe ser del
  año activo. `DELETE /tipos-pagos/{id}` nunca escribe.
- `POST /observador` no la lleva: la anotacion nueva nace siempre en el año
  activo.
- `POST /observador/anotaciones/{anotacion_id}/firma` (firma del acudiente,
  2026-10-27) la lleva con la regla con usuario: el profesor solo en el año
  activo; el admin tambien en preparacion o reabierto; nadie en uno cerrado.
  Lee el año en la misma consulta que bloquea la anotacion, asi que no le
  cuesta una consulta aparte.
- En asistencia, boletin y observaciones, la comprobacion de que el
  estudiante es del curso de la clase corre antes, en la ruta. Para una clase
  de un año que ya no es el activo esa comprobacion responde primero `403`
  ("El estudiante no pertenece a esta asignación"); el efecto es el mismo:
  no se guarda.

## Admisiones

Entrevista de admisión, pasos E2, E3 y E10: aspirantes nuevos del año en
preparación. Router **solo admin** (datos de menores, Ley 1581 de 2012), en
`app/routes/admisiones.py`. Detalle y decisiones en
`docs/funcionalidades/ENTREVISTA_ADMISION.md`.

- `GET /anios-lectivos/{anio_lectivo_id}/admisiones?resultado=`
- `POST /anios-lectivos/{anio_lectivo_id}/admisiones`
- `GET /admisiones/cuestionario` (paso E10)
- `GET /estudiantes/{estudiante_id}/admision` (paso E10)
- `GET /admisiones/{admision_id}`
- `PUT /admisiones/{admision_id}`
- `DELETE /admisiones/{admision_id}`
- `PUT /admisiones/{admision_id}/resultado` (paso E3)
- `POST /admisiones/{admision_id}/matricular` (paso E3)

Se consulta cualquier año. **Registrar, editar, borrar, poner el resultado y
matricular solo en un año en `preparacion`**; una admisión matriculada
(`estudiante_id`) es de solo consulta.

Desde el 2026-10-30, **registrar, editar, poner el resultado y matricular**
responden `403` "Este colegio no usa la entrevista de admisión." si el
colegio no la usa (`exigir_entrevista_admision`). Leer y borrar siguen
abiertos.

`GET /anios-lectivos/{anio_lectivo_id}/admisiones` acepta `resultado`
(`pendiente`, `aprobado` o `no_aprobado`; otro valor da `422`). Los conteos
son de todo el año, sin el filtro. Orden: apellido, nombre.

```jsonc
{
  "anio_lectivo": {"id": 3, "anio": 2027, "estado": "preparacion"},
  "editable": true,            // el año está en preparación
  "conteos": {"pendiente": 4, "aprobado": 2, "no_aprobado": 1, "matriculado": 1, "total": 7},
  "admisiones": [
    {
      "id": 7, "nombre": "Lina", "apellido": "Díaz",
      "tipo_documento": "RC", "documento_identidad": "2001",
      "curso_id": 20, "curso_nombre": "PRIMERO A", "curso_jornada": "Mañana",
      "acudiente_nombre": "Marta Díaz", "acudiente_telefono": "300...",
      "fecha_entrevista": "2026-10-20", "resultado": "pendiente",
      "estudiante_id": null, "creado_en": "...", "matriculada": false
    }
  ]
}
```

`POST /anios-lectivos/{anio_lectivo_id}/admisiones` responde `201` con la
admisión completa (igual que `GET /admisiones/{id}`). Cuerpo, todos los
textos recortados y los opcionales vacíos guardados como `null`:

```jsonc
{
  "nombre": "Lina",                 // obligatorio, hasta 100
  "apellido": "Díaz",               // obligatorio, hasta 100
  "tipo_documento": "RC",           // hasta 50
  "documento_identidad": "2001",    // hasta 20; no se repite en el año
  "fecha_nacimiento": "2019-03-04",
  "curso_id": 20,                   // curso activo del mismo año
  "acudiente_nombre": "Marta Díaz", // hasta 150
  "acudiente_parentesco": "Madre",  // hasta 50
  "acudiente_telefono": "300...",   // hasta 50
  "autoriza_datos": true,           // obligatorio y true
  "autoriza_nombre": "Marta Díaz"   // obligatorio, hasta 150
}
```

`PUT /admisiones/{admision_id}` recibe lo mismo **más la entrevista**, y
reemplaza todo (lo que no llega queda en `null`). No cambia el resultado, el
año ni el enlace al estudiante; si llegan, se ignoran:

```jsonc
{
  "fecha_entrevista": "2026-10-20",
  "entrevistador": "Psicóloga Ruiz",  // texto, hasta 150 (decisión 10)
  "asistentes": "Madre y abuela",     // hasta 250
  "colegio_anterior": "...",          // hasta 150
  "anio_cursado_anterior": "...",     // hasta 50
  "pre_escolar_anterior": "...",      // hasta 50
  "ebp_anterior": "...",              // hasta 50
  "motivo_retiro_anterior": "...",    // texto largo
  "paz_salvo_anterior": "Sí",         // hasta 10
  "ocupacion_padre": "...",           // hasta 100
  "ocupacion_madre": "...",           // hasta 100
  "vive_con": "...",                  // hasta 250
  "expectativas": "...",              // texto largo
  "observaciones": "...",             // texto largo
  "cuestionario": { /* las preguntas del anexo, ver abajo (paso E10) */ }
}
```

**`cuestionario` es la excepción al reemplazo completo:** si no llega, o
llega `null`, queda como estaba; si llega, reemplaza el bloque entero (`{}`
quita todas las respuestas). Así el formulario de antes, que no lo manda, no
borra respuestas.

`GET /admisiones/{admision_id}` (y las respuestas de `POST` y `PUT`): todas
las columnas de la tabla (`resultado`, `motivo_resultado`, `decidido_en`,
`estudiante_id`, `creado_en`, `actualizado_en` y `cuestionario` incluidas,
este último como objeto, `{}` si no hay respuestas), más `anio`,
`estado_anio`, `curso_nombre`, `curso_jornada`, `matriculada`, `editable`
(año en preparación y sin matricular) y `aviso_documento`:

```jsonc
"aviso_documento": null
// o, si el documento ya es de un estudiante del colegio (cualquier estado):
"aviso_documento": {
  "estudiante_id": 55, "nombre": "Lina", "apellido": "Díaz", "estado": "retirado",
  "mensaje": "El documento 2001 ya es de un estudiante del colegio: Lina Díaz (retirado). Al matricular, chocaría con ese estudiante."
}
```

El aviso no impide registrar. Al matricular, ese estudiante se usa como
exalumno que vuelve (ver `matricular` abajo).

`DELETE /admisiones/{admision_id}` responde
`{"mensaje": "Admisión borrada", "id": 7}`.

`PUT /admisiones/{admision_id}/resultado` recibe
`{"resultado": "aprobado" | "no_aprobado" | "pendiente", "motivo_resultado": "..."}`
y responde la admisión completa. `no_aprobado` exige `motivo_resultado` que
no esté en blanco (`422`). Guarda `decidido_en` con la fecha y hora; volver a
`pendiente` la borra. Se puede cambiar mientras la admisión no esté
matriculada.

`POST /admisiones/{admision_id}/matricular` recibe **la ficha del estudiante**,
el mismo cuerpo de `POST /estudiantes` (`curso_id` obligatorio, de un curso
activo del año de la admisión) y responde `201`:

```jsonc
{
  "mensaje": "Matrícula creada en 2027 para Lina Díaz.",
  "estudiante_id": 55,
  "matricula_id": 1055,
  "anio_lectivo_id": 3,
  "curso_id": 20,
  "estudiante_existente": false,   // true si era un exalumno que vuelve
  "admision": { /* la admisión completa, ya matriculada y no editable */ }
}
```

- Solo un aspirante `aprobado` y sin matricular (`409` si no).
- En una sola transacción: crea la ficha y la matrícula del año de la
  admisión, copia a la ficha lo que pasó a la entrevista (estudios
  anteriores y ocupación de los padres; un dato vacío en la entrevista no
  borra el que ya había) y enlaza la admisión. Si algo falla, no cambia nada.
- El estudiante queda `activo`, diga lo que diga la ficha.
- **Exalumno que vuelve (decisión 11):** si el `documento_identidad` de la
  ficha ya es de un estudiante, se usa ese mismo registro: su ficha se
  reemplaza como en `PUT /estudiantes/{id}` (la pantalla debe llenarla con lo
  que ya tiene) y conserva su historial. `409` si ya tiene matrícula en ese
  año, si estudia en el año activo (va por la promoción) o si está marcado
  como que no sigue.
- Valores de pago especiales: no se crean; se manejan aparte, como en el
  alta directa.
- `cuestionario` no se copia a la ficha: se lee con
  `GET /estudiantes/{estudiante_id}/admision`.

### Preguntas del anexo (paso E10)

La lista vive solo en el backend (`app/core/cuestionario_admision.py`). El
frontend la pide y arma el formulario con ella; el backend revisa cada
respuesta contra ella.

`GET /admisiones/cuestionario` responde la lista (13 secciones, 55
preguntas numeradas del 1 al 55). No lee la base:

```jsonc
{
  "secciones": [
    {
      "clave": "salud",
      "titulo": "Salud",
      "preguntas": [
        {
          "numero": 19, "clave": "dificultad_motora", "tipo": "si_no",
          "texto": "¿Tiene alguna dificultad motora?",
          "opciones": [{"valor": "si", "etiqueta": "Sí"}, {"valor": "no", "etiqueta": "No"}],
          "detalle": {"con": "si", "texto": "¿Cuál?", "maximo": 250}   // solo si la tiene
        },
        {
          "numero": 21, "clave": "enfermedades_padecidas", "tipo": "varias",
          "texto": "Enfermedades que padeció",
          "opciones": [{"valor": "hepatitis", "etiqueta": "Hepatitis"}, /* ... */
                       {"valor": "ninguno", "etiqueta": "Ninguna"}, {"valor": "otro", "etiqueta": "Otra"}],
          "otro": {"texto": "¿Cuál?", "maximo": 250},   // solo si tiene "Otro"
          "exclusiva": "ninguno"                         // solo en las preguntas 5 y 21
        }
      ]
    }
  ]
}
```

Otros campos según el tipo: `numero` trae `minimo` y `maximo`; `texto` y
`texto_largo` traen `maximo` (150 y 1000) y a veces `ayuda`; la pregunta 26
trae `"depende_de": {"pregunta": "seguimiento_profesional", "respuesta":
"si"}`. Las claves nunca cambian de significado.

Qué se manda en `cuestionario` (cada respuesta bajo la clave de su pregunta;
sin responder = la clave no está; `null`, un texto en blanco o una lista
vacía cuentan como sin responder y no se guardan):

```jsonc
{
  "como_lo_llaman": "Juancho",                                   // texto
  "numero_hermanos": 2,                                          // numero (entero)
  "usa_panal": {"respuesta": "no"},                              // si_no
  "dificultad_motora": {"respuesta": "si", "detalle": "Plantillas"},
  "tipo_vivienda": {"opcion": "otro", "otro": "Finca"},          // una
  "comidas_del_dia": {"marcadas": ["desayuno", "cena"]},         // varias
  "con_quien_queda": {"marcadas": ["otro"], "otro": "La vecina"}
}
```

Lo que se guarda (y se devuelve) va recortado y en el orden de la lista;
`marcadas`, en el orden de las opciones. `422` con un mensaje en español
(por ejemplo `Pregunta 2 («Número de hermanos»): tiene que estar entre 0 y
20.`) si: la pregunta no existe; la respuesta no tiene la forma de su tipo;
la opción no existe o está repetida; un número no es entero o está fuera de
su rango; un texto pasa su límite (detalle y "Otro": 250); hay detalle con la
respuesta que no lo pide, o "Otro" escrito sin elegir "Otro"; "Ninguno" va
con otras opciones; la 26 llega sin que la 25 sea "Sí"; o el bloque no es un
objeto.

`GET /estudiantes/{estudiante_id}/admision` (solo admin, en este router): la
admisión enlazada al estudiante, para "Datos de admisión" de la ficha. Un
estudiante sin admisión no es un error:

```jsonc
{"admision_id": 7, "anio": 2027, "fecha_entrevista": "2026-10-20",
 "cuestionario": {"usa_panal": {"respuesta": "no"}}}
// sin admisión:
{"admision_id": null, "anio": null, "fecha_entrevista": null, "cuestionario": {}}
```

Errores (el `detail` es un texto listo para mostrar):

- `403`: no es admin.
- `404`: el año o la admisión no existen.
- `409`: el año no está en preparación; la admisión está matriculada; el
  curso no es un curso activo del año; el documento ya lo tiene otro
  aspirante del año (también si dos altas llegan a la vez); al matricular,
  la admisión no está aprobada, el estudiante existente no puede entrar así,
  o algo se guardó a la vez (documento, matrícula o enlace).
- `422`: cuerpo inválido (falta un obligatorio, `autoriza_datos` no es
  `true`, un texto demasiado largo, `curso_id` no positivo, `no_aprobado`
  sin motivo, una respuesta de `cuestionario` que no corresponde a su
  pregunta).

## Estudiantes

- `POST /estudiantes`
- `GET /estudiantes`
- `GET /estudiantes?estado=activo|retirado|egresado|inactivo|todos`
- `GET /estudiantes/{estudiante_id}/detalles`
- `GET /estudiantes/{estudiante_id}/deudas`
- `GET /estudiantes/{estudiante_id}`
- `PUT /estudiantes/{estudiante_id}`
- `PATCH /estudiantes/{estudiante_id}/estado`

Notas:

- Si no se envia `estado`, el listado devuelve estudiantes `activo`.
- `estado=todos` permite consultar historico/administrativo sin filtrar por
  estado operativo.
- `PATCH /estudiantes/{estudiante_id}/estado` recibe:

```json
{
  "estado": "retirado"
}
```

- Estados validos: `activo`, `retirado`, `egresado`, `inactivo`.
- En `POST /estudiantes` y `PUT /estudiantes/{estudiante_id}`, el cuerpo no
  cambia: `curso_id` sigue siendo obligatorio. El servidor guarda ese curso
  en la matrícula del año activo y después sincroniza
  `estudiantes.curso_id`, que es solo su copia vigente. Un curso inexistente o
  de otro año responde `409` con `El curso seleccionado debe pertenecer al año
  lectivo activo.` Ninguna de las dos escrituras queda aplicada en ese caso.
- **SISBÉN y lugar de residencia** (desde el 2026-10-19, paso S1 de
  `docs/funcionalidades/SISBEN_RESIDENCIA.md`). `POST /estudiantes`,
  `PUT /estudiantes/{estudiante_id}` y `POST /admisiones/{id}/matricular`
  aceptan ocho campos opcionales:
  - `sisben`: `true`, `false` o `null` (sin dato).
  - `sisben_grupo`: `A`, `B`, `C` o `D`.
  - `sisben_subgrupo`: del grupo elegido (`A1`–`A5`, `B1`–`B7`, `C1`–`C18`,
    `D1`–`D21`).
  - `sisben_nivel`: `1`, `2` o `3` (SISBÉN III).
  - `barrio` (150), `municipio` (100), `zona_residencia` (`urbana` o
    `rural`) y `punto_referencia` (255).

  Reglas (`422` con el motivo en español): sin `sisben: true` no se aceptan
  grupo, subgrupo ni nivel; el subgrupo necesita el grupo y debe ser suyo.
  **Si el cuerpo no trae ninguno de los ocho, se quedan como estaban** (una
  pestaña abierta antes del cambio no los borra); si trae alguno, se
  reemplazan los ocho y el que falte queda en `null`. `GET
  /estudiantes/{estudiante_id}` los devuelve sin cambios en la ruta (lee la
  fila completa). `direccion` no cambia: es la calle o carrera y el número.
- `GET /estudiantes/{estudiante_id}/deudas` devuelve solo deuda academica
  pendiente del estudiante usando la logica central de cobros; no depende del
  resumen amplio de notas, observaciones o inventario.
- `GET /estudiantes/{estudiante_id}/deudas?anio_lectivo_id=` (opcional, desde
  la fase 2 del año lectivo): la deuda de ese año, con sus conceptos, el curso
  de la matricula de ese año y sus pagos. Sin el parametro, el año activo, como
  antes. Año inexistente o estudiante sin matricula en ese año: `404` con el
  mensaje.
- `GET /estudiantes?anio_lectivo_id=` (opcional, fase 3 del año lectivo, paso
  3.4; con y sin `limit`). Sin el parametro, **o con el del año activo**, la
  lista de siempre: todos los estudiantes con su curso actual, incluidos los
  que no tienen curso (Pagos y Ventas la usan para encontrar a cualquiera).
  Con otro año: los matriculados de ese año, cada uno con su `curso_id` de ese
  año; el filtro `estado` se aplica igual, sobre el estado de hoy. Año
  inexistente: `404`.
- `GET /estudiantes/{estudiante_id}/detalles?anio_lectivo_id=` (opcional,
  paso 3.5b): notas, faltas, observaciones y deuda del año activo o del
  pedido, por el curso de cada clase; los productos de inventario salen igual
  siempre. Las faltas sin clase registrada (`asistencia.asignacion_id` nulo)
  se cuentan en el año activo, como antes, y no en otros años. Año
  inexistente: `404`.
- Desde el paso 2.4 del año lectivo la respuesta trae ademas
  `deuda_anios_anteriores`: la deuda de cada año anterior al que se mira, en
  que el estudiante tuvo matricula, aparte de `total_deuda`. Mismo formato que
  en cartera; vacia mientras haya un solo año.
- Notas por periodo (2026-10-31, `docs/funcionalidades/NOTAS_RESUMEN_ESTUDIANTE.md`):
  la respuesta suma dos campos, con los cuatro periodos y el año de una vez.
  - `notas_por_periodo`: `{"materias": [{"materia", "tipo_evaluacion",
    "periodos": {"1".."4": {"nota", "valoracion"} | null}, "anio": ... |
    null}], "promedio": {"1".."4", "anio": número | null}}`.
    - La nota de cada periodo es la del reporte parcial: la planilla
      vigente, sin columnas internas, sin ceros y ponderada si hay
      porcentajes activos.
    - En preescolar, además, la carita (`valoracion`).
    - "Año" es el promedio de los periodos con nota.
    - `promedio` solo cuenta las materias numéricas.
    - Las materias son las del curso del estudiante en ese año, las mismas
      del reporte parcial, en el orden del boletín.
  - `inasistencias_por_periodo`: `{"1".."4", "anio"}`. "Año" es el total de
    siempre.
  - `notas`, `promedio_general` e `inasistencias` conservan su forma. Desde
    esta fecha se llenan con "Todo el año": las materias numéricas con su
    nota del año a un decimal. Antes eran el promedio de todas las celdas del
    año juntas.
  - Preescolar ya no tumba la sección de notas: su `AVG(nota)` vacío hacía
    fallar `float(None)`.

## Cuentas

- `GET /estado-cuenta/curso/{curso_id}`
- `GET /estado-cuenta/estudiante/{estudiante_id}`

Año lectivo (fase 3, paso 3.4): `GET /estado-cuenta/curso/{curso_id}` toma
los estudiantes de las matriculas del curso y calcula deuda y pagos en el año
de ese curso; el año viaja en la misma consulta de estudiantes (sin consultas
nuevas). Con un curso del año activo, todo es como antes. El de estudiante
sigue en el año activo.

## Pagos

- `POST /pagos`
- `GET /pagos/vencidos/opciones/{estudiante_id}`
- `GET /pagos/adelanto/opciones/{estudiante_id}`
- `POST /pagos/adelanto`
- `GET /pagos/{estudiante_id}`
- `POST /pagos/{pago_id}/anular`

Notas:

- `POST /pagos` mantiene el flujo compatible de pagos pendientes, abonos,
  metodos mixtos y cargos de inventario.
- `GET /pagos/vencidos/opciones/{estudiante_id}` devuelve los conceptos
  mensuales con sus cuotas vencidas, periodo, fecha limite, valor y saldo.
- `POST /pagos` acepta opcionalmente `aplicaciones`, una lista con
  `tipo_pago_id`, `periodo` y `monto`; si se omite conserva el contrato
  anterior.
- El backend vuelve a calcular las cuotas, bloquea el concepto durante la
  transaccion y rechaza meses repetidos, pagados o con montos superiores al
  saldo.
- Los pagos antiguos sin periodo se distribuyen solo para visualizacion por
  FIFO, desde el mes vencido mas antiguo.
- Las opciones de adelanto incluyen solamente conceptos `mensual` asignados al
  estudiante y meses posteriores al actual, sin superar el `mes_final` del
  concepto dentro del mismo año.
- `POST /pagos/adelanto` recibe `estudiante_id`, `tipo_pago_id`,
  `fecha` opcional, una lista no vacia de `metodos` y exactamente una modalidad:
  `cantidad_meses` o `monto_distribuir`.
- Con `monto_distribuir`, el backend cubre en orden los meses futuros: completa
  cada saldo y aplica el remanente como abono parcial al siguiente periodo.
- Las opciones futuras incluyen `saldo` por mes y `total_disponible`; un mes
  parcialmente abonado continua disponible por el valor restante.
- Cada elemento de `GET /pagos/adelanto/opciones/{estudiante_id}` incluye
  `mes_final`. El servidor vuelve a calcular ese límite al registrar el pago,
  por lo que un cliente no puede adelantar un periodo posterior enviándolo por
  su cuenta.
- El cliente no define el valor de las cuotas: el backend usa la prioridad
  valor del estudiante > valor del curso > valor base y valida la suma de los
  metodos.
- Un mes activo no puede adelantarse dos veces. La anulacion libera sus meses
  y mantiene el pago visible como anulado.
- Año lectivo (fase 2, `docs/funcionalidades/ANIO_LECTIVO.md`): `POST /pagos` y
  `POST /pagos/adelanto` aceptan `anio_lectivo_id` opcional en el cuerpo, y
  `GET /pagos/vencidos/opciones/{estudiante_id}` y
  `GET /pagos/adelanto/opciones/{estudiante_id}` lo aceptan como parametro
  opcional. Sin el, todo es del año activo, como antes. Con el, el pago se
  guarda en ese año y la deuda, los meses vencidos y los adelantos se calculan
  con los conceptos y el curso de ese año. Cualquier estado vale: un pago se
  registra en el año de la deuda que salda, aunque este cerrado. Un año que no
  existe responde `400` con el mensaje. Con el año siguiente en preparacion, en
  diciembre se pueden adelantar sus meses.
- Los adelantos futuros cuentan como ingreso desde su registro, pero no reducen
  la cartera exigible antes del mes aplicado.
- Los endpoints de adelanto requieren la migracion
  `20260716_pagos_adelantados.sql`; si falta responden `409`.
- La aplicacion de pagos distintos o metodos mixtos sobre una cuota requiere
  `20260716_pagos_aplicaciones_parciales.sql`.
- La distribucion de subsidios reutiliza esa estructura y no requiere una
  migracion adicional.

## Cursos

- `POST /cursos`
- `GET /cursos`
- `GET /cursos?estado=activo|inactivo|todos`
- `PUT /cursos/{curso_id}`
- `PATCH /cursos/{curso_id}/estado`

Notas:

- Si no se envia `estado`, el listado devuelve cursos `activo`.
- `estado=todos` permite consultar historico/administrativo sin filtrar por
  estado operativo.
- `PATCH /cursos/{curso_id}/estado` recibe:

```json
{
  "estado": "inactivo"
}
```

- Estados validos: `activo`, `inactivo`.
- Un curso `inactivo` no puede usarse en nuevas asignaciones ni ediciones de
  asignaciones activas.
- `POST /cursos` y `PUT /cursos/{curso_id}` responden `409 Conflict` si ya
  existe un curso con el mismo `nombre` y `jornada`.
- `POST /cursos`, `PUT /cursos/{curso_id}` y el listado aceptan/devuelven
  `director_grupo_id` (opcional, `int` o `null`; referencia a `profesor.id`).
  Ver `docs/funcionalidades/DIRECTOR_GRUPO.md`.
- Año lectivo (fase 3, paso 3.3): `GET /cursos` acepta `?anio_lectivo_id=`
  opcional (con y sin `limit`). Sin el, devuelve solo los cursos del año
  activo; un año que no existe da `404`. `estado=todos` sigue sin filtrar por
  estado, dentro del año. El `409` de nombre repetido compara solo con los
  cursos del mismo año: el del año activo al crear, el del propio curso al
  editar. Mientras haya un solo año, todo responde igual que antes.
- Año lectivo (fase 5, paso 5.3): el cuerpo de `POST /cursos` acepta
  `anio_lectivo_id` positivo y opcional. Si se envía, el backend comprueba que
  exista y que el admin pueda editarlo; `cerrado` responde `409` y un id
  inexistente, `422`. Si se omite, el cuerpo, la respuesta y el camino del año
  activo son los anteriores. `PUT /cursos/{curso_id}` no acepta el campo: un
  curso no se mueve de año al editarlo.

## Profesores

- `POST /profesores`
- `GET /profesores`
- `GET /profesores?estado=activo|inactivo|todos`
- `PUT /profesores/{profesor_id}`
- `PATCH /profesores/{profesor_id}/estado`

Notas:

- Si no se envia `estado`, el listado devuelve profesores `activo`.
- `estado=todos` permite consultar historico/administrativo sin filtrar por
  estado operativo.
- `PATCH /profesores/{profesor_id}/estado` recibe:

```json
{
  "estado": "inactivo"
}
```

- Estados validos: `activo`, `inactivo`.
- Un profesor `inactivo` no puede iniciar sesion ni ser asignado/actualizado en
  asignaciones activas.
- `POST /profesores` y `PUT /profesores/{profesor_id}` responden
  `409 Conflict` si ya existe un profesor con el mismo documento o email.

## Asignaciones

- `GET /asignaciones/lista`
- `PUT /asignaciones/{asignacion_id}`
- `DELETE /asignaciones/{asignacion_id}` desactiva la asignacion; no borra historial academico.
- `GET /hora/horarios-admin`
- `POST /asignaciones`
- `GET /profesores/{profesor_id}/disponibilidad?dia=Lunes`
- `GET /profesores/{profesor_id}/cursos`
- `GET /cursos/{curso_id}/profesores`
- `GET /cursos/{curso_id}/orden-boletin`
- `PUT /cursos/{curso_id}/orden-boletin`
- `DELETE /asignaciones/{profesor_id}/{curso_id}` legacy; desactiva la asignacion activa mas reciente.
- `GET /mis-clases/{profesor_id}` devuelve el ID academico seguro de la clase y
  la `jornada` definida en el curso; si el puntero almacenado no coincide con
  el mismo profesor, curso y materia, el backend usa el ID real de la
  asignacion.

Año lectivo (fase 3, paso 3.2, de `docs/funcionalidades/ANIO_LECTIVO.md`):

- `GET /asignaciones/lista`, `GET /hora/horarios-admin` y `GET
  /profesores/{profesor_id}/disponibilidad` aceptan `?anio_lectivo_id=`
  opcional (entero mayor que 0). Sin el, devuelven o cuentan solo lo del año
  activo; con el, lo de ese año. Un año que no existe da `404` con `El año
  lectivo seleccionado no existe.`
- `GET /mis-clases/{profesor_id}` y `GET /profesores/{profesor_id}/cursos`
  devuelven solo clases y cursos del año activo, sin parametro: el profesor
  no ve otros años.
- Al crear o editar una asignacion, el cruce de horario solo se busca entre
  clases del mismo año que el curso de la asignacion: una clase de 2026 no
  choca con una de 2027 a la misma hora.
- Mientras haya un solo año, todas estas respuestas son las mismas de antes.

`GET /cursos/{curso_id}/orden-boletin` devuelve una fila por materia activa
del curso, agrupando varios horarios de la misma materia.

`PUT /cursos/{curso_id}/orden-boletin` recibe el orden completo:

```json
{
  "materias": [
    { "materia_id": 10 },
    { "materia_id": 12 }
  ]
}
```

El backend convierte la posicion de la lista en `orden_boletin = 1, 2, 3...`
y actualiza todos los horarios activos de esa materia en el curso.

## Notas y boletin legacy

- `POST /notas`
- `GET /notas/{estudiante_id}`
- `GET /boletin/{estudiante_id}`
- `GET /planilla/{asignacion_id}`
- `GET /boletin/detallado/{estudiante_id}`

## Planilla

- `POST /planilla/nota`
- `GET /planilla-excel/{asignacion_id}/{periodo}`
- `DELETE /planilla/tipo`
- `POST /planilla/subnotas`
- `PUT /planilla/subnotas/{subnota_id}`
- `DELETE /planilla/subnotas/{subnota_id}?asignacion_id=`
- `POST /planilla/subnotas/valores`
- `PUT /planilla/tipos/porcentaje`

**Subnotas** (desde el 2026-10-21, paso A1 de
`docs/funcionalidades/SUBNOTAS_PLANILLA.md`). Cada tipo de nota puede tener
subnotas, las mismas para todo el curso. La celda del estudiante es su
promedio y la calcula el servidor. Las cuatro rutas nuevas comprueban el
permiso de la asignación (`403`), el año lectivo (`409` o `403`) y, al
calificar, que el estudiante sea del curso (`403`), todo en una sola conexión.
Sus errores llegan como `{"detail": "<mensaje en español>"}`.

- `GET /planilla-excel/...`: **sin parámetros nuevos, la respuesta es la de
  siempre** (Asistencia usa esta ruta). Con `?con_subnotas=true` agrega
  `subnotas` (`{"<tipo>": [{"id": 7, "nombre": "Taller 1"}]}`, en orden de
  creación, con el nombre exacto de la columna) y, en cada estudiante,
  `subnotas` (`{"<subnota_id>": 4.0}` o el código de la carita). Una consulta
  más, en la misma conexión.
- `POST /planilla/subnotas` con `{asignacion_id, periodo, tipo_nota, nombre}`
  (nombre de 1 a 60, recortado): `201` con `{id, tipo_nota, nombre}`. `404` si
  el tipo no está en la planilla, `409` si el nombre ya existe en ese tipo
  (sin distinguir mayúsculas), `422` si el tipo ya tiene 20 subnotas o es una
  columna interna (`mas_alto`, `Desde React`).
- `PUT /planilla/subnotas/{subnota_id}` con `{asignacion_id, nombre}`:
  `{id, nombre}`. No cambia ninguna nota. `404` si la subnota no es de esa
  clase, `409` si el nombre ya existe.
- `DELETE /planilla/subnotas/{subnota_id}?asignacion_id=`: borra la subnota y
  sus calificaciones, y recalcula la celda de quien la tenía calificada.
  Devuelve `{mensaje, calificaciones_borradas, celdas: {"<estudiante_id>":
  {nota, valoracion}}}`. Una celda sin nada que promediar queda vacía.
- `POST /planilla/subnotas/valores` con `{asignacion_id, periodo, tipo_nota,
  estudiante_id, tipo_evaluacion, valores: {"<subnota_id>": valor | null}}`:
  **solo toca las subnotas que llegan** (`null` la vacía). Recalcula y guarda
  la celda con las dos sentencias del guardado a mano, y devuelve
  `{estudiante_id, tipo_nota, tipo_evaluacion, nota, valoracion, subnotas}`.
  El nivel del curso manda sobre `tipo_evaluacion`: preescolar caritas
  (`destacado`, `logrado`, `proceso`, `apoyo`) y primaria números de 1 a 5.
  `422` si una subnota no es de ese tipo o una calificación no sirve.
- La celda es el promedio de las subnotas calificadas: las vacías no cuentan.
  Se redondea a dos decimales, mitad hacia arriba (4.125 → 4.13). En
  preescolar es la carita más cercana al promedio, con empate hacia la más
  alta.

Dos cambios en las rutas que ya existían:

- `POST /planilla/nota` responde **`409`** con "Esta nota se calcula con sus
  subnotas. Cámbiala desde las subnotas." si el estudiante tiene subnotas
  calificadas en ese tipo. Sin subnotas, igual que siempre. Una consulta más.
- `DELETE /planilla/tipo` borra también las subnotas del tipo, en la misma
  transacción. Misma respuesta. Una consulta más.

**Porcentajes por tipo de nota** (desde el 2026-10-22, paso B2b de
`docs/funcionalidades/SUBNOTAS_PLANILLA.md`, parte B). **Todavía no cambian
ninguna nota**: el cálculo ponderado se conecta al boletín, al reporte parcial
y a los rankings en pasos posteriores (B2c y B2d). Los porcentajes son
opcionales y van por clase y periodo.

- `PUT /planilla/tipos/porcentaje` con `{asignacion_id, periodo, tipo_nota,
  porcentaje}`. `porcentaje` es obligatorio: un entero de 1 a 100, o `null`
  para quitarlo. Responde `{tipo_nota, porcentaje, suma, activos}`, con el
  nombre exacto de la columna, la suma de la clase y si los porcentajes quedaron
  activos (todos los tipos con el suyo y suma de 100). `404` si el tipo no está
  en la planilla; `422` si no es un entero de 1 a 100, si la suma pasaría de
  100 o si es una columna interna. Mismas guardias que las subnotas (permiso
  `403`, año lectivo `409` o `403`), en una conexión. La clase se bloquea
  mientras se comprueba la suma, para que dos guardados a la vez no pasen de
  100.
- `GET /planilla-excel/...?con_porcentajes=true` agrega `porcentajes`
  (`{"<tipo>": 40}`, con el nombre exacto de la columna) y
  `porcentajes_activos`. Es aparte de `con_subnotas`; se pueden pedir los dos.
  Sin el parámetro, la respuesta es la de siempre. Una consulta más.
- `DELETE /planilla/tipo` quita también el porcentaje del tipo, en la misma
  transacción. Misma respuesta. Una consulta más (ahora 5 el admin y 6 el
  profesor, con la guardia del año).

## Asistencia

- `POST /asistencia`
- `GET /asistencia/historial/{asignacion_id}/{periodo}`

`POST /asistencia` recibe un lote no vacio de una misma asignacion, fecha y
periodo. Cada estudiante puede aparecer una sola vez y `estado` acepta
`presente` o `ausente`. Al actualizar, reemplaza los registros de los
estudiantes enviados sin eliminar asistencia historica de estudiantes que ya
no forman parte del listado activo.

## Materias

- `POST /materia`
- `GET /materias`
- `GET /materias?estado=activo|inactivo|todos`
- `PUT /materias/{materia_id}`
- `PATCH /materias/{materia_id}/estado`

Notas:

- Si no se envia `estado`, el listado devuelve materias `activo`.
- `estado=todos` permite consultar historico/administrativo sin filtrar por
  estado operativo.
- `PATCH /materias/{materia_id}/estado` recibe:

```json
{
  "estado": "inactivo"
}
```

- Estados validos: `activo`, `inactivo`.
- Una materia `inactivo` no puede usarse en nuevas asignaciones ni ediciones de
  asignaciones activas.
- `POST /materia` y `PUT /materias/{materia_id}` responden `409 Conflict` si
  ya existe una materia con el mismo nombre. En ese caso `detail` es un texto.
- Año lectivo (paso 3.6, decision 12 de `docs/funcionalidades/ANIO_LECTIVO.md`):
  el boletin y los certificados leen el nombre al imprimir, asi que
  renombrar una materia cambia tambien los documentos de otros años. Si el
  nombre guardado cambia y la materia se dicta en mas de un año, o en un año
  `cerrado` o `reabierto`, `PUT /materias/{materia_id}` **no guarda** y
  responde `409` con un objeto:

```json
{
  "detail": {
    "codigo": "materia_usada_en_otro_anio",
    "mensaje": "Esta materia se usa en 2026. Si cambias el nombre, también cambiará en los boletines y certificados de 2026."
  }
}
```

  Para guardar igual, el frontend reenvia el mismo cuerpo con
  `"confirmar_cambio_nombre": true` (solo el booleano `true` confirma). El
  nombre repetido se informa antes que este aviso. Con un solo año nunca
  avisa. Editar cuesta una consulta mas (3 en vez de 2), salvo con la
  confirmacion.

## Observaciones

- `POST /observaciones`
- `GET /observaciones/{estudiante_id}/{asignacion_id}/{periodo}`

`POST /observaciones` acepta `conductual`, `cognitivo` y `lenguaje` como textos
opcionales con valor vacio por defecto, pero exige contenido en al menos una
dimension. Los textos se normalizan antes de crear o actualizar el registro.

## Observador

Ver `docs/funcionalidades/OBSERVADOR_ESTUDIANTE.md`.

- `GET /observador/mis-estudiantes`
- `GET /observador/{estudiante_id}?periodo=`
- `POST /observador`
- `PUT /observador/{anotacion_id}`

Año lectivo (fase 3, paso 3.5b): `GET /observador/{estudiante_id}` devuelve
las anotaciones del año activo (antes, todas; con un solo año es lo mismo). El
admin puede pedir otro con `?anio_lectivo_id=` (y el `nivel` sale del curso de
ese año); un profesor que pida otro año recibe `403` con `Solo se puede
consultar el año lectivo activo.`; un año que no existe, `404`.

### Firma del acudiente (2026-10-27)

Ver `docs/funcionalidades/FIRMA_OBSERVADOR.md`.

- `POST /observador/anotaciones/{anotacion_id}/firma`: el acudiente firma una
  anotacion en pantalla. Cuerpo: `firmante_nombre`, `firmante_tipo_documento`,
  `firmante_documento`, `firmante_parentesco`, `imagen` (PNG en base64, con o
  sin `data:image/png;base64,`, maximo 100 KB) y `version` (la que trajo la
  bitacora). Quien la toma, la fecha y la hora no se aceptan del cuerpo: salen
  del token y del servidor. Respuestas: `201` con la firma sin imagen y con
  `firmante_documento_enmascarado`; `403` si no es el autor, el director de
  grupo del alumno ni el admin, o fuera de su año; `404` si la anotacion no
  existe; `409` si ya esta firmada, si cambio desde que se mostro o si su año
  esta cerrado; `422` si los datos o la imagen no sirven.
- `POST /observador/{estudiante_id}/firmas` (ampliacion del 2026-10-27): **una
  sola firma para varias anotaciones** del estudiante, las pendientes de un
  periodo. Cuerpo: los mismos datos de quien firma y la `imagen`, mas
  `anotaciones: [{id, version}]` (de 1 a 50, sin repetidas), que es la lista
  exacta que la pantalla mostro. **Todas o ninguna**: cada una pasa por la
  misma regla que la firma individual, y si una falla no se firma ninguna.
  Respuestas: `201` con la lista de firmas creadas; `404` si alguna no existe o
  no es de ese estudiante; `403`/`409` como la individual, con mensajes en
  plural. Lee todas en una consulta (`FOR UPDATE`) y las guarda con un solo
  `INSERT`.
- `GET /observador/{estudiante_id}/firmas?periodo=&anio_lectivo_id=`: las
  firmas, con la imagen (`data:` lista para un `<img>`) y el documento
  completo, de las anotaciones que devuelve la bitacora con los mismos
  filtros. Para imprimir. Misma puerta que la bitacora.
- `GET /observador/{estudiante_id}/firmantes-sugeridos`: el padre y la madre
  de la ficha (`parentesco`, `nombre`, `tipo_documento`, `documento`), solo los
  que tienen nombre. Para el admin, el director de grupo o un profesor con
  alguna anotacion del alumno este año; otro profesor recibe `403`.
- `GET /observador/{estudiante_id}`: cada anotacion suma `version`,
  `puede_firmar` (calculado con las mismas reglas que la firma) y `firma`
  (`null` o `firmante_nombre`, `firmante_tipo_documento`,
  `firmante_documento_enmascarado`, `firmante_parentesco`, `firmada_en`,
  `tomada_por_nombre` e `integra`). La imagen no viaja aqui. Sigue siendo una
  sola consulta.
- `PUT /observador/{anotacion_id}`: `409` si la anotacion ya esta firmada
  (`Esta anotacion ya tiene la firma del acudiente y no se puede editar...`).
  Le cuesta una consulta mas: bloquear la anotacion y mirar si tiene firma.
- No existe ruta para editar ni borrar una firma.

## Plan de clases

- `POST /plan-de-clases`
- `GET /plan-de-clases/{asignacion_id}`
- `DELETE /plan-de-clases/{plan_id}/imagen`
- `GET /admin/plan-de-clases`
- `GET /admin/plan-de-clases/{plan_id}`
- `PATCH /admin/plan-de-clases/{plan_id}/revision`
- `POST /admin/plan-de-clases/{plan_id}/observaciones`
- `GET /plan-de-clases/{plan_id}/observaciones`
- `PATCH /plan-de-clases/{plan_id}/observaciones/{observacion_id}/vista`
- `GET /notificaciones/planeadores`
- `DELETE /admin/plan-de-clases/{plan_id}/imagen`
- `GET /plan-de-clases/{asignacion_id}/anio-anterior`
- `GET /plan-de-clases/{asignacion_id}/anio-anterior/{plan_id}`
- `GET /plan-de-clases/cuadros`
- `PUT /admin/plan-de-clases/cuadros`

Notas:

- `POST /plan-de-clases` exige `asignacion_id`, `periodo` y `fecha`. Acepta
  `version_esperada`: el frontend envía `0` al crear o la `version_revision`
  cargada al actualizar.
- Si el plan cambió desde que el profesor lo abrió, `POST /plan-de-clases`
  responde `409` con `detail.mensaje` y `detail.version_actual`, sin modificar
  el registro. Los archivos nuevos recibidos en esa solicitud se eliminan.
- Omitir `version_esperada` conserva compatibilidad temporal con consumidores
  anteriores, aunque los clientes interactivos deben enviarla para quedar
  protegidos contra sobrescrituras.
- `GET /plan-de-clases/{asignacion_id}` acepta `fecha` para consultar un día
  exacto. Sin `fecha`, admite paginación opcional con `limit` entre 1 y 50 y
  `offset` mayor o igual que cero; si se omite `limit`, conserva la lista
  completa por compatibilidad.
- Las cajas de texto (`unidad`, `proposito`, `clase`, `estandar`, `dba`, `competencias`, `actividad_casa` y `tema`) son opcionales, aceptan texto largo y se guardan como texto vacio si no se envian.
- Los adjuntos `imagen1` e `imagen2` tambien son opcionales. Cada uno acepta
  una imagen PNG, JPG, JPEG o WEBP de hasta 5MB, o un PDF de hasta 15MB. El
  PDF ademas debe empezar por la firma `%PDF-`: no basta con renombrar el
  archivo. Ambos se guardan en el mismo campo y se sirven por
  `GET /uploads/{ruta}` con su propio tipo de contenido.
- Los planes retornan `estado_revision`, `version_revision`, fechas de
  seguimiento y contadores de observaciones.
- `GET /admin/plan-de-clases` acepta el filtro opcional `estado_revision`:
  `pendiente`, `visto`, `con_observaciones` o `revisado`. Para la bandeja
  consolidada, `pendiente` agrupa también el estado interno `visto` y
  `revisado` agrupa también `con_observaciones`; los dos valores internos se
  conservan por compatibilidad.
- Año lectivo (fase 3, paso 3.5b): `GET /admin/plan-de-clases` devuelve los
  planes de cursos del año activo, o del de `?anio_lectivo_id=`. No valida que
  el año exista: uno inexistente da la lista vacia.
- Marcar un plan como visto o revisado requiere `{ "estado", "version" }`.
  Cuando `estado` es `revisado`, admite además `comentario` opcional de hasta
  3000 caracteres. Si se envía, el comentario y la aprobación se guardan en la
  misma transacción y generan la notificación del profesor.
- Crear una observacion requiere `{ "observacion", "version" }`; el texto se
  normaliza y admite hasta 3000 caracteres.
- Si la version enviada por administracion ya cambio, el backend responde
  `409` con `version_actual` y no guarda la accion.
- Un nuevo guardado del profesor aumenta `version_revision` y normalmente
  devuelve el plan a `pendiente`, sin eliminar el historial de observaciones.
  Si la versión estaba en `con_observaciones`, la corrección conserva ese
  estado interno y no genera un nuevo pendiente ni otra notificación para
  administración. Si ya estaba en `revisado`, también conserva ese estado
  tenga o no observaciones y no vuelve a la bandeja pendiente.
- Solo el profesor propietario puede confirmar la lectura de una observacion;
  administracion conserva acceso de lectura al historial completo.
- `GET /notificaciones/planeadores` admite `limit` entre 1 y 20 (8 por
  defecto). Para administracion retorna un elemento por profesor con
  `profesor_id`, `profesor`, `cantidad` y `creada_at`; `total_no_leidas` cuenta
  todas las planeaciones pendientes y `total_profesores` los docentes
  involucrados. Para profesor retorna sus observaciones administrativas aun no
  leidas.
- Abrir o revisar el detalle administrativo marca como leidos los eventos del
  plan hasta esa version. Para el profesor, una observacion solo deja de estar
  pendiente cuando confirma su lectura mediante el endpoint `vista`.

Usar un plan del año pasado como base (año lectivo, fase 7, paso 7.2; ver
`docs/funcionalidades/ANIO_LECTIVO.md`). Las dos rutas solo leen; el plan
nuevo se guarda con `POST /plan-de-clases`, con fecha nueva, en `pendiente` y
sin evidencias:

- `GET /plan-de-clases/{asignacion_id}/anio-anterior` responde una lista de
  `{"id", "fecha", "periodo", "unidad", "tema"}`, por fecha (la mas antigua
  primero): los planes de la misma materia en el curso del que se copio el
  curso de la clase (`cursos.curso_origen_id`), de cualquier profesor y de
  cualquier estado de revision. Sin origen (curso creado desde cero o materia
  que no se dictaba alli), lista vacia.
- `GET /plan-de-clases/{asignacion_id}/anio-anterior/{plan_id}` responde
  `{"id", "unidad", "proposito", "clase", "estandar", "dba", "competencias",
  "actividad_casa", "tema"}`, cada texto vacio como `""`. Sin fecha, sin
  evidencias, sin periodo (el formulario conserva el que eligio el profesor) y
  sin estado de revision. `403` "Ese plan no es del año pasado de esta
  clase." si el plan no es del origen de esa clase o no existe.
- En las dos: `403` "No tienes permisos para esta asignación" si el profesor
  no dicta la clase, y la guardia del año sobre la clase (`409` año cerrado,
  `403` profesor fuera del año activo), porque sirven para crear un plan en
  ella. El cliente nunca manda ids de clases del año pasado.

### Nombres de los cuadros (2026-10-31)

Ver `docs/funcionalidades/NOMBRES_CUADROS_PLAN.md`. Viven en su propio router
(`app/routes/cuadros_plan_de_clases.py`), incluido **antes** que el del plan
para que `GET /plan-de-clases/{asignacion_id}` no atrape
`/plan-de-clases/cuadros`. Sin guardia de año lectivo: los nombres son del
colegio.

- `GET /plan-de-clases/cuadros`: cualquier sesión del colegio (profesor o
  admin). Responde `{"cuadros": [{"clave", "nombre", "ayuda"}]}` con **solo
  los cuadros renombrados**, en el orden del formulario. Lista vacía: todos
  con su nombre original, que vive en el frontend.
- `PUT /admin/plan-de-clases/cuadros`: solo admin (`403` al profesor, sin
  abrir la base). Cuerpo `{"cuadros": [{"clave", "nombre", "ayuda"}]}` con la
  lista **completa** de cuadros renombrados, de 0 a 9; los textos llegan
  recortados. Reemplaza todo en una transacción (bloquear, borrar e insertar)
  y responde como el `GET`. Lista vacía: vuelve a los originales.
- Claves: `unidad`, `estandar`, `tema`, `proposito`, `clase`, `dba`,
  `actividad_casa`, `imagen1` e `imagen2`. `competencias` no se renombra.
- `422` con un mensaje en `detail`, sin abrir la base: "Ese cuadro no existe
  en el plan de clase.", "Un cuadro aparece dos veces.", "Cada cuadro necesita
  un nombre.", "El nombre de un cuadro no puede pasar de 60 caracteres.", "El
  texto de ayuda no puede pasar de 150 caracteres." y "Los archivos no llevan
  texto de ayuda.". Más de 9 cuadros da el `422` del validador.
- Si dos admins guardan a la vez, gana el último. Que dos cuadros no se llamen
  igual lo revisa el frontend.

## Planeador anual

- `GET /planeador-anual/{asignacion_id}/{periodo}`
- `PUT /planeador-anual/{asignacion_id}/{periodo}`

Notas:

- El `PUT` recibe una lista cuya posicion determina el `slot` de cada fila.
- `unidad_tematica`, `estandar_competencia`, `contenido` y
  `actividades_recursos` son opcionales entre si, pero una fila con al menos
  uno de ellos exige `fecha` como fecha limite.
- Una fila con fecha y sin contenido se rechaza.
- Las filas completamente vacias son validas y eliminan el registro existente
  de ese `slot`, si lo habia.
- Los textos se recortan y una fecha vacia se normaliza a `null` antes de
  validar.
- Este contrato usa la tabla existente y no requiere migracion.

Traer el planeador del año pasado (año lectivo, fase 7, paso 7.1; ver
`docs/funcionalidades/ANIO_LECTIVO.md`):

- `GET /planeador-anual/{asignacion_id}/anio-anterior` responde
  `{"hay_origen": bool, "planeador_vacio": bool, "puede_traer": bool}`.
  `hay_origen`: hay algo escrito en el planeador de esa materia en el curso
  del que se copio el curso de la clase (`cursos.curso_origen_id`), de
  cualquier profesor. `planeador_vacio`: el planeador de la clase no tiene
  ninguna fila, en ningun periodo. `puede_traer` lo decide el backend: las dos
  anteriores y que la guardia del año deje guardar a este usuario. El
  frontend muestra el boton solo con `puede_traer`.
- `POST /planeador-anual/{asignacion_id}/anio-anterior`, sin cuerpo, copia
  ese planeador a la clase y responde `{"message": "...", "filas_copiadas":
  n}`. Copia periodo, slot y los cuatro textos; la `fecha` queda `null` (al
  guardar un periodo con el `PUT`, cada fila con contenido vuelve a exigir su
  fecha). Si la materia tuvo dos profesores en 2026, cada periodo sale entero
  de la clase mas reciente que escribio algo en el. Una fila sin texto no
  cuenta.
- Errores del `POST`, con `detail` de texto listo para mostrar: `409` si el
  planeador de la clase ya tiene alguna fila (nunca sobrescribe; tambien si
  llegan dos clics a la vez); `404` si no hay nada que traer o la clase no
  existe; y los de la guardia del año (`409` año cerrado, `403` profesor fuera
  del año activo). `403` si el profesor no dicta la clase.
- Las dos rutas van declaradas antes de las de un periodo: si no,
  `anio-anterior` se leeria como periodo y daria `422`.

## Dashboard

- `GET /dashboard/cumpleanos/admin?dias=7`
- `GET /dashboard/cumpleanos/profesor/{profesor_id}?dias=7`
- `GET /dashboard/inasistencias/{profesor_id}`
- `GET /dashboard/notas-bajas/{profesor_id}?curso_id={curso_id}&asignacion_id={asignacion_id}`
- `GET /dashboard/notas-altas/{profesor_id}?curso_id={curso_id}&asignacion_id={asignacion_id}`
- `GET /dashboard/ranking/{asignacion_id}/{periodo}`
- `GET /dashboard/ranking-mejor/{asignacion_id}/{periodo}`

Notas:

- `/dashboard/cumpleanos/admin` es solo para rol admin y devuelve estudiantes
  activos que cumplen anos dentro del rango solicitado con fecha local
  `America/Bogota`.
- `/dashboard/cumpleanos/profesor/{profesor_id}` valida el scope del profesor
  y devuelve solo estudiantes activos de cursos asignados al profesor.
- `dias` es opcional, por defecto `7`, y acepta valores de `0` a `31`.
- `/dashboard/notas-bajas/{profesor_id}` y `/dashboard/notas-altas/{profesor_id}` validan que el profesor solo consulte su propio scope.
- `curso_id` y `asignacion_id` son filtros opcionales para rendimiento; si se envian, el backend valida que pertenezcan al profesor.
- `/dashboard/inasistencias/{profesor_id}` cuenta solo las faltas de cursos
  del año activo (año lectivo, fase 3, paso 3.2). Los demas paneles del
  profesor ya parten de un curso o del curso actual del estudiante.
- **Porcentajes por tipo de nota** (desde el 2026-10-22, paso B2d de
  `docs/funcionalidades/SUBNOTAS_PLANILLA.md`, PB7): si la clase tiene sus
  porcentajes **activos** en ese periodo, los dos rankings usan la nota
  ponderada de cada estudiante, redondeada a dos decimales mitad hacia arriba
  (la consulta de siempre trunca), con el mismo corte en 3.0 y el mismo orden.
  Solo notas numéricas, como siempre: un estudiante solo con caritas no
  entra. Sin porcentajes activos, la consulta de siempre. Una consulta más
  sin porcentajes; con porcentajes activos, tres en vez de la del ranking.
  `notas-bajas` y `notas-altas` (que mezclan todo el año) no cambian.

## Usuarios

- `POST /usuarios`
- `GET /usuarios`
- `PUT /usuarios/{user_id}`
- `DELETE /usuarios/{user_id}`

## Reportes

- `GET /reportes/general`
- `GET /reportes/estado-cuenta/{curso_id}`
- `GET /reportes/ingresos-mes/{mes}`
- `GET /reportes/ingresos-rango`
- `GET /reportes/egresos-rango`

Año lectivo (fase 3, paso 3.3): en `GET /reportes/general`, `total_cursos` y
`estudiantes_por_curso` cuentan solo los cursos del año activo. Los demas
totales no cambian (dinero y egresos van por fecha).

Año lectivo (fase 3, paso 3.4): `GET /reportes/estado-cuenta/{curso_id}` toma
los estudiantes de las matriculas del curso y calcula en el año de ese curso.
Para saberlo hace una consulta mas al empezar (6/15/15 -> 7/16/16, aceptado por
el usuario el 2026-10-02). Con un curso del año activo, el resto es como antes.

## Tipos de pagos

- `POST /tipos-pagos`
- `GET /tipos-pagos`
- `PUT /tipos-pagos/{id}`
- `DELETE /tipos-pagos/{id}` bloqueado: responde `405 Method Not Allowed`.
- `GET /tipos-pagos/detallado`
- `GET /tipos-pagos/{id}/detalle`
- `PUT /tipos-pagos/{id}/configuracion`
- `GET /tipos-pagos/{id}/cursos`
- `PUT /tipos-pagos/{id}/cursos`
- `DELETE /tipos-pagos/{id}/cursos/{curso_id}`
- `GET /estudiantes/{estudiante_id}/valores-pago-personalizados`
- `PUT /estudiantes/{estudiante_id}/valores-pago-personalizados/{tipo_pago_id}`
- `DELETE /estudiantes/{estudiante_id}/valores-pago-personalizados/{tipo_pago_id}`
- `GET /estudiantes/{estudiante_id}/valores-pago`

`GET /estudiantes/{estudiante_id}/valores-pago?anio_lectivo_id=` (año
lectivo, 2026-10-12; solo admin, solo lee): lo que se le cobra al estudiante en
ese año, concepto por concepto. Sin el año, el activo. Son los mismos conceptos
que cuenta el cálculo de deudas (activos, no opcionales y con precio en el curso
de su matrícula de ese año), **aunque todavía no deba nada**: a diferencia de
`GET /estudiantes/{id}/deudas`, que solo trae conceptos con deuda, aquí sale la
mensualidad de un año que no ha empezado. Los valores salen de la regla de los
cobros (`_valor_unitario_concepto`), así que coinciden con lo que se cobra.

```json
{
  "estudiante_id": 7,
  "anio_lectivo_id": 3,
  "curso_id": 20,
  "conceptos": [
    {
      "tipo_pago_id": 12,
      "nombre": "MENSUALIDAD",
      "tipo_cobro": "mensual",
      "precio_curso": 200000.0,
      "valor_personalizado": 180000.0,
      "motivo": "Beca parcial",
      "valor_a_pagar": 180000.0
    }
  ]
}
```

`precio_curso` es el precio del curso (o el valor base del concepto si el
curso lo tiene en `0`); `valor_personalizado` y `motivo` son `null` sin valor
personalizado; `valor_a_pagar` es lo que paga. Un año inexistente o un
estudiante sin matrícula en ese año responden `404` con el mensaje en `detail`.
Para guardar o quitar un valor se siguen usando `PUT` y `DELETE` de
`valores-pago-personalizados`.

Desde la fase 5.6, el `GET` de valores personalizados acepta
`?anio_lectivo_id=`. Si se omite, conserva el año activo. La lectura toma el
curso de `matriculas` para ese mismo año. Al guardar con `PUT`, el año sale del
concepto y el precio por curso se valida contra la matrícula del estudiante en
ese año; un estudiante sin esa matrícula recibe `400` y no se escribe nada.

Configuracion avanzada completa de ejemplo (todos los campos son opcionales en
una actualizacion parcial):

```json
{
  "descripcion": "Pensión ordinaria",
  "tipo_cobro": "mensual",
  "fecha_limite": null,
  "dia_limite_mes": 5,
  "dias_gracia": 0,
  "mora_tipo": "porcentaje",
  "mora_valor": 0,
  "mes_inicial": 2,
  "mes_final": 11,
  "frecuencia_meses": 1,
  "generacion_automatica": false,
  "activo": true
}
```

`mes_final` forma parte de las respuestas detalladas y del cuerpo opcional de
`PUT /tipos-pagos/{id}/configuracion`. Acepta enteros entre `1` y `12`, usa
diciembre (`12`) por defecto y, para una configuracion efectiva de tipo
`mensual`, debe ser mayor o igual que `mes_inicial` cuando este exista. La regla
no se aplica a conceptos `unico`, `anual` u `opcional`; en los mensuales limita
cartera, cuotas vencidas y adelantos, sin cambiar ni eliminar pagos historicos.

Una pareja mensual invalida enviada junto con `tipo_cobro: "mensual"` falla en
validacion HTTP. El controlador bloquea la fila y combina los campos enviados
con los ya guardados; si esa configuracion efectiva queda invertida, el endpoint
responde `400` con
`El mes final no puede ser anterior al mes inicial.`. Si se intenta guardar
`mes_final` antes de aplicar `20260910_tipos_pagos_mes_final.sql`, responde
`409` e indica el comando de migracion. Las lecturas conservan `12` como
fallback mientras la columna no exista.

Año lectivo (fase 3, paso 3.3; cada concepto es de un año, decision 17):

- `GET /tipos-pagos` y `GET /tipos-pagos/detallado` aceptan
  `?anio_lectivo_id=` opcional. Sin el, devuelven solo los conceptos del año
  activo; un año que no existe da `404`.
- El `409` de nombre repetido de `POST` y `PUT /tipos-pagos` compara solo con
  los conceptos del mismo año: el activo al crear, el del propio concepto al
  editar.
- `PUT /tipos-pagos/{id}/cursos` responde `400` si algun curso es de otro año
  que el concepto, con el mensaje `Estos cursos no son del año lectivo del
  concepto: <nombres>.`, y no guarda nada. La comprobacion va en la misma
  consulta que ya miraba si el concepto existe.
- Mientras haya un solo año, todo responde igual que antes.
- Fase 5, paso 5.3: el cuerpo de `POST /tipos-pagos` acepta
  `anio_lectivo_id` positivo y opcional. Si se envía, valida existencia y que
  el año sea editable para el admin; `cerrado` responde `409` y un id
  inexistente, `422`. Si se omite, conserva la llamada, el SQL y la respuesta
  anteriores del año activo. `PUT /tipos-pagos/{id}` no acepta el campo y no
  mueve el concepto de año.

Valores personalizados por estudiante:

```json
{
  "valor": 120000,
  "motivo": "Acuerdo individual",
  "activo": true
}
```

Uso:

- Permiten definir una excepcion individual para un concepto sin modificar el valor base ni el valor asignado al curso.
- El backend exige que el concepto este asignado al curso del estudiante antes de guardar la excepcion.
- `DELETE` desactiva la excepcion vigente; no elimina historico fisicamente.
- Si falta la migracion `20260713_tipos_pagos_estudiantes.sql`, estos endpoints responden `409` con instruccion operativa.

## Inventario

- `GET /inventario`
- `GET /inventario?estado=activo|inactivo|todos`
- `POST /inventario`
- `PUT /inventario/{item_id}`
- `PATCH /inventario/{item_id}/estado`
- `DELETE /inventario/{item_id}` desactiva el producto; no borra historial de
  ventas.

Notas:

- Si no se envia `estado`, el listado devuelve productos `activo`.
- `estado=todos` permite consultar historico/administrativo sin filtrar por
  estado operativo.
- `PATCH /inventario/{item_id}/estado` recibe:

```json
{
  "estado": "inactivo"
}
```

- Estados validos: `activo`, `inactivo`.
- Un producto `inactivo` no aparece para nuevas ventas y el backend rechaza
  intentos de venderlo por API.

## Egresos

Router prefix: `/api/egresos`

- `GET /api/egresos/`
- `GET /api/egresos/?fecha_desde=YYYY-MM-DD&fecha_hasta=YYYY-MM-DD`
- `POST /api/egresos/`
- `PUT /api/egresos/{egreso_id}` solo para egresos con `origen = manual`.
- `DELETE /api/egresos/{egreso_id}` bloqueado: los egresos no se eliminan
  fisicamente.

Notas:

- Si no se envian fechas, el backend devuelve solo los egresos del dia actual.
- Si se envia solo `fecha_desde`, se consulta ese dia.
- Si se envian `fecha_desde` y `fecha_hasta`, se consulta el rango inclusivo.
- `POST /api/egresos/` exige `concepto`, `categoria` y `monto > 0`.
- Si el egreso es invalido, responde `400` con el detalle de validacion.
- El listado devuelve `origen` y `editable`; los egresos automaticos de nomina
  no son editables desde este modulo.
- Si se intenta editar un egreso no manual, responde `403`.

## Prestamos

Router prefix: `/api/prestamos`

- `GET /api/prestamos/`
- `GET /api/prestamos/?profesor_id={profesor_id}`
- `POST /api/prestamos/`
- `PUT /api/prestamos/{prestamo_id}/estado` solo permite saldar con
  `{"estado": "Pagado"}`.
- `DELETE /api/prestamos/{prestamo_id}` bloqueado: los prestamos no se
  eliminan fisicamente.

Notas:

- `POST /api/prestamos/` exige profesor valido, `monto > 0` y estado inicial
  `Pendiente`.
- Si el prestamo es invalido, responde `400` con el detalle de validacion.
- Los prestamos creados se conservan para trazabilidad y solo pueden pasar a
  `Pagado`.

## Ventas

Router prefix: `/api/ventas`

- `GET /api/ventas/`
- `GET /api/ventas/?limit=50&offset=0&busqueda=<texto>&estudiante_id=<id>&estado=<estado>`
- `GET /api/ventas/pendientes/{estudiante_id}`
- `POST /api/ventas/`
- `POST /api/ventas/{venta_id}/anular`
- `DELETE /api/ventas/{venta_id}` bloqueado: usar anulacion.

Notas:

- El listado conserva compatibilidad: sin `limit` devuelve lista simple; con
  `limit` devuelve respuesta paginada.
- `POST /api/ventas/` exige detalles de inventario y valida stock/valores en el
  controlador.
- La anulacion conserva trazabilidad, devuelve stock y anula pagos asociados
  cuando aplica.

## Listas de seguimiento

Registro libre del administrador por curso: columnas con el nombre que el elija
y, por alumno, un check mas una nota corta. Router admin-only. Detalle completo
en `docs/funcionalidades/LISTAS_SEGUIMIENTO.md`.

- `GET /listas-seguimiento/{curso_id}`
- `POST /listas-seguimiento/{curso_id}/columnas`
- `DELETE /listas-seguimiento/{curso_id}/columnas/{columna_id}`
- `POST /listas-seguimiento/{curso_id}/marcas`
- `POST /listas-seguimiento/columnas-en-todos-los-cursos`

`GET /listas-seguimiento/{curso_id}` devuelve columnas, alumnos y marcas en una
sola respuesta, para pintar la pantalla con una peticion:

```jsonc
{
  "curso_id": 12,
  "columnas": [{"id": 5, "nombre": "Asistio a la cumbre"}],
  "estudiantes": [
    {
      "estudiante_id": 101, "nombre": "Juan", "apellido": "Perez",
      "marcas": {"5": {"marcado": true, "nota": "Llego tarde"}}
    }
  ]
}
```

Las claves de `marcas` son el id de columna como texto. Una celda sin fila no
aparece; el frontend le pone el default (`marcado: false`, `nota: ""`), igual
que ya hace con las notas ausentes de la planilla. `404` si el curso no existe.

Año lectivo, paso 6.4b: los `estudiantes` son los **matriculados en ese
curso**, de todos los estados, y `POST .../marcas` valida contra esa misma
lista. Así un curso de un año pasado o en preparación trae a los suyos (antes
salía vacío fuera del año activo). En un curso del año activo la lista es la
misma de siempre.

`POST /listas-seguimiento/{curso_id}/columnas` recibe `{"nombre": "..."}` y
responde `201` con `{"id", "nombre"}`, el nombre ya recortado. `404` si el
curso no existe, `409` si ese curso ya tiene una columna con ese nombre
ignorando mayusculas y espacios repetidos, `422` si el nombre viene vacio o
pasa de 100 caracteres.

`DELETE /listas-seguimiento/{curso_id}/columnas/{columna_id}` borra la columna
y sus marcas en cascada. El borrado es definitivo, sin baja logica. `404` si la
columna no existe **o es de otro curso**: las dos cosas responden igual.

`POST /listas-seguimiento/{curso_id}/marcas` recibe una lista pelada, el mismo
formato que `POST /asistencia`:

```jsonc
[{"columna_id": 5, "estudiante_id": 101, "marcado": true, "nota": "Llego tarde"}]
```

`marcado` es obligatorio; `nota` puede faltar o venir `null`, y las dos formas
se guardan como cadena vacia. Responde `{"mensaje", "guardadas"}` con el numero
de celdas escritas. `422` si el lote viene vacio, si trae la misma celda dos
veces, si una nota pasa de 240 caracteres, o si alguna celda referencia una
columna o un alumno que no son de ese curso. El lote se valida entero antes de
escribir nada: o entra todo o no entra nada.

`POST /listas-seguimiento/columnas-en-todos-los-cursos` recibe
`{"nombre": "..."}`, **sin curso en la ruta**: no actua sobre un curso sino
sobre todos. Crea la columna en cada curso activo que aun no la tenga y
responde `{"creadas": 9, "omitidas": 16, "total": 25}`.

Tres cosas que no son evidentes:

- **Responde 200, no 201**, al contrario que el alta de una sola columna. Que
  no cree ninguna es un resultado valido y frecuente -pasa siempre que todos
  los cursos ya la tenian-, y un 201 fijo estaria mintiendo la mitad de las
  veces.
- **Los cursos que ya la tienen se saltan en silencio**, no dan error. Eso
  vuelve el endpoint repetible: un curso creado despues se rellena volviendo
  a llamarlo con el mismo nombre.
- **"Activo" significa lo mismo que en `GET /cursos`**:
  `COALESCE(LOWER(estado), 'activo') = 'activo'`, o sea que un curso con
  `estado` nulo **si** cuenta. Asi los cursos sobre los que actua son
  exactamente los que el admin ve en su selector.
- **Solo en los cursos de un año** (año lectivo, fase 3, paso 3.3): el de
  `?anio_lectivo_id=` o, sin el, el activo. Un año que no existe da `404`
  sin escribir nada.

Nacen columnas **independientes**, una por curso, no una compartida: son
copias con el mismo nombre y a partir de ahi cada una va por su lado. No hay
tablas nuevas. El `409` de este endpoint no es "ya existe esa columna" sino la
carrera entre dos peticiones simultaneas, y reintentar funciona.

## Auth SaaS

### POST /auth/cambiar-password

Protegido por sesion normal de admin de colegio.

Body:

```json
{
  "password_actual": "Temporal123",
  "password_nueva": "NuevaClave123"
}
```

Respuesta:

```json
{
  "mensaje": "Password actualizada",
  "debe_cambiar_password": false
}
```

Uso:

- Primer ingreso del admin inicial creado por super admin.
- Apaga `usuarios.debe_cambiar_password`.
- Rechaza passwords debiles o iguales a la temporal.

## Super Admin SaaS

- `GET /super-admin/tenants` devuelve `estado` efectivo y `estado_manual`.
- `POST /super-admin/tenants` crea admin inicial con
  `debe_cambiar_password = TRUE` y registra evento `tenant_creado`.
- `PATCH /super-admin/tenants/{tenant_id}/estado` cambia estado manual y
  registra motivo/auditoria.
- `GET /super-admin/tenants/{tenant_id}/estado-auditoria` lista los ultimos
  cambios de estado del tenant.
- `POST /super-admin/tenants/{tenant_id}/pagos` registra el pago de un colegio
  moviendo su fecha de proximo pago (desde el 2026-10-26). Es lo que reactiva a
  un colegio que pago: el estado efectivo sale de esa fecha, y un estado manual
  `activo` no le gana a una fecha vencida.

  ```json
  { "fecha_proximo_pago": "2026-12-01", "nota": "Transferencia" }
  ```

  - `fecha_proximo_pago` es obligatoria y debe ser posterior a hoy (fecha de
    Colombia) y no anterior al inicio de la suscripcion; `nota` es opcional.
  - Responde el tenant con la misma forma que el listado, ya con su `estado`
    recalculado.
  - Registra el evento `pago_registrado` en `public.tenant_eventos_auditoria`,
    con las dos fechas y la nota. La misma fecha que ya tenia no cambia nada ni
    deja registro.
  - Errores: 404 si el colegio no existe; 422 si la fecha es invalida, de hoy o
    anterior, anterior al inicio, o si el colegio no tiene suscripcion.
  - No guarda el monto pagado.

## Nomina

Router incluido con prefix `/api/nomina`

- `GET /api/nomina/empleados`
- `GET /api/nomina/historial`
- `POST /api/nomina/pagar`

## Boletines

Router prefix: `/boletines`

- `POST /boletines/guardar`
- `GET /boletines/referencia/{asignacion_id}/{periodo}`
- `GET /boletines/admin/generar/{estudiante_id}/{periodo}`
- `GET /boletines/admin/reporte-parcial/{estudiante_id}/{periodo}`

Notas:

- **Porcentajes por tipo de nota** (desde el 2026-10-22, paso B2c de
  `docs/funcionalidades/SUBNOTAS_PLANILLA.md`, PB5). Solo cambian algo en una
  clase cuyos porcentajes están **activos** en ese periodo (todos los tipos
  con el suyo y suma de 100):
  - `POST /boletines/guardar` guarda la definitiva que **calcula el
    servidor** (promedio ponderado, dos decimales mitad hacia arriba; en
    preescolar, el valor ponderado de las caritas), no la que llega en
    `definitiva`. Si el estudiante no tiene ninguna nota que ponderar, guarda
    la que llega, como siempre.
  - `GET /boletines/referencia/{asignacion_id}/{periodo}` agrega `definitiva`
    (número) a cada estudiante que tenga notas: es exactamente la que se
    guardará.
  - Sin porcentajes activos las dos rutas responden y guardan lo de siempre.
    Cuestan una consulta más (saber si la clase tiene porcentajes), dos si los
    tiene incompletos, y tres con porcentajes activos.
  - Paso B2d (PB7): `GET /boletines/admin/generar/...` usa la nota ponderada
    en la materia **sin boletín guardado** cuya clase tiene porcentajes
    activos (el respaldo de siempre era el promedio simple). Una materia con
    boletín guardado conserva su definitiva. Si todas lo tienen, no consulta
    nada más; si no, una consulta más (dos o tres con porcentajes).
  - Paso B2d (PB7): `GET /boletines/admin/reporte-parcial/...` usa la nota
    ponderada en cada materia cuya clase tiene porcentajes activos. Una
    consulta más (dos si alguna tiene porcentajes). Los detalles no cambian.
  - En el boletín del admin y en el reporte parcial **solo cuentan las notas
    numéricas**, como siempre: su nota de preescolar sigue vacía.
- `GET /boletines/admin/generar/{estudiante_id}/{periodo}` devuelve la
  definitiva guardada en boletin si existe.
- Si no existe definitiva guardada, o la definitiva guardada es `0`, usa como
  respaldo el promedio numerico de `notas_detalle` para ese estudiante,
  asignacion y periodo.
- El promedio de respaldo solo considera notas numericas mayores que `0`.
- `GET /boletines/admin/reporte-parcial/{estudiante_id}/{periodo}` devuelve una
  fotografia en tiempo real de `notas_detalle`, incluyendo `descripcion`, nota
  o valoracion y el promedio numerico vigente por materia. No depende de que el
  profesor haya guardado el boletin para administracion.
- Ambos endpoints devuelven `director_grupo`: `"Nombre Apellido"` del profesor
  asignado como director de grupo del curso del estudiante, o `null` si el
  curso no tiene uno asignado (`cursos.director_grupo_id`). Ver
  `docs/funcionalidades/DIRECTOR_GRUPO.md`.
- Año lectivo (fase 3, paso 3.5a): los dos endpoints de admin aceptan
  `?anio_lectivo_id=`. Sin el, o con el del año activo, el boletin y el
  reporte de siempre (mismas consultas). Con otro año, el curso es el de la
  matricula del estudiante ese año (materias, curso, jornada, director y
  compañeros del puesto). Un año que no existe da `404` con `El año lectivo
  seleccionado no existe.`
- El `puesto` cuenta solo las definitivas de cursos del año que se mira,
  tambien sin el parametro: el periodo 1 existe todos los años y, sin ese
  filtro, con dos años se mezclarian. Mientras haya un solo año, el puesto
  es el mismo de antes.
- Materias ocultas (fase 6, paso 6.3b): en el año activo y en el de
  preparación se ocultan las inactivas, como siempre. En un año `cerrado` o
  `reabierto` se ocultan las de su foto al cerrarse
  (`anios_lectivos_materias_ocultas`, decisión 13), aunque después se hayan
  activado o desactivado. Sin `anio_lectivo_id`, o con el activo, las
  consultas no cambiaron.

## Branding

- `GET /branding`
- `PUT /branding`
- `POST /branding/logo`
- `DELETE /branding/logo`

Notas:

- `GET /branding` y `PUT /branding` incluyen `codigo_dane` como dato
  institucional opcional del colegio.

## Plantillas

- `GET /plantillas`
- `GET /plantillas/activa/{tipo}`
- `POST /plantillas`
- `PUT /plantillas/{plantilla_id}`
- `POST /plantillas/{plantilla_id}/activar`
- `POST /plantillas/{plantilla_id}/duplicar`
- `DELETE /plantillas/{plantilla_id}`

## Cartera

- `GET /cartera/mora`
- `GET /cartera/mora/resumen`

Notas:

- Año lectivo (fase 2, paso 2.4): cada estudiante de `GET /cartera/mora` trae
  `deuda_anios_anteriores`, la deuda de cada año anterior al activo en que
  tuvo matricula (`anio_lectivo_id`, `anio`, `curso_id`, `deudas`,
  `total_deuda`), aparte de `total`, que sigue siendo la del año. Un
  estudiante que solo debe de años anteriores tambien aparece, con `total` 0.
  `GET /cartera/mora/resumen` suma esa deuda en `total_anios_anteriores`.
  Mientras haya un solo año, la lista viene vacia y el total en 0.
- Año lectivo (fase 3, paso 3.4): `GET /cartera/mora` y `GET
  /cartera/mora/resumen` aceptan `?anio_lectivo_id=`. Sin el, el año activo,
  como antes. Los estudiantes salen de las matriculas del año, cada uno con el
  curso de ese año (el mismo que fija sus precios). Mirando el año activo,
  solo estudiantes activos y con sus ventas pendientes, como siempre. Mirando
  otro año (decisiones 18 y 19 de `docs/funcionalidades/ANIO_LECTIVO.md`):
  todos sus matriculados que deben, aunque despues se hayan retirado, y **sin
  ventas** (no son de ningun año). Año inexistente: `404`.

## Paginacion compatible existente

Se observo soporte de `limit`/`offset` en endpoints como:

- `/estudiantes`
- `/api/ventas/`
- `/pagos/{estudiante_id}`
- `/inventario`
- `/reportes/ingresos-mes/{mes}`
- `/reportes/ingresos-rango`
- `/asignaciones/lista`
- `/profesores`
- `/cursos`
- `/materias`
- `/usuarios`

