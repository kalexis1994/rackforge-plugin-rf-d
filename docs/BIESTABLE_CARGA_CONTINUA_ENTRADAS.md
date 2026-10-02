# Corpus del contraste continuo de cargas

El 2 de octubre de 2026 se amplía el
[corpus de defecto](BIESTABLE_DEFECTO_CARGA_ENTRADAS.md) con el
[diagnóstico continuo](BIESTABLE_CARGA_CONTINUA_RESULTADOS.md) y su recibo.
Se reconstruyen las entradas de **30 informes** desde `8ed62c8`,
sin repetir experimentos históricos ni modificar sus archivos.

## Identidades y versiones

**222 entradas vigentes**: 219 blobs exactos y las tres excepciones
históricas LF→CRLF, con fuentes completas, SHA y pertenencia por informe.
No se cambia `.gitattributes`, la política de recibos o la comparación
histórica directa que falló. Cualquier diferencia adicional se rechaza.

Se conservan las cuatro versiones de pruebas fallidas identificadas por
recibo: presupuesto BDF2, ruta SVD, polarización y formato Decimal del cero
virtual. Este bloque no añade otra prueba fallida. Los 14 fallos de
cuadratura anteriores permanecen en sus informes. Los **390 residuales
cúbicos sobre 10 pA** son observaciones numéricas, conservadas completas,
distintas de fallos de suite o rechazo de nuevos pasos.

El archivo incluye leyes, productor/protocolo, datos, resumen, pruebas y
adaptador identificados por el nuevo recibo. El productor de corpus registra
además la identidad de sus propios ayudantes y todos los informes.
La auditoría final contrasta esas identidades con Git al cerrar el commit.

## Archivo y regresiones

[Datos](../evidence/loudness_latch_bdf_static_precision_continuous_inputs.json.gz):
334.467 bytes; SHA comprimido
`33d0d886dd907f160c4a8e2326c0825e4ae7a48e9381831029ad26678e0b36e5`;
SHA canónico
`c5bf2bc95d5260bdb2217d9e3454d3e74895c3b652e1a178de79671d64155118`.
El [resumen](../evidence/loudness_latch_bdf_static_precision_continuous_inputs_summary.json)
conserva todas las identidades. La
[suite](../tests/test_loudness_latch_bdf_static_precision_continuous_inputs.py)
reconstruye las 222 entradas, verifica cada versión fallida y rechaza
contenido alterado. Su
[recibo](../evidence/loudness_latch_bdf_static_precision_continuous_inputs_validation.json)
conserva **2/2 pruebas al primer intento**, 46,2108264 s, hashes antes/después
idénticos.

El bloque completo suma **6 pruebas nuevas** (4 + 2), todas al primer
intento: 496 diagnósticos continuos, 24 replays racionales, 24 evaluaciones
estáticas por corrientes y 96 FD de capacitancia, con cero solves no
lineales nuevos. No se repite la suite histórica completa.

```powershell
python tools/loudness_latch_bdf_static_precision_continuous_inputs.py
python tools/validate_bdf_static_precision_continuous_inputs.py
```

La identidad de bytes no acredita regularidad entre muestras, otra física,
portabilidad numérica o error global. El gate de **1 mV**, audio y deadline
continúan abiertos.
