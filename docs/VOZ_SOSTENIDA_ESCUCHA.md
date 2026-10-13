# Adaptación del recorrido sostenido

Definición antes de renderizar las trazas. Aplicar los gates de
[la trayectoria](VOZ_SOSTENIDA_PROTOCOLO.md) y conservar sus voltios/relojes.

Dos WAV nativos,1/2 µs:576 frames/12 ms, desde el fragmento12.004 ms.
Sinc18 kHz y Blackman±32/Fs, extensión constante sólo para el filtro,
escala0.01 V/FS; cuadratura8/16≤.25 LSB, PCM≤1 LSB. Comparar ambos WAV a
los mismos centros:≤2 µV y≤7 LSB. No normalización, DC removal, fades o loop.
Un microscopio100× de la traza fina tiene57619 frames/1.200395833 s;
representa12.004 ms mapeados con frecuencia100×más lenta.

Si los dos últimos ciclos completos sostenidos pasan **todos** los gates
congelados, puede publicarse una repetición de inspección de1.5 s desde el
último ciclo1 µs. Fuente delimitada por los resets originales; interpolación
lineal incluyendo sus dos bordes. Integrales Fourier del helper histórico
`render_vco1_circuit.py::coefficients`, sin una onda ideal en reemplazo.
Harmónicos hasta.45·48 kHz, escala fija0.01 V/FS y fades10 ms del helper.
Omitir DC explícitamente sólo en esta adaptación. Contraste de coeficientes
1/2 µs, sin ajustar ganancia por caso. PCM completo y ningún clip permitido.

El archivo repetido conserva el rótulo de **ciclo observado repetido**;
1.5 s de salida no significan1.5 s de simulación, una envolvente continua
o periodicidad del estado229. Es una escucha de la forma en una ventana
con contorno casi constante según el gate finito. Si los gates no pasan,
guardar mediciones y no generar ese archivo; las trazas y WAV nativos
siguen teniendo su alcance propio.
