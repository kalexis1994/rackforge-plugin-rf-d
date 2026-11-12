# Ruido y modulación de RF-D Voice 0.7.0

Importá `artifacts/rf-d-voice-0.7.0.rfplugin` y elegí **Wheel Motion**
en PLAY. Tocá una nota y subí la rueda de modulación MIDI. El preset
usa OSC3 libre en LO, una mezcla de 88 % OSC3 y 12 % ruido, y los dos
destinos de modulación. La voz sigue funcionando a 48 kHz con
MIDI 36–72.

## Panel

- **Noise Color** selecciona blanco o rosa para el mezclador. **Noise
  Level** ajusta el volumen. **Noise On** conecta la rama de ruido.
- **OSC 3 → Noise** recorre desde OSC3 al 0 % hasta ruido al 100 %.
  La señal de OSC3 se toma antes de su interruptor de audio.
- **Oscillator Modulation** y **Filter Modulation** habilitan la
  afinación y el cutoff por separado. **CC1** controla la intensidad.
  **CC121** devuelve la rueda a cero. El valor de la rueda se
  reinicia a cero al preparar la voz y pertenece a la interpretación.

## Circuito y modelo nominal

OP-EARLY, PDF pp. 7, 9 y 12, describe la mezcla, su rueda y los dos
destinos. En SVC-9 Fig. 9-8 y Fig. 9-17, PDF pp. 10 y 19, la placa 3
entrega ruido rojo en pin 2, rosa en pin 6 y blanco en pin 5. El
selector SW14 conmuta en pares. **White** usa blanco para audio y
rojo para modulación. **Pink** usa rosa en ambas rutas. La toma
de modulación precede al nivel y al interruptor del mezclador.
[Registro de fuentes](FUENTES.md).

El modelo usa xorshift32 con semilla fija y salida uniforme en
`[−1, 1)` a 96 kHz. El rosa combina seis polos de 16, 64, 256,
1024, 4096 y 16384 Hz con pesos proporcionales a `1/√f`. El rojo
filtra la misma rama rosa con tiempos nominales de 0,33 s y 0,22 s.
La reducción los obtiene de los productos de 2,2 MΩ por 0,15 µF
y 0,10 µF de la última sección de Fig. 9-8.
Las ganancias nominales de rosa y rojo son 4 y 55, con límite de
±1. El generador sigue corriendo aunque la rama esté desconectada.
La [mezcla reducida](MEZCLADOR_PANEL.md) conserva el peso de
conductancia 3 de R48 de 11 kΩ frente a 33 kΩ de cada oscilador.
La rama de ruido conectada carga el bus incluso con nivel cero.
Interruptores y nivel recorren su escala en hasta 64 frames.

El pin 7A de la placa CA3046 llega a las entradas de OSC1, OSC2 y
OSC3 en Fig. 9-3, PDF p. 5. R163 lleva modulación al sumador de OSC3
libre. El modelo toma OSC3 del subpaso anterior, a una distancia
de 10,42 µs, para cerrar esa realimentación. La rueda interpola
en hasta 64 frames. A profundidad máxima se aplican ±2 semitonos
de afinación y ±2 octavas de corriente de cola al filtro, ambas
escalas nominales. El filtro limita la corriente a su intervalo
validado. El nivel, el espectro del ruido de juntura y el taper
del panel quedan pendientes de contraste con el circuito.

## Verificación

El [recibo de 0.7.0](../evidence/rf_d_playable_voice04.json) incluye
ruido blanco y rosa con nivel fijo, carga de la rama en cero,
modulación aislada de los dos destinos, retorno de CC121,
selección de rojo y rosa con el mezclador desconectado y
automatización con los tres osciladores activos.
El rosa agregó 8,906 dB al cociente entre la potencia media de
150–300 Hz y 1,2–2,4 kHz frente al blanco. Con la rama de ruido
conectada a nivel cero, la señal de OSC1 a bajo nivel quedó en
0,2501 de su valor con la rama abierta. Los dos destinos activos
produjeron audio idéntico entre particiones de 127, 128, 480 y
4096 frames. Con los nuevos destinos y la rama de ruido apagados,
0.7.0 y 0.6.0 produjeron 28.800 frames idénticos en una escena
de tres osciladores, Emphasis, legato y entrada CC1.

El primer análisis de fase instantánea marcó 0,507 Hz de dispersión
después de CC121 y 4,315 Hz con modulación exclusiva de filtro.
La estimación incluía los bordes de la ventana y la fase variable
del ladder. La comprobación de afinación usa el pico espectral
enventanado, con tolerancia de 0,1 Hz. La dispersión de fase del
filtro se registra como medida aparte. El DSP se conservó entre
esos dos análisis.

`python -B tools/check_rf_d_playable_voice.py --modulation` prueba el
perfil 0.7.0. La opción `--package 0.7.0` exporta ese perfil bajo demanda.
El motor carga los estados de esas tres versiones y completa
los controles nuevos con sus valores iniciales.

## Salida física a 128 frames

El banco cargó **Wheel Motion** desde el paquete probado por hash
en el host corregido `37e5f803`. Alternó las notas 57 y 45 en
legato y envió CC1 con valores 127, 80, 127 y 48. ASIO4ALL y la
salida NVIDIA confirmaron 128 frames efectivos a 48 kHz.

| Pase admitido | Callbacks | Mediana | Máximo | Asignaciones de render | Plazos perdidos |
| --- | ---: | ---: | ---: | ---: | ---: |
| Control repetido | 1200 | 0,0931 ms | 0,1924 ms | 0 | 0 |
| Wheel Motion 1 | 4800 | 0,1307 ms | 0,2382 ms | 0 | 0 |
| Wheel Motion 2 | 4800 | 0,1316 ms | 0,2290 ms | 0 | 0 |

Los pases admitidos quedaron dentro de 1,333 ms. El primer
control registró una solicitud de reset de ASIO. La repetición
pasó con el mismo binario. El banco silenció los buffers del
dispositivo después de verificar la señal del motor y restauró
el perfil al terminar. La escucha queda pendiente.
[Recibo ASIO](../evidence/rf_d_playable_voice_asio04.json).

Con el registro de compilación de RackForge descrito en el
[protocolo de combustible](RECOVERY_ENGINE128_FUEL_PROTOCOLO.md),
ejecutar
`python -B tools/check_rf_d_playable_voice_asio.py --modulation --host-build tmp/lab-current/voice-fuel-build.jsonl`.
