# VCO 1 CA3046: límite ideal del convertidor exponencial

## Procedencia y alcance

Este cálculo usa la placa **CA3046 de Fig. 9-3**, no la μA726 ni la reedición. Sus conexiones están en **SVC-9, PDF p. 5** (también SVC-204D, PDF p. 61); los valores de C1, R50, R69 y R78 se cotejan con **SVC-9, tabla 7-5, PDF pp. 24–26**. Para la ley bipolar se usa [TI SLOA059B, PDF p. 6, ecuaciones (3)–(4)](https://www.ti.com/lit/an/sloa059b/sloa059b.pdf), registrado como `BJT-TI-2023` en [FUENTES.md](FUENTES.md). El [grafo de nodos](../evidence/vco1_ramp_graph.json) conserva las conexiones leídas. No hay instrumento físico ni un parámetro de transistor medido.

Este documento obtiene una **relación de corrientes/frecuencias entre dos estados** bajo supuestos ideales. No fija la afinación absoluta ni constituye un modelo audible de producción. El kit de estabilidad de §8.2 puede modificar R69 y la red de compensación; [REVISIONES.md](REVISIONES.md) lo mantiene como variante y no se fusiona con la placa nominal de Fig. 9-3.

## Lazo de referencia de IC3

La Fig. 9-3 conecta el colector de **Qb** (IC2 pin 1) a R50 de **39 kΩ** hacia masa y a la entrada **no inversora** de IC3 (pin 3). Su entrada inversora (pin 2) recibe la referencia marcada **−4 V**. IC3 (741) lleva su salida (pin 6) por **R69 = 15 kΩ** a la base de Qc (IC2 pin 12). R69 es un resistor fijo en la lista de repuestos, no un trimmer.

La base de Qc también conecta a **R78** hacia −10 V. El dibujo muestra una rama de **2 kΩ** y otra de **220 Ω en serie con 0,01 µF**. La tabla 7-5, PDF p. 26, cataloga R78/R106/R128 como una **red de resistencia y capacitancia**. El modelo de continua abre la rama capacitiva; su efecto en estabilidad y transitorios sigue pendiente.

La línea rotulada **−4 V** nace en la misma Fig. 9-3 de **R166 = 6,2 kΩ** hacia −10 V y **R174 = 3,9 kΩ** hacia masa, con **C14 = 0,12 µF** a masa. La [red compartida y sus cargas visibles](REFERENCIA_MENOS4V.md) conecta los tres osciladores. El divisor **sin carga** y con −10 V ideales daría `−10·3900/(6200+3900) = −3,861 V`, distinto de la etiqueta redondeada −4 V. Las corrientes de esas cargas aún no se conocen: ni el divisor sin carga ni la etiqueta bastan para declarar la tensión real del nodo. La alimentación de IC3 también requiere cotejo.

Si el lazo de IC3 está estable, no satura y su corriente de entrada es despreciable, entonces `V_Qb_colector ≈ V_referencia`. Sin otra carga en ese nodo, la corriente que baja desde masa por R50 es:

`I_Qb ≈ [0 V − V_referencia] / 39 000 Ω`.

Si se usa sólo la **etiqueta** −4 V, sale **102,56 µA**; si se usa el divisor **sin carga** a −3,861 V, sale **99,01 µA**. Son dos cálculos condicionados, **no un intervalo demostrado** para la placa real. Esta corriente de Qb no es la de Qa que descarga C1. La carga de la referencia, los offsets del 741 y la regulación pueden desplazar ambos supuestos.

## Ley ideal del par y razón de frecuencia

Qa y Qb tienen el mismo emisor físico (IC2 pin 3). La ecuación bipolar `V_BE = (kT/q) ln(I_C/I_S)` de TI, aplicada a ambos, da:

`I_Qa/I_Qb = (I_Sa/I_Sb) · exp[(V_Qa_base − V_Qb_base)/V_T]`, con `V_T = kT/q`.

`I_Sa/I_Sb` identifica el desajuste y no se ha medido. Para **dos estados de control a la misma temperatura**, si IC3 conserva `I_Qb` y el cociente de saturaciones no cambia, se cancela al dividir las dos ecuaciones:

`I_Qa,2/I_Qa,1 = exp[Δ(V_Qa_base − V_Qb_base)/V_T]`.

El [divisor R8](VCO1_CA3046.md) da, con C2 abierto en continua y sin corrientes de base, `Δ(V_Qb_base − V_Qa_base) = g(α)·ΔV_IC1`, donde `g(α) = (1000 + 100α)/1133` y `0 ≤ α ≤ 1` se mide desde el extremo de R8 unido a R19. El [sumador ideal de IC1](../tools/vco1_cv_reference.py) daría para +1 V en la línea KEYBOARD `ΔV_IC1 = −1000/51100 V`; por ello `Δ(V_Qa_base − V_Qb_base) = g(α)·1000/51100 V`.

Con `T = 298,15 K` (**25 °C hipotéticos en la unión**, `V_T ≈ 25,693 mV`), la razón ideal de `I_Qa` por +1 V va de **1,9587** (`α = 0`) a **2,0949** (`α = 1`); en `α = 0,5` es **2,0256**. Resolver esta ecuación aislada para razón 2 da `α ≈ 0,3106`. **No es una posición predicha de calibración:** la red de R42, el offset de IC1, el T.C. real de R20, las corrientes de base y el estado de IC3 cambian el resultado.

En el [submodelo ideal de C1](VCO1_CA3046.md), `f = I_Qa/(C1·4 V)` sólo si Qa es toda la corriente de extracción, los umbrales permanecen fijos y el reset consume tiempo despreciable. **Sólo bajo esas condiciones** la razón anterior de corrientes equivale a razón de frecuencias. No se conoce `I_Qa,1` sin el punto de polarización completo; multiplicar 102,56 µA de Qb por una razón *incremental* para declarar una frecuencia absoluta sería incorrecto.

[`tools/vco1_ideal_pair_reference.py`](../tools/vco1_ideal_pair_reference.py) calcula estas relaciones fuera del hilo de audio, con fuentes y supuestos visibles:

```powershell
python tools/vco1_ideal_pair_reference.py --keyboard-v 1 --r8-fraction 0.5
python -m unittest discover -s tests -v
```

## Vector de contraste y límites

| Condición ideal fija | Resultado | Qué podría refutar la extrapolación al circuito real |
| --- | ---: | --- |
| IC3 retiene Qb colector en la etiqueta −4 V, R50 = 39 kΩ | `I_Qb = 102,56 µA` **condicional** | Divisor sin carga da −3,861 V; cargas, offset, saturación o regulación cambian la referencia efectiva. |
| IC3 retiene Qb colector en el divisor sin carga | `I_Qb = 99,01 µA` **condicional** | No se conocen aún todas las cargas de la línea −4 V. |
| +1 V de teclado, R8 `α=0`, unión a 25 °C | Razón `I_Qa,2/I_Qa,1 = 1,9587` | R42, corrientes de base, temperatura y trimmer cambian la ganancia efectiva. |
| +1 V de teclado, R8 `α=0,5`, unión a 25 °C | Razón `2,0256` | Igual; no identifica posición real de R8. |
| +1 V de teclado, R8 `α=1`, unión a 25 °C | Razón `2,0949` | Igual; los extremos eléctricos del potenciómetro no son límites medidos de una unidad. |
| Paso `−1 V` con los mismos supuestos | Razón recíproca de `+1 V` | Histéresis, memoria RC o límites del lazo pueden romper la reciprocidad. |

**Estado RACE:** C1 parcial: la malla IC3→Qc→Qb y las conexiones visibles del divisor de referencia están trazadas, pero faltan las corrientes de carga, alimentación y reset completo. R11/R37 ya constan en el grafo, sin punto de ajuste conocido. C2 parcial: el voltio usado es la **línea de teclado en la placa**, no el panel ni MIDI. C3 hipótesis condicionada: ecuación bipolar y razón normalizada comprobables en el modelo ideal, sin validación de corriente absoluta, rango de lazo ni audio. El [explorador de carga DC](VCO1_CARGA_DC_IDEAL.md) ya incorpora IC1/R42, pero aún deja fuera la polarización completa de Qc/IC3 y los transitorios de R78. C4 abierto para dispersión y ley térmica de R20; C6 abierto sin instrumento.
