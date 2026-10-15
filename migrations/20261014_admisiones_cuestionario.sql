-- Entrevista de admisión, paso E9. Ver
-- docs/funcionalidades/ENTREVISTA_ADMISION.md, "Preguntas del anexo".
--
-- Agrega a admisiones la columna cuestionario: las respuestas a las preguntas
-- del anexo del colegio (familia, vivienda, salud, inclusión,
-- comportamiento...), todas juntas en un bloque JSON. Cada respuesta va bajo
-- la clave de su pregunta; una pregunta sin responder no aparece.
--
-- Es invisible: ningún código la usa todavía. El paso E10 la lee y la escribe.
--
-- Decisiones que se ven en el SQL, cada una con su motivo:
--
--   - Un bloque y no una columna por pregunta (55): si el colegio cambia el
--     anexo, se cambia la lista de preguntas en el código, sin otra migración
--     en todos los colegios. La base ya guarda bloques así en la
--     configuración de impresión.
--
--   - NOT NULL con '{}' por defecto: las admisiones que ya existen quedan con
--     el bloque vacío, sin rellenar nada a mano, y "sin responder" nunca es
--     NULL. Una columna con un valor fijo por defecto no reescribe la tabla.
--
--   - La base solo exige que sea un bloque (un objeto JSON, no una lista ni
--     un texto suelto). Qué preguntas existen y qué respuestas valen lo revisa
--     el backend (paso E10), con mensajes claros.
--
--   - Sin índice: nadie busca por una pregunta suelta.
--
--   - Reejecutable: ADD COLUMN IF NOT EXISTS y la regla solo si falta. El
--     runner ya impide repetirla; esto cubre reejecutarla a mano tras un fallo.

ALTER TABLE admisiones
    ADD COLUMN IF NOT EXISTS cuestionario JSONB NOT NULL DEFAULT '{}'::jsonb;

-- PostgreSQL no ofrece ADD CONSTRAINT IF NOT EXISTS (mismo patrón que
-- 20261008_anios_lectivos_activacion.sql).
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_admisiones_cuestionario_objeto'
          AND conrelid = 'admisiones'::regclass
    ) THEN
        ALTER TABLE admisiones
            ADD CONSTRAINT chk_admisiones_cuestionario_objeto
            CHECK (jsonb_typeof(cuestionario) = 'object');
    END IF;
END
$$;
