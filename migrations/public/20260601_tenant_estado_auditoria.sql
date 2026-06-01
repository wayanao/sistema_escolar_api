CREATE TABLE IF NOT EXISTS public.tenant_estado_auditoria (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES public.colegios(id),
    estado_anterior VARCHAR(30) NOT NULL,
    estado_nuevo VARCHAR(30) NOT NULL,
    motivo TEXT,
    super_admin_id INTEGER NOT NULL REFERENCES public.super_admins(id),
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tenant_estado_auditoria_tenant_id
ON public.tenant_estado_auditoria (tenant_id);

CREATE INDEX IF NOT EXISTS idx_tenant_estado_auditoria_creado_en
ON public.tenant_estado_auditoria (creado_en);
