# Convergencia temporal con una misma señal BUS

La [malla de discretización](../evidence/headphone_transient_dt_convergence.json) impone **la misma** senoide de `100 Hz`, `0,5 V` de amplitud, durante dos ciclos (`20 ms`) en la frontera BUS. El [oráculo acoplado de 62 nodos](TRANSITORIO_AURICULARES_ACOPLADO.md) arranca siempre del mismo reposo DC y usa SW18 ON, R20 inferior `2500 Ω`, R21 inferior `2000 Ω`, cargas HI/LO `10 kΩ/100 kΩ` y dos ramas J7 de `32 Ω`. R14=0 Ω y R73=500 Ω. Los parámetros de semiconductores siguen siendo los supuestos de la [malla numérica anterior](ESTRES_TRANSITORIO_AURICULARES.md). La topología proviene de SVC-9 Figs. 9-8/9-11/9-17, PDF pp. 10/13/19; la senoide BUS **no** representa una grabación ni una forma de onda de oscilador medida.

La [herramienta](../tools/headphone_transient_dt_convergence_reference.py) resolvió `96`, `192` y `384` pasos a `4,8`, `9,6` y `19,2 kHz` de muestreo matemático, respectivamente: **672 pasos** en total, siempre los mismos `20 ms`. Compara tensiones en los mismos instantes físicos, tomando cada segundo punto de la solución más fina. El residuo KCL máximo fue `9,96×10⁻¹¹ A` y se necesitaron hasta 5 iteraciones Newton.

| Nodo | Máxima diferencia 4,8→9,6 kHz | Máxima diferencia 9,6→19,2 kHz | Cociente |
| --- | ---: | ---: | ---: |
| J7 | `1,357 mV` | `0,746 mV` | `1,82` |
| Cursor R21 | `6,773 mV` | `3,659 mV` | `1,85` |
| C2_RIGHT | `25,871 mV` | `13,965 mV` | `1,85` |

Las diferencias máximas y RMS disminuyen al partir el paso en dos. Los cocientes se acercan al factor 2 esperado para error de **primer orden** de Euler implícito en el régimen de refinamiento; no constituyen una solución analítica ni certifican la precisión absoluta a 48/96 kHz. La [prueba](../tests/test_headphone_transient_dt_convergence_reference.py) fija señales, alineación, KCL, iteraciones y descenso de error para este escenario. No se ha contrastado contra SPICE, una unidad Model D, ni audio vintage.

Ya se derivó el [bloque analítico de placa 3](JACOBIAN_ANALITICO_AURICULARES.md); faltan las cincuenta columnas anteriores y un solver acotado que se pueda medir frente a este oráculo, además de otras frecuencias, niveles, controles y condiciones térmicas. Convergencia de tiempo y fidelidad sonora siguen siendo afirmaciones distintas.
