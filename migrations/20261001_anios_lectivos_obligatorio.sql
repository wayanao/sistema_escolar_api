-- Año lectivo, migracion B (el año pasa a ser obligatorio). Fase 1, punto 3
-- de docs/funcionalidades/ANIO_LECTIVO.md.
--
-- La migracion A dejo `anio_lectivo_id` admitiendo NULL en cinco tablas: entre
-- aplicarla y desplegar el codigo que escribe el año, el codigo viejo podia
-- crear filas sin año. Esta migracion cierra esa ventana: rellena lo que haya
-- quedado sin año, pone al dia las matriculas del año activo y vuelve
-- obligatoria la columna. Desde aqui la base de datos misma impide crear un
-- curso, un concepto de pago, una matricula, un pago o una anotacion del
-- observador sin año.
--
-- Se aplica DESPUES de desplegar el codigo de la fase 1, punto 2 (commit
-- df53299), nunca antes: con NOT NULL, el codigo viejo, que no escribe el año,
-- fallaria al crear cualquiera de esas filas. Todo INSERT de app/ en estas
-- tablas ya lo escribe, y tests/test_migracion_anios_lectivos_obligatorio.py
-- lo comprueba. Fuera de app/ quedan dos scripts que insertan sin año y
-- fallarian despues de esta migracion (ver la fase 1 del documento):
-- scripts/copiar_observaciones_al_observador.py, una copia historica ya hecha,
-- y scripts/seed_tenant_performance.py, datos de prueba.
--
-- No borra nada. Fuera de los NOT NULL no cambia la estructura: ni tablas, ni
-- indices, ni reglas nuevas.
--
-- Decisiones que se ven en el SQL, cada una con su motivo:
--
--   - Lo que quedo sin año recibe el año ACTIVO: la misma subconsulta que el
--     codigo escribe en toda fila nueva (ANIO_ACTIVO_ID_SQL de
--     app/repositories/anios_lectivos_repository.py). Es lo que el codigo
--     nuevo habria escrito si ya hubiera estado desplegado.
--
--   - Si un colegio no tiene año activo, se crea 2026, escrito y no calculado
--     con la fecha del dia, como en la migracion A. Es el caso de un colegio
--     dado de alta entre la migracion A y el despliegue: el esquema base trae
--     la tabla pero no la fila del año.
--
--   - Las matriculas del año activo se ponen al dia con `estudiantes.curso_id`,
--     que en esta ventana es la fuente de verdad: el codigo viejo creaba
--     estudiantes sin matricula y cambiaba cursos sin tocarla. Se crean las que
--     faltan y se corrigen las que no coinciden. No se borra ninguna, y
--     `estudiantes` no se modifica.
--
--   - Tres frenos, al estilo de la migracion A: si algo no cuadra, se detiene
--     con el detalle y el runner revierte ese tenant entero. Decidir que hacer
--     en esos casos es del usuario, no de esta migracion.
--
--   - Idempotente: el año solo se crea si falta, los rellenos solo tocan filas
--     sin año, la puesta al dia solo cambia lo que difiere y SET NOT NULL no
--     falla sobre una columna que ya lo es. El runner ya impide repetirla; esto
--     cubre reejecutarla a mano tras un fallo.

-- ---------------------------------------------------------------------------
-- 0. Freno: ninguna matricula sin año.
-- ---------------------------------------------------------------------------
-- Ningun camino del sistema crea matriculas sin año: la migracion A las creo
-- todas con el suyo (y se detenia si encontraba filas viejas), el codigo viejo
-- no escribe en `matriculas` y el nuevo siempre pone el año del curso. Si
-- aparece una, la creo algo de fuera: se detiene con el recuento y no adivina
-- a que año pertenece.

DO $$
DECLARE
    matriculas_sin_anio INTEGER;
BEGIN
    SELECT COUNT(*) INTO matriculas_sin_anio
    FROM matriculas
    WHERE anio_lectivo_id IS NULL;

    IF matriculas_sin_anio > 0 THEN
        RAISE EXCEPTION
            'matriculas tiene % fila(s) sin año lectivo; se requiere revision manual antes de volver obligatorio el año',
            matriculas_sin_anio;
    END IF;
END
$$;

-- ---------------------------------------------------------------------------
-- 1. Un año activo en cada colegio.
-- ---------------------------------------------------------------------------

INSERT INTO anios_lectivos (anio, estado, activado_en)
SELECT 2026, 'activo', CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM anios_lectivos WHERE estado = 'activo')
ON CONFLICT (anio) DO NOTHING;

-- Freno: si 2026 ya existia en otro estado, el INSERT anterior no hace nada y
-- el colegio seguiria sin año activo. No se adivina cual activar: se detiene.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM anios_lectivos WHERE estado = 'activo') THEN
        RAISE EXCEPTION
            'no hay año lectivo activo y no se pudo crear 2026; se requiere revision manual';
    END IF;
END
$$;

-- ---------------------------------------------------------------------------
-- 2. Lo que quedo sin año recibe el año activo.
-- ---------------------------------------------------------------------------
-- Son las filas que el codigo viejo creo entre la migracion A y el despliegue
-- y, en un colegio que no tenia año activo, tambien las de despues.

UPDATE cursos
SET anio_lectivo_id = (SELECT id FROM anios_lectivos WHERE estado = 'activo')
WHERE anio_lectivo_id IS NULL;

UPDATE tipos_de_pagos
SET anio_lectivo_id = (SELECT id FROM anios_lectivos WHERE estado = 'activo')
WHERE anio_lectivo_id IS NULL;

-- Incluidos los pagos de ventas: todo pago tiene año.
UPDATE pagos
SET anio_lectivo_id = (SELECT id FROM anios_lectivos WHERE estado = 'activo')
WHERE anio_lectivo_id IS NULL;

UPDATE observador_anotaciones
SET anio_lectivo_id = (SELECT id FROM anios_lectivos WHERE estado = 'activo')
WHERE anio_lectivo_id IS NULL;

-- ---------------------------------------------------------------------------
-- 3. Las matriculas del año activo, iguales al curso de cada estudiante.
-- ---------------------------------------------------------------------------
-- Va despues del relleno de cursos: un curso creado en la ventana no tenia
-- año, y sin el sus estudiantes no se sincronizarian. Es la misma sentencia
-- que `sincronizar_matricula_del_anio_activo` (el codigo la corre para un
-- estudiante al crearlo o editarlo), aqui para todos a la vez, retirados
-- incluidos como en la migracion A. La condicion del DO UPDATE deja intactas
-- las que ya coinciden.

INSERT INTO matriculas (estudiante_id, curso_id, anio_lectivo_id)
SELECT e.id, e.curso_id, c.anio_lectivo_id
FROM estudiantes e
JOIN cursos c ON c.id = e.curso_id
JOIN anios_lectivos al ON al.id = c.anio_lectivo_id
WHERE al.estado = 'activo'
ON CONFLICT (estudiante_id, anio_lectivo_id)
DO UPDATE SET curso_id = EXCLUDED.curso_id
WHERE matriculas.curso_id IS DISTINCT FROM EXCLUDED.curso_id;

-- ---------------------------------------------------------------------------
-- 4. Freno: la consulta de control del curso vigente debe dar 0.
-- ---------------------------------------------------------------------------
-- Es la consulta de "La regla del curso vigente" del documento. Despues del
-- paso 3 solo quedaria algo fuera de lo previsto; por ejemplo, un estudiante
-- sin curso que si tiene matricula del año activo. Esta migracion no borra
-- matriculas ni escribe `estudiantes.curso_id`: se detiene con el recuento.

DO $$
DECLARE
    estudiantes_descuadrados INTEGER;
BEGIN
    SELECT COUNT(*) INTO estudiantes_descuadrados
    FROM estudiantes e
    LEFT JOIN matriculas m
           ON m.estudiante_id = e.id
          AND m.anio_lectivo_id = (SELECT id FROM anios_lectivos WHERE estado = 'activo')
    WHERE e.curso_id IS DISTINCT FROM m.curso_id;

    IF estudiantes_descuadrados > 0 THEN
        RAISE EXCEPTION
            '% estudiante(s) con un curso distinto al de su matricula del año activo; se requiere revision manual',
            estudiantes_descuadrados;
    END IF;
END
$$;

-- ---------------------------------------------------------------------------
-- 5. El año pasa a ser obligatorio.
-- ---------------------------------------------------------------------------
-- Si quedara alguna fila sin año, PostgreSQL se niega a ponerlo y el runner
-- revierte el tenant: no queda a medias. SET NOT NULL bloquea cada tabla
-- mientras revisa sus filas; son tablas chicas, pero conviene aplicarla a una
-- hora tranquila. Ninguna otra columna cambia.

ALTER TABLE cursos
    ALTER COLUMN anio_lectivo_id SET NOT NULL;

ALTER TABLE tipos_de_pagos
    ALTER COLUMN anio_lectivo_id SET NOT NULL;

ALTER TABLE matriculas
    ALTER COLUMN anio_lectivo_id SET NOT NULL;

ALTER TABLE pagos
    ALTER COLUMN anio_lectivo_id SET NOT NULL;

ALTER TABLE observador_anotaciones
    ALTER COLUMN anio_lectivo_id SET NOT NULL;
