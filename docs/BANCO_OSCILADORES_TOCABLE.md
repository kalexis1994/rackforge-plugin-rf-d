# Banco de osciladores de RF-D Voice 0.5.0

Importá `artifacts/rf-d-voice-0.5.0.rfplugin` desde Plugins y elegí
**RF-D Voice** en PLAY. **Model D Saw** abre OSC1. **Three Oscillators**
activa los tres, con OSC2 triangular una quinta arriba y OSC3 cuadrado
una octava abajo. El instrumento sigue siendo monofónico, con MIDI 36–72,
host a 48 kHz, dos contornos y 48 frames de latencia.

## Panel y afinación

El manual clásico OP-EARLY, PDF pp. 6–8, describe las posiciones de los
selectores, las ramas de audio y el switch de control de OSC3. El
[registro de fuentes](FUENTES.md) identifica el documento. El código
usa la revisión [CA3046 documental](OBJETIVO.md).

| Control | Implementación tocable |
| --- | --- |
| Range | LO, 32′, 16′, 8′, 4′, 2′. Las posiciones audibles siguen −2, −1, 0, +1, +2 octavas desde A4 = 440 Hz en 8′. LO usa −6 octavas como hipótesis nominal. |
| Waveform | Triangular, sierra-triangular, sierra, cuadrada, pulso ancho y pulso angosto. En OSC3 la segunda posición reproduce la sierra con fase invertida en el tiempo. |
| Master Tune | ±100 cents lineales. Recorrido nominal para afinar el plugin. |
| OSC2/OSC3 Frequency | ±9 semitonos con seguimiento de teclado, equivalente al intervalo de sexta mayor del manual. |
| OSC3 Control | Al desactivarlo, OSC3 usa 220 Hz de referencia en 8′ y multiplica el recorrido de Frequency por 4, para un recorrido total de seis octavas. La referencia de 220 Hz es nominal. |
| Mixer | Los tres osciladores tienen volumen lineal 0–100 % e interruptor independiente. Ambos cambios interpolan en hasta 64 frames a 48 kHz. |

Las fases son libres, con arranques reproducibles de 0, 1/3 y 2/3 de
ciclo. El gatillo sólo acciona los contornos. Los cambios de rango o forma
de onda son conmutaciones discretas y conservan la fase del oscilador.

## Forma de onda, mezcla y nivel

La sierra y la triangular toman los coeficientes H128 de la
[familia reducida](VCO_FAMILIA_BUS_VOZ_APROXIMACION_RESULTADOS.md)
en CV −1,6 V y BUS nominal. Para sierra-triangular se combinan 10/57 de
sierra y 47/57 de triangular, proporciones del divisor R30/R31 con
fuentes ideales de la [conexión de panel](VCO1_CABLEADO_PANEL.md).
Los pulsos usan series de Fourier de onda rectangular ideal al 50 %,
35 % y 15 %. Los dos últimos anchos son nominales hasta contrastar sus
contactos y cargas. Se retira el término DC y se normaliza el pico de
cada forma de onda sobre todo su banco.

Cada banda tiene 2048 muestras y un límite de armónicos entre 128 y 1.
El oscilador interpola fase entre dos muestras y elige la banda más rica
cuyo último armónico queda por debajo de 20 kHz. Entre 16 y 20 kHz
de ese armónico interpola hacia la siguiente banda para que el cambio
sea continuo. El FIR de la voz sigue convirtiendo 96 kHz internos
a 48 kHz. Las bandas limitan el espectro de los osciladores antes de
la saturación del ladder.

El mezclador aproxima las tres ramas de [33 kΩ del panel](MEZCLADOR_PANEL.md)
con igual conductancia y la carga del filtro desacoplada. Cada
interruptor suma su fracción de conexión al denominador, incluso con
el volumen en cero. El divisor tiene mínimo 1 durante el fundido.
Los ±80 mV máximos del bus conservan la escala nominal de la voz.
Después del FIR, una compresión suave sobre 0,8 de escala digital deja
margen para los transitorios de acoplamiento de las ondas lentas.
El taper del potenciómetro, C27 cargado, diferencias por circuito
entre los tres osciladores y las curvas de calibración quedan en la
referencia eléctrica para el ajuste posterior.

## Verificación y compatibilidad

`python -B tools/check_rf_d_playable_voice.py` genera el paquete y lo
prueba en un store temporal. El [recibo de 0.5.0](../evidence/rf_d_playable_voice02.json)
registra pitch aislado, combinación de tres osciladores, espectro por
forma, seguimiento de OSC3, automatización y equivalencia bit a bit
entre tamaños de callback. Un primer ensayo de mezcla midió 329,525 Hz
en lugar de 329,628 Hz porque coincidían en la ventana de análisis la
quinta de OSC2 y el tercer armónico de OSC3 a 330 Hz. La regresión
usa una cuarta para separar los picos y conserva la quinta en la prueba
aislada de afinación y en el preset.

La prueba ABI verifica los 26 parámetros, los dos presets y la lectura de
los 11 valores del estado de 0.4.0 con los osciladores nuevos en sus
valores iniciales. RackForge puede fijar la versión de plugin en un
proyecto guardado. `--single-saw` permite regenerar el paquete 0.4.0
para esos proyectos. El estrés offline de RackForge usa los tres
osciladores activos.

## Medición con salida física

`python -B tools/check_rf_d_playable_voice_asio.py` instala el mismo
paquete por hash en un store temporal, carga el preset de tres
osciladores en un slot y alterna MIDI 57 y 45 en legato. El banco
silencia los buffers del dispositivo después de medir el render.
ASIO4ALL/NVIDIA confirmó 128 frames efectivos a 48 kHz, alternancia
de buffer y restauración del perfil. Queda pendiente la escucha.

| Pase | Callbacks | Mediana | Máximo | Sobre 1,333 ms | Plazos perdidos |
| --- | ---: | ---: | ---: | ---: | ---: |
| Control sin nota | 1200 | 0,0884 ms | 0,2036 ms | 0 | 0 |
| Tres osciladores 1 | 4800 | 0,0896 ms | 0,4923 ms | 0 | 0 |
| Tres osciladores 2 | 4800 | 0,0899 ms | 0,1651 ms | 0 | 0 |

Los dos pases activos tuvieron cero errores, avisos, fallos de slot e
intervalos superiores a 1,5 períodos. El control registró ocho avisos.
El criterio completo de admisión sigue abierto. El host registró una
asignación por callback, también en el control. El
[contraste de get_fuel](RECOVERY_ENGINE128_FUEL_RESULTADOS.md) identificó
ese patrón en el host base y eliminó la asignación en el host corregido.
Este paquete todavía requiere confirmación con ese host.
[Recibo ASIO](../evidence/rf_d_playable_voice_asio01.json).
