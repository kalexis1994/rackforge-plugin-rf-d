# Patches documentados para comparar el Model D y RF-D

El Model D clásico se ajustaba a mano. Moog publicó las
posiciones del panel para que un músico pudiera volver a
armar un sonido. **RF-D Factory** ofrece programas propios
de RackForge. Estas fichas históricas sirven para comparar
el motor de RF-D con ejecuciones de los mismos ajustes.
[Moog sobre las fichas de ajuste](https://moogmusic-help.freshdesk.com/en/support/solutions/articles/69000866923-moog-semi-modular-synthesizers-initial-patch-templates)
y [cuaderno de Tom Rhea](https://medias.audiofanzine.com/files/minimoog-sounds-by-tom-rhea-ld-480638.pdf).

## Tres escenas iniciales

Los tiempos indican el inicio del tramo según el [índice
del video](https://www.matrixsynth.com/2020/08/minimoog-sound-charts-by-tom-rhea.html).
Las posiciones proceden del dibujo de cada ficha. El intérprete
puede ajustar la afinación, las ruedas y otros mandos durante
la toma. El video se publicó en 2015. Quedan por identificar
el número de serie, la revisión de placa y la cadena de grabación.

| Escena | Ficha impresa / PDF | Observaciones para el contraste | Demo |
| --- | --- | --- | --- |
| Emerson’s Fat Bass | 15 / 8 | Tres sierras, 32′/16′/16′ y mixer 10/10/10. Cutoff −2, Emphasis 5 y Amount 3,5. Contrastar el peso de la octava baja, los armónicos y la caída del filtro. | [SynthMania 11:31](https://www.youtube.com/watch?v=S_FKXtwqJoQ&t=691s) |
| Bass Viol, Plucked | 6 / 4 | OSC1 híbrido de sierra y triángulo a 32′, mixer 8. Cutoff −3, Emphasis 4 y Amount 4. Decay de filtro 300 y de volumen 700 con sustain de volumen cero. Contrastar el ataque y la caída del cuerpo de la nota. | [SynthMania 3:27](https://www.youtube.com/watch?v=S_FKXtwqJoQ&t=207s) |
| Trumpet | 10 / 6 | Tres sierras a 8′, mixer 5/7/9. Cutoff −3, Emphasis 0 y Amount 4. Ataque de volumen 200 y de filtro 400. Contrastar la subida del nivel y del brillo en notas sostenidas. | [SynthMania 6:56](https://www.youtube.com/watch?v=S_FKXtwqJoQ&t=416s) |

## Ajustes iniciales de RF-D

Son puntos de partida para la voz actual, con el resto del
panel en los defaults de Model D Saw. La traducción usa
`10 × posición` para diales de 0–10 y `10 × (5 + posición)`
para Cutoff de −5 a +5. Las cifras de los contornos se llevan
a ms y la marca de ataque 0 se representa con 1 ms, el mínimo
de RF-D. La transferencia eléctrica de cada dial y la
calibración de la unidad de la demo siguen abiertas.
Las sierras de los osciladores se afinan a cero desviación
y la rueda queda a cero en la primera nota de laboratorio.
Las posiciones gráficas de la rueda sirven para orientar
un segundo pase por oído.

[Valores iniciales por parámetro](../evidence/rf_d_reference_patches.json).

## Primer render de RF-D

Se aplicaron los valores anteriores sobre el perfil `--midi`
a 48 kHz. Se usó MIDI 57 con Note On en el frame 960 y Note Off
en 48.960. Las particiones de 128 y 480 frames dieron el mismo
audio por bits. Las cifras son amplitudes normalizadas de RF-D.
El RMS temprano cubre 30–80 ms tras Note On y el tardío,
480–880 ms.

| Escena | Pico | RMS temprano | RMS tardío |
| --- | ---: | ---: | ---: |
| Emerson’s Fat Bass | 0,05673 | 0,01749 | 0,005789 |
| Bass Viol, Plucked | 0,09170 | 0,04315 | 0,000682 |
| Trumpet | 0,004455 | 0,0000353 | 0,003164 |

El nivel de Trumpet con la conversión inicial de Cutoff es
bajo. Conviene medir la apertura y el nivel con la toma
alineada para distinguir un problema de curva de perilla
de un problema de respuesta del filtro. Estas cifras
corresponden a una nota de prueba propia de RF-D. La
comparación con la ejecución de SynthMania está en la
[sección de Trumpet](#trumpet-para-comparar-la-apertura-del-filtro).

## Fat Bass y la sensibilidad a Cutoff y Emphasis

La [demo de SynthMania](https://www.youtube.com/watch?v=S_FKXtwqJoQ&t=691s)
muestra la misma ficha a 11:37. A 11:42 y 11:47 se ve el
instrumento en un ángulo oblicuo. A 11:52 la mano izquierda
aparece junto a las ruedas. Las tomas revisadas dejan
inciertas las teclas pulsadas, su duración y la trayectoria
de las ruedas. El análisis usa dos notas propias, MIDI 57 y 45,
con un segundo de gate y ambas ruedas en reposo.

Se conservaron los valores de la ficha, con Cutoff en 20, 30
o 40 y Emphasis en 40, 50 o 60. El punto central es 30/50.
Cada paso de diez puntos representa una división en la
conversión nominal del dial. Las 18 corridas miden RMS y
armónicos H1 a H8 en dos ventanas desde Note On. La temprana
cubre 30–175 ms y la tardía 480–880 ms. Para los armónicos
se usa proyección a múltiplos de 55 Hz en MIDI 57 y de
27,5 Hz en MIDI 45, con ventana Hann y eliminación de DC.

Con Emphasis en 50, mover Cutoff de 30 a 40 elevó la relación
tardía H4–H8 frente a H1–H3 en **18,7 dB** en MIDI 57 y
**19,4 dB** en MIDI 45. A Cutoff 30, mover Emphasis de 40 a 60
redujo esa relación en **2,9 dB** y **1,8 dB**. El signo del
efecto de Emphasis se invirtió a Cutoff 40. En RF-D conviene
fijar primero Cutoff con una nota aislada y comprobar Emphasis
en el entorno de esa posición. La medición usa el motor
reducido y sigue pendiente el contraste con el audio del video.
[Resultados completos](../evidence/rf_d_fat_bass_sweep01.json).

`python -B tools/check_rf_d_fat_bass.py --audition` genera
un solo WAV mono de 10 s en `artifacts/rf-d-fat-bass-audicion.wav`.
Reproduce MIDI 57 en cinco variantes y ajusta una ganancia
constante por variante para igualar el RMS de la nota sostenida.
Las métricas del recibo se calculan con los niveles originales.
`--write-report` guarda los resultados y el hash del componente.

| Inicio | Cutoff | Emphasis |
| --- | ---: | ---: |
| 0,00 s | 30 | 50 |
| 2,05 s | 20 | 50 |
| 4,10 s | 40 | 50 |
| 6,15 s | 30 | 40 |
| 8,20 s | 30 | 60 |

## Oboe para la comparación por oído

Oboe usa sólo OSC1 en el mezclador, con pulso ancho a 4′
y nivel de panel 4. La ficha marca Cutoff 0, Emphasis 5
y Amount 3. El filtro usa ataque/decay/sustain 10 ms,
600 ms y 8. El contorno de volumen usa 100 ms, 200 ms
y 8. OSC3 queda libre en LO como fuente de modulación,
con su canal de audio apagado. [Ficha impresa 9, página 5
del PDF](https://medias.audiofanzine.com/files/minimoog-sounds-by-tom-rhea-ld-480638.pdf#page=5)
y [demo de SynthMania a 6:05](https://www.youtube.com/watch?v=S_FKXtwqJoQ&t=365s).

La escucha usa un segundo de gate en MIDI 57, con
fundamental nominal de 440 Hz por el rango 4′. MIDI 60
sirve de segunda nota para verificar el efecto de Cutoff.
Se conserva Emphasis en 50 % y se prueba Cutoff en 50 %
según la ficha y en 40 y 60 % como posiciones vecinas.
El ancho de pulso es el 35 % nominal de RF-D. Las ruedas
quedan en reposo para aislar el timbre de la nota sostenida.
El A/B de la interpretación se documenta abajo.

`python -B tools/check_rf_d_oboe.py --audition --write-report`
repite la prueba y escribe un solo WAV mono con ganancia
constante por clip para igualar el RMS. El orden de escucha
es Cutoff 50, 40 y 60 % en 0,00, 2,05 y 4,10 s. Los datos
incluyen los controles, la frecuencia medida y los armónicos.
[Resultados](../evidence/rf_d_oboe_sweep01.json).

En la nota de 440 Hz, con Cutoff en 50 %, la relación
H4–H8 frente a H1–H3 es de −55,4 dB en el tramo sostenido.
Al abrir Cutoff a 60 %, esa relación sube 1,8 dB y el RMS
de la nota antes de igualar la ganancia sube 11,1 dB.
Este pase permite contrastar el timbre sostenido y la
forma del ataque. La diferencia de brillo entre variantes
es sutil con el nivel igualado.

### A/B de la segunda frase del Oboe

El fragmento dura 1,78 s y empieza cerca de 6:13 de la
demo. Las notas que suenan son Sol4, La♭4, Sol4, Fa4,
Sol4, La♭4 y Si4. El registro 4′ hace sonar estas notas
una octava por encima de las teclas MIDI. Los cambios de
altura y la caída del volumen permiten estimar las
duraciones, el legato y las dos pausas entre ataques.
[Interpretación de SynthMania](https://www.youtube.com/watch?v=S_FKXtwqJoQ&t=373s).

La afinación de RF-D se desplaza +25 cents según los
tramos sin vibrato. La mano tapa parte de la rueda.
La modulación final se reconstruye por su efecto audible,
con un triángulo cercano a 9,8 Hz y una curva de CC1 que
sube a 21 de 127 y vuelve a cero. La posición física y
los instantes de tecla quedan estimados. Se conservan los
ajustes de la ficha para Cutoff, Emphasis y ambos contornos.

`python -B tools/check_rf_d_oboe_ab.py --write-report`
repite el A/B con la captura local identificada por SHA256
en el recibo. Es una captura del audio reproducido por
YouTube. La toma original y el render pasan a mono y se
igualan mediante una ganancia constante por toma, sin EQ.
El WAV alterna Minimoog y RF-D dos veces, con comienzos
en 0,00, 2,08, 4,16 y 6,24 s.
[Transcripción, medidas y orden de escucha](../evidence/rf_d_oboe_ab01.json).

En el Fa4 sostenido, H2/H1 es −3,9 dB en el Minimoog
y −28,6 dB en RF-D. El vibrato final abarca 59 y 55 cents
respectivamente entre los percentiles 5 y 95. El nivel
igualado de cada toma es −22 dBFS RMS. La diferencia de
armónicos se mide sobre la captura publicada y el render
completo, con la transferencia de Cutoff y la cadena de
grabación de la demo pendientes de identificar.

### De dónde sale la pérdida de agudos

Se repitió la misma frase cambiando un control por vez.
Con Cutoff al 50 %, el pico de RF-D fue 0,035 FS frente al
umbral de 0,8 FS del limitador de salida. Reducir Output Level
de 50 a 25 dejó H2/H1 dentro de 0,1 dB del original de RF-D.
Reducir el nivel de OSC1 de 40 a 20 apenas movió esa relación.
Abrir Cutoff de 50 a 90 recuperó entre 22,4 y 22,6 dB de
H2/H1 en las siete notas.

| Fa4 sostenido | H2/H1 | H3/H1 | H5/H1 |
| --- | ---: | ---: | ---: |
| Minimoog de la demo | −3,9 dB | −13,0 dB | −6,9 dB |
| RF-D, Cutoff 50 | −28,6 dB | −64,0 dB | −68,1 dB |
| RF-D, Cutoff 90 | −6,0 dB | −23,1 dB | −7,0 dB |

La calibración **Filter Range** del manual de servicio de
1973 pide igualar la autooscilación a 440 Hz con Cutoff en −1,
Emphasis en 10 y ambos switches de teclado apagados. Con
el contorno desactivado, la voz de RF-D se estabiliza a
91,7 Hz en el 40 % equivalente a −1 y a 443,1 Hz en el 66,5 %.
La tabla del motor parte del RANGE provisional 0,1 de los
[tres puntos DC del oráculo](VOZ_APERTURA_CUTOFF_RESULTADOS.md).
Este contraste permite medir el error del control fuera del
patch. El ajuste al 90 % fue local para la escucha. Ese motor
usaba su curva anterior y el tercer armónico quedaba
unos 10 dB por debajo de la captura en el Fa4.
[Manual de servicio, página impresa 14](https://www.vintagesynthparts.com/wp-content/uploads/2016/08/MINIMOOG-D_SERVICE_MANUAL.pdf).

`python -B tools/check_rf_d_oboe_clarity.py --audition --write-report`
genera `artifacts/rf-d-oboe-cutoff-ab.wav` con la secuencia
Minimoog, RF-D al 50 %, Minimoog, RF-D al 90 %. Las tomas
mantienen −22 dBFS RMS. [Mediciones](../evidence/rf_d_oboe_clarity01.json).

### Oboe con el filtro calibrado

La voz MIDI calibra RANGE con Cutoff en la marca −1 y
Emphasis en 10. Se busca la corriente que reproduce el punto
de 440 Hz y se resuelve Q26/Q28 junto al ladder para todo el
recorrido del potenciómetro. La tabla de 41 corrientes en
amperios se contrasta en 40 puntos intermedios con error
relativo máximo de 0,39 %. La medida
estabilizada del motor da 439,99 Hz. En los puntos vecinos
35, 45 y 50 % da 315,82, 614,61 y 859,88 Hz.
[Manual de servicio, página impresa 14](https://www.vintagesynthparts.com/wp-content/uploads/2016/08/MINIMOOG-D_SERVICE_MANUAL.pdf#page=14).

A 96 kHz, el paso del ladder usa `g = x/(1+x)`, con
`x = Icola/(4·Vt·C·96000)`. Es el paso de Euler implícito
para la etapa linealizada, aplicado a la diferencia de
corrientes tanh del modelo reducido. La tabla de realimentación
se extiende al intervalo de coeficientes que ahora alcanza el
filtro abierto. La pendiente del mando presupone una relación
lineal entre la posición del panel y la fracción eléctrica de
R11. El ancho de **Wide Pulse** se toma del contacto 11 de la
simulación CA3046, que dio 30,42 % de estado alto.
[Red de cutoff](CUTOFF_NATIVO_Q26_Q28.md) · [Validación de pulsos](../evidence/vco1_circuit_validation.json).

Con los valores de la ficha y Cutoff al 50 %, el Fa4 da
H2/H1 de −3,6 dB y H3/H1 de −15,2 dB. La toma del Minimoog
da −3,9 y −13,0 dB respectivamente. En esa nota H4 queda
6,2 dB por encima de la captura y H6 queda 12,3 dB por debajo.
La calibración de rango es nominal y el A/B sigue usando
la captura de la demo.
[Mediciones por nota](../evidence/rf_d_oboe_calibrated01.json).

`python -B tools/check_rf_d_oboe_calibrated.py --audition --write-report`
genera `artifacts/rf-d-oboe-calibrado-ab.wav`. Alterna
Minimoog y RF-D dos veces con −22 dBFS RMS.

La batería de WASM y RackForge valida los ocho presets,
el estado restaurado y el render a 128, 480 y 4096 frames.
El mayor tiempo de captura de los presets a 128 frames fue
0,3224 ms. La prueba de Phones usa una señal menor para medir
la transferencia de pequeña señal con la nueva apertura.
El contraste de Filter CV usa la frecuencia que predice la
etapa discreta para cada corriente, con la tolerancia anterior.
[Pruebas del motor](../evidence/rf_d_voice_development09.json).

### Ajuste del Oboe a la toma de SynthMania

El A/B calibrado conservaba la diferencia que se oía en
los agudos. En Fa4, la banda de 2,2–4 kHz quedaba 21,1 dB
por debajo del Minimoog y la de 4–8 kHz, 30,7 dB por debajo.
Las dos relaciones usan la energía total de la nota.

Se compararon cinco bandas entre 700 Hz y 16 kHz y se
seleccionaron Cutoff 72 % y Emphasis 40 % con el Fa4 y el
Sol4 de las ventanas 275–430 y 600–720 ms. En las otras
cinco notas de la misma frase, la diferencia media por
banda bajó de 15,1 a 2,0 dB. En Fa4 quedaron 2,1 dB de
diferencia entre 2,2 y 4 kHz y 0,1 dB entre 4 y 8 kHz.
Las posiciones elegidas corresponden al ajuste de esta
captura y se conservan como valores del patch de escucha.
[Mediciones por nota y búsqueda](../evidence/rf_d_oboe_spectrum01.json).

`python -B tools/check_rf_d_oboe_spectrum.py --audition --write-report`
genera `artifacts/rf-d-oboe-brillo-ab.wav` a −22 dBFS RMS.
La secuencia empieza con Minimoog y RF-D ajustado. Después
repite Minimoog y reproduce RF-D con los valores de la ficha.

### Ajuste del cuerpo del Oboe

En la primera comparación con brillo ajustado, RF-D tenía
1,3 dB más de energía relativa en la fundamental de la
nota mediana. Los armónicos de 1,2 a 4 kHz quedaban más bajos.
El séptimo armónico medía −41,8 dB respecto de la fundamental
en el Minimoog y −21,0 dB en RF-D, como medianas de siete notas.
Un pulso rectangular con ciclo útil de 2/7 tiene un cero
teórico en ese armónico. Se ensayó 28,57 % como hipótesis
para la toma, con el 30,42 % de la placa como comparación.

El Fa4 y el Sol4 seleccionaron Cutoff 67 % y Emphasis 60 %,
con nivel de OSC1 al 40 %. En las otras cinco notas, el
error medio entre 1,2 y 4 kHz bajó de 3,4 a 2,1 dB.
La mayor recuperación se dio entre 2,2 y 4 kHz y el nivel
relativo entre 1,2 y 2,2 kHz sigue por debajo de la toma.
El error medio entre 4 y 8 kHz quedó en 2,4 dB. El ancho
de pulso de 2/7 se aplica en este experimento de escucha.
[Mediciones por nota](../evidence/rf_d_oboe_body01.json).

`python -B tools/check_rf_d_oboe_body.py --audition --write-report`
genera `artifacts/rf-d-oboe-cuerpo-ab.wav` a −22 dBFS RMS.
El RF-D con el ajuste de cuerpo entra en 2,08 s y el RF-D
del primer A/B anterior entra en 6,24 s.

### Ataque y articulación del Oboe

La toma de SynthMania alcanza el nivel sostenido en unos
20–30 ms en las tres entradas después de una pausa. En
RF-D, el ataque tarda más con el valor nominal de 100 ms
de la ficha. La primera entrada de la captura también
empieza con menos energía entre 2 y 8 kHz y gana brillo
durante los primeros 30 ms.

En el render de escucha se usa un ataque de volumen de
30 ms y se desplaza 6 ms el inicio de las tres notas
separadas. Se mantienen los cortes de nota, las uniones
legato, el vibrato y los controles del ajuste de cuerpo.
Se compara RMS en ventanas de 8 ms, relativo al nivel
de cada nota entre 50 y 70 ms desde el inicio transcrito.
El tiempo nuevo es un ajuste para esta interpretación.
[Curvas de ataque](../evidence/rf_d_oboe_articulation01.json).

`python -B tools/check_rf_d_oboe_articulation.py --audition --write-report`
genera `artifacts/rf-d-oboe-ataque-ab.wav` a −22 dBFS RMS.
El RF-D con el ataque ajustado entra en 2,08 s y el RF-D
del A/B de cuerpo entra en 6,24 s.

### Sobremuestreo en el Oboe

El motor de la prueba procesa a 96 kHz (2×) y entrega
48 kHz. La variante a 192 kHz (4×) usa los mismos eventos,
controles y ancho de pulso. Cada variante calcula el lazo
de Emphasis a su frecuencia interna y usa el FIR de
22 kHz con 1 ms de retardo. La respuesta de ambos FIR
varía menos de 0,001 dB en los puntos medidos entre 8 y
20 kHz. El sobremuestreo permite reducir el plegamiento
de armónicos que genera el procesamiento no lineal.
[Kahles, Esqueda y Välimäki, 2019](https://doi.org/10.17743/jaes.2019.0012).

En las siete notas, el cambio medio de 2× a 4× es de
0,13 dB en las bandas 2,2–4 y 4–8 kHz y de 0,61 dB
entre 12 y 18 kHz. En esa última banda, el error medio
frente a la toma sigue en 8,7 dB con 4×. La mediana del
tiempo de render de 128 frames en el banco WASM pasó de
0,109 a 0,196 ms en esta ejecución.

En el tono de 440 Hz, la energía fuera de los armónicos
queda cerca de −112 dB en ambas variantes, relativa a la
energía audible. En el tono de 1760 Hz con filtro abierto
pasa de −118,5 a −129,9 dB. La medida usa 200 ms de tono
sostenido y recoge todo residuo entre 20 Hz y 20 kHz fuera
de los bins armónicos. La variante 4× se ejecuta en el
banco de escucha.
[Mediciones por nota y frecuencia interna](../evidence/rf_d_oboe_oversampling01.json).

`python -B tools/check_rf_d_oboe_oversampling.py --audition --write-report`
genera `artifacts/rf-d-oboe-sobremuestreo-ab.wav` a −22 dBFS RMS.
La secuencia es Minimoog, RF-D 4×, Minimoog y RF-D 2×.
La última toma coincide por bytes con el RF-D de 2,08 s
del A/B de ataque.

### Ajuste de armónicos a 4×

En Fa4, el RF-D a 4× tenía entre 3 y 4 dB de menos en
H4 y H5 y unos 4 dB de más en H10. Para distinguir
esas diferencias, se midió cada armónico respecto de
la fundamental en las mismas ventanas por nota.

Se buscaron Cutoff, Emphasis y nivel de OSC1 sobre
Fa4 y Sol4, con el pulso y la articulación del último
A/B. El criterio suma tres errores medios en dB.
Incluye H2–H6, H8–H20 y cuatro bandas entre 1,2 y
12 kHz. Para los armónicos, la comparación usa un piso
de −45 dB respecto de la fundamental. Los valores
elegidos fueron 69 %, 45 % y 25 %, respectivamente.

En las cinco ventanas reservadas de la frase, el error
de H8–H20 pasó de 3,78 a 2,33 dB y el de las cuatro
bandas pasó de 2,85 a 2,21 dB. El de H2–H6 pasó de
2,93 a 3,12 dB. El error medio de la curva de ataque
quedó en 1,32 dB. Los valores son un ajuste del patch
a la captura de SynthMania.
[Mediciones por nota](../evidence/rf_d_oboe_refit01.json).

`python -B tools/check_rf_d_oboe_refit.py --audition --write-report`
genera `artifacts/rf-d-oboe-refit-ab.wav` a −22 dBFS RMS.
El RF-D ajustado entra en 2,08 s y el RF-D del A/B de
sobremuestreo entra en 6,24 s. Ambas tomas usan 4×.

### Cola de la grabación de SynthMania

La escucha del primer par del A/B con ajuste de armónicos
identificó una sensación de espacio en la toma del Minimoog.
La captura estéreo anterior a la mezcla a mono permite
contrastar esa observación. Se retira del canal diferencia
la componente proporcional a la señal mono, para descontar
un desbalance constante de ganancia entre canales.

Durante la última nota sostenida la correlación entre
canales es 0,999 y el residuo lateral queda 33,3 dB por
debajo del centro. Entre 155 y 250 ms después del Note Off
transcrito, la correlación baja a 0,35–0,16 y el residuo
queda entre 3,6 y 2,3 dB por debajo del centro. En esas
ventanas, entre 87 y 92 % de su energía de 100 Hz a 6 kHz
cae cerca de los armónicos de la nota final.

La cola estéreo sigue la última nota. Es compatible con
ambiente o procesamiento de la grabación y su origen
exacto queda abierto. Se toma el primer par del último A/B
como referencia de escucha para el timbre. La cola se
conserva como observación de la captura.
[Grabación de SynthMania](https://www.youtube.com/watch?v=S_FKXtwqJoQ&t=373s) ·
[Mediciones de la cola](../evidence/rf_d_oboe_tail01.json).

`python -B tools/check_rf_d_oboe_tail.py` repite el análisis
desde la captura estéreo y el WAV del A/B con ajuste de armónicos.

## Trumpet para comparar la apertura del filtro

La [ficha de Trumpet](https://medias.audiofanzine.com/files/minimoog-sounds-by-tom-rhea-ld-480638.pdf#page=6)
arranca con OSC1 en sierra a 8′ y nivel 5. Los otros dos
osciladores permiten engrosar el sonido al unísono. El A/B
usa la variante de un oscilador, Emphasis en cero y tracking
de teclado de un tercio. Se transcribió la primera frase de
la [demo de SynthMania](https://www.youtube.com/watch?v=S_FKXtwqJoQ&t=416s)
hasta la caída del Fa, con nueve notas y un arpegio ligado al
inicio. Los gates se estimaron a partir del audio, con rueda
fija y afinación global de +15,4 cents en RF-D.

Se probaron Cutoff y ambos ataques en seis notas y se
reservaron las tres últimas para verificar el ajuste. El
candidato usa Cutoff 40, ataque de filtro de 200 ms y ataque
de volumen de 110 ms. En las notas reservadas, el error
medio absoluto en H2–H8 respecto de H1 pasó de **8,65 a
3,87 dB**. El de la envolvente de ataque respecto del RMS
de la frase bajó de **9,78 a 1,39 dB**. Son ajustes para esta
toma. La grabación conserva su cadena original y queda
pendiente comprobar los valores en otra ejecución.
[Transcripción, ajuste y mediciones](../evidence/rf_d_trumpet_ab01.json).

`python -B tools/check_rf_d_trumpet_ab.py --write-report` usa
la referencia privada verificada por SHA-256. Renderiza a
48 kHz con sobremuestreo 4× y verifica igualdad por bits
a 128 y 480 frames. Genera `artifacts/rf-d-trumpet-ab.wav`,
con dos repeticiones a −22 dBFS RMS y ganancia constante
por frase. El Minimoog entra a 0,00 y 5,40 s. RF-D entra a
2,70 y 8,10 s.

## Cómo escuchar y medir

Para el A/B musical hay que identificar la nota, su duración y
los movimientos de rueda de un fragmento corto. Renderizar ese
gesto con los ajustes iniciales. Alinear el ataque y compensar
sólo la diferencia de nivel para la escucha. Comparar primero
armónicos relativos, forma del ataque y caída del filtro y
volumen. Registrar por separado las perillas que haya que
mover para acercar los dos sonidos. Conservar un tramo o una
nota adicional para comprobar que el ajuste se sostiene.

Hay dos referencias adicionales para aislar bloques.
AMAZONA publica osciladores y FM del filtro de un Minimoog de
1974, según el dueño que hizo la prueba. TONELAB declara una
unidad de 1973 y dedica tramos al banco de osciladores (3:45),
los contornos (11:22) y el filtro (14:40).
[Grabaciones de AMAZONA](https://www.amazona.de/vergleichstest-moog-minimoog-vs-vst-software-clones/#:~:text=Klangbeispiele)
y [demo de TONELAB](https://www.youtube.com/watch?v=_ft6GwpYBug&t=225s).

Los barridos directos que publicó Moog en 2016 aportan otra
escucha del filtro. La descripción declara captura sin EQ,
compresión ni efectos y deja abierta la revisión de la unidad.
El uso de cada grabación queda acotado por su procedencia.
[Barridos de Moog](https://soundcloud.com/moogmusicinc/3-filter-sweeps?in=moogmusicinc%2Fsets%2Fminimoog-model-d-sound-samples)
y [criterios de validación de RF-D](VALIDACION_SIN_HARDWARE.md).
