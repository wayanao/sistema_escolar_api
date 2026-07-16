-- =====================================================================
-- Migracion: multiples aplicaciones auditables por cuota mensual
-- Fecha: 2026-07-16
--
-- Permite que una cuota reciba abonos desde pagos distintos y que un pago
-- mixto distribuya sus metodos sobre el mismo periodo. No modifica datos.
-- =====================================================================

DROP INDEX IF EXISTS uq_pagos_aplicaciones_activas;

CREATE UNIQUE INDEX IF NOT EXISTS uq_pagos_aplicaciones_pago_periodo_activas
    ON pagos_aplicaciones (pago_id, tipo_pago_id, periodo)
    WHERE activo = TRUE;

CREATE INDEX IF NOT EXISTS idx_pagos_aplicaciones_cuota_activa
    ON pagos_aplicaciones (estudiante_id, tipo_pago_id, periodo)
    WHERE activo = TRUE;
