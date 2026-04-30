


# Base de Datos - Sistema Escolar

---

## 📘 Tabla: estudiantes

- id (PK) - integer
- nombre - varchar
- apellido - varchar
- documento_identidad - varchar
- curso_id (FK → cursos.id)
- estado - varchar
- anio_escolar - integer
- fecha_nacimiento - date
- descuento_matricula - numeric
- descuento_mensualidad - numeric

---

## 📘 Tabla: cursos

- id (PK) - integer
- nombre - varchar
- descripcion - text
- matricula - numeric
- mensualidad - numeric
- meses - integer

---

## 📘 Tabla: materias

- id (PK) - integer
- nombre - varchar
- descripcion - varchar

---

## 📘 Tabla: profesor

- id (PK) - integer
- nombre - varchar
- apellido - varchar
- documento_identidad - varchar
- email - varchar
- telefono - varchar
- password - varchar

---

## 📘 Tabla: asignaciones

- id (PK) - integer
- curso_id (FK → cursos.id)
- materia_id (FK → materias.id)
- profesor_id (FK → profesor.id)

---

## 📘 Tabla: asistencia

- id (PK) - integer
- estudiante_id (FK → estudiantes.id)
- asignacion_id (FK → asignaciones.id)
- fecha - date
- estado - varchar

---

## 📘 Tabla: notas

- id (PK) - integer
- estudiante_id (FK → estudiantes.id)
- asignacion_id (FK → asignaciones.id)
- nota - numeric
- periodo - integer

---

## 📘 Tabla: notas_detalle

- id (PK) - integer
- estudiante_id (FK → estudiantes.id)
- asignacion_id (FK → asignaciones.id)
- descripcion - varchar
- nota - numeric
- fecha - date

---

## 📘 Tabla: observaciones

- id (PK) - integer
- estudiante_id
- asignacion_id
- periodo
- conductual - text
- cognitivo - text
- lenguaje - text

---

## 📘 Tabla: matriculas

- id (PK) - integer
- estudiante_id (FK → estudiantes.id)
- curso_id (FK → cursos.id)
- anio - integer

---

## 📘 Tabla: pagos

- id (PK) - integer
- estudiante_id (FK → estudiantes.id)
- tipo_pago - varchar(100)
- monto - numeric
- fecha_pago - date
- estado - varchar
- mes - varchar
- fecha - timestamp
- descripcion - varchar

---

## 📘 Tabla: tipos_de_pagos

- id (PK) - integer
- nombre - varchar
- valor - numeric

---

## 📘 Tabla: plan_de_clases

- id (PK) - integer
- asignacion_id (FK → asignaciones.id)
- periodo - integer
- unidad - varchar
- proposito - text
- clase - text
- estandar - varchar
- dba - varchar
- competencias - text
- actividad_casa - text
- tema - varchar
- fecha - date
- imagen1 - varchar
- imagen2 - varchar
- created_at - timestamp
- updated_at - timestamp

---

## 📘 Tabla: planeador_anual

- id (PK) - integer
- asignacion_id (FK → asignaciones.id)
- periodo - integer
- slot - integer
- unidad_tematica - text
- estandar_competencia - text
- contenido - text
- actividades_recursos - text
- fecha - date

---

## 📘 Tabla: usuarios

- id (PK) - integer
- nombre - text
- email - text
- password - text
- rol - text
