# VCO 1: formador de pulso Q11/Q12 y salida 20B

## Evidencia y alcance

Se transcribe la placa osciladora CA3046 para números de serie menores de 10175: SVC-9, Fig. 9-3, PDF p. 5. Los valores y tipos de reemplazo se cotejaron con la tabla 7-5, PDF pp. 24–25. La descripción funcional de ancho de pulso procede de SVC-204D §2.16, PDF pp. 14–15. El [grafo parcial](../evidence/vco1_ramp_graph.json) contiene los nodos y componentes; el [cableado de panel](VCO1_CABLEADO_PANEL.md) procede de Fig. 9-17, PDF p. 19. No hay medición física del circuito.

## Camino del control, realimentación y salida

| Componente | Conexión comprobada | Valor/tipo |
| --- | --- | --- |
| R1 | Control de ancho 22B → base de Q11 | 43 kΩ |
| R40 | Colector de Q3 (`SCHMITT_DRIVE`) → base de Q11 | 43 kΩ |
| R44 | Sierra 9B → base de Q11 | 390 kΩ |
| R2 | Colector de Q12 → base de Q11 | 910 kΩ |
| Q11 | Emisor a masa, base en el nodo anterior, colector hacia R39 | PNP 2N4058 |
| R39 | Colector de Q11 → base de Q12 | 100 kΩ |
| R35 | Base de Q12 → sierra 9B | 100 kΩ |
| Q12 | Base en R39/R35, colector en R13/R2, emisor directamente en 9B | NPN 2N3392 |
| R13 | Colector de Q12 → rectangular 20B | 6,2 kΩ |
| R22 | Masa → rectangular 20B | 4,7 kΩ |

La línea de **22B** entra a R1 y cruza sin punto de unión la línea de masa que alimenta el emisor de Q11 y R22. El colector de Q12 se devuelve por R2 a la base de Q11, formando una realimentación dependiente del estado. El emisor de Q12 está conectado **directamente** a 9B, de modo que la carga del formador de pulso puede variar durante el ciclo. La salida rectangular de la placa está en **20B**, entre R22 y R13; el esquema la anota con aproximadamente **3,5 V**. Esta cifra anotada no es una amplitud calculada para la carga externa.

## Dos relaciones resistivas condicionadas

Si se imponen las tensiones de 22B, colector de Q3, 9B y colector de Q12, y se desprecia la corriente de base de Q11, la ley de nodos en su base es:

`(V_B−V_22B)/R1 + (V_B−V_Q3)/R40 + (V_B−V_9B)/R44 + (V_B−V_Q12c)/R2 = 0`.

La [referencia ejecutable](../tools/vco1_pulse_passive_reference.py) da pesos de **0,4635** para `V_22B` y **0,4635** para `V_Q3`, **0,0511** para `V_9B` y **0,0219** para `V_Q12c`. Los dos primeros coinciden porque R1 y R40 son iguales. El valor bajo del peso pasivo de R2 no permite omitirlo en un Schmitt: la conmutación de Q11/Q12 y la corriente de base no forman parte de esta cuenta.

Con el colector de Q12 **impuesto**, 20B sin carga externa y R22/R13 como únicas ramas de ese nodo, `V_20B = [R22/(R13+R22)]·V_Q12c ≈ 0,4312·V_Q12c`. La resistencia de Thévenin pasiva es `R22 || R13 ≈ 2,67 kΩ`. Es una atenuación **condicionada**: el voltaje real del colector depende de Q12, de su emisor móvil en 9B y de la realimentación por R2.

Estas ecuaciones no entregan un porcentaje de ciclo, un umbral ni el nivel cargado de 20B. El manual describe un rango nominal cercano a **50 %–15 %** para el pulso variable. Ya se conoce la [red externa de 22B y la carga seleccionada de 20B](VCO1_CABLEADO_PANEL.md), pero faltan la carga recíproca del control, las curvas de los dos transistores y la solución simultánea de 9B para derivar el ancho. Un comparador ideal con una sierra ideal sería otra hipótesis, no la transferencia extraída de esta placa.

```powershell
python tools/vco1_pulse_passive_reference.py
python -m unittest discover -s tests -q
```

Los tests aseguran conectividad y leyes de nodos; no validan audio. El siguiente corte eléctrico debe resolver Q11/Q12 conjuntamente con Q3, Q2/Q1 y las cargas de 9B/20B/22B, manteniendo la variante documental y las incertidumbres de C4 y Q5/Q6.
