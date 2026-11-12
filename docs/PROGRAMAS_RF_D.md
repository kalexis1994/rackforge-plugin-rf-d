# Programas de fábrica de RF-D

**RF-D Factory** aparece en Programs de RackForge. Los ocho
programas se diseñaron para la voz nominal CA3046 de RF-D.
El catálogo conserva el banco Pilot y sus seis identificadores.
Model D Saw sigue siendo el programa inicial.

| Programa | Ajuste y gesto |
| --- | --- |
| **Round Sub** | Triángulo de 16′ con un triángulo más tenue a la octava. Mantén la nota para oír el grave sostenido. |
| **Feedback Bass** | Sierra, cuadrada de 16′ y retorno LO al preamplificador. External Level regula la intensidad de la realimentación. |
| **Glide Lead** | Dos sierras con 0,12 semitonos de separación y glide de 170 ms. Toca notas ligadas para oír el recorrido. |
| **Wheel Vibrato** | Pulso con una triangular libre de OSC3 en LO. La rueda MIDI introduce vibrato de afinación. |
| **Filter Brass** | Dos sierras y una apertura de filtro de 72 ms. El ataque de volumen comienza antes. |
| **Pulse Pluck** | Pulso estrecho, ataque de 2 ms y caída de 115 ms en ambos contornos. |
| **Noise Sweep** | Ruido rosa con ataque de filtro de 145 ms. Mantén la nota para oír la apertura. |
| **Interval Drone** | Tres osciladores con octava inferior y quinta superior. Mantén una nota o cierra S‑Trigger desde Control Inputs. |

Los niveles, intervalos y tiempos de cada programa son
decisiones musicales de RF-D en las unidades del panel.
El afinador y S‑Trigger cargan apagados, incluso si se
habían dejado activos en el programa anterior.
[Definiciones completas](../plugin/voice/presets.json).

## Catálogo, motor y estado

La misma definición genera el catálogo que lee RackForge y
la tabla de ajustes que usa WASM. La generación valida cada
valor contra el parámetro identificado en el esquema. La voz
carga un conjunto de controles inicializado desde los valores
predeterminados y publica todos los ajustes juntos al terminar.
El estado `RFDC` conserva los valores editables para que el
host pueda reabrir el sonido por estado guardado o por ID.

`python -B tools/check_rf_d_playable_voice.py` ejecuta una
frase con legato, rueda y release para cada programa. Compara
el render del programa con los mismos ajustes aplicados como
parámetros y prueba particiones de 128 y 4096 frames. El banco
contrasta el efecto de la rueda en Wheel Vibrato y la diferencia
de release entre Interval Drone y Pulse Pluck.

RackForge carga cada programa por ID, guarda sus controles y
vuelve a abrir el sonido desde esos bytes. La prueba compara
los valores guardados y la salida por bits con WASM directo.
Glide Lead, Feedback Bass e Interval Drone también se reabren
a 480 y 4096 frames. Cada estado guardado ocupa 388 bytes.
Los picos de audio de la frase quedaron entre 0,161 y 0,314
de escala completa. El peor callback offline entre las
cargas y restauraciones a 128 frames fue de 0,281 ms,
dentro del margen de 1,333 ms.
[Resultados](../evidence/rf_d_voice_development08.json).

`--midi` reconstruye el perfil previo al banco de fábrica.
La escucha y el balance de nivel en dispositivo quedan pendientes.
