# Matriz de fidelidad

Los estados `desconocido`, `hipótesis`, `modelado`, `contrastado` y `cerrado para alcance declarado` se aplican **por columna**. Una fuente que documenta un control no prueba el audio. El estado inicial de todos los bloques es `desconocido` o `hipótesis`. La columna de audio identifica evidencia **externa**, no mediciones propias: RF-D se desarrolla [sin acceso físico](VALIDACION_SIN_HARDWARE.md).

| Bloque | Controles/datos | Topología/tiempo | Transferencia/cálculo | Audio externo | Riesgo audible | Próximo gate |
| --- | --- | --- | --- | --- | --- | --- |
| Teclado/glide/ruedas | Hipótesis | Desconocido | Desconocido | Desconocido | Medio | Grafo de placa 2 y escenas de legato simuladas |
| Tres osciladores | Entradas IC1 cotejadas; ley de panel y ancho de pulso pendiente | Rampa C1, bases Qa/Qb/Qc, lazo IC3, [etapa FET/Q3](VCO1_AMPLIFICADOR_FET.md), [Q2/Q1 y 21B](VCO1_TRIANGULO.md), [Q11/Q12 y 20B](VCO1_PULSO.md), [cargas de 9B](VCO1_SALIDA_SIERRA.md), ramal Q5/Q6→Q10 y pinout IC2 de [VCO 1](VCO1_CA3046.md); reset y cargas de panel parcialmente trazadas | [Razón exponencial ideal](VCO1_CONVERTIDOR_IDEAL.md), puerta FET y pesos pasivos de 9B/21B/20B, [control 22B, SW6 y R6/R45 como dos puertos](VCO1_CABLEADO_PANEL.md) **condicionados**; corriente absoluta y solver pendientes | Candidatos sin analizar | Alto | Punto DC del convertidor, curvas FET/BJT, R78 dinámica, Schmitt/reset, mapa de posiciones de SW6, bus de mezcla y solución acoplada |
| Ruido/modulación | Hipótesis | Hipótesis de manual | Desconocido | Desconocido | Medio | Redes y espectro calculado |
| Mezclador/feedback | Cinco fuentes e interruptores ON [trazados](MEZCLADOR_PANEL.md); J2 y SW15/16/17 de control de filtro con estados [trazados](BASE_Q26_CONTROL_FILTRO.md); R14 EMPHASIS 50 kΩ identificado, ley de giro y contactos OFF del mixer pendientes | Bus, [entrada C27/Q29](ENTRADA_FILTRO.md), [retorno C10→R14→R73→Q30](REGENERACION_FILTRO.md), [par inferior](PAR_ENTRADA_FILTRO_IDEAL.md), [base Q26](BASE_Q26_CONTROL_FILTRO.md) y [red Q26/Q28](COLA_FILTRO_Q26_Q28.md) trazados; R61 conflictivo | [KCL de cinco fuentes](MEZCLADOR_PANEL.md), [dos cargas pasivas](ENTRADA_FILTRO.md), [retorno pasivo](REGENERACION_FILTRO.md), [partición ideal Q29/Q30](PAR_ENTRADA_FILTRO_IDEAL.md), [base y llaves J2/SW15/SW16/SW17](BASE_Q26_CONTROL_FILTRO.md), [punto DC Q26/Q28](COLA_FILTRO_ACOPLADA_DC.md) y [BOTTOM/bases/TAIL condicionados](BASES_FILTRO_ACOPLADAS_DC.md) para ambos R61; lazo y saturación desconocidos | Desconocido | Alto | Resolver R61, red OFF del mixer, inyección y colectores del ladder, fuentes y parámetros reales; contrastar niveles y resonancia |
| Filtro ladder | Hipótesis | Hipótesis de manual | Desconocido | Candidatos sin analizar | Muy alto | Ecuaciones, ajuste de servicio y barridos simulados |
| Contornos/VCA | Hipótesis | Hipótesis de manual | Desconocido | Desconocido | Alto | Redes RC, VCA y transitorios calculados |
| Salida | Hipótesis | Hipótesis de manual | Desconocido | Desconocido | Medio | Carga y recorte del esquema |

## Afirmación pública actual

En el ladder, la [columna resistiva DC](COLUMNA_RESISTIVA_LADDER_DC.md) y las [pilas activas](PILAS_ACTIVAS_LADDER_DC.md) están trazadas. El cálculo DC con β e `I_S` impuestos incluye las corrientes de tap y márgenes de colector; la saturación, transferencia completa y audio permanecen desconocidos, así como el valor físico de R61.

RF-D **pretende** recrear un Model D clásico. No hay aún una implementación sonora ni resultados de comparación que permitan afirmar fidelidad.

La ausencia de hardware propio es permanente para este plan. Cada bloque puede alcanzar `cerrado para alcance declarado` en **topología** y **cálculo**, mientras su audio externo permanezca abierto. Ese estado nunca se interpretará como identidad sonora con un ejemplar vintage.
