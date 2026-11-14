# Programas de fábrica de RF-D

**Programs** de RackForge ofrece 40 programas de fábrica para el perfil
CA3046 nominal de RF-D. **Model D Classic** es el primer programa.
Cada programa de **Mono** selecciona una voz y cada programa de **Poly**
selecciona dos. Usá **Voices** después de cargar el sonido para cambiar
el límite a un máximo de seis. La elección de dos voces responde a las
[mediciones en la Pi](POLIFONIA_RF_D.md#raspberry-pi-4-a-128-frames).

## Mono

| Programa | Ajuste y gesto |
| --- | --- |
| **Model D Classic** | Sierra de 8′ y una triangular suave una octava abajo. Probá la misma línea grave una octava más arriba. |
| **Round Sub** | Triángulo de 16′ con un triángulo más tenue a la octava. Mantén la nota para oír el grave sostenido. |
| **Feedback Bass** | Sierra, cuadrada de 16′ y retorno LO al preamplificador. External Level regula la intensidad de la realimentación. |
| **Glide Lead** | Dos sierras con 0,12 semitonos de separación y glide de 170 ms. Toca notas ligadas para oír el recorrido. |
| **Wheel Vibrato** | Pulso con una triangular libre de OSC3 en LO. La rueda MIDI introduce vibrato de afinación. |
| **Filter Brass** | Dos sierras y una apertura de filtro de 72 ms. El ataque de volumen comienza antes. |
| **Pulse Pluck** | Pulso estrecho, ataque de 2 ms y caída de 115 ms en ambos contornos. |
| **Noise Sweep** | Ruido rosa con ataque de filtro de 145 ms. Mantén la nota para oír la apertura. |
| **Interval Drone** | Tres osciladores con octava inferior y quinta superior. Mantén una nota o cierra S‑Trigger desde Control Inputs. |
| **Nickel Bass** | Cuadrada de 16′ con un pulso de 8′ y una apertura corta de filtro. Tocá notas cortas en el registro grave. |
| **Amber Reed** | Cuadrada con un triángulo tenue y una breve apertura de filtro. Subí un poco la rueda al sostener una nota. |
| **Rosin String** | Sierra-triángulo y sierra levemente desafinadas. El volumen crece antes que el brillo. Usá legato para activar el glide. |
| **Porcelain Blocks** | Dos triángulos desafinados a 4′ con contornos breves. Tocá staccato en el registro medio. |
| **Fourth and Fifth** | Fundamental, cuarta y quinta simultáneas con sierra, cuadrada y triángulo. El glide traslada los tres intervalos juntos. |
| **Shutter Pulse** | OSC3 libre en LO mueve el filtro con un pulso asimétrico. Sostené una nota y subí la rueda. |
| **Copper Sidebands** | OSC3 libre modula la afinación a frecuencia de audio. La rueda introduce el timbre metálico. |
| **Ladder Whistle** | El ladder autooscila con las fuentes del mixer apagadas y sigue al teclado con ambos switches de tracking. Sostené las notas para dejar que crezca la resonancia. |
| **Oxide Bass** | Bajo de sierra y pulso con realimentación LO moderada y barrido corto. |
| **Rubber Octave** | Dos cuadradas graves con un ataque resonante y un sustain oscuro. |
| **Chrome Lead** | Sierra brillante con un pulso estrecho una octava arriba y vibrato en la rueda. |
| **Hollow Flute** | Triangular con un poco de ruido blanco y un ataque de viento suave. |
| **Clay Drum** | Triangular de 16′ con un golpe breve de ruido rosa. |
| **Slow Beacon** | Sierra-triángulo y sierra invertida con batido y apertura lenta. |
| **Ladder Zap** | Barrido corto y resonante del filtro excitado por ruido blanco. |

## Poly

| Programa | Gesto |
| --- | --- |
| **Afterglow Strings** | Dejá que las notas de un acorde se mezclen con el siguiente. |
| **Brass Section** | Probá golpes de acordes en el registro medio. |
| **Copper Comp** | Tocá acordes sincopados. |
| **Reed Choir** | Sostené dos notas cercanas para oír el batido. |
| **Felt Keys** | Dejá que el brillo inicial caiga con la tecla sostenida. |
| **Glass Tines** | Separá los acordes para oír el ataque agudo. |
| **Dry Clav** | Tocá acordes cortos en el registro medio. |
| **Drawbar Chords** | Probá acordes ligados con ataque inmediato. |
| **Ivory Combo** | Usá acordes rítmicos en el registro alto. |
| **Maple Pluck** | Probá acordes arpegiados. |
| **Amber Marimba** | Dejá espacio entre golpes. |
| **Woven Pad** | Sostené el acorde durante la apertura del filtro. |
| **Stillwater** | Escuchá el batido en notas largas. |
| **Air Ensemble** | Probá intervalos amplios sostenidos. |
| **Night Current** | Subí la rueda despacio con dos notas sostenidas. |
| **Ember Pulse** | Subí la rueda para alternar dos aperturas del filtro. |

Moog documenta cuerdas, metales y teclados eléctricos entre los programas del
Memorymoog. El manual del Matriarch describe cómo un ataque lento sirve para
cuerdas y cómo separar el ataque de volumen del ataque de brillo en metales.
Esas técnicas guiaron los programas Poly, con niveles, intervalos y tiempos
ajustados en las unidades del panel de RF-D.
[Catálogo Memorymoog de Moog](https://moogfoundation.org/wp-content/uploads/1982-Memorymoog-Catalog.pdf) ·
[Manual del Matriarch, p. 25](https://cdn.inmusicbrands.com/Moog/Matriarch/Matriarch_Manual_012023.pdf).

El afinador y S‑Trigger cargan apagados, incluso si se
habían dejado activos en el programa anterior.
[Definiciones completas](../plugin/voice/presets.json).

## Técnicas de los patches del Model D

- **Registro, articulación y batido.** Los ejemplos de bajo y
  percusión de las tablas de Tom Rhea enseñan a usar la octava para
  cambiar el cuerpo y el batido entre osciladores para dar movimiento
  a un ataque corto. Nickel Bass combina dos formas de pulso a una octava
  de distancia. Porcelain Blocks usa dos triángulos separados por
  0,94 semitonos. [Minimoog Patch Book, pp. 2 y 12](https://medias.audiofanzine.com/files/minimoog-patch-book-ld-480637.pdf#page=2).
- **Contornos separados y rueda.** Las tablas de cuerdas y vientos
  relacionan el ataque y el gesto de sostener la nota con la entrada
  del vibrato. Rosin String abre el volumen en 106 ms y el filtro en
  170 ms. Amber Reed usa la triangular libre de OSC3 para el vibrato
  y dos formas que comparten fundamental. [Minimoog Patch Book, pp. 4–9](https://medias.audiofanzine.com/files/minimoog-patch-book-ld-480637.pdf#page=4).
- **Afinaciones superpuestas.** El ajuste de *Aquatarkus* muestra
  cómo una cuarta y una quinta generan un acorde fijo con una sola tecla.
  Fourth and Fifth usa +5 y +7 semitonos con tres formas distintas
  y un contorno propio. [Minimoog Patch Book, p. 14](https://medias.audiofanzine.com/files/minimoog-patch-book-ld-480637.pdf#page=14).
- **OSC3 fuera del mixer.** Con OSC3 Control apagado, su frecuencia
  puede funcionar como reloj lento para el filtro o como modulador de
  afinación a frecuencia de audio. Shutter Pulse usa el pulso ancho
  en LO. Copper Sidebands usa un triángulo libre de unos 64 Hz.
  [Manual de operación, pp. PDF 7 y 11](https://funkwerkes.com/web/wp-content/techdocs/MixedProAudio/Minimoog-Manual.pdf#page=7) ·
  [Minimoog Patch Book, pp. 19–20](https://medias.audiofanzine.com/files/minimoog-patch-book-ld-480637.pdf#page=19).
- **El filtro como fuente.** A Emphasis máximo, el ladder se
  sostiene por sí solo. Ladder Whistle conserva el mixer apagado
  y usa el tracking completo para tocar el tono desde MIDI.
  [Manual de operación, p. PDF 12](https://funkwerkes.com/web/wp-content/techdocs/MixedProAudio/Minimoog-Manual.pdf#page=12).

Los diagramas vintage indican posiciones aproximadas. Los niveles
y tiempos del banco se ajustaron en las unidades de RF-D.
[Ficha de las Sound Charts de 1974](https://www.videohistoryproject.org/sound-charts-minimoog-patch-charts).

## Catálogo, motor y estado

La misma definición genera el catálogo que lee RackForge y
la tabla de ajustes que usa WASM. La generación valida cada
valor contra el parámetro identificado en el esquema. La voz
carga un conjunto de controles inicializado desde los valores
predeterminados y publica todos los ajustes juntos al terminar.
El estado `RFDC` conserva los valores editables para que el
host pueda reabrir el sonido por estado guardado o por ID.

`python -B tools/check_rf_d_playable_voice.py` ejecuta una
frase con legato, rueda y release para Mono. En Poly usa dos notas
solapadas y comprueba sus fundamentales antes de mover la rueda.
Ladder Whistle usa dos notas sostenidas separadas por una octava.
El ensayo compara el render del programa con los mismos ajustes
aplicados como parámetros y prueba particiones de 128 y 4096 frames. El banco
contrasta el efecto de la rueda en Wheel Vibrato, Amber Reed,
Shutter Pulse y Copper Sidebands, la afinación por octavas
de Ladder Whistle y el release de Interval Drone y Pulse Pluck.

RackForge carga cada programa por ID, guarda sus controles y
vuelve a abrir el sonido desde esos bytes. La prueba compara
los valores guardados y la salida por bits con WASM directo.
Glide Lead, Feedback Bass e Interval Drone también se reabren
a 480 y 4096 frames. El estado de sesión actual ocupa 460 bytes.
Los estados anteriores de 444 bytes conservan el modo de voz.
Los de 436 bytes se abren en Mono. Ambos cargan las profundidades
de expresión en cero.
El banco **User** admite 64 programas, recuerda las profundidades de
expresión y usa el modo **Voices** vigente.
El identificador de cada uno de los 16 programas de fábrica anteriores
sigue disponible. Los IDs de las pruebas antiguas siguen siendo
utilizables por las herramientas de laboratorio.
[Resultados](../evidence/rf_d_voice_development10.json).

`--midi` reconstruye el perfil previo al banco de fábrica.
La escucha y el balance de nivel en dispositivo quedan pendientes.
