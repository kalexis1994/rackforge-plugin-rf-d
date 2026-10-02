# Reproducción de ventanas, continuaciones y recibos

La nueva auditoría cubre las entradas de los informes de
[64 mapas estáticos](BIESTABLE_VENTANAS_ESTATICAS_RESULTADOS.md),
[continuación compensada](BIESTABLE_INTEGRADOR_COMPENSADO_RESULTADOS.md)
y todos sus intentos de validación. Fija los blobs de `7413e86`.

Se reconstruyen **137 entradas vigentes**: **134 blobs idénticos** y las
tres excepciones históricas LF en Git/CRLF en Windows. Se archivan otra
vez los bytes exactos, ambos SHA y transformación admitida. No se modifica
el `.gitattributes` raíz ni los informes anteriores; los recibos nuevos
usan la regla `-text` local ya fijada para el prefijo estático.

Una entrada de validación tiene además una versión anterior: la prueba
fallida del presupuesto BDF2. Esa fuente nunca fue un blob del commit de
referencia. Se reconstruye exclusivamente desde la fuente UTF-8 completa
del recibo fallido, verificando SHA, comando, ruta e índice de intento.
La versión vigente se reconstruye del blob; no se sustituye una por otra
ni se normalizan versiones arbitrarias. Cualquier cambio anterior que no
esté identificado en un recibo fallido se rechaza.

[Archivo completo](../evidence/loudness_latch_bdf_static_precision_window_inputs.json.gz):
**320.055 bytes**, SHA256 comprimido
`0e56901e6b6e8dd39f2d3c332d1f044e703ab504019f661d1978a0fceda17c37`;
SHA256 JSON canónico
`bfaa6b98656a7d3bfb5f62d43e54c522d61bf1e0c47bee6da5052f1dca1002d0`.
El [resumen](../evidence/loudness_latch_bdf_static_precision_window_inputs_summary.json)
conserva identidades, pertenencia a informes y versión de prueba archivada.

El [recibo](../evidence/loudness_latch_bdf_static_precision_window_inputs_validation.json)
registra **2/2 pruebas**, un intento exitoso, 8,0561 s y entradas intactas:
137 reconstrucciones por SHA, tres archivos históricos, prueba anterior
por recibo, gzip/JSON canónico y rechazo de alteraciones. Este corte suma
**10 pruebas nuevas** entre mapas, integrador y reproducción; no repite
ni afirma pasar la suite histórica completa.

`python tools/validate_bdf_static_precision_window_inputs.py`

Materializar las 137 entradas y las tres excepciones por su identidad en
un checkout aislado antes de reproducir; consultar el recibo si se desea
reproducir el adaptador fallido. La reconstrucción de bytes no prueba
ejecución numérica portable, precisión física, audio o deadline.
