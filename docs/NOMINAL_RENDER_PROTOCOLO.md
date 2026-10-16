# Render nominal desde DC hasta un único WAV

## Contrato previo al ensayo

Misma escena CA3046/SVC-204D y leyes SVC-9 pp.9/19/13/10 admitidas:
[nota/FIR](LONG_NOTE_AA_PROTOCOLO.md), [productor](OFFLINE_PRODUCER_PROTOCOLO.md).
El WAV actual procede del perfil fino full máximo 1 us, no del máximo
2 us del productor. Conservar ese perfil usando su seam interno para
limitar la propuesta que recibe voice::advance a 1 us. El productor aún
posee el Accepted completo; no modificar sus bytes, leyes o estimador.
Contrastar por bits con la referencia fina, sin tratar ambos perfiles
como el mismo archivo. No nuevos parámetros sonoros o entradas privadas.

RenderSession une cold_start, productor, cancelación terminal entre cuotas,
progreso eléctrico/consumido y cuerpo semiabierto. Conservar una muestra
ancla separada del cuerpo: 300 ms/14400 frames y futuro real hasta 301 ms,
14401 puntos leídos. Lectura 384 kHz, FIR 769 taps a 48 kHz, 1 ms de
latencia de disponibilidad; sin ceros futuros, normalización, fade o dither.
El único WAV float32 mono usa 1 V=1 FS y el header fmt/fact/data previo.
Una cuota cuenta llamadas adaptativas, no tiempo de CPU; DC queda fuera.

El core no hace IO, logging o heap en pump. Un sink WAV separado escribe
fuera de pump, comprueba orden/índices/nivel finito y cuerpo completo.
Un error de escritura es terminal: no reintentar bytes ambiguos ni
publicar un fragmento. Al cancelar conservar estado/pending/progreso en
memoria, sin más solves o salida. No es reanudación desde disco.

La herramienta pública sólo publica artifacts/rf-d-nominal-current.wav.
Compila con compiler/rlib congelados en tmp/lab-current; exige área vacía
y propiedad exclusiva, rechaza enlaces y no limpia archivos ajenos.
Escribe el resultado provisional allí. Ctrl+C solicita cancelación por
flag, comprobada antes/después del DC y entre cuotas. No promete interrumpir
un Newton o una inicialización. Verificar salida terminada, formato/conteos
y SHA admitido antes de os.replace en el mismo volumen. Cancelación/fallo
mantiene el WAV anterior; retirar provisionales después del recibo.

## Gates

- Un prefijo real de 9 ms de cuerpo +1 ms de soporte, con cuotas/capacidades
  variables: 10 ms físicos, 432 frames exportados y ancla 433. Valores
  float64 e índices iguales por bits al perfil fino archivado; WAV float32
  completo igual al header/payload independiente. Reanudar un Clone y
  cancelar su rama en el primer Accepted pendiente: sin solves/entrega
  extra y memoria intacta. Final idempotente, progreso monótono y heap
  cero medido sólo en pump/Clone. sizeof separado del workspace.
- Tres tests nuevos: cuerpo/ancla y cancelación terminal; preflight de
  frames sin bytes parciales por error de entrada; escritura incompleta
  inyectada y final obligatorio. Tests heredados no reejecutados.
- Ejecución real del entry point completo: cold_start hasta 301 ms, cuota
  128, máximo full 1 us. 301151 Accepted, 115585 entradas, 14401 observados,
  14400 exportados; WAV exacto al SHA previo. Esta nueva trayectoria larga
  se justifica por validar el ciclo completo, no sólo representación.
- Ejecutar el wrapper con cancelación anterior al DC y después del primer
  progreso, y fallo de proceso/publicación inyectado: nunca reemplazar
  el destino; limpiar sólo sus propios temporales. Invalidar argumentos y
  área ocupada antes de compilar. Guardar recibos acotados y replay de
  cualquier fallo no esperado antes de corregir fuentes/adaptadores.
- Conservar fuentes/inputs/SHA previos, un único WAV sin variantes retenidas,
  sin Cargo/cache/rlib nuevos. tmp/lab-current vacío al terminar, recibos
  nuevos <=8 MiB sin QA. No afirmar nueva auditoría original o parecido
  físico, tres VCO, CV general, MIDI o tiempo real.

## Corrección del oráculo de conteo antes de repetir

El primer ensayo y su replay fallan al exigir 10151 pasos en el prefijo
10 ms: es una extrapolación incorrecta de los 301151 de la nota completa.
No es un gate de error del circuito. Se conserva el recibo native01 y
sus fuentes; las muestras float64 ya comparadas no fallaron.
Sustituir esa constante por un control independiente 0–10 ms, con el
planificador fino anterior de máximo 1 us. Exigir conteo, estado HIGH/LOW
y Pipeline finales idénticos por bits, además de la comparación archivada.
Mantener Newton <=1 pA/2 nV, estimador <=1 y el gate completo 301151.
No cambiar el core, el integrador o el WAV para acomodar el conteo.
