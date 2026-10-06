-- Año lectivo, fase 5.2: origen de cursos y conceptos copiados.
--
-- Las dos columnas son opcionales: NULL significa que el registro se creo
-- desde cero. Cuando la fase 5.4 copie la configuracion al año siguiente,
-- guardara aqui el id del registro original.
--
-- Esta migracion no rellena ni cambia datos existentes. Los cursos y conceptos
-- de 2026 conservan NULL porque no son copias de otro año.

ALTER TABLE cursos
    ADD COLUMN IF NOT EXISTS curso_origen_id INTEGER;

ALTER TABLE tipos_de_pagos
    ADD COLUMN IF NOT EXISTS tipo_pago_origen_id INTEGER;

-- PostgreSQL no ofrece ADD CONSTRAINT IF NOT EXISTS. Cada clave se agrega solo
-- si falta, para que una ejecucion manual interrumpida se pueda repetir.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'cursos_curso_origen_id_fkey'
          AND conrelid = 'cursos'::regclass
    ) THEN
        ALTER TABLE cursos
            ADD CONSTRAINT cursos_curso_origen_id_fkey
            FOREIGN KEY (curso_origen_id) REFERENCES cursos (id);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'tipos_de_pagos_tipo_pago_origen_id_fkey'
          AND conrelid = 'tipos_de_pagos'::regclass
    ) THEN
        ALTER TABLE tipos_de_pagos
            ADD CONSTRAINT tipos_de_pagos_tipo_pago_origen_id_fkey
            FOREIGN KEY (tipo_pago_origen_id) REFERENCES tipos_de_pagos (id);
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS idx_cursos_curso_origen
ON cursos (curso_origen_id);

CREATE INDEX IF NOT EXISTS idx_tipos_de_pagos_tipo_pago_origen
ON tipos_de_pagos (tipo_pago_origen_id);
