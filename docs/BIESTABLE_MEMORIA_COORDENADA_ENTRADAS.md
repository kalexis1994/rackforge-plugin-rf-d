# Corpus de memoria por coordenada y segundo intervalo

El [productor](../tools/loudness_latch_bdf_static_precision_coordinate_memory_inputs.py)
añade el banco de refinamiento y comparación de 22 grupos y su recibo
primario. Recibo aceptado, helper, dos pruebas y validator se congelan en
`126ab21`; corpus y resumen, en `327fbf9`, antes de validar.

Se recuperan **495 entradas de 86 informes**, con **119 hashes propios**
(86 informes y 33 helpers). Se conservan las tres excepciones históricas
LF→CRLF y las **trece versiones fallidas anteriores de tests**, con sus
fuentes UTF-8 exactas. Este corte no añade fallos ni versiones corregidas.

Las ocho regresiones primarias pasan al primer intento en
**104,4604078 s**; las dos del corpus, también al primero, en
**79,6181683 s**. Son **diez pruebas nuevas**, con hashes de entradas
idénticos antes y después en ambos recibos.

Además de recuperar blobs y fuentes históricas, se comprueban los campos
tipados del nuevo informe: 168 refinamientos sobre soporte ya certificado,
16 coordenadas mejoradas, partición de 22 grupos, dos modos aceptados en
radio 1 µV y selección primaria fija [1,0]. El prefijo consta de dos
intervalos contiguos hasta 390,625 ns. Se verifican identidad de inversas
y tasas reutilizadas y cero solves, precondicionadores, métricas o consultas
LDL nuevos. Los rechazos y los límites de alcance quedan archivados.

[Datos](../evidence/loudness_latch_bdf_static_precision_coordinate_memory_inputs.json.gz):
**385097 bytes**, SHA comprimido
`f03fc9ae661924e96a3b87f4305db2df7225b63942f8ad04384779e728b78c5d`,
canónico `ca34b604faeedcb3a010e361235ca4c97fdef4d4283b7b5d59446776b92fff0f`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_coordinate_memory_inputs_summary.json)
y [recibo](../evidence/loudness_latch_bdf_static_precision_coordinate_memory_inputs_validation.json).

Una auditoría final recupera las 495 entradas y 119 hashes propios desde
Git y contrasta las trece fuentes fallidas. Los helpers, protocolos y datos
congelados siguen intactos; también los atributos Git y el integrador
original. Recuperar bytes no prueba portabilidad numérica ni identificación
física o sonido vintage. El [resultado](BIESTABLE_MEMORIA_COORDENADA_RESULTADOS.md)
certifica sólo el tramo nominal publicado: el gate global de 1 mV, la
trayectoria completa, el audio, el motor nativo y el deadline siguen abiertos.
