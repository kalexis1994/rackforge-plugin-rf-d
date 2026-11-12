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

```json
{
  "emerson_fat_bass": {
    "osc1_range": 1, "osc1_wave": 2, "saw_mix": 100,
    "osc2_range": 2, "osc2_wave": 2, "osc2_frequency": 0, "osc2_level": 100, "osc2_enabled": true,
    "osc3_range": 2, "osc3_wave": 2, "osc3_frequency": 0, "osc3_level": 100, "osc3_enabled": true, "osc3_tracking": true,
    "cutoff": 30, "emphasis": 50, "contour_amount": 35,
    "filter_tracking_one_third": true, "filter_tracking_two_thirds": true, "filter_modulation": true,
    "filter_attack": 1, "filter_decay": 300, "filter_sustain": 0,
    "loudness_attack": 1, "loudness_decay": 600, "loudness_sustain": 50, "decay_enabled": 1, "output_level": 50
  },
  "bass_viol_plucked": {
    "osc1_range": 1, "osc1_wave": 1, "saw_mix": 80,
    "osc3_range": 0, "osc3_wave": 0, "osc3_frequency": -7, "osc3_tracking": false,
    "cutoff": 20, "emphasis": 40, "contour_amount": 40,
    "filter_tracking_one_third": true, "filter_modulation": true,
    "filter_attack": 1, "filter_decay": 300, "filter_sustain": 40,
    "loudness_attack": 1, "loudness_decay": 700, "loudness_sustain": 0, "decay_enabled": 1, "output_level": 50
  },
  "trumpet": {
    "osc1_range": 3, "osc1_wave": 2, "saw_mix": 50,
    "osc2_range": 3, "osc2_wave": 2, "osc2_frequency": 0, "osc2_level": 70, "osc2_enabled": true,
    "osc3_range": 3, "osc3_wave": 2, "osc3_frequency": 0, "osc3_level": 90, "osc3_enabled": true, "osc3_tracking": true,
    "cutoff": 20, "emphasis": 0, "contour_amount": 40, "filter_tracking_one_third": true,
    "filter_attack": 400, "filter_decay": 400, "filter_sustain": 100,
    "loudness_attack": 200, "loudness_decay": 400, "loudness_sustain": 100, "decay_enabled": 1, "output_level": 50
  }
}
```

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
comparación con la ejecución de SynthMania queda pendiente.

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
