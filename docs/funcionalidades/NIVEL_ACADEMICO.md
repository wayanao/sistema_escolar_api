# Funcionalidad: Nivel académico (Preescolar y Primaria) — Backend

## Control

- Estado: **Fase 1 en curso.** Pasos 1 (columna + validación) y 3 (validación
  en planilla) implementados y verificados localmente. Pendiente: aplicar la
  migración real (paso 1b) y el paso 5 (asistencia por jornada).
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
| `POST /cursos`, `PUT /cursos/:id` | Acepta y devuelve `nivel` (opcional; si no llega, queda `NULL`). |
| `POST /notas` (planilla) | Deja de confiar ciegamente en `tipo_evaluacion` del cliente: lo valida/fuerza según el nivel del curso de la asignación. |
| `POST /asistencia` | Sin cambio de contrato. |

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
| Regla solo en pantalla, sin respaldo en el servidor | Validación obligatoria en `planilla_controller` antes de guardar. |
| Repetir la condición por nivel en varios archivos | `REGLAS_POR_NIVEL` centralizada. |
| Curso que cambia de nivel a mitad de año con historial mixto | La regla nueva aplica solo hacia adelante; nada histórico se recalcula. |
| Migración multi-tenant | Se aplica con el runner ya probado (`apply_migration.py`), igual que las 31 anteriores. |

## Plan de fases (backend)

1. ~~Migración: columna `nivel` en `cursos`.~~ **Hecho.**
   `migrations/20260901_cursos_nivel_academico.sql`: `ADD COLUMN IF NOT
   EXISTS nivel VARCHAR(20)`, restricción `chk_cursos_nivel` que solo admite
   `NULL`, `preescolar` o `primaria`, e índice `idx_cursos_nivel`.
   **Pendiente, requiere al usuario**: aplicar esta migración al schema de
   referencia (`tenant_colegio_1`) con `apply_migration.py` y luego
   regenerar `migrations/base/20260813_esquema_base_tenant.sql` con
   `scripts/generar_esquema_base.py --schema tenant_colegio_1`. No se hizo
   aquí porque requiere acceso a la base de datos real, fuera del alcance de
   este asistente sin autorización explícita adicional. Hasta que se haga,
   `scripts/verify.py` falla exactamente en
   `tests/test_esquema_base.py::test_la_base_incorpora_todas_las_migraciones_de_tenant`,
   con el mensaje que indica este mismo paso — es la señal esperada, no un
   error del código.
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
4. Confirmar si `boletin_controller`/`boletin_repository` necesitan la misma
   validación. **Sin empezar.**
5. Documentar la convención de "asignación de jornada" para que el
   administrador la cree desde la pantalla de Asignaciones ya existente.
   **Sin empezar.**
6. Pruebas de caracterización antes de cada cambio + `scripts/verify.py`.
   **En curso**, ver detalle de verificación abajo.
7. Aplicar la migración a los tenants con `apply_migration.py`. **Sin
   empezar**, requiere autorización explícita y acceso real cuando el
   usuario decida desplegar.

### Verificación de los pasos 1 (código), 2 y 3

- Archivos nuevos: `app/core/nivel_academico.py`,
  `migrations/20260901_cursos_nivel_academico.sql`,
  `tests/test_nivel_academico.py`, `tests/test_asignacion_academica.py`.
- Archivos modificados: `app/services/asignacion_academica.py` (nueva
  función `resolver_nivel_curso_cursor`), `app/controllers/planilla_controller.py`
  (usa las dos funciones nuevas), `tests/test_planilla_controlador.py` (3
  pruebas nuevas: preescolar fuerza desarrollo, primaria respeta lo
  solicitado, curso sin nivel mantiene el comportamiento anterior),
  `tests/test_planilla_caracterizacion.py` (conteo de consultas actualizado
  de 4/5 a 5/6, con el motivo documentado en el propio test).
- `scripts/verify.py`: **1153 pruebas pasaron** (subió de 1140; +13 nuevas),
  Ruff correcto, `pip check` correcto. **1 prueba falla**, la esperada del
  paso 1b (`test_la_base_incorpora_todas_las_migraciones_de_tenant`).
- `git diff --check`: exit 0. El diff pertenece exclusivamente a esta
  funcionalidad; no se tocó ningún otro dominio.
- Nada de esto se commiteó ni se hizo push. Ningún acceso a producción ni a
  ningún tenant real.

## Preguntas abiertas (decisión del usuario antes de implementar)

- ¿La asignación "Jornada" debe aparecer en el boletín como una materia más,
  o debe excluirse de ahí?
- ¿El nivel lo define siempre el administrador manualmente, o se quiere
  alguna sugerencia automática a partir del nombre del curso?
- ¿Se empieza con un colegio piloto antes de dejarlo disponible a todos los
  tenants?

## Entrega para el siguiente chat

- Última acción terminada: pasos 1 (código de la migración), 2 y 3 de la
  Fase 1, verificados localmente (ver arriba). Nada commiteado ni publicado.
- Archivos pendientes de commit (el usuario decide cuándo):
  `app/core/nivel_academico.py`,
  `migrations/20260901_cursos_nivel_academico.sql`,
  `tests/test_nivel_academico.py`, `tests/test_asignacion_academica.py`,
  y los cambios en `app/services/asignacion_academica.py`,
  `app/controllers/planilla_controller.py`,
  `tests/test_planilla_controlador.py`,
  `tests/test_planilla_caracterizacion.py`.
- Riesgo abierto conocido: `scripts/verify.py` falla 1 de 1154 pruebas hasta
  que se aplique la migración al schema de referencia y se regenere el
  esquema base (paso 1b). No lo marques como cumplido sin hacerlo.
- Siguiente acción exacta: el usuario decide entre (a) continuar con el
  paso 4 (revisar boletín) y el paso 5 (asistencia por jornada) antes de
  tocar la base de datos real, o (b) aplicar primero la migración real al
  schema de referencia para cerrar el paso 1b. Ninguna de las dos requiere
  esperar a la otra.
- Las 3 preguntas abiertas siguen sin respuesta del usuario.
