# Entradas de control del Model D en RF-D

La sección **Connections** del [panel de RF-D](PANEL_RF_D.md) ofrece
los jacks traseros como parámetros de RackForge. Se pueden ajustar desde el panel, automatizar y enlazar
a controles del host. Los valores continuos se expresan en voltios.
**S‑Trigger** encendido representa el contacto cerrado a masa.

| Control | Intervalo y reposo | Destino |
| --- | --- | --- |
| Oscillator CV | −2 a +2 V, reposo 0 V | Afinación de OSC1 y OSC2, más OSC3 con OSC3 Control activo |
| Filter CV | −2 a +2 V, reposo 0 V | Control de corte, con los switches de tracking y modulación en cualquier posición |
| Loudness CV | 0 a 5 V, reposo 5 V | Ganancia del segundo VCA, entre los contornos y la salida de referencia A‑440 |
| S‑Trigger | Contacto abierto o cerrado, reposo abierto | Gatillo común de los contornos de filtro y volumen |

Los rangos bipolares del panel y el suavizado de hasta 64 frames
por recorrido completo a 48 kHz son decisiones de RF-D. La voz
avanza los voltajes a 96 kHz y el contacto usa el offset exacto
de la automatización. Los cuatro controles se agregan al final
del estado para mantener los presets anteriores.

## Afinación y filtro

J1 llega al pin 8A de la placa CA3046. La Fig. 9-3 de SVC-9
PDF p. 5 muestra las ramas EXT y KEYBOARD con 51,1 kΩ por
oscilador. En OSC3 la llave SW2 selecciona el amplificador
de control. Se conserva la acción del jack en la ruta que sigue
al teclado. La reducción aplica 1 octava/V según la igualdad
de resistencias y la escala nominal del CV de teclado. El CV
se suma al pitch bend después del glide y por separado del
tracking del filtro. [Fuentes](FUENTES.md).

J2 entra por R51 de 100 kΩ al nodo de corte, con su contacto
normalizado a masa en SVC-9 Fig. 9-17 PDF p. 19. Las ramas de
tracking R53/R54 en paralelo también suman 100 kΩ, de modo
que RF-D aplica 1 octava/V en el mismo dominio de control
del ladder. El corte conserva los límites de corriente de la
reducción. La equivalencia supone fuentes de impedancia
despreciable y calibración nominal. [Red de Q26](BASE_Q26_CONTROL_FILTRO.md).

## Segundo VCA y Loudness CV

J3 conecta al pin 10 de placa 4. Su contacto normal conecta
R56 de panel de 33 kΩ a +10 V. R51 de placa de 33 kΩ va a
masa, con un punto medio ideal de 5 V antes de la corriente
de base. El recorrido sigue el [segundo VCA](NUCLEO_ACTIVO_VCA2_DC.md)
de SVC-9 Fig. 9-11 PDF p. 13 y SVC-204D §2.9 PDF p. 12.

En pequeña señal, la ganancia diferencial del par Q14/Q13
escala con la corriente de cola de Q21. El banco resuelve la
corriente de colector en 101 puntos de 0 a 5 V con bases de
Q14/Q13 a 8 V, cursor de balance de 9 V y R12 de 50 Ω por lado.
Usa `I_S=10⁻¹⁴ A`, `β_F=100`, `β_R=5` y `T=298,15 K`.
Se resta la fuga calculada a 0 V y se normaliza respecto de
5 V para obtener silencio y unidad en los extremos del panel.
El DSP interpola la tabla y multiplica el audio antes de
sumar el afinador. Quedan abiertos el efecto de la impedancia
de la fuente sobre la polarización, la curva a señal grande
y la dispersión de Q21.

## S‑Trigger

SO-1 llega a R49 y al colector Q20 de placa 2. El contacto
cerrado mantiene activos ambos contornos, como el tapón de
cortocircuito descrito por OP-EARLY PDF p. 13. La reducción
usa el estado combinado de tecla y contacto. Una tecla
nueva cambia el CV según la prioridad monofónica aunque
el contacto mantenga el contorno. Al soltar todas las teclas
se retiene el CV. Si nunca se tocó una tecla desde la preparación,
el drone parte de A4 en RF-D. [Circuito del gatillo](CONTORNO_VOLUMEN_CIRCUITO.md).

Un traspaso entre el teclado y el contacto al mismo frame
mantiene el gate. Se toma primero el cierre entrante y
después la apertura saliente. El cierre del contacto sigue
vigente si llega All Notes Off. La simulación detallada de
CR10/C7 y del biestable sigue disponible como referencia
eléctrica aparte de la voz tocable.

## Verificación

`python -B tools/check_rf_d_playable_voice.py` mide tres
osciladores con −1/0/+1 V, el desplazamiento del filtro por
CV frente al tracking y la transferencia del segundo VCA
en voltajes reservados. Comprueba el contacto sin MIDI,
los traspasos de gate por bits, la migración de estados
y la automatización a 127, 128, 480 y 4096 frames.
RackForge restaura los cuatro controles activos desde estado
y reproduce por bits el audio de WASM a 128, 480 y 4096 frames.
A 128 frames, los dos pases offline alcanzaron picos de
0,270 y 0,239 ms frente a un margen de 1,333 ms.
La tabla del VCA tuvo un error de ganancia máximo de
0,000364 en los 100 puntos de reserva.
[Resultados](../evidence/rf_d_voice_development06.json).

`--monitor` conserva el perfil previo de Phones y A‑440.
La prueba usa captura sintética y archivos temporales.
Queda pendiente la escucha en dispositivo.
