# Corpus de reconstrucción interior de cargas

El 2 de octubre de 2026 se amplía el
[corpus continuo](BIESTABLE_CARGA_CONTINUA_ENTRADAS.md) con la
[reconstrucción interior](BIESTABLE_CARGA_INTERIOR_RESULTADOS.md) y su recibo.
Se reconstruyen las entradas de **32 informes** desde `866c253`,
sin repetir experimentos históricos ni modificar sus datos.

## Bytes, versiones y observaciones

**230 entradas vigentes**: 227 blobs exactos y las tres excepciones
históricas LF→CRLF, con fuentes originales completas y SHA. Se conservan
los atributos Git y todos los gates anteriores. Cualquier diferencia
adicional se rechaza; coincidencia de JSON no sustituye identidad de bytes.

Se conservan cuatro versiones de pruebas fallidas por sus recibos:
presupuesto BDF2, SVD, polarización y formato Decimal del cero virtual.
Este bloque no añade versiones fallidas. Los 14 fallos de cuadratura y
390 observaciones de KCL del diagnóstico anterior permanecen intactos.
Los **1.173 incumplimientos interiores de 10 pA** quedan en el nuevo
informe; no se confunden con fallos de suite o rechazos de pasos nuevos.

Las entradas nuevas identifican el álgebra polinómica exacta, productor,
protocolo, datos, resumen, pruebas y adaptador. El corpus registra además
sus propios ayudantes y los 32 informes. La auditoría final comprueba
esas identidades contra Git al cerrar el commit.

## Archivo y verificación

[Datos](../evidence/loudness_latch_bdf_static_precision_dense_inputs.json.gz):
335.269 bytes; SHA comprimido
`13c6df6e1fbdf26a59c6d486bd1d46583deced6a1b9d46feda05b8268bcdbc93`;
SHA canónico
`fd9384a5ae9c33b2dddf57addcf07ffd588d1abe566962908f0663a0386707a8`.
El [resumen](../evidence/loudness_latch_bdf_static_precision_dense_inputs_summary.json)
conserva las identidades y versiones. La
[suite](../tests/test_loudness_latch_bdf_static_precision_dense_inputs.py)
reconstruye los 230 archivos y todas las versiones fallidas, con controles
negativos de contenido. El
[recibo](../evidence/loudness_latch_bdf_static_precision_dense_inputs_validation.json)
registra **2/2 pruebas**, primer intento, **46,5384083 s**, hashes
antes/después idénticos.

El bloque suma **siete pruebas nuevas** (5 + 2), todas al primer intento.
Cubren 496 soportes, 1.488 consultas, 10.416 restricciones exactas,
cubiertas del knee, 24 reconstrucciones independientes de Newton,
72 replays racionales y 288 FD locales. No se añade integración nueva
ni se repite toda la suite histórica.

```powershell
python tools/loudness_latch_bdf_static_precision_dense_inputs.py
python tools/validate_bdf_static_precision_dense_inputs.py
```

Reproducibilidad de bytes no certifica una trayectoria física ni precisión
numérica portable a otro BLAS/SO. El criterio global de **1 mV**, física,
audio y deadline siguen abiertos.
