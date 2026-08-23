# Capa 7: super_admin

Última revisión: 2026-08-23.

## Control

- Estado: **Activa** desde el 2026-08-23 por orden explícita del usuario.
- Commit base: `2ec924a3308581b746a61fa24a44f71433034dbc`.
- Rama acordada: `main`.
- Primera subcapa pendiente: **7.0**, inventario, contratos y caracterización.
- Código de producto modificado al activar: **Ninguno**.
- Dominio de esta capa: **`super_admin`, y solo ese**.
- Autorización: el usuario escribió «sigue super admin» después de que se le
  informó que `profesores` estaba cerrado, que su verificación manual seguía
  pendiente y que `super_admin` permanecía en espera.
- Decisión sobre verificaciones pendientes: la orden nombra el siguiente
  dominio y autoriza continuar localmente aceptando que la verificación manual
  de `profesores`, la de `branding` y las heredadas sigan pendientes. Ninguna
  se marca como cumplida.
- La activación es exclusivamente documental. No autoriza implementar 7.0,
  hacer commit, push, deploy, migraciones reales ni acceder a producción.

## Objetivo

Migrar el dominio de **super_admin** con contratos y pruebas, conservando su
comportamiento observable actual y tratando como invariantes de seguridad sus
privilegios y cualquier operación transversal entre tenants.

El índice maestro exige trabajar un dominio a la vez, caracterizar antes de
extraer y no crear abstracciones compartidas sin dos usos reales. La activación
no inspecciona código ni infiere la frontera; 7.0 debe delimitarla con evidencia.

## Dependencias de capas anteriores

- La capa 7 para `profesores` está cerrada: 7.0 y 7.1 completas, 7.2 y 7.3
  **No aplica**, compuerta de cierre con **1061 pruebas**, Ruff correcto y
  dependencias íntegras.
- Staging y rollback de `profesores` están documentados; su verificación manual
  propia permanece pendiente.
- El commit base de esta capa es el `HEAD` limpio vigente,
  `2ec924a3308581b746a61fa24a44f71433034dbc`.
- Los cuatro commits posteriores al base de `profesores` están explicados en su
  bitácora: `4f459c1` activa el dominio, `3ae2884` cierra 7.0, `3eb6a44`
  contiene 7.1 y `2ec924a` contiene el cierre documental. Sus archivos
  coinciden con el alcance registrado.
- `HEAD` coincide con la referencia local `origin/main`. No se consultó el
  remoto real ni se atribuye publicación, despliegue o GitHub Actions.
- Siguen pendientes, sin marcarse como cumplidas: la calibración operativa
  final de `DB_STATEMENT_TIMEOUT_MS`; evidencia de GitHub Actions posterior a
  la capa 0; pasos manuales heredados no confirmados; las verificaciones
  manuales de `branding` y `profesores`; y la rotación de la credencial
  privilegiada registrada en la capa 4.

## Alcance autorizado

- Trabajar únicamente en el dominio `super_admin`.
- En 7.0, delimitar la frontera real por entradas, llamadores, tablas,
  consumidores y efectos laterales, no solo por nombres de archivo.
- Inventariar métodos, paths, guards, permisos, roles, operaciones globales,
  ownership, tenant, payloads, status codes, respuestas, SQL, transacciones,
  conexiones y concurrencia.
- Identificar de forma explícita cualquier capacidad de crear, modificar,
  desactivar o acceder a tenants y credenciales privilegiadas.
- Agregar o conservar pruebas de caracterización antes de una extracción.
- Medir consultas y conexiones críticas antes y después de cambios posteriores.

## Fuera de alcance

- Reabrir `profesores`, `branding` u otro dominio cerrado por inferencia.
- Completar verificaciones heredadas o rotar credenciales dentro de esta
  activación.
- Cambiar rutas, payloads, status codes, permisos, roles, ownership, tenant,
  SQL observable, transacciones o comportamiento actual sin autorización
  explícita apoyada en caracterización.
- Crear privilegios, endpoints o capacidades nuevas.
- Cambiar PostgreSQL, `psycopg2`, schemas tenant, pool, timeouts, concurrencia,
  ORM o driver.
- Migraciones reales, acceso a producción, DDL, DML, deploy, commit o push.

## Invariantes

- Métodos, paths, status codes y forma exacta de las respuestas permanecen
  idénticos.
- Permisos, roles, ownership, alcance global y aislamiento entre tenants se
  conservan exactamente.
- SQL, parámetros, número y orden observable de operaciones y límites de
  transacción se conservan.
- Se conserva quién posee conexión, cursor, `commit`, `rollback` y demás
  efectos laterales.
- La DB síncrona permanece fuera del event loop y el `ContextVar` del tenant se
  preserva donde corresponda.
- No se crea una abstracción compartida sin dos consumidores reales.

## Línea base

| Comprobación | Comando | Resultado |
|---|---|---|
| Pruebas específicas | Por determinar en 7.0 | Pendiente |
| Suite global | `.\venv\Scripts\python.exe scripts\verify.py` | Pendiente para 7.0 |
| Ruff | Archivos de la subcapa | Pendiente |
| Dependencias | Incluidas en `scripts\verify.py` | Pendiente para 7.0 |

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 7.0 | Inventario, contratos y caracterización | **Pendiente y no iniciada** |
| 7.1 | Primera extracción protegida | Pendiente de evidencia de 7.0 |
| 7.2 | Segunda extracción o integración | Pendiente de evidencia de 7.0 |
| 7.3 | Retiro heredado y cierre | Pendiente de evidencia de 7.0 |

Las subcapas se adaptan al trabajo real. Las innecesarias se marcan `No aplica`
con una explicación; nunca se ejecutan dos sin orden explícita.

## Primera subcapa pendiente: trabajo exacto para 7.0

1. Delimitar la frontera real de `super_admin` por entradas, llamadores,
   tablas, consumidores y efectos laterales antes de contar o modificar nada.
2. Inspeccionar únicamente la documentación, fuentes y pruebas relacionadas
   con esa frontera.
3. Inventariar contratos HTTP, permisos, privilegios, alcance global,
   ownership, tenant, SQL, transacciones, recursos y comportamiento observable.
4. Medir consultas y conexiones por camino y buscar dependencias del tamaño de
   entrada o resultado.
5. Identificar consumidores y dependencias compartidas sin modificar dominios
   cerrados.
6. Revisar las pruebas relacionadas y agregar caracterización sin cambiar
   expectativas heredadas.
7. Resolver los supuestos documentales que produzca el inventario y registrar
   hallazgos sin corregirlos.
8. Archivos modificables en 7.0: pruebas de caracterización del dominio, esta
   bitácora y el índice maestro. No modificar producto durante el inventario.
9. Ejecutar pruebas específicas, Ruff sobre la caracterización, la compuerta
   global, `git diff --check` y revisión de alcance.
10. Actualizar esta bitácora con archivos, comandos, resultados, decisiones,
    riesgos y la siguiente acción exacta.
11. Detenerse al cerrar 7.0. No iniciar 7.1 en el mismo turno.

## Criterios de cierre de la subcapa

- Frontera delimitada con evidencia y sin reabrir dominios cerrados.
- Contratos privilegiados y tenant fijados por pruebas ejecutables.
- Consultas, conexiones, transacciones y efectos laterales medidos.
- Pruebas específicas, Ruff, compuerta y dependencias correctas.
- `git diff --check` correcto y diff exclusivo de 7.0.
- Bitácora actualizada con resultados, riesgos y siguiente acción.

## Criterios de cierre de la capa

- Todas las subcapas necesarias están cerradas.
- Compuerta global correcta.
- Contratos conservados o cambios explícitamente aprobados.
- Staging, rollback y verificación manual documentados.
- No se activa otro trabajo sin una nueva orden explícita del usuario.

## Decisiones

- **Activar `super_admin` y solo ese dominio.** El usuario lo nombró en la
  orden «sigue super admin» después del cierre de `profesores`.
- **Continuar localmente con verificaciones pendientes.** La orden sigue al
  aviso explícito de la verificación manual pendiente de `profesores`; ninguna
  verificación se considera cumplida y sus riesgos permanecen vigentes.
- **Usar el `HEAD` limpio vigente como commit base.** Es el punto posterior al
  cierre documental de `profesores` y todos sus descendientes desde el base
  anterior están explicados.
- **Activación exclusivamente documental.** No se inspecciona ni implementa
  7.0 en este turno.
- **No inferir la frontera privilegiada.** Archivos, rutas, permisos y tablas
  quedan como preguntas que 7.0 debe resolver con evidencia.

## Riesgos

- **Verificación manual de `profesores` pendiente.** Se aceptó continuar; un
  fallo real de admin, tenant, login o ciclo CRUD podría no estar cubierto por
  la compuerta automática.
- **Verificación manual de `branding` y verificaciones heredadas pendientes.**
  Conservan sus riesgos y esta capa no puede presentarlas como cumplidas.
- **Dominio privilegiado.** Una frontera, guard o operación transversal mal
  caracterizada podría afectar varios tenants; 7.0 debe fijar el modelo real
  antes de cualquier extracción.
- **Credencial privilegiada pendiente de rotación.** La capa 4 la registró y
  esta activación no autoriza rotarla ni asumir que el riesgo desapareció.
- **Publicación no comprobada contra el remoto real.** `HEAD` coincide con la
  referencia local `origin/main`, pero no se consultó el remoto ni se verificó
  deploy o GitHub Actions.

## Registro de ejecución

### 2026-08-23 — activación de la capa para `super_admin`

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git y commits locales
  validados directamente.
- Documentos leídos en el orden exigido: índice maestro, bitácora cerrada más
  reciente `07_PROFESORES.md`, instrucciones locales —no se encontraron— y
  `PLANTILLA_CAPA.md`.
- Autorización: el usuario escribió «sigue super admin» después de ser
  informado del cierre de `profesores`, de su verificación manual pendiente y
  de que `super_admin` seguía en espera.
- Rama acordada y observada: `main`.
- Estado antes de escribir: árbol limpio; `git status --porcelain=v1 --branch`
  mostró únicamente `## main...origin/main`.
- Commit base: `2ec924a3308581b746a61fa24a44f71433034dbc`, el `HEAD`
  limpio vigente y coincidente con la referencia local `origin/main`.
- Continuidad: los cuatro descendientes del base de `profesores` son
  `4f459c1` —activación—, `3ae2884` —7.0—, `3eb6a44` —7.1— y `2ec924a`
  —cierre documental—. Todos están explicados; la inspección del último mostró
  únicamente los dos documentos registrados.
- Estado de publicación observado localmente: `HEAD` coincide con
  `origin/main`. No se consultó el remoto real ni se verificó GitHub Actions.
- Decisión heredada: permanecen pendientes las verificaciones manuales de
  `profesores` y `branding`, la calibración de timeout, la evidencia de CI, los
  pasos manuales heredados y la rotación de la credencial privilegiada. El
  usuario aceptó continuar con sus riesgos.
- Archivos creados o modificados: esta bitácora y
  `docs/modularizacion/README.md`.
- Código de producto, pruebas, consultas, migraciones, schemas, configuración
  y dependencias inspeccionados o modificados: **ninguno**.
- Pruebas, conexiones a PostgreSQL, acceso a producción, commit, push y deploy:
  **ninguno**.
- Verificación documental: `git diff --check` terminó en exit 0 para el índice;
  `git diff --no-index --check -- NUL
  docs/modularizacion/07_SUPER_ADMIN.md` no reportó errores de whitespace —su
  exit 1 indica que el archivo nuevo difiere de `NUL`—. Los avisos fueron solo
  de normalización futura LF/CRLF.
- Revisión de alcance: `git status --short --branch` mostró exactamente el
  índice modificado y esta bitácora nueva sobre `main...origin/main`. El índice
  contiene una sola fila **Activa** y corresponde a `super_admin`.
- Siguiente acción exacta: ejecutar únicamente 7.0 conforme al trabajo exacto
  de esta bitácora y detenerse antes de 7.1.

## Entrega al próximo chat

- Capa activa: **7 para `super_admin`**.
- Última capa cerrada: **7 para `profesores`**.
- Primera subcapa pendiente: **7.0**, inventario, contratos y caracterización.
- Verificaciones pendientes aceptadas: manuales de `profesores` y `branding`,
  además de las heredadas del índice.
- Bloqueos: ninguno.
- Siguiente acción exacta: esperar una orden nueva para ejecutar únicamente
  7.0 y detenerse antes de 7.1.
