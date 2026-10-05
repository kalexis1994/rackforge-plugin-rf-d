# Corpus del ensayo de recintos compartidos

El productor y [protocolo](BIESTABLE_RECINTOS_COMPARTIDOS_PROTOCOLO.md)
se congelan en `beaf917` antes de medir. Archivo numérico, resumen, seis
regresiones y validator se fijan en `9f88fd1` antes de validar.

Las pruebas primarias reproducen cada referencia original, RHS, restos y
duración; constante y stamps compartidos; los 704 rangos completos,
recinto, inversa, tasas, acciones y cierres. Comprueban transporte desde
la fuente real del octavo soporte, interfaces, selección y parada.
Los negativos cubren extremos e interior fuera del rango, stamp y ley
por piezas distintos, dominio exponencial, duración y linaje alterados.
La consulta candidata se reconstruye en el mismo entorno; no demuestra
portabilidad binary64 de otra plataforma.

El corpus incluye todos los informes anteriores, el último recibo del
corpus previo, los datos nuevos y su recibo primario. Recupera los blobs
reales con las tres excepciones históricas LF→CRLF; conserva fuentes y
recibos anteriores. Verifica bytes antes de guardar sólo SHA en memoria.
Las fuentes y los datos numéricos anteriores permanecen intactos.

## Recibos y archivo

Las seis pruebas primarias pasan al primer intento en **579,7343017 s**,
con entradas idénticas antes/después. Reproducen el dominio compartido
completo, la inversa y sus tasas, las 512 acciones y todos los transportes.
El recibo aceptado y helper/tests/validator del corpus se fijan en
`3c8a2a1` antes de generar el archivo ampliado.

El corpus se congela en `166de48` antes de validar. Recupera **613 entradas
de 115 informes** y verifica **155 hashes propios** (115 informes y
40 helpers), con tres excepciones LF→CRLF. Conserva **17 fuentes anteriores**:
dieciséis fallidas históricas y una interrumpida, cada una ligada a su
comando, recibo, índice de intento, fuente UTF8 exacta y SHA.

Las dos pruebas del corpus pasan al primer intento en **78,3090523 s**,
con entradas idénticas antes/después. Son **ocho pruebas nuevas aceptadas**:
seis primarias y dos archivísticas, ambas suites al primero. No hay nuevos
fallos ni repetición de la medición para corregir un adaptador.

[Recibo primario](../evidence/loudness_latch_bdf_static_precision_shared_covers_validation.json),
[recibo del corpus](../evidence/loudness_latch_bdf_static_precision_shared_covers_inputs_validation.json),
[archivo](../evidence/loudness_latch_bdf_static_precision_shared_covers_inputs.json.gz)
y [resumen](../evidence/loudness_latch_bdf_static_precision_shared_covers_inputs_summary.json).

Corpus: 421042 bytes, SHA comprimido
`9d438a2dc132c4aeacaee608b0100909a319b4370693fd064aa71132a611ca2d`,
canónico `b55f0ce1c38532e4d6e565378a596b9cbe6337c14a7a6fd5f812552e99ae9d5d`.

Productor/protocolo corresponden a `beaf917`; datos, resumen y fuentes
primarias, a `9f88fd1`; recibo primario y fuentes del corpus, a `3c8a2a1`;
corpus/resumen, a `166de48`. Atributos Git, circuito, integrador y fuentes
numéricas anteriores siguen en `ea8e347`. No quedan cachés de Python.

Se admite la certificación alternativa de los mismos dieciséis soportes
hasta ≈125 µs, acumulado ≤0,793 µV. Se conserva el control anterior. La
reducción de pruebas offline no amplía cobertura ni identifica hardware:
1 mV global, voz, sonido vintage, audio nativo y deadline siguen abiertos.
