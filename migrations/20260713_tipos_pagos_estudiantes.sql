-- =====================================================================
-- Migracion: Valores personalizados de tipos de pago por estudiante
-- Fecha: 2026-07-13
--
-- Permite que un estudiante tenga un valor distinto al valor del curso para
-- un concepto de cobro especifico, sin modificar el curso ni el tipo de pago.
-- Regla de calculo:
--   valor estudiante activo > valor curso > valor base del tipo de pago.
-- =====================================================================

CREATE TABLE IF NOT EXISTS tipos_pagos_estudiantes (
    id SERIAL PRIMARY KEY,
    tipo_pago_id INTEGER NOT NULL REFERENCES tipos_de_pagos(id) ON DELETE CASCADE,
    estudiante_id INTEGER NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
    valor NUMERIC(12, 2) NOT NULL DEFAULT 0,
    motivo TEXT,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tipo_pago_id, estudiante_id)
);

ALTER TABLE tipos_pagos_estudiantes DROP CONSTRAINT IF EXISTS chk_tipos_pagos_estudiantes_valor;
ALTER TABLE tipos_pagos_estudiantes
    ADD CONSTRAINT chk_tipos_pagos_estudiantes_valor
    CHECK (valor >= 0);

CREATE INDEX IF NOT EXISTS idx_tipos_pagos_estudiantes_estudiante
    ON tipos_pagos_estudiantes(estudiante_id);

CREATE INDEX IF NOT EXISTS idx_tipos_pagos_estudiantes_tipo
    ON tipos_pagos_estudiantes(tipo_pago_id);

CREATE INDEX IF NOT EXISTS idx_tipos_pagos_estudiantes_activo
    ON tipos_pagos_estudiantes(activo);
