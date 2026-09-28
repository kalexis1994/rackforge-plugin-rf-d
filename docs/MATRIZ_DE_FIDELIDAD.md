# Matriz de fidelidad

Los estados `desconocido`, `hipótesis`, `modelado`, `contrastado` y `cerrado para alcance declarado` se aplican **por columna**. Una fuente que documenta un control no prueba el audio. El estado inicial de todos los bloques es `desconocido` o `hipótesis`.

| Bloque | Controles/datos | Topología/tiempo | Transferencia/cálculo | Audio físico | Riesgo audible | Próximo gate |
| --- | --- | --- | --- | --- | --- | --- |
| Teclado/glide/ruedas | Hipótesis | Desconocido | Desconocido | Desconocido | Medio | Unidad y trazas de CV |
| Tres osciladores | Hipótesis | Hipótesis de manual | Desconocido | Desconocido | Alto | Revisión de placa, formas y calibración |
| Ruido/modulación | Hipótesis | Hipótesis de manual | Desconocido | Desconocido | Medio | Espectro y rutas aisladas |
| Mezclador/feedback | Hipótesis | Hipótesis de manual | Desconocido | Desconocido | Alto | Nivel y saturación por fuente |
| Filtro ladder | Hipótesis | Hipótesis de manual | Desconocido | Desconocido | Muy alto | Nodos, ajuste de servicio y barridos |
| Contornos/VCA | Hipótesis | Hipótesis de manual | Desconocido | Desconocido | Alto | Envolventes y transitorios |
| Salida | Hipótesis | Hipótesis de manual | Desconocido | Desconocido | Medio | Nivel, carga y recorte |

## Afirmación pública actual

RF-D **pretende** recrear un Model D clásico. No hay aún una implementación sonora ni resultados de comparación que permitan afirmar fidelidad.
