# Matriz de fidelidad

Los estados `desconocido`, `hipótesis`, `modelado`, `contrastado` y `cerrado para alcance declarado` se aplican **por columna**. Una fuente que documenta un control no prueba el audio. El estado inicial de todos los bloques es `desconocido` o `hipótesis`. La columna de audio identifica evidencia **externa**, no mediciones propias: RF-D se desarrolla [sin acceso físico](VALIDACION_SIN_HARDWARE.md).

| Bloque | Controles/datos | Topología/tiempo | Transferencia/cálculo | Audio externo | Riesgo audible | Próximo gate |
| --- | --- | --- | --- | --- | --- | --- |
| Teclado/glide/ruedas | Hipótesis | Desconocido | Desconocido | Desconocido | Medio | Grafo de placa 2 y escenas de legato simuladas |
| Tres osciladores | Entradas IC1 cotejadas; ley de panel pendiente | Rampa C1, bases Qa/Qb/Qc, lazo IC3, tramo Q5/Q6→Q10 y pinout IC2 de [VCO 1](VCO1_CA3046.md); resto de reset hipótesis | [Razón exponencial ideal](VCO1_CONVERTIDOR_IDEAL.md) **condicionada**, corriente absoluta y solver pendientes | Candidatos sin analizar | Alto | Punto DC del convertidor, R78 dinámica, completar Schmitt/reset y salidas cargadas |
| Ruido/modulación | Hipótesis | Hipótesis de manual | Desconocido | Desconocido | Medio | Redes y espectro calculado |
| Mezclador/feedback | Hipótesis | Hipótesis de manual | Desconocido | Desconocido | Alto | Grafo, niveles y saturación por fuente |
| Filtro ladder | Hipótesis | Hipótesis de manual | Desconocido | Candidatos sin analizar | Muy alto | Ecuaciones, ajuste de servicio y barridos simulados |
| Contornos/VCA | Hipótesis | Hipótesis de manual | Desconocido | Desconocido | Alto | Redes RC, VCA y transitorios calculados |
| Salida | Hipótesis | Hipótesis de manual | Desconocido | Desconocido | Medio | Carga y recorte del esquema |

## Afirmación pública actual

RF-D **pretende** recrear un Model D clásico. No hay aún una implementación sonora ni resultados de comparación que permitan afirmar fidelidad.

La ausencia de hardware propio es permanente para este plan. Cada bloque puede alcanzar `cerrado para alcance declarado` en **topología** y **cálculo**, mientras su audio externo permanezca abierto. Ese estado nunca se interpretará como identidad sonora con un ejemplar vintage.
