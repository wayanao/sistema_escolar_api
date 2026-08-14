# Capa 4: reportes financieros

Última revisión: 2026-08-14.

## Control

- Estado: **Activa**.
- Commit base: `46fad2c4c12482830cc58ac28ea2512f96155fb8`.
- Rama acordada: `main`.
- Estado al activar: árbol limpio; `HEAD` coincidente con la referencia local
  `origin/main`.
- Primera subcapa pendiente: **4.0**.
- Progreso: ninguna subcapa iniciada.
- Código de producto modificado al activar: **ninguno**.
- Autorización: orden explícita del usuario el 2026-08-14 para corregir la
  continuidad documental y activar la capa 4. La activación no autoriza iniciar
  4.0 en este mismo turno.

## Objetivo

Modularizar el dominio de reportes financieros separando HTTP, reglas,
servicios y persistencia; eliminar el N+1 mediante consultas agrupadas
equivalentes; y medir las consultas críticas con `EXPLAIN ANALYZE` sobre datos
no productivos.

El resultado debe conservar rutas, métodos, payloads, status codes, permisos,
tenant, ownership, cálculos, orden, transacciones y demás comportamiento
observable. El objetivo procede exclusivamente del índice maestro; la
activación no inspeccionó el código y por eso no afirma todavía qué endpoints,
archivos, consultas o pruebas forman el dominio.

## Dependencias de capas anteriores

- Compuerta única `scripts/verify.py`, heredada de la capa 0. El último cierre
  local registrado, correspondiente a la capa 3, terminó en exit 0 con 570
  pruebas, Ruff correcto y dependencias íntegras; no se reprodujo durante esta
  activación documental.
- Ciclo de vida de conexiones, transacciones y timeouts definido en la capa 1.
  La calibración operativa de `DB_STATEMENT_TIMEOUT_MS` sigue **pendiente y
  aceptada**.
- DB síncrona fuera del event loop y limitador compartido de capacidad
  establecidos en la capa 2. Esta capa no puede reintroducir trabajo bloqueante
  en el event loop ni cambiar esa capacidad sin una nueva auditoría.
- Tenants versionados y alta reproducible cerrados en la capa 3. Los dos schemas
  conservados tienen 37 claves foráneas, 30 secuencias propias y 30 migraciones
  registradas.
- La última evidencia de GitHub Actions corresponde a la capa 0. No existe
  evidencia de un run remoto asociado a los cambios posteriores y esa
  verificación permanece **pendiente y aceptada**.

## Alcance autorizado

- Inventariar las entradas HTTP, reglas, consultas, pruebas y consumidores del
  dominio de reportes financieros mediante búsquedas dirigidas.
- Caracterizar antes de extraer rutas, métodos, payloads, status codes,
  permisos, roles, tenant, ownership, cálculos, orden, transacciones y errores.
- Separar progresivamente HTTP, reglas, servicios y persistencia, con pruebas de
  caracterización previas a cada extracción importante.
- Identificar y eliminar el N+1 solo mediante consultas agrupadas cuya
  equivalencia funcional quede demostrada.
- Contar y comparar las consultas críticas antes y después.
- Ejecutar `EXPLAIN ANALYZE` únicamente sobre datos no productivos y registrar
  el plan y las condiciones de medición.

## Fuera de alcance

- Pagos y tipos de pago, que pertenecen a la capa 5, salvo la lectura mínima
  indispensable para caracterizar un contrato consumido por reportes.
- Cambiar rutas, payloads, status codes, permisos, roles, ownership, reglas
  financieras, redondeos, orden o semántica transaccional.
- Cambiar PostgreSQL, `psycopg2`, el modelo de schemas tenant, el pool, los
  timeouts, el limitador de concurrencia, el ORM o el driver.
- Agregar funciones de producto, rediseñar respuestas o corregir defectos
  ajenos a la primera subcapa pendiente.
- Crear abstracciones compartidas sin dos usos reales comprobados.
- Ejecutar `EXPLAIN ANALYZE`, pruebas destructivas o consultas de medición sobre
  producción; hacer deploy, migraciones reales, commit o push.

## Invariantes

- Métodos, paths, status codes y forma exacta de las respuestas permanecen
  idénticos.
- Permisos, roles, ownership y aislamiento entre tenants se conservan sin
  excepción.
- Importes, saldos, filtros, agrupaciones, orden, nulos y redondeos conservan su
  resultado actual.
- La propiedad de cursor, conexión, `commit`, `rollback` y devolución al pool
  definida en la capa 1 no cambia.
- Ninguna operación DB síncrona vuelve al event loop ni se altera el limitador
  compartido sin medir de nuevo su capacidad.
- El SQL de dominio se conserva hasta que una subcapa autorice, con
  caracterización previa, sustituir un N+1 por una consulta agrupada
  equivalente. Esa autorización no permite ningún otro cambio de semántica.
- Toda medición que dependa del volumen de datos se hace fuera de producción y
  declara el conjunto de datos y las limitaciones de la evidencia.

## Línea base

| Comprobación | Comando | Resultado |
|---|---|---|
| Pruebas específicas | Se determina en 4.0 después del inventario dirigido | Pendiente; no ejecutada al activar |
| Suite global | `.\venv\Scripts\python.exe scripts\verify.py` | Pendiente de reproducir en 4.0; último cierre registrado: 570 pruebas |
| Ruff | Ejecutado por la compuerta global | Pendiente de reproducir en 4.0 |
| Dependencias | Ejecutado por la compuerta global | Pendiente de reproducir en 4.0 |

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 4.0 | Inventario, contratos, caracterización y línea base de consultas | **Pendiente** |

Las subcapas siguientes se definirán al cerrar 4.0 con evidencia del código y
las pruebas. No se anticipan fronteras, archivos ni mecanismos de
implementación durante la activación.

Nunca se ejecutan dos subcapas en el mismo turno.

## Primera subcapa pendiente: 4.0 — trabajo exacto

1. Confirmar `main`, árbol limpio y que todo commit posterior al base esté
   explicado en esta bitácora.
2. Reproducir la compuerta heredada y determinar las pruebas específicas sin
   ampliar el alcance.
3. Localizar mediante búsquedas dirigidas únicamente la documentación, entradas
   HTTP, archivos fuente y pruebas del dominio de reportes financieros.
4. Inventariar responsabilidades y dependencias actuales sin mover código:
   HTTP, reglas, persistencia, cálculos y efectos laterales.
5. Registrar los contratos observables exactos: rutas, métodos, payloads,
   status codes, permisos, tenant, ownership, orden, nulos, redondeos,
   transacciones y errores.
6. Caracterizar con pruebas los caminos que una extracción posterior pueda
   alterar. 4.0 no autoriza una extracción ni un cambio de producto.
7. Medir o instrumentar herméticamente el número de consultas de los caminos
   críticos para identificar con evidencia el N+1; no optimizarlo todavía.
8. Definir el conjunto no productivo y el procedimiento seguro que se usarán
   para `EXPLAIN ANALYZE`, sin acceder a producción.
9. Ejecutar las pruebas específicas, Ruff del alcance, la compuerta global y
   `git diff --check`; revisar que el diff pertenezca solo a 4.0.
10. Actualizar esta bitácora, definir la siguiente subcapa con la evidencia
    obtenida y detenerse sin iniciarla.

## Criterios de cierre de la subcapa 4.0

- El dominio y sus consumidores están inventariados con archivos y puntos de
  entrada concretos, sin lectura global innecesaria.
- Los contratos HTTP, financieros, de seguridad, tenant y transacción están
  enumerados y protegidos por caracterización suficiente.
- El N+1 está localizado con una línea base reproducible de consultas, no por
  inferencia.
- Existe un procedimiento de medición con `EXPLAIN ANALYZE` limitado a datos no
  productivos.
- No se modificó producto ni se inició una extracción.
- Pruebas específicas, Ruff, compuerta global y `git diff --check` terminan
  correctamente, y el diff es exclusivo de 4.0.
- La siguiente subcapa queda definida y no iniciada.

## Criterios de cierre de la capa

- Todas las subcapas necesarias están cerradas o marcadas `No aplica` con
  justificación.
- HTTP, reglas, servicios y persistencia del dominio están separados con
  contratos estables.
- El N+1 está eliminado mediante consultas agrupadas equivalentes y la mejora
  está medida.
- Las consultas críticas tienen evidencia de `EXPLAIN ANALYZE` sobre datos no
  productivos.
- Rutas, payloads, status codes, permisos, tenant, ownership, cálculos,
  transacciones y comportamiento observable permanecen conservados.
- La compuerta global, Ruff, dependencias y `git diff --check` terminan
  correctamente.
- Staging, rollback y verificación manual están documentados.
- La capa 5 queda en espera y no se activa sin orden explícita del usuario.

## Decisiones

- Se usa `46fad2c4c12482830cc58ac28ea2512f96155fb8` como commit base porque es el
  `HEAD` limpio vigente de `main` y coincide con la referencia local
  `origin/main` al activar.
- Los 13 commits posteriores al base de la capa 3 fueron auditados; sus asuntos
  y archivos están explicados materialmente en `03_MIGRACIONES_TENANTS.md`. No
  hay commits ajenos ni divergencia local.
- El usuario eligió continuar localmente y activar esta capa manteniendo
  pendientes la calibración de `DB_STATEMENT_TIMEOUT_MS` y la evidencia remota
  de GitHub Actions. Ninguna se marca como cumplida.
- La activación corrige la continuidad obsoleta de la capa 3 y consume la
  autorización puntual guardada en `PROMPT_CONTINUACION.md`.
- 4.0 queda limitada a inventario, contratos, caracterización y línea base. La
  activación no inventa las subcapas de implementación antes de leer el código.

## Riesgos

- Un reporte financiero puede parecer equivalente y aun cambiar importes,
  filtros, nulos, redondeos u orden. La mitigación es caracterizar respuestas y
  cálculos antes de separar o agrupar consultas.
- Una consulta agrupada puede romper permisos, ownership o aislamiento entre
  tenants aunque reduzca el número de consultas. La equivalencia debe incluir
  esos límites, no solo los totales.
- `DB_STATEMENT_TIMEOUT_MS` sigue sin calibrar. Una medición local no demuestra
  que una consulta pesada termine dentro del límite adecuado en el entorno real;
  el valor debe seguir tratándose como riesgo operativo pendiente.
- No hay evidencia de GitHub Actions para los cambios posteriores a la capa 0.
  Las verificaciones locales no se presentarán como CI remota.
- La capa 3 repuso claves foráneas en `tenant_2005`. Si el inventario descubre
  que algún reporte inserta o borra, puede encontrar restricciones que antes no
  existían; se documentará el comportamiento y no se cambiarán las claves por
  inferencia.
- `EXPLAIN ANALYZE` ejecuta la consulta. Debe usarse solo en un entorno no
  productivo confirmado y con datos adecuados; nunca contra producción.

## Registro de ejecución

### 2026-08-14 — activación de la capa

- Modo de acceso: mismo checkout local; Git validado directamente en
  `C:\Users\David\Documents\sistema_escolar_api`.
- Autorización: orden explícita del usuario para corregir la continuidad
  documental y activar la capa 4. La decisión mantiene pendientes y acepta el
  riesgo de `DB_STATEMENT_TIMEOUT_MS` sin calibrar y de la CI remota sin
  evidencia posterior a la capa 0.
- Rama acordada: `main`.
- Estado antes de escribir: árbol limpio; `HEAD` y la referencia local
  `origin/main` en `46fad2c4c12482830cc58ac28ea2512f96155fb8`.
- Continuidad: el base de la capa 3,
  `81882f3b1ee9e3b50076b0fc1fd93dcd9fd5ac70`, existe y es ancestro de `HEAD`.
  Sus 13 commits posteriores forman una historia lineal y todos están
  explicados en la bitácora cerrada.
- Archivos creados o modificados: esta bitácora,
  `docs/modularizacion/README.md`,
  `docs/modularizacion/03_MIGRACIONES_TENANTS.md` y
  `docs/modularizacion/PROMPT_CONTINUACION.md`.
- Correcciones de continuidad: el control de la capa 3 deja de señalar 3.5 como
  pendiente, el recuento pasa de 11 a 13 commits, el índice registra como
  resueltos la verificación manual y los dos puntos abiertos, y se retira la
  autorización puntual ya consumida.
- Código de producto, pruebas, consultas, configuración, dependencias y
  workflow inspeccionados o modificados: **ninguno**.
- Pruebas, migraciones, conexiones a PostgreSQL, acceso a producción, commit,
  push y deploy: **ninguno**.
- Comandos de precondición: `git status --short --branch`,
  `git branch --show-current`, `git rev-parse HEAD`,
  `git rev-parse --verify origin/main`, `git merge-base --is-ancestor` y
  `git log --reverse` desde el base de la capa 3; todos con resultado coherente
  con la activación.
- Verificación documental: `git diff --check` en exit 0; el chequeo equivalente
  del archivo nuevo no reportó errores de whitespace; `git status --short`
  contiene exclusivamente los cuatro documentos declarados; el índice marca
  exactamente una capa activa; y el diff completo fue revisado como
  exclusivamente documental.
- Evidencia remota: no se consultó ni se atribuye ningún run de GitHub Actions.
- Estado: capa 4 **activa**; 4.0 **pendiente y no iniciada**.
- Siguiente acción exacta: ejecutar únicamente 4.0 conforme al trabajo exacto
  anterior y detenerse antes de la siguiente subcapa.

## Entrega al próximo chat

- Capa activa: **4, reportes financieros**.
- Última subcapa terminada: ninguna de la capa 4; la última del programa fue
  3.6, cierre de la capa 3.
- Primera subcapa pendiente: **4.0**, inventario, contratos, caracterización y
  línea base de consultas.
- Commit base: `46fad2c4c12482830cc58ac28ea2512f96155fb8`, rama `main`.
- Precondición antes de 4.0: el usuario debe revisar esta activación y el árbol
  debe volver a estar limpio. Permanecen pendientes y aceptadas la calibración
  operativa de `DB_STATEMENT_TIMEOUT_MS` y la evidencia de GitHub Actions
  posterior a la capa 0.
- Siguiente acción exacta: revalidar Git, reproducir la compuerta, inspeccionar
  únicamente la documentación, código y pruebas relacionados con reportes
  financieros, completar 4.0 y detenerse sin iniciar otra subcapa.
