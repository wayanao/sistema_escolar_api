# Funcionalidad: Director de grupo en el boletín — Backend

## Control

- Estado: **Código completo, verificado localmente**. `scripts/verify.py`:
  1307 pruebas pasan (subió de 1297; +11 nuevas: 7 en
  `tests/test_curso_controlador.py`, 4 en `tests/test_boletin_caracterizacion.py`),
  Ruff y `pip check` correctos. **Una falla esperada y correcta**:
  `tests/test_esquema_base.py::test_la_base_incorpora_todas_las_migraciones_de_tenant`
  — es la compuerta automática que exige aplicar la migración real y
  regenerar el esquema base antes de que quede en verde; ver "Orden de
  despliegue obligatorio" más abajo. Nada commiteado ni publicado.
- Tipo: Función nueva de producto. No es una capa del programa de
  modularización de `docs/modularizacion/` y no debe confundirse con una.
- Repos afectados: este repo (`sistema_escolar_api`) y `frontend-react`. Ver
  también `frontend-react/docs/funcionalidades/DIRECTOR_GRUPO.md`, que cubre
  la parte de pantallas.
- Riesgo inicial: Bajo. Columna nueva, nullable, sin cambio de comportamiento
  para quien no la use; no toca autenticación, roles ni aislamiento de tenant.
- Última actualización: 2026-09-15.

## Objetivo

Que cada curso pueda declarar quién es su director de grupo (un profesor), y
que el boletín impreso muestre su nombre como **dato informativo aparte**,
sin reemplazar la línea de firma a mano que ya existe.

## Motivación

El boletín impreso (`BoletinImprimible.jsx`, frontend) solo tiene "Director
de Grupo" como una etiqueta fija de firma, sin nombre — a propósito, porque
ese documento se firma en físico (mismo patrón documentado en
`frontend-react/src/utils/observador/impresion.js`: "del director de grupo
no hace falta saber el nombre"). El usuario pidió que el nombre real también
aparezca, como referencia, sin tocar esa firma.

Se investigó primero si el dato ya existía en otra forma:

- `cursos` no tenía ningún campo de profesor.
- `asignaciones` es materia-profesor-curso-horario, simétrica: ninguna fila
  marca "este es el encargado del grupo". Derivarlo de ahí sería adivinar
  (¿el primer profesor asignado? ¿el de qué materia?) y no tiene sentido
  semántico: director de grupo es una propiedad del curso, no de una materia.

## Fuera de alcance

- No se resuelve ni se muestra el nombre del director de grupo en las
  respuestas de `GET /cursos` (listado simple ni paginado): esas respuestas
  siguen devolviendo solo `director_grupo_id`. El frontend ya tiene la lista
  de profesores por separado para el selector del formulario y para mostrar
  el nombre donde haga falta.
- No se agrega columna ni insignia de "Director de grupo" en la lista de
  Cursos (`ListaCursos.jsx`). Se puede agregar después si se pide.
- Reemplazar la línea de firma a mano de "Director de Grupo": decisión
  explícita del usuario, se mantiene igual.
- Boletines legacy, malla curricular, observador, plan de clases, pagos: sin
  cambios.

## Decisiones ya tomadas (con el usuario)

- El nombre del director de grupo es un **dato informativo aparte**, no
  reemplaza la firma a mano.
- Se asigna por curso (editando el curso), no por asignación.

## Diseño de datos

### Columna nueva: `cursos.director_grupo_id`

```sql
ALTER TABLE cursos
    ADD COLUMN IF NOT EXISTS director_grupo_id INTEGER
    REFERENCES profesor(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_cursos_director_grupo
ON cursos (director_grupo_id);
```

- Nullable: un curso sin director de grupo asignado se comporta exactamente
  igual que hoy.
- `ON DELETE SET NULL`: los profesores se desactivan con `estado`
  (`20260604_profesor_estado.sql`), no se borran físicamente; si algún día se
  borrara un profesor, el curso simplemente pierde la referencia en vez de
  bloquear el borrado o arrastrar un `CASCADE` no deseado. Mismo patrón que
  `plan_de_clases.revisado_por`/`admin_visto_por` en el esquema base.
- Se aplica a los tenants existentes con `apply_migration.py`, igual que las
  migraciones anteriores.

## Cambios de API

| Endpoint | Cambio |
|---|---|
| `POST /cursos`, `PUT /cursos/{curso_id}` | Acepta `director_grupo_id` (opcional, `int` o `null`). |
| `GET /cursos`, `GET /cursos?estado=...`, `PATCH /cursos/{curso_id}/estado` | Devuelven `director_grupo_id` (no el nombre, ver "Fuera de alcance"). |
| `GET /boletines/admin/generar/{estudiante_id}/{periodo}` | Devuelve `director_grupo`: `"Nombre Apellido"` si el curso tiene uno asignado, `null` si no. |
| `GET /boletines/admin/reporte-parcial/{estudiante_id}/{periodo}` | Mismo campo `director_grupo`, mismo criterio. |

### Archivos modificados

- `app/schemas/curso.py`: `CursoCreate.director_grupo_id: Optional[int] = None`.
- `app/controllers/curso_controller.py`: `crear_curso_controller` y
  `actualizar_curso_controller` leen y guardan `director_grupo_id`;
  `_formatear_curso` y las tres consultas de lectura
  (`obtener_cursos_controller`, `obtener_cursos_paginado_controller`,
  `actualizar_estado_curso_controller`) lo devuelven — mismo patrón exacto
  que se usó para `nivel` (ver `docs/funcionalidades/NIVEL_ACADEMICO.md`).
- `app/repositories/boletin_repository.py`: `leer_datos_del_estudiante` y
  `leer_datos_basicos_del_estudiante` agregan
  `LEFT JOIN profesor dg ON dg.id = c.director_grupo_id` y devuelven
  `director_grupo_nombre`/`director_grupo_apellido`. Cero consultas nuevas:
  es el mismo query con un JOIN más.
- `app/controllers/boletin_controller.py`: en `obtener_boletin_admin_controller`
  y `obtener_reporte_parcial_admin_controller`, arma `director_grupo` como
  `"Nombre Apellido"` o `None`. Usa `est_info.get(...)`, no `est_info[...]`,
  para no romper con `KeyError` los fixtures de prueba existentes que no
  incluyen esas claves.

## Invariantes

- Un curso sin director de grupo asignado se comporta exactamente igual que
  hoy; el boletín no muestra el dato (no muestra "Sin asignar", simplemente
  no aparece).
- Ningún colegio nota cambios hasta que un administrador asigne un director
  de grupo a un curso.
- La línea de firma a mano de "Director de Grupo" en el boletín no cambia.
- Permisos, roles y aislamiento por tenant no cambian.

## Riesgos y mitigación

| Riesgo | Mitigación |
|---|---|
| Migración multi-tenant | Se aplica con el runner ya probado (`apply_migration.py`). |
| Columna nueva usada por un `SELECT` en `boletin_repository.py` antes de existir en un tenant | Ver "Orden de despliegue obligatorio" — la migración debe estar aplicada a todos los tenants antes de publicar este código. |
| Repetir la lógica de "nombre completo" en dos controladores | Aceptado: son dos funciones ya separadas deliberadamente (`obtener_boletin_admin_controller` / `obtener_reporte_parcial_admin_controller`), mismo criterio que el resto del dominio boletín — no se crea una abstracción compartida por dos usos casi idénticos, siguiendo la misma regla que ya aplicó 7.1 al dominio. |

### Orden de despliegue obligatorio, sin excepción

Este código ejecuta `LEFT JOIN profesor dg ON dg.id = c.director_grupo_id`
en cada consulta de boletín. Si se publica en producción **antes** de que la
columna exista en un tenant, ese `SELECT` falla con "columna no existe" y ese
colegio deja de poder generar boletines.

1. Aplicar `migrations/20260915_cursos_director_grupo.sql` a **todos los
   tenants activos** con `apply_migration.py` (`--dry-run` primero).
2. Regenerar `migrations/base/20260813_esquema_base_tenant.sql` con
   `scripts/generar_esquema_base.py --schema <schema>`, **después** del paso
   1, nunca antes.
3. Confirmar que `tests/test_esquema_base.py` pasa (hoy falla a propósito,
   ver "Control" arriba).
4. Solo después, `git push origin main` — despliega producción
   automáticamente.

## Plan de fases (backend) — completado, pendiente de migración real

1. ~~Migración: columna `director_grupo_id` en `cursos`.~~ **Hecho.**
   `migrations/20260915_cursos_director_grupo.sql`. **No aplicada** a
   ningún tenant real ni a Neon todavía.
2. ~~`app/schemas/curso.py` y `app/controllers/curso_controller.py` leen,
   guardan y devuelven `director_grupo_id`.~~ **Hecho.** 7 pruebas nuevas en
   `tests/test_curso_controlador.py`.
3. ~~`boletin_repository.py` y `boletin_controller.py` arman `director_grupo`
   en ambos caminos (boletín oficial y reporte parcial).~~ **Hecho.** 4
   pruebas nuevas en `tests/test_boletin_caracterizacion.py`.
4. ~~`scripts/verify.py`.~~ **Hecho**, ver "Control" arriba.
5. Aplicar la migración real a los tenants con `apply_migration.py` y
   regenerar el esquema base. **Pendiente — decide el usuario cuándo.**

## Preguntas abiertas

- ¿Se debe mostrar el nombre del director de grupo también en la lista de
  Cursos (`ListaCursos.jsx`) para que el administrador vea de un vistazo
  quién está asignado a cada curso? **Sin responder** — no se implementó,
  ver "Fuera de alcance".

## Entrega para el siguiente chat

- Última acción terminada: código completo de este repo, verificado
  localmente (`scripts/verify.py`, 1307 pruebas + 1 falla esperada de la
  compuerta de migración). Nada commiteado ni publicado.
- Siguiente acción exacta: el usuario decide cuándo aplicar la migración
  real a los tenants operativos (`apply_migration.py`), regenerar el
  esquema base, y luego hacer commit y `git push origin main` — en ese
  orden, no al revés.
- Ver también `frontend-react/docs/funcionalidades/DIRECTOR_GRUPO.md` para
  la parte de pantallas (formulario de Curso y boletín).
