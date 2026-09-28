# VCO 1: selector de forma, ancho de pulso y carga de panel

## Fuente y conexiones

El diagrama de interconexión **SVC-9, Fig. 9-17, PDF p. 19** (SVC-204D completo, PDF p. 75) une la placa 1 CA3046 con los controles. La placa se lee en **Fig. 9-3, PDF p. 5**. El [registro estructurado](../evidence/vco1_panel_pulse_width.json) conserva los designadores de panel con sufijo `_PANEL` para distinguirlos de los homónimos en la placa. La lectura de Fig. 9-17 resuelve una transcripción previa: la entrada de ancho es **22B**, no 28B. Fig. 9-17 la rotula `OSC1 PULSE WIDTH IN`, junto a **20B** (`OSC1 PULSE`) y **21B** (`OSC1 TRI`).

El común de la sección inferior de **SW6**, contacto **14**, lleva la señal seleccionada a **22B**. En el esquema, el contacto **10** va a masa; el **11** es la unión de R34 de panel (1,5 kΩ a masa) con R33 de panel (1 kΩ); el **12** es la unión de R33 con R32 de panel (7,5 kΩ a −10 V). El **7** va a −10 V y los **8/9** aparecen abiertos. El mapa entre posiciones mecánicas y leyendas del panel queda por corroborar: los números anteriores son sólo contactos eléctricos.

La sección superior de SW6 lleva **20B** a sus contactos **4/5/6** de selección rectangular. **9B** llega al contacto **3** y al extremo de **R30 de panel, 47 kΩ**. La unión de R30 con **R31 de panel, 10 kΩ** alimenta el contacto **2**; el otro extremo de R31 se une a **21B** y al contacto **1**. R30 y R31 forman, por tanto, un puente permanente de **57 kΩ** entre 9B y 21B, incluso al seleccionar pulso. El común superior alimenta el extremo alto de **R6 de panel**, potenciómetro de nivel de oscilador 1 de **25 kΩ** cuyo extremo bajo va a masa. Su cursor sigue por **R45 de panel de 33 kΩ** hacia el interruptor de encendido del oscilador y la mezcla. La carga por el cursor depende de su posición y de la red de mezcla; se excluye de las cuentas siguientes.

## Referencia pasiva condicionada

Con el riel fijado en **−10 V**, selector sin cargar 22B y resistencias nominales, la cadena serie R34+R33+R32 suma **10 kΩ**. Por división de tensión, contacto 11 = **−1,5 V**, contacto 12 = **−2,5 V**. Sus resistencias de Thévenin, anulando el riel ideal, son `R34 || (R33+R32) = 1,275 kΩ` y `(R34+R33) || R32 = 1,875 kΩ`. Contactos 10 y 7 son 0 V y −10 V ideales respectivamente bajo estas hipótesis; 8 y 9 no fijan voltaje. Al unir el contacto 14 con 22B, R1 de placa (43 kΩ) carga el divisor y Q11 añade una corriente de base variable. Por eso esos voltajes abiertos **no** son los voltajes efectivos durante la oscilación.

Si se selecciona pulso y se deja abierta la carga del cursor de R6, la pista de 25 kΩ añade una rama de 20B a masa. Con el colector de Q12 impuesto, `R_g = R22 || R6 = 4,7 kΩ || 25 kΩ ≈ 3,956 kΩ` y `V_20B = [R_g/(R13+R_g)]·V_Q12c ≈ 0,38954·V_Q12c`. La cuenta anterior de [20B sin carga externa](VCO1_PULSO.md) daba 0,43119. Son dos fronteras pasivas distintas, no amplitudes medidas. Q12, su emisor en 9B, la posición del cursor y la carga del mixer deben resolverse juntos para obtener la forma rectangular real.

```powershell
python tools/vco1_panel_pulse_reference.py
python -m unittest discover -s tests -q
```

La [referencia ejecutable](../tools/vco1_panel_pulse_reference.py) coteja la red de panel con el grafo de placa y comprueba las divisiones anteriores. No asigna porcentajes de ciclo ni reemplaza una medición del instrumento.

## Puente de sierra y triángulo

El puente externo R30+R31 de **57 kΩ** queda en paralelo con **R23 de placa, 8,2 kΩ**, que también une 9B y 21B. Con el cursor de R6 abierto y SW6 en pulso, la resistencia pasiva combinada entre ambos terminales es `57 kΩ || 8,2 kΩ ≈ 7,169 kΩ`. No es la resistencia de salida de ninguna de las dos formas: ambas reciben otras ramas activas y pasivas en la placa.

Para voltajes de 9B y 21B **impuestos**, la [referencia de dos puertos](../tools/vco1_panel_waveform_reference.py) calcula las corrientes hacia el panel. En contacto 3, R6 añade **25 kΩ de 9B a masa**; en contacto 1 los añade de **21B a masa**. En contactos 4/5/6 R6 carga 20B, y el puente de 57 kΩ persiste entre 9B y 21B. En contacto 2, R6 carga la toma intermedia: con `g30=1/R30`, `g31=1/R31`, `g6=1/R6` y `G=g30+g31+g6`, su voltaje es `V_toma=(g30·V_9B+g31·V_21B)/G`; las corrientes de puerto son `(V_9B−V_toma)/R30` y `(V_21B−V_toma)/R31`. Esta red no equivale a un simple puente de 57 kΩ cuando el contacto 2 está cerrado.

Estas cuentas usan la pista completa de R6 y excluyen su cursor y la carga de mezcla. Tampoco resuelven Q1/Q2, Q3, Q11/Q12 ni el punto real de 9B/21B; indican las ramas que deberá incluir el solver en cada contacto. El cursor se trata por separado a continuación.

```powershell
python tools/vco1_panel_waveform_reference.py
python -m unittest discover -s tests -q
```

## Cursor de R6, SW9 encendido y bus del mixer

La Fig. 9-17 (SVC-9, PDF p. 19) muestra el cursor de **R6 de panel, 25 kΩ** pasando por **R45 de panel, 33 kΩ** y **SW9 en ON** al [bus común de las cinco fuentes](MEZCLADOR_PANEL.md), que entra por el **pin 4 de la placa 4**. La Fig. 9-11 (SVC-9, PDF p. 13) muestra ese pin como entrada de audio hacia **C27** y la red del filtro. La impedancia del bus depende de frecuencia, estado y las demás fuentes; no se reemplaza por una resistencia inventada. La conexión de SW9 en OFF queda fuera de esta referencia.

Sea `α = R_inferior/R6`, una **fracción eléctrica** de 0 a 1: `R_superior=(1−α)·25 kΩ`, `R_inferior=α·25 kΩ`. No equivale necesariamente a la rotación física del potenciómetro. Con tensiones impuestas `V_forma` en el contacto seleccionado de SW6 y `V_mix` en el pin 4, la ley de nodos del cursor `V_c` es

`(V_c−V_forma)/R_superior + V_c/R_inferior + (V_c−V_mix)/R45 = 0`.

La [referencia ejecutable](../tools/vco1_panel_level_reference.py) resuelve esta ecuación como **dos puertos pasivos**, con los extremos `α=0` y `α=1` tratados como contactos ideales. Cuando se impone `V_mix=0` únicamente para explorar la carga, la resistencia vista por la forma seleccionada es `R_superior + (R_inferior || R45)`: **25 kΩ** en `α=0`, **≈21,57 kΩ** en `α=0,5` y **≈14,22 kΩ** en `α=1`. Con `α=0` y SW9 encendido, R45 todavía conecta el **bus de mezcla a masa por 33 kΩ**: bajar a cero el nivel del oscilador no elimina esa carga pasiva. El valor real requiere resolver simultáneamente el bus; la corriente a través de R45 puede depender de los otros osciladores, ruido y entrada externa. Estos números no son una curva de volumen ni amplitudes de audio.

```powershell
python tools/vco1_panel_level_reference.py
python -m unittest discover -s tests -q
```
