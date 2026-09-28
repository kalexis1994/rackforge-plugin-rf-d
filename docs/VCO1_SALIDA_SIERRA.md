# VCO 1: cargas de la salida de sierra 9B

## Evidencia y alcance

El esquema de la placa CA3046 para números de serie menores de 10175 es SVC-9, Fig. 9-3, PDF p. 5. Los valores de repuesto se cotejaron con la tabla 7-5, PDF pp. 24–25. Las conexiones internas están en el [grafo parcial](../evidence/vco1_ramp_graph.json), y el [cableado de panel](VCO1_CABLEADO_PANEL.md) se trazó desde Fig. 9-17, PDF p. 19. No existe una medición propia del conector 9B.

## Conexiones directas del nodo 9B

| Rama | Otro extremo visible | Valor o tipo | Naturaleza de la carga |
| --- | --- | --- | --- |
| R34 | Colector de Q3 (`SCHMITT_DRIVE`) | 4,3 kΩ | Lleva la sierra interna a 9B. |
| R33 | Masa (`GND`) | 4,7 kΩ | Derivación a masa; su extremo superior comparte la línea de masa de Q5/Q6. |
| R23 | Salida `TRIANGLE #1`, terminal 21B | 8,2 kΩ | Acopla la etapa triangular a 9B. |
| R14 | Colector de Q2 / nodo de base de Q1 | 150 kΩ | Carga dependiente del formador triangular. |
| R29 | Emisor de Q2 | 10 kΩ, 1 % | Carga dependiente del formador triangular, omitida en el primer inventario de 9B. |
| R44 | Base de Q11 | 390 kΩ | Carga dependiente del formador de pulso. |
| R35 | Base de Q12 | 100 kΩ | Carga dependiente del formador de pulso. |
| Q12 | Emisor de 2N3392 | Transistor | Corriente no lineal del [formador de pulso](VCO1_PULSO.md), cuya salida está en 20B. |
| 9B | [R30/R31 de panel y SW6](VCO1_CABLEADO_PANEL.md) | 47 kΩ + 10 kΩ hacia 21B; R6 de 25 kΩ al seleccionar sierra | Carga externa por posición; cursor y mixer pendientes. |

La barra de −10 V pasa **por encima** de la salida de sierra, sin unión en los cruces de R33/R34. Esa distinción evita convertir R33 en una resistencia hacia −10 V. La forma rectangular sale por otro terminal, 20B, y el triángulo por 21B; el vínculo pasivo de 21B a 9B es R23.

## Cuenta pasiva condicionada

Si se imponen las tensiones de los otros siete extremos, se fija `I_emisor_Q12 = 0` sólo para esta cuenta y se deja abierto el cableado externo de 9B, la ley de nodos **de la placa aislada** es:

`V_9B = (V_Q3/R34 + 0/R33 + V_21B/R23 + V_Q2c/R14 + V_Q2e/R29 + V_Q11b/R44 + V_Q12b/R35) / G`,

con `G = 1/R34 + 1/R33 + 1/R23 + 1/R14 + 1/R29 + 1/R44 + 1/R35`.

El [trazado de Q2/Q1](VCO1_TRIANGULO.md) reveló R29 al completar el emisor de Q2. La [referencia ejecutable](../tools/vco1_saw_passive_reference.py) lee ahora las **siete** resistencias del grafo. La cuenta anterior de seis ramas (`1/G ≈ 1,705 kΩ`) era incompleta; con R29 entrega `1/G ≈ 1,457 kΩ` y estos coeficientes condicionados revisados:

| Tensión impuesta | Coeficiente en `V_9B` |
| --- | ---: |
| Colector de Q3 | 0,3388 |
| Masa | 0,3099 |
| Triángulo 21B | 0,1776 |
| Colector de Q2 | 0,0097 |
| Emisor de Q2 | 0,1457 |
| Base de Q11 | 0,0037 |
| Base de Q12 | 0,0146 |

Si sólo se considerasen R34/R33, la fracción del colector de Q3 sería `R33/(R33+R34) ≈ 0,5222`; **esa no es la red pasiva completa dibujada en la placa**. R23 y R29 cambian el coeficiente condicionado de Q3 a 0,3388. El [puente de panel R30+R31](VCO1_CABLEADO_PANEL.md) añade otra rama 9B–21B y R6 carga la forma seleccionada; por tanto, 0,3388 **tampoco** es un coeficiente con el panel conectado. Estas cuentas señalan qué ramas incluir en el futuro solver, pero **no miden diafonía ni amplitud de salida**: el triángulo y el pulso se generan en la misma placa, sus tensiones no son fronteras independientes y Q12 puede conducir.

```powershell
python tools/vco1_saw_passive_reference.py
python -m unittest discover -s tests -q
```

Los tests verifican valores, conectividad y suma de conductancias, incluido R29 para evitar que vuelva a faltar. La topología de [Q2/Q1](VCO1_TRIANGULO.md), [Q11/Q12](VCO1_PULSO.md) y las ramas pasivas de panel ya está trazada; para predecir audio hay que resolver sus corrientes y las cargas acopladas de 9B/21B junto con Q3. Hasta entonces, la sierra del [modelo de eventos de C1](../tools/vco1_reference.py) es un nodo interno idealizado y no una señal de 9B.
