-- Esquema base de un tenant. ARCHIVO GENERADO, no editar a mano.
--
-- Extraido de tenant_colegio_1 el 2026-10-22 con
-- scripts/generar_esquema_base.py. Para rehacerlo, aplica antes la
-- migracion nueva a ese schema y vuelve a ejecutar el script.
--
-- Se aplica con el search_path apuntando SOLO al schema destino. Sus
-- nombres no van cualificados: con otro schema en el camino, las claves
-- foraneas naceran apuntando alli.
--
-- No usar apply_migration.py con este archivo: es para dar de alta un
-- tenant nuevo, no para los existentes, que ya tienen estas tablas.
--
-- MIGRACIONES INCORPORADAS (47):
--   20260429_pagos_tipo_pago_largo.sql
--   20260429_plan_de_clases_reportes.sql
--   20260509_branding_plantillas_impresion.sql
--   20260517_tipos_pagos_avanzado.sql
--   20260526_cursos_solo_academicos.sql
--   20260527_pagos_anulacion.sql
--   20260527_pagos_venta_id.sql
--   20260527_ventas_anulacion.sql
--   20260601_usuarios_password_obligatorio.sql
--   20260602_asignaciones_activo.sql
--   20260604_cursos_estado.sql
--   20260604_egresos_origen.sql
--   20260604_inventario_estado.sql
--   20260604_materias_estado.sql
--   20260604_profesor_estado.sql
--   20260623_admin_nombres_mayuscula.sql
--   20260623_admin_unicos_academicos.sql
--   20260623_asignaciones_horarios_historial_unico.sql
--   20260623_asignaciones_unicas_activas.sql
--   20260623_institucion_branding_codigo_dane.sql
--   20260624_asignaciones_orden_boletin.sql
--   20260713_tipos_pagos_estudiantes.sql
--   20260715_plan_de_clases_estandar_dba_text.sql
--   20260715_plan_de_clases_textos_largos.sql
--   20260715_reparar_asignacion_academica_invalida.sql
--   20260716_pagos_adelantados.sql
--   20260716_pagos_aplicaciones_parciales.sql
--   20260722_plan_de_clases_integridad.sql
--   20260722_plan_de_clases_notificaciones.sql
--   20260722_plan_de_clases_revision.sql
--   20260825_observaciones_claves_foraneas.sql
--   20260901_cursos_nivel_academico.sql
--   20260908_observador_anotaciones.sql
--   20260908_observador_anotaciones_historicas.sql
--   20260908_observador_anotaciones_materia.sql
--   20260910_tipos_pagos_mes_final.sql
--   20260915_cursos_director_grupo.sql
--   20260921_listas_seguimiento.sql
--   20260930_anios_lectivos.sql
--   20261001_anios_lectivos_obligatorio.sql
--   20261006_anios_lectivos_origenes.sql
--   20261008_anios_lectivos_activacion.sql
--   20261013_admisiones.sql
--   20261014_admisiones_cuestionario.sql
--   20261019_estudiantes_sisben_residencia.sql
--   20261021_planilla_subnotas.sql
--   20261022_planilla_tipos_porcentaje.sql
-- FIN MIGRACIONES INCORPORADAS

CREATE TABLE IF NOT EXISTS admisiones (
    id SERIAL,
    anio_lectivo_id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    apellido character varying(100) NOT NULL,
    tipo_documento character varying(50),
    documento_identidad character varying(20),
    fecha_nacimiento date,
    curso_id integer,
    acudiente_nombre character varying(150),
    acudiente_parentesco character varying(50),
    acudiente_telefono character varying(50),
    autoriza_datos boolean NOT NULL,
    autoriza_nombre character varying(150) NOT NULL,
    fecha_entrevista date,
    entrevistador character varying(150),
    asistentes character varying(250),
    colegio_anterior character varying(150),
    anio_cursado_anterior character varying(50),
    pre_escolar_anterior character varying(50),
    ebp_anterior character varying(50),
    motivo_retiro_anterior text,
    paz_salvo_anterior character varying(10),
    ocupacion_padre character varying(100),
    ocupacion_madre character varying(100),
    vive_con character varying(250),
    expectativas text,
    observaciones text,
    resultado character varying(20) DEFAULT 'pendiente'::character varying NOT NULL,
    motivo_resultado text,
    decidido_en timestamp with time zone,
    estudiante_id integer,
    creado_en timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    actualizado_en timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    cuestionario jsonb DEFAULT '{}'::jsonb NOT NULL,
    CONSTRAINT chk_admisiones_autoriza CHECK (autoriza_datos),
    CONSTRAINT chk_admisiones_cuestionario_objeto CHECK ((jsonb_typeof(cuestionario) = 'object'::text)),
    CONSTRAINT chk_admisiones_matricula_aprobada CHECK (((estudiante_id IS NULL) OR ((resultado)::text = 'aprobado'::text))),
    CONSTRAINT chk_admisiones_motivo_no_aprobado CHECK ((((resultado)::text <> 'no_aprobado'::text) OR (NULLIF(TRIM(BOTH FROM motivo_resultado), ''::text) IS NOT NULL))),
    CONSTRAINT chk_admisiones_resultado CHECK (((resultado)::text = ANY ((ARRAY['pendiente'::character varying, 'aprobado'::character varying, 'no_aprobado'::character varying])::text[]))),
    CONSTRAINT admisiones_pkey PRIMARY KEY (id),
    CONSTRAINT admisiones_estudiante_id_key UNIQUE (estudiante_id)
);

CREATE TABLE IF NOT EXISTS anios_lectivos (
    id SERIAL,
    anio smallint NOT NULL,
    estado character varying(20) DEFAULT 'preparacion'::character varying NOT NULL,
    creado_en timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    activado_en timestamp without time zone,
    cerrado_en timestamp without time zone,
    CONSTRAINT chk_anios_lectivos_anio CHECK (((anio >= 2000) AND (anio <= 2100))),
    CONSTRAINT chk_anios_lectivos_estado CHECK (((estado)::text = ANY ((ARRAY['preparacion'::character varying, 'activo'::character varying, 'cerrado'::character varying, 'reabierto'::character varying])::text[]))),
    CONSTRAINT anios_lectivos_pkey PRIMARY KEY (id),
    CONSTRAINT anios_lectivos_anio_key UNIQUE (anio)
);

CREATE TABLE IF NOT EXISTS anios_lectivos_materias_ocultas (
    anio_lectivo_id integer NOT NULL,
    materia_id integer NOT NULL,
    CONSTRAINT anios_lectivos_materias_ocultas_pkey PRIMARY KEY (anio_lectivo_id, materia_id)
);

CREATE TABLE IF NOT EXISTS asignaciones (
    id SERIAL,
    curso_id integer NOT NULL,
    materia_id integer NOT NULL,
    profesor_id integer NOT NULL,
    dia character varying(20),
    horas integer,
    hora_inicio character varying(10),
    hora_fin character varying(10),
    activo boolean DEFAULT true NOT NULL,
    asignacion_academica_id integer,
    orden_boletin integer DEFAULT 100 NOT NULL,
    CONSTRAINT asignaciones_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS asistencia (
    id SERIAL,
    estudiante_id integer,
    asignacion_id integer,
    fecha date,
    estado character varying(20),
    periodo integer DEFAULT 1,
    CONSTRAINT asistencia_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS boletin_cabecera (
    id SERIAL,
    estudiante_id integer,
    asignacion_id integer,
    periodo integer,
    definitiva numeric(5,2),
    CONSTRAINT boletin_cabecera_pkey PRIMARY KEY (id),
    CONSTRAINT boletin_cabecera_estudiante_id_asignacion_id_periodo_key UNIQUE (estudiante_id, asignacion_id, periodo)
);

CREATE TABLE IF NOT EXISTS boletin_detalles (
    id SERIAL,
    boletin_id integer,
    nota numeric(5,2),
    observacion text,
    tipo_evaluacion character varying(30) DEFAULT 'numerica'::character varying,
    valoracion character varying(30),
    CONSTRAINT boletin_detalles_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS cursos (
    id SERIAL,
    nombre character varying(100),
    descripcion text,
    jornada character varying(20) DEFAULT 'Mañana'::character varying,
    estado character varying(30),
    nivel character varying(20),
    director_grupo_id integer,
    anio_lectivo_id integer NOT NULL,
    curso_origen_id integer,
    CONSTRAINT chk_cursos_nivel CHECK (((nivel IS NULL) OR ((nivel)::text = ANY ((ARRAY['preescolar'::character varying, 'primaria'::character varying])::text[])))),
    CONSTRAINT cursos_pkey PRIMARY KEY (id),
    CONSTRAINT cursos_id_anio_lectivo_key UNIQUE (id, anio_lectivo_id)
);

CREATE TABLE IF NOT EXISTS egresos (
    id SERIAL,
    concepto character varying(255) NOT NULL,
    monto numeric(12,2) NOT NULL,
    fecha date DEFAULT CURRENT_DATE,
    categoria character varying(100) DEFAULT 'Otros'::character varying,
    notas text,
    origen character varying(30),
    CONSTRAINT egresos_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS estudiantes (
    id SERIAL,
    nombre character varying(100),
    apellido character varying(100),
    documento_identidad character varying(20),
    curso_id integer,
    estado character varying(20),
    anio_escolar integer,
    fecha_nacimiento date,
    descuento_matricula numeric DEFAULT 0,
    descuento_mensualidad numeric DEFAULT 0,
    datos_medicos text,
    telefono character varying(50),
    email character varying(100),
    direccion character varying(255),
    nombre_padre character varying(100),
    telefono_padre character varying(50),
    nombre_madre character varying(100),
    telefono_madre character varying(50),
    contacto_emergencia character varying(150),
    tipo_documento character varying(50),
    lugar_expedicion character varying(150),
    eps character varying(100),
    estrato character varying(20),
    jornada character varying(50),
    colegio_anterior character varying(150),
    anio_cursado_anterior character varying(50),
    pre_escolar_anterior character varying(50),
    ebp_anterior character varying(50),
    motivo_retiro_anterior text,
    paz_salvo_anterior character varying(10),
    ocupacion_padre character varying(100),
    tipo_documento_padre character varying(50),
    documento_padre character varying(50),
    ocupacion_madre character varying(100),
    tipo_documento_madre character varying(50),
    documento_madre character varying(50),
    condicion_diagnostico character varying(255),
    sisben boolean,
    sisben_grupo character varying(1),
    sisben_subgrupo character varying(3),
    sisben_nivel smallint,
    barrio character varying(150),
    municipio character varying(100),
    zona_residencia character varying(10),
    punto_referencia character varying(255),
    CONSTRAINT chk_estudiantes_sisben_clasificacion CHECK (((sisben IS TRUE) OR ((sisben_grupo IS NULL) AND (sisben_subgrupo IS NULL) AND (sisben_nivel IS NULL)))),
    CONSTRAINT chk_estudiantes_sisben_grupo CHECK (((sisben_grupo)::text = ANY ((ARRAY['A'::character varying, 'B'::character varying, 'C'::character varying, 'D'::character varying])::text[]))),
    CONSTRAINT chk_estudiantes_sisben_nivel CHECK (((sisben_nivel >= 1) AND (sisben_nivel <= 3))),
    CONSTRAINT chk_estudiantes_sisben_subgrupo CHECK (((sisben_subgrupo IS NULL) OR ((sisben_grupo IS NOT NULL) AND ("left"((sisben_subgrupo)::text, 1) = (sisben_grupo)::text) AND ((sisben_subgrupo)::text ~ '^[A-D][1-9][0-9]?$'::text)))),
    CONSTRAINT chk_estudiantes_zona_residencia CHECK (((zona_residencia)::text = ANY ((ARRAY['urbana'::character varying, 'rural'::character varying])::text[]))),
    CONSTRAINT estudiantes_pkey PRIMARY KEY (id),
    CONSTRAINT estudiantes_documento_identidad_key UNIQUE (documento_identidad)
);

CREATE TABLE IF NOT EXISTS institucion_branding (
    id SERIAL,
    nombre_institucion character varying(255) DEFAULT ''::character varying,
    eslogan text DEFAULT ''::text,
    logo_principal_url character varying(500),
    logo_secundario_url character varying(500),
    direccion text DEFAULT ''::text,
    telefono character varying(50) DEFAULT ''::character varying,
    email character varying(150) DEFAULT ''::character varying,
    nit character varying(50) DEFAULT ''::character varying,
    sitio_web character varying(255) DEFAULT ''::character varying,
    color_primario character varying(20) DEFAULT '#0f314f'::character varying,
    color_secundario character varying(20) DEFAULT '#526775'::character varying,
    configuracion_extra jsonb DEFAULT '{}'::jsonb,
    creado_en timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    actualizado_en timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    codigo_dane character varying(20) DEFAULT ''::character varying,
    CONSTRAINT institucion_branding_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS inventario (
    id SERIAL,
    nombre character varying(255) NOT NULL,
    costo numeric(10,2) DEFAULT 0 NOT NULL,
    precio_venta numeric(10,2) DEFAULT 0 NOT NULL,
    stock_actual integer DEFAULT 0 NOT NULL,
    estado character varying(30),
    CONSTRAINT inventario_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS listas_seguimiento_columnas (
    id SERIAL,
    curso_id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT listas_seguimiento_columnas_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS listas_seguimiento_marcas (
    id SERIAL,
    columna_id integer NOT NULL,
    estudiante_id integer NOT NULL,
    marcado boolean DEFAULT false NOT NULL,
    nota text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_listas_seguimiento_marcas_nota_longitud CHECK (((nota IS NULL) OR (char_length(nota) <= 240))),
    CONSTRAINT listas_seguimiento_marcas_pkey PRIMARY KEY (id),
    CONSTRAINT listas_seguimiento_marcas_columna_id_estudiante_id_key UNIQUE (columna_id, estudiante_id)
);

CREATE TABLE IF NOT EXISTS materias (
    id SERIAL,
    nombre character varying(100),
    descripcion character varying(200),
    estado character varying(30),
    CONSTRAINT materias_pkey PRIMARY KEY (id),
    CONSTRAINT materias_nombre_key UNIQUE (nombre)
);

CREATE TABLE IF NOT EXISTS matriculas (
    id SERIAL,
    estudiante_id integer,
    curso_id integer,
    anio integer,
    anio_lectivo_id integer NOT NULL,
    estado_salida character varying(20),
    CONSTRAINT chk_matriculas_estado_salida CHECK (((estado_salida)::text = ANY ((ARRAY['retirado'::character varying, 'egresado'::character varying])::text[]))),
    CONSTRAINT matriculas_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS nomina (
    id SERIAL,
    profesor_id integer,
    fecha date DEFAULT CURRENT_DATE,
    salario_base numeric(12,2) NOT NULL,
    deduccion_prestamos numeric(12,2) DEFAULT 0,
    otros_descuentos numeric(12,2) DEFAULT 0,
    bonificaciones numeric(12,2) DEFAULT 0,
    total_pagado numeric(12,2) NOT NULL,
    notas text,
    CONSTRAINT nomina_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS notas (
    id SERIAL,
    estudiante_id integer,
    asignacion_id integer,
    nota numeric(3,2),
    periodo integer,
    CONSTRAINT notas_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS notas_detalle (
    id SERIAL,
    estudiante_id integer,
    asignacion_id integer,
    descripcion character varying(100),
    nota numeric(3,2),
    fecha date,
    periodo integer DEFAULT 1,
    tipo_evaluacion character varying(30) DEFAULT 'numerica'::character varying,
    valoracion character varying(30),
    CONSTRAINT notas_detalle_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS observaciones (
    id SERIAL,
    estudiante_id integer,
    asignacion_id integer,
    periodo integer,
    conductual text,
    cognitivo text,
    lenguaje text,
    CONSTRAINT observaciones_pkey PRIMARY KEY (id),
    CONSTRAINT unique_observacion UNIQUE (estudiante_id, asignacion_id, periodo)
);

CREATE TABLE IF NOT EXISTS observador_anotaciones (
    id SERIAL,
    estudiante_id integer NOT NULL,
    profesor_id integer NOT NULL,
    periodo integer NOT NULL,
    positiva boolean,
    conductual text DEFAULT ''::text NOT NULL,
    cognitivo text DEFAULT ''::text NOT NULL,
    lenguaje text DEFAULT ''::text NOT NULL,
    creada_en timestamp with time zone DEFAULT now(),
    editada_en timestamp with time zone,
    editada_por integer,
    materia character varying(100) DEFAULT ''::character varying NOT NULL,
    observacion_origen_id integer,
    anio_lectivo_id integer NOT NULL,
    CONSTRAINT observador_anotaciones_periodo_check CHECK (((periodo >= 1) AND (periodo <= 4))),
    CONSTRAINT observador_anotaciones_pkey PRIMARY KEY (id),
    CONSTRAINT observador_anotaciones_observacion_origen_id_key UNIQUE (observacion_origen_id)
);

CREATE TABLE IF NOT EXISTS pagos (
    id SERIAL,
    estudiante_id integer,
    tipo_pago character varying(100),
    monto numeric(10,2),
    fecha_pago date,
    estado character varying(20),
    mes character varying(20),
    fecha timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    descripcion character varying(255),
    motivo_anulacion text,
    fecha_anulacion timestamp without time zone,
    anulado_por integer,
    venta_id integer,
    anio_lectivo_id integer NOT NULL,
    CONSTRAINT pagos_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS pagos_aplicaciones (
    id BIGSERIAL,
    pago_id integer NOT NULL,
    estudiante_id integer NOT NULL,
    tipo_pago_id integer NOT NULL,
    periodo date NOT NULL,
    monto numeric(12,2) NOT NULL,
    activo boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_pagos_aplicaciones_monto_positivo CHECK ((monto > (0)::numeric)),
    CONSTRAINT chk_pagos_aplicaciones_periodo_inicio_mes CHECK ((EXTRACT(day FROM periodo) = (1)::numeric)),
    CONSTRAINT pagos_aplicaciones_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS plan_de_clases (
    id SERIAL,
    asignacion_id integer NOT NULL,
    unidad text NOT NULL,
    proposito text,
    estandar text,
    dba text,
    competencias text,
    tema text,
    fecha date NOT NULL,
    imagen1 character varying(500),
    imagen2 character varying(500),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    periodo integer DEFAULT 1,
    clase text DEFAULT ''::text,
    actividad_casa text DEFAULT ''::text,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    estado_revision character varying(24) DEFAULT 'pendiente'::character varying NOT NULL,
    version_revision integer DEFAULT 1 NOT NULL,
    enviado_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    admin_visto_at timestamp with time zone,
    admin_visto_por integer,
    revisado_at timestamp with time zone,
    revisado_por integer,
    CONSTRAINT ck_plan_de_clases_estado_revision CHECK (((estado_revision)::text = ANY ((ARRAY['pendiente'::character varying, 'visto'::character varying, 'con_observaciones'::character varying, 'revisado'::character varying])::text[]))),
    CONSTRAINT ck_plan_de_clases_version_revision CHECK ((version_revision >= 1)),
    CONSTRAINT plan_de_clases_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS plan_de_clases_notificaciones_admin (
    id SERIAL,
    plan_id integer NOT NULL,
    plan_version integer NOT NULL,
    creada_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    leida_at timestamp with time zone,
    CONSTRAINT ck_plan_notificacion_admin_version CHECK ((plan_version >= 1)),
    CONSTRAINT plan_de_clases_notificaciones_admin_pkey PRIMARY KEY (id),
    CONSTRAINT uq_plan_notificacion_admin_version UNIQUE (plan_id, plan_version)
);

CREATE TABLE IF NOT EXISTS plan_de_clases_observaciones (
    id SERIAL,
    plan_id integer NOT NULL,
    admin_id integer,
    plan_version integer NOT NULL,
    observacion text NOT NULL,
    creada_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    vista_por_profesor_at timestamp with time zone,
    CONSTRAINT ck_plan_observacion_texto CHECK (((length(btrim(observacion)) >= 1) AND (length(btrim(observacion)) <= 3000))),
    CONSTRAINT ck_plan_observacion_version CHECK ((plan_version >= 1)),
    CONSTRAINT plan_de_clases_observaciones_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS planeador_anual (
    id SERIAL,
    asignacion_id integer,
    periodo integer NOT NULL,
    slot integer NOT NULL,
    unidad_tematica text,
    estandar_competencia text,
    contenido text,
    actividades_recursos text,
    fecha date,
    CONSTRAINT planeador_anual_periodo_check CHECK (((periodo >= 1) AND (periodo <= 4))),
    CONSTRAINT planeador_anual_slot_check CHECK (((slot >= 1) AND (slot <= 8))),
    CONSTRAINT planeador_anual_pkey PRIMARY KEY (id),
    CONSTRAINT planeador_anual_asignacion_id_periodo_slot_key UNIQUE (asignacion_id, periodo, slot)
);

CREATE TABLE IF NOT EXISTS planilla_subnotas (
    id SERIAL,
    asignacion_id integer NOT NULL,
    periodo integer NOT NULL,
    tipo_nota character varying(100) NOT NULL,
    nombre character varying(60) NOT NULL,
    creada_en timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_planilla_subnotas_nombre_no_vacio CHECK ((char_length(TRIM(BOTH FROM nombre)) > 0)),
    CONSTRAINT chk_planilla_subnotas_tipo_nota_no_vacio CHECK ((char_length(TRIM(BOTH FROM tipo_nota)) > 0)),
    CONSTRAINT planilla_subnotas_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS planilla_subnotas_valores (
    id SERIAL,
    subnota_id integer NOT NULL,
    estudiante_id integer NOT NULL,
    nota numeric(3,2),
    valoracion character varying(30),
    actualizada_en timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_planilla_subnotas_valores_nota_rango CHECK (((nota IS NULL) OR ((nota >= (1)::numeric) AND (nota <= (5)::numeric)))),
    CONSTRAINT chk_planilla_subnotas_valores_un_solo_valor CHECK (((nota IS NULL) <> (valoracion IS NULL))),
    CONSTRAINT planilla_subnotas_valores_pkey PRIMARY KEY (id),
    CONSTRAINT planilla_subnotas_valores_subnota_id_estudiante_id_key UNIQUE (subnota_id, estudiante_id)
);

CREATE TABLE IF NOT EXISTS planilla_tipos_porcentaje (
    id SERIAL,
    asignacion_id integer NOT NULL,
    periodo integer NOT NULL,
    tipo_nota character varying(100) NOT NULL,
    porcentaje smallint NOT NULL,
    actualizado_en timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_planilla_tipos_porcentaje_rango CHECK (((porcentaje >= 1) AND (porcentaje <= 100))),
    CONSTRAINT chk_planilla_tipos_porcentaje_tipo_nota_no_vacio CHECK ((char_length(TRIM(BOTH FROM tipo_nota)) > 0)),
    CONSTRAINT planilla_tipos_porcentaje_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS plantilla_impresion (
    id SERIAL,
    tipo character varying(50) NOT NULL,
    nombre character varying(100) NOT NULL,
    codigo character varying(100),
    es_predefinida boolean DEFAULT false,
    activa boolean DEFAULT false,
    config_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    creado_en timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    actualizado_en timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT plantilla_impresion_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS prestamos (
    id SERIAL,
    profesor_id integer,
    monto numeric(12,2) NOT NULL,
    fecha date DEFAULT CURRENT_DATE,
    estado character varying(50) DEFAULT 'Pendiente'::character varying,
    notas text,
    pagado numeric(12,2) DEFAULT 0,
    CONSTRAINT prestamos_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS profesor (
    id SERIAL,
    nombre character varying(100),
    apellido character varying(100),
    documento_identidad character varying(20),
    email character varying(100),
    telefono character varying(20),
    password character varying(100),
    sueldo numeric(12,2) DEFAULT 0,
    estado character varying(30),
    CONSTRAINT profesor_pkey PRIMARY KEY (id),
    CONSTRAINT profesor_documento_identidad_key UNIQUE (documento_identidad),
    CONSTRAINT profesor_email_key UNIQUE (email),
    CONSTRAINT unique_documento_identidad UNIQUE (documento_identidad)
);

CREATE TABLE IF NOT EXISTS tipos_de_pagos (
    id SERIAL,
    nombre character varying(100) NOT NULL,
    valor numeric(10,2) DEFAULT 0,
    descripcion text,
    tipo_cobro character varying(20) DEFAULT 'unico'::character varying NOT NULL,
    fecha_limite date,
    dia_limite_mes smallint,
    dias_gracia smallint DEFAULT 0 NOT NULL,
    mora_tipo character varying(20),
    mora_valor numeric(12,2) DEFAULT 0 NOT NULL,
    mes_inicial smallint,
    frecuencia_meses smallint DEFAULT 1 NOT NULL,
    generacion_automatica boolean DEFAULT false NOT NULL,
    activo boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    mes_final smallint DEFAULT 12 NOT NULL,
    anio_lectivo_id integer NOT NULL,
    tipo_pago_origen_id integer,
    CONSTRAINT chk_dia_limite_mes CHECK (((dia_limite_mes IS NULL) OR ((dia_limite_mes >= 1) AND (dia_limite_mes <= 31)))),
    CONSTRAINT chk_mes_final CHECK (((mes_final >= 1) AND (mes_final <= 12))),
    CONSTRAINT chk_mes_inicial CHECK (((mes_inicial IS NULL) OR ((mes_inicial >= 1) AND (mes_inicial <= 12)))),
    CONSTRAINT chk_mora_tipo CHECK (((mora_tipo IS NULL) OR ((mora_tipo)::text = ANY ((ARRAY['porcentaje'::character varying, 'fijo'::character varying])::text[])))),
    CONSTRAINT chk_rango_meses_recurrencia CHECK ((((tipo_cobro)::text <> 'mensual'::text) OR (mes_inicial IS NULL) OR (mes_final >= mes_inicial))),
    CONSTRAINT chk_tipo_cobro CHECK (((tipo_cobro)::text = ANY ((ARRAY['unico'::character varying, 'mensual'::character varying, 'anual'::character varying, 'opcional'::character varying])::text[]))),
    CONSTRAINT tipos_de_pagos_pkey PRIMARY KEY (id),
    CONSTRAINT tipos_de_pagos_anio_nombre_key UNIQUE (anio_lectivo_id, nombre)
);

CREATE TABLE IF NOT EXISTS tipos_pagos_cursos (
    id SERIAL,
    tipo_pago_id integer NOT NULL,
    curso_id integer NOT NULL,
    valor numeric(12,2) DEFAULT 0 NOT NULL,
    activo boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT tipos_pagos_cursos_pkey PRIMARY KEY (id),
    CONSTRAINT tipos_pagos_cursos_tipo_pago_id_curso_id_key UNIQUE (tipo_pago_id, curso_id)
);

CREATE TABLE IF NOT EXISTS tipos_pagos_estudiantes (
    id SERIAL,
    tipo_pago_id integer NOT NULL,
    estudiante_id integer NOT NULL,
    valor numeric(12,2) DEFAULT 0 NOT NULL,
    motivo text,
    activo boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_tipos_pagos_estudiantes_valor CHECK ((valor >= (0)::numeric)),
    CONSTRAINT tipos_pagos_estudiantes_pkey PRIMARY KEY (id),
    CONSTRAINT tipos_pagos_estudiantes_tipo_pago_id_estudiante_id_key UNIQUE (tipo_pago_id, estudiante_id)
);

CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL,
    nombre text NOT NULL,
    email text NOT NULL,
    password text NOT NULL,
    rol text NOT NULL,
    debe_cambiar_password boolean DEFAULT false NOT NULL,
    CONSTRAINT usuarios_rol_check CHECK ((rol = ANY (ARRAY['profesor'::text, 'admin'::text]))),
    CONSTRAINT usuarios_pkey PRIMARY KEY (id),
    CONSTRAINT usuarios_email_key UNIQUE (email)
);

CREATE TABLE IF NOT EXISTS ventas (
    id SERIAL,
    estudiante_id integer,
    fecha timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    tipo_venta character varying(20) DEFAULT 'Contado'::character varying NOT NULL,
    total numeric(12,2) NOT NULL,
    estado character varying(20) DEFAULT 'Pagado'::character varying,
    notas text,
    pagado numeric(12,2) DEFAULT 0,
    motivo_anulacion text,
    fecha_anulacion timestamp without time zone,
    anulado_por integer,
    CONSTRAINT ventas_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS ventas_detalle (
    id SERIAL,
    venta_id integer,
    inventario_id integer,
    cantidad integer NOT NULL,
    precio_unitario numeric(12,2) NOT NULL,
    subtotal numeric(12,2) NOT NULL,
    CONSTRAINT ventas_detalle_pkey PRIMARY KEY (id)
);

-- Indices que no respaldan restricciones
CREATE INDEX IF NOT EXISTS idx_admisiones_anio ON admisiones USING btree (anio_lectivo_id, resultado);
CREATE UNIQUE INDEX IF NOT EXISTS idx_admisiones_documento_por_anio ON admisiones USING btree (anio_lectivo_id, documento_identidad) WHERE (documento_identidad IS NOT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS idx_anios_lectivos_un_activo ON anios_lectivos USING btree (estado) WHERE ((estado)::text = 'activo'::text);
CREATE UNIQUE INDEX IF NOT EXISTS idx_anios_lectivos_una_preparacion ON anios_lectivos USING btree (estado) WHERE ((estado)::text = 'preparacion'::text);
CREATE INDEX IF NOT EXISTS idx_anios_lectivos_materias_ocultas_materia ON anios_lectivos_materias_ocultas USING btree (materia_id);
CREATE INDEX IF NOT EXISTS idx_asignaciones_academica_id ON asignaciones USING btree (asignacion_academica_id);
CREATE INDEX IF NOT EXISTS idx_asignaciones_activo ON asignaciones USING btree (activo);
CREATE INDEX IF NOT EXISTS idx_asignaciones_curso_dia_activo ON asignaciones USING btree (curso_id, dia, activo);
CREATE INDEX IF NOT EXISTS idx_asignaciones_curso_orden_boletin ON asignaciones USING btree (curso_id, orden_boletin, materia_id) WHERE (activo = true);
CREATE UNIQUE INDEX IF NOT EXISTS idx_asignaciones_horario_activo_unico ON asignaciones USING btree (profesor_id, curso_id, materia_id, dia, hora_inicio, hora_fin) WHERE (activo = true);
CREATE INDEX IF NOT EXISTS idx_asignaciones_profesor_dia_activo ON asignaciones USING btree (profesor_id, dia, activo);
CREATE INDEX IF NOT EXISTS tenant_colegio_1_idx_asignaciones_curso_id ON asignaciones USING btree (curso_id);
CREATE INDEX IF NOT EXISTS tenant_colegio_1_idx_asignaciones_profesor_id ON asignaciones USING btree (profesor_id);
CREATE INDEX IF NOT EXISTS tenant_colegio_1_idx_asistencia_asignacion_periodo ON asistencia USING btree (asignacion_id, periodo);
CREATE INDEX IF NOT EXISTS tenant_colegio_1_idx_asistencia_estudiante_fecha ON asistencia USING btree (estudiante_id, fecha);
CREATE INDEX IF NOT EXISTS tenant_colegio_1_idx_boletin_cabecera_lookup ON boletin_cabecera USING btree (estudiante_id, asignacion_id, periodo);
CREATE INDEX IF NOT EXISTS idx_cursos_anio_lectivo ON cursos USING btree (anio_lectivo_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_cursos_anio_nombre_jornada_unico ON cursos USING btree (anio_lectivo_id, upper(regexp_replace(TRIM(BOTH FROM nombre), '[[:space:]]+'::text, ' '::text, 'g'::text)), lower(COALESCE(NULLIF(TRIM(BOTH FROM jornada), ''::text), 'Mañana'::text))) WHERE (NULLIF(TRIM(BOTH FROM COALESCE(nombre, ''::character varying)), ''::text) IS NOT NULL);
CREATE INDEX IF NOT EXISTS idx_cursos_curso_origen ON cursos USING btree (curso_origen_id);
CREATE INDEX IF NOT EXISTS idx_cursos_director_grupo ON cursos USING btree (director_grupo_id);
CREATE INDEX IF NOT EXISTS idx_cursos_estado ON cursos USING btree (estado);
CREATE INDEX IF NOT EXISTS idx_cursos_nivel ON cursos USING btree (nivel);
CREATE INDEX IF NOT EXISTS idx_egresos_origen ON egresos USING btree (origen);
CREATE INDEX IF NOT EXISTS tenant_colegio_1_idx_estudiantes_curso_id ON estudiantes USING btree (curso_id);
CREATE INDEX IF NOT EXISTS idx_inventario_estado ON inventario USING btree (estado);
CREATE INDEX IF NOT EXISTS idx_listas_seguimiento_columnas_curso ON listas_seguimiento_columnas USING btree (curso_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_listas_seguimiento_columnas_nombre_unico ON listas_seguimiento_columnas USING btree (curso_id, upper(regexp_replace(TRIM(BOTH FROM nombre), '[[:space:]]+'::text, ' '::text, 'g'::text)));
CREATE INDEX IF NOT EXISTS idx_listas_seguimiento_marcas_columna ON listas_seguimiento_marcas USING btree (columna_id);
CREATE INDEX IF NOT EXISTS idx_listas_seguimiento_marcas_estudiante ON listas_seguimiento_marcas USING btree (estudiante_id);
CREATE INDEX IF NOT EXISTS idx_materias_estado ON materias USING btree (estado);
CREATE UNIQUE INDEX IF NOT EXISTS idx_materias_nombre_unico ON materias USING btree (upper(regexp_replace(TRIM(BOTH FROM nombre), '[[:space:]]+'::text, ' '::text, 'g'::text))) WHERE (NULLIF(TRIM(BOTH FROM COALESCE(nombre, ''::character varying)), ''::text) IS NOT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS idx_matriculas_estudiante_anio_unico ON matriculas USING btree (estudiante_id, anio_lectivo_id);
CREATE INDEX IF NOT EXISTS tenant_colegio_1_idx_notas_detalle_estudiante_asignacion_period ON notas_detalle USING btree (estudiante_id, asignacion_id, periodo);
CREATE INDEX IF NOT EXISTS idx_observador_anotaciones_estudiante_anio ON observador_anotaciones USING btree (estudiante_id, anio_lectivo_id);
CREATE INDEX IF NOT EXISTS tenant_colegio_1_idx_observador_anotaciones_estudiante ON observador_anotaciones USING btree (estudiante_id, creada_en);
CREATE INDEX IF NOT EXISTS idx_pagos_estado ON pagos USING btree (estado);
CREATE INDEX IF NOT EXISTS idx_pagos_estudiante_anio_lectivo ON pagos USING btree (estudiante_id, anio_lectivo_id);
CREATE INDEX IF NOT EXISTS idx_pagos_venta_id ON pagos USING btree (venta_id);
CREATE INDEX IF NOT EXISTS tenant_colegio_1_idx_pagos_estudiante_id ON pagos USING btree (estudiante_id);
CREATE INDEX IF NOT EXISTS tenant_colegio_1_idx_pagos_fecha ON pagos USING btree (fecha);
CREATE INDEX IF NOT EXISTS tenant_colegio_1_idx_pagos_fecha_pago ON pagos USING btree (fecha_pago);
CREATE INDEX IF NOT EXISTS idx_pagos_aplicaciones_cuota_activa ON pagos_aplicaciones USING btree (estudiante_id, tipo_pago_id, periodo) WHERE (activo = true);
CREATE INDEX IF NOT EXISTS idx_pagos_aplicaciones_estudiante_periodo ON pagos_aplicaciones USING btree (estudiante_id, periodo);
CREATE INDEX IF NOT EXISTS idx_pagos_aplicaciones_pago ON pagos_aplicaciones USING btree (pago_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_pagos_aplicaciones_pago_periodo_activas ON pagos_aplicaciones USING btree (pago_id, tipo_pago_id, periodo) WHERE (activo = true);
CREATE INDEX IF NOT EXISTS idx_plan_de_clases_estado_revision ON plan_de_clases USING btree (estado_revision, enviado_at DESC);
CREATE INDEX IF NOT EXISTS idx_plan_de_clases_fecha ON plan_de_clases USING btree (fecha);
CREATE INDEX IF NOT EXISTS tenant_colegio_1_idx_plan_de_clases_asignacion_fecha ON plan_de_clases USING btree (asignacion_id, fecha);
CREATE INDEX IF NOT EXISTS tenant_colegio_1_idx_plan_de_clases_fecha ON plan_de_clases USING btree (fecha);
CREATE UNIQUE INDEX IF NOT EXISTS uq_plan_de_clases_asignacion_fecha ON plan_de_clases USING btree (asignacion_id, fecha);
CREATE INDEX IF NOT EXISTS idx_plan_notificaciones_admin_pendientes ON plan_de_clases_notificaciones_admin USING btree (creada_at DESC) WHERE (leida_at IS NULL);
CREATE INDEX IF NOT EXISTS idx_plan_notificaciones_admin_plan ON plan_de_clases_notificaciones_admin USING btree (plan_id, plan_version DESC);
CREATE INDEX IF NOT EXISTS idx_plan_observaciones_plan ON plan_de_clases_observaciones USING btree (plan_id, creada_at DESC);
CREATE INDEX IF NOT EXISTS idx_plan_observaciones_profesor_pendientes ON plan_de_clases_observaciones USING btree (plan_id, creada_at DESC) WHERE (vista_por_profesor_at IS NULL);
CREATE UNIQUE INDEX IF NOT EXISTS idx_planilla_subnotas_nombre_unico ON planilla_subnotas USING btree (asignacion_id, periodo, lower(TRIM(BOTH FROM tipo_nota)), lower(TRIM(BOTH FROM nombre)));
CREATE UNIQUE INDEX IF NOT EXISTS idx_planilla_tipos_porcentaje_tipo_unico ON planilla_tipos_porcentaje USING btree (asignacion_id, periodo, lower(TRIM(BOTH FROM tipo_nota)));
CREATE UNIQUE INDEX IF NOT EXISTS idx_plantilla_activa_unica ON plantilla_impresion USING btree (tipo) WHERE (activa = true);
CREATE UNIQUE INDEX IF NOT EXISTS idx_plantilla_codigo_unico ON plantilla_impresion USING btree (codigo) WHERE (codigo IS NOT NULL);
CREATE INDEX IF NOT EXISTS idx_plantilla_tipo ON plantilla_impresion USING btree (tipo);
CREATE UNIQUE INDEX IF NOT EXISTS idx_profesor_documento_unico ON profesor USING btree (TRIM(BOTH FROM documento_identidad)) WHERE (NULLIF(TRIM(BOTH FROM COALESCE(documento_identidad, ''::character varying)), ''::text) IS NOT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS idx_profesor_email_unico ON profesor USING btree (lower(TRIM(BOTH FROM email))) WHERE (NULLIF(TRIM(BOTH FROM COALESCE(email, ''::character varying)), ''::text) IS NOT NULL);
CREATE INDEX IF NOT EXISTS idx_profesor_estado ON profesor USING btree (estado);
CREATE INDEX IF NOT EXISTS idx_tipos_de_pagos_anio_lectivo ON tipos_de_pagos USING btree (anio_lectivo_id);
CREATE INDEX IF NOT EXISTS idx_tipos_de_pagos_tipo_pago_origen ON tipos_de_pagos USING btree (tipo_pago_origen_id);
CREATE INDEX IF NOT EXISTS idx_tipos_pagos_cursos_curso ON tipos_pagos_cursos USING btree (curso_id);
CREATE INDEX IF NOT EXISTS idx_tipos_pagos_cursos_tipo ON tipos_pagos_cursos USING btree (tipo_pago_id);
CREATE INDEX IF NOT EXISTS idx_tipos_pagos_estudiantes_activo ON tipos_pagos_estudiantes USING btree (activo);
CREATE INDEX IF NOT EXISTS idx_tipos_pagos_estudiantes_estudiante ON tipos_pagos_estudiantes USING btree (estudiante_id);
CREATE INDEX IF NOT EXISTS idx_tipos_pagos_estudiantes_tipo ON tipos_pagos_estudiantes USING btree (tipo_pago_id);
CREATE INDEX IF NOT EXISTS idx_ventas_estado ON ventas USING btree (estado);
CREATE INDEX IF NOT EXISTS tenant_colegio_1_idx_ventas_estudiante_estado ON ventas USING btree (estudiante_id, estado);

-- Claves foraneas, al final para no depender del orden de creacion
ALTER TABLE admisiones ADD CONSTRAINT admisiones_anio_lectivo_fkey FOREIGN KEY (anio_lectivo_id) REFERENCES anios_lectivos(id);
ALTER TABLE admisiones ADD CONSTRAINT admisiones_curso_anio_lectivo_fkey FOREIGN KEY (curso_id, anio_lectivo_id) REFERENCES cursos(id, anio_lectivo_id);
ALTER TABLE admisiones ADD CONSTRAINT admisiones_estudiante_fkey FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id);
ALTER TABLE anios_lectivos_materias_ocultas ADD CONSTRAINT anios_lectivos_materias_ocultas_anio_fkey FOREIGN KEY (anio_lectivo_id) REFERENCES anios_lectivos(id);
ALTER TABLE anios_lectivos_materias_ocultas ADD CONSTRAINT anios_lectivos_materias_ocultas_materia_fkey FOREIGN KEY (materia_id) REFERENCES materias(id);
ALTER TABLE asignaciones ADD CONSTRAINT asignaciones_asignacion_academica_id_fkey FOREIGN KEY (asignacion_academica_id) REFERENCES asignaciones(id);
ALTER TABLE asignaciones ADD CONSTRAINT asignaciones_curso_id_fkey FOREIGN KEY (curso_id) REFERENCES cursos(id);
ALTER TABLE asignaciones ADD CONSTRAINT asignaciones_materia_id_fkey FOREIGN KEY (materia_id) REFERENCES materias(id);
ALTER TABLE asignaciones ADD CONSTRAINT asignaciones_profesor_id_fkey FOREIGN KEY (profesor_id) REFERENCES profesor(id);
ALTER TABLE asistencia ADD CONSTRAINT asistencia_asignacion_id_fkey FOREIGN KEY (asignacion_id) REFERENCES asignaciones(id) ON DELETE CASCADE;
ALTER TABLE asistencia ADD CONSTRAINT asistencia_estudiante_id_fkey FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id);
ALTER TABLE boletin_cabecera ADD CONSTRAINT boletin_cabecera_asignacion_id_fkey FOREIGN KEY (asignacion_id) REFERENCES asignaciones(id) ON DELETE CASCADE;
ALTER TABLE boletin_cabecera ADD CONSTRAINT boletin_cabecera_estudiante_id_fkey FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE;
ALTER TABLE boletin_detalles ADD CONSTRAINT boletin_detalles_boletin_id_fkey FOREIGN KEY (boletin_id) REFERENCES boletin_cabecera(id) ON DELETE CASCADE;
ALTER TABLE cursos ADD CONSTRAINT cursos_anio_lectivo_id_fkey FOREIGN KEY (anio_lectivo_id) REFERENCES anios_lectivos(id);
ALTER TABLE cursos ADD CONSTRAINT cursos_curso_origen_id_fkey FOREIGN KEY (curso_origen_id) REFERENCES cursos(id);
ALTER TABLE cursos ADD CONSTRAINT cursos_director_grupo_id_fkey FOREIGN KEY (director_grupo_id) REFERENCES profesor(id) ON DELETE SET NULL;
ALTER TABLE estudiantes ADD CONSTRAINT estudiantes_curso_id_fkey FOREIGN KEY (curso_id) REFERENCES cursos(id);
ALTER TABLE listas_seguimiento_columnas ADD CONSTRAINT listas_seguimiento_columnas_curso_id_fkey FOREIGN KEY (curso_id) REFERENCES cursos(id) ON DELETE CASCADE;
ALTER TABLE listas_seguimiento_marcas ADD CONSTRAINT listas_seguimiento_marcas_columna_id_fkey FOREIGN KEY (columna_id) REFERENCES listas_seguimiento_columnas(id) ON DELETE CASCADE;
ALTER TABLE listas_seguimiento_marcas ADD CONSTRAINT listas_seguimiento_marcas_estudiante_id_fkey FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE;
ALTER TABLE matriculas ADD CONSTRAINT matriculas_anio_lectivo_id_fkey FOREIGN KEY (anio_lectivo_id) REFERENCES anios_lectivos(id);
ALTER TABLE matriculas ADD CONSTRAINT matriculas_curso_anio_lectivo_fkey FOREIGN KEY (curso_id, anio_lectivo_id) REFERENCES cursos(id, anio_lectivo_id);
ALTER TABLE matriculas ADD CONSTRAINT matriculas_curso_id_fkey FOREIGN KEY (curso_id) REFERENCES cursos(id);
ALTER TABLE matriculas ADD CONSTRAINT matriculas_estudiante_id_fkey FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id);
ALTER TABLE nomina ADD CONSTRAINT nomina_profesor_id_fkey FOREIGN KEY (profesor_id) REFERENCES profesor(id) ON DELETE CASCADE;
ALTER TABLE notas ADD CONSTRAINT notas_asignacion_id_fkey FOREIGN KEY (asignacion_id) REFERENCES asignaciones(id) ON DELETE CASCADE;
ALTER TABLE notas ADD CONSTRAINT notas_estudiante_id_fkey FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id);
ALTER TABLE notas_detalle ADD CONSTRAINT notas_detalle_asignacion_id_fkey FOREIGN KEY (asignacion_id) REFERENCES asignaciones(id) ON DELETE CASCADE;
ALTER TABLE notas_detalle ADD CONSTRAINT notas_detalle_estudiante_id_fkey FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id);
ALTER TABLE observaciones ADD CONSTRAINT observaciones_asignacion_id_fkey FOREIGN KEY (asignacion_id) REFERENCES asignaciones(id) ON DELETE CASCADE;
ALTER TABLE observaciones ADD CONSTRAINT observaciones_estudiante_id_fkey FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id);
ALTER TABLE observador_anotaciones ADD CONSTRAINT observador_anotaciones_anio_lectivo_id_fkey FOREIGN KEY (anio_lectivo_id) REFERENCES anios_lectivos(id);
ALTER TABLE observador_anotaciones ADD CONSTRAINT observador_anotaciones_editada_por_fkey FOREIGN KEY (editada_por) REFERENCES profesor(id);
ALTER TABLE observador_anotaciones ADD CONSTRAINT observador_anotaciones_estudiante_id_fkey FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id);
ALTER TABLE observador_anotaciones ADD CONSTRAINT observador_anotaciones_profesor_id_fkey FOREIGN KEY (profesor_id) REFERENCES profesor(id);
ALTER TABLE pagos ADD CONSTRAINT pagos_anio_lectivo_id_fkey FOREIGN KEY (anio_lectivo_id) REFERENCES anios_lectivos(id);
ALTER TABLE pagos ADD CONSTRAINT pagos_estudiante_id_fkey FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id);
ALTER TABLE pagos ADD CONSTRAINT pagos_venta_id_fkey FOREIGN KEY (venta_id) REFERENCES ventas(id);
ALTER TABLE pagos_aplicaciones ADD CONSTRAINT pagos_aplicaciones_estudiante_id_fkey FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id);
ALTER TABLE pagos_aplicaciones ADD CONSTRAINT pagos_aplicaciones_pago_id_fkey FOREIGN KEY (pago_id) REFERENCES pagos(id);
ALTER TABLE pagos_aplicaciones ADD CONSTRAINT pagos_aplicaciones_tipo_pago_id_fkey FOREIGN KEY (tipo_pago_id) REFERENCES tipos_de_pagos(id);
ALTER TABLE plan_de_clases ADD CONSTRAINT plan_de_clases_admin_visto_por_fkey FOREIGN KEY (admin_visto_por) REFERENCES usuarios(id) ON DELETE SET NULL;
ALTER TABLE plan_de_clases ADD CONSTRAINT plan_de_clases_asignacion_id_fkey FOREIGN KEY (asignacion_id) REFERENCES asignaciones(id);
ALTER TABLE plan_de_clases ADD CONSTRAINT plan_de_clases_revisado_por_fkey FOREIGN KEY (revisado_por) REFERENCES usuarios(id) ON DELETE SET NULL;
ALTER TABLE plan_de_clases_notificaciones_admin ADD CONSTRAINT plan_de_clases_notificaciones_admin_plan_id_fkey FOREIGN KEY (plan_id) REFERENCES plan_de_clases(id) ON DELETE CASCADE;
ALTER TABLE plan_de_clases_observaciones ADD CONSTRAINT plan_de_clases_observaciones_admin_id_fkey FOREIGN KEY (admin_id) REFERENCES usuarios(id) ON DELETE SET NULL;
ALTER TABLE plan_de_clases_observaciones ADD CONSTRAINT plan_de_clases_observaciones_plan_id_fkey FOREIGN KEY (plan_id) REFERENCES plan_de_clases(id) ON DELETE CASCADE;
ALTER TABLE planeador_anual ADD CONSTRAINT planeador_anual_asignacion_id_fkey FOREIGN KEY (asignacion_id) REFERENCES asignaciones(id) ON DELETE CASCADE;
ALTER TABLE planilla_subnotas ADD CONSTRAINT planilla_subnotas_asignacion_id_fkey FOREIGN KEY (asignacion_id) REFERENCES asignaciones(id) ON DELETE CASCADE;
ALTER TABLE planilla_subnotas_valores ADD CONSTRAINT planilla_subnotas_valores_estudiante_id_fkey FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id);
ALTER TABLE planilla_subnotas_valores ADD CONSTRAINT planilla_subnotas_valores_subnota_id_fkey FOREIGN KEY (subnota_id) REFERENCES planilla_subnotas(id) ON DELETE CASCADE;
ALTER TABLE planilla_tipos_porcentaje ADD CONSTRAINT planilla_tipos_porcentaje_asignacion_id_fkey FOREIGN KEY (asignacion_id) REFERENCES asignaciones(id) ON DELETE CASCADE;
ALTER TABLE prestamos ADD CONSTRAINT prestamos_profesor_id_fkey FOREIGN KEY (profesor_id) REFERENCES profesor(id) ON DELETE CASCADE;
ALTER TABLE tipos_de_pagos ADD CONSTRAINT tipos_de_pagos_anio_lectivo_id_fkey FOREIGN KEY (anio_lectivo_id) REFERENCES anios_lectivos(id);
ALTER TABLE tipos_de_pagos ADD CONSTRAINT tipos_de_pagos_tipo_pago_origen_id_fkey FOREIGN KEY (tipo_pago_origen_id) REFERENCES tipos_de_pagos(id);
ALTER TABLE tipos_pagos_cursos ADD CONSTRAINT tipos_pagos_cursos_curso_id_fkey FOREIGN KEY (curso_id) REFERENCES cursos(id) ON DELETE CASCADE;
ALTER TABLE tipos_pagos_cursos ADD CONSTRAINT tipos_pagos_cursos_tipo_pago_id_fkey FOREIGN KEY (tipo_pago_id) REFERENCES tipos_de_pagos(id) ON DELETE CASCADE;
ALTER TABLE tipos_pagos_estudiantes ADD CONSTRAINT tipos_pagos_estudiantes_estudiante_id_fkey FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE;
ALTER TABLE tipos_pagos_estudiantes ADD CONSTRAINT tipos_pagos_estudiantes_tipo_pago_id_fkey FOREIGN KEY (tipo_pago_id) REFERENCES tipos_de_pagos(id) ON DELETE CASCADE;
ALTER TABLE ventas ADD CONSTRAINT ventas_estudiante_id_fkey FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE SET NULL;
ALTER TABLE ventas_detalle ADD CONSTRAINT ventas_detalle_inventario_id_fkey FOREIGN KEY (inventario_id) REFERENCES inventario(id) ON DELETE SET NULL;
ALTER TABLE ventas_detalle ADD CONSTRAINT ventas_detalle_venta_id_fkey FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE;

-- Funciones
CREATE OR REPLACE FUNCTION validar_profesor_responsable_materia_curso()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    IF NEW.activo = TRUE AND EXISTS (
        SELECT 1
        FROM asignaciones a
        WHERE a.activo = TRUE
          AND a.curso_id = NEW.curso_id
          AND a.materia_id = NEW.materia_id
          AND a.profesor_id <> NEW.profesor_id
          AND a.id <> COALESCE(NEW.id, -1)
    ) THEN
        RAISE EXCEPTION 'Esta materia ya tiene otro profesor asignado en este curso.'
            USING ERRCODE = '23505';
    END IF;

    RETURN NEW;
END;
$function$
;

-- Disparadores
CREATE TRIGGER trg_profesor_responsable_materia_curso BEFORE INSERT OR UPDATE OF profesor_id, curso_id, materia_id, activo ON asignaciones FOR EACH ROW EXECUTE FUNCTION validar_profesor_responsable_materia_curso();
