# Corpus del radio balanceado en la misma métrica

La reconstrucción se amplía a **67 informes y 390 entradas**:
**387 blobs idénticos** y tres excepciones históricas LF→CRLF. Conserva
ocho versiones fallidas anteriores de tests. Helper, suite y validador se
congelaron en `dec95d7` antes de generar el corpus. Se añaden informe
balanceado y recibo primario, incluyendo sus dependencias transitivas.
No cambian atributos Git, entradas previas, parámetros ni gates.

[Datos](../evidence/loudness_latch_bdf_static_precision_balanced_inputs.json.gz):
**363043 bytes**, SHA comprimido
`e03473302970a91db066c9f3eef47f4e3d9d1bca155a26399c7a7f87e7c3dc9b`,
SHA canónico `087dd487232ead27b1b4d35961002e33967fac52d432c941b0593911901d2d24`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_balanced_inputs_summary.json).
La referencia Git fija blobs, identidades, membresía y versiones históricas.
Las excepciones recuperan exactamente los bytes originales; no se sustituye
el gate de bytes por igualdad de JSON canónico.

La [suite](../tests/test_loudness_latch_bdf_static_precision_balanced_inputs.py)
pasa **2/2 al primer intento**, 70.4458056 s. Exige cobertura exacta de
identidades, reconstrucción de blobs, excepciones declaradas y versiones
fallidas con su fuente por SHA. Comprueba esquemas, destinos independientes
y que Gamma es fijo, no ajustado a resultados, sin cambiar P, norma o anclaje.
El [recibo](../evidence/loudness_latch_bdf_static_precision_balanced_inputs_validation.json)
conserva conteos, comando, salida y SHA antes/después idénticos.

Este bloque suma **ocho regresiones nuevas**, todas pasan al primer intento:
seis del majorante y dos de reconstrucción. No hay nuevas validaciones
fallidas ni archivos rechazados. Se preservan los dos rechazos de reset,
las tasas positivas de ataque y todos los resultados anteriores.

**1 mV global sigue abierto.** Las cotas forzadas pequeñas conservan anclaje
hipotético, resto no lineal pendiente y cobertura parcial. Reconstrucción
exacta de evidencia no certifica física, voz audible o deadline.

```powershell
python tools/loudness_latch_bdf_static_precision_balanced_inputs.py
python tools/validate_bdf_static_precision_balanced_inputs.py
```
