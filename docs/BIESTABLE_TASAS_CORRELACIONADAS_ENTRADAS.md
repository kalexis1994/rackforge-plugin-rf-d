# Corpus de la variante correlacionada

Se amplía el [corpus constitutivo](BIESTABLE_MAGNITUD_RESIDUAL_ENTRADAS.md)
con la [variante correlacionada](BIESTABLE_TASAS_CORRELACIONADAS_RESULTADOS.md)
y sus dos recibos. Se reconstruyen entradas de 43 informes sin repetir
experimentos históricos ni cambiar los archivos o sus atributos Git.

Las tres materializaciones LF→CRLF conservan bytes completos e identidades
separadas del blob Git. Se mantienen las seis versiones fallidas anteriores,
ligadas a fuente, intento, comando y recibo; no hubo fallos nuevos en las
suites correlacionadas. El recibo nuevo declara esquema propio.

**272 entradas vigentes**: 269 blobs exactos y tres excepciones históricas.
Referencia de reconstrucción: `95461dc`. Se conservan
**seis versiones fallidas anteriores**, sin versiones fallidas nuevas.
El bloque suma **9 regresiones nuevas al primer intento**: cinco principales,
dos binomiales independientes y dos de reconstrucción/identidad.

[Datos](../evidence/loudness_latch_bdf_static_precision_correlated_inputs.json.gz): **345,139 bytes**;
SHA comprimido `61aea15de210d33784c14123997ca8989f52d1be5b840393a73f1d2b3bf28374`;
SHA canónico `f65611625e2ab592f8ee57b4d07943d7a7f9ad1008083a997f85c0548f091ab5`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_correlated_inputs_summary.json).
La [suite](../tests/test_loudness_latch_bdf_static_precision_correlated_inputs.py)
pasa **2/2**, primer intento, 54.6627821 s;
el [recibo](../evidence/loudness_latch_bdf_static_precision_correlated_inputs_validation.json)
conserva fuentes antes/después idénticas, entorno, comando y salidas.
Los tres recibos nuevos declaran esquemas propios. La etiqueta heredada
histórica se conserva con vínculo explícito de datos, suite y SHA.

Las comprobaciones cubren métodos independientes de capacitancia/binomial,
consulta del grafo completo y filtrado, recintos brutos/intersecciones,
cobertura y contribución absoluta de brackets. El certificado se aplica
al interpolante; la reproducibilidad no admite física, portabilidad numérica,
audio o cierre del criterio global de 1 mV.

```powershell
python tools/loudness_latch_bdf_static_precision_correlated_inputs.py
python tools/validate_bdf_static_precision_correlated_inputs.py
```
