# Capa N: NOMBRE

Última revisión: AAAA-MM-DD.

## Control

- Estado: En espera / Activa / Cerrada / Bloqueada.
- Commit base: `COMMIT`.
- Rama acordada: `RAMA`.
- Primera subcapa pendiente: N.0.
- Código de producto modificado al activar: Ninguno.

## Objetivo

Resultado observable que debe quedar al cerrar esta capa.

## Dependencias de capas anteriores

- Contrato o herramienta que esta capa consume.
- Evidencia concreta de que la capa anterior está cerrada.

## Alcance autorizado

- Responsabilidades, archivos y comportamientos que pueden tocarse.

## Fuera de alcance

- Mejoras cercanas que deben permanecer separadas.
- Dominios o tecnologías que no se modificarán.

## Invariantes

- Contratos HTTP que no pueden cambiar.
- Roles, ownership y tenant que deben conservarse.
- SQL, transacciones, archivos o concurrencia relevantes.

## Línea base

| Comprobación | Comando | Resultado |
|---|---|---|
| Pruebas específicas | `COMANDO` | Pendiente |
| Suite global | `COMANDO` | Pendiente |
| Ruff | `COMANDO` | Pendiente |
| Dependencias | `COMANDO` | Pendiente |

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| N.0 | Inventario, contratos y caracterización | Pendiente |
| N.1 | Primera extracción protegida | Pendiente |
| N.2 | Segunda extracción o integración | Pendiente |
| N.3 | Retiro heredado y cierre | Pendiente |

Las subcapas se adaptan al trabajo real. Las innecesarias se marcan `No aplica`
con una explicación; nunca se ejecutan dos sin orden explícita.

## Subcapa activa: trabajo exacto

1. Acción limitada y verificable.
2. Prueba que debe existir antes del cambio.
3. Archivos permitidos.
4. Comandos de verificación.
5. Punto exacto donde debe detenerse.

## Criterios de cierre de la subcapa

- Resultado observable.
- Pruebas y lint correctos.
- Diff exclusivo y sin duplicación heredada.
- Bitácora actualizada.

## Criterios de cierre de la capa

- Todas las subcapas necesarias están cerradas.
- Compuerta global correcta.
- Contratos conservados o cambios explícitamente aprobados.
- Staging, rollback y verificación manual documentados.
- Siguiente capa autorizada por el usuario.

## Decisiones

- Decisión, motivo y alternativa descartada.

## Riesgos

- Riesgo, evidencia, mitigación y responsable de validarlo.

## Registro de ejecución

### AAAA-MM-DD — subcapa N.X

- Commit observado:
- Archivos modificados:
- Pruebas antes:
- Cambio realizado:
- Comandos y resultados:
- Decisiones:
- Riesgos:
- Siguiente acción exacta:

## Entrega al próximo chat

- Capa activa:
- Última subcapa terminada:
- Primera subcapa pendiente:
- Bloqueos:
- Siguiente acción exacta:
