ALTER TABLE cursos
    ADD COLUMN IF NOT EXISTS director_grupo_id INTEGER
    REFERENCES profesor(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_cursos_director_grupo
ON cursos (director_grupo_id);
