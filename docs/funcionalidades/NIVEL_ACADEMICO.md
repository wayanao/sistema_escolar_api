# Funcionalidad: Nivel académico (Preescolar y Primaria) — Backend

## Control

- Estado: **Completo y migrado.** La migración `20260901_cursos_nivel_academico.sql`
  se aplicó el 2026-09-02 a los 2 tenants operativos
  (`tenant_colegio_1` y `tenant_2005`), con `OK` en ambos. El archivo base
  se regeneró en el mismo momento. `scripts/verify.py` corre **1171
  pruebas, exit 0** en pytest, Ruff y `pip check` — sin ninguna falla
  pendiente. Solo falta el commit (lo hace el usuario) y decidir cuándo
  hacer `git push origin main` (ver más abajo, el orden de despliegue ya no
  aplica retroactivamente porque los tenants ya tienen la columna, pero
  sigue siendo la regla para futuras migraciones de esta funcionalidad).
- Tipo: Función nueva de producto. No es una capa del programa de
  modularización de `docs/modularizacion/` y no debe confundirse con una.
- Repos afectados: este repo (`sistema_escolar_api`) y `frontend-react`. Ver
  también `frontend-react/docs/funcionalidades/NIVEL_ACADEMICO.md`, que cubre
  la parte de pantallas.
- Riesgo inicial: Medio. Multi-inquilino, cambia comportamiento observable de
  notas y asistencia, requiere validación nueva en el servidor.
- Última actualización: 2026-09-01.

## Objetivo

Que cada curso declare un nivel académico (`preescolar` o `primaria`) y que
ese dato controle, **validado en el servidor**, dos cosas:

1. el tipo de evaluación permitido al guardar una nota (numérica o
   desarrollo/caritas);
2. la forma en que se toma asistencia.

## Motivación

- El sistema ya distingue nota numérica de "desarrollo" (caritas) en
  `notas_detalle` y `boletin_detalles`, pero la elección de `tipo_evaluacion`
  es libre y no está atada al curso real. Se confirmó leyendo
  `app/controllers/planilla_controller.py`: hoy se guarda lo que mande el
  cliente, con `"numerica"` como valor por defecto si no llega nada.
- La asistencia siempre cuelga de una `asignacion_id` (curso + materia +
  profesor + horario). En preescolar, donde una sola maestra atiende toda la
  jornada, eso obliga a marcar asistencia una vez por cada materia del día.
- `cursos` no tiene ningún dato que indique a qué nivel pertenece.

## Fuera de alcance

- Boletines, malla curricular, observador del estudiante, plan de clases,
  pagos: sin cambios en esta propuesta.
- Otros niveles (bachillerato, etc.): no se crean ahora. El diseño no debe
  impedir agregarlos después.
- Migrar o corregir notas/asistencia ya guardadas: la regla aplica solo hacia
  adelante desde que un curso se marca con nivel.
- Permitir que un colegio configure excepciones a estas reglas (por ejemplo,
  preescolar con asistencia por materia): no en esta primera versión.

## Decisiones ya tomadas (con el usuario, en la conversación de origen)

- Alcance elegido: ampliar el modelo de datos actual, no crear secciones de
  menú ni áreas separadas.
- En preescolar se **mantienen** las asignaciones por materia (Matemáticas,
  Lenguaje, Arte...) para las notas. No se colapsan en un solo bloque por
  curso.
- Para asistencia se agrega, por curso de preescolar, **una asignación más**
  que representa la jornada completa (ej. materia "Asistencia diaria", la
  maestra titular). Se verificó contra el código real
  (`asignar_profesor_controller`, `validar_horario_unico`,
  `buscar_horario_identico` en `app/repositories/asignaciones_repository.py`)
  que esto **no choca** con ninguna asignación existente: la única validación
  de duplicado exige coincidencia exacta de profesor + curso + **materia** +
  día + horas, y como la materia es distinta, nunca coincide. No existe hoy
  ninguna validación que impida que dos asignaciones de un mismo profesor se
  crucen en horario.
- La regla de tipo de evaluación **debe** validarse en el servidor, no solo
  ocultarse en la pantalla. Se confirmó que hoy no hay ninguna validación de
  este tipo en el backend.
- Las reglas por nivel se centralizan en un único punto de configuración, no
  se repiten como condicionales sueltos por archivo.
- Un curso que cambia de nivel a mitad de camino no modifica su historial ya
  guardado; la regla nueva aplica solo a partir de ese momento.

## Diseño de datos

### Columna nueva: `cursos.nivel`

```sql
ALTER TABLE cursos ADD COLUMN nivel character varying(20);
```

- Valores válidos: `preescolar`, `primaria`, o `NULL` (sin definir).
- Un curso con `NULL` se comporta exactamente como hoy hasta que alguien lo
  configure explícitamente.
- Se guarda como texto y no como booleano, para poder sumar un tercer nivel a
  futuro sin cambiar el tipo de dato ni el diseño.
- Se aplica a los tenants existentes con `apply_migration.py`, igual que las
  31 migraciones ya incorporadas en
  `migrations/base/20260813_esquema_base_tenant.sql`. El esquema base
  generado también debe actualizarse para que un tenant nuevo nazca con la
  columna.

### Un solo lugar con las reglas de cada nivel

```python
REGLAS_POR_NIVEL = {
    "preescolar": {
        "tipo_evaluacion_forzado": "desarrollo",
        "asistencia_por_jornada": True,
    },
    "primaria": {
        "tipo_evaluacion_forzado": None,  # libre; por defecto "numerica"
        "asistencia_por_jornada": False,
    },
}
```

Todo el código que necesite saber "qué corresponde a este nivel" consulta
esta tabla. No se repite el condicional en cada controlador.

## Validación en el servidor (la pieza crítica)

Hoy, en `app/controllers/planilla_controller.py`:

```python
tipo_evaluacion = getattr(data, "tipo_evaluacion", "numerica") or "numerica"
```

Cambio propuesto: antes de guardar, resolver el curso de la asignación (ya
existe `resolver_asignacion_academica_id_cursor`, que se usa en el mismo
archivo) y mirar su `nivel`.

- Curso `preescolar` → se ignora lo que mande el cliente; se guarda siempre
  `tipo_evaluacion = "desarrollo"`.
- Curso `primaria` o sin nivel → se conserva el comportamiento actual.

Pendiente de verificar en la capa 0 de implementación: si
`boletin_controller.py` / `boletin_repository.py` consolidan
`boletin_detalles.tipo_evaluacion` a partir de `notas_detalle`, o si tienen su
propia ruta de escritura independiente. Si es independiente, necesita la
misma validación.

## Asistencia por jornada (preescolar)

No se toca la tabla `asistencia` ni su lógica (`asistencia_controller.py`,
`asistencia_repository.py` quedan intactos). Se reutiliza el modelo actual:

- Por cada curso de preescolar, se crea una asignación con una materia que
  represente el día completo (ej. "Asistencia diaria"), con la maestra
  titular como profesor.
- Esa asignación se usa exactamente igual que cualquier otra para
  `POST /asistencia`, el historial y "mis clases".
- Nada nuevo que programar en este repo para el guardado de asistencia en sí;
  el trabajo real de esta pieza es en el frontend (cuál asignación se
  preselecciona).

## Cambios de API

| Endpoint | Cambio |
|---|---|
| `POST /cursos`, `PUT /cursos/:id` | **Hecho.** Acepta y devuelve `nivel` (opcional; si no llega, queda `NULL`). Ver detalle abajo. |
| `POST /notas` (planilla) | Deja de confiar ciegamente en `tipo_evaluacion` del cliente: lo valida/fuerza según el nivel del curso de la asignación. |
| `POST /asistencia` | Sin cambio de contrato. |

### `POST /cursos` y `PUT /cursos/:id`: hueco cerrado

Al empezar la Fase 2 (frontend) se descubrió que este cambio, aunque estaba
en el plan desde el inicio, **nunca se implementó** durante los pasos 1-5:
`app/controllers/curso_controller.py` no leía, guardaba ni devolvía `nivel`
en ningún punto (creación, actualización, listado simple, listado paginado,
cambio de estado). Sin esto, el frontend no habría tenido nada real que
consumir.

Corregido: `app/schemas/curso.py` agrega `nivel: Optional[NivelCurso] = None`
(`NivelCurso = Literal["preescolar", "primaria"]` — un valor fuera de esos
dos, salvo ausente, es rechazado por Pydantic con 422, igual que ya hace
`EstadoCurso`). `curso_controller.py` lo lee y guarda en creación y
actualización, y lo devuelve en las cuatro funciones de lectura/escritura
que arman la respuesta (`_formatear_curso`, listado, listado paginado y
cambio de estado). 8 pruebas nuevas en `tests/test_curso_controlador.py`,
que no tenía cobertura previa en absoluto.

## Invariantes

- Un curso sin nivel definido se comporta exactamente como hoy.
- Ningún dato histórico de notas o asistencia se modifica por este cambio.
- Un colegio que no use preescolar no nota ninguna diferencia.
- Los contratos de asistencia (`POST /asistencia`, historial, mis-clases) no
  cambian de forma.
- Permisos, roles y aislamiento por tenant no cambian.

## Riesgos y mitigación

| Riesgo | Mitigación |
|---|---|
| Regla solo en pantalla, sin respaldo en el servidor | Validación obligatoria en `planilla_controller` y `boletin_controller` antes de guardar. |
| Repetir la condición por nivel en varios archivos | `REGLAS_POR_NIVEL` centralizada. |
| Curso que cambia de nivel a mitad de año con historial mixto | La regla nueva aplica solo hacia adelante; nada histórico se recalcula. |
| Migración multi-tenant | Se aplica con el runner ya probado (`apply_migration.py`), igual que las 31 anteriores. |
| **Orden de despliegue** (crítico, ver abajo) | La migración debe estar aplicada a todos los tenants **antes** de publicar este código en producción, nunca después. |

### Orden de despliegue obligatorio, sin excepción

Este código (`planilla_controller.py`, `boletin_controller.py`) ejecuta
`SELECT c.nivel FROM ... JOIN cursos c ...` en cada guardado de nota o
boletín. Si se publica en producción **antes** de que la columna `nivel`
exista en un tenant, ese `SELECT` falla con un error de PostgreSQL
("columna no existe") y **ese colegio deja de poder guardar notas y
boletines**, en todos sus cursos, no solo en preescolar.

Por eso el orden de publicación no es negociable:

1. Aplicar `migrations/20260901_cursos_nivel_academico.sql` a **todos los
   tenants activos** con `apply_migration.py` (no solo al schema de
   referencia del paso 1b, que es aparte y sirve para los tenants nuevos).
2. Solo después, hacer `git push origin main` de este código. Recordar que
   en este repositorio un push a `main` **despliega producción
   automáticamente**.

Nunca al revés. Este repositorio no tiene hoy una prueba automática que
bloquee ese error de orden; queda como responsabilidad de checklist manual
antes de publicar.

## Plan de fases (backend)

1. ~~Migración: columna `nivel` en `cursos`.~~ **Hecho.**
   `migrations/20260901_cursos_nivel_academico.sql`: `ADD COLUMN IF NOT
   EXISTS nivel VARCHAR(20)`, restricción `chk_cursos_nivel` que solo admite
   `NULL`, `preescolar` o `primaria`, e índice `idx_cursos_nivel`.
   **Aplicada el 2026-09-02** a los 2 tenants operativos
   (`tenant_colegio_1`, `tenant_2005`) por el usuario, con `apply_migration.py`
   apuntando al endpoint directo de Neon (el runner se niega sobre el
   agrupado `-pooler` desde la capa 3.4d del programa de migraciones — no es
   nuevo de esta funcionalidad). `migrations/base/20260813_esquema_base_tenant.sql`
   regenerado con `scripts/generar_esquema_base.py --schema tenant_colegio_1`
   en el mismo momento; ahora declara 32 migraciones incorporadas e incluye
   `nivel`, su `CHECK` y su índice.
2. ~~`REGLAS_POR_NIVEL` centralizada.~~ **Hecho.** Vive en
   `app/core/nivel_academico.py`, junto con `tipo_evaluacion_forzado(nivel)`
   y `resolver_tipo_evaluacion(nivel, tipo_evaluacion_solicitado)`, ambas
   funciones puras sin base de datos. Pruebas en
   `tests/test_nivel_academico.py`.
3. ~~`planilla_controller` valida/fuerza `tipo_evaluacion`.~~ **Hecho.**
   Se agregó `resolver_nivel_curso_cursor(cursor, asignacion_id)` en
   `app/services/asignacion_academica.py` (junto a
   `resolver_asignacion_academica_id_cursor`, mismo patrón de firma) y se
   usa en `registrar_nota_planilla_controller` antes de construir el
   payload. **Costo medido**: agrega una consulta SQL de solo lectura
   dentro de la misma conexión/transacción ya abierta -no abre una conexión
   nueva-. El costo por petición de `POST /planilla/nota` sube de 4 a 5
   consultas (admin) y de 5 a 6 (profesor); las conexiones no cambian (2 y 3
   respectivamente). Documentado y verificado en
   `tests/test_planilla_caracterizacion.py`.
4. ~~Confirmar si `boletin_controller`/`boletin_repository` necesitan la
   misma validación.~~ **Hecho, y la respuesta fue sí.** Se confirmó
   leyendo el código: `guardar_boletin_controller` tenía su propia ruta de
   escritura hacia `boletin_detalles.tipo_evaluacion`, **independiente** de
   `notas_detalle`/planilla, sin ninguna validación de nivel — la misma
   vulnerabilidad que planilla, y más grave porque cada detalle del lote
   podía traer su propio `tipo_evaluacion` suelto. Se aplicó el mismo patrón:
   `resolver_nivel_curso_cursor` + `resolver_tipo_evaluacion`, ahora también
   dentro del bucle que arma cada detalle (no solo en la cabecera), porque
   un curso preescolar debe forzar "desarrollo" en cada nota del boletín, no
   solo en la primera.
5. ~~Documentar la convención de "asignación de jornada".~~ **Hecho.** No
   requiere tabla ni columna nueva. Se reserva el nombre de materia exacto
   `"ASISTENCIA DIARIA"` (constante `NOMBRE_MATERIA_ASISTENCIA_JORNADA` en
   `app/core/nivel_academico.py`, junto a `es_asignacion_de_jornada(nombre)`
   para reconocerlo). Se confirmó leyendo `app/controllers/materia_controller.py`
   que el backend **ya normaliza** todo nombre de materia a mayúsculas,
   espacio simple y sin espacios en los extremos al crearla — por eso la
   constante ya está en esa forma canónica y una comparación exacta contra
   el nombre que devuelve la API es confiable, sin duplicar esa
   normalización. El administrador crea la asignación de jornada exactamente
   igual que cualquier otra (curso preescolar + materia "Asistencia diaria"
   + la maestra titular + horario que cubra el bloque institucional
   completo), desde la pantalla de Asignaciones ya existente. Sin cambios en
   `asistencia_controller.py`, `asistencia_repository.py` ni la tabla
   `asistencia`, tal como se verificó y acordó antes de empezar esta
   funcionalidad.
6. ~~Pruebas de caracterización antes de cada cambio + `scripts/verify.py`.~~
   **Hecho**, ver detalle de verificación abajo.
7. ~~Aplicar la migración a los tenants con `apply_migration.py`.~~
   **Hecho el 2026-09-02**, ver paso 1.

### Verificación final (todos los pasos, incluida la migración real)

- Archivos nuevos: `app/core/nivel_academico.py`,
  `migrations/20260901_cursos_nivel_academico.sql`,
  `tests/test_nivel_academico.py`, `tests/test_asignacion_academica.py`.
- Archivos modificados: `app/services/asignacion_academica.py` (nueva
  función `resolver_nivel_curso_cursor`), `app/controllers/planilla_controller.py`
  y `app/controllers/boletin_controller.py` (ambos usan las dos funciones
  nuevas), `tests/test_planilla_controlador.py` (3 pruebas nuevas: preescolar
  fuerza desarrollo, primaria respeta lo solicitado, curso sin nivel
  mantiene el comportamiento anterior), `tests/test_planilla_caracterizacion.py`
  (conteo de consultas actualizado de 4/5 a 5/6), `tests/test_boletin_caracterizacion.py`
  (2 pruebas nuevas: preescolar fuerza desarrollo en cada detalle del lote,
  primaria respeta lo solicitado; los 5 tests existentes que guardan un
  boletín ahora doblan también el resolver de nivel, igual que ya doblaban
  el de asignación académica).
- `scripts/verify.py`: **1171 pruebas pasaron, exit 0** (subió de 1140;
  +31 nuevas), Ruff correcto, `pip check` correcto. **Cero fallas** —tras
  aplicar la migración real y regenerar el esquema base, la última prueba
  pendiente (`test_la_base_incorpora_todas_las_migraciones_de_tenant`) ya
  pasa.
- Paso 5 agregó además `app/core/nivel_academico.py::NOMBRE_MATERIA_ASISTENCIA_JORNADA`
  y `es_asignacion_de_jornada`, con sus pruebas en `tests/test_nivel_academico.py`.
  Sin cambios en `app/controllers/asistencia_controller.py`,
  `app/repositories/asistencia_repository.py` ni en la tabla `asistencia`.
- Decisión del usuario sobre la pregunta abierta del boletín: la asignación
  de jornada se **excluye** del boletín (oficial y reporte parcial), por
  ahora. Implementado en `app/repositories/boletin_repository.py`
  (`leer_materias_del_estudiante` y `leer_planilla_vigente`, nuevo parámetro
  `nombre_materia_excluida`) y `app/controllers/boletin_controller.py`, con
  2 pruebas nuevas en `tests/test_boletin_caracterizacion.py`.
- `git diff --check`: exit 0. El diff pertenece exclusivamente a esta
  funcionalidad; no se tocó ningún otro dominio.
- La migración real y la regeneración del esquema base sí se ejecutaron
  contra los 2 tenants operativos, por el usuario, siguiendo el
  procedimiento documentado en `docs/MIGRACIONES.md`. El código de la
  aplicación (controllers, schemas, tests) sigue sin commitear ni publicar.

## Preguntas abiertas

- ~~¿La asignación "Jornada" debe aparecer en el boletín como una materia
  más, o debe excluirse de ahí?~~ **Respondida: se excluye, por ahora.** El
  usuario decidió que no debe verse como materia; podría reconsiderarse más
  adelante. Implementado: `leer_materias_del_estudiante` y
  `leer_planilla_vigente` (`app/repositories/boletin_repository.py`) reciben
  ahora un parámetro `nombre_materia_excluida`, y
  `boletin_controller.py` les pasa siempre
  `NOMBRE_MATERIA_ASISTENCIA_JORNADA`. Cubre tanto el boletín oficial
  (`obtener_boletin_admin_controller`) como el reporte parcial
  (`obtener_reporte_parcial_admin_controller`). Verificado con 2 pruebas
  nuevas en `tests/test_boletin_caracterizacion.py`.
- ¿El nivel lo define siempre el administrador manualmente, o se quiere
  alguna sugerencia automática a partir del nombre del curso? **Sigue sin
  respuesta.**
- ¿Se empieza con un colegio piloto antes de dejarlo disponible a todos los
  tenants? **Sigue sin respuesta.**

## Entrega para el siguiente chat

- Última acción terminada: **todo el código de la Fase 1 (pasos 1 a 7)**,
  incluida la migración real aplicada a los 2 tenants operativos y el
  esquema base regenerado. `scripts/verify.py` en verde total (1171
  pruebas, exit 0). Nada commiteado ni publicado todavía.
- Archivos pendientes de commit (el usuario decide cuándo):
  `app/core/nivel_academico.py`,
  `migrations/20260901_cursos_nivel_academico.sql`,
  `migrations/base/20260813_esquema_base_tenant.sql` (regenerado),
  `tests/test_nivel_academico.py`, `tests/test_asignacion_academica.py`,
  `tests/test_curso_controlador.py`,
  y los cambios en `app/services/asignacion_academica.py`,
  `app/controllers/planilla_controller.py`,
  `app/controllers/boletin_controller.py`,
  `app/repositories/boletin_repository.py`,
  `app/controllers/curso_controller.py`, `app/schemas/curso.py`,
  `app/routes/asignaciones.py`,
  `tests/test_planilla_controlador.py`,
  `tests/test_planilla_caracterizacion.py`,
  `tests/test_boletin_caracterizacion.py`,
  `tests/test_asignaciones_pagination.py`.
- Sin riesgos abiertos conocidos. La migración ya se aplicó a los 2 tenants
  operativos y el esquema base ya está regenerado; el orden de despliegue
  documentado (migrar antes de publicar) ya se cumplió para esta
  funcionalidad.
- Siguiente acción exacta: el usuario hace el commit de todo el trabajo
  (backend y frontend) cuando decida, y luego el push a `main` — que en
  este repositorio despliega producción automáticamente. Ya no hay ningún
  paso de base de datos pendiente antes de ese push.
- Quedan 2 preguntas abiertas sin respuesta (ver arriba): sugerencia
  automática de nivel por nombre de curso, y colegio piloto vs. todos los
  tenants. Ninguna bloquea el despliegue.
