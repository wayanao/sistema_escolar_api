ALTER TABLE cursos
    ADD COLUMN IF NOT EXISTS nivel VARCHAR(20);

ALTER TABLE cursos
    ADD CONSTRAINT chk_cursos_nivel
    CHECK (nivel IS NULL OR nivel IN ('preescolar', 'primaria'));

CREATE INDEX IF NOT EXISTS idx_cursos_nivel
ON cursos (nivel);
