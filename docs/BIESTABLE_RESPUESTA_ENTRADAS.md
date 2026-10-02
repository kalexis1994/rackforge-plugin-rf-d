# Entradas de respuesta finita y pequeña señal

El 2 de octubre de 2026 se amplió el
[corpus de memoria](BIESTABLE_MEMORIA_ENTRADAS.md) con el
[contraste de C7 y máximos](BIESTABLE_DIRECCIONES_EXTREMAS_RESULTADOS.md),
los [controles cero y niveles pequeños](BIESTABLE_PEQUENA_SENAL_RESULTADOS.md)
y sus recibos. Se reconstruyen las entradas de **16 informes** numéricos
y de validación desde la revisión **`1fe9aa1`**, sin repetir integración.

## Resultado de bytes

**173 entradas vigentes**: 170 blobs con bytes idénticos y las mismas
tres excepciones históricas LF→CRLF, archivadas íntegramente y verificadas
por SHA. Se mantienen el fallo original de comparación directa y el
alcance limitado de reconstrucción. No se normalizan datos, `.gitattributes`
ni informes anteriores.

Se reconstruyen también las **dos versiones históricas de pruebas fallidas**
desde sus recibos: el adaptador de presupuesto BDF2 y el adaptador de ruta
SVD. Cada versión conserva ruta, comando, índice de intento y SHA; las
versiones vigentes proceden de blobs. Se rechazan identidades o contenidos
alterados. Los dos nuevos experimentos no añaden fallos de suite;
conservan los **18 + 11 fallos numéricos individuales de ataque** en sus datos.

## Archivo y validación

[Datos](../evidence/loudness_latch_bdf_static_precision_memory_response_inputs.json.gz):
325.546 bytes; SHA comprimido
`74c823be4934e280320312265885d66a48f840098d63e2b936782b073e71365e`;
SHA canónico
`b597c7b218817f5dc03fd5f133abb2e6724966638a88160a1c882728fc1ab557`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_memory_response_inputs_summary.json)
incluye pertenencia por informe y todas las identidades.
El [recibo](../evidence/loudness_latch_bdf_static_precision_memory_response_inputs_validation.json)
conserva **2/2 pruebas**, un intento exitoso de 31,952 s, reconstrucción
completa, controles negativos y hashes idénticos antes/después.
Este corte suma **10 pruebas nuevas** (4 + 4 + 2), sin repetir toda
la suite histórica, y **12.544 solves no lineales nuevos** entre ambos
experimentos; el archivo de entradas no añade solves.

```
python tools/loudness_latch_bdf_static_precision_memory_response_inputs.py
python tools/validate_bdf_static_precision_memory_response_inputs.py
```

Identidad de bytes no prueba portabilidad de BLAS, fidelidad vintage,
defecto temporal exacto, cota global, audio ni deadline. Se mantienen
separados los gates centrales, individuales, de publicación y temporales.
