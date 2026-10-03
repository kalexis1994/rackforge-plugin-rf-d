# Corpus de comparación dirigida de bloques

Se amplía el corpus a **55 informes y 324 entradas**: **321 blobs idénticos**
y las tres excepciones históricas LF→CRLF. Se conservan ocho versiones
fallidas anteriores de tests. La referencia de reconstrucción es
`b34f19eaf9fab342115c5b62df571fb3d188cdc1`; helpers, pruebas y validador se commitearon
antes de generar. Los atributos Git, gates y datos anteriores no cambian.

Se añade el informe de comparación dirigida y su recibo. Las fuentes
incluyen los certificados anteriores de celdas y su corpus reconstruido,
así como la partición, serie positiva, núcleos y protocolo de este bloque.
Los destinos nuevos son propios y se verifica que no colisionen con
entradas, informes anteriores ni entre datos y resumen. Se conserva y
verifica también el primer archivo rechazado del bloque anterior, su
fuente, revisión, SHA y la restauración exacta del resumen histórico.
No hubo archivo rechazado ni test fallido en este bloque.

[Datos](../evidence/loudness_latch_bdf_static_precision_block_inputs.json.gz):
**356128 bytes**, SHA comprimido
`91c989726181fdbea1a95153353bd95196ff72411d1343ee038a81f0615bde54`,
SHA canónico `9c77f958bfa36180d853cb74c7dbdb905f1c0242a2c139a18fc6c6f4efdbd246`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_block_inputs_summary.json).

La [suite](../tests/test_loudness_latch_bdf_static_precision_block_inputs.py)
pasa **2/2 al primer intento**, 59.3192288 s. Reconstruye todos los
blobs, materializa excepciones, contrasta SHA, esquemas, versiones, destinos
y bytes canónicos; rechaza identidades alteradas. El [recibo](../evidence/loudness_latch_bdf_static_precision_block_inputs_validation.json)
conserva comandos, entorno, salidas y SHA antes/después idénticos.

El bloque suma **ocho regresiones nuevas**, todas pasan al primer intento:
seis de comparación y dos del corpus. La recuperación de archivos no
certifica error temporal del DAE, anclaje, recorrido completo, incertidumbre
física, audio o deadline. **1 mV global sigue abierto.**

```powershell
python tools/loudness_latch_bdf_static_precision_block_inputs.py
python tools/validate_bdf_static_precision_block_inputs.py
```
