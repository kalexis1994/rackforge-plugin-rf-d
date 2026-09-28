# Bus de mezcla del panel: cinco rutas en ON

## Evidencia y dominio

El diagrama de interconexión **SVC-9, Fig. 9-17, PDF p. 19** (SVC-204D completo, PDF p. 75) muestra las cinco rutas hacia el bus común de audio. El bus termina en el **pin 4 de la placa 4**; **SVC-9, Fig. 9-11, PDF p. 13** (SVC-204D p. 69) muestra C27 como primer elemento en serie de esa entrada. La [transcripción](../evidence/mixer_panel_bus.json) usa sufijo `_PANEL` para resistores de panel, cuyos designadores se repiten en las placas. Esta referencia comprende los estados **ON**; el cableado de contactos OFF y la corriente de C27/filtro aún no se han resuelto.

| Fuente | Control previo | Resistor de serie al bus | Interruptor ON |
| --- | --- | ---: | --- |
| Oscilador 1 | R6, 25 kΩ | R45, 33 kΩ | SW9 |
| Oscilador 2 | R7, 25 kΩ | R47, 33 kΩ | SW11 |
| Oscilador 3 | R8, 25 kΩ | R49, 33 kΩ | SW13 |
| Ruido | R10, 25 kΩ | R48, 11 kΩ | SW12 |
| Entrada externa | salida del preamplificador | R46, 33 kΩ | SW10 |

El [modelo de dos puertos de R6/R45](VCO1_CABLEADO_PANEL.md) se usa también para R7/R47, R8/R49 y R10/R48, con sus respectivos valores. Cada `α` es la fracción **eléctrica** de resistencia bajo el cursor, no una posición física calibrada ni una ley de taper. Los voltajes de las fuentes se imponen; la impedancia de salida de osciladores, ruido y preamplificador queda fuera de esta cuenta.

## Ley de nodos y caso de referencia

Para cada rama activa, la [referencia ejecutable](../tools/mixer_panel_bus_reference.py) reduce el potenciómetro y su resistor de serie a una matriz pasiva de dos puertos. Si `I_i(V_i,V_bus)` es la corriente que sale del bus hacia esa rama e `I_placa4` es la corriente que sale del bus hacia la placa 4, la ecuación es `Σ I_i + I_placa4 = 0`. El cálculo admite cualquier subconjunto de interruptores en **ON**, los cuatro cursores eléctricos y una corriente de placa impuesta. No aporta la ley real `I_placa4(V_bus, frecuencia, estado)`.

Como control aritmético, si las **cinco** fuentes están en ON, los cuatro cursores están arriba (`α=1`), la entrada de placa 4 está abierta (`I_placa4=0`) y los cinco voltajes de origen se imponen, cada rama de oscilador o externa tiene **33 kΩ** y ruido **11 kΩ** al bus. Por KCL, `V_bus = (V_osc1 + V_osc2 + V_osc3 + V_ext + 3·V_ruido)/7`; la resistencia pasiva de Thévenin del bus bajo esas fronteras es `33 kΩ / 7 ≈ 4,714 kΩ`. El peso triple de ruido proviene sólo de R48 frente a las cuatro resistencias de 33 kΩ. **No** es una relación de volumen audible: los niveles de las fuentes, el taper, C27 y el filtro no están incluidos.

Al bajar un cursor, su rama sigue cargando el bus cuando el interruptor está en ON. Por ejemplo, con R6 en su extremo de masa (`α=0`), SW9 deja **R45 = 33 kΩ** desde el bus a masa aunque el oscilador 1 no aporte voltaje por esa ruta idealizada. Por ello los pesos generales ya no son simplemente `1/7` y `3/7`, y pueden sumar menos de uno por las derivaciones a masa de los potenciómetros.

```powershell
python tools/mixer_panel_bus_reference.py
python -m unittest discover -s tests -q
```

Los tests comprueban los cinco valores y rutas ON, el caso de resistencias de serie, las derivaciones al bajar un cursor y la ley de nodos con una corriente externa impuesta. Para predecir mezcla, saturación o audio falta resolver la entrada de la placa 4, la carga entre fuentes por el bus, la red OFF y los generadores de señal.
