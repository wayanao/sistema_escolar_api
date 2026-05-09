-- Ejecutar en cada schema tenant.
-- Crea las tablas para identidad institucional (logos, eslogan, datos)
-- y plantillas de impresion editables, con sus plantillas predefinidas.

-- =====================================================================
-- 1. Tabla de identidad institucional (1 fila por tenant)
-- =====================================================================
CREATE TABLE IF NOT EXISTS institucion_branding (
    id SERIAL PRIMARY KEY,
    nombre_institucion VARCHAR(255) DEFAULT '',
    eslogan TEXT DEFAULT '',
    logo_principal_url VARCHAR(500),
    logo_secundario_url VARCHAR(500),
    direccion TEXT DEFAULT '',
    telefono VARCHAR(50) DEFAULT '',
    email VARCHAR(150) DEFAULT '',
    nit VARCHAR(50) DEFAULT '',
    sitio_web VARCHAR(255) DEFAULT '',
    color_primario VARCHAR(20) DEFAULT '#0f314f',
    color_secundario VARCHAR(20) DEFAULT '#526775',
    configuracion_extra JSONB DEFAULT '{}'::jsonb,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Garantiza una sola fila de branding por tenant.
INSERT INTO institucion_branding (nombre_institucion)
SELECT ''
WHERE NOT EXISTS (SELECT 1 FROM institucion_branding);

-- =====================================================================
-- 2. Tabla de plantillas de impresion
--    tipo: boletin | voucher_pago | volante_venta | reporte_estudiante
--          | observaciones | planeador
--    config_json: parametros visuales (colores, posicion logo, etc.)
-- =====================================================================
CREATE TABLE IF NOT EXISTS plantilla_impresion (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(50) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    codigo VARCHAR(100),
    es_predefinida BOOLEAN DEFAULT FALSE,
    activa BOOLEAN DEFAULT FALSE,
    config_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_plantilla_tipo
    ON plantilla_impresion(tipo);

-- Solo una plantilla activa por tipo.
CREATE UNIQUE INDEX IF NOT EXISTS idx_plantilla_activa_unica
    ON plantilla_impresion(tipo) WHERE activa = TRUE;

-- Codigo unico para identificar plantillas predefinidas (permite re-seed seguro).
CREATE UNIQUE INDEX IF NOT EXISTS idx_plantilla_codigo_unico
    ON plantilla_impresion(codigo) WHERE codigo IS NOT NULL;

-- =====================================================================
-- 3. Seed de plantillas predefinidas (3 estilos x 6 tipos = 18 plantillas)
--    Idempotente: ON CONFLICT por codigo no hace nada si ya existe.
-- =====================================================================

-- ---------- BOLETIN ----------
INSERT INTO plantilla_impresion (tipo, nombre, codigo, es_predefinida, activa, config_json) VALUES
('boletin', 'Clasico', 'boletin_clasico', TRUE, TRUE, '{
    "fuente": "Georgia, serif",
    "tamano_fuente_base": 12,
    "posicion_logo": "izquierda",
    "mostrar_logo_secundario": true,
    "mostrar_eslogan": true,
    "mostrar_pie": true,
    "mostrar_firmas": true,
    "encabezado_alineacion": "center",
    "borde_documento": true,
    "margen_top": 25, "margen_bottom": 25, "margen_left": 25, "margen_right": 25
}'::jsonb),
('boletin', 'Moderno', 'boletin_moderno', TRUE, FALSE, '{
    "fuente": "Inter, sans-serif",
    "tamano_fuente_base": 12,
    "posicion_logo": "izquierda",
    "mostrar_logo_secundario": false,
    "mostrar_eslogan": true,
    "mostrar_pie": true,
    "mostrar_firmas": true,
    "encabezado_alineacion": "left",
    "borde_documento": false,
    "margen_top": 20, "margen_bottom": 20, "margen_left": 20, "margen_right": 20
}'::jsonb),
('boletin', 'Minimalista', 'boletin_minimalista', TRUE, FALSE, '{
    "fuente": "Helvetica, Arial, sans-serif",
    "tamano_fuente_base": 11,
    "posicion_logo": "centro",
    "mostrar_logo_secundario": false,
    "mostrar_eslogan": false,
    "mostrar_pie": true,
    "mostrar_firmas": true,
    "encabezado_alineacion": "center",
    "borde_documento": false,
    "margen_top": 15, "margen_bottom": 15, "margen_left": 18, "margen_right": 18
}'::jsonb)
ON CONFLICT (codigo) WHERE codigo IS NOT NULL DO NOTHING;

-- ---------- VOUCHER DE PAGO ----------
INSERT INTO plantilla_impresion (tipo, nombre, codigo, es_predefinida, activa, config_json) VALUES
('voucher_pago', 'Clasico', 'voucher_pago_clasico', TRUE, TRUE, '{
    "fuente": "Georgia, serif",
    "tamano_fuente_base": 11,
    "posicion_logo": "izquierda",
    "mostrar_logo_secundario": false,
    "mostrar_eslogan": true,
    "mostrar_pie": true,
    "mostrar_firmas": true,
    "encabezado_alineacion": "center",
    "borde_documento": true,
    "margen_top": 20, "margen_bottom": 20, "margen_left": 20, "margen_right": 20
}'::jsonb),
('voucher_pago', 'Moderno', 'voucher_pago_moderno', TRUE, FALSE, '{
    "fuente": "Inter, sans-serif",
    "tamano_fuente_base": 11,
    "posicion_logo": "izquierda",
    "mostrar_logo_secundario": false,
    "mostrar_eslogan": false,
    "mostrar_pie": true,
    "mostrar_firmas": false,
    "encabezado_alineacion": "left",
    "borde_documento": false,
    "margen_top": 15, "margen_bottom": 15, "margen_left": 15, "margen_right": 15
}'::jsonb),
('voucher_pago', 'Minimalista', 'voucher_pago_minimalista', TRUE, FALSE, '{
    "fuente": "Helvetica, Arial, sans-serif",
    "tamano_fuente_base": 10,
    "posicion_logo": "centro",
    "mostrar_logo_secundario": false,
    "mostrar_eslogan": false,
    "mostrar_pie": false,
    "mostrar_firmas": false,
    "encabezado_alineacion": "center",
    "borde_documento": false,
    "margen_top": 12, "margen_bottom": 12, "margen_left": 12, "margen_right": 12
}'::jsonb)
ON CONFLICT (codigo) WHERE codigo IS NOT NULL DO NOTHING;

-- ---------- VOLANTE DE VENTA ----------
INSERT INTO plantilla_impresion (tipo, nombre, codigo, es_predefinida, activa, config_json) VALUES
('volante_venta', 'Clasico', 'volante_venta_clasico', TRUE, TRUE, '{
    "fuente": "Georgia, serif",
    "tamano_fuente_base": 11,
    "posicion_logo": "izquierda",
    "mostrar_logo_secundario": false,
    "mostrar_eslogan": true,
    "mostrar_pie": true,
    "mostrar_firmas": false,
    "encabezado_alineacion": "center",
    "borde_documento": true,
    "margen_top": 20, "margen_bottom": 20, "margen_left": 20, "margen_right": 20
}'::jsonb),
('volante_venta', 'Moderno', 'volante_venta_moderno', TRUE, FALSE, '{
    "fuente": "Inter, sans-serif",
    "tamano_fuente_base": 11,
    "posicion_logo": "derecha",
    "mostrar_logo_secundario": false,
    "mostrar_eslogan": false,
    "mostrar_pie": true,
    "mostrar_firmas": false,
    "encabezado_alineacion": "left",
    "borde_documento": false,
    "margen_top": 15, "margen_bottom": 15, "margen_left": 15, "margen_right": 15
}'::jsonb),
('volante_venta', 'Minimalista', 'volante_venta_minimalista', TRUE, FALSE, '{
    "fuente": "Helvetica, Arial, sans-serif",
    "tamano_fuente_base": 10,
    "posicion_logo": "centro",
    "mostrar_logo_secundario": false,
    "mostrar_eslogan": false,
    "mostrar_pie": false,
    "mostrar_firmas": false,
    "encabezado_alineacion": "center",
    "borde_documento": false,
    "margen_top": 12, "margen_bottom": 12, "margen_left": 12, "margen_right": 12
}'::jsonb)
ON CONFLICT (codigo) WHERE codigo IS NOT NULL DO NOTHING;

-- ---------- REPORTE ESTUDIANTE ----------
INSERT INTO plantilla_impresion (tipo, nombre, codigo, es_predefinida, activa, config_json) VALUES
('reporte_estudiante', 'Clasico', 'reporte_estudiante_clasico', TRUE, TRUE, '{
    "fuente": "Georgia, serif",
    "tamano_fuente_base": 12,
    "posicion_logo": "izquierda",
    "mostrar_logo_secundario": true,
    "mostrar_eslogan": true,
    "mostrar_pie": true,
    "mostrar_firmas": true,
    "encabezado_alineacion": "center",
    "borde_documento": true,
    "margen_top": 25, "margen_bottom": 25, "margen_left": 25, "margen_right": 25
}'::jsonb),
('reporte_estudiante', 'Moderno', 'reporte_estudiante_moderno', TRUE, FALSE, '{
    "fuente": "Inter, sans-serif",
    "tamano_fuente_base": 12,
    "posicion_logo": "izquierda",
    "mostrar_logo_secundario": false,
    "mostrar_eslogan": true,
    "mostrar_pie": true,
    "mostrar_firmas": true,
    "encabezado_alineacion": "left",
    "borde_documento": false,
    "margen_top": 20, "margen_bottom": 20, "margen_left": 20, "margen_right": 20
}'::jsonb),
('reporte_estudiante', 'Minimalista', 'reporte_estudiante_minimalista', TRUE, FALSE, '{
    "fuente": "Helvetica, Arial, sans-serif",
    "tamano_fuente_base": 11,
    "posicion_logo": "centro",
    "mostrar_logo_secundario": false,
    "mostrar_eslogan": false,
    "mostrar_pie": true,
    "mostrar_firmas": true,
    "encabezado_alineacion": "center",
    "borde_documento": false,
    "margen_top": 15, "margen_bottom": 15, "margen_left": 18, "margen_right": 18
}'::jsonb)
ON CONFLICT (codigo) WHERE codigo IS NOT NULL DO NOTHING;

-- ---------- OBSERVACIONES ----------
INSERT INTO plantilla_impresion (tipo, nombre, codigo, es_predefinida, activa, config_json) VALUES
('observaciones', 'Clasico', 'observaciones_clasico', TRUE, TRUE, '{
    "fuente": "Georgia, serif",
    "tamano_fuente_base": 12,
    "posicion_logo": "izquierda",
    "mostrar_logo_secundario": false,
    "mostrar_eslogan": true,
    "mostrar_pie": true,
    "mostrar_firmas": true,
    "encabezado_alineacion": "center",
    "borde_documento": true,
    "margen_top": 25, "margen_bottom": 25, "margen_left": 25, "margen_right": 25
}'::jsonb),
('observaciones', 'Moderno', 'observaciones_moderno', TRUE, FALSE, '{
    "fuente": "Inter, sans-serif",
    "tamano_fuente_base": 12,
    "posicion_logo": "izquierda",
    "mostrar_logo_secundario": false,
    "mostrar_eslogan": true,
    "mostrar_pie": true,
    "mostrar_firmas": true,
    "encabezado_alineacion": "left",
    "borde_documento": false,
    "margen_top": 20, "margen_bottom": 20, "margen_left": 20, "margen_right": 20
}'::jsonb),
('observaciones', 'Minimalista', 'observaciones_minimalista', TRUE, FALSE, '{
    "fuente": "Helvetica, Arial, sans-serif",
    "tamano_fuente_base": 11,
    "posicion_logo": "centro",
    "mostrar_logo_secundario": false,
    "mostrar_eslogan": false,
    "mostrar_pie": true,
    "mostrar_firmas": true,
    "encabezado_alineacion": "center",
    "borde_documento": false,
    "margen_top": 15, "margen_bottom": 15, "margen_left": 18, "margen_right": 18
}'::jsonb)
ON CONFLICT (codigo) WHERE codigo IS NOT NULL DO NOTHING;

-- ---------- PLANEADOR ----------
INSERT INTO plantilla_impresion (tipo, nombre, codigo, es_predefinida, activa, config_json) VALUES
('planeador', 'Clasico', 'planeador_clasico', TRUE, TRUE, '{
    "fuente": "Georgia, serif",
    "tamano_fuente_base": 11,
    "posicion_logo": "izquierda",
    "mostrar_logo_secundario": false,
    "mostrar_eslogan": true,
    "mostrar_pie": true,
    "mostrar_firmas": false,
    "encabezado_alineacion": "center",
    "borde_documento": true,
    "margen_top": 20, "margen_bottom": 20, "margen_left": 20, "margen_right": 20
}'::jsonb),
('planeador', 'Moderno', 'planeador_moderno', TRUE, FALSE, '{
    "fuente": "Inter, sans-serif",
    "tamano_fuente_base": 11,
    "posicion_logo": "izquierda",
    "mostrar_logo_secundario": false,
    "mostrar_eslogan": false,
    "mostrar_pie": true,
    "mostrar_firmas": false,
    "encabezado_alineacion": "left",
    "borde_documento": false,
    "margen_top": 15, "margen_bottom": 15, "margen_left": 15, "margen_right": 15
}'::jsonb),
('planeador', 'Minimalista', 'planeador_minimalista', TRUE, FALSE, '{
    "fuente": "Helvetica, Arial, sans-serif",
    "tamano_fuente_base": 10,
    "posicion_logo": "centro",
    "mostrar_logo_secundario": false,
    "mostrar_eslogan": false,
    "mostrar_pie": false,
    "mostrar_firmas": false,
    "encabezado_alineacion": "center",
    "borde_documento": false,
    "margen_top": 12, "margen_bottom": 12, "margen_left": 12, "margen_right": 12
}'::jsonb)
ON CONFLICT (codigo) WHERE codigo IS NOT NULL DO NOTHING;
