# Funcionalidad: Nivel académico (Preescolar y Primaria) — Backend

## Control

- Estado: **Propuesta, pendiente de aprobación. Nada implementado.**
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

1. Migración: columna `nivel` en `cursos`; actualizar el esquema base
   documentado.
2. `REGLAS_POR_NIVEL` centralizada, en un módulo propio (a decidir la
   ubicación exacta, ej. `app/core/`).
3. `planilla_controller` valida/fuerza `tipo_evaluacion` según el nivel del
   curso de la asignación.
4. Confirmar si `boletin_controller`/`boletin_repository` necesitan la misma
   validación (ver pendiente arriba).
5. Documentar la convención de "asignación de jornada" para que el
   administrador la cree desde la pantalla de Asignaciones ya existente.
6. Pruebas de caracterización antes de cada cambio + `scripts/verify.py`.
7. Aplicar la migración a los tenants con `apply_migration.py`.

## Preguntas abiertas (decisión del usuario antes de implementar)

- ¿La asignación "Jornada" debe aparecer en el boletín como una materia más,
  o debe excluirse de ahí?
- ¿El nivel lo define siempre el administrador manualmente, o se quiere
  alguna sugerencia automática a partir del nombre del curso?
- ¿Se empieza con un colegio piloto antes de dejarlo disponible a todos los
  tenants?

## Entrega para el siguiente chat

- Última fase terminada: ninguna. Esto es una propuesta, no hay código
  escrito.
- Siguiente acción exacta: esperar aprobación del usuario y respuesta a las
  preguntas abiertas; luego iniciar la Fase 1 (backend), paso 1, con
  verificación antes de seguir al paso 2.
- No hay commit base todavía porque no se ha tocado código de producto.
