# API Endpoints

Ultima revision documental: 2026-07-15.

## Routers

Los routers se incluyen en `app/main.py`.

Prefijos definidos en router:

- `boletines`: prefix `/boletines`
- `egresos`: prefix `/api/egresos`
- `prestamos`: prefix `/api/prestamos`
- `super_admin`: prefix `/super-admin`
- `ventas`: prefix `/api/ventas`
- `nomina`: incluido en `main.py` con prefix `/api/nomina`

Los demas routers usan paths completos en cada decorator.

## Auth

- `POST /login`
- `POST /logout`
- `POST /auth/cambiar-password`

## Tenant

- `GET /tenant/status`

## Super Admin

- `GET /super-admin/tenants`
- `POST /super-admin/tenants`
- `PATCH /super-admin/tenants/{tenant_id}/estado`
- `GET /super-admin/tenants/{tenant_id}/estado-auditoria`

## Uploads

- `GET /uploads/{file_path:path}`

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
- `GET /estudiantes/{estudiante_id}/deudas` devuelve solo deuda academica
  pendiente del estudiante usando la logica central de cobros; no depende del
  resumen amplio de notas, observaciones o inventario.

## Cuentas

- `GET /estado-cuenta/curso/{curso_id}`
- `GET /estado-cuenta/estudiante/{estudiante_id}`

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
  estudiante y meses posteriores al actual dentro del mismo año.
- `POST /pagos/adelanto` recibe `estudiante_id`, `tipo_pago_id`,
  `fecha` opcional, una lista no vacia de `metodos` y exactamente una modalidad:
  `cantidad_meses` o `monto_distribuir`.
- Con `monto_distribuir`, el backend cubre en orden los meses futuros: completa
  cada saldo y aplica el remanente como abono parcial al siguiente periodo.
- Las opciones futuras incluyen `saldo` por mes y `total_disponible`; un mes
  parcialmente abonado continua disponible por el valor restante.
- El cliente no define el valor de las cuotas: el backend usa la prioridad
  valor del estudiante > valor del curso > valor base y valida la suma de los
  metodos.
- Un mes activo no puede adelantarse dos veces. La anulacion libera sus meses
  y mantiene el pago visible como anulado.
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
  ya existe una materia con el mismo nombre.

## Observaciones

- `POST /observaciones`
- `GET /observaciones/{estudiante_id}/{asignacion_id}/{periodo}`

`POST /observaciones` acepta `conductual`, `cognitivo` y `lenguaje` como textos
opcionales con valor vacio por defecto, pero exige contenido en al menos una
dimension. Los textos se normalizan antes de crear o actualizar el registro.

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
- Las imagenes `imagen1` e `imagen2` tambien son opcionales.
- Los planes retornan `estado_revision`, `version_revision`, fechas de
  seguimiento y contadores de observaciones.
- `GET /admin/plan-de-clases` acepta el filtro opcional `estado_revision`:
  `pendiente`, `visto`, `con_observaciones` o `revisado`. Para la bandeja
  consolidada, `pendiente` agrupa también el estado interno `visto` y
  `revisado` agrupa también `con_observaciones`; los dos valores internos se
  conservan por compatibilidad.
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

Notas:

- `GET /boletines/admin/generar/{estudiante_id}/{periodo}` devuelve la
  definitiva guardada en boletin si existe.
- Si no existe definitiva guardada, o la definitiva guardada es `0`, usa como
  respaldo el promedio numerico de `notas_detalle` para ese estudiante,
  asignacion y periodo.
- El promedio de respaldo solo considera notas numericas mayores que `0`.

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

