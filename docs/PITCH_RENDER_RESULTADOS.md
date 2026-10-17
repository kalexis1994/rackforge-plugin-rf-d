# Secuencia experimental larga: resultado

2026-10-17. [Protocolo previo](PITCH_RENDER_PROTOCOLO.md),
[historias completas](../evidence/pitch_render_native02.json),
[publicación](../evidence/pitch_render_publication01.json) y
[QA](../evidence/pitch_render_tests01.json).

## Sonido y alcance

Cuerpo de 300 ms: KEY ON 1 ms, frecuencia f0 nominal, 1.5 f0 desde
100 ms, 0.5 f0 desde 200 ms, KEY OFF 250 ms. Retunes legato con fase,
contornos, puertos y cargas conservados. Soporte eléctrico hasta 301 ms.
14400 frames de cuerpo y un anchor; RAW 115585 por historia. La fuente
sigue siendo la transposición experimental de un ciclo nominal CA3046;
este resultado no identifica su respuesta física a otros CV o cargas.
Sin una unidad de referencia, no demuestra parecido audible vintage.

Desde la raíz:

```powershell
python -B tools/export_pitch_render.py
python -B tools/render_pitch.py --quota 128
```

El primer comando recupera la escucha desde el recibo, sin integrar.
El segundo integra la escena completa con máximo 0.5 us; es offline y
puede tardar muchos minutos. Ctrl+C cancela entre cuotas. La cuota cuenta
invocaciones adaptativas, sin presupuesto de CPU o promesa de tiempo real.

## Medición

Dos historias nuevas completas, máximos 1/0.5 us y 301151/602118
pasos aceptados. Coste completo del driver: 803.03/1690.56 s
en este banco; incluye solve/salida y no es un gate de deadline.
Newton <=1 pA/2 nV y estimador <=1. Heap cero medido
en procesamiento. Los 28802 frames de streaming con anchor coinciden
por bits con batch FIR en las dos historias. KEY/retunes se cortan en
sus ticks exactos; estados HIGH/LOW conservados en cada frontera.

Refinamiento temporal global y en las cuatro ventanas: peor RMS relativo
0.03458313 %, gate 0.1 %; máximo/pico de esa ventana
0.08426833 %, gate 0.3 %; media <=1 uV. El contraste
192/384 kHz separado pasa, peor RMS relativo 0.000009013 %,
gate 0.01 %. No es una demostración universal de ausencia de alias.
No se promovió el programa largo a partir de sus 24 ms anteriores.

Un test nuevo de incompatibilidad body/programa, 271 heredados y 272
cubiertos. Sólo se ejecutó el nuevo test; los tests de fase anidados se
filtraron. Colector, header WAV, preflight, escrituras parciales y flush
se heredan mediante identidad exacta de bytes. Las cancelaciones tardías
de Clone no resuelven ni modifican estado/salida/progreso; el original
continúa. Dos procesos reales cubren cancelación antes del DC y después
del primer progreso. Cabecera y payload alterados no se publican.
No se hizo una tercera integración larga para probar el wrapper: se
comparó su parser y ruta de publicación con la salida completa del mismo
driver auditado y con el WAV batch por bytes.

## Trazabilidad y almacenamiento

[Fallo de API](../evidence/pitch_render_native01.json) con replay de
compilación: el conversor batch devuelve unidad, no cantidad de muestras.
La [corrección acotada](../evidence/pitch_render_api_correction01.json)
no cambia gates o capacidades. También se conserva el
[prefijo fallido de preparación del wrapper](../evidence/pitch_render_wrapper_preparation_failure01.json)
y su replay: dos coincidencias de ruta exigían un reemplazo más preciso.
Los fallos no integraron audio. No se borraron evidencias admitidas.

La publicación reemplaza una vista regenerable fuera de los 8769 inputs
privados, manteniendo un único artifacts/rf-d-nominal-current.wav. Su
nombre histórico designa la escucha actual, ahora esta secuencia.
Hash anterior: `de9b9bed0e2842baa3d2a6df725281aa68a157cf35f675cc40dab84daf57b92f`.
Hash nuevo: `ff8f87596d71088340d0105f322b8b27ea643c10a900f856c28ede415a44b6f6`.
El tono fijo anterior se recupera con export_long_note_aa.py; sus fuentes
y recibos permanecen intactos. El renderer nominal conserva su admisión,
pero usarlo sustituye la vista actual por aquel tono fijo. Reexportar la
secuencia para volver a esta escena. Float32 mono 48 kHz, 1 V=1 FS,
sin normalización/fade/dither. El hash admitido precede al reemplazo
atómico en el mismo volumen. Fallo/cancelación preserva el WAV anterior.

Un único tmp/lab-current vacío al finalizar; ejecutable y candidatos
retirados. Compiler/rlib congelados, ningún Cargo/cache/input sonoro
privado nuevo, ningún nuevo contraste de filas originales o claim RT.
Siguiente: contrastar frecuencia/forma del VCO físico frente a CV y carga
fuera del punto nominal antes de promover esta transposición a emulación
general o control musical calibrado.

## Próximo dominio físico ya documentado

La [calibración de circuito anterior](../evidence/vco1_circuit_calibration_v1.json.gz)
y su [contrato](VCO1_CALIBRACION_PROTOCOLO.md) ajustaron dos trims a
220/1760 Hz, con CV de placa KEYBOARD -3.1/-0.1 V y otras cinco entradas
-2.1 V. R11=521.3126579373712 ohm, R8=0.2613404652606161; los puntos
reservados dan 439.142719257546 y 877.8409055657653 Hz (3.37637/4.25283
cents frente a 440/880), dentro del gate de laboratorio de 5 cents.
Es una referencia documental SPICE, no una unidad medida o ley MIDI.

El ciclo transpuesto en este bloque conserva R11=500 ohm y R8=.5, con
f0=410.801335673881226 Hz. No mezclar esa forma/puerto con los trims de
la calibración como si fuera la misma historia. El paso siguiente es
contrastar la ruta portable con aquellas fronteras y trims explícitos,
incluyendo forma/reset/corrientes y carga, antes de reducir una familia
de ciclos o responder dinámicamente a CV. No ajustar los puntos reservados
por nota para esconder el error de interpolación.
