# VCO 1: selector de forma, ancho de pulso y carga de panel

## Fuente y conexiones

El diagrama de interconexión **SVC-9, Fig. 9-17, PDF p. 19** (SVC-204D completo, PDF p. 75) une la placa 1 CA3046 con los controles. La placa se lee en **Fig. 9-3, PDF p. 5**. El [registro estructurado](../evidence/vco1_panel_pulse_width.json) conserva los designadores de panel con sufijo `_PANEL` para distinguirlos de los homónimos en la placa. La lectura de Fig. 9-17 resuelve una transcripción previa: la entrada de ancho es **22B**, no 28B. Fig. 9-17 la rotula `OSC1 PULSE WIDTH IN`, junto a **20B** (`OSC1 PULSE`) y **21B** (`OSC1 TRI`).

El común de la sección inferior de **SW6**, contacto **14**, lleva la señal seleccionada a **22B**. En el esquema, el contacto **10** va a masa; el **11** es la unión de R34 de panel (1,5 kΩ a masa) con R33 de panel (1 kΩ); el **12** es la unión de R33 con R32 de panel (7,5 kΩ a −10 V). El **7** va a −10 V y los **8/9** aparecen abiertos. El mapa entre posiciones mecánicas y leyendas del panel queda por corroborar: los números anteriores son sólo contactos eléctricos.

La sección superior de SW6 lleva **20B** a sus contactos **4/5/6** de selección rectangular. El común superior alimenta el extremo alto de **R6 de panel**, potenciómetro de nivel de oscilador 1 de **25 kΩ** cuyo extremo bajo va a masa. Su cursor sigue por **R45 de panel de 33 kΩ** hacia el interruptor de encendido del oscilador y la mezcla. La carga por el cursor depende de su posición y de la red de mezcla; se excluye de la cuenta siguiente. La ruta de sierra 9B y triángulo 21B también llega al selector, pero sus cargas según posición requieren una transcripción separada.

## Referencia pasiva condicionada

Con el riel fijado en **−10 V**, selector sin cargar 22B y resistencias nominales, la cadena serie R34+R33+R32 suma **10 kΩ**. Por división de tensión, contacto 11 = **−1,5 V**, contacto 12 = **−2,5 V**. Sus resistencias de Thévenin, anulando el riel ideal, son `R34 || (R33+R32) = 1,275 kΩ` y `(R34+R33) || R32 = 1,875 kΩ`. Contactos 10 y 7 son 0 V y −10 V ideales respectivamente bajo estas hipótesis; 8 y 9 no fijan voltaje. Al unir el contacto 14 con 22B, R1 de placa (43 kΩ) carga el divisor y Q11 añade una corriente de base variable. Por eso esos voltajes abiertos **no** son los voltajes efectivos durante la oscilación.

Si se selecciona pulso y se deja abierta la carga del cursor de R6, la pista de 25 kΩ añade una rama de 20B a masa. Con el colector de Q12 impuesto, `R_g = R22 || R6 = 4,7 kΩ || 25 kΩ ≈ 3,956 kΩ` y `V_20B = [R_g/(R13+R_g)]·V_Q12c ≈ 0,38954·V_Q12c`. La cuenta anterior de [20B sin carga externa](VCO1_PULSO.md) daba 0,43119. Son dos fronteras pasivas distintas, no amplitudes medidas. Q12, su emisor en 9B, la posición del cursor y la carga del mixer deben resolverse juntos para obtener la forma rectangular real.

```powershell
python tools/vco1_panel_pulse_reference.py
python -m unittest discover -s tests -q
```

La [referencia ejecutable](../tools/vco1_panel_pulse_reference.py) coteja la red de panel con el grafo de placa y comprueba las divisiones anteriores. No asigna porcentajes de ciclo ni reemplaza una medición del instrumento.
