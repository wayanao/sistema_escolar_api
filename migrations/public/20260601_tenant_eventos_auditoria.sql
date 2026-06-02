CREATE TABLE IF NOT EXISTS public.tenant_eventos_auditoria (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES public.colegios(id),
    evento VARCHAR(60) NOT NULL,
    detalle TEXT,
    super_admin_id INTEGER NOT NULL REFERENCES public.super_admins(id),
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tenant_eventos_auditoria_tenant_id
ON public.tenant_eventos_auditoria (tenant_id);

CREATE INDEX IF NOT EXISTS idx_tenant_eventos_auditoria_creado_en
ON public.tenant_eventos_auditoria (creado_en);
