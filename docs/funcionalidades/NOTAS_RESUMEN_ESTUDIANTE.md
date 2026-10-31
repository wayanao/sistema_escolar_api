# Funcionalidad: Notas por periodo en el resumen del estudiante — Backend

## Control

- Estado: **completo y publicado el 2026-10-31.**
  - Backend: `a7560e0`, con el paso 0 y el paso 1 juntos; Render Live,
    `/health` en `200`.
  - Pantalla: `f5a573d` en `frontend-react`; Vercel OK.
  - El usuario lo probó en local antes de publicar la pantalla.

  Ver "Avance del paso 1".
- Tipo: mejora del resumen del estudiante (la ficha del admin), que lee
  `GET /estudiantes/{id}/detalles`. No es un módulo de `docs/modularizacion/`.
- **Este es el documento principal.** La pantalla está en
  `frontend-react/docs/funcionalidades/NOTAS_RESUMEN_ESTUDIANTE.md`.
- Repos afectados: este (el cálculo y la respuesta) y `frontend-react` (la
  pantalla). **El backend va primero.** Sin migración.
- Riesgo: bajo. Solo cambia una lectura. No escribe nada ni toca notas,
  boletines o cobros.
- Última actualización: 2026-10-31.

## Objetivo

Que el admin vea en el resumen del estudiante:

- las notas **de cada periodo**, escogiendo el periodo;
- las de **preescolar**, con su carita;
- un "Todo el año";
- las inasistencias de lo que escogió.

## Lo que pasa hoy

`leer_promedios_por_materia` (`app/repositories/estudiantes_repository.py`)
hace `AVG(n.nota)` de todas las celdas del estudiante en el año, por materia:

1. **Mezcla todos los periodos** en un solo promedio, y no hay forma de
   escoger uno.
2. **Preescolar no sale.** Sus celdas guardan la carita en `valoracion` y
   dejan `nota` vacía. El `AVG` de una materia de caritas da `NULL`, y
   `float(None)` hace fallar la sección "notas" entera
   (`_registrar_error_detalle`). Por eso la ficha dice "No hay notas
   registradas" y "Promedio General: 0". **Se confirma con una prueba antes
   de cambiar nada** (paso 1).
3. **No calcula como el reporte parcial:** cuenta los ceros, no aplica los
   porcentajes por tipo de nota y no deja fuera las columnas internas.
4. `contar_inasistencias` cuenta todo el año, aunque `asistencia` guarda el
   `periodo`.

## Fuera de alcance

- **El reporte parcial impreso de preescolar.** Hoy deja la nota de la
  materia vacía. El cálculo nuevo queda en `app/core` para que pueda usarlo
  después, pero cambiarlo es un paso aparte.
- El boletín guardado por el profesor y la planilla, que no cambian.
- Las observaciones, las deudas y el inventario de la ficha.

## Decisiones ya tomadas (con el usuario, 2026-10-31)

| # | Decisión |
|---|---|
| 1 | Se **escoge el periodo**: 1, 2, 3 o 4 |
| 2 | **Preescolar muestra la carita** de cada materia. Sin "Promedio General" con número, porque el boletín de preescolar nunca usa números |
| 3 | Al abrir se ve **el último periodo con notas** |
| 4 | Hay **"Todo el año"**: el promedio de los periodos, no la mezcla de hoy |
| 5 | **Las inasistencias también por periodo**; en "Todo el año", el total |

## La nota de una materia en un periodo

La misma regla del **reporte parcial**, que es la foto de la planilla vigente
(`obtener_reporte_parcial_admin_controller`), más las caritas:

- Se toman las celdas de esa clase en ese periodo, **sin las columnas
  internas** (`mas_alto` y "Desde React", `admite_porcentaje`).
- **Primaria:** el promedio de las notas de 1 a 5. Los ceros no cuentan,
  como en el reporte parcial y en el boletín.
- **Preescolar:** cada carita se pasa a número con la escala de siempre
  (`valor_de_valoracion`). Se promedian, y el resultado es la carita más
  cercana (`valoracion_desde_promedio`), como en la planilla.
- **Con porcentajes activos** en esa clase y periodo, la nota ponderada
  (`calcular_nota_del_periodo`), en los dos niveles.
- **Tipo de la materia:** manda el nivel del curso (`resolver_tipo_evaluacion`).
  En un curso sin nivel, "desarrollo" si alguna celda es carita
  (`tipo_de_evaluacion_de_celdas`).
- Sin ninguna celda que cuente, la materia **no tiene nota** ese periodo.
- Dos decimales, mitad hacia arriba (`_redondear`). La pantalla muestra uno,
  como el reporte parcial.

**Puede no coincidir con el boletín enviado.** Si el profesor cambió notas
después de enviar el boletín, el resumen muestra la planilla de hoy, igual
que el reporte parcial.

### "Todo el año"

- **Por materia:** el promedio de las notas de los periodos que tienen nota
  (los valores de dos decimales). En preescolar, ese promedio pasado a
  carita.
- **Promedio general** de un periodo o del año, solo con las materias
  numéricas: el promedio de sus notas, como hoy se promedian los promedios
  por materia.

### Qué materias salen

Las de la planilla vigente del curso del estudiante en ese año, con la misma
lectura del reporte parcial (`leer_planilla_vigente`):

- sin "ASISTENCIA DIARIA" (`NOMBRE_MATERIA_ASISTENCIA_JORNADA`);
- sin las materias inactivas;
- en otro año, la del curso de su matrícula.

Van en el orden del boletín (`orden_boletin`). Una materia sin notas sale
igual, con "Sin nota".

## Inasistencias

`contar_inasistencias` pasa a contar **por periodo** (`GROUP BY
COALESCE(periodo, 1)`), con la misma regla de hoy: `ILIKE 'ausente'` y, en
el año activo, también las filas sin clase. "Todo el año" es la suma, que da
el mismo número de hoy.

## Cambios de API

`GET /estudiantes/{id}/detalles` (con o sin `anio_lectivo_id`) **suma dos
campos**. No cambia la ruta ni los parámetros:

```json
"notas_por_periodo": {
  "materias": [
    {
      "materia": "MATEMÁTICAS",
      "tipo_evaluacion": "numerica",
      "periodos": {
        "1": {"nota": 3.85, "valoracion": null},
        "2": null,
        "3": null,
        "4": null
      },
      "anio": {"nota": 3.85, "valoracion": null}
    },
    {
      "materia": "DIMENSIÓN COGNITIVA",
      "tipo_evaluacion": "desarrollo",
      "periodos": {
        "1": {"nota": 4.33, "valoracion": "logrado"},
        "2": null,
        "3": null,
        "4": null
      },
      "anio": {"nota": 4.33, "valoracion": "logrado"}
    }
  ],
  "promedio": {"1": 3.85, "2": null, "3": null, "4": null, "anio": 3.85}
},
"inasistencias_por_periodo": {"1": 2, "2": 0, "3": 0, "4": 0, "anio": 2}
```

- `null` significa sin nota.
- `promedio` es `null` cuando no hay ninguna materia numérica con nota.
- **Se conservan `notas`, `promedio_general` e `inasistencias`**, con la
  misma forma, para el frontend de hoy mientras sale el nuevo. Ahora se
  llenan con "Todo el año": las materias numéricas con su nota del año, el
  promedio con un decimal y el total de inasistencias. **Su número cambia a
  propósito** (decisión 4). La consulta vieja `leer_promedios_por_materia`
  se retira.
- La sección sigue degradando sola: si falla el cálculo, `errores.notas`, y
  lo demás llega igual.

## Consultas

Hoy la ficha hace 4 consultas propias, más las deudas
(`test_asignaciones_estudiantes_caracterizacion.py`). Con el cambio:

- las notas: **una lectura de la planilla del año** (todos los periodos a la
  vez, en vez de una consulta por periodo), con el nivel del curso;
- los porcentajes de las clases en los 4 periodos: **una consulta**, más una
  solo si alguna clase los tiene activos;
- las inasistencias: la misma consulta, agrupada por periodo.

Es **una o dos consultas más** al abrir la ficha. A cambio, **cambiar de
periodo en la pantalla no cuesta ninguna petición**, porque llegan todos de
una vez. Se fija con una prueba de conteo antes y después.

## Invariantes

1. Es solo lectura. No escribe nada.
2. La nota de un periodo es la del reporte parcial, más las caritas: un solo
   cálculo, en `app/core`.
3. Una sección que falla no tumba la ficha.
4. Cambiar de periodo no hace otra petición.
5. "Todo el año" en inasistencias da el mismo número de hoy.

## Riesgos y mitigación

| Riesgo | Mitigación |
|---|---|
| El número del año cambia frente a hoy | Es lo pedido (decisión 4); se dice en el aviso de publicación |
| El resumen no coincide con el boletín enviado | Es la planilla de hoy, como el reporte parcial; queda escrito arriba |
| Más consultas al abrir la ficha | Todos los periodos en una sola lectura; prueba de conteo |
| Romper la ficha que está publicada | Los campos viejos siguen, con la misma forma |

## Plan de pasos y orden de publicación

| Paso | Repo | Qué | ¿Lo ven los colegios? |
|---|---|---|---|
| 0 | ambos | Este documento y el del frontend | No |
| 1 | backend | Primero una prueba que muestre el fallo de preescolar. Luego el cálculo en `app/core`, la lectura del año, las inasistencias por periodo, la respuesta y las pruebas de conteo. Push sin migración | Sí: el número del año en la ficha de hoy |
| 2 | frontend | Los botones de periodo, las caritas y las inasistencias del periodo | Sí |
| 3 | ambos | Publicación y prueba en el Colegio Demo, con un estudiante de primaria y uno de preescolar | Sí |

## Preguntas abiertas

Ninguna. Las tres quedaron resueltas el 2026-10-31 (decisiones 3, 4 y 5).

## Avance del paso 1 (2026-10-31)

Construido como en el diseño. El detalle está en `docs/CAMBIOS_BACKEND.md` y
el contrato en `docs/API_ENDPOINTS.md` ("Notas por periodo").

- **Primero se confirmó el fallo de preescolar con el código viejo.**
  `test_detalles_de_preescolar_tumba_la_seccion_de_notas` pasó antes de
  cambiar nada. Ahora es `test_detalles_de_preescolar_muestra_la_carita`.
- **Las inasistencias, en una fila** con `count(*) FILTER` por periodo y el
  total: `(p1, p2, p3, p4, total)`. Un periodo vacío cuenta como el 1, que es
  el valor por defecto de la columna.
- **Las materias** se leen con los mismos filtros del reporte parcial,
  importados de `boletin_repository` (`_curso_del_estudiante` y
  `_materia_visible`), para que no se aparten.
- **Un hallazgo en los datos del Colegio Demo, que no es un error:** el
  estudiante 6 tiene 2 caritas en Educación Física, en un curso de
  **primaria**. Son de antes de clasificar el curso. Como el nivel manda, el
  resumen no las cuenta y deja "Sin nota", lo mismo que la planilla y el
  reporte parcial.

Verificación contra la base del Colegio Demo, con un script que solo lee y
llama al resumen y al reporte parcial reales:

- Primaria (estudiante 1): **0 diferencias** en los 4 periodos. Las
  inasistencias por periodo dan `{1: 4, ..., anio: 4}`.
- Preescolar (estudiante 9, curso de preescolar): Sociales, periodo 1,
  "logrado" (3,50). Es el empate entre "En proceso" y "Logrado", y gana la
  más alta, como en la planilla.
- `scripts/verify.py`: **3076 pasan**; Ruff y `pip check` limpios.

Publicación (2026-10-31): el usuario hizo el commit `a7560e0` y el push. Render
quedó Live, con `/health` en `200`. `GET /estudiantes/1/detalles` da `401` sin
sesión, como antes.

## Entrega para el siguiente paso

Los pasos 1 y 2 están publicados. El paso 3 se cumplió así:

- el usuario probó en local con el estudiante 1 (primaria) y el 9
  (preescolar), y dijo que todo estaba bien;
- después publicó la pantalla (`f5a573d`).

Queda pendiente, solo si se pide, **el reporte parcial impreso de
preescolar** ("Fuera de alcance"). Hoy deja vacía la nota de la materia, y
podría usar `app/core/notas_resumen.py` para mostrar su carita.
