# Repositories

Usa esta carpeta para consultas SQL por modulo cuando refactorices controladores.

Ejemplo de criterio:

- `estudiante_repository.py`: consultas de estudiantes.
- `pagos_repository.py`: consultas y escrituras de pagos.
- `boletin_repository.py`: consultas de boletines.

Los repositories no deben conocer detalles HTTP de FastAPI. Deben recibir datos simples y devolver datos simples.
