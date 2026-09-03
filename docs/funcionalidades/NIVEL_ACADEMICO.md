# Funcionalidad: Nivel académico (Preescolar y Primaria) — Backend

## Control

- Estado: **Completo y migrado**, con tres extensiones pedidas por el usuario
  después del cierre inicial: validar la asistencia en el servidor (ver
  "Extensión: validar la asignación de jornada"); tras un reporte real del
  usuario, **exceptuar la asignación de jornada de la validación general de
  cruce de horario** (ver "Extensión: excepción al cruce de horario" — esta
  corrige un error de análisis del propio asistente, no solo agrega una
  función); y **primaria dejó de ser libre**: ahora fuerza "numérica" igual
  que preescolar fuerza "desarrollo" (ver "Extensión: primaria también
  fuerza su tipo de evaluación" más abajo). La migración
  `20260901_cursos_nivel_academico.sql` se aplicó el 2026-09-02 a los 2
  tenants operativos (`tenant_colegio_1` y `tenant_2005`), con `OK` en
  ambos. El archivo base se regeneró en el mismo momento. `scripts/verify.py`
  corre **1184 pruebas, exit 0** en pytest, Ruff y `pip check` — sin
  ninguna falla pendiente. Solo falta el commit (lo
  hace el usuario) y decidir cuándo hacer `git push origin main`.
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
   completo), desde la pantalla de Asignaciones ya existente. En su momento
   se decidió **sin cambios** en `asistencia_controller.py`,
   `asistencia_repository.py` ni la tabla `asistencia` — ver la sección
   "Extensión: validar la asignación de jornada" más abajo, que sí los
   agregó después, a pedido explícito del usuario.
6. ~~Pruebas de caracterización antes de cada cambio + `scripts/verify.py`.~~
   **Hecho**, ver detalle de verificación abajo.
7. ~~Aplicar la migración a los tenants con `apply_migration.py`.~~
   **Hecho el 2026-09-02**, ver paso 1.

## Extensión: validar la asignación de jornada (posterior al cierre inicial)

Después de cerrar la Fase 1 y aplicar la migración, el usuario preguntó:
"¿si elijo otra materia en preescolar, igual me deja tomar asistencia otra
vez?" La respuesta honesta era **sí**: el diseño original solo creaba la
convención de nombre reservado, sin impedir que se tomara asistencia bajo
cualquier otra asignación del mismo curso. Se le presentó la disyuntiva
(dejarlo como costumbre vs. bloquear con un mensaje) y **eligió bloquear**.

### Diseño

- `app/services/asignacion_academica.py`: nueva función
  `resolver_nivel_y_materia_cursor(cursor, asignacion_id)`, que trae en una
  sola consulta el nivel del curso y el nombre de la materia (join a
  `cursos` y a `materias`), para no pagar dos consultas separadas.
- `app/core/nivel_academico.py`: `asistencia_por_jornada_requerida(nivel)`
  (deriva de `REGLAS_POR_NIVEL`) y `asistencia_rechazada_por_nivel(nivel,
  nombre_materia)`, que combina ambas reglas en una sola función pura:
  solo rechaza cuando el nivel exige jornada **y** la materia no es la
  reservada. Primaria y niveles sin definir nunca rechazan nada.
  `MENSAJE_ASISTENCIA_REQUIERE_JORNADA` es el texto exacto que ve la
  maestra.
- `app/controllers/asistencia_controller.py`: `guardar_asistencia_controller`
  resuelve nivel y materia justo después de resolver la asignación
  académica, y si `asistencia_rechazada_por_nivel` es verdadero, devuelve
  `{"error": ...}` **antes** de tocar `borrar_asistencia_del_lote` o
  `insertar_asistencia` — no se escribe nada. Es un 200 lógico con error en
  el cuerpo, igual que el resto de reglas de dominio de este programa
  (planilla, boletín), no una `HTTPException`.
- **Costo medido**: una consulta de solo lectura más por guardado de
  asistencia, dentro de la misma conexión ya abierta. El perfil de
  conexiones (2 para admin, 3 para profesor) no cambia.

### Verificación de la extensión

- Archivos modificados: los tres de arriba.
- Pruebas nuevas: 3 en `tests/test_asistencia_validaciones.py` (rechaza
  materia normal en preescolar, acepta la asignación de jornada, no rechaza
  nada en primaria), 3 en `tests/test_asistencia_caracterizacion.py`
  (conteo de consultas actualizado de 2/5 a 3/6, perfil de conexiones sin
  cambio en el rechazo, contrato HTTP 200 con error), 2 en
  `tests/test_asignacion_academica.py`, 5 en `tests/test_nivel_academico.py`.
  Los índices de consulta (`cursor.calls[N]`) de varias pruebas existentes
  de `test_asistencia_caracterizacion.py` se recalcularon para la nueva
  consulta intermedia.
- `scripts/verify.py`: **1183 pruebas, exit 0** (subió de 1171; +12
  nuevas), Ruff y `pip check` correctos.
- `git diff --check`: exit 0.
- Frontend también actualizado: ver
  `frontend-react/docs/funcionalidades/NIVEL_ACADEMICO.md`, sección
  equivalente — la pantalla de Asistencia ahora distingue este `{"error"}`
  del éxito real y se lo muestra a la maestra en vez de festejar un
  guardado que no ocurrió.

## Extensión: excepción al cruce de horario (corrige un error del asistente)

El usuario reportó, al intentar crear la asignación "Asistencia diaria" con
el horario completo de la jornada, un error real del sistema: *"El profesor
ya tiene una clase asignada en ese horario y ese día."* Esto contradecía lo
que se había afirmado antes en esta conversación (que ningún mecanismo
comparaba cruces de horario entre materias distintas del mismo profesor).

**Era un error de análisis, no un cambio del sistema.** Existe una segunda
función de validación, `verificar_cruce_horario` (y su gemela
`verificar_cruce_horario_editar`), en `app/controllers/asignacion_controller.py`,
que **no se había inspeccionado** al responder antes. A diferencia de
`validar_horario_unico` (que solo bloquea una repetición exacta de
profesor+curso+**materia**+día+horas), esta función sí compara **cualquier
solapamiento real de rango horario**, sin importar la materia — y lo hace
dos veces: una para el profesor, otra para el curso (salón):

```python
if h_inicio_db < hora_fin_nueva and h_fin_db > hora_inicio_nueva:
    return True  # los dos rangos se solapan
```

Como "Asistencia diaria" está pensada para cubrir todo el bloque de la
jornada (ej. 06:30-12:30), se solapa **por diseño** con las materias reales
del mismo profesor y del mismo curso — la validación general la rechazaba
correctamente según su propia lógica, pero esa lógica no debía aplicarle a
esta asignación en particular.

### Diseño

Se presentaron dos caminos al usuario: (a) buscar manualmente un hueco
horario libre para la asignación de jornada, sin tocar código; o (b) que el
sistema reconozca la asignación reservada y no le aplique el cruce. **Eligió
(b).**

- `app/repositories/asignaciones_repository.py`: nueva función
  `leer_nombre_materia(cursor, materia_id)`, una consulta puntual por id.
- `app/controllers/asignacion_controller.py`: en `asignar_profesor_controller`
  y en `editar_asignacion_controller`, justo antes de las dos llamadas a
  `verificar_cruce_horario`/`verificar_cruce_horario_editar`, se resuelve el
  nombre de la materia y, si `es_asignacion_de_jornada(nombre_materia)` es
  verdadero, **ambas** verificaciones de cruce se omiten. Las demás
  validaciones (rango institucional, coherencia con la jornada del curso)
  **se conservan** — solo se exceptúa el cruce con otras asignaciones.

### Verificación

- Archivos modificados: los dos de arriba.
- Pruebas nuevas: 2 en `tests/test_asignaciones_estudiantes_caracterizacion.py`
  (crear y editar la asignación de jornada con solapamiento real, sin
  rechazo). Pruebas existentes actualizadas: el conteo de consultas del
  camino feliz de creación subió de 12 a 13 (una consulta más, de solo
  lectura, dentro de la misma conexión), y los índices de varias pruebas de
  cruce/edición se recalcularon para la nueva consulta intermedia.
- `scripts/verify.py`: **1185 pruebas, exit 0** (subió de 1183; +2 nuevas),
  Ruff y `pip check` correctos.
- `git diff --check`: exit 0.
- Nota para quien continúe: no se modificó `verificar_cruce_horario` en sí
  ni su función gemela — ambas siguen protegiendo a todos los demás
  dominios exactamente igual que antes. La excepción vive enteramente en el
  punto donde se llaman, condicionada por nombre de materia reservado.

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
- `scripts/verify.py` en este punto del cierre inicial: **1171 pruebas,
  exit 0** (subió de 1140; +31 nuevas); las dos extensiones posteriores
  (asistencia y cruce de horario, documentadas arriba) lo llevaron a
  **1185**. Ruff y `pip check` correctos en todo momento. **Cero fallas** —tras
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

## Extensión: primaria también fuerza su tipo de evaluación

El usuario probó Planilla en un curso de primaria y notó que el selector de
tipo de evaluación seguía apareciendo (comportamiento original: primaria
era "libre"). Pidió que primaria dejara de ser libre también, igual que
preescolar.

### Diseño

Cambio mínimo gracias a que el diseño ya centralizaba la regla: en
`REGLAS_POR_NIVEL` (`app/core/nivel_academico.py`), el
`tipo_evaluacion_forzado` de `"primaria"` pasó de `None` a `"numerica"`.
Ningún otro archivo de producto cambió — `resolver_tipo_evaluacion`,
`planilla_controller.py` y `boletin_controller.py` ya consultaban esa tabla
en vez de tener la regla escrita a mano, así que heredaron el nuevo
comportamiento sin tocarlos.

**Lo único que sigue siendo libre es un curso sin `nivel` definido**
(`NULL`): ese caso no está en `REGLAS_POR_NIVEL`, así que
`tipo_evaluacion_forzado` devuelve `None` y se conserva el comportamiento
anterior a toda esta funcionalidad. Es una transición gradual: mientras un
curso no se clasifique, no cambia nada; en cuanto se marca preescolar o
primaria, su tipo de evaluación queda fijo.

### Verificación

- Archivo modificado: `app/core/nivel_academico.py` (una palabra: `None` →
  `"numerica"`, más el docstring).
- Pruebas actualizadas: `test_primaria_no_fuerza_nada` →
  `test_primaria_fuerza_numerica`; `test_primaria_respeta_lo_solicitado` y
  `test_primaria_sin_solicitud_cae_a_numerica` se fusionaron en
  `test_primaria_ignora_lo_que_pida_el_cliente`, todas en
  `tests/test_nivel_academico.py`. En `tests/test_planilla_controlador.py`
  y `tests/test_boletin_caracterizacion.py`, las pruebas que antes se
  llamaban "primaria respeta lo solicitado" ahora se llaman "primaria
  fuerza numérica aunque pidan desarrollo" y verifican exactamente eso.
- Las pruebas de asistencia (`asistencia_rechazada_por_nivel`,
  `asistencia_por_jornada_requerida`) **no cambiaron**: esa regla sigue
  aplicando solo a preescolar, es independiente del tipo de evaluación.
- `scripts/verify.py`: **1184 pruebas, exit 0** (bajó de 1185 a 1184 por la
  fusión de dos pruebas en una; el número de aserciones cubiertas no
  disminuyó). Ruff y `pip check` correctos.
- `git diff --check`: exit 0.
- Frontend actualizado en paralelo: ver
  `frontend-react/docs/funcionalidades/NIVEL_ACADEMICO.md`, sección
  equivalente.
