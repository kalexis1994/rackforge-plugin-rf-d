# Corpus del prefijo de 22 grupos

El [productor](../tools/loudness_latch_bdf_static_precision_fine_prefix_inputs.py)
añade el prefijo con memoria individual y su recibo primario. Recibo
aceptado, helper, dos tests y validator se congelan en `1885181`;
corpus y resumen, en `2604901`, antes de validar.

Se reconstruyen **507 entradas de 88 informes**, con **122 hashes propios**
(88 informes y 34 helpers). Se preservan las tres excepciones históricas
LF→CRLF y las **trece versiones fallidas anteriores de tests**. Este corte
no añade un fallo de test: ocho regresiones primarias y dos del corpus
pasan al primer intento.

Sí conserva un lanzamiento numérico interrumpido al convertir para
diagnóstico una cota racional a float. Su fuente exacta y blob `5c4a0b1`,
fase y salida observada se identifican por SHA; el informe completo no
se guardó. La ejecución corregida queda ligada a `b7b3879`. Ese fallo
no se presenta como una versión fallida de test ni como un resultado
completo admitido. La selección primaria del banco fuente sigue intacta.

Las ocho regresiones primarias pasan en **254,3650355 s**; las dos del
corpus, en **92,9207176 s**. Ambos recibos conservan entradas idénticas
antes/después. Las comprobaciones nuevas ligan el soporte secundario
[1,1], las 22 coordenadas, dos intervalos intentados y sólo uno añadido,
total de tres intervalos probados y primer hueco en índice 3. Verifican
32 recintos nuevos, 3168 consultas de tasa y 16 precondicionadores,
cero solves de trayectoria y sistemas de métrica, y todos los radios
rechazados del último soporte.

[Datos](../evidence/loudness_latch_bdf_static_precision_fine_prefix_inputs.json.gz):
**386217 bytes**, SHA comprimido
`0ee1dca048ed732ab5d503530fdb4ac6f83b3fca4f047e260538d58a4e979f17`,
canónico `37ec31f44fedc71a158d5c2de20c09516d333cd6b2636d63db9ed4463510bca3`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_fine_prefix_inputs_summary.json)
y [recibo](../evidence/loudness_latch_bdf_static_precision_fine_prefix_inputs_validation.json).

Una auditoría final recupera las 507 entradas y 122 hashes propios desde
Git, verifica las trece fuentes históricas y confirma los helpers y
protocolo congelados. Atributos Git, integrador y datos del corte anterior
permanecen intactos. Recuperar bytes no prueba portabilidad numérica,
circuito físico o sonido vintage. El [resultado](BIESTABLE_PREFIJO_22_RESULTADOS.md)
conserva aproximadamente 781,25 ns de error real certificado, sin admitir
el cuarto intervalo, el gate global de 1 mV, audio, motor nativo o deadline.
