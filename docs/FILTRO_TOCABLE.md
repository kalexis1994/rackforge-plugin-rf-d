# Filtro tocable de RF-D Voice 0.6.0

Importá `artifacts/rf-d-voice-0.6.0.rfplugin` desde Plugins y elegí
**RF-D Voice** en PLAY. **Resonant Bass** activa los tres osciladores,
Emphasis al 82 % y Keyboard ⅔. Para escuchar la autooscilación sola,
apagá los osciladores en el mezclador, poné Cutoff cerca del 65 %,
Contour Amount en cero, Emphasis al máximo y sostené una nota.
El instrumento sigue siendo monofónico, con MIDI 36–72 a 48 kHz.

## Controles y modelo nominal

**Emphasis** realimenta el cuarto escalón del ladder después de su
acoplamiento de recuperación. El [camino eléctrico de referencia](LAZO_EMPHASIS_PEQUENA_SENAL.md)
cruza C10 de 10 µF desde R7/R3, pasa por R14 y R73 y vuelve a Q30
en SVC-9 Fig. 9-11 y 9-17, PDF pp. 13 y 19. El retorno reducido
usa un RC de 10 µF por 1330 Ω, con R73 nominal y R76, que da 13,3 ms.
La carga activa de Q30 y la curva del potenciómetro R14 quedan para
contraste con el circuito.

La fase y magnitud para el comienzo de la autooscilación se calculan
con las cuatro etapas discretas, el acoplamiento de recuperación
de 10,34 ms, el de retorno de 13,3 ms y un tick de demora a 96 kHz.
En pequeña señal, cada etapa tiene transferencia
`g / (1 − (1 − g)·z⁻¹)`. Cada acoplamiento tiene transferencia
`a·(1 − z⁻¹) / (1 − a·z⁻¹)`, con `a = exp(−1/(96 kHz·τ))`.
El inverso de la magnitud del lazo en su primer cruce de −π da la
ganancia crítica. La tabla se interpola sobre 321 puntos logarítmicos
de `g` de 2⁻¹² a 2⁻². Se verifican los puntos medios contra el cálculo
directo. El límite de Emphasis al 100 % es 110 % de esa ganancia,
con techo de 8 V/V. El techo reduce el alcance de la autooscilación
en el extremo más cerrado del cutoff. El potenciómetro virtual
recorre linealmente esa escala. La saturación de los pares
diferenciales limita la amplitud, y un impulso de 0,514 µV nominal
inicia la oscilación al cruzar el umbral con la entrada en reposo.

**Keyboard ⅓** y **Keyboard ⅔** suman 0, ⅓, ⅔ o 1 de octava de
cutoff por octava de teclado, con ancla MIDI 57. Las ramas conmutadas
de 300 kΩ y 150 kΩ del [control de cutoff](CUTOFF_NATIVO_Q26_Q28.md)
fundamentan la relación 1:2. La voz multiplica la corriente nominal
de cola por `2^((nota − 57)·fracción/12)` y conserva el intervalo
de 0,2431 a 144,4219 µA. El tracking usa la nota de prioridad más
baja y retiene la última durante el release. El rango y la
afinación del oscilador quedan fuera de esa lectura.

## Verificación

El [recibo de 0.6.0](../evidence/rf_d_playable_voice03.json) registra
404,515 Hz de autooscilación a Cutoff 65 %, con el mezclador apagado.
Al subir una octava de teclado, se midieron 404,515 Hz con ambos
switches apagados, 509,414 Hz con ⅓, 643,606 Hz con ⅔ y 816,012 Hz
con ambos. La prueba verifica decaimiento por debajo del umbral,
legato con la nota baja y su liberación, automatización en distintas
particiones y respuesta finita con cutoff y tracking en los extremos.
La voz generó los mismos 28.800 frames que 0.5.0 en una escena con
tres osciladores, legato y cambio de onda con los controles nuevos
en cero. El motor importa los estados de 0.4.0 y 0.5.0 con los
controles nuevos en cero.

`python -B tools/check_rf_d_playable_voice.py` regenera 0.6.0 y
mide el preset resonante en RackForge a 128, 480 y 4096 frames.
`--oscillator-bank` y `--single-saw` regeneran 0.5.0 y 0.4.0
respectivamente para proyectos que conserven esas versiones.
