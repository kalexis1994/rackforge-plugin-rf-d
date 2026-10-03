# Corpus de pesos y cubierta ideal temporal

Se amplía el corpus a **51 informes y 305 entradas**: **302 blobs idénticos**
y las tres excepciones históricas LF→CRLF. La referencia de reconstrucción
es `be4f83f`; helper, test y validador se commitearon antes de generar.
Los atributos Git, fuentes históricas, datos previos y gates no cambian.

Se añade el informe de pesos y cubierta ideal temporal y su recibo. Los
archivos de los dos intentos de sintaxis son entradas por SHA del experimento:
conservan fuente exacta y revisión original, comprobadas desde sus blobs.
No se cuentan como versiones fallidas de tests: ninguna medición empezó.
El primer ensayo del testigo Decimal120 añade la **octava versión fallida de
prueba**. Se preservan sus bytes, SHA, comando y salida; la comparación
corregida usa un margen numérico separado y mantiene el certificado intacto.

El corpus identifica todas las entradas y versiones de los recibos previos,
incluida la etiqueta Gauss heredada declarada. Las matrices e intervalos nuevos
conservan esquemas propios. Se preservan los fallos de gates de las inversas
binary64 y los presupuestos uniformes inválidos de norma del bloque anterior.

[Datos](../evidence/loudness_latch_bdf_static_precision_weighted_inputs.json.gz):
**354.066 bytes**, SHA comprimido
`43480398121ca4f3ca63abcfc423085d0750de29250d6700793b0a19e724ac94`,
SHA canónico `23e91035cde5abbc8f0595be2079612fa14d8035a1d1f6c6d68d8628223200d8`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_weighted_inputs_summary.json).
La [suite](../tests/test_loudness_latch_bdf_static_precision_weighted_inputs.py)
pasa **2/2** al primer intento, 60,7384837 s.
El [recibo](../evidence/loudness_latch_bdf_static_precision_weighted_inputs_validation.json)
conserva comando, conteo, salidas, entorno y SHA antes/después idénticos.

El bloque suma **nueve regresiones nuevas**: siete del descriptor ponderado
pasan en el segundo intento y dos del corpus en el primero. Los ocho intervalos
cubren sus 64 celdas; esto no cubre una trayectoria completa desde DC.
La prueba de bytes no admite un mapa binary64 rechazado, fidelidad física,
error global de voltaje, audio o deadline.

```powershell
python tools/loudness_latch_bdf_static_precision_weighted_inputs.py
python tools/validate_bdf_static_precision_weighted_inputs.py
```
