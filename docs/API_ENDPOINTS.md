# API Endpoints

Estado documentado: 2026-05-25.

## Routers

Los routers se incluyen en `app/main.py`.

Prefijos definidos en router:

- `boletines`: prefix `/boletines`
- `egresos`: prefix `/api/egresos`
- `prestamos`: prefix `/api/prestamos`
- `ventas`: prefix `/api/ventas`
- `nomina`: incluido en `main.py` con prefix `/api/nomina`

Los demas routers usan paths completos en cada decorator.

## Auth

- `POST /login`
- `POST /logout`

## Uploads

- `GET /uploads/{file_path:path}`

## Estudiantes

- `POST /estudiantes`
- `GET /estudiantes`
- `GET /estudiantes/{estudiante_id}/detalles`
- `GET /estudiantes/{estudiante_id}`
- `PUT /estudiantes/{estudiante_id}`

## Cuentas

- `GET /estado-cuenta/curso/{curso_id}`
- `GET /estado-cuenta/estudiante/{estudiante_id}`

## Pagos

- `POST /pagos`
- `GET /pagos/{estudiante_id}`
- `POST /pagos/{pago_id}/anular`

## Cursos

- `POST /cursos`
- `GET /cursos`
- `PUT /cursos/{curso_id}`

## Profesores

- `POST /profesores`
- `GET /profesores`
- `PUT /profesores/{profesor_id}`

## Asignaciones

- `GET /asignaciones/lista`
- `PUT /asignaciones/{asignacion_id}`
- `DELETE /asignaciones/{asignacion_id}`
- `GET /hora/horarios-admin`
- `POST /asignaciones`
- `GET /profesores/{profesor_id}/cursos`
- `GET /cursos/{curso_id}/profesores`
- `DELETE /asignaciones/{profesor_id}/{curso_id}`
- `GET /mis-clases/{profesor_id}`

## Notas y boletin legacy

- `POST /notas`
- `GET /notas/{estudiante_id}`
- `GET /boletin/{estudiante_id}`
- `GET /planilla/{asignacion_id}`
- `GET /boletin/detallado/{estudiante_id}`
- `POST /boletin/guardar`

## Planilla

- `POST /planilla/nota`
- `GET /planilla-excel/{asignacion_id}/{periodo}`
- `DELETE /planilla/tipo`

## Asistencia

- `POST /asistencia`
- `GET /asistencia/historial/{asignacion_id}/{periodo}`

## Materias

- `POST /materia`
- `GET /materias`
- `PUT /materias/{materia_id}`

## Observaciones

- `POST /observaciones`
- `GET /observaciones/{estudiante_id}/{asignacion_id}/{periodo}`

## Plan de clases

- `POST /plan-de-clases`
- `GET /plan-de-clases/{asignacion_id}`
- `DELETE /plan-de-clases/{plan_id}/imagen`
- `GET /admin/plan-de-clases`
- `DELETE /admin/plan-de-clases/{plan_id}/imagen`

## Planeador anual

- `GET /planeador-anual/{asignacion_id}/{periodo}`
- `PUT /planeador-anual/{asignacion_id}/{periodo}`

## Dashboard

- `GET /dashboard/inasistencias/{profesor_id}`
- `GET /dashboard/notas-bajas/{profesor_id}`
- `GET /dashboard/notas-altas/{profesor_id}`
- `GET /dashboard/ranking/{asignacion_id}/{periodo}`
- `GET /dashboard/ranking-mejor/{asignacion_id}/{periodo}`

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

## Tipos de pagos

- `POST /tipos-pagos`
- `GET /tipos-pagos`
- `PUT /tipos-pagos/{id}`
- `DELETE /tipos-pagos/{id}`
- `GET /tipos-pagos/detallado`
- `GET /tipos-pagos/{id}/detalle`
- `PUT /tipos-pagos/{id}/configuracion`
- `GET /tipos-pagos/{id}/cursos`
- `PUT /tipos-pagos/{id}/cursos`
- `DELETE /tipos-pagos/{id}/cursos/{curso_id}`

## Inventario

- `GET /inventario`
- `POST /inventario`
- `PUT /inventario/{item_id}`
- `DELETE /inventario/{item_id}`

## Egresos

Router prefix: `/api/egresos`

- `GET /api/egresos/`
- `POST /api/egresos/`
- `DELETE /api/egresos/{egreso_id}`

## Prestamos

Router prefix: `/api/prestamos`

- `GET /api/prestamos/`
- `POST /api/prestamos/`
- `PUT /api/prestamos/{prestamo_id}/estado`
- `DELETE /api/prestamos/{prestamo_id}`

## Ventas

Router prefix: `/api/ventas`

- `GET /api/ventas/`
- `GET /api/ventas/pendientes/{estudiante_id}`
- `POST /api/ventas/`
- `POST /api/ventas/{venta_id}/anular`
- `DELETE /api/ventas/{venta_id}` bloqueado: usar anulacion

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

## Branding

- `GET /branding`
- `PUT /branding`
- `POST /branding/logo`
- `DELETE /branding/logo`

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
