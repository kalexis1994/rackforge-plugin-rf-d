# Corpus de forcing firmado y restitución de memoria

El [productor](../tools/loudness_latch_bdf_static_precision_signed_memory_inputs.py)
añade el informe de C7, su recibo primario y el recibo anterior del corpus
dirigido. Este último incorpora explícitamente las dos fuentes fallidas
propias de ese corte, con su versión final identificada. Recibo primario,
helper, tests y validator se congelan en `67be1ab`; corpus y resumen,
en `747d467`, antes de validar.

Se recuperan **564 entradas de 97 informes**, con **134 hashes propios**
(97 informes y 37 helpers), tres excepciones históricas LF→CRLF y
**quince versiones históricas de pruebas fallidas**. Las dos versiones
antes almacenadas en el recibo propio ahora tienen entradas explícitas
dentro de este corpus. Ningún archivo o informe anterior se modifica.

## Validación

Las ocho pruebas primarias pasan al primer intento en **66,8599714 s**;
las dos del corpus, también al primero, en **97,8725673 s**. Son **diez
pruebas nuevas aceptadas**, sin correcciones de fuente o datos en este corte.
Los recibos verifican entradas idénticas antes/después. Se reproducen las
16 inversas y acciones reutilizadas, 128 compensaciones, continuidad,
cierre, selección [1,1] y restitución de memoria antes de transporte.

El test conserva todos los bancos anteriores, incluido el prefijo dirigido
con primer hueco en índice 6 y sus dos errores de registro. El nuevo
informe admite ese séptimo soporte mediante otra ecuación auxiliar de
prueba; no reescribe el informe rechazado ni su selección. La particular
candidata, Bp, restos independientes y restitución quedan separados.

[Recibo primario](../evidence/loudness_latch_bdf_static_precision_signed_memory_validation.json),
[recibo del corpus](../evidence/loudness_latch_bdf_static_precision_signed_memory_inputs_validation.json)
y [resultado](BIESTABLE_FORCING_C7_RESULTADOS.md).

## Archivo

[Datos](../evidence/loudness_latch_bdf_static_precision_signed_memory_inputs.json.gz):
402546 bytes, SHA comprimido
`65950de4c42843b09dadf536abe888c8a005cdfa3ceac2c53e96abf7e4586ba0`,
canónico `638592d1a8c5771911465de3f69d368936be0edf7f1d0bda52c3923ce62624da`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_signed_memory_inputs_summary.json).

La auditoría final recupera las 564 entradas y 134 hashes propios desde
Git y verifica las quince fuentes fallidas. Helper, productor y protocolo
coinciden con `33c11a3`; datos con `c063e31`; corpus con `747d467`.
Atributos Git, fuentes de acción y evidencia anterior coinciden con
`0a6efa0`. Gates e integrador original permanecen intactos.

Recuperar bytes no prueba otro BLAS/SO ni fidelidad sonora. Se admite sólo
el prefijo nominal de siete soportes hasta ≈12,5 µs, error nodal ≤0,793 µV.
Trayectoria completa, meta global de 1 mV, identificación física, voz,
audio, motor nativo y deadline conservan sus gates independientes.
