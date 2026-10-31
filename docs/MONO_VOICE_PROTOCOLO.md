# Voz monofónica y presupuesto de audio

Protocolo previo, 2026-10-31. Objetivo: cerrar una API de voz por bloques
con notas, legato, liberación y salida de audio, y medir su coste real.
Reutilizar pitch_program_startup/voice/output sin cambiar sus ecuaciones,
contornos, gatillo, cargas, tolerancias, interpolación o FIR. Esta ruta
usa el ciclo nominal transpuesto, no la nueva familia H128 CV/BUS. Es
una voz experimental de un oscilador; no el panel completo de tres VCO.
SVC-9, revisión CA3046/SVC-204D y fuentes del protocolo PITCH_PROGRAM
siguen siendo el objetivo. No introducir otra revisión o ADSR genérico.

## Contrato

48 kHz mono, bloques de 1..128 muestras, eventos ordenados con offset
de muestra dentro del bloque. Notes MIDI 0..127; NoteOn sólo si su
frecuencia 440*2^((n-69)/12) Hz cae en [f0/2,2*f0] del adaptador anterior.
El mapeo temperado es extensión del host, no calibración del teclado.
Prioridad a la nota más baja, single trigger: legato conserva KEY ON;
NoteOn de velocidad cero equivale a NoteOff. Velocidad no altera ganancia.
AllNotesOff libera KEY y conserva fase/cargas. No sustain, pitch bend,
modulación o velocidad acústica admitidos. Documentar límites en la API.

DC propio antes del procesamiento. Estado fijo, sin asignación, IO, locks,
logging o lecturas de reloj dentro de render_block. Eventos inválidos
rechazan bloque completo; fallo numérico no publica estado/audio parcial.
El Workspace es scratch reutilizable, nunca estado audible. Mantener
fase al cambiar nota, carga de todos los capacitores y anillo FIR.

Reloj eléctrico anterior, TICK=125 ns/65536. Frontera MIDI/sample N se
redondea hacia arriba al múltiplo de8 ticks, error <8*TICK (~15.259 ps).
El semipaso mínimo conserva MIN_DT=4 ticks de chain_charge.
No avanzar por delante del final conocido del bloque. Integración cortada
en eventos, rejilla anterior de125 us y fin de bloque; máximo .5 us.
FIR centrado existente, latencia causal explícita48 muestras (1 ms).
Primeras48 salidas cero; no normalizar ni ocultar cómputo con prerender.

## Verificación antes de medir

Controlador: prioridad baja, duplicados, retorno a nota retenida, legato,
velocidad cero, all off, rechazo de notas fuera de dominio y eventos
fuera de orden/rango. Comparar fase anterior/nueva en cada cambio.
Bloque inválido deja estado y salida por bits, incluido cero con signo.

Escena real: KEY ON muestra48 con nota69; nota67 legato muestra96,
NoteOff67 y retorno69 muestra144, KEY OFF69 muestra192, segundo ataque
nota72 muestra288, OFF72 muestra336. Audio hasta480 muestras (10 ms). No declarar liberación
asentada en10 ms; los contornos/cola larga de la ruta anterior se heredan.
Comparar bloques64/128 por muestra y estado y refinamiento .5/.25 us.
Gates de audio anteriores: RMS relativo .001, máximo/pico .003,
media <=1 uV; cerca de cero usar absoluto1 uV. Pre-KEY absoluto1 uV.
Newton <=1 pA/2 nV, estimador<=1. Contraste adicional contra el productor
anterior para el mismo programa KEY/Hz; historia inicial independiente
por DC propio, misma fuente nominal declarada. No nuevo oráculo VCO.

## Coste

Build release directo con compiler/rlib congelados; registrar flags,
máquina, SO, estado de energía disponible y número de voces. Cronómetro
externo alrededor de cada render_block completo, sin IO en el intervalo.
Medir DC por separado, heap, invocaciones, pasos, iteraciones/intentonas,
duración de cada bloque, percentiles observados y peor bloque. Presupuesto
N/48000 segundos para64/128; objetivo de una voz <=50% del presupuesto,
ningún bloque observado >100%. Si falla, registrar RT rechazado; no
extrapolar una admisión desde media, cero heap o un microbenchmark.
La muestra corta identifica coste, no garantiza WCET o ausencia de xruns.
Warm-up y comparación/repeticiones se etiquetan; no omitir el arranque.

Un tmp/lab-current; sin Cargo/rlib/cache/WAV nuevo. Recibos <=8 MiB sin QA.
Procesos <=240 s inicialmente; si la voz requiere más, guardar progreso
y medir un prefijo acotado antes de ampliar explícitamente el presupuesto.
Conservar fallos y replay idéntico con fuentes antes de corregir.
Entradas privadas anteriores protegidas; rehash compiler/rlib usados.
