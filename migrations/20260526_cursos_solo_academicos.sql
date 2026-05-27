-- Cursos dejan de administrar cobros.
-- La fuente financiera queda en tipos_de_pagos + tipos_pagos_cursos.

ALTER TABLE cursos
    DROP COLUMN IF EXISTS matricula,
    DROP COLUMN IF EXISTS mensualidad,
    DROP COLUMN IF EXISTS meses;
