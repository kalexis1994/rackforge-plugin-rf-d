# Reconstrucción de las entradas del contraste estático

El contraste Decimal y sus dos rutas binary64 identifican **124 entradas
distintas**. Se verifican los blobs de `b8eb3f4` y se conservan sus SHA de
entrada; **121** coinciden en bytes con esos blobs. Las otras tres son los
mismos JSON LF en Git/CRLF en Windows de la [auditoría anterior](REPRODUCIBILIDAD_DE_ENTRADAS_HISTORICAS.md).
La ampliación no normaliza ni modifica ningún dato anterior.

El [paquete de entradas](../evidence/loudness_latch_bdf_static_precision_inputs.json.gz)
conserva las tres fuentes completas con sus CRLF, identidad del blob,
identidad del archivo usado y pertenencia a cada informe. Tamaño 316.131
bytes, SHA256 comprimido
`b97e53f998eb546c101eb5945895f9cf0858f50841db784c199c81d492bff299`.
Su [resumen](../evidence/loudness_latch_bdf_static_precision_inputs_summary.json)
conserva los 124 registros de identidad sin repetir las fuentes completas.

Para reconstruir los bytes, partir de los blobs de la revisión fijada,
materializando las 121 entradas idénticas y los tres archivos archivados
en un checkout aislado de reproducción. No asumir que los finales de línea
predeterminados de un checkout coinciden con esos bytes. Verificar los 124
SHA antes de ejecutar; el helper de reconstrucción rechaza cambios de
contenido o identidad y sólo admite la expansión LF→CRLF declarada.
Este paso reconstruye entradas; no prueba ejecutar el circuito en otro SO.

`python tools/validate_bdf_static_precision_inputs.py`

El [recibo](../evidence/loudness_latch_bdf_static_precision_inputs_validation.json)
registra **2/2 regresiones**, un intento exitoso y fuentes sin cambios.
Reconstruye los 124 SHA desde Git, verifica gzip/JSON canónico y rechaza
alteraciones. Los reportes numéricos, sus parámetros y gates permanecen
intactos. Los nuevos JSON usan la regla `-text` local ya fijada antes del
contraste estático, para preservar sus bytes también al hacer checkout.

El HEAD contextual del archivo y validación es `b8eb3f4`; sus productores
nuevos se identifican también por SHA y se archivan en el commit posterior.
