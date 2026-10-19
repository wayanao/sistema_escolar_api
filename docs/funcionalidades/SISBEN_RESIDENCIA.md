# Funcionalidad: SISBÉN y lugar de residencia — Backend

## Control

- Estado: **Diseñado (paso S0, 2026-10-19), nada implementado.**
- Tipo: Función nueva de producto. No es una capa del programa de
  modularización de `docs/modularizacion/` y no debe confundirse con una.
- Repos afectados: este repo (`sistema_escolar_api`) y `frontend-react`. Ver
  también `frontend-react/docs/funcionalidades/SISBEN_RESIDENCIA.md`, que
  cubre la pantalla.
- Riesgo: **Medio.** Hay migración en la tabla `estudiantes` de todos los
  tenants, pero son columnas nuevas, vacías y opcionales: no cambia ningún
  cobro, permiso ni dato existente.
- Fecha deseada: **antes de las matrículas de noviembre de 2026**, para no
  volver a pedirle estos datos a cada familia después.
- Última actualización: 2026-10-19.

## Objetivo

Que la ficha del estudiante (la que se llena al crear, al editar y al
matricular desde una admisión) guarde:

1. Si la familia tiene SISBÉN y su clasificación.
2. El lugar donde vive el estudiante, por partes, en vez de una sola caja de
   "Dirección".

## Diagnóstico (verificado en el código el 2026-10-19)

- `estudiantes` no tiene nada de SISBÉN. `grep -ri sisben` en los dos repos
  no encuentra nada.
- La dirección es una sola columna libre: `estudiantes.direccion`,
  `varchar(255)`.
- Todo el router `app/routes/estudiantes.py` exige admin
  (`get_current_active_admin`): el profesor no ve estos datos.
- `GET /estudiantes/{id}` lee con `SELECT *` (`estudiantes_repository.
  obtener_estudiante`) y nombra las columnas con `cursor.description`: las
  columnas nuevas salen solas en la respuesta, sin tocar esa ruta.
- `POST` y `PUT /estudiantes` usan `EstudianteCreate` y escriben **34 valores
  por posición** (`insertar_estudiante`, `actualizar_estudiante`). La misma
  tupla la arman `estudiante_controller.py` (crear y editar) y
  `anios_lectivos_controller._valores_globales_estudiante` (matricular desde
  una admisión, nuevo o exalumno). Un desplazamiento en esa tupla guardaría un
  dato en la columna de otro sin ningún error.
- `PUT /estudiantes/{id}` reemplaza la ficha entera: lo que no llega queda
  vacío. El frontend, al editar, devuelve todo lo que leyó del `GET`
  (`normalizarEstudianteParaEdicion`), pero una pestaña abierta antes del
  cambio, o el formulario viejo al matricular a un exalumno, no traería los
  campos nuevos.

## Decisiones ya tomadas (con el usuario, 2026-10-19)

1. **SISBÉN con grupo, subgrupo y nivel** (el usuario eligió "los dos"):
   - ¿Tiene SISBÉN?: sin dato, sí o no.
   - Grupo del SISBÉN IV: A, B, C o D.
   - Subgrupo del SISBÉN IV, según el grupo: A1 a A5, B1 a B7, C1 a C18,
     D1 a D21.
   - Nivel del SISBÉN III (el anterior), para quien solo tenga ese
     certificado. Valores: ver "Preguntas abiertas".
2. **Lugar de residencia en campos separados**: dirección (calle o carrera y
   número), barrio o vereda, municipio, zona (urbana o rural) y punto de
   referencia.
3. **Lo que ya está escrito en `direccion` no se toca.** No se parte
   automáticamente en barrio y municipio: cada quien lo escribió a su manera.
4. **Una pestaña vieja no borra los datos nuevos** (propuesta aceptada con la
   del diseño): si en el cuerpo no llega **ninguno** de los ocho campos
   nuevos, se quedan como estaban. Si llega alguno, se reemplazan los ocho
   (lo que falte queda vacío), para que el SISBÉN nunca quede a medias. Es la
   misma idea que protege `cuestionario` en las admisiones.

## Diseño de datos

Migración nueva `migrations/<fecha>_estudiantes_sisben_residencia.sql`, solo
`ADD COLUMN IF NOT EXISTS` y `CHECK`, todo opcional (`NULL` = sin dato):

| Columna | Tipo | Regla |
|---|---|---|
| `sisben` | `boolean` | `NULL` sin dato, `TRUE` sí, `FALSE` no |
| `sisben_grupo` | `varchar(1)` | `A`, `B`, `C` o `D` |
| `sisben_subgrupo` | `varchar(3)` | empieza por la letra del grupo |
| `sisben_nivel` | `smallint` | ver "Preguntas abiertas" |
| `barrio` | `varchar(150)` | texto libre |
| `municipio` | `varchar(100)` | texto libre |
| `zona_residencia` | `varchar(10)` | `urbana` o `rural` |
| `punto_referencia` | `varchar(255)` | texto libre |

Reglas en la base (`CHECK`), como defensa por si algo salta la API:

- valores permitidos de grupo, nivel y zona;
- el subgrupo exige grupo y empieza por su letra;
- sin SISBÉN (`sisben` distinto de `TRUE`) no hay grupo, subgrupo ni nivel.

El rango exacto de cada subgrupo (A1 a A5, etc.) lo valida la API, con
mensaje en español; en la base basta el formato.

`direccion` no cambia: sigue siendo la calle o carrera y el número.

## Contrato de la API

- `EstudianteCreate` suma los ocho campos opcionales. Un `model_validator`
  aplica las reglas de arriba y el rango del subgrupo, con mensajes claros
  (por ejemplo, "El subgrupo B9 no existe: el grupo B va de B1 a B7").
- `POST /estudiantes`: si llegan, se guardan; si no, quedan vacíos.
- `PUT /estudiantes/{id}`: decisión 4 (ninguno llega → se quedan como
  estaban; alguno llega → se reemplazan los ocho).
- `POST /admisiones/{id}/matricular`: igual que el `PUT` para el exalumno que
  vuelve, e igual que el `POST` para el aspirante nuevo.
- `GET /estudiantes/{id}`: trae las columnas nuevas sin cambios de código
  (`SELECT *`). Respuesta solo con claves de más: no rompe a nadie.

**Cómo se escribe sin tocar la tupla de 34.** Las dos sentencias de hoy
(`insertar_estudiante` y `actualizar_estudiante`) quedan letra por letra. Se
agrega una sola función de repositorio, `guardar_sisben_y_residencia`, que
hace un `UPDATE` de las ocho columnas, y se llama en la misma transacción
**solo si llegó alguno de los ocho campos** (`model_fields_set`). Se usa en
los cuatro caminos que escriben la ficha: crear, editar, aspirante nuevo y
exalumno que vuelve. Motivos:

- no se arriesga el orden de la tupla, que es el punto más frágil;
- mientras el frontend viejo siga publicado, nadie manda los campos nuevos y
  ninguna petición toca las columnas nuevas. Eso permite subir el backend
  **antes** de aplicar la migración en producción sin que nada falle (ver
  "Orden de publicación").

## Plan por pasos (cada uno con autorización explícita)

- **S0 — Diseño** (este documento). Sin código.
- **S1 — Backend.** Pruebas primero (deben fallar), después la migración, el
  esquema, el validador, `guardar_sisben_y_residencia` y las cuatro llamadas.
  Documentar en `docs/API_ENDPOINTS.md`, `docs/BASE_DATOS.md` y
  `docs/CAMBIOS_BACKEND.md`. `tests/test_esquema_base.py` fallará a propósito
  hasta el S2: es la compuerta que exige aplicar y regenerar.
- **S2 — Base de datos (lo hace el usuario).** Probar la migración en una
  rama de Neon (`PENDIENTE` → `OK` → `OMITIDA`), regenerar el esquema base
  desde esa rama, commit de migración, esquema base y código juntos. Después,
  ver "Orden de publicación".
- **S3 — Frontend.** Los campos en el formulario del estudiante. Detalle en el
  documento del frontend.

## Orden de publicación

1. Push del backend (S1 + S2) y esperar a que Render quede **Live**.
2. Aplicar la migración en `tenant_colegio_1` y `tenant_2005` con
   `apply_migration.py` y el `DATABASE_URL` directo.
3. Push del frontend (S3).

Por qué el push va antes de aplicar (igual que el paso E1 de la entrevista de
admisión): un colegio nuevo nace del esquema base y copia el historial de
migraciones de la plantilla. Y por qué no se rompe nada en el rato entre 1 y
2: con el frontend viejo, ninguna petición manda los campos nuevos (ver
"Contrato de la API").

## Fuera de alcance

- Departamento de residencia (ver "Preguntas abiertas").
- Mostrar SISBÉN o barrio en impresos: factura, certificados, boletín. La
  factura sigue mostrando solo `direccion`.
- Filtros, reportes o conteos por SISBÉN o por zona.
- Pedir estos datos en el registro del aspirante (Admisiones): se llenan en
  el formulario de matricular, que es la misma ficha.
- Borrar o partir `direccion`.

## Preguntas abiertas

- **Antes del S1: ¿qué valores tiene el "nivel"?** Propuesta: 1, 2 o 3, que es
  como se nombraba el SISBÉN III para los subsidios. Si el formulario en papel
  del colegio usa otros (por ejemplo, 1 a 6), cambia el `CHECK`.
- **Antes del S1: ¿se pide también el departamento?** Propuesta: no, solo el
  municipio, porque casi todos los estudiantes viven en el mismo
  departamento. Si se quiere, es una columna más en la misma migración;
  después costaría otra migración.

## Entrega para el siguiente chat

- Hecho: S0, el diseño, el 2026-10-19. No hay código de esta funcionalidad.
- Siguiente acción exacta: que el usuario responda las dos "Preguntas
  abiertas" y autorice el S1.
- Prompt para retomar: `docs/funcionalidades/PROMPT_CONTINUACION_SISBEN_RESIDENCIA.md`.
