# Corpus de propagación por celdas

El corpus amplía la reconstrucción a **53 informes y 313 entradas**:
**310 blobs idénticos** y las tres excepciones históricas LF→CRLF.
Conserva **ocho versiones fallidas de tests anteriores**; ninguna prueba
nueva falla. La referencia de reconstrucción es `7d76c55b30d4f1b9636e8cc7809dbc3058b2199f`.
Ayudante, pruebas y validador se commitearon antes de generar la versión válida.

La [suite](../tests/test_loudness_latch_bdf_static_precision_cell_inputs.py)
pasa **2/2 al primer intento** en 59.0434701 s. Verifica identidad
de cada fuente desde blobs, reconstrucción de excepciones, recibos tipados,
versiones fallidas, almacenamiento canónico y rechazo de bytes alterados.
El [recibo](../evidence/loudness_latch_bdf_static_precision_cell_inputs_validation.json)
conserva SHA antes/después idénticos.

[Datos](../evidence/loudness_latch_bdf_static_precision_cell_inputs.json.gz):
**355050 bytes**, SHA comprimido
`9a9ba45114831928921c822c05e522a55838236442f67c3113fc478c8f9be427`,
SHA canónico `f7fd4d50ce8ba838447d82499be82f5f6bcd49e9523acacd2fe8488ede6f364e`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_cell_inputs_summary.json).

## Intento de archivo rechazado

El primer adaptador conservó por error la ruta SUMMARY del corpus ponderado
y escribió allí el resumen nuevo. Su ejecución terminó con exit code 0,
pero se **rechaza** ese intento. Se restauró el resumen anterior exactamente
desde su blob; su SHA vigente sigue siendo
`27c87934660453625edff451847ade8f6715226ca7f3326ec85946276872e4d4`.
La medición numérica, sus datos y su validación no cambian ni se repiten.

El [registro](../evidence/loudness_latch_bdf_static_precision_cell_inputs_destination_attempt.json)
conserva fuente del adaptador, SHA, revisión `68712ce`, comando, destino,
bytes escritos y restaurados. Se preservan [datos del primer intento](../evidence/loudness_latch_bdf_static_precision_cell_inputs_first_attempt.json.gz)
y [resumen rechazado](../evidence/loudness_latch_bdf_static_precision_cell_inputs_first_attempt_summary.json).
La suite compara la fuente fallida con su blob original, identifica la
versión corregida y exige el SHA restaurado. Estos tres archivos quedan
ligados por SHA al corpus válido, junto a sus fuentes auxiliares.
No se cuenta como versión fallida de test ni como medición nueva.

El bloque suma **nueve regresiones nuevas**: siete de propagación y dos
de archivo, todas pasan al primer intento. Los atributos Git y datos
históricos permanecen intactos. Reconstruir bytes no cierra error del DAE,
anclaje, recorrido completo, fidelidad física, audio o deadline.
**1 mV global sigue abierto.**

```powershell
python tools/loudness_latch_bdf_static_precision_cell_inputs.py
python tools/validate_bdf_static_precision_cell_inputs.py
```
