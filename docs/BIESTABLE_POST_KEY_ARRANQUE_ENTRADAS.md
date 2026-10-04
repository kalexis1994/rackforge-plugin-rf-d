# Corpus de publicación y arranque post-KEY

El [productor](../tools/loudness_latch_bdf_static_precision_post_key_inputs.py)
amplía el corpus anterior con la publicación tipada, prefijo de 512 pasos
y recibo primario. Helpers, dos pruebas de corpus, validator y recibo aceptado
se fijan en `19aaf47`; el corpus se congela en `2d40cf6` antes de validar.
No se repite un solve ni se modifica la evidencia anterior.

Se reconstruyen **450 entradas de 78 informes**, con tres excepciones
históricas LF→CRLF y **diez versiones fallidas de tests**. No se añade una
versión fallida en este corte: ocho pruebas primarias y dos de corpus
pasan al primer intento. Ambos recibos registran fuentes idénticas antes
y después. El corpus conserva los intentos fallidos y sus versiones previas,
incluido el import fallido y los rechazos de escala y gate binary64.

Los **107 hashes propios** ligan 78 informes y 29 helpers de reconstrucción.
Cada entrada se coteja con blob Git y archivo de entrada real; las tres
excepciones se recuperan exactamente, con transformaciones declaradas y
sin esconder cambios bajo igualdad canónica. Los recibos nuevos mantienen
la política Git `-text` anterior, sin alterar atributos congelados.

Las dos regresiones pasan en **71,5121088 s**. Además del corpus histórico,
verifican identidad tipada del nuevo origen, anclaje local conocido,
512/512 intervalos, historia no fabricada, integrador original intacto y
cobertura de error continuo todavía cero. La restauración de bytes no
prueba portabilidad numérica ni identificación física.

[Datos](../evidence/loudness_latch_bdf_static_precision_post_key_inputs.json.gz): **376384 bytes**,
SHA comprimido `ab5dc55408c2db80e26c8a851ffbd591ca6f346ee4723e3dc492c0ce787e752e`,
canónico `0aaa73885633085f7ff3d44186b63eba14f74bca8d086a6942a9406a5b10f0f5`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_post_key_inputs_summary.json)
y [recibo](../evidence/loudness_latch_bdf_static_precision_post_key_inputs_validation.json).

**Diez pruebas nuevas aceptadas al primer intento**, sin relajar gates
ni regenerar mediciones. Global 1 mV, reconstrucción continua, resto no
lineal, hardware, voz completa y deadline quedan fuera de este certificado.
