# Glide y pitch bend en la voz de desarrollo

**Glide** activa el deslizamiento. **Glide Time** ajusta su duración
entre 1 y 10.000 ms. La primera nota tras preparar la voz fija el
CV. Las siguientes notas, con prioridad de la tecla más baja,
recorren el intervalo desde el valor retenido. Al soltar la última
tecla se congela el CV hasta la siguiente nota. El gate de los
contornos conserva sus reglas de legato y redisparo.

El [manual de operación](FUENTES.md) OP-EARLY p. 8 describe la
prioridad, el switch de Glide y la rueda de media octava. La retención
del teclado viene de SVC-204D p. 16, con esquema en p. 65. La
reducción aplica una carga exponencial de primer orden al CV, a
96 kHz. La constante de tiempo se elige para que quede el 1 % del
intervalo al cumplirse el tiempo nominal del panel. La ley del
potenciómetro y las fugas del circuito quedan para calibración.

El CV compartido alimenta los osciladores que siguen el teclado y
el tracking del filtro. El pitch bend MIDI de 14 bits se centra
en 8192 y recorre ±6 semitonos en los extremos. El esquema CA3046
SVC-9 p. 5 separa la suma BEND del CV de teclado y del amplificador
de OSC3 libre. El bend mueve OSC1, OSC2 y OSC3 con OSC3 Control
activo. CC121 centra el bend y devuelve CC1 a cero. El recorrido
completo del bend se suaviza en hasta 64 frames a 48 kHz.

`python -B tools/check_rf_d_playable_voice.py --keyboard` contrasta el glide con
la curva nominal, la retención durante el release, los extremos
del bend, la independencia de OSC3 libre y del filtro ante bend,
y el tracking durante el legato. El host carga el componente WASM
desde un directorio temporal. [Resultados](../evidence/rf_d_voice_development01.json).

La prueba midió 274,12 Hz, 235,84 Hz y 221,54 Hz en tres puntos
del glide de 440 a 220 Hz con tiempo de 500 ms. La frecuencia
quedó en 353,39 Hz al soltar una nota durante el recorrido.
El bend desde 220 Hz midió 311,13 Hz arriba y 155,56 Hz abajo.
El primer intento de medir el release envió 127 a un control
con rango 0–1 y quedó en la descarga corta. La repetición usó
el valor 1 para activar el release por decay.
