# Corpus de carga constitutiva y magnitud

Se amplía el [corpus de integrales](BIESTABLE_INTEGRAL_ACOTADA_ENTRADAS.md)
con los [recintos constitutivos y de magnitud](BIESTABLE_MAGNITUD_RESIDUAL_RESULTADOS.md)
y su recibo. Cuarenta informes mantienen leyes, protocolos, fuentes, datos,
resúmenes y validaciones sin repetir experimentos anteriores.

Las tres excepciones LF→CRLF conservan sus bytes y SHA separados de Git.
Cada versión histórica fallida se identifica con su fuente completa, comando,
intento y recibo. Las entradas se comparan antes/después; no se normalizan
archivos históricos. El recibo nuevo declara esquema propio; se preserva y
verifica la etiqueta heredada del recibo de integral anterior mediante su
suite, comando, SHA y tipo de datos.

**262 entradas vigentes**: 259 blobs exactos y tres excepciones históricas.
Referencia: `c180f44`. Se conservan **seis versiones de
pruebas fallidas**: cinco anteriores y la primera suite de este bloque.
Esta última archiva tanto el testigo fuera de dominio como la exigencia
incorrecta de grado para un exponente afín. La corrección sólo cambia
la fuente de tests; los datos y gates numéricos permanecen iguales.

El bloque suma **7 regresiones nuevas**: cinco del recinto en segundo intento
y dos del corpus al primero. Ambas suites conservan sus comandos, conteos,
entorno, salidas y hashes antes/después. El recibo del corpus declara
`bdf-static-constitutive-inputs-validation/v1`.

[Datos](../evidence/loudness_latch_bdf_static_precision_constitutive_inputs.json.gz): **343,926 bytes**;
SHA comprimido `142d5d31ef73816355d8b4a091979c163d11f06a593387bc47b7cf2568588ece`;
SHA canónico `fe014e2d0d5fe8887331f7b33fe3c9cf32220671c9df0526fcdceac25039f096`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_constitutive_inputs_summary.json).
La [suite](../tests/test_loudness_latch_bdf_static_precision_constitutive_inputs.py)
pasa **2/2 al primer intento**, 53.8357473 s;
el [recibo](../evidence/loudness_latch_bdf_static_precision_constitutive_inputs_validation.json)
registra fuentes antes/después idénticas. Ningún experimento histórico se repite.

Los controles nuevos incluyen log con series independientes, fórmulas de
Q/C a alta precisión, M=0 exacto, M=1, monotonía a ambos lados del knee,
polaridades y cancelación lineal. Ocho replays de recintos y 24 consultas
interiores Decimal120 comprueban el alcance reconstruido. La identidad de
bytes no admite fidelidad, portabilidad numérica ni el gate global de 1 mV.

```powershell
python tools/loudness_latch_bdf_static_precision_constitutive_inputs.py
python tools/validate_bdf_static_precision_constitutive_inputs.py
```
