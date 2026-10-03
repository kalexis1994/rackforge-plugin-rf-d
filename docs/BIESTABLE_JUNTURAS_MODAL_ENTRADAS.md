# Corpus del generador firmado de junturas

La reconstrucción se amplía a **61 informes y 357 entradas**:
**354 blobs idénticos** y tres excepciones históricas LF→CRLF.
Conserva las ocho versiones fallidas anteriores de tests. Helper, pruebas
y validador se congelaron en `4e499f1` antes de generar este corpus.
Se añaden el informe modal y su recibo, con todas las fuentes transitivas.
No cambian atributos Git, datos históricos, parámetros, normas o gates.

[Datos](../evidence/loudness_latch_bdf_static_precision_modal_inputs.json.gz):
**359317 bytes**, SHA comprimido
`ebfb51aed442ec439930a311953ddf7005fa955422d7dfb6b1fbaf975b1d89d0`,
SHA canónico `df937752b09ef9380129ad9386db730385b341864d6db4e17168fbbae2cfe5f7`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_modal_inputs_summary.json).
La referencia Git exacta, fuentes, membresía en informes y bytes archivados
permiten reconstruir cada entrada sin depender del checkout de Windows.

La [suite](../tests/test_loudness_latch_bdf_static_precision_modal_inputs.py)
pasa **2/2 al primer intento**, 69.869492 s. Comprueba cobertura exacta de identidades, blobs, excepciones, versiones
históricas, esquemas y destinos propios. El recibo modal tiene identidad
propia y no se confunde con el certificado de norma anterior. Los datos
numéricos históricos y las versiones fallidas permanecen intactos.
El [recibo](../evidence/loudness_latch_bdf_static_precision_modal_inputs_validation.json)
registra comando, conteos, salida y SHA antes/después idénticos.

Este bloque suma **ocho regresiones nuevas**, todas pasan al primer intento:
seis modales y dos de reconstrucción. No hay nuevas versiones de tests
fallidas ni intentos de archivo rechazados.
El conteo modal sólo certifica matrices congeladas del bloque interno.
**Anclaje, restos no lineales, recorrido completo y 1 mV global siguen abiertos.**
No hay cambios en audio o admisión de tiempo real.

```powershell
python tools/loudness_latch_bdf_static_precision_modal_inputs.py
python tools/validate_bdf_static_precision_modal_inputs.py
```
