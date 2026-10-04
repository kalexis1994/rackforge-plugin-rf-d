# Corpus del DC y la auditoría del evento KEY

La reconstrucción alcanza **73 informes y 423 entradas**:
**420 blobs idénticos** y tres excepciones históricas LF→CRLF. Conserva
**nueve versiones fallidas de tests**, incluida la primera fuente de la
suite de DC de este bloque. Helper, pruebas y validador del corpus se
fijaron en `3a93994` antes de generarlo. Se añaden datos DC y su recibo
de dos intentos, con sus dependencias transitivas y versiones identificadas.
No se modifican datos anteriores, atributos Git, parámetros o gates.

[Datos](../evidence/loudness_latch_bdf_static_precision_dc_inputs.json.gz):
**369511 bytes**, SHA comprimido
`19422881e3f7bf2eac3ded66f7615c5f1f2b911397d305e170a8592642071362`,
SHA canónico `c74cf9487fa5d329e7acc9341d9410493b79675430058c39c419352470774204`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_dc_inputs_summary.json).
Referencia Git, fuentes, membresías, versiones fallidas y transformaciones
históricas permiten recuperar exactamente los bytes utilizados.

La [suite](../tests/test_loudness_latch_bdf_static_precision_dc_inputs.py)
pasa **2/2 al primer intento**, 68.2006516 s. Exige cobertura exacta de
identidades, blobs, excepciones y fuentes fallidas por SHA. Verifica los
cuatro recintos DC, 25 memorias, refutación del dominio de KEY y ausencia
de un anclaje post-KEY demostrado. Comprueba ambos intentos primarios:
primero fallido, segundo exitoso, con fuentes intactas en cada ejecución.
El [recibo](../evidence/loudness_latch_bdf_static_precision_dc_inputs_validation.json)
conserva comandos, salida, conteos y SHA antes/después idénticos.

Este corte suma **ocho regresiones nuevas que pasan**: seis primarias en
el segundo intento y dos del corpus en el primero. El fallo original de
tests se preserva completo, con dos problemas en una única versión de
fuente. Los datos numéricos no se regeneraron ni se relajaron tolerancias.
La comparación corregida usa intervalos puntuales racionales exteriores,
sin considerar exacto un resultado Decimal redondeado.

**1 mV global sigue abierto.** El recinto DC es precisión numérica del
modelo nominal; la consistencia del evento KEY, anclaje posterior, resto
temporal y recorrido completo requieren pruebas propias. Bytes recuperables
no identifican física vintage, sonido o deadline.

```powershell
python tools/loudness_latch_bdf_static_precision_dc_inputs.py
python tools/validate_bdf_static_precision_dc_inputs.py
```
