# Productor offline con cuota y un paso pendiente

## Dominio y contrato antes del ensayo

Misma escena CA3046/SVC-204D, leyes SVC-9 pp.9/19/13/10, motor,
inicializador, cargas, coeficientes, nivel y relojes de la
[salida continua](STREAM_OUTPUT_PROTOCOLO.md). No hay nuevos parámetros
sonoros. KEY ON 1 ms, OFF 200 ms, máximo full 2 us, grilla 125 us.
El final es un múltiplo de 125 us entre 125 us y 301 ms; los finales
cortos son prefijos de laboratorio. El reloj termina sin rellenar el FIR.

El productor posee estado HIGH/LOW, reloj eléctrico, propuesta adaptativa,
próxima grilla, Pipeline y como máximo un old/Accepted pendiente. El
workspace se presta por llamada: scratch, no memoria física. cold_start
resuelve DC antes de pump; su coste no está cubierto por la cuota.
from_initial comprueba representación y tiempo cero, no certifica DC.

Cada llamada declara cuota de invocaciones de voice::advance, incluyendo
una que falle. Una invocación contiene Newton, line search y hasta 32
reintentos: esta cuota NO acota tiempo de CPU ni demuestra deadlines.
Retornar cantidad escrita, invocaciones, pasos publicados y motivo:
cuota, capacidad, final o fallo eléctrico. En un fallo devolver el progreso
parcial ya publicado, conservar diagnóstico y bloquear futuros avances;
no ocultar el error como falta de capacidad. Sin rollback global implícito.

Después de resolver un paso, el reloj/estado eléctricos pueden adelantar
al lector exactamente ese Accepted. Siempre intentar entregarlo antes de
otra integración. Si falta espacio, conservar todos sus campos sin
recalcular, descartar, duplicar o alterar eventos. Entrega atómica del paso;
la llamada completa puede haber publicado pasos previos. Una cuota cero
puede entregar un pendiente, pero no iniciar una integración. Sin pendiente
es no-op. Salida vacía puede consumir pasos que no producen Frame; debe
parar conservando el primero que necesite espacio. Retener índices de
fuente y disponibilidad del FIR, sin compensación nueva de latencia.

Clone copia todos los campos persistentes, incluyendo old, coarse/fine,
incrementos, etapas, h/error/intentos y contadores. No serializar dentro
de pump ni copiar el workspace como si fuera memoria física.

## Gates fijados

- Tres recorridos reales 0–10 ms, KEY ON 1 ms: cuotas/capacidades distintas,
  incluyendo cuota cero, salida cero, pausas, primer Frame y reanudación
  de pendientes. Cada uno termina en 5170 pasos, 3841 entradas y 433 Frames;
  mismos bits/índices que el prefijo AA8 archivado. Estado final y Pipeline
  iguales a la referencia de salida continua; no otra integración larga.
- Control independiente paso a paso en el primer recorrido: comparar cada
  Accepted completo y estado HIGH/LOW, h/error/intentos/iteraciones. Newton
  <=1 pA/2 nV y estimador <=1; no nuevas filas originales por esta unión.
- Forzar pendientes en el primer Frame y atravesando KEY: con capacidad
  cero repetir llamadas sin resolver otro paso ni cambiar campos/sentinelas.
  Drenar con cuota cero; ramas Clone y workspace nuevo deben dar los mismos
  bits. Probar final idempotente y fronteras de KEY OFF mediante prueba
  sintética del planificador, sin atribuirle un circuito de 200 ms simulado.
- Fallo de solver inyectado en prueba unitaria: conservar progreso, estado
  previo al solve fallido, diagnóstico y no volver a resolver al reintentar.
  No cambiar leyes o gates del solver para hacer pasar la prueba.
- Heap cero en pump/Clone medido, estado persistente <=48 KiB; declarar
  workspace aparte y no llamar sizeof pico total de stack o prueba RT.
- Compiler/rlib congelados, referencias previas por SHA256. Preservar fallo,
  fuentes e inputs y replay sin cambios antes de corregir. Recibos <=8 MiB
  sin QA; tmp/lab-current vacío al terminar, sin nuevo WAV/cache/Cargo/rlib.
  El WAV anterior se conserva por hash; no nuevos inputs sonoros privados.

No admisión de tiempo real, VCO físico completo, tres osciladores, MIDI,
CV general o fidelidad frente a un Model D físico.
