# Sensibilidad temporal condicionada de semiconductores BUS→J7

La [malla reproducible](../tools/headphone_transient_semiconductor_grid.py) ejecuta el [oráculo de 62 nodos](TRANSITORIO_AURICULARES_ACOPLADO.md) desde reposo DC durante **un ciclo** de senoide BUS ideal de `100 Hz`, `0,5 V` de amplitud y `96` pasos a `9,6 kHz` matemáticos. SW18 queda ON, R20/R21 inferiores `2500/2000 Ω`, HI/LO `10 kΩ/100 kΩ`, R14=0 Ω, R73=500 Ω y J7 lleva dos resistencias de `32 Ω`. La topología procede de **SVC-9 Fig. 9-8 PDF p. 10, Fig. 9-11 p. 13 y Fig. 9-17 p. 19**; las leyes BJT Ebers–Moll y diodo Shockley son las [declaradas en el punto DC](PUNTO_DC_AMP_AURICULARES.md). BUS y cargas son condiciones de laboratorio, no mediciones.

Nueve escenarios cruzan `β_F` de los tres BJT de placa 3 `{80,160,300}` con el **punto impuesto** de los dos diodos de placa 3 `V_F@100 mA={0,65;0,70;0,75} V`, a `298,15 K`; `I_S(BJT)=10⁻¹⁴ A`, `β_R=5` e idealidad `n=1,5` permanecen fijos. Otros dos casos cambian la temperatura común de ambas placas a `285` y `315 K` con β=160 y `V_F@100 mA=0,70 V`; el caso central de `298,15 K` ya pertenece a la malla de nueve. La función [rederiva `I_S` del diodo](../tools/output_diode_reference.py) desde ese punto impuesto a cada temperatura. Este método **no** es un modelo térmico identificado de una pieza vintage: mantiene el `I_S` BJT fijo, altera simultáneamente placa 4 y placa 3 y vuelve a condicionar el diodo. Los CR1/CR2 aquí son los de placa 3, distintos de los de placa 4.

La [evidencia](../evidence/headphone_transient_semiconductor_grid.json) contiene **11 escenarios y 1056 pasos**. El RMS J7 se calcula sobre los 96 valores de cada primer ciclo, por lo que incluye el transitorio de arranque y **no** es ganancia de régimen permanente ni potencia de auriculares. Valores ilustrativos:

| Cambio aislado dentro de la malla | RMS J7 del primer ciclo |
| --- | ---: |
| β placa 3 `80 / 160 / 300`, con diodo `0,70 V`, `298,15 K` | `6,05 / 6,48 / 6,70 mV` |
| Diodo placa 3 `0,65 / 0,70 / 0,75 V`, con β=160, `298,15 K` | `1,55 / 6,48 / 16,89 mV` |
| Temperatura común `285 / 298,15 / 315 K`, con β=160, diodo `0,70 V` | `18,68 / 6,48 / 0,984 mV` |

El residuo KCL máximo fue `9,9934×10⁻¹¹ A` y se requirieron hasta 4 iteraciones Newton. La [prueba](../tests/test_headphone_transient_semiconductor_grid.py) verifica los 11 casos, la convergencia y el orden creciente de salida con el punto de diodo dentro de cada β. En **este escenario condicionado**, la salida es mucho más sensible al punto supuesto de los diodos que al β directo supuesto de placa 3. La variación térmica no permite asignar causalidad a una placa o dispositivo. La prioridad experimental futura es conseguir curvas de TIS-92/TIS-93 y 1N458A representativos, datos de temperatura y contraste de audio con procedencia; ninguna de estas amplitudes calibra el RF-D frente a un Model D.
