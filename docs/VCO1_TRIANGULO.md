# VCO 1: formador de triángulo Q2/Q1

## Fuente y dominio

Este corte corresponde a la placa CA3046 para números de serie menores de 10175, SVC-9 Fig. 9-3, PDF p. 5. Los valores R3/R14/R23/R28/R29 y los tipos Q1/Q2 se cotejan con la tabla 7-5, PDF pp. 24–25. La descripción funcional del triángulo está en SVC-204D §2.16, PDF pp. 14–15. El [grafo parcial](../evidence/vco1_ramp_graph.json) usa nombres de nodos propios. No hay una unidad física medida.

## Camino trazado

| Elemento | Conexión de la figura | Valor o tipo |
| --- | --- | --- |
| Q2 | Base al colector de Q3 (`SCHMITT_DRIVE`); colector a `Q2_COLLECTOR`; emisor a `Q2_EMITTER` | NPN 2N3392 |
| R3 | +10 V a `Q2_COLLECTOR` | 10,7 kΩ, 1 % |
| R14 | `Q2_COLLECTOR` a sierra 9B | 150 kΩ |
| R29 | `Q2_EMITTER` a sierra 9B | 10 kΩ, 1 % |
| Q1 | Base a `Q2_COLLECTOR`; colector a +10 V; emisor a `Q1_EMITTER` | NPN 2N3392 |
| R28 | `Q1_EMITTER` a triángulo 21B | 750 Ω |
| R23 | Triángulo 21B a sierra 9B | 8,2 kΩ |

Q2 lee la **sierra interna** de Q3, no el conector 9B. Q1 toma el colector de Q2 y alimenta 21B a través de R28. R14, R29 y R23 cierran tres caminos distintos entre la etapa triangular y 9B. Al seguir el emisor de Q2 apareció **R29**, que faltaba en el [primer inventario pasivo de 9B](VCO1_SALIDA_SIERRA.md); los coeficientes de ese inventario se recalcularon. La salida 21B figura en el esquema con una excursión anotada aproximadamente de +1,7 a −1,7 V; esta transcripción no la deduce de modelos BJT.

## Límite pasivo en 21B

Con `V_Q1e` y `V_9B` **impuestas**, carga externa de 21B abierta y corriente de otros caminos al nodo despreciada, la ley de nodos da:

`(V_21B−V_Q1e)/R28 + (V_21B−V_9B)/R23 = 0`.

La [referencia ejecutable](../tools/vco1_triangle_passive_reference.py) devuelve `V_21B = 0,91620·V_Q1e + 0,08380·V_9B` y resistencia de Thévenin pasiva `R28 || R23 ≈ 687 Ω` con las dos fronteras fijadas. Es un **mapa resistivo de la placa aislada**, no el nivel real del conector: Q1/Q2 son no lineales, 9B depende de estas mismas ramas y el [panel añade R30/R31 y R6 según SW6](VCO1_CABLEADO_PANEL.md). La carga del cursor de R6 y del mixer sigue sin resolverse. La cifra anotada de ±1,7 V no se usa para elegir corrientes o `V_BE`.

```powershell
python tools/vco1_triangle_passive_reference.py
python -m unittest discover -s tests -q
```

Los tests comprueban la conectividad y la ley de nodos, no una forma triangular ni parecido audible. El próximo paso eléctrico es resolver Q2/Q1 junto con las cargas de 9B/21B y las curvas del 2N3392 antes de calcular amplitud, distorsión o transición entre ramas.
