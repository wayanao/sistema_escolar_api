CREATE TABLE IF NOT EXISTS public.tenant_suscripciones (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL UNIQUE REFERENCES public.colegios(id) ON DELETE CASCADE,
    fecha_inicio DATE NOT NULL,
    fecha_proximo_pago DATE NOT NULL,
    dias_gracia INTEGER NOT NULL DEFAULT 0 CHECK (dias_gracia >= 0),
    notas TEXT,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tenant_suscripciones_fecha_proximo_pago
ON public.tenant_suscripciones (fecha_proximo_pago);
