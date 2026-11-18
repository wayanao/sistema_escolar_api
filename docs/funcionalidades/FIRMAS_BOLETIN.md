# Firmas guardadas para el boletín

Documento principal. Pedido del usuario el 2026-11-12: "añadir una firma para
admin, en donde puedan salir todos los boletines firmados", y después
"¿se podría para profesores también?".

## Qué había

El boletín impreso del admin (`BoletinImprimible.jsx` en el frontend) termina
con dos rayas vacías, **"Director(a)"** y **"Director de Grupo"**, y se firma a
mano hoja por hoja. Los certificados ya guardan nombre, cargo y documento de
quien firma en la identidad institucional (`configuracion_extra`), pero no una
imagen de la firma.

## Decisiones del usuario (2026-11-12)

1. Firman **el rector(a)** (raya "Director(a)") y **el director de grupo**
   del curso (raya "Director de Grupo"). Los profesores de cada materia no
   firman el boletín.
2. La firma del rector(a) la sube **el admin**, en "Identidad institucional".
3. La firma de cada profesor la pone **el mismo profesor desde «Mi curso»**,
   la pantalla de los directores de grupo. El admin no puede subir la firma
   de un profesor: así nadie pone la firma de otro sin que lo sepa.
4. En los certificados, la firma del rector(a) es **opcional**: el admin
   elige si sale.
5. "Todos los boletines" se entendió como "que cada boletín salga firmado".
   Imprimir el curso entero de una vez queda como idea aparte, sin decidir.

## Decisiones técnicas

- **Tablas nuevas, no columnas.** `firma_institucional` (una sola fila) y
  `firmas_profesores` (una por profesor). La identidad institucional la lee
  cualquier usuario en cada impreso (`GET /branding`), y la ficha del profesor
  sale en otras pantallas: una columna con la imagen viajaría en esas lecturas,
  al alcance de quien no debe verla.
- **La imagen va en la base (`bytea`), no en `/uploads`.** Igual que la firma
  del acudiente (`FIRMA_OBSERVADOR.md`). Los archivos de `branding/<tenant>/`
  los puede abrir cualquier usuario del colegio; en la base, la firma solo sale
  por las rutas que la protegen.
- **PNG de hasta 100 KB**, revisado con la misma función de la firma del
  acudiente (`decodificar_imagen`), con mensajes propios. El frontend convierte
  la foto o el trazo en un PNG pequeño antes de enviarlo.
- **Quién ve qué:**
  - la firma del rector(a): solo el admin (`/firmas/institucional` y el
    boletín del admin);
  - la firma de un profesor: ese profesor (`/firmas/mia`) y el admin, solo
    dentro del boletín que genera. Los demás profesores, nunca.
- El `id` del profesor sale siempre de la sesión, nunca de la URL ni del
  cuerpo.
- Si el director de grupo cambia, el boletín usa la firma del director
  actual del curso, igual que ya pasa con su nombre.
- Si cambia la firma, los boletines que se impriman después salen con la
  nueva. Lo ya impreso no cambia.

## Base de datos

Migración `migrations/20261112_firmas_boletin.sql`. Dos tablas nuevas; ninguna
existente cambia.

| Tabla | Clave | Columnas |
| --- | --- | --- |
| `firma_institucional` | `id` = 1 (`CHECK`) | `imagen_png bytea` (1 a 102400 bytes), `actualizado_en`, `actualizado_por_id` (admin, sin clave foránea) |
| `firmas_profesores` | `profesor_id` → `profesor(id)` `ON DELETE CASCADE` | `imagen_png bytea` (1 a 102400 bytes), `actualizado_en` |

## API

Router `app/routes/firmas.py`, prefijo `/firmas`, protegido por
`get_current_user`.

| Ruta | Quién | Qué hace |
| --- | --- | --- |
| `GET /firmas/institucional` | admin | La firma del rector(a). |
| `PUT /firmas/institucional` | admin | Guarda o reemplaza. Cuerpo `{imagen}`. |
| `DELETE /firmas/institucional` | admin | La quita. |
| `GET /firmas/mia` | profesor | Su propia firma. |
| `PUT /firmas/mia` | profesor | Guarda o reemplaza la suya. Cuerpo `{imagen}`. |
| `DELETE /firmas/mia` | profesor | Quita la suya. |

- Todas responden `{imagen, actualizado_en}`: `imagen` es
  `data:image/png;base64,...` o `null`; `actualizado_en` en ISO o `null`.
- Un profesor en `/firmas/institucional` recibe `403` ("No tienes los permisos
  necesarios"). El admin en `/firmas/mia`, `403` ("Solo un profesor puede
  guardar aquí su propia firma.").
- Imagen que no es un PNG aceptable: `422` con "La firma no es una imagen
  válida. Vuelve a firmar o sube otra foto." o "La firma pesa demasiado.
  Vuelve a firmar o sube otra foto.".
- `GET /boletines/admin/generar/{estudiante_id}/{periodo}` trae además
  `firma_institucional` y `firma_director_grupo` (data URL o `null`). Una
  consulta más (de 5 a 6, siempre fija).

## Pasos

1. **Backend** (este repo): migración, `/firmas` y las firmas en el boletín
   del admin. **Construido el 2026-11-12, sin commit.** El usuario aplicó la
   migración en una rama de Neon y regeneró la base desde `tenant_colegio_1`
   (44 tablas): el cambio fue solo las dos tablas nuevas y la clave hacia
   `profesor`. `test_profesores_caracterizacion.py` sube de 7 a 8
   `REFERENCES profesor(id)`, con la clave nueva declarada con su
   `ON DELETE CASCADE`. `verify.py`: 3191 pruebas, ruff y pip check correctos.
   **Migración aplicada en producción el 2026-11-12** (el usuario, con
   `apply_migration.py`). Falta el commit y el push del backend: ya se pueden
   hacer, porque el frontend de hoy ignora los campos nuevos del boletín.
2. **Identidad institucional** (frontend): cuadro "Firma del rector(a)" para
   que el admin la suba con una foto o la firme con el dedo. **Construido el
   2026-11-12, sin commit** (detalle en
   `frontend-react/docs/funcionalidades/FIRMAS_BOLETIN.md`).
3. **«Mi curso»** (frontend): un solo botón grande, "Firmar con el dedo" (el
   recuadro del observador), y la foto como enlace. **Construido el
   2026-11-12, sin commit.**
4. **Boletín** (frontend): cada firma sobre su raya; sin firma, la raya queda
   para firmar a mano y el admin ve un aviso antes de imprimir. **Adelantado
   al paso 3 y construido el 2026-11-12, sin commit.**
5. **Certificados** (frontend): casilla «Con la firma del rector(a)»,
   desmarcada en cada certificado. **Construido el 2026-11-12, sin commit.**

## Ampliación: la firma del director en el observador (2026-11-18)

Pedido del usuario: "la firma del profesor puede salir en el observador que
imprime admin desde el observador del estudiante". Se le explicó que hoy solo
guardan firma los directores de grupo (desde «Mi curso») y que el observador
general termina con la raya «Firma del Director de Grupo». Confirmó las tres
cosas que se le preguntaron:

1. La firma es la del **director de grupo**, sobre su raya del pie. Que cada
   profesor firme sus propias anotaciones queda fuera: los que no son
   directores no tienen dónde guardar su firma.
2. **Se amplía el permiso de la decisión técnica "Quién ve qué"**: el admin ve
   la firma del director de grupo en el boletín **y en el observador** que
   imprime. Sigue siendo solo el admin y solo en documentos del colegio; un
   profesor nunca ve la firma de otro.
3. En el mismo cambio, el observador impreso muestra también las firmas del
   acudiente (paso 3 de `FIRMA_OBSERVADOR.md`).

- Ruta nueva `GET /firmas/director-grupo/{estudiante_id}`, solo admin, con
  `anio_lectivo_id` opcional: el curso sale de la matrícula de ese año, como
  en el boletín (`_curso_del_estudiante`). Una consulta
  (`leer_firma_del_director_de_grupo`). Sin migración.
- Es una ruta aparte, y no un campo más de `GET /observador/{id}/firmas`,
  porque esa responde una lista (cambiarla rompería su contrato) y porque la
  usan también los profesores.
- En el impreso: con firma, la raya lleva el nombre del director y su firma;
  sin firma, su nombre y la raya para firmar a mano, con un aviso para el
  admin antes de imprimir; sin director, la raya de siempre.

## Orden de publicación

1. Aplicar la migración en producción (todos los colegios).
2. Push del backend. Si el backend llega antes que las tablas, el boletín del
   admin falla en todos los colegios.
3. Push del frontend.
