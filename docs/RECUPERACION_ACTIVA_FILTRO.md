# Recuperación activa Q5–Q8 del filtro

## Procedencia y frontera

La Fig. 9-11 del **SVC-9, PDF p. 13** (SVC-204D p. 69) y la tabla 7-8, **SVC-9 pp. 30–31**, sustentan el [grafo transcrito](../evidence/filter_recovery_active_dc.json). La tabla identifica Q5/Q7 y Q6/Q8 como pares TIS97 apareados, pero no da parámetros de cada transistor. Las fuentes de alimentación nominales de esta referencia son ±10 V.

Los emisores superiores Q2 y Q3 del ladder llegan respectivamente por C5 y C1 (`0,22 µF`) a las bases de Q8 y Q6; R31 y R38 (`47 kΩ`) las ligan a masa. Q8 y Q6 alimentan como seguidores las bases de Q7 y Q5. R24 (`220 kΩ`) y R20 (`100 kΩ`) tiran esos nodos a −10 V; Q7/Q5 comparten R26 (`1 kΩ`) en la cola. Los colectores de **Q8 y Q7** se reúnen en `RECOVER_COLLECTOR`. Su carga llega a +10 V por **R3 `1 kΩ` → R7 `180 Ω` → R6 `47 Ω`**. El tap `R7/R3`, antes de C10, es la señal de [EMPHASIS](REGENERACION_FILTRO.md); el nodo `R6/R7` se desacopla a masa por C9 (`100 µF`). La referencia R3 se cotejó con la tabla 7-8: R23 pertenece a otro grupo de `100 Ω`.

En DC C1/C5/C9/C10 están abiertos. Por tanto, la [referencia DC de ocho nodos](../tools/filter_recovery_active_dc_reference.py) se resuelve independientemente del ladder. Incluye **ambas junturas** de cada BJT mediante Ebers–Moll y conserva las corrientes de base; no fija las bases artificialmente a 0 V. Para cada resistencia, `I=(V_a−V_b)/R`; por ejemplo:

```text
(10 − V_R6R7)/R6 = (V_R6R7 − V_R7R3)/R7
(V_R6R7 − V_R7R3)/R7 = (V_R7R3 − V_col)/R3
(V_R7R3 − V_col)/R3 = I_C,Q8 + I_C,Q7
I_E,Q7 + I_E,Q5 = (V_tail + 10)/R26
```

Las demás KCL incluyen R31/R38 y las corrientes de base de Q8/Q6 y Q7/Q5. El solver escala las ecuaciones en amperios, amortigua Newton y entrega residuo por nodo y matriz de conductancias en siemens. `I_S=10⁻¹⁴ A`, β directo `100`, β inverso `5` y `298,15 K` son **supuestos de escenario**, no mediciones del TIS97. Bajo ellos: `V_col≈2,961 V`, `V_R7R3≈8,698 V`, `V_tail≈−1,332 V`; el residuo máximo es `<4·10⁻¹⁴ A`. El resultado indica un punto matemático condicionado, no tensión de salida del instrumento.

## Pequeña señal cargada

La [referencia AC de 24 nodos](../tools/filter_recovery_active_small_signal_reference.py) pone en diagonal las matrices diferenciales del ladder de 16 nodos y de recuperación de ocho nodos. Estampa C5 y C1 entre los emisores superiores y las bases de recuperación, y C9 a masa. Resuelve `(G−jωC)v=b` para un bus de mezcla ideal de **1 V de perturbación**, acoplado por C27. El circuito de EMPHASIS a través de C10 queda abierto en esta etapa: el tap calculado tiene impedancia y ganancia de la recuperación activa, pero aún no se cierra el lazo hacia Q30.

| Escenario impuesto | `f` | `|V_R7R3/V_bus|` | `|ΔV_top/V_bus|` |
| --- | ---: | ---: | ---: |
| R61 = `200 Ω` | 100 Hz | 3,883 | 0,383 |
| R61 = `200 kΩ` | 100 Hz | 1,068 | 0,105 |

El alto valor del tap corresponde a **ganancia incremental** del circuito linealizado; no autoriza una señal física de 1 V allí ni predice margen antes de recorte. A 100 Hz, la frontera [pasiva](FRONTERA_RECUPERACION_FILTRO.md) daba `|ΔV_top/V_bus|≈0,406` y `0,112` en esos escenarios: la corriente de base activa modifica la carga del ladder. En 0 Hz C27 abre la entrada y todas las transferencias son cero. El residuo KCL complejo de las pruebas es `<10⁻¹¹ A/V`.

## Validez y próximos contrastes

La matriz AC es una **linealización local**; no incluye capacitancias de unión, ESR, fuga, variación de β, dispersión del par, dependencia térmica detallada ni limitación de excursión. Los dos valores R61 representan el [conflicto entre esquema y lista de piezas](ENTRADA_FILTRO.md), no dos variantes comprobadas. El siguiente cálculo debe conectar C10/R14/R73/R76 y la base activa de Q30 al tap, con `BOTTOM` dinámico, para barrer la ganancia de lazo. Luego hará falta una referencia temporal no lineal acoplada y la ruta VCA/salida. Sin unidad física ni captura comparable no se afirma fidelidad audible.

```powershell
python tools/filter_recovery_active_dc_reference.py
python tools/filter_recovery_active_small_signal_reference.py
python -m unittest discover -s tests -q
```
