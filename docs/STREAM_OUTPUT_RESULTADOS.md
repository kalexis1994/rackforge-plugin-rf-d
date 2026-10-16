# Salida continua con memoria fija y reanudación

## API y contrato temporal

[Protocolo](STREAM_OUTPUT_PROTOCOLO.md),
[implementación](../crates/rf-d-circuit/src/j7_stream_output.rs) y
[ensayo nativo](../evidence/stream_output_native01.json).

`Decimator::push` consume bloques de voltios a 384 kHz y conserva un anillo
de 769 posiciones. `Pipeline::append` une el mismo lector racional Radau
con ese anillo, manteniendo también el último estado HIGH/LOW completo.
No cambia motor, fuente VCO, coeficientes, nivel, puertos o cargas.
La fórmula escalar se contrasta estructuralmente con la ya admitida.

Cada `Frame` lleva `source_index`, `ready_input_index` y `voltage_v`.
El frame n está disponible al recibir la entrada 8n+384: 1 ms de retardo
real, 384 entradas o 48 frames de salida. La primera muestra de fuente se
publica después de la entrada 384; no se inventa futuro o flush con ceros.
La API no mueve KEY ni anuncia compensación de latencia en un host.

La muestra inicial se consume una sola vez. El anillo usa la misma
prehistoria DC izquierda y orden de acumulación que el FIR de nota completa.
Un bloque vacío es un no-op. Si falta capacidad para producir un frame,
el consumidor rechaza sin consumir muestras, etapa ni historia. El productor
conserva old/Accepted para reintentarlos antes de integrar otro paso;
el lector no revierte un estado eléctrico ya calculado por el productor.

## Equivalencia sobre la nota admitida

Se recuperan por hash los RAW y AA8 de los perfiles 2/1 us de 301 ms,
sin duplicarlos en otro recibo ni volver a simular esas notas. Dos perfiles,
tres particiones cada uno: escalar, irregular con vacíos y 127/128/129.
Las **14401 muestras por replay** coinciden por bits con AA8, incluidos
índice, orden y momento de disponibilidad. No se duplica el ancla final.

Se fuerzan fronteras antes/después de la primera publicación y en KEY OFF.
30 ramas de snapshot/retry y reanudación conservan muestras y contadores;
18 rechazos por capacidad y 70 bloques vacíos, heap cero. La reanudación
usa el estado clonado completo, no un reset del FIR o de fase de lectura.

Dos tests Rust nuevos: dominio/primer valor/capacidad y recuperación DC;
último punto legal del contador de 1000 s y rechazo atómico del siguiente.
Este último es una fixture de contador con historia DC coherente; no se
afirma haber integrado un circuito durante 1000 s. Los dos tests históricos
del FIR quedan excluidos de esta ejecución y se heredan por identidad.

## Unión real con el circuito

Dos integraciones independientes 0–10 ms, mismo DC/KEY ON 1 ms y máximo
2 us. Una alimenta la salida continua y la otra el lector anterior.
**5170 pasos** por trayectoria: estados HIGH/LOW, etapas/incrementos
coarse/fine y h/error iguales por bits en todos los pasos. Los 3841 puntos
RAW y 433 frames disponibles coinciden además con el prefijo archivado
de 301 ms y con la convolución anterior. No se cambia la historia eléctrica.

Seis rechazos de continuación, tres por capacidad y seis retries exactos,
con salida intacta y heap cero. Máximos Newton 0,999768 pA/1,995961 nV,
estimador 0,958473 y mínimo full 3,90625 ns; se mantienen gates 1 pA/2 nV
y error <=1. No se reejecuta la auditoría de 11662 filas originales ni se
declaran filas nuevas: se hereda por identidad del motor y sus entradas.

## Tamaño, alcance y conservación

`sizeof(Decimator)` **6168 bytes**; `sizeof(Pipeline)` **8080 bytes**.
El anterior `Buffer<115585>` mide 926592 bytes. La nueva historia de salida
es fija y no crece con la duración de la nota. Son tamaños de objetos,
no el pico de stack, un ahorro medido de CPU o una admisión de deadlines.
El solver sigue necesitando su propio workspace y sigue siendo offline.

[QA global](../evidence/stream_output_tests01.json): 4300 fuentes anteriores
y 8769 inputs privados protegidos; 259 tests anteriores heredados por
identidad y dos nuevos ejecutados. Un tmp/lab-current vacío al terminar;
sin Cargo, rlib/cache, WAV o carpetas de muestras nuevas. Se conserva por
hash el único WAV de 300 ms de la referencia, sin modificar su recibo.

Se admite entrega continua de esta escena nominal y su latencia explícita.
No es todavía un callback del host, MIDI, CV general, tres VCO o parecido
demostrado con hardware. Siguiente: integrar el productor/consumidor y su
paso pendiente en un ciclo de ejecución offline con control de trabajo,
antes de ampliar controles o afirmar tiempo real.
