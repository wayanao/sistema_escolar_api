-- Nombres de los cuadros del plan de clase, paso 1. Ver
-- docs/funcionalidades/NOMBRES_CUADROS_PLAN.md.
--
-- Cada colegio puede cambiar el nombre de los cuadros del plan de clase (y el
-- texto gris de ayuda de los cuadros de texto). Esta tabla guarda solo los
-- cuadros renombrados: un cuadro sin fila usa su nombre original, que vive en
-- el frontend. "Volver a los originales" borra todas las filas.
--
-- Una tabla enteramente nueva. Ninguna tabla existente se modifica, y
-- plan_de_clases no se toca: renombrar no cambia ningun plan.
--
-- Decisiones que se ven en el SQL, cada una con su motivo:
--
--   - clave es la llave primaria: un cuadro tiene como maximo un nombre. Que
--     clave sea uno de los nueve cuadros no es un CHECK: la lista vive en
--     app/core/cuadros_plan_de_clases.py, como las preguntas de la entrevista,
--     para que un cuadro nuevo no exija otra migracion en todos los colegios.
--
--   - nombre de 1 a 60 caracteres (varchar(60) mas un CHECK de no vacio).
--     ayuda hasta 150, vacia por defecto: vacia significa sin ayuda. El
--     backend revisa lo mismo antes, con mensajes en español.
--
--   - actualizado_por con ON DELETE SET NULL, igual que admin_visto_por y
--     revisado_por de plan_de_clases: borrar un admin no debe fallar ni
--     borrar los nombres del colegio.
--
--   - No se usa institucion_branding.configuracion_extra, aunque ya existe:
--     guardar la marca reemplaza ese bloque entero y borraria los nombres.
--
--   - Reejecutable: CREATE TABLE IF NOT EXISTS, con el CHECK dentro. El
--     runner ya impide repetirla; esto cubre reejecutarla a mano tras un
--     fallo.
--
-- Sin indice aparte: la llave primaria basta, y la tabla tiene como maximo
-- nueve filas.
--
-- Orden de publicacion: esta migracion se aplica ANTES del push del backend.
-- El codigo viejo no lee esta tabla, asi que aplicarla antes no cambia nada
-- para los colegios; el backend nuevo la lee al abrir el plan de clase.

CREATE TABLE IF NOT EXISTS plan_de_clases_cuadros (
    clave character varying(30) PRIMARY KEY,
    nombre character varying(60) NOT NULL,
    ayuda character varying(150) DEFAULT '' NOT NULL,
    actualizado_en timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    actualizado_por integer REFERENCES usuarios(id) ON DELETE SET NULL,
    CONSTRAINT chk_plan_de_clases_cuadros_nombre_no_vacio
        CHECK (char_length(btrim(nombre)) > 0)
);
