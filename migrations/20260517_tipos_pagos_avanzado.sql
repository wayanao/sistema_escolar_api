-- =====================================================================
-- Migración: Configuración avanzada de tipos de pago
-- Fecha: 2026-05-17
--
-- Extiende la tabla `tipos_de_pagos` con configuración financiera y crea
-- una tabla puente `tipos_pagos_cursos` para asignar conceptos a cursos
-- con valores diferenciados.
--
-- Esta migración se aplica POR CADA SCHEMA `tenant_*` mediante el script
-- scripts/apply_tipos_pagos_avanzado_migration.py
-- =====================================================================

-- 1) Columnas nuevas en tipos_de_pagos (no destructivas)
ALTER TABLE tipos_de_pagos
    ADD COLUMN IF NOT EXISTS descripcion TEXT,
    ADD COLUMN IF NOT EXISTS tipo_cobro VARCHAR(20) NOT NULL DEFAULT 'unico'
        -- valores admitidos: 'unico', 'mensual', 'anual', 'opcional'
        ,
    ADD COLUMN IF NOT EXISTS fecha_limite DATE,
    ADD COLUMN IF NOT EXISTS dia_limite_mes SMALLINT,
        -- día del mes (1-31) que vence una mensualidad recurrente
    ADD COLUMN IF NOT EXISTS dias_gracia SMALLINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS mora_tipo VARCHAR(20),
        -- 'porcentaje' | 'fijo' | NULL (sin mora)
    ADD COLUMN IF NOT EXISTS mora_valor NUMERIC(12, 2) NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS mes_inicial SMALLINT,
        -- mes (1-12) en que arranca la recurrencia anual
    ADD COLUMN IF NOT EXISTS frecuencia_meses SMALLINT NOT NULL DEFAULT 1,
        -- cada cuántos meses se genera (1 = mensual, 2 = bimestral, etc.)
    ADD COLUMN IF NOT EXISTS generacion_automatica BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS activo BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

-- Constraint de dominios (idempotente, se elimina y recrea)
ALTER TABLE tipos_de_pagos DROP CONSTRAINT IF EXISTS chk_tipo_cobro;
ALTER TABLE tipos_de_pagos
    ADD CONSTRAINT chk_tipo_cobro
    CHECK (tipo_cobro IN ('unico', 'mensual', 'anual', 'opcional'));

ALTER TABLE tipos_de_pagos DROP CONSTRAINT IF EXISTS chk_mora_tipo;
ALTER TABLE tipos_de_pagos
    ADD CONSTRAINT chk_mora_tipo
    CHECK (mora_tipo IS NULL OR mora_tipo IN ('porcentaje', 'fijo'));

ALTER TABLE tipos_de_pagos DROP CONSTRAINT IF EXISTS chk_dia_limite_mes;
ALTER TABLE tipos_de_pagos
    ADD CONSTRAINT chk_dia_limite_mes
    CHECK (dia_limite_mes IS NULL OR (dia_limite_mes BETWEEN 1 AND 31));

ALTER TABLE tipos_de_pagos DROP CONSTRAINT IF EXISTS chk_mes_inicial;
ALTER TABLE tipos_de_pagos
    ADD CONSTRAINT chk_mes_inicial
    CHECK (mes_inicial IS NULL OR (mes_inicial BETWEEN 1 AND 12));

-- 2) Tabla puente tipos_pagos_cursos
CREATE TABLE IF NOT EXISTS tipos_pagos_cursos (
    id SERIAL PRIMARY KEY,
    tipo_pago_id INTEGER NOT NULL REFERENCES tipos_de_pagos(id) ON DELETE CASCADE,
    curso_id INTEGER NOT NULL REFERENCES cursos(id) ON DELETE CASCADE,
    valor NUMERIC(12, 2) NOT NULL DEFAULT 0,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tipo_pago_id, curso_id)
);

CREATE INDEX IF NOT EXISTS idx_tipos_pagos_cursos_tipo
    ON tipos_pagos_cursos(tipo_pago_id);
CREATE INDEX IF NOT EXISTS idx_tipos_pagos_cursos_curso
    ON tipos_pagos_cursos(curso_id);
