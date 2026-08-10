# Capa 0: línea base y calidad

Última revisión: 2026-08-10.

## Control

- Estado: Activa; todavía no iniciada en código.
- Commit base: `b8c7653445a50bc1e230a19e0ca8bb088c47cb69`.
- Rama observada al documentar: `main`, alineada con `origin/main`.
- Rama de trabajo: Debe acordarse antes de modificar código; se recomienda
  `refactor/backend-linea-base-calidad`.
- Primera subcapa pendiente: 0.0, inventario reproducible.
- Código de producto modificado: Ninguno.

## Objetivo

Establecer una línea base confiable antes de tocar conexiones, concurrencia,
migraciones o dominios. Al cerrar esta capa, cualquier chat o desarrollador debe
poder ejecutar una sola compuerta y distinguir un fallo nuevo de uno preexistente.

## Alcance autorizado

- Inventario de contratos HTTP que deberán conservar las capas posteriores.
- Caracterización reproducible del estado actual de pruebas y herramientas.
- Corrección de las tres pruebas identificadas como sensibles a la fecha real.
- Un comando global de verificación local.
- CI que ejecute la misma compuerta en un entorno limpio.
- Documentación estrictamente relacionada.

## Fuera de alcance

- Mover rutas, controladores, services o repositories.
- Cambiar conexiones, pool, transacciones o timeouts.
- Modificar comportamiento `async`, threadpool o `ContextVar`.
- Ejecutar o cambiar migraciones de tenants.
- Optimizar consultas, agregar índices o usar `EXPLAIN ANALYZE`.
- Agregar `response_model` o normalizar errores de producto.
- Corregir fallos funcionales ajenos a las tres pruebas temporales.

## Línea base conocida

Una auditoría previa registró estos resultados, que deben reproducirse y
detallarse en la subcapa 0.0 antes de modificar pruebas:

| Comprobación | Resultado previo |
|---|---|
| Descubrimiento de pytest | 192 pruebas |
| Suite consolidada | 189 pasaron; 3 fallaron por sensibilidad temporal |
| Uploads con temporal controlado | 6 pasaron |
| Ruff global sin caché | Correcto |
| `pip check` | Correcto |
| CI del repositorio | No encontrado |
| Comando global único | No encontrado |

Estos números son evidencia previa, no el resultado final de esta capa. La
bitácora debe registrar nombres de pruebas, comandos completos, entorno y salida
actual cuando comience la subcapa 0.0.

## Contratos que la línea base debe registrar

No es necesario describir toda la implementación. Para cada familia de
endpoints se necesita como mínimo:

- método y path;
- actor y permiso;
- contexto tenant y ownership;
- entrada: query, path, JSON o multipart;
- status y forma de respuesta exitosa;
- errores observables relevantes;
- transacción, archivos u otros efectos;
- pruebas existentes que lo protegen.

El catálogo global `docs/API_ENDPOINTS.md` puede utilizarse como punto de
partida, pero la caracterización verificable debe enlazar pruebas o evidencia.

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 0.0 | Inventario reproducible de comandos, fallos y contratos | Pendiente |
| 0.1 | Tres pruebas temporales convertidas en deterministas | Pendiente |
| 0.2 | Comando global local de verificación | Pendiente |
| 0.3 | CI ejecutando la misma compuerta | Pendiente |
| 0.4 | Cierre documental y validación completa | Pendiente |

Solo se ejecuta una subcapa por turno salvo orden explícita del usuario.

## Subcapa 0.0: trabajo exacto

Esta es la única subcapa que debe iniciar el próximo chat:

1. Confirmar rama, estado limpio y commit base.
2. Identificar las tres pruebas temporales exactas y explicar por qué dependen
   del reloj, sin corregirlas todavía.
3. Registrar los comandos válidos para pytest, Ruff y `pip check` usando el
   entorno del repositorio.
4. Ejecutar y documentar la línea base sin modificar código.
5. Inventariar los contratos por familias usando `docs/API_ENDPOINTS.md`, las
   rutas y las pruebas, sin leer controladores no requeridos.
6. Actualizar esta bitácora y detenerse.

## Criterios para cerrar 0.0

- Los tres fallos tienen nombre, causa y evidencia.
- Los comandos de verificación se pueden copiar y repetir.
- Los fallos genuinos se distinguen de problemas del entorno local.
- Cada familia HTTP tiene al menos la ficha mínima de contrato o un enlace
  concreto a evidencia existente.
- No hay cambios en código de producto ni en comportamiento.
- Pruebas específicas aplicables y `git diff --check` están registrados.

## Criterios para cerrar toda la capa 0

- La suite completa termina correctamente sin depender de la fecha actual.
- Existe un comando global documentado y reproducible.
- CI ejecuta la misma compuerta desde un checkout limpio.
- No se cambió ningún contrato HTTP ni comportamiento funcional.
- El diff pertenece exclusivamente a calidad, CI y documentación.
- Se documentaron decisiones, riesgos y rollback.
- El usuario autorizó activar la capa 1.

## Decisiones vigentes

- Las tres pruebas se arreglarán mediante control explícito del reloj o datos
  relativos; no se relajarán aserciones para ocultar el fallo.
- La compuerta local y CI deben llamar las mismas verificaciones, evitando dos
  definiciones divergentes.
- Instalar o fijar dependencias no se mezclará automáticamente con esta capa;
  cualquier cambio deberá justificarse por reproducibilidad.
- La capa 0 no se utilizará para comenzar la modularización de dominios.

## Riesgos

- Que una prueba aparentemente temporal revele en realidad un defecto de
  negocio. En ese caso se detiene y se solicita decisión.
- Diferencias de Windows/Linux en temporales o paths de uploads.
- Que CI necesite secretos o PostgreSQL no disponibles; deberá separarse una
  suite hermética de cualquier integración externa.
- Convertir el comando global en un script que oculte fallos o dependa del
  estado local.

## Registro de ejecución

Todavía no hay una subcapa ejecutada. Cada entrega debe agregar aquí:

- fecha y commit observado;
- archivos modificados;
- comandos y resultados exactos;
- decisiones y riesgos nuevos;
- subcapa cerrada;
- siguiente acción exacta.

## Entrega al próximo chat

- Leer primero `docs/modularizacion/README.md` completo.
- Leer después este archivo completo.
- Capa activa: 0.
- Primera subcapa pendiente: 0.0.
- Siguiente acción exacta: reproducir y documentar la línea base; no corregir
  todavía las tres pruebas ni iniciar la subcapa 0.1.
