# Funcionalidad: "Mi curso" del director de grupo — Backend

## Control

- Estado: **pasos 1 y 2 construidos el 2026-11-07; paso 3 (backend con
  migración) construido el mismo día y probado en una rama de Neon; falta
  aplicar la migración en producción.** Paso 4 pendiente.
- **Este es el documento principal.** La pantalla está en
  `frontend-react/docs/funcionalidades/MI_CURSO_DIRECTOR.md`.
- Tipo: función nueva de producto. No es un módulo de `docs/modularizacion/`.
- Repos afectados: este (pasos 1 y 3) y `frontend-react` (pasos 2 y 4). **El
  backend va primero** en cada parte. El paso 3 trae migración.
- Riesgo: medio. El paso 1 abre a un profesor datos de otros profesores (con
  guarda nueva en el servidor) y el paso 3 crea una tabla.
- Última actualización: 2026-11-07.

## Objetivo

Pedidos del usuario, 2026-11-07:

1. «que cada director de grupo pueda ver el ranking general de los puestos y
   sus notas y sus inasistencias, ahí mismo en gestión boletín» (la pantalla
   Boletín Final del profesor, `/ingreso-boletin`). Aprobó el diseño: «así
   mismo por ahora».
2. «agregar ahí mismo, en la misma fila del estudiante, la caja de observación
   final que aparece en el boletín, para que cada director lo llene desde ahí».

## Lo que hay hoy

- `cursos.director_grupo_id` existe: se asigna en el formulario de Cursos, se
  imprime en el boletín y el observador ya lo usa como permiso
  (`app/core/firma_observador.py: puede_tomar_firma`). Ver `DIRECTOR_GRUPO.md`.
- **Puesto:** `boletin_repository.leer_puesto_en_el_curso` promedia
  (`AVG`) las `boletin_cabecera.definitiva` **guardadas** del estudiante en el
  periodo y rankea con `RANK()`. Solo se lee por `/boletines/admin/generar`
  (solo admin).
- **Inasistencias:** `estudiantes_repository.contar_inasistencias_por_periodo`
  cuenta por estudiante (`estado ILIKE 'ausente'`), no por curso.
- **Observación general del boletín: no se guarda.** `BoletinImprimible` la
  deja editable en pantalla (`contentEditable`) y se pierde al cerrar
  (`frontend-react/docs/modularizacion/BOLETINES.md`).
- Un profesor solo lee sus propias asignaciones (`require_asignacion_access`).

## Decisiones

- Solo ven y escriben **el director de ese curso** (profesor de la sesión =
  `cursos.director_grupo_id`) **y el admin**. Lo valida el servidor; la
  pantalla solo esconde la pestaña.
- Año lectivo activo, como el resto del perfil profesor.
- Puesto y notas salen de lo **guardado** en el boletín. Se informa, por
  materia, cuántos estudiantes faltan por guardar.
- Una petición por curso y periodo, con consultas agrupadas (sin una consulta
  por estudiante). Ver `docs/ESCALABILIDAD.md`.

## Plan por pasos (uno a la vez, con visto bueno del usuario)

### Paso 1 — Backend: lectura de "Mi curso" (sin migración)

- `GET /director-grupo/cursos`: cursos del año activo que dirige el
  profesor de la sesión (`[{id, nombre, jornada, nivel}]`). Admin: lista vacía
  (no usa esa pantalla).
- `GET /director-grupo/cursos/{curso_id}/{periodo}`, con guarda nueva
  `require_director_de_curso(curso_id, current_user)` en
  `app/core/permissions.py`: admin, o profesor que dirige ese curso del año
  activo; si no, `403`. Responde:

  ```json
  {
    "curso": {"id": 5, "nombre": "QUINTO A", "jornada": "Mañana", "nivel": "primaria"},
    "periodo": 2,
    "total_rankeados": 30,
    "materias": [
      {"asignacion_id": 55, "materia": "LENGUAJE", "profesor": "Lina Torres",
       "tipo_evaluacion": "numerica", "guardados": 28, "total": 30}
    ],
    "estudiantes": [
      {"estudiante_id": 101, "nombre": "Ana", "apellido": "Pérez", "puesto": 1,
       "promedio": 4.65, "notas": {"55": {"definitiva": 4.8, "guardada": true}},
       "inasistencias": {"periodo": 2, "anio": 5}}
    ]
  }
  ```

  `definitiva` es la guardada o, si no hay o es 0, el promedio de la planilla,
  como el boletín impreso; `guardada` dice si el profesor ya guardó. El puesto y
  el promedio solo cuentan lo guardado.

  Ordenada por puesto; quien no tiene puesto (nada guardado) va al final, por
  apellido.
- Archivos (construido): router nuevo `app/routes/director_grupo.py`
  (prefijo `/director-grupo`, registrado en `app/main.py`), controlador
  `app/controllers/director_grupo_controller.py`, repositorio
  `app/repositories/director_grupo_repository.py`, permiso en
  `app/core/permissions.py` y prueba `tests/test_director_grupo.py`. **No vive
  en `boletines.py`**: esas rutas tienen guardias de caracterización que fijan
  sus cuatro entradas y su SQL, y esto es otra vista. Documentado en
  `API_ENDPOINTS.md`, `ROLES_PERMISOS_BACKEND.md` y `CAMBIOS_BACKEND.md`.
- Pruebas mínimas: el director ve su curso; un profesor que no lo dirige
  recibe `403` (aunque dé clase en ese curso); admin ve; un curso de otro año
  no sale; preescolar; materias sin guardar cuentan bien.

#### Avance del paso 1 (2026-11-07)

- Construido y probado con dobles: 24 pruebas nuevas; `scripts/verify.py`
  con 3108 pruebas, ruff y pip check correctos.
- Las guardias que enumeran los repositorios (asistencia, dashboard, notas,
  planilla, ventas: de 23 a 24) y los consumidores de `profesor` anotan el
  repositorio nuevo.
- Comprobado contra la base real el 2026-11-07, con permiso del usuario, en
  una sesión `readonly` y solo en el Colegio Demo (`tenant_colegio_1`): el
  curso con más estudiantes (7, 2 materias, periodo 1) dio lo mismo que el
  boletín del admin estudiante por estudiante: puesto 7/7, definitiva por
  materia 7/7 e inasistencias 7/7. Cada consulta tarda ~60 ms.
- En el Demo ningún curso tiene director, así que el permiso y "cursos
  dirigidos" solo se ejecutaron con un profesor inexistente (corren sin error
  y no devuelven nada). Para probar la pantalla (paso 2) hay que asignar un
  director a un curso del Demo desde Cursos.

### Paso 2 — Pantalla: pestaña "Mi curso (director de grupo)"

Ver el documento de la pantalla. Construido el 2026-11-07 con las dos lecturas
del paso 1; sin cambios en el backend.

### Paso 3 — Backend: observación general guardada (con migración)

- Tabla nueva `boletin_observacion_general`: `estudiante_id`,
  `anio_lectivo_id`, `periodo`, `texto`, `actualizado_por`, `actualizado_en`;
  `UNIQUE (estudiante_id, anio_lectivo_id, periodo)`.
- `PUT /director-grupo/cursos/{curso_id}/{periodo}/observaciones/{estudiante_id}`
  con la misma guarda; el estudiante debe ser de ese curso.
- Campo nuevo `observacion_general` en la respuesta del paso 1 y en
  `/boletines/admin/generar` (aditivo: lo que ya lee esos endpoints no cambia).
- Migración según `docs/MIGRACIONES.md`: probar en una rama de Neon, aplicar
  con `apply_migration.py` (endpoint directo), regenerar el esquema base y
  subir migración y base juntas. Se aplica en producción **antes** del push.

#### Avance del paso 3 (2026-11-07)

- Largo máximo: **500 caracteres**, aceptado por el usuario («continua» tras
  la propuesta).
- Construido: migración `20261107_boletin_observacion_general.sql`, consultas
  en `director_grupo_repository.py` (leer las del curso, comprobar que el
  estudiante es del curso, `UPSERT`, borrar, leer una para el boletín del
  admin), `PUT .../observaciones/{estudiante_id}`, `observacion_general` en
  «Mi curso» y en `/boletines/admin/generar`.
- La observación se guarda solo del **año activo**; el boletín del admin la lee
  del año que se mira.
- Ruta: `PUT /director-grupo/cursos/{curso_id}/{periodo}/observaciones/{estudiante_id}`
  (no `/boletines/...`, como se pensó al diseñar).
- 2026-11-07, en la rama de Neon `prueba-observacion-general` (copia de
  producción, endpoint directo; el usuario lo hizo en su terminal): simulación
  con todo PENDIENTE, migración aplicada con OK en todos los colegios, esquema
  base regenerado desde `tenant_colegio_1` (solo cambió la tabla nueva, su
  índice, sus dos claves foráneas y la lista: 49 → 50). Prueba con un script
  que se niega a correr contra producción: guardar, reemplazar, «Mi curso», el
  boletín del admin, otro curso (404), más de 500 caracteres (la base lo
  rechaza) y texto vacío (borra): todo bien, y el script borró lo que
  escribió. `scripts/verify.py`: 3124 pruebas, ruff y pip check correctos.
- Pendiente, en este orden: commit (migración + base + código), **aplicar la
  migración en producción antes del push del backend** (el boletín del admin
  nuevo lee la tabla: sin ella daría error), push del backend y comprobar que
  Render quede Live.

### Paso 4 — Pantalla: la caja en cada fila y el impreso

Ver el documento de la pantalla.

## Preguntas abiertas (se hacen justo antes del paso que las necesita)

- Paso 3: largo máximo del texto. Propuesta: 500 caracteres (la caja impresa
  tiene espacio para unos tres renglones).
- Paso 4: en el impreso del admin, la caja sale con lo guardado. ¿El admin la
  puede seguir cambiando en pantalla solo para esa impresión, como hoy?
  Propuesta: sí.

## Riesgos

- Permisos: un profesor que no dirige el curso no debe ver las notas de otros
  profesores. Prueba explícita en el paso 1.
- Rendimiento: el curso entero en una petición con consultas agrupadas.
- Migración: solo crea una tabla; no cambia las que existen.
