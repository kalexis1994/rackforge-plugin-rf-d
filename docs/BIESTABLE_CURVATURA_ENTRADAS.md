# Entradas de curvatura y respuesta cuadrática

El 2 de octubre de 2026 se amplió el
[corpus de respuesta](BIESTABLE_RESPUESTA_ENTRADAS.md) con la
[curvatura derivada](BIESTABLE_CURVATURA_RESULTADOS.md), la
[respuesta reservada](BIESTABLE_RESPUESTA_CUADRATICA_RESULTADOS.md) y sus
recibos. Se reconstruyen entradas de **20 informes** numéricos y de
validación desde **`360ca35`**, sin repetir integración.

## Identidad de fuentes y fallos

**186 entradas vigentes**: 183 blobs con bytes idénticos y las mismas
tres excepciones históricas LF→CRLF. Se archivan sus fuentes completas,
SHA de blob y SHA de materialización; se rechazan cambios de contenido.
Se conserva el fallo original de comparación directa. No se normalizan
datos históricos ni políticas `.gitattributes` congeladas.

Se conservan **tres versiones de pruebas fallidas** desde sus recibos:
adaptadores de presupuesto BDF2, ruta SVD y polarización auxiliar inválida.
Cada versión tiene fuente exacta UTF-8, SHA, ruta, comando e índice de
intento; las versiones actuales se reconstruyen de blobs. La última prueba
pedía curvatura cero en una polarización que excedía el dominio exponencial:
el testigo posterior usa una polarización válida y comprueba también el
rechazo del caso inválido. No cambia helper, productor, gate ni datos.

Los fallos de suite son distintos de los fallos numéricos del predictor:
se retienen los 18 + 11 individuales anteriores y los **18 lineales nuevos**
en amplitudes reservadas. El pase del cuadrático no altera esos informes.

## Archivo y regresiones

[Datos](../evidence/loudness_latch_bdf_static_precision_memory_quadratic_inputs.json.gz):
328.955 bytes; SHA comprimido
`a86eccf3dccbf2ad14f5cee9aaa76fdb41dec559e849e9c9295bdd8b42c3301f`;
SHA canónico
`22ea9ecbd9931ce1af0ea1907c924d0a9188a679fed0a1abf1df79b6702bfe6b`.
El [resumen](../evidence/loudness_latch_bdf_static_precision_memory_quadratic_inputs_summary.json)
conserva identidades y pertenencia por informe. La
[suite](../tests/test_loudness_latch_bdf_static_precision_memory_quadratic_inputs.py)
reconstruye todo el corpus, comprueba todas las versiones y rechaza
fuentes/bytes alterados. El
[recibo](../evidence/loudness_latch_bdf_static_precision_memory_quadratic_inputs_validation.json)
conserva **2/2 pruebas**, primer intento, **39,2306258 s**, SHA antes/después
idénticos.

Este bloque suma **11 pruebas nuevas** (5 + 4 + 2); sólo la primera suite
necesitó el segundo intento, con fallo preservado. No se repite toda la suite
histórica. Se cuentan **9.216 solves no lineales nuevos** para respuesta y
**256 solves espaciales de seis RHS** para 1.536 segundas variaciones.
El archivo de entradas no añade solves. Tiempos offline no son deadlines.

```powershell
python tools/loudness_latch_bdf_static_precision_memory_quadratic_inputs.py
python tools/validate_bdf_static_precision_memory_quadratic_inputs.py
```

La identidad de bytes no prueba portabilidad numérica de BLAS, fidelidad
vintage, defecto temporal exacto, resto de Taylor global, audio o deadline.
El gate temporal de **1 mV desde DC** permanece abierto. El siguiente
problema es derivar el forzamiento/defecto temporal sobre historiales reales:
una recurrencia de perturbación inicial, incluso cuadrática, no lo entrega.
