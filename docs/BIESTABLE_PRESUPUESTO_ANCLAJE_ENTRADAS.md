# Corpus del presupuesto condicional de anclaje

La reconstrucción incluye **69 informes y 401 entradas**:
**398 blobs idénticos** y tres excepciones históricas LF→CRLF. Conserva
ocho versiones fallidas anteriores de tests. Helper, suite y validador se
fijaron en `e71f89e` antes de generar el corpus. Se añaden presupuesto de
anclaje y recibo primario, con todas sus dependencias transitivas.
No cambian atributos Git, fuentes anteriores, parámetros o gates.

[Datos](../evidence/loudness_latch_bdf_static_precision_anchor_inputs.json.gz):
**364426 bytes**, SHA comprimido
`f284193fb77c60474061ae6c197bf041892104bc1a5c19ec5d25574c1f657eb4`,
SHA canónico `6a858322b29ddf5778db1d56a54f5d82ea54d69038009934d566472178ab1ce2`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_anchor_inputs_summary.json).
La referencia Git fija blobs, fuentes, membresía y versiones históricas.
Se reconstruyen bytes exactos; las tres excepciones tienen contenido
original archivado y transformación declarada, sin normalizar evidencia previa.

La [suite](../tests/test_loudness_latch_bdf_static_precision_anchor_inputs.py)
pasa **2/2 al primer intento**, 67.4698739 s. Verifica cobertura exacta,
recuperación de blobs, excepciones y versiones fallidas por SHA. Exige
esquemas y destinos propios, y mantiene separados el gate de 1 mV, los
objetivos condicionales y las reservas no probadas del resto no lineal.
El [recibo](../evidence/loudness_latch_bdf_static_precision_anchor_inputs_validation.json)
conserva comandos, conteos, salida y SHA antes/después idénticos.

Este corte aporta **siete regresiones nuevas**, todas pasan al primer
intento: cinco de capacidades y dos de reconstrucción. No hay validaciones
fallidas nuevas ni archivos rechazados. Reset conserva sus dos candidatos
rechazados y todas las fuentes numéricas anteriores mantienen sus bytes.

**1 mV global sigue abierto.** Un objetivo pequeño para el anclaje no
demuestra que el error entrante lo cumpla. Reservas hipotéticas, ventanas
seleccionadas y reconstrucción exacta tampoco cierran resto, cobertura,
física, voz audible o deadline.

```powershell
python tools/loudness_latch_bdf_static_precision_anchor_inputs.py
python tools/validate_bdf_static_precision_anchor_inputs.py
```
