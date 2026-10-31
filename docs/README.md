# Documentacion Backend

Ultima revision documental: 2026-07-15.

Indice operativo para mantener control del backend SaaS escolar.

## Lectura rapida

- `PRODUCCION_BACKEND.md`: variables, Render, cookies, CORS, pool, R2 y checklist post-deploy.
- `CHECKLIST_PRODUCCION_BACKEND.md`: riesgos criticos e importantes antes/despues de produccion.
- `CAMBIOS_BACKEND.md`: bitacora historica de cambios tecnicos y documentales.
- `API_ENDPOINTS.md`: mapa de endpoints incluidos en `app/main.py`, incluyendo cartera, dashboard y valores personalizados de pago por estudiante.
- `ARQUITECTURA_BACKEND.md`: estructura de carpetas, routers, servicios, repositorios y ciclo de vida.
- `BASE_DATOS.md`: PostgreSQL, schemas tenant, pool, tablas, indices y migraciones.
- `MULTITENANT.md`: identificacion de tenant, `search_path`, estados SaaS y creacion de colegios.
- `SEGURIDAD.md`: login, JWT, cookie HttpOnly, CORS, permisos, uploads y hardening.
- `ROLES_PERMISOS_BACKEND.md`: roles `admin`, `profesor`, `super_admin` y dependencias de autorizacion.
- `MIGRACIONES.md`: runner `apply_migration.py`, migraciones publicas/tenant e historial.
- `ESCALABILIDAD.md`: lineamientos para crecer sin romper contratos actuales.
- `PLAN_EJECUCION_BACKEND.md`: orden sugerido para trabajo futuro.
- `modularizacion/README.md`: plan activo por capas y continuidad entre chats
  para la evolución segura del backend.

## Funcionalidades de producto

Funciones nuevas documentadas aparte del programa de modularizacion. Cada una
tiene su gemela en `frontend-react/docs/funcionalidades/` y su prompt de
continuacion para retomarla en otro chat u otro LLM.

- `funcionalidades/NIVEL_ACADEMICO.md`: niveles preescolar y primaria, tipo de
  evaluacion forzado y asistencia por jornada. **Completo y migrado.**
- `funcionalidades/OBSERVADOR_ESTUDIANTE.md`: observador unificado por
  estudiante, en bitacora acumulativa, en vez de una casilla por materia y
  periodo. **Disenado, nada implementado.**
- `funcionalidades/FIRMA_OBSERVADOR.md`: firma del acudiente en pantalla, una
  por anotacion; tabla `observador_firmas`, permisos (incluida la excepcion del
  admin), bloqueo de lo firmado y huella. Documento principal.
  **Paso 1 (backend) publicado el 2026-10-27; falta la pantalla (frontend).**
- `funcionalidades/LISTAS_SEGUIMIENTO.md`: columnas con nombre libre por
  curso para que el administrador marque alumnos (ej. asistencia a un
  evento, compra de un libro) fuera de notas y pagos. **Disenado, nada
  implementado.**
- `funcionalidades/ANIO_LECTIVO.md`: años lectivos (cursos por año,
  matriculas, cobros por año, consulta de años cerrados, preparar y activar
  el año siguiente). Incluye un error de cobros que aparece el 2027-01-01.
  **Fases 0 a 4 completas; fase 5 en curso. Los pasos 5.1 (`d113e15`) y 5.2
  (`a6f3cc0`) están completos; la migración de 5.2 fue verificada y aplicada en
  producción. Fecha limite: noviembre de 2026.**
- `funcionalidades/ENTREVISTA_ADMISION.md`: registrar aspirantes nuevos del
  año en preparación, hacerles la entrevista con la familia y dejar el
  resultado (aprobado o no aprobado); solo un aprobado se matricula. Vive en la
  preparación del año lectivo. **Diseñado (E0, 2026-10-12), nada
  implementado. Fecha limite: noviembre de 2026.**
- `funcionalidades/SISBEN_RESIDENCIA.md`: SISBÉN (grupo, subgrupo y nivel) y
  lugar de residencia por partes (barrio, municipio, zona, punto de
  referencia) en la ficha del estudiante. Migración en `estudiantes`.
  **Backend completo y migración en producción (2026-10-20); falta el
  frontend (S3).**
- `funcionalidades/SUBNOTAS_PLANILLA.md`: subnotas por tipo de nota en la
  planilla del profesor (su promedio va a la celda) y, después, porcentajes
  por tipo de nota. Dos tablas nuevas; la parte B cambia la nota del periodo.
  **Parte A (subnotas) publicada el 2026-10-21, backend y frontend. Parte B
  (porcentajes): diseño (B0) aprobado, caracterización (B1) hecha y B2 en
  completo el 2026-10-22 (backend: cálculo, tabla, ruta, boletín, reporte
  parcial y rankings), B3 (rama de Neon) bien y backend en producción el
  mismo día (`dfe0336`, Render Live) y frontend publicado también
  (`82eecf9`). Partes A y B completas y publicadas.**
- `funcionalidades/NOMBRES_CUADROS_PLAN.md`: nombres de los cuadros del plan
  de clase por colegio; tabla `plan_de_clases_cuadros` (solo los renombrados),
  `GET /plan-de-clases/cuadros` y `PUT /admin/plan-de-clases/cuadros` (solo
  admin). Documento principal. **Paso 1 (backend) publicado el 2026-10-31
  (`f4c7fcb`, migración en producción); falta la pantalla (frontend).**

## Estado actual resumido

- API FastAPI con PostgreSQL y `psycopg2`.
- Multi-tenant por schemas: `public` para datos globales y `tenant_*` para colegios.
- Sesion principal por cookie `token` HttpOnly; el JSON de login no expone JWT.
- Super admin vive en `public.super_admins` y entra con codigo de colegio `super_admin`.
- Archivos subidos se sirven por `/uploads/{file_path:path}` con autenticacion, tenant y ownership.
- Produccion puede usar almacenamiento local o Cloudflare R2 con `STORAGE_PROVIDER`.
- Conexion DB centralizada en `app/db/session.py` con `ThreadedConnectionPool`.

## Regla documental

Cuando se modifique backend, actualizar el documento del area tocada y registrar
el cambio en `CAMBIOS_BACKEND.md` si afecta produccion, seguridad, API,
base de datos, permisos, migraciones o comportamiento observable.
