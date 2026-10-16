# Salida continua por bloques, historia y latencia

## Dominio conservado

Misma escena CA3046/SVC-204D y leyes SVC-9 pp.9/19/13/10 de la
[nota admitida](LONG_NOTE_AA_PROTOCOLO.md). No cambiar motor, fuente,
inicializador, cargas o coeficientes FIR. Extensión de entrega de audio:
lector racional 384 kHz y FIR de 769 coeficientes hacia 48 kHz. Mantener
voltios, orden de acumulación, prehistoria izquierda y todas las memorias.

Un anillo fijo contiene las 769 últimas muestras; no almacenar la nota
completa. Inicializar el anillo con J7 inicial constante y consumir la
muestra inicial exactamente una vez. Publicar la muestra de fuente n sólo
cuando exista la entrada real i=8n+384. Es la misma convolución centrada
offline, con disponibilidad causal 1 ms posterior: 384 muestras de entrada
o 48 de salida. No rellenar el futuro con ceros ni mover KEY para ocultarlo.
Separar índice de la muestra de fuente e índice de entrada que la habilita.

El lector continuo recibe Accepted contiguos del motor admitido. Conserva
HIGH/LOW de 118 nodos para comprobar el empalme, sin realimentar el FIR.
Máximo full 2 us y dominio temporal hasta 1000 s, ya impuesto por la fuente
nominal. En ese paso cabe como máximo una muestra nueva de 384 kHz.
La capacidad del consumidor puede ser cero si no hay muestra de salida;
si falta un hueco necesario, rechazar sin consumir etapa, historia o audio.
Snapshot/reanudación en memoria mediante Clone, sin serde en procesamiento.
Después de un rechazo por capacidad, el productor conserva old/Accepted y
los reintenta antes de avanzar otro paso. La API de lectura no revierte
el estado eléctrico que el productor ya calculó ni permite descartar ese
paso pendiente. El consumidor reserva como máximo un Frame por Accepted.

## Gates previos al ensayo

- Ambos RAW archivados de 301 ms, máximos 2/1 us: entrega escalar, bloques
  irregulares y bloques 127/128/129. Las 14401 muestras y sus metadatos
  deben coincidir por bits con la salida AA8 admitida y entre particiones.
  No integrar otra nota larga para probar sólo una representación de salida.
- Ramas de snapshot/reanudación, bloques vacíos y fronteras de anillo deben
  conservar muestras, orden y contadores. Rechazos atómicos de capacidad,
  primer valor incompatible, no finitos/dominio y continuación inválida;
  retry exacto. Canal de salida sin escrituras parciales ante error.
- Camino completo real 0–10 ms, KEY ON 1 ms, máximo 2 us: lector continuo
  y lector de nota completa sobre dos integraciones independientes del
  mismo motor. Estados HIGH/LOW, h/error y muestras iguales por bits;
  contraste adicional con el prefijo RAW/AA8 de la nota de 301 ms archivada.
  Newton <=1 pA/2 nV, estimador <=1. Se hereda la auditoría original por
  identidad del motor y las etapas; no declarar nuevas filas originales.
- Heap cero medido en push/append y avance. Tamaño del estado <=12 KiB
  para decimador y <=16 KiB para la unión con lector; declarar sizeof,
  sin presentarlo como pico total de stack o mejora de deadline.

Un mismo punto de salida se publica una sola vez, aun al cortar bloques
en KEY o al reanudar. Al llegar a 301 ms hay 14401 puntos (cuerpo más ancla),
sin flush con ceros. El llamador decide el cuerpo semiabierto del bloque.

Preservar fallos, fuentes e inputs y repetir el gate sin cambios antes de
corregir. Compiler/rlib congelados; un tmp/lab-current vacío al terminar.
Recibos <=8 MiB sin QA, referenciando el RAW previo por hash en lugar de
duplicarlo. Conservar el único WAV admitido por hash, sin nuevas muestras,
Caches, Cargo o biblioteca. No admitir RT, MIDI, CV general o parecido físico.
