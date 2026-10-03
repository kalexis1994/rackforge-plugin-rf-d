# Corpus del certificado espectral de junturas

Se amplía la reconstrucción a **59 informes y 346 entradas**:
**343 blobs idénticos** y las tres excepciones históricas LF→CRLF.
Conserva ocho versiones fallidas anteriores de tests. La referencia de
reconstrucción es `60c0bd47eb36e325d5b4693386e7bf3b7d124158`; helpers, pruebas y
validador se commitearon antes de generar. No se cambian atributos Git,
datos históricos, normas, fuentes anteriores ni gates.

Se añaden el informe espectral y su recibo. Centro, radio, seeds,
bisecciones, pivotes y todas las consultas quedan identificados por SHA.
Las celdas reutilizan componentes RMS anteriores por índice y referencia
inmutable. Su reconstrucción exige idénticos forzamientos, acoplamientos,
conversiones nodales y referencia del anclaje; sólo M_JJ cambia.
Los esquemas distinguen consultas espectrales exactas de solves de circuito.

[Datos](../evidence/loudness_latch_bdf_static_precision_spectral_inputs.json.gz):
**358265 bytes**, SHA comprimido
`ed62dccac9495f0fe0ad1e5b8ae0ce6268c763b42d325e756a739f0d464e17d4`,
SHA canónico `3aac6aac5859a1c72715f7dc2a700455f2c83f34240258b599f84794d848efe7`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_spectral_inputs_summary.json).

La [suite](../tests/test_loudness_latch_bdf_static_precision_spectral_inputs.py)
pasa **2/2 al primer intento**, 64.6371497 s. Recupera todas las
entradas desde blobs, reconstruye excepciones, contrasta versiones, esquemas,
destinos propios y bytes canónicos. Rechaza fuentes alteradas. Se conserva
también el archivo rechazado de un bloque anterior y su restauración exacta.
El [recibo](../evidence/loudness_latch_bdf_static_precision_spectral_inputs_validation.json)
conserva comandos, entorno, salidas y SHA antes/después idénticos.

El bloque suma **siete regresiones nuevas**, todas pasan al primer intento:
cinco de espectro y dos del corpus. No hay nuevas pruebas fallidas ni
archivos rechazados. El certificado espectral y la recuperación de archivos
no cierran anclaje, restos, trayectoria completa, incertidumbre física,
audio o deadline. **1 mV global sigue abierto.**

```powershell
python tools/loudness_latch_bdf_static_precision_spectral_inputs.py
python tools/validate_bdf_static_precision_spectral_inputs.py
```
