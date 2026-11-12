# Entrada externa y sobrecarga en la voz de desarrollo

El bus **External Input** recibe audio mono desde la entrada de un
Rack. **External On** conecta la rama al mezclador y **External
Level** controla la señal que entra al preamplificador. El preset
**External Filter** deja sólo la entrada externa en el mezclador.
Una nota MIDI abre el VCA. La salida sigue duplicada a estéreo.

## Modelo nominal

OP-EARLY p. 9 describe la entrada y el uso de la luz de overload.
En SVC-9 Fig. 9-17 p. 19, J6 alimenta R9 de 1 MΩ y el cursor va a
la placa 4. En Fig. 9-11 p. 13, pin 11 entra por R78 y C23 al
preamplificador Q27/Q32/Q33. C20 conecta su salida al pin 17,
antes de la rama R46 de 33 kΩ y SW10 del [mezclador](MEZCLADOR_PANEL.md).
La luz toma señal del preamplificador antes de ese interruptor.
[Registro de fuentes](FUENTES.md).

El nivel digital de entrada se limita a ±1 y equivale a ±100 mV
en el jack virtual. Los valores no finitos se tratan como silencio.
Se interpola linealmente de 48 a 96 kHz. El potenciómetro virtual
aplica un nivel lineal de 0 a 100 %. Su ganancia y conexión usan
el mismo suavizado de hasta 64 frames que los otros canales.

Los dos acoplamientos RC son C23 de 0,1 µF con R78 + R66 de
101 kΩ, y C20 de 1 µF con una carga nominal de 33 kΩ.
Las constantes resultan 10,1 ms y 33 ms. La ganancia de banda
media parte de `1 + R61/R62 = 201` con la realimentación ideal.
Una tangente hiperbólica limita la excursión nominal a ±4 V.
R46 aporta una unidad de conductancia al promedio de mezcla,
igual que cada oscilador conectado. La escala relativa de la
rama usa ±1,7 V como referencia de un oscilador, según la
amplitud triangular dibujada en SVC-9 Fig. 9-3 p. 5.
La entrada externa puede llevar el ladder más allá de la
excursión nominal de los osciladores y saturar sus pares
diferenciales.

**Overload** indica cuándo la demanda de ganancia alcanza 4 V
antes de la limitación. El detector conserva un pico que decae
con el producto nominal R56 de 100 kΩ por C14 de 0,47 µF.
La indicación se lee como parámetro de sólo lectura y se
actualiza mientras el panel está visible. El taper, los límites
de excursión, la escala del jack virtual y la carga efectiva de
C20 son aproximaciones funcionales. La curva de los transistores
y el umbral de la lámpara quedan para contraste con el circuito.

## Verificación sin empaquetar

`python -B tools/check_rf_d_playable_voice.py` carga el WASM
desde un directorio temporal. La prueba mide ganancia a nivel
bajo, compresión y armónicos a nivel alto, caída del indicador
y carga de la rama conectada a nivel cero. También verifica
que una señal externa con el interruptor apagado conserve
bit a bit el audio del oscilador, y que la ruta externa sola
quede en silencio sin gate MIDI.

Con una senoide de 440 Hz y External Level al 60 %, el tercer
armónico pasó de 0,87 % del fundamental a 23,59 % al aumentar
la entrada de 0,025 a 0,95 de escala. La señal saturada tuvo
un pico digital de 0,889 y la carga a nivel cero dejó la
sierra en 0,5001 de su valor previo. El primer ensayo aplicó
un límite de pico al fundamental, que midió 1,009. El ensayo
corregido aplica ese límite a las muestras y conserva la
comprobación de compresión del fundamental.

En RackForge, el banco entrega una captura de dos canales con
un canal distractor. El slot toma el canal físico 2 y reproduce
bit a bit el WASM directo a 128, 480 y 4096 frames. Cuando el
canal 2 falta, el slot reproduce silencio. La captura es
sintética. El máximo observado a 128 frames fue 0,185 ms.
Quedan pendientes la escucha, la comprobación con dispositivo
físico y la realimentación de salida.
[Resultados](../evidence/rf_d_voice_development02.json).
