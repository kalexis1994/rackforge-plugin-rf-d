# Escena larga del programa experimental

Protocolo previo a medición, 2026-10-17. Continúa
[programa de fase](PITCH_PROGRAM_PROTOCOLO.md) y
[render nominal](NOMINAL_RENDER_PROTOCOLO.md). Misma revisión CA3046/SVC-204D,
red SVC-9 pp.5/19, unidades eléctricas, motor, cargas y FIR admitidos.
Ninguna calibración de CV/MIDI ni nueva evidencia de fidelidad física.

## Escena y representación

Una sola voz. f0 nominal al inicio; KEY ON en 1 ms; 1.5 f0 en 100 ms;
0.5 f0 en 200 ms; KEY OFF en 250 ms conservando esa frecuencia.
Legato en los dos retunes: fase continua, sin reiniciar contornos o cargas.
Cuerpo 0–300 ms a 48 kHz (14400 frames); soporte eléctrico real hasta
301 ms y un anchor adicional en 300 ms. 384 kHz RAW, mismos FIR 769/385.
El soporte de 1 ms no se rellena con silencio ni con muestras repetidas.
Sin ganancia, normalización, fade o dither; 1 V = 1 FS, float32 mono.

Derivar RenderSession y WavSink de la versión nominal mediante reemplazos
exactos. Cambiar sólo constructor/programa/perfil y entrada al productor;
conservar collect, relojes, header, preflight y tratamiento de fallos IO.
La sesión no hace IO/heap/logging. Cuotas son invocaciones, sin promesa RT.
Validar body_ms 1..300 y end=(body_ms+1) ms antes del DC.

## Gates predeclarados

- Dos historias completas e independientes con máximos 1 y 0.5 us.
  No trasladar automáticamente la admisión del programa de 24 ms.
  Newton <=1 pA/2 nV, estimador <=1, heap cero medido en pump.
  Eventos exactos, HIGH/LOW de 118 nodos conservados.
- RAW 115585; AA8 y AA4 14401 incluyendo anchor. Todos los frames/índices
  del streaming iguales por bits a batch AA8 de la misma historia.
- Refinamiento temporal sobre AA8: RMS relativo <=.001, máximo/pico
  <=.003, media <=1 uV. Ventanas: conjunto [0,14401), primer tono
  [48,4800), tono alto [4800,9600), bajo [9600,12000), liberación
  [12000,14401). Pre-KEY [0,48): diferencia máxima <=1 uV.
- Refinamiento de tasa AA4/AA8 de cada historia: mismas ventanas,
  RMS relativo <=.0001, máximo/pico <=.0003, media <=.1 uV.
  No generalizar estos gates a ausencia universal de alias.
- Cancelar un Clone después del primer retune; ningún solve, frame,
  progreso o estado eléctrico cambia; cancelación terminal. El original
  sigue su trayectoria. Verificar cuota cero sin resolver al inicio.
- WAV de cada historia idéntico a la conversión float32 batch; header
  validado independientemente. Publicar únicamente el perfil fino tras
  superar todos los gates. El wrapper público valida el hash admitido
  antes de os.replace en el mismo volumen. Probar cancelación real con
  proceso, preservando WAV anterior y dejando laboratorio vacío.
- Añadir un test de incompatibilidad body/programa (sin integrar);
  heredar las pruebas del sink mediante identidad exacta de sus bytes.

## Almacenamiento y publicación

Un tmp/lab-current, archivos propios fijos, vacío al terminar. Congelar
compiler/rlib. Recibos <=8 MiB sin QA; salidas completas comprimidas,
fallos con fuentes/inputs y replay sin cambios antes de corregir.
No repetir trayectorias anteriores ni añadir bibliotecas/Cargo/cache.

La escucha actual nominal es una vista regenerable, fuera de los 8769
inputs privados admitidos. Sólo tras PASS sustituir su contenido en
artifacts/rf-d-nominal-current.wav por esta escena, documentando hash
anterior/nuevo y regeneradores. El nombre histórico del archivo sigue
designando una única escucha actual. Los recibos originales y fuentes
permanecen inmutables; export_long_note_aa.py recupera el tono anterior.
La escena nueva se puede recuperar de su recibo sin integrar otra vez.
No acumular WAVs ni ejecutables. No declarar nuevas filas originales,
plugin tocable o VCO físico general por este render.
