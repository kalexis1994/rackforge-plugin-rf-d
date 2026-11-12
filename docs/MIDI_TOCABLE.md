# Interpretación MIDI en la voz de desarrollo

RF-D acepta notas MIDI de 0 a 127 en los 16 canales recibidos
del slot de RackForge. La prioridad de la tecla más baja sigue
el teclado del Model D documentado en OP-EARLY PDF p. 8.
La entrada MIDI extiende esa regla a todos los canales del
slot. El estado de una tecla pertenece a su canal y cada
Note On solapado tiene su correspondiente Note Off. Se
acepta también Note On con velocidad cero para soltar.
[Fuentes del Model D](FUENTES.md) y [especificación MIDI 1.0](https://midi.org/midi-1-0-detailed-specification).

La selección de nota y el estado del gate se mantienen
por separado. El gate suma teclas pulsadas, retenciones de
pedal y el contacto S‑Trigger. Una tecla pulsada tiene
prioridad sobre el CV retenido. Durante la retención el
CV conserva el último valor que alcanzó, incluido un
glide interrumpido. La velocidad permanece fuera de la
ley de amplitud del instrumento clásico.

| Mensaje | Acción en RF-D |
| --- | --- |
| CC64, 64–127 | El pedal retiene el gate al liberar una tecla de ese canal. |
| CC64, 0–63 | Libera la retención de ese canal. |
| CC123, All Notes Off | Suelta las teclas del canal y respeta su pedal. |
| CC120, All Sound Off | Limpia teclas y retención del canal. Cuando queda libre el gate compartido, pone los contornos a cero de inmediato. C2 y el FIR conservan su cola. |
| CC121, Reset All Controllers | Suelta el pedal del canal y devuelve el pitch bend y la rueda de modulación compartidos a reposo. |

El afinador sigue su recorrido de salida independiente. El
contacto S‑Trigger conserva el gate aunque llegue CC120.
El pedal y los mensajes de modo son adaptaciones de RackForge
para tocar con MIDI. [Tabla de mensajes de The MIDI Association](https://midi.org/summary-of-midi-1-0-messages).

## Extremos de registro y antialias

La frecuencia base usa `440 × 2^((nota−69)/12)` Hz antes
de rangos, afinación y CV. El banco de ondas conserva su
límite armónico de 20 kHz. Entre 20 y 22 kHz aplica un
descenso lineal de amplitud de la fundamental hasta cero.
Por encima del corte de 22 kHz del FIR a 48 kHz, se
conserva la fase módulo un ciclo y se silencia esa fuente.
Así se evita plegar una fundamental ultrasónica cuando se
combinan las teclas superiores, el selector de rango y
CV o bend. [Banco de osciladores](BANCO_OSCILADORES_TOCABLE.md).

## Verificación

`python -B tools/check_rf_d_playable_voice.py` verifica por
bits las notas solapadas, el pedal, los canales ajenos y
las particiones de 127, 128, 480 y 4096 frames. El banco
mide el retorno a la nota alta al soltar la baja, el corte
de contorno frente al release normal y la afinación en
ambos extremos MIDI dentro de banda. RackForge recibe la
misma secuencia con notas, pedal y corte por canal y se
compara con el render directo de WASM. La secuencia incluye
256 eventos en un frame, el límite del slot.

A 128 frames los dos pases offline de RackForge dieron
picos de 0,239 y 0,196 ms, dentro del margen de 1,333 ms.
El audio coincidió por bits con WASM también a 480 y 4096
frames. Los extremos medidos fueron 32,703 Hz para MIDI 0
en 2′ y 12.543,854 Hz para MIDI 127 en 8′.

En el primer pase, `[8001, 0xb0, 64, 64]` llegó al
adaptador de automatización del banco como el índice 44
de A‑440. El ABI rechazó el valor fraccional del switch
con estado −1. La secuencia corregida marca CC64 como
MIDI literal y conserva el valor, el frame y los umbrales.

La primera prueba de silencio fuera de banda dejaba el
oscilador mezclado antes de Note On. El estado del filtro
produjo un transitorio al abrirse el VCA. El banco conserva
esa secuencia y mide su cola. El contraste de silencio
abre el mezclador en el mismo frame en que entra la nota
fuera de banda, con el filtro aún en reposo.

`--control-inputs` reconstruye el perfil previo de jacks
traseros. Las pruebas son offline y quedan pendientes la
escucha y el controlador físico.
[Resultados](../evidence/rf_d_voice_development07.json).
