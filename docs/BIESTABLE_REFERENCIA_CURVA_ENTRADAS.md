# Corpus de referencias curvas y endpoints conservados

El productor amplía el corpus anterior con el recibo de aquel corpus,
el lanzamiento interrumpido, el informe curva/afín y su recibo primario.
Conserva las quince versiones históricas fallidas y las tres excepciones
LF→CRLF identificadas. No cambia datos anteriores ni los gates.

La validación primaria reproduce el RHS de las 119 ecuaciones, las dos
referencias, cargas/RC/Q, interfaces, todas las inversas, tasas, acciones y
cierres. Comprueba solución cuadrática exacta con tiempo físico y signo,
y un contraejemplo de restricción RC cuando p' es no nula en el endpoint.
Las consultas Decimal100 se comparan con las cotas racionales separando
el redondeo del observador; ese margen diagnóstico no altera certificados.

[Protocolo](BIESTABLE_REFERENCIA_CURVA_PROTOCOLO.md),
[resultado](BIESTABLE_REFERENCIA_CURVA_RESULTADOS.md),
[productor del corpus](../tools/loudness_latch_bdf_static_precision_curved_reference_inputs.py).

## Intento primario conservado

El primer intento ejecuta seis pruebas en 311,4793491 s; cinco pasan,
incluida la reproducción de recintos, tasas, acciones y cierres completos.
La prueba sintética falla antes de sus comprobaciones por TypeError:
el fixture pasa Fraction al hash JSON de la candidata binary64. El recibo
incluye fuente UTF8 exacta, SHA, comando y entradas antes/después idénticas.
Se archiva en `176269b` antes de corregir.

`50eb9a9` fija el fixture como enteros y cadenas racionales serializables.
Sólo cambian dos líneas de la prueba; datos, helper, productor, protocolo,
validator y gates permanecen idénticos. El corpus conserva las quince
fuentes fallidas anteriores y esta nueva versión por separado.

Las seis pruebas pasan en el segundo intento, **309,7310804 s**, con
entradas idénticas antes/después. Los 32 recintos de inversa, 3168
consultas de tasa y 256 acciones reproducen sus certificados completos.
El recibo aceptado y el helper/tests/validator del corpus se congelan en
`4162fa4` antes de generar el archivo ampliado.

## Archivo completo y recuperación

El corpus se congela en `07bafc9` antes de validar. Recupera **578 entradas
de 101 informes**, con **139 hashes propios** (101 informes y 38 helpers),
tres excepciones históricas LF→CRLF y **16 versiones de pruebas fallidas**.
Cada versión conserva fuente exacta, SHA, recibo, comando e índice de intento.
El lanzamiento interrumpido conserva el productor completo y su blob congelado.

Las dos pruebas del corpus pasan al primer intento en **103,5727587 s**.
Son **ocho pruebas nuevas aceptadas**: seis primarias al segundo y dos
archivísticas al primero. Ambos recibos mantienen entradas antes/después
idénticas. Los informes rechazados, el fallo primario y sus bytes permanecen
archivados; la corrección del fixture no repite la medición numérica.

[Recibo primario](../evidence/loudness_latch_bdf_static_precision_curved_reference_validation.json),
[recibo del corpus](../evidence/loudness_latch_bdf_static_precision_curved_reference_inputs_validation.json),
[archivo](../evidence/loudness_latch_bdf_static_precision_curved_reference_inputs.json.gz)
y [resumen](../evidence/loudness_latch_bdf_static_precision_curved_reference_inputs_summary.json).

Archivo: 410125 bytes, SHA comprimido
`4fdf919e0003e0e0826b228e4d8fef7368d2f0f6dced88aee4fcb446813a0068`,
canónico `69b71e5b2dac00fb3917e5e4c44a299c5febc0519f23dd519db5cd131a8e1add`.

La revisión final confirma helper/productor/protocolo idénticos a `04e5519`,
datos y validator primario a `0cf6e0c`, fuentes del corpus a `4162fa4`,
corpus a `07bafc9`, y atributos Git a `08bd258`. Sólo el fixture primario
cambia en `50eb9a9`. Los tests recuperan todas las entradas desde sus blobs
con las tres excepciones explícitas y verifican los 139 hashes propios.
Los 2015 enlaces locales de RF-D resuelven y no quedan cachés Python.

La recuperación de bytes no prueba otro SO/BLAS, trayectoria completa,
identificación física o audio. Se admite sólo el prefijo nominal de ocho
soportes hasta ≈25 µs, error acumulado ≤0,793 µV respecto a la referencia
por tramos. Meta global 1 mV, voz, audio nativo y deadline siguen abiertos.
