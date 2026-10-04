# Corpus del primer tubo no lineal

El [productor](../tools/loudness_latch_bdf_static_precision_startup_tube_inputs.py)
amplía el corpus anterior con la reconstrucción continua, sus tres radios
y el recibo de validación. El recibo aceptado, helper de recuperación,
dos pruebas y validator se congelan en `b0f8d8e`; los datos del corpus,
en `8821679`, antes de validar. No se repite el experimento del circuito.

Se reconstruyen **461 entradas de 80 informes**, conservando las tres
excepciones históricas LF→CRLF y **trece versiones fallidas de tests**.
Las tres nuevas versiones corresponden a los intentos de la prueba de
diagnóstico: comparación Decimal/cota racional en KCL, guard de topología
incompleto y comparación Decimal/cota racional en restricciones. Cada
fuente fallida se guarda con SHA, comando e índice de intento; la vigente
se reconstruye desde su blob propio. Ningún fallo modifica los datos
numéricos ni relaja los gates de circuito.

Los **110 hashes propios** ligan 80 informes y 30 helpers. Todas las
entradas se cotejan con archivos reales y blobs Git; las tres diferencias
históricas se reconstruyen por transformación explícita y se rechazan
cambios de contenido. Los atributos Git congelados permanecen intactos.
El experimento numérico sigue en `fbc5de1` y los datos en `cf6b215`.

La suite primaria conserva cuatro intentos, con ocho pruebas aceptadas
en el último; los cuatro declaran fuentes idénticas antes y después.
Las dos pruebas de corpus pasan al primer intento en **72,9542874 s**,
con entradas idénticas antes y después. La suite del corpus verifica también 24/24 inversas, tres rechazos y
cobertura continua real cero, sin confundir identidad de bytes con
portabilidad numérica o con identificación física.

[Datos](../evidence/loudness_latch_bdf_static_precision_startup_tube_inputs.json.gz):
**381178 bytes**, SHA comprimido
`f185dd3c380ee1f48ca636801e25cc1fac13df3bbb204b417bf5ff4cda3924c9`,
canónico `e7c81e98b2050e404615d4079aaf8affc26361bf5687c1ebfbe86e2d19d0a737`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_startup_tube_inputs_summary.json)
y [recibo](../evidence/loudness_latch_bdf_static_precision_startup_tube_inputs_validation.json).

La [prueba de tubo](BIESTABLE_PRIMER_TUBO_RESULTADOS.md) mantiene duración
certificada cero; 1 mV global, circuito físico, voz y deadline quedan abiertos.
