# VCO 1: cargas de la salida de sierra 9B

## Evidencia y alcance

El esquema de la placa CA3046 para números de serie menores de 10175 es SVC-9, Fig. 9-3, PDF p. 5. Los valores de repuesto se cotejaron con la tabla 7-5, PDF pp. 24–25. Las conexiones están en el [grafo parcial](../evidence/vco1_ramp_graph.json). No existe una medición propia del conector 9B ni de su carga fuera de esta placa.

## Conexiones directas del nodo 9B

| Rama | Otro extremo visible | Valor o tipo | Naturaleza de la carga |
| --- | --- | --- | --- |
| R34 | Colector de Q3 (`SCHMITT_DRIVE`) | 4,3 kΩ | Lleva la sierra interna a 9B. |
| R33 | Masa (`GND`) | 4,7 kΩ | Derivación a masa; su extremo superior comparte la línea de masa de Q5/Q6. |
| R23 | Salida `TRIANGLE #1`, terminal 21B | 8,2 kΩ | Acopla la etapa triangular a 9B. |
| R14 | Colector de Q2 / nodo de base de Q1 | 150 kΩ | Carga dependiente del formador triangular. |
| R44 | Base de Q11 | 390 kΩ | Carga dependiente del formador de pulso. |
| R35 | Base de Q12 | 100 kΩ | Carga dependiente del formador de pulso. |
| Q12 | Emisor de 2N3392 | Transistor | Corriente no lineal; su colector pertenece al formador de pulso. |
| 9B | Cableado externo a la placa | Desconocido | Impedancia y estados todavía sin resolver. |

La barra de −10 V pasa **por encima** de la salida de sierra, sin unión en los cruces de R33/R34. Esa distinción evita convertir R33 en una resistencia hacia −10 V. La forma rectangular sale por otro terminal, 20B, y el triángulo por 21B; el vínculo pasivo de 21B a 9B es R23.

## Cuenta pasiva condicionada

Si se imponen las tensiones de los otros seis extremos, se fija `I_emisor_Q12 = 0` sólo para esta cuenta, y se deja abierto el cableado externo de 9B, la ley de nodos es:

`V_9B = (V_Q3/R34 + 0/R33 + V_21B/R23 + V_Q2c/R14 + V_Q11b/R44 + V_Q12b/R35) / G`,

con `G = 1/R34 + 1/R33 + 1/R23 + 1/R14 + 1/R44 + 1/R35`.

La [referencia ejecutable](../tools/vco1_saw_passive_reference.py) lee esas resistencias del grafo. Entrega `1/G ≈ 1,705 kΩ` y los coeficientes condicionados siguientes:

| Tensión impuesta | Coeficiente en `V_9B` |
| --- | ---: |
| Colector de Q3 | 0,3965 |
| Masa | 0,3628 |
| Triángulo 21B | 0,2079 |
| Colector de Q2 | 0,0114 |
| Base de Q11 | 0,0044 |
| Base de Q12 | 0,0171 |

Si sólo se considerasen R34/R33, la fracción del colector de Q3 sería `R33/(R33+R34) ≈ 0,5222`; **esa no es la red pasiva completa dibujada**. R23 por sí sola tiene una conductancia suficiente para cambiar el coeficiente condicionado de Q3 a 0,3965. Esto señala qué ramas deben estar presentes en el futuro solver, pero **no mide diafonía ni amplitud de salida**: el triángulo y el pulso se generan en la misma placa, sus tensiones no son fronteras independientes y Q12 puede conducir. Tampoco conocemos la carga externa del conector.

```powershell
python tools/vco1_saw_passive_reference.py
python -m unittest discover -s tests -q
```

Los tests verifican valores, conectividad y suma de conductancias. Para predecir audio falta resolver Q2/Q1, Q11/Q12 y el cableado de 9B junto con Q3. Hasta entonces, la sierra del [modelo de eventos de C1](../tools/vco1_reference.py) es un nodo interno idealizado y no una señal de 9B.
