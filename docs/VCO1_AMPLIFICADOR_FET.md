# VCO 1: puente FET, transistor Q3 y realimentación de sierra

## Fuente y dominio

Se transcribe la placa osciladora CA3046 para números de serie menores de 10175: SVC-9, Fig. 9-3, PDF p. 5. Los designadores y valores se cotejan con la tabla 7-5, PDF pp. 24–25. La descripción funcional de C1 y el colector de Q3 procede de SVC-204D, §2.16, PDF pp. 14–15. El [grafo parcial](../evidence/vco1_ramp_graph.json) conserva las conexiones. No hay placa física ni capturas propias.

La figura dibuja los dos FET de **Q7 E402** con fuentes unidas. Este documento identifica terminales del **símbolo**, sin asignar pines del encapsulado ni parámetros eléctricos de una pieza instalada. Q8/Q9 están marcados 2N4058 PNP y Q3/Q4, 2N3392 NPN; los cuatro coinciden con la lista de repuestos. Esas referencias identifican familias, no curvas medidas.

## Tramo trazado

| Nodo del grafo | Uniones visibles | Papel eléctrico |
| --- | --- | --- |
| `RAMP_C1` | C1, Qa, Q10 y puerta izquierda de Q7 | Señal temporizadora que baja de 0 a −4 V según §2.16. |
| `FET_C4_LEFT` | Puerta derecha de Q7, R4 a +10 V, R25 a −10 V, R24/C4 hacia el colector de Q3 | Entrada de realimentación del par FET. |
| `FET_LEFT_DRAIN` / `FET_RIGHT_DRAIN` | Drenajes de Q7, R46/R5 a +10 V, bases de Q9/Q8 | Cargas separadas del par. |
| `FET_COMMON_SOURCE` | Fuentes unidas de Q7 y R47 de 100 Ω al colector de Q4 | Corriente común; depende de Q4. |
| `Q4_BASE` / `Q4_EMITTER` | R49 de 1 kΩ desde la referencia rotulada −4 V; R48 de 12 kΩ a −10 V | Polarización de Q4, no una corriente ya conocida. |
| `FET_C3_LEFT` | Emisores de Q8/Q9, R45 de 1,2 kΩ a +10 V y C3 de 100 pF | Acoplamiento capacitivo hacia el colector de Q3. |
| `Q3_BASE` | Colector de Q8 y R36 de 2,7 kΩ a −10 V | Excitación del transistor de salida interno. |
| `SCHMITT_DRIVE` | Colector de Q3, R15 a +10 V, R24/C4, C3, R30 hacia Q5 y R34 | Sierra **interna** que alimenta el disparo. |
| `SAW_OUTPUT_9B` | R34 de 4,3 kΩ desde el colector de Q3 y conector 9B | Salida de sierra de la placa; tiene otras conexiones sin transcribir. |

Q9 tiene el colector en la barra de **−10 V**, que cruza sin unión la línea inferior rotulada **−4 V** que alimenta R49. Q3 tiene el emisor en −10 V. En la parte inferior también hay dos líneas distintas: la barra de −10 V y la que termina en **9B**. Así, R34 lleva señal al conector, mientras R36 y R25 vuelven al riel negativo. Confundir cualquiera de estos cruces alteraría la carga y la realimentación.

## Única transferencia numérica cerrada en este corte

Con `V_Q3` **impuesta**, rieles en +10/−10 V, corriente de puerta de Q7 despreciable y C4 abierto en continua, la tensión de la puerta derecha `V_G` satisface:

`(V_G−10)/R4 + (V_G+10)/R25 + (V_G−V_Q3)/R24 = 0`,

con `R4 = 33,2 kΩ`, `R25 = 15 kΩ` y `R24 = 10,7 kΩ`. Para los dos extremos **nominales** que §2.16 asigna al colector de Q3, la [referencia ejecutable](../tools/vco1_fet_gate_reference.py) da:

| `V_Q3` impuesto | Puerta derecha calculada |
| ---: | ---: |
| +4 V | +0,044 V |
| −4 V | −3,886 V |

La puerta derecha se mueve casi por el mismo intervalo nominal de 0 a −4 V que describe la rampa en la otra puerta. Esa coincidencia es una **deducción de la red resistiva con extremos impuestos**, no una medición, ni prueba que el par produzca la ganancia, linealidad o fase necesarias. La derivada condicionada `dV_G/dV_Q3 = (1/R24)/(1/R4+1/R25+1/R24) ≈ 0,4913 V/V` no incluye la respuesta de Q7/Q8/Q3. Si cambian rieles, valores, corriente de puerta o el extremo real de Q3, cambian ambas cifras.

El conflicto de **C4 = 10 pF en el esquema frente a 100 pF en la tabla 7-5** no afecta esta cuenta de continua; sí afecta un eventual transitorio. C3, Q7, Q8, Q9, Q3 y la carga de 9B impiden deducir aún tiempo de reset, oscilación de alta frecuencia, sierra cargada o audio. La descripción funcional del manual tampoco proporciona una respuesta transitoria medida que cierre esos grados de libertad.

```powershell
python tools/vco1_fet_gate_reference.py --q3-collector-v 4
python tools/vco1_fet_gate_reference.py --q3-collector-v -4
python -m unittest discover -s tests -q
```

Los tests comprueban la ley de nodos y que el grafo conserve los cruces y valores transcritos; **no** validan fidelidad de una unidad vintage. El siguiente paso es obtener curvas primarias utilizables para E402/2N4058/2N3392, resolver dos perfiles de C4 y completar la carga del conector 9B antes de simular el lazo.
