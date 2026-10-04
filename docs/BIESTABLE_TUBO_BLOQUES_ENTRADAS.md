# Corpus de comparación dirigida del primer tubo

El [productor](../tools/loudness_latch_bdf_static_precision_startup_blocks_inputs.py)
amplía la auditoría con los nueve modos del tubo y su recibo primario.
Recibo aceptado, helper, dos pruebas y validator se fijan en `302cfc2`;
datos y resumen del corpus, en `d17ca21`, antes de validar.

Se reconstruyen **472 entradas de 82 informes**, con **113 hashes propios**
(82 informes y 31 helpers). Se conservan exactamente las tres excepciones
históricas LF→CRLF y las **trece versiones fallidas anteriores**. No se
introduce otra versión fallida en este corte: ocho regresiones primarias
y dos del corpus pasan al primer intento. Fuentes, datos y gates anteriores
permanecen intactos, incluidos los tres rechazos escalares del primer tubo.

Las dos pruebas del corpus pasan en **74,2571515 s**, con entradas idénticas
antes/después. Reconstruyen bytes desde blobs, verifican hashes, fuentes
fallidas identificadas y los nueve modos del nuevo banco. Comprueban
selección [1,2], un único cierre, ocho rechazos, duración certificada igual
al primer soporte real, cero solves/precondicionadores nuevos y gates
globales abiertos. La suite primaria pasa en **90,6609469 s**.
[Recibo primario](../evidence/loudness_latch_bdf_static_precision_startup_blocks_validation.json)
y [recibo de corpus](../evidence/loudness_latch_bdf_static_precision_startup_blocks_inputs_validation.json).

[Datos](../evidence/loudness_latch_bdf_static_precision_startup_blocks_inputs.json.gz):
**382283 bytes**, SHA comprimido
`011381ed8e748f7a9e09051f8ecf963847ae89c0acdb4c0c8f929b989710f899`,
canónico `c326daf9306c1ee8a211f5997b7e3f09102667364d7e2b381c9ff1fbc6714387`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_startup_blocks_inputs_summary.json).

La recuperación de bytes no prueba portabilidad entre plataformas ni
identificación vintage. El [resultado](BIESTABLE_TUBO_BLOQUES_RESULTADOS.md)
certifica únicamente el primer intervalo nominal; 1 mV global, voz completa,
física y deadline requieren evidencia independiente.
