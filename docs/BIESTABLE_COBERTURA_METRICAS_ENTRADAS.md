# Corpus del inventario de cobertura y conversiones de norma

La reconstrucción alcanza **71 informes y 412 entradas**:
**409 blobs idénticos** y tres excepciones históricas LF→CRLF. Conserva
ocho versiones fallidas anteriores de tests. Helper, suite y validador se
fijaron en `7d73570` antes de generar el corpus. Se añaden inventario de
cobertura/puentes y recibo primario, con sus dependencias transitivas.
No cambian atributos Git, fuentes anteriores, parámetros o gates.

[Datos](../evidence/loudness_latch_bdf_static_precision_coverage_inputs.json.gz):
**365555 bytes**, SHA comprimido
`afeedb2f151b330992f3a7059d3101c2460b7869c6445515f2212c612dbfba17`,
SHA canónico `6d4f9b8534dff04da8967c88d474c13a6290fd7cf66ff7ff5d4e0ac122e97798`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_coverage_inputs_summary.json).
Se conservan referencia Git, fuentes, membresías y versiones históricas;
las tres excepciones reconstruyen exactamente los bytes archivados.

La [suite](../tests/test_loudness_latch_bdf_static_precision_coverage_inputs.py)
pasa **2/2 al primer intento**, 69.6379643 s. Exige unión exacta de
identidades, recuperación de blobs, excepciones declaradas y versiones
fallidas por SHA. Verifica esquema, destinos propios, 8.022 intervalos
auditados, 36 puentes y 990 consultas. Mantiene separadas procedencia
numérica y cobertura del error real, cuyo tiempo certificado permanece cero.
El [recibo](../evidence/loudness_latch_bdf_static_precision_coverage_inputs_validation.json)
guarda comandos, conteos, salida y SHA antes/después idénticos.

Este corte suma **ocho regresiones nuevas**, todas pasan al primer intento:
seis de cobertura/puentes y dos de reconstrucción. No hay validaciones
fallidas nuevas ni archivos rechazados. Reset conserva sus dos candidatos
rechazados, con evidencia de inversa y modos sin modificar.

**1 mV global sigue abierto.** Linaje desde DC, soporte de un interpolante
y mapas entre normas no demuestran anclaje, resto, huecos temporales o
interfaces de historias distintas. La reconstrucción exacta tampoco
certifica física vintage, voz audible o deadline.

```powershell
python tools/loudness_latch_bdf_static_precision_coverage_inputs.py
python tools/validate_bdf_static_precision_coverage_inputs.py
```
