# VCO 1 CA3046: carga de continua ideal y condicionada

## Procedencia y variables

La malla transcrita de **SVC-9, Fig. 9-3, PDF p. 5** (SVC-204D, PDF p. 61) une IC1, R11/R37, R20, R42, el emisor de Qc, R79, Qa/Qb y el lazo IC3/R50. El [grafo parcial](../evidence/vco1_ramp_graph.json) fija los terminales. La ley del par usa [TI SLOA059B, PDF p. 6, ecuaciones (3)–(4)](https://www.ti.com/lit/an/sloa059b/sloa059b.pdf). La [referencia compartida](REFERENCIA_MENOS4V.md) aporta sólo un voltaje **condicional** a una corriente externa impuesta.

Se introducen explícitamente: seis voltajes **en las líneas de control de la placa** (BEND, TUNE, KEYBOARD, MOD, EXT, OSC1 RNG), resistencia activa `r11 ∈ [0, 1 kΩ]`, fracción `α ∈ [0, 1]` de R8, temperatura de unión, cociente hipotético `I_Sa/I_Sb` y corriente externa neta de la referencia −4 V. No conocemos los valores físicos de esas entradas ni las posiciones de ajuste de una unidad.

## Ecuaciones de la malla reducida

En continua, con IC1 ideal, entrada no inversora sin corriente y conectada a −5 V por R10, el nodo sumador vale `V_S = −5 V`. Llamamos `E` al emisor de Qc, `O` a la salida de IC1 e `I_a`, `I_b` a las corrientes colectoras de Qa y Qb, positivas hacia el array. Con `r_t = R37 + r11` y `V_10 = −10 V`:

`0 = Σ_j (V_S − V_j)/R_j + (V_S − V_10)/r_t + (V_S − O)/R20 + (V_S − E)/R42`.

El emisor de Qc suministra la corriente total del par si se desprecia su corriente de base:

`I_a + I_b = (E − V_10)/R79 + (E − V_S)/R42`.

Si IC3 mantiene el colector de Qb en `V_ref`, sin otras cargas allí, `I_b = (0 − V_ref)/R50`. Con bases de Qa/Qb sin corriente y C2 abierto, `V_Ba = −5 V`, `V_Bb = −5 V + g(α)(O + 5 V)` y `g(α) = (R19 + αR8)/(R9 + R8 + R19)`. La ecuación bipolar ideal exige:

`ln[I_a/(I_b·(I_Sa/I_Sb))] = (V_Ba − V_Bb)/V_T`, `V_T = kT/q`.

El [explorador de carga](../tools/vco1_ideal_dc_loadline.py) elimina `E` y `O` por las dos leyes de nodos, barre `I_a` en un intervalo numérico declarado y devuelve todos los cruces de la ecuación logarítmica detectados en ese intervalo. **No** selecciona una raíz por afinación deseada. El intervalo de búsqueda (por defecto 0,001–1000 µA) es un parámetro numérico, no el rango físico demostrado del VCO.

## Vector sintético de comprobación

Como regresión matemática, fijamos las seis líneas en **−2,1 V artificiales**, `r11 = 500 Ω`, `α = 0,5`, `I_Sa/I_Sb = 1`, unión a **25 °C hipotéticos** y `I_ext = 0` en la referencia. La única raíz encontrada en el intervalo por defecto da `I_a = 17,067 µA`, `I_b = 99,010 µA`, `O = −4,9513 V` y `E = −9,8536 V`. Cumple las dos leyes de nodos y el cociente exponencial dentro del error numérico. Esos seis voltajes iguales se eligieron sólo para hacer reproducible la prueba; **no representan** una posición de panel, nota, calibración ni valor nominal publicado de corriente de Qa.

En el mismo vector artificial, mover `r11` de 0 a 1000 Ω da raíces de 9,153 a 30,353 µA. Esto demuestra que la realimentación R42 y el trim entran en la ecuación acoplada. No demuestra el recorrido ni la escala de la perilla real. El resultado anterior de [razón incremental ideal](VCO1_CONVERTIDOR_IDEAL.md) sigue siendo una aproximación que omite la variación de E por R42.

```powershell
python tools/vco1_ideal_dc_loadline.py --bend-v -2.1 --tune-v -2.1 --keyboard-v -2.1 --mod-v -2.1 --ext-v -2.1 --osc1-range-v -2.1 --r11-active-ohm 500 --r8-fraction 0.5 --external-reference-current-ua 0 --mismatch-is-ratio 1 --temperature-c 25
```

## Gate y límites

La raíz sólo satisface un **subconjunto ideal de la polarización**. Falta comprobar la tensión de emisor común Qa/Qb, voltaje `V_BE` y `V_CE` de Qc, la salida exigida a IC3 a través de R69/R78, corrientes de base, límites de salida y offsets de ambos 741, regulación de −5/−10 V, cargas reales de −4 V y tolerancias. IC1 tiene alimentación **0/−10 V** en Fig. 9-3; una salida calculada entre esos rieles es condición necesaria, no comprobación de excursión válida. También faltan transitorios de C2/R78/C14 y reset de Q10. Por esas razones, el explorador **no** entrega frecuencia ni forma de onda, y C3 de RACE continúa como hipótesis condicionada.
