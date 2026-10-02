# Corpus de integrales acotadas

Se amplía el [corpus de balances](BIESTABLE_BALANCE_CARGA_ENTRADAS.md)
con la [integral acotada](BIESTABLE_INTEGRAL_ACOTADA_RESULTADOS.md) y su
recibo. Se reconstruyen entradas de 38 informes desde blobs comprometidos,
sin repetir el experimento completo ni modificar fuentes históricas.

Las tres excepciones históricas LF→CRLF conservan materialización exacta,
fuente completa y SHA separados del blob Git. Las cinco versiones anteriores
de pruebas fallidas se mantienen ligadas a su intento, comando y recibo;
la versión vigente se identifica por separado. Cualquier fallo nuevo se
archiva bajo la misma regla. Los hashes antes/después deben permanecer iguales.

**254 entradas vigentes**: 251 blobs exactos y tres excepciones históricas.
Se conservan **cinco versiones de pruebas fallidas**, todas anteriores.
Referencia de reconstrucción: `9b77b5d`. Ningún dato numérico
anterior se sobrescribe. El bloque suma **7/7 regresiones nuevas**, al primer
intento: cinco del recinto y dos de reconstrucción/identidad.

El recibo numérico heredó la etiqueta de esquema de Gauss. El corpus comprueba
su identidad por ruta, suite exacta, comando, número de pruebas, SHA y esquema
de datos de integral acotada. Se conserva el recibo original y se documenta
el vínculo; el recibo del corpus declara `bdf-static-enclosure-inputs-validation/v1`.
No inferir el tipo de experimento sólo de una etiqueta de envoltura heredada.

[Datos](../evidence/loudness_latch_bdf_static_precision_enclosure_inputs.json.gz): **340,450 bytes**;
SHA comprimido `71c465e6d1eef3c0abbda9515e00f98956111fcda48fff17ac00b943d4725e74`;
SHA canónico `a464c811552338cd9d17c0ee696b754bcdfe802497555829f09ac82ce8bedeb1`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_enclosure_inputs_summary.json).
La [suite](../tests/test_loudness_latch_bdf_static_precision_enclosure_inputs.py)
pasa **2/2**, primer intento, 53.1391674 s;
el [recibo](../evidence/loudness_latch_bdf_static_precision_enclosure_inputs_validation.json)
conserva fuentes antes/después idénticas, entorno, comando y salidas.

El ayudante, productor y protocolo racionales quedan congelados antes de
medir. Las operaciones exteriores se prueban con series independientes,
exponencial afín de fórmula cerrada, otra expansión cúbica y sellos de ambas
polaridades. Se contrastan recintos completos y ocho replays seleccionados.
La identidad de bytes no prueba portabilidad numérica, física ni audio.
El criterio global de 1 mV sigue abierto.

```powershell
python tools/loudness_latch_bdf_static_precision_enclosure_inputs.py
python tools/validate_bdf_static_precision_enclosure_inputs.py
```
